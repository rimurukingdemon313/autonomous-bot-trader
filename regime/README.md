# regime/

**Status: implemented** in [`aitrader/regime/model.py`](../aitrader/regime/model.py).

- Labels (trending up or down, ranging, transition, abnormal; low, normal
  or high volatility) come from **quantiles of the training rows only**,
  stored with the model version.
- **Familiarity**: Mahalanobis distance to the training distribution. Beyond
  the training 99.5th percentile the state is UNFAMILIAR and the decision is
  NO_TRADE.
- Persistence of each label on the training data is written to the
  knowledge card (`scripts/build_knowledge.py`). Whether a label is
  informative is measured, not assumed: PR-001 reports R by regime for
  every variant. A label that proves uninformative stays a description; it
  gates nothing except ABNORMAL and UNFAMILIAR.

Tests: `tests/unit/test_regime_and_patterns.py`.

## Binding contracts
[VALIDATION_CONTRACT.md](../VALIDATION_CONTRACT.md)
