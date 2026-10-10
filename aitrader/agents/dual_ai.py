"""The dual-AI trading desk: two professional traders on two different FREE OpenRouter models (docs/DUAL_AI.md).

    MARKET DATA -> CHART IMAGE -> TRADER 1 (vision) -> TRADER 2 (independent) -> SAME SIDE: AGREEMENT
                                                                              -> DIFFERENT: ONE DEBATE (verifier)
                -> FINAL BUY or SELL with entry / stop / target -> RISK ENGINE -> HARD RISK GATE -> PAPER BROKER

Selected with DECISION_MODE=dual_ai, and only with MODE=PAPER_FORWARD (the service refuses any other mode; a
context in another mode is answered NO_TRADE here as well).

THE AI DECIDES DIRECTION. Each trader must choose BUY or SELL: the side with the higher probability now, with an
entry, stop, target, risk:reward, confidence and the reasoning (structure, liquidity, momentum, trend, reversal
probability, invalidation). A mixed market is answered with the stronger side and a lower confidence, never
with a refusal.
  TRADER 1 (VisionTradingAnalyst) reads the chart image drawn from the same completed bars (charts/render.py),
  with the market data and every chart mark as numbers.
  TRADER 2 (IndependentTradingJudge) is a different model: it reads the raw data (OHLCV rows on both timeframes,
  volatility, spread, costs, structure, calendar), the chart (the image when its model can read images, its
  marks as numbers always) and Trader 1's analysis, forms its own view and picks its own side.
  SAME SIDE -> AGREEMENT: the trade candidate takes the levels of the more confident trader (Trader 1 on a tie).
  DIFFERENT SIDES -> ONE DEBATE: a third free model (another family when one exists) reads both analyses, the
  data and the chart and must pick BUY or SELL, saying why; the winner's levels are used. No second round.

THE RISK ENGINE DECIDES SAFETY. The candidate goes to the SAME risk engine, hard risk gate and execution engine
as every other decision. They size it and may refuse it (stop and target sanity, spread, costs, reward:risk,
daily loss, drawdown, exposure, every hard rule). No AI sizes anything, changes a limit or reaches the broker,
and a stated confidence never changes a size.

NO_TRADE is never a market opinion here. It means the decision could not be made at all:
- MARKET_UNAVAILABLE: stale or bad data, no quote, a position already open on the pair, trading paused, or the
  risk engine's account checks already refuse any trade (nothing is spent asking);
- AI_UNAVAILABLE: no OpenRouter key configured;
- NO_CHART, or a trader / the debate gave no usable answer (unavailable, quota spent, malformed): no decision
  is made on one trader alone, and a reply is never repaired;
- a validated lesson (confirmed out of sample) matching this exact context.

STRICT VALIDATION. A reply is one JSON object: a missing, wrongly typed, non-finite or out-of-range field, a side
other than BUY/SELL, a stop or target on the wrong side of the executable price, an entry more than 1 H1 ATR from
it (a misread price), a stop beyond 12 or a target beyond 15 H1 ATR, or a stated risk:reward that its own levels
contradict makes that reply unusable.

LEARNING is statistical only: each decision records both traders' answers, models and confidences, the rule
(AGREE / DEBATE) and the debate's choice; closed trades are scored per trader; the side that lost a debate is
followed forward as if taken, so whether the debate picks the better side is measured. Trader 2 and the
verifier are shown these measured records (LEARNING weeks only). No rule here moves with results.
"""

from __future__ import annotations

import dataclasses
import json
import math
import threading
from datetime import datetime, timezone
from pathlib import Path

from ..charts.render import RENDER_VERSION, Chart, render_chart
from ..data.resample import resample
from ..decision.synthesis import Decision, decision_id
from ..llm.free_models import FREE_MODELS_VERSION
from ..llm.openrouter import OPENROUTER_VERSION
from .llm_trader import MAX_STOP_ATR, agent_digest, no_trade_decision, pre_model_block, trade_decision, with_ai
from .types import MarketContext

DUAL_AI_VERSION = "dual-ai-1.0.0"
FAMILY = "DUAL_AI"
#: The side that lost a debate, followed forward under its own name: never mixed with the trades taken, in any
#: statistic or lesson scope.
LOSER_FAMILY, LOSER_SUFFIX = "DUAL_AI_DEBATE_LOSER", ":debate-loser"
SIDES = ("BUY", "SELL")
ENTRY_TOL_ATR = 1.0       # a market order: a stated entry further than this from the executable price is a misread
MAX_TARGET_ATR = 15.0
RR_ABS_TOL, RR_REL_TOL = 0.25, 0.20
HOLD_MINUTES = {"M15": 8 * 60, "H1": 48 * 60}
MIN_EXEC_BARS = {"M15": 60}  # fewer completed M15 bars than this: the chart executes on H1
EXEC_ROWS, HTF_ROWS = 60, 30
MAX_TOKENS = {"vision": 6000, "judge": 6000, "verifier": 5000}  # reasoning models think before they answer
CHART_KEEP = 300  # chart files kept on disk

_SCHEMA = """{{"direction": "BUY|SELL", "entry": <price>, "stop_loss": <price>, "take_profit": <price>,
  "confidence": <0-100>, "risk_reward": <reward/risk from your own levels>,
  "market_structure": "...", "liquidity": "...", "momentum": "...", "trend": "...",
  "reversal_probability": <0-100>, "invalidation": <the price that proves this side wrong>,
  "reason": "at most 4 sentences"}}"""

TRADER1_SYSTEM = """You are TRADER 1 on a professional trading desk: an experienced discretionary trader reading ONE
chart image of one instrument, now. The time is {time} UTC; treat it as the present and use nothing you may know
about prices or events after it.

The image: a header (instrument, bid/ask/spread, trend, ATR, volatility), the execution timeframe above and the
higher timeframe below. Marks: confirmed swings (HH/HL/LH/LL), BOS/CHoCH structure breaks, the order block, fair
value gaps, equal highs/lows (liquidity), sweeps, displacement candles, support/resistance, previous day/week
levels, the price and the ENTRY ZONE. Only completed bars are drawn. The JSON lists every mark with its exact
price and the market data: use those numbers, not pixel estimates.

Your job is to FIND THE SIDE WITH THE HIGHER PROBABILITY. You MUST choose BUY or SELL. When the picture is mixed,
choose the stronger side and let your confidence say how strong it is: a low confidence is a valid answer, a
refusal is not. Read the structure, the liquidity, the momentum, the trend on both timeframes and the chance of
a reversal, and place the trade as a professional would:
- the order is a market order: BUY fills at the ask, SELL at the bid; your entry is the current price, inside
  the ENTRY ZONE;
- the stop goes beyond the level that proves your side wrong; the target at a level price can reach within
  {hold} minutes given the volatility;
- you do not size the trade and you do not decide whether it may be taken: a second, independent trader gives
  his own view and a risk engine sizes the trade and may refuse it.

Reply with ONE JSON object only, no other text:
""" + _SCHEMA

TRADER2_SYSTEM = """You are TRADER 2 on a professional trading desk: an independent, experienced trader. You analyse
the same instrument, now, from the raw market data: completed OHLC bars on both timeframes (tick counts, not
traded volume: spot FX has none), volatility, spread and costs, market structure, the economic calendar, the
chart (the image if you can see it; its marks as numbers in "chart_marks" either way) and the desk's measured
record. The time is {time} UTC; treat it as the present and use nothing you may know about later prices or events.

Trader 1 has given his read in "trader1_analysis". Form YOUR OWN view first from the data, then compare: you may
agree or disagree, but agreeing because Trader 1 said so is not analysis. Say what in the data decides it.

Your job is to find the side with the higher probability. You MUST choose BUY or SELL. When the picture is
mixed, choose the stronger side and let your confidence say how strong it is: a refusal is not an answer. The
order is a market order (BUY at the ask, SELL at the bid); the stop goes beyond your invalidation; the target at
a level reachable within {hold} minutes. A risk engine sizes the trade and may refuse it.

Reply with ONE JSON object only, no other text:
""" + _SCHEMA

VERIFY_SYSTEM = """You are the DESK HEAD settling a disagreement: two professional traders analysed the same instrument
and chose opposite sides ("trader1_analysis", "trader2_analysis"). You have the market data, the chart (the
image if you can see it; its marks as numbers in "chart_marks" either way) and both arguments. The time is
{time} UTC; treat it as the present.

Decide which side is stronger and why. You MUST choose BUY or SELL: one of the two traders' sides. Judge the
arguments against the data, not the confidence each trader claimed.
Reply with ONE JSON object only, no other text:
{{"direction": "BUY|SELL", "confidence": <0-100>, "reason": "why this side's argument wins, at most 4 sentences"}}"""


# ── validation: a reply is used exactly as given, or not at all ─────────

def _num(x) -> bool:
    return isinstance(x, (int, float)) and not isinstance(x, bool) and math.isfinite(x)


def _text(x) -> bool:
    return isinstance(x, str) and bool(x.strip())


def _pct(x) -> bool:
    return _num(x) and 0 <= x <= 100


def check_levels(direction: str, d: dict, px: dict) -> str | None:
    """The entry, stop, target and stated risk:reward of one answer, against the executable price, or why not."""
    for k in ("entry", "stop_loss", "take_profit"):
        if not _num(d.get(k)) or d[k] <= 0:
            return f"{k} must be a positive finite price"
    side = 1 if direction == "BUY" else -1
    entry, stop, target = float(d["entry"]), float(d["stop_loss"]), float(d["take_profit"])
    fill = px["ask"] if side > 0 else px["bid"]
    atr = px["atr"]
    if abs(entry - fill) > ENTRY_TOL_ATR * atr:
        return (f"entry {entry} is {abs(entry - fill) / atr:.2f} H1 ATR from the executable price {fill}: a market "
                f"order fills at the current price (at most {ENTRY_TOL_ATR} ATR away is accepted)")
    if (entry - stop) * side <= 0 or (fill - stop) * side <= 0:
        return f"stop_loss {stop} is on the wrong side for {direction} (entry {entry}, executable {fill})"
    if (target - entry) * side <= 0 or (target - fill) * side <= 0:
        return f"take_profit {target} is on the wrong side for {direction} (entry {entry}, executable {fill})"
    if abs(fill - stop) / atr > MAX_STOP_ATR:
        return f"stop {abs(fill - stop) / atr:.1f} H1 ATR away is beyond {MAX_STOP_ATR}: a typo, not a stop"
    if abs(target - fill) / atr > MAX_TARGET_ATR:
        return f"target {abs(target - fill) / atr:.1f} H1 ATR away is beyond {MAX_TARGET_ATR}"
    rr = abs(target - entry) / abs(entry - stop)
    stated = d.get("risk_reward")
    if not _num(stated) or stated <= 0:
        return "risk_reward must be a positive number"
    if abs(stated - rr) > max(RR_ABS_TOL, RR_REL_TOL * rr):
        return f"stated risk_reward {stated} contradicts its own levels ({rr:.2f})"
    return None


def validate_trader(d: dict, px: dict) -> str | None:
    """One trader's answer: a side, levels, confidence and reasoning; the analysis fields typed when given."""
    if d.get("direction") not in SIDES:
        return "direction must be BUY or SELL: the desk always chooses a side"
    if not _pct(d.get("confidence")):
        return "confidence must be a number from 0 to 100"
    if not _text(d.get("reason")):
        return "reason must be text"
    if d.get("reversal_probability") is not None and not _pct(d["reversal_probability"]):
        return "reversal_probability must be a number from 0 to 100"
    if d.get("invalidation") is not None and not (_num(d["invalidation"]) and d["invalidation"] > 0):
        return "invalidation must be a price"
    for k in ("market_structure", "liquidity", "momentum", "trend"):
        if d.get(k) is not None and not isinstance(d[k], str):
            return f"{k} must be text"
    return check_levels(d["direction"], d, px)


def validate_verifier(d: dict) -> str | None:
    if d.get("direction") not in SIDES:
        return "direction must be BUY or SELL: the debate must choose a side"
    if not _pct(d.get("confidence")):
        return "confidence must be a number from 0 to 100"
    return None if _text(d.get("reason")) else "reason must be text"


def _clean(d: dict | None, keys: tuple) -> dict | None:
    """The fields the record keeps of an answer: the schema's own, text cut short."""
    if not isinstance(d, dict):
        return None
    return {k: (str(d[k])[:600] if isinstance(d.get(k), str) else d.get(k)) for k in keys}


TRADER_KEYS = ("direction", "entry", "stop_loss", "take_profit", "confidence", "risk_reward", "market_structure",
               "liquidity", "momentum", "trend", "reversal_probability", "invalidation", "reason")
VERIFY_KEYS = ("direction", "confidence", "reason")


def resolve(t1: dict, t2: dict, verdict: dict | None = None) -> dict:
    """The desk's rule, pure: whose side and whose levels. Same side: the more confident trader's levels (Trader 1
    on a tie). Opposite sides: the side the debate chose, with that trader's levels; no verdict, no decision."""
    if t1["direction"] == t2["direction"]:
        lead = "trader1" if t1["confidence"] >= t2["confidence"] else "trader2"
        return {"outcome": "TRADE", "rule": "AGREE", "direction": t1["direction"], "levels_from": lead,
                "loser": None}
    if verdict is None:
        return {"outcome": "NO_TRADE", "rule": "DEBATE_UNRESOLVED", "direction": None, "levels_from": None,
                "loser": None}
    lead = "trader1" if verdict["direction"] == t1["direction"] else "trader2"
    return {"outcome": "TRADE", "rule": "DEBATE", "direction": verdict["direction"], "levels_from": lead,
            "loser": "trader2" if lead == "trader1" else "trader1"}


# ── the data each trader reads ──────────────────────────────────────────

def chart_frames(ctx: MarketContext):
    """(execution bars, higher-timeframe bars) from the context's completed bars: M15 execution when there
    is enough of it, else H1; H4 resampled from H1 as the higher timeframe."""
    bars = ctx.bars or {}
    h1 = bars.get("H1")
    m15 = bars.get("M15")
    ex = m15 if m15 is not None and len(m15.as_of(ctx.t)) >= MIN_EXEC_BARS["M15"] else h1
    htf = None
    if h1 is not None and len(h1):
        try:
            htf = resample(h1, "H4", as_of=ctx.t)
        except ValueError:
            htf = None
    return ex, htf


def build_chart(ctx: MarketContext) -> Chart:
    ex, htf = chart_frames(ctx)
    if ex is None:
        raise ValueError("no completed bars for this instrument")
    levels = (ctx.market_map or {}).get("levels") if isinstance(ctx.market_map, dict) else None
    return render_chart(ctx.symbol, ex, htf, as_of=ctx.t, bid=float(ctx.bid), ask=float(ctx.ask), h1_atr=ctx.atr,
                        levels=levels, entry_atr=ENTRY_TOL_ATR)


def _rows(bars, as_of: int, n: int) -> list:
    if bars is None:
        return []
    b = bars.as_of(as_of)
    b = b.take(slice(max(0, len(b) - n), len(b)))
    return [[datetime.fromtimestamp(int(b.open_time[i]), timezone.utc).strftime("%d %H:%M"),
             round(float(b.mid_open[i]), 5), round(float(b.mid_high[i]), 5), round(float(b.mid_low[i]), 5),
             round(float(b.mid_close[i]), 5), int(b.ticks[i])] for i in range(len(b))]


def _iso(t: int) -> str:
    return datetime.fromtimestamp(int(t), timezone.utc).strftime("%Y-%m-%d %H:%M")


def _with_image(packet: dict, chart: Chart) -> list:
    return [{"type": "text", "text": json.dumps(packet, default=str)},
            {"type": "image_url", "image_url": {"url": chart.data_url()}}]


def trader1_packet(ctx: MarketContext, chart: Chart, hold: int) -> dict:
    return {"instrument": ctx.symbol, "decision_time_utc": _iso(ctx.t), "quote": {"bid": ctx.bid, "ask": ctx.ask},
            "holding_time_minutes": hold, "costs": ctx.costs, "chart_marks": chart.facts,
            "timeframe_summaries": ctx.mtf,
            "regime": {k: v for k, v in ctx.regime.as_dict().items() if k != "reasons"}}


def market_packet(ctx: MarketContext, reports: dict, chart: Chart, hold: int) -> dict:
    ex, htf = chart_frames(ctx)
    return {
        "instrument": ctx.symbol, "decision_time_utc": _iso(ctx.t), "quote": {"bid": ctx.bid, "ask": ctx.ask},
        "holding_time_minutes": hold, "costs": ctx.costs,
        "volatility": {"atr_h1": ctx.atr, "atr_execution": chart.facts.get("atr14_execution"),
                       "state": chart.facts.get("volatility"), "atr_percentile": chart.facts.get("atr_percentile")},
        "bar_fields": ["open_utc", "open", "high", "low", "close", "tick_count (not traded volume)"],
        "execution_bars": {"timeframe": ex.timeframe if ex is not None else None, "rows": _rows(ex, ctx.t, EXEC_ROWS)},
        "higher_timeframe_bars": {"timeframe": htf.timeframe if htf is not None else None,
                                  "rows": _rows(htf, ctx.t, HTF_ROWS)},
        "timeframe_summaries": ctx.mtf, "market_structure": ctx.market_map, "chart_marks": chart.facts,
        "regime": {k: v for k, v in ctx.regime.as_dict().items() if k != "reasons"},
        "calendar": ctx.news if ctx.news is not None else {"feed": {"status": "NOT_CONFIGURED"}, "events": None},
        "quant_agents": {k: {"summary": r.summary, "objections": [f"{o.severity} {o.code}: {o.message}"
                                                                   for o in r.objections][:5]}
                         for k, r in reports.items()},
        "desk_measured_record": (ctx.memory_brief or {}).get("dual_ai"),
    }


def trader1_messages(ctx, chart, hold) -> list[dict]:
    return [{"role": "system", "content": TRADER1_SYSTEM.format(time=_iso(ctx.t), hold=hold)},
            {"role": "user", "content": _with_image(trader1_packet(ctx, chart, hold), chart)}]


def trader2_messages(ctx, reports, chart, t1, hold) -> list[dict]:
    packet = {**market_packet(ctx, reports, chart, hold), "trader1_analysis": _clean(t1, TRADER_KEYS)}
    return [{"role": "system", "content": TRADER2_SYSTEM.format(time=_iso(ctx.t), hold=hold)},
            {"role": "user", "content": _with_image(packet, chart)}]


def verify_messages(ctx, reports, chart, t1, t2, hold) -> list[dict]:
    packet = {**market_packet(ctx, reports, chart, hold), "trader1_analysis": _clean(t1, TRADER_KEYS),
              "trader2_analysis": _clean(t2, TRADER_KEYS)}
    return [{"role": "system", "content": VERIFY_SYSTEM.format(time=_iso(ctx.t))},
            {"role": "user", "content": _with_image(packet, chart)}]


class _Configured:
    """What `pre_model_block` asks of a provider: is one configured."""

    def __init__(self, ok: bool) -> None:
        self.config = type("C", (), {"enabled": ok})()


# ── the desk ────────────────────────────────────────────────────────────

class DualAITrader:
    def __init__(self, client=None, chart_dir: str | Path | None = None) -> None:
        self.client = client
        self.chart_dir = Path(chart_dir) if chart_dir else None
        self.charts: dict[str, dict] = {}   # symbol -> the last chart (PNG bytes and what it showed)
        self.last: dict | None = None        # the last analysis, for the dashboard
        self._lock = threading.Lock()

    def _keep_chart(self, ctx: MarketContext, chart: Chart, did: str) -> None:
        with self._lock:
            self.charts[ctx.symbol] = {"png": chart.png, "meta": chart.meta, "t": ctx.t, "decision_id": did}
        if self.chart_dir is None:
            return
        try:
            self.chart_dir.mkdir(parents=True, exist_ok=True)
            (self.chart_dir / f"{ctx.symbol}_{ctx.t}.png").write_bytes(chart.png)
            files = sorted(self.chart_dir.glob("*.png"), key=lambda p: p.stat().st_mtime)
            for old in files[:-CHART_KEEP]:
                old.unlink(missing_ok=True)
        except OSError:
            pass  # the chart's hash is on the decision record; a lost file loses only the picture

    def decide(self, ctx: MarketContext, reports: dict, versions: dict, llm_opinions=None) -> Decision:
        if ctx.mode == "BACKTEST":
            raise ValueError("the dual-AI desk cannot be backtested honestly: the models may know what happened "
                             "after the decision time")
        v = {**versions, "dual_ai": DUAL_AI_VERSION, "chart": RENDER_VERSION, "openrouter": OPENROUTER_VERSION,
             "free_models": FREE_MODELS_VERSION}
        did = decision_id(ctx.symbol, ctx.timeframe, ctx.t, ctx.mode, v)
        agents = agent_digest(reports)
        rec: dict = {"version": DUAL_AI_VERSION, "symbol": ctx.symbol, "t": ctx.t, "calls": [], "models": {},
                     "chart": None, "trader1": None, "trader2": None, "verifier": None, "consensus": None,
                     "regime": ctx.regime.label, "vol_state": ctx.regime.vol_state}

        def done(d: Decision, verdict: str | None) -> Decision:
            view = {"action": d.decision, "confidence": (rec.get("consensus") or {}).get("desk_confidence"),
                    "method": "dual_ai " + str((rec.get("consensus") or {}).get("rule") or ""),
                    "timeframe": (rec.get("chart") or {}).get("execution_timeframe")}
            m = rec["models"]
            ai = {"provider": "openrouter", "dual_ai": rec, "view": view,
                  "model": "+".join(x for x in (m.get("trader1"), m.get("trader2"), m.get("verifier")) if x) or None}
            d.family, d.template = FAMILY, FAMILY
            with self._lock:
                self.last = {"decision_id": d.id, "symbol": ctx.symbol, "t": ctx.t, "decision": d.decision,
                             "reason": d.no_trade_reason or d.thesis, **rec}
            return with_ai(d, ai, verdict)

        def stop(reason: str, rule: str, contra=None) -> Decision:
            rec["consensus"] = {**(rec.get("consensus") or {}), "outcome": "NO_TRADE", "rule": rule, "reason": reason}
            return done(no_trade_decision(ctx, did, v, agents, reason, contra), rule)

        if ctx.mode != "PAPER_FORWARD":
            return stop(f"DECISION_MODE=dual_ai runs in MODE=PAPER_FORWARD only (this context is {ctx.mode})", "MODE")
        client = self.client
        if client is None or not client.config.configured:
            return stop("OPENROUTER_API_KEY is not set: the traders cannot be asked", "AI_UNAVAILABLE")
        blocked = pre_model_block(ctx, reports, _Configured(True))
        if blocked:
            return stop("market unavailable for a decision: " + blocked[0], "MARKET_UNAVAILABLE", blocked[1])
        try:
            chart = build_chart(ctx)
        except (ValueError, TypeError) as exc:
            return stop(f"no chart could be drawn ({exc}): the traders were not consulted", "NO_CHART")
        rec["chart"] = chart.meta
        self._keep_chart(ctx, chart, did)
        px = {"bid": float(ctx.bid), "ask": float(ctx.ask), "atr": float(ctx.atr)}
        hold = HOLD_MINUTES.get(chart.meta["execution_timeframe"], HOLD_MINUTES["H1"])
        rec["hold_minutes"] = hold
        key = f"{ctx.symbol}|{ctx.t}|{chart.meta['sha256'][:16]}"

        def why(r) -> str:
            return f"{r.status}{': ' + r.error if r.error else ''}"

        # Trader 1: the chart
        r1 = client.chat_json("vision", trader1_messages(ctx, chart, hold), lambda d: validate_trader(d, px),
                              dedupe_key=key + "|trader1", max_tokens=MAX_TOKENS["vision"])
        rec["calls"].append(r1.record())
        rec["models"]["trader1"] = r1.model
        if r1.data is not None:
            rec["trader1"] = _clean(r1.data, TRADER_KEYS)
        if not r1.ok:
            return stop(f"Trader 1 (vision) gave no usable answer ({why(r1)}): no decision on one trader alone",
                        "TRADER1_UNAVAILABLE")
        t1 = r1.data

        # Trader 2: independent, on a different model
        r2 = client.chat_json("judge", trader2_messages(ctx, reports, chart, t1, hold),
                              lambda d: validate_trader(d, px), dedupe_key=key + "|trader2",
                              max_tokens=MAX_TOKENS["judge"], avoid=(r1.model,))
        rec["calls"].append(r2.record())
        rec["models"]["trader2"] = r2.model
        if r2.data is not None:
            rec["trader2"] = _clean(r2.data, TRADER_KEYS)
        if not r2.ok:
            return stop(f"Trader 2 (independent) gave no usable answer ({why(r2)}): no decision on one trader alone",
                        "TRADER2_UNAVAILABLE")
        t2 = r2.data

        verdict = None
        if t1["direction"] != t2["direction"]:
            # one debate: a third model when one exists, never a second round
            r3 = client.chat_json("verifier", verify_messages(ctx, reports, chart, t1, t2, hold), validate_verifier,
                                  dedupe_key=key + "|verifier", max_tokens=MAX_TOKENS["verifier"],
                                  avoid=tuple(m for m in (r1.model, r2.model) if m), avoid_soft=True)
            rec["calls"].append(r3.record())
            rec["models"]["verifier"] = r3.model
            if r3.data is not None:
                rec["verifier"] = _clean(r3.data, VERIFY_KEYS)
            if not r3.ok:
                return stop(f"the traders disagree (Trader 1 {t1['direction']}, Trader 2 {t2['direction']}) and the "
                            f"debate gave no usable answer ({why(r3)})", "DEBATE_UNRESOLVED")
            verdict = r3.data
        res = resolve(t1, t2, verdict)
        lead = t1 if res["levels_from"] == "trader1" else t2
        confs = [lead["confidence"]] + ([verdict["confidence"]] if verdict else
                                        [t2["confidence"] if lead is t1 else t1["confidence"]])
        rec["consensus"] = {**res, "desk_confidence": round(min(confs) / 100, 3),
                            "stop_loss": float(lead["stop_loss"]), "take_profit": float(lead["take_profit"])}
        if res["loser"]:
            lose = t1 if res["loser"] == "trader1" else t2
            rec["debate_loser"] = {"trader": res["loser"], "direction": lose["direction"],
                                   "stop_loss": float(lose["stop_loss"]), "take_profit": float(lose["take_profit"]),
                                   "hold_minutes": hold}
        hit = _lesson(ctx, 1 if res["direction"] == "BUY" else -1)
        if hit:
            return stop(f"validated lesson {hit['lesson_id']}: {hit['statement']}", "LESSON",
                        [{"code": "LESSON_MATCH", "severity": "BLOCKING", "message": hit["statement"]}])
        story = (f"{res['rule']}: Trader 1 ({r1.model}) {t1['direction']} {t1['confidence']}: {t1['reason']} | "
                 f"Trader 2 ({r2.model}) {t2['direction']} {t2['confidence']}: {t2['reason']}")
        if verdict:
            story += f" | debate ({rec['models'].get('verifier')}) {verdict['direction']}: {verdict['reason']}"
        p = {"action": res["direction"], "timeframe": chart.meta["execution_timeframe"],
             "stop": float(lead["stop_loss"]), "target": float(lead["take_profit"]), "max_hold_minutes": hold,
             "thesis": story[:500],
             "invalidation": (f"price trades through {lead['invalidation']}" if _num(lead.get("invalidation"))
                              else f"price trades through the stop {float(lead['stop_loss'])}")}
        d = trade_decision(ctx, did, v, agents, reports, p,
                           [{"agent": "dual_ai", "claim": f"{res['rule']}: levels from {res['levels_from']}",
                             "models": rec["models"]}], evidence={"consensus": res["rule"]})
        return done(d, res["rule"])

    def chart_png(self, symbol: str) -> bytes | None:
        with self._lock:
            c = self.charts.get(symbol)
            return c["png"] if c else None


def _lesson(ctx: MarketContext, side: int) -> dict | None:
    kv = ctx.knowledge
    if kv is not None and hasattr(kv, "lessons_matching"):
        hits = kv.lessons_matching(FAMILY, ctx.regime.label, ctx.regime.vol_state, side, ctx.t)
        if hits:
            return hits[0]
    return None


def counterfactual_decision(d: Decision) -> Decision | None:
    """The side that lost a debate, as a decision record for the forward ledger only: followed forward as if it
    had been taken, so whether the debate chose the better side is measured. Never sent anywhere."""
    lose = ((d.ai or {}).get("dual_ai") or {}).get("debate_loser")
    if not lose:
        return None
    return dataclasses.replace(d, id=d.id + LOSER_SUFFIX, decision=lose["direction"], stop_loss=lose["stop_loss"],
                               take_profit=lose["take_profit"], max_hold_minutes=lose["hold_minutes"],
                               family=LOSER_FAMILY, template=LOSER_FAMILY, signal_class=LOSER_FAMILY,
                               edge_status="EXPERIMENTAL", ai_verdict="LOST_THE_DEBATE")


__all__ = ["DUAL_AI_VERSION", "DualAITrader", "FAMILY", "LOSER_FAMILY", "LOSER_SUFFIX", "build_chart",
           "check_levels", "counterfactual_decision", "resolve", "validate_trader", "validate_verifier"]
