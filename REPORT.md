# Funding radar: live paper ledger

Updated **2026-11-20 11:00 UTC**, run 1041, version `radar-1.0.0`. State from: cache. Quotes this hour: 2367.

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

- days: 43.62
- run_coverage: 0.9933
- closed_positions: 244
- open_positions: 4
- utilisation: 0.2507
- rf_apr_pct_declared: 3.875
- book_pnl_pct: -2.4817
- book_excess_pct: -2.6311
- ann_excess_deployed_pct: -88.309
- ann_excess_deployed_costs_x1.5_pct: -159.824
- ann_excess_deployed_costs_x2_pct: -231.339
- best_coin: INIT
- book_excess_without_best_coin_pct: -3.0854
- max_dd_pct: 2.4922
- t_excess_daily: -3.945

## Open positions

| Coin | Short | Long | Opened | Entry spread APR | Funding bp | Basis bp | Cost bp | Net bp |
|---|---|---|---|---|---|---|---|---|
| SOXL | mexc | gate | 2026-11-17 08:00 | 25.1% | 25.5 | 8.3 | 17.0 | **16.8** |
| PIEVERSE | mexc | gate | 2026-11-18 18:00 | 26.1% | 23.9 | 25.0 | 17.0 | **31.9** |
| KORU | mexc | gate | 2026-11-18 20:00 | 39.0% | 14.1 | 1.7 | 17.0 | **-1.2** |
| EVAA | mexc | gate | 2026-11-19 15:00 | 25.9% | 21.4 | 14.1 | 17.0 | **18.5** |

## Closed positions (244)

| Coin | Short | Long | Days | Reason | Net bp |
|---|---|---|---|---|---|
| IRYS | mexc | gate | 0.1 | spread_reversed | -45.0 |
| IRYS | mexc | gate | 0.4 | spread_reversed | -51.8 |
| SOXS | gate | mexc | 2.0 | spread_decayed | -12.0 |
| IRYS | mexc | gate | 0.3 | spread_reversed | -42.0 |
| MMT | mexc | gate | 0.6 | spread_reversed | -22.4 |
| EVAA | mexc | gate | 1.0 | rebalance | -93.1 |
| BLESS | mexc | gate | 2.3 | spread_decayed | -1.8 |
| KORU | mexc | gate | 0.0 | spread_decayed | -32.2 |
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

## Top opportunities this hour (passing the entry rule)

| Coin | Short | Long | 72 h spread APR | Now APR |
|---|---|---|---|---|
| EVAA | mexc | gate | 37.2% | 71.0% |
| SOXL | mexc | gate | 29.1% | 32.7% |

Rules and success criteria: `research/preregistrations/RADAR-1.md` on main.
