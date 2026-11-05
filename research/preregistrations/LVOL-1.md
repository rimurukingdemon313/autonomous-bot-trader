# LVOL-1: the low-volatility anomaly through its ETFs (preregistration)

**Written, frozen and registered on 2026-11-05, before any LVOL-1 data was fetched.**

The owner, 2026-11-05: "don't fixate on the AI trading; anything that makes us a profit; never stop".

| | |
|---|---|
| Frozen spec | `research/specs/LVOL-1.json` |
| Spec sha256 | `dd8a32e363bc57291e0f99a945749c5a08e8320f0f69bd74b1eb7f066cb2c826` |
| Code | `scripts/lvol1.py` and `scripts/volm1.py` (its Yahoo fetch and its alpha), sha256 `abdbe5f9e9a5bf0e1755a080e3f19820f04ac4aae940ee23447177fb10a1c89f`. Every command refuses to run if either hash changes |
| Run | `.github/workflows/lvol1-run.yml` on GitHub's runner, which can reach Yahoo (this environment cannot). It runs `fetch`, then `judge`, then `holdout` only if `judge` PASSED |
| Threshold | t ≥ **3.154**. That is the Bonferroni value for the 30 earlier tests on S&P 500 and US equity data in the registry plus this 1, and never below 3.0 |

## Why this question

- **The finding.** Stocks that move less have earned about as much as those that move more, so per unit of risk they
  have earned more (Black 1972; Ang, Hodrick, Xing & Zhang 2006; Frazzini & Pedersen 2014, "Betting Against Beta").
- **The mechanism.** Investors who cannot borrow buy risky stocks to reach for return, and overpay for them.
- **The instruments.** Since 2011 two ETFs have held the low-volatility side of the market: SPLV (S&P 500 Low
  Volatility) and USMV (MSCI USA Minimum Volatility). No test here has used them.
- **The question.** Do they beat the S&P 500 at its own risk, held the way a retail CFD holds them?

**Known before freezing.** Each of these is said now, so that it cannot be explained away later.

- Low-volatility investing became popular after 2011, and its stocks became expensive by 2016, so the premium may have
  been spent.
- **The sample is short.** The funds began in 2011, so the judged period has only 108 months.
- **The broker.** A CFD broker may not quote these funds at all.

## The rule (fixed; nothing is tuned)

- **The book.** It holds SPLV and USMV, half each. At every month's last close common to all three funds, it is traded
  back to half each, paying 0.05% of what is traded.
- **Excess returns.** The book's monthly excess return is its return minus the T-bill yield known at the month's start
  (`^IRX`, at most 7 days old) and a CFD's 2.5% a year markup, by calendar days. SPY's is computed the same way.
- **The test.** The alpha of the book on SPY: OLS with White standard errors, as in VOLM-1.
- **Missing data.** A month without a known yield is no trade.

## Periods

| Role | Period | Months |
|---|---|---|
| Development | 2012-01 → 2016-12 | 60 |
| Validation | 2017-01 → 2020-12 | 48 |
| Judged (significance) | 2012-01 → 2020-12 | 108 |
| Holdout | 2021-01 → 2026-09. The judge never reads it. It is opened once, only if LVOL-1 PASSED, as its own registered trial (LVOL-1-H) | 69 |

## Gates (all required)

| Gate | |
|---|---|
| t | White t of the monthly alpha over the judged period ≥ 3.154 |
| development | alpha > 0 in 2012 to 2016 |
| validation | alpha > 0 in 2017 to 2020 |
| costs ×2 | alpha > 0 with the trading cost and the markup doubled |
| each fund | SPLV alone and USMV alone each have an alpha > 0 |
| top year | no calendar year supplies more than 50% of the total alpha |

**Holdout rule.** Over 2021-01 to 2026-09, both of these must hold. Then it is VALIDATED; otherwise it is REJECTED.

- alpha > 0, with one-sided White t ≥ 1.645;
- alpha > 0 with the costs doubled.

**Reported, never gates.** The book's and SPY's own statistics, each fund's alpha, and each year.

## After the result

- **PASSED and VALIDATED.** If the broker quotes the funds, it is proposed to the owner as a paper strategy of its own
  (CLAUDE.md rule 14). The risk engine sizes it, and it is followed forward on paper apart from every other record.
  Never real money.
- **Anything else.** It is reported as it is, and nothing changes.

## Power, declared

- **The bar.** With 108 months, t ≥ 3.154 needs an alpha of about 1.0 of its own tracking error a year.
- **What that means.** The published low-volatility premium is a third of that or less. This test can confirm only an
  effect several times the published one, and a real one of ordinary size would FAIL. It is run because the queue
  holds it and its data is fresh. Its likely failure says little against the effect itself, and that would be reported
  as it is.

## Result (run 2026-11-05 on GitHub's runner; `research/knowledge/LVOL-1.json`)

**FAILED.** Three gates failed: t, validation and top year. The holdout (2021-01 to 2026-09) stays unread, and nothing
changes.

**The data.** SPLV had 3,900 daily closes from 2011-05-05, USMV 3,783 from 2011-10-20, SPY 8,501 and ^IRX 8,491, all
to 2026-11-05. All 108 judged months traded.

**The figures, 2012-01 to 2020-12.**

| | Value | Gate |
|---|---|---|
| Alpha on SPY, net | +0.076% a month, **+0.91% a year** | |
| White t | **0.44** | t ≥ 3.154: **failed** |
| Beta on SPY | 0.70 | reported |
| Development 2012-2016 | alpha > 0 | passed |
| Validation 2017-2020 | alpha ≤ 0 | **failed** |
| Costs doubled | alpha > 0 | passed |
| Each fund alone | SPLV > 0 and USMV > 0 | passed |
| Top year | one year gave more than 50% of the total | **failed** |

**What was lost, and why there is no second run.**

- The runner committed the data, this result in full and the registry verdict as 44225df. GitHub refused its push
  with "fatal error in commit_refs". The same GitHub-side failure refused this session's pushes from about 16:00 to
  16:06 UTC. The runner is gone.
- Its job log kept the judge's own line. That line, with the fetch and holdout lines, is copied to
  `research/results/lvol1-*.log`. The verdict is recorded from it.
- The judge prints every failed gate, so a gate it does not name passed. The magnitudes behind development,
  validation, costs ×2, each fund and each year are lost, and so are the data's hashes.
- LVOL-1 is not run again. A judged program never is, on the same data.

**What it means, and no more.**

- Over 2012-2020 the low-volatility ETFs earned about 0.9% a year more than their 0.70 beta to the S&P 500 implied.
  That is far inside the noise of 108 months.
- It was positive to 2016 and not after.
- As declared before the run, this test could confirm only an effect several times the published one. It says
  nothing more, either way.
