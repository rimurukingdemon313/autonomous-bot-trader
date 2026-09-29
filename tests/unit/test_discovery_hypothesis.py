"""Hypotheses are complete, falsifiable objects; the ledger enforces their lifecycle permanently."""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone

import pytest

from aitrader.llm.provider import LLMResult
from aitrader.research.discovery.hypothesis import (Hypothesis, Ledger, LedgerError, derive_next, from_lesson,
                                                    from_screen, llm_drafts, mechanism_for)
from aitrader.research.discovery.study import Condition

NOW = datetime(2026, 9, 29, 12, 0, tzinfo=timezone.utc)
FIDS = {f: f"{f}@1" for f in ("er120", "r24", "vol_ratio", "ma_slope", "session", "bar_body")}
RULES = {"min_trades": "n >= 100", "significance": "clustered t >= 3.07"}


def hyp(hid="H-1", condition="er120=high&r24=high", side="BUY", exit_="E1", **kw):
    base = dict(id=hid, statement="trends continue", rationale="observed on fit data", mechanism="momentum",
                features=("er120@1", "r24@1"), condition=condition, side=side, instruments=("EURUSD", "GBPUSD"),
                timeframe="H1", exit=exit_, expected_effect="mean net R > 0", falsification=("t < 3.07",), budget=8,
                origin="screen", program="P-1")
    return Hypothesis(**(base | kw))


def at(k):
    return NOW + timedelta(minutes=k)


def run_to(ledger, hid, final="VALIDATED"):
    ledger.transition(hid, "PREREGISTERED", at(1), trial="DP-X", preregistration_sha256="abc")
    ledger.transition(hid, "RUNNING", at(2), trial="DP-X")
    ledger.transition(hid, "COMPLETED", at(3), summary={"n": 120})
    ledger.transition(hid, final, at(4), **({"checks": {"all": True}} if final == "VALIDATED" else {"reason": "t"}))


# ── the object ─────────────────────────────────────────────────────────


def test_a_hypothesis_must_state_everything_needed_to_test_and_falsify_it():
    hyp().validate()
    for field, bad in (("statement", " "), ("mechanism", ""), ("falsification", ()), ("instruments", ()),
                       ("exit", "E99"), ("side", "LONG"), ("condition", "er120=huge"), ("budget", 0)):
        with pytest.raises((LedgerError, ValueError)):
            hyp(**{field: bad}).validate()


def test_a_hypothesis_never_carries_a_size():
    with pytest.raises(LedgerError):
        hyp(evidence={"lots": 2.0}).validate()
    with pytest.raises(LedgerError):
        hyp(evidence={"risk_pct": 1.0}).validate()
    assert "Risk Engine" in hyp().risk


def test_model_and_derived_hypotheses_are_prospective_only():
    with pytest.raises(LedgerError):
        hyp(origin="llm").validate()
    hyp(origin="llm", prospective_only=True).validate()


def test_substance_ignores_wording_but_not_what_is_tested():
    a, b = hyp(), hyp("H-2", statement="different words", rationale="other")
    assert a.substance() == b.substance()
    assert a.substance() != hyp(side="SELL").substance() != hyp(exit_="E2").substance()
    assert hyp(condition="r24=high&er120=high").substance() != a.substance()  # term order is part of the key


# ── the ledger ─────────────────────────────────────────────────────────


def test_the_lifecycle_is_enforced(tmp_path):
    led = Ledger(tmp_path / "l.jsonl")
    led.draft(hyp(), NOW)
    with pytest.raises(LedgerError):
        led.transition("H-1", "RUNNING", at(1), trial="X")  # must be preregistered first
    with pytest.raises(LedgerError):
        led.transition("H-1", "PREREGISTERED", at(1), trial="X")  # without the preregistration hash
    led.transition("H-1", "PREREGISTERED", at(1), trial="DP-X", preregistration_sha256="abc")
    led.transition("H-1", "RUNNING", at(2), trial="DP-X")
    led.transition("H-1", "RUNNING", at(3), trial="DP-X", resumed=True)  # after an interruption
    with pytest.raises(LedgerError):
        led.transition("H-1", "VALIDATED", at(4), checks={})  # not completed
    led.transition("H-1", "COMPLETED", at(4), summary={"n": 1})
    with pytest.raises(LedgerError):
        led.transition("H-1", "COMPLETED", at(3), summary={})  # back-dated and not permitted
    led.transition("H-1", "REJECTED", at(5), reason="t below threshold")
    for state in ("VALIDATED", "DRAFT", "RUNNING"):
        with pytest.raises(LedgerError):
            led.transition("H-1", state, at(6), checks={}, trial="X", reason="x")
    assert [e.get("state", "DRAFT") for e in led.history("H-1")] == [
        "DRAFT", "PREREGISTERED", "RUNNING", "RUNNING", "COMPLETED", "REJECTED"]


def test_a_rejected_idea_cannot_come_back_under_a_new_name(tmp_path):
    led = Ledger(tmp_path / "l.jsonl")
    led.draft(hyp(), NOW)
    run_to(led, "H-1", "REJECTED")
    with pytest.raises(LedgerError):
        led.draft(hyp("H-2", statement="momentum, rephrased"), at(5))
    with pytest.raises(LedgerError):  # prospective, but not naming its parent
        led.draft(hyp("H-2", origin="derived", prospective_only=True), at(5))
    led.draft(hyp("H-2", origin="derived", prospective_only=True, parent="H-1"), at(5))
    led.draft(hyp("H-3", side="SELL"), at(6))  # a different substance is a different idea
    with pytest.raises(LedgerError):
        led.draft(hyp("H-4", side="SELL", statement="again"), at(7))  # duplicates H-3 while it is open
    with pytest.raises(LedgerError):
        led.draft(hyp("H-3", side="SELL", exit_="E2"), at(7))  # ids are never reused


def test_the_ledger_survives_a_restart_and_keeps_rejections_searchable(tmp_path):
    path = tmp_path / "l.jsonl"
    led = Ledger(path)
    led.draft(hyp(), NOW)
    run_to(led, "H-1", "REJECTED")
    led.draft(hyp("H-2", condition="vol_ratio=low", features=("vol_ratio@1",), statement="quiet markets drift",
                  mechanism="compression before expansion"), at(5))
    again = Ledger(path)
    assert again.state("H-1") == "REJECTED" and again.state("H-2") == "DRAFT"
    assert again.history("H-1") == led.history("H-1")
    assert [h["id"] for h in again.search("momentum")] == ["H-1"]  # the mechanism text is searchable
    assert [h["id"] for h in again.search(state="REJECTED")] == ["H-1"]
    assert again.counts() == {"DRAFT": 1, "REJECTED": 1}


def test_an_edited_ledger_line_is_refused(tmp_path):
    path = tmp_path / "l.jsonl"
    Ledger(path).draft(hyp(), NOW)
    raw = json.loads(path.read_text())
    raw["hypothesis"]["side"] = "SELL"
    path.write_text(json.dumps(raw) + "\n")
    with pytest.raises(LedgerError):
        Ledger(path)


# ── generators ─────────────────────────────────────────────────────────


def test_a_screen_row_becomes_a_complete_draft_with_a_conjectured_mechanism():
    row = {"condition": "er120=high&r24=low", "side": "BUY", "n": 240, "mean_R": 0.12, "se": 0.04, "t": 3.1,
           "q": 0.05, "clusters": 150}
    h = from_screen("DP-X-H1", row, program="P", instruments=("EURUSD",), feature_ids=FIDS,
                    rules=RULES | {"screen_tests": 1734}, budget=8)
    h.validate()
    assert h.exit == "MENU" and h.features == ("er120@1", "r24@1") and "reversal" in h.mechanism
    assert "1734 tests" in h.rationale and h.evidence["screen"]["n"] == 240
    assert "continuation" in mechanism_for(Condition.parse("r24=high"), "BUY")
    assert "state-dependent" in mechanism_for(Condition.parse("vol_ratio=high"), "SELL")


class FakeModel:
    def __init__(self, reply):
        self.reply = reply

    def complete_json(self, agent, system, packet, validate):
        err = validate(self.reply)
        return LLMResult(err is None, agent, "fake-model", "OK" if err is None else "SCHEMA",
                         self.reply if err is None else None, error=err)


VOCAB = {"features": list(FIDS), "exits": ["E1", "E2"], "instruments": ["EURUSD", "GBPUSD"]}


def test_model_drafts_are_accepted_only_in_the_closed_vocabulary_and_only_prospectively():
    good = {"hypotheses": [{"statement": "s", "rationale": "r", "mechanism": "m", "side": "SELL", "exit": "E2",
                            "condition": [{"feature": "session", "bin": "low"}, {"feature": "r24", "bin": "high"}],
                            "instruments": ["EURUSD"]}]}
    out = llm_drafts(FakeModel(good), program="P", id_prefix="LLM-1", vocabulary=VOCAB, observations={},
                     rules=RULES, feature_ids=FIDS, cutoff="2025-01")
    assert len(out) == 1 and out[0].prospective_only and out[0].condition == "session=low&r24=high"
    out[0].validate()
    for bad in ({"feature": "rsi", "bin": "low"}, {"feature": "r24", "bin": "extreme"}):
        reply = json.loads(json.dumps(good))
        reply["hypotheses"][0]["condition"] = [bad]
        assert llm_drafts(FakeModel(reply), program="P", id_prefix="LLM-2", vocabulary=VOCAB, observations={},
                          rules=RULES, feature_ids=FIDS, cutoff="2025-01") == []  # never repaired
    reply = json.loads(json.dumps(good))
    reply["hypotheses"][0]["exit"] = "E7"
    assert llm_drafts(FakeModel(reply), program="P", id_prefix="LLM-3", vocabulary=VOCAB, observations={},
                      rules=RULES, feature_ids=FIDS, cutoff="2025-01") == []


def test_a_live_lesson_becomes_a_veto_hypothesis_or_nothing():
    lesson = {"lesson_id": "L:TREND_PULLBACK|-1|RANGING|HIGH_VOL", "status": "VALIDATED", "version": 2,
              "context": ["TREND_PULLBACK", -1, "RANGING", "HIGH_VOL"], "statement": "loses"}
    h = from_lesson("LS-1", lesson, program="P", instruments=("EURUSD",), feature_ids=FIDS, rules=RULES)
    h.validate()
    assert h.kind == "veto" and h.side == "SELL" and h.condition == "er120=low&vol_ratio=high"
    assert "cannot be expressed" in h.rationale
    up = dict(lesson, context=["BREAKOUT", 1, "TRENDING_UP", "LOW_VOL"])
    assert from_lesson("LS-2", up, program="P", instruments=("EURUSD",), feature_ids=FIDS,
                       rules=RULES).condition == "er120=high&ma_slope=high&vol_ratio=low"
    odd = dict(lesson, context=["X", 1, "ABNORMAL", "HIGH_VOL"])
    assert from_lesson("LS-3", odd, program="P", instruments=("EURUSD",), feature_ids=FIDS, rules=RULES) is None


def test_a_follow_up_comes_from_how_an_idea_failed_and_never_rescues_a_dead_one():
    h = hyp()
    assert derive_next(h, "E1", ["significance"], {}, program="P", hid="N-1") is None
    assert derive_next(h, "E1", ["permutation", "costs_stress"], {}, program="P", hid="N-1") is None
    n = derive_next(h, "E1", ["costs_stress"], {}, program="P", hid="N-1")
    n.validate()
    assert n.exit == "E2" and n.prospective_only and n.parent == "H-1" and n.origin == "derived"
    m = derive_next(h, "E3", ["instruments"], {}, program="P", hid="N-2", instruments_ok=("EURUSD",))
    assert m.instruments == ("EURUSD",) and m.exit == "E3"
