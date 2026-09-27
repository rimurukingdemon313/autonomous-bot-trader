"""The trading room: one team, several minds, discussing in turn and writing one joint decision.

Each member is a fake provider whose replies are scripted, so what each mind
saw, who spoke when, and what the team decided are known by construction.
"""

from __future__ import annotations

import json
import urllib.error

import pytest

from aitrader.agents.brain import Brain, BrainConfig
from aitrader.agents.trading_room import RoomConfig, TradingRoom, member_records
from aitrader.llm.provider import Endpoint, LLMClient, LLMConfig
from aitrader.memory.db import Database

from .test_agents import V, analog, ctx

MEMBERS = ("groq", "gemini", "openrouter", "bytez")


def trade(action="BUY", stop=1.0985, target=1.1040, tf="H4", **kw):
    return {"action": action, "timeframe": tf, "stop": stop, "target": target, "max_hold_hours": 36,
            "thesis": f"{action} idea", "invalidation": "x", "memory_used": "none", **kw}


NONE = {"action": "NO_TRADE", "thesis": "nothing clean here yet"}


class Room:
    """Scripted providers. `speak`: member -> reply (dict, a callable of the packet, or an HTTP status)."""

    def __init__(self, speak, joint=None):
        self.speak, self.joint = speak, joint
        self.calls: list[tuple[str, str, dict]] = []

    def transport(self, url, headers, body, timeout):
        member = url.split("//")[1].split(".")[0]
        system, user = body["messages"][0]["content"], json.loads(body["messages"][1]["content"])
        phase = "joint" if "JOINT DECISION" in system else "speak"
        self.calls.append((member, phase, user))
        reply = self.joint if phase == "joint" else self.speak.get(member)
        reply = reply(user) if callable(reply) else reply
        if isinstance(reply, int):
            raise urllib.error.HTTPError(url, reply, "scripted failure", {}, None)
        return {"choices": [{"message": {"content": json.dumps(reply)}}]}

    def brain(self, members=MEMBERS, **room):
        cfg = LLMConfig(providers=tuple(Endpoint(m, f"https://{m}.test/v1", "k", f"{m}-model") for m in members))
        return Brain(llm=LLMClient(cfg, self.transport),
                     config=BrainConfig(llm_agents=(), parallel=False, decision_mode="trading_room",
                                        room=RoomConfig(**room)))

    def spoke(self):
        return [m for m, p, _ in self.calls if p == "speak"]


def live_ctx(**kw):
    c = ctx(analogs={"T1:BUY": analog("T1:BUY", 0.1, 0.05)}, **kw)
    c.mode = "PAPER"
    return c


def test_each_mind_reads_everything_said_before_it_and_the_team_writes_one_decision():
    room = Room(speak={"groq": trade(), "gemini": trade(stop=1.0980, to_team="agree, but the stop belongs under the swing"),
                       "openrouter": NONE, "bytez": trade(stop=1.0980, target=1.1050, to_team="and the target can reach 1.1050")},
                joint=trade(stop=1.0980, target=1.1050, thesis="team: H4 pullback, stop under the swing"))
    d = room.brain().think(live_ctx(), V).decision
    r = d.independent_evidence["room"]
    order = r["order"]
    heard = [[s["member"] for s in u["discussion"]] for m, p, u in room.calls if p == "speak"]
    assert heard == [order[:i] for i in range(4)]  # the n-th mind heard the n-1 before it, in order
    assert d.decision == "BUY" and (d.stop_loss, d.take_profit) == (1.0980, 1.1050)  # the team's plan
    joint_user = next(u for m, p, u in room.calls if p == "joint")
    assert [s["member"] for s in joint_user["discussion"]] == order  # the joint decision read everyone
    assert r["head"] == order[0] and r["joint"]["action"] == "BUY"
    assert d.versions["trading_room"].startswith("trading-room-2.")


def test_the_speaking_order_rotates_between_decisions():
    orders = {tuple(TradingRoom.speaking_order(list(MEMBERS), "EURUSD", t)) for t in range(0, 4 * 60, 60)}
    assert len(orders) == 4 and all(sorted(o) == sorted(MEMBERS) for o in orders)


def test_when_every_mind_sees_nothing_no_joint_call_is_made():
    room = Room(speak={m: NONE for m in MEMBERS})
    d = room.brain().think(live_ctx(), V).decision
    assert d.decision == "NO_TRADE" and "saw nothing worth taking" in d.no_trade_reason
    assert [p for _, p, _ in room.calls] == ["speak"] * 4


def test_a_mind_can_be_convinced_by_what_it_heard():
    def persuadable(user):
        return trade() if any(s["action"] == "BUY" for s in user["discussion"]) else NONE

    room = Room(speak={"groq": trade(), "gemini": persuadable, "openrouter": persuadable, "bytez": persuadable},
                joint=trade())
    d = room.brain().think(live_ctx(), V).decision
    finals = d.independent_evidence["room"]["final"]
    first = d.independent_evidence["room"]["order"][0]
    assert d.decision == "BUY"
    if first != "groq":  # whoever spoke before groq had heard no BUY yet
        assert finals[first]["action"] == "NO_TRADE"
    assert finals[d.independent_evidence["room"]["order"][-1]]["action"] == "BUY"  # the last had heard groq


def test_the_joint_plan_is_checked_and_never_repaired():
    room = Room(speak={m: trade() for m in MEMBERS}, joint=trade(stop=1.1010))  # a BUY stop above the entry
    d = room.brain().think(live_ctx(), V).decision
    assert d.decision == "NO_TRADE" and "never repaired" in d.no_trade_reason and "wrong side" in d.no_trade_reason


def test_the_team_may_decide_on_no_trade():
    room = Room(speak={m: trade() for m in MEMBERS}, joint={**NONE, "thesis": "on reflection the H4 is overextended"})
    d = room.brain().think(live_ctx(), V).decision
    assert d.decision == "NO_TRADE" and "overextended" in d.no_trade_reason


def test_a_failing_provider_is_skipped_never_replaced_by_another_models_voice():
    room = Room(speak={"groq": 503, "gemini": trade(), "openrouter": trade(), "bytez": NONE}, joint=trade())
    d = room.brain(head="groq").think(live_ctx(), V).decision
    assert d.decision == "BUY"
    r = d.independent_evidence["room"]
    assert "groq" not in r["final"] and any(x["member"] == "groq" and x["status"] == "HTTP_ERROR" for x in r["discussion"])
    assert r["head"] != "groq"  # the configured writer was absent: the first mind present writes it
    assert [p for m, p, _ in room.calls if m == "groq"] == ["speak", "speak"]  # one retry on 503, then skipped
    assert all(all(s["member"] != "groq" for s in u["discussion"]) for _, _, u in room.calls)


def test_nobody_answering_fails_closed():
    room = Room(speak={m: 500 for m in MEMBERS})
    d = room.brain().think(live_ctx(), V).decision
    assert d.decision == "NO_TRADE" and "no member of the team answered" in d.no_trade_reason


def test_a_mind_speaks_only_through_its_own_provider():
    room = Room(speak={m: trade() for m in MEMBERS}, joint=trade())
    room.brain().think(live_ctx(), V)
    order = [m for m, p, _ in room.calls if p == "speak"]
    heard_self = [u["you"] for m, p, u in room.calls if p == "speak"]
    assert order == heard_self  # each request went to the provider of the mind speaking


def test_no_model_is_called_when_trading_is_paused_or_the_data_is_bad():
    room = Room(speak={m: trade() for m in MEMBERS})
    c = live_ctx()
    c.trading_allowed = False
    assert room.brain().think(c, V).decision.decision == "NO_TRADE"
    assert room.brain().think(live_ctx(flags=["latest bar closed 300 minutes ago"]), V).decision.decision == "NO_TRADE"
    assert room.calls == []


def test_a_validated_lesson_blocks_the_teams_trade():
    class Knowledge:
        def lessons_matching(self, family, reg, vol, direction, t):
            return [{"lesson_id": "L:room-buy", "version": 1, "statement": "LLM_TRADER BUY here loses"}] \
                if direction == 1 else []

        def family_regime_stats(self, *a):
            return None

    room = Room(speak={m: trade() for m in MEMBERS}, joint=trade())
    d = room.brain().think(live_ctx(knowledge=Knowledge()), V).decision
    assert d.decision == "NO_TRADE" and "L:room-buy" in d.no_trade_reason


def test_it_refuses_to_be_backtested():
    room = Room(speak={})
    with pytest.raises(ValueError, match="cannot be backtested"):
        room.brain().think(ctx(analogs={"T1:BUY": analog("T1:BUY", 0.1, 0.05)}), V)


@pytest.mark.parametrize("kw", [{"size": 0}, {"size": 9}])
def test_an_impossible_room_is_refused(kw):
    with pytest.raises(ValueError):
        RoomConfig(**kw)


def test_each_minds_record_counts_the_trades_it_argued_for_separately(tmp_path):
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
