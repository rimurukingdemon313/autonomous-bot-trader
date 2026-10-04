"""Forward evidence: shadow outcomes, partitions, statistics, lessons, edge status, routing, config.

Every market here is built by hand so the right answer is known before the code runs."""

from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from types import SimpleNamespace

import numpy as np
import pytest

from aitrader.data.bars import BarSeries
from aitrader.decision.edge_status import classify, execution_route
from aitrader.learning import metrics, taxonomy
from aitrader.learning.forward import EXPIRE_S, ForwardLedger, partition, walk
from aitrader.memory.db import Database

T0 = 1_700_000_000 // 3600 * 3600  # a Tuesday


def bars(rows, tf="M5", t0=T0, spread=0.0002):
    """rows: (open, high, low, close) in MID prices, one per bar starting at t0."""
    per = {"M1": 60, "M5": 300, "M15": 900, "H1": 3600}[tf]
    a = np.asarray(rows, float)
    h = spread / 2
    n = len(a)
    return BarSeries.from_columns("EURUSD", tf, "t", open_time=t0 + per * np.arange(n),
                                  bid_open=a[:, 0] - h, bid_high=a[:, 1] - h, bid_low=a[:, 2] - h, bid_close=a[:, 3] - h,
                                  ask_open=a[:, 0] + h, ask_high=a[:, 1] + h, ask_low=a[:, 2] + h, ask_close=a[:, 3] + h,
                                  ticks=np.full(n, 5), spread_mean=np.full(n, spread), spread_max=np.full(n, spread))


def prop(side=1, entry=1.1001, stop=1.0991, target=1.1021, hold_s=3600, t=T0, **kw):
    return {"decision_id": kw.pop("decision_id", "d1"), "symbol": "EURUSD", "t": t, "side": side, "entry": entry,
            "stop": stop, "target": target, "hold_s": hold_s, "risk_px": abs(entry - stop), "spread": 0.0002,
            "pip": 0.0001, "slippage_px": 0.00001, "commission_px": 0.00007, "partition": partition(t),
            "reward_risk": abs(target - entry) / abs(entry - stop), **kw}


# ── the walk ────────────────────────────────────────────────────────────

def test_a_target_hit_gives_exact_gross_cost_and_net():
    b = bars([(1.1000, 1.1005, 1.0998, 1.1004), (1.1004, 1.1030, 1.1003, 1.1025)] + [(1.1025, 1.1026, 1.1024, 1.1025)] * 12)
    o = walk(prop(), b, T0 + 86400)
    assert o["reason"] == "TARGET" and o["exit"] == pytest.approx(1.1021)
    fill = 1.1001 + 0.00001
    assert o["net_r"] == pytest.approx(((1.1021 - fill) - 0.00007) / 0.0010, abs=1e-6)
    assert o["gross_r"] - o["cost_r"] == pytest.approx(o["net_r"], abs=1e-6)  # gross - costs = net, exactly
    assert o["cost_r"] == pytest.approx((0.0002 + 0.00001 + 0 + 0.00007) / 0.0010, abs=1e-6)  # no slip on a target


def test_stop_comes_first_when_one_bar_touches_both():
    b = bars([(1.1000, 1.1030, 1.0980, 1.1000)] + [(1.1, 1.1001, 1.0999, 1.1)] * 12)
    o = walk(prop(), b, T0 + 86400)
    assert o["reason"] == "STOP" and o["net_r"] < -1.0


def test_a_gap_through_the_stop_fills_at_the_open_not_the_stop():
    b = bars([(1.0970, 1.0975, 1.0965, 1.0970)] + [(1.097, 1.0971, 1.0969, 1.097)] * 12)
    o = walk(prop(), b, T0 + 86400)
    assert o["reason"] == "STOP" and o["exit"] == pytest.approx(1.0970 - 0.0001 - 0.00001)  # bid open - slip


def test_a_time_exit_closes_at_the_bar_close():
    b = bars([(1.1000, 1.1004, 1.0998, 1.1002)] * 24)
    o = walk(prop(hold_s=1800), b, T0 + 86400)
    assert o["reason"] == "TIME" and o["exit_time"] == T0 + 1800


def test_no_bar_before_the_decision_or_not_yet_closed_is_used():
    # A bar that opened before the decision would have hit the target: it must be ignored.
    early = bars([(1.1000, 1.1100, 1.0999, 1.1050)] + [(1.1001, 1.1004, 1.0998, 1.1002)] * 24, t0=T0 - 300)
    o = walk(prop(), early, T0 + 3 * 86400)
    assert o["reason"] == "TIME" and o["mfe_r"] < 1.0  # the early bar's high never counted
    b = bars([(1.1000, 1.1030, 1.0999, 1.1025)] + [(1.1025, 1.1026, 1.1024, 1.1025)] * 12)
    assert walk(prop(), b, T0 + 299) is None  # the bar closes at T0+300: not known before
    # the exit is known at T0+300, but the post-exit window (for the post-mortem) completes at T0+3600
    assert walk(prop(), b, T0 + 300) is None
    assert walk(prop(), b, T0 + 3900)["reason"] == "TARGET"


def test_a_stop_that_was_too_tight_is_told_from_a_wrong_direction():
    path = [(1.1000, 1.1001, 1.0985, 1.0990)] + [(1.0990, 1.1030, 1.0989, 1.1028)] + [(1.1028, 1.1029, 1.1027, 1.1028)] * 12
    o = walk(prop(), bars(path), T0 + 86400)
    assert o["reason"] == "STOP" and o["target_after_exit"] is True
    assert "STOP_TOO_TIGHT" in taxonomy.tags({**prop(), "outcome": o})
    flat = [(1.1000, 1.1001, 1.0985, 1.0990)] + [(1.0990, 1.0992, 1.0970, 1.0975)] * 12
    o2 = walk(prop(), bars(flat), T0 + 86400)
    assert "WRONG_DIRECTION" in taxonomy.tags({**prop(), "outcome": o2})


def test_the_walk_is_pure():
    b = bars([(1.1000, 1.1030, 1.0999, 1.1025)] + [(1.1, 1.1001, 1.0999, 1.1)] * 12)
    assert walk(prop(), b, T0 + 86400) == walk(prop(), b, T0 + 86400)


# ── partitions ──────────────────────────────────────────────────────────

def test_partition_is_fixed_by_decision_time_in_week_blocks():
    weeks = {}
    for d in range(0, 7 * 30):
        t = T0 + d * 86400
        weeks.setdefault(datetime.fromtimestamp(t, timezone.utc).isocalendar()[1], set()).add(partition(t))
    assert all(len(v) == 1 for v in weeks.values())  # a whole week on one side
    share = sum(v == {"EVALUATION"} for v in weeks.values()) / len(weeks)
    assert 0.25 <= share <= 0.4


# ── the ledger: record, resolve, restart, immutability ──────────────────

class Feed:
    def __init__(self, series):
        self.series = series

    def bars_tf(self, symbol, tf, as_of, n):
        b = self.series.get(tf)
        return None if b is None else b.as_of(as_of)


def test_a_proposal_is_recorded_once_resolved_after_a_restart_and_never_edited(tmp_path):
    db = Database(tmp_path / "a.db")
    clock = lambda: T0  # noqa: E731
    led = ForwardLedger(db, clock)
    assert led.record(prop()) and not led.record(prop())  # the same decision twice: once
    b = bars([(1.1000, 1.1030, 1.0999, 1.1025)] + [(1.1025, 1.1026, 1.1024, 1.1025)] * 12)
    assert led.resolve(Feed({"M5": b}), T0 + 100) == []  # nothing closed yet
    led2 = ForwardLedger(Database(tmp_path / "a.db"), clock)  # a restart: pending survives in the journal
    out = led2.resolve(Feed({"M1": None, "M5": b}), T0 + 86400)
    assert len(out) == 1 and out[0]["reason"] == "TARGET" and out[0]["resolution_timeframe"] == "M5"
    assert led2.pending() == []
    with pytest.raises(sqlite3.IntegrityError):  # history cannot be rewritten: the trigger refuses
        db._conn.execute("UPDATE forward_outcomes SET partition='LEARNING'")
    assert db.verify_chain("forward_proposals")[0] and db.verify_chain("forward_outcomes")[0]


def test_no_data_for_thirty_days_is_unresolved_with_no_r_invented(tmp_path):
    led = ForwardLedger(Database(":memory:"), lambda: T0)
    led.record(prop())
    out = led.resolve(Feed({}), T0 + EXPIRE_S + 1)
    assert out[0]["status"] == "UNRESOLVED" and out[0]["net_r"] is None
    assert metrics.stats(led.rows())["n"] == 0 and metrics.stats(led.rows())["no_data"] == 1


def test_an_outcome_is_invisible_before_it_resolved(tmp_path):
    led = ForwardLedger(Database(":memory:"), lambda: T0)
    led.record(prop())
    b = bars([(1.1000, 1.1030, 1.0999, 1.1025)] + [(1.1025, 1.1026, 1.1024, 1.1025)] * 12)
    o = led.resolve(Feed({"M5": b}), T0 + 86400)[0]
    assert led.rows(as_of=o["resolved_at"] - 1)[0]["outcome"] is None
    assert led.rows(as_of=o["resolved_at"])[0]["outcome"]["reason"] == "TARGET"


# ── statistics ──────────────────────────────────────────────────────────

def row(net, i=0, sym="EURUSD", part="EVALUATION", cost=0.1, reason=None, t=None, **kw):
    t = t if t is not None else T0 + i * 7 * 86400
    return {"decision_id": f"d{i}", "symbol": sym, "t": t, "partition": part, "signal_class": "LLM_TRADER",
            "outcome": {"net_r": net, "gross_r": net + cost, "cost_r": cost, "resolved_at": t + 3600,
                        "reason": reason or ("TARGET" if net > 0 else "STOP"), "mfe_r": max(net, 0.1), "mae_r": -0.5},
            **kw}


def test_statistics_by_hand_and_small_samples_are_labelled():
    rs = [row(x, i) for i, x in enumerate([1.0, -1.0, -1.0, 2.0])]
    s = metrics.stats(rs)
    assert s["n"] == 4 and s["sample"] == "insufficient" and s["win_rate"] == 0.5
    assert s["profit_factor"] == pytest.approx(1.5) and s["max_drawdown_r"] == pytest.approx(2.0)
    assert s["max_consecutive_losses"] == 2 and s["net_r_total"] == pytest.approx(1.0)
    assert s["gross_r_total"] - s["cost_r_total"] == pytest.approx(s["net_r_total"])
    assert s["net_avg_costs_x2"] == pytest.approx(0.25 - 0.1)
    assert metrics.stats([row(1.0), row(1.0, 1)])["sample"] == "insufficient"  # 100% of two says nothing
    assert metrics.stats([])["sample"] == "none"


def test_eligibility_is_never_validation_and_needs_every_criterion():
    rng = np.random.default_rng(3)
    syms = ["EURUSD", "GBPUSD", "USDJPY"]
    rows = [row(float(x), i, sym=syms[i % 3], t=T0 + i * 3 * 86400) for i, x in enumerate(rng.normal(0.4, 1.0, 150))]
    ok = metrics.eligibility(rows, baseline_mean=-0.05)
    assert ok["status"] == "ELIGIBLE_FOR_REVIEW" and "VALIDATED" not in ok["status"]
    assert metrics.eligibility(rows, baseline_mean=None)["status"] != "ELIGIBLE_FOR_REVIEW"  # no baseline: no pass
    one = [dict(r, symbol="EURUSD") for r in rows]
    assert metrics.eligibility(one, -0.05)["criteria"]["symbol_share"]["pass"] is False
    learning_only = [dict(r, partition="LEARNING") for r in rows]
    assert metrics.eligibility(learning_only, -0.05)["status"] == "INSUFFICIENT"  # judged on EVALUATION only


# ── lessons: learning only, confirmed later, never from one trade ───────

def wrong_dir(i, part, t):
    return {"decision_id": f"w{i}", "symbol": "EURUSD", "t": t, "partition": part, "signal_class": "LLM_TRADER",
            "regime": "TREND", "model": "m1", "method": "breakout", "reward_risk": 2.0, "stop_atr": 1.0,
            "outcome": {"net_r": -1.05, "gross_r": -0.95, "cost_r": 0.1, "resolved_at": t + 3600, "reason": "STOP",
                        "mfe_r": 0.05, "mae_r": -1.0, "post_exit_best_r": 0.1, "target_after_exit": False}}


def test_a_lesson_needs_a_sample_and_out_of_sample_confirmation():
    learn = [wrong_dir(i, "LEARNING", T0 + i * 3600) for i in range(40)]
    assert taxonomy.evaluate(learn[:1], {}, T0 + 10 ** 7) == []  # one loss creates nothing
    # 29 identical losses, every one tagged: still below the 30-outcome sample, so still nothing
    assert taxonomy.evaluate(learn[:29], {}, T0 + 10 ** 7) == []
    created = taxonomy.evaluate(learn, {}, T0 + 10 ** 6)
    cands = {c["code"] for c in created if c["scope_kind"] == "signal_class"}
    assert {"WRONG_DIRECTION", "FALSE_BREAKOUT"} <= cands and all(c["status"] == "CANDIDATE" for c in created)
    prev = {c["lesson_id"]: c for c in created}
    # EVALUATION outcomes that resolved BEFORE the candidate existed cannot confirm it
    early_eval = [wrong_dir(100 + i, "EVALUATION", T0 + i * 60) for i in range(40)]
    assert not [c for c in taxonomy.evaluate(learn + early_eval, prev, T0 + 10 ** 6 + 1) if c["status"] == "ACTIVE"]
    late_eval = [wrong_dir(200 + i, "EVALUATION", T0 + 10 ** 6 + 10 + i * 60) for i in range(40)]
    act = [c for c in taxonomy.evaluate(learn + late_eval, prev, T0 + 10 ** 7) if c["status"] == "ACTIVE"]
    assert {c["code"] for c in act if c["scope_kind"] == "signal_class"} >= {"WRONG_DIRECTION"}


def test_evaluation_outcomes_never_create_a_lesson():
    ev = [wrong_dir(i, "EVALUATION", T0 + i * 3600) for i in range(60)]
    assert taxonomy.evaluate(ev, {}, T0 + 10 ** 7) == []


def test_overconfidence_is_measured_against_what_happened():
    rows = []
    for i in range(60):
        hit = i % 4 == 0  # 25% reach the target...
        rows.append({**wrong_dir(i, "LEARNING", T0 + i * 3600), "confidence": 0.8,  # ...while the model says 80%
                     "outcome": {"net_r": 2.0 if hit else -1.0, "gross_r": 2.1 if hit else -0.9, "cost_r": 0.1,
                                 "resolved_at": T0 + i * 3600 + 60, "reason": "TARGET" if hit else "STOP",
                                 "mfe_r": 2.0 if hit else 0.5, "mae_r": -0.3}})
    codes = {(c["code"], c["scope_kind"]) for c in taxonomy.evaluate(rows, {}, T0 + 10 ** 7)}
    assert ("AI_OVERCONFIDENCE", "model") in codes and ("AI_UNDERCONFIDENCE", "model") not in codes


def test_lessons_are_append_only_versions():
    db = Database(":memory:")
    book = taxonomy.LessonBook(db)
    learn = [wrong_dir(i, "LEARNING", T0 + i * 3600) for i in range(40)]
    first = book.update(learn, T0 + 10 ** 6)
    assert first and book.update(learn, T0 + 10 ** 6) == []  # nothing new: nothing written
    assert db.verify_chain("forward_lessons")[0]
    with pytest.raises(sqlite3.IntegrityError):
        db._conn.execute("DELETE FROM forward_lessons")


# ── edge status and routing: an AI opinion is never a validated edge ────

def dec(side="BUY", support=None):
    return SimpleNamespace(decision=side, supporting_evidence=support or [])


def test_a_confident_model_is_still_experimental():
    d = dec()
    d.ai = {"view": {"confidence": 0.99}}
    for mode in ("evidence", "llm_trader", "trading_room", "experimental_ai"):
        assert classify(d, mode) == "EXPERIMENTAL"
    assert classify(dec("NO_TRADE"), "llm_trader") == "NONE"


def test_only_a_promoted_healthy_validated_edge_is_validated():
    e = lambda status, health="HEALTHY": SimpleNamespace(edge_id="E1", status=status, health=health)  # noqa: E731
    d = dec(support=[{"edge_id": "E1"}])
    assert classify(d, "edges", [e("VALIDATED")]) == "VALIDATED"
    assert classify(d, "edges", [e("VALIDATED", "DEGRADED")]) == "PROMISING"
    assert classify(d, "edges", [e("PROMISING")]) == "PROMISING"
    assert classify(d, "edges", []) == "EXPERIMENTAL"
    assert classify(dec(support=[{"edge_id": "E2"}]), "edges", [e("VALIDATED")]) == "EXPERIMENTAL"


@pytest.mark.parametrize("status,mode,flag,route", [
    ("EXPERIMENTAL", "PAPER", False, "EXECUTE"),
    ("EXPERIMENTAL", "DEMO", False, "SHADOW"),
    ("PROMISING", "DEMO", False, "SHADOW"),
    ("EXPERIMENTAL", "DEMO", True, "EXECUTE"),
    ("VALIDATED", "DEMO", False, "EXECUTE"),
    ("VALIDATED", "LIVE", True, "SHADOW"),  # a mode this build does not know never executes
    ("EXPERIMENTAL", "anything", True, "SHADOW"),
    ("NONE", "PAPER", True, "NONE"),
])
def test_routing(status, mode, flag, route):
    assert execution_route(status, mode, flag) == route
