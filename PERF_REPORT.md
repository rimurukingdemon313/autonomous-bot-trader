# Paper systems: the performance audit and the optimization cycle

**PAPER ONLY · NOT REAL MONEY · NOTHING HERE IS A PROFIT CLAIM.** Written by the performance cycle on GitHub's runner (`scripts/perf_cycle.py`), with no person in the loop. It reads the paper systems' own ledgers, recomputes every figure by a second route, and changes neither system.

**بالعربي:** مكتب TRND-1: الرصيد $194,462.42، المحقّق -$2,660.70، غير المحقّق -$2,876.88، الصفقات المسكّرة 1. رادار RADAR-1: دفتره -2.70% من رأس ماله الورقي، 268 صفقة مسكّرة، الرابح منها 47. المطابقة: كل الأرقام تطابقت من مصدرين. تجربة التحسين: غير حاسمة لأن العيّنة صغيرة. المنافسين المسجّلين: 0. النظام الأصلي ما انلمس.

Updated 2026-11-24 23:17 UTC · perf-1.0.1 · cycles so far: 47

## 1. TRND-1: the trend desk's paper account

**Reconciled: 37 of 37 checks hold.** Each compares two routes to the same figure.

Last session: 2026-11-24 16:30 UTC. Paper only: no real money.

| | |
|---|---|
| Initial capital | $200,000.00 |
| Equity now | $194,462.42 |
| **Realized** P&L (closed trades, after every cost) | -$2,660.70 from -$2,652.95 gross |
| **Unrealized** P&L (open trades at the last close: a valuation, not a profit) | -$2,876.88 |
| Net after all costs (realized plus unrealized) | -$5,537.58 (-2.769%) |
| Open positions | 3 |
| Closed trades | 1: 0 won, 1 lost |
| Win rate | 0.0% |
| Average win / average loss | undefined: no winning trade / -$2,660.70 |
| Profit factor | 0.00 |
| Maximum drawdown, session closes | $8,359.66 |
| Maximum drawdown, inside a day | $8,490.31 |
| Below the peak now | $6,826.68 |
| Gross exposure | $69,875.47, 0.36x the equity |
| Loss if every stop were hit from here | $4,190.06 (limit $8,000.00) |
| Losing days | 10 of 12 |

Trade statistics: sample **insufficient** (1 closed). A ratio over no closed trade does not exist and is not shown as zero.

### Open positions and where the risk sits

| Index | Units | Entry | Mark | Move | Unrealized | Notional | Share of gross | Stop | Loss at the stop from here |
|---|---|---|---|---|---|---|---|---|---|
| GER40 | 0.84 | 26,268.04 | 25,017.06 | -4.76% | -$1,152.91 | $23,055.93 | 33.0% | 23,516.74 | $1,382.71 |
| UK100 | 1.7 | 10,783.50 | 10,466.57 | -2.94% | -$705.52 | $23,299.55 | 33.3% | 9,839.05 | $1,396.92 |
| US500 | 3.25 | 7,550.29 | 7,236.92 | -4.15% | -$1,018.45 | $23,519.99 | 33.7% | 6,802.94 | $1,410.43 |

Concentration: 3 positions, the largest 33.7% of the gross; by size that is 3.0 equal positions, and by risk it is **one**: four equity indices, all long: one risk factor held four times.

### Against a benchmark

| | Since the start | What it is |
|---|---|---|
| The desk | -$5,537.58 | realized plus unrealized, after costs |
| Cash | +$318.49 | 3.875% a year on the starting balance for 15.00 days |
| The same indices bought and held | n/a | after an exit, holding on needs the index's later closes: not in these files |
| The same positions at one times the account | n/a | not computable from these files |

### Month by month, against the $4,000 target (a target, never a quota)

| Month | Days | Net | Of $4,000 |
|---|---|---|---|
| 2026-11 | 12 | -$5,537.58 | -138.4% |

## 2. RADAR-1: the funding radar's paper ledger

**Reconciled: 24 of 24 checks hold.** Each compares two routes to the same figure.

Marks from 2026-10-07 20:00 UTC to 2026-11-24 23:00 UTC (48.12 days). Paper only: no order is ever sent. Its preregistered single look is on 2026-12-06 and is read as registered, whatever this audit says.

Capital: ten slots of 2N: 20N. The radar has no cash account; N is not a dollar amount. P&L is in basis points (bp) of one leg's notional; 2,000 bp summed over positions is 1% of the book.

| | In bp of N | In % of the book | On a $100,000 book (illustration) |
|---|---|---|---|
| **Realized** (closed positions, after every fill) | -5,382.7 | -2.6913% | -$2,691.33 |
| **Unrealized** (open positions at their marks, entry fills paid) | -15.3 | -0.0076% | -$7.63 |
| The book if every open position were closed now | -5,432.0 | -2.7160% | -$2,715.96 |

| | |
|---|---|
| Closed positions | 268: 47 won, 221 lost |
| Win rate | 17.5% |
| Average win / average loss | 74.1 bp / -40.1 bp |
| Profit factor | 0.39 |
| Mean net a position | -20.1 bp (t -4.68) |
| Open positions | 2 of 10 slots; on average 25.3% of the capital was deployed |
| Book P&L | -2.6990% |
| Book excess over cash (3.875%/yr on the capital in use) | -2.8449% |
| Annualised excess on the capital deployed | -85.5%/yr |
| The same with costs x1.5 / x2 | -155.2% / -224.8% |
| Maximum drawdown of the book (hourly marks) | 2.6990% |
| t of the daily excess | -4.29 |
| Best coin, and the book's excess without it | INIT: -3.2992% |

### Where it came from

Funding received **3,740 bp**, price moves between the legs **79 bp**, fills **-9,201 bp**: net **-5,383 bp**. A position earned 14.2 bp before costs and paid 34.3 bp: the costs are 2.41 times the gross. Half the positions were closed within 4.0 hours.

| Held for | Positions | Won | Sum | Mean | t | Funding | Price | Costs |
|---|---|---|---|---|---|---|---|---|
| 1 hour or less | 85 | 5 | -2,855 bp | -33.6 bp | -6.36 | 47 | 28 | 2,930 |
| 1 to 6 hours | 93 | 16 | -2,780 bp | -29.9 bp | -4.45 | 888 | -495 | 3,173 |
| 6 to 24 hours | 60 | 15 | -306 bp | -5.1 bp | -0.56 | 1,408 | 354 | 2,068 |
| over 3 days | 5 | 2 | -38 bp | -7.7 bp | -0.71 | 168 | -31 | 176 |
| 1 to 3 days | 25 | 9 | 597 bp | 23.9 bp | 0.98 | 1,229 | 222 | 854 |

| Closed for | Positions | Won | Sum | Mean | t | Funding | Price | Costs |
|---|---|---|---|---|---|---|---|---|
| spread_reversed | 140 | 26 | -2,893 bp | -20.7 bp | -4.13 | 2,031 | -123 | 4,801 |
| spread_decayed | 80 | 3 | -2,853 bp | -35.7 bp | -15.96 | 132 | -223 | 2,763 |
| rebalance | 48 | 18 | 364 bp | 7.6 bp | 0.42 | 1,576 | 425 | 1,637 |

| Known at the entry: entry spread | Positions | Won | Sum | Mean | t | Funding | Price | Costs |
|---|---|---|---|---|---|---|---|---|
| under 50%/yr | 159 | 21 | -4,410 bp | -27.7 bp | -8.33 | 1,173 | -110 | 5,473 |
| 50 to 100%/yr | 68 | 15 | -775 bp | -11.4 bp | -1.07 | 1,098 | 442 | 2,315 |
| 100%/yr or more | 41 | 11 | -198 bp | -4.8 bp | -0.28 | 1,469 | -254 | 1,413 |

| Known at the entry: venue pair | Positions | Won | Sum | Mean | t | Funding | Price | Costs |
|---|---|---|---|---|---|---|---|---|
| short mexc / long gate | 208 | 36 | -4,687 bp | -22.5 bp | -5.16 | 2,257 | 128 | 7,072 |
| short gate / long mexc | 28 | 4 | -525 bp | -18.7 bp | -0.83 | 786 | -359 | 952 |
| short hyperliquid / long gate | 8 | 1 | -215 bp | -26.9 bp | -2.73 | 56 | 41 | 312 |
| short mexc / long hyperliquid | 2 | 0 | -42 bp | -21.1 bp | -2.36 | 21 | 3 | 66 |
| short dydx / long gate | 1 | 0 | -23 bp | -22.9 bp | n/a | 13 | 4 | 40 |
| short hyperliquid / long mexc | 10 | 2 | -3 bp | -0.3 bp | -0.02 | 333 | -6 | 330 |
| short gate / long hyperliquid | 11 | 4 | 113 bp | 10.3 bp | 0.46 | 273 | 269 | 429 |

| Known at the entry: time since the coin's previous position | Positions | Won | Sum | Mean | t | Funding | Price | Costs |
|---|---|---|---|---|---|---|---|---|
| within 6 hours of the coin's previous exit | 173 | 30 | -3,000 bp | -17.3 bp | -2.72 | 2,710 | 212 | 5,923 |
| a first entry, or later | 95 | 17 | -2,382 bp | -25.1 bp | -7.45 | 1,029 | -133 | 3,278 |

51 coins were traded and 45 of them lost. The five worst and the five best:

| Coin | Positions | Won | Sum | Mean | t | Funding | Price | Costs |
|---|---|---|---|---|---|---|---|---|
| AKE | 26 | 3 | -1,005 bp | -38.6 bp | -3.57 | 262 | -382 | 884 |
| BTW | 20 | 3 | -821 bp | -41.0 bp | -7.06 | 61 | -202 | 680 |
| IRYS | 18 | 3 | -620 bp | -34.5 bp | -4.50 | 212 | -220 | 612 |
| SOXL | 19 | 1 | -618 bp | -32.5 bp | -9.64 | 122 | -94 | 646 |
| AGT | 20 | 2 | -416 bp | -20.8 bp | -1.10 | 48 | 216 | 680 |
| INIT | 7 | 5 | 917 bp | 131.0 bp | 1.67 | 1,009 | 165 | 257 |
| IOST | 4 | 3 | 450 bp | 112.4 bp | 0.98 | 358 | 227 | 136 |
| BULLA | 8 | 4 | 267 bp | 33.4 bp | 0.55 | 276 | 264 | 272 |
| ACE | 2 | 1 | 127 bp | 63.7 bp | 0.66 | 170 | 23 | 66 |
| RSR | 3 | 3 | 58 bp | 19.4 bp | 1.47 | 67 | 98 | 107 |

Concentration: the most traded coin (AKE) is 9.6% of the positions; by count the book is 22.5 equal coins. Venue pairs: short mexc / long gate 209, short gate / long mexc 29, short gate / long hyperliquid 11, short hyperliquid / long mexc 10, short hyperliquid / long gate 8, short mexc / long hyperliquid 2, short dydx / long gate 1.

| Open now | Short / long | Opened | Entry spread | Funding | Price | Fills paid | Net at the marks | Net if closed now |
|---|---|---|---|---|---|---|---|---|
| EVAA | mexc / gate | 2026-11-24 04:00 UTC | 43.5%/yr | 4.3 | 14.4 | 17.0 | 1.7 bp | -15.3 bp |
| SOXS | gate / mexc | 2026-11-24 23:00 UTC | 30.8%/yr | 0.0 | 0.0 | 17.0 | -17.0 bp | -34.0 bp |

## 3. The weakness, the hypothesis and the experiment

**Largest weakness** (a class known when a position is opened, measured against the rest of the book): entry spread, *under 50%/yr*: 159 positions, mean -27.7 bp (t -8.33) against -8.9 bp for the rest (t of the difference -1.91); 2,991 bp lost beyond what the rest would have.

**Hypothesis.** Positions opened on a trailing spread under 50%/yr do not earn their round trip. Asking twice the spread at the entry removes them; whether the entries that remain earn more than cash is what the replay measures.

**Tested by** the declared variant `thick-entry` in the replay below.

### The replay: the radar's frozen rules and the declared variants on the same stored quotes

Stored hours in hand: 477 (2026-11-04 23:00 UTC to 2026-11-24 23:00 UTC); days archived: 20; added this cycle: none.

Fidelity: the replay of the original rules reproduces 89 of the radar's 89 real positions opened in these hours to the hundredth of a basis point (89 matched by entry). Differences: 0 only in the real ledger, 2 only in the replay; 2 of them on a coin the radar already held when the replay began (AKE, IDOL, SOL, SOXL, UAI). The replay is taken as faithful.

Earlier part 2026-11-07 22:00 UTC to 2026-11-16 00:00 UTC; later part to 2026-11-25 00:00 UTC. Excess over cash in % of the book.

| Variant | What changes | Earlier: excess | positions | Later: excess | positions | closed | t (daily) | Later, less the original | its t |
|---|---|---|---|---|---|---|---|---|---|
| `original` | nothing: the registered rules | 0.1602% | 36 | -0.7458% | 55 | 53 | -3.16 | 0.0000% | n/a |
| `same-window` | trailing_entry_h=24 | -0.0035% | 53 | -0.7377% | 53 | 52 | -4.39 | 0.0080% | 0.03 |
| `thick-entry` | entry_trailing_apr=0.5, entry_now_apr=0.3 | 0.2752% | 25 | -0.1970% | 18 | 18 | -2.16 | 0.5488% | 2.84 |
| `patient-exit` | exit_now_apr=-1.0 | 0.3578% | 30 | -0.6570% | 52 | 49 | -3.18 | 0.0888% | 1.50 |
| `all-three` | trailing_entry_h=24, entry_trailing_apr=0.5, entry_now_apr=0.3, exit_now_apr=-1.0 | 0.3829% | 27 | -0.1419% | 24 | 23 | -2.00 | 0.6039% | 3.23 |

Candidate, chosen on the earlier part only: `all-three` (4 variants compared). **INCONCLUSIVE**: the later part holds 9 days and 23 closed positions: 30 and 30 are needed before anything is judged.

Gates on the later part: enough days no, enough positions no, excess over cash no, beats the original yes, costs x1.5 no, without best coin no.

A variant is proposed as a registered challenger only when every gate holds. A proposal is a request for a preregistered forward test, never a replacement of the original.

### Registered challengers, judged forward

None is registered. RADX-1, the diagnosis these variants came from, failed as registered (one of its two parts did not hold on the later positions), and by its own rule no challenger follows from it. One is registered only after a variant passes the gates above.


## 4. What is not claimed

- An unrealized gain is a valuation at the last close. It is not profit until the trade is closed.
- A variant that loses less than the original has not been shown to earn anything.
- No figure here is a backtest, and none is added to a research result.
