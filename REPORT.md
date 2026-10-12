# Funding radar: live paper ledger

Updated **2026-10-12 05:00 UTC**, run 103, version `radar-1.0.0`. State from: cache. Quotes this hour: 2374.

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

- days: 4.38
- run_coverage: 0.9717
- closed_positions: 8
- open_positions: 3
- utilisation: 0.0476
- rf_apr_pct_declared: 3.875
- book_pnl_pct: -0.137
- book_excess_pct: -0.1671
- ann_excess_deployed_pct: -318.131
- ann_excess_deployed_costs_x1.5_pct: -500.948
- ann_excess_deployed_costs_x2_pct: -683.766
- best_coin: W
- book_excess_without_best_coin_pct: -0.1788
- max_dd_pct: 0.1703
- t_excess_daily: -1.299

## Open positions

| Coin | Short | Long | Opened | Entry spread APR | Funding bp | Basis bp | Cost bp | Net bp |
|---|---|---|---|---|---|---|---|---|
| STRK | hyperliquid | gate | 2026-10-11 17:00 | 25.6% | 4.2 | 11.7 | 19.5 | **-3.5** |
| RLC | mexc | gate | 2026-10-12 02:00 | 41.5% | 2.1 | -41.4 | 17.0 | **-56.3** |
| W | hyperliquid | gate | 2026-10-12 03:00 | 29.4% | 7.3 | 55.2 | 19.5 | **43.1** |

## Closed positions (8)

| Coin | Short | Long | Days | Reason | Net bp |
|---|---|---|---|---|---|
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
| RLC | mexc | gate | 43.4% | 39.6% |
| W | hyperliquid | gate | 35.3% | 133.8% |

Rules and success criteria: `research/preregistrations/RADAR-1.md` on main.
