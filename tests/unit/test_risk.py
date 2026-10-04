"""The risk engine is the final authority, and the AI cannot move it."""

from __future__ import annotations

import itertools
from dataclasses import replace
from types import SimpleNamespace

import numpy as np
import pytest

from aitrader.risk.engine import (
    HARD_MAX_RISK_PCT, AccountState, FundedRules, InstrumentSpec, Quote, RiskEngine, RiskLimits,
    streak_multiplier,
)

NOW = 1_600_000_000
SPEC = InstrumentSpec("EURUSD", 100_000, 0.01, 0.01, 50.0, 1.0)
Q = Quote("EURUSD", 1.1000, 1.1001, NOW)


def decision(side="BUY", stop=1.0980, target=1.1040, conf=0.6, edge=0.1, did="d1", sym="EURUSD"):
    return SimpleNamespace(id=did, decision=side, instrument=sym, stop_loss=stop, take_profit=target,
                           confidence=conf, expected_R=edge, lower_R=edge / 2)


def account(**kw):
    base = dict(equity=20_000.0, balance=20_000.0, day_start_equity=20_000.0, peak_equity=20_000.0,
                start_balance=20_000.0)
    base.update(kw)
    return AccountState(**base)


def test_a_clean_proposal_is_sized_from_equity_and_stop_only():
    v = RiskEngine().evaluate(decision(), account(), SPEC, Q, NOW)
    assert v.approved, v.reasons
    # 0.5% of 20,000 = 100; stop distance 0.0021 -> 210 per lot -> 0.47 lots
    assert v.qty == pytest.approx(0.47)
    assert v.risk_amount <= 100.0 + 1e-9


def test_ai_confidence_and_claimed_edge_cannot_change_the_size():
    e = RiskEngine()
    sizes = {e.evaluate(decision(conf=c, edge=x), account(), SPEC, Q, NOW).qty
             for c, x in itertools.product((0.51, 0.99, 1.0), (0.01, 5.0, 100.0))}
    assert len(sizes) == 1


@pytest.mark.parametrize("state,reason", [
    (dict(kill_switch=True), "kill_switch"),
    (dict(kill_switch=None), "kill_switch"),
    (dict(paused=True), "paused"),
    (dict(halted=True), "halted"),
    (dict(equity=None), "equity"),
])
def test_switches_and_unknown_state_fail_closed(state, reason):
    v = RiskEngine().evaluate(decision(), account(**state), SPEC, Q, NOW)
    assert not v.approved and any(r.startswith(reason) for r in v.reasons)


def test_missing_or_stale_quote_and_missing_spec_reject():
    e = RiskEngine()
    assert not e.evaluate(decision(), account(), SPEC, None, NOW).approved
    assert not e.evaluate(decision(), account(), SPEC, replace(Q, time=NOW - 600), NOW).approved
    assert not e.evaluate(decision(), account(), None, Q, NOW).approved


def test_no_trade_decisions_are_never_approved():
    assert not RiskEngine().evaluate(decision(side="NO_TRADE"), account(), SPEC, Q, NOW).approved


@pytest.mark.parametrize("kw,name", [
    (dict(stop=1.1010), "stop_side"),
    (dict(target=1.0990), "target_side"),
    (dict(target=1.1010), "reward_risk"),
    (dict(stop=1.09999), "stop_distance"),  # right side, but within ~1 spread
])
def test_invalid_sl_tp_and_poor_rr_are_rejected(kw, name):
    v = RiskEngine().evaluate(decision(**kw), account(), SPEC, Q, NOW)
    assert not v.approved and any(r.startswith(name) for r in v.reasons)


def test_spread_too_large_for_the_stop_rejects():
    wide = Quote("EURUSD", 1.1000, 1.1008, NOW)
    v = RiskEngine().evaluate(decision(stop=1.0990, target=1.1060), account(), SPEC, wide, NOW)
    assert not v.approved and any("spread" in r or "stop_distance" in r for r in v.reasons)


def test_daily_loss_and_drawdown_limits():
    e = RiskEngine()
    assert not e.evaluate(decision(), account(equity=19_500, day_start_equity=20_000), SPEC, Q, NOW).approved
    v = e.evaluate(decision(), account(equity=18_000, day_start_equity=18_000, peak_equity=20_000), SPEC, Q, NOW)
    assert not v.approved and v.halt


def test_duplicates_same_symbol_and_exposure_limits():
    e = RiskEngine()
    assert not e.evaluate(decision(did="x"), account(), SPEC, Q, NOW, executed_ids={"x"}).approved
    held = [{"symbol": "EURUSD", "side": "BUY", "notional": 1000}]
    assert not e.evaluate(decision(), account(open_positions=held), SPEC, Q, NOW).approved
    two_usd = [{"symbol": "GBPUSD", "notional": 1}, {"symbol": "AUDUSD", "notional": 1}]
    assert not e.evaluate(decision(), account(open_positions=two_usd), SPEC, Q, NOW).approved
    three = [{"symbol": s, "notional": 1} for s in ("EURJPY", "GBPCHF", "AUDNZD")]
    assert not e.evaluate(decision(), account(open_positions=three), SPEC, Q, NOW).approved


def test_a_position_too_small_to_respect_risk_is_rejected_not_rounded_up():
    v = RiskEngine().evaluate(decision(), account(equity=100.0, day_start_equity=100.0, peak_equity=100.0), SPEC, Q, NOW)
    assert not v.approved and any(r.startswith("min_lot") for r in v.reasons)


def test_configured_risk_cannot_exceed_the_hard_ceiling():
    e = RiskEngine(RiskLimits(risk_per_trade_pct=25.0))
    v = e.evaluate(decision(), account(), SPEC, Q, NOW)
    assert v.approved and v.risk_pct <= HARD_MAX_RISK_PCT + 1e-9


def test_leverage_limit():
    e = RiskEngine(RiskLimits(max_leverage=1.0))
    # an 8-pip stop from the ask: within the cost ceiling (24%), and a size that needs ~7x leverage
    v = e.evaluate(decision(stop=1.1001 - 0.0008, target=1.1030), account(), SPEC, Q, NOW)
    assert not v.approved and any(r.startswith("leverage") for r in v.reasons)


def test_a_losing_streak_actually_reduces_risk_and_a_win_resets_it():
    assert streak_multiplier([-1.0, -1.0], 3, 0.25) == 1.0
    assert streak_multiplier([-1.0] * 3, 3, 0.25) == 0.5
    assert streak_multiplier([-1.0] * 6, 3, 0.25) == 0.25
    assert streak_multiplier([-1.0] * 30, 3, 0.25) == 0.25  # floor, never zero
    assert streak_multiplier([-1.0] * 3 + [1.5], 3, 0.25) == 1.0
    e = RiskEngine()
    fresh = e.evaluate(decision(), account(closed_r=[]), SPEC, Q, NOW)
    after3 = e.evaluate(decision(), account(closed_r=[-1.0] * 3), SPEC, Q, NOW)
    assert fresh.approved and after3.approved
    assert after3.qty < fresh.qty


def test_risk_only_ever_decreases_after_losses():
    """No martingale, no revenge: along any sequence, a loss never raises risk."""
    rng = np.random.default_rng(0)
    e = RiskEngine()
    for _ in range(200):
        seq = list(rng.choice([-1.0, 1.5], size=rng.integers(1, 15)))
        base = e.evaluate(decision(), account(closed_r=seq), SPEC, Q, NOW)
        after_loss = e.evaluate(decision(), account(closed_r=seq + [-1.0]), SPEC, Q, NOW)
        if base.approved and after_loss.approved:
            assert after_loss.qty <= base.qty
        assert streak_multiplier(seq, 3, 0.25) <= 1.0
    fresh = e.evaluate(decision(), account(closed_r=[]), SPEC, Q, NOW).qty
    for n in range(1, 12):
        assert e.evaluate(decision(), account(closed_r=[-1.0] * n), SPEC, Q, NOW).qty <= fresh


def test_funded_rules_are_the_stricter_limit():
    f = FundedRules("prop", daily_loss_pct=1.0, max_risk_per_trade_pct=0.25, no_weekend_holding=True)
    e = RiskEngine(RiskLimits(funded=f))
    v = e.evaluate(decision(), account(), SPEC, Q, NOW)
    assert v.approved and v.risk_pct <= 0.25 + 1e-9
    assert not e.evaluate(decision(), account(equity=19_790), SPEC, Q, NOW).approved
    friday_evening = 1_600_452_000  # Fri 2020-09-18 18:00 UTC
    assert not e.evaluate(decision(), account(), SPEC, replace(Q, time=friday_evening), friday_evening).approved


def test_every_rejection_names_its_cause():
    v = RiskEngine().evaluate(decision(stop=1.2), account(kill_switch=True), SPEC, Q, NOW)
    assert v.reasons and all(":" in r for r in v.reasons)


@pytest.mark.parametrize("state", [
    dict(kill_switch=True), dict(paused=True), dict(halted=True), dict(equity=None),
    dict(equity=19_500.0), dict(equity=18_000.0, day_start_equity=18_000.0),
    dict(open_positions=[{"symbol": "EURUSD", "notional": 1.0}]),
    dict(open_positions=[{"symbol": s, "notional": 1.0} for s in ("GBPUSD", "AUDUSD", "USDJPY")]),
    dict(),
])
def test_the_account_gates_are_the_same_checks_evaluate_applies(state):
    """account_gates() is what the orchestrator asks before spending a model call. It must never
    refuse what evaluate() would allow, and every account-level refusal evaluate() makes, it makes."""
    e = RiskEngine(RiskLimits(funded=FundedRules("test", daily_loss_pct=1.5)))
    a = account(**{"kill_switch": False, **state})
    gates = {c.name: c for c in e.account_gates(a, "EURUSD", NOW)}
    v = e.evaluate(decision(), a, SPEC, Q, NOW)
    by_name = {c.name: c for c in v.checks}
    for name, c in gates.items():
        if name in by_name:
            assert by_name[name] == c  # identical verdict and detail
    failed = [c for c in gates.values() if not c.passed]
    assert bool(failed) == (not v.approved)  # this proposal is otherwise clean


def test_the_whole_round_trip_cost_counts_against_the_stop_not_the_spread_alone():
    """risk-1.1.0: a 4-pip stop with a 1-pip spread passes the spread check (25%) but pays
    1.0 + 0.7 + 0.2 = 1.9 pips round trip, 47.5% of the risk: refused, never sized."""
    tight = decision(stop=1.0997, target=1.1011)  # 4 pips below the ask
    v = RiskEngine().evaluate(tight, account(), SPEC, Q, NOW)
    by = {c.name: c for c in v.checks}
    assert by["spread"].passed and not by["cost_to_risk"].passed and not v.approved
    ok = RiskEngine().evaluate(decision(), account(), SPEC, Q, NOW)  # a 21-pip stop: ~4.8%
    assert {c.name: c for c in ok.checks}["cost_to_risk"].passed and ok.approved


def test_the_cost_ceiling_can_only_be_tightened_by_configuration():
    from aitrader.service.config import ServiceConfig
    assert ServiceConfig.from_env({"RISK_MAX_COST_TO_RISK": "0.9"}).risk.max_cost_to_risk == 0.25
    assert ServiceConfig.from_env({"RISK_MAX_COST_TO_RISK": "0.1"}).risk.max_cost_to_risk == 0.1
