# Funding radar: live paper ledger

Updated **2026-10-31 16:00 UTC**, run 570, version `radar-1.0.0`. State from: cache. Quotes this hour: 2404.

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

- days: 23.83
- run_coverage: 0.9948
- closed_positions: 127
- open_positions: 6
- utilisation: 0.1628
- rf_apr_pct_declared: 3.875
- book_pnl_pct: -1.2494
- book_excess_pct: -1.3422
- ann_excess_deployed_pct: -127.527
- ann_excess_deployed_costs_x1.5_pct: -235.72
- ann_excess_deployed_costs_x2_pct: -343.914
- best_coin: IOST
- book_excess_without_best_coin_pct: -1.5636
- max_dd_pct: 1.3124
- t_excess_daily: -2.537

## Open positions

| Coin | Short | Long | Opened | Entry spread APR | Funding bp | Basis bp | Cost bp | Net bp |
|---|---|---|---|---|---|---|---|---|
| EVAA | mexc | gate | 2026-10-28 09:00 | 33.0% | 35.8 | -0.0 | 17.0 | **18.8** |
| PARTI | mexc | gate | 2026-10-30 16:00 | 37.3% | 20.1 | -6.1 | 17.0 | **-3.1** |
| PEPE | hyperliquid | mexc | 2026-10-30 18:00 | 27.2% | 16.5 | 2.7 | 16.5 | **2.7** |
| IDOL | mexc | gate | 2026-10-30 20:00 | 25.0% | 17.8 | -15.8 | 17.0 | **-15.1** |
| HYPE | hyperliquid | gate | 2026-10-31 05:00 | 25.1% | 2.1 | -6.5 | 19.5 | **-23.9** |
| LSK | gate | mexc | 2026-10-31 13:00 | 119.4% | 5.8 | 9.0 | 17.0 | **-2.1** |

## Closed positions (127)

| Coin | Short | Long | Days | Reason | Net bp |
|---|---|---|---|---|---|
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
| BTW | gate | mexc | 0.6 | rebalance | -76.3 |
| BULLA | mexc | gate | 0.1 | spread_reversed | -118.9 |
| BULLA | mexc | gate | 0.0 | rebalance | 130.4 |
| BULLA | mexc | gate | 0.1 | spread_reversed | -83.2 |
| BULLA | mexc | gate | 0.1 | rebalance | 15.8 |
| BTW | gate | mexc | 0.5 | rebalance | 7.9 |

## Top opportunities this hour (passing the entry rule)

| Coin | Short | Long | 72 h spread APR | Now APR |
|---|---|---|---|---|
| LSK | gate | mexc | 124.0% | 182.6% |
| PEPE | hyperliquid | mexc | 47.8% | 91.1% |
| IDOL | mexc | gate | 47.5% | 23.9% |
| HYPE | hyperliquid | gate | 27.2% | 68.2% |

Rules and success criteria: `research/preregistrations/RADAR-1.md` on main.
