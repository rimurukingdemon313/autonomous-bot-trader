# Funding radar: live paper ledger

Updated **2026-10-10 20:00 UTC**, run 70, version `radar-1.0.0`. State from: cache. Quotes this hour: 2374.

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

- days: 3.0
- run_coverage: 0.9589
- closed_positions: 0
- open_positions: 1
- utilisation: 0.0029
- rf_apr_pct_declared: 3.875
- book_pnl_pct: -0.0151
- book_excess_pct: -0.0236
- ann_excess_deployed_pct: -2067.883
- ann_excess_deployed_costs_x1.5_pct: -2812.483
- ann_excess_deployed_costs_x2_pct: -3557.083
- best_coin: MAGIC
- book_excess_without_best_coin_pct: 0.0
- max_dd_pct: 0.0151
- t_excess_daily: -1.0

## Open positions

| Coin | Short | Long | Opened | Entry spread APR | Funding bp | Basis bp | Cost bp | Net bp |
|---|---|---|---|---|---|---|---|---|
| MAGIC | mexc | gate | 2026-10-10 19:00 | 30.7% | 0.8 | -13.9 | 17.0 | **-30.1** |

## Closed positions (0)

| Coin | Short | Long | Days | Reason | Net bp |
|---|---|---|---|---|---|

## Top opportunities this hour (passing the entry rule)

| Coin | Short | Long | 72 h spread APR | Now APR |
|---|---|---|---|---|
| MAGIC | mexc | gate | 32.1% | 98.5% |

Rules and success criteria: `research/preregistrations/RADAR-1.md` on main.
