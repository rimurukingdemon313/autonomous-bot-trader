# Funding radar: live paper ledger

Updated **2026-10-12 14:00 UTC**, run 112, version `radar-1.0.0`. State from: cache. Quotes this hour: 2387.

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

- days: 4.75
- run_coverage: 0.9739
- closed_positions: 10
- open_positions: 2
- utilisation: 0.0616
- rf_apr_pct_declared: 3.875
- book_pnl_pct: -0.1205
- book_excess_pct: -0.143
- ann_excess_deployed_pct: -186.955
- ann_excess_deployed_costs_x1.5_pct: -323.585
- ann_excess_deployed_costs_x2_pct: -460.215
- best_coin: W
- book_excess_without_best_coin_pct: -0.1682
- max_dd_pct: 0.1703
- t_excess_daily: -1.11

## Open positions

| Coin | Short | Long | Opened | Entry spread APR | Funding bp | Basis bp | Cost bp | Net bp |
|---|---|---|---|---|---|---|---|---|
| STRK | hyperliquid | gate | 2026-10-11 17:00 | 25.6% | 6.3 | 3.2 | 19.5 | **-10.0** |
| W | hyperliquid | gate | 2026-10-12 03:00 | 29.4% | 14.0 | 76.3 | 19.5 | **70.8** |

## Closed positions (10)

| Coin | Short | Long | Days | Reason | Net bp |
|---|---|---|---|---|---|
| RSR | mexc | gate | 0.0 | spread_reversed | 4.7 |
| RLC | mexc | gate | 0.2 | spread_reversed | -49.3 |
| RLC | mexc | gate | 0.6 | spread_reversed | -26.0 |
| RLC | mexc | gate | 0.0 | spread_decayed | -16.3 |
| RLC | mexc | gate | 0.0 | spread_decayed | -56.7 |
| RLC | mexc | gate | 0.0 | spread_decayed | -19.4 |
| RLC | mexc | gate | 0.0 | spread_decayed | -31.7 |
| MAGIC | mexc | gate | 0.4 | spread_reversed | -36.4 |
| RLC | mexc | gate | 0.0 | spread_reversed | -49.9 |
| RLC | mexc | gate | 0.0 | spread_decayed | -21.0 |

## Top opportunities this hour (passing the entry rule)

| Coin | Short | Long | 72 h spread APR | Now APR |
|---|---|---|---|---|

Rules and success criteria: `research/preregistrations/RADAR-1.md` on main.
