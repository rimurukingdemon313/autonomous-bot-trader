# Funding radar: live paper ledger

Updated **2026-11-11 16:00 UTC**, run 830, version `radar-1.0.0`. State from: cache. Quotes this hour: 2429.

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

- days: 34.83
- run_coverage: 0.9916
- closed_positions: 195
- open_positions: 2
- utilisation: 0.2113
- rf_apr_pct_declared: 3.875
- book_pnl_pct: -2.1196
- book_excess_pct: -2.2143
- ann_excess_deployed_pct: -110.46
- ann_excess_deployed_costs_x1.5_pct: -195.067
- ann_excess_deployed_costs_x2_pct: -279.674
- best_coin: IOST
- book_excess_without_best_coin_pct: -2.4357
- max_dd_pct: 2.1986
- t_excess_daily: -3.853

## Open positions

| Coin | Short | Long | Opened | Entry spread APR | Funding bp | Basis bp | Cost bp | Net bp |
|---|---|---|---|---|---|---|---|---|
| PIEVERSE | mexc | gate | 2026-11-09 21:00 | 35.8% | 12.6 | -17.0 | 17.0 | **-21.4** |
| INIT | gate | mexc | 2026-11-11 12:00 | 2413.2% | 41.1 | -133.5 | 17.0 | **-109.4** |

## Closed positions (195)

| Coin | Short | Long | Days | Reason | Net bp |
|---|---|---|---|---|---|
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
| KORU | mexc | gate | 2.2 | spread_decayed | -51.8 |
| SOXL | mexc | gate | 0.2 | spread_reversed | -42.7 |
| AKE | mexc | gate | 0.1 | rebalance | -155.2 |
| SOXL | mexc | gate | 1.5 | spread_reversed | -57.9 |
| MUU | mexc | gate | 0.1 | spread_reversed | -33.9 |
| AKE | mexc | gate | 0.4 | spread_reversed | -22.3 |
| AKE | mexc | gate | 0.2 | rebalance | -31.5 |
| AKE | mexc | gate | 0.0 | spread_reversed | -33.4 |
| AKE | mexc | gate | 0.2 | spread_reversed | -150.0 |
| CLANKER | mexc | gate | 0.2 | spread_decayed | -7.1 |
| AKE | mexc | gate | 0.1 | spread_reversed | -75.3 |

## Top opportunities this hour (passing the entry rule)

| Coin | Short | Long | 72 h spread APR | Now APR |
|---|---|---|---|---|
| INIT | gate | mexc | 2355.1% | 174.3% |

Rules and success criteria: `research/preregistrations/RADAR-1.md` on main.
