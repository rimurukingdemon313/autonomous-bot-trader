# Round 2 research plan

Round 1 searched price-only transformations and found nothing that survives costs:

- 16 judged hypotheses and 2,700 screened cells;
- `docs/EDGE_DISCOVERY_AUDIT.md`.

Round 2 searches a different space: **information the bars do not contain**, used in
**conditional** hypotheses (regime → condition → direction), each preregistered and judged
once. The plan was written before any Round 2 outcome was read.

## Principles

1. **New information before new transformations.** Every family uses at least one series
   Round 1 did not have ([ROUND2_DATA_AUDIT.md](ROUND2_DATA_AUDIT.md)).
2. **Direction first.** Round 1's losses were mostly wrong direction and noise, not exits.
   Round 2 changes no exit. Each family uses a declared exit from the existing menu, matched
   to the signal's horizon:
   - D4: 20 days, for monthly information;
   - D3: 5 days, for fast information.
3. **Fixed states, not fitted thresholds.** Every condition is a categorical state at an
   economically interpretable level:
   - VIX 20 and 30;
   - a 10bp change in US yields;
   - a 5% move in oil;
   - the sign of the trend.

   Nothing is estimated from outcomes, so a condition cannot have been tuned.
4. **Multiple testing counts everything.** Every Round 2 test is charged to the same registry
   as Round 1, because it judges the same FX outcomes. The first family must clear t ≥ 3.29;
   the bar rises with each family.
5. **A longer judged period.** 2008-07-11 → 2017-01-01: 8.5 years including the 2008 crisis,
   the 2011 euro crisis, the 2014–15 dollar rally and the 2015 China shock. Because every
   judged period overlaps the 46 prior tests, the threshold is the same, and the longer
   period gives about 2.4 times the trades. The fit segment (2007-04 → 2008-07) supplies only
   the battery's regime medians. The holdout stays sealed.
6. **Stop after each family and evaluate.** When a family fails, its evidence is recorded and
   the next family starts. No failed hypothesis is re-run with other levels.

## Families, in priority order

| # | Family | New information | Hypotheses | Exit | Prior, stated in advance |
|---|---|---|---|---|---|
| R2A | Carry, conditional on the risk regime | VIX; the documented sign of policy-rate differentials | R2A-1: long AUDJPY, AUDUSD, NZDUSD while VIX < 20. R2A-2: short them after VIX rises more than 10% in 5 days | D4 / D3 | moderate for R2A-1. Carry is documented to pay in calm markets, but only its spot component is measurable here |
| R2B | US rate-differential changes | Fed H.15 10y | R2B-1: buy the pair whose USD leg last month's yield change favours. R2B-2: sell the disfavoured one. 7 USD pairs | D4 | low to moderate (the forward-premium anomaly) |
| R2C | Cross-asset: oil → CAD | EIA Brent | R2C-1 / R2C-2: USDCAD after a Brent move of more than 5% in 20 days | D3 | **low.** Ferraro, Rogoff & Rossi (2015) find the link contemporaneous, not lagged |
| R2D | Regime-conditioned momentum | VIX | R2D-1 / R2D-2: the time-series trend sign, only while VIX < 20, 12 pairs | D4 | moderate. Daniel & Moskowitz (2016): momentum crashes in panic states |
| — | Session and liquidity | — | **none new.** DP-001 already crossed the session state with 10 triggers (0 discoveries), and SL-002 judged the local-hours effect (−0.105R, n 8,901). On H1 the costs, 0.09–0.21R, exceed any gross effect found. A new session test would spend budget where Round 1 measured costs as the binding constraint | — | — |
| — | Synthesis (e.g. carry + momentum + calm) | — | **only if** a component family produces a PROMISING result. Combining failed components multiplies the tests without a reason to expect an edge | — | — |

That is 8 preregistered tests in 4 families. The budget stops there: at t ≥ 3.3 on about 8.5
years, a ninth test on these outcomes buys little power.

## What every candidate reports

`scripts/r2_report.py` reports:

- P(direction correct);
- gross R, with the costs split into spread, commission, slippage and swap;
- net R at lower, normal and higher costs;
- MFE, MAE and the worst MAE;
- holding time;
- the result by regime at entry, by instrument and by year.

## Promotion levels

RESEARCH → HYPOTHESIS → TESTING → PROMISING → VALIDATED → DEGRADED → RETIRED, or REJECTED.
The rules are in `aitrader/research/discovery/edges.py`.

- **PROMISING** means a judged, out-of-sample result that is positive with t ≥ 2, survives the
  cost stress and beats random entries, but misses the registry's bar. Its next step is a fresh
  test on new data, never a trade.
- **VALIDATED** requires every check. If nothing qualifies, VALIDATED = 0.
