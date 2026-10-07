# Execution contract

How an approved decision becomes exactly one broker action, and how the
system knows what really happened.

```
AI → DECISION → RISK ENGINE → EXECUTION ENGINE → BROKER
```

**The AI does not connect to the broker.** Only the execution engine sends
orders, only through the broker layer, and only orders the risk engine
approved and sized.

---

## 1. Properties

Execution must be:

- **Idempotent.** One approved decision produces at most one order,
  however many times the path is traversed.
- **Duplicate-safe.** Every decision has a stable identity. A second
  attempt with the same identity is refused, and so is a new decision for
  a setup already open or pending.
- **State-aware.** Before acting, it reads the broker's actual positions and
  orders. It does not act on its own memory alone.
- **Reconnect-safe.** A dropped connection never causes a resend.

## 2. Writes are never retried

A broker write (place, modify or close) whose outcome is unknown (a
timeout, a dropped connection, a server error) **is never sent again**. A
resent order can become a second real position.

- The outcome is marked **ambiguous**.
- The **only** recovery is to query the broker for the resulting state and
  reconcile.
- Reads may retry with bounded exponential backoff and jitter. Writes may
  not.

## 3. Intent before action

The intent to place an order is persisted **before** the order is sent. On
restart, any intent without a known outcome is reconciled against the
broker before anything new is done.

## 4. Recovery after restart

On startup, before trading:

1. load persisted intents, positions and state;
2. read the broker's positions and orders;
3. reconcile the two, and record every difference;
4. resolve every ambiguous intent from broker evidence;
5. only then allow new decisions.

If reconciliation cannot complete, no new orders are placed.

## 5. Final checks before submission

Immediately before submission, execution re-checks: account type, kill
switch, the live spread against the approved limit, that the instrument is
tradable now, and that the order still matches what was approved. Any
failure cancels the order and records the reason.

## 5a. The hard risk gate is the last step

The execution engine cannot be built without a `HardRiskGate`. After its final checks it asks the gate, holding
the gate from authorisation to the broker's answer. A refusal is `BLOCKED` with the gate's reason, and nothing
reaches the broker. An approval carries a single-use permit, bound to the exact order, and the paper broker
fills nothing without one. A definite broker rejection releases the reservation. An ambiguous outcome keeps
it, counted as open risk, until reconciliation confirms or releases it. docs/HARD_RISK_GATE.md.

## 6. What execution may not do

It may not change direction, size, entry type, stop or target from what was
approved. It may only refuse.

## 7. Records

Every intent, submission, broker response, fill, slippage, modification,
close, ambiguity and reconciliation is journaled, with latency, the spread
at submission, and the version stamps of the decision that caused it.
