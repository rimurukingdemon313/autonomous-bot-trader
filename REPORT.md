# Funding radar: live paper ledger

Updated **2026-11-25 09:00 UTC**, run 1159, version `radar-1.0.0`. State from: cache. Quotes this hour: 2380.

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

- days: 48.54
- run_coverage: 0.994
- closed_positions: 271
- open_positions: 4
- utilisation: 0.2544
- rf_apr_pct_declared: 3.875
- book_pnl_pct: -2.7619
- book_excess_pct: -2.9263
- ann_excess_deployed_pct: -86.956
- ann_excess_deployed_costs_x1.5_pct: -157.076
- ann_excess_deployed_costs_x2_pct: -227.196
- best_coin: INIT
- book_excess_without_best_coin_pct: -3.3806
- max_dd_pct: 2.7772
- t_excess_daily: -4.384

## Open positions

| Coin | Short | Long | Opened | Entry spread APR | Funding bp | Basis bp | Cost bp | Net bp |
|---|---|---|---|---|---|---|---|---|
| EVAA | mexc | gate | 2026-11-24 04:00 | 43.5% | 6.5 | 15.9 | 17.0 | **5.4** |
| SOXL | mexc | gate | 2026-11-25 00:00 | 28.9% | 3.3 | -2.9 | 17.0 | **-16.6** |
| SOXS | gate | mexc | 2026-11-25 02:00 | 33.3% | 9.2 | -0.1 | 17.0 | **-7.9** |
| SNXX | mexc | gate | 2026-11-25 04:00 | 44.0% | 2.3 | -6.1 | 17.0 | **-20.8** |

## Closed positions (271)

| Coin | Short | Long | Days | Reason | Net bp |
|---|---|---|---|---|---|
| SOXS | gate | mexc | 0.0 | spread_decayed | -41.0 |
| SOXS | gate | mexc | 0.0 | spread_decayed | -26.6 |
| SOXS | gate | mexc | 0.0 | spread_decayed | -33.6 |
| SOXS | gate | mexc | 0.0 | spread_decayed | -35.5 |
| SOXL | mexc | gate | 0.0 | spread_decayed | -33.8 |
| SOXL | mexc | gate | 0.0 | spread_decayed | -33.7 |
| SNXX | mexc | gate | 0.2 | spread_decayed | -42.2 |
| PIEVERSE | mexc | gate | 1.6 | spread_reversed | -30.4 |
| ACE | hyperliquid | mexc | 0.4 | spread_reversed | 159.9 |
| EVAA | mexc | gate | 0.9 | rebalance | -47.2 |
| SOXS | gate | mexc | 0.3 | spread_reversed | -40.8 |
| ACE | hyperliquid | mexc | 0.1 | spread_reversed | -32.6 |
| SOXS | gate | mexc | 0.5 | rebalance | -15.4 |
| SOXL | mexc | gate | 1.1 | rebalance | -39.2 |
| EVAA | mexc | gate | 0.5 | rebalance | -16.9 |
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

## Top opportunities this hour (passing the entry rule)

| Coin | Short | Long | 72 h spread APR | Now APR |
|---|---|---|---|---|
| SNXX | mexc | gate | 50.6% | 25.0% |
| SOXS | gate | mexc | 48.2% | 40.6% |
| SOXL | mexc | gate | 36.1% | 23.5% |
| EVAA | mexc | gate | 30.0% | 87.4% |

Rules and success criteria: `research/preregistrations/RADAR-1.md` on main.
