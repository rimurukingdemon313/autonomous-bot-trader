# CR-2: the plain funding carry must beat cash (preregistration)

| | |
|---|---|
| Frozen spec | `research/specs/CR-2.json` |
| Spec sha256 | `d8c7ca2fda9ec9b60f8658ffc43410ba77029e52f6828abff89debfe6d89a141` |
| Code | `scripts/cr2.py`, reusing `aitrader/research/crypto/cr.py` and `scripts/cr1.py` (both frozen by CR-1's hash) |
| Test | `tests/unit/test_cr2_runner.py`: zero funding loses to cash; a planted premium beats it |
| Counted tests | 1 |

## Why this exists, and how it differs from CR-1

CR-1 tested a **timing rule** for the carry: enter when trailing funding is high, leave when it turns
negative. That rule FAILED validation: it did not beat random timing, and a neighbour lost.

CR-1's development baseline, the carry held **all the time**, earned +8.9% a year on capital (t 4.5) in
2020–2022. Its validation baseline was lost to a boundary bug (`research/results/CR-1-regate.json`).

CR-2 tests that plain carry as its own hypothesis, with one change that makes it harder:

- **The return must exceed the risk-free rate, not zero.**
- A market-neutral position that earns less than Treasury bills is not an edge. CR-1 credited idle capital
  nothing and compared with zero.

**Data already seen:**

- 2020–2024 was seen by CR-1 (development and validation). It is recorded as "select" here, and the
  development gate is a walk-forward over its five calendar years.
- **2025-01-01 → 2026-09-29 has never been fetched.** It is the judge.

## Hypothesis

A delta-neutral position (long spot, short USDT-M perpetual, equal notional) on the 11 coins of CR-1's
point-in-time universe earns more than the US policy rate after:

- Binance VIP 0 taker fees;
- a declared spread and slippage;
- forced rebalances when the short leg's margin would run out (the perpetual at 1.8× entry).

**Mechanism.** Leveraged demand for long perpetual exposure. The limits to arbitrage are:

- capital split across legs;
- exchange counterparty risk;
- liquidation risk;
- access restrictions.

## Rules

| | |
|---|---|
| Position | each window, each coin: open at the window start (first common hour bar), hold, close at the window's last common bar. Capital 2N per coin, equal across coins |
| Windows | development: each calendar year 2020–2024 separately (one round trip per coin per year). Holdout: 2025-01-01 → 2026-09-29 as one window |
| Funding | exact, every settlement held |
| Costs | as CR-1: spot 10 bp, perpetual 5 bp, half-spread 1 bp (BTC, ETH) or 2 bp, slippage 1 bp, all per fill; ×1.5 stress |
| Risk-free | the BIS US policy rate public that day, /365 per calendar day. A day without a rate stops the run: never assumed |

## Development gates (all required)

- annualised excess return > 0;
- t ≥ 2.0 on daily excess returns;
- ≥ 4 of 5 calendar years with excess > 0;
- excess > 0 at costs × 1.5;
- maximum drawdown of cumulative excess ≤ 10%;
- ≥ 6 of 11 coins with excess > 0.

## Holdout rule (only if development passes; the data is fetched only then)

- excess > 0;
- t ≥ 1.645;
- excess > 0 at costs × 1.5;
- maximum drawdown ≤ 10%.

## Labels

| Label | Requires | Meaning |
|---|---|---|
| PROMISING BUT NOT YET PROVEN | the holdout passes | Not ROBUST: it still needs a forward paper test on live Binance quotes with recorded fills. Exchange and liquidation risk are not captured by any backtest |
| NO ROBUST EDGE FOUND | anything else | final for this hypothesis |

## Forbidden

- changing a rule, a coin, a cost or a gate after any result;
- fetching 2025+ before development passes;
- a second run.
