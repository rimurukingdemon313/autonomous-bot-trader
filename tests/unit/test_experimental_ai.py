"""DECISION_MODE=experimental_ai: proposer, specialists, deterministic synthesis, fail-closed paths,
provider failures, and the configuration and execution switches that keep it away from a live account."""

from __future__ import annotations

import json
from types import SimpleNamespace

import pytest

from aitrader.agents.brain import Brain, BrainConfig
from aitrader.agents.experimental_ai import FAMILY, ExperimentalConfig, synthesize
from aitrader.broker.paper import PaperBroker
from aitrader.execution.engine import ExecutionEngine
from aitrader.llm.provider import Endpoint, LLMClient, LLMConfig
from aitrader.risk.engine import RiskVerdict
from aitrader.service.config import ServiceConfig, ServiceConfigError

from .test_agents import V
from .test_execution import decision, setup, verdict
from .test_llm_trader import live_ctx

PROPOSAL = {"action": "BUY", "timeframe": "H4", "stop": 1.0985, "target": 1.1040, "max_hold_minutes": 600,
            "thesis": "H4 uptrend, pullback held", "invalidation": "H4 close below 1.0985", "confidence": 0.6,
            "expected_r": 0.4, "evidence": ["higher lows"], "reasons_against": ["NFP tomorrow"], "method": "trend"}


def two_providers():
    return LLMConfig(providers=(Endpoint("alpha", "https://a.test/v1", "k1", "ma"),
                                Endpoint("beta", "https://b.test/v1", "k2", "mb")))


def brain(proposer, specialist, calls, specialists=("adversary",), cfg=None):
    def t(url, headers, body, timeout):
        calls.append((url, body))
        system = body["messages"][0]["content"]
        reply = specialist(body) if "A colleague proposed" in system else proposer(body)
        if isinstance(reply, Exception):
            raise reply
        return {"choices": [{"message": {"content": reply if isinstance(reply, str) else json.dumps(reply)}}],
                "usage": {"prompt_tokens": 100, "completion_tokens": 20, "total_tokens": 120}}
    return Brain(llm=LLMClient(cfg or two_providers(), t),
                 config=BrainConfig(llm_agents=(), parallel=False, decision_mode="experimental_ai",
                                    experimental=ExperimentalConfig(specialists)))


AGREE = {"verdict": "AGREE", "direction": "BUY", "objections": [], "summary": "structure supports it"}


def test_a_challenged_and_surviving_proposal_is_an_experimental_trade_with_full_metadata():
    calls = []
    d = brain(lambda b: PROPOSAL, lambda b: AGREE, calls).think(live_ctx(), V).decision
    assert d.decision == "BUY" and d.family == FAMILY and d.ai_verdict == "TRADE"
    assert d.stop_loss == 1.0985 and d.take_profit == 1.1040  # verbatim: specialists cannot move a level
    assert d.ai["provider"] == "alpha" and d.ai["model"] == "ma" and d.ai["view"]["confidence"] == 0.6
    assert d.ai["view"]["reasons_against"] == ["NFP tomorrow"] and d.ai["disagreement"] == 0.0
    assert "b.test" in calls[1][0]  # the challenger is a different provider: a second mind, not an echo
    assert d.ai["specialists"]["adversary"]["tokens"]["prompt_tokens"] == 100


@pytest.mark.parametrize("specialist,why", [
    (lambda b: {"verdict": "DISAGREE", "direction": "SELL", "summary": "trap",
                "objections": [{"code": "FAKE_BREAKOUT_RISK", "severity": "BLOCKING", "reason": "no follow-through"}]},
     "BLOCKING"),
    (lambda b: {"verdict": "DISAGREE", "direction": "NONE", "summary": "x", "objections": [
        {"code": "OVEREXTENDED", "severity": "MAJOR", "reason": "a"}, {"code": "SPREAD_COST", "severity": "MAJOR", "reason": "b"}]},
     "MAJOR"),
    (lambda b: "this is not json", "unavailable or reply rejected"),
    (lambda b: {"verdict": "AGREE", "direction": "BUY", "objections": [{"code": "MADE_UP", "severity": "MINOR"}]},
     "unavailable or reply rejected"),  # an unknown objection code is a malformed reply
    (lambda b: TimeoutError("timed out"), "unavailable or reply rejected"),
])
def test_any_specialist_veto_or_failure_is_no_trade(specialist, why):
    d = brain(lambda b: PROPOSAL, specialist, []).think(live_ctx(), V).decision
    assert d.decision == "NO_TRADE" and why in d.no_trade_reason and d.family == FAMILY


def test_specialists_naming_the_opposite_direction_make_it_uncertain():
    d = brain(lambda b: PROPOSAL, lambda b: {"verdict": "DISAGREE", "direction": "SELL", "objections": [], "summary": "x"},
              [], specialists=("structure", "adversary")).think(live_ctx(), V).decision
    assert d.decision == "NO_TRADE" and d.ai_verdict == "UNCERTAIN" and d.ai["disagreement"] == 1.0


@pytest.mark.parametrize("reply,verdict_", [
    ({"action": "UNCERTAIN", "thesis": "mixed signals"}, "UNCERTAIN"),
    ({"action": "NO_TRADE", "thesis": "nothing here"}, "NO_TRADE"),
])
def test_the_proposer_may_decline_and_no_specialist_is_paid(reply, verdict_):
    calls = []
    d = brain(lambda b: reply, lambda b: AGREE, calls).think(live_ctx(), V).decision
    assert d.decision == "NO_TRADE" and d.ai_verdict == verdict_ and len(calls) == 1


def test_a_proposer_that_cannot_answer_is_no_trade():
    for bad in ("{", json.dumps({**PROPOSAL, "confidence": None}), json.dumps({**PROPOSAL, "stop": 1.2})):
        d = brain(lambda b, x=bad: x, lambda b: AGREE, []).think(live_ctx(), V).decision
        assert d.decision == "NO_TRADE"


def test_synthesis_is_a_rule_not_a_vote():
    assert synthesize("BUY", {"adversary": AGREE})[0] is None
    one_major = {"verdict": "DISAGREE", "direction": "NONE",
                 "objections": [{"code": "OVEREXTENDED", "severity": "MAJOR", "reason": "x"}]}
    assert synthesize("BUY", {"adversary": one_major})[0] is None  # one MAJOR is recorded, not a veto
    # the adversary arguing the other side is its job, not a direction call
    assert synthesize("BUY", {"adversary": {**AGREE, "verdict": "DISAGREE", "direction": "SELL"}})[0] is None


def test_unknown_specialist_roles_are_refused():
    with pytest.raises(ValueError):
        ExperimentalConfig(("adversary", "astrologer"))
    assert ExperimentalConfig.from_env({}).specialists == ("adversary",)
    assert ExperimentalConfig.from_env({"AI_SPECIALISTS": "quant, macro"}).specialists == ("quant", "macro")


def test_cost_tracking_is_per_provider_and_unpriced_is_not_zero():
    cfg = LLMConfig(providers=(Endpoint("alpha", "https://a.test/v1", "k", "ma", cost_in_per_mtok=1.0,
                                        cost_out_per_mtok=2.0), Endpoint("beta", "https://b.test/v1", "k", "mb")))
    b = brain(lambda x: PROPOSAL, lambda x: AGREE, [], cfg=cfg)
    b.think(live_ctx(), V)
    h = b.llm.health()["by_provider"]
    assert h["alpha"]["est_cost_usd"] == pytest.approx((100 * 1.0 + 20 * 2.0) / 1e6)
    assert h["beta"]["est_cost_usd"] is None and h["beta"]["prompt_tokens"] == 100


# ── configuration: live is impossible, ambiguity fails closed ──────────

def test_the_defaults_are_paper_and_no_live():
    c = ServiceConfig.from_env({})
    assert c.mode == "PAPER" and c.experimental_execute is False
    assert c.public()["live_trading"] is False and c.public()["paper_mode"] is True


@pytest.mark.parametrize("env", [
    {"LIVE_TRADING": "true"}, {"LIVE_TRADING": "1"}, {"LIVE_TRADING": "maybe"},
    {"MODE": "LIVE"}, {"MODE": "REAL"},
    {"PAPER_MODE": "true", "MODE": "DEMO"}, {"PAPER_MODE": "false"}, {"PAPER_MODE": "sometimes"},
    {"EXPERIMENTAL_EXECUTE": "true"},  # PAPER always simulates: the switch is DEMO-only
    {"EXPERIMENTAL_EXECUTE": "yes please", "MODE": "DEMO"},
    {"EXEC_MAX_DECISION_AGE_S": "5"},
])
def test_ambiguous_or_live_configuration_is_refused(env):
    with pytest.raises(ServiceConfigError):
        ServiceConfig.from_env(env)


def test_experimental_execute_is_refused_while_nothing_is_validated():
    """Takeover audit: no edge is VALIDATED, so DEMO sends no unvalidated order. The switch is refused."""
    with pytest.raises(ServiceConfigError, match="EXPERIMENTAL_EXECUTE"):
        ServiceConfig.from_env({"MODE": "DEMO", "PAPER_MODE": "false", "EXPERIMENTAL_EXECUTE": "true"})


# ── execution: no live path, shadow by default, stale and drifted refused ──

def test_there_is_no_live_argument_and_an_unverified_account_never_trades():
    feed, clock, db = setup()
    with pytest.raises(TypeError):
        ExecutionEngine(db, PaperBroker(feed, clock, db), clock, allow_live=True)
    broker = PaperBroker(feed, clock, db)
    broker.is_demo = lambda: None  # could not tell
    r = ExecutionEngine(db, broker, clock, allow_unvalidated=True).execute(decision(edge_status="VALIDATED"), verdict())
    assert r.status == "BLOCKED" and "no live path" in r.detail


def test_an_unvalidated_trade_is_blocked_unless_execution_of_it_was_enabled():
    feed, clock, db = setup()
    r = ExecutionEngine(db, PaperBroker(feed, clock, db), clock).execute(decision(), verdict())
    assert r.status == "BLOCKED" and "shadow only" in r.detail
    feed, clock, db = setup()
    missing = SimpleNamespace(id="d1", decision="BUY", instrument="EURUSD", timestamp=clock())  # no edge status
    assert ExecutionEngine(db, PaperBroker(feed, clock, db), clock).execute(missing, verdict()).status == "BLOCKED"
    feed, clock, db = setup()
    ok = ExecutionEngine(db, PaperBroker(feed, clock, db), clock).execute(decision(edge_status="VALIDATED"), verdict())
    assert ok.status == "FILLED"


def test_a_stale_decision_is_not_executed():
    feed, clock, db = setup()
    d = decision()
    d.timestamp = clock() - 3600
    r = ExecutionEngine(db, PaperBroker(feed, clock, db), clock, allow_unvalidated=True).execute(d, verdict())
    assert r.status == "BLOCKED" and "stale" in r.detail
    assert db.one("SELECT status FROM intents")["status"] == "BLOCKED"  # the intent is on record either way


def test_a_price_that_ran_away_from_the_entry_is_not_chased():
    feed, clock, db = setup()  # the market is at 1.10; the risk check priced the entry at 1.0990
    v = RiskVerdict("d1", True, qty=0.5, risk_amount=100, risk_pct=0.5, entry_ref=1.0990, stop=1.0970, target=1.1100)
    r = ExecutionEngine(db, PaperBroker(feed, clock, db), clock, allow_unvalidated=True).execute(decision(), v)
    assert r.status == "BLOCKED" and "not chased" in r.detail


def test_no_prompt_asks_for_a_trade_because_the_account_is_idle():
    """Inactivity is never a reason to trade (owner, 2026-10): the prompts say so, and nothing pushes."""
    from aitrader.agents import llm_trader, trading_room
    texts = [llm_trader.SYSTEM, trading_room._OWNER, *trading_room.STYLES.values()]
    for t in texts:
        low = " ".join(t.lower().split())
        for phrase in ("sit idle", "prefers a small", "prefer a small", "a new trade each minute", "anything reasonable"):
            assert phrase not in low, phrase
    assert "time without a trade costs nothing" in " ".join(llm_trader.SYSTEM.lower().split())
