# Funding radar: live paper ledger

Updated **2026-10-22 23:00 UTC**, run 361, version `radar-1.0.0`. State from: cache. Quotes this hour: 2412.

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

- days: 15.13
- run_coverage: 0.9918
- closed_positions: 64
- open_positions: 2
- utilisation: 0.0942
- rf_apr_pct_declared: 3.875
- book_pnl_pct: -0.6427
- book_excess_pct: -0.6744
- ann_excess_deployed_pct: -174.778
- ann_excess_deployed_costs_x1.5_pct: -322.312
- ann_excess_deployed_costs_x2_pct: -469.845
- best_coin: IOST
- book_excess_without_best_coin_pct: -0.8564
- max_dd_pct: 0.8707
- t_excess_daily: -2.773

## Open positions

| Coin | Short | Long | Opened | Entry spread APR | Funding bp | Basis bp | Cost bp | Net bp |
|---|---|---|---|---|---|---|---|---|
| IOST | mexc | gate | 2026-10-22 10:00 | 374.1% | 30.3 | 37.9 | 17.0 | **51.2** |
| XMR | hyperliquid | mexc | 2026-10-22 20:00 | 25.1% | 0.3 | 4.2 | 16.5 | **-12.0** |

## Closed positions (64)

| Coin | Short | Long | Days | Reason | Net bp |
|---|---|---|---|---|---|
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
| AGT | mexc | gate | 0.0 | spread_decayed | -19.7 |
| SAND | mexc | gate | 0.1 | spread_reversed | -26.7 |
| AGT | mexc | gate | 0.2 | spread_decayed | -22.8 |
| SAND | mexc | gate | 0.2 | spread_reversed | -39.8 |
| SAND | mexc | gate | 0.2 | spread_reversed | -38.0 |
| AGT | mexc | gate | 0.8 | spread_reversed | -5.3 |
| SAND | mexc | gate | 0.0 | spread_reversed | -12.2 |
| AGT | mexc | gate | 0.1 | spread_reversed | -31.8 |

## Top opportunities this hour (passing the entry rule)

| Coin | Short | Long | 72 h spread APR | Now APR |
|---|---|---|---|---|

Rules and success criteria: `research/preregistrations/RADAR-1.md` on main.
