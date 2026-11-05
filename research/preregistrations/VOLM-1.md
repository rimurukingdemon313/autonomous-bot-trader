# VOLM-1: volatility-managed S&P 500 exposure (preregistration)

**Written, frozen and registered on 2026-11-05, before any VOLM-1 data was fetched.**

The owner, 2026-11-05: "don't fixate on the AI trading; anything that makes us a profit; never stop".

| | |
|---|---|
| Frozen spec | `research/specs/VOLM-1.json` |
| Spec sha256 | `41b98c864d370876b7ab7f16246175fec8e1c485ec09d6e132b7bf8a651d1ffd` |
| Code | `scripts/volm1.py`, sha256 `f7689ff04d784e74734136b680e5d4f0d34c575fb207295474481da42343fc34`. Every command refuses to run if either hash changes |
| Run | `.github/workflows/volm1-run.yml` on GitHub's runner, which can reach Yahoo (this environment cannot). It runs `fetch`, then `judge`, then `holdout` only if `judge` PASSED |
| Threshold | t ≥ **3.113**. That is the Bonferroni value for the 26 earlier tests on S&P 500 and US equity-index data in the registry (multi-asset-etf 12, multi-asset-long 10, equity-index-b 2, us-vol-etp 2) plus this 1, and never below 3.0 |

## Why this question

Every earlier program here asked whether a signal predicts the market's direction. VOLM-1 does not: it asks whether
**holding less after turbulent months** improves what the market pays per unit of risk.

- **The finding.** Moreira & Muir (2017, "Volatility-Managed Portfolios", Journal of Finance) found that it does.
- **The mechanism.** Volatility clusters, but expected returns do not rise with it. So the risk a turbulent month
  brings is paid poorly.
- **The question.** Does that hold for the S&P 500 since 1995, held the way a retail CFD holds it, after costs?

**Known before freezing.** Each of these is said now, so that it cannot be explained away later.

- Cederburg, O'Doherty, Wang & Yan (2020) found the gain weak out of sample across many factors.
- **Most of the gain, if any, comes from a few crashes.** The rule is lighter after turbulent months, as in late 2008
  and March 2020. The top year gate exists for that.
- **Calm years run at the cap of 2.** That exposure pays financing on all of it.
- **The test is alpha, not the mean.** A book that only held more of the market would earn more in a rising market
  without any skill. The alpha asks whether it beats the market at the market's own risk.

## The rule (fixed; nothing is tuned)

- **Realised variance.** At each month's last close, RV = the sum of the month's squared daily S&P 500 returns (SPY,
  dividends included).
- **The exposure for the next month** = the mean RV of every month so far (this one included), divided by this
  month's RV. It is about 1 after an ordinary month, less after a turbulent one, more after a calm one, and never
  above 2.
- **Holding.** The position is held for the month. Its exposure drifts with the market and is traded back at the next
  month's last close, paying 0.05% of the notional traded.
- **Financing.** A CFD's long financing is the short rate plus a markup. Every unit of exposure pays the 3-month
  T-bill yield (`^IRX`, the one last published, at most 7 days old) plus 2.5% a year, by calendar days. The market
  it is compared with pays the same. A month with a day whose yield is unknown is no trade.
- **The test.** OLS of the managed book's monthly net excess return on the market's, with White standard errors. The
  alpha is the intercept.
- **Data.** Yahoo daily closes: SPY adjusted for dividends and splits, and `^IRX` as published. Each file's sha256 is
  in the manifest. The judge cuts its data at the holdout.

## Periods

| Role | Period | Months |
|---|---|---|
| Development | 1995-01 → 2008-12 | 168 |
| Validation | 2009-01 → 2021-12 | 156 |
| Judged (significance) | 1995-01 → 2021-12 | 324 |
| Holdout | 2022-01 → 2026-09. The judge never reads it. It is opened once, only if VOLM-1 PASSED, as its own registered trial (VOLM-1-H) | 57 |

## Gates (all required)

| Gate | |
|---|---|
| t | White t of the monthly alpha over the judged period ≥ 3.113 |
| development | alpha > 0 in 1995 to 2008 |
| validation | alpha > 0 in 2009 to 2021 |
| costs ×2 | alpha > 0 with the trading cost and the markup doubled |
| book pays | the managed book's own mean monthly net excess return > 0 |
| top year | no calendar year supplies more than 50% of the total alpha (each month's managed return minus beta times the market's) |

**Holdout rule.** Over 2022-01 to 2026-09, all three of these must hold. Then it is VALIDATED; otherwise it is
REJECTED.

- alpha > 0, with one-sided White t ≥ 1.645;
- alpha > 0 with the costs doubled;
- the managed book's own mean monthly excess return > 0.

**Reported, never gates.**

- The managed book's and the market's own statistics, with their worst drawdowns.
- The exposure: its mean, its range, and the months at the cap.
- Each year's alpha.

## After the result

- **PASSED and VALIDATED.** It is proposed to the owner as a paper strategy of its own (CLAUDE.md rule 14), on the US
  500 CFD, one decision a month. The risk engine sizes it, and it is followed forward on paper apart from every other
  record. Never real money.
- **Anything else.** It is reported as it is, and nothing changes.

## Power, declared

- **The bar.** With 324 months, t ≥ 3.113 needs an alpha of about 0.6 of its own tracking error a year.
- **What that means.** Moreira & Muir's market alpha was about half that over 1926 to 2015. A real effect of the
  published size would most likely FAIL here, and that would be reported as it is.
