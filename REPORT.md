# Funding radar: live paper ledger

Updated **2026-10-13 04:00 UTC**, run 126, version `radar-1.0.0`. State from: cache. Quotes this hour: 2387.

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

- days: 5.33
- run_coverage: 0.9767
- closed_positions: 13
- open_positions: 2
- utilisation: 0.0683
- rf_apr_pct_declared: 3.875
- book_pnl_pct: -0.1416
- book_excess_pct: -0.1648
- ann_excess_deployed_pct: -171.861
- ann_excess_deployed_costs_x1.5_pct: -310.04
- ann_excess_deployed_costs_x2_pct: -448.219
- best_coin: RSR
- book_excess_without_best_coin_pct: -0.172
- max_dd_pct: 0.1943
- t_excess_daily: -1.02

## Open positions

| Coin | Short | Long | Opened | Entry spread APR | Funding bp | Basis bp | Cost bp | Net bp |
|---|---|---|---|---|---|---|---|---|
| W | hyperliquid | gate | 2026-10-12 23:00 | 35.9% | 3.4 | -9.3 | 19.5 | **-25.5** |
| RSR | gate | hyperliquid | 2026-10-13 01:00 | 46.5% | 15.1 | 26.7 | 19.5 | **22.3** |

## Closed positions (13)

| Coin | Short | Long | Days | Reason | Net bp |
|---|---|---|---|---|---|
| RSR | mexc | gate | 0.2 | spread_reversed | 7.7 |
| W | hyperliquid | gate | 0.5 | spread_reversed | 34.7 |
| STRK | hyperliquid | gate | 1.0 | rebalance | -20.5 |
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
| RSR | mexc | hyperliquid | 140.7% | 192.6% |
| W | hyperliquid | gate | 38.8% | 54.3% |

Rules and success criteria: `research/preregistrations/RADAR-1.md` on main.
