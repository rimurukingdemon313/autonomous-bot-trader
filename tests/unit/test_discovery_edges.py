"""The edge registry says what the evidence says: statuses from verdicts, gaps as None, a fixed lifecycle."""

import json
from pathlib import Path

import pytest

from aitrader.research.discovery.edges import (STATUSES, TransitionError, build, from_confirmatory,
                                               from_walk_forward, transition)

ROOT = Path(__file__).resolve().parents[2]


def _judged(hid, side, mean, t, validated=False):
    return {"id": hid, "side": side, "condition": "r120=low&er120=high", "exit": "D4", "kind": "opportunity",
            "battery": {"failed": [] if validated else ["significance"],
                        "checks": {"significance": {"mean_R": mean, "t": t, "threshold": 3.1},
                                   "min_trades": {"n": 300}, "costs_stress": {"mean_R": mean - 0.05},
                                   "years": {"by_year": {"2014": 0.3, "2015": -0.1}}}}}


def test_only_a_validated_verdict_makes_a_validated_edge_and_missing_numbers_stay_none():
    art = {"program": "X-1", "validated": ["X-1-B"],
           "judged": [_judged("X-1-A", "SELL", 0.19, 1.0), _judged("X-1-B", "BUY", 0.3, 3.5, validated=True)]}
    a, b = from_confirmatory(art, {"X-1-A": {"timeframe": "D1", "instruments": ["EURUSD"]}})
    assert (a.status, a.direction, a.timeframe, a.instrument) == ("REJECTED", "SELL", "D1", ("EURUSD",))
    assert b.status == "VALIDATED" and b.timeframe is None  # unknown is None, not a guess
    assert a.gross_expectancy is None and a.profit_factor is None and a.drawdown is None
    assert a.complexity == 2 and a.failed_checks == ("significance",)
    assert a.cost_sensitivity == pytest.approx(0.14)


def test_a_failed_walk_forward_is_rejected_with_the_checks_it_failed():
    res = {"trial": "WF-9", "verdict": "FAIL", "threshold_t": 3.2,
           "spec": {"sides": [1, -1], "symbols": ["EURUSD"], "timeframe": "M15", "model": "stumps",
                    "features": ["r1", "r6"], "threshold_r": 0.0, "template": "T2"},
           "system": {"n": 500, "mean_R": -0.05, "t": -1.1},
           "folds": [{"start": "2011-01-01", "mean_R": -0.05}],
           "checks": {"min_trades": True, "beats_random": False}}
    e = from_walk_forward(res)
    assert (e.status, e.direction, e.timeframe, e.walk_forward_expectancy) == ("REJECTED", "BOTH", "M15", -0.05)
    assert e.failed_checks == ("beats_random",) and e.cost_sensitivity is None


def test_the_lifecycle_is_fixed_and_rejected_or_retired_is_final():
    art = {"program": "X-2", "validated": ["X-2-A"], "judged": [_judged("X-2-A", "BUY", 0.3, 3.5, True),
                                                                 _judged("X-2-B", "BUY", 0.0, 0.1)]}
    ok, bad = from_confirmatory(art)
    degraded = transition(ok, "DEGRADED")
    assert transition(degraded, "VALIDATED").status == "VALIDATED"  # decay that reverses is variance
    retired = transition(degraded, "RETIRED")
    for dead in (bad, retired):
        for s in STATUSES:
            with pytest.raises(TransitionError):
                transition(dead, s)
    with pytest.raises(TransitionError):
        transition(bad, "VALIDATED")  # a rejected idea never becomes validated in place


def test_promising_is_a_near_miss_with_real_evidence_and_never_validated():
    def judged(hid, mean, t, costs_ok, random_ok):
        c = _judged(hid, "BUY", mean, t)
        c["battery"]["checks"]["costs_stress"]["pass"] = costs_ok
        c["battery"]["checks"]["beats_random"] = {"pass": random_ok}
        return c
    art = {"program": "X-3", "validated": [], "judged": [
        judged("P", 0.2, 2.4, True, True), judged("Q", 0.2, 1.9, True, True), judged("S", 0.2, 2.4, False, True),
        judged("U", 0.2, 2.4, True, False), judged("V", -0.2, -2.4, True, True)]}
    got = {e.edge_id: e.status for e in from_confirmatory(art)}
    assert got == {"P": "PROMISING", "Q": "REJECTED", "S": "REJECTED", "U": "REJECTED", "V": "REJECTED"}
    p = next(e for e in from_confirmatory(art) if e.edge_id == "P")
    assert transition(p, "TESTING").status == "TESTING"  # the next step is a fresh test, not a trade
    with pytest.raises(TransitionError):
        transition(p, "DEGRADED")


def test_the_committed_registry_matches_the_committed_evidence():
    reg = build(ROOT / "research")
    ids = {e["edge_id"] for e in reg["edges"]}
    assert {"CP-001-T1", "SL-002-01", "WF-002"} <= ids
    for e in reg["edges"]:
        assert e["status"] in STATUSES
        for k in ("size", "lots", "risk_pct", "risk_amount"):
            assert k not in e
    # VALIDATED only where a committed, opened holdout says so; a program verdict alone never suffices
    holdouts = {}
    for f in (ROOT / "research" / "knowledge").glob("*.json"):
        art = json.loads(f.read_text())
        if isinstance(art, dict) and art.get("holdout_of"):
            holdouts.update({h: v for h, v in art.get("classification", {}).items() if v == "VALIDATED"})
    validated = {e["edge_id"] for e in reg["edges"] if e["status"] == "VALIDATED"}
    assert validated == set(holdouts) and reg["counts"]["VALIDATED"] == len(validated)
    assert validated <= {"DIV2-H1-TSMOM12"}  # a new VALIDATED edge must be reviewed here, not slip in
    passed = {k for k, p in reg["programs"].items() if p["verdict"] == "PASSED"}
    assert passed <= {"DIV-2"}
    assert all(p["verdict"] in ("FAILED", "FAIL", "PASSED") or p["verdict"].startswith("BLOCKED")
               for p in reg["programs"].values())
    vix = next((e for e in reg["edges"] if e["edge_id"] == "R4-XA-VIX-A"), None)
    if vix is not None:  # a recorded correction is carried into the registry, never silently applied
        assert vix["note"] and "registered population" in vix["note"] and vix["status"] == "REJECTED"
    committed = ROOT / "research" / "knowledge" / "edge_registry.json"
    assert json.loads(committed.read_text())["counts"] == reg["counts"]


def test_an_intraday_gate_stored_as_the_string_false_is_a_failed_check():
    """numpy booleans reach the artifact JSON as "True"/"False"; "False" is truthy and must still fail."""
    from aitrader.research.discovery import edges as E
    art = {"program": "ID-X", "t_required_validation": 3.5,
           "development": {"M-x": {"summary": {"trades": 400, "net_r": 0.05, "gross_r": 0.15, "t_day": 1.5,
                                               "profit_factor": 1.1, "max_drawdown_pct": 10.0},
                                   "detail": {"by_symbol": {"EURUSD": {}}, "by_year": {}},
                                   "gates": {"net_r": True, "symbols_positive": "False", "t_day": False,
                                             "min_trades": "True"},
                                   "vs_matched_random_welch_t": 5.0}}}
    rec = E.from_intraday(art)[0]
    assert rec.status == "REJECTED"
    assert set(rec.failed_checks) == {"development:symbols_positive", "development:t_day"}
