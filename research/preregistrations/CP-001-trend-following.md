# CP-001 — Published FX trend following, judged after its publication

Do the published time-series momentum and moving-average trend rules have positive net expectancy on 12 FX pairs from 2013-07 to 2017-01, one month holds, all costs charged?

Hypotheses (one judged test each), bins fitted on 2007-06-01 → 2013-07-01, judged on 2013-07-11 → 2017-01-01 with t >= 3.1804 and every battery check:

- **CP-001-T1** (opportunity, human): When the 120-day move is in its top tercile (a strong uptrend) at a daily close, a BUY held about a month (exit D4) has positive net expectancy. — `r120=high` BUY, exit D4
- **CP-001-T2** (opportunity, human): When the 120-day move is in its bottom tercile (a strong downtrend) at a daily close, a SELL held about a month (exit D4) has positive net expectancy. — `r120=low` SELL, exit D4
- **CP-001-T3** (opportunity, human): When the 48-day average is well above the 240-day average at a daily close, a BUY held about a month (exit D4) has positive net expectancy. — `ma_slope=high` BUY, exit D4
- **CP-001-T4** (opportunity, human): When the 48-day average is well below the 240-day average at a daily close, a SELL held about a month (exit D4) has positive net expectancy. — `ma_slope=low` SELL, exit D4

- min_trades: n >= 100
- significance: clustered (by week) t >= 3.180
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

Design sha256 `bed58d9cc7bcb7d5d1f18989692437fd36e40f6cf82cf2be8c025c53a92fbf14`; code sha256 `8f28050353eb38ed2c318269237557b767a5bd1edb04a2c9299d44e054a4716e`.
