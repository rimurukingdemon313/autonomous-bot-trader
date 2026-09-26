# Audit: security, leakage, risk, architecture

Done after the build, against the code as it is, not as it was designed.
Every "yes" names the code and the test behind it. Every defect found is
listed with its fix. Where something is **not** verified, this document
says so.

Commands that reproduce the evidence:

    bash scripts/check.sh              # the suite
    python scripts/mutation_audit.py   # remove each guard, require a failing test

## 1. Defects found by this audit, and fixed

| # | Defect | Consequence | Fix | Test |
|---|---|---|---|---|
| 1 | "Scan now" started a cycle in its own thread, beside the scheduler's cycle and bar monitoring | two cycles could each see no open position on a symbol and each open one | one re-entrant lock serialises cycles, monitoring and reverts | `test_cycles_monitoring_and_scans_never_overlap` |
| 2 | Reverting learning deleted lesson versions and moved the knowledge counter backwards | the next lesson change reused a version number that the database holds UNIQUE, so every later cycle failed; the revert was also lost on restart | a revert appends restoring versions and is itself a new, higher version | `test_learning_revert_is_a_new_version_survives_restart_and_learning_continues` |
| 3 | Outcomes of skipped candidates existed only in memory | after a restart, objection penalties and lessons lost most of their evidence | journalled in an immutable `evaluations` table and replayed on start | `test_skipped_candidates_outcomes_survive_a_restart`, `test_a_full_journal_lets_a_restart_rebuild_the_same_experience` |
| 4 | The live service decided every hour; research and the knowledge base decide every 4th bar | live trading at a frequency no test had measured | the service decides at the cadence written on the knowledge card | `test_the_service_decides_at_the_cadence_the_knowledge_was_tested_with` |
| 5 | The knowledge base was loaded without checking it | a corrupted or swapped artifact would have been used | loaded only if SHA-256 matches the card; otherwise nothing loads and nothing decides | `test_a_knowledge_base_loads_only_if_it_matches_its_card` |
| 6 | Only 3 component versions were stamped on decisions | results could not be grouped by agent, risk or execution version | `stamp()` records all 13 components | suite |
| 7 | Four safety guards had no test that noticed their removal | a regression would have passed CI | tests added (streak reduction, ambiguous price scale, LIVE refusal reason, market-wide block) | docs/MUTATION_AUDIT.md |
| 8 | Log redaction had no test | a regression could leak a password into Railway logs | test added, plus a redaction mutant | `tests/unit/test_observability.py` |
| 9 | The dashboard called the judged period "out of sample" | the archive's exposure overlaps part of 2010-2016 | now "judged period", with the pre-registered verdicts | — |
| 10 | An unfamiliar-state verdict from missing inputs looked like a strange market | an operator could not tell a feed without tick volume from a real outlier | the reason names the missing inputs | `test_an_unfamiliar_verdict_names_the_inputs_it_could_not_read` |
| 11 | Reflection read post-mortems from memory only | after a restart, loss-cause history restarted from zero | the last 500 post-mortems are reloaded from the journal at start | `test_postmortems_survive_a_restart_for_reflection` |
| 12 | The mutation audit itself left compiled mutants cached (same-size edit, same second) | a later run tested a mutant, not the code | no bytecode written during the audit; the module's cache is removed on restore | — |
| 13 | The image ran as a non-root user, and Railway mounts volumes as root | on Railway the service could not create its database and crashed on start; found by building the image and mounting a root-owned directory at `/data` | `docker-entrypoint.sh` gives `/data` to uid 10001, then drops privileges before the service starts | checked in a local container: root-owned volume, database created under uid 10001, process runs as 10001, survives `docker restart` |
| 14 | A startup failure crashed the process, so nothing answered | the platform showed a crash loop with no reason at the URL | the service serves 503 with the reason (naming `DATA_DIR`) and never trades | `test_a_failed_startup_serves_its_reason_and_never_trades` (the real process, over HTTP) |

## 2. Security

| Check | Result | Evidence |
|---|---|---|
| Secrets in the repository, **full history** | none. Searched: the credential identifiers the owner once pasted in chat, `PASSWORD=` with a value, `sk-…`, JWTs, `ghp_…`, quoted API keys | `git log -p --all` scan |
| Where secrets come from | environment variables only (Railway Variables); `.env.example` has names, no values | `.env.example`, `TradingConfig.from_env`, `LLMConfig.from_env` |
| Secrets in logs | redacted at the sink: secret env values, bearer tokens, JWTs, JSON secret keys | `test_observability.py`; mutant `log-redaction` |
| Secrets in the API / dashboard | none served; config is exposed only through `public()` | `test_no_secret_is_ever_served` |
| Access token leaves the broker adapter | no; the demo guard reads allow-listed claims as evidence only | `broker/tradelocker/demo_guard.py` |
| Controls | stop and pause need no token (making things safer is never locked); resume, clear-stop, scan, revert and verify need `DASHBOARD_TOKEN`, compared in constant time; with no token configured they are refused, not open | `test_resuming_or_initiating_needs_the_token`, `test_with_no_token_configured_dangerous_controls_are_refused_not_open`; mutant `token` |
| Cross-site | no CORS headers: a browser cannot read the API from another origin, and a cross-origin request carrying the token header fails its preflight. A plain cross-site POST can only reach pause and kill, which are safe by design | `service/server.py` |
| Static files | path traversal refused | `test_static_dashboard_is_served_and_path_traversal_is_refused` |
| Container | the service runs as uid 10001 (root only long enough to take ownership of the volume), numpy only, health check | `Dockerfile`, `docker-entrypoint.sh`; checked in a built image |

**Not done:** no external penetration test. There is no rate limiting on
the token check. A long random token (see OPERATIONS.md) is the defence.

## 3. Data leakage

| Path | Guard | Evidence |
|---|---|---|
| Features | every feature at bar *i* equals the feature on history truncated at *i*; five kinds of injected leak are detected | `test_features.py` |
| Resampling | only complete buckets; a forming bar is never emitted | `test_resample_does_not_leak_a_forming_bar_even_if_later_data_exists` |
| Live bars | the TradeLocker feed drops a bar whose close is after `as_of` | `adapter.bars`: `closed = t + 3600 <= as_of` |
| Pattern memory | an outcome is visible only after its `resolve_time` | `test_an_outcome_is_invisible_until_it_has_resolved`; mutant `memory-point-in-time` |
| Labels and tracker | identical by construction; the tracker resolves bar by bar | `test_tracker_matches_labels_exactly` |
| Regime model | quantiles fitted on rows decided before each test year minus a 5-day embargo | `backtest/runner.py`, `test_regime_fit_refuses_rows_after_its_training_cutoff` |
| Lessons | validated only on outcomes that resolved after the lesson was created | `learning/experience.py` |
| Whole system | changing the future does not change any past decision | `test_changing_the_future_does_not_change_the_past` |
| Final holdout | the loader truncates at 2017-01-01 without a key; single use | `test_registry_and_store.py`; mutants `holdout-loader`, `holdout-single-use` |
| Language model | excluded from every backtest (training-data look-ahead cannot be ruled out) | MODEL_CONTRACT.md §7 |
| Selection | every configuration is counted in the registry, archive included; thresholds are Bonferroni | `research/registry.jsonl` |

**Known exposure:** the archive tested this universe on 2012-11 → 2022-03.
PR-001's judged period (2010-2016) overlaps it from 2012-11. That is
declared in the registry and counted in the threshold. It is why a pass
would still need the sealed holdout.

## 4. Risk

| Check | Result | Evidence |
|---|---|---|
| Sole sizing authority | only `risk/engine.py` computes a quantity; agents, synthesis and execution never do | code search; `test_risk.py` |
| Ceiling | 1 % per trade whatever the configuration (environment values are clamped) | `test_risk_configuration_cannot_exceed_the_ceiling`; mutant `risk-ceiling` |
| After losses | risk halves every 3 consecutive losses, floors at 0.25×, never rises | `test_a_losing_streak_actually_reduces_risk_and_a_win_resets_it`, `test_risk_only_ever_decreases_after_losses` |
| Limits | daily loss 2 %, drawdown 8 % (halt until a person clears it), 3 positions, 2 per currency, 1 per instrument, leverage, spread against the stop, minimum R:R, minimum stop, quote age | `test_risk.py` |
| AI cannot bypass | a language model can only add objections; its directional weight is its measured forward reliability, starting at 0; it never sees the risk engine's inputs as writable | `test_llm_objections_are_subtractive`, `test_llm_agreement_cannot_lower_the_bar` |
| Learning cannot bypass | lessons can only block; penalties are clamped | ARCHITECTURE.md Amendment 1 |
| Execution | cannot change direction, size, stop or target; re-checks kill switch, pause, demo status, tradability and price vs stop right before sending | `test_execution.py`; mutants `exec-*` |

## 5. Architecture

- The flow is data → features → regime → memory → agents → synthesis →
  risk → execution → broker → outcomes → learning, in one orchestrator,
  shared by the backtest and the service
  (ARCHITECTURE.md, implementation map).
- Authority flows upward: any layer can refuse, none can override a
  refusal. Verified by the mutation audit (docs/MUTATION_AUDIT.md).
- Research and production share the same feature, agent, synthesis, risk
  and execution code. The one research/production difference found, the
  decision cadence, was fixed (defect 4).
- **Accepted simplifications.**
  - SQLite, not a server database: one process, one volume, and immutable
    tables with hash chains.
  - Exact nearest-neighbour search, not a vector database: it is fast
    enough at this scale.
  - One process runs the API, the scheduler and the monitor.

## 6. The twenty questions

| # | Question | Answer | Evidence |
|---|---|---|---|
| 1 | Is the Orchestrator actually functional? | **Yes** | `orchestrator/core.py` drives every backtest and the service; `test_backtest_runs_end_to_end_and_records_everything` |
| 2 | Are agents genuinely separated by responsibility? | **Yes** | five classes with separate inputs and outputs; the adversary can never support (`test_the_adversary_never_supports`) |
| 3 | Is evidence synthesis real? | **Yes** | analogue lower bound minus measured penalties; agreement cannot lower the bar (`test_major_objections_raise_the_bar_instead_of_voting`, `test_llm_agreement_cannot_lower_the_bar`) |
| 4 | Is the Risk Engine deterministic and authoritative? | **Yes** | pure function of its inputs; the only sizing code; mutation audit |
| 5 | Can AI bypass risk controls? | **No** | objections only; forward-measured weight starting at 0; no path from a model to size or execution |
| 6 | Is memory persistent? | **Yes** | SQLite on the volume, `memory_live.npz`, and experience rebuilt from journalled trades and shadow outcomes (defects 3 and 11) |
| 7 | Are trade records immutable? | **Yes** | triggers refuse UPDATE and DELETE; hash chains detect edits that bypass them (`test_db.py`; mutant `db-immutable`) |
| 8 | Does post-trade analysis actually happen? | **Yes** | a post-mortem for every closed trade, linked to its episode (`test_every_trade_can_be_reconstructed_from_the_journal`) |
| 9 | Does reflection actually happen? | **Yes** | every 25 closed trades: calibration, shadow vs traded, loss causes, drift, hypotheses; stored in `reflections` |
| 10 | Are learning updates versioned? | **Yes** | every lesson change is a knowledge version, stamped on later decisions |
| 11 | Can learning be reverted? | **Yes, since defect 2 was fixed** | `POST /api/control/knowledge/revert` (token), as a new version that survives restart |
| 12 | Is historical data protected from future leakage? | **Yes, with a declared exposure** | section 3 |
| 13 | Are backtests realistic? | **Mostly** | real bid/ask and measured spreads, pessimistic fills, stop first, gaps at the open. Slippage, commission and swap are declared approximations. No partial fills, and no rejections or requotes |
| 14 | Is execution isolated from reasoning? | **Yes** | execution receives an approved verdict and may only refuse it |
| 15 | Is duplicate execution protected? | **Yes** | deterministic client ids; `decision_id` UNIQUE on intents; a write is never resent; the cycle lock (defect 1) |
| 16 | Does the system fail closed? | **Yes** | missing data, an agent error, a malformed model reply, an unreadable kill switch, a missing or mismatched knowledge base, unverified demo status: each leads to no trade (mutation audit) |
| 17 | Does Railway restart recovery work? | **Verified in the production image locally, not on Railway itself** | the image was built from the Dockerfile and run with a root-owned volume at `/data`, as Railway mounts one: healthy, knowledge VERIFIED, and state kept across `docker restart`. The tests cover the kill switch, paper account, lessons, experience and intents across a restart, and an intent interrupted mid-submit is reconciled by query. A real Railway deploy has not been exercised from here |
| 18 | Is the dashboard using real backend state? | **Yes** | every panel reads an endpoint; missing values show N/A; no generated or sample data in the frontend |
| 19 | Are secrets protected? | **Yes** | section 2 |
| 20 | Can every trade decision be reconstructed later? | **Yes** | `test_every_trade_can_be_reconstructed_from_the_journal`; `GET /api/decisions/{id}` |

## 7. Not verified from this environment

- The TradeLocker adapter against the real API. The network policy blocks
  TradeLocker, so it is tested against a fake transport only.
- A Railway deployment itself. The production image was built and run
  locally, with a root-owned volume and a restart. Railway's own build and
  volume were not exercised.
- Any language model. Weights and model APIs are unreachable, so the LLM
  layer is tested against a fake transport only.
- Live-feed semantics. TradeLocker's spread is the current quote spread,
  not Dukascopy's per-bar mean, and its tick volume may be scaled
  differently. Both enter the familiarity check. If they shift the
  distribution, the system becomes more likely to say "unfamiliar", which
  fails safe, and the dashboard names the inputs.
