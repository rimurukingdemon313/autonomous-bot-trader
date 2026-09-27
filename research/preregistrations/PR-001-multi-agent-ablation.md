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

## Amendment 1 — before any run on the judged period

Written after a timing run on warm-up data only (GBPUSD, EURGBP, USDCAD,
AUDUSD, 2008-07 → 2009-07; the "fit" segment above) and before any
decision on 2010-2016 was computed.

**What the timing run showed.** The 8 % drawdown halt fired after 102
trades; the next 53 approved-by-everything-else candidates were refused
with `halted: human action required`. In operation a person reviews and
clears a halt. In a replay no one does, so the first 8 % drawdown ends the
experiment for good, and every later year contributes no trades.

**The primary run is unchanged.** The verdicts H1-H4 are judged on the
run with the halt, exactly as written above. A system that halts in its
first year has not shown an edge; that is a correct reading of H1.

**Added: an exploratory arm, no verdict.** The same four variants are run
again with the drawdown halt disabled (`max_drawdown_pct = 100`), every
other parameter identical, so the per-trade expectancy of each variant is
measured over the whole judged period rather than until the first halt.

- It produces **no verdict** and cannot rescue H1-H4: nothing in it passes
  or fails.
- It is registered separately (`PR-001x-nohalt-exploratory`, tests = 0,
  role `select`), so its exposure of 2010-2016 is on the record.
- Any hypothesis it suggests must be pre-registered anew and judged on
  data it did not see.

## RESULTS

Run 2026-09-26/27. Primary arm at commit `1ec33b8`; the exploratory arm
at a later commit. Before the primary's halt, both arms produced
**identical** trades in every variant (24 / 60 / 46 / 50), so the
changes in between did not alter backtest decisions. Judged by
`scripts/judge_pr001.py`, committed before any result existed. Full
numbers: `research/results/PR-001-judgement.json` and
`PR-001-summary.json`. Every hash chain verified.

### Verdicts (primary arm, as pre-registered)

| Hypothesis | Verdict | Numbers |
|---|---|---|
| **H1** C has an edge | **FAIL** | C: 46 trades, mean −0.308 R, t −1.79. Fails conditions 1-4 (sign and t, beats random, 0 of 7 positive years, fewer than 200 trades); drawdown −7.6 % |
| H2 learning adds value (C − B) | **FAIL** | +0.006 R, Welch t 0.03 |
| H3 memory adds value (B − A) | **FAIL** | +0.103 R, Welch t 0.38 |
| H4 agents beat random (A − R) | **FAIL** | −0.071 R, Welch t −0.26 |

Every variant stopped trading in January-February 2010:

- **B, C and R** hit the 8 % drawdown halt. The risk engine refused
  3,652 / 4,356 / 3,699 later approvals. This is the behaviour Amendment 1
  anticipated.
- **A** was never halted. It locked itself out. The Risk agent raises a
  MAJOR `DRAWDOWN_STATE` objection at 5 % drawdown, and A, as specified,
  trades only when there is no MAJOR objection. A reached about 6 %
  drawdown after 24 trades, so it never traded again, so equity never
  recovered, so the objection never cleared. A-nohalt is identical,
  24 trades, which confirms it was not the halt. **Finding:** a rule
  that stops on adverse account state, with no path back, is an
  absorbing state. B and C only raise their bar by a penalty and are not
  affected.

**Following the rules fixed above: H1 failed, so there is no robustness
battery and no final holdout. The holdout stays sealed, and the system
remains in RESEARCH with no demonstrated edge.**

### Exploratory arm (Amendment 1): no verdict

The same variants with the drawdown halt disabled, 2010-2016:

| Variant | Trades | Mean R | t | Win | PF (R) | Return | Max DD | Sharpe (daily, ann.) |
|---|---|---|---|---|---|---|---|---|
| A agents, no memory | 24 | −0.417 | −1.86 | 25 % | 0.47 | −4.2 % | −6.0 % | n/a |
| B + memory | 2,577 | −0.053 | −1.99 | 35.7 % | 0.92 | −47.4 % | −54.4 % | −0.69 |
| **C full system** | **2,928** | **−0.072** | **−2.90** | 35.1 % | 0.89 | **−53.5 %** | −58.5 % | −0.89 |
| R random | 3,143 | −0.159 | −7.38 | 36.5 % | 0.76 | −87.1 % | −87.3 % | −1.87 |

Comparisons, reported without verdict:

- C − R: +0.087 R, Welch t 2.65.
- C − B: −0.019 R, Welch t −0.53.
- B − A: +0.36 R, Welch t 1.61.
- A − R: −0.26 R, Welch t −1.14.

What this says, and no more:

- **The full system loses money after costs.** Its mean is significantly
  **negative** (t −2.9). Its year by year means: 2010 −0.09, 2011 −0.21,
  2012 −0.10, 2013 +0.03, 2014 −0.05, 2015 +0.01, 2016 −0.04. Two
  positive years out of seven.
- **The analogue memory filters.** It lost about half as much per trade
  as random direction under the same risk engine and costs. It does not
  turn a loss into a gain.
- **Learning did not help.** Lessons were created and validated (26
  validated, 17 rejected, 6 retired in C), but C did no better than B.
- **Regimes are not informative about outcomes here.** C is negative in
  every regime, least in TRANSITION (−0.03 R). Random is negative in
  every regime by about the same amount, which is what costs alone
  produce.
- By instrument: only GBPJPY (+0.056) and EURJPY (+0.010) were positive
  for C, over about 250 trades each. That is a selection-after-the-fact
  observation, not a finding.
- The recorded loss causes are mostly NORMAL_VARIANCE (877) and
  REGIME_SHIFT (539).

This agrees with the archive's thirteen families: on these instruments,
at this horizon, after realistic costs, nothing tested so far has an
edge. Any idea suggested by the exploratory arm is a new hypothesis. It
needs its own pre-registration and must be judged on data this arm has
not seen, which leaves the sealed holdout and forward (paper) data only.
