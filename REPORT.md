# Funding radar: live paper ledger

Updated **2026-11-19 18:00 UTC**, run 1024, version `radar-1.0.0`. State from: cache. Quotes this hour: 2363.

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

- days: 42.92
- run_coverage: 0.9932
- closed_positions: 241
- open_positions: 5
- utilisation: 0.2472
- rf_apr_pct_declared: 3.875
- book_pnl_pct: -2.4472
- book_excess_pct: -2.6016
- ann_excess_deployed_pct: -90.081
- ann_excess_deployed_costs_x1.5_pct: -163.268
- ann_excess_deployed_costs_x2_pct: -236.456
- best_coin: INIT
- book_excess_without_best_coin_pct: -3.056
- max_dd_pct: 2.4559
- t_excess_daily: -3.893

## Open positions

| Coin | Short | Long | Opened | Entry spread APR | Funding bp | Basis bp | Cost bp | Net bp |
|---|---|---|---|---|---|---|---|---|
| SOXL | mexc | gate | 2026-11-17 08:00 | 25.1% | 15.9 | 12.1 | 17.0 | **11.0** |
| SOXS | gate | mexc | 2026-11-17 18:00 | 26.4% | 15.4 | 21.2 | 17.0 | **19.6** |
| PIEVERSE | mexc | gate | 2026-11-18 18:00 | 26.1% | 18.4 | 5.5 | 17.0 | **6.9** |
| KORU | mexc | gate | 2026-11-18 20:00 | 39.0% | 5.6 | 1.5 | 17.0 | **-9.9** |
| EVAA | mexc | gate | 2026-11-19 15:00 | 25.9% | 4.3 | 11.3 | 17.0 | **-1.4** |

## Closed positions (241)

| Coin | Short | Long | Days | Reason | Net bp |
|---|---|---|---|---|---|
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
| EVAA | mexc | gate | 0.8 | rebalance | 11.4 |
| AKE | mexc | gate | 0.7 | spread_reversed | -40.9 |
| AKE | mexc | gate | 0.1 | spread_reversed | -40.7 |

## Top opportunities this hour (passing the entry rule)

| Coin | Short | Long | 72 h spread APR | Now APR |
|---|---|---|---|---|
| PIEVERSE | mexc | gate | 41.1% | 24.5% |
| EVAA | mexc | gate | 28.6% | 140.2% |

Rules and success criteria: `research/preregistrations/RADAR-1.md` on main.
