# features/

**Status: implemented** in [`aitrader/features/store.py`](../aitrader/features/store.py).

23 features on complete H1 bars (momentum, trend, volatility, structure,
execution cost, tick activity, calendar), each declared with its family,
lookback and definition. `FEATURE_VERSION` is stamped on every decision.

- One function computes them for research, backtest and the live service;
  a test asserts the research matrix equals the production row exactly.
- A value at bar *i* uses bars up to *i* only. The causality checker
  recomputes every feature on history truncated at *i* and must match; it
  is itself tested against deliberately injected leaks.
- Too little history gives NaN, never a default.
- Smart-money-concept ideas enter only as features (range position,
  breaks of prior highs and lows), never as a rule that trades.

Tests: `tests/unit/test_features.py`.

## Binding contracts
[DATA_CONTRACT.md](../DATA_CONTRACT.md) · [VALIDATION_CONTRACT.md](../VALIDATION_CONTRACT.md)
