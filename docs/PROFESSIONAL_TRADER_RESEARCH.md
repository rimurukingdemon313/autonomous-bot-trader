# Professional trader research

What documented, successful trading approaches actually do — and whether their principles
hold on **our** instruments, after **our** costs, out of sample.

A famous name is a reason to test a principle, never evidence that it works here. No signal is
copied; no performance claim is repeated as fact. We do not "read a trader's mind": each
decision process below is reconstructed from what the source documents, and every statement is
labelled with how much we actually know.

| Label | Meaning |
|---|---|
| **DOCUMENTED FACT** | stated in the cited source (a paper's measured result, a book's stated rule) |
| **INFERRED PRINCIPLE** | the general mechanism we extract from one or more sources; our reading, not theirs |
| **HYPOTHESIS** | a testable claim on our data, preregistered before it is judged |
| **VALIDATED EDGE** | a hypothesis that passed walk-forward / confirmation, the battery, the board and the registry threshold. **There are none.** |
| **UNCERTAIN CONCLUSION** | a pattern in our results too weak or too concentrated to act on |

The machine-readable form is `aitrader/research/discovery/library.py`, exported to
`research/knowledge/strategy_library.json` (methods, conflicts, principle priority) and
`research/knowledge/knowledge_graph.json` (TRADER/SOURCE → METHOD → PRINCIPLE → CONDITION →
FEATURE → ENTRY → EXIT → RISK → EXPECTED → TEST RESULT). `python scripts/strategy_library.py
export` regenerates both.

## Evidence quality

| Grade | What it takes | Examples in the library |
|---|---|---|
| A | peer-reviewed, out-of-sample or multi-decade, replicated | time-series momentum, carry, currency momentum, value |
| B | peer-reviewed, one study or one market | local-hours depreciation, market making theory |
| C | practitioner book with explicit rules, no audited record | Connors pullbacks, Crabel narrow ranges, Bollinger bands |
| D | teaching material with no published, audited performance | ICT / "smart money concepts" |

## The library and what our data says

| Method | Source (DOCUMENTED FACT) | Grade | Our test (HYPOTHESIS) | Result on our data | Status |
|---|---|---|---|---|---|
| Time-series momentum | Moskowitz, Ooi & Pedersen, JFE 2012; Hurst, Ooi & Pedersen, JPM 2017 | A | CP-001-T1/T2: 120-day move top/bottom tercile, D1, hold 20 days | long −0.02R (n 260); short +0.19R (n 251), t 1.03 vs 3.18 required; +0.86R in 2014, negative 2013 and 2016 | REJECTED |
| Moving-average trend | Faber 2007; Menkhoff & Taylor, JEL 2007 | A | CP-001-T3/T4: 48 vs 240-day average | long −0.00R; short +0.21R, t 1.00 | REJECTED |
| Donchian / Turtle breakout | Faith 2007; Hurst et al. 2017 | A | SL-001-01/02: new 120-day high/low, trailing exit D5 | long −0.04R (n 266); short +0.17R (n 290), t 0.65; fails permutation, years, instruments | REJECTED |
| Pullback in trend | Connors & Alvarez 2008 | C | SL-001-03/04: trend up and 6-day dip (mirror), D3 | −0.01R both sides; no better than random entries | REJECTED |
| Narrow-range breakout | Crabel 1990 | C | SL-001-05/06: tight range then strong day | long −0.16R (t −2.9); short −0.06R | REJECTED |
| Local-hours depreciation | Breedon & Ranaldo, JMCB 2013 | B | SL-002-01: sell EUR/GBP in European hours, H1 | −0.105R per trade, n 8,901, t −8.0 | REJECTED |
| Range reversion | Bollinger 2001 | C | DP-001 cells er120 × range_pos24 | every cell negative net | REJECTED |
| Liquidity sweep (SMC/ICT) | teaching material only | D | smc_sweep cells; SWEEP_REVERSAL family in PR-001; archive tests | no FDR discovery; lost in PR-001 | REJECTED |
| Regime switch (synthesis) | our synthesis of the continuation/reversal conflict | B | DP-001 cells er120 × r24 | every cell negative net | REJECTED |
| Carry | Lustig & Verdelhan, AER 2007; Menkhoff et al., JF 2012 | A | not testable here | needs interest rates; FRED/BIS/ECB blocked | RESEARCHED |
| Cross-sectional momentum | Menkhoff et al., JFE 2012 | A | not testable here | needs a ranking portfolio across many currencies | RESEARCHED |
| PPP value | Asness, Moskowitz & Pedersen, JF 2013 | A | not testable here | needs CPI data | RESEARCHED |
| Market making | Avellaneda & Stoikov, QF 2008 | B | not testable here | needs order-book data and limit-order latency; a retail account pays the spread instead of earning it | RESEARCHED |

Every judged form was preregistered (`research/preregistrations/CP-001-*.md`, `SL-00*-*.md`),
run once, and counted in the registry. Full numbers per check: `research/knowledge/CP-001.json`,
`SL-001.json`, `SL-002.json`.

## How the successful approaches decide (INFERRED PRINCIPLES)

Each method in the library carries a reconstructed decision process with the same twelve
fields — assumptions, direction, entry, stop, target, what it does with winners and with
losers, sizing, invalidation, when it stays out, what it prefers, what it ignores, and how it
behaves when the regime changes. Reading them side by side, the approaches with grade-A
evidence share a small set of habits:

1. **They trade slowly.** Documented, replicated edges in FX live at monthly horizons
   (momentum, carry, value), not hourly ones. Our own cost measurement explains why: an H1
   trade pays 0.09–0.21R in costs, a D1 trade about a fifth of that, a monthly rebalance almost
   nothing.
2. **They diversify across many markets** and size by volatility, so that no single position
   decides the year. Their published Sharpe ratios are portfolio results; a single pair's trades
   are much noisier.
3. **They accept long losing stretches** (momentum crashes, carry crashes) as the price of the
   premium. None of them claims a high win rate.
4. **Their edges are small and decay** after publication. That is a DOCUMENTED FACT for US
   equity anomalies (McLean & Pontiff, JF 2016); for FX it is an INFERRED PRINCIPLE. Our judged
   period starts after the momentum papers were published, so a decayed effect is what we
   would expect to measure.
5. **Short-horizon practitioner rules** (grades C/D) carry no audited record, and on our data
   none survived costs.

## Principle priority and conflicts

Priority = independent sources × best evidence grade (`principle_priority()`):
TREND_CONTINUATION (7 sources, A) > CUT_LOSSES_LET_WINNERS_RUN > BREAKOUT >
SHORT_TERM_REVERSAL (B) > CARRY, VOLATILITY_SCALING > … > LIQUIDITY_SWEEP (D, priority 0).

Conflicts are kept, not averaged away (`conflicts()`): 19 method pairs conflict, 11 of them
trend continuation against short-term reversal. The library's answer is a hypothesis, not a compromise: SL-REGIME-SWITCH says each
holds in its own regime (trend efficiency er120 deciding). DP-001 tested that on H1 — every
er120 × trigger cell was negative net of costs — so on our data neither side of the conflict
currently has an edge to resolve.

## Synthesis without copying

The M15/H1/H4 architecture is the synthesis the documented approaches suggest when they are
combined rather than copied: H4 for regime (where the grade-A trend evidence lives), H1 for
structure, M15 only for the entry. WF-003 tests exactly that on M15 with H1/H4 context, against
WF-002's H1 architecture, with identical data, costs and walk-forward method — see the
comparison in [TRADING_EDGE_REGISTRY.md](TRADING_EDGE_REGISTRY.md).

## UNCERTAIN CONCLUSION: the SELL side of trend

All three short-side trend forms were positive (+0.17 to +0.21R per trade) while every long-side
form was at or below zero. None was significant, and the gain is concentrated in 2014 — the
signature of one episode (the 2014–15 dollar rally: selling EURUSD, AUDUSD, NZDUSD in their
downtrends was buying dollars). It is recorded, not traded. It could be confirmed only on data
the judged period does not contain: the sealed holdout (single use, reserved for a candidate
that passes everything else) or data recorded from now on.

## Continuous learning

- An edge's live record is compared with its tested expectation by `edge_health`
  (`aitrader/decision/edge_engine.py`): a gap within 2 standard errors is **normal variance**
  and changes nothing; beyond it the edge is DEGRADED; negative with 95% confidence over ≥ 40
  trades, RETIRED. A few recent losses can never overwrite validated knowledge.
- Lessons from live losses follow CANDIDATE → VALIDATED (only on later outcomes) → RETIRED in
  `learning/experience.py`, and can only block.
- New documented methods enter as `Method` records with status RESEARCHED; `pending_tests()`
  turns a testable one into a DRAFT hypothesis charged against the registry.

## The final trading brain

At every M15 close the edge engine answers the twelve questions in its result (`answers`):
regime (measured H4/H1 values), principles that apply, principles in conflict, relevant edges,
validated BUY, validated SELL, expected value after costs, entry, invalidation, exit model,
current risk (the Risk Engine's), recent degradation — then BUY, SELL or ABSTAIN. With no
validated edge, questions 5–10 are answered "none", and the decision is ABSTAIN. That is the
truthful answer today; it changes only when research validates something.

## What would change the picture

Evidence the system does not have yet, in the order the library ranks it:

1. **Interest-rate data** (carry, grade A) — needs a network policy that allows FRED/ECB/BIS or a
   manually committed rate file.
2. **A wider universe** for cross-sectional momentum (grade A).
3. **Prospective data**: every M15 decision the scanner records from now on is new, untouched
   evidence. A hypothesis frozen today can be judged on it without spending the holdout.
