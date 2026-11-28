# Funding radar: live paper ledger

Updated **2026-11-28 12:00 UTC**, run 1234, version `radar-1.0.0`. State from: cache. Quotes this hour: 2389.

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

- days: 51.67
- run_coverage: 0.9944
- closed_positions: 284
- open_positions: 3
- utilisation: 0.2533
- rf_apr_pct_declared: 3.875
- book_pnl_pct: -2.9085
- book_excess_pct: -3.0724
- ann_excess_deployed_pct: -86.069
- ann_excess_deployed_costs_x1.5_pct: -155.026
- ann_excess_deployed_costs_x2_pct: -223.983
- best_coin: INIT
- book_excess_without_best_coin_pct: -3.4981
- max_dd_pct: 2.9102
- t_excess_daily: -4.607

## Open positions

| Coin | Short | Long | Opened | Entry spread APR | Funding bp | Basis bp | Cost bp | Net bp |
|---|---|---|---|---|---|---|---|---|
| SOXS | gate | mexc | 2026-11-27 08:00 | 25.5% | 11.6 | 1.9 | 17.0 | **-3.5** |
| EVAA | mexc | gate | 2026-11-28 08:00 | 34.6% | 2.3 | -13.8 | 17.0 | **-28.4** |
| WLFI | gate | mexc | 2026-11-28 12:00 | 25.8% | 0.0 | 0.0 | 17.0 | **-17.0** |

## Closed positions (284)

| Coin | Short | Long | Days | Reason | Net bp |
|---|---|---|---|---|---|
| WLFI | gate | mexc | 0.1 | spread_reversed | 2.1 |
| WLFI | mexc | hyperliquid | 0.0 | spread_decayed | -2.5 |
| EVAA | mexc | gate | 0.2 | rebalance | -51.3 |
| BULLA | mexc | gate | 0.6 | spread_reversed | 33.4 |
| EVAA | mexc | gate | 0.1 | spread_reversed | -29.2 |
| INIT | gate | mexc | 0.7 | rebalance | -55.7 |
| EVAA | mexc | gate | 0.1 | rebalance | -22.7 |
| EVAA | mexc | gate | 1.9 | rebalance | -38.5 |
| BULLA | mexc | gate | 0.1 | rebalance | -70.3 |
| SOXL | mexc | gate | 1.3 | spread_reversed | -61.0 |
| SNXX | mexc | gate | 0.8 | spread_reversed | -31.2 |
| SOXS | gate | mexc | 0.9 | spread_reversed | -6.9 |
| EVAA | mexc | gate | 1.3 | rebalance | 49.4 |
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

## Top opportunities this hour (passing the entry rule)

| Coin | Short | Long | 72 h spread APR | Now APR |
|---|---|---|---|---|
| EVAA | mexc | gate | 32.9% | 62.4% |
| WLFI | gate | mexc | 25.8% | 33.5% |

Rules and success criteria: `research/preregistrations/RADAR-1.md` on main.
