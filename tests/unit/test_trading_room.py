"""The trading room: several models hunt, debate, and a head trader picks; the rules around them are code.

Each member is a fake provider whose replies are scripted per phase, so every
room outcome, agreement, a split, a missing quorum, a failing provider, a head
that tries to overstep, is constructed and its correct answer known.
"""

from __future__ import annotations

import json
import urllib.error

import pytest

from aitrader.agents.brain import Brain, BrainConfig
from aitrader.agents.trading_room import RoomConfig, member_records
from aitrader.llm.provider import Endpoint, LLMClient, LLMConfig
from aitrader.memory.db import Database

from .test_agents import V, analog, ctx, regime

MEMBERS = ("groq", "gemini", "openrouter", "bytez")


def trade(action="BUY", stop=1.0985, target=1.1040, tf="H4", **kw):
    return {"action": action, "timeframe": tf, "stop": stop, "target": target, "max_hold_hours": 36,
            "thesis": f"{action} idea", "invalidation": "x", "memory_used": "none", **kw}


NONE = {"action": "NO_TRADE", "thesis": "waiting for a retest of 1.0950"}
SELL = trade("SELL", stop=1.1030, target=1.0970)


class Room:
    """Scripted providers. `hunt`/`debate`: member -> reply (dict, or an HTTP status to fail with)."""

    def __init__(self, hunt, debate=None, head=None):
        self.hunt, self.debate, self.head = hunt, debate or {}, head
        self.calls: list[tuple[str, str]] = []

    def transport(self, url, headers, body, timeout):
        member = url.split("//")[1].split(".")[0]
        system, user = body["messages"][0]["content"], json.loads(body["messages"][1]["content"])
        phase = "head" if "HEAD TRADER" in system else "debate" if "round1" in user else "hunt"
        self.calls.append((member, phase))
        if phase == "head":
            reply = self.head
        else:
            script = self.hunt if phase == "hunt" else self.debate
            reply = script.get(member, self.hunt.get(member)) if phase == "debate" else script.get(member)
        if isinstance(reply, int):
            raise urllib.error.HTTPError(url, reply, "scripted failure", {}, None)
        return {"choices": [{"message": {"content": json.dumps(reply)}}]}

    def brain(self, members=MEMBERS, **room):
        cfg = LLMConfig(providers=tuple(Endpoint(m, f"https://{m}.test/v1", "k", f"{m}-model") for m in members))
        return Brain(llm=LLMClient(cfg, self.transport),
                     config=BrainConfig(llm_agents=(), parallel=False, decision_mode="trading_room",
                                        room=RoomConfig(**room)))

    def phases(self, phase):
        return sorted(m for m, p in self.calls if p == phase)


def live_ctx(**kw):
    c = ctx(analogs={"T1:BUY": analog("T1:BUY", 0.1, 0.05)}, **kw)
    c.mode = "PAPER"
    return c


def test_a_supported_trade_is_the_picked_members_trade_verbatim():
    room = Room(hunt={"groq": trade(), "gemini": trade(stop=1.0980, target=1.1050), "openrouter": NONE, "bytez": NONE},
                debate={"openrouter": trade(stop=1.0980, target=1.1050, critique="groq's stop is inside the noise")},
                head={"decision": "TRADE", "pick": "gemini", "reason": "wider stop behind the swing", "stop": 1.2})
    d = room.brain().think(live_ctx(), V).decision
    assert d.decision == "BUY" and d.family == "LLM_TRADER"
    assert (d.stop_loss, d.take_profit) == (1.0980, 1.1050)  # gemini's levels; the head's "stop" is ignored
    r = d.independent_evidence["room"]
    assert r["picked"] == "gemini" and r["head"] == "groq" and r["quorum"] == 2
    assert r["final"]["openrouter"]["critique"] == "groq's stop is inside the noise"
    assert d.versions["trading_room"].startswith("trading-room-")
    assert room.phases("hunt") == room.phases("debate") == sorted(MEMBERS) and room.phases("head") == ["groq"]


def test_when_nobody_finds_a_trade_the_room_stops_after_the_hunt():
    room = Room(hunt={m: NONE for m in MEMBERS})
    d = room.brain().think(live_ctx(), V).decision
    assert d.decision == "NO_TRADE" and "no trader found a trade" in d.no_trade_reason
    assert "retest of 1.0950" in d.no_trade_reason  # it says what it is waiting for
    assert [p for _, p in room.calls] == ["hunt"] * 4  # nothing more is spent


def test_a_room_split_between_buy_and_sell_is_no_trade_and_the_head_is_not_asked():
    room = Room(hunt={"groq": trade(), "gemini": trade(), "openrouter": SELL, "bytez": SELL})
    d = room.brain().think(live_ctx(), V).decision
    assert d.decision == "NO_TRADE" and "split" in d.no_trade_reason
    assert room.phases("head") == []


def test_a_lone_voice_below_the_quorum_does_not_trade():
    room = Room(hunt={"groq": trade(), "gemini": NONE, "openrouter": NONE, "bytez": NONE})
    d = room.brain().think(live_ctx(), V).decision
    assert d.decision == "NO_TRADE" and "only 1 of 4" in d.no_trade_reason and "quorum is 2" in d.no_trade_reason
    assert room.phases("head") == []


def test_the_debate_can_win_members_over():
    room = Room(hunt={"groq": trade(), "gemini": NONE, "openrouter": NONE, "bytez": NONE},
                debate={"gemini": trade(critique="groq is right, the H4 pullback held")},
                head={"decision": "TRADE", "pick": "groq", "reason": "clean"})
    d = room.brain().think(live_ctx(), V).decision
    assert d.decision == "BUY" and sorted(json.loads(json.dumps(d.independent_evidence["room"]["final"]))) == sorted(MEMBERS)


def test_an_unusable_trade_is_an_abstention_never_repaired():
    wrong_side = trade(stop=1.1010)  # a BUY stop above the entry
    room = Room(hunt={"groq": trade(), "gemini": wrong_side, "openrouter": NONE, "bytez": NONE},
                head={"decision": "TRADE", "pick": "groq", "reason": "x"})
    d = room.brain().think(live_ctx(), V).decision
    assert d.decision == "NO_TRADE" and "only 1 of 4" in d.no_trade_reason
    assert "wrong side" in d.independent_evidence["room"]["final"]["gemini"]["dropped"]


def test_the_head_cannot_pick_a_trader_who_does_not_support_the_trade():
    room = Room(hunt={"groq": trade(), "gemini": trade(), "openrouter": NONE, "bytez": NONE},
                head={"decision": "TRADE", "pick": "bytez", "reason": "I prefer bytez"})
    d = room.brain().think(live_ctx(), V).decision
    assert d.decision == "NO_TRADE" and "head trader could not decide" in d.no_trade_reason


def test_the_head_may_decline():
    room = Room(hunt={"groq": trade(), "gemini": trade(), "openrouter": NONE, "bytez": NONE},
                head={"decision": "NO_TRADE", "pick": None, "reason": "target runs into the daily high"})
    d = room.brain().think(live_ctx(), V).decision
    assert d.decision == "NO_TRADE" and "daily high" in d.no_trade_reason


def test_a_failing_provider_is_absent_never_replaced_by_another_models_voice():
    room = Room(hunt={"groq": 503, "gemini": trade(), "openrouter": trade(), "bytez": NONE},
                head={"decision": "TRADE", "pick": "gemini", "reason": "x"})
    d = room.brain().think(live_ctx(), V).decision
    assert d.decision == "BUY"
    r = d.independent_evidence["room"]
    assert r["round1"]["groq"]["status"] == "HTTP_ERROR" and "groq" not in r["final"]
    assert r["head"] == "gemini"  # the configured head was absent: the first present member chairs
    assert [p for m, p in room.calls if m == "groq"] == ["hunt", "hunt"]  # one retry on 503, then absent


def test_with_one_member_left_the_quorum_is_capped_by_who_is_present():
    room = Room(hunt={"groq": trade()}, head={"decision": "TRADE", "pick": "groq", "reason": "x"})
    d = room.brain(members=("groq",), size=1, quorum=1).think(live_ctx(), V).decision
    assert d.decision == "BUY" and d.independent_evidence["room"]["quorum"] == 1


def test_no_model_is_called_when_trading_is_paused_or_the_market_is_blocked():
    room = Room(hunt={m: trade() for m in MEMBERS})
    c = live_ctx()
    c.trading_allowed = False
    assert room.brain().think(c, V).decision.decision == "NO_TRADE"
    assert room.brain().think(live_ctx(rg=regime(familiar=False)), V).decision.decision == "NO_TRADE"
    assert room.calls == []


def test_a_validated_lesson_blocks_the_rooms_trade():
    class Knowledge:
        def lessons_matching(self, family, reg, vol, direction, t):
            return [{"lesson_id": "L:room-buy", "version": 1, "statement": "LLM_TRADER BUY here loses"}] \
                if direction == 1 else []

        def family_regime_stats(self, *a):
            return None

    room = Room(hunt={"groq": trade(), "gemini": trade(), "openrouter": NONE, "bytez": NONE})
    d = room.brain().think(live_ctx(knowledge=Knowledge()), V).decision
    assert d.decision == "NO_TRADE" and "L:room-buy" in d.no_trade_reason and room.phases("head") == []


def test_it_refuses_to_be_backtested():
    room = Room(hunt={})
    with pytest.raises(ValueError, match="cannot be backtested"):
        room.brain().think(ctx(analogs={"T1:BUY": analog("T1:BUY", 0.1, 0.05)}), V)


@pytest.mark.parametrize("kw", [{"size": 0}, {"size": 9}, {"size": 2, "quorum": 3}, {"quorum": 0}])
def test_an_impossible_room_is_refused(kw):
    with pytest.raises(ValueError):
        RoomConfig(**kw)


def test_each_members_record_counts_the_trades_it_backed_separately(tmp_path):
    db = Database(tmp_path / "r.db")
    finals = [({"groq": "BUY", "gemini": "BUY", "bytez": "NO_TRADE"}, 1.5),
              ({"groq": "BUY", "gemini": "NO_TRADE", "bytez": "NO_TRADE"}, -1.0)]
    for i, (final, r) in enumerate(finals):
        dec = {"id": f"d{i}", "decision": "BUY", "family": "LLM_TRADER",
               "independent_evidence": {"room": {"final": {m: {"action": a} for m, a in final.items()}}}}
        db.append("decisions", {"id": f"d{i}", "symbol": "EURUSD", "timeframe": "H4", "decision": "BUY",
                                "mode": "PAPER", "payload": dec})
        db.append("trades", {"position_id": f"p{i}", "decision_id": f"d{i}", "symbol": "EURUSD", "r": r,
                             "payload": {"decision": dec}})
    rec = member_records(db)
    assert rec["groq"]["supported"] == {"trades": 2, "win_rate": 0.5, "avg_R": 0.25, "sample": "insufficient"}
    assert rec["gemini"]["supported"]["trades"] == 1 and rec["gemini"]["stood_aside"]["avg_R"] == -1.0
    assert rec["bytez"]["supported"] == {"trades": 0}
