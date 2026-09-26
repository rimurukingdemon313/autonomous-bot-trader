"""The whole system, end to end, on constructed data.

The most important test here: change the market AFTER time T and check that
every decision made up to T is identical. If anything in the pipeline —
features, regime, memory, agents, synthesis, risk, execution, learning —
could see the future, this fails.
"""

from __future__ import annotations

from datetime import datetime, timezone

import numpy as np
import pytest

from aitrader.backtest.runner import BacktestConfig, epoch, run
from aitrader.data.bars import BarSeries
from aitrader.decision.synthesis import SynthesisConfig
from aitrader.orchestrator.tracker import OutcomeTracker
from aitrader.research.labels import BUY, SELL, CostModel, compute_labels


def market(symbol, start, n, seed, base):
    rng = np.random.default_rng(seed)
    # regime-switching drift so that trends, ranges and breakouts all occur
    drift = np.repeat(rng.choice([-1, 0, 1], size=n // 200 + 1) * 0.00012, 200)[:n]
    steps = drift + rng.normal(0, 0.0009, n)
    mid = base * np.exp(np.cumsum(steps))
    o = np.concatenate(([mid[0]], mid[:-1]))
    wick = np.abs(rng.normal(0, 0.0005, n)) * base
    hi, lo = np.maximum(o, mid) + wick, np.minimum(o, mid) - wick
    spread = base * (0.00008 + 0.00004 * rng.random(n))
    t = start + 3600 * np.arange(n)
    # remove weekend hours (Fri 21:00 - Sun 21:00) like a real FX calendar
    dow = ((t // 86400) + 4) % 7  # 0 = Monday
    hour = (t % 86400) // 3600
    keep = ~(((dow == 4) & (hour >= 21)) | (dow == 5) | ((dow == 6) & (hour < 21)))
    half = spread / 2
    return BarSeries.from_columns(
        symbol, "H1", "synthetic", open_time=t[keep],
        bid_open=(o - half)[keep], bid_high=(hi - half)[keep], bid_low=(lo - half)[keep], bid_close=(mid - half)[keep],
        ask_open=(o + half)[keep], ask_high=(hi + half)[keep], ask_low=(lo + half)[keep], ask_close=(mid + half)[keep],
        ticks=rng.integers(100, 900, n)[keep], spread_mean=spread[keep], spread_max=(spread * 2)[keep])


START = epoch(2009, 1, 5)


@pytest.fixture(scope="module")
def data():
    n = 24 * 7 * 60  # ~60 weeks of hours
    return {"EURUSD": market("EURUSD", START, n, 1, 1.30), "GBPUSD": market("GBPUSD", START, n, 2, 1.55)}


def cfg(name="t", **kw):
    base = dict(name=name, symbols=["EURUSD", "GBPUSD"], warmup_start=START, start=START + 30 * 7 * 86400,
                end=START + 58 * 7 * 86400, every=4)
    base.update(kw)
    return BacktestConfig(**base)


def test_tracker_matches_labels_exactly(data):
    s = data["EURUSD"]
    rows = np.arange(300, 3000, 97)
    lab = compute_labels(s, 0.0001, rows=rows)
    from aitrader.research.labels import atr24
    atr = atr24(s)
    tracked = []
    tr = OutcomeTracker(lambda _s: 0.0001, CostModel(), on_resolved=tracked.append)
    for i in range(len(s)):
        bar = {"open_time": int(s.open_time[i]), "close_time": int(s.available_at[i]),
               **{f: float(getattr(s, f)[i]) for f in ("bid_open", "bid_high", "bid_low", "bid_close",
                                                      "ask_open", "ask_high", "ask_low", "ask_close")}}
        tr.on_bar("EURUSD", bar)
        if i in set(rows.tolist()):
            tr.track(str(i), "EURUSD", int(s.available_at[i]), float(atr[i]), np.zeros(3), {})
    got = {int(t.key): {l.action: l.r for l in t.legs} for t in tracked}
    for j, row in enumerate(rows):
        if row not in got:
            continue
        for key, side in [("T1", BUY), ("T1", SELL), ("T2", BUY), ("T2", SELL)]:
            want = lab.outcomes[(key, side)].r[j]
            if np.isfinite(want):
                assert got[row][f"{key}:{'BUY' if side > 0 else 'SELL'}"] == pytest.approx(want, rel=1e-9, abs=1e-12)


@pytest.fixture(scope="module")
def full_run(data):
    return run(cfg("full"), data)


def test_backtest_runs_end_to_end_and_records_everything(full_run):
    r = full_run
    assert r["counts"]["decisions"] > 100
    assert r["chains_ok"]
    assert r["final_patterns"] > r["seeded_patterns"]  # memory grew from experience
    assert r["counts"]["no_trade"] > 0
    m = r["metrics"]["overall"]
    if m["n"]:
        assert "avg_R" in m and "sample" in m


def test_the_same_inputs_give_the_same_result(data, full_run):
    again = run(cfg("full"), data)
    assert again["counts"] == full_run["counts"]
    assert [t["r"] for t in again["trades"]] == [t["r"] for t in full_run["trades"]]


def test_changing_the_future_does_not_change_the_past(data, full_run):
    cut = START + 44 * 7 * 86400
    altered = {}
    for sym, s in data.items():
        k = int(np.searchsorted(s.open_time, cut))
        f = {x: np.array(getattr(s, x)) for x in ("open_time", "bid_open", "bid_high", "bid_low", "bid_close",
                                                    "ask_open", "ask_high", "ask_low", "ask_close", "ticks",
                                                    "spread_mean", "spread_max")}
        shock = np.linspace(1.0, 1.25, len(s) - k)  # a completely different future
        for x in ("bid_open", "bid_high", "bid_low", "bid_close", "ask_open", "ask_high", "ask_low", "ask_close"):
            f[x][k:] = f[x][k:] * shock
        altered[sym] = BarSeries.from_columns(sym, "H1", "synthetic", **f)
    other = run(cfg("full"), altered)
    # Trades that CLOSED before the cut, and every decision count up to it, must match.
    before = [t for t in full_run["trades"] if t["closed"] < cut]
    before_other = [t for t in other["trades"] if t["closed"] < cut]
    assert len(before) >= 20, "coverage guard: a leakage test over no trades proves nothing"
    assert [(t["symbol"], t["opened"], t["r"]) for t in before] == \
           [(t["symbol"], t["opened"], t["r"]) for t in before_other]


def test_ablation_variants_run_through_the_same_risk_engine(data):
    rules = run(cfg("rules", synthesis=SynthesisConfig(mode="rules")), data)
    rnd = run(cfg("random", synthesis=SynthesisConfig(mode="random", random_trade_prob=0.05, seed=3)), data)
    for r in (rules, rnd):
        assert r["chains_ok"]
        # every executed trade went through a risk verdict
        assert r["counts"]["executed"] <= r["counts"]["trade_decisions"]


def test_a_full_journal_lets_a_restart_rebuild_the_same_experience(data, tmp_path):
    """What the service journals is enough to rebuild every resolved outcome, skipped candidates included."""
    import json

    from aitrader.learning.experience import Evaluation
    from aitrader.memory.db import Database

    res = run(cfg("journal", journal="full", db_path=str(tmp_path / "j.db")), data)
    db = Database(tmp_path / "j.db")
    shadows = sum(len(json.loads(r["payload"])["evaluations"]) for r in db.query("SELECT payload FROM evaluations"))
    trades = len(db.query("SELECT 1 FROM episodes WHERE kind='TRADE'"))
    assert shadows > 0
    rebuilt = [Evaluation(**{**e, "objections": tuple(e["objections"])})
               for r in db.query("SELECT payload FROM evaluations") for e in json.loads(r["payload"])["evaluations"]]
    assert all(not e.traded for e in rebuilt)
    assert shadows + trades == res["learning"]["resolved"] + res["learning"]["pending"]
