# Funding radar: live paper ledger

Updated **2026-10-15 06:00 UTC**, run 176, version `radar-1.0.0`. State from: cache. Quotes this hour: 2384.

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

- days: 7.42
- run_coverage: 0.9832
- closed_positions: 20
- open_positions: 2
- utilisation: 0.0665
- rf_apr_pct_declared: 3.875
- book_pnl_pct: -0.2554
- book_excess_pct: -0.2775
- ann_excess_deployed_pct: -211.367
- ann_excess_deployed_costs_x1.5_pct: -359.335
- ann_excess_deployed_costs_x2_pct: -507.303
- best_coin: RSR
- book_excess_without_best_coin_pct: -0.3058
- max_dd_pct: 0.277
- t_excess_daily: -2.259

## Open positions

| Coin | Short | Long | Opened | Entry spread APR | Funding bp | Basis bp | Cost bp | Net bp |
|---|---|---|---|---|---|---|---|---|
| KORU | mexc | gate | 2026-10-15 00:00 | 25.6% | 5.9 | -2.7 | 17.0 | **-13.7** |
| WAL | mexc | gate | 2026-10-15 05:00 | 59.2% | 1.3 | 18.4 | 17.0 | **2.7** |

## Closed positions (20)

| Coin | Short | Long | Days | Reason | Net bp |
|---|---|---|---|---|---|
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
| WAL | mexc | gate | 60.3% | 132.9% |
| KORU | mexc | gate | 30.1% | 82.9% |

Rules and success criteria: `research/preregistrations/RADAR-1.md` on main.
