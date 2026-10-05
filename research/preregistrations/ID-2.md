# ID-2: an opportunity engine for active intraday trading (preregistration)

**Written, frozen and committed before any outcome of this design was computed.** The computations
on real data before writing are listed in "What was computed before the freeze" below.

| | |
|---|---|
| Frozen spec | `research/specs/ID-2.json` |
| Spec sha256 | `4b3aa7ef0fac23b362dc10aac0f669d99d6e8ace489cdbaeec22dcc7fe32fc64` |
| Code | `aitrader/research/discovery/opportunity.py` (opp-1.0.0), `scripts/id2.py`, with `intraday.py` and `scripts/id1.py` (all hashed in the spec) |
| Data | The M5 bid/ask bars ID-1 built, 2009–2016, 8 instruments (branch `id-data`) |
| Tests registered | 30 (18 model configurations + 12 deterministic rule configurations). Controls are not tests |
| Validation threshold | t ≥ **3.5524** = max(3.0, the registry's Bonferroni for fx-majors 2014–2016 with these 30 tests) |
| Untouched test | The fx-majors holdout, 2017-01 → 2022-07: never opened, M5 bars not built |

## Why this is not a repeat of failed research

| Earlier work | What it tested | What ID-2 changes |
|---|---|---|
| ID-1 (FAILED) | 16 single M5 rules, each alone, at M5-ATR stops | Every bar is a candidate. One model weighs **all** families together, so it can find a context in which a trigger works, which a single rule cannot. Stops and exits scale up to H1 ATR, where cost per R is lower. The risk engine's account limits apply as a portfolio |
| DP-001 / SL-002 (REJECTED) | ridge, logistic, k-NN and depth-1 stumps on H1/M15 bars, fixed horizons | M5 decisions with bid/ask fills and measured costs. A new **depth-3 tree** family that can express interactions. Memory features. A net-R target that includes cost |
| PR-001 | Multi-agent filter over random entries: +0.087R over random, still negative | The estimate is the selector, not a filter on random entries, and it is judged against simple rules as well as random |
| TOM, RC, DIV, carry, COT, flow | Daily and lower-frequency effects | **Not reopened.** ID-2 is intraday only and holds no position overnight |

## What the engine does

```
scanner: every M5 bar opening 07:00-19:55 UTC, Monday-Friday, BOTH sides
  -> 45 causal features + 5 per-scale inputs + instrument identity (58 columns)
  -> walk-forward estimate of the standard trade's NET R
  -> take candidates whose estimate > tau, highest estimate first
  -> the production risk engine's entry checks and account limits
  -> EXECUTE or NO TRADE
```

**Trade frequency is an output.** The scanner proposes roughly 300 candidates an hour across the
panel; the estimate decides how many to take, from none upwards. Nothing forces a trade.

### The standard trade (`opportunity.label`, identical to `intraday.simulate`)

**Entry:** decided at an M5 bar's close; filled at the next M5 open on the correct side of the
quote (ask for a BUY, bid for a SELL), plus 0.1 pip slippage.

**Stop and target:**

- stop 1.5 × ATR_S from the signal close;
- target 2R;
- the stop is checked before the target in every bar, and a gap fills at the open.

**Exit scales:**

| Scale | ATR of | Maximum hold |
|---|---|---|
| S5 | 5-minute bars | 48 bars, 4 h |
| S15 | completed 15-minute bars | 96 bars, 8 h |
| S60 | completed 60-minute bars | 144 bars, 12 h |

**Always flat by 20:55 UTC**, and before any gap of more than an hour. There is no overnight
exposure, so no financing (it is still computed if a position ever crosses 21:00).

**Agreement with the simulator:** a test requires every field (entry, exit, risk, gross, spread,
slippage, commission, financing, R, reason) to match `intraday.simulate` to 1e-12, at normal and
stressed costs, on all three scales.

**Costs:** as ID-1, and provisional against TradeLocker's real spreads.

- measured bid/ask spread on every fill;
- 0.7 pip commission per round trip;
- 0.1 pip slippage per market fill;
- the production risk engine's entry checks: stop ≥ 3 spreads, spread ≤ 25% of the stop,
  round trip ≤ 25% of the stop, reward:risk ≥ 1.2.

### Features (`FEATURES`, `SCALE_FEATURES`; oriented to the side)

- **"Signed"** features flip for a SELL.
- **"Pair"** features swap, so that a BUY's distance to the high is a SELL's distance to the low.
- No feature has special status, and no feature was chosen by its outcome.

| Group | Features |
|---|---|
| momentum | 1/3/12/48-bar move in ATR; 12-bar move z |
| reversion | distance from EMA(20) and EMA(100) in ATR |
| breakout | position in the 48-bar range; close beyond the previous 20 bars; generic failed breakout in the last 6 bars; room to the 288-bar high / low |
| structure | swing trend (HH+HL / LH+LL, confirmed fractals); break of structure and CHoCH in the last 6 bars; distance to the last confirmed swing high / low |
| liquidity (SMC) | previous-day, Asian-range and equal-level sweeps, BOS+FVG and order-block events in the last 6 bars (ID-1's detectors); distance to the previous day's high / low |
| volatility | ATR rank (week); Bollinger-width rank (1,000 bars); ATR(M5)/ATR(H1); the bar's range and body |
| cost | round-trip cost / the scale's stop (per scale) |
| session | hour (sin/cos); weekday; first 30 minutes of London / New York |
| mtf | H1 and H4 EMA(50) slope of completed bars; previous day's return and position in its range; 1-hour and 4-hour move in H1 ATR |
| cross | USD-index 12-bar z, signed for the instrument; own move minus the USD-implied move; 288-bar correlation with the USD index; AUDJPY 12-bar z (risk on/off) |
| volume | tick count / its 288-bar mean; one-bar move × that ratio (tick counts are quote updates, not traded volume) |
| memory | mean net R of the last 50 resolved candidates of this instrument on this side, and on the other side; of the last 60 in the same UTC hour. Only trades whose exit bar is **before** the decision bar count |
| identity | side; instrument (one-hot) |

**Causality** is tested by truncation: every feature, memory and cost input at a bar is identical
when all instruments' later bars are deleted.

### Models (two declared families, fixed hyper-parameters, no search)

| Family | Definition |
|---|---|
| ridge | α = 10 on standardised inputs; missing values take the training median |
| trees | gradient-boosted regression trees: depth 3, 150 rounds, shrinkage 0.1, 32 quantile bins, ≥ 1,000 rows per leaf; deterministic |

**Target:** the standard trade's realised **net** R at the scale.

**Training rows:** tradable candidates on a 15-minute grid. Overlapping labels are not new
evidence.

**Walk-forward:** refitted every January, using only trades that **exited** at least a day before
the fold. The development folds are 2011, 2012 and 2013, trained on 2009–2010, 2009–2011 and
2009–2012. A test checks the exit rule.

### Selection and the account

**Eligible:** tradable candidates whose estimate exceeds τ. Candidates at the same moment are
taken in descending estimate.

**Account limits** (the production risk engine's own, `RiskLimits`):

- at most 3 open positions;
- one per instrument;
- at most 2 sharing a currency;
- no new entry on a trading day whose closed trades have already lost 4R (2% at 0.5% risk).

A test checks each limit.

**Sizing:** none here. R is reported at 0.25%, 0.5% and 1% risk, without compounding. The risk
engine stays the only sizing authority.

## The 30 tests and the controls

| ID | What |
|---|---|
| `M-{ridge,trees}-{S5,S15,S60}-tau{0.00,0.05,0.10}` (18) | the engine at threshold τ on the estimated net R |
| `R-MOM-{scale}` | simple momentum: 12-bar move z ≥ 2.0, trade with it (neighbours 1.75 / 2.25) |
| `R-MR-{scale}` | simple mean reversion: close ≥ 2.5 ATR from EMA(20), fade it (2.25 / 2.75) |
| `R-BRK-{scale}` | simple breakout: first close beyond the previous 20 bars' high/low, trade it (15 / 25) |
| `R-SWEEP-{scale}` | liquidity sweep (A1/A2/A3 events), fade it (penetration 0.10 ATR; 0.05 / 0.15) |
| control `RANDOM-{scale}` | one random tradable candidate per instrument-day, random side, 3 seeds |
| matched random, for every test | the same number of candidates in the selection's own UTC hours and period, random side, through the same portfolio, 3 seeds |

**Every rule uses the same template and portfolio as the engine.** The comparison "does the model
beat simple rules" is therefore like for like.

## Periods and gates

| Stage | Period | Role |
|---|---|---|
| Development | data 2009–2013; **judged on 2011–2013**, each year predicted out of sample | `select`: every test and control |
| Validation | 2014–2016, models refitted each January on everything resolved before it | `judge`: **the single best promoted test only** |
| Untouched test | 2017-01 → 2022-07 | holdout: validation passers only, once |

**Promotion (development 2011–2013, all required):**

1. ≥ 300 trades;
2. net R > 0;
3. t ≥ 2.0 on daily net R (every weekday counted);
4. profit factor ≥ 1.10;
5. net R > 0 at costs × 1.25;
6. beats its matched random by Welch t ≥ 2.0;
7. net R > 0 on ≥ 60% of the instruments with ≥ 30 trades.

Of the tests that pass, **only the one with the highest t** goes to validation.

**Validation (all required):**

1. t ≥ 3.5524;
2. net R > 0;
3. profit factor ≥ 1.20;
4. costs × 1.5 net R > 0;
5. slippage 0.3 pip per fill net R > 0;
6. ≥ 60% of instruments positive;
7. ≥ 60% of rolling 3-month windows profitable;
8. beats matched random (Welch t ≥ 2.0);
9. **both declared neighbours** net R > 0 (τ ± 0.05 for the engine; the parameter pair for a rule).

**Holdout:** t ≥ z(1 − 0.05/k), net R > 0, profit factor ≥ 1.1, costs × 1.5 > 0, and ≥ 55% of
3-month windows profitable. The holdout's M5 bars are built only if something passes validation.

**Verdicts:**

| Verdict | When |
|---|---|
| PRODUCTION CANDIDATE | passed the holdout and the executability checks; paper/demo first, never live |
| STRONG RESEARCH CANDIDATE | passed validation; holdout not yet run, or failed narrowly |
| PROMISING BUT NEEDS MORE DATA | promoted, and validation net R > 0 with t ≥ 2.0, but below 3.55 |
| NO EDGE | not promoted, or validation net R ≤ 0 |
| INVALID / DATA PROBLEM | the data or the pipeline cannot support a judgement |

## Reported for every test

- **Trades:** count, trades a month, holding time (mean, median, p90), win rate, average win and
  loss.
- **Expectancy:** gross R and its spread / commission / slippage / financing parts, cost per
  trade, net R, t, profit factor.
- **Account:** net return, annual return, Sharpe, a per-trade Sortino, maximum drawdown, at 0.25%,
  0.5% and 1%.
- **Windows:** weekly (share profitable, median, worst, best); rolling 1-, 3- and 6-month windows
  (share profitable, median, worst, best, drawdown inside).
- **Breakdowns:**
  - by instrument, year, session and direction (BUY / SELL);
  - by regime: volatility; trend vs range;
  - concentration: the share of profit from the best 10% of trades;
  - simultaneous positions.

## Descriptive analyses (declared now; not tests, never used to choose anything for validation)

On the development years 2011–2013, out of sample:

1. **Does the estimate rank opportunities at all?** Realised net R by predicted decile, the
   Spearman rank correlation, and the share of candidates predicted above 0 and above 0.05. This
   is reported for every family and scale, whether or not any selection trades.
2. **Which information matters (ablations):**
   - ridge, every scale, each of the 13 feature groups dropped, and each used alone;
   - trees, on the scale where the full trees model ranks best, each group dropped.
   - This answers whether liquidity/SMC, structure, memory, cross-market or any other family
     adds information beyond the rest.
3. **Model vs simple rules vs random:** the engine's selections against the rule tests and the
   controls at the same scale.

## What ID-2 does not test (declared)

- **M1.** The data is M5. M1 stops would be about half as wide, so costs per R would roughly
  double from M5's ≈ 0.17R. The cost arithmetic rules it out before any test.
- **A language model.** It cannot be backtested honestly: its training data contains the outcomes.
  The engine emits a structured `Opportunity` record that a later AI layer can read and veto, never
  change.
- **Exit management beyond the template** (break-even, trailing, partials, model-driven exits).
  These are left for a candidate that first shows a positive entry edge.
- **Index CFDs.** No intraday bid/ask source was reachable (ID-1).

## What was computed before the freeze

All of this was on development data. No model was fitted to real data and no selection was
evaluated.

- **A correctness check of the labeller** against `intraday.simulate` on EURUSD 2011-01 → 2011-03
  (900 sampled trades, all identical). It printed the mean net R of **all** EURUSD candidates in
  that quarter: S5 −0.13, S15 −0.096, S60 −0.055. That is an unconditional (random-entry) figure
  for one instrument and one quarter, and it selects nothing.
- **A feasibility run on the 2009–2013 panel:** 3.05M candidate rows per scale. Rows refused by the
  risk engine's entry checks: S5 1.23M, S15 232k, S60 9.9k. Run time and memory were also
  measured, including one 10-round tree fit timed without predicting anything.

## What would follow

- **A passer** would become a paper/demo candidate behind the unchanged risk engine, demo guard and
  execution guards. Nothing is promoted automatically, and nothing here touches live trading.
- **A failure of everything** would be reported as NO EDGE, with the ranking and ablation
  evidence that shows *why*: whether the model found no information at all, or found information
  smaller than the costs.
