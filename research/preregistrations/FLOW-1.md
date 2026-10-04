# FLOW-1: scheduled order flow at the Tokyo and London fixes (preregistration)

**Written and committed before any FLOW-1 outcome was computed.**

| | |
|---|---|
| Frozen spec | `research/specs/FLOW-1.json` |
| Spec sha256 | `6d09ec9c406597e4422de3704be32651688a727f2baeaae895e3beef1b0bc985` |
| Frozen code | `aitrader/research/discovery/flow.py`, `scripts/flow1.py` and the data loaders (`code_sha256` in the spec); every stage refuses to run if any of them changed |
| Read before writing | spread by hour and bar counts by hour (predictors only). This found that hour 00 UTC is missing from the source mirror for 12 of 13 instruments |
| Not read | any return, mean or test statistic |

## Why this question, after 54 rejections

Every earlier hypothesis asked whether price patterns, indicators, positioning or macro levels
predict price; all failed. Loss forensics showed gross edges within ±0.03R of zero and costs of
about 0.09R per trade (docs/EDGE_DISCOVERY_AUDIT.md). FLOW-1 changes the source of information:
**scheduled, non-informational order flow**. Benchmark fixes force large orders to execute at a
known time. Prices are pushed toward the order and later revert. The mechanism is institutional
and documented, it does not depend on a pattern recurring by chance, and every trade happens at
a fixed clock time, so the number of observations is large.

## Hypotheses (4 tests)

| ID | Rule (fixed from the literature; nothing is tuned) |
|---|---|
| FLOW1-H1-GOTOBI-PRE | On Tokyo gotobi days (5th, 10th, 15th, 20th, 25th, last day; previous weekday if on a weekend), **long USDJPY 08:00 → 10:00 JST** (bar opens 23:00 UTC → 01:00 UTC). Importers' dollar purchases funnel into the 09:55 JST fixing (Ito & Yamada 2017) |
| FLOW1-H2-GOTOBI-POST | Same days, **short USDJPY 10:00 → 12:00 JST** (01:00 → 03:00 UTC): the demand is gone after the fix |
| FLOW1-H3-FIX-MONTHEND | Last business day of each month, for each of EURUSD, GBPUSD, AUDUSD, NZDUSD, USDJPY, USDCHF, USDCAD: **fade the 15:00 → 15:45 London move, entering 16:15 and exiting 17:15 London**. Pre-fix pressure from benchmark orders reverses after the 4 p.m. WM/Reuters fix (Evans 2018; Melvin & Prins 2015) |
| FLOW1-H4-FIX-DAILY | The same rule on every other business day |

H3 and H4 count one observation per day: the mean across the available pairs, which must
number at least 4. The pairs share the dollar leg, so they are not independent observations.

## Data and costs

- **Data:** Dukascopy M15 bid/ask through the sealed `DataStore`; the 2017+ data is truncated
  without the single-use key.
- **The missing hour.** Hour 00 UTC is absent at the source: the GitHub mirror has no `00h`
  files. H1 and H2 use only bar opens that exist (23:00, 01:00, 03:00 UTC). No stop is used, so
  only the two endpoints matter.
- **Fills:** a buy pays the ask plus 0.1 pip of slippage; a sell receives the bid minus 0.1 pip.
- **Commission:** 0.7 pip per round trip.
- **Units:** results are in basis points of the entry mid.
- **No trade without a price:** a missing bar at an entry or exit time is no trade, never the
  nearest bar.
- **Holidays:** Japanese public holidays are not modelled. On those days there is no fixing, so
  their inclusion can only dilute the effect.

## Periods

| Role | Period |
|---|---|
| Development | 2007-04-01 → 2011-12-31 |
| Validation | 2012-01-01 → 2016-12-31 |
| Judged (significance) | 2007-04-01 → 2016-12-31, role `judge` in the registry |
| Sealed holdout | 2017-01-01 → 2018-05-31, opened once, only if a hypothesis passes every gate |

## Gates (all required)

1. **t ≥ 3.4305.** This is the two-sided Bonferroni threshold at 5% over the registry's 79
   earlier tests on this period plus these 4. It is fixed and is not lowered.
2. Mean net > 0 in development **and** in validation, separately.
3. At least 60% of years (with ≥ 20 observations) have a positive net mean.
4. Mean net > 0 with spread, slippage and commission **all doubled**.
5. No single year supplies more than 50% of the total net.
6. H3/H4: mean net > 0 leaving out any one pair.
7. H1/H2: the gotobi mean exceeds the same window on non-gotobi days (Welch t ≥ 2). The effect
   must belong to the mechanism, not to the time of day.

## Holdout rule

The holdout is opened once, by trial FLOW-1-H, for the passers only. A passer is VALIDATED if its
mean net > 0 with one-sided t ≥ z(0.05 / number of passers), and mean net > 0 with costs ×2. If
nothing passes the gates, the holdout stays sealed.

## Power, stated in advance

- **Sample size.** About 700 gotobi days and about 117 month-ends fall in the judged period.
- **What H1 needs.** USDJPY's two-hour volatility in the Tokyo morning is typically 10–20 bps.
  H1 needs a net mean of about 2 bps (≈ 2 pips) to reach t = 3.43, which means a gross effect of
  about 4 pips after roughly 1.8 pips of costs.
- **What H3 needs.** H3 needs a large month-end effect: about 0.3 of a daily standard deviation
  per observation.
- **Reading a failure.** A failure means the effect is smaller than that after costs, not that it
  is absent.

## What a pass would and would not mean

- **A pass:** a passer becomes a VALIDATED edge only through the holdout. It then enters
  production as a scheduled strategy through the same risk engine, never sized by research.
- **A failure:** the hypothesis is recorded as REJECTED; it is not re-run with other windows.
