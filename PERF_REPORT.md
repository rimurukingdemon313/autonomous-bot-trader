# Paper systems: the performance audit and the optimization cycle

**PAPER ONLY · NOT REAL MONEY · NOTHING HERE IS A PROFIT CLAIM.** Written by the performance cycle on GitHub's runner (`scripts/perf_cycle.py`), with no person in the loop. It reads the paper systems' own ledgers, recomputes every figure by a second route, and changes neither system.

**بالعربي:** مكتب TRND-1: الرصيد $194,784.79، المحقّق -$2,660.70، غير المحقّق -$2,554.51، الصفقات المسكّرة 1. رادار RADAR-1: دفتره -2.86% من رأس ماله الورقي، 281 صفقة مسكّرة، الرابح منها 49. المطابقة: كل الأرقام تطابقت من مصدرين. تجربة التحسين: غير حاسمة لأن العيّنة صغيرة. المنافسين المسجّلين: 0. النظام الأصلي ما انلمس.

Updated 2026-11-27 23:33 UTC · perf-1.0.1 · cycles so far: 61

## 1. TRND-1: the trend desk's paper account

**Reconciled: 37 of 37 checks hold.** Each compares two routes to the same figure.

Last session: 2026-11-26 16:30 UTC. Paper only: no real money.

| | |
|---|---|
| Initial capital | $200,000.00 |
| Equity now | $194,784.79 |
| **Realized** P&L (closed trades, after every cost) | -$2,660.70 from -$2,652.95 gross |
| **Unrealized** P&L (open trades at the last close: a valuation, not a profit) | -$2,554.51 |
| Net after all costs (realized plus unrealized) | -$5,215.21 (-2.608%) |
| Open positions | 3 |
| Closed trades | 1: 0 won, 1 lost |
| Win rate | 0.0% |
| Average win / average loss | undefined: no winning trade / -$2,660.70 |
| Profit factor | 0.00 |
| Maximum drawdown, session closes | $8,359.66 |
| Maximum drawdown, inside a day | $8,490.31 |
| Below the peak now | $6,504.31 |
| Gross exposure | $70,208.88, 0.36x the equity |
| Loss if every stop were hit from here | $4,210.08 (limit $8,000.00) |
| Losing days | 11 of 14 |

Trade statistics: sample **insufficient** (1 closed). A ratio over no closed trade does not exist and is not shown as zero.

### Open positions and where the risk sits

| Index | Units | Entry | Mark | Move | Unrealized | Notional | Share of gross | Stop | Loss at the stop from here |
|---|---|---|---|---|---|---|---|---|---|
| GER40 | 0.84 | 26,268.04 | 25,214.77 | -4.01% | -$969.88 | $23,218.53 | 33.1% | 23,702.59 | $1,392.46 |
| UK100 | 1.7 | 10,783.50 | 10,608.80 | -1.62% | -$389.41 | $23,647.13 | 33.7% | 9,972.74 | $1,417.78 |
| US500 | 3.25 | 7,550.29 | 7,182.53 | -4.87% | -$1,195.22 | $23,343.22 | 33.2% | 6,751.81 | $1,399.84 |

Concentration: 3 positions, the largest 33.7% of the gross; by size that is 3.0 equal positions, and by risk it is **one**: four equity indices, all long: one risk factor held four times.

### Against a benchmark

| | Since the start | What it is |
|---|---|---|
| The desk | -$5,215.21 | realized plus unrealized, after costs |
| Cash | +$360.96 | 3.875% a year on the starting balance for 17.00 days |
| The same indices bought and held | n/a | after an exit, holding on needs the index's later closes: not in these files |
| The same positions at one times the account | n/a | not computable from these files |

### Month by month, against the $4,000 target (a target, never a quota)

| Month | Days | Net | Of $4,000 |
|---|---|---|---|
| 2026-11 | 14 | -$5,215.21 | -130.4% |

## 2. RADAR-1: the funding radar's paper ledger

**Reconciled: 24 of 24 checks hold.** Each compares two routes to the same figure.

Marks from 2026-10-07 20:00 UTC to 2026-11-27 23:00 UTC (51.12 days). Paper only: no order is ever sent. Its preregistered single look is on 2026-12-06 and is read as registered, whatever this audit says.

Capital: ten slots of 2N: 20N. The radar has no cash account; N is not a dollar amount. P&L is in basis points (bp) of one leg's notional; 2,000 bp summed over positions is 1% of the book.

| | In bp of N | In % of the book | On a $100,000 book (illustration) |
|---|---|---|---|
| **Realized** (closed positions, after every fill) | -5,716.4 | -2.8582% | -$2,858.21 |
| **Unrealized** (open positions at their marks, entry fills paid) | -0.4 | -0.0002% | -$0.18 |
| The book if every open position were closed now | -5,733.8 | -2.8669% | -$2,866.89 |

| | |
|---|---|
| Closed positions | 281: 49 won, 232 lost |
| Win rate | 17.4% |
| Average win / average loss | 72.8 bp / -40.0 bp |
| Profit factor | 0.38 |
| Mean net a position | -20.3 bp (t -4.94) |
| Open positions | 1 of 10 slots; on average 25.4% of the capital was deployed |
| Book P&L | -2.8584% |
| Book excess over cash (3.875%/yr on the capital in use) | -3.0041% |
| Annualised excess on the capital deployed | -84.8%/yr |
| The same with costs x1.5 / x2 | -153.2% / -221.5% |
| Maximum drawdown of the book (hourly marks) | 2.8682% |
| t of the daily excess | -4.53 |
| Best coin, and the book's excess without it | INIT: -3.4299% |

### Where it came from

Funding received **3,843 bp**, price moves between the legs **83 bp**, fills **-9,643 bp**: net **-5,716 bp**. A position earned 14.0 bp before costs and paid 34.3 bp: the costs are 2.46 times the gross. Half the positions were closed within 4.0 hours.

| Held for | Positions | Won | Sum | Mean | t | Funding | Price | Costs |
|---|---|---|---|---|---|---|---|---|
| 1 hour or less | 88 | 5 | -2,956 bp | -33.6 bp | -6.58 | 50 | 26 | 3,032 |
| 1 to 6 hours | 96 | 16 | -2,902 bp | -30.2 bp | -4.63 | 897 | -524 | 3,275 |
| 6 to 24 hours | 64 | 16 | -366 bp | -5.7 bp | -0.67 | 1,460 | 378 | 2,204 |
| over 3 days | 5 | 2 | -38 bp | -7.7 bp | -0.71 | 168 | -31 | 176 |
| 1 to 3 days | 28 | 10 | 547 bp | 19.5 bp | 0.89 | 1,268 | 234 | 956 |

| Closed for | Positions | Won | Sum | Mean | t | Funding | Price | Costs |
|---|---|---|---|---|---|---|---|---|
| spread_reversed | 145 | 27 | -2,988 bp | -20.6 bp | -4.24 | 2,080 | -96 | 4,971 |
| spread_decayed | 83 | 3 | -2,954 bp | -35.6 bp | -16.50 | 136 | -225 | 2,865 |
| rebalance | 53 | 19 | 226 bp | 4.3 bp | 0.26 | 1,628 | 405 | 1,807 |

| Known at the entry: entry spread | Positions | Won | Sum | Mean | t | Funding | Price | Costs |
|---|---|---|---|---|---|---|---|---|
| under 50%/yr | 171 | 23 | -4,688 bp | -27.4 bp | -8.65 | 1,265 | -72 | 5,881 |
| 50 to 100%/yr | 68 | 15 | -775 bp | -11.4 bp | -1.07 | 1,098 | 442 | 2,315 |
| 100%/yr or more | 42 | 11 | -254 bp | -6.0 bp | -0.35 | 1,481 | -287 | 1,447 |

| Known at the entry: venue pair | Positions | Won | Sum | Mean | t | Funding | Price | Costs |
|---|---|---|---|---|---|---|---|---|
| short mexc / long gate | 216 | 38 | -4,857 bp | -22.5 bp | -5.31 | 2,333 | 154 | 7,344 |
| short gate / long mexc | 33 | 4 | -689 bp | -20.9 bp | -1.09 | 814 | -381 | 1,122 |
| short hyperliquid / long gate | 8 | 1 | -215 bp | -26.9 bp | -2.73 | 56 | 41 | 312 |
| short mexc / long hyperliquid | 2 | 0 | -42 bp | -21.1 bp | -2.36 | 21 | 3 | 66 |
| short dydx / long gate | 1 | 0 | -23 bp | -22.9 bp | n/a | 13 | 4 | 40 |
| short hyperliquid / long mexc | 10 | 2 | -3 bp | -0.3 bp | -0.02 | 333 | -6 | 330 |
| short gate / long hyperliquid | 11 | 4 | 113 bp | 10.3 bp | 0.46 | 273 | 269 | 429 |

| Known at the entry: time since the coin's previous position | Positions | Won | Sum | Mean | t | Funding | Price | Costs |
|---|---|---|---|---|---|---|---|---|
| within 6 hours of the coin's previous exit | 183 | 32 | -3,177 bp | -17.4 bp | -2.86 | 2,791 | 295 | 6,263 |
| a first entry, or later | 98 | 17 | -2,540 bp | -25.9 bp | -7.83 | 1,052 | -211 | 3,380 |

51 coins were traded and 45 of them lost. The five worst and the five best:

| Coin | Positions | Won | Sum | Mean | t | Funding | Price | Costs |
|---|---|---|---|---|---|---|---|---|
| AKE | 26 | 3 | -1,005 bp | -38.6 bp | -3.57 | 262 | -382 | 884 |
| BTW | 20 | 3 | -821 bp | -41.0 bp | -7.06 | 61 | -202 | 680 |
| SOXL | 20 | 1 | -679 bp | -33.9 bp | -9.69 | 130 | -129 | 680 |
| IRYS | 18 | 3 | -620 bp | -34.5 bp | -4.50 | 212 | -220 | 612 |
| AGT | 20 | 2 | -416 bp | -20.8 bp | -1.10 | 48 | 216 | 680 |
| INIT | 8 | 5 | 861 bp | 107.6 bp | 1.50 | 1,020 | 132 | 291 |
| IOST | 4 | 3 | 450 bp | 112.4 bp | 0.98 | 358 | 227 | 136 |
| BULLA | 10 | 5 | 230 bp | 23.1 bp | 0.47 | 308 | 263 | 340 |
| ACE | 2 | 1 | 127 bp | 63.7 bp | 0.66 | 170 | 23 | 66 |
| RSR | 3 | 3 | 58 bp | 19.4 bp | 1.47 | 67 | 98 | 107 |

Concentration: the most traded coin (AKE) is 9.2% of the positions; by count the book is 22.8 equal coins. Venue pairs: short mexc / long gate 216, short gate / long mexc 34, short gate / long hyperliquid 11, short hyperliquid / long mexc 10, short hyperliquid / long gate 8, short mexc / long hyperliquid 2, short dydx / long gate 1.

| Open now | Short / long | Opened | Entry spread | Funding | Price | Fills paid | Net at the marks | Net if closed now |
|---|---|---|---|---|---|---|---|---|
| SOXS | gate / mexc | 2026-11-27 08:00 UTC | 25.5%/yr | 11.1 | 5.5 | 17.0 | -0.4 bp | -17.4 bp |

## 3. The weakness, the hypothesis and the experiment

**Largest weakness** (a class known when a position is opened, measured against the rest of the book): entry spread, *under 50%/yr*: 171 positions, mean -27.4 bp (t -8.65) against -9.3 bp for the rest (t of the difference -1.85); 3,089 bp lost beyond what the rest would have.

**Hypothesis.** Positions opened on a trailing spread under 50%/yr do not earn their round trip. Asking twice the spread at the entry removes them; whether the entries that remain earn more than cash is what the replay measures.

**Tested by** the declared variant `thick-entry` in the replay below.

### The replay: the radar's frozen rules and the declared variants on the same stored quotes

Stored hours in hand: 547 (2026-11-04 23:00 UTC to 2026-11-27 21:00 UTC); days archived: 23; added this cycle: none.

Fidelity: the replay of the original rules reproduces 100 of the radar's 101 real positions opened in these hours to the hundredth of a basis point (101 matched by entry). Differences: 0 only in the real ledger, 2 only in the replay; 2 of them on a coin the radar already held when the replay began (AKE, IDOL, SOL, SOXL, UAI). The replay is taken as faithful.

Earlier part 2026-11-07 22:00 UTC to 2026-11-17 00:00 UTC; later part to 2026-11-27 22:00 UTC. Excess over cash in % of the book.

| Variant | What changes | Earlier: excess | positions | Later: excess | positions | closed | t (daily) | Later, less the original | its t |
|---|---|---|---|---|---|---|---|---|---|
| `all-three` | entry_now_apr=0.3, entry_trailing_apr=0.5, exit_now_apr=-1.0, trailing_entry_h=24 | 0.3646% | 31 | -0.1842% | 27 | 25 | -2.56 | 0.6728% | 3.37 |
| `original` | nothing: the registered rules | 0.1026% | 40 | -0.8571% | 63 | 62 | -3.54 | 0.0000% | n/a |
| `patient-exit` | exit_now_apr=-1.0 | 0.2996% | 33 | -0.7547% | 61 | 57 | -3.53 | 0.1024% | 1.75 |
| `same-window` | trailing_entry_h=24 | -0.0994% | 62 | -0.8365% | 60 | 58 | -4.64 | 0.0205% | 0.08 |
| `thick-entry` | entry_now_apr=0.3, entry_trailing_apr=0.5 | 0.2366% | 29 | -0.1905% | 16 | 16 | -2.04 | 0.6665% | 3.44 |

Candidate, chosen on the earlier part only: `all-three` (4 variants compared). **INCONCLUSIVE**: the later part holds 11 days and 25 closed positions: 30 and 30 are needed before anything is judged.

Gates on the later part: beats the original yes, costs x1.5 no, enough days no, enough positions no, excess over cash no, without best coin no.

A variant is proposed as a registered challenger only when every gate holds. A proposal is a request for a preregistered forward test, never a replacement of the original.

### Registered challengers, judged forward

None is registered. RADX-1, the diagnosis these variants came from, failed as registered (one of its two parts did not hold on the later positions), and by its own rule no challenger follows from it. One is registered only after a variant passes the gates above.


## 4. What is not claimed

- An unrealized gain is a valuation at the last close. It is not profit until the trade is closed.
- A variant that loses less than the original has not been shown to earn anything.
- No figure here is a backtest, and none is added to a research result.
