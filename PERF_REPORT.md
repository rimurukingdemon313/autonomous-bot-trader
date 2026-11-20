# Paper systems: the performance audit and the optimization cycle

**PAPER ONLY · NOT REAL MONEY · NOTHING HERE IS A PROFIT CLAIM.** Written by the performance cycle on GitHub's runner (`scripts/perf_cycle.py`), with no person in the loop. It reads the paper systems' own ledgers, recomputes every figure by a second route, and changes neither system.

**بالعربي:** مكتب TRND-1: الرصيد $196,056.12، المحقّق $0.00، غير المحقّق -$3,943.89، الصفقات المسكّرة 0. رادار RADAR-1: دفتره -2.51% من رأس ماله الورقي، 246 صفقة مسكّرة، الرابح منها 43. المطابقة: كل الأرقام تطابقت من مصدرين. تجربة التحسين: غير حاسمة لأن العيّنة صغيرة. المنافسين المسجّلين: 0. النظام الأصلي ما انلمس.

Updated 2026-11-20 20:32 UTC · perf-1.0.1 · cycles so far: 28

## 1. TRND-1: the trend desk's paper account

**Reconciled: 40 of 40 checks hold.** Each compares two routes to the same figure.

Last session: 2026-11-19 21:00 UTC. Paper only: no real money.

| | |
|---|---|
| Initial capital | $200,000.00 |
| Equity now | $196,056.12 |
| **Realized** P&L (closed trades, after every cost) | $0.00 from $0.00 gross |
| **Unrealized** P&L (open trades at the last close: a valuation, not a profit) | -$3,943.89 |
| Net after all costs (realized plus unrealized) | -$3,943.88 (-1.972%) |
| Open positions | 4 |
| Closed trades | 0: 0 won, 0 lost |
| Win rate | undefined: no closed trade |
| Average win / average loss | undefined: no closed trade / undefined: no closed trade |
| Profit factor | undefined: no closed trade |
| Maximum drawdown, session closes | $5,232.98 |
| Maximum drawdown, inside a day | $5,318.25 |
| Below the peak now | $5,232.98 |
| Gross exposure | $93,896.37, 0.48x the equity |
| Loss if every stop were hit from here | $5,630.68 (limit $8,000.00) |
| Losing days | 8 of 9 |

Trade statistics: sample **none** (0 closed). A ratio over no closed trade does not exist and is not shown as zero.

### Open positions and where the risk sits

| Index | Units | Entry | Mark | Move | Unrealized | Notional | Share of gross | Stop | Loss at the stop from here |
|---|---|---|---|---|---|---|---|---|---|
| GER40 | 0.84 | 26,268.04 | 25,463.06 | -3.06% | -$743.32 | $23,512.63 | 25.0% | 23,935.98 | $1,410.11 |
| UK100 | 1.7 | 10,783.50 | 10,452.20 | -3.07% | -$743.72 | $23,463.59 | 25.0% | 9,825.54 | $1,406.76 |
| US500 | 3.25 | 7,550.29 | 7,175.58 | -4.96% | -$1,217.81 | $23,320.64 | 24.8% | 6,745.28 | $1,398.48 |
| NAS100 | 0.89 | 27,908.47 | 26,516.30 | -4.99% | -$1,239.04 | $23,599.51 | 25.1% | 24,926.03 | $1,415.34 |

Concentration: 4 positions, the largest 25.1% of the gross; by size that is 4.0 equal positions, and by risk it is **one**: four equity indices, all long: one risk factor held four times.

### Against a benchmark

| | Since the start | What it is |
|---|---|---|
| The desk | -$3,943.88 | realized plus unrealized, after costs |
| Cash | +$216.31 | 3.875% a year on the starting balance for 10.19 days |
| The same indices bought and held | -$3,943.89 | identical to the desk while no trade has closed: the rule has not yet made one decision the holder would not have made |
| The same positions at one times the account | -$7,982.57 | the same P&L scaled from the desk's exposure to one times the account: what the validated rule's own sizing would show; the desk's risk limits do not allow it |

### Month by month, against the $4,000 target (a target, never a quota)

| Month | Days | Net | Of $4,000 |
|---|---|---|---|
| 2026-11 | 9 | -$3,943.88 | -98.6% |

## 2. RADAR-1: the funding radar's paper ledger

**Reconciled: 24 of 24 checks hold.** Each compares two routes to the same figure.

Marks from 2026-10-07 20:00 UTC to 2026-11-20 20:00 UTC (44.00 days). Paper only: no order is ever sent. Its preregistered single look is on 2026-12-06 and is read as registered, whatever this audit says.

Capital: ten slots of 2N: 20N. The radar has no cash account; N is not a dollar amount. P&L is in basis points (bp) of one leg's notional; 2,000 bp summed over positions is 1% of the book.

| | In bp of N | In % of the book | On a $100,000 book (illustration) |
|---|---|---|---|
| **Realized** (closed positions, after every fill) | -5,045.3 | -2.5227% | -$2,522.66 |
| **Unrealized** (open positions at their marks, entry fills paid) | 32.6 | 0.0163% | +$16.28 |
| The book if every open position were closed now | -5,063.7 | -2.5319% | -$2,531.88 |

| | |
|---|---|
| Closed positions | 246: 43 won, 203 lost |
| Win rate | 17.5% |
| Average win / average loss | 75.6 bp / -40.9 bp |
| Profit factor | 0.39 |
| Mean net a position | -20.5 bp (t -4.46) |
| Open positions | 3 of 10 slots; on average 25.1% of the capital was deployed |
| Book P&L | -2.5064% |
| Book excess over cash (3.875%/yr on the capital in use) | -2.6487% |
| Annualised excess on the capital deployed | -87.9%/yr |
| The same with costs x1.5 / x2 | -158.9% / -229.9% |
| Maximum drawdown of the book (hourly marks) | 2.5228% |
| t of the daily excess | -3.99 |
| Best coin, and the book's excess without it | INIT: -3.1030% |

### Where it came from

Funding received **3,389 bp**, price moves between the legs **21 bp**, fills **-8,455 bp**: net **-5,045 bp**. A position earned 13.9 bp before costs and paid 34.4 bp: the costs are 2.48 times the gross. Half the positions were closed within 3.0 hours.

| Held for | Positions | Won | Sum | Mean | t | Funding | Price | Costs |
|---|---|---|---|---|---|---|---|---|
| 1 hour or less | 82 | 5 | -2,752 bp | -33.6 bp | -6.13 | 46 | 30 | 2,828 |
| 1 to 6 hours | 87 | 15 | -2,639 bp | -30.3 bp | -4.24 | 840 | -509 | 2,970 |
| 6 to 24 hours | 51 | 14 | -238 bp | -4.7 bp | -0.47 | 1,216 | 309 | 1,763 |
| over 3 days | 4 | 1 | -62 bp | -15.5 bp | -1.59 | 127 | -47 | 142 |
| 1 to 3 days | 22 | 8 | 646 bp | 29.4 bp | 1.07 | 1,160 | 238 | 752 |

| Closed for | Positions | Won | Sum | Mean | t | Funding | Price | Costs |
|---|---|---|---|---|---|---|---|---|
| spread_reversed | 133 | 25 | -2,857 bp | -21.5 bp | -4.22 | 1,837 | -130 | 4,565 |
| spread_decayed | 76 | 3 | -2,708 bp | -35.6 bp | -15.16 | 131 | -212 | 2,627 |
| rebalance | 37 | 15 | 520 bp | 14.1 bp | 0.60 | 1,420 | 363 | 1,263 |

| Known at the entry: entry spread | Positions | Won | Sum | Mean | t | Funding | Price | Costs |
|---|---|---|---|---|---|---|---|---|
| under 50%/yr | 146 | 19 | -4,126 bp | -28.3 bp | -7.88 | 1,026 | -121 | 5,031 |
| 50 to 100%/yr | 59 | 13 | -721 bp | -12.2 bp | -1.03 | 894 | 396 | 2,011 |
| 100%/yr or more | 41 | 11 | -198 bp | -4.8 bp | -0.28 | 1,469 | -254 | 1,413 |

| Known at the entry: venue pair | Positions | Won | Sum | Mean | t | Funding | Price | Costs |
|---|---|---|---|---|---|---|---|---|
| short mexc / long gate | 191 | 33 | -4,314 bp | -22.6 bp | -4.78 | 2,095 | 85 | 6,494 |
| short gate / long mexc | 25 | 4 | -433 bp | -17.3 bp | -0.69 | 769 | -352 | 850 |
| short hyperliquid / long gate | 8 | 1 | -215 bp | -26.9 bp | -2.73 | 56 | 41 | 312 |
| short hyperliquid / long mexc | 8 | 1 | -131 bp | -16.3 bp | -1.21 | 162 | -29 | 264 |
| short mexc / long hyperliquid | 2 | 0 | -42 bp | -21.1 bp | -2.36 | 21 | 3 | 66 |
| short dydx / long gate | 1 | 0 | -23 bp | -22.9 bp | n/a | 13 | 4 | 40 |
| short gate / long hyperliquid | 11 | 4 | 113 bp | 10.3 bp | 0.46 | 273 | 269 | 429 |

| Known at the entry: time since the coin's previous position | Positions | Won | Sum | Mean | t | Funding | Price | Costs |
|---|---|---|---|---|---|---|---|---|
| within 6 hours of the coin's previous exit | 159 | 26 | -2,916 bp | -18.3 bp | -2.69 | 2,447 | 84 | 5,448 |
| a first entry, or later | 87 | 17 | -2,129 bp | -24.5 bp | -6.69 | 941 | -63 | 3,007 |

50 coins were traded and 44 of them lost. The five worst and the five best:

| Coin | Positions | Won | Sum | Mean | t | Funding | Price | Costs |
|---|---|---|---|---|---|---|---|---|
| AKE | 26 | 3 | -1,005 bp | -38.6 bp | -3.57 | 262 | -382 | 884 |
| BTW | 20 | 3 | -821 bp | -41.0 bp | -7.06 | 61 | -202 | 680 |
| IRYS | 18 | 3 | -620 bp | -34.5 bp | -4.50 | 212 | -220 | 612 |
| SOXL | 14 | 1 | -448 bp | -32.0 bp | -7.02 | 89 | -61 | 476 |
| AGT | 20 | 2 | -416 bp | -20.8 bp | -1.10 | 48 | 216 | 680 |
| INIT | 7 | 5 | 917 bp | 131.0 bp | 1.67 | 1,009 | 165 | 257 |
| IOST | 4 | 3 | 450 bp | 112.4 bp | 0.98 | 358 | 227 | 136 |
| BULLA | 8 | 4 | 267 bp | 33.4 bp | 0.55 | 276 | 264 | 272 |
| RSR | 3 | 3 | 58 bp | 19.4 bp | 1.47 | 67 | 98 | 107 |
| IDOL | 2 | 1 | 20 bp | 10.0 bp | 0.52 | 74 | 14 | 68 |

Concentration: the most traded coin (AKE) is 10.4% of the positions; by count the book is 21.4 equal coins. Venue pairs: short mexc / long gate 194, short gate / long mexc 25, short gate / long hyperliquid 11, short hyperliquid / long gate 8, short hyperliquid / long mexc 8, short mexc / long hyperliquid 2, short dydx / long gate 1.

| Open now | Short / long | Opened | Entry spread | Funding | Price | Fills paid | Net at the marks | Net if closed now |
|---|---|---|---|---|---|---|---|---|
| PIEVERSE | mexc / gate | 2026-11-18 18:00 UTC | 26.1%/yr | 26.6 | 6.7 | 17.0 | 16.3 bp | -0.7 bp |
| EVAA | mexc / gate | 2026-11-19 15:00 UTC | 25.9%/yr | 29.5 | 29.0 | 17.0 | 41.5 bp | 24.5 bp |
| SOXL | mexc / gate | 2026-11-20 16:00 UTC | 27.4%/yr | 1.5 | -9.7 | 17.0 | -25.2 bp | -42.2 bp |

## 3. The weakness, the hypothesis and the experiment

**Largest weakness** (a class known when a position is opened, measured against the rest of the book): entry spread, *under 50%/yr*: 146 positions, mean -28.3 bp (t -7.88) against -9.2 bp for the rest (t of the difference -1.80); 2,784 bp lost beyond what the rest would have.

**Hypothesis.** Positions opened on a trailing spread under 50%/yr do not earn their round trip. Asking twice the spread at the entry removes them; whether the entries that remain earn more than cash is what the replay measures.

**Tested by** the declared variant `thick-entry` in the replay below.

### The replay: the radar's frozen rules and the declared variants on the same stored quotes

Stored hours in hand: 377 (2026-11-04 23:00 UTC to 2026-11-20 19:00 UTC); days archived: 16; added this cycle: none.

Fidelity: the replay of the original rules reproduces 65 of the radar's 68 real positions opened in these hours to the hundredth of a basis point (68 matched by entry). Differences: 0 only in the real ledger, 2 only in the replay; 2 of them on a coin the radar already held when the replay began (AKE, IDOL, SOL, SOXL, UAI). The replay is taken as faithful.

Earlier part 2026-11-07 22:00 UTC to 2026-11-14 00:00 UTC; later part to 2026-11-20 20:00 UTC. Excess over cash in % of the book.

| Variant | What changes | Earlier: excess | positions | Later: excess | positions | closed | t (daily) | Later, less the original | its t |
|---|---|---|---|---|---|---|---|---|---|
| `original` | nothing: the registered rules | 0.2419% | 28 | -0.6315% | 42 | 39 | -2.71 | 0.0000% | n/a |
| `same-window` | trailing_entry_h=24 | 0.1051% | 42 | -0.5572% | 41 | 38 | -6.32 | 0.0743% | 0.38 |
| `thick-entry` | entry_trailing_apr=0.5, entry_now_apr=0.3 | 0.3751% | 18 | -0.2893% | 17 | 17 | -4.54 | 0.3422% | 1.60 |
| `patient-exit` | exit_now_apr=-1.0 | 0.3137% | 25 | -0.4349% | 37 | 33 | -1.87 | 0.1965% | 2.49 |
| `all-three` | trailing_entry_h=24, entry_trailing_apr=0.5, entry_now_apr=0.3, exit_now_apr=-1.0 | 0.3626% | 23 | -0.1143% | 18 | 16 | -1.63 | 0.5171% | 2.71 |

Candidate, chosen on the earlier part only: `thick-entry` (4 variants compared). **INCONCLUSIVE**: the later part holds 7 days and 17 closed positions: 30 and 30 are needed before anything is judged.

Gates on the later part: enough days no, enough positions no, excess over cash no, beats the original no, costs x1.5 no, without best coin no.

A variant is proposed as a registered challenger only when every gate holds. A proposal is a request for a preregistered forward test, never a replacement of the original.

### Registered challengers, judged forward

None is registered. RADX-1, the diagnosis these variants came from, failed as registered (one of its two parts did not hold on the later positions), and by its own rule no challenger follows from it. One is registered only after a variant passes the gates above.


## 4. What is not claimed

- An unrealized gain is a valuation at the last close. It is not profit until the trade is closed.
- A variant that loses less than the original has not been shown to earn anything.
- No figure here is a backtest, and none is added to a research result.
