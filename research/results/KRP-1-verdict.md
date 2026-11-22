# KRP-1 verdict: FAILED (development, 2026-11-22)

Judged once by run 44978747723 of `.github/workflows/krp1.yml` (head b7e1f39, the registration commit; its Run step
ran from 03:02:10 to 03:17:31 UTC, after registration at 02:50 UTC), with the registered code sha256 `42c9b2ed...`
and spec sha256 `cce30275...`, on 2018-01-01 to 2025-02-28. It printed:

```
{"program": "KRP-1", "verdict": "FAILED", "t": {"0.05": -0.8697910228458722, "0.1": -0.9186511559188468}}
```

At a 5% premium it FAILED (t -0.87 against a bar of 3.0); at 10% it was INCONCLUSIVE, with 138 entries where the
preregistration requires 150 (its t, -0.92, was below zero too). One threshold failed and none passed, so the
study's verdict is FAILED. The entries it judged are on the `krp-data` branch (commit c1d9be2,
`data/KRP-1-events.json.gz`): 288 at a 5% premium (258 days, 40 coins) and 138 at 10% (122 days, 17 coins). Averaged over days, as the study averages them, the coin beat bitcoin by +0.29% (5%) and
+0.11% (10%) over the 24 hours before costs, less than the 0.6% a round trip costs: -0.31% and -0.49% net. The
median entry lost to bitcoin even before costs (-0.13% and -0.21%); 49% and 48% of entries beat it. (Computed
here from those published entries; the judged record, below, gives the same means.)

## The records that were lost

Its commit step failed. While it ran, main had moved on (SCX-1's development records and SCX-1-V's registration had
been appended to `research/registry.jsonl`), the rebase of its own appended line conflicted, and the step stopped as
it was written to. KRP-1's verdict line and `research/knowledge/KRP-1.json` never reached main; the registry still
reads KRP-1 as pending. The commit step of `krp1.yml` and `scx1.yml` now copies a study's own files and registry
lines onto a fresh main and retries, which was tested against a concurrent append before it was pushed.

## The reproduction, and its rule, fixed before it runs

The same registered code is run once more on the same stage, only to write the lost records. **The verdict that
binds is the first run's: FAILED.** The second must print the same verdict and the same two t values, and its
entries must equal those on c1d9be2. Any difference is a fault to be found and reported, never a result, and no
figure from the second run replaces one of the first.

## The reproduction: run 44982217651, identical

Run 44982217651 (head f4bf099; judged at 03:47:49 UTC, recorded on main by 27ca2b8, its entries on `krp-data` commit
6957de9) ran the same registered code (`42c9b2ed...`) and spec (`cce30275...`) on the same stage: 6,061 Binance
archive files, none absent; 205 Upbit markets, none absent; 204 coins; no bar after 2025-03-02 02:00 UTC was read.
Its entries equal those on c1d9be2 at both thresholds, and its verdict and both t values equal the first run's to
the last digit (`-0.8697910228458722`, `-0.9186511559188468`). The rule above was met: the records on main are the
first run's verdict, written by its exact reproduction. Record: `research/knowledge/KRP-1.json`.

| Threshold | Entries | Days | Coins | Net a day | t | Before costs | Costs doubled | Korean discounts (same rule) | Placebo p95 | Verdict |
|---|---|---|---|---|---|---|---|---|---|---|
| 5% | 288 | 258 | 40 | **-0.31%** | **-0.87** | +0.29% | -0.91% | -0.66% (57) | +0.05% | FAILED |
| 10% | 138 | 122 | 17 | -0.49% | -0.92 | | | | | INCONCLUSIVE (138 < 150 entries) |

At 5% every gate failed but one: both halves (-0.17%, then -0.46%), the five best removed (-0.56%), the best day
removed (-0.40%: 2021-05-19), the best coin removed (-0.47%: XEC), an hour later (-0.23%), and the placebo (22% of its
draws at or above the rule). The one it passed: Korean discounts of the same size did worse still (-0.66%). 44% of
entries were positive, the median -0.73%; the worst -29.3%, the best +29.5%.

## What it says

A coin whose Korean premium had just jumped beat bitcoin over the next day by about 0.3% before costs, less than
half of the 0.6% a round trip costs, and it did not do so reliably: the median entry lost to bitcoin before costs.
Whatever residents do to close a coin-relative gap, it does not leave a day-long drift on Binance that a buyer an
hour late can collect. **KRP-1 FAILED as registered.** KRP-1-V is not registered and will not be; no variant is
judged on these days.
