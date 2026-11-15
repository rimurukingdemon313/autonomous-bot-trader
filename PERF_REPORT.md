# Paper systems: the performance audit and the optimization cycle

**PAPER ONLY · NOT REAL MONEY · NOTHING HERE IS A PROFIT CLAIM.** Written by the performance cycle on GitHub's runner (`scripts/perf_cycle.py`), with no person in the loop. It reads the paper systems' own ledgers, recomputes every figure by a second route, and changes neither system.

**بالعربي:** مكتب TRND-1: الرصيد $200,783.01، المحقّق $0.00، غير المحقّق +$783.01، الصفقات المسكّرة 0. رادار RADAR-1: دفتره -1.99% من رأس ماله الورقي، 210 صفقة مسكّرة، الرابح منها 40. المطابقة: كل الأرقام تطابقت من مصدرين. تجربة التحسين: غير حاسمة لأن العيّنة صغيرة. المنافسين المسجّلين: 0. النظام الأصلي ما انلمس.

Updated 2026-11-15 11:13 UTC · perf-1.0.1 · cycles so far: 3

## 1. TRND-1: the trend desk's paper account

**Reconciled: 40 of 40 checks hold.** Each compares two routes to the same figure.

Last session: 2026-11-13 21:00 UTC. Paper only: no real money.

| | |
|---|---|
| Initial capital | $200,000.00 |
| Equity now | $200,783.01 |
| **Realized** P&L (closed trades, after every cost) | $0.00 from $0.00 gross |
| **Unrealized** P&L (open trades at the last close: a valuation, not a profit) | +$783.01 |
| Net after all costs (realized plus unrealized) | +$783.01 (0.392%) |
| Open positions | 4 |
| Closed trades | 0: 0 won, 0 lost |
| Win rate | undefined: no closed trade |
| Average win / average loss | undefined: no closed trade / undefined: no closed trade |
| Profit factor | undefined: no closed trade |
| Maximum drawdown, session closes | $506.09 |
| Maximum drawdown, inside a day | $1,052.51 |
| Below the peak now | $506.09 |
| Gross exposure | $98,980.50, 0.49x the equity |
| Loss if every stop were hit from here | $5,935.74 (limit $8,000.00) |
| Losing days | 4 of 5 |

Trade statistics: sample **none** (0 closed). A ratio over no closed trade does not exist and is not shown as zero.

### Open positions and where the risk sits

| Index | Units | Entry | Mark | Move | Unrealized | Notional | Share of gross | Stop | Loss at the stop from here |
|---|---|---|---|---|---|---|---|---|---|
| GER40 | 0.84 | 26,268.04 | 26,749.20 | 1.83% | +$448.44 | $24,930.19 | 25.2% | 25,144.95 | $1,495.16 |
| UK100 | 1.7 | 10,783.50 | 10,902.10 | 1.10% | +$267.68 | $24,606.44 | 24.9% | 10,248.44 | $1,475.33 |
| US500 | 3.25 | 7,550.29 | 7,561.42 | 0.15% | +$36.17 | $24,574.61 | 24.8% | 7,107.97 | $1,473.71 |
| NAS100 | 0.89 | 27,908.47 | 27,942.99 | 0.12% | +$30.72 | $24,869.26 | 25.1% | 26,267.11 | $1,491.53 |

Concentration: 4 positions, the largest 25.2% of the gross; by size that is 4.0 equal positions, and by risk it is **one**: four equity indices, all long: one risk factor held four times.

### Against a benchmark

| | Since the start | What it is |
|---|---|---|
| The desk | +$783.01 | realized plus unrealized, after costs |
| Cash | +$88.91 | 3.875% a year on the starting balance for 4.19 days |
| The same indices bought and held | +$783.01 | identical to the desk while no trade has closed: the rule has not yet made one decision the holder would not have made |
| The same positions at one times the account | +$1,584.84 | the same P&L scaled from the desk's exposure to one times the account: what the validated rule's own sizing would show; the desk's risk limits do not allow it |

### Month by month, against the $4,000 target (a target, never a quota)

| Month | Days | Net | Of $4,000 |
|---|---|---|---|
| 2026-11 | 5 | +$783.01 | 19.6% |

## 2. RADAR-1: the funding radar's paper ledger

**Reconciled: 24 of 24 checks hold.** Each compares two routes to the same figure.

Marks from 2026-10-07 20:00 UTC to 2026-11-15 10:00 UTC (38.58 days). Paper only: no order is ever sent. Its preregistered single look is on 2026-12-06 and is read as registered, whatever this audit says.

Capital: ten slots of 2N: 20N. The radar has no cash account; N is not a dollar amount. P&L is in basis points (bp) of one leg's notional; 2,000 bp summed over positions is 1% of the book.

| | In bp of N | In % of the book | On a $100,000 book (illustration) |
|---|---|---|---|
| **Realized** (closed positions, after every fill) | -3,953.5 | -1.9768% | -$1,976.76 |
| **Unrealized** (open positions at their marks, entry fills paid) | -24.1 | -0.0120% | -$12.04 |
| The book if every open position were closed now | -4,011.6 | -2.0058% | -$2,005.80 |

| | |
|---|---|
| Closed positions | 210: 40 won, 170 lost |
| Win rate | 19.0% |
| Average win / average loss | 80.7 bp / -42.2 bp |
| Profit factor | 0.45 |
| Mean net a position | -18.8 bp (t -3.53) |
| Open positions | 2 of 10 slots; on average 21.7% of the capital was deployed |
| Book P&L | -1.9888% |
| Book excess over cash (3.875%/yr on the capital in use) | -2.0942% |
| Annualised excess on the capital deployed | -91.8%/yr |
| The same with costs x1.5 / x2 | -171.8% / -251.7% |
| Maximum drawdown of the book (hourly marks) | 2.1986% |
| t of the daily excess | -3.37 |
| Best coin, and the book's excess without it | INIT: -2.5485% |

### Where it came from

Funding received **3,072 bp**, price moves between the legs **201 bp**, fills **-7,226 bp**: net **-3,954 bp**. A position earned 15.6 bp before costs and paid 34.4 bp: the costs are 2.21 times the gross. Half the positions were closed within 3.0 hours.

| Held for | Positions | Won | Sum | Mean | t | Funding | Price | Costs |
|---|---|---|---|---|---|---|---|---|
| 1 to 6 hours | 81 | 14 | -2,429 bp | -30.0 bp | -3.93 | 823 | -486 | 2,766 |
| 1 hour or less | 71 | 5 | -2,343 bp | -33.0 bp | -5.25 | 47 | 65 | 2,454 |
| over 3 days | 2 | 1 | -22 bp | -10.9 bp | -0.90 | 56 | -4 | 74 |
| 6 to 24 hours | 39 | 12 | 148 bp | 3.8 bp | 0.30 | 1,049 | 448 | 1,350 |
| 1 to 3 days | 17 | 8 | 693 bp | 40.8 bp | 1.16 | 1,096 | 178 | 582 |

| Closed for | Positions | Won | Sum | Mean | t | Funding | Price | Costs |
|---|---|---|---|---|---|---|---|---|
| spread_reversed | 118 | 24 | -2,443 bp | -20.7 bp | -3.63 | 1,695 | -88 | 4,050 |
| spread_decayed | 61 | 2 | -2,192 bp | -35.9 bp | -14.30 | 79 | -154 | 2,117 |
| rebalance | 31 | 14 | 682 bp | 22.0 bp | 0.80 | 1,298 | 442 | 1,059 |

| Known at the entry: entry spread | Positions | Won | Sum | Mean | t | Funding | Price | Costs |
|---|---|---|---|---|---|---|---|---|
| under 50%/yr | 122 | 18 | -3,363 bp | -27.6 bp | -6.58 | 808 | 44 | 4,215 |
| 50 to 100%/yr | 47 | 11 | -393 bp | -8.4 bp | -0.56 | 795 | 410 | 1,598 |
| 100%/yr or more | 41 | 11 | -198 bp | -4.8 bp | -0.28 | 1,469 | -254 | 1,413 |

| Known at the entry: venue pair | Positions | Won | Sum | Mean | t | Funding | Price | Costs |
|---|---|---|---|---|---|---|---|---|
| short mexc / long gate | 161 | 31 | -3,406 bp | -21.2 bp | -3.81 | 1,824 | 244 | 5,474 |
| short gate / long mexc | 20 | 3 | -281 bp | -14.1 bp | -0.45 | 744 | -345 | 680 |
| short hyperliquid / long gate | 7 | 1 | -183 bp | -26.2 bp | -2.31 | 35 | 55 | 273 |
| short hyperliquid / long mexc | 8 | 1 | -131 bp | -16.3 bp | -1.21 | 162 | -29 | 264 |
| short mexc / long hyperliquid | 2 | 0 | -42 bp | -21.1 bp | -2.36 | 21 | 3 | 66 |
| short dydx / long gate | 1 | 0 | -23 bp | -22.9 bp | n/a | 13 | 4 | 40 |
| short gate / long hyperliquid | 11 | 4 | 113 bp | 10.3 bp | 0.46 | 273 | 269 | 429 |

| Known at the entry: time since the coin's previous position | Positions | Won | Sum | Mean | t | Funding | Price | Costs |
|---|---|---|---|---|---|---|---|---|
| within 6 hours of the coin's previous exit | 138 | 25 | -2,241 bp | -16.2 bp | -2.08 | 2,273 | 220 | 4,734 |
| a first entry, or later | 72 | 15 | -1,712 bp | -23.8 bp | -5.61 | 798 | -19 | 2,492 |

42 coins were traded and 35 of them lost. The five worst and the five best:

| Coin | Positions | Won | Sum | Mean | t | Funding | Price | Costs |
|---|---|---|---|---|---|---|---|---|
| AKE | 21 | 2 | -904 bp | -43.0 bp | -3.28 | 207 | -397 | 714 |
| BTW | 20 | 3 | -821 bp | -41.0 bp | -7.06 | 61 | -202 | 680 |
| IRYS | 15 | 3 | -481 bp | -32.1 bp | -3.52 | 153 | -125 | 510 |
| SOXL | 13 | 1 | -447 bp | -34.4 bp | -8.24 | 62 | -68 | 442 |
| AGT | 20 | 2 | -416 bp | -20.8 bp | -1.10 | 48 | 216 | 680 |
| INIT | 7 | 5 | 917 bp | 131.0 bp | 1.67 | 1,009 | 165 | 257 |
| IOST | 4 | 3 | 450 bp | 112.4 bp | 0.98 | 358 | 227 | 136 |
| BULLA | 8 | 4 | 267 bp | 33.4 bp | 0.55 | 276 | 264 | 272 |
| RSR | 3 | 3 | 58 bp | 19.4 bp | 1.47 | 67 | 98 | 107 |
| IDOL | 2 | 1 | 20 bp | 10.0 bp | 0.52 | 74 | 14 | 68 |

Concentration: the most traded coin (AKE) is 10.4% of the positions; by count the book is 18.8 equal coins. Venue pairs: short mexc / long gate 163, short gate / long mexc 20, short gate / long hyperliquid 11, short hyperliquid / long mexc 8, short hyperliquid / long gate 7, short mexc / long hyperliquid 2, short dydx / long gate 1.

| Open now | Short / long | Opened | Entry spread | Funding | Price | Fills paid | Net at the marks | Net if closed now |
|---|---|---|---|---|---|---|---|---|
| PIEVERSE | mexc / gate | 2026-11-09 21:00 UTC | 35.8%/yr | 27.2 | -17.6 | 17.0 | -7.4 bp | -24.4 bp |
| AKE | mexc / gate | 2026-11-14 16:00 UTC | 62.8%/yr | 12.5 | -12.2 | 17.0 | -16.7 bp | -33.7 bp |

## 3. The weakness, the hypothesis and the experiment

**Largest weakness** (a class known when a position is opened, measured against the rest of the book): entry spread, *under 50%/yr*: 122 positions, mean -27.6 bp (t -6.58) against -6.7 bp for the rest (t of the difference -1.74); 2,543 bp lost beyond what the rest would have.

**Hypothesis.** Positions opened on a trailing spread under 50%/yr do not earn their round trip. Asking twice the spread at the entry removes them; whether the entries that remain earn more than cash is what the replay measures.

**Tested by** the declared variant `thick-entry` in the replay below.

### The replay: the radar's frozen rules and the declared variants on the same stored quotes

Stored hours in hand: 246 (2026-11-04 23:00 UTC to 2026-11-15 08:00 UTC); days archived: 11; added this cycle: 2026-11-14.

Fidelity: the replay of the original rules reproduces 29 of the radar's 31 real positions opened in these hours to the hundredth of a basis point (31 matched by entry). Differences: 0 only in the real ledger, 2 only in the replay; 2 of them on a coin the radar already held when the replay began (AKE, IDOL, SOL, SOXL, UAI). The replay is taken as faithful.

Earlier part 2026-11-07 22:00 UTC to 2026-11-11 00:00 UTC; later part to 2026-11-15 09:00 UTC. Excess over cash in % of the book.

| Variant | What changes | Earlier: excess | positions | Later: excess | positions | closed | t (daily) | Later, less the original | its t |
|---|---|---|---|---|---|---|---|---|---|
| `original` | nothing: the registered rules | 0.0237% | 12 | 0.1669% | 21 | 20 | 0.98 | 0.0000% | n/a |
| `same-window` | trailing_entry_h=24 | -0.1172% | 21 | 0.1593% | 28 | 25 | 1.01 | -0.0076% | -0.14 |
| `thick-entry` | entry_trailing_apr=0.5, entry_now_apr=0.3 | 0.0195% | 11 | 0.2956% | 12 | 11 | 1.36 | 0.1287% | 1.56 |
| `patient-exit` | exit_now_apr=-1.0 | 0.0638% | 11 | 0.2822% | 17 | 15 | 2.37 | 0.1153% | 1.47 |
| `all-three` | trailing_entry_h=24, entry_trailing_apr=0.5, entry_now_apr=0.3, exit_now_apr=-1.0 | -0.0272% | 15 | 0.4336% | 10 | 8 | 3.04 | 0.2667% | 3.00 |

Candidate, chosen on the earlier part only: `patient-exit` (4 variants compared). **INCONCLUSIVE**: the later part holds 5 days and 15 closed positions: 30 and 30 are needed before anything is judged.

Gates on the later part: enough days no, enough positions no, excess over cash no, beats the original no, costs x1.5 yes, without best coin no.

A variant is proposed as a registered challenger only when every gate holds. A proposal is a request for a preregistered forward test, never a replacement of the original.

### Registered challengers, judged forward

None is registered. RADX-1, the diagnosis these variants came from, failed as registered (one of its two parts did not hold on the later positions), and by its own rule no challenger follows from it. One is registered only after a variant passes the gates above.


## 4. What is not claimed

- An unrealized gain is a valuation at the last close. It is not profit until the trade is closed.
- A variant that loses less than the original has not been shown to earn anything.
- No figure here is a backtest, and none is added to a research result.
