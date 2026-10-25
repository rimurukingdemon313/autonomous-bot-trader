# Funding radar: live paper ledger

Updated **2026-10-25 07:00 UTC**, run 417, version `radar-1.0.0`. State from: cache. Quotes this hour: 2392.

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

- days: 17.46
- run_coverage: 0.9929
- closed_positions: 84
- open_positions: 1
- utilisation: 0.1127
- rf_apr_pct_declared: 3.875
- book_pnl_pct: -0.9252
- book_excess_pct: -0.9544
- ann_excess_deployed_pct: -178.272
- ann_excess_deployed_costs_x1.5_pct: -314.761
- ann_excess_deployed_costs_x2_pct: -451.251
- best_coin: IOST
- book_excess_without_best_coin_pct: -1.1759
- max_dd_pct: 0.9252
- t_excess_daily: -3.312

## Open positions

| Coin | Short | Long | Opened | Entry spread APR | Funding bp | Basis bp | Cost bp | Net bp |
|---|---|---|---|---|---|---|---|---|
| ORDER | mexc | gate | 2026-10-25 02:00 | 72.0% | 28.8 | -1.3 | 17.0 | **10.5** |

## Closed positions (84)

| Coin | Short | Long | Days | Reason | Net bp |
|---|---|---|---|---|---|
| SOXL | mexc | gate | 0.4 | spread_reversed | -35.8 |
| IRYS | mexc | gate | 0.0 | spread_reversed | -72.6 |
| IRYS | mexc | gate | 0.1 | spread_reversed | -88.7 |
| BIRB | mexc | gate | 0.3 | spread_reversed | -3.1 |
| ORDER | mexc | gate | 0.2 | spread_reversed | -52.1 |
| IRYS | mexc | gate | 0.4 | rebalance | 4.7 |
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

## Top opportunities this hour (passing the entry rule)

| Coin | Short | Long | 72 h spread APR | Now APR |
|---|---|---|---|---|
| ORDER | mexc | gate | 107.6% | 224.3% |

Rules and success criteria: `research/preregistrations/RADAR-1.md` on main.
