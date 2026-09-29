"""The loop closes for hypotheses the screen did not produce: a confirmatory program judges
drafts from any source once, and refuses the ones history cannot honestly judge."""

from __future__ import annotations

from dataclasses import replace
from datetime import date, datetime, timezone

import pytest

from aitrader.research.discovery.battery import BatteryRules
from aitrader.research.discovery.catalog import FeatureCatalog, FeatureRecord
from aitrader.research.discovery.confirm import ConfirmatoryProgram, ConfirmDesign
from aitrader.research.discovery.hypothesis import Hypothesis, Ledger, from_lesson
from aitrader.research.discovery.program import ProgramError
from aitrader.research.discovery.study import Segment
from aitrader.research.registry import Holdout, Registry
from tests.unit.discovery_market import SYMBOLS, planted

NOW = datetime(2026, 9, 29, 12, 0, tzinfo=timezone.utc)
HOLDOUT = Holdout("synthetic", date(2012, 6, 1), datetime(2026, 1, 1, tzinfo=timezone.utc), "test seal")
FIT = Segment("fit", "fit", date(2010, 1, 11), date(2010, 12, 1))
JUDGE = Segment("judge", "judge", date(2010, 12, 11), date(2012, 4, 1))
FIDS = {f: f"{f}@1" for f in ("A", "B", "er120", "vol_ratio", "ma_slope")}
RULES_TEXT = {"significance": "t >= frozen"}


def hyp(hid, condition, side, kind="opportunity", origin="human", **kw):
    feats = tuple(FIDS[t.split("=")[0]] for t in condition.split("&"))
    return Hypothesis(id=hid, statement=f"{condition} {side} ({kind})", rationale="by construction",
                      mechanism="planted", features=feats, condition=condition, side=side, instruments=SYMBOLS,
                      timeframe="H1", exit="E1", expected_effect="as stated", falsification=("the battery",), budget=1,
                      origin=origin, program="CP-T1", kind=kind, **kw)


def setup(tmp_path, hypotheses, **kw):
    cat = FeatureCatalog(tmp_path / "features.jsonl")
    cat.open_program("CP-T1", 10, NOW)
    for f in FIDS:
        rec = cat.register(FeatureRecord(f, f"synthetic {f}", "test", "continuous", "H1", ("synthetic",), "tests",
                                         "1", "by construction", "test", "CP-T1"), NOW)
        cat.record_leakage(rec.id, [], 10, list(SYMBOLS), NOW)
    led = Ledger(tmp_path / "ledger.jsonl")
    for h in hypotheses:
        led.draft(h, NOW)
    reg = Registry.load(tmp_path / "registry.jsonl", HOLDOUT)
    d = ConfirmDesign("CP-T1", "confirm drafts", "do the drafts hold?", "synthetic", SYMBOLS,
                      tuple(h.id for h in hypotheses), FIT, JUDGE, BatteryRules(t_threshold=1.0, permutations=40,
                                                                                  random_draws=4),
                      HOLDOUT.start, groups=(("A", ((0.0,), (1.0,), (2.0,))),), **kw)
    d = replace(d, rules=replace(d.rules, t_threshold=reg.threshold_for_next(
        "synthetic", JUDGE.start, JUDGE.end, new_tests=len(hypotheses))))
    return ConfirmatoryProgram(d, reg, led, cat, tmp_path / "knowledge", lambda: NOW)


def test_drafts_from_any_source_are_judged_once_by_the_same_battery(tmp_path):
    lesson = {"lesson_id": "L:X|-1|RANGING|HIGH_VOL", "status": "VALIDATED", "version": 2, "statement": "loses",
              "context": ["X", -1, "RANGING", "HIGH_VOL"]}
    hs = [hyp("C-1", "A=high", "BUY"),
          hyp("C-2", "A=high", "SELL", kind="veto"),
          from_lesson("C-3", lesson, program="CP-T1", instruments=SYMBOLS, feature_ids=FIDS, rules=RULES_TEXT)]
    prog = setup(tmp_path, hs)
    prog.preregister(tmp_path / "CP-T1.md", "CP-T1.md")
    assert {prog.ledger.state(h.id) for h in hs} == {"PREREGISTERED"}
    art = prog.run(planted(n=20_000))
    states = {h.id: prog.ledger.state(h.id) for h in hs}
    assert states["C-1"] == "VALIDATED"  # the planted rise
    assert states["C-2"] == "VALIDATED"  # selling into it loses, robustly and specifically
    # the lesson's context loses too, but only because every trade pays costs: random entries lose as much,
    # so the claim that THIS context is bad is not supported
    assert states["C-3"] == "REJECTED"
    c3 = next(c for c in art["judged"] if c["id"] == "C-3")
    assert "beats_random" in c3["battery"]["failed"] and c3["battery"]["checks"]["significance"]["pass"]
    assert Registry.load(tmp_path / "registry.jsonl", HOLDOUT).verdict_of("CP-T1").status == "PASSED"
    with pytest.raises(ProgramError):
        prog.run(planted(n=20_000))  # once


def test_a_prospective_draft_is_never_judged_on_history_older_than_itself(tmp_path):
    h = hyp("C-9", "A=high", "BUY", origin="derived", prospective_only=True, parent="C-0")
    prog = setup(tmp_path, [h])
    with pytest.raises(ProgramError):
        prog.preregister(tmp_path / "x.md", "x.md")
    assert not prog.registry.trials and prog.ledger.state("C-9") == "DRAFT"


def test_a_draft_that_leaves_its_exit_open_cannot_be_confirmed(tmp_path):
    prog = setup(tmp_path, [replace(hyp("C-5", "A=high", "BUY"), exit="MENU")])
    with pytest.raises(ProgramError):
        prog.preregister(tmp_path / "x.md", "x.md")


def test_changed_code_is_refused_and_the_holdout_is_out_of_reach(tmp_path):
    prog = setup(tmp_path, [hyp("C-1", "A=high", "BUY")])
    prog.preregister(tmp_path / "x.md", "x.md")
    other = ConfirmatoryProgram(prog.design, prog.registry, prog.ledger, prog.catalog, tmp_path / "k", lambda: NOW,
                                code_hash=lambda: "changed")
    with pytest.raises(ProgramError):
        other.run(planted(n=20_000))
    late = replace(prog.design, judge=Segment("judge", "judge", date(2010, 12, 11), date(2012, 7, 1)))
    with pytest.raises(ProgramError):
        late.validate()


def test_an_interrupted_confirmation_resumes_to_the_complete_result(tmp_path, monkeypatch):
    import aitrader.research.discovery.confirm as confirm_mod
    hs = [hyp("C-1", "A=high", "BUY"), hyp("C-2", "A=high", "SELL", kind="veto")]
    prog = setup(tmp_path, hs)
    prog.preregister(tmp_path / "CP-T1.md", "CP-T1.md")
    market = planted(n=20_000)
    real = confirm_mod.synthesize
    calls = {"n": 0}

    def crash_on_second(*a, **k):
        calls["n"] += 1
        if calls["n"] == 2:
            raise RuntimeError("the process died")
        return real(*a, **k)

    monkeypatch.setattr(confirm_mod, "synthesize", crash_on_second)
    with pytest.raises(RuntimeError):
        prog.run(market)
    assert prog.ledger.state("C-1") == "VALIDATED" and prog.ledger.state("C-2") == "RUNNING"
    monkeypatch.setattr(confirm_mod, "synthesize", real)
    again = ConfirmatoryProgram(prog.design, Registry.load(tmp_path / "registry.jsonl", HOLDOUT),
                                Ledger(tmp_path / "ledger.jsonl"), FeatureCatalog(tmp_path / "features.jsonl"),
                                tmp_path / "knowledge", lambda: NOW)
    art = again.run(market)
    assert art["validated"] == ["C-1", "C-2"] and art["verdict"] == "PASSED"  # C-1 was not lost on resume
