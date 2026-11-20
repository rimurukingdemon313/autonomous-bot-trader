# Paper systems: the performance audit and the optimization cycle

**PAPER ONLY · NOT REAL MONEY · NOTHING HERE IS A PROFIT CLAIM.** Written by the performance cycle on GitHub's runner (`scripts/perf_cycle.py`), with no person in the loop. It reads the paper systems' own ledgers, recomputes every figure by a second route, and changes neither system.

**بالعربي:** مكتب TRND-1: الرصيد $197,543.01، المحقّق $0.00، غير المحقّق -$2,456.98، الصفقات المسكّرة 0. رادار RADAR-1: دفتره -2.43% من رأس ماله الورقي، 242 صفقة مسكّرة، الرابح منها 43. المطابقة: كل الأرقام تطابقت من مصدرين. تجربة التحسين: غير حاسمة لأن العيّنة صغيرة. المنافسين المسجّلين: 0. النظام الأصلي ما انلمس.

Updated 2026-11-20 02:25 UTC · perf-1.0.1 · cycles so far: 25

## 1. TRND-1: the trend desk's paper account

**Reconciled: 40 of 40 checks hold.** Each compares two routes to the same figure.

Last session: 2026-11-18 21:00 UTC. Paper only: no real money.

| | |
|---|---|
| Initial capital | $200,000.00 |
| Equity now | $197,543.01 |
| **Realized** P&L (closed trades, after every cost) | $0.00 from $0.00 gross |
| **Unrealized** P&L (open trades at the last close: a valuation, not a profit) | -$2,456.98 |
| Net after all costs (realized plus unrealized) | -$2,456.99 (-1.228%) |
| Open positions | 4 |
| Closed trades | 0: 0 won, 0 lost |
| Win rate | undefined: no closed trade |
| Average win / average loss | undefined: no closed trade / undefined: no closed trade |
| Profit factor | undefined: no closed trade |
| Maximum drawdown, session closes | $3,793.05 |
| Maximum drawdown, inside a day | $4,153.85 |
| Below the peak now | $3,746.09 |
| Gross exposure | $95,357.64, 0.48x the equity |
| Loss if every stop were hit from here | $5,718.37 (limit $8,000.00) |
| Losing days | 7 of 8 |

Trade statistics: sample **none** (0 closed). A ratio over no closed trade does not exist and is not shown as zero.

### Open positions and where the risk sits

| Index | Units | Entry | Mark | Move | Unrealized | Notional | Share of gross | Stop | Loss at the stop from here |
|---|---|---|---|---|---|---|---|---|---|
| GER40 | 0.84 | 26,268.04 | 25,735.49 | -2.03% | -$491.99 | $23,775.69 | 24.9% | 24,192.07 | $1,425.89 |
| UK100 | 1.7 | 10,783.50 | 10,550.70 | -2.16% | -$521.79 | $23,648.17 | 24.8% | 9,918.13 | $1,417.83 |
| US500 | 3.25 | 7,550.29 | 7,323.38 | -3.01% | -$737.46 | $23,800.98 | 25.0% | 6,884.21 | $1,427.30 |
| NAS100 | 0.89 | 27,908.47 | 27,115.51 | -2.84% | -$705.74 | $24,132.80 | 25.3% | 25,489.28 | $1,447.34 |

Concentration: 4 positions, the largest 25.3% of the gross; by size that is 4.0 equal positions, and by risk it is **one**: four equity indices, all long: one risk factor held four times.

### Against a benchmark

| | Since the start | What it is |
|---|---|---|
| The desk | -$2,456.99 | realized plus unrealized, after costs |
| Cash | +$195.08 | 3.875% a year on the starting balance for 9.19 days |
| The same indices bought and held | -$2,456.98 | identical to the desk while no trade has closed: the rule has not yet made one decision the holder would not have made |
| The same positions at one times the account | -$4,973.02 | the same P&L scaled from the desk's exposure to one times the account: what the validated rule's own sizing would show; the desk's risk limits do not allow it |

### Month by month, against the $4,000 target (a target, never a quota)

| Month | Days | Net | Of $4,000 |
|---|---|---|---|
| 2026-11 | 8 | -$2,456.99 | -61.4% |

## 2. RADAR-1: the funding radar's paper ledger

**Reconciled: 24 of 24 checks hold.** Each compares two routes to the same figure.

Marks from 2026-10-07 20:00 UTC to 2026-11-20 02:00 UTC (43.25 days). Paper only: no order is ever sent. Its preregistered single look is on 2026-12-06 and is read as registered, whatever this audit says.

Capital: ten slots of 2N: 20N. The radar has no cash account; N is not a dollar amount. P&L is in basis points (bp) of one leg's notional; 2,000 bp summed over positions is 1% of the book.

| | In bp of N | In % of the book | On a $100,000 book (illustration) |
|---|---|---|---|
| **Realized** (closed positions, after every fill) | -4,932.6 | -2.4663% | -$2,466.30 |
| **Unrealized** (open positions at their marks, entry fills paid) | 70.2 | 0.0351% | +$35.12 |
| The book if every open position were closed now | -4,947.4 | -2.4737% | -$2,473.68 |

| | |
|---|---|
| Closed positions | 242: 43 won, 199 lost |
| Win rate | 17.8% |
| Average win / average loss | 75.6 bp / -41.1 bp |
| Profit factor | 0.40 |
| Mean net a position | -20.4 bp (t -4.36) |
| Open positions | 5 of 10 slots; on average 24.9% of the capital was deployed |
| Book P&L | -2.4312% |
| Book excess over cash (3.875%/yr on the capital in use) | -2.5873% |
| Annualised excess on the capital deployed | -88.2%/yr |
| The same with costs x1.5 / x2 | -160.6% / -233.0% |
| Maximum drawdown of the book (hourly marks) | 2.4922% |
| t of the daily excess | -3.84 |
| Best coin, and the book's excess without it | INIT: -3.0416% |

### Where it came from

Funding received **3,294 bp**, price moves between the legs **92 bp**, fills **-8,319 bp**: net **-4,933 bp**. A position earned 14.0 bp before costs and paid 34.4 bp: the costs are 2.46 times the gross. Half the positions were closed within 3.0 hours.

| Held for | Positions | Won | Sum | Mean | t | Funding | Price | Costs |
|---|---|---|---|---|---|---|---|---|
| 1 hour or less | 82 | 5 | -2,752 bp | -33.6 bp | -6.13 | 46 | 30 | 2,828 |
| 1 to 6 hours | 86 | 15 | -2,594 bp | -30.2 bp | -4.17 | 836 | -495 | 2,936 |
| 6 to 24 hours | 50 | 14 | -187 bp | -3.7 bp | -0.37 | 1,165 | 377 | 1,729 |
| over 3 days | 3 | 1 | -62 bp | -20.5 bp | -1.72 | 100 | -54 | 108 |
| 1 to 3 days | 21 | 8 | 662 bp | 31.5 bp | 1.10 | 1,146 | 234 | 718 |

| Closed for | Positions | Won | Sum | Mean | t | Funding | Price | Costs |
|---|---|---|---|---|---|---|---|---|
| spread_reversed | 130 | 25 | -2,745 bp | -21.1 bp | -4.07 | 1,770 | -52 | 4,463 |
| spread_decayed | 76 | 3 | -2,708 bp | -35.6 bp | -15.16 | 131 | -212 | 2,627 |
| rebalance | 36 | 15 | 521 bp | 14.5 bp | 0.60 | 1,394 | 356 | 1,229 |

| Known at the entry: entry spread | Positions | Won | Sum | Mean | t | Funding | Price | Costs |
|---|---|---|---|---|---|---|---|---|
| under 50%/yr | 143 | 19 | -4,058 bp | -28.4 bp | -7.77 | 934 | -64 | 4,929 |
| 50 to 100%/yr | 58 | 13 | -676 bp | -11.7 bp | -0.97 | 891 | 410 | 1,977 |
| 100%/yr or more | 41 | 11 | -198 bp | -4.8 bp | -0.28 | 1,469 | -254 | 1,413 |

| Known at the entry: venue pair | Positions | Won | Sum | Mean | t | Funding | Price | Costs |
|---|---|---|---|---|---|---|---|---|
| short mexc / long gate | 187 | 33 | -4,201 bp | -22.5 bp | -4.66 | 2,000 | 157 | 6,358 |
| short gate / long mexc | 25 | 4 | -433 bp | -17.3 bp | -0.69 | 769 | -352 | 850 |
| short hyperliquid / long gate | 8 | 1 | -215 bp | -26.9 bp | -2.73 | 56 | 41 | 312 |
| short hyperliquid / long mexc | 8 | 1 | -131 bp | -16.3 bp | -1.21 | 162 | -29 | 264 |
| short mexc / long hyperliquid | 2 | 0 | -42 bp | -21.1 bp | -2.36 | 21 | 3 | 66 |
| short dydx / long gate | 1 | 0 | -23 bp | -22.9 bp | n/a | 13 | 4 | 40 |
| short gate / long hyperliquid | 11 | 4 | 113 bp | 10.3 bp | 0.46 | 273 | 269 | 429 |

| Known at the entry: time since the coin's previous position | Positions | Won | Sum | Mean | t | Funding | Price | Costs |
|---|---|---|---|---|---|---|---|---|
| within 6 hours of the coin's previous exit | 156 | 26 | -2,804 bp | -18.0 bp | -2.58 | 2,380 | 162 | 5,346 |
| a first entry, or later | 86 | 17 | -2,128 bp | -24.7 bp | -6.70 | 914 | -70 | 2,973 |

50 coins were traded and 44 of them lost. The five worst and the five best:

| Coin | Positions | Won | Sum | Mean | t | Funding | Price | Costs |
|---|---|---|---|---|---|---|---|---|
| AKE | 26 | 3 | -1,005 bp | -38.6 bp | -3.57 | 262 | -382 | 884 |
| BTW | 20 | 3 | -821 bp | -41.0 bp | -7.06 | 61 | -202 | 680 |
| IRYS | 16 | 3 | -523 bp | -32.7 bp | -3.83 | 158 | -138 | 544 |
| SOXL | 13 | 1 | -447 bp | -34.4 bp | -8.24 | 62 | -68 | 442 |
| AGT | 20 | 2 | -416 bp | -20.8 bp | -1.10 | 48 | 216 | 680 |
| INIT | 7 | 5 | 917 bp | 131.0 bp | 1.67 | 1,009 | 165 | 257 |
| IOST | 4 | 3 | 450 bp | 112.4 bp | 0.98 | 358 | 227 | 136 |
| BULLA | 8 | 4 | 267 bp | 33.4 bp | 0.55 | 276 | 264 | 272 |
| RSR | 3 | 3 | 58 bp | 19.4 bp | 1.47 | 67 | 98 | 107 |
| IDOL | 2 | 1 | 20 bp | 10.0 bp | 0.52 | 74 | 14 | 68 |

Concentration: the most traded coin (AKE) is 10.5% of the positions; by count the book is 21.5 equal coins. Venue pairs: short mexc / long gate 192, short gate / long mexc 25, short gate / long hyperliquid 11, short hyperliquid / long gate 8, short hyperliquid / long mexc 8, short mexc / long hyperliquid 2, short dydx / long gate 1.

| Open now | Short / long | Opened | Entry spread | Funding | Price | Fills paid | Net at the marks | Net if closed now |
|---|---|---|---|---|---|---|---|---|
| SOXL | mexc / gate | 2026-11-17 08:00 UTC | 25.1%/yr | 20.0 | 0.3 | 17.0 | 3.3 bp | -13.7 bp |
| PIEVERSE | mexc / gate | 2026-11-18 18:00 UTC | 26.1%/yr | 21.4 | 11.5 | 17.0 | 15.9 bp | -1.1 bp |
| KORU | mexc / gate | 2026-11-18 20:00 UTC | 39.0%/yr | 9.6 | 6.1 | 17.0 | -1.3 bp | -18.3 bp |
| EVAA | mexc / gate | 2026-11-19 15:00 UTC | 25.9%/yr | 14.8 | 17.4 | 17.0 | 15.2 bp | -1.8 bp |
| IRYS | mexc / gate | 2026-11-19 20:00 UTC | 34.4%/yr | 35.7 | 18.4 | 17.0 | 37.1 bp | 20.1 bp |

## 3. The weakness, the hypothesis and the experiment

**Largest weakness** (a class known when a position is opened, measured against the rest of the book): entry spread, *under 50%/yr*: 143 positions, mean -28.4 bp (t -7.77) against -8.8 bp for the rest (t of the difference -1.83); 2,796 bp lost beyond what the rest would have.

**Hypothesis.** Positions opened on a trailing spread under 50%/yr do not earn their round trip. Asking twice the spread at the entry removes them; whether the entries that remain earn more than cash is what the replay measures.

**Tested by** the declared variant `thick-entry` in the replay below.

### The replay: the radar's frozen rules and the declared variants on the same stored quotes

Stored hours in hand: 357 (2026-11-04 23:00 UTC to 2026-11-19 23:00 UTC); days archived: 15; added this cycle: none.

Fidelity: the replay of the original rules reproduces 61 of the radar's 66 real positions opened in these hours to the hundredth of a basis point (66 matched by entry). Differences: 0 only in the real ledger, 2 only in the replay; 2 of them on a coin the radar already held when the replay began (AKE, IDOL, SOL, SOXL, UAI). The replay is taken as faithful.

Earlier part 2026-11-07 22:00 UTC to 2026-11-13 00:00 UTC; later part to 2026-11-20 00:00 UTC. Excess over cash in % of the book.

| Variant | What changes | Earlier: excess | positions | Later: excess | positions | closed | t (daily) | Later, less the original | its t |
|---|---|---|---|---|---|---|---|---|---|
| `all-three` | entry_now_apr=0.3, entry_trailing_apr=0.5, exit_now_apr=-1.0, trailing_entry_h=24 | 0.1939% | 20 | 0.0943% | 20 | 16 | 0.49 | 0.5360% | 2.90 |
| `original` | nothing: the registered rules | 0.1072% | 25 | -0.4416% | 43 | 38 | -1.36 | 0.0000% | n/a |
| `patient-exit` | exit_now_apr=-1.0 | 0.1689% | 23 | -0.2411% | 37 | 32 | -0.77 | 0.2005% | 2.58 |
| `same-window` | trailing_entry_h=24 | -0.0048% | 35 | -0.3499% | 44 | 39 | -1.70 | 0.0917% | 0.48 |
| `thick-entry` | entry_now_apr=0.3, entry_trailing_apr=0.5 | 0.1833% | 17 | -0.0410% | 16 | 16 | -0.17 | 0.4006% | 1.95 |

Candidate, chosen on the earlier part only: `all-three` (4 variants compared). **INCONCLUSIVE**: the later part holds 7 days and 16 closed positions: 30 and 30 are needed before anything is judged.

Gates on the later part: beats the original no, costs x1.5 no, enough days no, enough positions no, excess over cash no, without best coin no.

A variant is proposed as a registered challenger only when every gate holds. A proposal is a request for a preregistered forward test, never a replacement of the original.

### Registered challengers, judged forward

None is registered. RADX-1, the diagnosis these variants came from, failed as registered (one of its two parts did not hold on the later positions), and by its own rule no challenger follows from it. One is registered only after a variant passes the gates above.


## 4. What is not claimed

- An unrealized gain is a valuation at the last close. It is not profit until the trade is closed.
- A variant that loses less than the original has not been shown to earn anything.
- No figure here is a backtest, and none is added to a research result.
