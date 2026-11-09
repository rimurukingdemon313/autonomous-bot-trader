# FXS-1: the time-of-day effect in FX (home currencies weaken in their own working hours)

**Pre-registered 2026-11-09, before any FXS-1 outcome was computed.**

| | |
|---|---|
| Frozen spec | `research/specs/FXS-1.json`, sha256 `f5b338b51ee5fc1ea00bd90af57c42284ff3ce92460b51252b0953a31de81bea` |
| Code | `scripts/fxs1.py`, sha256 `3c2ad2321658917fb975713232b4b3d4608207f67f1a8179e2b352b38942bded` |
| Threshold | t ≥ **3.6158**: Bonferroni over every test the registry records on fx-majors in 2009-2016, plus this one |

## Why

- **The mission.** The owner's FX mission of 2026-11-09 (`docs/FX_MISSION.md`): find a Forex edge that survives
  rigorous out-of-sample testing at realistic costs, or say that none was found.
- **The finding behind the test.** Ranaldo (2009, *Journal of Banking & Finance*) found that a currency tends to
  depreciate during its own country's working hours and to appreciate during foreign working hours. Breedon &
  Ranaldo (2013, *Journal of Money, Credit and Banking*) found the same pattern across currencies and time zones,
  and in order flow. They read it as people buying foreign currency in their own working hours. Their working paper
  describes a simple profitable EUR/USD strategy.
- **Not a repeat.** Earlier session rules here were price patterns at a session's open: ID-1 B6, QT-1 T2/T3 and
  FLOW-1's fix. Session time was one input among many in ID-2's model (IC ≤ 0.07 alone). No test here has held a pair
  through the hours in which this hypothesis says its direction.

## The rule

FXS-1 holds each pair only in the hours where the hypothesis says which way it moves. Otherwise it is flat.

| Window | Opens | Closes | Trades |
|---|---|---|---|
| TOKYO | 09:00 Tokyo | 08:00 London | buy USDJPY (the yen weakens in Tokyo's hours) |
| EUROPE | 08:00 London | 08:00 New York | sell EURUSD, sell GBPUSD, buy USDCHF (Europe's currencies weaken in Europe's hours) |
| US | 17:00 London | 16:00 New York | buy EURUSD, buy GBPUSD, sell USDCHF, sell USDJPY (the dollar weakens in America's hours) |

- **Overlap and night.** The hours when both Europe and New York work, and the night after 16:00 New York, carry no
  prediction, so nothing is held.
- **The clock.** Every edge is in that city's own time on that date, daylight saving included. The clock is the only
  input: no price decides a trade.
- **Execution.** A market order at the open of the first M5 bar at or after a window opens, reversed at the open of
  the first bar at or after it closes. A window is skipped if either bar opens more than 10 minutes late, or if a
  data gap of over an hour falls inside it. Monday to Friday only.
- **The weekend and the rollover.** Nothing is held over a weekend or through 17:00 New York. So a standard account
  and a swap-free account pay and earn no swap on these trades.

## Data and costs

| | |
|---|---|
| Bars | `data/m5/*_M5_2009_2016.npz`: Dukascopy bid and ask, M5, through `scripts/id1.py`'s loader, which refuses 2017 on |
| Spread | the bars' own bid and ask at entry and at exit: variable, measured, news hours included |
| Commission | 0.7 pip a round trip (about $7 a standard lot; ID-1's value) |
| Slippage | 0.1 pip a fill |
| Stress | spread, commission and slippage all x1.5 and x2 |
| Delay | the whole book again with every entry and exit one bar (5 minutes) late |

## The test

| | |
|---|---|
| Statistic | t of the book's mean daily net, 2009-01-01..2016-12-31. The book holds one unit of notional per trade; a day's net is the sum of its trades' net in basis points |
| Development / validation | 2009-2013 / 2014-2016: the rule has nothing to fit, so both are consistency gates |
| Random control | the same trades with random sides (seeds 11, 12, 13): the same cost, no direction |
| Uncertainty | a 95% bootstrap interval of the mean daily net, resampling whole calendar months, 10,000 draws |

**Gates (all required):**

1. Daily net t ≥ 3.6158.
2. Mean daily net > 0 in development, and > 0 in validation.
3. Mean daily net > 0 at costs x1.5. Costs x2 are reported.
4. The net per trade beats the random-side control by a Welch t of 2.0 or more.
5. At least 3 of the 4 pairs are net positive.
6. No calendar year holds more than 50% of the total net.
7. The bootstrap interval lies above zero.
8. The trade-level profit factor is 1.10 or more.
9. Mean daily net > 0 with one bar of delay.

## What was read before

- **2009-2016 is this project's most-read FX data.** Each of those years was read by 141 to 164 earlier tests, which
  is why the threshold counts them. ID-2 read session time as a model input on these bars.
- **No FXS-1 outcome was computed before this freeze.** The papers' own tables could not be read from this
  workspace (their hosts are outside its network), so no published size is assumed.

## Power, stated before the test

| | |
|---|---|
| A round trip on these pairs | about 1.2-1.6 bp of notional: spread, two slippages and the commission |
| To reach the bar | the hypothesis's move must average roughly 2.5 bp or more per window and pair, in the predicted direction |
| Gross 2 bp | t about 2 |
| Gross 1.5 bp | t about 0.6 |

**Chance of passing:** unknown, and probably low. ID-2's session input carried little information on these bars.

## The holdout

Only if every gate passes: fx-majors 2017-01-01..2022-07-09, with M5 bars built only then through ID-1's holdout
procedure, opened once as FXS-1-H.

- **Gates:** daily net t ≥ 1.645 (one-sided 5%), mean daily net > 0, and mean > 0 at costs x1.5.
- **VALIDATED:** the edge registry calls it validated only at a holdout t of 2.5 or more.

## After the verdict

- **FAILED:** it is recorded as it is, and nothing changes.
- **PASSED:** the holdout above, once.
- **Never:** whatever the result, nothing reaches production, live execution or the risk settings within this
  mission. A validated rule would be a paper candidate under CLAUDE.md rule 14, never real money.
