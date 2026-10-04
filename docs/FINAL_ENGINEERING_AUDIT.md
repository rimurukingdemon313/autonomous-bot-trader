# Final engineering audit

Date: 2026-10-04. Starting point: commit `b00ca74` (RV-1 result, Path B: no deployable edge).
Scope: one engineering and validation pass, whose goal is to make the existing system operational,
measurable and able to discover an edge from forward evidence. It is **not** a new research
round. No hypothesis was tested, no threshold was changed, and the sealed 2017 holdout was not
opened.

> **There is no profitability guarantee of any kind.** No edge is validated in this repository.
> Every trade the system makes today is EXPERIMENTAL. The forward ledger measures whether that
> ever changes; it does not assume it will.

## 1. What was inspected

**Contracts and documents:**

- PROJECT_SPEC, ARCHITECTURE and ROADMAP;
- the engineering, research, validation, data, model, risk, execution and security contracts;
- docs/AUDIT, GAP_REPORT, AI_MODELS, OPERATIONS and FINAL_RESEARCH_REPORT;
- the research registry and results (unchanged).

**Code, in the live path:**

- `service/` (config, runtime, server, dashboard);
- `orchestrator/` (core, tracker) and `agents/` (brain, llm_trader, trading_room, analysts, types);
- `decision/` (synthesis, edge_engine) and `llm/provider.py`;
- `risk/engine.py` and `execution/engine.py`;
- `broker/` (base, paper, tradelocker demo guard and adapter);
- `memory/` (db, trade_memory) and `learning/` (experience, review);
- `backtest/runner.py`, `observability.py`, the Dockerfile and railway.json.

**Tests:** all of them, including `test_architecture.py` and `scripts/mutation_audit.py`.

**The map, as built:**

    DATA (TradeLocker | Yahoo, completed bars only) → FEATURES (23 causal, store) → REGIME (fitted model)
    → MEMORY (analogue patterns, trade memory, lessons) → AGENTS (market, setup, risk, adversary, reviewer)
    → AI (evidence reviews | llm_trader | trading_room | experimental_ai) → SYNTHESIS (decision record)
    → [NEW] EDGE STATUS + COST + TIMEFRAMES → RISK ENGINE (only sizer, final authority)
    → [NEW] ROUTE (EXECUTE | SHADOW) → EXECUTION (intent first, never resends) → BROKER (paper | demo)
    → OUTCOME (closures, post-mortems, template shadows) → [NEW] FORWARD LEDGER (every proposal)
    → LEARNING (experience lessons, reflection, [NEW] forward lessons, forward statistics)

## 2. What was broken or unsafe

| # | Finding | Severity | Fixed |
|---|---|---|---|
| 1 | Both model prompts asked the model not to let the account "sit idle" and to prefer "a small, short trade to waiting"; the scalp style asked for "a new trade each minute when the market offers anything reasonable". This is trade-forcing language, against the owner's rule. | high | yes: removed; the prompts now say time without a trade costs nothing; a test forbids the phrases; a mutant re-inserting them is killed |
| 2 | `ExecutionEngine(allow_live=...)`: an argument that waived the demo check. No caller used it, but it was a live code path. | high | yes: removed. `is_demo() is True` is now required, with no waiver; tested |
| 3 | The orchestrator imported `research.hypotheses`, and with it the research lab, so production loaded the laboratory. `test_architecture` did not look at the orchestrator or the service. | medium | yes: proposals moved to `learning/proposals.py` (re-exported for the lab); the architecture test now covers the orchestrator, service, learning, memory and llm |
| 4 | No edge status. Model and analogue trades were indistinguishable from validated ones on records and on the dashboard. | high | yes: `edge_status` on every decision; no AI path can be VALIDATED |
| 5 | DEMO sent every approved trade, unvalidated ones included, to the broker with no opt-in. | medium | yes: in DEMO they are SHADOW unless `EXPERIMENTAL_EXECUTE=true`; the execution engine re-checks |
| 6 | Model outputs had no UNCERTAIN, no confidence, no reasons against, and no stated invalidation requirement. | medium | yes: strict schema (llm-trader 1.12.0); malformed replies are NO_TRADE, never repaired |
| 7 | Shadow outcomes covered only the four template actions, so a model's own proposals that were risk-rejected (or not executed) were never followed. Template shadow tracks lived only in memory, so a restart lost the unresolved ones. | medium | yes: the forward ledger records and resolves every proposal from the journal, restart-safe |
| 8 | Nothing separated learning data from evaluation data in the forward record; the model's memory read every past trade. | medium | yes: week-block partitions; model memory and lesson creation read LEARNING only |
| 9 | No stale-decision guard and no entry-drift guard before submission. | medium | yes: `EXEC_MAX_DECISION_AGE_S` (default 900 s) and 0.25R adverse drift → BLOCKED |
| 10 | Startup reconciliation did not read the account, or list journal positions the broker no longer holds. | low | yes: both, and an unreadable account pauses trading |
| 11 | No `/readyz` and no `/metrics`. | low | yes |
| 12 | No per-provider token or cost tracking; a result did not say which provider answered. | low | yes |
| 13 | The dashboard scrolled horizontally on a phone (390 px → 547 px) because of the event log and the reflection text. | low | yes: measured 390 px after the fix |
| 15 | During this work, two NEW mutants first survived: a test of "no bar before the decision" passed only because the walk was waiting for the post-exit window, and no test proved that 29 outcomes cannot create a lesson | medium | yes: both tests strengthened (the code was correct); a full re-run killed all 135 |
| 14 | Two mutation-audit entries were stale before this work (`cadence-evidence-refused`, `room-own-voice`): their snippets no longer matched the code. | low | yes: re-pointed at the current code |

## 3. What was preserved, unchanged

- **Research history.** The registry, every preregistration, every result, the edge registry
  (54 REJECTED, 0 PROMISING, 0 VALIDATED) and the sealed holdout. No research file was edited.
- **Risk.** The risk engine (`risk-1.0.0`, untouched): only sizer; 1% hard ceiling; size never
  depends on confidence; risk only decreases after losses.
- **Execution.** Intent before action, no resend on ambiguity, reconciliation by query.
- **Demo checks.** The two-signal TradeLocker demo guard. Controls split by direction, with the
  token required to resume or widen. JSON logs with secret redaction at the sink.
- **Storage.** Immutable hash-chained tables.
- **Learning.** The existing experience lifecycle and the reflection proposals.
- **Decision modes.** Every existing mode: evidence, llm_trader, trading_room, edges.

## 4. What was newly implemented

| Component | File |
|---|---|
| Edge status and execution route | `aitrader/decision/edge_status.py` |
| Decision record: edge status, signal class, AI verdict and metadata, cost estimate, timeframes | `aitrader/decision/synthesis.py` (decision-1.2.0) |
| Strict model reply: UNCERTAIN, confidence, expected R, evidence, reasons against, invalidation, regime, analogues | `aitrader/agents/llm_trader.py` (1.12.0) |
| Experimental AI mode: proposer, specialist roles, deterministic synthesis | `aitrader/agents/experimental_ai.py` |
| Forward ledger: every proposal, shadow outcome, gross/cost/net R, MFE/MAE, post-exit path, partitions | `aitrader/learning/forward.py` |
| Forward statistics, breakdowns, calibration, eligibility | `aitrader/learning/metrics.py` |
| Structured forward lessons (13 codes, candidate → active only out of sample) | `aitrader/learning/taxonomy.py` |
| Routing (EXECUTE / SHADOW), forward ticks, active lessons in the model's memory | `aitrader/orchestrator/core.py` (1.12.0) |
| Execution guards: no live argument, unvalidated, stale, drift | `aitrader/execution/engine.py` (exec-1.3.0) |
| `LIVE_TRADING`, `PAPER_MODE`, `EXPERIMENTAL_EXECUTE`, `EXEC_MAX_DECISION_AGE_S` | `aitrader/service/config.py` |
| `/readyz`, `/metrics`, `/api/evidence`, `/api/lessons`; startup reconciliation of the account | `aitrader/service/server.py`, `runtime.py` (service-1.7.0) |
| Provider attribution, tokens, cost per provider | `aitrader/llm/provider.py` |
| Partitioned model memory | `aitrader/memory/trade_memory.py` |
| Dashboard: orders/edge/live chips, forward-evidence panel, forward lessons, phone layout | `aitrader/service/static/*` |
| New database tables `forward_proposals`, `forward_outcomes`, `forward_lessons` (append-only) | `aitrader/memory/db.py` (schema 3) |

## 5. Tests

- **Test count:** **661** (593 before this work; 68 new). **Result:** **661 passed, 0 failed, 0 skipped** (`bash scripts/check.sh`).
- **New tests:** `tests/unit/test_forward.py`, `tests/unit/test_experimental_ai.py` and
  `tests/integration/test_forward_service.py`.
- **What they cover:**
  - shadow outcomes, including stop-first, gap fills, time exits, no early or unclosed bars,
    purity, and costs (gross − costs = net);
  - partitions and restart recovery of pending proposals;
  - immutability, and UNRESOLVED with no invented R;
  - statistics, including small-sample labels and eligibility (never validation);
  - lessons: never from one trade, never from evaluation data, confirmed only later, calibration;
  - edge status and routing for every mode, with an unknown mode never executing;
  - the experimental AI: veto, failure, timeout, malformed and uncertain paths, a different
    provider for the challenger, and cost tracking;
  - configuration refusals: LIVE_TRADING, PAPER_MODE contradiction, EXPERIMENTAL_EXECUTE outside
    DEMO, ambiguous flags;
  - execution: no live argument, unverified account, unvalidated decision, stale decision, entry
    drift;
  - DEMO shadow end to end (nothing submitted);
  - an experimental trade end to end on paper;
  - the model never reads an evaluation-week trade;
  - `/readyz`, `/metrics` and `/api/evidence` over HTTP.
- **Existing tests:** all pass. Fixture model replies were completed with the now-required
  `confidence` and `invalidation`, so the tests reach the checks they test. One assertion was
  updated for a deliberate change: the model's memory now counts LEARNING-week trades only. No
  production check was weakened.
- **Mutation audit:** **135 of 135 killed** (docs/MUTATION_AUDIT.md). It includes 23 new mutants for the
  guards added here.

## 6. Safety verification

| Claim | Where it is enforced | Test |
|---|---|---|
| Default is PAPER, live off | `ServiceConfig.from_env` | `test_the_defaults_are_paper_and_no_live` |
| `LIVE_TRADING=true`, `MODE=LIVE`, unknown modes and ambiguous flags are refused at startup | config | `test_ambiguous_or_live_configuration_is_refused`, `test_live_mode_is_refused_at_configuration` |
| No order without a positively verified demo/paper account; no waiver exists | execution engine | `test_there_is_no_live_argument_and_an_unverified_account_never_trades` + mutant `exec-demo` |
| An unvalidated trade is never sent in DEMO unless the operator opted in | orchestrator route, then execution engine again | `test_in_demo_an_unvalidated_trade_is_shadow_never_sent`, `test_routing` |
| A model's confidence never makes a trade VALIDATED | `edge_status.classify` | `test_a_confident_model_is_still_experimental` |
| The AI cannot size, change a limit, move a level or bypass the risk engine | architecture test (only the risk engine sizes); levels passed verbatim | `test_architecture.py`, `test_a_challenged_and_surviving_proposal...` |
| AI failure, malformed reply or timeout → NO_TRADE | llm_trader, experimental_ai | `test_any_specialist_veto_or_failure_is_no_trade`, `test_any_broken_or_unsafe_reply...` |
| Stale data / stale decision / runaway price → no trade | risk quote age; execution age and drift | `test_a_stale_decision...`, `test_a_price_that_ran_away...` |
| Duplicate orders impossible | intent UNIQUE per decision; paper client id once | `test_fill_then_duplicate_is_not_resent` |
| Unknown write results reconciled, never resent | execution engine | existing tests + mutant `exec-no-resend` |
| Restart: positions, orders, account and pending evidence recovered before trading | runtime reconciliation; journal | `test_state_survives_a_restart`, `test_unresolved_proposals_survive_a_restart...` |
| No learning leakage | partitions; `rows(as_of)`; resolution order | `test_evaluation_outcomes_never_create_a_lesson`, `test_an_outcome_is_invisible_before_it_resolved`, `test_the_model_never_reads_an_evaluation_week_trade` |
| Production never imports the research lab | import graph | `test_the_research_lab_is_not_imported_by_the_live_decision_path` |
| Secrets never in logs or responses | redaction at the sink; `public()` views | `test_no_secret_is_ever_served`, `test_observability.py` |

## 7. Status

- **AI providers.** Provider-agnostic and OpenAI-compatible. The first provider is primary, the
  second secondary, the rest fallbacks. Each call has a timeout, one retry on a 429 or 5xx, then a
  cooldown; there are per-provider and global daily budgets, and token and cost tracking. No model
  is configured by default, so nothing expensive is used unless configured. With no provider
  configured, the model modes are NO_TRADE and the evidence mode runs without model reviews.
- **Paper.**
  - Works continuously, on TradeLocker or Yahoo data.
  - The simulated account fills at bid/ask with slippage and commission, with stop-first bar
    checks; it persists in the database and survives a restart.
  - Experimental trades execute on paper and are labelled.
- **Demo.**
  - The TradeLocker demo guard is unchanged: two independent signals, and absence of evidence
    fails.
  - Unvalidated trades are SHADOW unless `EXPERIMENTAL_EXECUTE=true`.
  - It was not exercised against a live TradeLocker server in this session, because no
    credentials were used.
- **Railway.**
  - Dockerfile and railway.json are unchanged: health check `/healthz`, restart on failure.
  - State lives on a persistent `/data` volume; shutdown is graceful (SIGTERM).
  - New: `/readyz` and `/metrics` for monitoring, and broker connection status on the dashboard.
- **Live.** Does not exist. No code path can create it.

## 8. Remaining limitations (honest)

1. **No edge.** Nothing has been shown to make money. Forward samples start at zero; with about
   72 decisions a day at most, the 100 EVALUATION outcomes eligibility needs (a third of weeks)
   take months, depending on how often trades are proposed.
2. **Paper fills.**
   - **Latency:** paper fills are immediate at the current quote. No latency is simulated; the
     stale-decision and drift guards bound its effect.
   - **Swap:** declared in ATR terms (an approximation).
   - **Partial fills:** not modelled in paper. In DEMO, TradeLocker's fill is recorded as
     reported.
3. **Forward costs.** Forward costs use the decision-time spread and declared slippage and
   commission. DEMO's measured fills should be compared with them before any promotion
   (criterion 11 in docs/FORWARD_VALIDATION.md).
4. **Tags.** FALSE_BREAKOUT and LIQUIDITY_SWEEP_FAILURE are tagged from the stated method or
   family text, a weak signal. They are labelled as such and remain information only.
5. **Model memory.** The language-model trader's memory now excludes evaluation-week trades. The
   older analogue experience lifecycle keeps its own sequential out-of-sample rule rather than the
   week partition. Both are leakage-safe by construction; they are different rules.
6. **Template shadow tracks.** The tracker's in-memory template shadow tracks (used for analogue
   memory growth) are still lost on restart if unresolved. The forward ledger, which is what
   evaluation uses, is not affected.
7. **Demo routing tests.** The DEMO routing is tested with the paper broker standing in for the
   demo account; the TradeLocker adapter has its own fake-transport tests.

## 9. What would constitute a validated edge

The full definition is in docs/FORWARD_VALIDATION.md §6. In summary, all of the following, on
EVALUATION-partition forward outcomes and then on a further untouched period after the family is
frozen and registered:

- at least 100 resolved outcomes, with mean net R > 0 after all costs and t ≥ 2.5;
- still positive with costs doubled, and positive in both chronological halves;
- no instrument above 50% of trades, and no single day above 20%;
- a maximum drawdown of at most 20R;
- above the unconditional baseline over the same weeks;
- no leakage, and robust to the spread and slippage measured in DEMO;
- then an operator's reviewed promotion into the promoted-edge file.

A model saying it is confident is not on the list.

## 10. Statement

This system can now collect, separate and judge forward evidence without fooling itself. It has
not found an edge. It does not guarantee any profit and none should be expected from it until the
evidence above exists. If no edge exists in the information available to it, the correct output
of this system is a growing, honest record that says so.

## Addendum: edge mission (after 693ea9b)

See docs/EDGE_MISSION_REPORT.md for the full report. Two engineering findings belong here.

- **Data defect.** The Dukascopy tick mirror this repository ingests (FX-Data on GitHub) has no
  `00h` hourly files: 00:00–01:00 UTC is missing every day for 12 of 13 instruments. EURUSD is
  complete. The gap was confirmed at the source by listing a branch's files.
  - H1/H4/D1 bars are still built, but without that hour. A stop or target touched only inside it
    is seen one bar late.
  - It is 4.2% of hours and cannot explain the absence of an edge.
  - It is the Tokyo fix hour, which shaped FLOW-1's design.
  - Re-ingesting from Dukascopy directly would close it; that host is blocked from the research
    container.
- **Cost under-count in the risk engine.** Fixed in risk-1.1.0: the full round trip (spread,
  commission and slippage on both fills) must now be ≤ 25% of the stop distance; before, only the
  spread counted. `RISK_MAX_COST_TO_RISK` can only lower it.
