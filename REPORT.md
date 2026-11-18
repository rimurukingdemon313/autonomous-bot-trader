# Funding radar: live paper ledger

Updated **2026-11-18 15:00 UTC**, run 997, version `radar-1.0.0`. State from: cache. Quotes this hour: 2359.

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

- days: 41.79
- run_coverage: 0.993
- closed_positions: 231
- open_positions: 6
- utilisation: 0.2363
- rf_apr_pct_declared: 3.875
- book_pnl_pct: -2.2742
- book_excess_pct: -2.4294
- ann_excess_deployed_pct: -90.405
- ann_excess_deployed_costs_x1.5_pct: -166.217
- ann_excess_deployed_costs_x2_pct: -242.03
- best_coin: INIT
- book_excess_without_best_coin_pct: -2.8837
- max_dd_pct: 2.2742
- t_excess_daily: -3.81

## Open positions

| Coin | Short | Long | Opened | Entry spread APR | Funding bp | Basis bp | Cost bp | Net bp |
|---|---|---|---|---|---|---|---|---|
| BLESS | mexc | gate | 2026-11-17 04:00 | 28.2% | 17.2 | 8.0 | 17.0 | **8.3** |
| SOXL | mexc | gate | 2026-11-17 08:00 | 25.1% | 10.2 | 4.0 | 17.0 | **-2.8** |
| SNXX | mexc | gate | 2026-11-17 11:00 | 25.2% | 2.6 | 22.2 | 17.0 | **7.8** |
| SOXS | gate | mexc | 2026-11-17 18:00 | 26.4% | 12.4 | 13.1 | 17.0 | **8.5** |
| BREV | gate | mexc | 2026-11-18 15:00 | 55.4% | 0.0 | 0.0 | 17.0 | **-17.0** |
| EVAA | mexc | gate | 2026-11-18 15:00 | 45.8% | 0.0 | 0.0 | 17.0 | **-17.0** |

## Closed positions (231)

| Coin | Short | Long | Days | Reason | Net bp |
|---|---|---|---|---|---|
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
| AGT | mexc | gate | 0.0 | spread_reversed | -25.6 |
| AGT | mexc | gate | 0.1 | spread_reversed | -60.9 |
| AGT | mexc | gate | 0.1 | spread_reversed | -4.7 |

## Top opportunities this hour (passing the entry rule)

| Coin | Short | Long | 72 h spread APR | Now APR |
|---|---|---|---|---|
| BREV | gate | mexc | 55.4% | 401.2% |
| SOXL | mexc | gate | 46.8% | 19.8% |
| EVAA | mexc | gate | 45.8% | 52.0% |
| SOXS | gate | mexc | 42.9% | 38.3% |

Rules and success criteria: `research/preregistrations/RADAR-1.md` on main.
