# R2B — US rate-differential changes

Does last month's change in US 10-year yields predict the next month's move of the USD pairs, in the direction the changed differential favours?

Hypotheses (one judged test each), bins fitted on 2007-04-02 → 2008-07-01, judged on 2008-07-11 → 2017-01-01 with t >= 3.2905 and every battery check:

- **R2B-1** (opportunity, human): When last month's US 10y average moved more than 10bp in the direction that favours buying the pair (yields up for USDxxx, down for xxxUSD), buying it and holding about a month (exit D4) has positive net expectancy. — `usd_rate=high` BUY, exit D4
- **R2B-2** (opportunity, human): When last month's US 10y average moved more than 10bp in the direction that favours selling the pair, selling it and holding about a month (exit D4) has positive net expectancy. — `usd_rate=low` SELL, exit D4

- min_trades: n >= 100
- significance: clustered (by week) t >= 3.291
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

Design sha256 `43f1ccd9ef138b5a4cca0fb1c1f0b132f03be42ecadbc5c491bdd6c36e224b7e`; code sha256 `540e1ebad7ddecc13841998be1a87b7c2d871cfeb1e85aed6a3b98a0eb8db0ad`.

## Stated before the run

- Coverage (feature values only): the state favours buying the pair on 31-35% of judged days, selling
  on 31-35%, no move on ~34%, on every USD pair. Expected trades: roughly 300-450 per hypothesis (D4).
- Power: the smallest detectable net mean at the frozen threshold is about 0.2R.
- R2A has already FAILED; R2B is judged on its own, charged to the same registry.
