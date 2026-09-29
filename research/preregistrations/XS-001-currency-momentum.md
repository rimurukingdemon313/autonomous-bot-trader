# XS-001 — Published cross-sectional currency momentum, judged after its publication

Does buying the currencies that were strongest against the dollar over the last 24 days, and selling the weakest, held about a month, have positive net expectancy on the seven USD pairs from 2013-07 to 2017-01, all costs charged?

Hypotheses (one judged test each), bins fitted on 2007-06-01 → 2013-07-01, judged on 2013-07-11 → 2017-01-01 with t >= 3.2670 and every battery check:

- **XS-001-L** (opportunity, human): When the pair's currency is among the strongest against the dollar over 24 days (relative to the other six) at a daily close, a BUY of the pair held about a month (exit D4) has positive net expectancy. — `xs_mom=high` BUY, exit D4
- **XS-001-S** (opportunity, human): When the pair's currency is among the weakest against the dollar over 24 days (relative to the other six) at a daily close, a SELL of the pair held about a month (exit D4) has positive net expectancy. — `xs_mom=low` SELL, exit D4

- min_trades: n >= 100
- significance: clustered (by week) t >= 3.267
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

Design sha256 `b77be7b743f2be05a532939f48be12d3dab33f9d1eb669313f682dea3c87b8fe`; code sha256 `6da0e48627ff237cc8c169419d0735bb41525e43e541b7d8f3d997d1bf597651`.
