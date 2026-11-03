# Funding radar: live paper ledger

Updated **2026-11-03 14:00 UTC**, run 640, version `radar-1.0.0`. State from: cache. Quotes this hour: 2399.

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

- days: 26.75
- run_coverage: 0.9953
- closed_positions: 149
- open_positions: 2
- utilisation: 0.1856
- rf_apr_pct_declared: 3.875
- book_pnl_pct: -1.6245
- book_excess_pct: -1.6939
- ann_excess_deployed_pct: -125.117
- ann_excess_deployed_costs_x1.5_pct: -220.972
- ann_excess_deployed_costs_x2_pct: -316.826
- best_coin: IOST
- book_excess_without_best_coin_pct: -1.9154
- max_dd_pct: 1.6245
- t_excess_daily: -3.183

## Open positions

| Coin | Short | Long | Opened | Entry spread APR | Funding bp | Basis bp | Cost bp | Net bp |
|---|---|---|---|---|---|---|---|---|
| AIN | mexc | gate | 2026-11-01 08:00 | 68.9% | 48.1 | 9.1 | 17.0 | **40.1** |
| SOXL | mexc | gate | 2026-11-03 08:00 | 25.1% | 3.4 | -3.1 | 17.0 | **-16.7** |

## Closed positions (149)

| Coin | Short | Long | Days | Reason | Net bp |
|---|---|---|---|---|---|
| AKE | mexc | gate | 0.2 | spread_reversed | -57.1 |
| AKE | mexc | gate | 0.1 | spread_reversed | -107.5 |
| HYPE | hyperliquid | gate | 3.0 | spread_decayed | -24.4 |
| AKE | mexc | gate | 0.1 | spread_reversed | -79.8 |
| ZRO | hyperliquid | mexc | 1.0 | spread_decayed | -27.7 |
| ESPORTS | mexc | gate | 0.1 | spread_reversed | -0.9 |
| ESPORTS | mexc | gate | 0.1 | spread_reversed | 15.5 |
| XPL | hyperliquid | gate | 0.8 | spread_decayed | -31.4 |
| PARTI | mexc | gate | 2.0 | spread_decayed | -16.1 |
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

## Top opportunities this hour (passing the entry rule)

| Coin | Short | Long | 72 h spread APR | Now APR |
|---|---|---|---|---|
| SOXL | mexc | gate | 29.2% | 33.3% |

Rules and success criteria: `research/preregistrations/RADAR-1.md` on main.
