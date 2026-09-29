# R2A — Carry, conditional on the risk regime

Do the positive-carry legs (long AUDJPY, AUDUSD, NZDUSD) earn a positive spot return net of costs while the risk regime is calm, and lose while risk is rising?

Hypotheses (one judged test each), bins fitted on 2007-04-02 → 2008-07-01, judged on 2008-07-11 → 2017-01-01 with t >= 3.2790 and every battery check:

- **R2A-1** (opportunity, human): While VIX closes below 20, buying the high-yield currency against USD or JPY and holding about a month (exit D4) has positive net expectancy from the spot move alone. — `vix_state=low` BUY, exit D4
- **R2A-2** (opportunity, human): When VIX has risen more than 10% over five closes, selling the high-yield currency against USD or JPY and holding a week (exit D3) has positive net expectancy. — `vix_trend=high` SELL, exit D3

- min_trades: n >= 100
- significance: clustered (by week) t >= 3.279
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

Design sha256 `3ccad0432ed9a936bbedc8ea4f893def0eb40fc4dda27a1a207fde5999f81da5`; code sha256 `540e1ebad7ddecc13841998be1a87b7c2d871cfeb1e85aed6a3b98a0eb8db0ad`.

## Stated before the run

- Coverage (feature values only, no outcomes read): VIX < 20 on 62.7% of judged days, VIX rising
  > 10% in 5 closes on 20.7%. Expected trades: about 200 (R2A-1, D4) and 200-270 (R2A-2, D3).
- Power: at the frozen threshold and a per-trade standard deviation near 1.1R, the smallest
  detectable net mean is about 0.25R. A smaller real effect will not be detected.
- Costs: swap is not charged (see the rationale above); r2_report.py also shows every result with
  the standard D1 swap charged, and at lower and higher costs.
