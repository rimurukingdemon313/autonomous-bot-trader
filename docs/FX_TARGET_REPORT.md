# $4,000 a month on $200,000 in Forex: is it credible?

## Answer: no. No Forex strategy found here can credibly target $4,000 a month net at acceptable risk.

**Completed 2026-11-09.**

| The target | $4,000 average monthly net profit on $200,000: 2% a month, 24% a year simple |
|---|---|
| The evidence | 176 FX tests (`docs/FX_MISSION_REPORT.md`), none validated |
| This analysis | `scripts/fx_target.py` → `research/results/FX-TARGET.json` |

**What the analysis is.** It takes the monthly net returns of the judged books and scales them to risk levels fixed
before looking: 5%, 10% and 20% a year of volatility (or 0.25%, 0.5% and 1% risk a trade), plus the one level at which
the historical average would have been exactly $4,000. The capital is a fixed $200,000, not compounded, as the target
is stated. It judges nothing, selects nothing and changes no verdict.

**How to read the bootstrap.** It is 10,000 paths of 60 months, built from 12-month blocks of the sample. It assumes
the sample's edge persists, and no candidate has shown that. **So every probability of reaching the target below is
an upper bound.**

## 1. The best validated strategy

**None exists.** No FX candidate here passed its preregistered gates.

The three below are the only ones that can be put in dollar terms:

| Candidate | What it is | Status |
|---|---|---|
| **FXT-1** | Monthly time-series momentum in GBP, JPY, CHF, CAD, AUD and NZD against the dollar, 1975-1989 (H.10), swap-free | FAILED on t alone: 2.71 against 3.6294 |
| **ID-2 best** | The best of ID-2's 18 M5 configurations (ridge S15 τ 0.05), walk-forward 2011-2013, picked after the fact | REJECTED: t 1.56 against 3.5524; its profit-factor and pair gates failed |
| **FXS-1** | The time-of-day effect, M5 bid/ask 2009-2016 | FAILED: net negative |

## 2-5. Monthly net profit, months above $4,000, worst months, drawdown

### FXT-1 (1975-1989): the only candidate whose whole period was positive

| Configuration | Risk | Mean month | Median month | Months profitable | Months ≥ $4,000 | Worst month | Max drawdown | Worst day |
|---|---|---|---|---|---|---|---|---|
| Conservative | 5% vol, gross 0.9x | **$583** | $192 | 53% | 11% | −$6,753 | 9.6% | −1.8% |
| Moderate | 10% vol, gross 1.8x | $1,167 | $384 | 53% | 28% | −$13,507 | 19.2% | −3.6% |
| Aggressive | 20% vol, gross 3.7x | $2,334 | $767 | 53% | 41% | −$27,014 | 38.4% | −7.3% |
| **At the target** | **34% vol, gross 6.3x** | **$4,000** | **$1,314** | 53% | 47% | **−$46,297** | **65.8%** | **−12.5%** |

**The distribution of months at the target level** (deciles, 10th to 90th): −$18,536, −$11,608, −$6,142, −$3,232,
**+$1,314** (median), +$7,901, +$11,707, +$19,861, +$29,070. The worst 12 months lost $90,028. Losing months: 85 of
180, the longest run 5.

**The bootstrap** (60-month paths; upper bounds):

| Configuration | P(drawdown ≥ 10%) | P(≥ 20%) | P(≥ 50%: ruin) | P(5-year average ≥ $4,000) | P(first year ≥ $4,000) | Median 5-year average month |
|---|---|---|---|---|---|---|
| Conservative | 8% | 0.03% | 0% | 0% | 0% | $557 |
| Moderate | 71% | 8% | 0% | 0% | 7% | $1,114 |
| Aggressive | 100% | 71% | 2% | 14% | 24% | $2,229 |
| **At the target** | **100%** | **99%** | **38%** | **47%** | 45% | $3,820 |

**If the edge halved** (published effects lose about half after publication), the target would need 8.3 times the
book's risk:

- the historical drawdown would be 222% of the capital;
- the chance of ruin within five years would be 98%.

### ID-2 best (2011-2013): the attractive backtest the brief warns about

| Configuration | Risk a trade | Mean month | Median | Months profitable | Months ≥ $4,000 | Worst month | Max drawdown |
|---|---|---|---|---|---|---|---|
| Conservative | 0.25% | $1,101 | $1,583 | 61% | 28% | −$7,309 | 3.6% |
| Moderate | 0.5% | $2,202 | $3,166 | 61% | 42% | −$14,617 | 7.3% |
| Aggressive | 1.0% | $4,405 | $6,331 | 61% | 56% | −$29,234 | 14.6% |
| At the target | 0.91% | $4,000 | $5,749 | 61% | 56% | −$26,548 | 13.3% |

**On paper it reaches the target at about 0.9% risk a trade. It is not credible:**

- **It was picked after the fact,** as the best of 18 configurations on the same months. If none had any edge, the
  best of 18 would still show a t of about 1.8 by luck. Its t is 1.56: what chance alone produces.
- **It failed its own gates** (profit factor, pairs). Its validation years (2014-2016) were never computed, so it has
  no independent out-of-sample test.
- **Its edge shrank inside the sample:** +0.068, +0.091, then +0.016 R a trade in 2011, 2012 and 2013.
- **Its bootstrap is unreliable.** It resamples only 36 months, so it mostly repeats the selected sample. Its "0%
  chance of a losing 5 years" is an artefact of that, not a measurement.

### FXS-1 (2009-2016): risk cannot fix a negative expectancy

| Configuration | Mean month | Months profitable | Max drawdown | P(ruin, 5 years) |
|---|---|---|---|---|
| 5% vol | −$746 | 41% | 47% | 3% |
| 10% vol | −$1,492 | 41% | 95% | 57% |
| 20% vol | −$2,983 | 41% | 190% | 93% |

**No level of risk reaches the target. More risk only loses faster.**

## 4 (continued). Out-of-sample worst months

- **FXT-1 has no fitted parameter**, so both halves of 1975-1989 are out of sample for the rule. Its modern years
  (2017 on) stay sealed, because it failed its judge.
  - **1983-1989, the validation half:** the mean month at the target level was $5,203, the worst −$38,016.
  - **1975-1982:** the mean was $2,947, the worst −$46,296.
  - **The conservative level:** 1983-1989 mean $759 (worst −$5,546); 1975-1982 mean $430 (worst −$6,754).
- **ID-2's months** were each predicted by a model fitted on earlier trades only. At 1% risk the worst month was
  −$29,234 (December 2013).

## 6. The risk and leverage the target requires

| | Per position | Book | Leverage | What it means |
|---|---|---|---|---|
| FXT-1 | 41% volatility target per currency | 34% a year | average gross 6.3x | A worst month of −23% of the capital; a worst day of −12.5%. A funded account's 5% daily and 10% total loss limits would both be breached (P = 100%) |
| ID-2 best | 0.91% of the capital at risk on each trade | — | about 40 trades a month, several open at once | Drawdown 13% on its own selected sample. A funded account's 10% limit would be breached on 100% of the bootstrap paths |

**The brief's rule applies here.** These are the risk levels needed to *force* the target onto a backtest, so none
is recommended. The highest risk consistent with preserving capital is the conservative level. There, the best
candidate's historical average is **about $580 a month**.

## 7. Years and regimes

**FXT-1 by year, conservative level (5% vol), in dollars on $200,000:**

| 1975 | 1976 | 1977 | 1978 | 1979 | 1980 | 1981 | 1982 | 1983 | 1984 | 1985 | 1986 | 1987 | 1988 | 1989 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| +8,276 | +2,461 | +28,335 | +18,510 | −5,094 | −3,236 | −9,043 | +1,064 | +9,053 | +14,351 | +12,064 | −571 | +17,946 | +4,478 | +6,436 |

- **When it won.** In the long dollar trends: the dollar's fall in 1977-1978, its rise in 1983-1985, its fall in
  1985-1987.
- **When it lost.** At the dollar's turns: 1979-1981, the deepest fall (August 1979 → December 1981), and 1986.
- **At the target level** every one of those numbers is 6.9 times larger. 1981 alone would have lost $61,990, 31% of
  the capital.
- **ID-2 by year (1% risk):** 2011 +$72,258, 2012 +$67,996, 2013 +$18,314. The last is the decay noted above.

## 8. A realistic paper-trading plan

The only honest next step is evidence on months that have not happened yet. Nothing in it touches production or
real money.

1. **FXT-F, preregistered before its first month.**
   - **The rule.** FXT-1 unchanged on the seven H.10 majors (EUR added, as FXT-1's holdout rule specifies), rebalanced
     at 17:00 New York on each month's first business day, filled at the next noon rate.
   - **Account and size.** A $200,000 paper account at the conservative level: 5% annual volatility, about 0.9x
     gross.
   - **Mechanics.** A monthly calculation on GitHub's runner, like FUNDED-P. It is not the execution engine, which
     refuses any rule not VALIDATED.
   - **Costs.** The declared 2 bp each way, replaced by the broker's measured spreads when they exist.
2. **What it may show, on 1975-1989's figures.** About $580 a month on average, $4,000 or more in about 1 month in 9,
   a worst month near −$6,800 and a drawdown near 10%. Those are the old years, not a forecast.
3. **A kill rule.** A 10% drawdown on the paper account (a funded account's maximum loss) ends it, recorded as a
   breach.
4. **One judgement at a fixed date** (36 months), with preregistered gates: mean > 0, mean > 0 at costs x2, t
   reported. At a Sharpe ratio of 0.7, three years give a t of about 1.2. It can reveal a large failure, but it cannot
   confirm a small edge, which would take many more years.
5. **In parallel: real costs.** The intraday information found (ID-2's selections, FXS-1's EURUSD European-hours leg)
   is about as large as the assumed costs. Record the funded account's real spreads and commissions for months.
   Only then can a cost-measured successor be preregistered, on data nobody has read.

## 9. Conclusion: is $4,000 a month statistically credible?

**No.**

- **No validated strategy.** Not one Forex strategy here has passed its preregistered gates (176 tests).
- **The best candidate falls far short.** The strongest, FXT-1, would have averaged about $580 a month at a
  capital-preserving risk, if its 1975-1989 edge had persisted. The archive's trend rules failed on 2017-2022, so even
  that is not assured.
- **The target needs ruinous risk.** On that candidate it takes 6.3x leverage. Even on the historical sample that
  means:
  - a 66% drawdown and a $46,000 worst month;
  - a 38% chance of a 50% loss within five years;
  - a certain breach of a funded account's 10% limit;
  - with half the edge, ruin is close to certain.
- **The one backtest that reaches it is not credible.** ID-2's best was picked after the fact, its t of 1.56 is what
  luck produces, and it has no independent test.

**What the evidence supports is a modest, unvalidated expectation.** A few hundred dollars a month at most, at
conservative risk, with a wide range around it. Reaching $4,000 a month would take either a genuinely stronger edge,
which nothing here has found, or more capital at the same modest risk. On FXT-1's historical figure, that would be
roughly $1.4 million at the conservative level, still unvalidated.

## Correction to section 8 (2026-11-09, before anything was registered): FXT-F is not run

**FXT-F cannot be preregistered under the project's own rules.**

- **The seal.** It covers fx-majors from 2017-01-01 with no end (`research/holdout.json`). The registry treats any
  later trial that touches it as its one final test, and that test opens only for a candidate that passed. FXT-1
  failed its judge.
- **The warm-up reads sealed history.** FXT-1's rule needs 12 months of rates and 60 days of volatility before its
  first decision. A December 2026 start would read 2025-2026 rates, which are sealed history.
- **The clean form is too slow.** A forward-only universe reading nothing before registration (TOM-F's convention)
  would first trade in about 2028 and be judged in about 2031, at an expected t near 1.2. That is not a useful
  paper plan.

**What remains of the plan:**

- **Measured costs.** Recording the account's real spreads and commissions is measurement, not a test, and needs no
  seal. A cost-measured successor to ID-2 could then be judged on ID-2's own validation years (2014-2016, never
  computed for it). It would open the seal only if it passed, as ID-1's procedure registers.
- **No FX strategy is fit for paper trading now.** The system's paper strategy remains TRND-1 on the four index CFDs
  (`docs/TREND_DESK.md`).

**The FX data budget is spent.** Under these rules:

- the pre-2017 years carry 176 tests (bar 3.63);
- every month from 2017 on, past or future, is reserved for a single final test of a passer.

Changing the seal, for example ending it at a date so that later months can carry forward tests, would be a change to
the research rules. It is left as it is.

**One dependency, checked in the code.**

- **Nothing can record real costs yet.** Measured costs need a connection to the account's broker. None exists:
  `aitrader/broker/` holds only the paper broker, and no spread recorder remains in the code.
- **Until then, no FX step can add evidence** under these rules.
- **Research continues** on the other instruments a funded account quotes (`research/QUEUE.md`).
