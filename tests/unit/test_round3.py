"""Round 3 is frozen before its data exists, and it cannot run on substitutes."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
import round3  # noqa: E402

from aitrader.research.discovery.edges import build  # noqa: E402
from aitrader.research.discovery.hypothesis import Ledger  # noqa: E402
from aitrader.research.registry import Holdout  # noqa: E402


def test_the_committed_design_is_the_frozen_one_and_any_change_is_refused(monkeypatch):
    assert round3.frozen() == round3.SPEC
    changed = json.loads(json.dumps(round3.SPEC))
    changed["hypotheses"][0]["condition"] = "rate_level=mid"  # a threshold or condition tuned after the fact
    monkeypatch.setattr(round3, "SPEC", changed)
    with pytest.raises(SystemExit):
        round3.frozen()


def test_without_both_sides_of_the_differential_no_pair_qualifies_and_nothing_runs():
    pairs, cov = round3.gate(Holdout.load(ROOT / "research" / "holdout.json"))
    assert pairs == [] and cov["EUR"]["status"] == "AVAILABLE" and cov["USD"]["status"] == "UNAVAILABLE"
    assert len(pairs) < round3.MIN_PAIRS


def test_round3_is_in_the_registry_as_unrun_hypotheses_and_repeats_no_earlier_idea():
    reg = build(ROOT / "research")
    r3 = [e for e in reg["edges"] if e["program"] == "R3"]
    assert len(r3) == len(round3.SPEC["hypotheses"]) and all(e["status"] == "HYPOTHESIS" for e in r3)
    earlier = {h.condition for h in Ledger(ROOT / "research" / "discovery" / "ledger.jsonl").hypotheses()}
    assert len(earlier) >= 20  # Round 1 and Round 2 drafts are all there
    for h in round3.SPEC["hypotheses"]:
        assert "rate_" in h["condition"] or "policy_move" in h["condition"]  # every one uses the differential
        assert h["condition"] not in earlier
