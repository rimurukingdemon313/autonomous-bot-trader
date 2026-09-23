# risk/

**Status: empty. Phase 8.**

## Purpose
The independent risk engine: the final authority on whether a proposal is
executed, and the only code that computes a size.

## Responsibilities (when built)
Per-trade risk, daily loss, maximum drawdown, leverage, exposure,
concurrent positions, spread, slippage, abnormal conditions, duplicate
orders, broker and API failures, emergency shutdown, and a funded-account
compliance layer (rules supplied by the owner).

## Boundaries
- Cannot be bypassed by any flag, caller, confidence level or
  configuration.
- Risk decreases in response to adverse state, and **never increases**. No
  martingale, no revenge sizing.
- Fails closed.

## Binding contracts
[RISK_CONTRACT.md](../RISK_CONTRACT.md)
