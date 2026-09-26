# execution/

**Status: implemented** in [`aitrader/execution/engine.py`](../aitrader/execution/engine.py).

- The **intent is written before the order is sent**, with a deterministic
  client id derived from the decision.
- Right before submission it re-checks the kill switch (an unreadable one
  counts as active), pause, account type, tradability, and that the live
  price is still on the right side of the stop.
- **No write is ever retried.** `AmbiguousExecution` leaves the intent
  `UNKNOWN`; the only recovery is to find the order at the broker by its
  client id. It is never resent.
- On restart, every `UNKNOWN` intent is reconciled before any new decision.
  Positions the system did not open start it **paused**.
- It cannot change direction, size, stop or target. It can only refuse.

Tests: `tests/unit/test_execution.py`, `tests/unit/test_tradelocker_adapter.py`.

## Binding contracts
[EXECUTION_CONTRACT.md](../EXECUTION_CONTRACT.md)
