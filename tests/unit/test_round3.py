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


def test_the_bis_file_qualifies_only_pairs_covered_on_both_sides_for_the_whole_period():
    if not (ROOT / "data" / "rates" / "WS_CBPOL_csv_flat.csv").exists():
        pytest.skip("the BIS WS_CBPOL file is not committed (data/rates/manifest.json records its sha256)")
    pairs, cov = round3.gate(Holdout.load(ROOT / "research" / "holdout.json"))
    # the BoJ had no policy rate from 2013-04 to 2016-09: JPY is not covered, and no JPY pair qualifies
    assert cov["JPY"]["status"] == "UNAVAILABLE" and all("JPY" not in p for p in pairs)
    assert pairs == ["EURUSD", "GBPUSD", "AUDUSD", "USDCAD", "USDCHF", "NZDUSD", "EURGBP", "EURCHF"]
    assert len(pairs) >= round3.MIN_PAIRS


def test_round3_is_in_the_registry_as_unrun_hypotheses_and_repeats_no_earlier_idea():
    reg = build(ROOT / "research")
    r3 = [e for e in reg["edges"] if e["program"] == "R3"]
    assert len(r3) == len(round3.SPEC["hypotheses"])
    judged = (ROOT / "research" / "knowledge" / "R3.json").exists()
    assert all(e["status"] in (("VALIDATED", "PROMISING", "REJECTED") if judged else ("HYPOTHESIS",)) for e in r3)
    earlier = {h.condition for h in Ledger(ROOT / "research" / "discovery" / "ledger.jsonl").hypotheses()}
    assert len(earlier) >= 20  # Round 1 and Round 2 drafts are all there
    for h in round3.SPEC["hypotheses"]:
        assert "rate_" in h["condition"] or "policy_move" in h["condition"]  # every one uses the differential
        assert h["condition"] not in earlier
