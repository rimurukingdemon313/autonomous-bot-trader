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

#: 1.1.0: Round 2 methods (risk-regime carry, forward premium, commodity currencies, momentum crashes) and
#: labelled claims per method
#: 1.2.0: Round 4 methods (positioning, news surprises, safe havens, gold/AUD, Taylor-rule inflation)
#: 1.3.0: positioning is no longer data-blocked: tested in COT-1 (CFTC TFF files supplied by the user), rejected
LIBRARY_VERSION = "library-1.3.0"
STATUSES = ("RESEARCHED", "HYPOTHESIS", "TESTING", "VALIDATED", "REJECTED", "DEGRADED", "RETIRED")
#: every claim a method record makes is labelled with how much we actually know
CLAIM_LABELS = ("DOCUMENTED FACT", "INFERRED PRINCIPLE", "HYPOTHESIS", "TESTING", "VALIDATED", "REJECTED",
                "UNCERTAIN")
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
    "RISK_REGIME": "risk appetite (e.g. implied volatility) decides whether risky currencies are bought or dumped",
    "FORWARD_PREMIUM": "a currency whose relative interest rate rose tends to appreciate, not depreciate as UIP says",
    "COMMODITY_CURRENCY": "a commodity exporter's currency moves with the price of its main export",
    "MOMENTUM_CRASH": "momentum strategies lose most in panic states and sharp rebounds; calm states are safer",
    "POSITIONING": "crowded speculative positioning precedes reversals (or: position changes carry information)",
    "NEWS_SURPRISE": "the unexpected part of a macro release moves the currency",
    "SAFE_HAVEN": "in risk-off episodes investors buy the safe-haven currencies (JPY, CHF)",
    "TAYLOR_RULE": "inflation and output gaps predict policy, and so the currency, through expected rates",
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
    claims: tuple[tuple[str, str], ...] = ()  # (label, statement): never inference presented as fact

    def __post_init__(self) -> None:
        if self.status not in STATUSES:
            raise ValueError(f"{self.strategy_id}: unknown status {self.status}")
        if any(label not in CLAIM_LABELS or not text.strip() for label, text in self.claims):
            raise ValueError(f"{self.strategy_id}: every claim needs a known label and a statement")
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
           "calm markets", "long the high-rate currency", "monthly", "portfolio", "monthly", "G10 FX",
           ("vix_state", "vix_trend"),
           tests=({"condition": "vix_state=low", "side": "BUY", "exit": "D4", "timeframe": "D1"},
                  {"condition": "vix_trend=high", "side": "SELL", "exit": "D3", "timeframe": "D1"}),
           status="REJECTED",
           results=({"trial": "R2A", "hypothesis": "R2A-1/R2A-2", "verdict": "REJECTED",
                     "summary": "spot legs only (no carry income measurable): long AUDJPY/AUDUSD/NZDUSD while VIX < 20 "
                                "-0.119R (n 263, P(direction) 45%); short after VIX rises -0.056R (n 475). The omitted "
                                "income is estimated at +0.05-0.08R and would not change the sign"},
                    {"trial": "R3", "hypothesis": "R3-A/B/G/H", "verdict": "REJECTED",
                     "summary": "BIS policy rates, 8 pairs, 2008-07 -> 2017-01, carry income included as a "
                                "RATE-DIFFERENTIAL CARRY PROXY: carry long -0.083R net (n 341; carry +0.045R, spot "
                                "-0.101R gross, P(direction) 41%); while VIX < 20 -0.117R; without a recent policy "
                                "move -0.044R"}),
           claims=(("DOCUMENTED FACT", "carry portfolios across many currencies earned a premium, with crashes in "
                                       "global risk-off (Lustig & Verdelhan 2007; Menkhoff et al. 2012)"),
                   ("DOCUMENTED FACT", "AUD and NZD out-yielded USD and JPY at every date from 2008-07 to 2016-12 "
                                       "(prior knowledge of RBA/RBNZ/Fed/BoJ policy rates; not re-opened here)"),
                   ("INFERRED PRINCIPLE", "the premium is compensation for crash risk, so it should be earned in "
                                          "calm regimes"),
                   ("REJECTED", "the spot legs of three positive-carry majors rise in calm regimes (R2A-1)"),
                   ("REJECTED", "carry currencies keep falling for a week after VIX starts rising (R2A-2)"),
                   ("REJECTED", "carry INCLUDING its interest income (rate-differential proxy, BIS policy rates) has "
                                "positive net expectancy on 8 majors, 2008-2016 (R3-A/G/H): the income is smaller "
                                "than the spot loss"),
                   ("UNCERTAIN", "carry on the JPY pairs: untestable under the frozen rule (no BoJ policy rate "
                                 "2013-04 -> 2016-09)"))),
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
    Method("SL-FORWARD-PREMIUM", "Rate-differential momentum (the forward-premium anomaly)", "macro / systematic",
           (Source("Fama, Forward and spot exchange rates, J. Monetary Economics 14 (1984)", "academic", "A"),
            Source("Engel, The forward discount anomaly and the risk premium, J. Empirical Finance 3 (1996)",
                   "academic", "A")),
           ("FORWARD_PREMIUM",),
           _dp(assumptions="uncovered interest parity fails: capital chases yield slowly, so the currency whose "
                           "relative rate rose keeps appreciating; information used: interest-rate changes",
               prefers="clear, persistent policy divergence", avoids="rate moves driven by risk-off flight to safety",
               direction="with the change in the differential", entry="after the rate change is known (monthly)",
               stop="none documented; portfolio risk", target="none", sizing="portfolio", winners="held",
               losers="held; rebalanced monthly", regime_change="reverses in crises (flight to safety)",
               invalidation="the differential moving back", stays_out="not documented", ignores="charts"),
           "policy divergence", "buy the currency whose relative yield rose", "monthly", "portfolio", "monthly",
           "G10 FX", ("usd_rate",),
           tests=({"condition": "usd_rate=high", "side": "BUY", "exit": "D4", "timeframe": "D1"},
                  {"condition": "usd_rate=low", "side": "SELL", "exit": "D4", "timeframe": "D1"}),
           status="REJECTED",
           results=({"trial": "R2B", "hypothesis": "R2B-1/R2B-2", "verdict": "REJECTED",
                     "summary": "last month's US 10y change (> 10bp) as the differential change, 7 USD pairs: "
                                "-0.108R (n 396, P(direction) 46%) and -0.061R (n 381, 51%): coin-flip direction"},
                    {"trial": "R3", "hypothesis": "R3-C/D/E/F", "verdict": "REJECTED",
                     "summary": "the true two-sided policy differential: widening -0.160R (n 149), narrowing -0.108R "
                                "(n 218), accelerating +0.007R (n 249, t 0.10), after a policy move -0.151R (n 95)"}),
           claims=(("DOCUMENTED FACT", "regressions of currency changes on the forward premium give the wrong sign "
                                       "for UIP (Fama 1984)"),
                   ("INFERRED PRINCIPLE", "a CHANGE in the differential should be followed by appreciation of the "
                                          "currency it favours"),
                   ("HYPOTHESIS", "with only US rates observable, the US 10y change stands in for the differential "
                                  "change (other rates near their floors in 2008-2016)"),
                   ("REJECTED", "the next month's move follows last month's US-yield change (R2B)"),
                   ("REJECTED", "the next month's move follows a widening, narrowing or accelerating policy-rate "
                                "differential, or a recent policy move (R3-C/D/E/F)"))),
    Method("SL-COMMODITY-FX", "Commodity currencies follow their export prices", "macro / cross-asset",
           (Source("Chen & Rogoff, Commodity currencies, J. International Economics 60 (2003)", "academic", "A"),
            Source("Ferraro, Rogoff & Rossi, Can oil prices forecast exchange rates?, J. Int. Money and Finance 54 "
                   "(2015)", "academic", "A")),
           ("COMMODITY_CURRENCY",),
           _dp(assumptions="terms of trade drive the real exchange rate of commodity exporters; information used: "
                           "the commodity price",
               prefers="large, persistent commodity moves", avoids="moves driven by the USD itself",
               direction="with the export price", entry="documented as CONTEMPORANEOUS (same day), not lagged",
               stop="n/a (a documented relationship, not a trading rule)", target="n/a", sizing="n/a",
               winners="n/a", losers="n/a", regime_change="the link weakens when the commodity's share of exports "
                                                         "falls", invalidation="n/a",
               stays_out="n/a", ignores="n/a"),
           "large oil moves", "buy the currency oil favours after a 5% move in 20 days", "5-day time exit", "fixed",
           "D1", "USDCAD", ("oil_pull",),
           tests=({"condition": "oil_pull=high", "side": "BUY", "exit": "D3", "timeframe": "D1"},
                  {"condition": "oil_pull=low", "side": "SELL", "exit": "D3", "timeframe": "D1"}),
           status="REJECTED",
           results=({"trial": "R2C", "hypothesis": "R2C-1/R2C-2", "verdict": "REJECTED",
                     "summary": "buy USDCAD after oil fell > 5%: +0.047R net (n 169, P(direction) 56%, t 0.77), "
                                "mostly the 2014-15 oil collapse; the mirror -0.088R"},),
           claims=(("DOCUMENTED FACT", "the oil-CAD link is strong at daily frequency but contemporaneous; lagged "
                                       "oil does not forecast CAD out of sample (Ferraro et al. 2015)"),
                   ("REJECTED", "a 20-day oil move predicts the next week of USDCAD at the required level (R2C)"),
                   ("UNCERTAIN", "a lagged effect in LARGE, persistent oil moves (2014-15): positive here, not "
                                 "distinguishable from one episode"))),
    Method("SL-MOMENTUM-CRASH", "Momentum only outside panic states", "systematic",
           (Source("Daniel & Moskowitz, Momentum crashes, J. Financial Economics 122 (2016)", "academic", "A"),
            Source("Moskowitz, Ooi & Pedersen, Time series momentum, J. Financial Economics 104 (2012)", "academic",
                   "A")),
           ("TREND_CONTINUATION", "MOMENTUM_CRASH", "RISK_REGIME"),
           _dp(assumptions="momentum's losses cluster in high-volatility panic states and rebounds; information "
                           "used: the trend sign and a risk-regime gauge",
               prefers="calm, trending markets", avoids="panic states (high implied volatility)",
               direction="the sign of the 120-day move", entry="while the risk regime is calm",
               stop="documented versions scale down instead of stopping", target="none",
               sizing="volatility-scaled (documented); ours: the Risk Engine", winners="held",
               losers="exit when the sign flips", regime_change="the gauge moving to stress",
               invalidation="the regime or the trend sign changing", stays_out="panic states", ignores="value"),
           "calm regimes", "trend sign while VIX < 20", "20-day time exit, 3 ATR stop", "fixed", "D1", "G10 FX",
           ("trend_sign", "vix_state"),
           tests=({"condition": "trend_sign=high&vix_state=low", "side": "BUY", "exit": "D4", "timeframe": "D1"},
                  {"condition": "trend_sign=low&vix_state=low", "side": "SELL", "exit": "D4", "timeframe": "D1"}),
           status="REJECTED",
           results=({"trial": "R2D", "hypothesis": "R2D-1/R2D-2", "verdict": "REJECTED",
                     "summary": "12 pairs, 2008-07 -> 2017-01: BUY uptrends while calm -0.040R (n 593); SELL "
                                "downtrends while calm +0.077R (n 581, t 0.85, passes cost/delay stress; fails "
                                "significance, random, years, instruments, outliers: EURCHF 2015 dominates)"},),
           claims=(("DOCUMENTED FACT", "equity momentum's worst losses occur in panic states and rebounds (Daniel & "
                                       "Moskowitz 2016)"),
                   ("INFERRED PRINCIPLE", "the same crash mechanism applies to FX time-series momentum"),
                   ("REJECTED", "restricting FX momentum to VIX < 20 produces a net edge on either side (R2D)"),
                   ("UNCERTAIN", "the SELL side of FX trend: positive but insignificant in four separate tests "
                                 "(CP-001-T2, CP-001-T4, SL-001-02, R2D-2), each dominated by one episode"))),
    Method("SL-POSITIONING", "Speculative positioning (CFTC Commitments of Traders)", "positioning / sentiment",
           (Source("Klitgaard & Weir, Exchange rate changes and net positions of speculators in the futures market, "
                   "FRBNY Economic Policy Review 10 (2004)", "institutional", "B"),
            Source("Tornell & Yuan, Speculation and hedging in the currency futures markets: are they informative to "
                   "the spot exchange rates?, J. Futures Markets 32 (2012)", "academic", "B")),
           ("POSITIONING",),
           _dp(assumptions="speculators' net futures positions reveal flows; extremes mark crowded trades; "
                           "information used: weekly CFTC positions (Tuesday data, released Friday)",
               direction="against extremes (reversal) or with changes (flow)", entry="after the Friday release",
               stop="not documented", target="not documented", sizing="not documented", winners="n/a", losers="n/a",
               regime_change="extremes can persist in strong trends", invalidation="positions unwinding",
               stays_out="no extreme", ignores="n/a", prefers="liquid CME currency futures", avoids="n/a"),
           "crowded positioning", "fade the extreme / follow the change", "weeks", "52-week percentile, fixed 0.90/0.10",
           "weekly", "the seven direct USD pairs (CME currency futures)", ("cot_spec_pct", "cot_spec_flow_pct"),
           tests=tuple({"condition": f"rule:{r}", "side": "SIGNED", "exit": "D3", "timeframe": "D1"}
                       for r in ("p_rev", "p_cont", "c_rev", "c_cont", "i_rev", "i_cont", "f_cont", "f_rev", "u_rev",
                                 "v_rev", "x_veto")),
           status="REJECTED",
           results=({"trial": "COT-1", "hypothesis": "COT1-P/C/I/F/U/V/X (11)", "verdict": "REJECTED",
                     "summary": "Leveraged Money extremes: against -0.063R (n 915, t -1.97), with -0.011R (n 912); "
                                "with price also extreme, with +0.017R (t 0.37; carried by EURUSD and 2008); COT added "
                                "under 0.01R to a price-only rule; as a crowding veto on the 13-week trend: no "
                                "difference (+0.0002R). Judged 2008-07 .. 2016-01 at t >= 3.414; holdout not opened"},),
           claims=(("DOCUMENTED FACT", "weekly changes in speculators' net positions move WITH the exchange rate in the "
                                       "same week (Klitgaard & Weir 2004)"),
                   ("UNCERTAIN", "positioning extremes have been reported to precede reversals (Tornell & Yuan "
                                 "2012), on pre-2012 data; not re-opened here"),
                   ("REJECTED", "Leveraged Money positioning extremes, flows, unwinds or crowding predict the next "
                                "week's direction of the seven USD pairs after costs, 2008-07 .. 2016-01 (COT-1)"))),
    Method("SL-NEWS-SURPRISE", "Macro announcement surprises", "event / macro",
           (Source("Andersen, Bollerslev, Diebold & Vega, Micro effects of macro announcements: real-time price "
                   "discovery in foreign exchange, American Economic Review 93 (2003)", "academic", "A"),),
           ("NEWS_SURPRISE",),
           _dp(assumptions="only the surprise (actual minus consensus) is news; information used: historical "
                           "consensus forecasts and first-release values",
               direction="with the surprise", entry="documented: within minutes of the release", stop="n/a",
               target="n/a", sizing="n/a", winners="n/a", losers="n/a", regime_change="the response is state-dependent",
               invalidation="n/a", stays_out="n/a", ignores="n/a", prefers="US releases", avoids="n/a"),
           "release times", "the surprise's direction", "minutes", "n/a", "intraday", "G10 FX", (),
           untestable_because="DATA-BLOCKED: historical consensus is proprietary (Bloomberg/Reuters) and the calendar "
                              "sites are refused; revised values would leak; nothing is reconstructed",
           claims=(("DOCUMENTED FACT", "surprises move FX within minutes, and the adjustment is fast (Andersen et al. "
                                       "2003)"),
                   ("INFERRED PRINCIPLE", "a fast, complete response leaves little for a daily-bar system after costs"),
                   ("UNCERTAIN", "any multi-day drift after surprises on our pairs: untested, data unavailable"))),
    Method("SL-SAFE-HAVEN", "Safe-haven currencies after risk shocks", "macro / risk",
           (Source("Ranaldo & Soederlind, Safe haven currencies, Review of Finance 14 (2010)", "academic", "A"),
            Source("Habib & Stracca, Getting beyond carry trade: what makes a safe haven currency?, J. International "
                   "Economics 87 (2012)", "academic", "A")),
           ("SAFE_HAVEN", "RISK_REGIME"),
           _dp(assumptions="in risk-off, investors repatriate and buy JPY and CHF; information used: equity "
                           "implied volatility (VIX)",
               direction="long JPY/CHF after a risk shock", entry="after the shock", stop="n/a", target="n/a",
               sizing="n/a", winners="n/a", losers="n/a", regime_change="policy intervention (SNB floor, BoJ QQE)",
               invalidation="risk appetite returning", stays_out="calm markets", ignores="n/a",
               prefers="acute shocks", avoids="n/a"),
           "risk shocks", "buy the haven that has not yet moved", "a week", "fixed", "D1", "JPY/CHF pairs",
           ("vix_jump", "own5"),
           tests=({"condition": "vix_jump=high&own5=high", "side": "SELL", "exit": "D3", "timeframe": "D1"},),
           status="REJECTED",
           results=({"trial": "R4", "hypothesis": "R4-XA-VIX-A", "verdict": "REJECTED",
                     "summary": "registered 5 pairs: -0.134R (n 156, t -2.07, P(direction) 53%); the formal run judged "
                                "11 pairs by an engine defect (fixed; research/knowledge/corrections.json), also "
                                "rejected"},),
           claims=(("DOCUMENTED FACT", "JPY and CHF appreciate CONTEMPORANEOUSLY with risk shocks (Ranaldo & "
                                       "Soederlind 2010)"),
                   ("REJECTED", "a haven that has not yet moved catches up in the week after a >= 20% VIX jump "
                                "(R4-XA-VIX-A)"))),
    Method("SL-GOLD-AUD", "Gold leading the Australian dollar", "cross-asset",
           (Source("Chen & Rogoff, Commodity currencies, J. International Economics 60 (2003)", "academic", "A"),
            Source("Chen, Rogoff & Rossi, Can exchange rates forecast commodity prices?, Quarterly J. Economics 125 "
                   "(2010)", "academic", "A")),
           ("COMMODITY_CURRENCY",),
           _dp(assumptions="gold is a large Australian export; information used: the gold price",
               direction="with gold, when AUD has not followed", entry="after a 2% 5-day gold move", stop="n/a",
               target="n/a", sizing="n/a", winners="n/a", losers="n/a", regime_change="n/a", invalidation="n/a",
               stays_out="n/a", ignores="n/a", prefers="n/a", avoids="n/a"),
           "gold moves", "buy (sell) AUD after gold rose (fell) and AUD did not", "a week", "fixed", "D1", "AUD pairs",
           ("gold_pull", "own5"),
           tests=({"condition": "gold_pull=high&own5=low", "side": "BUY", "exit": "D3", "timeframe": "D1"},
                  {"condition": "gold_pull=low&own5=high", "side": "SELL", "exit": "D3", "timeframe": "D1"}),
           status="REJECTED",
           results=({"trial": "R4", "hypothesis": "R4-XA-GOLD-A/B", "verdict": "REJECTED",
                     "summary": "BUY +0.015R (n 102, t 0.16; +0.10R better than its price-only control, but negative "
                                "at 1.5% and 2.5% gold thresholds and without its best trade); SELL -0.163R (n 84)"},),
           claims=(("DOCUMENTED FACT", "commodity-currency exchange rates forecast commodity prices better than the "
                                       "reverse (Chen, Rogoff & Rossi 2010)"),
                   ("REJECTED", "gold leads AUD over the following week (R4-XA-GOLD-A/B)"))),
    Method("SL-TAYLOR-INFLATION", "Inflation-driven policy expectations (Taylor-rule fundamentals)", "macro",
           (Source("Molodtsova & Papell, Out-of-sample exchange rate predictability with Taylor rule fundamentals, "
                   "J. International Economics 77 (2009)", "academic", "A"),),
           ("TAYLOR_RULE",),
           _dp(assumptions="higher inflation implies a more hawkish central bank and a stronger currency; information "
                           "used: both countries' inflation and output gaps",
               direction="toward the currency whose inflation accelerates", entry="monthly, after the CPI release",
               stop="n/a", target="n/a", sizing="n/a", winners="n/a", losers="n/a", regime_change="zero lower bound",
               invalidation="n/a", stays_out="n/a", ignores="charts", prefers="both countries' data", avoids="n/a"),
           "monthly", "buy the pair favoured by US inflation acceleration", "about a month", "fixed", "D1", "USD pairs",
           ("usd_infl",),
           tests=({"condition": "usd_infl=high", "side": "BUY", "exit": "D4", "timeframe": "D1"},
                  {"condition": "usd_infl=low", "side": "SELL", "exit": "D4", "timeframe": "D1"}),
           status="REJECTED",
           results=({"trial": "R4", "hypothesis": "R4-MACRO-CPI-A/B", "verdict": "REJECTED",
                     "summary": "US side only (foreign monthly CPI unavailable): -0.049R (n 337, P(direction) 48%) and "
                                "-0.003R (n 332, 51%); positive only in 2008-2010 and when VIX >= 30"},),
           claims=(("DOCUMENTED FACT", "two-country Taylor-rule fundamentals showed out-of-sample predictability on "
                                       "1973-2006 data (Molodtsova & Papell 2009)"),
                   ("REJECTED", "US inflation acceleration alone predicts the USD pairs over the next month (R4)"),
                   ("UNCERTAIN", "the two-country version: untestable, foreign monthly CPI unavailable"))),
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
        for i, (label, text) in enumerate(m.claims):
            edges.append((mid, "claims", node("claim", f"{m.strategy_id}:{i}", text=text, knowledge_class=label)))
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
