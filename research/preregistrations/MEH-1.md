# MEH-1: month-end equity-hedge rebalancing at the London 4 pm fix (preregistration)

**Written, frozen and registered on 2026-11-04, before any MEH-1 outcome was computed and before the index closes it
reads were fetched.** The owner, 2026-11-04: "change everything if you must; the most important thing is a profit;
don't stop; don't fool me with promises".

| | |
|---|---|
| Frozen spec | `research/specs/MEH-1.json` |
| Spec sha256 | `3e8700907777bdb5f6e648013f604d647477d0800af6076fb034d73bb9853b5a` |
| Code | `scripts/meh1.py` and `aitrader/research/discovery/flow.py`, sha256 `299d0cb2c4aadfbd152ab0588124b67e608086c69ed5f00c38f72f23a7b29eb7` (every command refuses to run if either hash changes) |
| FX data | the local Dukascopy M5 bid/ask, 2009-2016 (`data/m5`, ID-1's); the sealed 2017+ data is not read |
| Index data | daily closes of `^GSPC` and the seven home indices from Yahoo, fetched on GitHub's runner (`.github/workflows/meh1-data.yml`, branch `meh1-data`), each file checked against its manifest sha256 before it is read |
| Threshold | t ≥ **3.61**: the registry's Bonferroni value for the 164 earlier tests on fx-majors over this period plus these 2 |

## Why this question

FLOW-1 asked whether the 4 pm fix's own move reverses, and it did not. MEH-1 asks the question Melvin & Prins (2015,
"Equity hedging and exchange rates at the London 4 p.m. fix", Journal of Financial Markets) put:

- Investors who hold foreign equities and hedge the currency must re-hedge at month-end, when their holdings' value
  has changed. Much of that is executed at the fix.
- When US equities have beaten a market over the month, foreign holders of US equities must sell more dollars than
  that market's US holders must buy back. So the dollar should weaken into the fix, and the reverse when US equities
  trailed.
- The mechanism is institutional and still in place. It does not depend on a price pattern recurring by chance.

## The rule (fixed; nothing is tuned)

- **When.** On the last weekday of each month (T), for each of EURUSD, GBPUSD, AUDUSD, NZDUSD, USDJPY, USDCHF and
  USDCAD.
- **Signal.** D is the S&P 500's return minus the pair's home index's return (Euro Stoxx 50, FTSE 100, S&P/ASX 200,
  NZX 50, Nikkei 225, SMI, S&P/TSX), each in its own currency. It runs from the last close of the previous month to
  the last close before T, so no close of T itself is read.
- **Side.**
  - D > 0: the dollar should weaken, so buy EUR, GBP, AUD and NZD against it, and sell USD against JPY, CHF and CAD.
  - D < 0: the reverse.
  - D = 0, or an index missing a close within a week of the previous month's end: no trade for that pair.
- **H1:** enter at 13:00 London, exit at 16:00 London (the fix). **H2:** enter at 15:00 London, exit at 16:00.
- **Prices and costs.** These are FLOW-1's. Each fill is at the bar's open bid/ask with 0.1 pip of slippage, plus
  0.7 pip of commission a round trip. A missing bar is no trade.
- **The observation.** One month-end is one observation: the mean net bps across its pairs, which must number at
  least 4. The pairs share the dollar leg.

## Periods

| Role | Period |
|---|---|
| Development | 2009-01 → 2012-12 (48 month-ends) |
| Validation | 2013-01 → 2016-12 (48 month-ends) |
| Judged (significance) | 2009-01 → 2016-12 |
| Sealed holdout | 2017-01 → 2018-05 (the fx-majors holdout). Opened once, only for a passer, through the registry's final-test procedure |

## Gates (all required, per hypothesis)

| Gate | |
|---|---|
| t | t of the mean net bps over 2009-2016 ≥ 3.61 |
| development | mean net > 0 in 2009-2012 |
| validation | mean net > 0 in 2013-2016 |
| years | ≥ 60% of the years have positive net |
| costs ×2 | mean net > 0 with spread, slippage and commission all doubled |
| top year | no single year supplies more than 50% of the total net |
| leave one pair out | mean net > 0 leaving out any one pair |
| specificity | the month-end mean exceeds the same rule on every other weekday of the month (Welch t ≥ 2): it must be a month-end flow, not an every-day equity-to-FX effect |

**Holdout rule** (a passer only): over 2017-01 → 2018-05, mean net > 0, and mean net > 0 with costs ×2.

## After the result

- **A passer, validated on the holdout.** It is proposed to the owner as a paper strategy of its own (CLAUDE.md
  rule 14). The risk engine sizes it, and it is followed forward on paper. Never real money.
- **Anything else.** It is reported as it is. Nothing changes.

## Known before freezing, said now

- **Power.** 96 month-ends is a small sample for t ≥ 3.61, which needs a month-end Sharpe of about 0.37. A real but
  modest flow may well fail here, and that would be reported as it is.
- **The fix changed in February 2015.** Its window widened from one minute to five, inside the validation period.
  That is a reason the effect could differ between the halves, not an excuse if it does.
- **The calendar.** Weekdays only: UK holidays at a month-end (the late-May bank holiday) are not removed, as in
  FLOW-1. The fix is still published on those days.

## Result (run 2026-11-04; `research/knowledge/MEH-1.json`)

**FAILED.** Neither hypothesis passed its gates, so the sealed holdout stays sealed and nothing changes.

- The index closes were fetched on GitHub's runner (branch `meh1-data`, `60e16c6`). All eight series ran from
  2008-01 to 2026-11, and every file matched its manifest sha256.
- The judge read 96 month-ends, 2009-01 to 2016-12.

| | H1: 13:00 → 16:00 London | H2: 15:00 → 16:00 London |
|---|---|---|
| Gross, mean bps a month-end (t) | +0.10 (0.05) | **+3.29 (2.86)** |
| Costs, mean bps | 2.00 | 2.10 |
| Net, mean bps (t) | −1.90 (−0.99) | +1.19 (**1.04**) |
| Development / validation, net | −0.99 / −2.81 | +1.71 / +0.67 |
| Costs ×2, net | −3.90 | −0.91 |
| The same rule on every other weekday (placebo), net | −2.30 | −1.92 |
| Specificity, Welch t | 0.21 | 2.67 |
| Failed gates | all eight | t, costs ×2, top year |

**What it means, and no more.**

- **In the last hour into the fix there is a month-end move in the direction the hedging flow predicts.** It is
  +3.3 bps gross, it is specific to month-end (Welch t 2.67 against the other weekdays), and it appears in both
  halves. That is consistent with Melvin & Prins.
- **It is not a trade.** The spread, slippage and commission take 2.1 bps of it. What is left, +1.2 bps, is far
  from the registered t of 3.61, and it turns negative when costs double.
- **The three hours from 13:00 show nothing.** If the flow exists, it is in the last hour.
- This is the project's recurring finding: a gross effect too small for retail costs. A desk paying less than about
  1 bp a round trip might see it differently, but this one does not.
