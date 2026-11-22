# KRP-1 verdict: FAILED (development, 2026-11-22)

Judged once by run 44978747723 of `.github/workflows/krp1.yml` (head b7e1f39, the registration commit; its Run step
ran from 03:02:10 to 03:17:31 UTC, after registration at 02:50 UTC), with the registered code sha256 `42c9b2ed...`
and spec sha256 `cce30275...`, on 2018-01-01 to 2025-02-28. It printed:

```
{"program": "KRP-1", "verdict": "FAILED", "t": {"0.05": -0.8697910228458722, "0.1": -0.9186511559188468}}
```

Both thresholds failed against a bar of 3.0, with a t below zero. The entries it judged are on the `krp-data`
branch (commit c1d9be2, `data/KRP-1-events.json.gz`): 288 at a 5% premium (258 days, 40 coins) and 138 at 10%
(122 days, 17 coins). Averaged over days, as the study averages them, the coin beat bitcoin by +0.29% (5%) and
+0.11% (10%) over the 24 hours before costs, less than the 0.6% a round trip costs: -0.31% and -0.49% net. The
median entry lost to bitcoin even before costs (-0.13% and -0.21%); 49% and 48% of entries beat it. (Computed
here from those published entries; the judged record follows below once it is rewritten.)

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
