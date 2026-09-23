# Validation contract

How any claim of an edge is tested before it is believed.

---

## 1. Chronological splits only

Data is split **by time**, never at random. For any experiment:

```
TRAIN  →  [gap]  →  VALIDATION  →  [gap]  →  OUT-OF-SAMPLE (TEST)
```

- **Train** is used to fit.
- **Validation** is used to choose: models, hyperparameters, thresholds,
  features.
- **Out-of-sample** is used only to judge. Nothing is chosen from it.

Each experiment records the exact `TRAIN_START`, `TRAIN_END`,
`VALIDATION_START`, `VALIDATION_END`, `TEST_START` and `TEST_END`.

**Forbidden:** train on all data, test on the same data, and call it
success.

## 2. Walk-forward

A single split is one sample of luck. Walk-forward repeats it: train,
validate, test, then move the window forward and repeat.

- **Expanding** windows (training grows) and/or **rolling** windows
  (training has a fixed length) are used, whichever the question needs,
  and the choice is recorded.
- The out-of-sample result is the **concatenation of all test windows**,
  each produced by a model that never saw it.
- Consistency across windows is reported, not just the total.

## 3. Purging and embargo

A label that looks forward (for example "the outcome over the next N
bars") overlaps the start of the next segment. So:

- **Purge:** training or validation rows whose label window reaches into a
  later segment are removed.
- **Embargo:** a gap follows every boundary, at least as long as the
  longest label horizon plus the longest feature memory that matters.

Label contamination across segments is tested for, not assumed away.

## 4. Everything fitted is fitted on train only

This includes normalization statistics, scalers, cluster centres, regime
boundaries, feature-selection decisions, and anything else estimated from
data. A z-score computed over the whole series is a leak. Leakage tests
prove each of these is fitted without the later data
([docs/TESTING_PHILOSOPHY.md](docs/TESTING_PHILOSOPHY.md)).

## 5. Baselines

Every model is compared, **net of the same costs**, with:

1. **NO_TRADE**, which scores zero and is surprisingly hard to beat;
2. **random entries** at the same frequency, holding time and costs;
3. **simple heuristics**, such as the sign of recent momentum;
4. **the predecessor project's approaches**, where they apply.

A model that does not beat all the baselines out of sample has not found
an edge.

## 6. Statistics

Reported for every candidate. **No single number selects a model**, and
the highest profit never does.

- expectancy and average R per trade, after costs;
- profit factor, win rate, average win and average loss in R;
- Sharpe and Sortino of the periodic return series;
- maximum drawdown and time under water;
- tail risk (for example the worst 5% of outcomes);
- stability across walk-forward windows, instruments, years and regimes;
- number of trades, with small samples labelled **insufficient**;
- statistical significance, **corrected for every test in the registry**
  for that dataset (Holm or Bonferroni), and Sharpe deflated for the number
  of configurations tried;
- a permutation test: the real result against results with labels
  shuffled in time blocks;
- calibration: whether predicted probabilities and expected R match what
  was realised.

## 7. Robustness — try to destroy every good model

A candidate that looks good is attacked before it is believed:

- spread ×1.5 and ×2; slippage ×2; higher commission and financing;
- execution delayed by one bar;
- missing data (random bars removed);
- other instruments; other periods; other regimes;
- parameters perturbed around the chosen values (a result that sits on a
  sharp peak is fragile);
- Monte Carlo: bootstrapped trade sequences and random trade ordering, to
  produce drawdown and ruin distributions;
- volatility changes and regime shifts.

**If it collapses: REJECT.** If it survives, it may proceed.

## 8. Final holdout policy

The final holdout is one period of data that is:

- **unseen**: nobody has looked at it for any purpose;
- **untouched**: never used for training, feature selection, hyperparameter
  tuning, model selection, threshold selection, prompt tuning or strategy
  discovery;
- **protected**: the registry refuses any use of it except the documented
  final test;
- **versioned**: its exact boundaries and data version are recorded when
  it is sealed;
- **auditable**: every access is a registry entry.

Procedure:

1. The holdout is **chosen and sealed in Phase 1**, before any research
   touches the data. It is normally the most recent period available.
2. The final test runs only when a candidate has passed walk-forward and
   robustness, **and** the code, model and decision rule have been
   **frozen**, **and** the pass rule has been pre-registered.
3. The final test runs **once**, by a committed script, and records
   **PASS**, **FAIL** or **INCONCLUSIVE**.
4. **Nothing is modified on the basis of the holdout result.** The model is
   not adjusted until it passes. The holdout is not reopened because a
   model failed. It is not re-run in search of a better number.
5. After it is used, the holdout is **spent**, and the registry records it
   as contaminated. Any later final test needs data that did not exist at
   the time of the first one, which in practice means the passage of time
   or paper trading.

The cleanest holdout of all is the future. Paper trading is, in effect, a
holdout that no one could have seen.

## 9. Verdicts

- **PASS**: every pre-registered criterion is met.
- **FAIL**: any criterion is not met.
- **INCONCLUSIVE**: too few trades or too little time to tell. This is not
  a softer PASS; it is treated as not passed.
- **INVALID**: the experiment was flawed (for example, leakage was found
  afterwards). It stays in the registry with the reason.

## 10. What an edge must show

Before anything moves to paper trading, all of the following:

- walk-forward net expectancy with a **positive lower confidence bound**,
  after multiple-testing correction;
- it beats every baseline and the permutation distribution;
- it holds across instruments, years and regimes;
- it survives the robustness battery;
- its predictions are calibrated;
- the final holdout is **PASS**.
