# RV-1: cross-sectional currency information (preregistration)

**Written and committed before any RV-1 outcome was computed.**

- **Frozen spec:** `research/specs/RV-1.json`, spec sha256
  `3bcf1b1bb496613d8502f61a448cf5a6ad315e353f3e55fb7f63caafe0210517`. Its code hash freezes
  `aitrader/research/discovery/rv.py`, `scripts/rv1.py` and the data loaders. Each stage refuses to run
  if either has changed.
- **Read before writing this:**
  - signal and regime counts, from predictors only;
  - a point-in-time check of every signal at 40 real decisions, 2000–2016: 0 differences when all data
    unusable at the decision is removed.
- **Not read:** no forward return, IC, book result or cost.

## Question

Can the system tell **which currencies will outperform the others** over the next week, rather than
"will EURUSD rise"? Every earlier test (48 rejected) predicted single pairs, whose moves the common
dollar factor dominates. RV-1 removes that factor by construction.

## Universe and data

**Currencies:** USD, EUR, JPY, GBP, CHF, CAD, AUD, NZD. Exactly these eight; none is added, none is
dropped.

**Data:**

| Data | Use |
|---|---|
| **H.10** noon rates, primary vintage 2018-10-17 (`aitrader/data/h10.py`) | Stage 1 signals and returns; signals in every stage |
| **BIS** policy rates (`aitrader/data/rates.py`) | Carry signal and the financing proxy. Point in time; stale observations are not carried |
| **Dukascopy** M15 bid/ask | Stage 2 and holdout execution only |

**AUD.** The repository's **AUDUSD is never read**: it is defective in 2008-01..09 and 2009-04..09
(H.10 audit). Stage 2 and the holdout synthesise AUDUSD from AUDJPY / USDJPY, with the bid as
AUDJPY bid / USDJPY ask and the ask as AUDJPY ask / USDJPY bid.

**JPY carry.** JPY has no policy rate on 289 of the 376 Stage-1 weeks (zero rates and QE). It is
**excluded** from the carry cross-section on those weeks, which then ranks seven currencies. It is
**never filled**.

In Stage 2 and the holdout, a currency without a policy rate at the decision is excluded from
**every** book that week, because its financing cannot be priced.

**Transformation.**

- Value of each currency in USD (USD = 1), then the log.
- **Relative return** = a currency's return minus the mean of all eight. The common move cancels.
- Only dates on which all seven H.10 rates exist are used. H.10's no-rate days are common to all
  seven.

## Timing

- **Decision:** Friday 17:00 New York.
- **H.10 information:** only rates usable then, i.e. dated up to the business day before; normally
  Thursday's noon fixing.
- **Policy rates:** those public at the decision.
- **Forward week:** from the first H.10 fixing **after** the Friday (normally Monday noon) to the
  first fixing at least 7 days later (at most 10, else the week is skipped).
- **Sampling:** weekly, with non-overlapping forward windows.

## Signals

Each signal is a score per currency, where + means expected to outperform under the literature's
sign.

| Signal | Score |
|---|---|
| carry | the policy rate |
| momentum | the mean of the cross-sectional ranks of the log change over 91 and 364 days, ending at the last fixing ≥ 7 days before the last usable fixing (skip one week) |
| reversal | minus the log change over the last 7 days |
| value | minus the log change over the last 1,820 days (five years; available from 2004) |

**Regime.**

- **Global FX volatility** = the mean absolute daily log change of the seven currencies against USD,
  over the last 20 usable changes (Menkhoff, Sarno, Schmeling & Schrimpf 2012).
- **HIGH** if it is above the median of the previous (up to 156, at least 52) weekly values, else
  **LOW**. Strictly earlier values only.

## Stage 1: the information test (six tests)

**Data.** 2000-01-01 → 2007-03-30, on H.10; the judged forward windows end before 2007-03-30.

**Statistic.** The weekly Spearman IC between the score and the next week's relative returns, over
≥ 6 currencies.

- t = mean IC / (sd / √weeks), on non-overlapping weeks.
- For H5 and H6: the Welch t of mean IC in LOW minus HIGH.

| ID | Test | Weeks available |
|---|---|---|
| RV1-H1-CARRY | carry IC ≠ 0 | 376 |
| RV1-H2-MOMENTUM | momentum IC ≠ 0 | 375 |
| RV1-H3-REVERSAL | one-week reversal IC ≠ 0 | 376 |
| RV1-H4-VALUE | five-year reversal IC ≠ 0 | 168 |
| RV1-H5-CARRY-VOL | carry IC, LOW − HIGH ≠ 0 | 200 LOW / 172 HIGH |
| RV1-H6-MOMENTUM-VOL | momentum IC, LOW − HIGH ≠ 0 | 200 LOW / 172 HIGH |

**Threshold.** |t| ≥ **2.807**, two-sided Bonferroni at 5% over the registry's 4 earlier tests on
these outcomes plus these 6. It is fixed and is not lowered.

**Gate for H1–H4.** All of:

- |t| ≥ 2.807;
- ≥ 100 weeks;
- the same sign of mean IC in both halves of the period;
- leaving out any one currency never flips the sign;
- the currency-neutral book's gross mean has the same sign.

**Gate for H5–H6.** All of:

- |t| ≥ 2.807;
- ≥ 50 weeks in each regime;
- the same sign of the difference in both halves.

**Candidate.** The direction is the sign of the mean IC.

- A regime hypothesis trades its signal only in the regime with the higher mean IC, and is flat in
  the other.

**Reported for each test:**

- weeks, the mean and sd of IC, and t;
- IC by year and by half;
- leave-one-currency-out;
- t without the most favourable week, and the 1%-trimmed mean;
- the book's gross mean, t and Sharpe;
- the contribution by currency;
- the book without its 5 best weeks.

**If nothing passes,** RV-1 has FAILED. There is no Stage 2, and nothing else is tried.

## The book

- **Weights:** centred cross-sectional ranks, scaled to sum to 0 with gross exposure 2 (one unit long,
  one short) over the currencies with a score. With fewer than 6, there is no position.
- **USD** is one of the eight; the book is neutral to the move common to all eight.
- **Sizing:** weights are fractions of a notional. Sizing, limits and execution remain the Risk
  Engine's alone.

## Stage 2: realistic books (passing candidates only)

**Period:** 2008-07-01 → 2017-01-01 (442 weeks).

**Execution.**

- The book rebalances at the H.10 entry fixing time (Monday noon New York), on Dukascopy bid/ask: the
  bar closing then, else the nearest within 60 minutes.
- If any pair's quote is missing, there is no rebalance that week.

**Costs.**

- The measured half-spread on every change of position.
- Slippage of 0.1 pip per fill.
- Commission of 0.7 pip per round trip.
- **Financing:** position × (its policy rate − the USD policy rate) × days / 360, minus 0.5% a year on
  gross exposure.

**Threshold.** The registry's Bonferroni over its tests on 2008-07..2017-01 plus the number of
candidates, computed when trial RV-1-S2 is registered (78 earlier tests → about t ≥ 3.4).

**Controls.**

- **Always-trade:** the candidate rebalanced weekly (primary).
- **Abstention:** hold only when the signal's raw cross-sectional dispersion is ≥ the median of its
  previous (up to 156, ≥ 52) weekly values; otherwise flat. This is compared, not gating.
- **Price-only control, for the carry candidates:** the momentum book under the same gating. The
  candidate's OLS alpha on it must have t ≥ 2.
- **Price signals:** 1,000 random-rank books (seed 20261004). The candidate's gross mean must exceed
  their 95th percentile.

**Robustness checks (all required):**

| Check | Requirement |
|---|---|
| R1 | net mean > 0 in 2008-07..2012-06 and in 2012-07..2016 |
| R2 | ≥ 60% of years (≥ 26 weeks) net positive |
| R3 | no currency carries > 50% of gross P&L, and leaving out any one currency keeps net > 0 |
| R4 | net > 0 without the 5 best weeks |
| R5 | net > 0 with spread, slippage and commission × 2 |
| R6 | net > 0 when every rebalance is one business day later |
| R7 | not significantly negative (t ≤ −2) in either volatility regime |
| R8 | the control test |

**Outcomes:**

- Net mean > 0, t ≥ the Stage-2 threshold, and R1–R8 → **holdout eligible**. Only the best by t; any
  others become PROMISING.
- Net mean > 0, t ≥ 2, and R1–R8 → **PROMISING**.
- Anything else → **REJECTED**.

## Holdout: 2017, sealed

- It is opened once, by trial RV-1-H with the single-use key, and only for that one candidate.
- **Pass:** net mean > 0 with t ≥ 1.645, and net > 0 with costs × 2.

## Classification

| Classification | Requirements |
|---|---|
| **VALIDATED** | the Stage-1 gate, Stage 2 at its threshold with R1–R8, and the holdout |
| **PROMISING** | the Stage-1 gate, and Stage-2 net t ≥ 2 with R1–R8, short of validation |
| **REJECTED** | anything else |

Only a VALIDATED edge may enter the Edge Engine, and then only for paper trading first.

## Power, stated in advance

Stage 1 detects a mean IC of about 0.05; about 0.08 for value. Stage 2 at t ≈ 3.4 over 442 weeks
needs an annual net Sharpe of about 1.2, a demanding bar.

A real but weaker effect would be reported as not detected, not as absent.
