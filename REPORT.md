# Funding radar: live paper ledger

Updated **2026-10-29 23:00 UTC**, run 529, version `radar-1.0.0`. State from: cache. Quotes this hour: 2396.

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

- days: 22.12
- run_coverage: 0.9944
- closed_positions: 118
- open_positions: 3
- utilisation: 0.1367
- rf_apr_pct_declared: 3.875
- book_pnl_pct: -1.2095
- book_excess_pct: -1.2666
- ann_excess_deployed_pct: -154.107
- ann_excess_deployed_costs_x1.5_pct: -280.214
- ann_excess_deployed_costs_x2_pct: -406.322
- best_coin: IOST
- book_excess_without_best_coin_pct: -1.488
- max_dd_pct: 1.3124
- t_excess_daily: -2.485

## Open positions

| Coin | Short | Long | Opened | Entry spread APR | Funding bp | Basis bp | Cost bp | Net bp |
|---|---|---|---|---|---|---|---|---|
| BTW | gate | mexc | 2026-10-27 23:00 | 56.0% | 12.2 | -20.2 | 17.0 | **-25.0** |
| EVAA | mexc | gate | 2026-10-28 09:00 | 33.0% | 19.6 | 3.0 | 17.0 | **5.6** |
| XMR | hyperliquid | mexc | 2026-10-29 21:00 | 28.3% | 3.6 | -18.1 | 16.5 | **-31.0** |

## Closed positions (118)

| Coin | Short | Long | Days | Reason | Net bp |
|---|---|---|---|---|---|
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
| IRYS | mexc | gate | 0.2 | spread_reversed | -41.8 |
| BTW | gate | mexc | 0.0 | spread_decayed | -26.9 |
| IRYS | mexc | gate | 0.2 | spread_reversed | -44.2 |

## Top opportunities this hour (passing the entry rule)

| Coin | Short | Long | 72 h spread APR | Now APR |
|---|---|---|---|---|
| EVAA | mexc | gate | 56.9% | 30.4% |
| XMR | hyperliquid | mexc | 31.6% | 95.4% |

Rules and success criteria: `research/preregistrations/RADAR-1.md` on main.
