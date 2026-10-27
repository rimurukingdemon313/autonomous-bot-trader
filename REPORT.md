# Funding radar: live paper ledger

Updated **2026-10-27 19:00 UTC**, run 477, version `radar-1.0.0`. State from: cache. Quotes this hour: 2410.

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

- days: 19.96
- run_coverage: 0.9938
- closed_positions: 102
- open_positions: 3
- utilisation: 0.1168
- rf_apr_pct_declared: 3.875
- book_pnl_pct: -1.1628
- book_excess_pct: -1.2128
- ann_excess_deployed_pct: -191.766
- ann_excess_deployed_costs_x1.5_pct: -334.195
- ann_excess_deployed_costs_x2_pct: -476.624
- best_coin: IOST
- book_excess_without_best_coin_pct: -1.4342
- max_dd_pct: 1.1902
- t_excess_daily: -3.496

## Open positions

| Coin | Short | Long | Opened | Entry spread APR | Funding bp | Basis bp | Cost bp | Net bp |
|---|---|---|---|---|---|---|---|---|
| BTW | gate | mexc | 2026-10-27 06:00 | 59.7% | 5.3 | -10.4 | 17.0 | **-22.1** |
| AIN | mexc | gate | 2026-10-27 15:00 | 49.1% | 4.5 | -1.5 | 17.0 | **-14.0** |
| Q | mexc | gate | 2026-10-27 15:00 | 25.7% | 3.2 | 9.1 | 17.0 | **-4.7** |

## Closed positions (102)

| Coin | Short | Long | Days | Reason | Net bp |
|---|---|---|---|---|---|
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
| IOST | mexc | gate | 2.5 | spread_reversed | 117.2 |
| ORDER | mexc | gate | 0.0 | spread_reversed | -5.1 |
| BIRB | mexc | gate | 0.1 | spread_reversed | -83.8 |
| IRYS | mexc | gate | 0.2 | spread_reversed | 42.6 |
| BIRB | mexc | gate | 0.2 | rebalance | 26.8 |
| IRYS | mexc | gate | 0.5 | rebalance | -20.9 |

## Top opportunities this hour (passing the entry rule)

| Coin | Short | Long | 72 h spread APR | Now APR |
|---|---|---|---|---|
| BTW | gate | mexc | 54.4% | 64.8% |
| AIN | mexc | gate | 52.3% | 101.8% |
| Q | mexc | gate | 33.9% | 86.1% |

Rules and success criteria: `research/preregistrations/RADAR-1.md` on main.
