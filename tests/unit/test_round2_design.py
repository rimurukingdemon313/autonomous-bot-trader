"""Round 2's design as registered: fixed states only, the holdout untouched, and no repeat research."""

from __future__ import annotations

import shutil
import sys
from dataclasses import replace
from pathlib import Path

import pytest

from aitrader.research.discovery.hypothesis import Ledger, LedgerError
from aitrader.research.discovery.macro import GROUPS3, macro_primitives
from aitrader.research.discovery.study import Condition
from aitrader.research.registry import Holdout

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
import round2  # noqa: E402


def test_every_condition_is_a_fixed_state_and_the_judged_period_stops_before_the_holdout():
    prims = macro_primitives({"vix": None, "us10y": None, "brent": None})
    holdout = Holdout.load(ROOT / "research" / "holdout.json")
    assert round2.JUDGE.end <= holdout.start and round2.FIT.end < round2.JUDGE.start
    for fam in round2.FAMILIES.values():
        for s in fam.specs:
            for f in Condition.parse(s.condition).features:
                assert f in prims and prims[f].kind == "categorical"  # nothing fitted to outcomes
        prog_groups = {f: GROUPS3 for f in round2.features(fam)}
        assert set(prog_groups) == set(round2.features(fam))


def test_the_same_idea_under_a_new_name_is_refused(tmp_path):
    led_path = tmp_path / "ledger.jsonl"
    shutil.copy(ROOT / "research" / "discovery" / "ledger.jsonl", led_path)
    led = Ledger(led_path)
    original = led.get("R2A-1")
    again = replace(original, id="R2X-1", statement="Buying carry when markets are calm is profitable (reworded).")
    with pytest.raises(LedgerError):
        from datetime import datetime, timezone
        led.draft(again, datetime(2026, 10, 1, tzinfo=timezone.utc))
