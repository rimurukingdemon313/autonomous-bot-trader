# Funding radar: live paper ledger

Updated **2026-10-31 22:00 UTC**, run 576, version `radar-1.0.0`. State from: cache. Quotes this hour: 2404.

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

- days: 24.08
- run_coverage: 0.9948
- closed_positions: 129
- open_positions: 7
- utilisation: 0.1679
- rf_apr_pct_declared: 3.875
- book_pnl_pct: -1.2882
- book_excess_pct: -1.3924
- ann_excess_deployed_pct: -127.06
- ann_excess_deployed_costs_x1.5_pct: -233.64
- ann_excess_deployed_costs_x2_pct: -340.22
- best_coin: IOST
- book_excess_without_best_coin_pct: -1.6138
- max_dd_pct: 1.3124
- t_excess_daily: -2.648

## Open positions

| Coin | Short | Long | Opened | Entry spread APR | Funding bp | Basis bp | Cost bp | Net bp |
|---|---|---|---|---|---|---|---|---|
| EVAA | mexc | gate | 2026-10-28 09:00 | 33.0% | 39.9 | 13.1 | 17.0 | **36.0** |
| PARTI | mexc | gate | 2026-10-30 16:00 | 37.3% | 20.7 | -7.6 | 17.0 | **-3.9** |
| PEPE | hyperliquid | mexc | 2026-10-30 18:00 | 27.2% | 23.8 | 8.7 | 16.5 | **16.0** |
| IDOL | mexc | gate | 2026-10-30 20:00 | 25.0% | 19.3 | -13.4 | 17.0 | **-11.2** |
| HYPE | hyperliquid | gate | 2026-10-31 05:00 | 25.1% | 5.0 | -4.0 | 19.5 | **-18.6** |
| LSK | gate | mexc | 2026-10-31 13:00 | 119.4% | 12.2 | -13.9 | 17.0 | **-18.7** |
| TRX | gate | hyperliquid | 2026-10-31 22:00 | 26.8% | 0.0 | 0.0 | 19.5 | **-19.5** |

## Closed positions (129)

| Coin | Short | Long | Days | Reason | Net bp |
|---|---|---|---|---|---|
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
| BTW | gate | mexc | 0.6 | rebalance | -76.3 |
| BULLA | mexc | gate | 0.1 | spread_reversed | -118.9 |
| BULLA | mexc | gate | 0.0 | rebalance | 130.4 |
| BULLA | mexc | gate | 0.1 | spread_reversed | -83.2 |

## Top opportunities this hour (passing the entry rule)

| Coin | Short | Long | 72 h spread APR | Now APR |
|---|---|---|---|---|
| LSK | gate | mexc | 131.3% | 86.9% |
| PEPE | hyperliquid | mexc | 56.7% | 67.3% |
| HYPE | hyperliquid | gate | 30.2% | 21.6% |
| TRX | gate | hyperliquid | 26.8% | 31.7% |

Rules and success criteria: `research/preregistrations/RADAR-1.md` on main.
