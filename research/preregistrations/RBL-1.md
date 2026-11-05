# RBL-1: the month-end rebalancing reversal in the S&P 500 (preregistration)

**Written, frozen and registered on 2026-11-05, before any RBL-1 price was fetched.**

The owner, 2026-11-05: "never stop; keep going until something comes out".

| | |
|---|---|
| Frozen spec | `research/specs/RBL-1.json` |
| Spec sha256 | `7cede37add71e267ad1de1b8868f44d7fef617a715e41e58a7ce3621c9f7cf3a` |
| Code | `scripts/rbl1.py` and `scripts/phd1.py` (its NYSE calendar), sha256 `c3fc2cd8ad82f4870961904343f93070dd4dbee8d86ebf1ba1d6874de0d81696`. Every command refuses to run if either hash changes |
| Run | `.github/workflows/rbl1-run.yml` on GitHub's runner, which can reach Yahoo (this environment cannot). It runs `fetch`, then `judge`, then `holdout` only if `judge` PASSED. It also prints the result and the registry line to its log, so a refused push cannot lose them |
| Threshold | t ≥ **3.180**. That is the Bonferroni value for 33 earlier tests plus this 1, and never below 3.0. The 33 are every test on S&P 500, US equity or US Treasury data: multi-asset-etf (12), multi-asset-long (10), equity-index-b (2), us-vol-etp (2), us-equity-etf (5) and us-treasury-daily (2). A trial on two of them is counted on each |

## Why this question

- **The finding.** Harvey, Mazzoleni & Melone (2025, "The Unintended Consequences of Rebalancing") found that funds
  holding stocks and bonds at fixed weights trade predictably. When stocks have beaten bonds, "funds sell stocks and
  buy bonds, leading to a decrease in equity returns of 17 basis points over the next day". The opposite happens when
  bonds have beaten stocks.
- **The mechanism.** Pension funds, balanced funds and target-date funds rebalance to fixed weights, many of them at
  month-end. Mature pension funds also sell assets at month-end to pay benefits.
- **Their signal.** The equity weight of a 60/40 portfolio rebalanced at each month-end, minus 60%. Its predictability
  "is strong at month-end": it concentrates in the last week of the month. Their trading strategy holds the sign of the
  negative signal in that week and on the next month's first business day. Combined with an intra-month signal, it had
  a Sharpe ratio above 1 from 1997.
- **The question.** Does the month-end part alone pay on the S&P 500, held the way a retail CFD holds the US 500, which
  the owner's broker quotes?

**Known before freezing.** Each of these is said now, so that it cannot be explained away later.

- **This is a replication.** The paper's sample runs from 1997 to about 2023. RBL-1's judged period (2003-2018) and
  most of its holdout (2019-2026) lie inside it. A pass would confirm the paper on a tradable instrument; it would
  not show that the effect lasts.
- **The paper was read only in excerpts.** Its hosts are blocked here, so a GitHub runner printed the paper's lines
  that match a few keywords to a job log. The definitions above come from those lines. Some details could not be read:
  the exact days of the last week, and the signal's lag on the first business day.
- **RBL-1 is simpler than the paper's strategy.** It keeps only the month-end signal. It trades only stocks, where the
  paper's strategy paired S&P 500 futures against Treasury futures. It fixes one signal at T−4 for the whole hold,
  where the paper updated it daily.
- **Costs.** An index CFD's spread and five to eight nights of markup cost about 0.1% a month.
- **The bar is high.** US equity data here already carries 33 tests.

## The rule (fixed; nothing is tuned)

- **The calendar.** Each month's last trading day T, and the four before it, are computed from the NYSE's rules and its
  known unscheduled closures (`scripts/phd1.py`, checked against the NYSE's published calendars in PHD-1). T+1 is the
  next month's first trading day.
- **The signal.** A 60/40 portfolio of the S&P 500 (SPY) and the 10-year Treasury (IEF) is rebalanced at the previous
  month's last close. At the close of T−4 it has drifted to an equity weight w. The signal is w − 60%.
- **The trade.** From the close of T−4 to the close of T+1 (five trading days):
  - short the S&P 500 if the signal is positive (stocks are overweight, so the funds sell them);
  - long if it is negative;
  - no trade if it is exactly zero.
- **Costs.** 0.02% a side. A long pays the T-bill yield plus 2.5% a year for each night. A short is paid the T-bill
  yield minus 2.5% a year. The yield is the one last published (`^IRX`, at most 7 days old).
- **No trade.** A month whose closes or financing are unknown is no trade.
- **The statistic.** The mean net return per month, with its t.

## Periods

A month belongs to the period its hold closes in, so no month falls between two periods and none is counted twice.

| Role | Holds closing in | Months |
|---|---|---|
| Development | 2003-01 → 2010-12 | 96 |
| Validation | 2011-01 → 2018-12 | 96 |
| Judged (significance) | 2003-01 → 2018-12 | 192 |
| Holdout | 2019-01 → 2026-09. The judge never reads it. It is opened once, only if RBL-1 PASSED, as its own registered trial (RBL-1-H) | 93 |

## Gates (all required)

| Gate | |
|---|---|
| t | t of the mean net return per month over the judged period ≥ 3.180 |
| development | mean net per month > 0, holds closing in 2003 to 2010 |
| validation | mean net per month > 0, holds closing in 2011 to 2018 |
| costs ×2 | mean net per month > 0 with the cost per side and the markup doubled |
| both signs | the months it shorts and the months it holds long each have a mean net > 0 |
| top year | no calendar year supplies more than 50% of the total |

The both-signs gate keeps the result from being the market's own drift: a book that is long in some months and short in
others must earn on each side.

**Holdout rule.** Over the holds closing in 2019-01 to 2026-09, both of these must hold. Then it is VALIDATED;
otherwise it is REJECTED.

- mean net per month > 0, with one-sided t ≥ 1.645;
- mean net per month > 0 with the costs doubled.

**Reported, never gates.** The hit rate, each year, and every month left out.

## After the result

- **PASSED and VALIDATED.** It is proposed to the owner as a paper strategy of its own (CLAUDE.md rule 14), on the US
  500 CFD. That would be twelve trades a year. The risk engine sizes it, and it is followed forward on paper apart
  from every other record. Never real money.
- **Anything else.** It is reported as it is, and nothing changes.

## Power, declared

- **At the paper's strength.** About 16 basis points a day for a one-standard-deviation signal, over five days, is
  about 0.6% a month before costs. The S&P 500 moves about 2.5% over five days at one standard deviation, so that is
  about 0.24 of a month's spread. Over 192 months, t is about 3.3 before costs and about 2.9 after them.
- **What that means.** RBL-1 can pass only if the effect in 2003-2018 was at least as strong as the paper's average. A
  weaker one would FAIL. Its failure would then say only that the month-end part alone, on stocks alone, does not pay
  a retail CFD, and that would be reported as it is.
