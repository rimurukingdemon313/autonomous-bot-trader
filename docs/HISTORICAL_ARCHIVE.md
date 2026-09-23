# Historical research archive

## What it is

The predecessor project, **`rimurukingdemon313/claude-bot-trade-backoff-symbolfix`**,
is this project's **Historical Research Archive**. It was a working,
DEMO-only TradeLocker bot (an SMC strategy, a risk engine, an executor, a
dashboard), and it holds a substantial body of pre-registered research.

It is **not deleted** and **not modified** to become this project. It is a
reference.

## Transfer policy

- **No code has been copied** from the archive into this repository.
- Something may be transferred later **only after review and explicit
  approval**, one component at a time, with its tests, and it must satisfy
  this project's contracts as they stand, not the archive's.
- A transferred component gets a new version in this project and records
  its origin.

## What the archive established

These are research findings. They are recorded here so that this project
does not spend its evidence re-testing what is already known, and so that
its multiple-testing count starts honestly.

**No edge was found in thirteen strategy families**, tested under
pre-registered rules with realistic costs on 2012-11 → 2022-03 data for 12
instruments:

- **SMC** (the archive's own strategy): 14,594 trades, **−0.075R per
  trade, t = −9.29** after costs. Frictionless, it was **+0.016R
  (t = 1.68)**: no meaningful edge even before costs.
- **A mean-reversion mode**: 38,971 trades, −0.069R, t = −14.3. Removed.
- **Three published trend-following rules** (Donchian, time-series
  momentum, moving-average trend): all failed the held-out test; two were
  significantly negative (t ≈ −3.1).
- **An eight-family program** (adaptive trend, cross-sectional momentum,
  z-score reversion, volatility breakout, tick-VWAP reversion, regime
  switching, trend pullback, London opening range): **none passed even
  the first gate.** Before costs, every family sat within a few hundredths
  of an R of zero.

The consistent pattern: **simple price-derived rules on these instruments
carry almost no directional information, and costs then turn "nothing"
into a steady loss.** Cost in R is roughly spread divided by stop
distance, so short-horizon, tight-stop approaches are hit hardest.

## What this means for this project

1. **The archive's dataset is not unseen.** Sixteen hypothesis verdicts
   were read from it, and every year from 2012 to 2022 was used by at least
   fourteen of them. Its experiment registry records this. Those uses are
   imported into this project's registry before any new research touches
   that data, and a new test on it faces a correspondingly high bar
   (about |t| > 2.97 at the time of archiving).
2. **Broker history from 2022-04-01 onward was sealed** in the archive as
   an unused holdout. Whether this project adopts that seal, or chooses its
   own holdout in Phase 1, is decided before any research starts.
3. **The prior is sobering.** A more flexible model on the same inputs
   might find interactions that simple rules miss. It is also more capable
   of fitting noise. This project's validation contract exists because of
   that.

## Engineering lessons carried over as rules

Each of these was a real defect in the archive, and each is now a rule in
[ENGINEERING_RULES.md](../ENGINEERING_RULES.md) or a contract:

- The dataset's timestamps were in broker server time (New York + 7h,
  following US daylight saving), not UTC. Every session rule ran on the
  wrong hours until the clock was measured → **DATA_CONTRACT §3**.
- A wrong price-scale divisor produced complete, normal-looking backtests
  that measured nothing → **ambiguous scale is an error**.
- A causality test missed a one-bar leak until it was replaced by a
  per-decision truncation test, with a meta-test that injects a leak →
  **tests that guard must be able to fail**.
- The backtester once saw more history than the live system did →
  **one feature definition, one lookback, for research and production**.
- A server error on an order was once treated as retryable → **writes are
  never retried**.
- The stop was set without accounting for the spread → **costs are part of
  every label and every decision**.
