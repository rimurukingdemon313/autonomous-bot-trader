# Paper systems: the performance audit and the optimization cycle

**PAPER ONLY · NOT REAL MONEY · NOTHING HERE IS A PROFIT CLAIM.** Written by the performance cycle on GitHub's runner (`scripts/perf_cycle.py`), with no person in the loop. It reads the paper systems' own ledgers, recomputes every figure by a second route, and changes neither system.

**بالعربي:** مكتب TRND-1: الرصيد $194,787.97، المحقّق -$2,660.70، غير المحقّق -$2,551.34، الصفقات المسكّرة 1. رادار RADAR-1: دفتره -2.66% من رأس ماله الورقي، 265 صفقة مسكّرة، الرابح منها 47. المطابقة: كل الأرقام تطابقت من مصدرين. تجربة التحسين: غير حاسمة لأن العيّنة صغيرة. المنافسين المسجّلين: 0. النظام الأصلي ما انلمس.

Updated 2026-11-24 13:17 UTC · perf-1.0.1 · cycles so far: 45

## 1. TRND-1: the trend desk's paper account

**Reconciled: 37 of 37 checks hold.** Each compares two routes to the same figure.

Last session: 2026-11-23 21:00 UTC. Paper only: no real money.

| | |
|---|---|
| Initial capital | $200,000.00 |
| Equity now | $194,787.97 |
| **Realized** P&L (closed trades, after every cost) | -$2,660.70 from -$2,652.95 gross |
| **Unrealized** P&L (open trades at the last close: a valuation, not a profit) | -$2,551.34 |
| Net after all costs (realized plus unrealized) | -$5,212.03 (-2.606%) |
| Open positions | 3 |
| Closed trades | 1: 0 won, 1 lost |
| Win rate | 0.0% |
| Average win / average loss | undefined: no winning trade / -$2,660.70 |
| Profit factor | 0.00 |
| Maximum drawdown, session closes | $8,359.66 |
| Maximum drawdown, inside a day | $8,490.31 |
| Below the peak now | $6,501.13 |
| Gross exposure | $70,181.96, 0.36x the equity |
| Loss if every stop were hit from here | $4,208.46 (limit $8,000.00) |
| Losing days | 9 of 11 |

Trade statistics: sample **insufficient** (1 closed). A ratio over no closed trade does not exist and is not shown as zero.

### Open positions and where the risk sits

| Index | Units | Entry | Mark | Move | Unrealized | Notional | Share of gross | Stop | Loss at the stop from here |
|---|---|---|---|---|---|---|---|---|---|
| GER40 | 0.84 | 26,268.04 | 25,336.52 | -3.55% | -$858.36 | $23,346.51 | 33.3% | 23,817.03 | $1,400.14 |
| UK100 | 1.7 | 10,783.50 | 10,480.30 | -2.81% | -$674.53 | $23,315.46 | 33.2% | 9,851.95 | $1,397.89 |
| US500 | 3.25 | 7,550.29 | 7,236.92 | -4.15% | -$1,018.45 | $23,519.99 | 33.5% | 6,802.94 | $1,410.43 |

Concentration: 3 positions, the largest 33.5% of the gross; by size that is 3.0 equal positions, and by risk it is **one**: four equity indices, all long: one risk factor held four times.

### Against a benchmark

| | Since the start | What it is |
|---|---|---|
| The desk | -$5,212.03 | realized plus unrealized, after costs |
| Cash | +$301.24 | 3.875% a year on the starting balance for 14.19 days |
| The same indices bought and held | n/a | after an exit, holding on needs the index's later closes: not in these files |
| The same positions at one times the account | n/a | not computable from these files |

### Month by month, against the $4,000 target (a target, never a quota)

| Month | Days | Net | Of $4,000 |
|---|---|---|---|
| 2026-11 | 11 | -$5,212.03 | -130.3% |

## 2. RADAR-1: the funding radar's paper ledger

**Reconciled: 24 of 24 checks hold.** Each compares two routes to the same figure.

Marks from 2026-10-07 20:00 UTC to 2026-11-24 13:00 UTC (47.71 days). Paper only: no order is ever sent. Its preregistered single look is on 2026-12-06 and is read as registered, whatever this audit says.

Capital: ten slots of 2N: 20N. The radar has no cash account; N is not a dollar amount. P&L is in basis points (bp) of one leg's notional; 2,000 bp summed over positions is 1% of the book.

| | In bp of N | In % of the book | On a $100,000 book (illustration) |
|---|---|---|---|
| **Realized** (closed positions, after every fill) | -5,279.6 | -2.6398% | -$2,639.81 |
| **Unrealized** (open positions at their marks, entry fills paid) | -38.2 | -0.0191% | -$19.12 |
| The book if every open position were closed now | -5,334.8 | -2.6674% | -$2,667.43 |

| | |
|---|---|
| Closed positions | 265: 47 won, 218 lost |
| Win rate | 17.7% |
| Average win / average loss | 74.1 bp / -40.2 bp |
| Profit factor | 0.40 |
| Mean net a position | -19.9 bp (t -4.59) |
| Open positions | 1 of 10 slots; on average 25.4% of the capital was deployed |
| Book P&L | -2.6589% |
| Book excess over cash (3.875%/yr on the capital in use) | -2.7958% |
| Annualised excess on the capital deployed | -84.4%/yr |
| The same with costs x1.5 / x2 | -153.4% / -222.3% |
| Maximum drawdown of the book (hourly marks) | 2.6959% |
| t of the daily excess | -4.23 |
| Best coin, and the book's excess without it | INIT: -3.2501% |

### Where it came from

Funding received **3,739 bp**, price moves between the legs **81 bp**, fills **-9,099 bp**: net **-5,280 bp**. A position earned 14.4 bp before costs and paid 34.3 bp: the costs are 2.38 times the gross. Half the positions were closed within 4.0 hours.

| Held for | Positions | Won | Sum | Mean | t | Funding | Price | Costs |
|---|---|---|---|---|---|---|---|---|
| 1 to 6 hours | 93 | 16 | -2,780 bp | -29.9 bp | -4.45 | 888 | -495 | 3,173 |
| 1 hour or less | 82 | 5 | -2,752 bp | -33.6 bp | -6.13 | 46 | 30 | 2,828 |
| 6 to 24 hours | 60 | 15 | -306 bp | -5.1 bp | -0.56 | 1,408 | 354 | 2,068 |
| over 3 days | 5 | 2 | -38 bp | -7.7 bp | -0.71 | 168 | -31 | 176 |
| 1 to 3 days | 25 | 9 | 597 bp | 23.9 bp | 0.98 | 1,229 | 222 | 854 |

| Closed for | Positions | Won | Sum | Mean | t | Funding | Price | Costs |
|---|---|---|---|---|---|---|---|---|
| spread_reversed | 140 | 26 | -2,893 bp | -20.7 bp | -4.13 | 2,031 | -123 | 4,801 |
| spread_decayed | 77 | 3 | -2,750 bp | -35.7 bp | -15.38 | 132 | -221 | 2,661 |
| rebalance | 48 | 18 | 364 bp | 7.6 bp | 0.42 | 1,576 | 425 | 1,637 |

| Known at the entry: entry spread | Positions | Won | Sum | Mean | t | Funding | Price | Costs |
|---|---|---|---|---|---|---|---|---|
| under 50%/yr | 156 | 21 | -4,307 bp | -27.6 bp | -8.14 | 1,172 | -108 | 5,371 |
| 50 to 100%/yr | 68 | 15 | -775 bp | -11.4 bp | -1.07 | 1,098 | 442 | 2,315 |
| 100%/yr or more | 41 | 11 | -198 bp | -4.8 bp | -0.28 | 1,469 | -254 | 1,413 |

| Known at the entry: venue pair | Positions | Won | Sum | Mean | t | Funding | Price | Costs |
|---|---|---|---|---|---|---|---|---|
| short mexc / long gate | 206 | 36 | -4,620 bp | -22.4 bp | -5.09 | 2,257 | 128 | 7,004 |
| short gate / long mexc | 27 | 4 | -489 bp | -18.1 bp | -0.78 | 786 | -358 | 918 |
| short hyperliquid / long gate | 8 | 1 | -215 bp | -26.9 bp | -2.73 | 56 | 41 | 312 |
| short mexc / long hyperliquid | 2 | 0 | -42 bp | -21.1 bp | -2.36 | 21 | 3 | 66 |
| short dydx / long gate | 1 | 0 | -23 bp | -22.9 bp | n/a | 13 | 4 | 40 |
| short hyperliquid / long mexc | 10 | 2 | -3 bp | -0.3 bp | -0.02 | 333 | -6 | 330 |
| short gate / long hyperliquid | 11 | 4 | 113 bp | 10.3 bp | 0.46 | 273 | 269 | 429 |

| Known at the entry: time since the coin's previous position | Positions | Won | Sum | Mean | t | Funding | Price | Costs |
|---|---|---|---|---|---|---|---|---|
| within 6 hours of the coin's previous exit | 172 | 30 | -2,966 bp | -17.2 bp | -2.69 | 2,710 | 212 | 5,889 |
| a first entry, or later | 93 | 17 | -2,313 bp | -24.9 bp | -7.24 | 1,028 | -132 | 3,210 |

51 coins were traded and 45 of them lost. The five worst and the five best:

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
| ACE | 2 | 1 | 127 bp | 63.7 bp | 0.66 | 170 | 23 | 66 |
| RSR | 3 | 3 | 58 bp | 19.4 bp | 1.47 | 67 | 98 | 107 |

Concentration: the most traded coin (AKE) is 9.8% of the positions; by count the book is 22.4 equal coins. Venue pairs: short mexc / long gate 207, short gate / long mexc 27, short gate / long hyperliquid 11, short hyperliquid / long mexc 10, short hyperliquid / long gate 8, short mexc / long hyperliquid 2, short dydx / long gate 1.

| Open now | Short / long | Opened | Entry spread | Funding | Price | Fills paid | Net at the marks | Net if closed now |
|---|---|---|---|---|---|---|---|---|
| EVAA | mexc / gate | 2026-11-24 04:00 UTC | 43.5%/yr | 1.8 | -23.0 | 17.0 | -38.2 bp | -55.2 bp |

## 3. The weakness, the hypothesis and the experiment

**Largest weakness** (a class known when a position is opened, measured against the rest of the book): entry spread, *under 50%/yr*: 156 positions, mean -27.6 bp (t -8.14) against -8.9 bp for the rest (t of the difference -1.89); 2,915 bp lost beyond what the rest would have.

**Hypothesis.** Positions opened on a trailing spread under 50%/yr do not earn their round trip. Asking twice the spread at the entry removes them; whether the entries that remain earn more than cash is what the replay measures.

**Tested by** the declared variant `thick-entry` in the replay below.

### The replay: the radar's frozen rules and the declared variants on the same stored quotes

Stored hours in hand: 467 (2026-11-04 23:00 UTC to 2026-11-24 13:00 UTC); days archived: 20; added this cycle: none.

Fidelity: the replay of the original rules reproduces 85 of the radar's 85 real positions opened in these hours to the hundredth of a basis point (85 matched by entry). Differences: 0 only in the real ledger, 2 only in the replay; 2 of them on a coin the radar already held when the replay began (AKE, IDOL, SOL, SOXL, UAI). The replay is taken as faithful.

Earlier part 2026-11-07 22:00 UTC to 2026-11-16 00:00 UTC; later part to 2026-11-24 14:00 UTC. Excess over cash in % of the book.

| Variant | What changes | Earlier: excess | positions | Later: excess | positions | closed | t (daily) | Later, less the original | its t |
|---|---|---|---|---|---|---|---|---|---|
| `original` | nothing: the registered rules | 0.1602% | 36 | -0.7052% | 51 | 50 | -2.95 | 0.0000% | n/a |
| `same-window` | trailing_entry_h=24 | -0.0035% | 53 | -0.7392% | 52 | 51 | -4.41 | -0.0340% | -0.13 |
| `thick-entry` | entry_trailing_apr=0.5, entry_now_apr=0.3 | 0.2752% | 25 | -0.1970% | 18 | 18 | -2.16 | 0.5082% | 2.67 |
| `patient-exit` | exit_now_apr=-1.0 | 0.3578% | 30 | -0.6113% | 48 | 46 | -3.00 | 0.0938% | 1.67 |
| `all-three` | trailing_entry_h=24, entry_trailing_apr=0.5, entry_now_apr=0.3, exit_now_apr=-1.0 | 0.3829% | 27 | -0.1588% | 24 | 23 | -2.26 | 0.5463% | 2.85 |

Candidate, chosen on the earlier part only: `all-three` (4 variants compared). **INCONCLUSIVE**: the later part holds 9 days and 23 closed positions: 30 and 30 are needed before anything is judged.

Gates on the later part: enough days no, enough positions no, excess over cash no, beats the original no, costs x1.5 no, without best coin no.

A variant is proposed as a registered challenger only when every gate holds. A proposal is a request for a preregistered forward test, never a replacement of the original.

### Registered challengers, judged forward

None is registered. RADX-1, the diagnosis these variants came from, failed as registered (one of its two parts did not hold on the later positions), and by its own rule no challenger follows from it. One is registered only after a variant passes the gates above.


## 4. What is not claimed

- An unrealized gain is a valuation at the last close. It is not profit until the trade is closed.
- A variant that loses less than the original has not been shown to earn anything.
- No figure here is a backtest, and none is added to a research result.
