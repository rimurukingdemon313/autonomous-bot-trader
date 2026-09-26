# risk/

**Status: implemented** in [`aitrader/risk/engine.py`](../aitrader/risk/engine.py):
the only code that approves a trade or computes a size.

Checks, each recorded with its measured value in the verdict:

- per-trade risk (default 0.5 %, hard ceiling 1 % whatever the config);
- daily loss 2 %;
- maximum drawdown 8 %, which **halts** until a person clears it;
- 3 open positions, 2 per currency, one per instrument;
- leverage, spread against the stop, minimum reward:risk, minimum stop in
  spreads, quote age, instrument tradability;
- a funded-account layer whose rules the operator supplies; the stricter
  limit always wins.

A losing streak halves risk every 3 losses down to 0.25×. **Nothing
increases risk**: no martingale, no recovery sizing. Any input it cannot
read gives a rejection.

Tests: `tests/unit/test_risk.py` (including that risk never rises after
losses).

## Binding contracts
[RISK_CONTRACT.md](../RISK_CONTRACT.md)
