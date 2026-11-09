# Funding radar: live paper ledger

Updated **2026-11-09 07:00 UTC**, run 773, version `radar-1.0.0`. State from: cache. Quotes this hour: 2415.

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

- days: 32.46
- run_coverage: 0.991
- closed_positions: 181
- open_positions: 4
- utilisation: 0.2102
- rf_apr_pct_declared: 3.875
- book_pnl_pct: -2.1362
- book_excess_pct: -2.2419
- ann_excess_deployed_pct: -120.853
- ann_excess_deployed_costs_x1.5_pct: -206.526
- ann_excess_deployed_costs_x2_pct: -292.199
- best_coin: IOST
- book_excess_without_best_coin_pct: -2.4633
- max_dd_pct: 2.1914
- t_excess_daily: -3.93

## Open positions

| Coin | Short | Long | Opened | Entry spread APR | Funding bp | Basis bp | Cost bp | Net bp |
|---|---|---|---|---|---|---|---|---|
| IDOL | mexc | gate | 2026-11-07 17:00 | 26.8% | 54.5 | 15.9 | 17.0 | **53.4** |
| ZEC | gate | mexc | 2026-11-08 22:00 | 25.7% | 7.6 | -9.2 | 17.0 | **-18.6** |
| JCT | mexc | gate | 2026-11-09 02:00 | 93.2% | 11.5 | 59.6 | 17.0 | **54.1** |
| PEPE | mexc | hyperliquid | 2026-11-09 06:00 | 25.0% | 0.5 | -3.2 | 16.5 | **-19.2** |

## Closed positions (181)

| Coin | Short | Long | Days | Reason | Net bp |
|---|---|---|---|---|---|
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

## Top opportunities this hour (passing the entry rule)

| Coin | Short | Long | 72 h spread APR | Now APR |
|---|---|---|---|---|
| JCT | mexc | gate | 106.4% | 251.2% |
| PEPE | mexc | hyperliquid | 25.5% | 30.5% |

Rules and success criteria: `research/preregistrations/RADAR-1.md` on main.
