"""The trading room: one mind with several brains. Each brain is a different provider's model.

Selected with DECISION_MODE=trading_room (PAPER or DEMO only). The members do
not vote. They think TOGETHER, in turn, and reach ONE joint decision:

1. DISCUSSION. Each member has a ROLE, like the desks of one trading
   firm: TREND (the big picture on H4/D1, the team's bias), PRICE (levels,
   entry and stop on M5/M15/H1), NEWS (the economic calendar and the
   session: is now a good moment) and RISK (costs, the account, the team's
   past mistakes and lessons). They speak in that order. Each reads the
   packet AND everything said so far, then builds on it from its role:
   agrees and adds, corrects a mistake, or argues for a better plan.
   Members are assigned roles in AI_PROVIDERS order; with fewer members a
   member holds several neighbouring roles, with more a role gets a second voice.
2. JOINT DECISION. One member (AI_ROOM_HEAD, else the first present) reads
   the whole discussion and writes the team's single decision: the plan
   the team converged on, or none.

If every member recommends NO_TRADE, the joint call is skipped: nothing is
invented and nothing more is spent.

Fixed in code, not in any prompt:

- a member speaks only through its own provider (`only=`); a member whose
  provider fails is skipped, never replaced by another model's voice;
- the joint plan passes the same checks as the single trader: a wrong-side
  or absurdly far stop is NO_TRADE, never repaired; the risk engine sizes it
  and may refuse it; a validated lesson against its side blocks it;
- the same pre-model gates: paused, stopped, bad or stale data, a position
  already open on the pair -> no model is called.

Everything said is recorded on the decision (`independent_evidence["room"]`),
so each member's forward record can be measured separately.
"""

from __future__ import annotations

import os
from dataclasses import dataclass

from ..decision.synthesis import Decision, decision_id
from .llm_trader import (
    FAMILY, LLM_TRADER_VERSION, agent_digest, lesson_block, level_problem, market_packet, no_trade_decision,
    pre_model_block, trade_decision, validate_proposal,
)
from .types import MarketContext

#: 1.1.0: M5/M15 bars in the packet and as trade timeframes.
#: 1.2.0: neutral prompts; a split went to the head; default quorum 1.
#: 2.0.0 (owner: "one body with four minds"): no independent votes; the members discuss in
#: turn, each building on the others, and one member writes the team's joint decision.
#: 2.1.0 (owner: "one is the news, one the price..."): each member has a role; they speak in
#: role order; the packet carries the economic calendar.
ROOM_VERSION = "trading-room-2.1.0"

#: The desks of one trading firm, in speaking order: direction, then entry, then timing, then checks.
ROLES = (
    ("TREND", "the big picture: direction and momentum on H4 and D1, where price sits in the higher-timeframe "
              "range, the volatility state. You give the team its bias."),
    ("PRICE", "price action: structure, key levels, the entry and where the stop belongs on M5, M15 and H1. "
              "You turn the bias into a precise plan."),
    ("NEWS", "news and timing: the economic calendar in the JSON (releases for this pair's currencies, how soon, "
             "how important, forecast vs previous) and the session open now. You judge whether now is a good "
             "moment and what could move the price. If the calendar is unavailable, say so; never invent news."),
    ("RISK", "risk and memory: spread and costs against the stop and target, the account, and the team's past "
             "trades and lessons. You check the plan, fix what is unsafe or repeats a past mistake, and make "
             "the target realistic."),
)


def assign_roles(members: list[str]) -> dict[str, list[str]]:
    """Members take roles in order. Fewer members than roles: one member holds several; more: second voices."""
    names = [r for r, _ in ROLES]
    if not members:
        return {}
    n = len(members)
    if n <= len(names):  # contiguous blocks, so the last speaker still holds RISK
        return {m: names[i * len(names) // n:(i + 1) * len(names) // n] for i, m in enumerate(members)}
    return {m: [names[i % len(names)]] for i, m in enumerate(members)}

_DATA = """Use ONLY the data in the JSON: completed bars on M5 and M15 (when present), H1, H4 and D1, the live quote,
the account, the quantitative agents' findings (information, not orders), and the team's memory of its past
trades (losses first) with the reflections written on them. The decision time is {time}; treat it as the
present and do not use any knowledge of prices or events after it."""

_OWNER = """The owner wants an active team that finds trades, short ones on M5/M15 included, whenever the market
offers a reasonable opportunity. Every trading choice is the team's own: direction, timeframe, style, stop,
target, holding time, or no trade. No one sizes positions: a risk engine does that and may refuse a trade."""

SPEAK = """You are {name}, one of {n} minds of ONE trading team: {members}. You are not competitors. You think
together as one trader with {n} brains, and your team's record is shared (each mind's contribution is also
tracked). You decide for ONE instrument, now.
""" + _DATA + """
""" + _OWNER + """

YOUR ROLE in the team: {role}
You see all the data, but contribute above all from your role; your teammates cover the others.
"discussion" in the JSON holds what your teammates have said so far, in order, with their roles (empty if
you speak first). Build on it: agree and add what they missed, correct a mistake, or argue for a better plan
and try to convince them. Then state the plan you want the team to take.

Reply with ONE JSON object only:
{{"action": "BUY|SELL|NO_TRADE", "timeframe": "M5|M15|H1|H4|D1", "stop": <price or null>, "target": <price or null>,
  "max_hold_hours": <1-336 or null>, "thesis": "your analysis and your plan, at most 5 sentences",
  "to_team": "what you say to your teammates: what you agree with, what you correct, at most 3 sentences",
  "invalidation": "what would prove the plan wrong", "memory_used": "which past trade or lesson you used, or none"}}"""

JOINT = """You are {name}, writing the JOINT DECISION of your trading team ({members}): one trader with {n} brains.
""" + _DATA + """
""" + _OWNER + """

"discussion" in the JSON holds everything the team said, in order, with each member's role: TREND gave the
bias, PRICE the levels, NEWS the timing, RISK the checks. Write the ONE plan the team converged on, combining
the best of each role: the direction, timeframe, stop, target and holding time
the team stands behind, or NO_TRADE if the team concluded there is nothing worth taking.

Reply with ONE JSON object only:
{{"action": "BUY|SELL|NO_TRADE", "timeframe": "M5|M15|H1|H4|D1", "stop": <price or null>, "target": <price or null>,
  "max_hold_hours": <1-336 or null>, "thesis": "the team's reasoning, at most 5 sentences",
  "invalidation": "what would prove the plan wrong", "memory_used": "which past trade or lesson the team used, or none"}}"""


@dataclass(frozen=True)
class RoomConfig:
    size: int = 4          # members taken from AI_PROVIDERS, in order
    head: str = ""         # provider name that writes the joint decision; default the first member present

    def __post_init__(self) -> None:
        if not 1 <= self.size <= 8:
            raise ValueError("AI_ROOM_SIZE must be 1..8")

    @classmethod
    def from_env(cls, env: dict | None = None) -> "RoomConfig":
        e = os.environ if env is None else env
        return cls(size=int(e.get("AI_ROOM_SIZE", "4")), head=e.get("AI_ROOM_HEAD", "").strip().lower())


def validate_speech(d: dict) -> str | None:
    problem = validate_proposal(d)
    if problem:
        return problem
    t = d.get("to_team")
    return None if t is None or isinstance(t, str) else "to_team must be text"


def _view(p: dict | None, model: str | None = None, status: str = "OK") -> dict:
    if p is None:
        return {"status": status, "model": model}
    return {"status": status, "model": model, "action": p.get("action"), "timeframe": p.get("timeframe"),
            "stop": p.get("stop"), "target": p.get("target"), "max_hold_hours": p.get("max_hold_hours"),
            "thesis": str(p.get("thesis") or "")[:500], "invalidation": str(p.get("invalidation") or "")[:200],
            "memory_used": str(p.get("memory_used") or "")[:200],
            **({"to_team": str(p.get("to_team"))[:400]} if p.get("to_team") else {})}


class TradingRoom:
    def __init__(self, llm, config: RoomConfig | None = None) -> None:
        self.llm = llm
        self.config = config or RoomConfig()

    def members(self) -> list[str]:
        if self.llm is None or not self.llm.config.enabled:
            return []
        return [ep.name for ep in self.llm.config.endpoints()][: self.config.size]

    @staticmethod
    def speaking_order(roles: dict[str, list[str]]) -> list[str]:
        """Role order: TREND, then PRICE, then NEWS, then RISK; second voices after the first ones."""
        rank = {r: i for i, (r, _) in enumerate(ROLES)}
        first = {m: rank[rs[0]] + (len(ROLES) if m in list(roles)[len(ROLES):] else 0) for m, rs in roles.items()}
        return sorted(roles, key=lambda m: first[m])

    def decide(self, ctx: MarketContext, reports: dict, versions: dict, llm_opinions=None) -> Decision:
        if ctx.mode == "BACKTEST":
            raise ValueError("the trading room cannot be backtested honestly: the models may know "
                             "what happened after the decision time")
        v = {**versions, "llm_trader": LLM_TRADER_VERSION, "trading_room": ROOM_VERSION}
        did = decision_id(ctx.symbol, ctx.timeframe, ctx.t, ctx.mode, v)
        agents = agent_digest(reports)
        members = self.members()
        roles = assign_roles(members)
        order = self.speaking_order(roles)
        room: dict = {"members": members, "roles": roles, "order": order, "head": None, "discussion": [],
                      "final": {}, "joint": None, "outcome": None}

        def no_trade(reason: str, contra=None) -> Decision:
            room["outcome"] = reason
            return no_trade_decision(ctx, did, v, agents, reason, contra, evidence={"room": room})

        blocked = pre_model_block(ctx, reports, self.llm)
        if blocked:
            return no_trade(blocked[0], contra=blocked[1])
        packet = market_packet(ctx, reports)
        n, names = len(members), ", ".join(members)

        # 1. DISCUSSION: in turn, each member reads everything said so far.
        said: list[dict] = []
        desc = dict(ROLES)
        for m in order:
            role = " AND ".join(f"{r}, {desc[r]}" for r in roles[m])
            res = self.llm.complete_json(
                f"room:{m}", SPEAK.format(name=m, n=n, members=names, time=packet["decision_time"], role=role),
                {**packet, "you": m, "discussion": list(said)}, validate_speech,
                cache_key=f"{ctx.symbol}|{ctx.t}|speak|{len(said)}", only=m)
            if not res.ok:
                room["discussion"].append({"member": m, "role": "+".join(roles[m]), "status": res.status,
                                           "model": res.model})
                continue  # skipped: nobody speaks for it
            view = _view(res.data, res.model)
            if view["action"] != "NO_TRADE":
                problem = level_problem(ctx, res.data)
                if problem:
                    view["dropped"] = problem  # recorded; its teammates still read what it argued
            said.append({"member": m, "role": "+".join(roles[m]), **{k: view.get(k) for k in (
                "action", "timeframe", "stop", "target", "max_hold_hours", "thesis", "to_team", "invalidation")}})
            room["discussion"].append({"member": m, "role": "+".join(roles[m]), **view})
            room["final"][m] = view
        present = [m for m in order if m in room["final"]]
        if not present:
            return no_trade("no member of the team answered (" +
                            ", ".join(f"{d['member']}: {d['status']}" for d in room["discussion"]) + "): failing closed")
        if all(room["final"][m]["action"] == "NO_TRADE" for m in present):
            views = "; ".join(f"{m}: {room['final'][m]['thesis'][:160]}" for m in present)
            return no_trade(f"the team saw nothing worth taking ({len(present)} of {n} spoke). {views}")

        # 2. JOINT DECISION: one member writes the plan the team converged on.
        head = self.config.head if self.config.head in present else present[0]
        room["head"] = head
        system = JOINT.format(name=head, n=n, members=names, time=packet["decision_time"])
        joint_packet = {**packet, "discussion": said}
        res = self.llm.complete_json("room:joint", system, joint_packet, validate_proposal,
                                     cache_key=f"{ctx.symbol}|{ctx.t}|joint", only=head)
        if not res.ok:  # that provider failed: another member's model writes it, under the same rules
            res = self.llm.complete_json("room:joint", system, joint_packet, validate_proposal,
                                         cache_key=f"{ctx.symbol}|{ctx.t}|joint-any")
        if not res.ok:
            return no_trade(f"the team's joint decision could not be written ({res.status}): failing closed")
        p = res.data
        room["joint"] = _view(p, res.model)
        if p["action"] == "NO_TRADE":
            return no_trade(f"team decision ({res.model}): no trade. {str(p.get('thesis') or '')[:400]}")
        problem = level_problem(ctx, p)
        if problem:
            return no_trade(f"team decision rejected, never repaired: {problem}")
        hit = lesson_block(ctx, 1 if p["action"] == "BUY" else -1)
        if hit:
            return no_trade(f"validated lesson {hit['lesson_id']}: {hit['statement']}",
                            contra=[{"code": "LESSON_MATCH", "severity": "BLOCKING", "message": hit["statement"]}])
        backers = [m for m in present if room["final"][m]["action"] == p["action"]]
        room["outcome"] = (f"team {p['action']} on {p['timeframe']}, written by {head}"
                           + (f"; argued for by {', '.join(backers)}" if backers else ""))
        support = [{"agent": f"room:{d['member']}", "claim": f"{d['member']}: {d.get('to_team') or d['thesis']}",
                    "model": room["final"][d["member"]]["model"]} for d in said]
        support.append({"agent": "room:joint", "claim": f"joint decision by {head}: {str(p['thesis'])[:300]}",
                        "model": res.model})
        return trade_decision(ctx, did, v, agents, reports, p, support, evidence={"room": room})


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
