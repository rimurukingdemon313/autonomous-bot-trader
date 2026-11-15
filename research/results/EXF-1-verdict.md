# EXF-1: the verdict

**FAILED, as registered** (dev stage, 2021-2023, judged once on 2026-11-15 by run 2 of `exf1.yml`; record
`research/knowledge/EXF-1.json`, preregistration `research/preregistrations/EXF-1.md`). Nothing was changed or run
again. Calculations below that are not in the record are marked as such.

## The rule (facts from the record)

| Threshold on the previous rate | Trades | Weeks | Net a trade | t | Before fills | Funding received | Placebo 95th pct | Gates failed |
|---|---|---|---|---|---|---|---|---|
| 0.05% | 30,824 | 157 | -11.9 bp | -7.36 | +8.1 bp | +13.5 bp | -16.8 bp | 7 of 8 (all but the placebo) |
| 0.1% | 14,225 | 157 | -8.5 bp | -3.07 | +11.5 bp | +20.9 bp | -13.8 bp | 7 of 8 (all but the placebo) |
| 0.2% | 5,706 | 148 | -10.0 bp | -1.61 | +10.0 bp | +30.8 bp | -11.5 bp | 7 of 8 (all but the placebo) |
| 0.5% | 1,223 | 120 | -20.3 bp | -2.50 | -0.3 bp | +49.8 bp | -2.9 bp | 8 of 8 |

Of 44,814 candidates at 0.05%, 13,904 were below the volume floor and 86 had a bar missing; 1,423 of the trades met a
settled rate of the other sign. No bar file was absent. The median 5-minute quote volume before entry was 397,000.

## The mechanism (facts from the record: every complete settlement)

| abs(F) | Settlements | Mean abs(F) | Premium move, signed | Pass-through | Before T | After T |
|---|---|---|---|---|---|---|
| up to 0.011% (the dead zone) | 179,961 | 0.9 bp | -0.1 bp | -0.08 | +0.3 | -0.3 |
| 0.011% to 0.05% | 69,542 | 2.7 bp | +0.6 bp | 0.20 | +0.1 | +0.5 |
| 0.05% to 0.1% | 25,337 | 6.9 bp | +1.8 bp | 0.26 | 0.0 | +1.8 |
| 0.1% to 0.2% | 11,915 | 14.0 bp | +4.8 bp | 0.34 | -0.9 | +5.7 |
| 0.2% to 0.5% | 6,089 | 28.6 bp | +11.7 bp | 0.41 | -4.2 | +15.9 |
| above 0.5% | 1,353 | 97.5 bp | +60.7 bp | 0.62 | -6.2 | +66.9 |

## Why it failed (calculation on the record)

The frictionless prediction holds in direction: across a settlement the premium jumps the way the payment says,
almost all of it after T, by a share of the payment that grows with its size. But the index moves the same way, so
the contract's own price takes back more than the premium shows: 1 - (before fills / funding received) = 0.40, 0.45,
0.67 and 1.0 at the four thresholds. What is left, 8 to 11 bp before fills where the payments are moderate, is less
than two taker fills of 10 bp; where payments are largest, nothing is left, and the trade does no better than the same
trade at hours with no payment.

## What follows

No later stage is registered, and the 2021-2023 bars are spent for any rule about funding settlements. The one route
the result leaves is passive execution, which bars cannot test: a maker's fill at the best bid or ask instead of two
taker fills. It needs the archive's best bid and ask (`bookTicker`) and a fill model that counts an order filled only
when trades go through its price, judged on 2024-2025, which no stage has read. That is a new hypothesis, to be
registered as one.
