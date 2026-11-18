# Funding radar: live paper ledger

Updated **2026-11-18 19:00 UTC**, run 1001, version `radar-1.0.0`. State from: cache. Quotes this hour: 2359.

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

- days: 41.96
- run_coverage: 0.9931
- closed_positions: 236
- open_positions: 6
- utilisation: 0.2378
- rf_apr_pct_declared: 3.875
- book_pnl_pct: -2.401
- book_excess_pct: -2.5572
- ann_excess_deployed_pct: -94.2
- ann_excess_deployed_costs_x1.5_pct: -170.813
- ann_excess_deployed_costs_x2_pct: -247.426
- best_coin: INIT
- book_excess_without_best_coin_pct: -3.0115
- max_dd_pct: 2.401
- t_excess_daily: -3.822

## Open positions

| Coin | Short | Long | Opened | Entry spread APR | Funding bp | Basis bp | Cost bp | Net bp |
|---|---|---|---|---|---|---|---|---|
| BLESS | mexc | gate | 2026-11-17 04:00 | 28.2% | 17.3 | 14.8 | 17.0 | **15.1** |
| SOXL | mexc | gate | 2026-11-17 08:00 | 25.1% | 11.6 | -1.9 | 17.0 | **-7.3** |
| SOXS | gate | mexc | 2026-11-17 18:00 | 26.4% | 14.1 | 1.6 | 17.0 | **-1.3** |
| EVAA | mexc | gate | 2026-11-18 15:00 | 45.8% | 2.1 | -25.1 | 17.0 | **-40.0** |
| PIEVERSE | mexc | gate | 2026-11-18 18:00 | 26.1% | 1.8 | -7.0 | 17.0 | **-22.3** |
| KORU | mexc | gate | 2026-11-18 19:00 | 39.3% | 0.0 | 0.0 | 17.0 | **-17.0** |

## Closed positions (236)

| Coin | Short | Long | Days | Reason | Net bp |
|---|---|---|---|---|---|
| KORU | mexc | gate | 0.0 | spread_decayed | -42.9 |
| KORU | mexc | gate | 0.0 | spread_decayed | -26.3 |
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

## Top opportunities this hour (passing the entry rule)

| Coin | Short | Long | 72 h spread APR | Now APR |
|---|---|---|---|---|
| SOXL | mexc | gate | 47.0% | 33.1% |
| EVAA | mexc | gate | 43.4% | 49.7% |
| SOXS | gate | mexc | 43.0% | 32.3% |
| KORU | mexc | gate | 39.3% | 22.9% |
| PIEVERSE | mexc | gate | 27.9% | 158.6% |

Rules and success criteria: `research/preregistrations/RADAR-1.md` on main.
