# broker/

**Status: implemented** in [`aitrader/broker/`](../aitrader/broker/).

| File | What it does |
|---|---|
| `base.py` | The `Broker` and `MarketFeed` interfaces, and the errors the execution engine understands (`AmbiguousExecution`, `BrokerRejected`). |
| `paper.py` | The paper account ($20,000 by default), pessimistic fills, state in the database so a restart resumes it; a client id is accepted once. |
| `tradelocker/` | TradeLocker client, transport, history, symbols and demo guard **transferred from the archive** (see `_compat.py` and docs/HISTORICAL_ARCHIVE.md), behind `adapter.py`. |

- Credentials come from environment variables only (`TRADELOCKER_*`).
  They never leave this layer and are redacted at the log sink.
- Demo status needs two independent signals (our URL, the broker's own
  account record or token claims). Missing evidence fails. An account
  **name** can only fail the check, never pass it: a user can set it.
- Reads retry with bounded backoff; **writes are never retried**. An
  unknown outcome raises `AmbiguousExecution` and is resolved by querying
  the broker for the order's client id.
- `REQUIRE_DEMO = True` has no environment override.

**Not verified from here:** the adapter is tested against a fake
transport. This environment cannot reach TradeLocker, so its first run
against the real demo API is the owner's (docs/OPERATIONS.md).

## Binding contracts
[EXECUTION_CONTRACT.md](../EXECUTION_CONTRACT.md) · [SECURITY_CONTRACT.md](../SECURITY_CONTRACT.md)
