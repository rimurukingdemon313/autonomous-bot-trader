# Funding radar: live paper ledger

Updated **2026-10-24 23:00 UTC**, run 409, version `radar-1.0.0`. State from: cache. Quotes this hour: 2400.

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

- days: 17.12
- run_coverage: 0.9927
- closed_positions: 78
- open_positions: 4
- utilisation: 0.1098
- rf_apr_pct_declared: 3.875
- book_pnl_pct: -0.7991
- book_excess_pct: -0.8528
- ann_excess_deployed_pct: -167.875
- ann_excess_deployed_costs_x1.5_pct: -306.706
- ann_excess_deployed_costs_x2_pct: -445.537
- best_coin: IOST
- book_excess_without_best_coin_pct: -1.0742
- max_dd_pct: 0.8707
- t_excess_daily: -2.978

## Open positions

| Coin | Short | Long | Opened | Entry spread APR | Funding bp | Basis bp | Cost bp | Net bp |
|---|---|---|---|---|---|---|---|---|
| IRYS | mexc | gate | 2026-10-24 16:00 | 253.0% | 9.0 | 25.8 | 17.0 | **17.8** |
| BIRB | mexc | gate | 2026-10-24 18:00 | 131.7% | 10.1 | 31.3 | 17.0 | **24.4** |
| ORDER | mexc | gate | 2026-10-24 21:00 | 42.1% | 12.9 | -7.8 | 17.0 | **-11.9** |
| SOXL | mexc | gate | 2026-10-24 21:00 | 25.7% | 1.6 | -0.0 | 17.0 | **-15.4** |

## Closed positions (78)

| Coin | Short | Long | Days | Reason | Net bp |
|---|---|---|---|---|---|
| IOST | mexc | gate | 2.5 | spread_reversed | 117.2 |
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

## Top opportunities this hour (passing the entry rule)

| Coin | Short | Long | 72 h spread APR | Now APR |
|---|---|---|---|---|
| IRYS | mexc | gate | 262.7% | 79.1% |
| BIRB | mexc | gate | 137.7% | 127.5% |
| ORDER | mexc | gate | 61.8% | 874.2% |
| SOXL | mexc | gate | 27.6% | 55.8% |

Rules and success criteria: `research/preregistrations/RADAR-1.md` on main.
