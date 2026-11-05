# FOMC-1: the pre-FOMC announcement drift on the US 500 CFD (preregistration)

**Written, frozen and registered on 2026-11-05, before any FOMC-1 price was fetched.**

The owner, 2026-11-05: "don't fixate on the AI trading; anything that makes us a profit; never stop".

| | |
|---|---|
| Frozen spec | `research/specs/FOMC-1.json` |
| Spec sha256 | `085f33fabc97bc14c417d0f82a4dadbc5bdf5431292a45c76dadf23f841dacbe` |
| Code | `scripts/fomc1.py`, `scripts/xts1.py` and `scripts/ingest_dukascopy_candles.py`, sha256 `9f96134e9aa4f8c80230555268a883145ed8cbd9b9789d3b038be36e4f3b2cc3`. Every command after `spec` refuses to run if either hash changes |
| Calendar | `data/fomc/calendar.json`, checked at its source on GitHub's runner before the freeze (`fomc1-calendar` branch) |
| Run | `.github/workflows/fomc1-run.yml` on GitHub's runner, which can reach Dukascopy (this environment cannot). It runs `fetch`, then `judge`, then `holdout` only if `judge` PASSED |
| Threshold | t ≥ **3.144**. That is the Bonferroni value for the 28 earlier tests on index CFDs in the registry plus these 2, and never below 3.0 |

## Why this question

Every earlier program here asked whether some signal predicts a price, and none survived costs since 2008. FOMC-1
asks about a scheduled event instead:

- **The finding.** Lucca & Moench (2015, "The Pre-FOMC Announcement Drift", Journal of Finance) found that from 1994
  to 2011 the S&P 500 rose about 49 bps on average in the 24 hours before scheduled FOMC statements. That was a large
  share of the period's equity premium, earned on eight days a year.
- **The likely mechanism.** Risk resolved at a known time is paid for ahead of it.
- **The question.** Did the drift survive its publication, at a retail CFD's real costs? The paper circulated from
  2011 (New York Fed Staff Report 512), so every event tested here comes after it.

**Why NE-1 set it aside, and what changed.** NE-1 (2026-10) set this candidate aside for two reasons:

- **Too few events.** That is still true. It is declared under "Power" below as a limit, not explained away.
- **No calendar in the repository.** There is one now, and each date was checked at its source (next section).

## The calendar, checked before the freeze

`python scripts/fomc1.py calendar` ran on GitHub's runner. For each listed date it fetched the Fed's own press release
(`federalreserve.gov/newsevents/pressreleases/monetary<YYYYMMDD>a.htm`). Three runs, no price read in any:

1. **2013 to 2026-09.** All 109 pages exist and are the FOMC statement. The 85 from 2016 say "For release at 2:00 p.m.
   EDT" or "EST". The 24 from 2013 to 2015 failed the check.
2. **The same list again,** recording each page's own words. The pages of 2013 to 2015 say only "For immediate
   release". Their 2:00 pm time cannot be confirmed at the source, so they are **not events**.
3. **The final list, 2016-01 to 2026-09.** 85 events, all confirmed: eight a year, seven in 2020 and six in 2026 to
   September. In 2020 the scheduled March meeting was replaced by the unscheduled Sunday decision of 15 March, which
   had no 2:00 pm statement.

**Known before freezing.** Each of these is said now, so that it cannot be explained away later.

- Kurov, Wolfe & Gilbert (2021, "The disappearing pre-FOMC announcement drift", Finance Research Letters) report that
  the drift faded after 2015. The verified sample starts in 2016, so this test may simply confirm them.
- 2016 to 2021 was mostly a rising market. The timing gate exists for that: the events must beat the same window on
  ordinary weeks.
- Two meetings fell the day after a US presidential election: November 2020 (judged period) and November 2024
  (holdout). A control window, 8 to 9 November 2016, also spans one. Nothing is excluded for it: the rule is fixed.

## The rule (fixed; nothing is tuned)

- **Entry.** Buy the US 500 CFD (Dukascopy `USA500IDXUSD`) at the **ask** at 14:00 New York time on the weekday before
  the statement. The price is the close of the minute that ends then.
- **Exit.** Sell at the **bid** at 13:55 New York time on the statement's day, five minutes before it.
- **Costs.**
  - the quoted spread at both fills;
  - slippage of a quarter of the quoted spread at each fill;
  - overnight financing at the US policy rate public that day plus 2.5% a year, day count 360, for each night held.
- **Missing data.** A missing quote, or an unknown policy rate, means no trade. It is never filled in.
- **The control.** The same clock window, on the same weekdays, one week before and one week after each event, with
  the same costs.

## Periods

| Role | Period | Events |
|---|---|---|
| Development | 2016-01-01 → 2018-12-31 | 24 |
| Validation | 2019-01-01 → 2021-12-31 | 23 |
| Judged (significance) | 2016-01-01 → 2021-12-31 | 47 |
| Holdout | 2022-01-01 → 2026-09-30. The judge cuts its data there and never reads these prices. It is opened once, only if FOMC-1 PASSED, as its own registered trial (FOMC-1-H) | 38 |

## Gates (all required)

| Gate | |
|---|---|
| t | t of the mean net return per event over the judged period ≥ 3.144 |
| development | mean net per event > 0 in 2016 to 2018 |
| validation | mean net per event > 0 in 2019 to 2021 |
| costs ×2 | mean net per event > 0 with every cost doubled |
| top year | no calendar year supplies more than 50% of the total net |
| timing | the events beat the controls: mean difference > 0, with Welch t ≥ 2.0 |

**Holdout rule.** Over 2022-01 to 2026-09, all three of these must hold. Then it is VALIDATED; otherwise it is
REJECTED.

- mean net per event > 0, with one-sided t ≥ 1.645;
- mean net per event > 0 with every cost doubled;
- the events' mean above the controls' mean.

**Reported, never gates.**

- The gross mean and the mean cost per event.
- The hit rate.
- Each year's total.
- Every event's gross and net.
- The controls' own statistics.

## After the result

- **PASSED and VALIDATED.** It is proposed to the owner as a paper strategy of its own (CLAUDE.md rule 14), eight
  trades a year. The risk engine sizes it, and it is followed forward on paper apart from every other record. Never
  real money.
- **Anything else.** It is reported as it is, and nothing changes.

## Power, declared

- **The bar.** With 47 events, t ≥ 3.144 needs a mean of about 0.46 times the per-event standard deviation. With
  24-hour moves of about 1%, that is a mean near 0.46% per event: the drift at about its full published size.
- **What that means.** A real drift at half that size would FAIL here, and that would be reported as it is.
- **The holdout.** Its 38 events can confirm a drift that size, at one-sided t of about 2.8.

## Status: ABANDONED (2026-11-05, before any outcome was computed); superseded by FOMC-1A

**The fetch could not finish.** The run started at 08:45 UTC on one runner (`fomc1-run` 74edc12):

- Dukascopy's datafeed served it about one day of minute quotes every 150 seconds: 14 of the 510 days in 35 minutes.
- At that rate the fetch needs about 21 hours, against the job's 150-minute limit.
- The frozen fetch also refused the whole run on any one day that could not be fetched. Earlier ingests here lost a
  few days in a hundred that way (`ix4b-data`: 6 failed days in 132).

**What was and was not done.**

- The run was cancelled at about 09:20 UTC.
- No quotes file was written and the judge never ran. The log of the 14 days fetched is in `fomc1-run` ade5236; it
  holds no price.
- The registry records FOMC-1 as ABANDONED, with `outcome_computed: false`.

**What replaces it.** FOMC-1A (`research/preregistrations/FOMC-1A.md`) is the same rule, events, costs, control,
periods, gates and holdout. It imports them from this script unchanged. The only change is that the fetch runs in
parallel shards.
