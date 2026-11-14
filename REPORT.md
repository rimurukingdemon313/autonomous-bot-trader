# Funding radar: live paper ledger

Updated **2026-11-14 09:00 UTC**, run 895, version `radar-1.0.0`. State from: cache. Quotes this hour: 2368.

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

- days: 37.54
- run_coverage: 0.9922
- closed_positions: 206
- open_positions: 4
- utilisation: 0.217
- rf_apr_pct_declared: 3.875
- book_pnl_pct: -1.9252
- book_excess_pct: -2.0451
- ann_excess_deployed_pct: -92.253
- ann_excess_deployed_costs_x1.5_pct: -173.741
- ann_excess_deployed_costs_x2_pct: -255.228
- best_coin: INIT
- book_excess_without_best_coin_pct: -2.5128
- max_dd_pct: 2.1986
- t_excess_daily: -3.265

## Open positions

| Coin | Short | Long | Opened | Entry spread APR | Funding bp | Basis bp | Cost bp | Net bp |
|---|---|---|---|---|---|---|---|---|
| PIEVERSE | mexc | gate | 2026-11-09 21:00 | 35.8% | 22.1 | -16.6 | 17.0 | **-11.5** |
| INIT | gate | mexc | 2026-11-12 00:00 | 2438.5% | 540.5 | 93.1 | 17.0 | **616.6** |
| AKE | mexc | gate | 2026-11-14 04:00 | 28.8% | 17.3 | 34.9 | 17.0 | **35.2** |
| BARD | mexc | gate | 2026-11-14 08:00 | 81.6% | 2.1 | -7.8 | 17.0 | **-22.7** |

## Closed positions (206)

| Coin | Short | Long | Days | Reason | Net bp |
|---|---|---|---|---|---|
| ARIA | mexc | gate | 0.8 | spread_decayed | -61.4 |
| BARD | mexc | gate | 0.2 | spread_reversed | -51.5 |
| AGT | mexc | gate | 0.0 | spread_reversed | -25.6 |
| AGT | mexc | gate | 0.1 | spread_reversed | -60.9 |
| AGT | mexc | gate | 0.1 | spread_reversed | -4.7 |
| AGT | mexc | gate | 0.6 | spread_reversed | -6.2 |
| JCT | mexc | gate | 0.0 | spread_decayed | -20.1 |
| JCT | mexc | gate | 0.0 | spread_decayed | -1.6 |
| JCT | mexc | gate | 0.0 | spread_decayed | -61.7 |
| JCT | mexc | gate | 0.0 | spread_decayed | -37.0 |
| INIT | gate | mexc | 0.5 | rebalance | -29.1 |
| JCT | mexc | gate | 0.0 | spread_decayed | -27.0 |
| INIT | hyperliquid | mexc | 0.2 | spread_reversed | 73.6 |
| JCT | mexc | gate | 0.0 | spread_decayed | -67.4 |
| INIT | gate | hyperliquid | 0.1 | spread_reversed | 100.8 |
| JCT | mexc | gate | 0.1 | spread_reversed | -4.8 |
| INIT | gate | hyperliquid | 0.1 | spread_reversed | 101.6 |
| INIT | gate | hyperliquid | 0.0 | spread_reversed | -49.7 |
| JCT | mexc | gate | 0.2 | spread_reversed | -70.2 |
| INIT | gate | hyperliquid | 0.4 | spread_reversed | 146.4 |
| JCT | mexc | gate | 0.3 | spread_reversed | -11.4 |
| PEPE | mexc | hyperliquid | 1.0 | spread_decayed | -30.0 |
| JCT | mexc | gate | 1.2 | rebalance | 82.3 |
| ZEC | gate | mexc | 0.5 | spread_reversed | -39.8 |
| IDOL | mexc | gate | 1.6 | spread_reversed | 29.5 |
| JCT | mexc | gate | 0.2 | rebalance | 38.1 |
| AKE | mexc | gate | 1.2 | spread_reversed | -32.0 |
| SOL | dydx | gate | 3.1 | spread_decayed | -22.9 |
| UAI | mexc | gate | 0.8 | spread_reversed | -26.5 |
| SOXL | mexc | gate | 0.2 | spread_decayed | -49.4 |

## Top opportunities this hour (passing the entry rule)

| Coin | Short | Long | 72 h spread APR | Now APR |
|---|---|---|---|---|
| BARD | mexc | gate | 86.4% | 153.7% |
| AKE | mexc | gate | 56.6% | 1304.8% |

Rules and success criteria: `research/preregistrations/RADAR-1.md` on main.
