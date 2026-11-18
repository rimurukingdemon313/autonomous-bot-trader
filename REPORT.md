# Funding radar: live paper ledger

Updated **2026-11-18 17:00 UTC**, run 999, version `radar-1.0.0`. State from: cache. Quotes this hour: 2359.

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

- days: 41.88
- run_coverage: 0.993
- closed_positions: 234
- open_positions: 5
- utilisation: 0.237
- rf_apr_pct_declared: 3.875
- book_pnl_pct: -2.3626
- book_excess_pct: -2.5098
- ann_excess_deployed_pct: -92.886
- ann_excess_deployed_costs_x1.5_pct: -168.912
- ann_excess_deployed_costs_x2_pct: -244.937
- best_coin: INIT
- book_excess_without_best_coin_pct: -2.9641
- max_dd_pct: 2.3626
- t_excess_daily: -3.833

## Open positions

| Coin | Short | Long | Opened | Entry spread APR | Funding bp | Basis bp | Cost bp | Net bp |
|---|---|---|---|---|---|---|---|---|
| BLESS | mexc | gate | 2026-11-17 04:00 | 28.2% | 17.3 | 5.7 | 17.0 | **6.0** |
| SOXL | mexc | gate | 2026-11-17 08:00 | 25.1% | 10.8 | -5.9 | 17.0 | **-12.1** |
| SOXS | gate | mexc | 2026-11-17 18:00 | 26.4% | 13.2 | -1.6 | 17.0 | **-5.4** |
| EVAA | mexc | gate | 2026-11-18 15:00 | 45.8% | 1.1 | -21.0 | 17.0 | **-36.9** |
| KORU | mexc | gate | 2026-11-18 17:00 | 38.8% | 0.0 | 0.0 | 17.0 | **-17.0** |

## Closed positions (234)

| Coin | Short | Long | Days | Reason | Net bp |
|---|---|---|---|---|---|
| KORU | mexc | gate | 0.0 | spread_decayed | -37.0 |
| BREV | gate | mexc | 0.1 | spread_decayed | -77.3 |
| SNXX | mexc | gate | 1.2 | spread_reversed | -9.4 |
| MUU | mexc | gate | 0.0 | spread_decayed | -33.7 |
| EVAA | mexc | gate | 0.0 | spread_decayed | -6.8 |
| MUU | mexc | gate | 0.0 | spread_decayed | -33.7 |
| EVAA | mexc | gate | 0.0 | spread_decayed | -69.0 |
| BREV | gate | mexc | 0.0 | spread_reversed | -37.4 |
| MUU | mexc | gate | 0.0 | spread_decayed | -33.6 |
| BREV | gate | mexc | 0.2 | spread_reversed | -33.2 |
| PIEVERSE | mexc | gate | 8.6 | rebalance | -39.8 |
| KORU | mexc | gate | 0.9 | spread_decayed | -60.0 |
| AKE | mexc | gate | 1.2 | spread_reversed | -8.0 |
| BREV | gate | mexc | 0.1 | spread_reversed | 8.0 |
| EVAA | mexc | gate | 0.3 | spread_reversed | -26.2 |
| EVAA | mexc | gate | 1.0 | rebalance | -17.8 |
| LIT | hyperliquid | gate | 0.6 | spread_reversed | -31.7 |
| BLESS | mexc | gate | 0.1 | rebalance | -21.6 |
| AKE | mexc | gate | 0.6 | spread_reversed | -17.8 |
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

## Top opportunities this hour (passing the entry rule)

| Coin | Short | Long | 72 h spread APR | Now APR |
|---|---|---|---|---|
| SOXL | mexc | gate | 48.2% | 32.4% |
| EVAA | mexc | gate | 44.1% | 37.5% |
| SOXS | gate | mexc | 43.7% | 37.3% |
| KORU | mexc | gate | 38.8% | 19.4% |

Rules and success criteria: `research/preregistrations/RADAR-1.md` on main.
