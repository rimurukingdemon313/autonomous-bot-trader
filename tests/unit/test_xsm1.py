"""XSM-1 on markets built so the answer is known: stablecoins, fiat and leveraged tokens are not coins; the universe
and the pick read only what was known at the rebalance close; a delisting's loss is kept; every trade pays, the
week's drift included; coins whose rise persists pass and coins that reverse fail; the archive's listing is read to
its last page; a month is read only when it matches its sha256; the judge never reads the holdout."""

from __future__ import annotations

import gzip
import hashlib
import io
import json
import zipfile
from datetime import date, datetime, timedelta, timezone

import pytest

import scripts.xsm1 as X


def test_stablecoins_fiat_and_leveraged_tokens_are_not_coins():
    names = ["BTCUSDT", "ETHUSDT", "JUPUSDT", "SUSDT", "PAXGUSDT", "USDCUSDT", "FDUSDUSDT", "TUSDUSDT", "BUSDUSDT",
             "DAIUSDT", "USTUSDT", "EURUSDT", "BTCUPUSDT", "BTCDOWNUSDT", "ETHBULLUSDT", "BULLUSDT", "ETHBTC"]
    bases = {n[:-4] for n in names if n.endswith("USDT")}
    kept = [n for n in names if X.tradable(n, bases)]
    assert kept == ["BTCUSDT", "ETHUSDT", "JUPUSDT", "SUSDT", "PAXGUSDT"]  # JUP is a coin: no "J" to lever


START = date(2018, 1, 1)


def series(days: int, price=lambda k: 100.0, vol=lambda k: 1.0, start: date = START) -> dict:
    return {start + timedelta(days=k): (price(k), vol(k)) for k in range(days)}


def test_the_universe_and_the_pick_read_only_what_was_known_at_the_close():
    d = START + timedelta(days=120)
    data = {f"C{i:02d}USDT": series(200, vol=lambda k, i=i: 100.0 - i) for i in range(14)}
    data["NEWUSDT"] = series(89, vol=lambda k: 1e9, start=d - timedelta(days=88))  # 89 closes to d: too new
    gap = series(200, vol=lambda k: 1e9)
    del gap[d - timedelta(days=50)]
    data["GAPUSDT"] = gap  # a day missing within the 90 to d
    data["LATEUSDT"] = series(200, vol=lambda k: 1e9 if k > 120 else 0.0)  # its volume comes after d
    got = X.universe(data, d)
    assert "NEWUSDT" not in got and "GAPUSDT" not in got and got[0] == "C00USDT" and got[-1] == "LATEUSDT"
    assert len(got) == 15
    data["NEWUSDT"] = series(90, vol=lambda k: 1e9, start=d - timedelta(days=89))  # 90 closes: it qualifies, and leads
    assert X.universe(data, d)[0] == "NEWUSDT"
    assert X.universe({k: v for k, v in list(data.items())[:11]}, d) is None  # fewer than 12: no trade

    rows = series(200, price=lambda k: 100.0 + (k if k <= 120 else 1000.0))  # a jump after d is not momentum at d
    assert X.momentum(rows, d) == pytest.approx(220.0 / 199.0 - 1)


def test_a_delistings_loss_is_kept_and_a_coin_with_no_later_close_is_valued_at_entry():
    d = START + timedelta(days=100)
    full = series(120, price=lambda k: 100.0 if k <= 100 else 90.0)
    assert X.week_return(full, d) == (pytest.approx(-0.10), True)
    gone = {k: v for k, v in series(104, price=lambda k: 100.0 if k <= 100 else 5.0).items()}  # last close: d + 3
    assert X.week_return(gone, d) == (pytest.approx(-0.95), False)
    assert X.week_return(series(101), d) == (0.0, False)


def market(drift, wiggle=0.001):
    """24 coins from 2018-01 to 2024-07, volume fixed by rank (the top 20 are C00..C19), each moving by drift(i, week)
    every day, plus a small fixed wiggle."""
    days = (date(2024, 7, 1) - START).days
    data = {}
    for i in range(24):
        p, rows = 100.0, {}
        for k in range(days):
            day = START + timedelta(days=k)
            week = ((day - date(2017, 12, 31)).days - 1) // 7  # Monday..Sunday: the week a rebalance holds
            p *= 1 + drift(i, week) + (wiggle if (k + i) % 2 else -wiggle)
            rows[day] = (p, 1000.0 - i)
        data[f"C{i:02d}USDT"] = rows
    return data


def test_every_trade_pays_and_the_weeks_drift_is_traded_back():
    data = market(lambda i, w: 0.0001 * (24 - i), wiggle=0.0)  # the same four lead every week
    rows = X.books(data, date(2018, 10, 1), date(2018, 11, 1))
    first, second = rows[0], rows[1]
    assert first["book"]["gross"] - first["book"]["net"] == pytest.approx(X.COST * 1.0)  # bought from cash
    assert second["book"]["gross"] - second["book"]["net"] < X.COST * 0.05  # same coins, drift traded back only
    assert first["held"] == second["held"] == ["C00USDT", "C01USDT", "C02USDT", "C03USDT"]
    assert len(first["coins"]) == X.TOP_VOLUME


def persists(i, w):
    """8-week regimes: half the coins rise 0.5% a day, half fall, and the halves change each regime."""
    return 0.005 if (i * 7 + (w // 8) * 3) % 4 < 2 else -0.005


def reverses(i, w):
    """Each coin's move flips every week: last week's winners are next week's losers."""
    return (0.002 + 0.0003 * i) * (1 if w % 2 else -1)


def test_coins_whose_rise_persists_pass_and_coins_that_reverse_fail():
    res = X.gates(market(persists), thr=3.16)
    assert res["passed"], res["failed_gates"]
    assert res["difference"]["mean"] > 0.01 and res["weeks_without_trade"] == 0
    bad = X.gates(market(reverses), thr=3.16)
    assert not bad["passed"] and bad["difference"]["mean"] < 0
    assert {"t", "development", "validation"} <= set(bad["failed_gates"])


def test_the_archives_listing_is_read_to_its_last_page(monkeypatch):
    ns = 'xmlns="http://s3.amazonaws.com/doc/2006-03-01/"'
    pages = {
        "": f'<ListBucketResult {ns}><Prefix>p/</Prefix><IsTruncated>true</IsTruncated><NextMarker>p/B/</NextMarker>'
            '<CommonPrefixes><Prefix>p/A/</Prefix></CommonPrefixes><CommonPrefixes><Prefix>p/B/</Prefix>'
            '</CommonPrefixes></ListBucketResult>',
        "p/B/": f'<ListBucketResult {ns}><Prefix>p/</Prefix><IsTruncated>false</IsTruncated>'
                '<CommonPrefixes><Prefix>p/C/</Prefix></CommonPrefixes><Contents><Key>p/x.zip</Key></Contents>'
                '</ListBucketResult>'}

    def fake(url):
        marker = url.split("marker=")[1].replace("%2F", "/")
        return pages[marker].encode()
    monkeypatch.setattr(X, "_get", fake)
    assert X.list_s3("p/") == (["p/A/", "p/B/", "p/C/"], ["p/x.zip"])


def month_zip(rows):
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        z.writestr("X-1d.csv", "".join(",".join(map(str, r)) + "\n" for r in rows))
    data = buf.getvalue()
    return data, f"{hashlib.sha256(data).hexdigest()}  X.zip\n".encode()


def test_a_month_is_read_only_when_it_matches_its_sha256():
    ms = int(datetime(2024, 12, 31, tzinfo=timezone.utc).timestamp() * 1000)
    us = int(datetime(2025, 1, 1, tzinfo=timezone.utc).timestamp() * 1_000_000)  # the archive's microseconds
    data, chk = month_zip([[ms, 1, 2, 0.5, 1.5, 10, ms + 1, 15.0, 3, 0, 0, 0],
                           [us, 1, 2, 0.5, 1.7, 10, us + 1, 17.0, 3, 0, 0, 0]])
    assert X.parse_month(data, chk) == [("2024-12-31", 1.5, 15.0), ("2025-01-01", 1.7, 17.0)]
    with pytest.raises(ValueError, match="sha256"):
        X.parse_month(data + b"x", chk)


def test_the_judge_never_reads_the_holdout_and_never_fills_a_month(tmp_path, monkeypatch):
    monkeypatch.setattr(X, "DATA", tmp_path)

    def write(body: str, failed: dict):
        gz = gzip.compress(body.encode(), mtime=0)
        (tmp_path / "klines.csv.gz").write_bytes(gz)
        (tmp_path / "manifest.json").write_text(json.dumps({"file": "klines.csv.gz", "failed_months": failed,
                                                            "sha256": hashlib.sha256(gz).hexdigest()}))
    body = "symbol,date,close,quote_volume\nBTCUSDT,2024-06-30,1.0,5.0\nBTCUSDT,2024-07-01,2.0,5.0\n"
    write(body, {"ETHUSDT": [{"month": "2025-02", "why": "not fetched"}]})  # a holdout month: the judge goes on
    assert X.load(X.JUDGE[1]) == {"BTCUSDT": {date(2024, 6, 30): (1.0, 5.0)}}
    write(body, {"ETHUSDT": [{"month": "2021-05", "why": "not fetched"}]})
    with pytest.raises(SystemExit, match="nothing is filled"):
        X.load(X.JUDGE[1])
    write(body, {})
    (tmp_path / "klines.csv.gz").write_bytes(gzip.compress(b"symbol,date,close,quote_volume\n", mtime=0))
    with pytest.raises(SystemExit, match="does not match its manifest"):
        X.load(X.JUDGE[1])


def test_the_threshold_counts_every_earlier_crypto_test():
    class Reg:
        def tests_on(self, u, a, b):
            return {"crypto-binance-usdtm": 10, "crypto-binance-spot": 6, "crypto-xvenue-hl-binance": 8}.get(u, 0)
    assert X.threshold(Reg()) == pytest.approx(max(3.0, X.bonferroni_t(24 + X.TESTS)))
