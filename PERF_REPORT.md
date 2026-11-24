# Paper systems: the performance audit and the optimization cycle

**PAPER ONLY · NOT REAL MONEY · NOTHING HERE IS A PROFIT CLAIM.** Written by the performance cycle on GitHub's runner (`scripts/perf_cycle.py`), with no person in the loop. It reads the paper systems' own ledgers, recomputes every figure by a second route, and changes neither system.

**بالعربي:** مكتب TRND-1: الرصيد $192,929.44، المحقّق -$2,660.70، غير المحقّق -$4,409.87، الصفقات المسكّرة 1. رادار RADAR-1: دفتره -2.60% من رأس ماله الورقي، 261 صفقة مسكّرة، الرابح منها 46. المطابقة: كل الأرقام تطابقت من مصدرين. تجربة التحسين: غير حاسمة لأن العيّنة صغيرة. المنافسين المسجّلين: 0. النظام الأصلي ما انلمس.

Updated 2026-11-24 03:17 UTC · perf-1.0.1 · cycles so far: 44

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

Marks from 2026-10-07 20:00 UTC to 2026-11-24 03:00 UTC (47.29 days). Paper only: no order is ever sent. Its preregistered single look is on 2026-12-06 and is read as registered, whatever this audit says.

Capital: ten slots of 2N: 20N. The radar has no cash account; N is not a dollar amount. P&L is in basis points (bp) of one leg's notional; 2,000 bp summed over positions is 1% of the book.

| | In bp of N | In % of the book | On a $100,000 book (illustration) |
|---|---|---|---|
| **Realized** (closed positions, after every fill) | -5,319.8 | -2.6599% | -$2,659.91 |
| **Unrealized** (open positions at their marks, entry fills paid) | 124.2 | 0.0621% | +$62.10 |
| The book if every open position were closed now | -5,246.1 | -2.6231% | -$2,623.06 |

| | |
|---|---|
| Closed positions | 261: 46 won, 215 lost |
| Win rate | 17.6% |
| Average win / average loss | 72.2 bp / -40.2 bp |
| Profit factor | 0.38 |
| Mean net a position | -20.4 bp (t -4.69) |
| Open positions | 3 of 10 slots; on average 25.5% of the capital was deployed |
| Book P&L | -2.5978% |
| Book excess over cash (3.875%/yr on the capital in use) | -2.7505% |
| Annualised excess on the capital deployed | -83.6%/yr |
| The same with costs x1.5 / x2 | -152.5% / -221.4% |
| Maximum drawdown of the book (hourly marks) | 2.6959% |
| t of the daily excess | -4.11 |
| Best coin, and the book's excess without it | INIT: -3.2048% |

### Where it came from

Funding received **3,587 bp**, price moves between the legs **57 bp**, fills **-8,964 bp**: net **-5,320 bp**. A position earned 14.0 bp before costs and paid 34.3 bp: the costs are 2.46 times the gross. Half the positions were closed within 3.0 hours.

| Held for | Positions | Won | Sum | Mean | t | Funding | Price | Costs |
|---|---|---|---|---|---|---|---|---|
| 1 hour or less | 82 | 5 | -2,752 bp | -33.6 bp | -6.13 | 46 | 30 | 2,828 |
| 1 to 6 hours | 92 | 16 | -2,738 bp | -29.8 bp | -4.38 | 887 | -486 | 3,139 |
| 6 to 24 hours | 58 | 14 | -419 bp | -7.2 bp | -0.81 | 1,265 | 318 | 2,001 |
| over 3 days | 5 | 2 | -38 bp | -7.7 bp | -0.71 | 168 | -31 | 176 |
| 1 to 3 days | 24 | 9 | 627 bp | 26.1 bp | 1.04 | 1,221 | 226 | 820 |

| Closed for | Positions | Won | Sum | Mean | t | Funding | Price | Costs |
|---|---|---|---|---|---|---|---|---|
| spread_reversed | 138 | 25 | -3,023 bp | -21.9 bp | -4.47 | 1,892 | -181 | 4,734 |
| spread_decayed | 76 | 3 | -2,708 bp | -35.6 bp | -15.16 | 131 | -212 | 2,627 |
| rebalance | 47 | 18 | 411 bp | 8.7 bp | 0.47 | 1,563 | 451 | 1,603 |

| Known at the entry: entry spread | Positions | Won | Sum | Mean | t | Funding | Price | Costs |
|---|---|---|---|---|---|---|---|---|
| under 50%/yr | 155 | 21 | -4,276 bp | -27.6 bp | -8.08 | 1,164 | -103 | 5,337 |
| 50 to 100%/yr | 65 | 14 | -845 bp | -13.0 bp | -1.20 | 954 | 415 | 2,214 |
| 100%/yr or more | 41 | 11 | -198 bp | -4.8 bp | -0.28 | 1,469 | -254 | 1,413 |

| Known at the entry: venue pair | Positions | Won | Sum | Mean | t | Funding | Price | Costs |
|---|---|---|---|---|---|---|---|---|
| short mexc / long gate | 203 | 36 | -4,500 bp | -22.2 bp | -4.96 | 2,236 | 166 | 6,902 |
| short gate / long mexc | 27 | 4 | -489 bp | -18.1 bp | -0.78 | 786 | -358 | 918 |
| short hyperliquid / long gate | 8 | 1 | -215 bp | -26.9 bp | -2.73 | 56 | 41 | 312 |
| short hyperliquid / long mexc | 9 | 1 | -163 bp | -18.1 bp | -1.50 | 202 | -68 | 297 |
| short mexc / long hyperliquid | 2 | 0 | -42 bp | -21.1 bp | -2.36 | 21 | 3 | 66 |
| short dydx / long gate | 1 | 0 | -23 bp | -22.9 bp | n/a | 13 | 4 | 40 |
| short gate / long hyperliquid | 11 | 4 | 113 bp | 10.3 bp | 0.46 | 273 | 269 | 429 |

| Known at the entry: time since the coin's previous position | Positions | Won | Sum | Mean | t | Funding | Price | Costs |
|---|---|---|---|---|---|---|---|---|
| within 6 hours of the coin's previous exit | 169 | 29 | -3,049 bp | -18.0 bp | -2.80 | 2,559 | 180 | 5,788 |
| a first entry, or later | 92 | 17 | -2,271 bp | -24.7 bp | -7.12 | 1,028 | -123 | 3,176 |

51 coins were traded and 46 of them lost. The five worst and the five best:

| Coin | Positions | Won | Sum | Mean | t | Funding | Price | Costs |
|---|---|---|---|---|---|---|---|---|
| AKE | 26 | 3 | -1,005 bp | -38.6 bp | -3.57 | 262 | -382 | 884 |
| BTW | 20 | 3 | -821 bp | -41.0 bp | -7.06 | 61 | -202 | 680 |
| IRYS | 18 | 3 | -620 bp | -34.5 bp | -4.50 | 212 | -220 | 612 |
| SOXL | 17 | 1 | -550 bp | -32.4 bp | -8.56 | 122 | -94 | 578 |
| AGT | 20 | 2 | -416 bp | -20.8 bp | -1.10 | 48 | 216 | 680 |
| INIT | 7 | 5 | 917 bp | 131.0 bp | 1.67 | 1,009 | 165 | 257 |
| IOST | 4 | 3 | 450 bp | 112.4 bp | 0.98 | 358 | 227 | 136 |
| BULLA | 8 | 4 | 267 bp | 33.4 bp | 0.55 | 276 | 264 | 272 |
| RSR | 3 | 3 | 58 bp | 19.4 bp | 1.47 | 67 | 98 | 107 |
| ESPORTS | 2 | 1 | 15 bp | 7.3 bp | 0.90 | 4 | 79 | 68 |

Concentration: the most traded coin (AKE) is 9.8% of the positions; by count the book is 22.3 equal coins. Venue pairs: short mexc / long gate 205, short gate / long mexc 27, short gate / long hyperliquid 11, short hyperliquid / long mexc 10, short hyperliquid / long gate 8, short mexc / long hyperliquid 2, short dydx / long gate 1.

| Open now | Short / long | Opened | Entry spread | Funding | Price | Fills paid | Net at the marks | Net if closed now |
|---|---|---|---|---|---|---|---|---|
| PIEVERSE | mexc / gate | 2026-11-22 17:00 UTC | 31.8%/yr | 7.5 | -2.7 | 17.0 | -12.3 bp | -29.3 bp |
| EVAA | mexc / gate | 2026-11-23 07:00 UTC | 50.7%/yr | 12.0 | -13.8 | 17.0 | -18.7 bp | -35.7 bp |
| ACE | hyperliquid / mexc | 2026-11-23 18:00 UTC | 89.1%/yr | 128.2 | 43.5 | 16.5 | 155.2 bp | 138.7 bp |

## 3. The weakness, the hypothesis and the experiment

**Largest weakness** (a class known when a position is opened, measured against the rest of the book): entry spread, *under 50%/yr*: 155 positions, mean -27.6 bp (t -8.08) against -9.8 bp for the rest (t of the difference -1.77); 2,751 bp lost beyond what the rest would have.

**Hypothesis.** Positions opened on a trailing spread under 50%/yr do not earn their round trip. Asking twice the spread at the entry removes them; whether the entries that remain earn more than cash is what the replay measures.

**Tested by** the declared variant `thick-entry` in the replay below.

### The replay: the radar's frozen rules and the declared variants on the same stored quotes

Stored hours in hand: 457 (2026-11-04 23:00 UTC to 2026-11-24 03:00 UTC); days archived: 20; added this cycle: 2026-11-23.

Fidelity: the replay of the original rules reproduces 83 of the radar's 83 real positions opened in these hours to the hundredth of a basis point (83 matched by entry). Differences: 0 only in the real ledger, 2 only in the replay; 2 of them on a coin the radar already held when the replay began (AKE, IDOL, SOL, SOXL, UAI). The replay is taken as faithful.

Earlier part 2026-11-07 22:00 UTC to 2026-11-16 00:00 UTC; later part to 2026-11-24 04:00 UTC. Excess over cash in % of the book.

| Variant | What changes | Earlier: excess | positions | Later: excess | positions | closed | t (daily) | Later, less the original | its t |
|---|---|---|---|---|---|---|---|---|---|
| `original` | nothing: the registered rules | 0.1602% | 36 | -0.6432% | 49 | 46 | -2.50 | 0.0000% | n/a |
| `same-window` | trailing_entry_h=24 | -0.0035% | 53 | -0.6985% | 51 | 48 | -3.72 | -0.0553% | -0.21 |
| `thick-entry` | entry_trailing_apr=0.5, entry_now_apr=0.3 | 0.2752% | 25 | -0.1850% | 18 | 16 | -1.92 | 0.4581% | 2.31 |
| `patient-exit` | exit_now_apr=-1.0 | 0.3578% | 30 | -0.5440% | 46 | 43 | -2.50 | 0.0991% | 1.85 |
| `all-three` | trailing_entry_h=24, entry_trailing_apr=0.5, entry_now_apr=0.3, exit_now_apr=-1.0 | 0.3829% | 27 | -0.1307% | 23 | 22 | -1.78 | 0.5125% | 2.53 |

Candidate, chosen on the earlier part only: `all-three` (4 variants compared). **INCONCLUSIVE**: the later part holds 9 days and 22 closed positions: 30 and 30 are needed before anything is judged.

Gates on the later part: enough days no, enough positions no, excess over cash no, beats the original no, costs x1.5 no, without best coin no.

A variant is proposed as a registered challenger only when every gate holds. A proposal is a request for a preregistered forward test, never a replacement of the original.

### Registered challengers, judged forward

None is registered. RADX-1, the diagnosis these variants came from, failed as registered (one of its two parts did not hold on the later positions), and by its own rule no challenger follows from it. One is registered only after a variant passes the gates above.


## 4. What is not claimed

- An unrealized gain is a valuation at the last close. It is not profit until the trade is closed.
- A variant that loses less than the original has not been shown to earn anything.
- No figure here is a backtest, and none is added to a research result.
