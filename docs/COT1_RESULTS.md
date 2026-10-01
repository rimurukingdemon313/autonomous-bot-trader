# COT-1 results: does CFTC positioning add directional information to FX? — FAILED

| | |
|---|---|
| Preregistration | [research/preregistrations/COT-1.md](../research/preregistrations/COT-1.md), committed in `a3201c9` before any outcome was computed |
| Spec | sha256 `0d850397…2054e` |
| Code | sha256 `1843a078…55c2` |
| Verdicts and every number below | `research/knowledge/COT-1.json` |
| Judged period | 2008-07-11 → 2016-01-01, once; development 2008-07 → 2014 and validation 2014 → 2016 reported separately |
| Costs | standard D1 costs |
| Exit | D3 (one week, 2 × ATR stop) |
| Standard | the full battery, the preregistered gates, and **t ≥ 3.4136** (67 earlier tests + 11) |

All figures are in R per trade, net of costs, unless marked gross. "t" is the clustered t (by week).

## Verdict

**11 hypotheses tested. 11 REJECTED. 0 PROMISING. 0 VALIDATED.**

- No hypothesis reached PROMISING, so the 2016 confirmation was **not computed**, as preregistered.
- The sealed 2017 holdout was **not opened**. It remains available for a future candidate.

## Results (judged period)

| ID | n | Win % | Avg win / loss | Gross | Cost | **Net** | t | PF | Max DD (R) | Total R | Dev | Val | vs its price control | Without top 5 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| P-REV (against extreme) | 915 | 45.6 | 0.56 / −0.59 | −0.016 | 0.047 | **−0.063** | −1.97 | 0.80 | 65.9 | −57.2 | −0.056 | −0.081 | +0.007 | −0.087 |
| P-CONT (with extreme) | 912 | 48.4 | 0.58 / −0.56 | +0.036 | 0.048 | **−0.011** | −0.35 | 0.96 | 45.9 | −10.2 | −0.030 | +0.041 | +0.006 | −0.026 |
| C-REV (COT + price extreme, against) | 410 | 42.7 | 0.65 / −0.62 | −0.035 | 0.045 | **−0.081** | −1.59 | 0.77 | 37.3 | −33.0 | −0.077 | −0.088 | −0.011 | −0.135 |
| C-CONT (COT + price extreme, with) | 409 | 52.1 | 0.59 / −0.60 | +0.063 | 0.046 | **+0.017** | 0.37 | 1.06 | 19.5 | +7.0 | −0.007 | +0.072 | **+0.034** | −0.009 |
| I-REV (COT extreme, price not, against) | 505 | 47.9 | 0.50 / −0.56 | 0.000 | 0.048 | **−0.048** | −1.34 | 0.84 | 33.8 | −24.2 | −0.040 | −0.075 | +0.022 | −0.068 |
| I-CONT (COT extreme, price not, with) | 504 | 45.2 | 0.57 / −0.53 | +0.012 | 0.048 | **−0.036** | −0.95 | 0.88 | 34.3 | −18.2 | −0.047 | −0.001 | −0.019 | −0.062 |
| F-CONT (4-week flow, with) | 575 | 43.7 | 0.56 / −0.57 | −0.031 | 0.047 | **−0.077** | −2.09 | 0.76 | 55.1 | −44.5 | −0.073 | −0.099 | −0.073 | −0.096 |
| F-REV (4-week flow, against) | 575 | 49.4 | 0.57 / −0.58 | +0.037 | 0.046 | **−0.010** | −0.25 | 0.97 | 28.8 | −5.6 | −0.027 | +0.068 | +0.051 | −0.035 |
| U-REV (unwind started) | 271 | 45.8 | 0.53 / −0.58 | −0.027 | 0.047 | **−0.074** | −1.46 | 0.77 | 23.9 | −20.0 | −0.022 | −0.235 | −0.004 | −0.115 |
| V-REV (extreme + VIX ≥ 20) | 421 | 45.1 | 0.58 / −0.61 | −0.025 | 0.045 | **−0.069** | −1.30 | 0.79 | 37.6 | −29.2 | −0.066 | −0.122 (n 26) | −0.010 | −0.099 |
| X-VETO (crowded trend trades lose) | 820 | 48.4 | 0.58 / −0.56 | +0.037 | 0.047 | −0.011 (claim +0.011) | 0.31 | 0.96 | 40.1 | −8.6 | +0.029 | −0.039 | +0.0002 | +0.004 |

**Robustness** (claim-signed mean R):

| ID | Neighbouring levels 0.85 / 0.95 | z-score definition | Costs ×2 | Delay one bar | Long / short the currency |
|---|---|---|---|---|---|
| P-REV | −0.073 / −0.086 | −0.076 | −0.109 | −0.087 | −0.097 / −0.016 |
| P-CONT | −0.004 / −0.013 | −0.009 | −0.063 | −0.032 | −0.083 / +0.042 |
| C-CONT | +0.013 / +0.077 | +0.004 | −0.036 | −0.014 | −0.059 / +0.060 |
| F-REV | −0.020 / −0.077 | −0.012 | −0.055 | −0.003 | −0.032 / +0.011 |
| X-VETO | +0.001 / +0.012 | +0.009 | +0.062 | +0.039 | — |

## Price-only, COT-only, price + COT

Same decision bars, entry, exit, costs and 1R throughout.

| Mapping | Segment | A: price only | B: COT only | C: price + COT | **B − A** | **C − A** |
|---|---|---|---|---|---|---|
| Reversal | development | −0.047 (735) | −0.056 (669) | −0.077 (284) | −0.008 | −0.030 |
| Reversal | validation | −0.116 (364) | −0.081 (246) | −0.088 (126) | +0.034 | +0.028 |
| Reversal | **judged** | −0.070 (1,099) | −0.063 (915) | −0.081 (410) | **+0.007** | **−0.011** |
| Continuation | development | −0.053 (734) | −0.030 (667) | −0.007 (283) | +0.023 | +0.046 |
| Continuation | validation | +0.054 (363) | +0.041 (245) | +0.072 (126) | −0.014 | +0.017 |
| Continuation | **judged** | −0.017 (1,097) | −0.011 (912) | +0.017 (409) | **+0.006** | **+0.034** |

**The incremental value of positioning is about zero.**

- COT alone beats the same rule on price by **+0.006 to +0.007R per trade**, about a fifth of one
  standard error (≈ 0.03R).
- The only increment that is positive in both development and validation is positioning as a
  **confirmation** of a price extreme, in the continuation direction (C-CONT − A-CONT: +0.046,
  +0.017, judged +0.034).
- But C-CONT itself is +0.017R net (t 0.37), and the board found it is carried by EURUSD (144% of
  its total R) and by 2008 (168%). Without them the rest earns −0.009 to −0.013R per trade.

**As a crowding filter on the 13-week trend it does nothing.**

| Trades | n | Net |
|---|---|---|
| All trend trades | 2,615 | −0.0098R |
| Uncrowded trend trades | 1,796 | −0.0096R |
| Crowded trend trades | 820 | −0.0105R |

## Walk-forward

**Fixed rules, year by year** (each year is out of sample; nothing is fitted):

- Only X-VETO's claim holds in at least 60% of its years (5 of 8), and its overall effect is
  +0.011R (t 0.31), no different from the uncrowded trend trades. Every other hypothesis fails the
  years check.
- The continuation rules (P-CONT, C-CONT, and the price-only A-CONT and A-TREND) are positive in
  **2008 and 2014**, the two strong USD-trend years, and negative in most of 2009–2013.
  - P-CONT: +0.22R in 2008 and +0.12R in 2014; −0.17R to +0.01R in the other years.

**Selection walk-forward** (descriptive): each year, trade the hypothesis that was best in all
earlier years. The choice flips four times.

| Year | Chosen | That year |
|---|---|---|
| 2010 | I-CONT | −0.091 |
| 2011 | C-CONT | −0.025 |
| 2012 | F-REV | −0.203 |
| 2013 | C-CONT | −0.097 |
| 2014 | C-CONT | +0.116 |
| 2015 | C-CONT | +0.022 |
| **Pooled** | | **−0.055R (n 401, t −1.29)** |

"Pick the best COT rule so far" loses.

## 2016 confirmation and the 2017 holdout

- **Not computed and not opened.** No hypothesis earned PROMISING, the preregistered condition for
  either.
- The sealed holdout is unspent.

## Why each was rejected

Every hypothesis failed significance (the best t is 0.37 against 3.414) and beats-random. Beyond
that:

| Hypothesis | Failed checks |
|---|---|
| P-REV, C-REV, I-REV, I-CONT, F-CONT, U-REV, V-REV | negative in development **and** validation; fail costs, delay, perturbation, years, instruments, leave-one-out, regimes, outliers and top-5 |
| P-CONT, F-REV | negative in development; negative under cost stress, delay and the neighbouring levels |
| C-CONT | negative in development; negative under cost stress and delay; negative without its 5 best trades; carried by EURUSD and 2008 |
| X-VETO | the crowded trend trades do not lose; their mean equals the uncrowded ones' |

## What the experiment taught

1. **TFF Leveraged Money positioning does not carry tradable directional information for the seven
   USD pairs at a one-week horizon, 2008–2015.**
   - The best gross edge is +0.063R. Costs per trade are 0.047R.
   - The best net is +0.017R (t 0.37).
   - With 900 trades, an edge of about 0.11R would have been needed to pass t ≥ 3.41, and about
     0.065R to reach PROMISING's t ≥ 2. None came close.
2. **Positioning mostly restates price.**
   - Speculators' extremes coincide with price extremes: 45% of the positioning extremes are also
     price extremes.
   - What is left over (I-*) carries nothing: −0.048 and −0.036.
   - COT over price adds about +0.007R.
   - This agrees with the documented finding that position changes move *with* the exchange rate in
     the same week (Klitgaard & Weir 2004): by the Monday after the report, the information is in
     the price.
3. **Direction.**
   - Level extremes lean toward continuation (−0.011 against −0.063 for reversal).
   - Flow extremes lean toward reversal (−0.010 against −0.077 for continuation).
   - Neither is significant. Both are mostly the USD trend of 2008 and 2014: short-the-currency
     trades earned +0.04 to +0.06R; long-the-currency trades lost.
4. **Crowding does not predict a stall.** Crowded trend trades perform exactly like uncrowded ones.
   As a veto or regime filter, positioning removes trades without improving the rest.
5. **Costs are the binding constraint at this horizon.**
   - A one-week D3 trade costs about 0.047R.
   - Every rule and control here, price-only included, has a gross edge between −0.035R and
     +0.063R.
   - A weekly signal needs a gross edge of about 0.1R just to clear costs and noise.

## What this means for the search

Positioning is **not** a directional signal, confirmation signal, regime filter or veto in this
form. It is recorded as REJECTED in the edge registry and in the strategy library
(SL-POSITIONING, library 1.3.0).

The only unexplained regularity is the small, consistent increment of positioning as a confirmation
of continuation (C-CONT − A-CONT positive in both development and validation). It is too small, too
concentrated and too far from significance to act on.

It may be retested only as a **new, preregistered** study on data COT-1 never judged:

- 2016 (COT-unseen);
- prospective weekly reports from now on.

The holdout opens only for a candidate that passes everything else first.

Directions this result argues for, each needing its own preregistration:

- **Longer horizons**, where the cost share is smaller (a 4-week D4 trade costs a fraction of a
  weekly one).
- **Cross-sectional positioning**: ranking currencies against each other instead of against their
  own history. This removes the USD factor that dominated every result here.

No position sizing, live system or risk-engine code was touched.
