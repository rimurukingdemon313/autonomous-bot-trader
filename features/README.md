# features/

**Status: empty. Phase 2.**

## Purpose
The single feature store: the one definition of every feature, used
identically by research, training, backtesting, paper trading and
production.

## Responsibilities (when built)
- Each feature records: name, version, timestamp, instrument, timeframe,
  source and calculation metadata.
- A feature value at decision time T depends only on information available
  at or before T.
- Missing inputs produce a missing value, never a default.

## Boundaries
- There is no separate "backtest" or "live" calculation of any feature.
- No indicator is privileged. A feature stays only if it adds independent
  information and improves out-of-sample robustness.

## Binding contracts
[DATA_CONTRACT.md](../DATA_CONTRACT.md) · [ENGINEERING_RULES.md](../ENGINEERING_RULES.md) §2 ·
[docs/TESTING_PHILOSOPHY.md](../docs/TESTING_PHILOSOPHY.md)
