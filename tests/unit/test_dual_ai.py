"""The dual-AI desk, with OpenRouter mocked: each trader always chooses a side; the same side is an agreement and
the only way to a trade; opposite sides are no trade, with ONE debate in shadow whose pick and rejected side are
followed forward, never traded; a reply is used exactly as given or not at all; the desk never sizes anything,
and otherwise NO_TRADE only means the decision could not be made."""

from __future__ import annotations

import json
import math

import pytest

from aitrader.agents.brain import Brain, BrainConfig
from aitrader.agents.dual_ai import (
    FAMILY, LOSER_FAMILY, PICK_FAMILY, check_levels, counterfactual_decisions, resolve, validate_trader,
    validate_verifier,
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


# ── disagreement: no trade, the debate in shadow ────────────────────────

def test_opposite_sides_are_no_trade_whatever_the_debate_says_and_both_sides_are_followed_in_shadow():
    d, fake = think(scripted(t1=("SELL", 82), t2=("BUY", 79), debate="BUY"))
    assert [c["role"] for c in fake.calls] == ["trader1", "trader2", "debate"]
    assert fake.calls[2]["model"] == DEBATE  # a third model, neither trader's
    p3 = packet_of(fake.calls[2]["body"])
    assert p3["trader1_analysis"]["direction"] == "SELL" and p3["trader2_analysis"]["direction"] == "BUY"
    assert has_image(fake.calls[2]["body"])
    rec = d.ai["dual_ai"]
    assert d.decision == "NO_TRADE" and not d.is_trade and d.stop_loss is None and d.take_profit is None
    assert rec["consensus"]["rule"] == "DISAGREE" and rec["consensus"]["outcome"] == "NO_TRADE"
    assert rec["consensus"]["debate_pick"] == "BUY" and rec["consensus"]["pick_from"] == "trader2"
    assert "disagree" in d.no_trade_reason and "would have chosen BUY" in d.no_trade_reason
    assert rec["verifier"]["reason"].startswith("BUY")
    pick, loser = counterfactual_decisions(d)
    assert pick.family == PICK_FAMILY and pick.decision == "BUY" and pick.id.endswith(":debate-pick")
    assert pick.stop_loss == pytest.approx(ASK - 1.2 * ATR) and pick.ai_verdict == "DEBATE_PICK_NOT_TRADED"
    assert loser.family == LOSER_FAMILY and loser.decision == "SELL" and loser.id.endswith(":debate-loser")
    assert loser.stop_loss == pytest.approx(BID + 1.0 * ATR) and loser.ai_verdict == "LOST_THE_DEBATE"
    assert all(cf.edge_status == "EXPERIMENTAL" and cf.max_hold_minutes for cf in (pick, loser))


def test_a_shadow_debate_for_trader_1_is_still_no_trade():
    d, _ = think(scripted(t1=("SELL", 70), t2=("BUY", 95), debate="SELL"))
    assert d.decision == "NO_TRADE" and d.ai["dual_ai"]["consensus"]["pick_from"] == "trader1"
    assert [cf.decision for cf in counterfactual_decisions(d)] == ["SELL", "BUY"]


def test_an_unusable_debate_is_the_same_no_trade_with_nothing_to_follow_and_no_second_round():
    d, fake = think(scripted(t1=("SELL", 80), t2=("BUY", 80), debate="HOLD"))
    assert d.decision == "NO_TRADE" and d.ai["dual_ai"]["consensus"]["rule"] == "DISAGREE"
    assert d.ai["dual_ai"]["consensus"]["debate_pick"] is None and counterfactual_decisions(d) == []
    assert "no usable answer" in d.no_trade_reason
    assert len(fake.calls) == 3


def test_an_agreement_is_a_trade_with_nothing_followed_in_shadow():
    d, _ = think(scripted(t1=("BUY", 60), t2=("BUY", 99)))
    assert d.decision == "BUY" and d.ai["dual_ai"]["consensus"]["rule"] == "AGREE"
    assert counterfactual_decisions(d) == [] and "shadow" not in d.ai["dual_ai"]


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
    (good(reversal_probability=[20]), "reversal_probability"),
    (good(invalidation={"price": 1.09}), "invalidation"),
    ({k: v for k, v in good().items() if k != "stop_loss"}, "stop_loss"),
])
def test_a_malformed_or_impossible_answer_is_rejected_never_repaired(reply, why):
    problem = validate_trader(reply, PX)
    assert problem and why in problem
    d, fake = think(scripted(trader1=reply))
    assert d.decision == "NO_TRADE" and d.ai["dual_ai"]["consensus"]["rule"] == "TRADER1_UNAVAILABLE"
    # every free vision model gave the same unusable answer: each asked once, none repaired, Trader 2 never asked
    assert {c["role"] for c in fake.calls} == {"trader1"} and len(fake.calls) == len({c["model"] for c in fake.calls})


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
    assert resolve(a, b) == {"outcome": "TRADE", "rule": "AGREE", "direction": "BUY", "levels_from": "trader2"}
    assert resolve(b, a)["levels_from"] == "trader1"
    s = answer("SELL", BID, ASK, ATR)
    for verdict in (None, {"direction": "SELL"}, {"direction": "BUY"}):
        r = resolve(a, s, verdict)
        assert r["outcome"] == "NO_TRADE" and r["rule"] == "DISAGREE" and r["direction"] is None
        assert r["levels_from"] is None
    assert resolve(a, s)["pick_from"] is None and resolve(a, s)["loser"] is None
    assert resolve(a, s, {"direction": "SELL"})["pick_from"] == "trader2"
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
    assert d.decision == "NO_TRADE" and d.ai["dual_ai"]["consensus"]["rule"] == "NOT_ASKED"
    assert fake.calls == []


def test_a_refusal_before_the_traders_are_asked_says_which_rule_refused_never_that_the_market_was_missing():
    # found in the 2026-10-19 report: 88 decisions read "market unavailable for a decision: risk engine:
    # trading_calendar (...)": the market was there, a rule had refused
    c = desk_ctx()
    c.account_blocks = ["trading_calendar (Monday 12:00 UTC: no new position from 12:00 to 16:00 UTC)"]
    d, fake = think(scripted(), c)
    assert d.decision == "NO_TRADE" and fake.calls == []
    assert d.ai["dual_ai"]["consensus"]["rule"] == "NOT_ASKED"
    assert d.no_trade_reason.startswith("risk engine: trading_calendar (Monday 12:00 UTC")
    assert "market unavailable" not in d.no_trade_reason
    from aitrader.learning.dual_ai_stats import UNAVAILABLE
    assert "NOT_ASKED" in UNAVAILABLE and "MARKET_UNAVAILABLE" in UNAVAILABLE  # the old name still counted


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


def test_the_traders_market_description_is_recorded_as_given_and_never_voids_the_trade():
    # found by the live check: a model wrote its invalidation as a sentence where a price was asked
    reply = good(invalidation="a close below the 1.0985 swing low", reversal_probability="about 25%")
    assert validate_trader(reply, PX) is None
    d, _ = think(scripted(trader1=reply, t2=("BUY", 70)))
    assert d.decision == "BUY" and d.ai["dual_ai"]["trader1"]["invalidation"].startswith("a close below")
    assert d.invalidation == "a close below the 1.0985 swing low"


def test_the_traders_are_told_the_risk_engines_own_limits():
    from aitrader.risk.engine import RiskEngine
    lim = RiskEngine().trade_limits("EURUSD", 0.00012)
    assert lim["min_reward_risk"] == 1.2 and lim["min_stop_distance"] > 0.00012 / 0.25 - 1e-12
    c = desk_ctx()
    c.costs = {"total": 0.0002, "risk_engine_limits": lim}
    _, fake = think(scripted(), c)
    for call in fake.calls:
        assert packet_of(call["body"])["costs"]["risk_engine_limits"]["min_stop_distance"] == lim["min_stop_distance"]
    assert "min_stop_distance" in fake.calls[0]["body"]["messages"][0]["content"]


def deadlines(reply, within):
    """The wall-clock budget each call was given, by role."""
    brain, fake = desk(reply)
    c = desk_ctx()
    c.decide_within_s = within
    asked = {}
    real = brain.dual_ai.client.chat_json

    def spy(role, *a, **kw):
        asked[role] = kw.get("deadline_s")
        return real(role, *a, **kw)
    brain.dual_ai.client.chat_json = spy
    return brain.think(c, V).decision, asked, fake


def test_with_too_little_time_left_no_trader_is_asked_and_it_is_no_trade():
    # found live (2026-10-16): two agreements were refused as stale (933 s, 1103 s old) after the other pair's shadow
    # debate waited 420 s on a busy model. An answer that would come too late to execute is not asked for.
    d, asked, fake = deadlines(scripted(), within=10)
    assert d.decision == "NO_TRADE" and asked == {} and not fake.calls
    assert d.ai["dual_ai"]["consensus"]["rule"] == "TRADER1_UNAVAILABLE" and "too old to execute" in d.no_trade_reason


def test_every_call_ends_before_the_decision_would_be_too_old_and_the_shadow_debate_waits_briefly():
    d, asked, _ = deadlines(scripted(t1=("BUY", 80), t2=("SELL", 70)), within=300)
    assert d.decision == "NO_TRADE" and set(asked) == {"vision", "judge", "verifier"}
    assert 250 < asked["vision"] <= 300 and asked["judge"] <= 300  # never longer than is left
    assert asked["verifier"] <= 120  # measurement only: it never holds up the next decision long
    _, free, _ = deadlines(scripted(t1=("BUY", 80), t2=("SELL", 70)), within=None)
    assert free == {"vision": 420.0, "judge": 420.0, "verifier": 120.0}  # no known limit: the caps


def test_when_one_vision_model_answers_badly_another_trader_1_model_is_asked():
    # found in the live run (GBPUSD 11:45): the first vision model answered without JSON
    def t1(body):
        return "not json" if body["model"] == VISION else answer("SELL", BID, ASK, ATR, confidence=70)
    d, fake = think(scripted(trader1=t1, t2=("SELL", 66)))
    assert d.decision == "SELL" and d.ai["dual_ai"]["models"]["trader1"] == DEBATE
    call = d.ai["dual_ai"]["calls"][0]
    assert call["tried"][0]["model"] == VISION and call["tried"][0]["status"].startswith("INVALID")
    assert d.ai["dual_ai"]["models"]["trader2"] not in (DEBATE,)  # still a different model from Trader 1


# ── Trader 1 reads the chart's numbers when no vision model answers ─────

TEXT3 = "plain/text-d:free"


def numbers_desk(reply):
    from tests.openrouter_kit import CATALOG, model
    fake = FakeOpenRouter(reply, catalog=CATALOG + [model(TEXT3, image=False, ii=20)])
    brain = Brain(config=BrainConfig(llm_agents=(), parallel=False, decision_mode="dual_ai"), openrouter=client(fake))
    return brain, fake


def busy_vision(t1=("BUY", 70), vision=None, numbers=None):
    """Every request with the chart image fails; Trader 1 on the chart's numbers answers (or `numbers`)."""
    def t1_reply(body):
        if has_image(body):
            return vision(body) if vision else (503, {}, {"error": {"message": "overloaded"}})
        return numbers(body) if numbers else answer(t1[0], BID, ASK, ATR, confidence=t1[1])
    return t1_reply


def test_when_no_vision_model_answers_trader_1_reads_the_same_chart_as_numbers_on_a_text_model():
    # found in the live run of 2026-10-13: 23 of 40 decisions lost while every free vision model was busy
    brain, fake = numbers_desk(scripted(trader1=busy_vision(), t2=("BUY", 66)))
    d = brain.think(desk_ctx(), V).decision
    rec = d.ai["dual_ai"]
    assert d.decision == "BUY" and rec["consensus"]["rule"] == "AGREE" and rec["trader1_input"] == "numbers"
    assert rec["models"] == {"trader1": TEXT3, "trader2": TRADER}  # still two different models
    vision = {c["model"] for c in fake.calls if c["role"] == "trader1" and has_image(c["body"])}
    numbers = [c for c in fake.calls if c["role"] == "trader1" and not has_image(c["body"])]
    assert vision == {VISION, DEBATE} and [c["model"] for c in numbers] == [TEXT3]  # each asked; the new one once
    body = numbers[0]["body"]
    assert "could not be read" in body["messages"][0]["content"]
    assert packet_of(body)["chart_marks"] == packet_of(fake.calls[0]["body"])["chart_marks"]  # the same chart
    assert [c["role"] for c in rec["calls"]] == ["vision", "trader1_numbers", "judge"]
    assert not rec["calls"][0]["ok"] and rec["calls"][1]["ok"]


@pytest.mark.parametrize("status,payload,why", [
    (401, {"error": {"message": "invalid api key"}}, "KEY_REJECTED"),
    (429, {"error": {"message": "Rate limit exceeded: free-models-per-day"}}, "DAILY_QUOTA"),
])
def test_no_numbers_fallback_after_a_stop_another_model_would_not_fix(status, payload, why):
    brain, fake = numbers_desk(scripted(trader1=busy_vision(vision=lambda b: (status, {}, payload))))
    d = brain.think(desk_ctx(), V).decision
    rec = d.ai["dual_ai"]
    assert d.decision == "NO_TRADE" and rec["consensus"]["rule"] == "TRADER1_UNAVAILABLE" and why in d.no_trade_reason
    assert rec["trader1_input"] == "image" and len(rec["calls"]) == 1
    assert [c for c in fake.calls if not has_image(c["body"])] == []


def test_when_the_numbers_reply_is_unusable_too_it_is_no_trade_naming_both():
    brain, _ = numbers_desk(scripted(trader1=busy_vision(numbers=lambda b: "not json")))
    d = brain.think(desk_ctx(), V).decision
    assert d.decision == "NO_TRADE" and d.ai["dual_ai"]["consensus"]["rule"] == "TRADER1_UNAVAILABLE"
    assert "vision" in d.no_trade_reason and "on the chart's numbers: INVALID" in d.no_trade_reason



# ── an agreement uses levels the risk engine can accept, when one trader has them ──

LIM = {"min_reward_risk": 1.2, "min_stop_distance": 0.0003}


def lim_ctx():
    c = desk_ctx()
    c.costs = {**c.costs, "risk_engine_limits": LIM}
    return c


def test_when_the_more_confident_traders_levels_are_inside_the_limits_the_other_traders_own_are_used():
    # found live (2026-10-14): 27 of 51 agreements refused for their levels; in 13 the other trader's respected them
    tight = answer("BUY", BID, ASK, ATR, confidence=90, stop_atr=1.0, target_atr=1.0)  # reward:risk 1.0 < 1.2
    d, _ = think(scripted(trader1=tight, t2=("BUY", 70)), lim_ctx())
    rec = d.ai["dual_ai"]
    assert d.decision == "BUY" and rec["consensus"]["levels_from"] == "trader2" and "levels_reason" in rec["consensus"]
    assert d.stop_loss == pytest.approx(ASK - 1.2 * ATR) and d.take_profit == pytest.approx(ASK + 2.4 * ATR)  # as given


def test_the_more_confident_traders_levels_stay_when_they_fit_or_when_neither_does():
    d, _ = think(scripted(t1=("BUY", 90), t2=("BUY", 70)), lim_ctx())
    assert d.ai["dual_ai"]["consensus"]["levels_from"] == "trader1"  # both fit: confidence decides, as before
    tight1 = answer("BUY", BID, ASK, ATR, confidence=90, stop_atr=1.0, target_atr=1.0)
    tight2 = answer("BUY", BID, ASK, ATR, confidence=70, stop_atr=1.0, target_atr=1.1)
    d, _ = think(scripted(trader1=tight1, trader2=tight2), lim_ctx())
    assert d.decision == "BUY" and d.ai["dual_ai"]["consensus"]["levels_from"] == "trader1"  # the risk engine decides
    assert "levels_reason" not in d.ai["dual_ai"]["consensus"]
    d, _ = think(scripted(trader1=tight1, t2=("BUY", 70)))  # no published limits: no preference
    assert d.ai["dual_ai"]["consensus"]["levels_from"] == "trader1"


def test_fits_limits_reads_the_published_limits_at_the_executable_price():
    from aitrader.agents.dual_ai import fits_limits
    ok = answer("SELL", BID, ASK, ATR, stop_atr=1.0, target_atr=1.5)
    assert fits_limits(ok, PX, LIM) and fits_limits(ok, PX, None)
    assert not fits_limits(answer("SELL", BID, ASK, ATR, stop_atr=1.0, target_atr=1.1), PX, LIM)  # reward:risk 1.1
    assert not fits_limits(answer("SELL", BID, ASK, ATR, stop_atr=0.2, target_atr=0.5), PX, LIM)  # stop 0.0002 < 0.0003
