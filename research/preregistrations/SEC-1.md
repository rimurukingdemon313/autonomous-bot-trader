# SEC-1: US sector momentum, monthly (preregistration)

**Written, frozen and registered on 2026-11-05, before any SEC-1 data was fetched.**

The owner, 2026-11-05: "don't fixate on the AI trading; anything that makes us a profit; never stop".

| | |
|---|---|
| Frozen spec | `research/specs/SEC-1.json` |
| Spec sha256 | `02182e32212ebf6bff71697c8470d4c379928a88eedd2562acf47678467018c5` |
| Code | `scripts/sec1.py`, sha256 `c7d9cf76e3ba4d110194700fe7f6340049fa06eaac2b2ce20cc4b2903a23c86d`. Every command refuses to run if either hash changes |
| Run | `.github/workflows/sec1-run.yml` on GitHub's runner, which can reach Yahoo (this environment cannot). It runs `fetch`, then `judge`, then `holdout` only if `judge` PASSED |
| Threshold | t ≥ **3.124**. That is the Bonferroni value for the 27 earlier tests on S&P 500 and US equity data in the registry (VOLM-1's included) plus this 1, and never below 3.0 |

## Why this question

- **The finding.** Moskowitz & Grinblatt (1999, "Do Industries Explain Momentum?", Journal of Finance) found that the
  industries that rose most over the past six months kept beating the others over the next month. Much of stock
  momentum, they found, is industry momentum.
- **Why it might hold.** Industries move on slow-spreading news (earnings cycles, regulation, commodity prices), and
  investors update late.
- **The question.** Did it hold after its publication, across the nine sectors of the S&P 500 that have had a fund
  since 1998, at a retail trader's costs?

**Known before freezing.** Each of these is said now, so that it cannot be explained away later.

- Sector rotation by momentum became a common product after 2000, so the effect may be crowded away.
- **The comparison.** The nine sectors are all large and correlated, so the difference between three of them and all
  nine is modest even when it is real.
- **Crashes.** A momentum book can lose badly at sharp turns, as in 2009, when the laggards rebounded first.

## The rule (fixed; nothing is tuned)

- **The ranking.** At each month's last close, rank the nine Select Sector SPDR funds (XLB, XLE, XLF, XLI, XLK, XLP,
  XLU, XLV, XLY) by their total return over the six months to that close (dividends in), ties by name.
- **The book.** It holds the top three, equally weighted, for the next month.
- **The benchmark.** It holds all nine, equally weighted.
- **Costs.** Each month both are traded back to their weights, the month's drift included, paying 0.05% of the
  notional traded.
- **Missing data.** A fund without the closes a month needs means no trade that month, for both. The next month
  starts from flat and pays to enter.
- **The question.** The monthly difference: the book's net minus the benchmark's.
- **Data.** Yahoo daily closes adjusted for dividends and splits. Each file's sha256 is in the manifest. The judge cuts
  its data at the holdout.

## Periods

| Role | Period | Months |
|---|---|---|
| Development | 2000-01 → 2008-12 | 108 |
| Validation | 2009-01 → 2017-12 | 108 |
| Judged (significance) | 2000-01 → 2017-12 | 216 |
| Holdout | 2018-01 → 2026-09. The judge never reads it. It is opened once, only if SEC-1 PASSED, as its own registered trial (SEC-1-H) | 105 |

## Gates (all required)

| Gate | |
|---|---|
| t | t of the mean monthly difference over the judged period ≥ 3.124 |
| development | mean monthly difference > 0 in 2000 to 2008 |
| validation | mean monthly difference > 0 in 2009 to 2017 |
| costs ×2 | mean monthly difference > 0 with the cost doubled |
| top year | no calendar year supplies more than 50% of the total difference |

**Holdout rule.** Over 2018-01 to 2026-09, both of these must hold. Then it is VALIDATED; otherwise it is REJECTED.

- the mean monthly difference > 0, with one-sided t ≥ 1.645;
- the mean monthly difference > 0 with the cost doubled.

**Reported, never gates.**

- The book's and the benchmark's own statistics and worst drawdowns.
- Each year.
- How many months each fund was held.

## After the result

- **PASSED and VALIDATED.** It is proposed to the owner as a paper strategy of its own (CLAUDE.md rule 14). The risk
  engine sizes it, and it is followed forward on paper apart from every other record. Never real money.
- **Anything else.** It is reported as it is, and nothing changes.

## Power, declared

- **The bar.** With 216 months, t ≥ 3.124 needs a monthly mean of about 0.21 times the difference's monthly standard
  deviation. That is a Sharpe ratio of about 0.74 a year on the difference.
- **What that means.** If the difference moves about 3% a month, the book must beat the nine by about 0.64% a month.
- **The likely outcome.** A real but modest effect would FAIL here, and that would be reported as it is.
