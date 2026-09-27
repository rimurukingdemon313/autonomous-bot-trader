"""The five specialised agents.

Each agent has ONE responsibility and a deterministic quantitative core that
reads only the point-in-time MarketContext. An optional language-model layer
(`LLMReviewer`) may add reasoning and objections on top of the same evidence
packet; it never replaces the core and never sees anything the core did not.

1. MarketAnalyst      - describes the market: trend, momentum, volatility,
                        liquidity, structure, regime, key levels. Takes no side.
2. SetupAnalyst       - proposes candidate trades from several families, NOT
                        one strategy, and attaches the historical-analogue
                        evidence for each.
3. RiskAnalyst        - looks for reasons NOT to trade: costs, abnormal or
                        unfamiliar conditions, exposure, correlation, drawdown,
                        rollover, weekend, unknown event risk.
4. AdversarialAnalyst - tries to prove the best candidate wrong. It can object;
                        it cannot approve (its stance is never SUPPORT).
5. ReviewerAnalyst    - judges the QUALITY of the evidence behind each
                        candidate BEFORE synthesis: analogue sample, noise,
                        age and concentration, template agreement, validated
                        lessons, the family's track record. It never sees the
                        decision; synthesis (aitrader/decision/synthesis.py)
                        weighs all five reports.

None of them computes a position size or a risk amount; that is the risk
engine's alone (RISK_CONTRACT.md §1).
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from datetime import datetime, timezone

import numpy as np

from ..research.labels import TEMPLATES
from .types import (
    AGENT_VERSION, OBJECTION_CODES, SEVERITIES, AgentReport, Evidence, MarketContext, Objection,
    SetupCandidate,
)

SIDE = {1: "BUY", -1: "SELL"}


def _v(ctx: MarketContext, name: str) -> float:
    x = ctx.features.values.get(name, float("nan"))
    return float(x) if x is not None else float("nan")


def _fin(*xs: float) -> bool:
    return all(np.isfinite(x) for x in xs)


def _report(agent: str, started: float) -> AgentReport:
    return AgentReport(agent=agent, version=AGENT_VERSION, status="OK", stance="NEUTRAL",
                       started=started, finished=started)


# ─────────────────────────────────────────────────────────────────────────
# 1. Market analyst
# ─────────────────────────────────────────────────────────────────────────


class MarketAnalyst:
    name = "market"

    def analyze(self, ctx: MarketContext) -> AgentReport:
        rep = _report(self.name, time.time())
        rep.stance = "DESCRIBE"
        rg = ctx.regime
        slope, er120, r24, r120 = _v(ctx, "ma_slope"), _v(ctx, "er120"), _v(ctx, "r24"), _v(ctx, "r120")
        if _fin(slope, er120):
            rep.evidence.append(Evidence(
                self.name, f"trend {('up' if rg.trend_direction > 0 else 'down') if rg.trend_direction else 'flat'}"
                f" (efficiency {er120:.2f}, MA spread {slope:+.2f} ATR)",
                rg.trend_direction, float(min(1.0, er120 / 0.5)), ("ma_slope", "er120")))
        if _fin(r24, r120):
            agree = np.sign(r24) == np.sign(r120) and r24 != 0
            rep.evidence.append(Evidence(
                self.name, f"momentum 24-bar {r24:+.2f} vs 120-bar {r120:+.2f} ATR: "
                f"{'aligned' if agree else 'in conflict'} across horizons",
                int(np.sign(r24)) if agree else 0, float(min(1.0, abs(r120) / 10)), ("r24", "r120")))
        vr = _v(ctx, "vol_ratio")
        if np.isfinite(vr):
            rep.evidence.append(Evidence(self.name, f"volatility {rg.vol_state.lower()} (ATR24/ATR240 {vr:.2f})",
                                         0, float(min(1.0, abs(vr - 1))), ("vol_ratio",)))
        act = _v(ctx, "tick_activity")
        if np.isfinite(act):
            rep.evidence.append(Evidence(self.name, f"tick activity {act:.2f}x its 10-day mean"
                                         + (" (thin market)" if act < 0.5 else ""), 0,
                                         float(min(1.0, abs(act - 1))), ("tick_activity",)))
        st, sw = _v(ctx, "smc_structure"), _v(ctx, "smc_sweep")
        if np.isfinite(st):
            rep.evidence.append(Evidence(self.name, f"swing structure {st:+.0f} (higher highs/lows = +2)",
                                         int(np.sign(st)), abs(st) / 2, ("smc_structure",)))
        if np.isfinite(sw) and sw != 0:
            rep.evidence.append(Evidence(self.name, f"liquidity sweep {'of lows, closed back above' if sw > 0 else 'of highs, closed back below'}",
                                         int(sw), 0.5, ("smc_sweep",)))
        rep.summary = (f"{ctx.symbol} {rg.label} / {rg.vol_state}; familiarity distance "
                       f"{rg.familiarity_distance:.2f} ({'familiar' if rg.familiar else 'UNFAMILIAR'}).")
        rep.finished = time.time()
        return rep


# ─────────────────────────────────────────────────────────────────────────
# 2. Setup analyst
# ─────────────────────────────────────────────────────────────────────────


class SetupAnalyst:
    """Proposes, across families, and lets the evidence rank them."""

    name = "setup"
    MAX_CANDIDATES = 8

    def triggers(self, ctx: MarketContext) -> list[tuple[str, int, str]]:
        """(family, direction, why) for every family whose conditions hold now."""
        rg = ctx.regime
        out: list[tuple[str, int, str]] = []
        dist, er120, slope = _v(ctx, "dist_ma48"), _v(ctx, "er120"), _v(ctx, "ma_slope")
        if rg.trend_direction and _fin(dist) and -1.5 <= dist * rg.trend_direction <= 0.0:
            out.append(("TREND_PULLBACK", rg.trend_direction,
                        f"pullback of {abs(dist):.2f} ATR against a {'rising' if rg.trend_direction > 0 else 'falling'} trend"))
        bh, bl = _v(ctx, "brk_hi120"), _v(ctx, "brk_lo120")
        if _fin(bh) and bh > 0:
            out.append(("BREAKOUT", 1, f"close {bh:.2f} ATR above the prior 120-bar high"))
        if _fin(bl) and bl < 0:
            out.append(("BREAKOUT", -1, f"close {abs(bl):.2f} ATR below the prior 120-bar low"))
        rp = _v(ctx, "range_pos120")
        if rg.label == "RANGING" and _fin(rp):
            if rp >= 0.9:
                out.append(("MEAN_REVERSION", -1, f"top of range ({rp:.2f}) in a ranging market"))
            elif rp <= 0.1:
                out.append(("MEAN_REVERSION", 1, f"bottom of range ({rp:.2f}) in a ranging market"))
        sw = _v(ctx, "smc_sweep")
        if _fin(sw) and sw != 0:
            out.append(("SWEEP_REVERSAL", int(sw), "liquidity sweep and close back inside"))
        return out

    def candidate(self, ctx: MarketContext, family: str, direction: int, template, why: str) -> SetupCandidate | None:
        if ctx.atr is None or not np.isfinite(ctx.atr) or ctx.atr <= 0 or ctx.bid is None or ctx.ask is None:
            return None
        entry = ctx.ask if direction > 0 else ctx.bid
        stop = entry - direction * template.stop_atr * ctx.atr
        target = entry + direction * template.target_atr * ctx.atr
        action = f"{template.key}:{SIDE[direction]}"
        ev = ctx.analogs.get(action)
        a = ev.actions.get(action) if ev is not None else None
        return SetupCandidate(
            family=family, direction=direction, template=template.key, entry=float(entry),
            stop=float(stop), target=float(target), reward_risk=template.reward_risk,
            max_bars=template.max_bars,
            invalidation=f"{why}; invalid on a {'close below' if direction > 0 else 'close above'} "
                         f"{stop:.5g} or after {template.max_bars} bars",
            analog=(ev.as_dict() if ev is not None else None),
            expected_r=(a.mean_r if a else None), lower_r=(a.lower if a else None),
            win_rate=(a.win_rate if a else None), n_analogs=(a.n if a else 0))

    def analyze(self, ctx: MarketContext) -> AgentReport:
        rep = _report(self.name, time.time())
        seen: set[str] = set()
        cands: list[SetupCandidate] = []
        for family, direction, why in self.triggers(ctx):
            for tpl in TEMPLATES:
                c = self.candidate(ctx, family, direction, tpl, why)
                if c is not None:
                    cands.append(c)
                    seen.add(c.action)
                    rep.evidence.append(Evidence(self.name, f"{family} {SIDE[direction]} ({tpl.key}): {why}",
                                                 direction, 0.5, (family.lower(),)))
        # Discovery: an opportunity no named family describes, found only in
        # the historical analogues. The AI is not confined to the families.
        for action, ev in ctx.analogs.items():
            a = ev.actions.get(action)
            if a is None or action in seen or a.lower <= 0:
                continue
            key, side = action.split(":")
            tpl = next(t for t in TEMPLATES if t.key == key)
            c = self.candidate(ctx, "ANALOG_DISCOVERY", 1 if side == "BUY" else -1, tpl,
                               f"historical analogues favour {side} (lower bound {a.lower:+.3f}R, n={a.n})")
            if c is not None:
                cands.append(c)
        cands.sort(key=lambda c: (c.lower_r if c.lower_r is not None else -9.0), reverse=True)
        rep.candidates = cands[: self.MAX_CANDIDATES]
        best = rep.candidates[0] if rep.candidates else None
        if best is not None and best.lower_r is not None and best.lower_r > 0:
            rep.stance = "SUPPORT"
            rep.summary = (f"best: {best.family} {best.action}, analogue expectancy {best.expected_r:+.3f}R "
                           f"(lower {best.lower_r:+.3f}R, n={best.n_analogs}).")
        else:
            rep.summary = ("no candidate" if best is None else
                           f"best candidate {best.family} {best.action} lacks positive lower-bound expectancy")
        rep.finished = time.time()
        return rep


# ─────────────────────────────────────────────────────────────────────────
# 3. Risk analyst (analytical; the deterministic risk engine is separate)
# ─────────────────────────────────────────────────────────────────────────

CORRELATION_GROUPS = (
    frozenset({"EURUSD", "GBPUSD", "AUDUSD", "NZDUSD", "XAUUSD"}),  # USD as quote
    frozenset({"USDJPY", "USDCAD", "USDCHF"}),                     # USD as base
    frozenset({"EURJPY", "GBPJPY", "AUDJPY"}),                     # JPY crosses
)


@dataclass(frozen=True)
class RiskAnalystConfig:
    spread_major: float = 0.12   # spread+costs as a share of the stop distance
    spread_blocking: float = 0.25
    quote_max_age_s: int = 180
    drawdown_major_pct: float = 5.0
    max_same_currency: int = 2


class RiskAnalyst:
    name = "risk"

    def __init__(self, config: RiskAnalystConfig = RiskAnalystConfig(), calendar_available: bool = False) -> None:
        self.config = config
        self.calendar_available = calendar_available

    def analyze(self, ctx: MarketContext, candidates: list[SetupCandidate]) -> AgentReport:
        rep = _report(self.name, time.time())
        cfg = self.config
        obj = rep.objections
        rg = ctx.regime
        if ctx.data_flags:
            obj.append(Objection("DATA_QUALITY", "BLOCKING", self.name, "; ".join(ctx.data_flags)))
        if not ctx.features.complete:
            obj.append(Objection("DATA_QUALITY", "BLOCKING", self.name,
                                 f"features missing: {', '.join(ctx.features.missing[:6])}"))
        if rg.abnormal:
            obj.append(Objection("ABNORMAL_MARKET", "BLOCKING", self.name, "; ".join(rg.reasons) or rg.label))
        if not rg.familiar:
            obj.append(Objection("UNFAMILIAR_STATE", "BLOCKING", self.name,
                                 f"familiarity distance {rg.familiarity_distance:.2f}"))
        if ctx.quote_time is None or ctx.bid is None or ctx.ask is None:
            obj.append(Objection("STALE_DATA", "BLOCKING", self.name, "no current quote"))
        elif ctx.t - ctx.quote_time > cfg.quote_max_age_s:
            obj.append(Objection("STALE_DATA", "BLOCKING", self.name, f"quote is {ctx.t - ctx.quote_time}s old"))
        stale = ctx.features.metadata.get("stale_seconds")
        if stale is not None and stale > 2 * 3600:
            obj.append(Objection("STALE_DATA", "BLOCKING", self.name, f"last closed bar is {stale // 60} minutes old"))

        if ctx.bid is not None and ctx.ask is not None and ctx.atr:
            for c in candidates[:3]:
                stop_dist = abs(c.entry - c.stop)
                share = (ctx.ask - ctx.bid) / stop_dist if stop_dist > 0 else float("inf")
                if share >= cfg.spread_blocking:
                    obj.append(Objection("SPREAD_COST", "BLOCKING", self.name,
                                         f"spread is {share:.0%} of the stop for {c.action}", {"action": c.action}))
                elif share >= cfg.spread_major:
                    obj.append(Objection("SPREAD_COST", "MAJOR", self.name,
                                         f"spread is {share:.0%} of the stop for {c.action}", {"action": c.action}))

        acct = ctx.account
        if acct.drawdown_pct is not None and acct.drawdown_pct >= cfg.drawdown_major_pct:
            obj.append(Objection("DRAWDOWN_STATE", "MAJOR", self.name, f"account drawdown {acct.drawdown_pct:.1f}%"))
        held = [p.get("symbol", "") for p in acct.open_positions]
        if ctx.symbol in held:
            obj.append(Objection("EXPOSURE", "BLOCKING", self.name, f"a {ctx.symbol} position is already open"))
        ccy = {ctx.symbol[:3], ctx.symbol[3:]}
        same_ccy = sum(1 for s in held if {s[:3], s[3:]} & ccy)
        if same_ccy >= cfg.max_same_currency:
            obj.append(Objection("EXPOSURE", "MAJOR", self.name, f"{same_ccy} open positions share a currency"))
        for g in CORRELATION_GROUPS:
            if ctx.symbol in g and any(s in g and s != ctx.symbol for s in held):
                obj.append(Objection("CORRELATED_POSITION", "MAJOR", self.name,
                                     f"open position in the same correlation group as {ctx.symbol}"))
                break

        now = datetime.fromtimestamp(ctx.t, timezone.utc)
        minutes = now.hour * 60 + now.minute
        if 20 * 60 + 45 <= minutes <= 22 * 60 + 15:
            obj.append(Objection("ROLLOVER_WINDOW", "MAJOR", self.name, "daily rollover: spreads widen"))
        if now.weekday() == 4 and now.hour >= 18:
            obj.append(Objection("WEEKEND_GAP", "MAJOR", self.name, "Friday evening: position would carry over the weekend"))
        if not self.calendar_available:
            obj.append(Objection("EVENT_RISK_UNKNOWN", "MINOR", self.name,
                                 "no economic calendar connected: scheduled-event risk is unknown, not zero"))
        rep.stance = "OPPOSE" if any(o.severity != "MINOR" for o in obj) else "NEUTRAL"
        rep.summary = f"{len(obj)} objection(s): " + ", ".join(sorted({o.code for o in obj})) if obj else "no risk objections"
        rep.finished = time.time()
        return rep


# ─────────────────────────────────────────────────────────────────────────
# 4. Adversarial analyst
# ─────────────────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class AdversarialConfig:
    overextended_atr: float = 3.0
    late_entry_r24: float = 4.0


class AdversarialAnalyst:
    """Tries to disprove the trade. Never SUPPORT."""

    name = "adversary"

    def __init__(self, config: AdversarialConfig = AdversarialConfig()) -> None:
        self.config = config

    def analyze(self, ctx: MarketContext, candidates: list[SetupCandidate]) -> AgentReport:
        rep = _report(self.name, time.time())
        cfg = self.config
        for c in candidates[:3]:
            d = c.direction
            tag = {"action": c.action, "family": c.family}
            r120, slope = _v(ctx, "r120"), _v(ctx, "ma_slope")
            if _fin(r120, slope) and np.sign(r120) == -d and np.sign(slope) == -d:
                rep.objections.append(Objection("COUNTER_TREND_HTF", "MAJOR", self.name,
                                                f"{c.action} opposes the 120-bar trend (r120 {r120:+.1f}, slope {slope:+.1f})", tag))
            dist = _v(ctx, "dist_ma48")
            if _fin(dist) and dist * d > cfg.overextended_atr:
                rep.objections.append(Objection("OVEREXTENDED", "MAJOR", self.name,
                                                f"price already {abs(dist):.1f} ATR from its 48-bar mean in the trade direction", tag))
            r24 = _v(ctx, "r24")
            if _fin(r24) and r24 * d > cfg.late_entry_r24:
                rep.objections.append(Objection("LATE_ENTRY", "MAJOR", self.name,
                                                f"{abs(r24):.1f} ATR already moved in 24 bars", tag))
            if c.family == "BREAKOUT":
                er24, body = _v(ctx, "er24"), _v(ctx, "bar_body")
                if _fin(er24, body) and (er24 < 0.2 or body * d < 0):
                    rep.objections.append(Objection("FAKE_BREAKOUT_RISK", "MAJOR", self.name,
                                                    f"breakout with weak follow-through (efficiency {er24:.2f}, body {body:+.2f})", tag))
            sw = _v(ctx, "smc_sweep")
            if _fin(sw) and sw == -d:
                rep.objections.append(Objection("SWEEP_AGAINST", "MAJOR", self.name,
                                                "the last bar swept liquidity against this direction", tag))
        rep.stance = "OPPOSE" if rep.objections else "NEUTRAL"
        rep.summary = (f"{len(rep.objections)} objection(s) against the leading candidates"
                       if rep.objections else "no argument found against the leading candidates")
        rep.finished = time.time()
        return rep


# ─────────────────────────────────────────────────────────────────────────
# 5. Reviewer: the quality of the evidence, before synthesis
# ─────────────────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class ReviewerConfig:
    min_analogs: int = 60
    min_similarity: float = 0.5
    stale_days: float = 3 * 365.0
    concentrated_share: float = 0.5


class ReviewerAnalyst:
    """Judges how much the evidence behind each candidate can be trusted.

    Independent of the decision: it reads the same point-in-time context and
    candidates as the Adversary and never sees synthesis. The Adversary
    argues from the MARKET that a trade is wrong; the Reviewer asks whether
    the EVIDENCE for it is good enough to believe: the analogues (how many,
    how similar, how noisy, how old, how concentrated), whether the two
    action templates agree, validated lessons, and the family's track record.
    Its stance is DESCRIBE: it grades evidence, it does not pick a side.
    """

    name = "reviewer"

    def __init__(self, config: ReviewerConfig = ReviewerConfig()) -> None:
        self.config = config

    def analyze(self, ctx: MarketContext, candidates: list[SetupCandidate]) -> AgentReport:
        rep = _report(self.name, time.time())
        rep.stance = "DESCRIBE"
        cfg = self.config
        grades = []
        for c in candidates[:3]:
            tag = {"action": c.action, "family": c.family}
            an = c.analog
            issues = 0
            if an is None or c.n_analogs < cfg.min_analogs or an.get("similarity", 0) < cfg.min_similarity:
                rep.objections.append(Objection("WEAK_ANALOG_EVIDENCE", "MAJOR", self.name,
                                                f"{c.n_analogs} analogues, similarity {an.get('similarity', 0) if an else 0:.2f}", tag))
                issues += 1
            elif c.expected_r is not None and c.expected_r < 0:
                rep.objections.append(Objection("ANALOG_CONTRADICTION", "MAJOR", self.name,
                                                f"historical analogues averaged {c.expected_r:+.3f}R in this direction", tag))
                issues += 1
            if an is not None and c.expected_r is not None and c.lower_r is not None:
                se = (c.expected_r - c.lower_r) / 1.28
                if se > 0 and abs(c.expected_r) < se:
                    rep.objections.append(Objection("ANALOG_NOISE", "MINOR", self.name,
                                                    f"expectancy {c.expected_r:+.3f}R is inside one standard error ({se:.3f}R)", tag))
                    issues += 1
                age = an.get("median_age_days")
                if age is not None and age > cfg.stale_days:
                    rep.objections.append(Objection("ANALOG_STALE", "MINOR", self.name,
                                                    f"median analogue is {age / 365:.1f} years old", tag))
                    issues += 1
                share = an.get("top_symbol_share")
                if share is not None and share > cfg.concentrated_share:
                    rep.objections.append(Objection("ANALOG_CONCENTRATED", "MINOR", self.name,
                                                    f"{share:.0%} of analogues come from one instrument", tag))
                    issues += 1
                side = c.action.split(":")[1]
                for other, a in (an.get("actions") or {}).items():
                    if other != c.action and other.endswith(":" + side) and a.get("mean_r") is not None \
                            and np.sign(a["mean_r"]) == -np.sign(c.expected_r) and c.expected_r != 0:
                        rep.objections.append(Objection("TEMPLATE_DISAGREEMENT", "MINOR", self.name,
                                                        f"{other} analogues averaged {a['mean_r']:+.3f}R, "
                                                        f"{c.action} {c.expected_r:+.3f}R", tag))
                        issues += 1
                        break
            kv = ctx.knowledge
            if kv is not None:
                for lesson in kv.lessons_matching(c.family, ctx.regime.label, ctx.regime.vol_state, c.direction, ctx.t):
                    rep.objections.append(Objection("LESSON_MATCH", "BLOCKING", self.name,
                                                    f"validated lesson {lesson['lesson_id']} v{lesson['version']}: {lesson['statement']}",
                                                    {**tag, "lesson": lesson["lesson_id"], "version": lesson["version"]}))
                    issues += 1
                st = kv.family_regime_stats(c.family, ctx.regime.label, ctx.t)
                if st and st["n_eff"] >= 30 and st["mean"] + 1.28 * st["se"] < 0:
                    rep.objections.append(Objection("REGIME_MISMATCH", "MAJOR", self.name,
                                                    f"{c.family} in {ctx.regime.label}: {st['mean']:+.3f}R over {st['n']} resolved cases", tag))
                    issues += 1
            grades.append(f"{c.family} {c.action}: {'clean' if not issues else f'{issues} issue(s)'}")
        rep.summary = ("evidence quality — " + "; ".join(grades)) if grades else "no candidate to review"
        rep.finished = time.time()
        return rep


def validate_llm_review(data: dict) -> str | None:
    """Schema for every agent's language-model review. Returns a problem or None."""
    if data.get("stance") not in ("SUPPORT", "OPPOSE", "NEUTRAL"):
        return "stance must be SUPPORT, OPPOSE or NEUTRAL"
    if data.get("direction", "NONE") not in ("BUY", "SELL", "NONE"):
        return "direction must be BUY, SELL or NONE"
    objs = data.get("objections", [])
    if not isinstance(objs, list) or len(objs) > 8:
        return "objections must be a list of at most 8"
    for o in objs:
        if not isinstance(o, dict) or o.get("code") not in OBJECTION_CODES or o.get("severity") not in SEVERITIES:
            return "each objection needs a known code and severity"
    summary = data.get("summary", "")
    if not isinstance(summary, str) or len(summary) > 1200:
        return "summary must be a string under 1200 characters"
    return None
