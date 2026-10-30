# Funding radar: live paper ledger

Updated **2026-10-30 20:00 UTC**, run 550, version `radar-1.0.0`. State from: cache. Quotes this hour: 2405.

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

- days: 23.0
- run_coverage: 0.9946
- closed_positions: 121
- open_positions: 7
- utilisation: 0.1467
- rf_apr_pct_declared: 3.875
- book_pnl_pct: -1.2429
- book_excess_pct: -1.3371
- ann_excess_deployed_pct: -146.409
- ann_excess_deployed_costs_x1.5_pct: -266.312
- ann_excess_deployed_costs_x2_pct: -386.214
- best_coin: IOST
- book_excess_without_best_coin_pct: -1.5585
- max_dd_pct: 1.3124
- t_excess_daily: -2.559

## Open positions

| Coin | Short | Long | Opened | Entry spread APR | Funding bp | Basis bp | Cost bp | Net bp |
|---|---|---|---|---|---|---|---|---|
| EVAA | mexc | gate | 2026-10-28 09:00 | 33.0% | 29.3 | 1.4 | 17.0 | **13.7** |
| Q | mexc | gate | 2026-10-30 00:00 | 25.6% | 16.0 | 5.9 | 17.0 | **4.9** |
| TRX | mexc | hyperliquid | 2026-10-30 11:00 | 28.6% | 19.3 | 10.6 | 16.5 | **13.5** |
| PARTI | mexc | gate | 2026-10-30 16:00 | 37.3% | 4.1 | -6.6 | 17.0 | **-19.5** |
| PEPE | hyperliquid | mexc | 2026-10-30 18:00 | 27.2% | 3.7 | -2.5 | 16.5 | **-15.2** |
| XMR | hyperliquid | mexc | 2026-10-30 20:00 | 32.8% | 0.0 | 0.0 | 16.5 | **-16.5** |
| IDOL | mexc | gate | 2026-10-30 20:00 | 25.0% | 0.0 | 0.0 | 17.0 | **-17.0** |

## Closed positions (121)

| Coin | Short | Long | Days | Reason | Net bp |
|---|---|---|---|---|---|
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
| BTW | mexc | gate | 0.1 | spread_decayed | -39.7 |
| IRYS | mexc | gate | 0.0 | spread_reversed | -48.1 |
| IRYS | mexc | gate | 0.5 | spread_reversed | 3.4 |
| BTW | gate | mexc | 0.0 | spread_decayed | -51.9 |
| BTW | gate | mexc | 0.0 | spread_decayed | -28.5 |

## Top opportunities this hour (passing the entry rule)

| Coin | Short | Long | 72 h spread APR | Now APR |
|---|---|---|---|---|
| TRX | mexc | hyperliquid | 48.7% | 52.0% |
| XMR | hyperliquid | mexc | 32.8% | 44.3% |
| PEPE | hyperliquid | mexc | 31.2% | 134.8% |
| Q | mexc | gate | 30.9% | 100.3% |
| IDOL | mexc | gate | 25.0% | 166.4% |

Rules and success criteria: `research/preregistrations/RADAR-1.md` on main.
