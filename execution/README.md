# execution/

**Status: empty. Phase 9.**

## Purpose
Turn an approved, sized decision into exactly one broker action, and
establish what actually happened.

## Responsibilities (when built)
- Idempotent, duplicate-safe, state-aware, reconnect-safe order handling.
- The intent is persisted before any order is sent.
- Reconciliation on restart before any new order.
- Final pre-submission checks: account type, kill switch, spread,
  tradability, and that the order still matches its approval.

## Boundaries
- **Writes are never retried.** An ambiguous outcome is resolved by querying
  the broker.
- It may not change direction, size, stop or target. It may only refuse.

## Binding contracts
[EXECUTION_CONTRACT.md](../EXECUTION_CONTRACT.md) · [RISK_CONTRACT.md](../RISK_CONTRACT.md)
