# Paper systems: the performance audit and the optimization cycle

**PAPER ONLY · NOT REAL MONEY · NOTHING HERE IS A PROFIT CLAIM.** Written by the performance cycle on GitHub's runner (`scripts/perf_cycle.py`), with no person in the loop. It reads the paper systems' own ledgers, recomputes every figure by a second route, and changes neither system.

**بالعربي:** مكتب TRND-1: الرصيد $195,564.39، المحقّق -$2,660.70، غير المحقّق -$1,774.92، الصفقات المسكّرة 1. رادار RADAR-1: دفتره -2.88% من رأس ماله الورقي، 283 صفقة مسكّرة، الرابح منها 49. المطابقة: كل الأرقام تطابقت من مصدرين. تجربة التحسين: غير حاسمة لأن العيّنة صغيرة. المنافسين المسجّلين: 0. النظام الأصلي ما انلمس.

Updated 2026-11-28 08:04 UTC · perf-1.0.1 · cycles so far: 62

## 1. TRND-1: the trend desk's paper account

**Reconciled: 37 of 37 checks hold.** Each compares two routes to the same figure.

Last session: 2026-11-27 21:00 UTC. Paper only: no real money.

| | |
|---|---|
| Initial capital | $200,000.00 |
| Equity now | $195,564.39 |
| **Realized** P&L (closed trades, after every cost) | -$2,660.70 from -$2,652.95 gross |
| **Unrealized** P&L (open trades at the last close: a valuation, not a profit) | -$1,774.92 |
| Net after all costs (realized plus unrealized) | -$4,435.61 (-2.218%) |
| Open positions | 3 |
| Closed trades | 1: 0 won, 1 lost |
| Win rate | 0.0% |
| Average win / average loss | undefined: no winning trade / -$2,660.70 |
| Profit factor | 0.00 |
| Maximum drawdown, session closes | $8,359.66 |
| Maximum drawdown, inside a day | $8,490.31 |
| Below the peak now | $5,724.71 |
| Gross exposure | $71,007.93, 0.36x the equity |
| Loss if every stop were hit from here | $4,258.02 (limit $8,000.00) |
| Losing days | 11 of 15 |

Trade statistics: sample **insufficient** (1 closed). A ratio over no closed trade does not exist and is not shown as zero.

### Open positions and where the risk sits

| Index | Units | Entry | Mark | Move | Unrealized | Notional | Share of gross | Stop | Loss at the stop from here |
|---|---|---|---|---|---|---|---|---|---|
| GER40 | 0.84 | 26,268.04 | 25,440.49 | -3.15% | -$762.58 | $23,443.08 | 33.0% | 23,914.77 | $1,405.93 |
| UK100 | 1.7 | 10,783.50 | 10,698.30 | -0.79% | -$189.93 | $23,848.82 | 33.6% | 10,056.87 | $1,429.89 |
| US500 | 3.25 | 7,550.29 | 7,297.24 | -3.35% | -$822.41 | $23,716.03 | 33.4% | 6,859.64 | $1,422.20 |

Concentration: 3 positions, the largest 33.6% of the gross; by size that is 3.0 equal positions, and by risk it is **one**: four equity indices, all long: one risk factor held four times.

### Against a benchmark

| | Since the start | What it is |
|---|---|---|
| The desk | -$4,435.61 | realized plus unrealized, after costs |
| Cash | +$386.17 | 3.875% a year on the starting balance for 18.19 days |
| The same indices bought and held | n/a | after an exit, holding on needs the index's later closes: not in these files |
| The same positions at one times the account | n/a | not computable from these files |

### Month by month, against the $4,000 target (a target, never a quota)

| Month | Days | Net | Of $4,000 |
|---|---|---|---|
| 2026-11 | 15 | -$4,435.61 | -110.9% |

## 2. RADAR-1: the funding radar's paper ledger

**Reconciled: 24 of 24 checks hold.** Each compares two routes to the same figure.

Marks from 2026-10-07 20:00 UTC to 2026-11-28 07:00 UTC (51.46 days). Paper only: no order is ever sent. Its preregistered single look is on 2026-12-06 and is read as registered, whatever this audit says.

Capital: ten slots of 2N: 20N. The radar has no cash account; N is not a dollar amount. P&L is in basis points (bp) of one leg's notional; 2,000 bp summed over positions is 1% of the book.

| | In bp of N | In % of the book | On a $100,000 book (illustration) |
|---|---|---|---|
| **Realized** (closed positions, after every fill) | -5,770.3 | -2.8851% | -$2,885.13 |
| **Unrealized** (open positions at their marks, entry fills paid) | 2.1 | 0.0010% | +$1.04 |
| The book if every open position were closed now | -5,785.2 | -2.8926% | -$2,892.59 |

| | |
|---|---|
| Closed positions | 283: 49 won, 234 lost |
| Win rate | 17.3% |
| Average win / average loss | 72.8 bp / -39.9 bp |
| Profit factor | 0.38 |
| Mean net a position | -20.4 bp (t -4.99) |
| Open positions | 1 of 10 slots; on average 25.3% of the capital was deployed |
| Book P&L | -2.8841% |
| Book excess over cash (3.875%/yr on the capital in use) | -3.0304% |
| Annualised excess on the capital deployed | -85.2%/yr |
| The same with costs x1.5 / x2 | -153.7% / -222.2% |
| Maximum drawdown of the book (hourly marks) | 2.8856% |
| t of the daily excess | -4.56 |
| Best coin, and the book's excess without it | INIT: -3.4562% |

### Where it came from

Funding received **3,838 bp**, price moves between the legs **101 bp**, fills **-9,710 bp**: net **-5,770 bp**. A position earned 13.9 bp before costs and paid 34.3 bp: the costs are 2.46 times the gross. Half the positions were closed within 4.0 hours.

| Held for | Positions | Won | Sum | Mean | t | Funding | Price | Costs |
|---|---|---|---|---|---|---|---|---|
| 1 hour or less | 89 | 5 | -2,959 bp | -33.2 bp | -6.57 | 45 | 61 | 3,065 |
| 1 to 6 hours | 97 | 16 | -2,954 bp | -30.4 bp | -4.71 | 897 | -542 | 3,309 |
| 6 to 24 hours | 64 | 16 | -366 bp | -5.7 bp | -0.67 | 1,460 | 378 | 2,204 |
| over 3 days | 5 | 2 | -38 bp | -7.7 bp | -0.71 | 168 | -31 | 176 |
| 1 to 3 days | 28 | 10 | 547 bp | 19.5 bp | 0.89 | 1,268 | 234 | 956 |

| Closed for | Positions | Won | Sum | Mean | t | Funding | Price | Costs |
|---|---|---|---|---|---|---|---|---|
| spread_reversed | 145 | 27 | -2,988 bp | -20.6 bp | -4.24 | 2,080 | -96 | 4,971 |
| spread_decayed | 84 | 3 | -2,957 bp | -35.2 bp | -16.24 | 130 | -190 | 2,898 |
| rebalance | 54 | 19 | 175 bp | 3.2 bp | 0.20 | 1,628 | 387 | 1,841 |

| Known at the entry: entry spread | Positions | Won | Sum | Mean | t | Funding | Price | Costs |
|---|---|---|---|---|---|---|---|---|
| under 50%/yr | 173 | 23 | -4,742 bp | -27.4 bp | -8.74 | 1,260 | -54 | 5,948 |
| 50 to 100%/yr | 68 | 15 | -775 bp | -11.4 bp | -1.07 | 1,098 | 442 | 2,315 |
| 100%/yr or more | 42 | 11 | -254 bp | -6.0 bp | -0.35 | 1,481 | -287 | 1,447 |

| Known at the entry: venue pair | Positions | Won | Sum | Mean | t | Funding | Price | Costs |
|---|---|---|---|---|---|---|---|---|
| short mexc / long gate | 217 | 38 | -4,908 bp | -22.6 bp | -5.37 | 2,334 | 136 | 7,378 |
| short gate / long mexc | 33 | 4 | -689 bp | -20.9 bp | -1.09 | 814 | -381 | 1,122 |
| short hyperliquid / long gate | 8 | 1 | -215 bp | -26.9 bp | -2.73 | 56 | 41 | 312 |
| short mexc / long hyperliquid | 3 | 0 | -45 bp | -14.9 bp | -1.85 | 16 | 39 | 99 |
| short dydx / long gate | 1 | 0 | -23 bp | -22.9 bp | n/a | 13 | 4 | 40 |
| short hyperliquid / long mexc | 10 | 2 | -3 bp | -0.3 bp | -0.02 | 333 | -6 | 330 |
| short gate / long hyperliquid | 11 | 4 | 113 bp | 10.3 bp | 0.46 | 273 | 269 | 429 |

| Known at the entry: time since the coin's previous position | Positions | Won | Sum | Mean | t | Funding | Price | Costs |
|---|---|---|---|---|---|---|---|---|
| within 6 hours of the coin's previous exit | 183 | 32 | -3,177 bp | -17.4 bp | -2.86 | 2,791 | 295 | 6,263 |
| a first entry, or later | 100 | 17 | -2,593 bp | -25.9 bp | -7.95 | 1,047 | -193 | 3,447 |

52 coins were traded and 46 of them lost. The five worst and the five best:

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

Concentration: the most traded coin (AKE) is 9.2% of the positions; by count the book is 22.8 equal coins. Venue pairs: short mexc / long gate 217, short gate / long mexc 34, short gate / long hyperliquid 11, short hyperliquid / long mexc 10, short hyperliquid / long gate 8, short mexc / long hyperliquid 3, short dydx / long gate 1.

| Open now | Short / long | Opened | Entry spread | Funding | Price | Fills paid | Net at the marks | Net if closed now |
|---|---|---|---|---|---|---|---|---|
| SOXS | gate / mexc | 2026-11-27 08:00 UTC | 25.5%/yr | 11.6 | 7.4 | 17.0 | 2.1 bp | -14.9 bp |

## 3. The weakness, the hypothesis and the experiment

**Largest weakness** (a class known when a position is opened, measured against the rest of the book): entry spread, *under 50%/yr*: 173 positions, mean -27.4 bp (t -8.74) against -9.3 bp for the rest (t of the difference -1.86); 3,124 bp lost beyond what the rest would have.

**Hypothesis.** Positions opened on a trailing spread under 50%/yr do not earn their round trip. Asking twice the spread at the entry removes them; whether the entries that remain earn more than cash is what the replay measures.

**Tested by** the declared variant `thick-entry` in the replay below.

### The replay: the radar's frozen rules and the declared variants on the same stored quotes

Stored hours in hand: 557 (2026-11-04 23:00 UTC to 2026-11-28 07:00 UTC); days archived: 24; added this cycle: 2026-11-27.

Fidelity: the replay of the original rules reproduces 103 of the radar's 103 real positions opened in these hours to the hundredth of a basis point (103 matched by entry). Differences: 0 only in the real ledger, 2 only in the replay; 2 of them on a coin the radar already held when the replay began (AKE, IDOL, SOL, SOXL, UAI). The replay is taken as faithful.

Earlier part 2026-11-07 22:00 UTC to 2026-11-18 00:00 UTC; later part to 2026-11-28 08:00 UTC. Excess over cash in % of the book.

| Variant | What changes | Earlier: excess | positions | Later: excess | positions | closed | t (daily) | Later, less the original | its t |
|---|---|---|---|---|---|---|---|---|---|
| `original` | nothing: the registered rules | 0.0120% | 48 | -0.7916% | 57 | 56 | -3.21 | 0.0000% | n/a |
| `same-window` | trailing_entry_h=24 | -0.2052% | 68 | -0.7497% | 57 | 53 | -4.02 | 0.0419% | 0.16 |
| `thick-entry` | entry_trailing_apr=0.5, entry_now_apr=0.3 | 0.2075% | 30 | -0.1615% | 15 | 15 | -1.72 | 0.6301% | 3.20 |
| `patient-exit` | exit_now_apr=-1.0 | 0.2255% | 40 | -0.6792% | 55 | 52 | -3.06 | 0.1124% | 1.90 |
| `all-three` | trailing_entry_h=24, entry_trailing_apr=0.5, entry_now_apr=0.3, exit_now_apr=-1.0 | 0.3494% | 32 | -0.1558% | 27 | 25 | -2.11 | 0.6358% | 3.16 |

Candidate, chosen on the earlier part only: `all-three` (4 variants compared). **INCONCLUSIVE**: the later part holds 11 days and 25 closed positions: 30 and 30 are needed before anything is judged.

Gates on the later part: enough days no, enough positions no, excess over cash no, beats the original yes, costs x1.5 no, without best coin no.

A variant is proposed as a registered challenger only when every gate holds. A proposal is a request for a preregistered forward test, never a replacement of the original.

### Registered challengers, judged forward

None is registered. RADX-1, the diagnosis these variants came from, failed as registered (one of its two parts did not hold on the later positions), and by its own rule no challenger follows from it. One is registered only after a variant passes the gates above.


## 4. What is not claimed

- An unrealized gain is a valuation at the last close. It is not profit until the trade is closed.
- A variant that loses less than the original has not been shown to earn anything.
- No figure here is a backtest, and none is added to a research result.
