# DAY-1: the 2-day RSI pullback in an uptrend, on the four index CFDs, at a swap-free account's costs

**Pre-registered 2026-11-08, before any DAY-1 outcome was computed.** Frozen spec sha256
`60f0cb404472bda539469bd75e4e6cec3b32ab61f7795fbfae0c2bbebfaff21b`, code sha256
`952aecf70cc61d3caf7db8ed4e968d02fc98348a9f4f8ce164aa96f6f0a3442f` (`scripts/day1.py`,
`research/specs/DAY-1.json`). Threshold t ≥ **3.3879**, counting every earlier test on index or US equity data,
intraday ones included.

## Why

- **The owner, 2026-11-08:** "$4,000 a month; trades so I see the account moving; more profit than loss; make it
  happen."
- **What TRND-1 does:** it is validated and traded by the trend desk, but it trades a few times a year. On the desk's
  own replay (2004-2026) it made about 3.4% a year on $200,000.
- **The question here:** does a published short-term rule trade several times a month on the same four index CFDs,
  and earn a positive net return after costs, on years it was not published from?

## The rule (Connors & Alvarez, *Short Term Trading Strategies That Work*, 2009)

For each index separately:

- **Uptrend:** the close is above the mean of the last 200 closes, that one included.
- **Buy:** flat, in an uptrend, and the 2-day RSI (Wilder's) below 10. Buy at that close.
- **Sell:**
  - at the first close above the mean of the last 5 closes;
  - at the latest, at the 10th close after the entry;
  - at a protective stop 6% below the entry close, hit by a day's low. A day that opens below the stop fills at the
    open. The stop is the bot's own one-day stop.
- **Positions:** one per index; long or flat, never short. A signal is acted on only at the close it appears.
- **Costs:** 0.05% at each fill (spread, slippage and commission). No financing (swap-free). Price indices, so no
  dividends.

The thresholds (200, 2, 10, 5, 10 days) are the published ones. None was chosen here, and no other version will be run
on these years.

## The test

| | |
|---|---|
| Instruments | ^GSPC, ^NDX, ^GDAXI, ^FTSE (the US 500, US Tech 100, GER 40 and UK 100 CFDs), Yahoo daily open, high, low and close from 1988-06 |
| Basket | A quarter of the capital per index while it holds a trade. The daily return is the mean of the four indices' daily strategy returns; an index without a bar that day counts 0 |
| Statistic | t of the basket's mean daily net return, 1990-01-01..2020-12-31 |
| Development / validation | 1990..2005 / 2006..2020 |
| Gates | complete (each index has bars from before 1989-06 through 2020-12); t ≥ 3.3879; development mean > 0; validation mean > 0; costs doubled mean > 0; no year more than 50% of the total |
| Holdout | 2021-01..2026-09, opened once and only if the judge PASSED. Mean daily net return > 0, and > 0 with the cost doubled; its t is reported, and the registry validates it only at t ≥ 2.5 |

## What was read before

- **These index years are not untouched.**
  - RC-EQ (1990-2020) judged other rules on index CFDs.
  - TRND-1-H read the month-end closes of 2021-2026.
  - The trend desk's replay ran TRND-1's monthly rule over 2004-2026.
- **No test here has computed a short-term rule on them.** That is why the threshold counts every earlier test on this
  data.

## The power check, made before building

The published post-2007 out-of-sample figures for this family range widely: 0.25-0.69% a trade over 2007-2009 (CXO
Advisory), and about 0.26% a trade on the S&P 500 over 2016-2026.

| | |
|---|---|
| Expected activity | about 12 trades a year per index, about 4 days each |
| At +0.26% a trade net | the basket reaches about t 2.6 over 31 years |
| At +0.4% a trade | about t 4 |

**Chance of passing:** roughly one in three if the effect is near its published size, less if it has decayed.

This is built because the owner asked for an active rule, and because at its published size it can pass.

## Islamic notes

- Long or flat: no short sale.
- No interest-bearing instrument.
- No financing in a swap-free account.

## After the verdict

- **PASSED, and VALIDATED on its holdout:** it is built as a paper desk of its own (CLAUDE.md rule 14) on the four
  index CFDs, sized by the risk engine and followed forward on paper; never real money. The owner's word of
  2026-11-08 covers this.
- **Otherwise:** it is reported as it is, and nothing changes.

## Result (2026-11-08): FAILED, on t alone

Judged once on GitHub's runner (`research/knowledge/DAY-1.json`, `research/results/day1-judge.log`). The holdout
stays unread.

| | |
|---|---|
| 1990..2020 | +1.81% a year on the basket, t **2.48** against the bar of 3.3879 |
| Development, 1990..2005 | +3.01% a year, t 3.02 |
| Validation, 2006..2020 | +0.52% a year, t 0.49 |
| Costs doubled | +1.06% a year |
| Trades | 941: 69.6% won, +0.24% a trade net on average. 879 closed at the 5-day mean, 53 at the stop, 9 at the 10th close |
| Losing years | 13 of 31; worst fall 13.5%; no year more than 19% of the total |

**What it says:**

- The published rule did what it is known for: about seven trades in ten won.
- Its profit was in 1990-2005, and after 2006 it was nearly gone (t 0.49). That is the decay that follows
  publication, which the same rule on more indices or other thresholds would not undo.
- It is not run again on these years.
