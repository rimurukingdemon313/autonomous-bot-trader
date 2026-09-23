# Roadmap

Each phase has a goal, deliverables and an **exit gate**. A phase is not
complete because its code exists. It is complete when its gate is met, with
evidence, and the next phase has been approved.

**Only Phase 0 is in progress. No other phase may start until Phase 0 has
been reviewed and approved.**

---

## Phase 0 — Repository + specification  *(current)*
**Goal:** agree what is being built, and the rules it must obey, before any
code exists.
**Deliverables:** README, specification, architecture, contracts,
engineering rules, process documents, directory READMEs, templates.
**Exit gate:** the contracts are reviewed and approved by the owner.
**Contains no code.**

## Phase 1 — Data foundation
**Goal:** a trustworthy, versioned and auditable market-data layer.
**Deliverables:**
- a sourcing decision: which history, from where, under what licence, and
  how many years genuinely exist per instrument;
- ingestion, validation and a documented time convention;
- a data-quality report per instrument;
- **the final holdout period chosen and sealed** before any research looks
  at the data.
**Exit gate:** data-integrity tests pass; the quality report is reviewed;
the holdout is sealed and its seal is tested.

## Phase 2 — Feature foundation
**Goal:** one feature definition, shared by research and production.
**Deliverables:** a feature store with versioned definitions and
calculation metadata; causality tests for every feature.
**Exit gate:** every feature passes truncation (look-ahead) tests, and
adversarial injected leaks are detected.

## Phase 3 — Research framework
**Goal:** make honest research the easy path.
**Deliverables:** an experiment registry, pre-registration workflow, label
definitions that include costs, and baselines.
**Exit gate:** the registry refuses duplicate, back-dated and unregistered
experiments; label tests pass.

## Phase 4 — Validation / walk-forward
**Goal:** a validation harness that cannot be fooled easily.
**Deliverables:** chronological splits, walk-forward (expanding and/or
rolling), purging and embargo, a robustness battery, and
multiple-testing-aware statistics.
**Exit gate:** leakage tests for splitting, normalization, feature
selection, hyperparameter selection and model selection all pass.

## Phase 5 — AI research layer
**Goal:** models that estimate outcome probabilities and expected R after
costs, with calibrated uncertainty.
**Deliverables:** baseline models first, more complex ones only if they
beat the simpler ones out of sample; model cards; frozen artifacts.
**Exit gate:** walk-forward results reported against baselines, including
the result "no edge found" if that is what the evidence shows.

## Phase 6 — Regime detection
**Goal:** describe market context, and recognise unfamiliar states.
**Deliverables:** regime descriptions supported by data; a familiarity
(out-of-distribution) measure that forces NO_TRADE.
**Exit gate:** regimes are shown to be persistent and informative, or are
dropped; out-of-distribution detection is tested.

## Phase 7 — Decision engine
**Goal:** a single structured decision, BUY / SELL / NO_TRADE, with its
reasoning, journaled before execution.
**Deliverables:** the decision record, the opportunity evaluation, and
NO_TRADE reasons.
**Exit gate:** malformed, missing, contradictory or out-of-range inputs
resolve to NO_TRADE, by test.

## Phase 8 — Risk integration
**Goal:** the independent risk engine as final authority.
**Deliverables:** the risk engine per [RISK_CONTRACT.md](RISK_CONTRACT.md),
a funded-account compliance layer (rules supplied by the owner), and a
kill switch.
**Exit gate:** risk tests pass, including "risk never increases after
losses" and "no path bypasses risk".

## Phase 9 — Execution
**Goal:** safe order handling.
**Deliverables:** execution and broker layers per
[EXECUTION_CONTRACT.md](EXECUTION_CONTRACT.md), with reconciliation and
restart recovery.
**Exit gate:** duplicate-order, ambiguous-outcome, reconnect and recovery
tests pass against a fake broker.

## Phase 10 — Paper trading
**Goal:** the whole system running on live data, with no orders sent.
**Entry requires:** the final holdout test run once with a PASS, and owner
approval.
**Records:** every decision and NO_TRADE, simulated executions, latency,
spread, slippage, P/L, drawdown and model version.
**Exit gate:** paper results fall inside the range the validation
predicted, over a pre-registered minimum period.

## Phase 11 — Demo
**Goal:** real broker execution on a demo account.
**Entry requires:** paper gate met, and owner approval.
**Exit gate:** demo results consistent with paper; execution quality
measured; no unresolved safety incidents.

## Phase 12 — Live readiness
**Goal:** decide, on evidence, whether real money is justified.
**Entry requires:** every earlier gate met, and owner approval.
**Output:** a written evidence review. The review can conclude "not
ready", and that is a valid outcome.
**There is no automatic transition to LIVE.**

---

## If a gate fails

The candidate goes back to research and the failure is recorded (see
[docs/FAILURE_POLICY.md](docs/FAILURE_POLICY.md)). The infrastructure
built so far still stands. A system that records, monitors and decides
NO_TRADE is a legitimate place to stop.
