"""The dual-AI trading desk: two professional traders on two different FREE OpenRouter models (docs/DUAL_AI.md).

    MARKET DATA -> CHART IMAGE -> TRADER 1 (vision) -> TRADER 2 (independent) -> SAME SIDE: AGREEMENT
                -> BUY or SELL with entry / stop / target -> RISK ENGINE -> HARD RISK GATE -> PAPER BROKER
                                                                              -> DIFFERENT: NO TRADE
                                                                                 (one debate, in shadow only)

Selected with DECISION_MODE=dual_ai, and only with MODE=PAPER_FORWARD (the service refuses any other mode; a
context in another mode is answered NO_TRADE here as well).

THE AI DECIDES DIRECTION. Each trader must choose BUY or SELL: the side with the higher probability now, with an
entry, stop, target, risk:reward, confidence and the reasoning (structure, liquidity, momentum, trend, reversal
probability, invalidation). A mixed market is answered with the stronger side and a lower confidence, never
with a refusal.
  TRADER 1 (VisionTradingAnalyst) reads the chart image drawn from the same completed bars (charts/render.py),
  with the market data and every chart mark as numbers. When no free vision model gives a usable answer, it
  reads the same chart from those numbers on a text model (recorded: trader1_input "numbers").
  TRADER 2 (IndependentTradingJudge) is a different model: it reads the raw data (OHLCV rows on both timeframes,
  volatility, spread, costs, structure, calendar), the chart (the image when its model can read images, its
  marks as numbers always) and Trader 1's analysis, forms its own view and picks its own side.
  SAME SIDE -> AGREEMENT: the trade candidate takes the levels of the more confident trader (Trader 1 on a tie).
  DIFFERENT SIDES -> NO TRADE (DISAGREE): two independent traders on opposite sides is an unclear market, and
  the desk stands aside. One debate still runs, IN SHADOW: a third free model (another family when one exists)
  reads both analyses, the data and the chart and must pick BUY or SELL; its pick and the side it rejected are
  followed forward as if taken and never traded, so whether standing aside was right is measured. No second round.

THE RISK ENGINE DECIDES SAFETY. The candidate goes to the SAME risk engine, hard risk gate and execution engine
as every other decision. They size it and may refuse it (stop and target sanity, spread, costs, reward:risk,
daily loss, drawdown, exposure, every hard rule). No AI sizes anything, changes a limit or reaches the broker,
and a stated confidence never changes a size.

NO_TRADE is a market opinion here in one case only: the traders disagree (DISAGREE). Otherwise it means the
decision could not be made at all:
- NOT_ASKED (MARKET_UNAVAILABLE before 1.6.0): stale or bad data, no quote, a position already open on the pair,
  trading paused, or the risk engine already refuses any trade (the calendar, a news window, full positions);
  nothing is spent asking, and the reason says which;
- AI_UNAVAILABLE: no OpenRouter key configured;
- NO_CHART, or a trader gave no usable answer (unavailable, quota spent, malformed): no decision is made on one
  trader alone, and a reply is never repaired;
- a validated lesson (confirmed out of sample) matching this exact context.

STRICT VALIDATION. A reply is one JSON object: a missing, wrongly typed, non-finite or out-of-range field, a side
other than BUY/SELL, a stop or target on the wrong side of the executable price, an entry more than 1 H1 ATR from
it (a misread price), a stop beyond 12 or a target beyond 15 H1 ATR, or a stated risk:reward that its own levels
contradict makes that reply unusable.

LEARNING is statistical only: each decision records both traders' answers, models and confidences, the rule
(AGREE / DISAGREE) and the shadow debate's choice; closed trades are scored per trader; on a disagreement the
debate's pick and the side it rejected are both followed forward as if taken, so what standing aside skipped
and whether the debate picks the better side are measured. Trader 2 and the verifier are shown these measured
records (LEARNING weeks only). No rule here moves with results.
"""

from __future__ import annotations

import dataclasses
import json
import math
import threading
import time
from datetime import datetime, timezone
from pathlib import Path

from ..charts.render import RENDER_VERSION, Chart, render_chart
from ..data.resample import resample
from ..decision.synthesis import Decision, decision_id
from ..llm.free_models import FREE_MODELS_VERSION
from ..llm.openrouter import OPENROUTER_VERSION
from .llm_trader import MAX_STOP_ATR, agent_digest, no_trade_decision, pre_model_block, trade_decision, with_ai
from .types import MarketContext

#: 1.1.0 (live check): the traders are told the risk engine's per-trade limits (minimum stop distance, minimum
#:        reward:risk) so their levels can be executed; the analysis fields are recorded as given (text or number) and
#:        never void a trade; the trade fields stay exact.
#: 1.2.0 (operator's choice, 2026-10-13): a trade only when both traders choose the same side. Opposite sides are
#:        NO_TRADE (DISAGREE); the debate runs in shadow and its pick and the side it rejected are followed forward,
#:        never traded. (1.1.0 traded the debate's pick: 4 debate trades so far, too few to judge either way.)
#: 1.3.0 (live, 2026-10-13: 23 of 40 decisions lost when every free vision model was busy at peak hours): when no
#:        vision model gives a usable answer, Trader 1 reads the same chart from its numbers (every mark at its exact
#:        price) on a text model of the third pool, never one already asked for the decision; recorded as
#:        trader1_input "numbers" (else "image"). The image prompt is unchanged.
#: 1.4.0 (live, 2026-10-14: 27 of 51 agreements refused by the risk engine for their levels; in 13 the other
#:        trader's own levels respected its limits): when both choose the same side and the more confident trader's
#:        levels fall inside the risk engine's published per-trade limits (RiskEngine.trade_limits: minimum stop
#:        distance, minimum reward:risk, at the executable price) while the other's respect them, the other's are
#:        used. Both are the traders' own, never edited; the risk engine still decides.
#: 1.5.0 (live, 2026-10-16: two agreements refused as stale, 933 s and 1103 s old, after the other pair's shadow
#:        debate waited 420 s on a busy model): every call has a time budget. A trader is asked only while the
#:        decision can still execute in time (MarketContext.decide_within_s), and never for longer than is left;
#:        the shadow debate, measurement only, waits at most SHADOW_DEBATE_DEADLINE_S. Prompts are unchanged.
#: 1.6.0 (operator, 2026-10-19): a decision refused before the traders are asked is NOT_ASKED, with the refusal
#:        as its reason ("risk engine: trading_calendar (...)"); it read "market unavailable for a decision", 88
#:        times that day, when the market was there and a rule had refused. Record only: nothing decides by it.
DUAL_AI_VERSION = "dual-ai-1.6.0"
FAMILY = "DUAL_AI"
#: The two sides of a disagreement, followed forward under their own names (never traded): the side the shadow
#: debate picked, and the side it rejected. Never mixed with the trades taken, in any statistic or lesson scope.
PICK_FAMILY, PICK_SUFFIX = "DUAL_AI_DEBATE_PICK", ":debate-pick"
LOSER_FAMILY, LOSER_SUFFIX = "DUAL_AI_DEBATE_LOSER", ":debate-loser"
SHADOW = {PICK_FAMILY: (PICK_SUFFIX, "DEBATE_PICK_NOT_TRADED"), LOSER_FAMILY: (LOSER_SUFFIX, "LOST_THE_DEBATE")}
SIDES = ("BUY", "SELL")
ENTRY_TOL_ATR = 1.0       # a market order: a stated entry further than this from the executable price is a misread
MAX_TARGET_ATR = 15.0
RR_ABS_TOL, RR_REL_TOL = 0.25, 0.20
HOLD_MINUTES = {"M15": 8 * 60, "H1": 48 * 60}
MIN_EXEC_BARS = {"M15": 60}  # fewer completed M15 bars than this: the chart executes on H1
EXEC_ROWS, HTF_ROWS = 60, 30
MAX_TOKENS = {"vision": 12000, "judge": 12000, "verifier": 12000}  # reasoning models think before they answer
CALL_DEADLINE_S = 420.0          # a trader's call, across its retries and fallbacks
SHADOW_DEBATE_DEADLINE_S = 120.0  # the shadow debate is measurement only: it never holds up the next decision long
MIN_CALL_S = 30.0                # less time left than this: the trader is not asked (its answer would come too late)
#: Trader 1 reads the chart as numbers on a text model only when no vision model gave a usable answer, never after
#: a stop that another model would not fix (no key, budget or quota spent, spend on the key, a policy block)
NO_FALLBACK = frozenset({"NOT_CONFIGURED", "BUDGET", "DAILY_QUOTA", "KEY_REJECTED", "PAID_USAGE", "NOT_FREE",
                         "WRONG_MODEL", "DATA_POLICY"})
CHART_KEEP = 300  # chart files kept on disk

_SCHEMA = """{{"direction": "BUY|SELL", "entry": <price>, "stop_loss": <price>, "take_profit": <price>,
  "confidence": <0-100>, "risk_reward": <reward/risk from your own levels>,
  "market_structure": "...", "liquidity": "...", "momentum": "...", "trend": "...",
  "reversal_probability": <0-100>, "invalidation": <the price that proves this side wrong>,
  "reason": "at most 4 sentences"}}"""

_T1_IMAGE = """You are TRADER 1 on a professional trading desk: an experienced discretionary trader reading ONE
chart image of one instrument, now. The time is {time} UTC; treat it as the present and use nothing you may know
about prices or events after it.

The image: a header (instrument, bid/ask/spread, trend, ATR, volatility), the execution timeframe above and the
higher timeframe below. Marks: confirmed swings (HH/HL/LH/LL), BOS/CHoCH structure breaks, the order block, fair
value gaps, equal highs/lows (liquidity), sweeps, displacement candles, support/resistance, previous day/week
levels, the price and the ENTRY ZONE. Only completed bars are drawn. The JSON lists every mark with its exact
price and the market data: use those numbers, not pixel estimates.

"""
#: Trader 1 when no free vision model gives a usable answer: the same chart, read from its numbers
_T1_NUMBERS = """You are TRADER 1 on a professional trading desk: an experienced discretionary trader reading ONE
chart of one instrument, now. The time is {time} UTC; treat it as the present and use nothing you may know
about prices or events after it.

The chart image could not be read this time, so you read the same chart from its numbers. The JSON gives the
quote, costs, volatility and timeframe summaries, and in "chart_marks" every mark of the chart with its exact
price, on the execution and the higher timeframe: confirmed swings (HH/HL/LH/LL), BOS/CHoCH structure breaks, the
order block, fair value gaps, equal highs/lows (liquidity), sweeps, displacement candles, support/resistance,
previous day/week levels, the price and the ENTRY ZONE. Only completed bars are used.

"""
_T1_TASK = """Your job is to FIND THE SIDE WITH THE HIGHER PROBABILITY. You MUST choose BUY or SELL. When the picture is mixed,
choose the stronger side and let your confidence say how strong it is: a low confidence is a valid answer, a
refusal is not. Read the structure, the liquidity, the momentum, the trend on both timeframes and the chance of
a reversal, and place the trade as a professional would:
- the order is a market order: BUY fills at the ask, SELL at the bid; your entry is the current price, inside
  the ENTRY ZONE;
- the stop goes beyond the level that proves your side wrong; the target at a level price can reach within
  {hold} minutes given the volatility;
- the risk engine refuses a stop closer to the entry than costs.risk_engine_limits.min_stop_distance and a
  reward:risk below min_reward_risk: place levels that respect them, or the trade will not be executed;
- you do not size the trade and you do not decide whether it may be taken: a second, independent trader gives
  his own view and a risk engine sizes the trade and may refuse it.

Reply with ONE JSON object only, no other text:
""" + _SCHEMA
TRADER1_SYSTEM = _T1_IMAGE + _T1_TASK
TRADER1_NUMBERS_SYSTEM = _T1_NUMBERS + _T1_TASK

TRADER2_SYSTEM = """You are TRADER 2 on a professional trading desk: an independent, experienced trader. You analyse
the same instrument, now, from the raw market data: completed OHLC bars on both timeframes (tick counts, not
traded volume: spot FX has none), volatility, spread and costs, market structure, the economic calendar, the
chart (the image if you can see it; its marks as numbers in "chart_marks" either way) and the desk's measured
record. The time is {time} UTC; treat it as the present and use nothing you may know about later prices or events.

Trader 1 has given his read in "trader1_analysis". Form YOUR OWN view first from the data, then compare: you may
agree or disagree, but agreeing because Trader 1 said so is not analysis. Say what in the data decides it.

Your job is to find the side with the higher probability. You MUST choose BUY or SELL. When the picture is
mixed, choose the stronger side and let your confidence say how strong it is: a refusal is not an answer. The
order is a market order (BUY at the ask, SELL at the bid); the stop goes beyond your invalidation, and no closer to
the entry than costs.risk_engine_limits.min_stop_distance; the target at a level reachable within {hold} minutes,
with reward:risk at least min_reward_risk. A risk engine sizes the trade and may refuse it.

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


#: The fields that decide the trade: each must be exactly right, or the answer is unusable.
TRADE_FIELDS = ("direction", "entry", "stop_loss", "take_profit", "confidence", "risk_reward", "reason")
#: The trader's description of the market: recorded as given (text or number), never used to price, size or route
#: a trade, so a model writing "below the 1.0850 low" where a bare price was asked does not void its trade
#: (found by the live check). A list, an object or a boolean there is still a malformed answer.
ANALYSIS_FIELDS = ("market_structure", "liquidity", "momentum", "trend", "reversal_probability", "invalidation")


def validate_trader(d: dict, px: dict) -> str | None:
    """One trader's answer: a side, levels, confidence and reasoning exactly; the analysis fields as text or number."""
    if d.get("direction") not in SIDES:
        return "direction must be BUY or SELL: the desk always chooses a side"
    if not _pct(d.get("confidence")):
        return "confidence must be a number from 0 to 100"
    if not _text(d.get("reason")):
        return "reason must be text"
    for k in ANALYSIS_FIELDS:
        v = d.get(k)
        if v is not None and not isinstance(v, str) and not _num(v):
            return f"{k} must be text or a number"
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
    """The desk's rule, pure: whose side and whose levels. Same side: a trade, on the more confident trader's levels
    (Trader 1 on a tie). Opposite sides: no trade, whatever the debate says; the debate's pick (when it answered)
    and the side it rejected are named for the shadow record only."""
    if t1["direction"] == t2["direction"]:
        lead = "trader1" if t1["confidence"] >= t2["confidence"] else "trader2"
        return {"outcome": "TRADE", "rule": "AGREE", "direction": t1["direction"], "levels_from": lead}
    pick = None if verdict is None else "trader1" if verdict["direction"] == t1["direction"] else "trader2"
    return {"outcome": "NO_TRADE", "rule": "DISAGREE", "direction": None, "levels_from": None,
            "debate_pick": None if verdict is None else verdict["direction"], "pick_from": pick,
            "loser": None if pick is None else "trader2" if pick == "trader1" else "trader1"}


def fits_limits(t: dict, px: dict, lim: dict | None) -> bool:
    """Whether a trader's own levels respect the risk engine's published per-trade limits at the executable price.
    Used only to choose between the two traders' levels when both chose the same side: the risk engine still
    decides, with the live quote at the time. Unknown limits give no preference."""
    if not lim:
        return True
    side = 1 if t["direction"] == "BUY" else -1
    e = px["ask"] if side > 0 else px["bid"]
    stop = abs(e - float(t["stop_loss"]))
    return stop > 0 and stop >= float(lim["min_stop_distance"]) and (
        abs(float(t["take_profit"]) - e) / stop >= float(lim["min_reward_risk"]))


def _shadow_side(t: dict, who: str, family: str, hold: int) -> dict:
    return {"family": family, "trader": who, "direction": t["direction"], "stop_loss": float(t["stop_loss"]),
            "take_profit": float(t["take_profit"]), "hold_minutes": hold}


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


def trader1_numbers_messages(ctx, chart, hold) -> list[dict]:
    """Trader 1 on a text model: the same packet (every chart mark at its exact price), no image."""
    return [{"role": "system", "content": TRADER1_NUMBERS_SYSTEM.format(time=_iso(ctx.t), hold=hold)},
            {"role": "user", "content": json.dumps(trader1_packet(ctx, chart, hold), default=str)}]


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
            return stop(blocked[0], "NOT_ASKED", blocked[1])
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
        started = time.monotonic()

        def why(r) -> str:
            return f"{r.status}{': ' + r.error if r.error else ''}"

        def budget(cap: float) -> float | None:
            """Seconds a call may take: its cap, or what is left before the decision would be too old to execute;
            None when too little is left to ask at all."""
            if ctx.decide_within_s is None:
                return cap
            rest = ctx.decide_within_s - (time.monotonic() - started)
            return min(cap, rest) if rest >= MIN_CALL_S else None

        def late(who: str) -> str:
            return (f"{who} was not asked: too little time left before the decision would be too old to execute "
                    f"({ctx.decide_within_s:.0f} s at the start)")

        # Trader 1: the chart image
        dl = budget(CALL_DEADLINE_S)
        if dl is None:
            return stop(late("Trader 1") + ": no decision", "TRADER1_UNAVAILABLE")
        r1 = client.chat_json("vision", trader1_messages(ctx, chart, hold), lambda d: validate_trader(d, px),
                              dedupe_key=key + "|trader1", max_tokens=MAX_TOKENS["vision"], deadline_s=dl)
        rec["calls"].append(r1.record())
        rec["models"]["trader1"] = r1.model
        rec["trader1_input"] = "image"
        failed = f"Trader 1 (vision) gave no usable answer ({why(r1)})"
        if not r1.ok and r1.status not in NO_FALLBACK:
            # no free vision model answered usably (busy, unavailable, an unusable reply): Trader 1 reads the same
            # chart from its numbers on a text model of the third pool (Trader 2's best model stays Trader 2's),
            # never one already asked for this decision; a reply is still used as given or not at all
            asked = tuple(m for m in [*(m for m, _ in r1.tried), r1.model] if m)
            dl = budget(CALL_DEADLINE_S)
            if dl is None:
                return stop(f"{failed}; {late('the chart as numbers')}: no decision on one trader alone",
                            "TRADER1_UNAVAILABLE")
            r1 = client.chat_json("trader1_numbers", trader1_numbers_messages(ctx, chart, hold),
                                  lambda d: validate_trader(d, px), dedupe_key=key + "|trader1-numbers",
                                  max_tokens=MAX_TOKENS["vision"], avoid=asked, deadline_s=dl)
            rec["calls"].append(r1.record())
            rec["models"]["trader1"] = r1.model
            rec["trader1_input"] = "numbers"
            failed += f"; on the chart's numbers: {why(r1)}"
        if r1.data is not None:
            rec["trader1"] = _clean(r1.data, TRADER_KEYS)
        if not r1.ok:
            return stop(f"{failed}: no decision on one trader alone", "TRADER1_UNAVAILABLE")
        t1 = r1.data

        # Trader 2: independent, on a different model
        dl = budget(CALL_DEADLINE_S)
        if dl is None:
            return stop(late("Trader 2") + ": no decision on one trader alone", "TRADER2_UNAVAILABLE")
        r2 = client.chat_json("judge", trader2_messages(ctx, reports, chart, t1, hold),
                              lambda d: validate_trader(d, px), dedupe_key=key + "|trader2",
                              max_tokens=MAX_TOKENS["judge"], avoid=(r1.model,), deadline_s=dl)
        rec["calls"].append(r2.record())
        rec["models"]["trader2"] = r2.model
        if r2.data is not None:
            rec["trader2"] = _clean(r2.data, TRADER_KEYS)
        if not r2.ok:
            return stop(f"Trader 2 (independent) gave no usable answer ({why(r2)}): no decision on one trader alone",
                        "TRADER2_UNAVAILABLE")
        t2 = r2.data

        if t1["direction"] != t2["direction"]:
            # opposite sides: no trade. One debate (a third model when one exists, never a second round) runs in
            # shadow: its pick and the side it rejected are followed forward as if taken, never traded.
            dl = budget(SHADOW_DEBATE_DEADLINE_S)
            r3 = None if dl is None else client.chat_json(
                "verifier", verify_messages(ctx, reports, chart, t1, t2, hold), validate_verifier,
                dedupe_key=key + "|verifier", max_tokens=MAX_TOKENS["verifier"],
                avoid=tuple(m for m in (r1.model, r2.model) if m), avoid_soft=True, deadline_s=dl)
            if r3 is not None:
                rec["calls"].append(r3.record())
                rec["models"]["verifier"] = r3.model
                if r3.data is not None:
                    rec["verifier"] = _clean(r3.data, VERIFY_KEYS)
            res = resolve(t1, t2, r3.data if r3 is not None and r3.ok else None)
            rec["consensus"] = res
            if res["pick_from"]:
                sides = {"trader1": t1, "trader2": t2}
                rec["shadow"] = [_shadow_side(sides[res["pick_from"]], res["pick_from"], PICK_FAMILY, hold),
                                 _shadow_side(sides[res["loser"]], res["loser"], LOSER_FAMILY, hold)]
            seen = (f"the debate ({r3.model}) would have chosen {res['debate_pick']}: followed forward in shadow, "
                    "not traded" if res["pick_from"] else late("the shadow debate") if r3 is None else
                    f"the shadow debate gave no usable answer ({why(r3)})")
            return stop(f"the traders disagree (Trader 1 {t1['direction']} {t1['confidence']}, Trader 2 "
                        f"{t2['direction']} {t2['confidence']}): no trade unless both choose the same side; {seen}",
                        "DISAGREE")
        res = resolve(t1, t2)
        if res["outcome"] != "TRADE":
            return stop(f"the desk's rule gave no trade ({res['rule']})", res["rule"])
        traders, lim = {"trader1": t1, "trader2": t2}, (ctx.costs or {}).get("risk_engine_limits")
        other = "trader2" if res["levels_from"] == "trader1" else "trader1"
        if not fits_limits(traders[res["levels_from"]], px, lim) and fits_limits(traders[other], px, lim):
            res = {**res, "levels_from": other,
                   "levels_reason": f"the more confident trader's levels are inside the risk engine's per-trade limits; "
                                    f"{other}'s own levels respect them"}
        lead = traders[res["levels_from"]]
        rec["consensus"] = {**res, "desk_confidence": round(min(t1["confidence"], t2["confidence"]) / 100, 3),
                            "stop_loss": float(lead["stop_loss"]), "take_profit": float(lead["take_profit"])}
        hit = _lesson(ctx, 1 if res["direction"] == "BUY" else -1)
        if hit:
            return stop(f"validated lesson {hit['lesson_id']}: {hit['statement']}", "LESSON",
                        [{"code": "LESSON_MATCH", "severity": "BLOCKING", "message": hit["statement"]}])
        story = (f"{res['rule']}: Trader 1 ({r1.model}) {t1['direction']} {t1['confidence']}: {t1['reason']} | "
                 f"Trader 2 ({r2.model}) {t2['direction']} {t2['confidence']}: {t2['reason']}")
        p = {"action": res["direction"], "timeframe": chart.meta["execution_timeframe"],
             "stop": float(lead["stop_loss"]), "target": float(lead["take_profit"]), "max_hold_minutes": hold,
             "thesis": story[:500],
             "invalidation": (f"price trades through {lead['invalidation']}" if _num(lead.get("invalidation"))
                              else str(lead["invalidation"])[:200] if _text(lead.get("invalidation"))
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


def counterfactual_decisions(d: Decision) -> list[Decision]:
    """The two sides of a disagreement (the shadow debate's pick and the side it rejected), as decision records for
    the forward ledger only: each followed forward as if it had been taken, so what standing aside skipped and
    whether the debate chose the better side are measured. Never sent anywhere."""
    out = []
    for s in ((d.ai or {}).get("dual_ai") or {}).get("shadow") or []:
        suffix, verdict = SHADOW[s["family"]]
        out.append(dataclasses.replace(d, id=d.id + suffix, decision=s["direction"], stop_loss=s["stop_loss"],
                                       take_profit=s["take_profit"], max_hold_minutes=s["hold_minutes"],
                                       family=s["family"], template=s["family"], signal_class=s["family"],
                                       edge_status="EXPERIMENTAL", ai_verdict=verdict))
    return out


__all__ = ["DUAL_AI_VERSION", "DualAITrader", "FAMILY", "LOSER_FAMILY", "LOSER_SUFFIX", "PICK_FAMILY", "PICK_SUFFIX",
           "build_chart", "check_levels", "counterfactual_decisions", "resolve", "validate_trader", "validate_verifier"]
