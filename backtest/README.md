# backtest/

**Status: implemented** in [`aitrader/backtest/`](../aitrader/backtest/).

| File | What it does |
|---|---|
| `runner.py` | Walk-forward replay of the **whole** system: the same orchestrator, agents, synthesis, risk engine, execution engine and paper broker as the live service, driven by a `ReplayFeed` clock. Warm-up seeds memory from labels; the regime model is refit at each year start on rows before it minus a 5-day embargo. |
| `metrics.py` | Expectancy, t, win rate, profit factor, drawdown, Sharpe/Sortino when meaningful, breakdowns by year, instrument, regime and setup; small samples labelled `insufficient`. |

Fills are pessimistic (`aitrader/broker/paper.py`): market orders at the
live ask/bid plus slippage, stop first when stop and target share a bar, a
gap through the stop fills at the open, commission and swap per New York
close. Slippage, commission and swap are **declared approximations**,
recorded with every result.

The language-model layer is not part of any backtest (MODEL_CONTRACT.md §7).

Tests: `tests/integration/test_pipeline.py` (tracker = labels parity,
determinism, "changing the future does not change the past", ablation).

Run: `python scripts/run_pr001.py` (the pre-registered experiment).

## Binding contracts
[VALIDATION_CONTRACT.md](../VALIDATION_CONTRACT.md) · [RESEARCH_CONTRACT.md](../RESEARCH_CONTRACT.md)
