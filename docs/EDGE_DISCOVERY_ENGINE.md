# The edge-discovery engine

The objective is to **find trading edges**, BUY or SELL, that keep a positive expected value
after realistic costs, out of sample. Win rate is not the objective and neither is
NO_TRADE. When the engine has found nothing, it ABSTAINS and says why (CLAUDE.md rule 8).
The audit that motivated this design is in [EDGE_DISCOVERY_AUDIT.md](EDGE_DISCOVERY_AUDIT.md).

There are two halves, joined only by a file a person writes.

```
RESEARCH (offline, research code only)                   LIVE (service, never imports research)
─────────────────────────────────────                    ──────────────────────────────────────
hypotheses: documented methods, screens, models,         every 15 minutes (SCAN_TIMEFRAME=M15):
  learned losses, AI drafts                                H4 features  -> regime / macro context
     -> preregistration (registry counts every test)       H1 features  -> intermediate structure
     -> walk-forward / confirmatory judgement              M15 features -> execution
     -> 12-check battery + 5-analyst board                    -> EDGE ENGINE (promoted edges only)
     -> edge registry (research/knowledge/                    -> RISK ENGINE (sole sizing authority)
        edge_registry.json)                                   -> execution guards -> DEMO / paper
     -> single-use holdout
     -> person reviews -> models/artifacts/promoted_edges.json ──────────────┘
```

## Research half

| Stage | Code | What it guarantees |
|---|---|---|
| Features | `research/discovery/primitives.py`, `catalog.py`, `universe.py` | Every feature has a provenance record and passes the leakage gate before it may be used |
| Exits, studied jointly with entries | `research/discovery/exits.py` (E1–E8 on H1, D1–D5 on D1) | An entry is judged with a declared exit, never the best exit after the fact. Each outcome records MFE and MAE |
| Costs | `research/labels.py` `CostModel` | Measured spread paid on entry; slippage 0.1 pip per fill; commission 0.7 pip per round trip; swap per night. Stress: costs ×1.5, slippage ×2 |
| Screening | `research/discovery/screen.py` | BH-FDR within the screen; week-clustered standard errors |
| Walk-forward | `research/lab.py` | Expanding yearly folds; training only on outcomes resolved before the fold, minus a 5-day embargo; random baseline; robustness |
| Confirmation | `research/discovery/confirm.py` | Fixed hypotheses judged once on a segment nothing was fitted on |
| Battery | `research/discovery/battery.py` | 12 checks: trades, significance, random, permutation, costs, delay, perturbation, years, instruments, leave-one-out, regimes, outliers |
| Board | `research/discovery/board.py` | Market, opportunity, risk, adversarial and reviewer analysts, plus optional AI objections. No voting: any blocking objection holds |
| Registry | `research/registry.py` | Every test on a period is counted; the next test's threshold rises (Bonferroni) |
| Edge registry | `research/discovery/edges.py`, `scripts/edge_registry.py` | One record per judged hypothesis, rebuilt from the evidence |
| Loss forensics | `research/discovery/forensics.py` | Each loss classified by counterfactuals on the same bars |
| Strategy library | `research/discovery/library.py` | Documented methods as testable principles, with conflicts kept |

**Expected value, not win rate.** Every result is expressed as net R per trade after costs,
with its standard error. The battery's gross/net split shows how much of the result is
cost. Worse-cost (×1.5 / ×2) and one-bar-late results are reported beside it.

**Overfitting control.**

- Pre-registration is committed before any judged data is read.
- Every configuration counts against the budget.
- A frozen threshold is taken from the registry.
- Perturbation checks move the tercile edges.
- Parameters are few: complexity is recorded per edge.

**Regimes.** They are measured, not assumed. Every judged edge reports its mean per
er120 × vol_ratio cell. A cell significantly negative fails the regime check.

## Live half

### The M15 scanner

It is `SCAN_TIMEFRAME=M15` in `service/config.py`, with `decision_interval_s` of 900 seconds
in `service/runtime.py`. It runs only with `DECISION_MODE=edges`, `llm_trader` or
`trading_room`. The evidence mode keeps its H1 cadence, because its knowledge card was
validated on it.

At every M15 close, `orchestrator/core.py` `_frames` computes causal features on:

- M15 (execution);
- H1 (intermediate);
- H4 (context).

Each is read from its own last closed bar.

### The edge engine

`aitrader/decision/edge_engine.py`, via `agents/edge_trader.py`.

- **Sides.** BUY and SELL edges are evaluated independently.
- **Conditions.** An edge matches only when every one of its conditions is known and true. A
  missing feature is never a match.
- **Score** is a conservative expected value after today's costs:

  ```
  score = out-of-sample mean R − 1 × its standard error − max(0, today's cost − cost assumed in testing)
  ```

- **Decision.** The best positive score becomes BUY or SELL. It carries entry, stop,
  target, maximum hold, the edge id, its trial and the whole evidence report.
- **No duplicates.** An instrument with an open position is not doubled, and a setup already
  decided is not re-decided (the setup id is deterministic per edge, bar and side).
- **Health.** An edge whose live record is DEGRADED or RETIRED is not used. `edge_health`
  tells normal variance from decay:
  - DEGRADED: at least 20 trades, and the live mean is more than 2 standard errors below
    the tested mean;
  - RETIRED: at least 40 trades, and the live mean is below zero with 95% confidence.
- **Sizing and approval.** The risk engine sizes and may refuse. An edge file that carries
  any size field is refused at load.

**Today there is no promoted edge**, so the engine abstains every time, with the reason
"no promoted edges exist: the research has not validated one". That is the honest output
until a hypothesis passes.

### Correlated stacking

The risk engine's exposure limits apply to every mode unchanged. The edge engine adds the
per-instrument rule above.

## AI's role: researcher, never trader

In research, a language model may:

- draft hypotheses, from a closed vocabulary only (`test_a_language_model_may_draft_hypotheses_only_from_the_closed_vocabulary`);
- raise objections on the board.

A draft is charged against the registry like any other test, and is prospective only.

The model never sizes, never promotes, never overrides a failed check. In the live
`llm_trader` and `trading_room` modes, the model proposes and the risk engine disposes.

## Learning from losses

1. Every closed trade is classified: `learning/review.py` live, `forensics.py` in research.
2. Lessons are hypotheses, with the stages CANDIDATE → VALIDATED | REJECTED → RETIRED
   (`learning/experience.py`).
3. A lesson needs a significant sample, and is validated only on outcomes resolved **after**
   it was created.
4. A validated lesson can only block. It can never add risk.
5. One loss changes nothing (`test_one_loss_or_one_win_changes_nothing`).

## Tests for the required properties

| Property | Tests |
|---|---|
| No look-ahead | `test_changing_the_future_does_not_change_the_past`, `test_the_causality_check_catches_an_injected_one_bar_leak`, `test_a_context_feature_reads_only_the_last_closed_higher_timeframe_bar` |
| No leakage | `test_the_leakage_gate_rejects_a_leaky_feature_and_admits_a_causal_one`, `test_the_truncation_test_catches_a_leak_through_another_instrument` |
| Realistic costs | `test_the_spread_is_paid_on_entry`, `test_a_wider_spread_can_only_make_outcomes_worse`, `test_an_edge_that_costs_eat_fails_the_cost_stress`, `test_todays_extra_cost_is_charged_against_the_edge` |
| Walk-forward separation | `test_walk_forward_trains_only_on_outcomes_resolved_before_each_fold`, `test_a_segment_purges_rows_whose_outcome_would_cross_its_end` |
| Deterministic backtests | `test_results_are_reproducible_from_the_registered_spec`, `test_decision_ids_are_deterministic_for_idempotency` |
| Edge registration and retirement | `tests/unit/test_discovery_edges.py`, `test_health_tells_normal_variance_from_decay`, `test_degraded_retired_or_unpromoted_edges_are_not_used` |
| Learning from losses | `tests/unit/test_discovery_forensics.py`, `test_one_loss_or_one_win_changes_nothing`, `test_a_losing_streak_actually_reduces_risk_and_a_win_resets_it` |
| BUY and SELL candidates | `test_buy_and_sell_are_searched_independently_and_the_stronger_evidence_wins`, `test_sells_mirror_buys_and_pay_the_spread_on_the_ask` |
| Risk Engine integration | `test_an_edge_decision_is_sized_and_approved_only_by_the_risk_engine`, `test_an_edge_file_can_never_carry_a_size`, `test_only_the_risk_engine_computes_a_position_size` |
| Abstain with a reason | `test_nothing_promoted_means_abstain_and_it_says_why` |

## Promotion (a person's step)

An edge is promoted only if **all** of the following hold:

- it is VALIDATED in the edge registry;
- it passed the single-use holdout under a sole pre-registered final test;
- a person has read its evidence.

The person writes the edge to `models/artifacts/promoted_edges.json` with status
`PAPER_TEST` or `DEMO_TEST`. `LIVE_APPROVED` exists as a name only: the demo guard refuses
live endpoints whatever the file says.
