# RADX-1: where the funding radar's losses come from (preregistration)

**Written 2026-11-14, before any figure of the later part was computed.** Research only. RADX-1 judges a diagnosis
of RADAR-1's paper ledger. It changes nothing in the radar, validates no remedy and no strategy, and does not touch
RADAR-1's own forward test, whose single look stays on 2026-12-06 20:00 UTC with its frozen code.

| | |
|---|---|
| Code | `aitrader/perf/radx.py`, `aitrader/perf/stats.py`, `scripts/radx1.py` |
| Code sha256 | `805ee45ccc1b0e8e9a60baaa800fd69cf3cde9c33ffdc638f85e444bd2d3c76c` (`python scripts/radx1.py hash`) |
| Data | `ledger.json` on the `radar-data` branch at commit `274a965`: RADAR-1's public paper ledger, marks to 2026-11-14 18:00 UTC, 210 closed positions and 2 open |
| Ledger sha256 | `e5685649f89f14cd8c1149f989b7f6c522240f270067f5971b0c034fa87edee1` (the JSON with its keys sorted); the judge refuses any other file |
| Tests | `tests/unit/test_perf_radx.py`: ledgers built so the answer is known |
| Counted tests | 2, on `crypto-perp-live-xvenue`, 2026-10-30 to 2026-11-14 |
| Bar | t <= -3.0 for each prediction (the registry's floor; Bonferroni over the three tests now on this universe would ask only 2.39) |

## Why

RADAR-1 has lost about 2% of its book in 38 days, and its daily excess over cash stands at t -3.4. Its preregistered
look is three weeks away and will be read as registered. The owner's order of 2026-11-13 asks where the losses come
from and whether an improvement survives an independent check. This is the first half of that: the diagnosis.

## The split

By the hour a position was **opened**:

| Part | Positions | Use |
|---|---|---|
| Design | opened before 2026-10-30 11:00 UTC (`1793358000`): 122 closed positions | read freely; everything below comes from it |
| Later | opened at or after that hour and closed by the snapshot: 88 closed positions | **not read.** Each prediction is computed on it once |

The cut was fixed on 2026-11-13 as the 60th percentile of the opening times of the 204 positions closed by then,
before any outcome of a later position was computed. Open positions are left out: their outcome is not final.

## What the design part showed

A position's net is its funding received, plus what its two legs' prices did, less every fill's cost, in basis points
of one leg's notional.

| | Positions | Mean net | t | Sum |
|---|---|---|---|---|
| All | 122 | -19.4 bp | -2.83 | -2,367 bp |
| Funding +1,317 bp, price +496 bp, costs -4,180 bp | | | | |
| Opened on a trailing spread under 50%/yr | 81 | -27.6 bp | -4.64 | -2,235 bp |
| Opened within 6 h after the same coin's previous position closed for a decayed spread | 27 | -34.6 bp | -10.24 | -933 bp |
| Either | 83 | -27.7 bp | -4.77 | -2,301 bp |
| Neither | 39 | -1.7 bp | | -66 bp |

Two mechanisms, both visible in the rules themselves:

1. **Thin entries.** A round trip costs 33 to 39 bp. At 25%/yr a spread pays 0.29 bp an hour, so the position must
   last about five days at its entry spread to pay for its own fills; three quarters of the positions were closed
   within six hours.
2. **Churn.** The entry reads the 72-hour trailing spread and the exit reads the 24-hour one. A coin whose spread
   was wide two days ago and is gone now passes the entry and meets the exit in the next hour, then passes the
   entry again. Each turn costs a full round trip.

## The predictions, frozen

On the later part, with the same definitions (`THIN_APR = 0.50`, `CHURN_H = 6`):

- **P1, thin entries.** The positions opened on a trailing spread under 50%/yr have a negative mean net: t <= -3.0,
  and the mean stays negative without the coin that lost the most in the class.
- **P2, churn after decay.** The positions opened within six hours after the same coin's previous position was
  closed for `spread_decayed` have a negative mean net: t <= -3.0, and the mean stays negative without the coin
  that lost the most in the class.

The t-statistic is the mean over its standard error with positions as observations. Positions on one coin follow one
another and positions on different coins overlap in time; nothing is adjusted for that, and the gate without the
worst coin is the guard against one coin carrying a class.

**Verdict:** PASSED if both hold, FAILED otherwise, with the part that failed named. One look: the judge refuses a
second run, a changed code and any other ledger.

## What I had already seen (declared)

- The design part, in full.
- The radar's public `REPORT.md` of 2026-11-13 18:00 and 2026-11-14 18:00 UTC: the book's totals for the whole
  period, and the last 30 closed positions as coin, venues, days, exit reason and net. Those rows show several
  same-day `spread_decayed` exits on one coin, so **P2 is not blind**. The entry spread of a closed position is not
  printed there, so P1's quantity had not been seen.
- No figure of the later part by class, by entry spread or by time since the previous exit.

## What follows

- PASSED: the two mechanisms are worth a remedy. A remedy cannot be measured on the ledger, because removing an
  entry changes which later entries happen and the ledger does not hold the positions that were never opened. It
  is measured by replaying the radar's frozen decision code on the radar's own stored quotes under other
  parameters, and then forward from a registered hour (`docs/PERFORMANCE_ENGINEERING.md`, RADAR-C).
- FAILED: the pattern of the first three weeks did not last. No challenger is registered on it.
- Either way RADAR-1 is read on 2026-12-06 as registered. A diagnosis is not a strategy: the design part's 39
  positions outside both classes averaged -1.7 bp, so stopping these losses is not the same as making money.
