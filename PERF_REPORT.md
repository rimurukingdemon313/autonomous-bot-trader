# Paper systems: the performance audit and the optimization cycle

**PAPER ONLY · NOT REAL MONEY · NOTHING HERE IS A PROFIT CLAIM.** Written by the performance cycle on GitHub's runner (`scripts/perf_cycle.py`), with no person in the loop. It reads the paper systems' own ledgers, recomputes every figure by a second route, and changes neither system.

**بالعربي:** مكتب TRND-1: الرصيد $193,917.29، المحقّق -$2,660.70، غير المحقّق -$3,422.02، الصفقات المسكّرة 1. رادار RADAR-1: دفتره -2.78% من رأس ماله الورقي، 275 صفقة مسكّرة، الرابح منها 48. المطابقة: كل الأرقام تطابقت من مصدرين. تجربة التحسين: غير حاسمة لأن العيّنة صغيرة. المنافسين المسجّلين: 0. النظام الأصلي ما انلمس.

Updated 2026-11-26 17:05 UTC · perf-1.0.1 · cycles so far: 55

## 1. TRND-1: the trend desk's paper account

**Reconciled: 37 of 37 checks hold.** Each compares two routes to the same figure.

Last session: 2026-11-25 21:00 UTC. Paper only: no real money.

| | |
|---|---|
| Initial capital | $200,000.00 |
| Equity now | $193,917.29 |
| **Realized** P&L (closed trades, after every cost) | -$2,660.70 from -$2,652.95 gross |
| **Unrealized** P&L (open trades at the last close: a valuation, not a profit) | -$3,422.02 |
| Net after all costs (realized plus unrealized) | -$6,082.71 (-3.041%) |
| Open positions | 3 |
| Closed trades | 1: 0 won, 1 lost |
| Win rate | 0.0% |
| Average win / average loss | undefined: no winning trade / -$2,660.70 |
| Profit factor | 0.00 |
| Maximum drawdown, session closes | $8,359.66 |
| Maximum drawdown, inside a day | $8,490.31 |
| Below the peak now | $7,371.81 |
| Gross exposure | $69,080.55, 0.36x the equity |
| Loss if every stop were hit from here | $4,142.32 (limit $8,000.00) |
| Losing days | 11 of 13 |

Trade statistics: sample **insufficient** (1 closed). A ratio over no closed trade does not exist and is not shown as zero.

### Open positions and where the risk sits

| Index | Units | Entry | Mark | Move | Unrealized | Notional | Share of gross | Stop | Loss at the stop from here |
|---|---|---|---|---|---|---|---|---|---|
| GER40 | 0.84 | 26,268.04 | 24,701.38 | -5.96% | -$1,435.50 | $22,633.39 | 32.8% | 23,220.00 | $1,357.36 |
| UK100 | 1.7 | 10,783.50 | 10,426.40 | -3.31% | -$791.30 | $23,103.94 | 33.4% | 9,801.32 | $1,385.12 |
| US500 | 3.25 | 7,550.29 | 7,182.53 | -4.87% | -$1,195.22 | $23,343.22 | 33.8% | 6,751.81 | $1,399.84 |

Concentration: 3 positions, the largest 33.8% of the gross; by size that is 3.0 equal positions, and by risk it is **one**: four equity indices, all long: one risk factor held four times.

### Against a benchmark

| | Since the start | What it is |
|---|---|---|
| The desk | -$6,082.71 | realized plus unrealized, after costs |
| Cash | +$343.71 | 3.875% a year on the starting balance for 16.19 days |
| The same indices bought and held | n/a | after an exit, holding on needs the index's later closes: not in these files |
| The same positions at one times the account | n/a | not computable from these files |

### Month by month, against the $4,000 target (a target, never a quota)

| Month | Days | Net | Of $4,000 |
|---|---|---|---|
| 2026-11 | 13 | -$6,082.71 | -152.1% |

## 2. RADAR-1: the funding radar's paper ledger

**Reconciled: 24 of 24 checks hold.** Each compares two routes to the same figure.

Marks from 2026-10-07 20:00 UTC to 2026-11-26 16:00 UTC (49.83 days). Paper only: no order is ever sent. Its preregistered single look is on 2026-12-06 and is read as registered, whatever this audit says.

Capital: ten slots of 2N: 20N. The radar has no cash account; N is not a dollar amount. P&L is in basis points (bp) of one leg's notional; 2,000 bp summed over positions is 1% of the book.

| | In bp of N | In % of the book | On a $100,000 book (illustration) |
|---|---|---|---|
| **Realized** (closed positions, after every fill) | -5,533.5 | -2.7668% | -$2,766.77 |
| **Unrealized** (open positions at their marks, entry fills paid) | -23.5 | -0.0118% | -$11.76 |
| The book if every open position were closed now | -5,574.0 | -2.7870% | -$2,787.03 |

| | |
|---|---|
| Closed positions | 275: 48 won, 227 lost |
| Win rate | 17.5% |
| Average win / average loss | 73.6 bp / -39.9 bp |
| Profit factor | 0.39 |
| Mean net a position | -20.1 bp (t -4.80) |
| Open positions | 1 of 10 slots; on average 25.4% of the capital was deployed |
| Book P&L | -2.7785% |
| Book excess over cash (3.875%/yr on the capital in use) | -2.9211% |
| Annualised excess on the capital deployed | -84.4%/yr |
| The same with costs x1.5 / x2 | -152.9% / -221.3% |
| Maximum drawdown of the book (hourly marks) | 2.7964% |
| t of the daily excess | -4.40 |
| Best coin, and the book's excess without it | INIT: -3.3754% |

### Where it came from

Funding received **3,775 bp**, price moves between the legs **131 bp**, fills **-9,439 bp**: net **-5,534 bp**. A position earned 14.2 bp before costs and paid 34.3 bp: the costs are 2.42 times the gross. Half the positions were closed within 4.0 hours.

| Held for | Positions | Won | Sum | Mean | t | Funding | Price | Costs |
|---|---|---|---|---|---|---|---|---|
| 1 hour or less | 88 | 5 | -2,956 bp | -33.6 bp | -6.58 | 50 | 26 | 3,032 |
| 1 to 6 hours | 93 | 16 | -2,780 bp | -29.9 bp | -4.45 | 888 | -495 | 3,173 |
| 6 to 24 hours | 62 | 15 | -344 bp | -5.5 bp | -0.63 | 1,424 | 368 | 2,136 |
| over 3 days | 5 | 2 | -38 bp | -7.7 bp | -0.71 | 168 | -31 | 176 |
| 1 to 3 days | 27 | 10 | 585 bp | 21.7 bp | 0.96 | 1,245 | 262 | 922 |

| Closed for | Positions | Won | Sum | Mean | t | Funding | Price | Costs |
|---|---|---|---|---|---|---|---|---|
| spread_reversed | 143 | 26 | -2,992 bp | -20.9 bp | -4.26 | 2,055 | -144 | 4,903 |
| spread_decayed | 83 | 3 | -2,954 bp | -35.6 bp | -16.50 | 136 | -225 | 2,865 |
| rebalance | 49 | 19 | 413 bp | 8.4 bp | 0.47 | 1,584 | 500 | 1,671 |

| Known at the entry: entry spread | Positions | Won | Sum | Mean | t | Funding | Price | Costs |
|---|---|---|---|---|---|---|---|---|
| under 50%/yr | 166 | 22 | -4,561 bp | -27.5 bp | -8.50 | 1,208 | -58 | 5,711 |
| 50 to 100%/yr | 68 | 15 | -775 bp | -11.4 bp | -1.07 | 1,098 | 442 | 2,315 |
| 100%/yr or more | 41 | 11 | -198 bp | -4.8 bp | -0.28 | 1,469 | -254 | 1,413 |

| Known at the entry: venue pair | Positions | Won | Sum | Mean | t | Funding | Price | Costs |
|---|---|---|---|---|---|---|---|---|
| short mexc / long gate | 211 | 37 | -4,730 bp | -22.4 bp | -5.19 | 2,277 | 168 | 7,174 |
| short gate / long mexc | 32 | 4 | -633 bp | -19.8 bp | -1.01 | 802 | -348 | 1,088 |
| short hyperliquid / long gate | 8 | 1 | -215 bp | -26.9 bp | -2.73 | 56 | 41 | 312 |
| short mexc / long hyperliquid | 2 | 0 | -42 bp | -21.1 bp | -2.36 | 21 | 3 | 66 |
| short dydx / long gate | 1 | 0 | -23 bp | -22.9 bp | n/a | 13 | 4 | 40 |
| short hyperliquid / long mexc | 10 | 2 | -3 bp | -0.3 bp | -0.02 | 333 | -6 | 330 |
| short gate / long hyperliquid | 11 | 4 | 113 bp | 10.3 bp | 0.46 | 273 | 269 | 429 |

| Known at the entry: time since the coin's previous position | Positions | Won | Sum | Mean | t | Funding | Price | Costs |
|---|---|---|---|---|---|---|---|---|
| within 6 hours of the coin's previous exit | 179 | 31 | -3,120 bp | -17.4 bp | -2.82 | 2,743 | 264 | 6,127 |
| a first entry, or later | 96 | 17 | -2,414 bp | -25.1 bp | -7.55 | 1,032 | -133 | 3,312 |

51 coins were traded and 45 of them lost. The five worst and the five best:

| Coin | Positions | Won | Sum | Mean | t | Funding | Price | Costs |
|---|---|---|---|---|---|---|---|---|
| AKE | 26 | 3 | -1,005 bp | -38.6 bp | -3.57 | 262 | -382 | 884 |
| BTW | 20 | 3 | -821 bp | -41.0 bp | -7.06 | 61 | -202 | 680 |
| SOXL | 20 | 1 | -679 bp | -33.9 bp | -9.69 | 130 | -129 | 680 |
| IRYS | 18 | 3 | -620 bp | -34.5 bp | -4.50 | 212 | -220 | 612 |
| AGT | 20 | 2 | -416 bp | -20.8 bp | -1.10 | 48 | 216 | 680 |
| INIT | 7 | 5 | 917 bp | 131.0 bp | 1.67 | 1,009 | 165 | 257 |
| IOST | 4 | 3 | 450 bp | 112.4 bp | 0.98 | 358 | 227 | 136 |
| BULLA | 8 | 4 | 267 bp | 33.4 bp | 0.55 | 276 | 264 | 272 |
| ACE | 2 | 1 | 127 bp | 63.7 bp | 0.66 | 170 | 23 | 66 |
| RSR | 3 | 3 | 58 bp | 19.4 bp | 1.47 | 67 | 98 | 107 |

Concentration: the most traded coin (AKE) is 9.4% of the positions; by count the book is 22.7 equal coins. Venue pairs: short mexc / long gate 212, short gate / long mexc 32, short gate / long hyperliquid 11, short hyperliquid / long mexc 10, short hyperliquid / long gate 8, short mexc / long hyperliquid 2, short dydx / long gate 1.

| Open now | Short / long | Opened | Entry spread | Funding | Price | Fills paid | Net at the marks | Net if closed now |
|---|---|---|---|---|---|---|---|---|
| EVAA | mexc / gate | 2026-11-25 11:00 UTC | 31.8%/yr | 21.3 | -27.8 | 17.0 | -23.5 bp | -40.5 bp |

## 3. The weakness, the hypothesis and the experiment

**Largest weakness** (a class known when a position is opened, measured against the rest of the book): entry spread, *under 50%/yr*: 166 positions, mean -27.5 bp (t -8.50) against -8.9 bp for the rest (t of the difference -1.89); 3,079 bp lost beyond what the rest would have.

**Hypothesis.** Positions opened on a trailing spread under 50%/yr do not earn their round trip. Asking twice the spread at the entry removes them; whether the entries that remain earn more than cash is what the replay measures.

**Tested by** the declared variant `thick-entry` in the replay below.

### The replay: the radar's frozen rules and the declared variants on the same stored quotes

Stored hours in hand: 517 (2026-11-04 23:00 UTC to 2026-11-26 15:00 UTC); days archived: 22; added this cycle: none.

Fidelity: the replay of the original rules reproduces 94 of the radar's 95 real positions opened in these hours to the hundredth of a basis point (95 matched by entry). Differences: 0 only in the real ledger, 2 only in the replay; 2 of them on a coin the radar already held when the replay began (AKE, IDOL, SOL, SOXL, UAI). The replay is taken as faithful.

Earlier part 2026-11-07 22:00 UTC to 2026-11-17 00:00 UTC; later part to 2026-11-26 16:00 UTC. Excess over cash in % of the book.

| Variant | What changes | Earlier: excess | positions | Later: excess | positions | closed | t (daily) | Later, less the original | its t |
|---|---|---|---|---|---|---|---|---|---|
| `original` | nothing: the registered rules | 0.1026% | 40 | -0.7785% | 57 | 56 | -3.20 | 0.0000% | n/a |
| `same-window` | trailing_entry_h=24 | -0.0994% | 62 | -0.7662% | 52 | 51 | -4.35 | 0.0123% | 0.05 |
| `thick-entry` | entry_trailing_apr=0.5, entry_now_apr=0.3 | 0.2366% | 29 | -0.1583% | 14 | 14 | -1.71 | 0.6202% | 3.19 |
| `patient-exit` | exit_now_apr=-1.0 | 0.2996% | 33 | -0.6826% | 55 | 53 | -3.17 | 0.0959% | 1.63 |
| `all-three` | trailing_entry_h=24, entry_trailing_apr=0.5, entry_now_apr=0.3, exit_now_apr=-1.0 | 0.3646% | 31 | -0.1507% | 22 | 21 | -2.13 | 0.6278% | 3.17 |

Candidate, chosen on the earlier part only: `all-three` (4 variants compared). **INCONCLUSIVE**: the later part holds 10 days and 21 closed positions: 30 and 30 are needed before anything is judged.

Gates on the later part: enough days no, enough positions no, excess over cash no, beats the original yes, costs x1.5 no, without best coin no.

A variant is proposed as a registered challenger only when every gate holds. A proposal is a request for a preregistered forward test, never a replacement of the original.

### Registered challengers, judged forward

None is registered. RADX-1, the diagnosis these variants came from, failed as registered (one of its two parts did not hold on the later positions), and by its own rule no challenger follows from it. One is registered only after a variant passes the gates above.


## 4. What is not claimed

- An unrealized gain is a valuation at the last close. It is not profit until the trade is closed.
- A variant that loses less than the original has not been shown to earn anything.
- No figure here is a backtest, and none is added to a research result.
