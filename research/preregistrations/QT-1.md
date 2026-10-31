# QT-1: do the Quarters schools earn anything on M5 after real costs? (preregistration)

**Written, frozen and committed before any strategy outcome was computed.** The only real-data
computation before writing was signal **counts and run times** of each rule on EURUSD, 2009–2013.
No fill, return, R, win rate or P&L of any rule was computed.

| | |
|---|---|
| Frozen spec | `research/specs/QT-1.json` |
| Spec sha256 | `d4cbe656bbb0c7a08907673f6ee9859bde1a724849766558d57e390b88a8d46b` |
| Code | `aitrader/research/discovery/quarters.py` (qt-1.0.0), with ID-1's `intraday.py` (id-1.0.0) and `scripts/id1.py`, and `scripts/qt1.py` (all hashed in the spec: `7247efc8…a93`) |
| Data | ID-1's M5 bid/ask bars 2009–2016 (branch `id-data`), unchanged |
| Untouched test | The fx-majors holdout, 2017-01 on, stays sealed. A passer opens it only through ID-1's own `holdout` procedure, preregistered first |

## Why

The owner asked on 2026-10-30 why the bot lets a model read direction instead of using the
schools traders use, SMC and "Quarters". The SMC rules were tested in ID-1 and all of them lost
after costs (A1–A6). The Quarters schools had not been tested. Two schools share the name, so both
are tested, each as its teachers state it.

**Price quarters (Quarters Theory).**

- **The levels.** Quarter levels every 25 pips: 00, 25, 50, 75, or 0.25 yen on a JPY pair.
- **The claim.** Price moves from one quarter level to the next. It reverses at an untouched
  level, or runs to the next level once one breaks.
- **The academic version.** Osler (2000, 2003): take-profit orders cluster at round numbers,
  which causes reversals there. Stop-loss orders cluster just beyond them, which causes
  accelerations.

**Time quarters (the Quarterly Theory, taught alongside SMC/ICT).**

- **The cycle.** Every period has four quarters: accumulation, manipulation, distribution, then
  continuation or reversal (AMDX).
- **The day's quarters** are the 6-hour sessions from 18:00 New York: Asia, London, New York AM
  and New York PM.
- **The true open** is the open of the second quarter. For the day it is 00:00 New York. For a
  session it is the start of its second 90-minute quarter.
- **The trade.** The manipulation is a false move away from the true open, and the distribution
  runs the other way.

## The rules (five tests)

New York time follows the US daylight rules (second Sunday of March to first Sunday of
November). Every rule decides at a bar's close and enters at the next bar's open, or with a limit
order where stated.

### Q1-QUARTER-FADE (FX majors; gold has no pip grid)

At each bar's close, 07:00–20:00 UTC, Monday to Friday:

- **The levels considered.** The first quarter level above the trading day's high so far, and
  the first below its low so far. Both are untouched today by construction.
- **When an order is placed.** When the nearer of the two is within 12.5 pips of the close, a
  limit order rests at that level, against the approach, for 24 bars: a sell at the level above,
  a buy at the level below.
- **Stop and target.** Stop 12.5 pips beyond the level; target 2R from it.
- **Limits.** One order per level per day; time exit after 48 bars.

### Q2-QUARTER-BREAK (FX majors)

A bar (07:00–20:00 UTC) closes beyond a quarter level that the previous bar closed on the other
side of:

- **Entry.** Trade in the direction of the break at the next open.
- **Stop and target.** Stop 12.5 pips from the close; target 2R.
- **Limits.** The first break of each level in each direction per day; time exit after 48 bars.

### T1-DAILY-AMD (all eight instruments)

- **The quarters.** Asia (18:00–00:00 New York) accumulates a range. London (00:00–06:00)
  manipulates. New York AM (06:00–12:00) distributes.
- **The signal.** At the close of London's 05:55 bar, London traded beyond the Asian range on
  **one** side only, and closed on that side of the true day open (00:00 New York).
- **The trade.** Trade the other way at 06:00. Stop beyond London's extreme + 0.10 ATR; target
  2R; time exit at 12:00 New York.
- **Data needed.** Asia and London need 36 bars each.

### T2-NY-TRUE-OPEN (all eight)

- **The quarters.** The New York AM session's quarters: Q1 06:00–07:30 and Q2 07:30–09:00, with
  the true session open at 07:30.
- **The signal.** At the close of the 08:55 bar, Q2 ran beyond Q1's range on **one** side only
  and closed on that side of the true session open.
- **The trade.** Trade the other way at 09:00. Stop beyond Q2's extreme + 0.10 ATR; target 2R;
  time exit at 12:00 New York.
- **Data needed.** Each quarter needs 12 bars.

### T3-LONDON-TRUE-OPEN (all eight)

The same rule on the London session:

- the quarters are Q1 00:00–01:30 and Q2 01:30–03:00;
- the true session open is at 01:30;
- entry is at 03:00 and the time exit at 06:00 New York.

**Neighbourhood grid (validation robustness only).**

- **Q1 and Q2:** stop {10, 12.5, 15} pips × r {1.5, 2, 2.5}.
- **T1–T3:** buffer {0.05, 0.10, 0.20} ATR × r {1.5, 2, 2.5}.

**Declared before running.**

- **The missing hour.** Hour 00 UTC is missing for every pair except EURUSD (ID-1's audit), so
  the Asian range of T1 is formed from about 60 of its 72 bars on those pairs.
- **The large quarters.** The 250-pip large quarters are too rare on M5 to test here.

## What is reused from ID-1, unchanged

- **The engine.** The fill model, bid/ask on every bar, the costs (commission 0.7 pip round trip,
  slippage 0.1 pip per market fill, financing) and the production risk engine's entry checks.
- **The controls.** The matched-random control (3 seeds).
- **The periods.** Development 2009–2013; validation 2014–2016.

## Gates (ID-1's)

**Promotion, on development.** All of:

- at least 300 trades;
- net R > 0;
- t (daily) ≥ 2.0;
- profit factor ≥ 1.10;
- beats its matched random by Welch t ≥ 2.0;
- 60% of symbols positive.

**Pass, on validation, promoted rules only.** All of:

- t (daily) ≥ **3.5661**, the registry's Bonferroni over every test touching 2014–2016 plus these five;
- net R > 0;
- profit factor ≥ 1.20;
- net R > 0 at costs × 1.5;
- 60% of symbols positive;
- 60% of three-month windows profitable;
- beats matched random by t ≥ 2.0;
- 75% of the grid positive.

**After the result.**

- **No rule passes.** QT-1 is recorded FAILED and nothing about the bot changes.
- **A rule passes.** It is still not traded until the sealed holdout confirms it, through its
  own preregistration. A strategy that came out of a research run is never wired into the bot on
  development or validation numbers alone.
