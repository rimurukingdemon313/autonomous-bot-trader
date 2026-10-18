# Funding radar: live paper ledger

Updated **2026-10-18 23:00 UTC**, run 265, version `radar-1.0.0`. State from: cache. Quotes this hour: 2385.

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

- days: 11.12
- run_coverage: 0.9888
- closed_positions: 36
- open_positions: 1
- utilisation: 0.094
- rf_apr_pct_declared: 3.875
- book_pnl_pct: -0.3896
- book_excess_pct: -0.409
- ann_excess_deployed_pct: -144.486
- ann_excess_deployed_costs_x1.5_pct: -258.137
- ann_excess_deployed_costs_x2_pct: -371.787
- best_coin: RSR
- book_excess_without_best_coin_pct: -0.4374
- max_dd_pct: 0.4059
- t_excess_daily: -1.86

## Open positions

| Coin | Short | Long | Opened | Entry spread APR | Funding bp | Basis bp | Cost bp | Net bp |
|---|---|---|---|---|---|---|---|---|
| AGT | mexc | gate | 2026-10-18 09:00 | 53.6% | 6.3 | 7.9 | 17.0 | **-2.9** |

## Closed positions (36)

| Coin | Short | Long | Days | Reason | Net bp |
|---|---|---|---|---|---|
| SAND | mexc | gate | 0.0 | spread_reversed | -12.2 |
| AGT | mexc | gate | 0.1 | spread_reversed | -31.8 |
| ICNT | mexc | gate | 0.2 | spread_reversed | -50.0 |
| AGT | mexc | gate | 0.2 | spread_reversed | -21.7 |
| ICNT | mexc | gate | 0.1 | spread_reversed | -34.4 |
| AGT | mexc | gate | 0.5 | spread_reversed | 62.9 |
| SOXL | mexc | gate | 0.7 | spread_reversed | -37.4 |
| KORU | mexc | gate | 2.7 | spread_reversed | -19.8 |
| AGT | mexc | gate | 0.2 | rebalance | -87.9 |
| AGT | mexc | gate | 0.1 | rebalance | -60.4 |
| AGT | mexc | gate | 0.0 | spread_reversed | -119.1 |
| AGT | mexc | gate | 0.0 | rebalance | 297.5 |
| AGT | mexc | gate | 0.2 | rebalance | -90.9 |
| WAL | mexc | gate | 0.0 | spread_reversed | -25.0 |
| WAL | mexc | gate | 0.0 | spread_reversed | -30.4 |
| WAL | mexc | gate | 0.1 | spread_reversed | -16.0 |
| WAL | mexc | gate | 0.2 | spread_reversed | -20.2 |
| WAL | mexc | gate | 0.0 | spread_reversed | -52.0 |
| W | hyperliquid | gate | 0.0 | spread_decayed | -56.8 |
| W | hyperliquid | gate | 0.0 | spread_decayed | -33.7 |
| RSR | gate | hyperliquid | 0.5 | spread_reversed | 45.8 |
| W | hyperliquid | mexc | 0.2 | spread_decayed | -51.6 |
| W | hyperliquid | gate | 0.2 | spread_reversed | -51.2 |
| RSR | mexc | gate | 0.2 | spread_reversed | 7.7 |
| W | hyperliquid | gate | 0.5 | spread_reversed | 34.7 |
| STRK | hyperliquid | gate | 1.0 | rebalance | -20.5 |
| RSR | mexc | gate | 0.0 | spread_reversed | 4.7 |
| RLC | mexc | gate | 0.2 | spread_reversed | -49.3 |
| RLC | mexc | gate | 0.6 | spread_reversed | -26.0 |
| RLC | mexc | gate | 0.0 | spread_decayed | -16.3 |

## Top opportunities this hour (passing the entry rule)

| Coin | Short | Long | 72 h spread APR | Now APR |
|---|---|---|---|---|
| AGT | mexc | gate | 54.4% | 39.6% |

Rules and success criteria: `research/preregistrations/RADAR-1.md` on main.
