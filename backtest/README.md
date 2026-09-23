# backtest/

**Status: empty. Phase 4.**

## Purpose
Historical simulation used by validation and walk-forward.

## Responsibilities (when built)
- Use the **same** feature definitions, decision logic and risk rules as
  production, with the same lookback the live system has.
- Fill pessimistically: at the next available price after the decision,
  with spread, slippage and commission. When stop and target fall in the
  same bar, assume the stop. Financing is charged where it applies.
- Record every declared cost approximation with the results.

## Boundaries
- Never reads data after the decision time.
- Results are evidence only under the validation contract. A backtest by
  itself proves nothing.

## Binding contracts
[VALIDATION_CONTRACT.md](../VALIDATION_CONTRACT.md) · [DATA_CONTRACT.md](../DATA_CONTRACT.md)
