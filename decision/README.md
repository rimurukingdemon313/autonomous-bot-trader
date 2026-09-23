# decision/

**Status: empty. Phase 7.**

## Purpose
Turn model estimates into a single structured decision, **BUY**, **SELL**
or **NO_TRADE**, and journal it before anything else happens.

## Responsibilities (when built)
- The decision record: decision, instrument, timeframe, timestamp, market
  state, regime, familiarity, thesis, supporting and contradicting
  evidence, entry, stop, target, exit logic, invalidation, probability,
  expected R after costs with uncertainty, NO_TRADE reason, and every
  version stamp.
- NO_TRADE by default whenever evidence is insufficient, state is
  unfamiliar, or any input is missing or malformed.

## Boundaries
- Never sets position size or risk amount.
- Never forces a trade to meet a count, a target or a schedule.
- Never sends anything to the broker. Its output goes to the risk engine.

## Binding contracts
[PROJECT_SPEC.md](../PROJECT_SPEC.md) §4, §8 · [RISK_CONTRACT.md](../RISK_CONTRACT.md)
