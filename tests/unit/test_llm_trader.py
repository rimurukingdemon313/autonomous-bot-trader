"""The language-model trader: what it may decide, what makes it fail closed, and its memory.

The model is a fake transport whose replies are known in advance, so every
scenario, from sound trades to broken replies, is constructed.
"""

from __future__ import annotations

import json

import numpy as np
import pytest

from aitrader.agents.brain import Brain, BrainConfig
from aitrader.agents.llm_trader import multi_timeframe
from aitrader.backtest.runner import epoch
from aitrader.llm.provider import LLMClient, LLMConfig
from aitrader.memory.db import Database
from aitrader.memory.trade_memory import TradeMemory

from .test_agents import V, analog, ctx, regime

CFG = LLMConfig("openai_compatible", "https://example.test/v1", "k", "m1")


def fake(reply, calls):
    def t(url, headers, body, timeout):
        calls.append(body)
        content = reply(body) if callable(reply) else reply
        return {"choices": [{"message": {"content": content}}], "usage": {"total_tokens": 10}}
    return t


def trader(reply, calls, **cfg):
    return Brain(llm=LLMClient(CFG, fake(reply, calls)),
                 config=BrainConfig(llm_agents=(), parallel=False, decision_mode="llm_trader", **cfg))


def live_ctx(**kw):
    c = ctx(analogs={"T1:BUY": analog("T1:BUY", 0.1, 0.05)}, **kw)
    c.mode = "PAPER"
    return c


BUY = json.dumps({"action": "BUY", "timeframe": "H4", "stop": 1.0985, "target": 1.1040, "max_hold_hours": 36,
                  "thesis": "H4 uptrend, pullback held", "invalidation": "H4 close below 1.0985",
                  "memory_used": "last EURUSD loss: I entered late; this entry is at the pullback"})


def test_a_sound_proposal_becomes_a_decision_the_risk_engine_will_size():
    calls = []
    d = trader(BUY, calls).think(live_ctx(), V).decision
    assert d.decision == "BUY" and d.family == "LLM_TRADER" and d.timeframe == "H4"
    assert d.entry == pytest.approx(1.10006) and d.stop_loss == 1.0985 and d.take_profit == 1.1040
    assert d.max_hold_hours == 36 and "llm_trader" in d.versions
    assert d.expected_R is None and d.probability is None  # never a model's self-reported number as evidence
    assert "memory used" in d.supporting_evidence[0]["claim"]
    assert len(calls) == 1 and "memory" in json.loads(calls[0]["messages"][1]["content"])


@pytest.mark.parametrize("reply,why", [
    ("not json at all", "rejected"),
    (json.dumps({"action": "BUY", "timeframe": "H4", "stop": 1.1010, "target": 1.1040, "max_hold_hours": 10,
                 "thesis": "x"}), "wrong side"),
    (json.dumps({"action": "BUY", "timeframe": "H4", "stop": 1.0999, "target": 1.1040, "max_hold_hours": 10,
                 "thesis": "x"}), "outside"),  # a 0.07-ATR stop is noise, not a stop
    (json.dumps({"action": "BUY", "timeframe": "M1", "stop": 1.0985, "target": 1.1040, "max_hold_hours": 10,
                 "thesis": "x"}), "rejected"),
    (json.dumps({"action": "YOLO"}), "rejected"),
    (json.dumps({"action": "SELL", "timeframe": "H1", "stop": 1.1030, "target": 1.0970, "max_hold_hours": 9999,
                 "thesis": "x"}), "rejected"),
])
def test_any_broken_or_unsafe_reply_is_no_trade_and_never_repaired(reply, why):
    d = trader(reply, []).think(live_ctx(), V).decision
    assert d.decision == "NO_TRADE" and why in d.no_trade_reason


def test_a_market_wide_block_stops_the_decision_before_the_model_is_paid():
    calls = []
    d = trader(BUY, calls).think(live_ctx(rg=regime(familiar=False)), V).decision
    assert d.decision == "NO_TRADE" and "before consulting the model" in d.no_trade_reason
    assert calls == []


def test_when_trading_is_paused_the_model_is_not_consulted():
    calls = []
    c = live_ctx()
    c.trading_allowed = False
    assert trader(BUY, calls).think(c, V).decision.decision == "NO_TRADE"
    assert calls == []


def test_without_a_configured_model_it_fails_closed():
    b = Brain(llm=None, config=BrainConfig(llm_agents=(), parallel=False, decision_mode="llm_trader"))
    d = b.think(live_ctx(), V).decision
    assert d.decision == "NO_TRADE" and "no language model is configured" in d.no_trade_reason


def test_it_refuses_to_be_backtested():
    c = ctx(analogs={"T1:BUY": analog("T1:BUY", 0.1, 0.05)})  # mode BACKTEST
    with pytest.raises(ValueError, match="cannot be backtested"):
        trader(BUY, []).think(c, V)


def test_a_validated_lesson_about_its_own_trades_blocks_the_repeat():
    class Knowledge:
        def lessons_matching(self, family, reg, vol, direction, t):
            return [{"lesson_id": "L:llm-buy-trend", "version": 2, "statement": "LLM_TRADER BUY in TRENDING_UP loses"}] \
                if (family, direction) == ("LLM_TRADER", 1) else []

        def family_regime_stats(self, *a):
            return None

    d = trader(BUY, []).think(live_ctx(knowledge=Knowledge()), V).decision
    assert d.decision == "NO_TRADE" and "L:llm-buy-trend" in d.no_trade_reason


def test_an_unknown_decision_mode_is_refused_not_defaulted():
    with pytest.raises(ValueError, match="refused"):
        BrainConfig(decision_mode="yolo")


def test_the_timeframes_it_reads_contain_only_completed_bars():
    from tests.integration.test_pipeline import market
    h1 = market("EURUSD", epoch(2009, 1, 5), 24 * 40, 1, 1.3)
    as_of = int(h1.available_at[-1]) - 1800  # mid-way through the last hour: that bar is still forming
    visible = h1.take(slice(0, int(np.searchsorted(h1.available_at, as_of, side="right"))))
    mtf = multi_timeframe(visible, as_of)
    assert set(mtf) == {"H1", "H4", "D1"}
    last_h4 = mtf["H4"]["bars"][-1]
    assert mtf["H1"]["close"] == pytest.approx(float(visible.mid_close[-1]))
    assert last_h4 and mtf["D1"]["bars"]  # completed higher-timeframe bars exist, and nothing later than as_of does


def test_memory_brings_back_its_own_losses_with_its_own_reflections(tmp_path):
    db = Database(tmp_path / "m.db")
    for i, (sym, r) in enumerate([("EURUSD", -1.0), ("GBPUSD", 1.4), ("EURUSD", -0.8)]):
        rec = {"decision": {"id": f"d{i}", "family": "LLM_TRADER", "thesis": f"idea {i}", "regime": {"label": "RANGING"}},
               "position": {"side": "BUY", "opened": 1000 + i, "entry": 1.1, "stop": 1.09, "target": 1.12},
               "exit": {"reason": "STOP" if r < 0 else "TARGET"}, "postmortem": {"cause": "ENTRY_TIMING"}}
        db.append("trades", {"position_id": f"p{i}", "decision_id": f"d{i}", "symbol": sym, "r": r, "payload": rec})
    db.append("reflections", {"payload": {"kind": "trade", "decision_id": "d2", "text": "entered into resistance",
                                          "lesson": "wait for the retest"}})
    brief = TradeMemory(db).brief("EURUSD", "RANGING", 10**10)
    assert brief["my_record"] == {"trades": 3, "win_rate": 0.333, "avg_R": -0.133, "total_R": -0.4, "sample": "insufficient"}
    losses = [v for v in brief["relevant_past_trades"] if v["R"] < 0]
    assert len(losses) == 2 and any(v["my_lesson"] == "wait for the retest" for v in losses)
