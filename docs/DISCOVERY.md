# The discovery engine

`aitrader/research/discovery/` turns market data into knowledge that has been **accepted or
rejected under statistical control**, and records both. It is research only. Nothing that
trades imports it, and a VALIDATED hypothesis is a finding, not a rule. The
`tests/unit/test_architecture.py` tests check this in the import graph.

```
MARKET DATA ─► FEATURES (catalog, leakage gate) ─► PATTERNS (bounded screen, BH-FDR)
   ─► HYPOTHESES (ledger: DRAFT) ─► REGISTRATION (registry trial, frozen threshold, document)
   ─► VALIDATION (every declared exit; the model family) ─► CONFIRMATION (12-check battery)
   ─► RESEARCH BOARD (5 analysts, no vote, can only subtract) ─► VALIDATED / REJECTED
   ─► KNOWLEDGE (research/knowledge) ─► NEXT HYPOTHESES (follow-ups, lessons, LLM drafts)
   ─► CONFIRMATORY PROGRAM ─► …
```

| Step | Module | What it guarantees |
|---|---|---|
| Features | `primitives.py`, `catalog.py`, `universe.py` | 12 new causal features on dimensions production lacks. Each of the 35 features used carries a record: definition, timeframe, required data, provenance, version, point-in-time rule, the question it answers, leakage status, experiments and results. A per-program budget applies. Only a feature that passed the truncation test (every input, **other instruments included**, cut at the decision bar) can be used. |
| Exits | `exits.py` | A declared menu of 8 exits: barrier ×3, time, trailing, breakeven, partial and structure. Fills are pessimistic: stop first, gaps fill at the open, and dynamic stops move at the close. E1 and E2 reproduce the existing T1/T2 labels exactly. |
| Study | `study.py` | Three chronological segments. An outcome never straddles two of them: purge plus embargo. Terciles are fitted on discovery rows only and frozen. There is one position per instrument per hypothesis, so overlapping signals are not extra trades. |
| Patterns | `screen.py`, `stats.py` | A declared grid of single bins and state×trigger pairs, both sides. **Every** cell is a test: a cell too small to judge gets p = 1 and is still counted. Standard errors are clustered by week. Benjamini–Hochberg is applied over all cells. |
| Hypotheses | `hypothesis.py` | See "Hypotheses" below. |
| Validation | `battery.py` | 12 checks; see "Validation" below. The deflated Sharpe ratio is reported for information. |
| Board | `board.py` | market, opportunity, risk, adversarial, and an **independent reviewer** that recomputes n, mean and clustered t from the raw trades with its own code. It also checks segment bounds, overlaps, the declared exit, the frozen threshold and the preregistration hash. There is no vote. A blocking objection turns VALIDATED into REJECTED, and nothing turns REJECTED into VALIDATED. A language model may add objections; it cannot approve anything. |
| Programs | `program.py`, `confirm.py` | See "Programs" below. |

## Hypotheses

A hypothesis is a complete, falsifiable object. Its fields are:

- statement, rationale and conjectured mechanism;
- features, as catalog ids;
- condition, side, instruments and timeframe;
- entry, exit and risk definitions;
- expected effect and falsification criteria;
- a budget of configurations;
- origin, program and parent.

It never carries a size: risk is always "1R = the exit's initial stop distance; the size is the
Risk Engine's alone".

The ledger is append-only. Its lifecycle:

```
DRAFT → PREREGISTERED → RUNNING → COMPLETED → VALIDATED | REJECTED | SHELVED
```

A rejected idea stays searchable. Its **substance**, meaning condition, side, exit, instruments,
timeframe and kind (whatever the wording), cannot be drafted again as new. The only exception is
a prospective retest that names it as its parent.

Sources of hypotheses:

- **the screen**, from observations on the discovery segment;
- **the model family**;
- **live lessons**, via `from_lesson`. These become veto hypotheses, translated approximately,
  and the rationale says so;
- **follow-ups** via `derive_next`, derived from *how* an idea failed. There are none when the
  core claim failed, and they are always prospective;
- **a language model**, via `llm_drafts`. It must use the closed vocabulary, is never repaired,
  and is always prospective, because every bar of history predates its training cutoff.

## Validation

A hypothesis is VALIDATED only if all 12 checks pass:

- enough trades;
- clustered t at or above the **registry's** Bonferroni threshold, which counts every earlier
  test on the judged period;
- it beats random entries;
- a circular-shift permutation test;
- cost stress: spread ×1.5, slippage ×2, commission and swap ×1.5;
- a one-bar delay;
- tercile edges moved by ±0.05 quantile;
- years;
- instruments;
- leave-one-instrument-out;
- regime cells (er120 × vol_ratio);
- outlier dependence.

A veto is judged on −R.

The same module decomposes the expectancy into:

- win rate, average win and average loss;
- profit factor and drawdown in R;
- losing streaks;
- MFE, MAE and holding time;
- costs versus gross;
- exit reasons;
- results by instrument, year, session and regime.

## Programs

`program.py` runs a **discovery program**:

- `preregister()` writes the catalog, runs the leakage test on real bars, registers the trial
  with fit, select and judge roles, and writes the document. It reads no outcome.
- `run()` refuses to run twice, and refuses if the design hash or the code hash differs from the
  registration.
- A run is deterministic, so a replay produces identical bytes. It is resumable: an interrupted
  run reaches the same result.

`confirm.py` runs a **confirmatory program**. It judges hypotheses that already exist, from any
source. Each must name one exit. A prospective hypothesis is refused on data older than itself.

## Multiple testing: what is counted where

| Stage | Control |
|---|---|
| Screen (fit) | Benjamini–Hochberg over **all** cells, q = 0.10. The grid is declared before any data is read. |
| Validation (select) | A selection filter: every exit per survivor, the best K advance. It is honestly a selection, and is recorded as `configurations`. |
| Confirmation (judge) | Bonferroni with the registry's count of every earlier test on the period plus these K. Frozen at preregistration. |
| Everything | The deflated Sharpe ratio is computed over all configurations. The registry records tests (judged) and configurations (examined). |

## Models

The `stumps` family (boosted decision stumps, numpy) joins ridge, logistic and k-NN in
`research/models.py`:

- its hyper-parameters are fixed;
- missing values are replaced by the training median;
- for a feature with few distinct values it splits between values, otherwise at quantile cuts;
- it is deterministic.

A model hypothesis is trained on discovery data. Its threshold and exit are chosen on validation
among declared configurations, and it is judged by the same battery.

## Running it (research machine)

```
python scripts/discover.py design        # the DP-001 design, its hash and frozen threshold; writes nothing
python scripts/discover.py preregister   # catalog + leakage on real bars + registry + document
python scripts/discover.py run           # once
python scripts/discover.py status | search TEXT
```

## What it cannot do

- It sees H1 bars of 12 FX pairs from 2007–2016, and every year of that has been used before by
  earlier trials; the registry counts it. The only unseen data is the sealed holdout, which
  discovery never opens, and data that does not exist yet.
- It has no order-book data, volume or order flow (tick counts are activity, not volume), no
  news, and no macro data.
- Features are limited to the declared primitives and the lab's grammar. It does not synthesize
  features from raw data.
- Conditions have at most two terms in the screen. Deeper interactions reach it only through the
  stumps model, which has depth 1: additive, no interactions.
- Prospective hypotheses (LLM drafts, follow-ups) wait for new data. Nothing yet feeds recorded
  paper-trading data back into a confirmatory program automatically.
- A VALIDATED finding changes nothing in production. Promotion is a separate, reviewed step,
  gated by the single-use holdout.

## Results so far

| Program | Verdict | Summary |
|---|---|---|
| DP-001 (H1, 1,734 cells + stumps model) | **FAILED** | 0 screen discoveries. Every cell had a negative net mean; the best was −0.089R. The model: 0 of 48 validation configurations passed, best +0.008R (t 0.16). Descriptively, gross expectancy on H1 is within ±0.03R of zero for every exit, while costs are 0.09–0.21R per trade. See [research/results/DP-001-summary.md](../research/results/DP-001-summary.md). |

## The next experiment to register: DP-002 (not registered, not run)

The motivation comes from DP-001's descriptive result. On H1, costs are 0.09–0.21R per trade
against a gross expectancy near zero. At a daily horizon, the same spread, slippage and
commission in pips are about a fifth as large per unit of risk.

- **Question.** With decisions made once a day at the New York close, does any cell of a declared
  daily grid, or a boosted-stumps model on daily features, have positive net expectancy? It must
  survive validation and then the frozen battery.
- **Data.** The same 12 FX pairs, as D1 bars from complete M15 bars. Lookback from 2007-03-30.
  The holdout stays sealed.
- **Segments.** The same as DP-001:
  - fit: 2007-06-01 → 2011-01-01;
  - select: 2011-01-11 → 2013-07-01;
  - judge: 2013-07-11 → 2017-01-01.
- **Grid.** 2 × (14 × 3 + 49 × 9) = **966 tests**.
  - States (7): er120, vol_ratio, ma_slope, range_pos120, usd_basket, atr_pctile, usd_corr.
  - Triggers (7): r1, r6, r24, bar_body, range_pos24, up_persistence, range_contraction.
  - All are computed on D1 bars, with windows counted in days.
  - Excluded because they are meaningless on D1: hour_sin, hour_cos, session, h4_trend, d1_trend.
- **Exits.** A declared daily menu, counted in D1 bars:
  - D1: barrier 1.0/1.5 ATR, 10 bars (the screen's exit);
  - D2: barrier 1.5/3.0 ATR, 20 bars;
  - D3: time exit after 5 bars, 2 ATR stop;
  - D4: time exit after 20 bars, 3 ATR stop;
  - D5: trailing 2 ATR, 40 bars.
- **Costs.**
  - Spread as measured, slippage 0.1 pip per fill, commission 0.7 pip per round trip.
  - Swap re-expressed as 0.01 × ATR24(D1) per night. That matches DP-001's 0.05 × ATR24(H1),
    since D1 ATR ≈ 5 × H1 ATR.
- **Stages.**
  - Screen: BH q = 0.10, n ≥ 100, keep 20.
  - Validation: n ≥ 80 and t ≥ 2.0.
  - Judged: 5 finalists plus the stumps model (stride 1) = **6 judged tests**.
- **Threshold.** The registry now counts 24 tests on the judged period (18 earlier + DP-001's 6),
  so with 6 more the threshold is **t ≥ 3.144**. It is re-read from the registry at registration.
- **Battery and board.** Unchanged.
- **Power, stated before it runs.** At t ≥ 3.144 and a standard deviation of about 1R, the
  smallest detectable net mean is 0.18R at 300 judged trades, 0.16R at 400 and 0.13R at 600.
  A smaller edge will go undetected. That is the price of a period that 30 tests have now used.
- **Code to add and test before registering.**
  - A D1 loader restricted to the features above.
  - The D exit menu.
  - The swap scaling.
  - The truncation leakage test on D1 bars.
  - A synthetic D1 program run with a planted effect.
- **If DP-002 fails too:** stop searching price-only features on these bars. The next evidence
  must come from data the system lacks (interest rates for carry, positioning, order flow), or
  from prospective data recorded after a hypothesis is frozen.
