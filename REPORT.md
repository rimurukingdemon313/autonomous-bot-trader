# Funding radar: live paper ledger

Updated **2026-11-19 07:00 UTC**, run 1013, version `radar-1.0.0`. State from: cache. Quotes this hour: 2361.

**PAPER ONLY.** No order is ever sent. Every number is computed from public live quotes. Positions are short the perpetual on the venue paying more funding and long it on the other, on the same coin. Costs are each venue's taker fee plus 5 bp per fill.

| Venue | Status |
|---|---|
| hyperliquid | ok |
| gate | ok |
| mexc | ok |
| dydx | ok |

## Forward test RADAR-1

**WAIT**: the single look is on 2026-12-06 20:00 UTC

## Performance (paper; capital = 2N per slot x 10 slots; excess = net P&L minus cash on 2N while open)

- days: 42.46
- run_coverage: 0.9931
- closed_positions: 237
- open_positions: 7
- utilisation: 0.2428
- rf_apr_pct_declared: 3.875
- book_pnl_pct: -2.3985
- book_excess_pct: -2.5666
- ann_excess_deployed_pct: -91.509
- ann_excess_deployed_costs_x1.5_pct: -166.265
- ann_excess_deployed_costs_x2_pct: -241.021
- best_coin: INIT
- book_excess_without_best_coin_pct: -3.021
- max_dd_pct: 2.4154
- t_excess_daily: -3.797

## Open positions

| Coin | Short | Long | Opened | Entry spread APR | Funding bp | Basis bp | Cost bp | Net bp |
|---|---|---|---|---|---|---|---|---|
| BLESS | mexc | gate | 2026-11-17 04:00 | 28.2% | 17.3 | 2.2 | 17.0 | **2.5** |
| SOXL | mexc | gate | 2026-11-17 08:00 | 25.1% | 14.1 | -2.1 | 17.0 | **-5.1** |
| SOXS | gate | mexc | 2026-11-17 18:00 | 26.4% | 14.8 | 1.6 | 17.0 | **-0.6** |
| EVAA | mexc | gate | 2026-11-18 15:00 | 45.8% | 6.4 | -15.6 | 17.0 | **-26.2** |
| PIEVERSE | mexc | gate | 2026-11-18 18:00 | 26.1% | 16.3 | 8.6 | 17.0 | **7.9** |
| KORU | mexc | gate | 2026-11-18 20:00 | 39.0% | 1.5 | -0.1 | 17.0 | **-15.6** |
| MMT | mexc | gate | 2026-11-19 00:00 | 25.4% | 1.9 | 16.4 | 17.0 | **1.3** |

## Closed positions (237)

| Coin | Short | Long | Days | Reason | Net bp |
|---|---|---|---|---|---|
| KORU | mexc | gate | 0.0 | spread_decayed | -32.2 |
| KORU | mexc | gate | 0.0 | spread_decayed | -42.9 |
| KORU | mexc | gate | 0.0 | spread_decayed | -26.3 |
| KORU | mexc | gate | 0.0 | spread_decayed | -37.0 |
| BREV | gate | mexc | 0.1 | spread_decayed | -77.3 |
| SNXX | mexc | gate | 1.2 | spread_reversed | -9.4 |
| MUU | mexc | gate | 0.0 | spread_decayed | -33.7 |
| EVAA | mexc | gate | 0.0 | spread_decayed | -6.8 |
| MUU | mexc | gate | 0.0 | spread_decayed | -33.7 |
| EVAA | mexc | gate | 0.0 | spread_decayed | -69.0 |
| BREV | gate | mexc | 0.0 | spread_reversed | -37.4 |
| MUU | mexc | gate | 0.0 | spread_decayed | -33.6 |
| BREV | gate | mexc | 0.2 | spread_reversed | -33.2 |
| PIEVERSE | mexc | gate | 8.6 | rebalance | -39.8 |
| KORU | mexc | gate | 0.9 | spread_decayed | -60.0 |
| AKE | mexc | gate | 1.2 | spread_reversed | -8.0 |
| BREV | gate | mexc | 0.1 | spread_reversed | 8.0 |
| EVAA | mexc | gate | 0.3 | spread_reversed | -26.2 |
| EVAA | mexc | gate | 1.0 | rebalance | -17.8 |
| LIT | hyperliquid | gate | 0.6 | spread_reversed | -31.7 |
| BLESS | mexc | gate | 0.1 | rebalance | -21.6 |
| AKE | mexc | gate | 0.6 | spread_reversed | -17.8 |
| RARE | mexc | gate | 0.0 | spread_decayed | -56.9 |
| EVAA | mexc | gate | 0.8 | rebalance | 11.4 |
| AKE | mexc | gate | 0.7 | spread_reversed | -40.9 |
| AKE | mexc | gate | 0.1 | spread_reversed | -40.7 |
| AKE | mexc | gate | 0.8 | spread_decayed | 6.6 |
| BARD | mexc | gate | 0.2 | spread_reversed | -38.3 |
| INIT | gate | mexc | 2.5 | rebalance | 573.2 |
| AKE | mexc | gate | 0.3 | spread_reversed | 34.3 |

## Top opportunities this hour (passing the entry rule)

| Coin | Short | Long | 72 h spread APR | Now APR |
|---|---|---|---|---|

Rules and success criteria: `research/preregistrations/RADAR-1.md` on main.
