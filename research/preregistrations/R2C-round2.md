# R2C — Cross-asset: oil and the Canadian dollar

Does a 20-day move in Brent of more than 5% predict the next week's move of USDCAD, in the direction oil favours?

Hypotheses (one judged test each), bins fitted on 2007-04-02 → 2008-07-01, judged on 2008-07-11 → 2017-01-01 with t >= 3.3015 and every battery check:

- **R2C-1** (opportunity, human): After Brent fell more than 5% over 20 observations, buying USDCAD and holding a week (exit D3) has positive net expectancy. — `oil_pull=high` BUY, exit D3
- **R2C-2** (opportunity, human): After Brent rose more than 5% over 20 observations, selling USDCAD and holding a week (exit D3) has positive net expectancy. — `oil_pull=low` SELL, exit D3

- min_trades: n >= 100
- significance: clustered (by week) t >= 3.302
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

Design sha256 `318d548bffd345a6fd47a01835af39b166656467d7edf8969a50df6907656c6f`; code sha256 `540e1ebad7ddecc13841998be1a87b7c2d871cfeb1e85aed6a3b98a0eb8db0ad`.

## Stated before the run

- Coverage (feature values only): oil fell > 5% over 20 observations (favours buying USDCAD) on 26.6%
  of judged days, rose > 5% on 30.5%. One instrument, exit D3: roughly 100-200 trades per hypothesis;
  min_trades (100) may fail on its own.
- Prior: LOW. Ferraro, Rogoff & Rossi (2015) document a contemporaneous, not a lagged, oil-CAD link.
- Power: the smallest detectable net mean at the frozen threshold is about 0.3R.
