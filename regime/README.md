# regime/

**Status: empty. Phase 6.**

## Purpose
Describe the market context, and decide how **familiar** the current
state is compared with the data the models learned from.

## Responsibilities (when built)
- Regime descriptions (for example trend, range, high or low volatility,
  transition, abnormal), **only where the data supports them**: they must
  be persistent and informative, or they are dropped.
- A familiarity / out-of-distribution measure. An unfamiliar state forces
  NO_TRADE.

## Boundaries
- No fixed list of regimes is assumed.
- Regime boundaries are fitted on training data only.

## Binding contracts
[VALIDATION_CONTRACT.md](../VALIDATION_CONTRACT.md) · [MODEL_CONTRACT.md](../MODEL_CONTRACT.md) §2
