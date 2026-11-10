"""LIQ-1 stage 1 on markets built so the answer is known: cascades placed at known hours, a rebound of known size after
them (or none), and the traps a look-ahead or a filled-in price would fall into. No test reaches Binance."""

from __future__ import annotations

import hashlib
import io
import zipfile
from datetime import date, datetime, timedelta, timezone

import numpy as np
import pytest

import scripts.liq1 as L

UTC = timezone.utc
START = datetime(2021, 1, 1, tzinfo=UTC)


def build(symbol="BTCUSDT", hours=24 * 160, cascades=(), rebound=0.0, rebound_noise=0.0, seed=1, start=START,
          spike_after=None, drift=0.0):
    """Hourly klines with small noise and flat open interest; at each cascade hour i a -8% hour and a 10% fall in open
    interest; from hour i + 2 on, 26 hours that add `rebound` over any 24 of them (so an entry at i + 2 or at i + 3 held
    24 hours earns exactly `rebound` above the drift, when rebound_noise is 0). `spike_after` puts a +20% hour at i + 1,
    between the event and the entry: no trade may earn it. `drift`, a log return every other hour, can repay the
    cascades, so that a random entry earns as much as one after a cascade when nothing reverses."""
    rng = np.random.default_rng(seed)
    r = drift + rng.normal(0.0, 0.004, hours)
    d = np.zeros(hours)
    for i in cascades:  # the hours after each cascade first, the cascades last, so a later one is never overwritten
        r[i + 1] = 0.20 if spike_after else drift
        r[i + 2:i + 28] = drift + np.log1p(rebound) / 24 + rng.normal(0.0, rebound_noise, len(r[i + 2:i + 28]))
    for i in cascades:
        r[i], d[i] = -0.08, -0.10
    o, c, q = np.empty(hours), np.empty(hours), np.empty(hours + 1)
    p, q[0] = 100.0, 1e6
    for i in range(hours):
        o[i], c[i] = p, p * np.exp(r[i])
        p = c[i]
        q[i + 1] = q[i] * np.exp(d[i])
    t0 = int(start.timestamp())
    return L.Series(symbol, t0, o, c, q[:hours])


def far(n, first=L.WINDOW_H + 10, gap=60):
    return [first + k * gap for k in range(n)]


END = START + timedelta(days=400)


# ── the event and the trade ─────────────────────────────────────────────────

def test_the_cascades_built_are_the_events_found_and_each_trade_earns_the_rebound_built_after_it():
    cas = far(5)
    s = build(cascades=cas, rebound=0.03)
    assert L.events(s) == cas  # flat open interest elsewhere: nothing else falls below its 1st percentile
    tr, missing = L.trades(s, L.events(s), END)
    assert missing == 0 and [t["event_hour"] for t in tr] == [s.at(i).isoformat() for i in cas]
    assert all(t["entry"] == s.at(i + 2).isoformat() and t["exit"] == s.at(i + 26).isoformat() for t, i in zip(tr, cas))
    assert np.allclose([t["gross"] for t in tr], 0.03)
    assert np.allclose(L.net(tr), 0.03 - 2 * L.COST) and np.allclose(L.net(tr, 2.0), 0.03 - 4 * L.COST)


def test_nothing_after_the_event_hour_changes_it_and_the_hour_before_the_entry_is_never_earned():
    cas = far(3)
    s = build(cascades=cas, rebound=0.03, spike_after=True)
    tr, _ = L.trades(s, L.events(s), END)
    assert np.allclose([t["gross"] for t in tr], 0.03)  # the +20% hour between the event and the entry is not in it
    last = cas[-1]
    t2 = build(cascades=cas, rebound=0.03, spike_after=True)
    t2.open[last + 1:] *= 3.0  # rewrite every price and open interest after the event hour
    t2.close[last + 1:] *= 0.5
    t2.oi[last + 2:] *= 7.0
    assert [i for i in L.events(t2) if i <= last] == [i for i in L.events(s) if i <= last]


def test_a_percentile_never_sees_its_own_hour_or_any_later_one():
    x = np.random.default_rng(3).normal(0, 1, 3000)
    p = L.trailing_pct(x, window=2160, min_n=1800, q=1.0)
    i = 2500
    assert p[i] == np.percentile(x[i - 2160:i], 1.0)
    y = x.copy()
    y[i:] = -1e9  # hour i and everything after it
    assert L.trailing_pct(y, window=2160, min_n=1800, q=1.0)[i] == p[i]
    assert np.isnan(p[:2160]).all()  # no percentile before a full window


def test_one_position_at_a_time_an_event_inside_an_open_trade_is_passed_over():
    first = L.WINDOW_H + 10
    s = build(cascades=[first, first + 10, first + 40], rebound=0.03)
    tr, _ = L.trades(s, L.events(s), END)
    assert [t["event_hour"] for t in tr] == [s.at(first).isoformat(), s.at(first + 40).isoformat()]


def test_a_missing_price_or_snapshot_is_never_filled_in():
    cas = far(3)
    s = build(cascades=cas, rebound=0.03)
    s.oi[cas[0] + 1] = np.nan  # the snapshot that closes the first event hour
    s.open[cas[1] + 26] = np.nan  # the second trade's exit price
    ev = L.events(s)
    assert cas[0] not in ev and cas[1] in ev
    tr, missing = L.trades(s, ev, END)
    assert missing == 1 and [t["event_hour"] for t in tr] == [s.at(cas[2]).isoformat()]


def test_a_trade_whose_exit_reaches_the_end_of_the_stage_is_not_taken():
    cas = far(2)
    s = build(cascades=cas, rebound=0.03)
    end = s.at(cas[1] + 26)  # the second exit lands exactly on the end: excluded
    tr, missing = L.trades(s, L.events(s), end)
    assert len(tr) == 1 and missing == 0


# ── the gates ───────────────────────────────────────────────────────────────

GAP = 150  # the mean hours between cascades: fewer than 1% of any window, as the 1st percentile assumes


def poisson(n, seed, first=L.WINDOW_H + 10):
    """n cascade hours at random, memoryless: the hours after one are as likely to hold another as any hours are."""
    gaps = np.random.default_rng(seed).exponential(GAP, n).astype(int) + 1
    return [int(first + g) for g in np.cumsum(gaps) - gaps[0]]


def two_coins(rebound, n=36, noise=0.002):
    """Two coins whose cascades come at random and are repaid on average by the drift between them. With no rebound,
    the hours after a cascade are like any others, so a trade then earns what a random entry earns."""
    out = {}
    for sym, seed in (("BTCUSDT", 5), ("ETHUSDT", 6)):
        cas = poisson(n, seed + 100)
        out[sym] = build(sym, hours=cas[-1] + 400, cascades=cas, rebound=rebound, rebound_noise=noise, seed=seed,
                         drift=0.08 / GAP)
    return out


def test_cascades_more_frequent_than_the_percentile_stop_counting_as_extreme():
    """The rule's own property: an event must be rarer than 1% of the window. Cascades every 60 hours fill the window's
    lowest 1%, and later ones are no longer below it."""
    cas = far(40, gap=60)
    s = build(hours=L.WINDOW_H + 60 * 40 + 100, cascades=cas, rebound=0.03)
    ev = L.events(s)
    assert ev[:5] == cas[:5] and len(ev) < len(cas)


def test_a_planted_rebound_passes_every_gate():
    res = L.evaluate(two_coins(0.04), END)
    assert res["passed"] and res["failed_gates"] == [], res["failed_gates"]
    assert res["all"]["trades"] >= L.MIN_TRADES and res["random"]["p95"] < res["all"]["mean"]
    assert res["all"]["mean"] - res["random"]["mean"] == pytest.approx(0.04, abs=0.012)  # the rebound, above chance
    assert res["projected_stage2_t"] >= L.PROJECTED_T_MIN


def test_cascades_followed_by_nothing_fail_and_match_the_random_entries():
    res = L.evaluate(two_coins(0.0, noise=0.004), END)
    assert not res["passed"] and "beats_random" in res["failed_gates"]
    se = res["all"]["sd"] / np.sqrt(res["all"]["trades"])
    assert abs(res["all"]["mean"] - res["random"]["mean"]) < 2 * se  # the drift alone: what a random entry earns


def test_too_few_trades_fail_whatever_they_earned():
    res = L.evaluate(two_coins(0.04, n=8), END)
    assert "trades" in res["failed_gates"] and not res["passed"]


def test_the_week_clustered_t_counts_one_cascade_on_both_coins_once():
    x = np.array([0.01, 0.012, -0.002, 0.004, 0.02, 0.018])
    weeks_one_each = ["a", "b", "c", "d", "e", "f"]
    weeks_paired = ["a", "a", "b", "b", "c", "c"]
    assert L.cluster_t(x, weeks_paired) < L.cluster_t(x, weeks_one_each)  # fewer independent weeks, less evidence


# ── the data ────────────────────────────────────────────────────────────────

def test_stage_one_lists_and_reads_nothing_from_2024_on():
    for sym in L.SYMBOLS:
        urls = [u for _, u in L.files(sym)]
        assert urls and all("2024-" not in u and "2025-" not in u and "2026-" not in u for u in urls)
        assert any(f"{L.OI_FIRST[sym]:%Y-%m-%d}" in u for u in urls)
    assert L.DEV_END == L.STAGE2[0] == date(2024, 1, 1)


def _zip(name, text):
    b = io.BytesIO()
    with zipfile.ZipFile(b, "w") as z:
        z.writestr(name, text)
    return b.getvalue()


def test_a_file_that_differs_from_its_checksum_stops_the_fetch(monkeypatch):
    raw = _zip("x.csv", "create_time,symbol,sum_open_interest\n")
    good = hashlib.sha256(raw).hexdigest()
    monkeypatch.setattr(L, "_get", lambda url, tries=4: (f"{good}  x.zip".encode() if url.endswith(".CHECKSUM") else raw))
    assert L.checked("https://x/x.zip")[1] == good
    monkeypatch.setattr(L, "_get", lambda url, tries=4: (b"0" * 64 + b"  x.zip" if url.endswith(".CHECKSUM") else raw))
    with pytest.raises(SystemExit):
        L.checked("https://x/x.zip")


def test_only_snapshots_on_the_hour_are_kept_and_a_kline_header_is_skipped():
    m = _zip("m.csv", "create_time,symbol,sum_open_interest,sum_open_interest_value\n"
                      "2021-12-01 00:00:00,BTCUSDT,100.5,1\n2021-12-01 00:05:00,BTCUSDT,101,1\n"
                      "2021-12-01 01:00:00,BTCUSDT,99,1\n")
    assert L.parse_metrics(m) == ({"2021-12-01T00": 100.5, "2021-12-01T01": 99.0}, 0)
    ms = int(datetime(2021, 12, 1, 3, tzinfo=UTC).timestamp() * 1000)
    k = _zip("k.csv", f"open_time,open,high,low,close,volume\n{ms},10,11,9,10.5,1\n{(ms + 3600000) * 1000},10.5,11,9,10,1\n")
    assert L.parse_klines(k) == ({"2021-12-01T03": (10.0, 10.5), "2021-12-01T04": (10.5, 10.0)}, 0)


def test_a_row_that_cannot_be_read_leaves_its_hour_missing_and_is_counted():
    m = _zip("m.csv", "\ufeffcreate_time,symbol,sum_open_interest\n2021-12-01 00:00:00.000,BTCUSDT,100\n"
                      "2021-12-01 01:00:00,BTCUSDT,\nnot a time,BTCUSDT,5\n2021-12-01 02:00:00,BTCUSDT,0\n")
    assert L.parse_metrics(m) == ({"2021-12-01T00": 100.0}, 3)
    ms = int(datetime(2021, 12, 1, 3, tzinfo=UTC).timestamp() * 1000)
    k = _zip("k.csv", f"{ms},10,11,9,nan,1\n{ms + 3600000},10,11,9,10.5,1\n")
    assert L.parse_klines(k) == ({"2021-12-01T04": (10.0, 10.5)}, 1)


def test_an_hour_from_2024_on_is_refused_by_the_fetch_and_by_the_loader(tmp_path, monkeypatch):
    """Stage 2's data may never reach stage 1, even if a listed file held them."""
    import json
    monkeypatch.setattr(L, "DATA", tmp_path)
    metrics = _zip("m.csv", "create_time,symbol,sum_open_interest\n2023-12-31 23:00:00,BTCUSDT,10\n"
                            "2024-01-01 00:00:00,BTCUSDT,11\n")
    monkeypatch.setattr(L, "files", lambda sym: [("metrics", f"https://x/{sym}.zip")])
    monkeypatch.setattr(L, "checked", lambda url: (metrics, hashlib.sha256(metrics).hexdigest()))
    with pytest.raises(SystemExit, match="2024-01-01"):
        L.cmd_fetch(datetime(2026, 11, 10, tzinfo=UTC))
    oi = {"2023-12-31T23": 10.0, "2024-01-01T00": 11.0}
    kl = {"2023-12-31T23": [1.0, 1.0], "2024-01-01T00": [1.0, 1.0]}
    man = {"symbols": {}}
    for sym in L.SYMBOLS:
        (tmp_path / f"{sym}-oi.json").write_text(L._canon(oi))
        (tmp_path / f"{sym}-klines.json").write_text(L._canon(kl))
        man["symbols"][sym] = {"oi_sha256": hashlib.sha256(L._canon(oi).encode()).hexdigest(),
                               "klines_sha256": hashlib.sha256(L._canon(kl).encode()).hexdigest()}
    (tmp_path / "manifest.json").write_text(json.dumps(man))
    with pytest.raises(SystemExit, match="refuses"):
        L.load()
