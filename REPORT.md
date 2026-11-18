# Funding radar: live paper ledger

Updated **2026-11-18 03:00 UTC**, run 985, version `radar-1.0.0`. State from: cache. Quotes this hour: 2353.

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

- days: 41.29
- run_coverage: 0.9929
- closed_positions: 220
- open_positions: 8
- utilisation: 0.2317
- rf_apr_pct_declared: 3.875
- book_pnl_pct: -2.1018
- book_excess_pct: -2.2705
- ann_excess_deployed_pct: -87.313
- ann_excess_deployed_costs_x1.5_pct: -162.713
- ann_excess_deployed_costs_x2_pct: -238.113
- best_coin: INIT
- book_excess_without_best_coin_pct: -2.7248
- max_dd_pct: 2.1986
- t_excess_daily: -3.537

## Open positions

| Coin | Short | Long | Opened | Entry spread APR | Funding bp | Basis bp | Cost bp | Net bp |
|---|---|---|---|---|---|---|---|---|
| PIEVERSE | mexc | gate | 2026-11-09 21:00 | 35.8% | 41.6 | -41.9 | 17.0 | **-17.3** |
| AKE | mexc | gate | 2026-11-17 02:00 | 88.8% | 14.4 | 1.2 | 17.0 | **-1.4** |
| BLESS | mexc | gate | 2026-11-17 04:00 | 28.2% | 11.0 | 34.6 | 17.0 | **28.6** |
| SOXL | mexc | gate | 2026-11-17 08:00 | 25.1% | 9.1 | 3.9 | 17.0 | **-4.0** |
| KORU | mexc | gate | 2026-11-17 09:00 | 25.4% | 0.4 | 10.2 | 17.0 | **-6.4** |
| SNXX | mexc | gate | 2026-11-17 11:00 | 25.2% | 1.0 | 23.6 | 17.0 | **7.6** |
| SOXS | gate | mexc | 2026-11-17 18:00 | 26.4% | 6.1 | 6.5 | 17.0 | **-4.4** |
| BREV | gate | mexc | 2026-11-18 03:00 | 56.4% | 0.0 | 0.0 | 17.0 | **-17.0** |

## Closed positions (220)

| Coin | Short | Long | Days | Reason | Net bp |
|---|---|---|---|---|---|
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

## Top opportunities this hour (passing the entry rule)

| Coin | Short | Long | 72 h spread APR | Now APR |
|---|---|---|---|---|
| BREV | gate | mexc | 56.4% | 137.5% |
| SOXL | mexc | gate | 49.0% | 23.8% |
| SNXX | mexc | gate | 41.6% | 16.6% |
| SOXS | gate | mexc | 39.4% | 83.5% |
| BLESS | mexc | gate | 38.5% | 16.2% |

Rules and success criteria: `research/preregistrations/RADAR-1.md` on main.
