# Funding radar: live paper ledger

Updated **2026-10-28 11:00 UTC**, run 493, version `radar-1.0.0`. State from: cache. Quotes this hour: 2409.

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

- days: 20.62
- run_coverage: 0.994
- closed_positions: 109
- open_positions: 4
- utilisation: 0.1245
- rf_apr_pct_declared: 3.875
- book_pnl_pct: -1.2437
- book_excess_pct: -1.3047
- ann_excess_deployed_pct: -187.359
- ann_excess_deployed_costs_x1.5_pct: -326.478
- ann_excess_deployed_costs_x2_pct: -465.597
- best_coin: IOST
- book_excess_without_best_coin_pct: -1.5261
- max_dd_pct: 1.3124
- t_excess_daily: -3.683

## Open positions

| Coin | Short | Long | Opened | Entry spread APR | Funding bp | Basis bp | Cost bp | Net bp |
|---|---|---|---|---|---|---|---|---|
| AIN | mexc | gate | 2026-10-27 15:00 | 49.1% | 28.9 | 17.8 | 17.0 | **29.8** |
| BTW | gate | mexc | 2026-10-27 23:00 | 56.0% | 3.9 | 4.9 | 17.0 | **-8.2** |
| BULLA | mexc | gate | 2026-10-28 06:00 | 73.9% | 37.8 | 75.8 | 17.0 | **96.7** |
| EVAA | mexc | gate | 2026-10-28 09:00 | 33.0% | 1.3 | -13.8 | 17.0 | **-29.5** |

## Closed positions (109)

| Coin | Short | Long | Days | Reason | Net bp |
|---|---|---|---|---|---|
| Q | mexc | gate | 0.1 | spread_reversed | 29.0 |
| Q | mexc | gate | 0.0 | rebalance | -159.5 |
| BULLA | mexc | gate | 0.0 | spread_reversed | -75.4 |
| Q | mexc | gate | 0.6 | rebalance | -6.3 |
| BULLA | mexc | gate | 0.1 | spread_reversed | 60.9 |
| BULLA | mexc | gate | 0.1 | spread_reversed | -63.7 |
| BTW | gate | mexc | 0.6 | rebalance | -76.3 |
| BULLA | mexc | gate | 0.1 | spread_reversed | -118.9 |
| BULLA | mexc | gate | 0.0 | rebalance | 130.4 |
| BULLA | mexc | gate | 0.1 | spread_reversed | -83.2 |
| BULLA | mexc | gate | 0.1 | rebalance | 15.8 |
| BTW | gate | mexc | 0.5 | rebalance | 7.9 |
| IRYS | mexc | gate | 0.2 | spread_reversed | -24.4 |
| BTW | mexc | gate | 0.1 | spread_decayed | -39.7 |
| IRYS | mexc | gate | 0.0 | spread_reversed | -48.1 |
| IRYS | mexc | gate | 0.5 | spread_reversed | 3.4 |
| BTW | gate | mexc | 0.0 | spread_decayed | -51.9 |
| BTW | gate | mexc | 0.0 | spread_decayed | -28.5 |
| IRYS | mexc | gate | 0.2 | spread_reversed | -41.8 |
| BTW | gate | mexc | 0.0 | spread_decayed | -26.9 |
| IRYS | mexc | gate | 0.2 | spread_reversed | -44.2 |
| IRYS | mexc | gate | 0.1 | spread_reversed | -15.4 |
| BTW | mexc | gate | 0.1 | spread_reversed | -56.1 |
| ORDER | mexc | gate | 0.4 | spread_reversed | 20.7 |
| IRYS | mexc | gate | 0.0 | spread_reversed | -22.9 |
| SOXL | mexc | gate | 0.4 | spread_reversed | -35.8 |
| IRYS | mexc | gate | 0.0 | spread_reversed | -72.6 |
| IRYS | mexc | gate | 0.1 | spread_reversed | -88.7 |
| BIRB | mexc | gate | 0.3 | spread_reversed | -3.1 |
| ORDER | mexc | gate | 0.2 | spread_reversed | -52.1 |

## Top opportunities this hour (passing the entry rule)

| Coin | Short | Long | 72 h spread APR | Now APR |
|---|---|---|---|---|
| BTW | gate | mexc | 93.6% | 32.4% |
| AIN | mexc | gate | 77.7% | 83.0% |
| EVAA | mexc | gate | 34.7% | 65.9% |

Rules and success criteria: `research/preregistrations/RADAR-1.md` on main.
