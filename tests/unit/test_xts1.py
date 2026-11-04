"""XTS-1 on prices built so the answer is known: the exposure for a day reads only the closes before it; a change of
exposure pays its cost and holding pays nothing; a missing price is no trade, never filled; a market that trends pays
the rule and one that whipsaws does not; the judge never reads the holdout's prices; a month whose archive does not
match its published sha256 is refused."""

from __future__ import annotations

import hashlib
import io
import json
import zipfile
from datetime import date, timedelta

import pytest

import scripts.xts1 as X


def series(start: date, end: date, step) -> dict[date, float]:
    """Closes from `start` to `end`, each day's return given by step(day index)."""
    out, c, d, i = {}, 100.0, start, 0
    while d < end:
        out[d] = c
        c *= 1 + step(i)
        d += timedelta(days=1)
        i += 1
    return out


def trends(i):  # 60 days up 1% a day, 60 days down 1% a day, again and again
    return 0.01 if (i // 60) % 2 == 0 else -0.01


def test_the_exposure_for_a_day_reads_only_the_closes_before_it():
    c = series(date(2020, 1, 1), date(2020, 3, 1), lambda i: 0.01)
    d = date(2020, 2, 10)
    assert X.exposure(c, d) == 1.0  # up over 7, 14 and 28 days
    later = {**c, d + timedelta(days=1): 1.0, d + timedelta(days=2): 1e9}  # anything after d
    assert X.exposure(later, d) == 1.0
    mixed = {**c, d: c[d - timedelta(days=10)]}  # back to its level of 10 days ago: down over 7, up over 14 and 28
    assert X.exposure(mixed, d) == pytest.approx(2 / 3)
    assert X.exposure({k: v for k, v in c.items() if k != d - timedelta(days=14)}, d) is None  # a close it needs


def test_a_change_of_exposure_pays_its_cost_and_holding_pays_nothing():
    c = series(date(2020, 1, 1), date(2020, 4, 1), lambda i: 0.01)
    s = X.sleeve(c, date(2020, 2, 1), date(2020, 3, 1))
    first, second = s[date(2020, 2, 1)], s[date(2020, 2, 2)]
    assert first["exp"] == 1.0 and first["net"] == pytest.approx(first["ret"] - X.COST)  # entering from flat
    assert second["net"] == pytest.approx(second["ret"])  # held: no cost
    gap = {k: v for k, v in c.items() if k != date(2020, 2, 10)}
    s = X.sleeve(gap, date(2020, 2, 1), date(2020, 3, 1))
    assert date(2020, 2, 10) not in s and date(2020, 2, 11) not in s  # no price, no trade: never filled
    # the lookbacks that need the missing close cannot be read either; the first day traded again pays to re-enter
    back = min(d for d in s if d > date(2020, 2, 11))
    assert s[back]["net"] == pytest.approx(s[back]["ret"] - X.COST)


def book_data(val_step=trends):
    a, b = date(2017, 11, 1), date(2024, 7, 1)
    return {s: {**series(a, X.VAL[0], trends), **{d: v for d, v in series(a, b, lambda i: trends(i)
                                                                           if date(2017, 11, 1) + timedelta(days=i)
                                                                           < X.VAL[0] else val_step(i)).items()
                                                  if d >= X.VAL[0]}} for s in X.SYMBOLS}


def test_a_market_that_trends_pays_the_rule_and_its_timing_beats_holding_the_same_exposure():
    res = X.gates(book_data(), thr=3.0)
    assert res["passed"], res["failed_gates"]
    assert res["net"]["mean"] > 0 and res["timing"]["mean"] > 0 and res["top_year_share"] <= 0.5


def test_a_market_that_whipsaws_in_validation_fails_it():
    whipsaw = book_data(val_step=lambda i: 0.03 if i % 2 == 0 else -0.029)  # up a day, down a day
    res = X.gates(whipsaw, thr=3.0)
    assert not res["passed"] and "validation" in res["failed_gates"] and res["development"]["mean"] > 0


def write_month(rows: list[tuple[int, float]]) -> tuple[bytes, bytes]:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        z.writestr("X-1d.csv", "".join(f"{t},1,1,1,{c},1,{t + 86_399_999},1,1,1,1,0\n" for t, c in rows))
    data = buf.getvalue()
    return data, f"{hashlib.sha256(data).hexdigest()}  X-1d.zip\n".encode()


def test_a_month_is_read_only_when_its_archive_matches_the_published_sha256():
    data, chk = write_month([(1_514_764_800_000, 13_500.5), (1_514_851_200_000_000, 14_000.0)])  # ms, then µs
    assert X.parse_month(data, chk) == [("2018-01-01", 13_500.5), ("2018-01-02", 14_000.0)]
    with pytest.raises(ValueError, match="sha256"):
        X.parse_month(data + b"x", chk)
    bad, chk2 = write_month([(1_514_764_800_000, -1.0)])
    with pytest.raises(ValueError, match="invalid close"):
        X.parse_month(bad, chk2)


def test_the_judge_never_reads_the_holdouts_prices_and_refuses_a_missing_month(tmp_path, monkeypatch):
    monkeypatch.setattr(X, "DATA", tmp_path)
    for s in X.SYMBOLS:
        (tmp_path / f"{s}_1d.csv").write_text("date,close\n2024-06-30,1.0\n2024-07-01,2.0\n")
    man = {"symbols": {s: {"failed_months": []} for s in X.SYMBOLS}}
    (tmp_path / "manifest.json").write_text(json.dumps(man))
    got = X.load(X.JUDGE[1])
    assert all(list(v) == [date(2024, 6, 30)] for v in got.values())  # cut at the holdout
    man["symbols"]["ETHUSDT"]["failed_months"] = [{"month": "2020-03", "why": "not fetched"}]
    (tmp_path / "manifest.json").write_text(json.dumps(man))
    with pytest.raises(SystemExit, match="nothing is filled"):
        X.load(X.JUDGE[1])
    man["symbols"]["ETHUSDT"]["failed_months"] = [{"month": "2025-03", "why": "not fetched"}]  # a holdout month
    (tmp_path / "manifest.json").write_text(json.dumps(man))
    assert X.load(X.JUDGE[1])  # the judge does not need it


def test_the_threshold_counts_every_earlier_crypto_test():
    class Reg:
        def tests_on(self, u, a, b):
            return {"crypto-binance-usdtm": 10, "crypto-binance-usdtm-all": 5}.get(u, 0)
    assert X.threshold(Reg()) == pytest.approx(max(3.0, X.bonferroni_t(15 + X.TESTS)))
    assert X.threshold(type("R", (), {"tests_on": lambda self, u, a, b: 0})()) == 3.0  # never below 3.0
