# Funding radar: live paper ledger

Updated **2026-11-08 21:00 UTC**, run 763, version `radar-1.0.0`. State from: cache. Quotes this hour: 2414.

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

- days: 32.04
- run_coverage: 0.9909
- closed_positions: 180
- open_positions: 1
- utilisation: 0.2088
- rf_apr_pct_declared: 3.875
- book_pnl_pct: -2.1741
- book_excess_pct: -2.2532
- ann_excess_deployed_pct: -123.669
- ann_excess_deployed_costs_x1.5_pct: -209.046
- ann_excess_deployed_costs_x2_pct: -294.423
- best_coin: IOST
- book_excess_without_best_coin_pct: -2.4746
- max_dd_pct: 2.1806
- t_excess_daily: -4.068

## Open positions

| Coin | Short | Long | Opened | Entry spread APR | Funding bp | Basis bp | Cost bp | Net bp |
|---|---|---|---|---|---|---|---|---|
| IDOL | mexc | gate | 2026-11-07 17:00 | 26.8% | 40.5 | 8.6 | 17.0 | **32.1** |

## Closed positions (180)

| Coin | Short | Long | Days | Reason | Net bp |
|---|---|---|---|---|---|
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
| AKE | mexc | gate | 0.0 | rebalance | -16.6 |
| TRUMP | gate | hyperliquid | 0.4 | spread_reversed | -26.2 |
| AKE | mexc | gate | 0.1 | spread_reversed | -52.7 |
| SOXL | mexc | gate | 2.3 | rebalance | 8.0 |
| AKE | mexc | gate | 0.8 | spread_reversed | 125.1 |
| CLANKER | mexc | gate | 0.2 | rebalance | -34.6 |
| AKE | mexc | gate | 0.0 | spread_decayed | -92.7 |
| AKE | mexc | gate | 0.0 | spread_decayed | -20.0 |
| AKE | mexc | gate | 0.0 | spread_decayed | -46.2 |
| AKE | mexc | gate | 0.0 | spread_decayed | -0.3 |
| AKE | mexc | gate | 0.0 | spread_decayed | -48.0 |
| AIN | mexc | gate | 3.0 | spread_reversed | 45.4 |
| AGT | gate | mexc | 0.2 | spread_reversed | -89.0 |
| AGT | gate | mexc | 0.4 | spread_reversed | -25.5 |
| AKE | mexc | gate | 0.0 | spread_reversed | -12.9 |

## Top opportunities this hour (passing the entry rule)

| Coin | Short | Long | 72 h spread APR | Now APR |
|---|---|---|---|---|

Rules and success criteria: `research/preregistrations/RADAR-1.md` on main.
