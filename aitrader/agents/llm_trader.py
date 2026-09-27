"""The language-model trader: a model reads the market like a discretionary trader and proposes a trade.

Selected with DECISION_MODE=llm_trader (PAPER or DEMO only). What it may and
may not do is fixed here, in code:

MAY: choose BUY, SELL or NO_TRADE; choose the timeframe it reasons on (M5,
M15, H1, H4 or D1, all from completed bars only); set the stop, the target and a
maximum holding time; write its thesis and invalidation. Before deciding it
reads its own record, its past trades most relevant now (losses first) with
its own reflections on them, and the validated lessons.

MAY NOT: size a trade, change a risk limit, reach the broker, or act while
trading is paused or stopped. Every proposal goes to the SAME risk engine and
execution engine as every other decision, which may refuse it.

FAIL CLOSED: a required analyst that failed, bad or stale data, a position
already open on the pair, no model configured, a failed or malformed reply, a
stop on the wrong side or absurdly far, or a validated lesson against this
exact context -> NO_TRADE, with the reason. The quantitative system's view of
the market (unfamiliar, abnormal) is shown to the model as information; it is
not a veto. How tight a stop may be is the risk engine's spread-based check.

NOT BACKTESTABLE: a model trained on text written after a historical date
knows what happened next. It is refused in BACKTEST mode; its record can only
be built forward, on prices no one has seen (docs/RESEARCH_LOG.md).
"""

from __future__ import annotations

from datetime import datetime, timezone

import numpy as np

from ..data.bars import BarSeries
from ..data.resample import resample
from ..decision.synthesis import Decision, decision_id
from .types import MarketContext

#: 1.1.0: also reads completed M5 and M15 bars when the broker provides them, and may trade on them.
#: 1.2.0 (owner: "it controls itself"): the prompt no longer steers its style; the quantitative
#: system's market JUDGEMENTS (unfamiliar, abnormal) are information, not a veto; no minimum stop
#: distance of its own: the risk engine's spread-based stop checks decide what is too tight.
LLM_TRADER_VERSION = "llm-trader-1.2.0"
FAMILY = "LLM_TRADER"
TIMEFRAMES = ("M5", "M15", "H1", "H4", "D1")
MAX_STOP_ATR = 12.0  # in H1 ATR: wider than this is a typo, not a stop (too tight: the risk engine decides)
#: The quantitative objections that still stop a decision before any model is asked. They concern the
#: DATA or the account, not a view of the market: a model must never trade on wrong or stale prices,
#: and a second position on the same pair would be refused by the risk engine anyway.
PRE_MODEL_BLOCKS = ("DATA_QUALITY", "STALE_DATA", "EXPOSURE")
MAX_HOLD_HOURS = 336

SYSTEM = """You are a professional discretionary FX trader managing a paper account.
You decide for ONE instrument, now. The decision time is {time}; treat it as the present.
Use ONLY the data in the JSON you are given: completed bars on M5 and M15 (when present), H1, H4 and D1, the live quote,
the account, the quantitative agents' findings (information, not orders), and YOUR OWN MEMORY: your record, your
past trades most relevant now (losses first) with your own reflections on them, and validated lessons.
Do not use any knowledge of prices or events after the decision time, even if you have it.

Every choice is yours: whether to trade at all, the direction, the timeframe, your style, where the stop and
the target go, how long to hold. No style, quota or setup is required of you. Use your memory as you see fit
and say which part of it you used. You do NOT size positions: a risk engine does that and may refuse a trade.

Reply with ONE JSON object only:
{{"action": "BUY|SELL|NO_TRADE", "timeframe": "M5|M15|H1|H4|D1", "stop": <price or null>, "target": <price or null>,
  "max_hold_hours": <1-336 or null>, "thesis": "why, in at most 4 sentences",
  "invalidation": "what would prove you wrong", "memory_used": "which past trade or lesson you applied, or none"}}"""

REFLECT = """You are reviewing one of YOUR OWN closed paper trades, to learn from it.
Be specific and honest. A loss is not automatically a mistake: sometimes a sound trade loses.
Reply with ONE JSON object only:
{"what_happened": "1-2 sentences", "was_it_a_mistake": true|false,
 "mistake": "the specific error, or null", "lesson": "one concrete rule for next time, or null"}"""


def _tf_summary(bars: BarSeries, n_show: int) -> dict | None:
    if bars is None or len(bars) < 3:
        return None
    c, h, lo = bars.mid_close, bars.mid_high, bars.mid_low
    pc = np.concatenate(([c[0]], c[:-1]))
    tr = np.maximum(h - lo, np.maximum(abs(h - pc), abs(lo - pc)))
    atr = float(tr[-min(14, len(tr)):].mean())
    k = min(20, len(c))
    hi20, lo20 = float(h[-k:].max()), float(lo[-k:].min())

    def chg(m):
        return round(float((c[-1] - c[-1 - m]) / atr), 2) if len(c) > m and atr > 0 else None

    last = [{"t": datetime.fromtimestamp(int(bars.open_time[i]), timezone.utc).strftime("%m-%d %H:%M"),
             "o": round(float(bars.mid_open[i]), 5), "h": round(float(h[i]), 5),
             "l": round(float(lo[i]), 5), "c": round(float(c[i]), 5)} for i in range(max(0, len(c) - n_show), len(c))]
    return {"close": round(float(c[-1]), 5), "atr14": round(atr, 6),
            "change_atr": {"1": chg(1), "5": chg(5), "20": chg(20)},
            "range20": {"high": round(hi20, 5), "low": round(lo20, 5),
                        "position": round(float((c[-1] - lo20) / (hi20 - lo20)), 2) if hi20 > lo20 else None},
            "bars": last}


LOWER_SHOW = {"M5": 24, "M15": 16}  # bars shown per lower timeframe


def multi_timeframe(h1: BarSeries, as_of: int, lower: dict | None = None) -> dict:
    """Summaries on M5/M15 (when the broker provides them), H1, H4 and D1, each from COMPLETED
    bars only: the feed never returns a forming bar and resample never emits one."""
    out = {tf: _tf_summary(b, LOWER_SHOW[tf]) for tf, b in (lower or {}).items()
           if tf in LOWER_SHOW and b is not None and len(b)}
    out["H1"] = _tf_summary(h1, 24)
    for tf, n in (("H4", 18), ("D1", 15)):
        try:
            out[tf] = _tf_summary(resample(h1, tf, as_of=as_of), n)
        except ValueError:
            out[tf] = None
    return out


def validate_proposal(d: dict) -> str | None:
    """Shape only; prices are checked against the live quote in `LLMTrader.decide`."""
    if d.get("action") not in ("BUY", "SELL", "NO_TRADE"):
        return "action must be BUY, SELL or NO_TRADE"
    if d["action"] == "NO_TRADE":
        return None if isinstance(d.get("thesis", ""), str) else "thesis must be text"
    if d.get("timeframe") not in TIMEFRAMES:
        return f"timeframe must be one of {', '.join(TIMEFRAMES)}"
    for k in ("stop", "target"):
        if not isinstance(d.get(k), (int, float)) or not np.isfinite(d[k]) or d[k] <= 0:
            return f"{k} must be a positive price"
    mh = d.get("max_hold_hours")
    if not isinstance(mh, int) or not 1 <= mh <= MAX_HOLD_HOURS:
        return f"max_hold_hours must be an integer 1..{MAX_HOLD_HOURS}"
    if not isinstance(d.get("thesis"), str) or not d["thesis"].strip():
        return "a trade needs a thesis"
    return None


def validate_reflection(d: dict) -> str | None:
    if not isinstance(d.get("what_happened"), str) or not isinstance(d.get("was_it_a_mistake"), bool):
        return "what_happened (text) and was_it_a_mistake (bool) are required"
    return None


REQUIRED_AGENTS = ("market", "setup", "risk", "adversary", "reviewer")


def pre_model_block(ctx: MarketContext, reports: dict, llm) -> tuple[str, list] | None:
    """Why no model may be consulted for this decision, or None. Checked BEFORE anything is spent."""
    for name in REQUIRED_AGENTS:
        r = reports.get(name)
        if r is None or not r.ok:
            return f"agent '{name}' {'missing' if r is None else r.status}: failing closed", []
    blocking = [o for r in reports.values() for o in r.objections
                if o.severity == "BLOCKING" and not o.data.get("action") and o.code in PRE_MODEL_BLOCKS]
    if blocking:
        return ("blocked before consulting the model: " + "; ".join(f"{o.code}: {o.message}" for o in blocking[:3]),
                [o.as_dict() for o in blocking])
    if not ctx.trading_allowed:
        return "trading is paused or stopped: the model was not consulted", []
    if llm is None or not llm.config.enabled:
        return "no language model is configured (AI_PROVIDER / AI_PROVIDERS): failing closed", []
    if ctx.bid is None or ctx.ask is None or ctx.atr is None or not np.isfinite(ctx.atr) or ctx.atr <= 0:
        return "no live quote or ATR: nothing to price a trade against", []
    return None


def market_packet(ctx: MarketContext, reports: dict) -> dict:
    return {
        "instrument": ctx.symbol, "decision_time": datetime.fromtimestamp(ctx.t, timezone.utc).isoformat(),
        "quote": {"bid": ctx.bid, "ask": ctx.ask, "spread": round(ctx.ask - ctx.bid, 6)},
        "account": {"equity": ctx.account.equity, "drawdown_pct": ctx.account.drawdown_pct,
                    "open_positions": ctx.account.open_positions},
        "timeframes": ctx.mtf,
        "quant_agents": {k: {"summary": r.summary,
                             "objections": [f"{o.severity} {o.code}: {o.message}" for o in r.objections][:6]}
                         for k, r in reports.items()},
        "regime": {k: val for k, val in ctx.regime.as_dict().items() if k != "reasons"},
        "memory": ctx.memory_brief,
        "calendar": ctx.news if ctx.news is not None else {"feed": {"status": "NOT_CONFIGURED"}, "events": None},
    }


def level_problem(ctx: MarketContext, p: dict) -> str | None:
    """A proposed trade whose prices cannot stand, or None. Checked against the live quote; never repaired."""
    side = 1 if p["action"] == "BUY" else -1
    entry = ctx.ask if side > 0 else ctx.bid
    stop, target = float(p["stop"]), float(p["target"])
    if (entry - stop) * side <= 0 or (target - entry) * side <= 0:
        return (f"model proposed {p['action']} with stop {stop} / target {target} on the wrong side "
                f"of the entry {entry}: rejected, never repaired")
    dist = abs(entry - stop) / ctx.atr
    if dist > MAX_STOP_ATR:
        return f"stop {dist:.2f} H1-ATR from entry is beyond {MAX_STOP_ATR}: a typo, not a stop: rejected"
    return None


def lesson_block(ctx: MarketContext, side: int) -> dict | None:
    """A validated lesson against this model-trader context, or None."""
    kv = ctx.knowledge
    if kv is not None and hasattr(kv, "lessons_matching"):
        hits = kv.lessons_matching(FAMILY, ctx.regime.label, ctx.regime.vol_state, side, ctx.t)
        if hits:
            return hits[0]
    return None


def agent_digest(reports: dict) -> dict:
    return {k: {"status": r.status, "stance": r.stance, "summary": r.summary, "objections": len(r.objections)}
            for k, r in reports.items()}


def no_trade_decision(ctx: MarketContext, did: str, v: dict, agents: dict, reason: str, contra=None, support=None,
                      evidence: dict | None = None) -> Decision:
    return Decision(did, "NO_TRADE", ctx.symbol, ctx.timeframe, ctx.t, ctx.mode, {}, ctx.regime.as_dict(),
                    reason, support or [], contra or [], None, None, None, None, "LLM", FAMILY,
                    None, None, None, None, None, None, None, None, reason, agents, evidence or {}, 0, v)


def trade_decision(ctx: MarketContext, did: str, v: dict, agents: dict, reports: dict, p: dict,
                   support: list, evidence: dict | None = None) -> Decision:
    """A validated proposal, verbatim: the levels are the model's, the size is the risk engine's."""
    side = 1 if p["action"] == "BUY" else -1
    entry = ctx.ask if side > 0 else ctx.bid
    stop, target = float(p["stop"]), float(p["target"])
    rr = abs(target - entry) / abs(entry - stop)
    thesis = f"{p['action']} {ctx.symbol} on {p['timeframe']}: {str(p['thesis'])[:500]}"
    return Decision(
        did, p["action"], ctx.symbol, p["timeframe"], ctx.t, ctx.mode, {}, ctx.regime.as_dict(), thesis,
        support, [{"agent": k, "code": o.code, "severity": o.severity, "message": o.message}
                  for k, r in reports.items() for o in r.objections][:12],
        float(entry), stop, target, f"stop {stop:.5g}, target {target:.5g}, time exit after {p['max_hold_hours']}h",
        "LLM", FAMILY, None, None, None, None, None, None, 1.0,
        str(p.get("invalidation") or "")[:300] or None, None, agents,
        {"note": "model-proposed; no measured expectancy exists until its forward record does",
         "reward_risk": round(rr, 3), **(evidence or {})}, 1, v,
        max_hold_hours=int(p["max_hold_hours"]))


class LLMTrader:
    def __init__(self, llm) -> None:
        self.llm = llm

    # ── decide ──────────────────────────────────────────────────────────

    def decide(self, ctx: MarketContext, reports: dict, versions: dict, llm_opinions=None) -> Decision:
        if ctx.mode == "BACKTEST":
            raise ValueError("the language-model trader cannot be backtested honestly: the model may know "
                             "what happened after the decision time")
        v = {**versions, "llm_trader": LLM_TRADER_VERSION}
        did = decision_id(ctx.symbol, ctx.timeframe, ctx.t, ctx.mode, v)
        agents = agent_digest(reports)

        def no_trade(reason: str, contra=None, support=None) -> Decision:
            return no_trade_decision(ctx, did, v, agents, reason, contra, support)

        blocked = pre_model_block(ctx, reports, self.llm)
        if blocked:
            return no_trade(blocked[0], contra=blocked[1])
        packet = market_packet(ctx, reports)
        res = self.llm.complete_json("trader", SYSTEM.format(time=packet["decision_time"]), packet,
                                     validate_proposal, cache_key=f"{ctx.symbol}|{ctx.t}")
        if not res.ok:
            return no_trade(f"language model unavailable or reply rejected ({res.status}): failing closed")
        p = res.data
        memory_note = {"agent": "llm_trader", "claim": f"memory used: {str(p.get('memory_used') or 'none')[:200]}",
                       "model": res.model}
        if p["action"] == "NO_TRADE":
            return no_trade(f"model: {str(p.get('thesis') or 'no trade')[:400]}", support=[memory_note])
        problem = level_problem(ctx, p)
        if problem:
            return no_trade(problem)
        hit = lesson_block(ctx, 1 if p["action"] == "BUY" else -1)
        if hit:
            return no_trade(f"validated lesson {hit['lesson_id']}: {hit['statement']}",
                            contra=[{"code": "LESSON_MATCH", "severity": "BLOCKING", "message": hit["statement"]}])
        return trade_decision(ctx, did, v, agents, reports, p, [memory_note])

    # ── learn from a closed trade ───────────────────────────────────────

    def reflect(self, trade: dict) -> dict | None:
        """The model's own review of one closed trade, or None if unavailable (the deterministic post-mortem stands)."""
        if self.llm is None or not self.llm.config.enabled:
            return None
        res = self.llm.complete_json("reflector", REFLECT, trade, validate_reflection)
        if not res.ok:
            return None
        d = res.data
        return {"kind": "trade", "decision_id": trade.get("decision_id"), "model": res.model,
                "text": str(d.get("what_happened"))[:400], "mistake": (str(d["mistake"])[:300] if d.get("mistake") else None),
                "was_it_a_mistake": d["was_it_a_mistake"], "lesson": (str(d["lesson"])[:300] if d.get("lesson") else None),
                "version": LLM_TRADER_VERSION}
