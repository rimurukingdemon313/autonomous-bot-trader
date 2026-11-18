# Paper systems: the performance audit and the optimization cycle

**PAPER ONLY · NOT REAL MONEY · NOTHING HERE IS A PROFIT CLAIM.** Written by the performance cycle on GitHub's runner (`scripts/perf_cycle.py`), with no person in the loop. It reads the paper systems' own ledgers, recomputes every figure by a second route, and changes neither system.

**بالعربي:** مكتب TRND-1: الرصيد $198,091.51، المحقّق $0.00، غير المحقّق -$1,908.49، الصفقات المسكّرة 0. رادار RADAR-1: دفتره -2.41% من رأس ماله الورقي، 237 صفقة مسكّرة، الرابح منها 43. المطابقة: كل الأرقام تطابقت من مصدرين. تجربة التحسين: غير حاسمة لأن العيّنة صغيرة. المنافسين المسجّلين: 0. النظام الأصلي ما انلمس.

Updated 2026-11-18 20:42 UTC · perf-1.0.1 · cycles so far: 18

## 1. TRND-1: the trend desk's paper account

**Reconciled: 40 of 40 checks hold.** Each compares two routes to the same figure.

Last session: 2026-11-17 21:00 UTC. Paper only: no real money.

| | |
|---|---|
| Initial capital | $200,000.00 |
| Equity now | $198,091.51 |
| **Realized** P&L (closed trades, after every cost) | $0.00 from $0.00 gross |
| **Unrealized** P&L (open trades at the last close: a valuation, not a profit) | -$1,908.49 |
| Net after all costs (realized plus unrealized) | -$1,908.49 (-0.954%) |
| Open positions | 4 |
| Closed trades | 0: 0 won, 0 lost |
| Win rate | undefined: no closed trade |
| Average win / average loss | undefined: no closed trade / undefined: no closed trade |
| Profit factor | undefined: no closed trade |
| Maximum drawdown, session closes | $3,197.59 |
| Maximum drawdown, inside a day | $3,788.59 |
| Below the peak now | $3,197.59 |
| Gross exposure | $96,023.47, 0.48x the equity |
| Loss if every stop were hit from here | $5,758.28 (limit $8,000.00) |
| Losing days | 6 of 7 |

Trade statistics: sample **none** (0 closed). A ratio over no closed trade does not exist and is not shown as zero.

### Open positions and where the risk sits

| Index | Units | Entry | Mark | Move | Unrealized | Notional | Share of gross | Stop | Loss at the stop from here |
|---|---|---|---|---|---|---|---|---|---|
| GER40 | 0.84 | 26,268.04 | 26,044.62 | -0.85% | -$206.91 | $24,119.64 | 25.1% | 24,482.65 | $1,446.52 |
| UK100 | 1.7 | 10,783.50 | 10,689.40 | -0.87% | -$211.42 | $24,017.00 | 25.0% | 10,048.51 | $1,439.96 |
| US500 | 3.25 | 7,550.29 | 7,340.28 | -2.78% | -$682.53 | $23,855.91 | 24.8% | 6,900.10 | $1,430.58 |
| NAS100 | 0.89 | 27,908.47 | 27,001.03 | -3.25% | -$807.63 | $24,030.92 | 25.0% | 25,381.68 | $1,441.22 |

Concentration: 4 positions, the largest 25.1% of the gross; by size that is 4.0 equal positions, and by risk it is **one**: four equity indices, all long: one risk factor held four times.

### Against a benchmark

| | Since the start | What it is |
|---|---|---|
| The desk | -$1,908.49 | realized plus unrealized, after costs |
| Cash | +$173.84 | 3.875% a year on the starting balance for 8.19 days |
| The same indices bought and held | -$1,908.49 | identical to the desk while no trade has closed: the rule has not yet made one decision the holder would not have made |
| The same positions at one times the account | -$3,862.85 | the same P&L scaled from the desk's exposure to one times the account: what the validated rule's own sizing would show; the desk's risk limits do not allow it |

### Month by month, against the $4,000 target (a target, never a quota)

| Month | Days | Net | Of $4,000 |
|---|---|---|---|
| 2026-11 | 7 | -$1,908.49 | -47.7% |

## 2. RADAR-1: the funding radar's paper ledger

**Reconciled: 24 of 24 checks hold.** Each compares two routes to the same figure.

Marks from 2026-10-07 20:00 UTC to 2026-11-18 20:00 UTC (42.00 days). Paper only: no order is ever sent. Its preregistered single look is on 2026-12-06 and is read as registered, whatever this audit says.

Capital: ten slots of 2N: 20N. The radar has no cash account; N is not a dollar amount. P&L is in basis points (bp) of one leg's notional; 2,000 bp summed over positions is 1% of the book.

| | In bp of N | In % of the book | On a $100,000 book (illustration) |
|---|---|---|---|
| **Realized** (closed positions, after every fill) | -4,761.2 | -2.3806% | -$2,380.60 |
| **Unrealized** (open positions at their marks, entry fills paid) | -54.7 | -0.0273% | -$27.33 |
| The book if every open position were closed now | -4,917.9 | -2.4589% | -$2,458.93 |

| | |
|---|---|
| Closed positions | 237: 43 won, 194 lost |
| Win rate | 18.1% |
| Average win / average loss | 75.6 bp / -41.3 bp |
| Profit factor | 0.41 |
| Mean net a position | -20.1 bp (t -4.22) |
| Open positions | 6 of 10 slots; on average 23.8% of the capital was deployed |
| Book P&L | -2.4079% |
| Book excess over cash (3.875%/yr on the capital in use) | -2.5644% |
| Annualised excess on the capital deployed | -94.2%/yr |
| The same with costs x1.5 / x2 | -171.0% / -247.7% |
| Maximum drawdown of the book (hourly marks) | 2.4079% |
| t of the daily excess | -3.82 |
| Best coin, and the book's excess without it | INIT: -3.0187% |

### Where it came from

Funding received **3,246 bp**, price moves between the legs **142 bp**, fills **-8,149 bp**: net **-4,761 bp**. A position earned 14.3 bp before costs and paid 34.4 bp: the costs are 2.41 times the gross. Half the positions were closed within 3.0 hours.

| Held for | Positions | Won | Sum | Mean | t | Funding | Price | Costs |
|---|---|---|---|---|---|---|---|---|
| 1 hour or less | 82 | 5 | -2,752 bp | -33.6 bp | -6.13 | 46 | 30 | 2,828 |
| 1 to 6 hours | 86 | 15 | -2,594 bp | -30.2 bp | -4.17 | 836 | -495 | 2,936 |
| over 3 days | 3 | 1 | -62 bp | -20.5 bp | -1.72 | 100 | -54 | 108 |
| 6 to 24 hours | 47 | 14 | -29 bp | -0.6 bp | -0.06 | 1,150 | 448 | 1,627 |
| 1 to 3 days | 19 | 8 | 675 bp | 35.5 bp | 1.13 | 1,113 | 212 | 650 |

| Closed for | Positions | Won | Sum | Mean | t | Funding | Price | Costs |
|---|---|---|---|---|---|---|---|---|
| spread_decayed | 74 | 3 | -2,694 bp | -36.4 bp | -15.51 | 98 | -234 | 2,559 |
| spread_reversed | 128 | 25 | -2,681 bp | -20.9 bp | -3.97 | 1,762 | -48 | 4,395 |
| rebalance | 35 | 15 | 614 bp | 17.5 bp | 0.72 | 1,386 | 423 | 1,195 |

| Known at the entry: entry spread | Positions | Won | Sum | Mean | t | Funding | Price | Costs |
|---|---|---|---|---|---|---|---|---|
| under 50%/yr | 138 | 19 | -3,887 bp | -28.2 bp | -7.52 | 886 | -14 | 4,759 |
| 50 to 100%/yr | 58 | 13 | -676 bp | -11.7 bp | -0.97 | 891 | 410 | 1,977 |
| 100%/yr or more | 41 | 11 | -198 bp | -4.8 bp | -0.28 | 1,469 | -254 | 1,413 |

| Known at the entry: venue pair | Positions | Won | Sum | Mean | t | Funding | Price | Costs |
|---|---|---|---|---|---|---|---|---|
| short mexc / long gate | 183 | 33 | -4,042 bp | -22.1 bp | -4.50 | 1,968 | 212 | 6,222 |
| short gate / long mexc | 24 | 4 | -421 bp | -17.6 bp | -0.67 | 753 | -359 | 816 |
| short hyperliquid / long gate | 8 | 1 | -215 bp | -26.9 bp | -2.73 | 56 | 41 | 312 |
| short hyperliquid / long mexc | 8 | 1 | -131 bp | -16.3 bp | -1.21 | 162 | -29 | 264 |
| short mexc / long hyperliquid | 2 | 0 | -42 bp | -21.1 bp | -2.36 | 21 | 3 | 66 |
| short dydx / long gate | 1 | 0 | -23 bp | -22.9 bp | n/a | 13 | 4 | 40 |
| short gate / long hyperliquid | 11 | 4 | 113 bp | 10.3 bp | 0.46 | 273 | 269 | 429 |

| Known at the entry: time since the coin's previous position | Positions | Won | Sum | Mean | t | Funding | Price | Costs |
|---|---|---|---|---|---|---|---|---|
| within 6 hours of the coin's previous exit | 154 | 26 | -2,709 bp | -17.6 bp | -2.50 | 2,355 | 214 | 5,278 |
| a first entry, or later | 83 | 17 | -2,052 bp | -24.7 bp | -6.47 | 892 | -72 | 2,871 |

48 coins were traded and 42 of them lost. The five worst and the five best:

| Coin | Positions | Won | Sum | Mean | t | Funding | Price | Costs |
|---|---|---|---|---|---|---|---|---|
| AKE | 26 | 3 | -1,005 bp | -38.6 bp | -3.57 | 262 | -382 | 884 |
| BTW | 20 | 3 | -821 bp | -41.0 bp | -7.06 | 61 | -202 | 680 |
| IRYS | 15 | 3 | -481 bp | -32.1 bp | -3.52 | 153 | -125 | 510 |
| SOXL | 13 | 1 | -447 bp | -34.4 bp | -8.24 | 62 | -68 | 442 |
| AGT | 20 | 2 | -416 bp | -20.8 bp | -1.10 | 48 | 216 | 680 |
| INIT | 7 | 5 | 917 bp | 131.0 bp | 1.67 | 1,009 | 165 | 257 |
| IOST | 4 | 3 | 450 bp | 112.4 bp | 0.98 | 358 | 227 | 136 |
| BULLA | 8 | 4 | 267 bp | 33.4 bp | 0.55 | 276 | 264 | 272 |
| RSR | 3 | 3 | 58 bp | 19.4 bp | 1.47 | 67 | 98 | 107 |
| IDOL | 2 | 1 | 20 bp | 10.0 bp | 0.52 | 74 | 14 | 68 |

Concentration: the most traded coin (AKE) is 10.7% of the positions; by count the book is 21.4 equal coins. Venue pairs: short mexc / long gate 188, short gate / long mexc 25, short gate / long hyperliquid 11, short hyperliquid / long gate 8, short hyperliquid / long mexc 8, short mexc / long hyperliquid 2, short dydx / long gate 1.

| Open now | Short / long | Opened | Entry spread | Funding | Price | Fills paid | Net at the marks | Net if closed now |
|---|---|---|---|---|---|---|---|---|
| BLESS | mexc / gate | 2026-11-17 04:00 UTC | 28.2%/yr | 17.3 | 21.4 | 17.0 | 21.7 bp | 4.7 bp |
| SOXL | mexc / gate | 2026-11-17 08:00 UTC | 25.1%/yr | 12.0 | -3.9 | 17.0 | -9.0 bp | -26.0 bp |
| SOXS | gate / mexc | 2026-11-17 18:00 UTC | 26.4%/yr | 14.4 | -3.3 | 17.0 | -5.9 bp | -22.9 bp |
| EVAA | mexc / gate | 2026-11-18 15:00 UTC | 45.8%/yr | 2.7 | -30.3 | 17.0 | -44.6 bp | -61.6 bp |
| PIEVERSE | mexc / gate | 2026-11-18 18:00 UTC | 26.1%/yr | 3.6 | 13.4 | 17.0 | 0.1 bp | -16.9 bp |
| KORU | mexc / gate | 2026-11-18 20:00 UTC | 39.0%/yr | 0.0 | 0.0 | 17.0 | -17.0 bp | -34.0 bp |

## 3. The weakness, the hypothesis and the experiment

**Largest weakness** (a class known when a position is opened, measured against the rest of the book): entry spread, *under 50%/yr*: 138 positions, mean -28.2 bp (t -7.52) against -8.8 bp for the rest (t of the difference -1.80); 2,668 bp lost beyond what the rest would have.

**Hypothesis.** Positions opened on a trailing spread under 50%/yr do not earn their round trip. Asking twice the spread at the entry removes them; whether the entries that remain earn more than cash is what the replay measures.

**Tested by** the declared variant `thick-entry` in the replay below.

### The replay: the radar's frozen rules and the declared variants on the same stored quotes

Stored hours in hand: 327 (2026-11-04 23:00 UTC to 2026-11-18 17:00 UTC); days archived: 14; added this cycle: none.

Fidelity: the replay of the original rules reproduces 53 of the radar's 58 real positions opened in these hours to the hundredth of a basis point (58 matched by entry). Differences: 0 only in the real ledger, 2 only in the replay; 2 of them on a coin the radar already held when the replay began (AKE, IDOL, SOL, SOXL, UAI). The replay is taken as faithful.

Earlier part 2026-11-07 22:00 UTC to 2026-11-13 00:00 UTC; later part to 2026-11-18 18:00 UTC. Excess over cash in % of the book.

| Variant | What changes | Earlier: excess | positions | Later: excess | positions | closed | t (daily) | Later, less the original | its t |
|---|---|---|---|---|---|---|---|---|---|
| `original` | nothing: the registered rules | 0.1072% | 25 | -0.3322% | 35 | 30 | -1.12 | 0.0000% | n/a |
| `same-window` | trailing_entry_h=24 | -0.0048% | 35 | -0.3177% | 40 | 34 | -1.52 | 0.0144% | 0.10 |
| `thick-entry` | entry_trailing_apr=0.5, entry_now_apr=0.3 | 0.1833% | 17 | -0.0410% | 16 | 16 | -0.17 | 0.2912% | 1.73 |
| `patient-exit` | exit_now_apr=-1.0 | 0.1689% | 23 | -0.1437% | 29 | 23 | -0.50 | 0.1885% | 2.55 |
| `all-three` | trailing_entry_h=24, entry_trailing_apr=0.5, entry_now_apr=0.3, exit_now_apr=-1.0 | 0.1939% | 20 | 0.1006% | 15 | 12 | 0.52 | 0.4328% | 2.84 |

Candidate, chosen on the earlier part only: `all-three` (4 variants compared). **INCONCLUSIVE**: the later part holds 6 days and 12 closed positions: 30 and 30 are needed before anything is judged.

Gates on the later part: enough days no, enough positions no, excess over cash no, beats the original no, costs x1.5 no, without best coin no.

A variant is proposed as a registered challenger only when every gate holds. A proposal is a request for a preregistered forward test, never a replacement of the original.

### Registered challengers, judged forward

None is registered. RADX-1, the diagnosis these variants came from, failed as registered (one of its two parts did not hold on the later positions), and by its own rule no challenger follows from it. One is registered only after a variant passes the gates above.


## 4. What is not claimed

- An unrealized gain is a valuation at the last close. It is not profit until the trade is closed.
- A variant that loses less than the original has not been shown to earn anything.
- No figure here is a backtest, and none is added to a research result.
