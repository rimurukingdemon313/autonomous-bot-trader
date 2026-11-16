# Paper systems: the performance audit and the optimization cycle

**PAPER ONLY · NOT REAL MONEY · NOTHING HERE IS A PROFIT CLAIM.** Written by the performance cycle on GitHub's runner (`scripts/perf_cycle.py`), with no person in the loop. It reads the paper systems' own ledgers, recomputes every figure by a second route, and changes neither system.

**بالعربي:** مكتب TRND-1: الرصيد $200,783.01، المحقّق $0.00، غير المحقّق +$783.01، الصفقات المسكّرة 0. رادار RADAR-1: دفتره -2.04% من رأس ماله الورقي، 215 صفقة مسكّرة، الرابح منها 42. المطابقة: كل الأرقام تطابقت من مصدرين. تجربة التحسين: غير حاسمة لأن العيّنة صغيرة. المنافسين المسجّلين: 0. النظام الأصلي ما انلمس.

Updated 2026-11-16 22:18 UTC · perf-1.0.1 · cycles so far: 9

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

Marks from 2026-10-07 20:00 UTC to 2026-11-16 22:00 UTC (40.08 days). Paper only: no order is ever sent. Its preregistered single look is on 2026-12-06 and is read as registered, whatever this audit says.

Capital: ten slots of 2N: 20N. The radar has no cash account; N is not a dollar amount. P&L is in basis points (bp) of one leg's notional; 2,000 bp summed over positions is 1% of the book.

| | In bp of N | In % of the book | On a $100,000 book (illustration) |
|---|---|---|---|
| **Realized** (closed positions, after every fill) | -4,074.1 | -2.0370% | -$2,037.03 |
| **Unrealized** (open positions at their marks, entry fills paid) | -15.4 | -0.0077% | -$7.71 |
| The book if every open position were closed now | -4,160.0 | -2.0800% | -$2,079.99 |

| | |
|---|---|
| Closed positions | 215: 42 won, 173 lost |
| Win rate | 19.5% |
| Average win / average loss | 77.3 bp / -42.3 bp |
| Profit factor | 0.44 |
| Mean net a position | -18.9 bp (t -3.63) |
| Open positions | 4 of 10 slots; on average 22.1% of the capital was deployed |
| Book P&L | -2.0447% |
| Book excess over cash (3.875%/yr on the capital in use) | -2.1732% |
| Annualised excess on the capital deployed | -90.3%/yr |
| The same with costs x1.5 / x2 | -168.6% / -246.9% |
| Maximum drawdown of the book (hourly marks) | 2.1986% |
| t of the daily excess | -3.47 |
| Best coin, and the book's excess without it | INIT: -2.6275% |

### Where it came from

Funding received **3,124 bp**, price moves between the legs **198 bp**, fills **-7,396 bp**: net **-4,074 bp**. A position earned 15.5 bp before costs and paid 34.4 bp: the costs are 2.23 times the gross. Half the positions were closed within 3.0 hours.

| Held for | Positions | Won | Sum | Mean | t | Funding | Price | Costs |
|---|---|---|---|---|---|---|---|---|
| 1 to 6 hours | 82 | 14 | -2,470 bp | -30.1 bp | -3.99 | 824 | -494 | 2,800 |
| 1 hour or less | 72 | 5 | -2,400 bp | -33.3 bp | -5.37 | 44 | 45 | 2,488 |
| over 3 days | 2 | 1 | -22 bp | -10.9 bp | -0.90 | 56 | -4 | 74 |
| 6 to 24 hours | 42 | 14 | 124 bp | 3.0 bp | 0.25 | 1,104 | 473 | 1,452 |
| 1 to 3 days | 17 | 8 | 693 bp | 40.8 bp | 1.16 | 1,096 | 178 | 582 |

| Closed for | Positions | Won | Sum | Mean | t | Funding | Price | Costs |
|---|---|---|---|---|---|---|---|---|
| spread_reversed | 120 | 24 | -2,525 bp | -21.0 bp | -3.75 | 1,710 | -117 | 4,118 |
| spread_decayed | 63 | 3 | -2,242 bp | -35.6 bp | -13.97 | 92 | -149 | 2,185 |
| rebalance | 32 | 15 | 693 bp | 21.7 bp | 0.81 | 1,322 | 464 | 1,093 |

| Known at the entry: entry spread | Positions | Won | Sum | Mean | t | Funding | Price | Costs |
|---|---|---|---|---|---|---|---|---|
| under 50%/yr | 124 | 19 | -3,408 bp | -27.5 bp | -6.64 | 829 | 46 | 4,283 |
| 50 to 100%/yr | 50 | 12 | -468 bp | -9.4 bp | -0.67 | 826 | 406 | 1,700 |
| 100%/yr or more | 41 | 11 | -198 bp | -4.8 bp | -0.28 | 1,469 | -254 | 1,413 |

| Known at the entry: venue pair | Positions | Won | Sum | Mean | t | Funding | Price | Costs |
|---|---|---|---|---|---|---|---|---|
| short mexc / long gate | 166 | 33 | -3,526 bp | -21.2 bp | -3.94 | 1,876 | 242 | 5,644 |
| short gate / long mexc | 20 | 3 | -281 bp | -14.1 bp | -0.45 | 744 | -345 | 680 |
| short hyperliquid / long gate | 7 | 1 | -183 bp | -26.2 bp | -2.31 | 35 | 55 | 273 |
| short hyperliquid / long mexc | 8 | 1 | -131 bp | -16.3 bp | -1.21 | 162 | -29 | 264 |
| short mexc / long hyperliquid | 2 | 0 | -42 bp | -21.1 bp | -2.36 | 21 | 3 | 66 |
| short dydx / long gate | 1 | 0 | -23 bp | -22.9 bp | n/a | 13 | 4 | 40 |
| short gate / long hyperliquid | 11 | 4 | 113 bp | 10.3 bp | 0.46 | 273 | 269 | 429 |

| Known at the entry: time since the coin's previous position | Positions | Won | Sum | Mean | t | Funding | Price | Costs |
|---|---|---|---|---|---|---|---|---|
| within 6 hours of the coin's previous exit | 141 | 26 | -2,316 bp | -16.4 bp | -2.14 | 2,305 | 215 | 4,836 |
| a first entry, or later | 74 | 16 | -1,758 bp | -23.8 bp | -5.69 | 819 | -17 | 2,560 |

43 coins were traded and 36 of them lost. The five worst and the five best:

| Coin | Positions | Won | Sum | Mean | t | Funding | Price | Costs |
|---|---|---|---|---|---|---|---|---|
| AKE | 24 | 3 | -979 bp | -40.8 bp | -3.50 | 239 | -402 | 816 |
| BTW | 20 | 3 | -821 bp | -41.0 bp | -7.06 | 61 | -202 | 680 |
| IRYS | 15 | 3 | -481 bp | -32.1 bp | -3.52 | 153 | -125 | 510 |
| SOXL | 13 | 1 | -447 bp | -34.4 bp | -8.24 | 62 | -68 | 442 |
| AGT | 20 | 2 | -416 bp | -20.8 bp | -1.10 | 48 | 216 | 680 |
| INIT | 7 | 5 | 917 bp | 131.0 bp | 1.67 | 1,009 | 165 | 257 |
| IOST | 4 | 3 | 450 bp | 112.4 bp | 0.98 | 358 | 227 | 136 |
| BULLA | 8 | 4 | 267 bp | 33.4 bp | 0.55 | 276 | 264 | 272 |
| RSR | 3 | 3 | 58 bp | 19.4 bp | 1.47 | 67 | 98 | 107 |
| IDOL | 2 | 1 | 20 bp | 10.0 bp | 0.52 | 74 | 14 | 68 |

Concentration: the most traded coin (AKE) is 11.4% of the positions; by count the book is 18.9 equal coins. Venue pairs: short mexc / long gate 169, short gate / long mexc 20, short gate / long hyperliquid 11, short hyperliquid / long gate 8, short hyperliquid / long mexc 8, short mexc / long hyperliquid 2, short dydx / long gate 1.

| Open now | Short / long | Opened | Entry spread | Funding | Price | Fills paid | Net at the marks | Net if closed now |
|---|---|---|---|---|---|---|---|---|
| PIEVERSE | mexc / gate | 2026-11-09 21:00 UTC | 35.8%/yr | 36.3 | -29.5 | 17.0 | -10.2 bp | -27.2 bp |
| AKE | mexc / gate | 2026-11-16 09:00 UTC | 98.6%/yr | 7.8 | -5.0 | 17.0 | -14.2 bp | -31.2 bp |
| EVAA | mexc / gate | 2026-11-16 09:00 UTC | 50.3%/yr | 11.7 | 18.9 | 17.0 | 13.5 bp | -3.5 bp |
| LIT | hyperliquid / gate | 2026-11-16 15:00 UTC | 50.2%/yr | 17.4 | -2.4 | 19.5 | -4.5 bp | -24.0 bp |

## 3. The weakness, the hypothesis and the experiment

**Largest weakness** (a class known when a position is opened, measured against the rest of the book): entry spread, *under 50%/yr*: 124 positions, mean -27.5 bp (t -6.64) against -7.3 bp for the rest (t of the difference -1.73); 2,501 bp lost beyond what the rest would have.

**Hypothesis.** Positions opened on a trailing spread under 50%/yr do not earn their round trip. Asking twice the spread at the entry removes them; whether the entries that remain earn more than cash is what the replay measures.

**Tested by** the declared variant `thick-entry` in the replay below.

### The replay: the radar's frozen rules and the declared variants on the same stored quotes

Stored hours in hand: 281 (2026-11-04 23:00 UTC to 2026-11-16 19:00 UTC); days archived: 12; added this cycle: none.

Fidelity: the replay of the original rules reproduces 34 of the radar's 38 real positions opened in these hours to the hundredth of a basis point (38 matched by entry). Differences: 0 only in the real ledger, 2 only in the replay; 2 of them on a coin the radar already held when the replay began (AKE, IDOL, SOL, SOXL, UAI). **The replay is NOT faithful enough: read nothing from the table below.**

Earlier part 2026-11-07 22:00 UTC to 2026-11-12 00:00 UTC; later part to 2026-11-16 20:00 UTC. Excess over cash in % of the book.

| Variant | What changes | Earlier: excess | positions | Later: excess | positions | closed | t (daily) | Later, less the original | its t |
|---|---|---|---|---|---|---|---|---|---|
| `original` | nothing: the registered rules | 0.0840% | 18 | 0.0337% | 22 | 19 | 0.19 | 0.0000% | n/a |
| `same-window` | trailing_entry_h=24 | -0.0668% | 30 | -0.0055% | 31 | 23 | -0.03 | -0.0392% | -0.63 |
| `thick-entry` | entry_trailing_apr=0.5, entry_now_apr=0.3 | 0.0889% | 16 | 0.1670% | 13 | 10 | 0.70 | 0.1333% | 1.53 |
| `patient-exit` | exit_now_apr=-1.0 | 0.1231% | 17 | 0.1916% | 16 | 13 | 1.24 | 0.1579% | 2.13 |
| `all-three` | trailing_entry_h=24, entry_trailing_apr=0.5, entry_now_apr=0.3, exit_now_apr=-1.0 | 0.0795% | 19 | 0.2943% | 12 | 7 | 1.68 | 0.2606% | 3.02 |

Candidate, chosen on the earlier part only: `patient-exit` (4 variants compared). **INCONCLUSIVE**: the later part holds 5 days and 13 closed positions: 30 and 30 are needed before anything is judged.

Gates on the later part: enough days no, enough positions no, excess over cash no, beats the original no, costs x1.5 yes, without best coin no.

A variant is proposed as a registered challenger only when every gate holds. A proposal is a request for a preregistered forward test, never a replacement of the original.

### Registered challengers, judged forward

None is registered. RADX-1, the diagnosis these variants came from, failed as registered (one of its two parts did not hold on the later positions), and by its own rule no challenger follows from it. One is registered only after a variant passes the gates above.


## 4. What is not claimed

- An unrealized gain is a valuation at the last close. It is not profit until the trade is closed.
- A variant that loses less than the original has not been shown to earn anything.
- No figure here is a backtest, and none is added to a research result.
