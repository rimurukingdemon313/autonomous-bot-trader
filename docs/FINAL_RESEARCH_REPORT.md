# Final research report: the master program and RV-1

## Final state: **RESEARCH FAILED — NO DEPLOYABLE EDGE** (Path B)

**No candidate in this repository's research is VALIDATED.** The edge registry holds:

- 54 REJECTED;
- 0 PROMISING;
- 0 VALIDATED.

The system is therefore **not ready for paper or demo trading of an edge**: there is no edge to trade.

The infrastructure is unchanged and intact:

- the Edge Engine, which abstains with NO TRADE;
- the Risk Engine, the demo guard and the paper engine;
- the TradeLocker adapter.

Running it now would correctly produce NO TRADE.

## 1. Repository state

| Item | State |
|---|---|
| Branch | `main` |
| Research commits | H.10 audit `a0b410c` → RV-1 preregistration `57f6449` → this report (the research commit) |
| Live trading, Risk Engine, execution, broker integration, sizing | **not modified** by any of this work |
| Tests | the full suite passes: 593 at the preregistration; the final count is in §15 |

## 2–3. H.10 data audit

- **Commit:** `a0b410c`.
- **Verdict:** SUFFICIENT FOR RV-1.
- **Report:** [H10_DATA_AUDIT.md](H10_DATA_AUDIT.md).

**What it established:**

- **Provenance:** Federal Reserve H.10 → FRED → the datahub mirror. The mirror is used at pinned
  commits, because the official endpoints are unreachable here.
- **Official values recovered exactly:** 0 of 4,524 per currency fall off the published grid.
- **No revisions** across three vintages, 1999–2016.
- **Timing:** noon New York, confirmed against bid/ask data in every year 2008–2016.
- **Point in time:** a rate is usable from 17:00 New York on the next business day.
- **JPY** has no policy rate on 2,577 of 4,695 weekdays, 1999–2016.

## 4–5. RV-1 preregistration and frozen specification

**Preregistration commit:** `57f6449`, made before any outcome was computed.

| Item | Value |
|---|---|
| Spec | `research/specs/RV-1.json`, sha256 `3bcf1b1bb496613d8502f61a448cf5a6ad315e353f3e55fb7f63caafe0210517` |
| Document | [research/preregistrations/RV-1.md](../research/preregistrations/RV-1.md) |
| Registry | trial `RV-1`: 6 tests, \|t\| ≥ 2.807, which is Bonferroni over the 4 earlier tests on 2000-01..2007-03 plus 6 |
| Point-in-time check | 40 real decisions, 2000–2016: 0 differences when every unusable observation is removed |

**The design.**

| Element | Frozen as |
|---|---|
| Universe | USD, EUR, JPY, GBP, CHF, CAD, AUD, NZD |
| Data | H.10 (signals; Stage-1 returns), BIS policy rates, Dukascopy bid/ask (Stage-2 execution) |
| Transformation | currency values in USD; the relative return is the return minus the mean of the eight, so the common dollar move cancels |
| Timing | decision on Friday at 17:00 New York, using rates usable then (normally Thursday's noon fixing); forward week from Monday's fixing to the next Monday's |
| Book | centred ranks, sum 0, gross 2; currency-neutral; no sizing (the Risk Engine's) |
| Stage-1 statistic | the weekly Spearman IC against the next week's relative returns; t over non-overlapping weeks |
| Stage-2 threshold | the registry's Bonferroni over its tests on 2008-07..2017-01 plus the number of candidates (**3.4171** with one candidate) |
| Holdout | 2017, sealed, single-use, for ONE candidate that passed everything else |

**Gates.**

- **Stage 1:** |t| ≥ 2.807, ≥ 100 weeks, both halves the same sign, no single currency flipping the
  sign, and the book the same sign.
- **Stage 2:** net t at the Stage-2 threshold, plus robustness checks R1–R8.

## 6–8. Stage 1: the information test, 2000-01 → 2007-03 (H.10)

| ID | Test | Weeks | Mean IC | t (required 2.807) | Gates | Result |
|---|---|---|---|---|---|---|
| **RV1-H1-CARRY** | high-rate currencies outperform | 376 | **+0.081** | **3.09** | all pass | **PASSED → Stage 2** |
| RV1-H2-MOMENTUM | 3- and 12-month relative momentum, skip a week | 375 | +0.029 | 1.18 | t | rejected |
| RV1-H3-REVERSAL | one-week reversal | 376 | +0.007 | 0.30 | t, halves, leave-one-out | rejected |
| RV1-H4-VALUE | five-year reversal (a PRICE proxy, not PPP) | 168 | −0.035 | −0.98 | t, book sign | rejected |
| RV1-H5-CARRY-VOL | carry IC, low minus high volatility | 200 / 172 | +0.015 (low 0.088, high 0.074) | 0.27 | t | rejected |
| RV1-H6-MOMENTUM-VOL | momentum IC, low minus high volatility | 200 / 172 | +0.103 (low +0.076, high −0.028) | 2.10 | t | rejected |

**Carry in Stage 1.** Ranking currencies by policy rate predicted next-week relative performance:

- mean IC is positive in **every** year 2000–2007 (+0.002 to +0.193);
- the halves are +0.067 and +0.096;
- leaving out any one currency, the IC stays between +0.068 and +0.094;
- without its most favourable week, t is still 3.01.

**But the information was small in money.** The currency-neutral book earned +0.073% a week gross
(annual Sharpe 0.47, t 1.25), mostly from USD and NZD. The IC measures rank agreement; the book's
return is dominated by a few large relative moves.

**H6 (t 2.10)** is a near miss and is recorded as REJECTED. It is not carried forward.

## 9–11. Stage 2: carry on bid/ask with costs, 2008-07 → 2016

Trial `RV-1-S2`: 1 candidate, threshold t ≥ 3.4171, 440 weeks.

| Measure | Weekly, % of notional |
|---|---|
| Gross (spot P&L) | −0.036% (t −0.41) |
| Financing (rate differential minus the 0.5%/yr markup) | +0.036% |
| Costs (spread, slippage, commission) | 0.0003% |
| **Net** | **−0.001%** (t −0.01; annual Sharpe 0.00) |
| Abstention control (dispersion ≥ median) | −0.057% (t −1.22): worse |

**The interest earned was cancelled exactly by the high-yielders' spot losses.** This is the same
result as R3's pair-level test (+0.045R carry against −0.101R spot), now in a currency-neutral form.

**Robustness:**

| Check | Result |
|---|---|
| R1 halves | 2008-07..2012-06 −0.029%/wk, 2012-07..2016 +0.024%/wk: **fail** |
| R2 years | 6 of 8 positive (2013 and 2015 negative): pass |
| R3 concentration | total gross P&L negative; the largest drag is CHF (−0.082). Leaving out AUD or NZD turns net more negative: **fail** |
| R4 outliers | −0.076%/wk without the 5 best weeks: **fail** |
| R5 costs × 2 | −0.0013%/wk: **fail** |
| R6 one day later | −0.001%/wk: **fail** |
| R7 regimes | low volatility +0.088%/wk (t 1.17), high −0.096%/wk (t −0.59); neither significantly negative: pass |
| R8 incremental | OLS alpha over the price-only momentum book −0.038%/wk, t −0.51: **fail** |

**Classification of RV1-H1-CARRY: REJECTED.** It passed Stage 1 and failed Stage 2: net ≤ 0, t far
below 3.4171, and six of eight robustness checks failed.

**Reporting notes:**

- The artifact field `turnover_mean` records gross exposure (always 2.0), not turnover. Weekly
  turnover was low because carry ranks rarely change; that is why costs are only 0.0003% a week.
- The book's one-time opening cost (about 1–2 bp) is not in the weekly series.

Neither affects the verdict.

**Not a basis for a new test.** Carry's better result in low volatility is the opposite-signed half
of H5, which Stage 1 did not support (t 0.27).

## 12. The 2017 holdout

**Not opened.** No candidate passed Stage 2, the preregistered condition. The sealed holdout remains
unspent.

## 13–14. Data quality and the AUDUSD defect

**The defect.** The repository's Dukascopy **AUDUSD** is defective in 2008-01 → 2008-09 and
2009-04 → 2009-09:

- it departs from Dukascopy's own AUDJPY / USDJPY by monthly medians of 7–30 bp, with maxima about
  140 bp;
- H.10 agrees with the triangle.

**RV-1 never read it.**

- Stage 1 used H.10.
- Stage 2 and the holdout path synthesise AUDUSD from AUDJPY / USDJPY: the bid is AUDJPY bid /
  USDJPY ask, the ask is AUDJPY ask / USDJPY bid.

**Earlier results that could theoretically be affected.** These traded AUDUSD from the defective
series inside the defective months:

| Programs | How the defective data entered |
|---|---|
| R2A–R2D, R3, R4 (the CPI legs), COT-1 | judged periods from 2008-07 |
| DP-001 / DP-002 | discovery and validation segments |
| WF-001 / WF-002 / WF-003 | training folds |
| CP-001, SL-001, SL-002, XS-001 | fit periods only; their judged periods start 2013-07 |

**Why no verdict changes.**

- AUDUSD is 1 of 7–12 instruments, and the defective months are about 9 of the 102 judged months. So
  at most about 1–1.5% of judged trades are touched.
- Even if each of those trades had moved by a full 1R, far more than a ≤140 bp level error does to
  a daily-ATR-scaled trade, a mean would shift by about 0.015R.
- The closest any of these came to its threshold needed more than 0.1R.

**Nothing has been rerun or rewritten.** The defect is documented here and in the H.10 audit. Any
future research on AUDUSD must repair or replace those months first.

## 15. Tests

The full suite passes; the count at this commit is in its message.

**New tests:**

- `tests/unit/test_rv.py`, 11 tests:
  - average ranks and Spearman;
  - book neutrality;
  - decision timing;
  - signals unchanged under truncation;
  - a planted carry effect found and a null world not;
  - regimes using only past weeks;
  - costs and financing by hand;
  - USD-quoted valuation;
  - edge-registry adapter behaviour;
  - no risk, execution or broker reach;
  - frozen-spec integrity.
- `tests/unit/test_h10.py`, 8 tests.

## 16. Research commit

This report's commit. It includes:

- `research/knowledge/RV-1.json` (Stage 1) and `RV-1-S2.json` (Stage 2);
- the edge registry;
- the strategy library 1.4.0.

## 17. Final classification

| Candidate | Classification |
|---|---|
| RV1-H1-CARRY | **REJECTED** (Stage 1 passed; Stage 2 failed) |
| RV1-H2-MOMENTUM | **REJECTED** (Stage 1) |
| RV1-H3-REVERSAL | **REJECTED** (Stage 1) |
| RV1-H4-VALUE | **REJECTED** (Stage 1) |
| RV1-H5-CARRY-VOL | **REJECTED** (Stage 1) |
| RV1-H6-MOMENTUM-VOL | **REJECTED** (Stage 1) |

## 18. Does a genuine, deployable edge exist?

**No.**

Across 54 judged candidates, plus about 2,700 screened cells, no edge has passed the repository's
standards. The full list covers:

- pair-by-pair price rules;
- machine-learned models, from H1 to M15;
- macro, rate, positioning and cross-asset information;
- now, cross-sectional currency-neutral books.

**What the evidence supports claiming:**

- Cross-sectional carry carried real **ranking information** in 2000–2007: IC t 3.09 at a
  multiple-testing-corrected bar. That is a documented fact.
- That information **did not earn money after 2008**: the interest income equalled the spot loss.
- At a one-week horizon on these eight currencies, no price-, rate-, positioning- or
  cross-asset-based signal tested here has shown a tradable edge after costs.

**What it does not support claiming:**

- any profitability, in backtest or live;
- any reason to enable a strategy, on paper or in demo.

## 19. Is the AI architecture ready for paper or demo?

**For an edge: no, because there is no validated edge to put through it.**

**The architecture is preserved:**

- Data → Features → Quant signal (Edge Engine) → Edge Validator (registry; VALIDATED only) → AI
  interpretation (can only veto) → Risk Engine (final authority) → Execution (demo-guarded) →
  Learning.
- With zero VALIDATED edges, the Edge Validator passes nothing, and the system's correct output is
  NO TRADE (CLAUDE.md rule 8).
- Integration into the Edge Engine, paper monitoring and demo preparation, the program's Path A, were
  **not started**: their precondition (a VALIDATED edge) was not met.

## 20. Remaining engineering work

None is required by this program. The two items below are data hygiene, not research rounds; no new
research round is proposed.

1. **AUDUSD data repair.** Replace or flag Dukascopy AUDUSD for 2008-01..09 and 2009-04..09, for
   example by triangulating from AUDJPY / USDJPY, before any future research reads it.
2. **Prospective evidence.** Bars, spreads and H.10 rates recorded from now on are the only untouched
   data left, apart from the sealed 2017 holdout. They are the only way any future claim could be
   judged on unseen data.
