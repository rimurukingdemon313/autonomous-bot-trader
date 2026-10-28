# Funding radar: live paper ledger

Updated **2026-10-28 06:00 UTC**, run 488, version `radar-1.0.0`. State from: cache. Quotes this hour: 2411.

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

- days: 20.42
- run_coverage: 0.9939
- closed_positions: 108
- open_positions: 4
- utilisation: 0.1219
- rf_apr_pct_declared: 3.875
- book_pnl_pct: -1.3124
- book_excess_pct: -1.3725
- ann_excess_deployed_pct: -203.439
- ann_excess_deployed_costs_x1.5_pct: -345.771
- ann_excess_deployed_costs_x2_pct: -488.102
- best_coin: IOST
- book_excess_without_best_coin_pct: -1.5939
- max_dd_pct: 1.3124
- t_excess_daily: -3.892

## Open positions

| Coin | Short | Long | Opened | Entry spread APR | Funding bp | Basis bp | Cost bp | Net bp |
|---|---|---|---|---|---|---|---|---|
| AIN | mexc | gate | 2026-10-27 15:00 | 49.1% | 23.7 | 3.3 | 17.0 | **10.0** |
| BTW | gate | mexc | 2026-10-27 23:00 | 56.0% | 2.6 | 18.8 | 17.0 | **4.3** |
| BULLA | mexc | gate | 2026-10-28 06:00 | 73.9% | 0.0 | 0.0 | 17.0 | **-17.0** |
| Q | mexc | gate | 2026-10-28 06:00 | 45.7% | 0.0 | 0.0 | 17.0 | **-17.0** |

## Closed positions (108)

| Coin | Short | Long | Days | Reason | Net bp |
|---|---|---|---|---|---|
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
| IRYS | mexc | gate | 0.4 | rebalance | 4.7 |

## Top opportunities this hour (passing the entry rule)

| Coin | Short | Long | 72 h spread APR | Now APR |
|---|---|---|---|---|
| BULLA | mexc | gate | 73.9% | 245.5% |
| AIN | mexc | gate | 71.8% | 147.2% |
| BTW | gate | mexc | 59.5% | 38.1% |
| Q | mexc | gate | 45.7% | 48.0% |

Rules and success criteria: `research/preregistrations/RADAR-1.md` on main.
