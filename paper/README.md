# paper/

**Status: empty. Phase 10.**

## Purpose
Run the complete system on live data with simulated execution, as the
first test on data that no one could have seen.

## Entry conditions
Every gate up to and including the final holdout PASS, and explicit owner
approval.

## Responsibilities (when built)
Record every decision and every NO_TRADE, every simulated execution,
latency, spread, slippage, P/L, drawdown, and the model version.

## Boundaries
- No automatic transition to DEMO or LIVE.
- Any failed gate returns the system to PAUSED.

## Binding contracts
[docs/SYSTEM_LIFECYCLE.md](../docs/SYSTEM_LIFECYCLE.md) · [RISK_CONTRACT.md](../RISK_CONTRACT.md)
