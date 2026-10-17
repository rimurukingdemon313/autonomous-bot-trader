# Funding radar: live paper ledger

Updated **2026-10-17 00:00 UTC**, run 218, version `radar-1.0.0`. State from: cache. Quotes this hour: 2384.

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

- days: 9.17
- run_coverage: 0.9864
- closed_positions: 25
- open_positions: 3
- utilisation: 0.0784
- rf_apr_pct_declared: 3.875
- book_pnl_pct: -0.2029
- book_excess_pct: -0.2359
- ann_excess_deployed_pct: -122.992
- ann_excess_deployed_costs_x1.5_pct: -250.872
- ann_excess_deployed_costs_x2_pct: -378.753
- best_coin: AGT
- book_excess_without_best_coin_pct: -0.3219
- max_dd_pct: 0.3433
- t_excess_daily: -1.212

## Open positions

| Coin | Short | Long | Opened | Entry spread APR | Funding bp | Basis bp | Cost bp | Net bp |
|---|---|---|---|---|---|---|---|---|
| KORU | mexc | gate | 2026-10-15 00:00 | 25.6% | 15.7 | -6.0 | 17.0 | **-7.3** |
| AGT | mexc | gate | 2026-10-17 00:00 | 34.4% | 0.0 | 0.0 | 17.0 | **-17.0** |
| SOXL | mexc | gate | 2026-10-17 00:00 | 25.1% | 0.0 | 0.0 | 17.0 | **-17.0** |

## Closed positions (25)

| Coin | Short | Long | Days | Reason | Net bp |
|---|---|---|---|---|---|
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
| RLC | mexc | gate | 0.0 | spread_decayed | -56.7 |
| RLC | mexc | gate | 0.0 | spread_decayed | -19.4 |
| RLC | mexc | gate | 0.0 | spread_decayed | -31.7 |
| MAGIC | mexc | gate | 0.4 | spread_reversed | -36.4 |
| RLC | mexc | gate | 0.0 | spread_reversed | -49.9 |
| RLC | mexc | gate | 0.0 | spread_decayed | -21.0 |

## Top opportunities this hour (passing the entry rule)

| Coin | Short | Long | 72 h spread APR | Now APR |
|---|---|---|---|---|
| AGT | mexc | gate | 34.4% | 112.1% |
| KORU | mexc | gate | 29.9% | 60.6% |
| SOXL | mexc | gate | 25.1% | 64.8% |

Rules and success criteria: `research/preregistrations/RADAR-1.md` on main.
