"""The strategy library: documented trading approaches, reduced to principles we can TEST.

This module does not copy anyone's trades, signals or claims. For each documented approach it
records WHY its practitioners or researchers decide as they do (the decision process as the
source documents it), the principles underneath, the conditions they depend on, and — where our
data allows — a machine-testable hypothesis in the engine's closed vocabulary. The only thing
that can move an entry to VALIDATED is our own preregistered test on our own data after costs.

Knowledge classes, kept apart on purpose:

    DOCUMENTED_FACT     what the cited source states or reports (as cited, not re-verified here)
    INFERRED_PRINCIPLE  the general rule we read out of it
    HYPOTHESIS          that principle as a falsifiable statement about OUR instruments
    VALIDATED_EDGE      a hypothesis that survived our battery (none so far)
    UNCERTAIN           what the evidence does not settle

Sources are ranked by EVIDENCE QUALITY, never popularity:

    A  peer-reviewed research with long out-of-sample history across many markets
    B  peer-reviewed or institutional research with narrower evidence
    C  practitioner books with explicit, reproducible rules but no independent audit
    D  practitioner doctrine without published, reproducible performance (e.g. ICT/SMC teaching)

Every citation here is "cited from prior knowledge": none was re-opened in this project
(docs/RESEARCH_LOG.md). A citation is a reason to test an idea, never evidence that it works here.
"""

from __future__ import annotations

import json
from collections import defaultdict
from dataclasses import asdict, dataclass, field

LIBRARY_VERSION = "library-1.0.0"
STATUSES = ("RESEARCHED", "HYPOTHESIS", "TESTING", "VALIDATED", "REJECTED", "DEGRADED", "RETIRED")
QUALITY = {"A": "peer-reviewed, long multi-market evidence", "B": "peer-reviewed or institutional, narrower",
           "C": "practitioner rules, reproducible, unaudited", "D": "practitioner doctrine, no reproducible record"}

PRINCIPLES = {
    "TREND_CONTINUATION": "prices that have moved persistently tend to keep moving the same way for a while",
    "SHORT_TERM_REVERSAL": "short, sharp moves tend to partly retrace",
    "PULLBACK_IN_TREND": "a short move against an established trend is an entry in the trend's direction",
    "VOLATILITY_EXPANSION": "a quiet, narrow market tends to be followed by a larger move",
    "BREAKOUT": "a close beyond a prior extreme starts a move in that direction",
    "LIQUIDITY_SWEEP": "a run of stops beyond a swing is followed by a reversal",
    "LOCAL_HOURS_DEPRECIATION": "a currency tends to weaken during its own market's trading hours",
    "CARRY": "high-interest currencies earn their rate differential and tend not to fall by as much",
    "VALUE_PPP": "exchange rates revert slowly toward purchasing-power parity",
    "CROSS_SECTIONAL_MOMENTUM": "currencies that outperformed others keep outperforming for a while",
    "REGIME_DEPENDENCE": "which of continuation or reversal works depends on the market's regime",
    "VOLATILITY_SCALING": "risk per position scaled to its volatility keeps risk steady",
    "CUT_LOSSES_LET_WINNERS_RUN": "small fixed losses, open-ended gains (trailing exits)",
    "INVENTORY_SPREAD_CAPTURE": "providing liquidity earns the spread against adverse selection",
}


@dataclass(frozen=True)
class Source:
    citation: str
    kind: str  # academic | book | institutional | practitioner
    quality: str  # A | B | C | D
    verification: str = "cited from prior knowledge; not re-opened in this project"


@dataclass(frozen=True)
class Method:
    strategy_id: str
    name: str
    school: str
    sources: tuple[Source, ...]
    principles: tuple[str, ...]
    decision_process: dict  # documented: assumptions, prefers, avoids, direction, entry, stop, target, sizing,
    #                         winners, losers, regime change, invalidation, stays out when, ignores
    market_conditions: str
    entry_logic: str
    exit_logic: str
    risk_logic: str
    timeframe: str
    instruments: str
    features: tuple[str, ...]  # our catalogued features that express it
    tests: tuple[dict, ...] = ()  # machine-testable forms: {"condition", "side", "exit", "timeframe"}
    untestable_because: str | None = None
    status: str = "RESEARCHED"
    results: tuple[dict, ...] = ()  # {"trial", "hypothesis", "verdict", "summary"}

    def __post_init__(self) -> None:
        if self.status not in STATUSES:
            raise ValueError(f"{self.strategy_id}: unknown status {self.status}")
        if any(p not in PRINCIPLES for p in self.principles):
            raise ValueError(f"{self.strategy_id}: undeclared principle")
        if not self.sources or any(s.quality not in QUALITY for s in self.sources):
            raise ValueError(f"{self.strategy_id}: every method needs a graded source")
        if not self.tests and not self.untestable_because:
            raise ValueError(f"{self.strategy_id}: say how it is tested, or why it cannot be")

    @property
    def evidence_quality(self) -> str:
        return min(s.quality for s in self.sources)  # "A" < "B" < ...: the best source


def _dp(**kw) -> dict:
    return kw


LIBRARY: tuple[Method, ...] = (
    Method("SL-TSMOM", "Time-series momentum", "systematic trend following",
           (Source("Moskowitz, Ooi & Pedersen, Time series momentum, J. Financial Economics 104 (2012)", "academic", "A"),
            Source("Hurst, Ooi & Pedersen, A century of evidence on trend-following investing, J. Portfolio "
                   "Management (2017)", "academic", "A")),
           ("TREND_CONTINUATION", "CUT_LOSSES_LET_WINNERS_RUN", "VOLATILITY_SCALING"),
           _dp(assumptions="under-reaction and slow-moving capital make trends persist over 1-12 months",
               prefers="markets with sustained macro trends", avoids="nothing explicitly: always positioned",
               direction="the sign of the past 12-month (or 1-3 month) return", entry="rebalance monthly",
               stop="none fixed; position flips when the sign flips", target="none",
               sizing="inverse to volatility (a volatility target)", winners="held while the trend persists",
               losers="exit when the signal flips", regime_change="suffers at trend reversals (momentum crashes)",
               invalidation="the signal changing sign", stays_out="never; small when volatility is high",
               ignores="fundamental value and news"),
           "persistent directional moves; many uncorrelated markets", "past 6-12 month move positive -> long; negative -> short",
           "monthly re-evaluation; about a month's holding", "volatility-scaled position size",
           "D1 decision, monthly holding", "diversified futures incl. FX", ("r120", "ma_slope"),
           tests=({"condition": "r120=high", "side": "BUY", "exit": "D4", "timeframe": "D1"},
                  {"condition": "r120=low", "side": "SELL", "exit": "D4", "timeframe": "D1"}),
           status="REJECTED",
           results=({"trial": "CP-001", "hypothesis": "CP-001-T1/T2", "verdict": "REJECTED",
                     "summary": "short side +0.19R/trade, almost all from 2014; long side 0; t~1.0 vs 3.18 required"},)),
    Method("SL-MA-TREND", "Moving-average trend filter", "systematic trend following",
           (Source("Faber, A quantitative approach to tactical asset allocation, J. Wealth Management (2007)", "academic", "B"),
            Source("Menkhoff & Taylor, The obstinate passion of foreign exchange professionals: technical analysis, "
                   "J. Economic Literature 45 (2007)", "academic", "A")),
           ("TREND_CONTINUATION",),
           _dp(assumptions="a price above its long average is in an uptrend", prefers="trending markets",
               avoids="choppy markets (whipsaws accepted as a cost)", direction="short average vs long average",
               entry="on the cross or while above", stop="the reverse cross", target="none",
               sizing="equal or volatility-scaled", winners="held", losers="exit on reverse cross",
               regime_change="loses in ranges", invalidation="the reverse cross", stays_out="below the average (long-only form)",
               ignores="everything but price"),
           "trends", "48-day average above the 240-day average -> long (mirror short)", "held about a month",
           "equal risk", "D1", "multi-asset; widely used in FX", ("ma_slope",),
           tests=({"condition": "ma_slope=high", "side": "BUY", "exit": "D4", "timeframe": "D1"},
                  {"condition": "ma_slope=low", "side": "SELL", "exit": "D4", "timeframe": "D1"}),
           status="REJECTED",
           results=({"trial": "CP-001", "hypothesis": "CP-001-T3/T4", "verdict": "REJECTED",
                     "summary": "long side 0; short side +0.21R/trade from 2014 only; t~1.0"},)),
    Method("SL-DONCHIAN", "Channel breakout (Donchian / Turtle rules)", "systematic trend following",
           (Source("Faith, Way of the Turtle (2007)", "book", "C"),
            Source("Hurst, Ooi & Pedersen (2017), breakout rules as a form of trend following", "academic", "A")),
           ("BREAKOUT", "TREND_CONTINUATION", "CUT_LOSSES_LET_WINNERS_RUN"),
           _dp(assumptions="a new N-day extreme marks the start of a trend", prefers="markets breaking out of ranges",
               avoids="re-entering soon after a losing breakout (a filter in the original rules)",
               direction="the side of the breakout", entry="a close/touch beyond the prior N-day high/low",
               stop="2 ATR", target="none: a trailing exit at the opposite shorter channel",
               sizing="1% of equity per ATR unit (volatility scaling)", winners="trailed", losers="stopped at 2 ATR",
               regime_change="many small losses in ranges, rare large wins", invalidation="the stop",
               stays_out="no breakout", ignores="fundamentals"),
           "range breaks into trends", "close near/above the prior 120-day high -> long (mirror short)",
           "trailing 2 ATR, up to 40 days", "risk per trade fixed by ATR", "D1", "futures incl. FX", ("brk_hi120", "brk_lo120"),
           tests=({"condition": "brk_hi120=high", "side": "BUY", "exit": "D5", "timeframe": "D1"},
                  {"condition": "brk_lo120=low", "side": "SELL", "exit": "D5", "timeframe": "D1"}),
           status="REJECTED",
           results=({"trial": "SL-001", "hypothesis": "SL-001-01/02", "verdict": "REJECTED", "summary": "long -0.04R (n 266); short +0.17R (n 290) but fails permutation, years, instruments, outliers; t 0.65"},)),
    Method("SL-PULLBACK", "Short-term pullback within a trend", "short-term mean reversion",
           (Source("Connors & Alvarez, Short Term Trading Strategies That Work (2008)", "book", "C"),),
           ("PULLBACK_IN_TREND", "SHORT_TERM_REVERSAL"),
           _dp(assumptions="short-term extremes revert, and do so best in the direction of the longer trend",
               prefers="an established long-term trend", avoids="trading against the long-term trend",
               direction="the long-term trend's", entry="after a short, sharp move against it",
               stop="often none in the book; here a 2 ATR protective stop", target="a short-term recovery",
               sizing="fixed", winners="exit quickly on recovery", losers="time exit",
               regime_change="fails when the trend itself ends", invalidation="the trend breaking",
               stays_out="no trend, or no pullback", ignores="news"),
           "an uptrend with a short dip (mirror for downtrend)", "long-term average up and 6-day move in its low tercile -> long",
           "exit after 5 days", "fixed", "D1", "stock indices in the source; untested there on FX", ("ma_slope", "r6"),
           tests=({"condition": "ma_slope=high&r6=low", "side": "BUY", "exit": "D3", "timeframe": "D1"},
                  {"condition": "ma_slope=low&r6=high", "side": "SELL", "exit": "D3", "timeframe": "D1"}),
           status="REJECTED",
           results=({"trial": "SL-001", "hypothesis": "SL-001-03/04", "verdict": "REJECTED", "summary": "long -0.01R (n 395); short -0.01R (n 343); nothing beats random entries"},)),
    Method("SL-NR-BREAKOUT", "Volatility contraction then expansion (narrow-range breakout)", "short-term patterns",
           (Source("Crabel, Day Trading with Short Term Price Patterns and Opening Range Breakout (1990)", "book", "C"),),
           ("VOLATILITY_EXPANSION", "BREAKOUT"),
           _dp(assumptions="volatility clusters and mean-reverts: contraction precedes expansion",
               prefers="a narrow range after wider ones", avoids="already-expanded markets",
               direction="the side the range breaks", entry="the break of the narrow range", stop="the other side of the range",
               target="a multiple of the range or the session close", sizing="fixed", winners="short holds",
               losers="the stop", regime_change="n/a", invalidation="a close back inside",
               stays_out="no contraction", ignores="longer-term direction"),
           "a tight 24-day range within the 120-day range, then a strong day", "range_contraction low and the last day's move high -> long",
           "barrier 1.0/1.5 ATR, 10 days", "fixed", "D1", "futures in the source", ("range_contraction", "r1"),
           tests=({"condition": "range_contraction=low&r1=high", "side": "BUY", "exit": "D1", "timeframe": "D1"},
                  {"condition": "range_contraction=low&r1=low", "side": "SELL", "exit": "D1", "timeframe": "D1"}),
           status="REJECTED",
           results=({"trial": "SL-001", "hypothesis": "SL-001-05/06", "verdict": "REJECTED", "summary": "long -0.16R (n 552, t -2.9); short -0.06R (n 579): breakouts after contraction lose after costs"},)),
    Method("SL-LOCAL-HOURS", "Currencies weaken during their own trading hours", "intraday seasonality",
           (Source("Breedon & Ranaldo, Intraday patterns in FX returns and order flow, J. Money, Credit and Banking "
                   "45 (2013)", "academic", "B"),),
           ("LOCAL_HOURS_DEPRECIATION",),
           _dp(assumptions="domestic order flow (local buyers of foreign currency) during local hours",
               prefers="liquid majors", avoids="n/a (a documented pattern, not a trading doctrine)",
               direction="against the currency whose market is open", entry="at the start of the local session",
               stop="n/a", target="the end of the session", sizing="n/a", winners="n/a", losers="n/a",
               regime_change="n/a", invalidation="n/a", stays_out="n/a", ignores="n/a"),
           "European hours for EUR/GBP/CHF pairs", "during the London/overlap session, sell EUR- and GBP-based pairs against USD",
           "12 H1 bars", "fixed", "H1", "EURUSD, GBPUSD", ("session",),
           tests=({"condition": "session=mid", "side": "SELL", "exit": "E3", "timeframe": "H1",
                   "instruments": ["EURUSD", "GBPUSD"]},),
           status="REJECTED",
           results=({"trial": "SL-002", "hypothesis": "SL-002-01", "verdict": "REJECTED", "summary": "n 8,901, -0.105R per trade (t -8.0): the documented effect is far smaller than an H1 trade's costs"},)),
    Method("SL-RANGE-REVERSION", "Mean reversion inside ranges (band trading)", "discretionary / technical",
           (Source("Bollinger, Bollinger on Bollinger Bands (2001)", "book", "C"),),
           ("SHORT_TERM_REVERSAL", "REGIME_DEPENDENCE"),
           _dp(assumptions="in a range, extremes revert to the middle", prefers="low trend efficiency",
               avoids="trending markets (band walks)", direction="toward the middle", entry="at a band extreme",
               stop="beyond the extreme", target="the middle band", sizing="fixed", winners="exit at the middle",
               losers="stopped", regime_change="stop trading when a trend starts", invalidation="a band walk",
               stays_out="trending markets", ignores="n/a"),
           "ranging markets", "low trend efficiency and price at a 24-bar extreme -> fade it", "short barrier",
           "fixed", "H1", "any", ("er120", "range_pos24"),
           tests=({"condition": "er120=low&range_pos24=high", "side": "SELL", "exit": "E1", "timeframe": "H1"},
                  {"condition": "er120=low&range_pos24=low", "side": "BUY", "exit": "E1", "timeframe": "H1"}),
           status="REJECTED",
           results=({"trial": "DP-001", "hypothesis": "screen cells er120 x range_pos24", "verdict": "REJECTED",
                     "summary": "every cell negative net of costs on 2007-2010; no FDR discovery"},)),
    Method("SL-SMC-SWEEP", "Liquidity sweep reversal (SMC / ICT)", "practitioner price action",
           (Source("ICT / 'smart money concepts' teaching (no published, audited performance)", "practitioner", "D"),),
           ("LIQUIDITY_SWEEP", "SHORT_TERM_REVERSAL"),
           _dp(assumptions="institutions run stops beyond swings, then reverse", prefers="swept highs/lows at session times",
               avoids="no sweep", direction="against the sweep", entry="after price reclaims the swept level",
               stop="beyond the sweep", target="the opposite liquidity", sizing="fixed risk",
               winners="partials at liquidity", losers="stopped", regime_change="not specified",
               invalidation="acceptance beyond the swept level", stays_out="no setup", ignores="indicators"),
           "a confirmed swing swept and reclaimed", "smc_sweep = +1 -> long; -1 -> short", "barrier or structure exit",
           "fixed", "H1", "FX", ("smc_sweep",),
           tests=({"condition": "smc_sweep=high", "side": "BUY", "exit": "E1", "timeframe": "H1"},
                  {"condition": "smc_sweep=low", "side": "SELL", "exit": "E1", "timeframe": "H1"}),
           status="REJECTED",
           results=({"trial": "DP-001 / PR-001 / archive", "hypothesis": "smc_sweep cells; SWEEP_REVERSAL family",
                     "verdict": "REJECTED", "summary": "no FDR discovery; the production family lost in PR-001"},)),
    Method("SL-CARRY", "Currency carry", "macro / systematic",
           (Source("Lustig & Verdelhan, The cross-section of foreign currency risk premia, American Economic Review "
                   "97 (2007)", "academic", "A"),
            Source("Menkhoff, Sarno, Schmeling & Schrimpf, Carry trades and global FX volatility, J. Finance 67 (2012)",
                   "academic", "A")),
           ("CARRY",),
           _dp(assumptions="interest differentials are not fully offset by depreciation (a risk premium)",
               prefers="calm, low-volatility markets", avoids="volatility spikes (carry crashes)",
               direction="long high-yield, short low-yield", entry="monthly rebalance", stop="none; risk-off exits",
               target="none", sizing="portfolio weights", winners="held", losers="held through; crash risk",
               regime_change="crashes in global risk-off", invalidation="rate differential closing",
               stays_out="when volatility spikes (in managed versions)", ignores="charts"),
           "calm markets", "long the high-rate currency", "monthly", "portfolio", "monthly", "G10 FX", (),
           untestable_because="needs interest-rate data per currency; the rate sources are blocked by the network "
                              "policy here (FRED, BIS, ECB refused)"),
    Method("SL-XS-MOMENTUM", "Cross-sectional currency momentum", "systematic",
           (Source("Menkhoff, Sarno, Schmeling & Schrimpf, Currency momentum strategies, J. Financial Economics 106 "
                   "(2012)", "academic", "A"),),
           ("CROSS_SECTIONAL_MOMENTUM",),
           _dp(assumptions="relative winners keep winning", prefers="many currencies", avoids="n/a",
               direction="rank currencies by past return", entry="monthly", stop="none", target="none",
               sizing="equal-weight portfolios", winners="held", losers="rotated out",
               regime_change="weakens after high volatility", invalidation="rank change", stays_out="never",
               ignores="n/a"),
           "any", "long the top-ranked currencies, short the bottom", "monthly", "portfolio", "monthly", "G10 FX",
           ("xs_mom",),
           tests=({"condition": "xs_mom=high", "side": "BUY", "exit": "D4", "timeframe": "D1"},
            {"condition": "xs_mom=low", "side": "SELL", "exit": "D4", "timeframe": "D1"}),
           status="REJECTED",
           results=({"trial": "XS-001", "hypothesis": "XS-001-L/S", "verdict": "REJECTED",
                     "summary": "the dollar legs of the seven majors (24-day rank, ~1-month hold): strongest BUY "
                                "-0.13R (n 203, t -2.1), weakest SELL -0.11R (n 188, t -1.7); every battery check "
                                "failed. The paper's effect lives mostly in minor currencies, absent here"},)),
    Method("SL-PPP-VALUE", "FX value (purchasing-power parity)", "macro / systematic",
           (Source("Asness, Moskowitz & Pedersen, Value and momentum everywhere, J. Finance 68 (2013)", "academic", "A"),),
           ("VALUE_PPP",), _dp(assumptions="exchange rates revert slowly to PPP", prefers="long horizons"),
           "any", "long undervalued currencies", "years", "portfolio", "monthly", "G10 FX", (),
           untestable_because="needs price-level (CPI) data; not available here"),
    Method("SL-MARKET-MAKING", "Market making / spread capture", "high-frequency",
           (Source("Avellaneda & Stoikov, High-frequency trading in a limit order book, Quantitative Finance 8 (2008)",
                   "academic", "B"),),
           ("INVENTORY_SPREAD_CAPTURE",), _dp(assumptions="earn the spread, manage inventory and adverse selection"),
           "liquid, stable markets", "quote both sides", "inventory limits", "inventory risk", "tick", "any", (),
           untestable_because="needs order-book data, limit orders and latency a retail broker does not offer; a "
                              "retail account pays the spread instead of earning it"),
    Method("SL-REGIME-SWITCH", "Continuation or reversal, chosen by regime", "synthesis (ours)",
           (Source("Synthesis of SL-TSMOM/SL-DONCHIAN (continuation) and SL-PULLBACK/SL-RANGE-REVERSION (reversal); "
                   "their conflict is the hypothesis", "institutional", "B"),),
           ("REGIME_DEPENDENCE", "TREND_CONTINUATION", "SHORT_TERM_REVERSAL"),
           _dp(assumptions="both schools are right in their own regime"),
           "trend efficiency decides which school applies",
           "high er120 and a strong 24-bar move -> go with it; low er120 and the same move -> fade it",
           "barrier", "fixed", "H1", "FX", ("er120", "r24"),
           tests=({"condition": "er120=high&r24=high", "side": "BUY", "exit": "E1", "timeframe": "H1"},
                  {"condition": "er120=low&r24=high", "side": "SELL", "exit": "E1", "timeframe": "H1"}),
           status="REJECTED",
           results=({"trial": "DP-001", "hypothesis": "screen cells er120 x r24 (both sides)", "verdict": "REJECTED",
                     "summary": "no cell discovered; every cell negative net of costs"},)),
)


def library() -> tuple[Method, ...]:
    return LIBRARY


def conflicts(methods=LIBRARY) -> list[dict]:
    """Pairs of methods whose principles predict opposite actions in overlapping conditions. Kept, not resolved:
    each conflict is itself a hypothesis (does a regime separate them?)."""
    opposite = {("TREND_CONTINUATION", "SHORT_TERM_REVERSAL"), ("BREAKOUT", "SHORT_TERM_REVERSAL"),
                ("BREAKOUT", "LIQUIDITY_SWEEP")}
    out = []
    for i, a in enumerate(methods):
        for b in methods[i + 1:]:
            for p, q in opposite:
                if (p in a.principles and q in b.principles) or (q in a.principles and p in b.principles):
                    out.append({"a": a.strategy_id, "b": b.strategy_id, "principles": [p, q],
                                "question": "under which regime does each hold? (see SL-REGIME-SWITCH)"})
                    break
    return out


def principle_priority(methods=LIBRARY) -> list[dict]:
    """Research priority: principles supported by several INDEPENDENT sources of good quality rank higher.
    Priority orders what to test next; it is never evidence that anything works here."""
    score = defaultdict(lambda: {"methods": [], "sources": set(), "best": "D"})
    for m in methods:
        for p in m.principles:
            s = score[p]
            s["methods"].append(m.strategy_id)
            s["sources"] |= {src.citation for src in m.sources}
            s["best"] = min(s["best"], m.evidence_quality)
    weight = {"A": 3, "B": 2, "C": 1, "D": 0}
    rows = [{"principle": p, "methods": v["methods"], "independent_sources": len(v["sources"]),
             "best_quality": v["best"], "priority": len(v["sources"]) * weight[v["best"]]} for p, v in score.items()]
    return sorted(rows, key=lambda r: (-r["priority"], r["principle"]))


def knowledge_graph(methods=LIBRARY) -> dict:
    """SOURCE -> METHOD -> PRINCIPLE -> CONDITION/FEATURE -> TEST -> RESULT, as nodes and edges."""
    nodes, edges = {}, []

    def node(kind, key, **data):
        nid = f"{kind}:{key}"
        nodes.setdefault(nid, {"id": nid, "kind": kind, **data})
        return nid

    for m in methods:
        mid = node("method", m.strategy_id, name=m.name, status=m.status, evidence_quality=m.evidence_quality,
                   knowledge_class="DOCUMENTED_FACT")
        for s in m.sources:
            edges.append((node("source", s.citation, quality=s.quality, kind_of_source=s.kind), "documents", mid))
        for p in m.principles:
            edges.append((mid, "rests_on", node("principle", p, text=PRINCIPLES[p], knowledge_class="INFERRED_PRINCIPLE")))
        for f in m.features:
            edges.append((mid, "measured_by", node("feature", f)))
        for t in m.tests:
            tid = node("hypothesis", f"{m.strategy_id}:{t['condition']}:{t['side']}", knowledge_class="HYPOTHESIS", **t)
            edges.append((mid, "tested_as", tid))
        for r in m.results:
            rid = node("result", f"{r['trial']}:{m.strategy_id}", **r)
            edges.append((mid, "judged_by", rid))
        if m.untestable_because:
            edges.append((mid, "blocked_by", node("gap", m.strategy_id, reason=m.untestable_because,
                                                   knowledge_class="UNCERTAIN")))
    return {"version": LIBRARY_VERSION, "nodes": list(nodes.values()),
            "edges": [{"from": a, "rel": r, "to": b} for a, r, b in edges]}


def pending_tests(methods=LIBRARY) -> list[tuple[Method, dict]]:
    """Machine-testable forms of methods not yet judged: the next hypotheses for the engine."""
    return [(m, t) for m in methods if m.status in ("RESEARCHED", "HYPOTHESIS") for t in m.tests]


def to_json(methods=LIBRARY) -> list[dict]:
    out = []
    for m in methods:
        d = asdict(m)
        d["evidence_quality"] = m.evidence_quality
        out.append(d)
    return json.loads(json.dumps(out, default=list))
