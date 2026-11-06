# Funding radar: live paper ledger

Updated **2026-11-06 01:00 UTC**, run 699, version `radar-1.0.0`. State from: cache. Quotes this hour: 2409.

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

- days: 29.21
- run_coverage: 0.9957
- closed_positions: 167
- open_positions: 4
- utilisation: 0.1953
- rf_apr_pct_declared: 3.875
- book_pnl_pct: -1.8435
- book_excess_pct: -1.9392
- ann_excess_deployed_pct: -124.816
- ann_excess_deployed_costs_x1.5_pct: -219.464
- ann_excess_deployed_costs_x2_pct: -314.112
- best_coin: IOST
- book_excess_without_best_coin_pct: -2.1606
- max_dd_pct: 1.8757
- t_excess_daily: -3.491

## Open positions

| Coin | Short | Long | Opened | Entry spread APR | Funding bp | Basis bp | Cost bp | Net bp |
|---|---|---|---|---|---|---|---|---|
| SOL | dydx | gate | 2026-11-05 05:00 | 27.8% | 8.3 | 4.1 | 20.0 | **-7.6** |
| SOXL | mexc | gate | 2026-11-05 15:00 | 48.2% | 11.2 | -5.8 | 17.0 | **-11.6** |
| KORU | mexc | gate | 2026-11-05 17:00 | 25.2% | 7.2 | 1.5 | 17.0 | **-8.3** |
| AKE | mexc | gate | 2026-11-05 22:00 | 167.0% | 8.0 | 20.3 | 17.0 | **11.3** |

## Closed positions (167)

| Coin | Short | Long | Days | Reason | Net bp |
|---|---|---|---|---|---|
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
| PEPE | hyperliquid | mexc | 1.7 | spread_reversed | -10.8 |
| AIN | mexc | gate | 0.0 | spread_decayed | -17.4 |
| AIN | mexc | gate | 0.0 | spread_decayed | -24.0 |

## Top opportunities this hour (passing the entry rule)

| Coin | Short | Long | 72 h spread APR | Now APR |
|---|---|---|---|---|
| AKE | mexc | gate | 156.8% | 233.9% |
| SOXL | mexc | gate | 56.5% | 80.0% |
| KORU | mexc | gate | 34.3% | 100.5% |

Rules and success criteria: `research/preregistrations/RADAR-1.md` on main.
