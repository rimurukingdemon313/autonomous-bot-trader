# Funding radar: live paper ledger

Updated **2026-11-22 21:00 UTC**, run 1099, version `radar-1.0.0`. State from: cache. Quotes this hour: 2369.

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

- days: 46.04
- run_coverage: 0.9937
- closed_positions: 256
- open_positions: 3
- utilisation: 0.2522
- rf_apr_pct_declared: 3.875
- book_pnl_pct: -2.6022
- book_excess_pct: -2.7504
- ann_excess_deployed_pct: -86.886
- ann_excess_deployed_costs_x1.5_pct: -157.151
- ann_excess_deployed_costs_x2_pct: -227.416
- best_coin: INIT
- book_excess_without_best_coin_pct: -3.2047
- max_dd_pct: 2.607
- t_excess_daily: -4.142

## Open positions

| Coin | Short | Long | Opened | Entry spread APR | Funding bp | Basis bp | Cost bp | Net bp |
|---|---|---|---|---|---|---|---|---|
| SOXL | mexc | gate | 2026-11-22 11:00 | 28.3% | 9.2 | 0.1 | 17.0 | **-7.7** |
| PIEVERSE | mexc | gate | 2026-11-22 17:00 | 31.8% | 1.5 | -1.1 | 17.0 | **-16.6** |
| EVAA | mexc | gate | 2026-11-22 20:00 | 60.0% | 0.3 | 11.4 | 17.0 | **-5.3** |

## Closed positions (256)

| Coin | Short | Long | Days | Reason | Net bp |
|---|---|---|---|---|---|
| IDOL | mexc | gate | 0.7 | spread_reversed | -29.0 |
| EVAA | mexc | gate | 0.2 | rebalance | -47.2 |
| PIEVERSE | mexc | gate | 0.2 | rebalance | -6.7 |
| EVAA | mexc | gate | 0.1 | rebalance | 26.4 |
| PIEVERSE | mexc | gate | 3.6 | rebalance | 23.6 |
| EVAA | mexc | gate | 0.1 | rebalance | -38.6 |
| EVAA | mexc | gate | 0.9 | rebalance | -15.2 |
| SOXL | mexc | gate | 0.4 | spread_reversed | -26.0 |
| EVAA | mexc | gate | 1.7 | rebalance | 20.2 |
| SOXL | mexc | gate | 0.5 | spread_reversed | -37.0 |
| SOXL | mexc | gate | 3.3 | rebalance | -0.6 |
| KORU | mexc | gate | 1.8 | spread_reversed | -15.4 |
| IRYS | mexc | gate | 0.1 | spread_reversed | -45.0 |
| IRYS | mexc | gate | 0.4 | spread_reversed | -51.8 |
| SOXS | gate | mexc | 2.0 | spread_decayed | -12.0 |
| IRYS | mexc | gate | 0.3 | spread_reversed | -42.0 |
| MMT | mexc | gate | 0.6 | spread_reversed | -22.4 |
| EVAA | mexc | gate | 1.0 | rebalance | -93.1 |
| BLESS | mexc | gate | 2.3 | spread_decayed | -1.8 |
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

## Top opportunities this hour (passing the entry rule)

| Coin | Short | Long | 72 h spread APR | Now APR |
|---|---|---|---|---|
| EVAA | mexc | gate | 58.9% | 34.6% |
| PIEVERSE | mexc | gate | 31.8% | 29.3% |

Rules and success criteria: `research/preregistrations/RADAR-1.md` on main.
