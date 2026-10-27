# Funding radar: live paper ledger

Updated **2026-10-27 15:00 UTC**, run 473, version `radar-1.0.0`. State from: cache. Quotes this hour: 2410.

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

- days: 19.79
- run_coverage: 0.9937
- closed_positions: 100
- open_positions: 4
- utilisation: 0.1146
- rf_apr_pct_declared: 3.875
- book_pnl_pct: -1.1902
- book_excess_pct: -1.248
- ann_excess_deployed_pct: -203.201
- ann_excess_deployed_costs_x1.5_pct: -348.482
- ann_excess_deployed_costs_x2_pct: -493.763
- best_coin: IOST
- book_excess_without_best_coin_pct: -1.4694
- max_dd_pct: 1.1902
- t_excess_daily: -3.572

## Open positions

| Coin | Short | Long | Opened | Entry spread APR | Funding bp | Basis bp | Cost bp | Net bp |
|---|---|---|---|---|---|---|---|---|
| BTW | gate | mexc | 2026-10-27 06:00 | 59.7% | 2.4 | -18.6 | 17.0 | **-33.2** |
| AIN | mexc | gate | 2026-10-27 15:00 | 49.1% | 0.0 | 0.0 | 17.0 | **-17.0** |
| BULLA | mexc | gate | 2026-10-27 15:00 | 43.6% | 0.0 | 0.0 | 17.0 | **-17.0** |
| Q | mexc | gate | 2026-10-27 15:00 | 25.7% | 0.0 | 0.0 | 17.0 | **-17.0** |

## Closed positions (100)

| Coin | Short | Long | Days | Reason | Net bp |
|---|---|---|---|---|---|
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
| BTW | mexc | gate | 0.0 | spread_reversed | -43.0 |
| BTW | mexc | gate | 0.0 | spread_decayed | -46.0 |

## Top opportunities this hour (passing the entry rule)

| Coin | Short | Long | 72 h spread APR | Now APR |
|---|---|---|---|---|
| BTW | gate | mexc | 49.7% | 24.7% |
| AIN | mexc | gate | 49.1% | 234.5% |
| BULLA | mexc | gate | 43.6% | 40.5% |
| Q | mexc | gate | 25.7% | 83.4% |

Rules and success criteria: `research/preregistrations/RADAR-1.md` on main.
