# Paper systems: the performance audit and the optimization cycle

**PAPER ONLY · NOT REAL MONEY · NOTHING HERE IS A PROFIT CLAIM.** Written by the performance cycle on GitHub's runner (`scripts/perf_cycle.py`), with no person in the loop. It reads the paper systems' own ledgers, recomputes every figure by a second route, and changes neither system.

**بالعربي:** مكتب TRND-1: الرصيد $192,929.44، المحقّق -$2,660.70، غير المحقّق -$4,409.87، الصفقات المسكّرة 1. رادار RADAR-1: دفتره -2.54% من رأس ماله الورقي، 248 صفقة مسكّرة، الرابح منها 44. المطابقة: كل الأرقام تطابقت من مصدرين. تجربة التحسين: غير حاسمة لأن العيّنة صغيرة. المنافسين المسجّلين: 0. النظام الأصلي ما انلمس.

Updated 2026-11-21 20:17 UTC · perf-1.0.1 · cycles so far: 34

## 1. TRND-1: the trend desk's paper account

**Reconciled: 37 of 37 checks hold.** Each compares two routes to the same figure.

Last session: 2026-11-20 21:00 UTC. Paper only: no real money.

| | |
|---|---|
| Initial capital | $200,000.00 |
| Equity now | $192,929.44 |
| **Realized** P&L (closed trades, after every cost) | -$2,660.70 from -$2,652.95 gross |
| **Unrealized** P&L (open trades at the last close: a valuation, not a profit) | -$4,409.87 |
| Net after all costs (realized plus unrealized) | -$7,070.56 (-3.535%) |
| Open positions | 3 |
| Closed trades | 1: 0 won, 1 lost |
| Win rate | 0.0% |
| Average win / average loss | undefined: no winning trade / -$2,660.70 |
| Profit factor | 0.00 |
| Maximum drawdown, session closes | $8,359.66 |
| Maximum drawdown, inside a day | $8,490.31 |
| Below the peak now | $8,359.66 |
| Gross exposure | $68,438.86, 0.35x the equity |
| Loss if every stop were hit from here | $2,720.27 (limit $8,000.00) |
| Losing days | 9 of 10 |

Trade statistics: sample **insufficient** (1 closed). A ratio over no closed trade does not exist and is not shown as zero.

### Open positions and where the risk sits

| Index | Units | Entry | Mark | Move | Unrealized | Notional | Share of gross | Stop | Loss at the stop from here |
|---|---|---|---|---|---|---|---|---|---|
| GER40 | 0.84 | 26,268.04 | 24,802.03 | -5.58% | -$1,351.15 | $22,858.76 | 33.4% | 23,935.98 | $798.19 |
| UK100 | 1.7 | 10,783.50 | 10,345.80 | -4.06% | -$978.23 | $23,122.14 | 33.8% | 9,725.52 | $1,386.28 |
| US500 | 3.25 | 7,550.29 | 6,910.14 | -8.48% | -$2,080.49 | $22,457.96 | 32.8% | 6,745.28 | $535.80 |

Concentration: 3 positions, the largest 33.8% of the gross; by size that is 3.0 equal positions, and by risk it is **one**: four equity indices, all long: one risk factor held four times.

### Against a benchmark

| | Since the start | What it is |
|---|---|---|
| The desk | -$7,070.56 | realized plus unrealized, after costs |
| Cash | +$237.54 | 3.875% a year on the starting balance for 11.19 days |
| The same indices bought and held | n/a | after an exit, holding on needs the index's later closes: not in these files |
| The same positions at one times the account | n/a | not computable from these files |

### Month by month, against the $4,000 target (a target, never a quota)

| Month | Days | Net | Of $4,000 |
|---|---|---|---|
| 2026-11 | 10 | -$7,070.56 | -176.8% |

## 2. RADAR-1: the funding radar's paper ledger

**Reconciled: 24 of 24 checks hold.** Each compares two routes to the same figure.

Marks from 2026-10-07 20:00 UTC to 2026-11-21 20:00 UTC (45.00 days). Paper only: no order is ever sent. Its preregistered single look is on 2026-12-06 and is read as registered, whatever this audit says.

Capital: ten slots of 2N: 20N. The radar has no cash account; N is not a dollar amount. P&L is in basis points (bp) of one leg's notional; 2,000 bp summed over positions is 1% of the book.

| | In bp of N | In % of the book | On a $100,000 book (illustration) |
|---|---|---|---|
| **Realized** (closed positions, after every fill) | -5,062.1 | -2.5310% | -$2,531.03 |
| **Unrealized** (open positions at their marks, entry fills paid) | -13.1 | -0.0065% | -$6.54 |
| The book if every open position were closed now | -5,126.2 | -2.5631% | -$2,563.07 |

| | |
|---|---|
| Closed positions | 248: 44 won, 204 lost |
| Win rate | 17.7% |
| Average win / average loss | 74.4 bp / -40.9 bp |
| Profit factor | 0.39 |
| Mean net a position | -20.4 bp (t -4.47) |
| Open positions | 3 of 10 slots; on average 25.1% of the capital was deployed |
| Book P&L | -2.5376% |
| Book excess over cash (3.875%/yr on the capital in use) | -2.6824% |
| Annualised excess on the capital deployed | -87.1%/yr |
| The same with costs x1.5 / x2 | -157.1% / -227.1% |
| Maximum drawdown of the book (hourly marks) | 2.5418% |
| t of the daily excess | -4.04 |
| Best coin, and the book's excess without it | INIT: -3.1367% |

### Where it came from

Funding received **3,435 bp**, price moves between the legs **26 bp**, fills **-8,523 bp**: net **-5,062 bp**. A position earned 14.0 bp before costs and paid 34.4 bp: the costs are 2.46 times the gross. Half the positions were closed within 3.0 hours.

| Held for | Positions | Won | Sum | Mean | t | Funding | Price | Costs |
|---|---|---|---|---|---|---|---|---|
| 1 hour or less | 82 | 5 | -2,752 bp | -33.6 bp | -6.13 | 46 | 30 | 2,828 |
| 1 to 6 hours | 87 | 15 | -2,639 bp | -30.3 bp | -4.24 | 840 | -509 | 2,970 |
| 6 to 24 hours | 52 | 14 | -275 bp | -5.3 bp | -0.54 | 1,223 | 299 | 1,797 |
| over 3 days | 4 | 1 | -62 bp | -15.5 bp | -1.59 | 127 | -47 | 142 |
| 1 to 3 days | 23 | 9 | 666 bp | 29.0 bp | 1.11 | 1,200 | 253 | 786 |

| Closed for | Positions | Won | Sum | Mean | t | Funding | Price | Costs |
|---|---|---|---|---|---|---|---|---|
| spread_reversed | 134 | 25 | -2,894 bp | -21.6 bp | -4.28 | 1,844 | -139 | 4,599 |
| spread_decayed | 76 | 3 | -2,708 bp | -35.6 bp | -15.16 | 131 | -212 | 2,627 |
| rebalance | 38 | 16 | 540 bp | 14.2 bp | 0.63 | 1,460 | 377 | 1,297 |

| Known at the entry: entry spread | Positions | Won | Sum | Mean | t | Funding | Price | Costs |
|---|---|---|---|---|---|---|---|---|
| under 50%/yr | 148 | 20 | -4,143 bp | -28.0 bp | -7.88 | 1,072 | -116 | 5,099 |
| 50 to 100%/yr | 59 | 13 | -721 bp | -12.2 bp | -1.03 | 894 | 396 | 2,011 |
| 100%/yr or more | 41 | 11 | -198 bp | -4.8 bp | -0.28 | 1,469 | -254 | 1,413 |

| Known at the entry: venue pair | Positions | Won | Sum | Mean | t | Funding | Price | Costs |
|---|---|---|---|---|---|---|---|---|
| short mexc / long gate | 193 | 34 | -4,331 bp | -22.4 bp | -4.79 | 2,141 | 90 | 6,562 |
| short gate / long mexc | 25 | 4 | -433 bp | -17.3 bp | -0.69 | 769 | -352 | 850 |
| short hyperliquid / long gate | 8 | 1 | -215 bp | -26.9 bp | -2.73 | 56 | 41 | 312 |
| short hyperliquid / long mexc | 8 | 1 | -131 bp | -16.3 bp | -1.21 | 162 | -29 | 264 |
| short mexc / long hyperliquid | 2 | 0 | -42 bp | -21.1 bp | -2.36 | 21 | 3 | 66 |
| short dydx / long gate | 1 | 0 | -23 bp | -22.9 bp | n/a | 13 | 4 | 40 |
| short gate / long hyperliquid | 11 | 4 | 113 bp | 10.3 bp | 0.46 | 273 | 269 | 429 |

| Known at the entry: time since the coin's previous position | Positions | Won | Sum | Mean | t | Funding | Price | Costs |
|---|---|---|---|---|---|---|---|---|
| within 6 hours of the coin's previous exit | 161 | 27 | -2,933 bp | -18.2 bp | -2.70 | 2,494 | 89 | 5,516 |
| a first entry, or later | 87 | 17 | -2,129 bp | -24.5 bp | -6.69 | 941 | -63 | 3,007 |

50 coins were traded and 44 of them lost. The five worst and the five best:

| Coin | Positions | Won | Sum | Mean | t | Funding | Price | Costs |
|---|---|---|---|---|---|---|---|---|
| AKE | 26 | 3 | -1,005 bp | -38.6 bp | -3.57 | 262 | -382 | 884 |
| BTW | 20 | 3 | -821 bp | -41.0 bp | -7.06 | 61 | -202 | 680 |
| IRYS | 18 | 3 | -620 bp | -34.5 bp | -4.50 | 212 | -220 | 612 |
| SOXL | 15 | 1 | -485 bp | -32.3 bp | -7.60 | 96 | -71 | 510 |
| AGT | 20 | 2 | -416 bp | -20.8 bp | -1.10 | 48 | 216 | 680 |
| INIT | 7 | 5 | 917 bp | 131.0 bp | 1.67 | 1,009 | 165 | 257 |
| IOST | 4 | 3 | 450 bp | 112.4 bp | 0.98 | 358 | 227 | 136 |
| BULLA | 8 | 4 | 267 bp | 33.4 bp | 0.55 | 276 | 264 | 272 |
| RSR | 3 | 3 | 58 bp | 19.4 bp | 1.47 | 67 | 98 | 107 |
| IDOL | 2 | 1 | 20 bp | 10.0 bp | 0.52 | 74 | 14 | 68 |

Concentration: the most traded coin (AKE) is 10.4% of the positions; by count the book is 21.4 equal coins. Venue pairs: short mexc / long gate 196, short gate / long mexc 25, short gate / long hyperliquid 11, short hyperliquid / long gate 8, short hyperliquid / long mexc 8, short mexc / long hyperliquid 2, short dydx / long gate 1.

| Open now | Short / long | Opened | Entry spread | Funding | Price | Fills paid | Net at the marks | Net if closed now |
|---|---|---|---|---|---|---|---|---|
| PIEVERSE | mexc / gate | 2026-11-18 18:00 UTC | 26.1%/yr | 34.3 | 1.0 | 17.0 | 18.4 bp | 1.4 bp |
| EVAA | mexc / gate | 2026-11-21 08:00 UTC | 60.8%/yr | 7.2 | -4.3 | 17.0 | -14.1 bp | -31.1 bp |
| SOXL | mexc / gate | 2026-11-21 18:00 UTC | 25.9%/yr | 2.7 | -3.1 | 17.0 | -17.4 bp | -34.4 bp |

## 3. The weakness, the hypothesis and the experiment

**Largest weakness** (a class known when a position is opened, measured against the rest of the book): entry spread, *under 50%/yr*: 148 positions, mean -28.0 bp (t -7.88) against -9.2 bp for the rest (t of the difference -1.78); 2,782 bp lost beyond what the rest would have.

**Hypothesis.** Positions opened on a trailing spread under 50%/yr do not earn their round trip. Asking twice the spread at the entry removes them; whether the entries that remain earn more than cash is what the replay measures.

**Tested by** the declared variant `thick-entry` in the replay below.

### The replay: the radar's frozen rules and the declared variants on the same stored quotes

Stored hours in hand: 402 (2026-11-04 23:00 UTC to 2026-11-21 20:00 UTC); days archived: 17; added this cycle: none.

Fidelity: the replay of the original rules reproduces 70 of the radar's 70 real positions opened in these hours to the hundredth of a basis point (70 matched by entry). Differences: 0 only in the real ledger, 2 only in the replay; 2 of them on a coin the radar already held when the replay began (AKE, IDOL, SOL, SOXL, UAI). The replay is taken as faithful.

Earlier part 2026-11-07 22:00 UTC to 2026-11-14 00:00 UTC; later part to 2026-11-21 21:00 UTC. Excess over cash in % of the book.

| Variant | What changes | Earlier: excess | positions | Later: excess | positions | closed | t (daily) | Later, less the original | its t |
|---|---|---|---|---|---|---|---|---|---|
| `original` | nothing: the registered rules | 0.2419% | 28 | -0.6565% | 44 | 41 | -2.75 | 0.0000% | n/a |
| `same-window` | trailing_entry_h=24 | 0.1051% | 42 | -0.7490% | 49 | 47 | -4.99 | -0.0925% | -0.36 |
| `thick-entry` | entry_trailing_apr=0.5, entry_now_apr=0.3 | 0.3751% | 18 | -0.2863% | 18 | 17 | -4.15 | 0.3702% | 1.74 |
| `patient-exit` | exit_now_apr=-1.0 | 0.3137% | 25 | -0.4706% | 39 | 36 | -2.03 | 0.1859% | 2.15 |
| `all-three` | trailing_entry_h=24, entry_trailing_apr=0.5, entry_now_apr=0.3, exit_now_apr=-1.0 | 0.3626% | 23 | -0.1242% | 19 | 17 | -1.88 | 0.5323% | 2.70 |

Candidate, chosen on the earlier part only: `thick-entry` (4 variants compared). **INCONCLUSIVE**: the later part holds 8 days and 17 closed positions: 30 and 30 are needed before anything is judged.

Gates on the later part: enough days no, enough positions no, excess over cash no, beats the original no, costs x1.5 no, without best coin no.

A variant is proposed as a registered challenger only when every gate holds. A proposal is a request for a preregistered forward test, never a replacement of the original.

### Registered challengers, judged forward

None is registered. RADX-1, the diagnosis these variants came from, failed as registered (one of its two parts did not hold on the later positions), and by its own rule no challenger follows from it. One is registered only after a variant passes the gates above.


## 4. What is not claimed

- An unrealized gain is a valuation at the last close. It is not profit until the trade is closed.
- A variant that loses less than the original has not been shown to earn anything.
- No figure here is a backtest, and none is added to a research result.
