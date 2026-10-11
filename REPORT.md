# Funding radar: live paper ledger

Updated **2026-10-11 15:00 UTC**, run 89, version `radar-1.0.0`. State from: cache. Quotes this hour: 2374.

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

- days: 3.79
- run_coverage: 0.9674
- closed_positions: 7
- open_positions: 1
- utilisation: 0.0236
- rf_apr_pct_declared: 3.875
- book_pnl_pct: -0.1386
- book_excess_pct: -0.148
- ann_excess_deployed_pct: -648.027
- ann_excess_deployed_costs_x1.5_pct: -945.867
- ann_excess_deployed_costs_x2_pct: -1243.707
- best_coin: MAGIC
- book_excess_without_best_coin_pct: -0.1294
- max_dd_pct: 0.1386
- t_excess_daily: -1.17

## Open positions

| Coin | Short | Long | Opened | Entry spread APR | Funding bp | Basis bp | Cost bp | Net bp |
|---|---|---|---|---|---|---|---|---|
| RLC | mexc | gate | 2026-10-11 10:00 | 47.6% | 5.6 | -34.5 | 17.0 | **-45.9** |

## Closed positions (7)

| Coin | Short | Long | Days | Reason | Net bp |
|---|---|---|---|---|---|
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
| RLC | mexc | gate | 46.4% | 74.9% |

Rules and success criteria: `research/preregistrations/RADAR-1.md` on main.
