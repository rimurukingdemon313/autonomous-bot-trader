# Paper systems: the performance audit and the optimization cycle

**PAPER ONLY · NOT REAL MONEY · NOTHING HERE IS A PROFIT CLAIM.** Written by the performance cycle on GitHub's runner (`scripts/perf_cycle.py`), with no person in the loop. It reads the paper systems' own ledgers, recomputes every figure by a second route, and changes neither system.

**بالعربي:** مكتب TRND-1: الرصيد $199,456.62، المحقّق $0.00، غير المحقّق -$543.39، الصفقات المسكّرة 0. رادار RADAR-1: دفتره -2.12% من رأس ماله الورقي، 219 صفقة مسكّرة، الرابح منها 42. المطابقة: كل الأرقام تطابقت من مصدرين. تجربة التحسين: غير حاسمة لأن العيّنة صغيرة. المنافسين المسجّلين: 0. النظام الأصلي ما انلمس.

Updated 2026-11-17 11:17 UTC · perf-1.0.1 · cycles so far: 12

## 1. TRND-1: the trend desk's paper account

**Reconciled: 40 of 40 checks hold.** Each compares two routes to the same figure.

Last session: 2026-11-16 21:00 UTC. Paper only: no real money.

| | |
|---|---|
| Initial capital | $200,000.00 |
| Equity now | $199,456.62 |
| **Realized** P&L (closed trades, after every cost) | $0.00 from $0.00 gross |
| **Unrealized** P&L (open trades at the last close: a valuation, not a profit) | -$543.39 |
| Net after all costs (realized plus unrealized) | -$543.38 (-0.272%) |
| Open positions | 4 |
| Closed trades | 0: 0 won, 0 lost |
| Win rate | undefined: no closed trade |
| Average win / average loss | undefined: no closed trade / undefined: no closed trade |
| Profit factor | undefined: no closed trade |
| Maximum drawdown, session closes | $1,832.48 |
| Maximum drawdown, inside a day | $1,975.39 |
| Below the peak now | $1,832.48 |
| Gross exposure | $97,471.75, 0.49x the equity |
| Loss if every stop were hit from here | $5,845.23 (limit $8,000.00) |
| Losing days | 5 of 6 |

Trade statistics: sample **none** (0 closed). A ratio over no closed trade does not exist and is not shown as zero.

### Open positions and where the risk sits

| Index | Units | Entry | Mark | Move | Unrealized | Notional | Share of gross | Stop | Loss at the stop from here |
|---|---|---|---|---|---|---|---|---|---|
| GER40 | 0.84 | 26,268.04 | 26,597.89 | 1.26% | +$306.17 | $24,688.64 | 25.3% | 25,002.72 | $1,480.67 |
| UK100 | 1.7 | 10,783.50 | 10,881.10 | 0.91% | +$219.53 | $24,475.21 | 25.1% | 10,228.70 | $1,467.46 |
| US500 | 3.25 | 7,550.29 | 7,416.34 | -1.77% | -$435.34 | $24,103.10 | 24.7% | 6,971.59 | $1,445.44 |
| NAS100 | 0.89 | 27,908.47 | 27,196.40 | -2.55% | -$633.75 | $24,204.80 | 24.8% | 25,565.32 | $1,451.66 |

Concentration: 4 positions, the largest 25.3% of the gross; by size that is 4.0 equal positions, and by risk it is **one**: four equity indices, all long: one risk factor held four times.

### Against a benchmark

| | Since the start | What it is |
|---|---|---|
| The desk | -$543.38 | realized plus unrealized, after costs |
| Cash | +$152.61 | 3.875% a year on the starting balance for 7.19 days |
| The same indices bought and held | -$543.39 | identical to the desk while no trade has closed: the rule has not yet made one decision the holder would not have made |
| The same positions at one times the account | -$1,099.84 | the same P&L scaled from the desk's exposure to one times the account: what the validated rule's own sizing would show; the desk's risk limits do not allow it |

### Month by month, against the $4,000 target (a target, never a quota)

| Month | Days | Net | Of $4,000 |
|---|---|---|---|
| 2026-11 | 6 | -$543.38 | -13.6% |

## 2. RADAR-1: the funding radar's paper ledger

**Reconciled: 24 of 24 checks hold.** Each compares two routes to the same figure.

Marks from 2026-10-07 20:00 UTC to 2026-11-17 11:00 UTC (40.62 days). Paper only: no order is ever sent. Its preregistered single look is on 2026-12-06 and is read as registered, whatever this audit says.

Capital: ten slots of 2N: 20N. The radar has no cash account; N is not a dollar amount. P&L is in basis points (bp) of one leg's notional; 2,000 bp summed over positions is 1% of the book.

| | In bp of N | In % of the book | On a $100,000 book (illustration) |
|---|---|---|---|
| **Realized** (closed positions, after every fill) | -4,162.9 | -2.0815% | -$2,081.46 |
| **Unrealized** (open positions at their marks, entry fills paid) | -84.4 | -0.0422% | -$42.20 |
| The book if every open position were closed now | -4,366.3 | -2.1832% | -$2,183.16 |

| | |
|---|---|
| Closed positions | 219: 42 won, 177 lost |
| Win rate | 19.2% |
| Average win / average loss | 77.3 bp / -41.9 bp |
| Profit factor | 0.44 |
| Mean net a position | -19.0 bp (t -3.71) |
| Open positions | 7 of 10 slots; on average 22.4% of the capital was deployed |
| Book P&L | -2.1237% |
| Book excess over cash (3.875%/yr on the capital in use) | -2.2791% |
| Annualised excess on the capital deployed | -92.1%/yr |
| The same with costs x1.5 / x2 | -170.6% / -249.2% |
| Maximum drawdown of the book (hourly marks) | 2.1986% |
| t of the daily excess | -3.60 |
| Best coin, and the book's excess without it | INIT: -2.7334% |

### Where it came from

Funding received **3,173 bp**, price moves between the legs **201 bp**, fills **-7,537 bp**: net **-4,163 bp**. A position earned 15.4 bp before costs and paid 34.4 bp: the costs are 2.23 times the gross. Half the positions were closed within 3.0 hours.

| Held for | Positions | Won | Sum | Mean | t | Funding | Price | Costs |
|---|---|---|---|---|---|---|---|---|
| 1 to 6 hours | 83 | 14 | -2,492 bp | -30.0 bp | -4.03 | 827 | -485 | 2,834 |
| 1 hour or less | 72 | 5 | -2,400 bp | -33.3 bp | -5.37 | 44 | 45 | 2,488 |
| over 3 days | 2 | 1 | -22 bp | -10.9 bp | -0.90 | 56 | -4 | 74 |
| 6 to 24 hours | 45 | 14 | 57 bp | 1.3 bp | 0.12 | 1,150 | 466 | 1,559 |
| 1 to 3 days | 17 | 8 | 693 bp | 40.8 bp | 1.16 | 1,096 | 178 | 582 |

| Closed for | Positions | Won | Sum | Mean | t | Funding | Price | Costs |
|---|---|---|---|---|---|---|---|---|
| spread_reversed | 122 | 24 | -2,574 bp | -21.1 bp | -3.82 | 1,740 | -123 | 4,191 |
| spread_decayed | 63 | 3 | -2,242 bp | -35.6 bp | -13.97 | 92 | -149 | 2,185 |
| rebalance | 34 | 15 | 654 bp | 19.2 bp | 0.76 | 1,342 | 473 | 1,161 |

| Known at the entry: entry spread | Positions | Won | Sum | Mean | t | Funding | Price | Costs |
|---|---|---|---|---|---|---|---|---|
| under 50%/yr | 125 | 19 | -3,430 bp | -27.4 bp | -6.68 | 832 | 56 | 4,317 |
| 50 to 100%/yr | 53 | 12 | -535 bp | -10.1 bp | -0.77 | 873 | 399 | 1,807 |
| 100%/yr or more | 41 | 11 | -198 bp | -4.8 bp | -0.28 | 1,469 | -254 | 1,413 |

| Known at the entry: venue pair | Positions | Won | Sum | Mean | t | Funding | Price | Costs |
|---|---|---|---|---|---|---|---|---|
| short mexc / long gate | 169 | 33 | -3,584 bp | -21.2 bp | -4.00 | 1,904 | 258 | 5,746 |
| short gate / long mexc | 20 | 3 | -281 bp | -14.1 bp | -0.45 | 744 | -345 | 680 |
| short hyperliquid / long gate | 8 | 1 | -215 bp | -26.9 bp | -2.73 | 56 | 41 | 312 |
| short hyperliquid / long mexc | 8 | 1 | -131 bp | -16.3 bp | -1.21 | 162 | -29 | 264 |
| short mexc / long hyperliquid | 2 | 0 | -42 bp | -21.1 bp | -2.36 | 21 | 3 | 66 |
| short dydx / long gate | 1 | 0 | -23 bp | -22.9 bp | n/a | 13 | 4 | 40 |
| short gate / long hyperliquid | 11 | 4 | 113 bp | 10.3 bp | 0.46 | 273 | 269 | 429 |

| Known at the entry: time since the coin's previous position | Positions | Won | Sum | Mean | t | Funding | Price | Costs |
|---|---|---|---|---|---|---|---|---|
| within 6 hours of the coin's previous exit | 143 | 26 | -2,352 bp | -16.4 bp | -2.18 | 2,330 | 222 | 4,904 |
| a first entry, or later | 76 | 16 | -1,811 bp | -23.8 bp | -5.86 | 843 | -21 | 2,633 |

45 coins were traded and 39 of them lost. The five worst and the five best:

| Coin | Positions | Won | Sum | Mean | t | Funding | Price | Costs |
|---|---|---|---|---|---|---|---|---|
| AKE | 25 | 3 | -997 bp | -39.9 bp | -3.56 | 247 | -394 | 850 |
| BTW | 20 | 3 | -821 bp | -41.0 bp | -7.06 | 61 | -202 | 680 |
| IRYS | 15 | 3 | -481 bp | -32.1 bp | -3.52 | 153 | -125 | 510 |
| SOXL | 13 | 1 | -447 bp | -34.4 bp | -8.24 | 62 | -68 | 442 |
| AGT | 20 | 2 | -416 bp | -20.8 bp | -1.10 | 48 | 216 | 680 |
| INIT | 7 | 5 | 917 bp | 131.0 bp | 1.67 | 1,009 | 165 | 257 |
| IOST | 4 | 3 | 450 bp | 112.4 bp | 0.98 | 358 | 227 | 136 |
| BULLA | 8 | 4 | 267 bp | 33.4 bp | 0.55 | 276 | 264 | 272 |
| RSR | 3 | 3 | 58 bp | 19.4 bp | 1.47 | 67 | 98 | 107 |
| IDOL | 2 | 1 | 20 bp | 10.0 bp | 0.52 | 74 | 14 | 68 |

Concentration: the most traded coin (AKE) is 11.5% of the positions; by count the book is 19.4 equal coins. Venue pairs: short mexc / long gate 176, short gate / long mexc 20, short gate / long hyperliquid 11, short hyperliquid / long gate 8, short hyperliquid / long mexc 8, short mexc / long hyperliquid 2, short dydx / long gate 1.

| Open now | Short / long | Opened | Entry spread | Funding | Price | Fills paid | Net at the marks | Net if closed now |
|---|---|---|---|---|---|---|---|---|
| PIEVERSE | mexc / gate | 2026-11-09 21:00 UTC | 35.8%/yr | 39.0 | -22.2 | 17.0 | -0.2 bp | -17.2 bp |
| AKE | mexc / gate | 2026-11-17 02:00 UTC | 88.8%/yr | 10.3 | -12.5 | 17.0 | -19.3 bp | -36.3 bp |
| BLESS | mexc / gate | 2026-11-17 04:00 UTC | 28.2%/yr | 5.5 | 14.1 | 17.0 | 2.6 bp | -14.4 bp |
| SOXL | mexc / gate | 2026-11-17 08:00 UTC | 25.1%/yr | 1.4 | -5.9 | 17.0 | -21.5 bp | -38.5 bp |
| EVAA | mexc / gate | 2026-11-17 09:00 UTC | 60.2%/yr | 0.2 | 4.7 | 17.0 | -12.1 bp | -29.1 bp |
| KORU | mexc / gate | 2026-11-17 09:00 UTC | 25.4%/yr | 0.5 | -0.5 | 17.0 | -17.0 bp | -34.0 bp |
| SNXX | mexc / gate | 2026-11-17 11:00 UTC | 25.2%/yr | 0.0 | 0.0 | 17.0 | -17.0 bp | -34.0 bp |

## 3. The weakness, the hypothesis and the experiment

**Largest weakness** (a class known when a position is opened, measured against the rest of the book): entry spread, *under 50%/yr*: 125 positions, mean -27.4 bp (t -6.68) against -7.8 bp for the rest (t of the difference -1.73); 2,455 bp lost beyond what the rest would have.

**Hypothesis.** Positions opened on a trailing spread under 50%/yr do not earn their round trip. Asking twice the spread at the entry removes them; whether the entries that remain earn more than cash is what the replay measures.

**Tested by** the declared variant `thick-entry` in the replay below.

### The replay: the radar's frozen rules and the declared variants on the same stored quotes

Stored hours in hand: 297 (2026-11-04 23:00 UTC to 2026-11-17 11:00 UTC); days archived: 13; added this cycle: none.

Fidelity: the replay of the original rules reproduces 45 of the radar's 45 real positions opened in these hours to the hundredth of a basis point (45 matched by entry). Differences: 0 only in the real ledger, 2 only in the replay; 2 of them on a coin the radar already held when the replay began (AKE, IDOL, SOL, SOXL, UAI). The replay is taken as faithful.

Earlier part 2026-11-07 22:00 UTC to 2026-11-12 00:00 UTC; later part to 2026-11-17 12:00 UTC. Excess over cash in % of the book.

| Variant | What changes | Earlier: excess | positions | Later: excess | positions | closed | t (daily) | Later, less the original | its t |
|---|---|---|---|---|---|---|---|---|---|
| `original` | nothing: the registered rules | 0.0840% | 18 | -0.0612% | 29 | 23 | -0.30 | 0.0000% | n/a |
| `same-window` | trailing_entry_h=24 | -0.0668% | 30 | -0.1074% | 37 | 30 | -0.52 | -0.0462% | -0.68 |
| `thick-entry` | entry_trailing_apr=0.5, entry_now_apr=0.3 | 0.0889% | 16 | 0.1178% | 14 | 12 | 0.47 | 0.1790% | 2.01 |
| `patient-exit` | exit_now_apr=-1.0 | 0.1231% | 17 | 0.1187% | 22 | 15 | 0.64 | 0.1799% | 2.46 |
| `all-three` | trailing_entry_h=24, entry_trailing_apr=0.5, entry_now_apr=0.3, exit_now_apr=-1.0 | 0.0795% | 19 | 0.2694% | 13 | 8 | 1.41 | 0.3306% | 3.94 |

Candidate, chosen on the earlier part only: `patient-exit` (4 variants compared). **INCONCLUSIVE**: the later part holds 6 days and 15 closed positions: 30 and 30 are needed before anything is judged.

Gates on the later part: enough days no, enough positions no, excess over cash no, beats the original no, costs x1.5 no, without best coin no.

A variant is proposed as a registered challenger only when every gate holds. A proposal is a request for a preregistered forward test, never a replacement of the original.

### Registered challengers, judged forward

None is registered. RADX-1, the diagnosis these variants came from, failed as registered (one of its two parts did not hold on the later positions), and by its own rule no challenger follows from it. One is registered only after a variant passes the gates above.


## 4. What is not claimed

- An unrealized gain is a valuation at the last close. It is not profit until the trade is closed.
- A variant that loses less than the original has not been shown to earn anything.
- No figure here is a backtest, and none is added to a research result.
