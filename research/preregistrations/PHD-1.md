# PHD-1: the pre-holiday effect in the S&P 500 (preregistration)

**Written, frozen and registered on 2026-11-05, before any PHD-1 data was fetched.**

The owner, 2026-11-05: "don't fixate on the AI trading; anything that makes us a profit; never stop".

| | |
|---|---|
| Frozen spec | `research/specs/PHD-1.json` |
| Spec sha256 | `77ecc265ad5e2e818c9ce7a0f976c408e3ad34eaadd991535f3dd4b4ea9cd902` |
| Code | `scripts/phd1.py` and `scripts/volm1.py` (its Yahoo fetch), sha256 `031a5dfdcd9e1c986d0680094c816b0bd2656b9827ce456d5d0973d47f553d67`. Every command refuses to run if either hash changes |
| Run | `.github/workflows/phd1-run.yml` on GitHub's runner, which can reach Yahoo (this environment cannot). It runs `fetch`, then `judge`, then `holdout` only if `judge` PASSED |
| Threshold | t ≥ **3.144**. That is the Bonferroni value for the 28 earlier tests on S&P 500 and US equity data in the registry (VOLM-1 and SEC-1 included) plus these 2, and never below 3.0 |

## Why this question

- **The finding.** Lakonishok & Smidt (1988) and Ariel (1990) found that US stocks earned many times their usual daily
  return on the trading day before a market holiday.
- **The mechanisms offered.** Short covering before a long closure, and a mood effect.
- **The question.** Does the S&P 500 still pay on that day, since 1995, after a retail CFD's costs, and more than on
  an ordinary day?

**Known before freezing.** Each of these is said now, so that it cannot be explained away later.

- Later studies found the effect fading in large stocks after it was published.
- **Few events.** There are about nine a year, so 1995 to 2021 holds about 240. Only a large effect can pass.
- **Long weekends.** A Monday holiday's event is the Friday before it, so most events are Fridays.

## The rule (fixed; nothing is tuned)

- **The calendar.** The scheduled NYSE holidays are computed from their published rules (`nyse_holidays`):
  - New Year's Day, which is not observed on a Friday when it falls on a Saturday;
  - Martin Luther King Jr. Day from 1998;
  - Washington's Birthday, Good Friday and Memorial Day;
  - Juneteenth from 2022;
  - Independence Day, Labor Day, Thanksgiving and Christmas.

  A Saturday holiday is observed on the Friday before and a Sunday one on the Monday after. Before freezing, the rules
  were checked against the NYSE's published calendars for 1995, 1998, 2016, 2019, 2021, 2022 and 2023.
- **The event day** is the last trading day before each holiday.
- **The trade.** Buy the S&P 500 (SPY, dividends included) at the close of the trading day before the event day, and
  sell at the event day's close.
- **Costs.** Each side pays 0.02% (spread and slippage). Each night held pays the T-bill yield (`^IRX`, the one last
  published, at most 7 days old) plus 2.5% a year.
- **The control.** Every other trading day, held the same way at the same costs.
- **Missing financing.** A day whose financing is unknown is left out of both.
- **The calendar is checked against the data** before anything is judged:
  - no computed holiday may have a close;
  - every weekday without a close must be a computed holiday or a known unscheduled closure (`UNSCHEDULED`: 1994-04-27,
    2001-09-11 to 14, 2004-06-11, 2007-01-02, 2012-10-29 and 30, 2018-12-05, 2025-01-09).

  Otherwise nothing is judged.

## Periods

| Role | Period |
|---|---|
| Development | 1995-01-01 → 2008-12-31 |
| Validation | 2009-01-01 → 2021-12-31 |
| Judged (significance) | 1995-01-01 → 2021-12-31 |
| Holdout | 2022-01-01 → 2026-09-30. The judge never reads it. It is opened once, only if PHD-1 PASSED, as its own registered trial (PHD-1-H) |

## Gates (all required)

| Gate | |
|---|---|
| t | t of the mean net return on event days over the judged period ≥ 3.144 |
| development | mean net per event > 0 in 1995 to 2008 |
| validation | mean net per event > 0 in 2009 to 2021 |
| costs ×2 | mean net per event > 0 with the costs and the markup doubled |
| beats ordinary days | event days beat every other day held the same way: mean difference > 0, with Welch t ≥ 2.0 |
| top year | no calendar year supplies more than 50% of the total net |

**Holdout rule.** Over 2022-01 to 2026-09, all three of these must hold. Then it is VALIDATED; otherwise it is
REJECTED.

- mean net per event > 0, with one-sided t ≥ 1.645;
- mean net per event > 0 with the costs doubled;
- the events' mean above the ordinary days' mean.

**Reported, never gates.** The ordinary days' own statistics, the hit rate, each year, and every event day.

## After the result

- **PASSED and VALIDATED.** It is proposed to the owner as a paper strategy of its own (CLAUDE.md rule 14), on the US
  500 CFD, about nine trades a year. The risk engine sizes it, and it is followed forward on paper apart from every
  other record. Never real money.
- **Anything else.** It is reported as it is, and nothing changes.

## Power, declared

- **The bar.** With about 240 events and daily moves of about 1.2%, t ≥ 3.144 needs a mean of about 0.24% per event,
  after costs. That is the effect at about its size before 1990.
- **What that means.** A real but faded effect would FAIL here, and that would be reported as it is.

## Result (run 2026-11-05 on GitHub's runner; `research/knowledge/PHD-1.json`)

**FAILED.** Four gates failed: t, costs ×2, beats ordinary days and top year. The holdout (2022-01 to 2026-09)
stays unread, and nothing changes.

**The data.** SPY had 8,500 closes and `^IRX` 8,490 (1993 to 2026-11-04). The computed holiday calendar agreed with
the data's own trading days, so the judge ran.

**The figures, 1995 to 2021.** Each figure is a one-day hold, net of both sides and the night's financing.

| | Mean per day | t | Gate |
|---|---|---|---|
| Event days (236) | +0.053% | **0.82** | t ≥ 3.144: **failed** |
| Development 1995-2008 (121) | +0.035% | 0.36 | > 0: passed |
| Validation 2009-2021 (115) | +0.073% | 0.86 | > 0: passed |
| Costs doubled | −0.001% | −0.01 | > 0: **failed** |
| Reported: ordinary days (6,561) | −0.012% | −0.78 | never a gate |
| Events minus ordinary days | +0.065% | **0.98** | Welch t ≥ 2.0: **failed** |

- The hit rate was 54.7%.
- 1999 alone supplied 71% of the total, so the top year gate failed too.

**What it means, and no more.**

- The eve of a market holiday still paid a little more than an ordinary day, about +0.065% after the same costs.
  That is a fraction of the 1963-1987 effect, and well within chance (t 0.98).
- After a CFD's costs it is about zero.
- As registered, the holdout is not opened for a hypothesis that failed.
