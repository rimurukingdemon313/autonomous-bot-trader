# What the research record says when it is read together

**RESEARCH ONLY · NOTHING HERE IS A PROFIT CLAIM.** Written by `scripts/research_meta.py` from the committed record alone: the registry, the edge registry and the discovery lab's ledger of classed rules. No market data is read, so nothing is looked at that was not already looked at, and no test is charged. It describes the record; it validates nothing.

Generated 2026-11-22 16:49 UTC · meta-1.0.0

## 1. What was read

- 97 registered hypotheses with 1,924 counted tests; 87 verdicts: 74 FAILED, 10 PENDING, 10 PASSED, 2 ABANDONED, 1 INCONCLUSIVE.
- 163 judged trading edges: 153 REJECTED, 5 UNCERTAIN, 4 PROMISING, 1 VALIDATED.
- 660 rules found in data by the discovery lab and classed, each kept with its reason: 235 NEGATIVE_EXPECTANCY, 159 OVERFIT, 148 INSUFFICIENT_POWER, 58 INSUFFICIENT_DATA, 42 DUPLICATE, 18 REPEATS_CLOSED_FAMILY.

## 2. The registered hypotheses, by the data they used

| Data | Hypotheses | Counted tests | Failed | Passed | Pending |
|---|---|---|---|---|---|
| `crypto-perp-daily` | 2 | 614 | 2 | 0 | 0 |
| `us-etf-broad-daily` | 2 | 612 | 2 | 0 | 0 |
| `energy-futures-eia` | 2 | 401 | 2 | 0 | 0 |
| `fx-majors` | 38 | 176 | 30 | 1 | 6 |
| `index-cfd-intraday` | 7 | 32 | 6 | 0 | 0 |
| `multi-asset-etf` | 5 | 12 | 3 | 1 | 1 |
| `crypto-binance-usdtm` | 4 | 11 | 3 | 1 | 0 |
| `multi-asset-long` | 4 | 10 | 2 | 1 | 1 |
| `crypto-xvenue-hl-binance` | 4 | 8 | 2 | 2 | 0 |
| `crypto-binance-spot` | 4 | 7 | 3 | 0 | 0 |
| `us-equity-etf` | 5 | 6 | 5 | 0 | 0 |
| `crypto-binance-usdtm-all` | 1 | 5 | 1 | 0 | 0 |
| `crypto-perp-funding-settlements` | 1 | 4 | 1 | 0 | 0 |
| `equity-index-forward` | 1 | 3 | 0 | 0 | 1 |
| `crypto-perp-live-xvenue` | 2 | 3 | 1 | 0 | 1 |
| `equity-index-monthly` | 3 | 3 | 0 | 2 | 1 |
| `crypto-spot-crowded-shorts` | 1 | 3 | 1 | 0 | 0 |
| `crypto-spot-high-funding` | 1 | 3 | 1 | 0 | 0 |
| `stablecoin-pairs-weekend` | 2 | 3 | 1 | 1 | 0 |
| `equity-index-b` | 2 | 2 | 0 | 1 | 1 |
| `us-vol-etp` | 1 | 2 | 1 | 0 | 0 |
| `us-treasury-daily` | 2 | 2 | 2 | 0 | 0 |
| `crypto-spot-liquidation-falls` | 1 | 2 | 1 | 0 | 0 |
| `crypto-spot-spot-led-rallies` | 1 | 2 | 1 | 0 | 0 |
| `crypto-spot-korean-premium` | 1 | 2 | 1 | 0 | 0 |
| `metals-futures-daily` | 1 | 1 | 1 | 0 | 0 |
| `em-fx-daily` | 1 | 1 | 1 | 0 | 0 |
| `equity-index-daily` | 1 | 1 | 1 | 0 | 0 |
| `crypto-perp-new-listings` | 1 | 1 | 1 | 0 | 0 |

A PASSED line is a stage, not an edge: RV-1, DIV-2, DIV-2-H, RC-EQ2-H, CR-1, CR-4, CR-5, TRND-1, TRND-1-H, SCX-1. The edge registry below says which of them is a validated edge: TRND-1.

Pending: archive-smc-h1, archive-smc-h2, archive-trend-3, archive-reversion, archive-smc-utc-rerun, archive-edge-program-8, TOM-D, TOM-F, RADAR-1, TRND-F.

## 3. Why the judged edges failed

Of 153 rejected edges, 135 have a recorded mean after costs and 101 of those are negative. 140 have a t-statistic: its median is -1.33, and 8 reached 2. 8 failed a single gate, 5 of them the bar itself.

| Gate failed | Edges |
|---|---|
| t_day | 52 |
| profit_factor | 51 |
| symbols_positive | 51 |
| t | 50 |
| beats_random | 46 |
| years | 46 |
| significance | 45 |
| outliers | 45 |
| net_r | 44 |
| leave_one_out | 44 |
| delay_stress | 40 |
| instruments | 40 |

The gates fail together: an edge that is not there fails its t, its random baseline, its halves and its instruments at once. The exceptions are the near misses, which failed on the bar alone:

| Near miss | t | Bar |
|---|---|---|
| DAY-1 | in its artifact | 3.39 |
| FXT-1 | 2.71 | 3.63 |
| RCEQ-E1-TOM | 2.24 | 3.00 |
| TME-1 | in its artifact | 3.08 |

## 4. The rules found in data

### Perpetuals (55 Binance contracts by day)

280 rules: 83 NEGATIVE_EXPECTANCY, 72 INSUFFICIENT_POWER, 60 OVERFIT, 28 INSUFFICIENT_DATA, 19 DUPLICATE, 18 REPEATS_CLOSED_FAMILY.

**Does a rule's strength where it was found carry to the rows after?** Over 252 rules the correlation between the fit-row t and the check-row t is **0.241** (by rank 0.160; standard error 0.063).

| By strength on the fit rows | Rules | Fit t | Mean check t | Positive after costs |
|---|---|---|---|---|
| weakest quarter | 64 | -2.14 to 1.68 | -0.49 | 33% |
| second | 63 | 1.69 to 2.28 | -0.09 | 56% |
| third | 63 | 2.30 to 2.86 | -0.32 | 38% |
| strongest quarter | 62 | 2.90 to 9.82 | 0.05 | 58% |

**Before and after costs.** Before costs the check-row t are centred at 0.43 (spread 1.00) and 68% are positive. After costs: centred at -0.22 (spread 1.19), 46% positive. 52 of the 83 rules that lost did so only after costs.

| Held for | Rules | Median before costs | Median after costs | Mean check t | Positive after costs |
|---|---|---|---|---|---|
| under 2 rows | 104 | 5.01 bp a row | -1.24 bp a row | -0.39 | 42% |
| 2 to 5 rows | 78 | 3.19 bp a row | -0.85 bp a row | -0.09 | 47% |
| 5 to 15 rows | 51 | 1.08 bp a row | -0.27 bp a row | -0.15 | 45% |
| 15 rows or more | 19 | 1.91 bp a row | 1.28 bp a row | 0.07 | 63% |

| Family | Rules | Mean check t | Positive after costs | Positive before costs only | Overfit |
|---|---|---|---|---|---|
| anomaly | 7 | 0.41 | 3 | 1 | 0 |
| combination | 33 | -0.18 | 15 | 6 | 14 |
| cross-asset lead-lag | 24 | -0.10 | 12 | 5 | 1 |
| cross-sectional | 38 | -1.21 | 10 | 16 | 4 |
| evolved rule | 18 | 0.52 | 13 | 1 | 5 |
| information (non-linear) | 47 | -0.14 | 20 | 11 | 18 |
| ordinal pattern | 24 | -0.74 | 8 | 6 | 7 |
| own-lag | 8 | 0.22 | 4 | 4 | 0 |
| pooled book | 6 | -0.14 | 4 | 2 | 2 |
| pooled time-series | 24 | 0.21 | 14 | 3 | 2 |
| regime | 23 | 0.26 | 13 | 1 | 7 |

**The 72 weak positives** (positive on the check rows, not told from noise; 11 families; mean check t 0.80, best 2.76). They were chosen on the check rows from a population centred at -0.22. A t-statistic's own sampling spread is about one, so of a rule's distance from the centre about 30% is expected to survive: a member's expected t on new rows is **0.09**. Held together with the capital shared by family, they show t 5.78 on the rows they were chosen on (if uncorrelated) and an expected **0.63** on new rows: a chance of about 0.9% to reach 3.0. By their own plans 1 of 72 could be told from noise with one more year of rows and 4 with three (median 45.4 years).

Recognised by what they do as families already judged and closed: CR-3 11, XTS-1 6, TRND-1 1.

### Funds (31 US-listed funds by day)

278 rules: 109 NEGATIVE_EXPECTANCY, 78 OVERFIT, 51 INSUFFICIENT_POWER, 21 DUPLICATE, 19 INSUFFICIENT_DATA.

**Does a rule's strength where it was found carry to the rows after?** Over 259 rules the correlation between the fit-row t and the check-row t is **-0.029** (by rank -0.052; standard error 0.062).

| By strength on the fit rows | Rules | Fit t | Mean check t | Positive after costs |
|---|---|---|---|---|
| weakest quarter | 65 | -4.94 to 1.25 | -0.53 | 31% |
| second | 65 | 1.26 to 2.20 | -0.55 | 31% |
| third | 65 | 2.21 to 3.34 | -0.31 | 46% |
| strongest quarter | 64 | 3.37 to 7.98 | -0.88 | 20% |

**Before and after costs.** Before costs the check-row t are centred at 0.14 (spread 0.90) and 54% are positive. After costs: centred at -0.57 (spread 1.08), 32% positive. 56 of the 109 rules that lost did so only after costs.

| Held for | Rules | Median before costs | Median after costs | Mean check t | Positive after costs |
|---|---|---|---|---|---|
| under 2 rows | 121 | -0.01 bp a row | -1.27 bp a row | -0.92 | 23% |
| 2 to 5 rows | 84 | 0.47 bp a row | -0.48 bp a row | -0.38 | 36% |
| 5 to 15 rows | 42 | 0.39 bp a row | 0.06 bp a row | 0.08 | 55% |
| 15 rows or more | 12 | -0.59 bp a row | -0.74 bp a row | -0.55 | 17% |

| Family | Rules | Mean check t | Positive after costs | Positive before costs only | Overfit |
|---|---|---|---|---|---|
| anomaly | 5 | 0.03 | 3 | 0 | 2 |
| combination | 36 | -0.65 | 11 | 9 | 21 |
| cross-asset lead-lag | 24 | -0.57 | 7 | 4 | 2 |
| cross-sectional | 36 | -0.70 | 11 | 15 | 0 |
| evolved rule | 24 | -0.18 | 8 | 4 | 12 |
| information (non-linear) | 48 | -0.64 | 17 | 8 | 18 |
| ordinal pattern | 24 | -1.02 | 4 | 7 | 11 |
| own-lag | 8 | -1.40 | 0 | 0 | 7 |
| pooled book | 6 | -1.20 | 2 | 1 | 4 |
| pooled time-series | 24 | -0.19 | 10 | 6 | 1 |
| regime | 24 | -0.09 | 10 | 2 | 0 |

**The 51 weak positives** (positive on the check rows, not told from noise; 9 families; mean check t 0.67, best 1.70). They were chosen on the check rows from a population centred at -0.57. A t-statistic's own sampling spread is about one, so of a rule's distance from the centre about 14% is expected to survive: a member's expected t on new rows is **-0.40**. Held together with the capital shared by family, they show t 3.80 on the rows they were chosen on (if uncorrelated) and an expected **-2.26** on new rows: a chance of about 0.0% to reach 3.0. By their own plans 0 of 51 could be told from noise with one more year of rows and 0 with three (median 106.0 years).

### Energy (WTI and natural gas by day)

102 rules: 43 NEGATIVE_EXPECTANCY, 25 INSUFFICIENT_POWER, 21 OVERFIT, 11 INSUFFICIENT_DATA, 2 DUPLICATE.

**Does a rule's strength where it was found carry to the rows after?** Over 91 rules the correlation between the fit-row t and the check-row t is **0.031** (by rank 0.103; standard error 0.107).

| By strength on the fit rows | Rules | Fit t | Mean check t | Positive after costs |
|---|---|---|---|---|
| weakest quarter | 23 | -2.74 to 0.64 | -0.50 | 30% |
| second | 23 | 0.95 to 1.65 | -1.06 | 26% |
| third | 23 | 1.66 to 2.30 | -0.51 | 35% |
| strongest quarter | 22 | 2.33 to 4.63 | -0.42 | 41% |

**Before and after costs.** Before costs the check-row t are centred at -0.13 (spread 1.04) and 44% are positive. After costs: centred at -0.63 (spread 1.09), 33% positive. 10 of the 43 rules that lost did so only after costs.

Holding times were not recorded for this panel's rules (its scan ran under the lab's first version).

| Family | Rules | Mean check t | Positive after costs | Positive before costs only | Overfit |
|---|---|---|---|---|---|
| anomaly | 6 | -0.25 | 3 | 0 | 0 |
| combination | 16 | -1.17 | 2 | 1 | 6 |
| cross-asset lead-lag | 10 | -0.36 | 4 | 1 | 0 |
| evolved rule | 24 | -0.06 | 11 | 3 | 9 |
| information (non-linear) | 11 | -0.50 | 4 | 2 | 2 |
| ordinal pattern | 5 | -1.61 | 1 | 0 | 1 |
| own-lag | 8 | -0.64 | 2 | 2 | 0 |
| pooled book | 6 | -1.77 | 0 | 1 | 3 |
| regime | 5 | -0.49 | 3 | 0 | 0 |

**The 25 weak positives** (positive on the check rows, not told from noise; 8 families; mean check t 0.54, best 1.43). They were chosen on the check rows from a population centred at -0.63. A t-statistic's own sampling spread is about one, so of a rule's distance from the centre about 16% is expected to survive: a member's expected t on new rows is **-0.44**. Held together with the capital shared by family, they show t 1.94 on the rows they were chosen on (if uncorrelated) and an expected **-1.58** on new rows: a chance of about 0.0% to reach 3.0. By their own plans 0 of 25 could be told from noise with one more year of rows and 0 with three (median 226.0 years).

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
  New listings (NEWL-1, 2026-11-15) failed in a different way from the rest: the typical new perpetual did fall
  against seasoned ones (median +15.7% for the short, 71% of 812 events positive), but a short with no stop is
  exposed to squeezes on thin new floats: 29 events lost more than their notional, and one outweighed every gain.
  The mean was -0.1% at t -0.01 (`research/results/NEWL-1-verdict.md`).
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
