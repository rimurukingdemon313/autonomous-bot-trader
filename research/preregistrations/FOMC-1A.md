# FOMC-1A: FOMC-1's rule, fetched in parallel shards (preregistration)

**Written, frozen and registered on 2026-11-05, before any FOMC-1A or FOMC-1 outcome was computed.**

The owner, 2026-11-05: "don't fixate on the AI trading; anything that makes us a profit; never stop".

| | |
|---|---|
| Frozen spec | `research/specs/FOMC-1A.json` |
| Spec sha256 | `6e23b4917a88724986c720599e3858554f458fcba5ea50e8849795d93eaed304` |
| Code | `scripts/fomc1a.py` with the unchanged `scripts/fomc1.py`, `scripts/xts1.py` and `scripts/ingest_dukascopy_candles.py`, sha256 `35e21316b028f4da7284dda5e292f0c8fa896edc8048d16fdda64e29d3bb9ab8`. Every command after `spec` refuses to run if either hash changes |
| Run | `.github/workflows/fomc1a-run.yml`: 16 shards fetch at once on separate runners, then one job runs `merge`, `judge`, and `holdout` only if `judge` PASSED |
| Threshold | t ≥ **3.163**. That is the Bonferroni value for the 30 earlier tests on index CFDs in the registry (FOMC-1's 2 included, though it computed nothing) plus these 2, and never below 3.0 |

## Why an amendment

FOMC-1 (`research/preregistrations/FOMC-1.md`) was ABANDONED before any outcome was computed, because its fetch could
not finish:

- one runner got about one day of minute quotes every 150 seconds, about 21 hours for the 510 days;
- its fetch refused the whole run on any one day it could not fetch.

## What is FOMC-1's, unchanged

All of these are imported from `scripts/fomc1.py`, which is not edited:

- **The question.** Did the pre-FOMC announcement drift (Lucca & Moench 2015) survive its publication, at a retail
  CFD's real costs?
- **The 85 events.** Each was checked at the Fed's own press release: the FOMC statement, "For release at 2:00 p.m.",
  2016-01 to 2026-09 (`data/fomc/calendar.json`).
- **The rule.** Buy the US 500 CFD at the ask at 14:00 New York time the weekday before the statement, and sell at the
  bid at 13:55 on its day.
- **The costs.** The quoted spread, a quarter of it as slippage at each fill, and financing at the US policy rate plus
  2.5% a year.
- **The control.** The same window one week before and one week after each event.
- **The periods.** Development 2016 to 2018 and validation 2019 to 2021, judged together (47 events). The holdout is
  2022-01 to 2026-09 (38 events), opened once and only after a pass.
- **The gates, the holdout rule, what is reported, and what happens after the result.**

FOMC-1's "Known before freezing" and "Power, declared" sections apply here as written. Only a drift near its full
published size can pass t ≥ 3.163 with 47 events.

## What changes

- **The fetch runs in 16 shards on separate runners**, each with its own share of the days (`fetch <i> 16`). A day
  that fails is tried once more, more slowly, at the end of its shard. A day that fails again is recorded as `failed`
  and never filled.
- **`merge` joins the shards** into FOMC-1's own quotes file and manifest. It refuses unless every day is accounted for
  by exactly one shard: ok, empty (no quotes, such as a holiday), or failed.
- **Failed days are no trade.** A window that touches a failed day is no trade, like any missing quote. Fetch
  failures have nothing to do with what the market did, so this costs power, not honesty.
- **A limit on lost events.** If more than one in ten of a period's event windows is lost to failed days, that period
  is not judged at all. That means more than 4 of the 47, or more than 3 of the 38.
