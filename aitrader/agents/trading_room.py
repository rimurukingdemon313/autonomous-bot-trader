"""The trading room: several language models, each from its own provider, hunt for a trade together.

Selected with DECISION_MODE=trading_room (PAPER or DEMO only). One decision
for one instrument runs in three steps:

1. HUNT. Every member reads the same market packet (M5/M15/H1/H4/D1 completed bars,
   quote, account, the quantitative agents, the shared trade memory) and,
   without seeing the others, decides freely: a trade of its own choosing,
   or none.
2. DEBATE. If anyone wants a trade, every member reads everyone's views and
   gives a FINAL position: keep, change, take another's trade, or stand
   aside. If nobody wants one, the room stops here and nothing more is spent.
3. HEAD. The head trader reads the final positions, the critiques and each
   member's track record, and takes ONE member's trade, or none. The
   members may disagree, even on direction: weighing that is the head's job.

What is fixed in code, not in any prompt:

- a member speaks only through its own provider (`only=`); a member whose
  provider fails is absent, never replaced by another model's voice;
- every final trade passes the same checks as the single trader: wrong-side
  or absurdly far stops are dropped, never repaired;
- a direction held by fewer traders than AI_ROOM_QUORUM (default 1, capped
  by the members present) is not eligible;
- the head can only pick a supporter's trade verbatim: it cannot invent a
  trade, move a level, or change a size (no one here sizes anything);
- a validated lesson against the chosen side -> NO_TRADE;
- the same pre-model gates as the single trader: paused, stopped, a
  market-wide BLOCKING objection, no quote -> no model is called.

Everything the room said is recorded on the decision (`independent_evidence
["room"]`), so each member's forward record can be measured separately.
"""

from __future__ import annotations

import os
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass

from ..decision.synthesis import Decision, decision_id
from .llm_trader import (
    FAMILY, LLM_TRADER_VERSION, agent_digest, lesson_block, level_problem, market_packet, no_trade_decision,
    pre_model_block, trade_decision, validate_proposal,
)
from .types import MarketContext

#: 1.1.0: M5/M15 bars in the packet and as trade timeframes.
#: 1.2.0 (owner: "they control themselves"): neutral prompts that steer no style; a BUY/SELL
#: split goes to the head instead of forcing NO_TRADE; the default quorum is 1.
ROOM_VERSION = "trading-room-1.2.0"

HUNT = """You are {name}, one of {n} professional discretionary FX traders in a trading room. Each of you
runs on a different AI model; your own record is tracked separately from the others'.
You decide for ONE instrument, now. The decision time is {time}; treat it as the present.
Use ONLY the data in the JSON: completed bars on M5 and M15 (when present), H1, H4 and D1, the live quote, the
account, the quantitative agents' findings (information, not orders), and the room's memory of its past trades
(losses first) with the reflections written on them. Do not use any knowledge of prices or events after the
decision time.

Read the market your own way. Every choice is yours: whether to trade at all, the direction, the timeframe,
your style, where the stop and the target go, how long to hold. No style, quota or setup is required of you.
You have not seen the other traders' views yet. Use the memory as you see fit and say which part you used.
You do NOT size positions: a risk engine does that and may refuse a trade.

Reply with ONE JSON object only:
{{"action": "BUY|SELL|NO_TRADE", "timeframe": "M5|M15|H1|H4|D1", "stop": <price or null>, "target": <price or null>,
  "max_hold_hours": <1-336 or null>, "thesis": "your reasoning, at most 4 sentences",
  "invalidation": "what would prove you wrong", "memory_used": "which past trade or lesson you applied, or none"}}"""

DEBATE = """You are {name} in the same trading room. The decision time is still {time}.
"round1" in the JSON holds every trader's first view, yours included. Discuss them as you see fit, then
give your FINAL position: keep yours, change it, take another trader's trade (copy its levels), or NO_TRADE.
It is entirely your call. The same data rules apply: nothing after the decision time.

Reply with ONE JSON object only, the same fields as before plus a critique:
{{"action": "BUY|SELL|NO_TRADE", "timeframe": "M5|M15|H1|H4|D1", "stop": <price or null>, "target": <price or null>,
  "max_hold_hours": <1-336 or null>, "thesis": "your final case, at most 4 sentences",
  "invalidation": "what would prove you wrong", "memory_used": "...",
  "critique": "what you think of the other views, at most 3 sentences"}}"""

HEAD = """You are the HEAD TRADER of the room. The decision time is {time}.
"eligible" holds the traders' final trades (they may disagree, even on direction); "others" holds the
traders who chose not to trade or whose trade could not be used, and why; "track_records" holds each
trader's forward record so far (small samples say little). The decision is yours: take ONE of the
eligible trades exactly as proposed, or none. You cannot change a level or invent a trade.

Reply with ONE JSON object only:
{{"decision": "TRADE|NO_TRADE", "pick": "<trader name from eligible, or null>", "reason": "at most 3 sentences"}}"""


@dataclass(frozen=True)
class RoomConfig:
    size: int = 4          # members taken from AI_PROVIDERS, in order
    quorum: int = 1        # traders who must hold a trade's direction for it to be eligible (capped by those present)
    head: str = ""         # provider name of the head trader; default the first member

    def __post_init__(self) -> None:
        if not 1 <= self.size <= 8:
            raise ValueError("AI_ROOM_SIZE must be 1..8")
        if not 1 <= self.quorum <= self.size:
            raise ValueError("AI_ROOM_QUORUM must be between 1 and AI_ROOM_SIZE")

    @classmethod
    def from_env(cls, env: dict | None = None) -> "RoomConfig":
        e = os.environ if env is None else env
        return cls(size=int(e.get("AI_ROOM_SIZE", "4")), quorum=int(e.get("AI_ROOM_QUORUM", "1")),
                   head=e.get("AI_ROOM_HEAD", "").strip().lower())


def validate_debate(d: dict) -> str | None:
    problem = validate_proposal(d)
    if problem:
        return problem
    c = d.get("critique")
    return None if c is None or isinstance(c, str) else "critique must be text"


def validate_head(eligible: set[str]):
    def check(d: dict) -> str | None:
        if d.get("decision") not in ("TRADE", "NO_TRADE"):
            return "decision must be TRADE or NO_TRADE"
        if d["decision"] == "TRADE" and d.get("pick") not in eligible:
            return f"pick must be one of {sorted(eligible)}"
        return None
    return check


def _view(p: dict | None, model: str | None = None, status: str = "OK") -> dict:
    if p is None:
        return {"status": status, "model": model}
    return {"status": status, "model": model, "action": p.get("action"), "timeframe": p.get("timeframe"),
            "stop": p.get("stop"), "target": p.get("target"), "max_hold_hours": p.get("max_hold_hours"),
            "thesis": str(p.get("thesis") or "")[:400], "invalidation": str(p.get("invalidation") or "")[:200],
            "memory_used": str(p.get("memory_used") or "")[:200],
            **({"critique": str(p.get("critique"))[:300]} if p.get("critique") else {})}


class TradingRoom:
    def __init__(self, llm, config: RoomConfig | None = None) -> None:
        self.llm = llm
        self.config = config or RoomConfig()
        self._pool = ThreadPoolExecutor(max_workers=8, thread_name_prefix="room")

    def members(self) -> list[str]:
        if self.llm is None or not self.llm.config.enabled:
            return []
        return [ep.name for ep in self.llm.config.endpoints()][: self.config.size]

    def _ask(self, members, fn) -> dict:
        return dict(zip(members, self._pool.map(fn, members)))

    def decide(self, ctx: MarketContext, reports: dict, versions: dict, llm_opinions=None) -> Decision:
        if ctx.mode == "BACKTEST":
            raise ValueError("the trading room cannot be backtested honestly: the models may know "
                             "what happened after the decision time")
        v = {**versions, "llm_trader": LLM_TRADER_VERSION, "trading_room": ROOM_VERSION}
        did = decision_id(ctx.symbol, ctx.timeframe, ctx.t, ctx.mode, v)
        agents = agent_digest(reports)
        members = self.members()
        room: dict = {"members": members, "quorum": None, "head": None, "round1": {}, "final": {},
                      "picked": None, "outcome": None}

        def no_trade(reason: str, contra=None) -> Decision:
            room["outcome"] = reason
            return no_trade_decision(ctx, did, v, agents, reason, contra, evidence={"room": room})

        blocked = pre_model_block(ctx, reports, self.llm)
        if blocked:
            return no_trade(blocked[0], contra=blocked[1])
        packet = market_packet(ctx, reports)
        n = len(members)

        # 1. HUNT: independent, in parallel, each through its own provider.
        def hunt(m):
            return self.llm.complete_json(f"room:{m}", HUNT.format(name=m, n=n, time=packet["decision_time"]),
                                          packet, validate_proposal, cache_key=f"{ctx.symbol}|{ctx.t}|hunt",
                                          only=m)
        first = self._ask(members, hunt)
        present = [m for m in members if first[m].ok]
        room["round1"] = {m: _view(first[m].data, first[m].model, first[m].status) for m in members}
        if not present:
            return no_trade("no trader in the room answered (" +
                            ", ".join(f"{m}: {first[m].status}" for m in members) + "): failing closed")
        quorum = min(self.config.quorum, len(present))
        room["quorum"] = quorum
        if all(first[m].data["action"] == "NO_TRADE" for m in present):
            waiting = "; ".join(f"{m}: {str(first[m].data.get('thesis') or '')[:160]}" for m in present)
            return no_trade(f"no trader wanted a trade ({len(present)} of {n} present). Their views: {waiting}")

        # 2. DEBATE: everyone sees round 1 and gives a final position.
        round1 = {m: room["round1"][m] for m in present}

        def debate(m):
            return self.llm.complete_json(f"room:{m}", DEBATE.format(name=m, time=packet["decision_time"]),
                                          {**packet, "you": m, "round1": round1}, validate_debate,
                                          cache_key=f"{ctx.symbol}|{ctx.t}|debate", only=m)
        second = self._ask(present, debate)
        finals: dict[str, dict] = {}
        for m in present:
            res = second[m]
            p = res.data if res.ok else first[m].data  # a member that cannot debate keeps its first position
            view = _view(p, res.model if res.ok else first[m].model, "OK" if res.ok else f"KEPT_ROUND1 ({res.status})")
            if p["action"] != "NO_TRADE":
                problem = level_problem(ctx, p)
                if problem:
                    view["dropped"] = problem  # an unusable trade is an abstention, never repaired
                else:
                    finals[m] = p
            room["final"][m] = view

        if not finals:
            return no_trade("after the debate no trader holds a usable trade")
        # A direction is eligible when at least `quorum` traders hold it (1 by default: any trader's
        # trade may be taken). Disagreement on direction is the head's to weigh, not a veto.
        backers = {side: sorted(m for m, p in finals.items() if p["action"] == side) for side in ("BUY", "SELL")}
        weak = [side for side, ms in backers.items() if ms and len(ms) < quorum]
        eligible = {m: p for m, p in finals.items() if len(backers[p["action"]]) >= quorum}
        if not eligible:
            return no_trade("no direction has the quorum of " + str(quorum) + " traders: " +
                            "; ".join(f"{side} {', '.join(backers[side])}" for side in weak))
        blocked = {}
        for side in {p["action"] for p in eligible.values()}:
            hit = lesson_block(ctx, 1 if side == "BUY" else -1)
            if hit:
                blocked[side] = hit
        eligible = {m: p for m, p in eligible.items() if p["action"] not in blocked}
        if not eligible:
            hit = next(iter(blocked.values()))
            return no_trade(f"validated lesson {hit['lesson_id']}: {hit['statement']}",
                            contra=[{"code": "LESSON_MATCH", "severity": "BLOCKING", "message": hit["statement"]}])
        supporters = sorted(eligible)

        # 3. HEAD: picks one supporter's trade verbatim, or none.
        head = self.config.head if self.config.head in present else present[0]
        room["head"] = head
        others = {m: room["final"][m] for m in present if m not in eligible}
        records = (ctx.memory_brief or {}).get("room_track_records") or {}
        head_packet = {"instrument": ctx.symbol, "decision_time": packet["decision_time"], "quote": packet["quote"],
                       "timeframes": packet["timeframes"], "eligible": {m: room["final"][m] for m in supporters},
                       "others": others, "track_records": records}
        check = validate_head(set(supporters))
        res = self.llm.complete_json("room:head", HEAD.format(time=packet["decision_time"]), head_packet, check,
                                     cache_key=f"{ctx.symbol}|{ctx.t}|head", only=head)
        if not res.ok:  # the head's provider failed: another provider may chair, under the same rules
            res = self.llm.complete_json("room:head", HEAD.format(time=packet["decision_time"]), head_packet,
                                         check, cache_key=f"{ctx.symbol}|{ctx.t}|head-any")
        if not res.ok:
            return no_trade(f"the head trader could not decide ({res.status}): failing closed")
        room["head_model"], room["head_reason"] = res.model, str(res.data.get("reason") or "")[:400]
        if res.data["decision"] == "NO_TRADE":
            return no_trade(f"head trader ({res.model}) declined: {room['head_reason']}")
        pick = res.data["pick"]
        room["picked"] = pick
        side = eligible[pick]["action"]
        room["outcome"] = f"{side} by {pick}, held by {', '.join(backers[side])}"
        support = [{"agent": f"room:{m}", "claim": f"{m}: {room['final'][m]['thesis']}",
                    "model": room["final"][m]["model"]} for m in backers[side]]
        support.append({"agent": "room:head", "claim": f"head picked {pick}: {room['head_reason']}", "model": res.model})
        return trade_decision(ctx, did, v, agents, reports, eligible[pick], support, evidence={"room": room})


def member_records(db) -> dict:
    """Each member's forward record on the room's executed trades: the trades it supported, and those it did not.

    Built from the immutable journal (trades joined to their decisions). Below 30 trades the
    sample is reported as insufficient, because a win rate over a handful says nothing.
    """
    import json
    out: dict[str, dict] = {}
    rows = db.query("SELECT t.r AS r, d.payload AS dp FROM trades t JOIN decisions d ON d.id = t.decision_id "
                    "ORDER BY t.seq")
    for row in rows:
        if row["r"] is None:
            continue
        dec = json.loads(row["dp"])
        room = (dec.get("independent_evidence") or {}).get("room")
        if dec.get("family") != FAMILY or not room:
            continue
        for m, view in (room.get("final") or {}).items():
            rec = out.setdefault(m, {"supported": [], "stood_aside": []})
            backed = view.get("action") == dec.get("decision") and not view.get("dropped")
            rec["supported" if backed else "stood_aside"].append(float(row["r"]))

    def stats(rs):
        n = len(rs)
        if not n:
            return {"trades": 0}
        return {"trades": n, "win_rate": round(sum(1 for x in rs if x > 0) / n, 3), "avg_R": round(sum(rs) / n, 3),
                "sample": "insufficient" if n < 30 else "adequate"}
    return {m: {"supported": stats(r["supported"]), "stood_aside": stats(r["stood_aside"])} for m, r in out.items()}
