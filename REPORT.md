# Funding radar: live paper ledger

Updated **2026-10-24 14:00 UTC**, run 400, version `radar-1.0.0`. State from: cache. Quotes this hour: 2400.

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

- days: 16.75
- run_coverage: 0.9926
- closed_positions: 75
- open_positions: 2
- utilisation: 0.1048
- rf_apr_pct_declared: 3.875
- book_pnl_pct: -0.7602
- book_excess_pct: -0.7956
- ann_excess_deployed_pct: -167.137
- ann_excess_deployed_costs_x1.5_pct: -306.362
- ann_excess_deployed_costs_x2_pct: -445.587
- best_coin: IOST
- book_excess_without_best_coin_pct: -1.0195
- max_dd_pct: 0.8707
- t_excess_daily: -2.717

## Open positions

| Coin | Short | Long | Opened | Entry spread APR | Funding bp | Basis bp | Cost bp | Net bp |
|---|---|---|---|---|---|---|---|---|
| IOST | mexc | gate | 2026-10-22 10:00 | 374.1% | 110.1 | 45.2 | 17.0 | **138.2** |
| BIRB | mexc | gate | 2026-10-24 14:00 | 99.6% | 0.0 | 0.0 | 17.0 | **-17.0** |

## Closed positions (75)

| Coin | Short | Long | Days | Reason | Net bp |
|---|---|---|---|---|---|
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
| BTW | gate | mexc | 0.2 | spread_reversed | -51.0 |
| AGT | mexc | gate | 0.0 | spread_reversed | -15.9 |

## Top opportunities this hour (passing the entry rule)

| Coin | Short | Long | 72 h spread APR | Now APR |
|---|---|---|---|---|
| BIRB | mexc | gate | 99.6% | 127.2% |

Rules and success criteria: `research/preregistrations/RADAR-1.md` on main.
