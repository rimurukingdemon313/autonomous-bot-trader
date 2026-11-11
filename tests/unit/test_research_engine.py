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


def hyp(title, universe="new:ftse-auction", horizon="swing", rule=None, sharpe=1.2, years=12.0, cls="forced flows"):
    return {"title": title, "mechanism": "forced sellers at a fixed time", "mechanism_class": cls, "universe": universe,
            "horizon": horizon,
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
          hyp("FX majors drift", universe="fx-majors", sharpe=0.5, years=10.0, cls="risk premium"),
          hyp("closing auction imbalance", universe="new:ftse-auction", sharpe=1.2, years=12.0, cls="liquidity provision")]
    rv = [{"index": 0, "verdict": "REJECT", "category": "repeats_closed_family", "reason": "repeats the gotobi flows",
           "duplicate_of": "FLOW-1"},
          {"index": 1, "verdict": "PASS", "category": None, "reason": "plausible", "duplicate_of": None},
          {"index": 2, "verdict": "PASS", "category": None, "reason": "plausible", "duplicate_of": None,
           "conditions_flag": None}]
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
    # fx-majors: the bar of the ten fresh years the idea would use, by the tests the registry counts on them
    assert got[1]["power"]["expected_t"] == round(0.5 * 10 ** 0.5, 3) < got[1]["power"]["bar"] > 3.5
    assert got[2]["power"]["bar"] == E.BAR_FLOOR == 3.0  # data no test here has read: the floor every program is judged at
    assert [i["idea_class"] for i in got] == ["REPEATS_CLOSED_FAMILY", "INSUFFICIENT_POWER", "UNTESTED_HYPOTHESIS"]
    assert got[0]["critic_category"] == "repeats_closed_family" and got[1]["power"]["plan"]["ways"]
    assert [i["mechanism_class"] for i in got] == ["forced flows", "risk premium", "liquidity provision"]
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
    new = hyp("a genuinely different idea", universe="new:gold-fix", rule="buy gold at the London PM fix",
              cls="macro and policy")
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
    ({"hypotheses": [hyp("x"), hyp("y", rule="other", cls="volatility")]},
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


def test_the_third_production_cycle_replayed_three_failing_models_are_passed_over_and_the_tries_are_bounded(tmp_path):
    """2026-11-09 18:51 UTC: the three models offered timed out, were cut at max_tokens and were rate-limited, and the
    step failed. Now a fourth and a fifth are asked; past the fifth the step fails, recorded, and the next run retries."""
    p, r = three()
    failing = [("recursive/flint-v1.0:free", "TIMEOUT"),
               ("nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free",
                "INVALID: the reply was cut at max_tokens before its JSON (a reasoning model spent the budget thinking)"),
               ("xingchen-agi/xing4.0-29b-a4b:free", "RATE_LIMITED")]

    def ask_with(n_failing):
        bad = failing + [(f"lab-{k}/also-busy:free", "RATE_LIMITED") for k in range(n_failing - len(failing))]
        calls = []

        def ask(role, messages, validate, avoid):
            calls.append(role)
            if role == "researcher":
                for m, status in bad:
                    if m not in avoid:
                        return False, status, None, m, "as in production"
                return True, "OK", p, "lab-z/strong:free", None
            return True, "OK", r, "lab-y/critic:free", None
        return ask, calls

    ask, calls = ask_with(3)
    res = E.Engine(ROOT, tmp_path / "a", ask, DAY1).run()
    assert res.ideas == "OK" and calls == ["researcher"] * 4 + ["critic"]
    ask, calls = ask_with(E.MODEL_TRIES)
    res = E.Engine(ROOT, tmp_path / "b", ask, DAY1).run()
    assert res.ideas.startswith("FAILED") and calls == ["researcher"] * E.MODEL_TRIES  # bounded: the job's time holds
    assert ideas(tmp_path / "b") == [] and len(cycles(tmp_path / "b")[-1]["detail"]["attempts"]) == E.MODEL_TRIES


def test_the_proposer_is_told_each_numbers_range_exactly_as_the_validator_enforces_it():
    """1.1.1: in the fourth cycle a model answered with a claimed Sharpe ratio outside a range its prompt never stated.
    The prompt now states every range from the validator's own constants. The validator still repairs nothing."""
    for k, (lo, hi) in E.NUMBERS.items():
        assert f"- {k}: a JSON number above {lo:g} and at most {hi:g}, never text;" in E.SYSTEM_PROPOSER
        for bad in (lo, lo - 1, hi + 0.01, str(hi), None, True, float("nan")):
            why = E.validate_proposal({"hypotheses": [hyp("x") | {k: bad}]}, set())
            assert why is not None and k in why
        assert E.validate_proposal({"hypotheses": [hyp("x") | {k: hi}]}, set()) is None


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


def test_an_idea_that_cannot_reach_its_bar_is_kept_with_a_plan_not_dropped_in_silence():
    decision, why, pw = E.decide(hyp("x", sharpe=0.5, years=4.0), 3.0)  # expects t 1.0 against 3.0
    assert decision == "DROPPED_POWER" and E.idea_class(decision, None) == "INSUFFICIENT_POWER"
    plan = pw["plan"]
    assert plan["years_of_fresh_data_needed"] == 36.0  # (3.0 / 0.5) squared: t grows with the square root of the years
    assert plan["independent_instruments_needed"] == 9  # (3.0 / 1.0) squared: or of the instruments in one book
    assert "kept with a plan" in why and "36 years" in why and "9 independent instruments" in why
    assert E.decide(hyp("x", sharpe=1.6, years=4.0), 3.0)[2].get("plan") is None  # one that can pass needs none
    assert E.idea_class("QUEUED_FOR_BUILD", None) == "UNTESTED_HYPOTHESIS"  # queued is untested, not promising


def test_a_critic_must_name_one_of_five_reasons_and_short_selling_is_not_one():
    ok = {"index": 0, "verdict": "PASS", "category": None, "reason": "fine", "duplicate_of": None}
    assert E.validate_review({"reviews": [ok]}, 1) is None
    # the first production cycle's rejection, word for word: no category, and a reason that breaks no condition
    said = {"index": 0, "verdict": "REJECT", "duplicate_of": None,
            "reason": "Violates owner's swap-free/no interest-bearing instrument condition (requires short selling and leverage)."}
    assert "needs a category" in E.validate_review({"reviews": [said]}, 1)
    assert "needs a category" in E.validate_review({"reviews": [{**said, "category": "breaks_owner_conditions"}]}, 1)
    assert "name the family" in E.validate_review({"reviews": [{**said, "category": "repeats_closed_family"}]}, 1)
    assert E.validate_review({"reviews": [{**said, "category": "no_mechanism"}]}, 1) is None
    assert "carries no category" in E.validate_review({"reviews": [{**ok, "category": "no_mechanism"}]}, 1)
    assert "conditions_flag" in E.validate_review({"reviews": [{**ok, "conditions_flag": "needs short selling"}]}, 1)
    assert E.validate_review({"reviews": [{**ok, "conditions_flag": "needs_overnight_financing"}]}, 1) is None
    assert "ARE allowed" in E.SYSTEM_PROPOSER and "SHORT\nSELLING AND LEVERAGE ARE ALLOWED" in E.SYSTEM_CRITIC
    assert set(E.REJECTIONS.values()) >= {"SCIENTIFICALLY_INVALID", "INSUFFICIENT_DATA", "REPEATS_CLOSED_FAMILY"}


def test_a_doubt_about_the_owners_conditions_is_a_flag_for_the_loop_and_the_arithmetic_still_decides(tmp_path):
    hs = [hyp("short the richest perpetual", universe="new:perp-basis", sharpe=1.9, years=4.0, cls="risk premium")]
    flagged = {"reviews": [{"index": 0, "verdict": "PASS", "category": None, "reason": "it may need financing overnight",
                            "duplicate_of": None, "conditions_flag": "needs_overnight_financing"}]}
    E.Engine(ROOT, tmp_path, scripted({"hypotheses": hs}, flagged), DAY1).run()
    got = ideas(tmp_path)
    assert len(got) == 1 and got[0]["decision"] == "QUEUED_FOR_BUILD"  # 1.9 x sqrt(4) = 3.8 against 3.0
    assert got[0]["conditions_flag"] == "needs_overnight_financing" and got[0]["critic_verdict"] == "PASS"
    # the old way of saying it is out of schema: the next model is asked, and nothing is recorded on its word
    old = {"reviews": [{"index": 0, "verdict": "REJECT", "reason": "requires short selling", "duplicate_of": None}]}
    res = E.Engine(ROOT, tmp_path / "b", scripted({"hypotheses": hs}, old), DAY1).run()
    assert res.ideas.startswith("FAILED: the critic gave no usable answer") and ideas(tmp_path / "b") == []


def test_an_idea_is_gated_on_its_own_windows_bar_and_never_below_three(tmp_path):
    eng = E.Engine(ROOT, tmp_path, None, DAY1)
    reg = eng._registry()
    recent = eng.bar_for(hyp("x", universe="energy-futures-eia", years=2.0), reg)
    whole = eng.bar_for(hyp("x", universe="energy-futures-eia", years=30.0), reg)
    assert recent == 3.0  # the discovery scan charged rows from 1994 to 2011: not the rows of a test on 2024-2026
    assert whole > 3.5 and reg.tests_on("energy-futures-eia") > 400  # an idea that reaches back into them pays for it
    assert eng.bar_for(hyp("x", universe="new:never-read", years=50.0), reg) == 3.0  # the floor, not a first test's 2.24
    assert 3.5 < eng.bar_for(hyp("x", universe="fx-majors", years=10.0), reg) < eng.bar_for(
        hyp("x", universe="fx-majors", years=60.0), reg)  # the more of the read years an idea needs, the higher
    bars = eng.bars()
    assert bars["energy-futures-eia"]["tests"] == 0 and bars["energy-futures-eia"]["next_bar_t"] == 3.0
    assert bars["energy-futures-eia"]["tests_ever"] > 400 and all(b["next_bar_t"] >= 3.0 for b in bars.values())


def test_a_cycles_ideas_come_from_different_mechanism_classes_and_the_least_used_are_listed_first(tmp_path):
    same = {"hypotheses": [hyp("a"), hyp("b", rule="another rule entirely")]}
    assert "different mechanism classes" in E.validate_proposal(same, set())
    assert "mechanism_class must be one of" in E.validate_proposal({"hypotheses": [hyp("a", cls="chart pattern")]}, set())
    assert E.validate_proposal({"hypotheses": [hyp("a"), hyp("b", cls="volatility")]}, set()) is None
    ask = scripted(*three())
    E.Engine(ROOT, tmp_path, ask, DAY1).run()
    eng = E.Engine(ROOT, tmp_path, None, DAY1 + timedelta(days=1))
    counts = eng.classes()
    assert counts["forced flows"] == counts["risk premium"] == counts["liquidity provision"] == 1 and sum(counts.values()) == 3
    ask2 = scripted(None, None)
    E.Engine(ROOT, tmp_path, ask2, DAY1 + timedelta(days=1)).run()
    listing = ask2.calls[0]["messages"][1]["content"].split("Mechanism classes proposed here so far (fewest first):")[1]
    order = [x[2:].split(":")[0] for x in listing.split("\n\n")[0].strip().splitlines()]
    assert order[-3:] == ["forced flows", "risk premium", "liquidity provision"] and len(order) == len(E.MECHANISMS)
    assert order[0] == "information diffusion"  # never proposed: first


def test_the_discovery_labs_lessons_reach_the_proposer(tmp_path):
    r = copy_repo(tmp_path)
    assert E.lab_lessons(r) == []  # no lab record there: nothing is invented
    (r / "research" / "dlab").mkdir()
    (r / "research" / "dlab" / "lessons.json").write_text(json.dumps({"lessons": ["mkt-a: 40 rules; 0 promising", 7]}))
    assert E.lab_lessons(r) == ["the discovery lab's record: mkt-a: 40 rules; 0 promising"]
    ask = scripted(None, None)
    E.Engine(r, tmp_path / "state", ask, DAY1).run()
    said = ask.calls[0]["messages"][1]["content"]
    assert "the discovery lab's record: mkt-a: 40 rules; 0 promising" in said and "breadth:" in said
    (r / "research" / "dlab" / "lessons.json").write_text("not json")
    assert E.lab_lessons(r) == []


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
    assert "Class: UNTESTED_HYPOTHESIS." in engine and "Class: INSUFFICIENT_POWER." in engine and "kept with a plan" in engine
    assert "closing auction imbalance (new:ftse-auction; queued 2026-11-10" in engine
    assert "RESEARCH ONLY · NO MONEY · NOT A TRADING RESULT" in text
    js = json.loads((tmp_path / "RESEARCH_REPORT.json").read_text())
    assert js["engine"]["by_decision"] == {"DROPPED_POWER": 1, "QUEUED_FOR_BUILD": 1, "REJECTED_BY_CRITIC": 1}
