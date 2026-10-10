"""The dual-AI desk, with OpenRouter mocked: each trader always chooses a side; the same side is an agreement,
opposite sides are settled by ONE debate; a reply is used exactly as given or not at all; the desk never sizes
anything, and NO_TRADE only ever means the decision could not be made."""

from __future__ import annotations

import json
import math

import pytest

from aitrader.agents.brain import Brain, BrainConfig
from aitrader.agents.dual_ai import (
    FAMILY, LOSER_FAMILY, check_levels, counterfactual_decision, resolve, validate_trader, validate_verifier,
)

from tests.integration.test_pipeline import market
from tests.openrouter_kit import DEBATE, TRADER, VISION, FakeOpenRouter, answer, client, has_image, packet_of
from tests.unit.test_agents import T, V, analog, ctx

BID, ASK, ATR = 1.10000, 1.10006, 0.0010
PX = {"bid": BID, "ask": ASK, "atr": ATR}


def desk_ctx(mode="PAPER_FORWARD", **kw):
    c = ctx(analogs={"T1:BUY": analog("T1:BUY", 0.1, 0.05)}, **kw)
    c.mode = mode
    c.bars = {"H1": market("EURUSD", T - 3600 * 24 * 40, 24 * 40, 5, 1.10)}
    c.costs = {"spread": 0.00006, "total": 0.00009}
    return c


def desk(reply, **ckw):
    fake = FakeOpenRouter(reply)
    brain = Brain(config=BrainConfig(llm_agents=(), parallel=False, decision_mode="dual_ai"),
                  openrouter=client(fake, **ckw))
    return brain, fake


def scripted(t1=("BUY", 80), t2=("BUY", 80), debate="BUY", **over):
    def reply(role, body):
        if role in over:
            return over[role](body) if callable(over[role]) else over[role]
        if role == "trader1":
            return answer(t1[0], BID, ASK, ATR, confidence=t1[1], stop_atr=1.0, target_atr=2.0)
        if role == "trader2":
            return answer(t2[0], BID, ASK, ATR, confidence=t2[1], stop_atr=1.2, target_atr=2.4)
        return {"direction": debate, "confidence": 70, "reason": f"{debate}: structure and liquidity favour it"}
    return reply


def think(reply, c=None, **ckw):
    brain, fake = desk(reply, **ckw)
    d = brain.think(c or desk_ctx(), V).decision
    return d, fake


# ── agreement ───────────────────────────────────────────────────────────

def test_same_side_is_an_agreement_and_a_trade_candidate_with_the_more_confident_traders_levels():
    d, fake = think(scripted(t1=("BUY", 87), t2=("BUY", 91)))
    assert d.decision == "BUY" and d.family == FAMILY and d.signal_class is None  # the orchestrator stamps the class
    rec = d.ai["dual_ai"]
    assert rec["consensus"]["rule"] == "AGREE" and rec["consensus"]["levels_from"] == "trader2"
    assert d.stop_loss == pytest.approx(ASK - 1.2 * ATR) and d.take_profit == pytest.approx(ASK + 2.4 * ATR)
    assert d.entry == ASK  # a market order at the executable price; the size is the risk engine's alone
    assert [c["role"] for c in fake.calls] == ["trader1", "trader2"] and len(fake.calls) == 2
    assert fake.calls[0]["model"] == VISION and fake.calls[1]["model"] == TRADER  # two different models
    assert rec["models"] == {"trader1": VISION, "trader2": TRADER}


def test_on_equal_confidence_trader_1s_levels_are_used():
    d, _ = think(scripted(t1=("SELL", 80), t2=("SELL", 80)))
    assert d.decision == "SELL" and d.ai["dual_ai"]["consensus"]["levels_from"] == "trader1"
    assert d.stop_loss == pytest.approx(BID + 1.0 * ATR)


def test_a_low_confidence_agreement_is_still_a_candidate_the_risk_engine_decides():
    d, _ = think(scripted(t1=("BUY", 41), t2=("BUY", 38)))
    assert d.decision == "BUY" and d.ai["view"]["confidence"] == pytest.approx(0.38)


def test_trader_1_sees_the_chart_image_and_trader_2_gets_the_data_the_marks_and_trader_1s_analysis():
    _, fake = think(scripted())
    t1, t2 = fake.calls[0]["body"], fake.calls[1]["body"]
    assert has_image(t1) and "chart_marks" in packet_of(t1) and "timeframe_summaries" in packet_of(t1)
    p2 = packet_of(t2)
    assert not has_image(t2)  # its model cannot read images: the same chart's marks as numbers instead
    assert p2["trader1_analysis"]["direction"] == "BUY" and p2["chart_marks"]["execution_timeframe"]
    assert p2["execution_bars"]["rows"] and p2["higher_timeframe_bars"]["timeframe"] == "H4"
    assert len(p2["execution_bars"]["rows"][0]) == 6  # open time, OHLC, tick count
    assert "costs" in p2 and "volatility" in p2


# ── disagreement and the debate ─────────────────────────────────────────

def test_opposite_sides_start_one_debate_and_the_chosen_side_wins_with_its_traders_levels():
    d, fake = think(scripted(t1=("SELL", 82), t2=("BUY", 79), debate="BUY"))
    assert [c["role"] for c in fake.calls] == ["trader1", "trader2", "debate"]
    assert fake.calls[2]["model"] == DEBATE  # a third model, neither trader's
    p3 = packet_of(fake.calls[2]["body"])
    assert p3["trader1_analysis"]["direction"] == "SELL" and p3["trader2_analysis"]["direction"] == "BUY"
    assert has_image(fake.calls[2]["body"])
    rec = d.ai["dual_ai"]
    assert d.decision == "BUY" and rec["consensus"]["rule"] == "DEBATE" and rec["consensus"]["levels_from"] == "trader2"
    assert d.stop_loss == pytest.approx(ASK - 1.2 * ATR) and "debate" in d.thesis
    assert rec["verifier"]["reason"].startswith("BUY") and rec["debate_loser"]["direction"] == "SELL"
    loser = counterfactual_decision(d)
    assert loser.family == LOSER_FAMILY and loser.decision == "SELL" and loser.id.endswith(":debate-loser")
    assert loser.stop_loss == pytest.approx(BID + 1.0 * ATR)


def test_the_debate_can_choose_trader_1():
    d, _ = think(scripted(t1=("SELL", 70), t2=("BUY", 95), debate="SELL"))
    assert d.decision == "SELL" and d.ai["dual_ai"]["consensus"]["levels_from"] == "trader1"


def test_an_unusable_debate_leaves_the_disagreement_unresolved_no_second_round():
    d, fake = think(scripted(t1=("SELL", 80), t2=("BUY", 80), debate="HOLD"))
    assert d.decision == "NO_TRADE" and d.ai["dual_ai"]["consensus"]["rule"] == "DEBATE_UNRESOLVED"
    assert len(fake.calls) == 3


def test_an_agreement_never_calls_the_debate_and_no_decision_makes_more_than_three_calls():
    _, fake = think(scripted(t1=("BUY", 60), t2=("BUY", 99)))
    assert len(fake.calls) == 2
    _, fake = think(scripted(t1=("BUY", 60), t2=("SELL", 99)))
    assert len(fake.calls) == 3


# ── strict validation: used as given or not at all ──────────────────────

def good(**over):
    return {**answer("BUY", BID, ASK, ATR), **over}


@pytest.mark.parametrize("reply,why", [
    (good(direction="NO_TRADE"), "BUY or SELL"),
    (good(direction="HOLD"), "BUY or SELL"),
    (good(confidence=True), "confidence"),
    (good(confidence=150), "confidence"),
    (good(confidence=math.nan), "confidence"),
    (good(entry=math.inf), "entry"),
    (good(stop_loss=ASK + 0.0005), "wrong side"),        # a BUY stop above the price
    (good(take_profit=ASK - 0.0005), "wrong side"),      # a BUY target below the price
    (good(entry=ASK + 3 * ATR), "executable price"),     # a misread price
    (good(stop_loss=ASK - 20 * ATR, risk_reward=0.1), "beyond"),
    (good(risk_reward=5.0), "contradicts"),              # 2.0 by its own levels
    (good(reason=""), "reason"),
    (good(reversal_probability=-5), "reversal_probability"),
    ({k: v for k, v in good().items() if k != "stop_loss"}, "stop_loss"),
])
def test_a_malformed_or_impossible_answer_is_rejected_never_repaired(reply, why):
    problem = validate_trader(reply, PX)
    assert problem and why in problem
    d, fake = think(scripted(trader1=reply))
    assert d.decision == "NO_TRADE" and d.ai["dual_ai"]["consensus"]["rule"] == "TRADER1_UNAVAILABLE"
    assert len(fake.calls) == 1  # no decision on one trader alone: Trader 2 is not asked


def test_malformed_json_from_trader_2_is_no_trade():
    d, fake = think(scripted(trader2="BUY because it looks good"))
    assert d.decision == "NO_TRADE" and d.ai["dual_ai"]["consensus"]["rule"] == "TRADER2_UNAVAILABLE"


def test_validators_accept_a_well_formed_answer_and_check_the_debate():
    assert validate_trader(good(), PX) is None and check_levels("SELL", answer("SELL", BID, ASK, ATR), PX) is None
    assert validate_verifier({"direction": "SELL", "confidence": 60, "reason": "x"}) is None
    assert validate_verifier({"direction": "NO_TRADE", "confidence": 60, "reason": "x"})
    assert validate_verifier({"direction": "BUY", "confidence": "high", "reason": "x"})


def test_resolve_is_the_desk_rule():
    a, b = answer("BUY", BID, ASK, ATR, confidence=70), answer("BUY", BID, ASK, ATR, confidence=71)
    assert resolve(a, b) == {"outcome": "TRADE", "rule": "AGREE", "direction": "BUY", "levels_from": "trader2",
                             "loser": None}
    s = answer("SELL", BID, ASK, ATR)
    assert resolve(a, s)["rule"] == "DEBATE_UNRESOLVED"
    assert resolve(a, s, {"direction": "SELL"})["levels_from"] == "trader2"
    assert resolve(a, s, {"direction": "BUY"})["loser"] == "trader2"


# ── unavailable is not an opinion ───────────────────────────────────────

def test_a_failing_trader_2_is_no_trade_not_a_decision_on_trader_1_alone():
    d, _ = think(scripted(trader2=lambda body: (503, {}, {"error": {"message": "overloaded"}})))
    assert d.decision == "NO_TRADE" and d.ai["dual_ai"]["consensus"]["rule"] == "TRADER2_UNAVAILABLE"


def test_a_spent_daily_quota_is_reported_as_the_ai_being_unavailable():
    d, _ = think(scripted(trader1=lambda b: (429, {}, {"error": {"message": "Rate limit exceeded: free-models-per-day"}})))
    assert d.decision == "NO_TRADE" and "DAILY_QUOTA" in d.no_trade_reason


def test_when_trading_is_paused_nothing_is_asked():
    c = desk_ctx()
    c.trading_allowed = False
    d, fake = think(scripted(), c)
    assert d.decision == "NO_TRADE" and d.ai["dual_ai"]["consensus"]["rule"] == "MARKET_UNAVAILABLE"
    assert fake.calls == []


def test_without_a_key_nothing_is_asked():
    d, fake = think(scripted(), key="PASTE_MY_KEY_HERE")
    assert d.ai["dual_ai"]["consensus"]["rule"] == "AI_UNAVAILABLE" and fake.calls == [] and fake.headers == []


def test_outside_paper_forward_the_desk_does_not_decide_and_cannot_be_backtested():
    d, fake = think(scripted(), desk_ctx(mode="PAPER"))
    assert d.decision == "NO_TRADE" and d.ai["dual_ai"]["consensus"]["rule"] == "MODE" and fake.calls == []
    brain, _ = desk(scripted())
    with pytest.raises(ValueError):
        brain.think(desk_ctx(mode="BACKTEST"), V)


def test_the_same_decision_point_is_asked_once():
    brain, fake = desk(scripted())
    c = desk_ctx()
    a = brain.think(c, V).decision
    b = brain.think(c, V).decision
    assert a.id == b.id and len(fake.calls) == 2  # the second answer comes from the duplicate cache


def test_the_record_keeps_answers_models_and_request_ids_never_the_key():
    from tests.openrouter_kit import KEY
    d, _ = think(scripted())
    blob = json.dumps(d.as_dict(), default=str)
    assert KEY not in blob and "Bearer" not in blob
    calls = d.ai["dual_ai"]["calls"]
    assert all(c["request_id"] and c["model"] for c in calls) and d.ai["dual_ai"]["chart"]["sha256"]
