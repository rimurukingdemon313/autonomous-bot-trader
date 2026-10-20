# Funding radar: live paper ledger

Updated **2026-10-20 06:00 UTC**, run 296, version `radar-1.0.0`. State from: cache. Quotes this hour: 2398.

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

- days: 12.42
- run_coverage: 0.99
- closed_positions: 46
- open_positions: 0
- utilisation: 0.0956
- rf_apr_pct_declared: 3.875
- book_pnl_pct: -0.5438
- book_excess_pct: -0.5563
- ann_excess_deployed_pct: -172.208
- ann_excess_deployed_costs_x1.5_pct: -295.483
- ann_excess_deployed_costs_x2_pct: -418.757
- best_coin: RSR
- book_excess_without_best_coin_pct: -0.5847
- max_dd_pct: 0.5444
- t_excess_daily: -2.483

## Open positions

| Coin | Short | Long | Opened | Entry spread APR | Funding bp | Basis bp | Cost bp | Net bp |
|---|---|---|---|---|---|---|---|---|

## Closed positions (46)

| Coin | Short | Long | Days | Reason | Net bp |
|---|---|---|---|---|---|
| AGT | mexc | gate | 0.0 | spread_reversed | -15.9 |
| BTW | gate | mexc | 0.2 | spread_reversed | -53.5 |
| AGT | mexc | gate | 0.2 | spread_decayed | -44.1 |
| AGT | mexc | gate | 0.0 | spread_decayed | -45.4 |
| AGT | mexc | gate | 0.0 | spread_decayed | -19.7 |
| SAND | mexc | gate | 0.1 | spread_reversed | -26.7 |
| AGT | mexc | gate | 0.2 | spread_decayed | -22.8 |
| SAND | mexc | gate | 0.2 | spread_reversed | -39.8 |
| SAND | mexc | gate | 0.2 | spread_reversed | -38.0 |
| AGT | mexc | gate | 0.8 | spread_reversed | -5.3 |
| SAND | mexc | gate | 0.0 | spread_reversed | -12.2 |
| AGT | mexc | gate | 0.1 | spread_reversed | -31.8 |
| ICNT | mexc | gate | 0.2 | spread_reversed | -50.0 |
| AGT | mexc | gate | 0.2 | spread_reversed | -21.7 |
| ICNT | mexc | gate | 0.1 | spread_reversed | -34.4 |
| AGT | mexc | gate | 0.5 | spread_reversed | 62.9 |
| SOXL | mexc | gate | 0.7 | spread_reversed | -37.4 |
| KORU | mexc | gate | 2.7 | spread_reversed | -19.8 |
| AGT | mexc | gate | 0.2 | rebalance | -87.9 |
| AGT | mexc | gate | 0.1 | rebalance | -60.4 |
| AGT | mexc | gate | 0.0 | spread_reversed | -119.1 |
| AGT | mexc | gate | 0.0 | rebalance | 297.5 |
| AGT | mexc | gate | 0.2 | rebalance | -90.9 |
| WAL | mexc | gate | 0.0 | spread_reversed | -25.0 |
| WAL | mexc | gate | 0.0 | spread_reversed | -30.4 |
| WAL | mexc | gate | 0.1 | spread_reversed | -16.0 |
| WAL | mexc | gate | 0.2 | spread_reversed | -20.2 |
| WAL | mexc | gate | 0.0 | spread_reversed | -52.0 |
| W | hyperliquid | gate | 0.0 | spread_decayed | -56.8 |
| W | hyperliquid | gate | 0.0 | spread_decayed | -33.7 |

## Top opportunities this hour (passing the entry rule)

| Coin | Short | Long | 72 h spread APR | Now APR |
|---|---|---|---|---|

Rules and success criteria: `research/preregistrations/RADAR-1.md` on main.
