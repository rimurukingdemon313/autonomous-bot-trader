# Funding radar: live paper ledger

Updated **2026-10-24 22:00 UTC**, run 408, version `radar-1.0.0`. State from: cache. Quotes this hour: 2400.

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

- days: 17.08
- run_coverage: 0.9927
- closed_positions: 77
- open_positions: 5
- utilisation: 0.1091
- rf_apr_pct_declared: 3.875
- book_pnl_pct: -0.8283
- book_excess_pct: -0.8903
- ann_excess_deployed_pct: -177.247
- ann_excess_deployed_costs_x1.5_pct: -317.655
- ann_excess_deployed_costs_x2_pct: -458.064
- best_coin: IOST
- book_excess_without_best_coin_pct: -1.1027
- max_dd_pct: 0.8707
- t_excess_daily: -3.141

## Open positions

| Coin | Short | Long | Opened | Entry spread APR | Funding bp | Basis bp | Cost bp | Net bp |
|---|---|---|---|---|---|---|---|---|
| IOST | mexc | gate | 2026-10-22 10:00 | 374.1% | 124.9 | 8.2 | 17.0 | **116.1** |
| IRYS | mexc | gate | 2026-10-24 16:00 | 253.0% | 8.1 | 34.9 | 17.0 | **26.0** |
| BIRB | mexc | gate | 2026-10-24 18:00 | 131.7% | 8.4 | 19.7 | 17.0 | **11.1** |
| ORDER | mexc | gate | 2026-10-24 21:00 | 42.1% | 4.8 | -47.6 | 17.0 | **-59.7** |
| SOXL | mexc | gate | 2026-10-24 21:00 | 25.7% | 0.9 | -3.6 | 17.0 | **-19.7** |

## Closed positions (77)

| Coin | Short | Long | Days | Reason | Net bp |
|---|---|---|---|---|---|
| ORDER | mexc | gate | 0.0 | spread_reversed | -5.1 |
| BIRB | mexc | gate | 0.1 | spread_reversed | -83.8 |
| IRYS | mexc | gate | 0.2 | spread_reversed | 42.6 |
| BIRB | mexc | gate | 0.2 | rebalance | 26.8 |
| IRYS | mexc | gate | 0.5 | rebalance | -20.9 |
| BTW | mexc | gate | 0.0 | spread_reversed | -43.0 |
| BTW | mexc | gate | 0.0 | spread_decayed | -46.0 |
| IRYS | mexc | gate | 0.1 | rebalance | -51.9 |
| BTW | mexc | gate | 0.0 | spread_decayed | -67.2 |
| BTW | mexc | gate | 0.1 | spread_decayed | -32.3 |
| IRYS | mexc | gate | 0.0 | spread_reversed | -84.2 |
| IRYS | mexc | gate | 0.1 | rebalance | -17.0 |
| XMR | hyperliquid | mexc | 0.5 | spread_reversed | -24.0 |
| BTW | mexc | gate | 0.1 | rebalance | 3.4 |
| ALT | gate | hyperliquid | 0.0 | spread_reversed | -42.4 |
| IOST | mexc | gate | 0.3 | spread_reversed | 18.2 |
| IOST | mexc | gate | 0.2 | rebalance | 427.2 |
| BTW | gate | mexc | 0.0 | spread_decayed | 4.1 |
| BTW | gate | mexc | 0.0 | spread_decayed | -81.1 |
| IOST | mexc | gate | 0.0 | rebalance | -113.1 |
| SOXL | mexc | gate | 0.0 | spread_decayed | -33.9 |
| SOXL | mexc | gate | 0.0 | spread_decayed | -34.6 |
| SOXL | mexc | gate | 0.0 | spread_decayed | -31.8 |
| SOXL | mexc | gate | 0.0 | spread_decayed | -38.6 |
| SOXL | mexc | gate | 0.0 | spread_decayed | -29.5 |
| SOXL | mexc | gate | 0.0 | spread_decayed | -32.4 |
| BTW | gate | mexc | 0.1 | spread_decayed | -67.8 |
| SOXL | mexc | gate | 0.0 | spread_decayed | -31.5 |
| BTW | gate | mexc | 0.1 | spread_reversed | -58.2 |
| BTW | gate | mexc | 0.1 | spread_reversed | -44.0 |

## Top opportunities this hour (passing the entry rule)

| Coin | Short | Long | 72 h spread APR | Now APR |
|---|---|---|---|---|
| IRYS | mexc | gate | 261.8% | 82.6% |
| BIRB | mexc | gate | 138.5% | 169.9% |
| ORDER | mexc | gate | 49.7% | 544.0% |
| SOXL | mexc | gate | 26.8% | 75.1% |

Rules and success criteria: `research/preregistrations/RADAR-1.md` on main.
