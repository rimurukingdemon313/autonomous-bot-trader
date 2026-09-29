# Edge-discovery audit

A forensic audit of why the system has not made money in testing. Every number below is
read from a committed artifact, named beside it. Where the evidence cannot answer a
question, the audit says so and does not estimate.

## 1. The short answer

The system does not lose because it is too cautious. It loses because **no hypothesis
tested so far has a gross edge larger than the cost of trading it**.

- On H1, the gross expectancy of every declared entry-and-exit pair is within ±0.03R of zero.
- The costs are 0.09–0.21R per trade.
- Every filter we have built makes the result less bad than random entries. None makes it
  positive.

| Horizon | Gross expectancy | Cost per trade | Source |
|---|---|---|---|
| H1 | ±0.03R, every exit | 0.09–0.21R. E1 0.139R, E2 0.105R, E4 0.087R | DP-001 discovery-segment decomposition, `research/results/DP-001-summary.md` |
| D1 | — | About a fifth of the H1 cost per unit of risk. 14.9% of cells had a positive net mean, against 0% on H1 | `research/results/DP-002-summary.md` |

## 2. Is NO_TRADE the problem?

It is not the cause, but it is real. In PR-001's full-period ablation, 97.3% of 125,992
decisions were NO_TRADE and 826 approved proposals were refused by the risk engine
(variant B-nohalt; `data/results/PR-001/B-nohalt.json`).

The test of whether abstaining costs money is to force the trades and look. Every program
since DP-001 does exactly that: it trades **every** bar where a condition holds, with no
confidence gate and no AI veto. The results are no better.

| Evidence | Trades | Net mean R | What it shows |
|---|---|---|---|
| DP-001, 1,734 H1 cells, every bar the condition holds | 12,123 for the best-populated model configuration | best cell −0.089R; model E1 −0.118R | more trades, same sign |
| SL-002, the Breedon–Ranaldo local-hours effect | 8,901 | −0.105R (t −8.0) | a documented effect traded every day is still negative |
| WF-002, stumps model on every 4th H1 bar | 1,328 | −0.126R | a model trading freely is no better than random |
| PR-001 R-nohalt, random entries through the same pipeline | 3,143 | −0.159R | what "just trade more" costs |

**Conclusion.** Removing the abstention would have lost more money, not less. The
abstention is a symptom — nothing in the pipeline has a positive expectancy to trade on —
not the disease. The system's objective is now to *find* an edge (see
[EDGE_DISCOVERY_ENGINE.md](EDGE_DISCOVERY_ENGINE.md)). NO_TRADE remains the correct output
when none has been found (CLAUDE.md rule 8). It is no longer treated as success.

## 3. The multi-agent pipeline (PR-001)

These numbers come from `research/results/PR-001-judgement.json`. The run covered
2010-2016, 12 pairs and H1 bars, and was pre-registered.

### Primary, as registered

Every variant hit its drawdown halt during 2010 and made 24–60 trades. All four
hypotheses (H1–H4) are **FAIL**.

### Exploratory, with the halt removed

This part is not a verdict: it was declared exploratory before it ran.

| Variant | Trades | Mean R | t | Win rate | Profit factor (R) | Max drawdown |
|---|---|---|---|---|---|---|
| B: memory | 2,577 | −0.053 | −1.99 | 35.7% | 0.92 | −54% |
| C: memory + learning | 2,928 | −0.072 | −2.90 | 35.1% | 0.89 | −58% |
| R: random entries | 3,143 | −0.159 | −7.38 | 36.5% | 0.76 | −87% |

- **The filters improve on random.** C vs R: +0.087R, Welch t 2.65. B vs R is about +0.1R.
  This is the only positive finding in the project's history, and it is *relative*: better
  than random, still below zero.
- **Learning did not help.** C vs B: −0.019R (t −0.53).
- **One source produced most of the trades.** The analog (k-NN) source made 85% of B's
  trades, at −0.043R. Every rule family was negative on its own.

## 4. Why the trades lost

### PR-001: calculated by `learning/review.py`

`review.py` classifies every closed losing trade from its recorded price path. The counts
below are from each variant's `loss_causes`.

| Cause | B: losers | B: share of R lost | C: share of R lost | R: share of R lost |
|---|---|---|---|---|
| NORMAL_VARIANCE | 784 | 46.9% | 45.6% | 41.0% |
| REGIME_SHIFT | 463 | 28.2% | 28.6% | 20.6% |
| EXIT_MANAGEMENT | 213 | 12.9% | 12.8% | 12.5% |
| ENTRY_TIMING | 197 | 12.1% | 12.9% | 20.1% |
| THESIS_WRONG | 0 | 0% | 0% | 5.7% |

Losers exited on the stop 1,577 times out of 1,657 in B.

**Reading.** Almost half the R lost is ordinary variance around a small negative mean. That
is exactly what a strategy with no edge looks like: there is no single fixable error to
remove.

Against random entries, the filters **halve the entry-timing and thesis-wrong losses**
(ENTRY_TIMING falls from 20.1% to 12.1%). That is where their +0.1R comes from. Nothing in
the table points to a change that would turn −0.05R into a positive number.

### New loss forensics: counterfactual, per trade

`aitrader/research/discovery/forensics.py` classifies each loss by what the same bars show
would have happened otherwise. The priority order is fixed:

1. COSTS: a gross winner that became a net loser;
2. EXIT_GAVE_BACK: reached +1R, then lost;
3. STOP_TOO_TIGHT: a stop twice as wide would have won;
4. ENTRY_TIMING: one bar earlier or later would have won;
5. WRONG_DIRECTION: never reached +0.25R, and the opposite side would have won;
6. NORMAL_VARIANCE.

`tests/unit/test_discovery_forensics.py` tests each cause on a path built so the answer is
known. It is applied to the walk-forward trades in the experiment log where a result
records them.

## 5. Are the backtests themselves honest?

Each bias below is checked by a test that fails when the bias is injected.

| Bias | Guard | Test |
|---|---|---|
| Look-ahead in features | Causality and truncation tests: changing the future must not change any past feature | `test_changing_the_future_does_not_change_the_past`, `test_the_causality_check_catches_an_injected_one_bar_leak`, `test_the_truncation_test_catches_a_leak_through_another_instrument` |
| A forming bar used as closed | Resampling and bar availability | `test_resample_does_not_leak_a_forming_bar_even_if_later_data_exists`, `test_bars_exclude_the_forming_bar_and_only_the_latest_spread_is_known` |
| Label leakage across folds | Walk-forward trains only on outcomes resolved before each fold, minus an embargo | `test_walk_forward_trains_only_on_outcomes_resolved_before_each_fold`, `test_a_segment_purges_rows_whose_outcome_would_cross_its_end` |
| Higher-timeframe context leakage | H1/H4 context is read from the last **closed** higher bar | `test_a_context_feature_reads_only_the_last_closed_higher_timeframe_bar` |
| A leaky feature entering research | Leakage gate at pre-registration | `test_the_leakage_gate_rejects_a_leaky_feature_and_admits_a_causal_one`, `test_a_leaky_feature_stops_preregistration_and_is_remembered` |
| Understated costs | Spread paid on entry at the measured bid/ask; slippage, commission and swap charged; a wider spread can only hurt | `test_the_spread_is_paid_on_entry`, `test_costs_and_a_delayed_entry_are_charged`, `test_a_wider_spread_can_only_make_outcomes_worse`, `test_time_exit_on_a_dead_market_costs_exactly_the_frictions` |
| Selection bias and multiple testing | Every test ever run on a period is counted, and the next threshold rises (Bonferroni over the registry, BH-FDR within a screen) | `research/registry.jsonl`; `docs/DISCOVERY.md` § Multiple testing |
| Non-determinism | Seeds fixed; results reproduce from the registered spec | `test_results_are_reproducible_from_the_registered_spec` |
| Peeking at the holdout | 2017 onward is sealed: the loader truncates at the seal without a single-use key. The archive experiments that read 2017–2022 before the seal existed are declared as prior exposure, not hidden | `test_loader_truncates_at_the_seal_without_a_key`, `test_exposure_before_the_seal_is_declared_not_blocking` |

The live dashboard's six trades (17% wins, −0.1R) are too few to say anything. With six
trades, a strategy with a true +0.2R edge would show a negative mean about a third of the
time.

## 6. What has been ruled out, and what has not

**Ruled out on our data.** All of these fail after costs, out of sample, under the
registry's multiple-testing threshold:

- price-only H1 features in the declared space (DP-001);
- the same on D1 (DP-002);
- published time-series momentum and moving-average trend (CP-001);
- Donchian breakout, trend pullback and narrow-range breakout, both sides (SL-001);
- local-hours depreciation (SL-002);
- a boosted-stumps model on the 23 production features, walked forward (WF-002);
- cross-sectional currency momentum on the seven majors (XS-001).

The complete list, with numbers, is in [TRADING_EDGE_REGISTRY.md](TRADING_EDGE_REGISTRY.md).

**Not ruled out, because it could not be tested here.**

- **Carry and PPP value.** They need interest-rate and price-level data. FRED, BIS and ECB
  are blocked by this environment's network policy.
- **Cross-sectional momentum beyond the majors.** XS-001 tested it on the seven USD majors and rejected it (−0.13R and −0.11R). The minor currencies where the paper finds it are not in our data.
- **Order flow, positioning and market making.** No data.

These remain RESEARCHED in the strategy library, not REJECTED.

**One pattern worth recording, but not an edge.** All three SELL-side trend forms judged
on D1 had positive means: CP-001-T2 +0.19R, CP-001-T4 +0.21R and SL-001-02 +0.17R. Every
BUY-side form was at or below zero.

None of the three was significant (t 0.6–1.0 against a required 3.2). CP-001-T2 earned
+0.86R per trade in 2014 and lost in 2013 and 2016, which is the signature of one episode
(the 2014–15 US dollar rally), not a rule. It is recorded as an **UNCERTAIN CONCLUSION**.
Testing it would need data the holdout seals, or data recorded from now on.
