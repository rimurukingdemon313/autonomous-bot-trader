# Round 2's strategies on every possible trade

**DESCRIPTIVE BACKTEST, NOT A TEST: it cannot change a verdict (SCX-1 and KRP-1 FAILED as registered); a row chosen for being the best is a fit to the past, not an edge.** KRP-1's validation months, 2025-03 to 2026-10, are read here for the first time: they are spent for the Korean-premium family.

Run 2026-11-22T10:07:05.598434+00:00 (r2-backtest-1.0.0). Every row is in `research/results/ROUND2-full-backtest.json`, with every trade of the two registered rules.

## SCX-1: stablecoins at the weekend (2018-12-16 to 2026-10-25)

Sunday 22:00 UTC close, exit 23 hours later; 364 archive files, 0 absent; pairs: BUSDUSDT, FDUSDUSDT, PAXUSDT, TUSDUSDT, USDCUSDT, USDPUSDT.

| Threshold | Swaps | Weeks | Gross a swap | t (gross) | Net at 1 bp a fill | t | Net at 10 bp a fill | $10,000 at 1 bp a fill | Worst fall |
|---|---|---|---|---|---|---|---|---|---|
| 1 bp | 1384 | 401 | +2.4 bp | 3.50 | +0.4 bp | 0.55 | -17.6 bp | $10,153 (+0.19% a year) | -3.00% |
| 3 bp | 1117 | 356 | +2.8 bp | 3.72 | +0.8 bp | 1.10 | -17.2 bp | $10,306 (+0.38% a year) | -1.60% |
| 5 bp | 891 | 323 | +3.5 bp | 4.06 | +1.5 bp | 1.74 | -16.5 bp | $10,497 (+0.62% a year) | -1.27% |
| 10 bp (registered) | 493 | 230 | +4.9 bp | 4.14 | +2.9 bp | 2.46 | -15.1 bp | $10,695 (+0.86% a year) | -1.15% |
| 20 bp | 205 | 110 | +8.1 bp | 3.19 | +6.1 bp | 2.40 | -11.9 bp | $10,693 (+0.86% a year) | -1.33% |
| 50 bp | 67 | 33 | +20.9 bp | 2.70 | +18.9 bp | 2.45 | +0.9 bp | $10,644 (+0.80% a year) | -1.21% |

The same rule at 10 bp on every day of the week (22:00 UTC, 23 hours):

| Day | Swaps | Gross a swap | t | Net at 1 bp a fill |
|---|---|---|---|---|
| Monday | 511 | +4.2 bp | 3.89 | +2.2 bp |
| Tuesday | 481 | +2.2 bp | 2.14 | +0.2 bp |
| Wednesday | 531 | +3.1 bp | 2.22 | +1.1 bp |
| Thursday | 541 | +2.7 bp | 1.44 | +0.7 bp |
| Friday | 508 | +1.7 bp | 1.84 | -0.3 bp |
| Saturday | 514 | +0.2 bp | 0.19 | -1.8 bp |
| Sunday | 493 | +4.9 bp | 4.14 | +2.9 bp |

The registered rule (10 bp) by year, at 1 bp a fill:

| Year | Swaps | Gross | Net | Sum of nets |
|---|---|---|---|---|
| 2018 | 9 | +34.5 bp | +32.5 bp | +292.8 bp |
| 2019 | 115 | +11.1 bp | +9.1 bp | +1042.9 bp |
| 2020 | 49 | +6.2 bp | +4.2 bp | +208.0 bp |
| 2021 | 31 | +3.8 bp | +1.8 bp | +55.1 bp |
| 2022 | 21 | -0.0 bp | -2.0 bp | -43.0 bp |
| 2023 | 46 | +14.6 bp | +12.6 bp | +580.4 bp |
| 2024 | 72 | +3.3 bp | +1.3 bp | +96.2 bp |
| 2025 | 101 | +0.1 bp | -1.9 bp | -196.1 bp |
| 2026 | 49 | +2.1 bp | +0.1 bp | +5.8 bp |

## KRP-1: the Korean coin premium (2018-01-01 to 2026-10-29)

an hour after the 00:00 UTC close; long the coin on Binance spot, short bitcoin; 9485 archive files (0 absent), 205 Upbit markets (0 absent), 204 coins.

Fresh spikes (the registered rule's kind), every threshold and hold:

| Threshold, hold | Trades | Days | Gross a trade (vs bitcoin) | t (gross) | Net at 0.6% | t | Net at 0.2% | $10,000 at 0.6% | at 0.2% | Worst fall at 0.6% |
|---|---|---|---|---|---|---|---|---|---|---|
| 2%, 6h | 1051 | 601 | +0.34% | 2.59 | -0.26% | -2.05 | +0.14% | $8,321 | $11,802 | -19.02% |
| 3%, 6h | 753 | 469 | +0.40% | 2.47 | -0.20% | -1.24 | +0.20% | $9,124 | $11,784 | -13.67% |
| 5%, 6h | 429 | 306 | +0.56% | 2.58 | -0.04% | -0.18 | +0.36% | $9,826 | $11,499 | -8.97% |
| 10%, 6h | 200 | 145 | +0.59% | 1.69 | -0.01% | -0.03 | +0.39% | $9,867 | $10,681 | -7.88% |
| 20%, 6h | 76 | 58 | +0.48% | 0.81 | -0.12% | -0.21 | +0.28% | $9,856 | $10,161 | -4.93% |
| 2%, 24h | 1053 | 602 | +0.15% | 0.59 | -0.45% | -1.78 | -0.05% | $7,876 | $11,179 | -32.47% |
| 3%, 24h | 754 | 470 | +0.12% | 0.43 | -0.48% | -1.67 | -0.08% | $8,650 | $11,175 | -18.52% |
| 5%, 24h (registered) | 429 | 306 | +0.43% | 1.14 | -0.17% | -0.44 | +0.23% | $9,664 | $11,310 | -13.22% |
| 10%, 24h | 200 | 145 | +0.77% | 1.21 | +0.17% | 0.27 | +0.57% | $10,114 | $10,949 | -7.54% |
| 20%, 24h | 76 | 58 | +1.45% | 1.28 | +0.85% | 0.75 | +1.25% | $10,224 | $10,541 | -4.34% |
| 2%, 72h | 653 | 390 | -0.71% | -1.42 | -1.31% | -2.63 | -0.91% | $7,012 | $8,607 | -32.47% |
| 3%, 72h | 468 | 295 | -0.75% | -1.25 | -1.35% | -2.25 | -0.95% | $7,763 | $9,010 | -27.97% |
| 5%, 72h | 246 | 177 | -0.16% | -0.19 | -0.76% | -0.93 | -0.36% | $8,875 | $9,668 | -17.10% |
| 10%, 72h | 102 | 78 | +1.46% | 1.05 | +0.86% | 0.62 | +1.26% | $10,574 | $10,993 | -9.70% |
| 20%, 72h | 43 | 36 | +1.36% | 0.88 | +0.76% | 0.49 | +1.16% | $10,129 | $10,306 | -3.75% |
| 2%, 168h | 521 | 314 | -1.98% | -2.50 | -2.58% | -3.26 | -2.18% | $4,901 | $5,741 | -58.92% |
| 3%, 168h | 363 | 232 | -1.05% | -1.06 | -1.65% | -1.67 | -1.25% | $6,775 | $7,565 | -46.97% |
| 5%, 168h | 181 | 129 | -2.03% | -1.85 | -2.63% | -2.40 | -2.23% | $7,171 | $7,618 | -30.97% |
| 10%, 168h | 75 | 57 | +1.31% | 0.85 | +0.71% | 0.46 | +1.11% | $10,341 | $10,614 | -8.11% |
| 20%, 168h | 34 | 28 | +1.21% | 0.55 | +0.61% | 0.28 | +1.01% | $9,774 | $9,901 | -5.33% |

Every premium day, fresh or not (24 hours):

| Threshold, hold | Trades | Days | Gross a trade (vs bitcoin) | t (gross) | Net at 0.6% | t | Net at 0.2% | $10,000 at 0.6% | at 0.2% | Worst fall at 0.6% |
|---|---|---|---|---|---|---|---|---|---|---|
| 2%, 24h | 1818 | 1015 | +0.11% | 0.65 | -0.49% | -2.77 | -0.09% | $5,424 | $10,456 | -50.64% |
| 3%, 24h | 1444 | 899 | +0.13% | 0.67 | -0.47% | -2.34 | -0.07% | $6,278 | $10,690 | -39.19% |
| 5%, 24h (registered) | 1027 | 744 | +0.30% | 1.31 | -0.30% | -1.34 | +0.10% | $7,536 | $11,204 | -33.05% |
| 10%, 24h | 658 | 527 | +0.30% | 1.22 | -0.30% | -1.21 | +0.10% | $7,964 | $10,357 | -27.73% |
| 20%, 24h | 350 | 313 | +0.46% | 1.29 | -0.14% | -0.39 | +0.26% | $9,187 | $10,568 | -17.60% |

Korean discounts instead (the contrast; 24 hours):

| Threshold, hold | Trades | Days | Gross a trade (vs bitcoin) | t (gross) | Net at 0.6% | t | Net at 0.2% | $10,000 at 0.6% | at 0.2% | Worst fall at 0.6% |
|---|---|---|---|---|---|---|---|---|---|---|
| 2%, 24h | 254 | 213 | -0.78% | -0.80 | -1.38% | -1.41 | -0.98% | $7,000 | $7,750 | -36.57% |
| 3%, 24h | 156 | 143 | +0.23% | 0.12 | -0.37% | -0.19 | +0.03% | $9,152 | $9,741 | -27.16% |
| 5%, 24h (registered) | 97 | 93 | -1.44% | -0.88 | -2.04% | -1.24 | -1.64% | $8,115 | $8,437 | -24.48% |
| 10%, 24h | 56 | 56 | -1.35% | -0.51 | -1.95% | -0.74 | -1.55% | $8,856 | $9,057 | -18.52% |
| 20%, 24h | 27 | 27 | -6.05% | -1.55 | -6.65% | -1.71 | -6.25% | $8,309 | $8,400 | -19.24% |

The registered rule (5%, 24 hours) by year, at 0.6% a round trip:

| Year | Trades | Gross | Net | Sum of nets |
|---|---|---|---|---|
| 2018 | 7 | -3.10% | -3.70% | -25.9% |
| 2019 | 19 | +0.47% | -0.13% | -2.5% |
| 2020 | 35 | -0.86% | -1.46% | -51.0% |
| 2021 | 68 | +2.25% | +1.65% | +112.5% |
| 2022 | 92 | -0.41% | -1.01% | -92.7% |
| 2023 | 45 | +0.56% | -0.04% | -1.8% |
| 2024 | 10 | +3.18% | +2.58% | +25.8% |
| 2025 | 125 | +0.09% | -0.51% | -63.5% |
| 2026 | 28 | -0.18% | -0.78% | -21.9% |

Read it as a description. The registered rows were judged once, on their own stages, and failed; the others were never registered, and the best of many rows is expected to look good by chance.
