# Roadmap

Each phase has a goal, deliverables and an **exit gate**. A phase is not
complete because its code exists. It is complete when its gate is met, with
evidence, and the next phase has been approved.

## Where each gate stands

The owner approved the Phase 0 contracts and the full build. Code existing
is not a gate: this table says which gates are met **with evidence**.

| Phase | Gate | Evidence |
|---|---|---|
| 0 Specification | **met** | owner approval |
| 1 Data | **met**, except the owner's review of the quality report | `data/manifest.json`; `tests/unit/test_data.py`; holdout sealed and its seal mutation-tested |
| 2 Features | **met** | truncation test on every feature; five kinds of injected leak detected |
| 3 Research framework | **met** | registry refuses duplicate, back-dated and unregistered post-seal trials; label tests |
| 4 Validation | **partly met** | expanding walk-forward with a 5-day embargo, point-in-time memory, Bonferroni thresholds. The robustness battery is written into PR-001 but runs only if H1 passes. Leakage through selection is controlled by the registry (every configuration is counted), not by a code test |
| 5 AI research | **reported** | PR-001, research/preregistrations/PR-001-multi-agent-ablation.md, RESULTS |
| 6 Regime | **partly met** | familiarity (out-of-distribution) tested and forces NO_TRADE; persistence measured on training rows (knowledge card); informativeness measured as R by regime in PR-001 |
| 7 Decision | **met** | malformed, missing, contradictory and out-of-range inputs give NO_TRADE (unit tests, mutation audit) |
| 8 Risk | **met** | `tests/unit/test_risk.py`; docs/MUTATION_AUDIT.md |
| 9 Execution | **met against a fake broker** | duplicate, ambiguous-outcome and restart tests. Not yet run against the real TradeLocker API |
| 10 Paper | **not met** | built and runnable as a forward test of an unvalidated candidate (docs/SYSTEM_LIFECYCLE.md, Amendment 1); no paper results exist yet |
| 11 Demo | **not met** | built behind the two-signal demo check; not run |
| 12 Live | **not started** | `MODE=LIVE` is refused by the software |

---

## Phase 0 — Repository + specification
**Goal:** agree what is being built, and the rules it must obey, before any
code exists.
**Deliverables:** README, specification, architecture, contracts,
engineering rules, process documents, directory READMEs, templates.
**Exit gate:** the contracts are reviewed and approved by the owner.
**Contained no code.**

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
approval — as a validated system. An unvalidated candidate may run here as
a forward test only (docs/SYSTEM_LIFECYCLE.md, Amendment 1).
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
