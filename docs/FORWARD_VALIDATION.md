# Forward validation and learning

Historical research ended without a deployable edge (docs/FINAL_RESEARCH_REPORT.md: 54 hypotheses
REJECTED, 0 PROMISING, 0 VALIDATED; the 2017 holdout is still sealed). The absence of a
validated edge is a result, not a bug. From here, evidence can only come **forward**, on prices no
one had seen when the decision was made. This document says how the running system collects it,
how it learns from it without leaking, and what it would take to call anything an edge.

No result in this repository is a claim of profitability, and none should be read as one.

## 1. Edge status: every signal says what stands behind it

Each decision records `edge_status`, set once at decision time (`aitrader/decision/edge_status.py`):

| Status | Meaning | Where it can come from |
|---|---|---|
| **VALIDATED** | passed the definition in §6, then reviewed and promoted by an operator | only `models/artifacts/promoted_edges.json`, written by research + operator; health HEALTHY |
| **PROMISING** | measured and positive, short of validation; or a validated edge whose health degraded | the same file |
| **EXPERIMENTAL** | every other proposal: the analogue synthesis (PR-001 FAILED), the language-model trader, the trading room, experimental AI | the default for any trade |
| **NONE** | not a trade | |

A model's stated confidence never changes the status. "95% sure" is a sentence, not a sample.
Forward results never relabel a decision either: the most they can say is ELIGIBLE_FOR_REVIEW (§5).

`signal_class` names the path that produced it: EVIDENCE, LLM_TRADER, TRADING_ROOM, EDGE,
EXPERIMENTAL_AI. Results are always broken down by it; two classes are never averaged together.

## 2. Routing: EXECUTE or SHADOW

| | PAPER | DEMO (default) | DEMO + `EXPERIMENTAL_EXECUTE=true` |
|---|---|---|---|
| VALIDATED | execute (simulated) | execute on the demo account | execute on the demo account |
| PROMISING / EXPERIMENTAL | execute (simulated) | **SHADOW** | execute on the demo account |

**SHADOW** means the following:

- the risk engine still evaluates the trade and its verdict is journalled;
- the proposal goes into the forward ledger and is followed to its outcome;
- no order is ever sent.

The execution engine applies the same rule a second time (`allow_unvalidated`), so no other path
can send an unvalidated trade. LIVE does not exist. A mode the code does not know never
executes, not even a VALIDATED edge.

## 3. The forward ledger (`aitrader/learning/forward.py`)

Every BUY/SELL proposal is written to the immutable `forward_proposals` table at decision time.
This covers executed, shadow and risk-rejected proposals alike.

**Each proposal records:**

- **The trade:** instrument, side, entry reference, stop, target and holding time.
- **Planned risk:** in price and in units of H1 ATR, plus the reward:risk.
- **Status and routing:** edge status, signal class, family, the route (EXECUTE / SHADOW / REJECTED),
  the risk verdict and its reasons, and whether it executed.
- **The model:** provider, model, verdict (TRADE / NO_TRADE / UNCERTAIN), stated confidence and
  expected R, and method.
- **The market:** regime, volatility state, session, and the timeframes read.
- **Cost:** the estimated cost, and the spread at the decision.
- **Partition:** LEARNING or EVALUATION (§4).

The decision record itself (`decisions` table) additionally holds the model's thesis, evidence,
reasons against, invalidation, analogues, latency and token counts, every agent's report and the
feature snapshot.

### Resolving an outcome

An outcome is computed by **walking completed bars** that opened at or after the decision time:

- **Bars:** the finest timeframe the feed can supply for the span (M1, then M5, M15 or H1).
- **Stop or target:** a stop comes before a target in the same bar. A gap through the stop fills at
  the open. A target fills at its price, never better.
- **Time exit:** at the bar's close.
- **Nothing early:** nothing is known before the bar that reveals it has closed.
- **After the exit:** the path is followed to the end of the holding window, for the post-mortem
  only. This tells a stop that was too tight (the target was reached later) apart from a wrong
  direction.
- **Restart-safe:** resolution reads the feed, so an unresolved proposal is simply walked again
  after a restart.
- **No data:** after 30 days without data the outcome is recorded as UNRESOLVED, with no R. A value
  is never invented.

### Costs

Costs are separated exactly: **gross R − cost R = net R**.

- **Cost:** the spread at the decision, slippage on each market fill, and commission.
- **Denominator:** everything is divided by the planned risk (entry to stop).

### Execution quality

Executed trades also have their real result in `trades`. The two can be compared to measure
execution shortfall.

## 4. Partitions: learning data and evaluation data never mix

Each decision belongs to **LEARNING** or **EVALUATION** by its decision time alone, never by its
outcome. Every third ISO week is EVALUATION. A whole week per block keeps neighbouring, correlated
decisions on the same side.

| Reads | LEARNING | EVALUATION |
|---|---|---|
| forward lessons: creation (§5) | yes | no |
| forward lessons: confirmation | no | yes, only outcomes resolved after the lesson was created |
| the model traders' own memory of past trades (`TradeMemory`) | yes | no |
| forward eligibility (§5) | no | yes |

Timestamps enforce the rest. An outcome is invisible to every query "as of t" until it has resolved
by t (`ForwardLedger.rows(as_of=t)`). The experience view admits outcomes only as they resolve.
Tables are append-only with hash chains, so a result cannot be edited after the fact.

The existing analogue-learning lifecycle (`learning/experience.py`) keeps its own leakage rule.
A lesson is validated only on outcomes that resolved after its creation, at Bonferroni-corrected
significance, and a validated lesson can only block.

## 5. What the system learns, and what learning may change

### Per-trade tags

Each resolved outcome is tagged deterministically (`learning/taxonomy.py`):

- WRONG_DIRECTION
- BAD_ENTRY
- STOP_TOO_TIGHT
- TARGET_TOO_CLOSE
- VOLATILITY_MISMATCH
- COST_EROSION
- FALSE_BREAKOUT
- LIQUIDITY_SWEEP_FAILURE

### Aggregate lessons

These are measured over a scope (a signal class, regime, instrument or model):

- BAD_REGIME
- SYMBOL_FAILURE
- MODEL_FAILURE
- AI_OVERCONFIDENCE and AI_UNDERCONFIDENCE (stated probability of reaching the target, against what
  happened)

### Lifecycle

Versions are appended to the immutable `forward_lessons` table.

- **CANDIDATE:** created from LEARNING outcomes only. It needs at least 30 outcomes in the scope, a
  negative mean net R, and a tag that explains at least 25% of them (at least 10 occurrences). An
  aggregate lesson instead needs t ≤ −2, or a calibration gap of at least 0.10 with z ≥ 2.
- **ACTIVE:** the same test holds again on at least 30 EVALUATION outcomes that resolved after the
  candidate was created.
- **REJECTED:** that confirmation failed.

One trade can never create, confirm or reject a lesson.

### What an active lesson may change

**An ACTIVE lesson is information only:**

- it is shown to the model traders in their memory, and on the dashboard;
- it never changes code, a parameter, a risk limit or a size;
- it never creates a trade.

**The analogue-learning lessons are different.** Their validated lessons may block a trade in their
exact context; they can never add one.

### Forward statistics

These are kept for every family, and broken down by signal class, route, edge status, symbol,
model, regime, timeframe and session (`learning/metrics.py`, served at `/api/evidence`):

- sample size and win rate;
- average, median and expectancy, with the standard deviation and t;
- gross, cost and net R, kept separate;
- profit factor, maximum drawdown in R and the longest losing streak;
- MFE and MAE;
- net R with costs doubled;
- concentration by symbol, day, model and regime;
- calibration;
- daily, weekly and monthly series.

Below 30 resolved outcomes, a sample is labelled "insufficient".

## 6. The exact definition of a validated edge

A candidate becomes **VALIDATED** only when all of these hold. Each must be shown, not assumed.

### A. Forward eligibility

This is computed automatically by `metrics.eligibility` on EVALUATION outcomes only, and shown as
ELIGIBLE_FOR_REVIEW:

1. at least **100** resolved outcomes in the evaluation partition;
2. **mean net R > 0 after all costs**, with **t ≥ 2.5**;
3. still positive with **every cost doubled**;
4. positive in **both chronological halves**;
5. no instrument supplies more than **50%** of trades, and no single day more than **20%**;
6. a maximum drawdown of at most **20R**;
7. a mean net R above the **unconditional baseline** over the same weeks: the template entries'
   shadow outcomes. With no baseline measured, this criterion fails.

### B. Review and confirmation

These are done by a human, as a registered research step:

8. the family and its exact rules are **frozen and registered** before the confirming period (the
   research registry; RESEARCH_CONTRACT.md). Its multiple-testing threshold counts every family
   that was ever examined;
9. it is confirmed on a further **untouched** forward period that begins after the freeze, with the
   same criteria;
10. no leakage is found: point-in-time checks and the architecture tests pass, and the result does
    not depend on a model that could have seen the period (a language-model family can only be
    confirmed forward, never on history);
11. the evidence holds under the realistic spread and slippage actually measured in DEMO, not only
    the declared paper approximations.

### C. Promotion

12. An operator writes the edge into `models/artifacts/promoted_edges.json` (status VALIDATED, with
    its trial id and evidence). Only then do its decisions carry VALIDATED. Its health is monitored,
    and a degraded edge falls back to PROMISING.

The sealed 2017 historical holdout is not part of this path. It stays sealed. Opening it requires a
historical candidate that earned it under its own preregistration.

## 7. Reading the dashboard honestly

- **Forward evidence** shows gross, costs and net separately, and every breakdown.
- **EXPERIMENTAL** and **SHADOW** are labels, not apologies. They mark results that are evidence
  being collected.
- **A positive number with "insufficient" beside it** is not an edge.
- **A negative number** is reported exactly as it is, and losses are never hidden.
