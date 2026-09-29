# R2D — Regime-conditioned time-series momentum

Does time-series momentum, rejected unconditionally in CP-001, have positive net expectancy when restricted in advance to calm risk regimes?

Hypotheses (one judged test each), bins fitted on 2007-04-02 → 2008-07-01, judged on 2008-07-11 → 2017-01-01 with t >= 3.3121 and every battery check:

- **R2D-1** (opportunity, human): While VIX is below 20, buying a pair whose 120-day move is up and holding about a month (exit D4) has positive net expectancy. — `trend_sign=high&vix_state=low` BUY, exit D4
- **R2D-2** (opportunity, human): While VIX is below 20, selling a pair whose 120-day move is down and holding about a month (exit D4) has positive net expectancy. — `trend_sign=low&vix_state=low` SELL, exit D4

- min_trades: n >= 100
- significance: clustered (by week) t >= 3.312
- beats_random: Welch t vs random entries >= 2.0 (20 draws)
- permutation: circular-shift p < 0.05 (200 shifts)
- costs_stress: mean R > 0 with spread x1.5, slippage x2, commission and swap x1.5
- delay_stress: mean R > 0 with entry one bar late
- perturbation: mean R > 0 with tercile edges moved by -0.05 and +0.05 quantile
- years: >= 60% of years with >= 20 trades positive (>= 2 years)
- instruments: >= 60% of instruments with >= 20 trades positive (>= 2 instruments)
- leave_one_out: mean R > 0 with any one instrument removed
- regimes: no regime cell (er120 x vol_ratio, discovery medians) with t <= -2.0; >= 2 cells with >= 20 trades positive
- outliers: top 5% of trades carry < 50% of total R

Design sha256 `1daec1d8de9c7099c183bcde22ad69e84a202b5537faecb9c8e7ff94227e50e2`; code sha256 `540e1ebad7ddecc13841998be1a87b7c2d871cfeb1e85aed6a3b98a0eb8db0ad`.

## Stated before the run

- Coverage (feature values only, EURUSD): 120-day trend up while VIX < 20 on 29.3% of judged days, down
  while VIX < 20 on 33.5%. Twelve pairs, exit D4: roughly 500-700 trades per hypothesis.
- Power: the smallest detectable net mean at the frozen threshold is about 0.15R.
- This is a CONDITIONAL hypothesis about why CP-001's unconditional momentum failed (crash states),
  stated from Daniel & Moskowitz (2016) before any judged data was read; CP-001 used r120 terciles on
  2013-07 -> 2017-01, this uses the sign of the move while VIX < 20 on 2008-07 -> 2017-01.
