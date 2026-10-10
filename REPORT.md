# Funding radar: live paper ledger

Updated **2026-10-10 23:00 UTC**, run 73, version `radar-1.0.0`. State from: cache. Quotes this hour: 2374.

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

- days: 3.12
- run_coverage: 0.9605
- closed_positions: 1
- open_positions: 2
- utilisation: 0.0096
- rf_apr_pct_declared: 3.875
- book_pnl_pct: -0.0157
- book_excess_pct: -0.0329
- ann_excess_deployed_pct: -576.902
- ann_excess_deployed_costs_x1.5_pct: -1023.662
- ann_excess_deployed_costs_x2_pct: -1470.422
- best_coin: MAGIC
- book_excess_without_best_coin_pct: -0.0275
- max_dd_pct: 0.0248
- t_excess_daily: -1.0

## Open positions

| Coin | Short | Long | Opened | Entry spread APR | Funding bp | Basis bp | Cost bp | Net bp |
|---|---|---|---|---|---|---|---|---|
| MAGIC | mexc | gate | 2026-10-10 19:00 | 30.7% | 4.2 | 19.4 | 17.0 | **6.5** |
| RLC | mexc | gate | 2026-10-10 23:00 | 55.7% | 0.0 | 0.0 | 17.0 | **-17.0** |

## Closed positions (1)

| Coin | Short | Long | Days | Reason | Net bp |
|---|---|---|---|---|---|
| RLC | mexc | gate | 0.0 | spread_decayed | -21.0 |

## Top opportunities this hour (passing the entry rule)

| Coin | Short | Long | 72 h spread APR | Now APR |
|---|---|---|---|---|
| RLC | mexc | gate | 55.7% | 33.7% |
| MAGIC | mexc | gate | 34.8% | 82.8% |

Rules and success criteria: `research/preregistrations/RADAR-1.md` on main.
