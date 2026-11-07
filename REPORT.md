# Funding radar: live paper ledger

Updated **2026-11-07 07:00 UTC**, run 729, version `radar-1.0.0`. State from: cache. Quotes this hour: 2414.

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

- days: 30.46
- run_coverage: 0.9959
- closed_positions: 174
- open_positions: 4
- utilisation: 0.2022
- rf_apr_pct_declared: 3.875
- book_pnl_pct: -2.1063
- book_excess_pct: -2.2068
- ann_excess_deployed_pct: -131.506
- ann_excess_deployed_costs_x1.5_pct: -222.682
- ann_excess_deployed_costs_x2_pct: -313.857
- best_coin: IOST
- book_excess_without_best_coin_pct: -2.4282
- max_dd_pct: 2.1063
- t_excess_daily: -3.988

## Open positions

| Coin | Short | Long | Opened | Entry spread APR | Funding bp | Basis bp | Cost bp | Net bp |
|---|---|---|---|---|---|---|---|---|
| SOL | dydx | gate | 2026-11-05 05:00 | 27.8% | 11.3 | 1.1 | 20.0 | **-7.7** |
| KORU | mexc | gate | 2026-11-05 17:00 | 25.2% | 14.6 | -21.9 | 17.0 | **-24.3** |
| UAI | mexc | gate | 2026-11-07 06:00 | 26.2% | 1.1 | 7.3 | 17.0 | **-8.6** |
| AKE | mexc | gate | 2026-11-07 07:00 | 151.5% | 0.0 | 0.0 | 17.0 | **-17.0** |

## Closed positions (174)

| Coin | Short | Long | Days | Reason | Net bp |
|---|---|---|---|---|---|
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
| AKE | mexc | gate | 0.1 | spread_reversed | -29.8 |
| AKE | mexc | gate | 0.2 | spread_reversed | -57.1 |
| AKE | mexc | gate | 0.1 | spread_reversed | -107.5 |
| HYPE | hyperliquid | gate | 3.0 | spread_decayed | -24.4 |
| AKE | mexc | gate | 0.1 | spread_reversed | -79.8 |
| ZRO | hyperliquid | mexc | 1.0 | spread_decayed | -27.7 |

## Top opportunities this hour (passing the entry rule)

| Coin | Short | Long | 72 h spread APR | Now APR |
|---|---|---|---|---|
| AKE | mexc | gate | 151.5% | 66.6% |
| UAI | mexc | gate | 27.5% | 96.4% |

Rules and success criteria: `research/preregistrations/RADAR-1.md` on main.
