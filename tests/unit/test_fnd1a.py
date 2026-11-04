"""FND-1A (FND-1 amended before any outcome) on funding and prices built so the answer is known: the crowding signal reads only the settlements published
before the close it decides at; above the crowded rate the book stands aside; a crowd that is followed by a crash
pays the rule, and one followed by more gains does not; the judge never reads the holdout's prices or settlements; a
month whose archive does not match its published sha256 is refused."""

from __future__ import annotations

import hashlib
import io
import json
import zipfile
from datetime import date, datetime, timedelta, timezone

import pytest

import scripts.fnd1a as F


def ts(d: date, h: int = 0) -> int:
    return int(datetime(d.year, d.month, d.day, h, tzinfo=timezone.utc).timestamp())


def coin(start: date, end: date, ret, rate):
    """Closes moved by ret(day index), and three settlements a day at 00:00, 08:00 and 16:00 at rate(day index)."""
    closes, ft, fr, c, d, i = {}, [], [], 100.0, start, 0
    while d < end:
        closes[d] = c
        for h in (0, 8, 16):
            ft.append(ts(d, h))
            fr.append(rate(i))
        c *= 1 + ret(i)
        d += timedelta(days=1)
        i += 1
    return {"closes": closes, "fund_t": ft, "fund_r": fr}


def test_the_crowding_signal_reads_only_settlements_published_before_the_close():
    c = coin(date(2021, 1, 1), date(2021, 3, 1), lambda i: 0.0, lambda i: 0.0001)
    d = date(2021, 2, 1)
    assert F.crowded_mean(c, d) == pytest.approx(0.0001)
    at_close = ts(d + timedelta(days=1))  # the settlement at the decision time itself, and anything after it
    spiked = {**c, "fund_r": [0.01 if t >= at_close else r for t, r in zip(c["fund_t"], c["fund_r"])]}
    assert F.crowded_mean(spiked, d) == pytest.approx(0.0001)
    thin = {**c, "fund_t": c["fund_t"][::2], "fund_r": c["fund_r"][::2]}  # 10 or 11 of the 21: too few to read
    assert F.crowded_mean(thin, d) is None


def test_above_the_crowded_rate_the_book_stands_aside():
    calm = coin(date(2021, 1, 1), date(2021, 3, 1), lambda i: 0.0, lambda i: F.CROWDED)  # at the rate: not above it
    hot = coin(date(2021, 1, 1), date(2021, 3, 1), lambda i: 0.0, lambda i: F.CROWDED * 1.01)
    assert F.exposure(calm, date(2021, 2, 1)) == 1.0 and F.exposure(hot, date(2021, 2, 1)) == 0.0


def cycle(after_crowd: float):
    """60-day cycles: 40 calm days rising 0.5% a day, 10 crowded days (funding 0.05%) rising 0.3%, then 10 days moving
    `after_crowd` a day as the crowd unwinds; funding back to 0.01%."""
    def ret(i):
        k = i % 60
        return 0.005 if k < 40 else 0.003 if k < 50 else after_crowd

    def rate(i):
        return 0.0005 if 40 <= i % 60 < 50 else 0.0001
    return {s: coin(date(2019, 12, 1), date(2024, 7, 1), ret, rate) for s in F.SYMBOLS}


def test_a_crowd_followed_by_a_crash_pays_the_rule_and_its_timing_beats_holding():
    res = F.gates(cycle(-0.02), thr=3.11)
    assert res["passed"], res["failed_gates"]
    assert res["timing"]["mean"] > 0 and 0 < res["share_of_days_flat"]["BTCUSDT"] < 0.3


def test_a_crowd_followed_by_more_gains_fails_the_timing_gate():
    res = F.gates(cycle(0.02), thr=3.11)
    assert not res["passed"] and "timing" in res["failed_gates"] and res["timing"]["mean"] < 0


def funding_month(rows):
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        z.writestr("X-fundingRate.csv", "calc_time,funding_interval_hours,last_funding_rate\n"
                   + "".join(f"{t},8,{r}\n" for t, r in rows))
    data = buf.getvalue()
    return data, f"{hashlib.sha256(data).hexdigest()}  X.zip\n".encode()


def test_a_funding_month_is_read_only_when_it_matches_its_sha256_and_its_rates_are_plausible():
    data, chk = funding_month([(1_577_836_800_000, 0.0001), (1_577_865_600_000, -0.0002)])
    assert F.parse_funding(data, chk) == [(1_577_836_800, 0.0001), (1_577_865_600, -0.0002)]
    with pytest.raises(ValueError, match="sha256"):
        F.parse_funding(data + b"x", chk)
    bad, chk2 = funding_month([(1_577_836_800_000, 0.5)])
    with pytest.raises(ValueError, match="implausible"):
        F.parse_funding(bad, chk2)


def test_the_judge_never_reads_the_holdouts_prices_or_settlements(tmp_path, monkeypatch):
    monkeypatch.setattr(F, "DATA", tmp_path)
    for s in F.SYMBOLS:
        (tmp_path / f"{s}_1d.csv").write_text("date,close\n2024-06-30,1.0\n2024-07-01,2.0\n")
        (tmp_path / f"{s}_funding.csv").write_text(f"t,rate\n{ts(date(2024, 6, 30), 16)},0.0001\n"
                                                   f"{ts(date(2024, 7, 1))},0.0009\n")
    man = {"symbols": {s: {"failed_months": []} for s in F.SYMBOLS}}
    (tmp_path / "manifest.json").write_text(json.dumps(man))
    got = F.load(F.JUDGE[1])
    for v in got.values():
        assert list(v["closes"]) == [date(2024, 6, 30)] and v["fund_r"] == [0.0001]
    man["symbols"]["BTCUSDT"]["failed_months"] = [{"month": "2021-05", "kind": "funding", "why": "not fetched"}]
    (tmp_path / "manifest.json").write_text(json.dumps(man))
    with pytest.raises(SystemExit, match="nothing is filled"):
        F.load(F.JUDGE[1])
    # the amendment: the funding archive begins in 2020-01, so its absence before that is no gap; the klines' is
    man["symbols"]["BTCUSDT"]["failed_months"] = [{"month": m, "kind": "funding", "why": "not fetched"}
                                                  for m in ("2019-09", "2019-10", "2019-11", "2019-12")]
    (tmp_path / "manifest.json").write_text(json.dumps(man))
    assert F.load(F.JUDGE[1])
    man["symbols"]["BTCUSDT"]["failed_months"] = [{"month": "2019-12", "kind": "klines", "why": "not fetched"}]
    (tmp_path / "manifest.json").write_text(json.dumps(man))
    with pytest.raises(SystemExit, match="nothing is filled"):
        F.load(F.JUDGE[1])


def test_the_threshold_counts_every_earlier_crypto_test_xts1_included():
    class Reg:
        def tests_on(self, u, a, b):
            return {"crypto-binance-usdtm": 10, "crypto-binance-spot": 2}.get(u, 0)
    assert F.threshold(Reg()) == pytest.approx(max(3.0, F.bonferroni_t(12 + F.TESTS)))
