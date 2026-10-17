# Funding radar: live paper ledger

Updated **2026-10-17 22:00 UTC**, run 240, version `radar-1.0.0`. State from: cache. Quotes this hour: 2384.

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

- days: 10.08
- run_coverage: 0.9877
- closed_positions: 32
- open_positions: 1
- utilisation: 0.0933
- rf_apr_pct_declared: 3.875
- book_pnl_pct: -0.3344
- book_excess_pct: -0.3528
- ann_excess_deployed_pct: -138.57
- ann_excess_deployed_costs_x1.5_pct: -251.605
- ann_excess_deployed_costs_x2_pct: -364.64
- best_coin: RSR
- book_excess_without_best_coin_pct: -0.3811
- max_dd_pct: 0.3433
- t_excess_daily: -1.6

## Open positions

| Coin | Short | Long | Opened | Entry spread APR | Funding bp | Basis bp | Cost bp | Net bp |
|---|---|---|---|---|---|---|---|---|
| AGT | mexc | gate | 2026-10-17 21:00 | 50.6% | 0.3 | 8.6 | 17.0 | **-8.1** |

## Closed positions (32)

| Coin | Short | Long | Days | Reason | Net bp |
|---|---|---|---|---|---|
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
| RLC | mexc | gate | 0.0 | spread_decayed | -56.7 |
| RLC | mexc | gate | 0.0 | spread_decayed | -19.4 |
| RLC | mexc | gate | 0.0 | spread_decayed | -31.7 |
| MAGIC | mexc | gate | 0.4 | spread_reversed | -36.4 |

## Top opportunities this hour (passing the entry rule)

| Coin | Short | Long | 72 h spread APR | Now APR |
|---|---|---|---|---|
| AGT | mexc | gate | 50.6% | 23.0% |

Rules and success criteria: `research/preregistrations/RADAR-1.md` on main.
