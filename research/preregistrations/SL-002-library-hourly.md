# SL-002 — Strategy library, H1 forms

Do documented trading principles, in their testable H1 forms, have positive net expectancy on our FX data after costs?

Hypotheses (one judged test each), bins fitted on 2007-06-01 → 2013-07-01, judged on 2013-07-11 → 2017-01-01 with t >= 3.2544 and every battery check:

- **SL-002-01** (opportunity, human): Currencies weaken during their own trading hours: session=mid SELL (exit E3) has positive net expectancy on our FX data — `session=mid` SELL, exit E3

- min_trades: n >= 100
- significance: clustered (by week) t >= 3.254
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

Design sha256 `ceb2ab7a3f303d748918163b1bd1204d8f0a7f6ef28b68ad8e3bf78f7b3ee610`; code sha256 `c0494f9161b07e1a04525a6a85e5c26207fd3dd7ee4be28edab189aaed0852c6`.
