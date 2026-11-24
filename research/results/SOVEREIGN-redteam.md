# SOVEREIGN: the owner's three strategies on real daily bars

**RED TEAM, RESEARCH ONLY: a replay of the owner's own code on real daily bars; it validates nothing.** The owner's own code (`research/external/sovereign/sovereign_top3_suite.py`, unchanged) run on 5,175 daily bars of QQQ, SPY, IWM, GLD, SLV, USO and IBIT (2006-04-28 to 2026-11-20; IBIT from 2024-11-01), by `scripts/sovereign_redteam.py`. Every figure is in `research/results/SOVEREIGN-redteam.json`.

## The weights it prints for 2026-11-20 (T1)

| Rule | The replay | The spec |
|---|---|---|
| SOVEREIGN-TITAN-MAX | IBIT -0.2750, QQQ -0.3282, SLV -0.1320, USO -0.2440 | IBIT -0.2750, QQQ -0.3282, SLV -0.1320, USO -0.2440 |
| SOVEREIGN-TITAN-7 | IBIT -0.2750, QQQ -0.3282, SLV -0.1320, USO -0.2440 | IBIT -0.2750, QQQ -0.3282, SLV -0.1320, USO -0.2440 |
| SEC-TSMOM-4 | IBIT -0.2375, QQQ -0.3044, SLV -0.1140, USO -0.2263 | IBIT -0.2375, QQQ -0.3044, SLV -0.1140, USO -0.2263 |

The replay reproduces them to the fourth decimal: the data and the engines are the ones its author ran.

## Its five regimes, each from $200,000 (T2)

| Rule | Regime | The spec, 8 bps | Replay, 8 bps | 16 bps | One day late | Sharpe | Worst fall | Worst day | Days with a 5% daily loss |
|---|---|---|---|---|---|---|---|---|---|
| SOVEREIGN-TITAN-MAX | 2008-2013 | +75,369 | -7,700 | -12,956 | -3,601 | -0.06 | -16.5% | -5.5% | 1 |
| SOVEREIGN-TITAN-MAX | 2014-2019 | +31,271 | +5,718 | +2,677 | +354 | 0.11 | -11.6% | -2.7% | 0 |
| SOVEREIGN-TITAN-MAX | 2020-2024 | +117,417 | +106,965 | +91,648 | +118,239 | 0.76 | -17.1% | -7.4% | 5 |
| SOVEREIGN-TITAN-MAX | 2024-2025 | +7,996 | -7,199 | -10,087 | -5,956 | -0.27 | -9.7% | -4.2% | 0 |
| SOVEREIGN-TITAN-MAX | 2025-2026 | +82,238 | +89,947 | +82,513 | +69,428 | 2.20 | -9.4% | -4.6% | 2 |
| SOVEREIGN-TITAN-7 | 2008-2013 | +66,874 | -9,603 | -20,835 | -9,814 | -0.07 | -18.0% | -5.5% | 2 |
| SOVEREIGN-TITAN-7 | 2014-2019 | -12,220 | -21,685 | -26,819 | -19,015 | -0.32 | -13.7% | -4.7% | 1 |
| SOVEREIGN-TITAN-7 | 2020-2024 | +112,376 | +88,175 | +86,743 | +89,518 | 0.62 | -19.4% | -7.5% | 5 |
| SOVEREIGN-TITAN-7 | 2024-2025 | +4,516 | -11,094 | -13,630 | -8,596 | -0.51 | -9.7% | -3.9% | 0 |
| SOVEREIGN-TITAN-7 | 2025-2026 | +54,467 | -5,157 | +23,745 | +20,661 | -0.17 | -10.9% | -4.6% | 3 |
| SEC-TSMOM-4 | 2008-2013 | +34,544 | +4,137 | -9,072 | +22,586 | 0.08 | -16.2% | -3.9% | 0 |
| SEC-TSMOM-4 | 2014-2019 | -13,702 | -12,263 | -20,344 | -5,603 | -0.18 | -11.7% | -4.3% | 0 |
| SEC-TSMOM-4 | 2020-2024 | +96,900 | +82,503 | +70,071 | +72,637 | 0.72 | -16.7% | -4.9% | 1 |
| SEC-TSMOM-4 | 2024-2025 | +12,836 | -13,448 | -14,912 | -7,927 | -0.64 | -9.2% | -3.1% | 0 |
| SEC-TSMOM-4 | 2025-2026 | +46,590 | +46,670 | +36,377 | +15,265 | 1.38 | -8.5% | -3.8% | 2 |

| Rule | Regimes won, the spec | Regimes won, the replay | Sum, the spec | Sum, the replay |
|---|---|---|---|---|
| SOVEREIGN-TITAN-MAX | 5/5 | 3/5 | +314,291 | +187,731 |
| SOVEREIGN-TITAN-7 | 4/5 | 1/5 | +226,013 | +40,636 |
| SEC-TSMOM-4 | 4/5 | 3/5 | +177,168 | +107,599 |

## One account from 2008 to 2026 (T3)

| Rule | Profit, 8 bps | a year | Sharpe | t | Worst fall | Worst day | Profit, 16 bps | Losing years | With the spec's live layer |
|---|---|---|---|---|---|---|---|---|---|
| SOVEREIGN-TITAN-MAX | +107,081 | 2.3% | 0.34 | 1.46 | -17.1% | -7.4% | +46,086 | 10 of 19 | stopped for good on 2008-03-25, -3,020 |
| SOVEREIGN-TITAN-7 | +38,104 | 0.9% | 0.17 | 0.75 | -20.7% | -7.5% | -5,037 | 7 of 19 | stopped for good on 2008-03-25, -1,824 |
| SEC-TSMOM-4 | +66,841 | 1.5% | 0.27 | 1.18 | -18.0% | -3.9% | -845 | 8 of 19 | stopped for good on 2008-09-22, +10,377 |

SPY held over the same span, no cost: +1,174,097 (10.8% a year), Sharpe 0.62, worst fall -51.5% (T6).

Year by year, 8 bps (SOVEREIGN-TITAN-MAX): 2008 -1.1%, 2009 -2.8%, 2010 -2.0%, 2011 -3.7%, 2012 +2.5%, 2013 +3.5%, 2014 +3.6%, 2015 -2.0%, 2016 -0.2%, 2017 +2.3%, 2018 -0.0%, 2019 -2.5%, 2020 +23.7%, 2021 +11.0%, 2022 -4.7%, 2023 -0.8%, 2024 +0.0%, 2025 +3.8%, 2026 +17.4%.

## A prop firm's rules from every start date (T4)

| Rule | Starts (every 21 days) | Failed within a year (5% daily or 10% total, on the day's adverse extremes) |
|---|---|---|
| SOVEREIGN-TITAN-MAX | 215 | 106 (49.3%) |
| SOVEREIGN-TITAN-7 | 215 | 116 (54.0%) |
| SEC-TSMOM-4 | 215 | 55 (25.6%) |

## Does the direction carry information? (T5, before costs)

| Rule | Sharpe before costs | 200 placebos: median | 95th percentile | Placebos at or above |
|---|---|---|---|---|
| SOVEREIGN-TITAN-MAX | 0.52 | -0.03 | 0.28 | 0.0% |
| SOVEREIGN-TITAN-7 | 0.21 | -0.04 | 0.28 | 13.0% |
| SEC-TSMOM-4 | 0.40 | -0.04 | 0.31 | 2.0% |

## The spec's own checklist (T0)

- Look-ahead: a close moved by half changes no earlier weight in any of the three rules.
- No weight passes its cap (TAIL_CAPS times 1.10, or 0.95 for SEC-TSMOM-4) on any of the 5,175 days.
- The shield's steps are as stated: half at -5%, a quarter at -7.5%, nothing at -4% in a day or -8.5% in all.
- **The 90-day short guards of SOVEREIGN-TITAN-MAX do not hold for the positions it holds:** its five-tranche average keeps a short for days after its guard has turned it off. Days short while the guard says no (of the days short): GLD 54 of 894, IWM 83 of 649, QQQ 61 of 367, SLV 149 of 1471, SPY 34 of 191.

Read it as a replay of the owner's code, not as a test of it: nothing here was preregistered, and its 2025-2026 year is the one its parameters were chosen on.
