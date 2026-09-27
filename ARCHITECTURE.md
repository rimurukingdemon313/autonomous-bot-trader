# Architecture

The layers, their responsibilities and their authority were fixed in
Phase 0, before any code existed. **What was built, and where, is at the
end:** [Implementation map](#implementation-map) and
[Amendment 1: bounded runtime learning](#amendment-1--bounded-runtime-learning).

---

## The pipeline

```
 MARKET DATA
     ↓
 DATA VALIDATION
     ↓
 MARKET STATE
     ↓
 FEATURES
     ↓
 REGIME / CONTEXT
     ↓
 AI RESEARCH / MODELS
     ↓
 OPPORTUNITY
     ↓
 TRADE DECISION ──────────────► JOURNAL  (recorded BEFORE risk sees it)
     ↓
 RISK ENGINE    ◄── final authority over whether anything is sent
     ↓
 EXECUTION
     ↓
 BROKER
     ↓
 RESULT ──────────────────────► JOURNAL
     ↓
 LEARNING / RESEARCH            (offline: never changes the live system directly)
```

Information flows downward. **Authority flows the other way**: any layer
below the decision may refuse what the layers above propose, and no layer
above may override a refusal.

## Layers

For each layer: what it is responsible for, and the limits of its authority.

### 1. Market data
**Responsible for** acquiring prices and any other market inputs, each
stamped with source, instrument, timeframe, the timestamp it describes and
the time it became available.
**May not** fill gaps, invent volume, spread, liquidity or any other value,
or alter history after the fact. A missing value is delivered as missing.

### 2. Data validation
**Responsible for** rejecting or flagging bad data: gaps, duplicates,
out-of-order timestamps, impossible prices, stale feeds, scale errors,
unclosed ("forming") bars and clock problems.
**May not** repair data silently. It passes data through, flags it, or
stops it. A flag travels with the data, so every later layer can see it.

### 3. Market state
**Responsible for** assembling, for a decision time T, exactly what was
knowable at T: closed bars, the current quote, account and position state,
and data-quality flags. This layer is where the future-information rule is
enforced by construction.
**May not** include anything timestamped or made available after T.

### 4. Features
**Responsible for** turning market state into measurable quantities.
There is **one** feature definition, used identically in research,
training, backtesting, paper trading and production. Each feature carries
a version, and its calculation metadata is recorded.
**May not** have a "research version" and a "live version". A feature
whose value at T depends on anything after T is a defect, caught by test.

### 5. Regime / context
**Responsible for** describing what kind of market this is, and **how
familiar** the current state is compared with what the models were trained
on. "Unknown or unseen" is a first-class answer.
**May not** assume a fixed list of regimes. Regime definitions are
hypotheses like any other and must be supported by data.

### 6. AI research / models
**Responsible for** estimating, for candidate actions, the probability of
outcomes and the expected R after costs, together with the uncertainty of
that estimate. Models are trained offline and deployed as frozen,
versioned artifacts.
**May not** retrain, re-tune or modify itself in production. It never sees
broker credentials, account balances used for sizing, or the risk engine's
internal state.

### 7. Opportunity
**Responsible for** evaluating candidates across instruments, timeframes
and contexts, and ranking them by evidence rather than by count. It
considers execution conditions: spread, liquidity and correlation with
exposure already held.
**May not** manufacture a candidate so that "something" gets traded.

### 8. Trade decision
**Responsible for** producing a single structured decision record,
BUY / SELL / NO_TRADE, with thesis, supporting and contradicting evidence,
entry, stop, target, exit logic, invalidation, probability, expected R,
uncertainty and every relevant version stamp. The record is journaled
**before** it goes anywhere else.
**May not** set position size or risk amount. NO_TRADE is the default
whenever the evidence does not clear the bar, when state is unfamiliar, or
when any input is missing.

### 9. Risk engine — final authority
**Responsible for** approving or rejecting every proposal, and for
computing the size of anything it approves. It enforces per-trade risk,
daily loss, drawdown, leverage, exposure, concurrent positions, spread,
slippage, abnormal conditions, duplicate protection, broker health,
emergency shutdown and funded-account constraints.
**No other layer may compute a size or a risk amount.** No API, flag,
prompt or configuration lets the AI bypass it. See
[RISK_CONTRACT.md](RISK_CONTRACT.md).

### 10. Execution
**Responsible for** turning an approved, sized order into exactly one
broker action, and for knowing the true outcome. It is idempotent,
duplicate-safe, state-aware and reconnect-safe. A write whose outcome is
unknown is **never retried**; the broker is queried instead. See
[EXECUTION_CONTRACT.md](EXECUTION_CONTRACT.md).
**May not** change direction, size, stop or target from what the risk
engine approved.

### 11. Broker
**Responsible for** the connection to the broker, and nothing else. It is
the **only** layer that holds broker credentials. It verifies the account
type (demo or live) from the broker's own evidence, and refuses to operate
when that evidence is missing or contradictory.
**May not** expose credentials or tokens to any other layer, log them, or
switch endpoints on retry or error.

### 12. Result
**Responsible for** reconciling what actually happened (fills, slippage,
costs, P/L in money and in R) against what was decided. Unknown values are
recorded as unknown.

### 13. Journal
**Responsible for** an append-only record of every decision (including
NO_TRADE), every risk verdict, every execution event and every result,
each with its version stamps. It is the evidence base for all later
learning and for every performance claim.
**May not** be edited or pruned to improve how results look.

### 14. Learning / research
**Responsible for** error analysis, attributing results to causes,
generating hypotheses and running experiments under the research contract,
and producing new **candidate** versions.
**May not** change the running system. A candidate reaches production only
by the lifecycle: new version, then test, then validation, then approval.
It never increases risk in response to a loss.

## Authority boundaries

| Action | Who may do it |
|---|---|
| Propose a trade | Decision layer, from model output |
| Decide NO_TRADE | Any layer: decision, risk, execution or data validation |
| Compute position size or risk amount | **Risk engine only** |
| Approve a trade | **Risk engine only** |
| Send an order | **Execution only**, and only an approved one |
| Hold broker credentials | **Broker layer only** |
| Change a production model | **Nobody at runtime**; only a new approved version |
| Increase risk after a loss | **Nobody** |
| Move to LIVE | **A human**, explicitly, after every gate |
| Stop trading (kill switch, pause) | The operator, from anywhere, at any time, without needing a credential |
| Resume, widen or initiate trading | The operator, authenticated |

## Separation of environments

```
RESEARCH / TRAINING / BACKTESTING        PRODUCTION INFERENCE / PAPER / DEMO
  heavy compute, experiment registry   →   frozen model artifacts, lightweight
  may use large libraries                  inference, minimal dependencies
          │                                          │
          └──────── SAME feature definitions ────────┘
```

- Research and training run separately from production. They can use
  whatever tooling the research needs.
- Production loads **frozen, versioned artifacts** and performs inference
  only.
- Both sides import the **same** feature definitions. A feature computed
  differently in the two places makes every backtest a measurement of a
  system that does not run.

## Failure behaviour (fail closed)

| Condition | Behaviour |
|---|---|
| Market data stale, missing or failing validation | NO_TRADE for the affected instrument |
| State unfamiliar (out of distribution) | NO_TRADE |
| Model artifact missing, unverified or failed validation | NO_TRADE |
| Persistence unavailable | No new orders |
| Kill switch unreadable | Treated as active |
| Account type cannot be verified | No trading; kill switch trips; the reason names the fields checked |
| Broker write outcome unknown | Never retried; broker queried; reconciled |
| Startup incomplete | No trading, but health is still served so the failure is visible |

## What is deliberately not decided here

Model families, feature sets, indicators, timeframes, instruments,
databases, languages beyond what the contracts require, and hosting. These
are chosen in their phases, on evidence, and the choices are recorded.

---

## Implementation map

```
 ReplayFeed / TradeLocker feed ──► Orchestrator (aitrader/orchestrator/core.py), one cycle per closed H1 bar
                                     │
   features (23, causal) ──► regime + familiarity ──► pattern memory: k nearest RESOLVED past situations
                                     │
         ┌──── five analysts, one point-in-time packet, all BEFORE synthesis ─────┐
         │ Market        Setup          Risk          Adversary       Reviewer    │
         │ describes     proposes       costs/        the case        evidence    │
         │                              conditions    against         quality     │
         │ regime,       candidate      cost/spread   the case        analogues,  │
         │ familiarity   templates      vs stop       against         lessons     │
         └──── optional language-model layer: may only ADD objections ───────────┘
                                     │
   Evidence synthesis (not a vote): analogue lower-bound expectancy − measured penalties
                                     │  BUY / SELL / NO_TRADE, journalled before risk sees it
   Risk engine ──► sole sizing authority; may refuse; halts on drawdown
                                     │
   Execution engine ──► intent written first; never resends; reconciles on restart
                                     │
   Paper broker or TradeLocker (demo only, two-signal check)
                                     │
   Outcome tracker ──► real outcomes of trades + SHADOW outcomes of skipped candidates
                                     │
   Learning (experience, lessons, post-mortems, reflections) ──► next cycle's evidence
```

| Layer (above) | Code | Tests |
|---|---|---|
| 1 Market data | `aitrader/data/` (`ticks`, `bars`, `resample`, `store`, `feed`), `broker/tradelocker/adapter.py` for live bars | `unit/test_data.py` |
| 2 Validation | `aitrader/data/validate.py`, `instruments.price_scale` | `unit/test_data.py` |
| 3-4 State, features | `aitrader/features/store.py` | `unit/test_features.py` |
| 5 Regime / context | `aitrader/regime/model.py` | `unit/test_regime_and_patterns.py` |
| 6 AI research / models | `aitrader/memory/patterns.py` (analogue memory), `aitrader/research/labels.py`, `aitrader/agents/`, `aitrader/llm/provider.py` | `unit/test_agents.py` |
| 7-8 Opportunity, decision | `aitrader/agents/analysts.py` (setup), `aitrader/decision/synthesis.py` | `unit/test_agents.py` |
| 9 Risk | `aitrader/risk/engine.py` | `unit/test_risk.py` |
| 10 Execution | `aitrader/execution/engine.py` | `unit/test_execution.py` |
| 11 Broker | `aitrader/broker/` (`paper`, `tradelocker/`) | `unit/test_tradelocker_adapter.py` |
| 12 Journal | `aitrader/memory/db.py`: SQLite, immutable tables with hash chains | `unit/test_db.py` |
| 13 Learning / research | `aitrader/learning/`, `aitrader/orchestrator/tracker.py`, `aitrader/research/registry.py`, `aitrader/backtest/` | `unit/test_learning.py`, `integration/test_pipeline.py` |
| 13b Research lab (research machine only) | `aitrader/research/lab.py`, `models.py`, `features_lab.py`, `hypotheses.py`; `scripts/research_lab.py` | `unit/test_research_lab.py`, `unit/test_architecture.py` |
| Service, dashboard | `aitrader/service/` | `integration/test_service.py` |

Environments: research and backtesting (`scripts/`, `aitrader/backtest/`)
and the service (`python -m aitrader`) import the **same** feature,
agent, synthesis, risk and execution code; the backtest drives it with a
replay clock.

## Amendment 1 — bounded runtime learning

The owner asked for a system that learns from its own outcomes while it
runs. Layer 13 above says learning "may not change the running system";
this amendment states exactly how far it may, and nothing else changes.

**Runtime learning MAY change, from resolved outcomes only:**

- the penalty a MAJOR objection adds to the required edge, once that
  objection has a track record of at least 30 resolved cases: the measured
  difference in R, clamped to **[0.01, 0.25] R**;
- whether a **validated lesson** blocks a context. A lesson is validated
  only on outcomes that resolved after it was discovered, with a
  Bonferroni-corrected significance test. A validated lesson can only
  **block**. It is retired when later evidence reverses it;
- the pattern memory, which grows by one row per resolved situation;
- the weight of a language model's opinion, which is its measured forward
  reliability, starting at 0.

**It may NOT change:** position size, risk per trade, any risk limit,
direction, entry, stop or target of a candidate, the feature definitions,
the regime model, the action templates, or the demo, risk and execution
guards. It cannot create a trade that the evidence did not support.

Every statistic behind these changes counts **effective** samples: outcomes
that overlap in time, and several templates of one decision, are not
counted as independent evidence (learning 1.2.0).

Every change is a new knowledge version, stamped on every later decision,
listed on the dashboard, and revertible by an authenticated operator
(`POST /api/control/knowledge/revert`). One win or one loss cannot create,
validate or retire anything: the thresholds are sample sizes and
significance.

## Amendment 2 — the research lab

Research that can widen the system's choices (instrument, timeframe,
features, model, entry) runs in `aitrader/research/lab.py`, on the
research machine, under RESEARCH_CONTRACT §5:

- a declared, counted space;
- registration first, with a frozen threshold;
- purged, embargoed walk-forward;
- baselines and robustness;
- a single verdict per trial.

Its boundary with production is structural:

- the lab writes only under `research/artifacts/`, never where production
  loads;
- the live decision path cannot import it (checked in the import graph);
- a lab PASS is a *research candidate*. It reaches production only through
  a reviewed promotion that includes the single-use holdout test.

Reflection may *propose* experiments (the `experiments` journal); it
cannot run them.
