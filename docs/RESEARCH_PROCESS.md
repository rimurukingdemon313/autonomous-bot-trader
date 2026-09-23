# Research process

The day-to-day procedure that implements [RESEARCH_CONTRACT.md](../RESEARCH_CONTRACT.md).

## The loop

```
Observation → Hypothesis → Experiment → Validation → Out-of-sample test
  → Robustness test → Version → Deployment candidate
```

1. **Observe.** Something in the data, in a journal or in the literature
   suggests a relationship. Or an error analysis of a losing trade does.
2. **State the hypothesis** so it can fail: what, where, when, and what
   result would refute it.
3. **Pre-register it**: data ranges and their roles, features, model,
   parameters and search space, costs, pass rule. Commit it. Register it.
4. **Build the test**, and commit any clarifications before looking at
   results.
5. **Train, then validate**, on their own segments.
6. **Judge out of sample**, by walk-forward.
7. **Attack it** with the robustness battery.
8. **Record the verdict**, whatever it is.
9. **If it passed**, version it as a deployment candidate. It still has to
   face the final holdout and the lifecycle.

## Learning from a losing trade

```
TRADE RESULT → ERROR ANALYSIS → HYPOTHESIS → EXPERIMENT → VALIDATION → NEW VERSION
```

Error analysis first asks: **was this loss inside the predicted
distribution?** A model that predicts a 45% chance of success will lose
more than half its trades. Losses that match the prediction are variance,
not errors, and they change nothing.

Only a pattern of outcomes **outside** the predicted distribution is
evidence of a systematic error. That evidence becomes a hypothesis, and
goes through the loop above.

A loss never leads to: increased risk, martingale, a revenge trade, a
doubled size, or a violated drawdown rule.

## The forbidden loop

```
Loss → change random parameters → backtest again → repeat until profitable
```

It is forbidden because it always ends in "success". Given enough
attempts, some parameter set fits the past by chance. The registry exists
so that the number of attempts is visible and is charged against every
result.

## Budgets

Every dataset has a finite amount of evidence in it. Each test spends
some: the significance bar for the next test rises. When the bar is higher
than any plausible edge could clear, research on that dataset stops, and
new data (usually the passage of time) is needed. That is a normal end
state, and is reported as such.
