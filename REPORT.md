# Funding radar: live paper ledger

Updated **2026-10-24 08:00 UTC**, run 394, version `radar-1.0.0`. State from: cache. Quotes this hour: 2400.

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

- days: 16.5
- run_coverage: 0.9924
- closed_positions: 72
- open_positions: 2
- utilisation: 0.102
- rf_apr_pct_declared: 3.875
- book_pnl_pct: -0.7756
- book_excess_pct: -0.8102
- ann_excess_deployed_pct: -177.445
- ann_excess_deployed_costs_x1.5_pct: -317.002
- ann_excess_deployed_costs_x2_pct: -456.56
- best_coin: IOST
- book_excess_without_best_coin_pct: -1.0182
- max_dd_pct: 0.8707
- t_excess_daily: -2.815

## Open positions

| Coin | Short | Long | Opened | Entry spread APR | Funding bp | Basis bp | Cost bp | Net bp |
|---|---|---|---|---|---|---|---|---|
| IOST | mexc | gate | 2026-10-22 10:00 | 374.1% | 98.2 | 24.8 | 17.0 | **106.0** |
| IRYS | mexc | gate | 2026-10-23 22:00 | 221.4% | 18.4 | 31.5 | 17.0 | **32.9** |

## Closed positions (72)

| Coin | Short | Long | Days | Reason | Net bp |
|---|---|---|---|---|---|
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
| BTW | gate | mexc | 0.2 | spread_reversed | -53.5 |
| AGT | mexc | gate | 0.2 | spread_decayed | -44.1 |
| AGT | mexc | gate | 0.0 | spread_decayed | -45.4 |

## Top opportunities this hour (passing the entry rule)

| Coin | Short | Long | 72 h spread APR | Now APR |
|---|---|---|---|---|

Rules and success criteria: `research/preregistrations/RADAR-1.md` on main.
