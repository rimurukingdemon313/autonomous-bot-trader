## 5. The director's reading (2026-11-15)

Written by hand by the research director (`claude-fable-5-2`, through the scheduled session of
`docs/RESEARCH_INSTITUTION.md`), from the tables above and from `research/QUEUE.md`. Everything above this line is
computed; everything below is a reading of it, and is dated so that it can be wrong on the record.

### The patterns the failures share

1. **On the perpetuals the information is there before costs and gone after them.** Before costs 68% of the rules are
   positive on rows they were not fitted on and their t are centred at +0.43. After 7 to 13 basis points a fill they
   are centred at -0.22. Fifty-two of the 83 rules that lost there lost only after costs. A rule held under two rows
   earns 5.0 bp a row before costs and loses 1.2 after.
2. **On the funds and on energy there is nothing before costs either.** The funds' check-row t before costs are
   centred at +0.14 with a spread of 0.90, which is what noise gives; energy's are centred below zero.
3. **Strength where a rule was found predicts nothing on the funds** (correlation -0.03 over 259 rules; the strongest
   quarter on the fit rows was the worst afterwards) **and a little on the perpetuals** (+0.24). The lab's methods
   find structure on the funds' fit rows that is not in the funds.
4. **The judged edges fail every gate at once.** Of 138 rejected, 89 of the 120 with a recorded mean lost after
   costs, and the median t is -1.30. Only 7 failed a single gate. An edge that is not there fails its t, its random
   baseline, its halves and its instruments together: the gates are not picking at a real edge's weak side.
5. **The near misses are published effects that were there and decayed, or that costs took half of.** DAY-1's
   pullback earned t 3.02 to 2005 and 0.49 after. The Treasury month-end effect is t 4.07 before a retail CFD's costs
   and 2.24 after. Neither can reach a bar above 3 on the data that exist.

### Hidden conditions: looked for, and what was found

| Looked for | Found |
|---|---|
| A holding period at which the perpetuals' rules survive costs | Only at 15 rows or more is the median positive after costs (+1.28 bp a row, 63% positive), on 19 rules with a mean t of +0.07. Slow rules are not killed by costs and carry almost no signal. Nineteen rules decide nothing |
| A family that works on one panel | On the perpetuals four families have a positive mean check t (evolved rules +0.52, anomalies +0.41, regimes +0.26, pooled time-series +0.21). None is told from zero: their rules share instruments and days. On the funds and on energy no family is positive |
| Rules that only costs stopped | 52 on the perpetuals, 56 on the funds, 10 on energy. On the funds this is not hidden information: before costs the population is noise, so a rule that was positive before costs was the upper half of noise |
| A real effect spread thinly over the weak positives | No. Chosen on the check rows and shrunk for it, their aggregate is expected at t 0.63 on new rows on the perpetuals (under one chance in a hundred to reach 3.0) and below zero on the funds and on energy |

### How the failed families relate

- **Crypto.** Funding carry (CR-1 to CR-5): the premium was competed down to the cost of capital within a year or
  two of being visible. Momentum across coins (XSM-1) and within a coin (XTS-1): positive to 2021, negative from
  2022. On the perpetuals the lab's own rules were recognised as these by what they do 30 times: 18 in the scan, and
  12 in the directed test before any test was spent on them.
  The live radar (RADAR-1) is the same carry measured where it is new, and its paper ledger says the round trip
  costs more than the carry lasts (`docs/PERFORMANCE_ENGINEERING.md`).
- **Calendar and flow effects** (month-end, the turn of the month, auctions, pre-FOMC, holidays, sessions: MEH-1,
  TME-1, RBL-1, TSY-1, FOMC-1A, PHD-1 and FXS-1 among them): one answer. Each is small, most are visible before
  costs, and none clears a bar that counts the others.
- **Trend.** The one validated result (TRND-1) is market exposure with a smaller drawdown, not an edge over the
  market, and says so.
- **FX majors.** 38 hypotheses and 176 tests at a bar of 3.63, and every month from 2017 sealed. Nothing more is
  asked of that data.

### What has never been tested, and why

| Direction | Why not yet | What it would need |
|---|---|---|
| **Costs charged on net trades.** The lab charges every part of a book its own costs. A book of many rules on the same instruments pays for trades that would cancel | Examined on 2026-11-15 from the recorded figures and **set aside** (below) | New code in the lab, and a reason to expect the rules' daily P&L to be nearly independent |
| Maker fills instead of taker fills | Cannot be verified on daily bars or on a paper ledger: a maker fill is not guaranteed | A live recorder of the book at the venues. Not a backtest |
| Hours inside the day on the perpetuals | Each new panel is charged 600 tests, and no mechanism has been proposed that the daily panel does not already hold | A hypothesis with a mechanism first, as a directed test: a few rules, not a scan |
| Options and volatility surfaces | No free data of the quality a test needs | The owner's decision on paid data. Not asked for |
| Single stocks across the section | The published anomalies are documented as halved after publication and costs (Chen & Velikov) | A reason to expect otherwise |

### What deserves a new experiment

| Class | Rules | Decision |
|---|---|---|
| Lost on the check rows | 235 | None. For the 52 perpetual rules that lost only after costs, see the one experiment below |
| Overfit | 159 | None |
| Positive, not told from noise | 148 | Not one by one (a median of 45 to 226 more years of rows would be needed), and **not as a chosen aggregate** (withdrawn, `research/director/log.jsonl`) |
| Too few rows | 58 | They wait for rows. Nothing is done to them |
| Duplicates, closed families | 60 | None: they are already answered |
| The one direction that was left | | The netted population book on the perpetuals: **set aside** after its arithmetic (below) |

### The last direction, and why it is set aside

On the perpetuals the population of rules earns before costs and loses after them, and the lab charges every rule
its own fills. Held as one book that trades only its net position in each coin, the 262 rules that are not closed
families would pay less. From the recorded check-row figures, a day and per unit of capital, the capital shared by
family and then by rule: **+3.83 bp before costs, 4.37 bp of costs, -0.53 bp after**.

What decides it is not the cost. It is how the rules' daily P&L move together:

| Average correlation between the rules | The book's t on the check rows before any cost | With costs halved | With costs divided by three |
|---|---|---|---|
| 0 (independent) | 6.0 | 2.6 | 3.8 |
| 0.02 | 3.0 | 1.3 | 1.9 |
| 0.05 | 2.0 | 0.9 | 1.3 |
| 0.10 | 1.5 | 0.6 | 0.9 |

These are 262 rules on 55 coins that rise and fall together. At a correlation of 0.05 the book stands near t 1.3
with its costs divided by three, and about the same on the unread rows, against a bar of 3.0. It would reach the bar
only if the rules were independent, and then it would reach it before costs too. My first estimate of its chance (5
to 10 in a hundred, written on 2026-11-14) was too high: it is 1 to 5. The lab asks for three in a hundred before it
spends even a place that costs the bar nothing, and this would also need a new kind of book in the lab's evaluator.
It is recorded in `research/director/log.jsonl` so that it is not rediscovered as an idea.

**So, as of 2026-11-15, no experiment on the data in hand is justified.** The panels that can be had for nothing
have been searched by 88 registered hypotheses and 660 rules, and the one validated result is market exposure with a
smaller drawdown. What could change this is new information, not another pass over the same bars: the two forward
tests that are running (RADAR-1 on 2026-12-06, TRND-F in 2029), a recorder of what cannot be read off daily bars, or
data the owner decides to buy. An empty queue with its reasons is the honest state of this record.
