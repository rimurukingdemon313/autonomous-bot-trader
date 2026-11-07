# Funding radar: live paper ledger

Updated **2026-11-07 00:00 UTC**, run 722, version `radar-1.0.0`. State from: cache. Quotes this hour: 2414.

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

- days: 30.17
- run_coverage: 0.9959
- closed_positions: 170
- open_positions: 4
- utilisation: 0.2008
- rf_apr_pct_declared: 3.875
- book_pnl_pct: -1.9489
- book_excess_pct: -2.0483
- ann_excess_deployed_pct: -124.091
- ann_excess_deployed_costs_x1.5_pct: -214.72
- ann_excess_deployed_costs_x2_pct: -305.349
- best_coin: IOST
- book_excess_without_best_coin_pct: -2.2698
- max_dd_pct: 1.9742
- t_excess_daily: -3.726

## Open positions

| Coin | Short | Long | Opened | Entry spread APR | Funding bp | Basis bp | Cost bp | Net bp |
|---|---|---|---|---|---|---|---|---|
| SOL | dydx | gate | 2026-11-05 05:00 | 27.8% | 10.2 | 10.1 | 20.0 | **0.3** |
| SOXL | mexc | gate | 2026-11-05 15:00 | 48.2% | 18.9 | -14.4 | 17.0 | **-12.5** |
| KORU | mexc | gate | 2026-11-05 17:00 | 25.2% | 13.7 | -12.5 | 17.0 | **-15.8** |
| AKE | mexc | gate | 2026-11-06 16:00 | 122.9% | 20.9 | 12.1 | 17.0 | **15.9** |

## Closed positions (170)

| Coin | Short | Long | Days | Reason | Net bp |
|---|---|---|---|---|---|
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
| ESPORTS | mexc | gate | 0.1 | spread_reversed | -0.9 |
| ESPORTS | mexc | gate | 0.1 | spread_reversed | 15.5 |
| XPL | hyperliquid | gate | 0.8 | spread_decayed | -31.4 |
| PARTI | mexc | gate | 2.0 | spread_decayed | -16.1 |

## Top opportunities this hour (passing the entry rule)

| Coin | Short | Long | 72 h spread APR | Now APR |
|---|---|---|---|---|
| AKE | mexc | gate | 145.1% | 216.8% |
| SOXL | mexc | gate | 57.7% | 30.8% |

Rules and success criteria: `research/preregistrations/RADAR-1.md` on main.
