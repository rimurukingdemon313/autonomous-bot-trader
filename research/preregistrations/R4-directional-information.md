# R4 — Directional information from outside the FX pair

Does gold, a VIX spike or US inflation acceleration predict an FX pair's direction BEYOND its own recent price, after costs, out of sample?

Hypotheses (one judged test each), bins fitted on 2007-04-02 → 2008-07-01, judged on 2008-07-11 → 2017-01-01 with t >= 3.3720 and every battery check:

- **R4-XA-GOLD-A** (opportunity, human): After gold rose >= 2% over 5 days while the AUD pair FELL, buying the AUD pair and holding a week (D3) has positive net expectancy. — `gold_pull=high&own5=low` BUY, exit D3
- **R4-XA-GOLD-B** (opportunity, human): After gold fell >= 2% over 5 days while the AUD pair ROSE, selling it and holding a week (D3) has positive net expectancy. — `gold_pull=low&own5=high` SELL, exit D3
- **R4-XA-VIX-A** (opportunity, human): After VIX jumped >= 20% over 5 closes while a JPY- or CHF-quoted pair still ROSE, selling it (buying the safe haven) and holding a week (D3) has positive net expectancy. — `vix_jump=high&own5=high` SELL, exit D3
- **R4-MACRO-CPI-A** (opportunity, human): When the latest US CPI shows 12-month inflation >= 0.3pp higher than 3 months earlier, buying the pair whose USD leg that favours (and when it decelerates, the pair that sells USD) and holding about a month (D4) has positive net expectancy. — `usd_infl=high` BUY, exit D4
- **R4-MACRO-CPI-B** (opportunity, human): When the US inflation change disfavours the pair's USD leg by >= 0.3pp, selling the pair and holding about a month (D4) has positive net expectancy. — `usd_infl=low` SELL, exit D4

- min_trades: n >= 100
- significance: clustered (by week) t >= 3.372
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

Design sha256 `c29fa3793878bd8380fd7b7fe128452cc96063f506a0fe6a86bc8d61ad9040ca`; code sha256 `2d4abc31594ce71b5b16eb89af54d6b5f16b960f9fa07f3379028a91ab7fdcb9`.

## Stated before the run (feature values only; no outcome read)

- Share of judged days each condition holds: GOLD-A 4.4-5.7% (AUD pairs; gold exists from 2011-05),
  GOLD-B 3.2-5.6%, VIX-A 1.6-4.8% (5 pairs), CPI-A/B 31-36% (7 USD pairs). Expected trades: ~110-140
  (gold, near the 100-trade minimum), ~150 (VIX), ~250-400 (CPI).
- Power at the frozen threshold: the smallest detectable net mean is ~0.2-0.3R.
- Information value: each hypothesis's price-only control (own5 alone, same pairs/side/exit) will be
  reported beside it (descriptive); the verdict is the battery's.
- DATA-BLOCKED, not tested and not approximated: CFTC positioning, consensus surprises, central-bank
  decision surprises, first-release macro (docs/ROUND4_AUDIT.md).
