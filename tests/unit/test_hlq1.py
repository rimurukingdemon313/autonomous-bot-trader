"""HLQ-1 on markets built so that the answer is known: a price drawn to its visible clusters pays the rule; a price
that ignores them does not; a market that falls whatever its clusters say is no magnet."""

from __future__ import annotations

import gzip
import io
import json
import math
import zipfile
from datetime import date, datetime, timedelta, timezone

import numpy as np
import pytest

import scripts.hlq1 as S
from aitrader.research.events import hlq as H
from aitrader.research.registry import Registry, Trial, Use, Verdict

NOW = datetime(2027, 6, 13, 12, 0, tzinfo=timezone.utc)
M = H.MINUTE
CFG = {"lo": 0.01, "hi": 0.05, "imbalance": 0.75, "min_share": 0.01, "hold": 720}
C = 0.001


def test_positions_become_liquidation_levels_and_no_account_is_kept():
    states = [
        {"assetPositions": [{"position": {"coin": "BTC", "szi": "2", "liquidationPx": "95.1"}},
                            {"position": {"coin": "ETH", "szi": "-1", "liquidationPx": "103.1"}},
                            {"position": {"coin": "DOGE", "szi": "5", "liquidationPx": "1"}}]},
        {"assetPositions": [{"position": {"coin": "BTC", "szi": "1", "liquidationPx": None}},
                            {"position": {"coin": "BTC", "szi": "-3", "liquidationPx": "150"}},
                            {"position": {"coin": "BTC", "szi": "bad", "liquidationPx": "99"}}]}, None]
    a = H.aggregate(states, {"BTC": 100.0, "ETH": 100.0})
    assert set(a) == {"BTC", "ETH"}  # a coin without a mark is left out
    b = a["BTC"]
    assert b["L"] == {-20: 200.0} and b["L_usd"] == 300.0 and b["L_noliq"] == 100.0 and b["L_n"] == 2
    assert b["S"] == {} and b["S_far"] == 300.0 and b["S_n"] == 1
    assert a["ETH"]["S"] == {12: 100.0}
    assert "0x" not in json.dumps(a)


def test_a_signal_needs_one_side_to_dominate_a_cluster_large_enough():
    a = {"L": {"-20": 3e6, "-8": 1e6, "-2": 9e9}, "S": {"12": 1e6, "30": 9e9}, "oi_usd": 1e8}
    L, S_, dl, ds = H.clusters(a, 0.01, 0.05)  # -2 (0.375%) and 30 (7.6%) lie outside 1%..5%
    assert (L, S_) == (4e6, 1e6) and abs(dl - (3e6 * 0.04875 + 1e6 * 0.01875) / 4e6) < 1e-12 and abs(ds - 0.03125) < 1e-12
    s = H.signal(a, 0.01, 0.05, 0.75, 0.01)
    assert s["dir"] == -1 and abs(s["dist"] - dl) < 1e-12 and abs(s["B"] - 0.6) < 1e-12
    assert H.signal({**a, "S": {"12": 2e6}}, 0.01, 0.05, 0.75, 0.01) is None  # 4 of 6 is not three quarters
    assert H.signal({**a, "oi_usd": 1e9}, 0.01, 0.05, 0.75, 0.01) is None  # 0.5% of open interest
    assert H.signal({**a, "oi_usd": None}, 0.01, 0.05, 0.75, 0.01) is None
    up = H.signal({"L": {"-8": 1e6}, "S": {6: 5e6}, "oi_usd": 1e8}, 0.01, 0.05, 0.75, 0.01)
    assert up["dir"] == 1 and abs(up["dist"] - 0.01625) < 1e-12


def _path(prices, t0=0, wick=0.0):
    p = H.Path(t0, len(prices))
    rows, prev = [], prices[0]
    for i, x in enumerate(prices):
        o = prev
        rows.append((t0 + i * M, o, max(o, x) * (1 + wick), min(o, x) * (1 - wick), x))
        prev = x
    p.put(rows)
    return p


def test_a_trade_ends_at_its_target_its_stop_or_its_time_and_a_missing_minute_is_not_filled():
    up = _path([100.0] * 10 + [101.0, 102.5] + [102.5] * 20)
    t = H.trade(up, 30_000, +1, 0.02, C, 30)  # decided at 0:30: enters minute 1
    assert t["entry_ms"] == M and t["how"] == "target" and abs(t["ret"] - 0.02) < 1e-12 and abs(t["net"] - 0.018) < 1e-12
    s = H.trade(up, 0, -1, 0.02, C, 30)
    assert s["how"] == "stop" and abs(s["ret"] + 0.02) < 1e-12
    both = _path([100.0] * 5 + [100.0] * 20, wick=0.03)  # every minute reaches both levels: the stop
    assert H.trade(both, 0, +1, 0.02, C, 10)["how"] == "stop"
    flat = H.trade(_path([100.0] * 40), 0, +1, 0.02, C, 30)
    assert flat["how"] == "time" and flat["ret"] == 0.0
    hole = _path([100.0] * 40)
    hole.h[7] = np.nan
    assert H.trade(hole, 0, +1, 0.02, C, 30).get("missing")
    assert H.trade(_path([100.0] * 20), 0, +1, 0.02, C, 30).get("missing")  # the hold runs past the archive


def market(coins=("BTC", "ETH", "SOL", "XRP"), days=60, start="2026-12-01", magnet=True, drift=0.0, every=24,
           seed=7, all_signal_down=False, fall=180, back=360):
    """Snapshots every 30 minutes; on every `every`-th (staggered by coin) the longs below dominate: 4-6 million
    liquidated 1.6-2.4% under the mark against half a million of shorts above. Elsewhere the two sides balance. When
    `magnet`, the price falls 3% over the three hours after a signal and climbs back over the next six."""
    t0 = S.ms(start + "T00:00:00Z")
    n = days * 1440 + 4000
    rng = np.random.default_rng(seed)
    snaps, paths = {}, {}
    for k, c in enumerate(coins):
        inc = rng.normal(0, 0.0003, n) + drift
        xs = []
        for m in range(days * 48):
            t = t0 + m * 30 * M
            sig = (m - k) % every == 0 or (all_signal_down and m % 2 == 0)
            if sig:
                b = -7 - (m // every) % 3
                rec = {"L": {str(b): 4e6 + 1e6 * (m % 3)}, "S": {"11": 5e5}}
                i = (t + M - t0) // M + 1
                if magnet:
                    inc[i:i + fall] += math.log(0.97) / fall
                    inc[i + fall:i + fall + back] -= math.log(0.97) / back
            else:
                rec = {"L": {"-12": 1e6}, "S": {"11": 1e6}}
            xs.append({**rec, "oi_usd": 1e8, "t": t, "t_end": t + M})
        snaps[c] = xs
        price = 100 * np.exp(np.cumsum(inc))
        paths[c] = _path(list(price), t0, wick=0.0001)
    return t0, snaps, paths


def judged(t0, snaps, paths, days=60, min_events=150, min_days=40, cfg=CFG):
    first, last = t0, t0 + days * H.DAY
    evs = H.events(snaps, paths, first, last, cfg, C)
    late = H.events(snaps, paths, first, last, cfg, C, delay=30)
    plac = H.placebos(snaps, paths, evs, cfg, C, draws=20)
    return H.judge(evs, late, plac, 3.0, C, min_events, min_days, ("BTC", "ETH"), 30, draws=200), evs


def test_a_price_drawn_to_its_clusters_pays_the_rule():
    r, evs = judged(*market())
    assert r["verdict"] == "PASSED", r.get("gates")
    assert r["target_share"] > 0.9 and r["placebo_p95"] < r["mean_net"] / 2 and r["owner_trades"] >= 30
    assert all(e["dir"] == -1 for e in evs if not e.get("missing"))


def test_a_price_that_ignores_its_clusters_pays_nothing():
    r, _ = judged(*market(magnet=False))
    assert r["verdict"] == "FAILED" and r["mean_net"] < 0.002


def test_a_market_that_falls_whatever_its_clusters_say_is_no_magnet():
    # half the snapshots point down, and the price falls steadily all the time: the same short pays as much without
    # a signal, so the rule must not beat its placebo
    r, _ = judged(*market(magnet=False, drift=-0.00002, all_signal_down=True))
    assert r["mean_net"] > 0 and not r["gates"]["beats_placebo"] and r["verdict"] == "FAILED"


def test_a_move_that_is_over_within_half_an_hour_is_not_tradable():
    r, _ = judged(*market(fall=20, back=20))
    assert r["mean_net"] > 0.01 and r["late_mean"] < 0 and not r["gates"]["late_entry"] and r["verdict"] == "FAILED"


def test_the_placebo_is_drawn_only_where_the_rule_saw_no_signal_and_away_from_the_entry(monkeypatch):
    t0, snaps, paths = market(coins=("BTC",), days=10, every=6)
    e = [x for x in H.events(snaps, paths, t0, t0 + 10 * H.DAY, CFG, C) if not x.get("missing")][8]
    seen, real = [], H.trade
    monkeypatch.setattr(H, "trade", lambda p, at, *a, **k: seen.append(at) or real(p, at, *a, **k))
    plac = H.placebos(snaps, paths, [e], CFG, C, draws=40)
    sig = {s["t_end"] for s in snaps["BTC"] if H.signal(s, 0.01, 0.05, 0.75, 0.01) is not None}
    assert len(plac[("BTC", e["t"])]) == len(seen) == 40 and not set(seen) & sig
    assert all(6 * 3_600_000 <= abs(t - e["t"]) <= 3 * H.DAY for t in seen)


def test_without_the_owners_coins_or_with_too_few_entries_it_does_not_pass():
    r, _ = judged(*market(coins=("SOL", "XRP", "DOGE", "ADA")))
    assert r["gates"]["t"] and not r["gates"]["owner_instruments"] and r["verdict"] == "FAILED"
    r2, _ = judged(*market(days=10), days=10)
    assert r2["verdict"] == "INCONCLUSIVE"


def test_one_position_per_coin_and_nothing_after_the_exit_changes_a_trade():
    t0, snaps, paths = market(coins=("BTC",), days=12, every=2)
    evs = H.events(snaps, paths, t0, t0 + 12 * H.DAY, CFG, C)
    ok = [e for e in evs if not e.get("missing")]
    assert len(ok) > 5 and all(b["t"] >= a["exit_ms"] for a, b in zip(ok, ok[1:]))
    e = ok[2]
    i = (e["exit_ms"] - t0) // M + 1
    for arr in (paths["BTC"].o, paths["BTC"].h, paths["BTC"].l, paths["BTC"].c):
        arr[i:] *= 7.0
    again = next(x for x in H.events(snaps, paths, t0, t0 + 12 * H.DAY, CFG, C) if x["t"] == e["t"])
    assert abs(again["ret"] - e["ret"]) < 1e-12


def test_the_stage_can_reach_its_minimum_and_the_spec_keeps_its_promises():
    st = S.SPEC["stages"]["forward"]
    a, b = (datetime.fromisoformat(x.replace("Z", "+00:00")) for x in st["snapshots"])
    assert (b - a).days >= st["min_days"] and date.fromisoformat(st["not_before"]) > b.date() + timedelta(days=4)
    assert S.SPEC["bar_floor"] >= 3.0 and "swap-free" in S.SPEC["instrument"] and S.SPEC["owner_coins"] == ["BTC", "ETH"]
    assert S.SPEC["rule"]["lo"] < S.SPEC["rule"]["hi"] and S.SPEC["rule"]["imbalance"] > 0.5
    assert S.binance_symbol("kPEPE") == "PEPEUSDT" and S.binance_symbol("BTC") == "BTCUSDT"


def _fake_hyperliquid(fail_one=True):
    addrs = [f"0x{k:040x}" for k in range(1, 4)]

    def fetch(url, body):
        if url == S.BOARD:
            return {"leaderboardRows": [{"ethAddress": a, "accountValue": str(1e6 * (k + 1))} for k, a in enumerate(addrs)]}
        if body["type"] == "metaAndAssetCtxs":
            return [{"universe": [{"name": "BTC"}, {"name": "ETH"}, {"name": "OLD", "isDelisted": True},
                                  {"name": "TINY"}]},
                    [{"markPx": "100", "openInterest": "1000000"}, {"markPx": "100", "openInterest": "200000"},
                     {"markPx": "1", "openInterest": "1"}, {"markPx": "1", "openInterest": "10"}]]
        if body["type"] == "clearinghouseState":
            if fail_one and body["user"] == addrs[0]:
                raise RuntimeError("timed out")
            return {"assetPositions": [{"position": {"coin": "BTC", "szi": "1", "liquidationPx": "98.1"}}]}
        raise AssertionError(body)
    return fetch, addrs


def test_a_snapshot_counts_what_did_not_answer_and_writes_no_address(tmp_path):
    fetch, addrs = _fake_hyperliquid()
    clock = iter([1_800_000_000_000, 1_800_000_090_000]).__next__
    s = S.snapshot(fetch, clock, accounts=3)
    assert s["answered"] == 2 and s["failed"] == 1 and s["t_end"] - s["t"] == 90_000
    assert set(s["coins"]) == {"BTC", "ETH"}  # TINY's open interest is below the floor; OLD is delisted
    assert s["coins"]["BTC"]["L"] == {"-8": 200} and s["coins"]["BTC"]["oi_usd"] == 100_000_000
    f = S.write_snapshot(s, tmp_path)
    text = gzip.open(f, "rt").read()
    assert not any(a in text for a in addrs) and "0x" not in text


def test_only_the_window_and_the_registered_recorder_are_read(tmp_path):
    first, last = S.ms("2026-12-01T00:00:00Z"), S.ms("2027-06-01T00:00:00Z")
    for t, v in ((first - 60_000, S.REC_VERSION), (first + 60_000, S.REC_VERSION), (first + 120_000, "hlq-rec-0.9"),
                 (last, S.REC_VERSION)):
        S.write_snapshot({"v": v, "t": t - 30_000, "t_end": t, "coins": {"BTC": {"L": {}, "S": {}, "oi_usd": 1}}}, tmp_path)
    by, seen = S.load_snapshots(tmp_path, first, last)
    assert seen == {"snapshots": 1, "other_recorder": 1} and len(by["BTC"]) == 1


def _zip_month(rows):
    b = io.BytesIO()
    with zipfile.ZipFile(b, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("k.csv", "\n".join(f"{t * 1000},{o},{h},{lo},{c},0,0,0,0,0,0,0" for t, o, h, lo, c in rows))
    return b.getvalue()


def archive(paths, broken=None):
    files = {}
    for c, p in paths.items():
        by = {}
        for i in range(p.n):
            t = p.t0 + i * M
            by.setdefault(datetime.fromtimestamp(t / 1000, timezone.utc).strftime("%Y-%m"), []).append(
                (t, p.o[i], p.h[i], p.l[i], p.c[i]))
        for mo, rows in by.items():
            files[S.kline_url(S.binance_symbol(c), mo)] = _zip_month(rows)

    def fetch(u):
        if broken and broken in u:
            raise RuntimeError("timed out")
        return files.get(u)
    return fetch


def registered(tmp_path, code=None, coins=("BTC", "ETH")):
    reg = Registry(tmp_path / "registry.jsonl")
    st = S.SPEC["stages"]["forward"]
    a, b = (date.fromisoformat(x[:10]) for x in st["snapshots"])
    reg.register(Trial(id="HLQ-1", registered=datetime(2026, 11, 20, tzinfo=timezone.utc), title="t", hypothesis="h",
                       uses=(Use(S.UNIVERSE, a, b, "judge"),), tests=1, configurations=1, preregistration=S.DOC,
                       design={"code_sha256": code or S.code_hash(), "spec_sha256": S.spec_sha(), "stage": "forward",
                               "coins": list(coins)}))
    return reg


def test_the_forward_stage_is_judged_once_on_its_window_and_reads_no_minute_after_its_last_exit(tmp_path):
    t0, snaps, paths = market(coins=("BTC", "ETH"), days=184, every=24)
    last = S.ms("2027-06-01T00:00:00Z")
    for c, p in paths.items():  # a minute past the last exit that would wreck every trade if it were read
        i = (last + (2880 + 40) * M - p.t0) // M
        p.o[i:], p.h[i:], p.l[i:], p.c[i:] = 1e-6, 1e-6, 1e-6, 1e-6
    for m in range(184 * 48):
        t = t0 + m * 30 * M
        S.write_snapshot({"v": S.REC_VERSION, "t": t, "t_end": t + M,
                          "coins": {c: {k: v for k, v in snaps[c][m].items() if k not in ("t", "t_end")} for c in snaps}},
                         tmp_path / "snaps")
    reg = registered(tmp_path)
    body = S.run("forward", tmp_path / "data", tmp_path / "snaps", NOW, fetch=archive(paths), reg=reg, out_dir=tmp_path)
    assert body["verdict"] == "PASSED", body["result"].get("gates")
    assert body["coins_judged"] == ["BTC", "ETH"] and body["result"]["bar"] == 3.0 and reg.status_of("HLQ-1") == "PASSED"
    assert body["last_minute_read"].startswith("2027-06-03") and body["last_minute_held"] <= body["last_minute_read"]
    with pytest.raises(SystemExit, match="judged once"):
        S.run("forward", tmp_path / "data", tmp_path / "snaps", NOW, fetch=archive(paths), reg=reg, out_dir=tmp_path)


def test_nothing_is_judged_unregistered_early_with_other_code_or_on_a_partial_archive(tmp_path):
    t0, snaps, paths = market(coins=("BTC",), days=3)
    no = lambda u: pytest.fail("fetched")  # noqa: E731
    with pytest.raises(SystemExit, match="not registered"):
        S.run("forward", tmp_path / "d", tmp_path, NOW, fetch=no, reg=Registry(tmp_path / "r.jsonl"), out_dir=tmp_path / "o")
    (tmp_path / "x").mkdir()
    with pytest.raises(SystemExit, match="on or after"):
        S.run("forward", tmp_path / "d", tmp_path, NOW - timedelta(days=5), fetch=no, reg=registered(tmp_path / "x"),
              out_dir=tmp_path / "o")
    (tmp_path / "y").mkdir()
    with pytest.raises(SystemExit, match="differs"):
        S.run("forward", tmp_path / "d", tmp_path, NOW, fetch=no, reg=registered(tmp_path / "y", code="0" * 64),
              out_dir=tmp_path / "o")
    (tmp_path / "z").mkdir()
    S.write_snapshot({"v": S.REC_VERSION, "t": S.ms("2026-12-02T00:00:00Z"), "t_end": S.ms("2026-12-02T00:01:00Z"),
                      "coins": {"BTC": {"L": {}, "S": {}, "oi_usd": 1}}}, tmp_path / "z" / "s")
    with pytest.raises(SystemExit, match="partial"):
        S.run("forward", tmp_path / "d", tmp_path / "z" / "s", NOW, fetch=archive(paths, broken="2027-01"),
              reg=registered(tmp_path / "z"), out_dir=tmp_path / "z")


def test_registration_comes_before_the_window_and_includes_the_owners_coins(tmp_path, monkeypatch):
    monkeypatch.setattr(S, "registry", lambda: Registry(tmp_path / "r.jsonl"))
    doc = tmp_path / "doc.md"
    monkeypatch.setattr(S, "DOC", str(doc))
    monkeypatch.setattr(S, "ROOT", tmp_path)
    monkeypatch.setattr(S, "code_hash", lambda: "c" * 64)
    doc.write_text("nothing quoted")
    early = datetime(2026, 11, 20, tzinfo=timezone.utc)
    with pytest.raises(SystemExit, match="must quote"):
        S.preregister("forward", early, ["BTC", "ETH"])
    doc.write_text(f"{'c' * 64} {S.spec_sha()}")
    with pytest.raises(SystemExit, match="before its first snapshot"):
        S.preregister("forward", datetime(2026, 12, 1, 0, 5, tzinfo=timezone.utc), ["BTC", "ETH"])
    with pytest.raises(SystemExit, match="bitcoin and ether"):
        S.preregister("forward", early, ["SOL"])
    S.preregister("forward", early, ["BTC", "ETH", "SOL"])
    assert Registry.load(tmp_path / "r.jsonl").get("HLQ-1").design["coins"] == ["BTC", "ETH", "SOL"]
