# COT-1 — CFTC positioning as directional information for FX

**Preregistered before any outcome was computed.** The frozen, machine-readable design is
`research/specs/COT-1.json`, with spec sha256
`0d850397a5bbe4e5723d120d0e039585fa303bac516421380ffee1a37d72054e`. The code is frozen by the code
hash in the same file. `scripts/cot1.py run` refuses to run if either has changed.

**What was read before this was written:**

- the data audit ([docs/COT_DATA_AUDIT.md](../../docs/COT_DATA_AUDIT.md));
- a truncation (look-ahead) test of every feature and rule on 385 real decision rows, which found
  0 leaks;
- how many signals each rule produces per segment (`research/results/COT-1-event-counts.json`).

**No trade outcome, return or price move after a decision was computed.**

## Question

Does the positioning of speculators in the CME currency futures (CFTC TFF, Leveraged Money) predict
the direction of the seven direct USD pairs over the following week? It must do so:

- after costs;
- out of sample;
- adding something beyond a price-only rule that has the same timing, exit and costs.

The goal is to find out, **not to prove that COT works.** A rejection is an acceptable answer
(CLAUDE.md rule 8).

## Instruments

EURUSD, GBPUSD, AUDUSD and NZDUSD use the currency future as is: long the future means long the
pair. USDJPY, USDCHF and USDCAD use the currency future with the **sign inverted**: bullish JPY means
selling USDJPY.

Not used here:

- cross-rate futures (too sparse; see the audit);
- derived cross pairs, which would be a separate, separately preregistered extension.

## Data and timing (point in time)

- **Data:** CFTC TFF Futures-Only bulk files, verified against `data/cot/manifest.json` and loaded
  by `aitrader/data/cot.py`.
- **Release:** a report is used from **17:00 New York on the first weekday ≥ as-of + 6 days**.
- **2013 shutdown:** as-of 2013-10-01 → 2013-12-24 is dropped entirely. These reports are never
  dated by guess and never used as history.
- **Decision bar:** the first D1 bar (New York close) closing at or after the release. A report that
  is superseded before any bar closes makes no decision.
- **No interpolation and no future data.** The truncation test is part of `scripts/cot1.py draft`
  and of the unit tests (`tests/unit/test_cot_study.py`). Those tests include a planted look-ahead
  that the check must catch.

## Positioning definition, lookback and normalisation

| Item | Definition |
|---|---|
| Positioning (`spec`) | (Leveraged Money long − Leveraged Money short) / open interest. Spreads are excluded. Signed so that + is bullish the currency |
| Lookback | **52 weeks, frozen**: the reports whose as-of falls in [as-of − 364 days, as-of). At least 39 reports are required, otherwise the value is unknown (NaN), never a default. No other lookback is tested here |
| Normalisation | Percentile rank among those reports, with ties counting half. A z-score against the same window is reported only as a robustness variant |
| Extreme | Percentile **≥ 0.90** (bullish) or **≤ 0.10** (bearish). Fixed |
| Flow | `spec` minus `spec` of the report 25–31 days earlier (4 weeks), as a percentile in the same window |
| Step | `spec` minus `spec` of the report 4–10 days earlier (1 week) |
| Price features | The currency's log value in USD at the decision bar; its 4-week change; its 13-week (65 D1 bars) trend. Sampled on the **same weekly decision bars** as the positioning |
| Volatility | VIX close public at the decision bar. VIX ≥ 20 is "stress" |

TFF has no "commercial / non-commercial" split; those are categories of the legacy report.

- The speculator category is **Leveraged Money**.
- Dealer and Asset Manager net positions are computed and reported descriptively. They are not
  tested here.

## Hypotheses: 11 judged tests, counted in the registry

Each rule gives a **currency direction**; the pair's side is that direction times the pair's
orientation. All are one-week trades with the same exit.

| ID | Family | Rule | Price-only control |
|---|---|---|---|
| COT1-P-REV | primary | `spec` at an extreme → trade **against** it | A-REV |
| COT1-P-CONT | primary | `spec` at an extreme → trade **with** it | A-CONT |
| COT1-C-REV | price + COT | `spec` **and** price at a same-side extreme → against | A-REV |
| COT1-C-CONT | price + COT | the same → with | A-CONT |
| COT1-I-REV | COT beyond price | `spec` at an extreme, price **not** at the same-side extreme → against `spec` | A-REV |
| COT1-I-CONT | COT beyond price | the same → with `spec` | A-CONT |
| COT1-F-CONT | flow | flow at an extreme → with the flow | AF-CONT |
| COT1-F-REV | flow | flow at an extreme → against the flow | AF-REV |
| COT1-U-REV | unwind | `spec` at an extreme **and** last week's step points back → against `spec` | A-REV |
| COT1-V-REV | volatility regime | `spec` at an extreme **and** VIX ≥ 20 → against `spec` | AV-REV |
| COT1-X-VETO | filter (veto) | the 13-week trend trade where `spec` is already extreme **in the trend's direction** **loses** (claim judged on −R) | A-TREND vs A-TREND-UNCROWDED |

**Both mappings, not one.** The primary hypothesis is tested with BOTH mappings, continuation and
reversal, because neither is assumed. They are exact mirrors before costs. The same holds for
price + COT, for COT beyond price, and for flow.

**Price-only controls.** The controls are not hypotheses, cannot be promoted and are not counted.
Every rule and every control requires `spec` to be defined, so they share **one decision set**.

| Control | Rule |
|---|---|
| A-REV / A-CONT | price at a 52-week extreme, against / with |
| AF-CONT / AF-REV | 4-week price change at a 52-week extreme |
| AV-REV | price extreme with VIX ≥ 20, against |
| A-TREND | the sign of the 13-week trend at every decision |
| A-TREND-UNCROWDED | A-TREND minus the crowded decisions |

**A/B/C comparison:**

- A (price only) = A-REV / A-CONT;
- B (COT only) = P-REV / P-CONT;
- C (price + COT) = C-REV / C-CONT.

All three share the decision bars, entry, exit, costs and risk unit.

**Signal counts before any outcome** (signals, not trades):

| Rule | Development | Validation | Judged |
|---|---|---|---|
| P-* | 670 | 246 | 916 |
| C-* | 285 | 126 | 411 |
| I-* | 385 | 120 | 505 |
| F-* | 470 | 106 | 576 |
| U-REV | 205 | 66 | 271 |
| V-REV | 396 | **26** | 422 |
| X-VETO | 606 | 217 | 823 |

V-REV has few validation signals because VIX was rarely ≥ 20 in 2014–2015. Its validation gate is
therefore weak, and this is stated now, not discovered later.

## Entry, exit, stop and costs

- **Entry:** market order at the open of the bar after the decision bar, which is the decision
  bar's close.
- **Exit:** **D3** from the existing exit menu.
  - Time exit after 5 D1 bars, which is the next decision bar's close.
  - Protective stop at 2.0 × ATR24(D1).
  - No target.
  - **1R = the stop distance.**
- **Fills:** the shared simulator's pessimistic fills (bid/ask, stop checked first, gap fills at
  the open).
- **Positions:** one per pair at a time, across both sides.
- **Sizing:** no size anywhere; sizing is the Risk Engine's alone.
- **Costs:** the standard D1 model.
  - The measured spread.
  - 0.1 pip of slippage per fill.
  - 0.7 pip of commission per round trip.
  - Swap of 0.01 × ATR24(D1) per night.

## Periods (strict chronology, never shuffled)

| Segment | Period | Role |
|---|---|---|
| Fit | 2007-04-02 → 2008-07-01 | er120 / vol_ratio regime medians only. Nothing else is estimated |
| Development | 2008-07-11 → 2014-01-01 | Reported separately; gate |
| Validation | 2014-01-01 → 2016-01-01 | Reported separately; gate |
| Judged | 2008-07-11 → 2016-01-01 | The battery and the significance test |
| 2016 confirmation | 2016-01-01 → 2017-01-01 | **Computed only for a PROMISING-or-better hypothesis** |
| Sealed holdout | 2017-01-01 → 2018-01-01 | **Opened only for ONE hypothesis that passed everything else** |

**Purging.** Segments purge every decision whose 5-bar outcome would cross the segment's end.

**Walk-forward.** Nothing is fitted, so each calendar year is an out-of-sample fold of a fixed rule
(the battery's years check). A walk-forward of **selection** is reported **descriptively**:

- In each year 2010–2015, trade the opportunity hypothesis with the best mean over all earlier years
  (≥ 30 trades).
- This shows whether "pick the best COT rule so far" would have worked. No verdict depends on it.

### The holdout, and why 2016 and 2017 are treated differently

The request defines 2016–2017 as the untouched holdout. The project's frozen protocol
(`docs/RESEARCH_PROTOCOL.md` §2) seals **2017 onward** as single-use:

> one pre-registered final test of one candidate that passed everything else

This study obeys both:

- **2016** has never been used for positioning, and it lies outside the seal. It is the
  confirmation year for any hypothesis that earns PROMISING or better.
- **2017** is opened, by the separate command `scripts/cot1.py holdout` that spends the single-use
  key, only for the single best hypothesis that passed everything else.
- A merely PROMISING hypothesis **never** opens 2017.
- **Not opening the holdout for a failed hypothesis is the point:** it stays available for a
  future edge.

## Statistical standard

**Significance.** The clustered t (by week of entry) on the judged period must be
**≥ 3.4136**.

- This is Bonferroni at 5% over the 67 earlier registry tests on these outcomes plus these 11
  (`registry.threshold_for_next`).
- It is unchanged from every round. It is not lowered.

**The battery.** All twelve existing checks apply, unchanged:

- `min_trades` ≥ 100;
- `significance`;
- `beats_random`: Welch t ≥ 2 against random entries that take random sides;
- `permutation`;
- `costs_stress`;
- `delay_stress`;
- `perturbation`: here, the **neighbouring levels** 0.85/0.15 and 0.95/0.05, which must both stay
  positive;
- `years`;
- `instruments`;
- `leave_one_out`;
- `regimes`;
- `outliers`.

**Additional preregistered gates.** Each gate is marked `gate: true`. A failed gate blocks
PROMISING as well as VALIDATED (`edges.judged_status`, edges 1.3.0).

| Gate | Requirement |
|---|---|
| development | claim-signed mean R > 0 on 2008-07 → 2014 |
| validation | mean R > 0 on 2014 → 2016 |
| incremental | the judged mean minus the declared price-only control's judged mean > 0. For the veto: A-TREND-UNCROWDED's mean minus A-TREND's mean > 0 |
| top5_removed | judged mean > 0 without the 5 best trades |
| confirmation_2016 | (only when computed) 2016 mean > 0, and > 0 under the cost stress |

**The board.** The 5-analyst board can only subtract.

## Statuses

**PROMISING** requires all of the following. It is a near miss worth a fresh test, **never a
trading rule**.

- judged mean > 0;
- t ≥ 2.0;
- the cost stress and beats-random checks pass;
- every gate passes;
- the 2016 confirmation passes.

**VALIDATED** requires, in this order:

1. every battery check at t ≥ 3.4136;
2. no blocking board objection;
3. every gate;
4. the 2016 confirmation;
5. then the sealed holdout: 2016–2017 pooled mean > 0 with clustered t ≥ 1.645, the 2017 mean
   alone > 0, and the 2016–2017 mean > 0 under the cost stress.

**REJECTED** is everything else, with the failing checks named.

Even VALIDATED is research evidence. Promotion to paper or demo is a person's decision
(`RESEARCH_PROTOCOL.md` §9). Live money is never enabled.

## Robustness reported for every hypothesis

**Gating checks:**

- neighbouring levels;
- delay;
- cost stress;
- without the 5 best trades;
- years, instruments, leave-one-out, regimes and outliers.

**Reported descriptively:**

- the z-score definition at the normal quantiles of the same levels;
- bullish vs bearish extremes (long vs short the currency);
- costs ×2 (spread ×2, slippage ×4, commission and swap ×2);
- without the single best trade.

## Metrics reported

For every hypothesis and control, per segment:

- trades, win rate, average win and loss;
- expectancy in R, total R (net return at 1R per trade);
- profit factor, maximum drawdown;
- per-trade Sharpe, clustered t;
- gross vs net and cost per trade;
- results by instrument, by year and by regime.

Also reported:

- the incremental value of each COT rule over its price-only control;
- the A/B/C table.

## What would change the plan

**Nothing, once this is committed.** A different lookback, levels, exit, pair set or derived
crosses is a **new, separately preregistered study** with new ids. It is charged against the
registry like any other.

Not tested here:

- asset-manager and dealer positioning as signals;
- relative currency strength;
- positioning acceleration;
- position sizing, which belongs to the Risk Engine.
