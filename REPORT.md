# Funding radar: live paper ledger

Updated **2026-11-01 12:00 UTC**, run 590, version `radar-1.0.0`. State from: cache. Quotes this hour: 2404.

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

- days: 24.67
- run_coverage: 0.9949
- closed_positions: 140
- open_positions: 4
- utilisation: 0.1759
- rf_apr_pct_declared: 3.875
- book_pnl_pct: -1.4932
- book_excess_pct: -1.5754
- ann_excess_deployed_pct: -133.467
- ann_excess_deployed_costs_x1.5_pct: -238.392
- ann_excess_deployed_costs_x2_pct: -343.317
- best_coin: IOST
- book_excess_without_best_coin_pct: -1.7968
- max_dd_pct: 1.4986
- t_excess_daily: -2.989

## Open positions

| Coin | Short | Long | Opened | Entry spread APR | Funding bp | Basis bp | Cost bp | Net bp |
|---|---|---|---|---|---|---|---|---|
| PARTI | mexc | gate | 2026-10-30 16:00 | 37.3% | 21.3 | -9.7 | 17.0 | **-5.4** |
| HYPE | hyperliquid | gate | 2026-10-31 05:00 | 25.1% | 6.4 | -4.0 | 19.5 | **-17.1** |
| AIN | mexc | gate | 2026-11-01 08:00 | 68.9% | 4.0 | 5.8 | 17.0 | **-7.3** |
| XPL | hyperliquid | gate | 2026-11-01 08:00 | 31.5% | 0.1 | 5.7 | 19.5 | **-13.7** |

## Closed positions (140)

| Coin | Short | Long | Days | Reason | Net bp |
|---|---|---|---|---|---|
| PEPE | hyperliquid | mexc | 1.7 | spread_reversed | -10.8 |
| AIN | mexc | gate | 0.0 | spread_decayed | -17.4 |
| AIN | mexc | gate | 0.0 | spread_decayed | -24.0 |
| EVAA | mexc | gate | 3.9 | rebalance | 1.2 |
| AIN | mexc | gate | 0.0 | spread_decayed | -50.1 |
| LSK | gate | mexc | 0.2 | spread_reversed | -73.0 |
| AIN | mexc | gate | 0.1 | spread_reversed | -61.2 |
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

## Top opportunities this hour (passing the entry rule)

| Coin | Short | Long | 72 h spread APR | Now APR |
|---|---|---|---|---|
| AIN | mexc | gate | 71.0% | 72.5% |

Rules and success criteria: `research/preregistrations/RADAR-1.md` on main.
