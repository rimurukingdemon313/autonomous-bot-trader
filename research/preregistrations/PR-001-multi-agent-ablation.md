# PR-001 — Does the multi-agent system have an edge, and which parts add value?

**Committed before any run on real data.** The commit timestamp is the
evidence. Results are appended below the line "RESULTS" and judged by the
rules written here, unchanged.

## Question

On bid/ask data it has never been tuned on, does the full system (five
agents, historical-analogue memory, evidence synthesis, evidence-based
lessons, deterministic risk engine, execution) show positive expectancy
after costs, out of sample? And which components add measurable value?

## Data

- Dukascopy tick data (bid and ask) aggregated to M15, resampled to H1 on
  complete bars only (`data/manifest.json` records every source commit).
- 12 instruments: EURUSD GBPUSD USDJPY AUDUSD USDCAD USDCHF NZDUSD EURGBP
  EURJPY GBPJPY EURCHF AUDJPY. XAUUSD is excluded: it starts in 2011, has
  no warm-up history, and would enter the memory late.
- Research period: 2007-01-01 → 2017-01-01. The final holdout (from
  2017-01-01) stays sealed; the loader cannot read it without a key.

## Timeline (walk-forward, point-in-time)

| Segment | Dates | Role |
|---|---|---|
| Warm-up | 2007-01-01 → 2010-01-01 | fit: pattern-memory scaler, first regime model; memory seeded from labels |
| Judged | 2010-01-01 → 2017-01-01 | judge: every decision, trade and lesson |

- The regime model is refit at each year start on every row decided before
  that year minus a 5-day embargo (expanding window).
- Pattern memory grows through the judged period, but a past situation is
  evidence at time T only if its outcome had resolved by T.
- Lessons are validated only on outcomes after their discovery.

## Fixed parameters — none tuned on this data

Decision cadence every 4 closed H1 bars per instrument · action templates
T1 (stop 1.0 ATR, target 1.5 ATR, 24 bars) and T2 (1.5 / 3.0 ATR, 48 bars)
· analogues k = 100, lower bound = mean − 1.28 × SE · base margin 0 R ·
default MAJOR-objection penalty 0.03 R · risk 0.5 % per trade, daily loss
2 %, max drawdown 8 % (halt), 3 open positions, 2 per currency · costs:
measured spread, slippage 0.1 pip per fill, commission 0.7 pip round trip,
swap 0.05 × ATR24(H1) per New York close — the last three are declared
approximations · start balance $20,000.

## Variants (ablation)

| Id | What it is |
|---|---|
| A | Agents, no memory: first family setup (T1) with no blocking or major objection |
| B | Agents + analogue memory + evidence synthesis; learning OFF (no lessons, default penalties) |
| C | B + learning ON (lessons, measured objection penalties) — the full system as it can be tested historically |
| R | Random direction, T1, trade probability 0.03 per decision, seed 7 — same risk engine |

The language-model layer is NOT part of any historical variant: its
judgement cannot be validated on history it may remember
(MODEL_CONTRACT.md §7). It is evaluated only forward, in paper trading.

## Hypotheses and pass rules — 4 verdicts

The registry holds 16 earlier verdicts on this universe. With these 4, a
two-sided Bonferroni threshold over 20 tests is **|t| > 3.02**.

**H1 (primary). C has an edge.** PASSES only if ALL hold on the judged
period:
1. mean R per trade > 0 and t > 3.02;
2. mean R of C exceeds mean R of R (Welch t > 2.0);
3. mean R > 0 in at least 4 of the 7 calendar years;
4. at least 200 trades;
5. maximum realised drawdown < 25 %.

**H2. Learning adds value:** mean R of C − B > 0, Welch t > 2.24.
**H3. Memory adds value:** mean R of B − A > 0, Welch t > 2.24.
**H4. The agents beat random:** mean R of A − R > 0, Welch t > 2.24.
(2.24 = Holm's most lenient step for the three secondary comparisons is
not used; the strictest, Bonferroni over three, is used for all.)

## What follows, fixed now

- **H1 FAILS** → no robustness battery, no final holdout: the holdout stays
  sealed for a future candidate. The system is reported as having no
  demonstrated edge, and remains in RESEARCH status.
- **H1 PASSES** → robustness battery (spread ×1.5 and ×2, slippage ×2,
  one-bar delay, leave-one-instrument-out, per-year). If it survives, a
  separate pre-registration for the single final-holdout test is written
  and committed before the holdout is opened.
- Every variant's full metrics are reported whatever the verdicts:
  expectancy, profit factor, drawdown, Sharpe/Sortino where meaningful,
  win rate, average win/loss, consecutive losses, trades, exposure, and
  breakdowns by year, instrument, regime and setup family.

## RESULTS

*(to be appended after the run, judged by the rules above)*
