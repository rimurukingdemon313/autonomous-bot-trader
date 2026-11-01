# Funding radar: live paper ledger

Updated **2026-11-01 00:00 UTC**, run 578, version `radar-1.0.0`. State from: cache. Quotes this hour: 2404.

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

- days: 24.17
- run_coverage: 0.9948
- closed_positions: 133
- open_positions: 5
- utilisation: 0.1696
- rf_apr_pct_declared: 3.875
- book_pnl_pct: -1.3512
- book_excess_pct: -1.4379
- ann_excess_deployed_pct: -129.187
- ann_excess_deployed_costs_x1.5_pct: -235.767
- ann_excess_deployed_costs_x2_pct: -342.347
- best_coin: IOST
- book_excess_without_best_coin_pct: -1.6593
- max_dd_pct: 1.3512
- t_excess_daily: -2.787

## Open positions

| Coin | Short | Long | Opened | Entry spread APR | Funding bp | Basis bp | Cost bp | Net bp |
|---|---|---|---|---|---|---|---|---|
| EVAA | mexc | gate | 2026-10-28 09:00 | 33.0% | 41.7 | 5.4 | 17.0 | **30.1** |
| PARTI | mexc | gate | 2026-10-30 16:00 | 37.3% | 20.8 | -7.8 | 17.0 | **-4.0** |
| PEPE | hyperliquid | mexc | 2026-10-30 18:00 | 27.2% | 25.5 | 6.8 | 16.5 | **15.8** |
| HYPE | hyperliquid | gate | 2026-10-31 05:00 | 25.1% | 5.1 | -1.9 | 19.5 | **-16.2** |
| AIN | mexc | gate | 2026-10-31 23:00 | 73.2% | 0.2 | -3.7 | 17.0 | **-20.5** |

## Closed positions (133)

| Coin | Short | Long | Days | Reason | Net bp |
|---|---|---|---|---|---|
| TRX | gate | hyperliquid | 0.0 | spread_decayed | -48.5 |
| LSK | gate | mexc | 0.5 | spread_reversed | -58.5 |
| IDOL | mexc | gate | 1.2 | spread_reversed | -9.4 |
| TRX | gate | hyperliquid | 0.0 | spread_decayed | -34.6 |
| TRX | gate | hyperliquid | 0.0 | spread_decayed | -41.6 |
| TRX | gate | hyperliquid | 0.0 | spread_decayed | -38.8 |
| AIN | mexc | gate | 0.2 | spread_reversed | -33.8 |
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

## Top opportunities this hour (passing the entry rule)

| Coin | Short | Long | 72 h spread APR | Now APR |
|---|---|---|---|---|
| PEPE | hyperliquid | mexc | 58.8% | 74.5% |

Rules and success criteria: `research/preregistrations/RADAR-1.md` on main.
