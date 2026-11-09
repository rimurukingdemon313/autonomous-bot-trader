"""The autonomous research engine (scripts/research_engine.py). The models are scripted: the fake replaces the network,
never the engine's own logic.

The engine never registers, tests, approves or trades anything. A model that fails or answers out of schema
records nothing, and the next run retries. A rerun or a crash never records an idea twice. A tampered record or a
stall fails the cycle visibly. The power gate is plain arithmetic."""

from __future__ import annotations

import ast
import json
import shutil
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

import scripts.research_cycle as RC
import scripts.research_engine as E

ROOT = Path(E.__file__).resolve().parent.parent
DAY1 = datetime(2026, 11, 10, 4, 47, tzinfo=timezone.utc)


def hyp(title, universe="new:ftse-auction", horizon="swing", rule=None, sharpe=1.2, years=12.0):
    return {"title": title, "mechanism": "forced sellers at a fixed time", "universe": universe, "horizon": horizon,
            "rule": rule or f"buy at the close when {title} holds, sell at the next close",
            "data_source": "a public daily series", "evidence": "Someone (2020), Journal: 12 bp a day",
            "claimed_sharpe_annual": sharpe, "years_of_fresh_data": years, "why_new": "never tested here",
            "needs_short_or_leverage": "neither"}


def scripted(proposal, review, proposer="lab-a/model-1", critic="lab-b/model-2"):
    """A proposer and a critic that answer as scripted: a dict, None (unavailable) or an exception (a crash)."""
    calls = []

    def ask(role, messages, validate, avoid):
        calls.append({"role": role, "avoid": avoid, "messages": messages})
        data, model = (proposal, proposer) if role == "researcher" else (review, critic)
        if isinstance(data, Exception):
            raise data
        if data is None:
            return False, "UNAVAILABLE", None, None, "the provider is down"
        why = validate(data)
        if why:
            return False, f"INVALID: {why}", None, model, why
        return True, "OK", data, model, None
    ask.calls = calls
    return ask


def three():
    hs = [hyp("a repeat of a dropped family"),
          hyp("FX majors drift", universe="fx-majors", sharpe=0.5, years=10.0),
          hyp("closing auction imbalance", universe="new:ftse-auction", sharpe=1.2, years=12.0)]
    rv = [{"index": 0, "verdict": "REJECT", "reason": "repeats the gotobi flows", "duplicate_of": "FLOW-1"},
          {"index": 1, "verdict": "PASS", "reason": "plausible", "duplicate_of": None},
          {"index": 2, "verdict": "PASS", "reason": "plausible", "duplicate_of": None}]
    return {"hypotheses": hs}, {"reviews": rv}


def ideas(state):
    return E.read_jsonl(state / "ideas.jsonl")


def cycles(state):
    return E.read_jsonl(state / "cycles.jsonl")


# ── one cycle ────────────────────────────────────────────────────────────


def test_a_cycle_records_every_idea_once_with_the_decision_the_critic_and_the_arithmetic_reached(tmp_path):
    ask = scripted(*three())
    res = E.Engine(ROOT, tmp_path, ask, DAY1).run()
    assert res.exit_code == 0 and res.integrity == [] and res.ideas == "OK"
    got = ideas(tmp_path)
    assert [i["decision"] for i in got] == ["REJECTED_BY_CRITIC", "DROPPED_POWER", "QUEUED_FOR_BUILD"]
    assert got[0]["duplicate_of"] == "FLOW-1" and got[0]["power"] is None  # a rejected idea is never power-checked
    assert got[1]["power"]["expected_t"] == round(0.5 * 10 ** 0.5, 3) < got[1]["power"]["bar"] > 3.6  # fx-majors
    from aitrader.research.registry import bonferroni_t
    assert got[2]["power"]["bar"] == round(bonferroni_t(1), 4)  # data no test here has read: the first test's bar
    assert all(i["proposer"] == "lab-a/model-1" and i["critic"] == "lab-b/model-2" for i in got)
    assert [c["role"] for c in ask.calls] == ["researcher", "critic"]
    assert ask.calls[1]["avoid"] == ("lab-a/model-1",)  # the critic may never be the proposer's model
    assert "FLOW-1" in ask.calls[0]["messages"][1]["content"]  # the families already tested are in its context
    assert [(c["step"], c["status"]) for c in cycles(tmp_path)] == [("integrity", "OK"), ("ideas", "OK")]


def test_a_rerun_the_same_day_asks_no_model_and_records_nothing_twice(tmp_path):
    E.Engine(ROOT, tmp_path, scripted(*three()), DAY1).run()
    again = scripted(*three())
    res = E.Engine(ROOT, tmp_path, again, DAY1 + timedelta(hours=3)).run()
    assert res.ideas == "SKIPPED" and again.calls == [] and len(ideas(tmp_path)) == 3


def test_a_crash_after_the_ideas_were_written_never_writes_them_twice(tmp_path):
    E.Engine(ROOT, tmp_path, scripted(*three()), DAY1).run()
    rows = [c for c in cycles(tmp_path) if c["step"] != "ideas"]  # the checkpoint after the write was lost
    (tmp_path / "cycles.jsonl").write_text("".join(json.dumps(r) + "\n" for r in rows))
    again = scripted(*three())
    assert E.Engine(ROOT, tmp_path, again, DAY1 + timedelta(hours=1)).run().ideas == "SKIPPED"
    assert again.calls == [] and len(ideas(tmp_path)) == 3


def test_the_same_idea_another_day_is_never_recorded_again_however_it_is_worded(tmp_path):
    E.Engine(ROOT, tmp_path, scripted(*three()), DAY1).run()
    old = hyp("closing auction imbalance", rule="BUY at the close when closing auction imbalance holds; sell at "
              "the NEXT close.")
    new = hyp("a genuinely different idea", universe="new:gold-fix", rule="buy gold at the London PM fix")
    rv = {"reviews": [{"index": 0, "verdict": "PASS", "reason": "ok", "duplicate_of": None},
                      {"index": 1, "verdict": "PASS", "reason": "ok", "duplicate_of": None}]}
    res = E.Engine(ROOT, tmp_path, scripted({"hypotheses": [old, new]}, rv), DAY1 + timedelta(days=1)).run()
    assert [i["title"] for i in res.new_ideas] == ["a genuinely different idea"]
    assert len(ideas(tmp_path)) == 4 and res.integrity == []


def test_the_state_restored_elsewhere_carries_on_as_if_never_stopped(tmp_path):
    a, b = tmp_path / "run1", tmp_path / "run2"
    E.Engine(ROOT, a, scripted(*three()), DAY1).run()
    shutil.copytree(a, b)  # the next runner restores the state from the research-data branch
    again = scripted(*three())
    assert E.Engine(ROOT, b, again, DAY1 + timedelta(hours=5)).run().ideas == "SKIPPED" and again.calls == []
    nxt = E.Engine(ROOT, b, scripted(*three()), DAY1 + timedelta(days=1)).run()
    assert nxt.ideas == "OK" and nxt.new_ideas == []  # the same three ideas: already recorded, nothing added
    assert [c["cycle"] for c in cycles(b) if c["step"] == "ideas"] == ["2026-11-10", "2026-11-11"]


# ── failures: nothing invented, retried, visible ─────────────────────────


@pytest.mark.parametrize("proposal,review,why", [
    (None, None, "the proposer gave no usable answer (UNAVAILABLE"),
    ({"hypotheses": [hyp("x", horizon="weekly")]}, None, "horizon must be one of"),
    ({"hypotheses": [hyp("x") | {"claimed_sharpe_annual": "1.2"}]}, None, "claimed_sharpe_annual must be a number"),
    ({"hypotheses": [hyp("x", universe="Bitcoin")]}, None, "neither a listed market"),
    ({"hypotheses": [hyp("x")]}, None, "the critic gave no usable answer"),
    ({"hypotheses": [hyp("x")]}, {"reviews": [{"index": 0, "verdict": "MAYBE", "reason": "?"}]}, "PASS or REJECT"),
    ({"hypotheses": [hyp("x"), hyp("y", rule="other")]},
     {"reviews": [{"index": 0, "verdict": "PASS", "reason": "ok"}]}, "exactly 2"),
])
def test_a_model_that_fails_or_answers_out_of_schema_records_nothing_and_is_never_repaired(tmp_path, proposal,
                                                                                            review, why):
    res = E.Engine(ROOT, tmp_path, scripted(proposal, review), DAY1).run()
    assert res.ideas.startswith("FAILED") and why in res.ideas and res.exit_code == 0
    assert ideas(tmp_path) == [] and cycles(tmp_path)[-1]["status"] == "FAILED"


def test_a_model_answering_out_of_schema_is_not_repaired_the_next_model_is_asked_instead(tmp_path):
    p, r = three()
    calls = []

    def ask(role, messages, validate, avoid):
        calls.append((role, avoid))
        if role == "researcher" and "lab-a/bad" not in avoid:
            return False, "INVALID: " + validate({"hypotheses": [hyp("x", horizon="weekly")]}), None, "lab-a/bad", "x"
        return (True, "OK", p, "lab-c/good", None) if role == "researcher" else (True, "OK", r, "lab-b/critic", None)
    res = E.Engine(ROOT, tmp_path, ask, DAY1).run()
    assert res.ideas == "OK" and calls == [("researcher", ()), ("researcher", ("lab-a/bad",)),
                                           ("critic", ("lab-c/good",))]
    assert {i["proposer"] for i in ideas(tmp_path)} == {"lab-c/good"}


def test_a_rate_limited_model_is_passed_over_not_waited_out_and_every_attempt_is_recorded(tmp_path):
    p, r = three()
    calls = []

    def ask(role, messages, validate, avoid):
        calls.append((role, avoid))
        if role == "researcher" and "lab-a/busy" not in avoid:
            return False, "RATE_LIMITED", None, "lab-a/busy", "HTTP 429: temporarily rate-limited upstream"
        if role == "researcher" and "lab-d/slow" not in avoid:
            return False, "TIMEOUT", None, "lab-d/slow", "no answer in time"
        return (True, "OK", p, "lab-c/good", None) if role == "researcher" else (True, "OK", r, "lab-b/critic", None)
    res = E.Engine(ROOT, tmp_path, ask, DAY1).run()
    assert res.ideas == "OK" and len(ideas(tmp_path)) == 3
    assert calls[:3] == [("researcher", ()), ("researcher", ("lab-a/busy",)), ("researcher", ("lab-a/busy", "lab-d/slow"))]
    done = [c for c in cycles(tmp_path) if c["step"] == "ideas"][-1]
    assert [a["status"] for a in done["detail"]["attempts"]] == ["RATE_LIMITED", "TIMEOUT", "OK", "OK"]
    no_model = E.Engine(ROOT, tmp_path / "x", scripted(None, None), DAY1)
    assert no_model.run().ideas.startswith("FAILED") and len(no_model.attempts) == 1  # nothing else would answer


def test_after_a_failure_the_next_run_retries_and_completes(tmp_path):
    assert E.Engine(ROOT, tmp_path, scripted(None, None), DAY1).run().ideas.startswith("FAILED")
    res = E.Engine(ROOT, tmp_path, scripted(*three()), DAY1 + timedelta(hours=1)).run()
    assert res.ideas == "OK" and len(ideas(tmp_path)) == 3
    assert [(c["step"], c["status"]) for c in cycles(tmp_path) if c["step"] == "ideas"] == [("ideas", "FAILED"),
                                                                                           ("ideas", "OK")]


def test_a_crash_inside_the_step_is_recorded_and_writes_nothing(tmp_path):
    res = E.Engine(ROOT, tmp_path, scripted(RuntimeError("boom"), None), DAY1).run()
    assert res.ideas == "FAILED: RuntimeError: boom" and ideas(tmp_path) == []


def test_the_critic_answering_as_the_proposers_own_model_records_nothing(tmp_path):
    p, r = three()
    res = E.Engine(ROOT, tmp_path, scripted(p, r, proposer="same/model", critic="same/model"), DAY1).run()
    assert "the critic was the proposer's own model" in res.ideas and ideas(tmp_path) == []


def test_no_model_client_is_a_visible_failure_not_an_invented_idea(tmp_path):
    res = E.Engine(ROOT, tmp_path, None, DAY1).run()
    assert "OPENROUTER_API_KEY is not set" in res.ideas and ideas(tmp_path) == []


def test_three_days_without_a_successful_idea_step_is_a_visible_stall(tmp_path):
    E.Engine(ROOT, tmp_path, scripted(*three()), DAY1).run()
    two = E.Engine(ROOT, tmp_path, scripted(None, None), DAY1 + timedelta(days=2)).run()
    assert not two.stalled and two.exit_code == 0
    four = E.Engine(ROOT, tmp_path, scripted(None, None), DAY1 + timedelta(days=4)).run()
    assert four.stalled and four.exit_code == 2 and cycles(tmp_path)[-1]["step"] == "stall"


def copy_repo(tmp_path) -> Path:
    r = tmp_path / "repo"
    for rel in ("research/registry.jsonl", "research/holdout.json", "research/QUEUE.md"):
        (r / rel).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(ROOT / rel, r / rel)
    for d in ("research/knowledge", "research/preregistrations"):
        shutil.copytree(ROOT / d, r / d)
    return r


def test_a_tampered_record_or_a_changed_seal_fails_the_cycle_visibly(tmp_path):
    r = copy_repo(tmp_path)
    assert E.Engine(r, tmp_path / "s0", scripted(*three()), DAY1).run().integrity == []
    k = r / "research" / "knowledge" / "TRND-1.json"
    k.write_text(k.read_text().replace('"verdict": "PASSED"', '"verdict": "PASSED", "edited": true'))
    res = E.Engine(r, tmp_path / "s1", scripted(*three()), DAY1).run()
    assert res.exit_code == 1 and any("TRND-1: its evidence no longer matches" in p for p in res.integrity)
    h = r / "research" / "holdout.json"
    h.write_text(h.read_text().replace('"start": "2017-01-01"', '"start": "2019-01-01"'))
    res = E.Engine(r, tmp_path / "s2", scripted(*three()), DAY1).run()
    assert any("the seal" in p for p in res.integrity) and res.exit_code == 1


# ── what it is and is not allowed to do ──────────────────────────────────


def test_the_power_gate_is_arithmetic_and_an_implausible_claim_is_dropped():
    pw = E.power(1.0, 9.0, 2.5)
    assert pw["expected_t"] == 3.0 and pw["p_pass"] == 0.691
    assert E.decide(hyp("x", sharpe=2.5), 2.0)[0] == "DROPPED_IMPLAUSIBLE"
    assert E.decide(hyp("x", sharpe=0.8, years=9.0), 2.5)[0] == "DROPPED_POWER"  # expects t 2.4 against 2.5
    assert E.decide(hyp("x", sharpe=0.9, years=9.0), 2.5)[0] == "QUEUED_FOR_BUILD"  # expects t 2.7


def test_the_engine_cannot_trade_register_or_judge():
    tree = ast.parse((ROOT / "scripts" / "research_engine.py").read_text())
    imported = {n.module for n in ast.walk(tree) if isinstance(n, ast.ImportFrom) and n.module} | \
        {a.name for n in ast.walk(tree) if isinstance(n, ast.Import) for a in n.names}
    assert not any(m.startswith(("aitrader.broker", "aitrader.execution", "aitrader.position", "aitrader.risk",
                                 "aitrader.service")) for m in imported)
    called = {n.func.attr for n in ast.walk(tree) if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)}
    assert not called & {"register", "record_verdict", "place_market_order", "close_position", "modify_position"}


def test_the_cycle_writes_its_report_with_the_engine_kept_apart(tmp_path, capsys):
    code = RC.cycle(tmp_path, DAY1, scripted(*three()))
    assert code == 0
    text = (tmp_path / "RESEARCH_REPORT.md").read_text()
    engine = text.split("## The autonomous engine's ideas")[1].split("## Validation status")[0]
    assert "QUEUED_FOR_BUILD**: closing auction imbalance" in engine and "REJECTED_BY_CRITIC" in engine
    assert "closing auction imbalance (new:ftse-auction; queued 2026-11-10" in engine
    assert "RESEARCH ONLY · NO MONEY · NOT A TRADING RESULT" in text
    js = json.loads((tmp_path / "RESEARCH_REPORT.json").read_text())
    assert js["engine"]["by_decision"] == {"DROPPED_POWER": 1, "QUEUED_FOR_BUILD": 1, "REJECTED_BY_CRITIC": 1}
