# Funding radar: live paper ledger

Updated **2026-10-31 13:00 UTC**, run 567, version `radar-1.0.0`. State from: cache. Quotes this hour: 2404.

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

- days: 23.71
- run_coverage: 0.9947
- closed_positions: 126
- open_positions: 7
- utilisation: 0.1601
- rf_apr_pct_declared: 3.875
- book_pnl_pct: -1.2525
- book_excess_pct: -1.3528
- ann_excess_deployed_pct: -131.528
- ann_excess_deployed_costs_x1.5_pct: -242.243
- ann_excess_deployed_costs_x2_pct: -352.959
- best_coin: IOST
- book_excess_without_best_coin_pct: -1.5742
- max_dd_pct: 1.3124
- t_excess_daily: -2.543

## Open positions

| Coin | Short | Long | Opened | Entry spread APR | Funding bp | Basis bp | Cost bp | Net bp |
|---|---|---|---|---|---|---|---|---|
| EVAA | mexc | gate | 2026-10-28 09:00 | 33.0% | 34.6 | 4.6 | 17.0 | **22.2** |
| PARTI | mexc | gate | 2026-10-30 16:00 | 37.3% | 19.5 | -8.1 | 17.0 | **-5.5** |
| PEPE | hyperliquid | mexc | 2026-10-30 18:00 | 27.2% | 13.2 | -14.0 | 16.5 | **-17.3** |
| IDOL | mexc | gate | 2026-10-30 20:00 | 25.0% | 16.5 | -27.8 | 17.0 | **-28.3** |
| HYPE | hyperliquid | gate | 2026-10-31 05:00 | 25.1% | 0.9 | 3.1 | 19.5 | **-15.5** |
| AIN | mexc | gate | 2026-10-31 11:00 | 85.1% | 1.2 | 14.8 | 17.0 | **-1.1** |
| LSK | gate | mexc | 2026-10-31 13:00 | 119.4% | 0.0 | 0.0 | 17.0 | **-17.0** |

## Closed positions (126)

| Coin | Short | Long | Days | Reason | Net bp |
|---|---|---|---|---|---|
| AIN | mexc | gate | 0.1 | spread_reversed | 0.6 |
| XMR | hyperliquid | mexc | 0.4 | spread_reversed | -21.6 |
| Q | mexc | gate | 0.1 | spread_reversed | -9.0 |
| Q | mexc | gate | 1.1 | rebalance | 49.6 |
| TRX | mexc | hyperliquid | 0.5 | spread_reversed | -12.1 |
| XMR | hyperliquid | mexc | 0.2 | spread_reversed | -32.1 |
| BTW | gate | mexc | 2.6 | rebalance | -12.7 |
| XMR | hyperliquid | mexc | 0.3 | spread_reversed | -36.3 |
| Q | mexc | gate | 0.2 | spread_reversed | -52.9 |
| Q | mexc | gate | 0.0 | spread_decayed | -40.6 |
| Q | mexc | gate | 0.0 | spread_decayed | -45.2 |
| Q | mexc | gate | 0.0 | spread_decayed | -30.2 |
| Q | mexc | gate | 0.0 | spread_decayed | 12.3 |
| BULLA | mexc | gate | 0.9 | spread_reversed | 401.5 |
| Q | mexc | gate | 0.0 | spread_reversed | -55.0 |
| AIN | mexc | gate | 1.1 | spread_reversed | 22.4 |
| Q | mexc | gate | 0.2 | spread_reversed | -4.8 |
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

## Top opportunities this hour (passing the entry rule)

| Coin | Short | Long | 72 h spread APR | Now APR |
|---|---|---|---|---|
| LSK | gate | mexc | 119.4% | 532.4% |
| AIN | mexc | gate | 84.0% | 44.9% |
| IDOL | mexc | gate | 45.9% | 55.6% |
| PEPE | hyperliquid | mexc | 43.3% | 90.8% |
| HYPE | hyperliquid | gate | 25.7% | 29.9% |

Rules and success criteria: `research/preregistrations/RADAR-1.md` on main.
