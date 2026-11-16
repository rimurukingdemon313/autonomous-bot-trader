# Funding radar: live paper ledger

Updated **2026-11-16 20:00 UTC**, run 954, version `radar-1.0.0`. State from: cache. Quotes this hour: 2367.

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

- days: 40.0
- run_coverage: 0.9927
- closed_positions: 215
- open_positions: 4
- utilisation: 0.2201
- rf_apr_pct_declared: 3.875
- book_pnl_pct: -2.0498
- book_excess_pct: -2.178
- ann_excess_deployed_pct: -90.852
- ann_excess_deployed_costs_x1.5_pct: -169.452
- ann_excess_deployed_costs_x2_pct: -248.052
- best_coin: INIT
- book_excess_without_best_coin_pct: -2.6323
- max_dd_pct: 2.1986
- t_excess_daily: -3.476

## Open positions

| Coin | Short | Long | Opened | Entry spread APR | Funding bp | Basis bp | Cost bp | Net bp |
|---|---|---|---|---|---|---|---|---|
| PIEVERSE | mexc | gate | 2026-11-09 21:00 | 35.8% | 36.0 | -9.2 | 17.0 | **9.8** |
| AKE | mexc | gate | 2026-11-16 09:00 | 98.6% | 5.8 | -2.2 | 17.0 | **-13.4** |
| EVAA | mexc | gate | 2026-11-16 09:00 | 50.3% | 9.4 | 3.9 | 17.0 | **-3.6** |
| LIT | hyperliquid | gate | 2026-11-16 15:00 | 50.2% | 15.6 | -14.4 | 19.5 | **-18.4** |

## Closed positions (215)

| Coin | Short | Long | Days | Reason | Net bp |
|---|---|---|---|---|---|
| RARE | mexc | gate | 0.0 | spread_decayed | -56.9 |
| EVAA | mexc | gate | 0.8 | rebalance | 11.4 |
| AKE | mexc | gate | 0.7 | spread_reversed | -40.9 |
| AKE | mexc | gate | 0.1 | spread_reversed | -40.7 |
| AKE | mexc | gate | 0.8 | spread_decayed | 6.6 |
| BARD | mexc | gate | 0.2 | spread_reversed | -38.3 |
| INIT | gate | mexc | 2.5 | rebalance | 573.2 |
| AKE | mexc | gate | 0.3 | spread_reversed | 34.3 |
| BARD | mexc | gate | 0.1 | spread_reversed | -54.8 |
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

## Top opportunities this hour (passing the entry rule)

| Coin | Short | Long | 72 h spread APR | Now APR |
|---|---|---|---|---|
| AKE | mexc | gate | 100.4% | 99.9% |
| EVAA | mexc | gate | 55.2% | 109.2% |

Rules and success criteria: `research/preregistrations/RADAR-1.md` on main.
