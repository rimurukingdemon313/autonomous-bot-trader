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
#: 1.3.0: the packet carries the economic calendar and the history desk.
#: 1.4.0 (owner: "no fixed duration, even a minute"): holding time in MINUTES (1 to 20160), M1 bars,
#: and the model reviews its open trades and may close them whenever it decides.
#: 1.5.0: the owner's wish that the account not sit idle is stated.
#: 1.7.0: bars as rows (bar_fields names the columns) and fewer of them (M1 24, M5 18, M15 12, H4 12, D1 10;
#:        each timeframe keeps its 20-bar summary): fewer tokens per decision, so more decisions per free day.
#: 1.8.0: the reply schema lists M1, which was always accepted but never offered.
#: 1.9.0: the packet carries the market map and intermarket context; any method is invited and named.
#: 1.11.0: the packet carries the strategy desk.
#: 1.12.0: no trade-forcing language: the "account should not sit idle" request is removed (a trade must be
#:         justified by the data, never by inactivity); the reply adds UNCERTAIN, confidence, expected_r,
#:         reasons_against, evidence, regime and analogues. A trade needs an invalidation and a confidence.
#: 1.10.0: fewer rows (H1 12, M1 15, H4 6, D1 5; levels are in the map), no history example list, a leaner
#:         map, so the joint call fits
#:         a free tier's per-minute token limit (Groq answered 413 "request too large").
LLM_TRADER_VERSION = "llm-trader-1.12.0"
FAMILY = "LLM_TRADER"
TIMEFRAMES = ("M1", "M5", "M15", "H1", "H4", "D1")
MAX_STOP_ATR = 12.0  # in H1 ATR: wider than this is a typo, not a stop (too tight: the risk engine decides)
#: The quantitative objections that still stop a decision before any model is asked. They concern the
#: DATA or the account, not a view of the market: a model must never trade on wrong or stale prices,
#: and a second position on the same pair would be refused by the risk engine anyway.
PRE_MODEL_BLOCKS = ("DATA_QUALITY", "STALE_DATA", "EXPOSURE")
MAX_HOLD_HOURS = 336  # legacy field, still accepted
MAX_HOLD_MINUTES = 20160  # 14 days; 1 = one minute

SYSTEM = """You are a professional discretionary FX trader managing a paper account.
You decide for ONE instrument, now. The decision time is {time}; treat it as the present.
Use ONLY the data in the JSON you are given: completed bars on M1, M5 and M15 (when present), H1, H4 and D1, the live quote,
the account, the quantitative agents' findings (information, not orders), the economic calendar, the history
desk (what fixed trades did, after costs, in the most similar past situations), the market map (structure
computed from completed bars: swings, BOS/CHoCH, order blocks, fair value gaps, liquidity and sweeps, previous
day/week and session levels, round numbers), intermarket context (dollar index, US 10-year yield, gold, S&P 500
futures), the strategy desk (the classic indicators, which of 16 well-known strategies fire on the last completed
bar, and a scoreboard of how each did on this pair's recent history after spread), and YOUR OWN MEMORY: your record,
your past trades most relevant now (losses first) with your own reflections on them, and validated lessons.
Do not use any knowledge of prices or events after the decision time, even if you have it.

Use whatever method you judge strongest here and now: SMC/ICT, price action, momentum, mean reversion,
intermarket, news, or a combination; the map is information, not an instruction. Name it in "method".
Every choice is yours: whether to trade at all, the direction, the timeframe, your style, where the stop and
the target go, how long to hold (from one minute to two weeks). No style, quota or setup is required of you, and
you will be asked about your open trades as time passes: you may close them whenever you decide.
The owner's objective is profit after costs; every loss is recorded against your record. Time without a
trade costs nothing: never trade because the account has been idle, to reach a count, or to recover a loss.
Trade only when you can justify the setup from the data; otherwise answer NO_TRADE, or UNCERTAIN when the
evidence is mixed. Use your memory as you see fit and say which part of it you used. You do NOT size positions: a risk engine does that and may refuse a trade.

Your confidence is recorded and later compared with what actually happened; it never changes the size.

Reply with ONE JSON object only:
{{"action": "BUY|SELL|NO_TRADE|UNCERTAIN", "timeframe": "M1|M5|M15|H1|H4|D1", "stop": <price or null>,
  "target": <price or null>, "max_hold_minutes": <1-20160 or null>, "thesis": "why, in at most 4 sentences",
  "confidence": <0.0-1.0, required for BUY/SELL>, "expected_r": <the R you expect, or null>,
  "evidence": ["the specific facts in the data that support it"], "reasons_against": ["the strongest reasons not to"],
  "invalidation": "what would prove you wrong (required for BUY/SELL)", "regime": "the market regime as you read it",
  "analogues": "similar past situations you relied on, or none", "memory_used": "which past trade or lesson you applied, or none",
  "method": "the method you used, in a few words"}}"""

REFLECT = """You are reviewing one of YOUR OWN closed paper trades, to learn from it.
Be specific and honest. A loss is not automatically a mistake: sometimes a sound trade loses.
Reply with ONE JSON object only:
{"what_happened": "1-2 sentences", "was_it_a_mistake": true|false,
 "mistake": "the specific error, or null", "lesson": "one concrete rule for next time, or null"}"""


BAR_FIELDS = ["open_utc (day hh:mm)", "open", "high", "low", "close"]


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

    # One row per bar, in the order of BAR_FIELDS: the same numbers without a key on every value.
    # Free tiers are counted in tokens per day, so the packet's size decides how many decisions fit.
    last = [[datetime.fromtimestamp(int(bars.open_time[i]), timezone.utc).strftime("%d %H:%M"),
             round(float(bars.mid_open[i]), 5), round(float(h[i]), 5), round(float(lo[i]), 5), round(float(c[i]), 5)]
            for i in range(max(0, len(c) - n_show), len(c))]
    return {"close": round(float(c[-1]), 5), "atr14": round(atr, 6),
            "change_atr": {"1": chg(1), "5": chg(5), "20": chg(20)},
            "range20": {"high": round(hi20, 5), "low": round(lo20, 5),
                        "position": round(float((c[-1] - lo20) / (hi20 - lo20)), 2) if hi20 > lo20 else None},
            "bar_fields": BAR_FIELDS, "bars": last}


LOWER_SHOW = {"M1": 15, "M5": 18, "M15": 12}  # bars shown per lower timeframe (each also has a 20-bar summary)


def multi_timeframe(h1: BarSeries, as_of: int, lower: dict | None = None) -> dict:
    """Summaries on M5/M15 (when the broker provides them), H1, H4 and D1, each from COMPLETED
    bars only: the feed never returns a forming bar and resample never emits one."""
    out = {tf: _tf_summary(b, LOWER_SHOW[tf]) for tf, b in (lower or {}).items()
           if tf in LOWER_SHOW and b is not None and len(b)}
    out["H1"] = _tf_summary(h1, 12)
    for tf, n in (("H4", 6), ("D1", 5)):  # their levels and structure are in the market map
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
    if hold_minutes(d) is None:
        return f"max_hold_minutes must be an integer 1..{MAX_HOLD_MINUTES}"
    if not isinstance(d.get("thesis"), str) or not d["thesis"].strip():
        return "a trade needs a thesis"
    return None


def _texts(x, n: int = 6) -> list[str] | None:
    """A list of short strings, or None when the field is not one (absent is an empty list)."""
    if x is None:
        return []
    if not isinstance(x, list) or not all(isinstance(i, str) for i in x):
        return None
    return [i.strip()[:200] for i in x[:n] if i.strip()]


def validate_trader_reply(d: dict) -> str | None:
    """The language-model trader's full reply. Stricter than `validate_proposal` (which the trading
    room's members share): UNCERTAIN is a recorded answer, and a trade must state its confidence and
    what would invalidate it. A malformed field is a rejected reply (NO_TRADE), never repaired."""
    if d.get("action") == "UNCERTAIN":
        return None if isinstance(d.get("thesis", ""), str) else "thesis must be text"
    problem = validate_proposal(d)
    if problem or d["action"] == "NO_TRADE":
        return problem
    c = d.get("confidence")
    if not isinstance(c, (int, float)) or isinstance(c, bool) or not np.isfinite(c) or not 0.0 <= c <= 1.0:
        return "a trade needs a confidence between 0 and 1"
    if not isinstance(d.get("invalidation"), str) or not d["invalidation"].strip():
        return "a trade needs an invalidation condition"
    e = d.get("expected_r")
    if e is not None and (not isinstance(e, (int, float)) or isinstance(e, bool) or not np.isfinite(e) or abs(e) > 50):
        return "expected_r must be a number (in R) or null"
    for k in ("evidence", "reasons_against"):
        if _texts(d.get(k)) is None:
            return f"{k} must be a list of text"
    return None


def model_view(p: dict) -> dict:
    """What the model said beyond the levels, as recorded on the decision. Never used to size or price."""
    return {"action": p.get("action"), "confidence": p.get("confidence"), "expected_r": p.get("expected_r"),
            "evidence": _texts(p.get("evidence")) or [], "reasons_against": _texts(p.get("reasons_against")) or [],
            "regime": str(p.get("regime") or "")[:200] or None, "analogues": str(p.get("analogues") or "")[:300] or None,
            "method": str(p.get("method") or "")[:120] or None, "memory_used": str(p.get("memory_used") or "")[:200] or None,
            "invalidation": str(p.get("invalidation") or "")[:300] or None, "timeframe": p.get("timeframe")}


def hold_minutes(d: dict) -> int | None:
    """The proposal's maximum holding time in minutes (max_hold_minutes, or the older max_hold_hours)."""
    m = d.get("max_hold_minutes")
    if isinstance(m, int) and not isinstance(m, bool) and 1 <= m <= MAX_HOLD_MINUTES:
        return m
    h = d.get("max_hold_hours")
    if m is None and isinstance(h, int) and not isinstance(h, bool) and 1 <= h <= MAX_HOLD_HOURS:
        return h * 60
    return None


REVIEW = """You are the trader who holds this open paper position. The time is {time}; treat it as the present.
Use ONLY the data in the JSON: the position, the live quote, completed bars (M1 to H1), the calendar.
Decide freely: keep holding, or close it now at the market. The stop and target stay on the broker either way,
and you cannot change them or the size. The owner's objective is profit after costs.
Reply with ONE JSON object only: {{"action": "HOLD|CLOSE", "reason": "at most 2 sentences"}}"""


def validate_review(d: dict) -> str | None:
    if d.get("action") not in ("HOLD", "CLOSE"):
        return "action must be HOLD or CLOSE"
    return None if isinstance(d.get("reason", ""), str) else "reason must be text"


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
    if ctx.account_blocks:
        # The risk engine's own account checks (daily loss spent, positions full...): it would refuse
        # whatever the model proposed, so nothing is spent asking.
        return ("risk engine: " + "; ".join(ctx.account_blocks[:3]) + ": the model was not consulted", [])
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
        # the desk's statistics without its example list: the list repeated what the statistics say
        "history": ({k: v for k, v in ctx.history.items() if k != "closest_examples"} if ctx.history is not None
                    else {"available": False, "reason": "no history desk"}),
        "market_map": ctx.market_map if ctx.market_map is not None else {"available": False},
        "strategy_desk": ctx.strategy_desk if ctx.strategy_desk is not None else {"available": False},
        "intermarket": ctx.intermarket if ctx.intermarket is not None else {"available": False,
                                                                            "reason": "not provided by this data source"},
    }


def _scalars(x):
    """The top-level numbers, words and flags of a section; nested lists and tables dropped."""
    if not isinstance(x, dict):
        return x
    return {k: v for k, v in x.items() if isinstance(v, (int, float, str, bool)) or v is None}


def _trim(x, n: int):
    """Every list inside `x` cut to its last `n` items (the most recent bars/events)."""
    if isinstance(x, list):
        return [_trim(v, n) for v in x[-n:]]
    if isinstance(x, dict):
        return {k: _trim(v, n) for k, v in x.items()}
    return x


def compact_packet(packet: dict, level: int) -> dict:
    """A shorter view of the same market for a provider whose request limit the full packet exceeds.

    Nothing is invented or summarised by guesswork: sections are only cut, least important first,
    and the packet says so. The quote, account, regime, the member's own role and what the team
    has said are always kept.
    1: the desk statistics (strategy desk, history, intermarket) keep only their headline numbers;
    2: also the market map, memory and calendar, and every bar list is cut to its last 5 entries;
    3: those sections are dropped, the timeframes are H1/H4/D1 with 3 bars, the discussion is abridged."""
    p = dict(packet)
    heavy = ("strategy_desk", "history", "intermarket")
    for k in heavy:
        if k in p:
            p[k] = _scalars(p[k])
    if level >= 2:
        for k in ("market_map", "memory"):
            if k in p:
                p[k] = _scalars(p[k])
        if isinstance(p.get("calendar"), dict):
            p["calendar"] = _trim(p["calendar"], 3)
        if "timeframes" in p:
            p["timeframes"] = _trim(p["timeframes"], 5)
    if level >= 3:
        for k in heavy + ("market_map", "memory"):
            p.pop(k, None)
        if isinstance(p.get("timeframes"), dict):
            p["timeframes"] = {k: _trim(v, 3) for k, v in p["timeframes"].items() if k in ("H1", "H4", "D1")}
        if isinstance(p.get("quant_agents"), dict):
            p["quant_agents"] = {k: {"summary": v.get("summary")} for k, v in p["quant_agents"].items()}
        if isinstance(p.get("discussion"), list):
            p["discussion"] = [{k: (str(v)[:200] if isinstance(v, str) else v) for k, v in d.items()}
                               for d in p["discussion"]]
    p["packet_note"] = (f"shortened view (level {level}) to fit this provider's request limit: some sections "
                        "were cut or omitted, never altered")
    return p


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
        float(entry), stop, target, f"stop {stop:.5g}, target {target:.5g}, time exit after {hold_minutes(p)} min",
        "LLM", FAMILY, None, None, None, None, None, None, 1.0,
        str(p.get("invalidation") or "")[:300] or None, None, agents,
        {"note": "model-proposed; no measured expectancy exists until its forward record does",
         "reward_risk": round(rr, 3), **(evidence or {})}, 1, v,
        max_hold_minutes=hold_minutes(p))


def call_record(res) -> dict:
    """One model call as recorded on a decision: who answered, how, how fast, and its token count.
    Never the key, never the prompt."""
    provider = getattr(res, "provider", None)
    model = res.model
    if provider and model and provider != "default" and model.startswith(provider + ":"):
        model = model[len(provider) + 1:]
    return {"provider": provider, "model": model, "status": res.status, "ok": bool(res.ok),
            "latency_ms": round(float(res.latency_ms or 0.0), 1), "tokens": res.tokens, "error": res.error,
            "cached": bool(getattr(res, "cached", False))}


def with_ai(d: Decision, ai: dict, verdict: str | None) -> Decision:
    d.ai, d.ai_verdict = ai, verdict
    return d


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
                                     validate_trader_reply, cache_key=f"{ctx.symbol}|{ctx.t}", shrink=compact_packet)
        ai = call_record(res)
        if not res.ok:
            return with_ai(no_trade(f"language model unavailable or reply rejected ({res.status}): failing closed"),
                           ai, None)
        p = res.data
        ai["view"] = model_view(p)
        memory_note = {"agent": "llm_trader", "claim": f"memory used: {str(p.get('memory_used') or 'none')[:200]}",
                       "model": res.model}
        if p["action"] == "UNCERTAIN":
            return with_ai(no_trade(f"model UNCERTAIN: {str(p.get('thesis') or 'mixed evidence')[:400]}",
                                    support=[memory_note]), ai, "UNCERTAIN")
        if p["action"] == "NO_TRADE":
            return with_ai(no_trade(f"model: {str(p.get('thesis') or 'no trade')[:400]}", support=[memory_note]),
                           ai, "NO_TRADE")
        problem = level_problem(ctx, p)
        if problem:
            return with_ai(no_trade(problem), ai, "TRADE")
        hit = lesson_block(ctx, 1 if p["action"] == "BUY" else -1)
        if hit:
            return with_ai(no_trade(f"validated lesson {hit['lesson_id']}: {hit['statement']}",
                                    contra=[{"code": "LESSON_MATCH", "severity": "BLOCKING", "message": hit["statement"]}]),
                           ai, "TRADE")
        return with_ai(trade_decision(ctx, did, v, agents, reports, p, [memory_note]), ai, "TRADE")

    # ── manage an open trade ────────────────────────────────────────────

    def review(self, packet: dict) -> dict | None:
        """HOLD or CLOSE for one open position, or None when no model answered (the position simply
        keeps its broker-side stop and target: an unanswered review never closes anything)."""
        if self.llm is None or not self.llm.config.enabled:
            return None
        res = self.llm.complete_json("reviewer", REVIEW.format(time=packet.get("time")), packet, validate_review)
        if not res.ok:
            return None
        return {"action": res.data["action"], "reason": str(res.data.get("reason") or "")[:300], "model": res.model}

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
