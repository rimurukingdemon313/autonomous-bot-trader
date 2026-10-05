"""Strict promotion gates and the canonical research status (takeover audit, steps 3 and 10)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

from aitrader.research import promotion as P

ROOT = Path(__file__).resolve().parents[2]

ALL_PASS = {"min_outcomes": 150, "net_positive": 0.08, "t_stat": 3.1, "median_positive": 0.02,
            "first_half_positive": 0.05, "second_half_positive": 0.06, "forward_positive": 0.04,
            "costs_x2_positive": 0.03, "delay_positive": 0.05, "no_leakage": True, "no_survivorship": True,
            "max_instrument_trade_share": 0.3, "max_day_profit_share": 0.05, "max_month_profit_share": 0.12,
            "max_trade_profit_share": 0.04, "max_drawdown_r": 12.0, "beats_baseline": True,
            "parameter_stability": True, "feature_stability": True, "no_broker_anomaly": True,
            "independent_review": True, "reproduced_clean": True, "demo_consistent": True,
            "human_promotion_record": "2027-01-01 operator X, ticket 12"}


def test_every_gate_must_pass_for_validated():
    assert P.status(ALL_PASS) == ("VALIDATED", [])
    for gate in P.GATES:
        broken = {**ALL_PASS, gate: None}  # unmeasured
        st, why = P.status(broken)
        assert st != "VALIDATED" and any(gate in w for w in why), gate


def test_quantitative_passes_without_review_or_forward_are_only_eligible_for_review():
    ev = {**ALL_PASS, **{k: None for k in P.HUMAN_OR_FORWARD}}
    st, why = P.status(ev)
    assert st == "ELIGIBLE_FOR_REVIEW" and len(why) == len(P.HUMAN_OR_FORWARD)


@pytest.mark.parametrize("bad", [{"net_positive": -0.01}, {"costs_x2_positive": -0.002}, {"no_leakage": False}])
def test_a_disqualifying_failure_is_failed_not_short(bad):
    assert P.status({**ALL_PASS, **bad})[0] == "FAILED"


def test_positive_and_t_above_two_but_short_of_the_gates_is_promising_and_below_two_is_failed():
    ev = {"min_outcomes": 441, "net_positive": 0.0016, "t_stat": 2.18, "costs_x2_positive": 0.0005}
    assert P.status(ev)[0] == "PROMISING"
    assert P.status(ev, forward_running=True)[0] == "FORWARD_TESTING"
    assert P.status({**ev, "t_stat": 1.9})[0] == "FAILED"
    assert P.status({**ev, "t_stat": 0.26})[0] == "FAILED"  # a positive sign is not evidence


def test_unregistered_or_unjudged_work_is_never_promoted():
    assert P.status(ALL_PASS, registered=False)[0] == "PROPOSED"
    assert P.status(ALL_PASS, judged=False)[0] == "REGISTERED"


def _status():
    path = ROOT / "research_status.json"
    if not path.exists():
        pytest.skip("research_status.json not generated")
    return json.loads(path.read_text())


def test_the_canonical_status_uses_only_the_strict_vocabulary_and_never_validates_without_every_gate():
    st = _status()
    assert {x["status"] for x in st["experiments"]} <= set(P.STATUSES)
    for e in st["validated_edges"]:
        assert P.status((e.get("curated") or {}).get("evidence") or {})[0] == "VALIDATED"
    if not st["validated_edges"]:
        assert st["final_statement"] in ("NO EDGE — DO NOT TRADE", "ELIGIBLE FOR REVIEW — NOT VALIDATED, DO NOT TRADE")
    div = next(x for x in st["experiments"] if x["experiment_id"] == "DIV-2-H")
    assert div["registry_verdict"] == "PASSED" and div["status"] == "FAILED"  # a registry PASS is not a validation
    assert all(h["state"] in ("SEALED", "OPENED") for h in st["sealed_periods"])
    fx = next(h for h in st["sealed_periods"] if h["universe"] == "fx-majors")
    assert fx["state"] == "SEALED"


def test_the_readme_headline_is_generated_from_the_canonical_status():
    sys.path.insert(0, str(ROOT / "scripts"))
    import research_status as RS
    st = _status()
    assert RS.headline(st) in (ROOT / "README.md").read_text(), "README headline is stale: run scripts/research_status.py"
