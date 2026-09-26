# paper/

**Status: implemented.** The paper account is
[`aitrader/broker/paper.py`](../aitrader/broker/paper.py); the service runs
it on live TradeLocker prices with `MODE=PAPER` (docs/OPERATIONS.md).

## Entry conditions
Paper and demo runs of an **unvalidated** candidate are allowed as forward
tests (docs/SYSTEM_LIFECYCLE.md, Amendment 1). They are labelled
unvalidated on the dashboard, recorded under their version stamp, and
never count as validation. They do not move the system up the lifecycle:
LIVE still needs every gate, and `MODE=LIVE` is refused by the software.

## Records
Every decision and every NO_TRADE with its reasons, every simulated fill,
spread, slippage, P/L, drawdown, and the version stamp, in the database.

## Boundaries
- No automatic transition to DEMO or LIVE.
- A failed safety check pauses or halts; it never loosens a limit.

## Binding contracts
[docs/SYSTEM_LIFECYCLE.md](../docs/SYSTEM_LIFECYCLE.md) · [RISK_CONTRACT.md](../RISK_CONTRACT.md)
