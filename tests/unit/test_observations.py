"""Live learning reads the journal, reports honestly on small samples, and changes nothing."""

from __future__ import annotations

import json

from aitrader.learning.observations import MIN_N, observations, review


def journal(n_win: int, n_loss: int, edge="E-1", cost_now=0.05):
    decisions, trades = [], []
    for i in range(n_win + n_loss):
        did = f"d{i}"
        decisions.append({"id": did, "symbol": "EURUSD", "mode": "edges", "decision": "BUY", "payload": json.dumps({
            "regime": {"label": "TREND", "vol_state": "LOW", "familiar": i % 10 != 0},
            "evidence": {"edge_engine": {"chosen": {"edge_id": edge, "cost_now_R": cost_now,
                                                    "cost_assumed_R": 0.05}}},
            "context": {"t": 1_600_000_000 + i * 900, "frames": {"H4": {"er120": 0.5}}}})})
        r = 1.0 if i < n_win else -1.0
        trades.append({"decision_id": did, "r": r, "payload": json.dumps(
            {"mfe_r": 1.2, "mae_r": -0.4, "exit": {"reason": "TARGET" if r > 0 else "STOP"},
             "postmortem": {"cause": None if r > 0 else "NORMAL_VARIANCE"}})})
    decisions.append({"id": "skip", "symbol": "EURUSD", "mode": "edges", "decision": "NO_TRADE",
                      "payload": json.dumps({"no_trade_reason": "ABSTAIN: no promoted edges"})})
    return decisions, trades


def test_every_decision_becomes_one_observation_with_its_state_and_outcome():
    d, t = journal(3, 2)
    obs = observations(d, t, [{"decision_id": "skip", "payload": json.dumps(
        {"evaluations": [{"action": "T2:BUY", "outcome_r": -0.3, "objections": ["X"]}]})}])
    assert len(obs) == 6
    first = obs[0]
    assert first["traded"] and first["r"] == 1.0 and first["frames"] == {"H4": {"er120": 0.5}}
    assert first["edge_id"] == "E-1" and first["regime"] == "TREND"
    skip = obs[-1]
    assert not skip["traded"] and skip["reason"].startswith("ABSTAIN") and skip["shadow"][0]["r"] == -0.3


def test_small_samples_are_reported_as_insufficient_not_as_rates():
    d, t = journal(2, 1)
    rep = review(observations(d, t, []))
    assert rep["conditions"]["regime"]["TREND|BUY"] == {"n": 3, "sample": "insufficient"}


def test_decay_and_broken_cost_assumptions_are_flagged_but_nothing_is_changed():
    d, t = journal(5, MIN_N * 2 + 10, cost_now=0.2)
    before = json.dumps([d, t])
    rep = review(observations(d, t, []), tested={"E-1": {"mean": 0.3, "se": 0.05, "cost_r": 0.05}})
    e = rep["edges"]["E-1"]
    assert e["health"]["state"] in ("DEGRADED", "RETIRED")
    assert e["cost_assumption_holds"] is False and e["live_cost_R"] == 0.2
    assert rep["new_regimes"]["unfamiliar_decisions"] > 0 and rep["loss_causes"] == {"NORMAL_VARIANCE": MIN_N * 2 + 10}
    assert json.dumps([d, t]) == before  # the journal is read, never written
