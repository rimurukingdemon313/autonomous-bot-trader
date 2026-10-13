# PAPER FORWARD TEST — NOT REAL MONEY

Updated 2026-10-13 14:00 UTC · mode `PAPER_FORWARD` · profile `PAPER-FORWARD-200K` · shift started 2026-10-13 14:00 UTC · decision system `dual_ai`

Research status (historical, unchanged): **NO EDGE — DO NOT TRADE (historical research; this test measures forward)**. This run measures the system forward; it is not evidence of an edge until it has a sample and the forward-eligibility rules say so.

| Account | Equity | P&L today | Total P&L | Drawdown | Open | Trades | Win rate | Expectancy | Profit factor | Risk | Bot |
|---|---|---|---|---|---|---|---|---|---|---|---|
| $200,000.00 | $199,448.39 | $-904.89 | $-551.61 | $-551.61 | 1 | 8 (insufficient) | 37.5% | -0.170R | 0.58 | ACTIVE | RUNNING |

## Last decisions (decision → risk → paper execution)

- 10-13 11:30 AUDJPY BUY: AI DECISION → RISK REJECTED — cost_to_risk: round-trip cost is 25.0% of the stop (max 25%): spread 0.018 + commission and slippage
- 10-13 10:15 EURUSD SELL: AI DECISION → RISK APPROVED → PAPER EXECUTED
- 10-13 10:00 EURCHF BUY: AI DECISION → RISK APPROVED → PAPER EXECUTED
- 10-13 09:45 EURJPY SELL: AI DECISION → RISK APPROVED → RISK REJECTED — hard risk gate: RISK_GATE_REJECTED reason=FINANCING_EXCEEDS_RISK equity_conservative=199621.61 daily_pnl=-731.67 daily_limit=-10000.00 total_pnl=-378.39 total_limit=-20000.00 open_risk=299.96 max_loss
- 10-13 09:15 USDCHF SELL: AI DECISION → RISK REJECTED — reward_risk: 0.91 vs minimum 1.2
- 10-13 07:45 AUDUSD SELL: AI DECISION → RISK REJECTED — quote: age 108s, bid 0.69685, ask 0.69695
- 10-13 06:30 USDJPY SELL: AI DECISION → RISK APPROVED → PAPER EXECUTED
- 10-13 02:45 USDCAD SELL: AI DECISION → RISK APPROVED → PAPER EXECUTED
- 10-13 01:30 AUDUSD SELL: AI DECISION → RISK APPROVED → PAPER EXECUTED
- 10-12 21:45 EURUSD SELL: AI DECISION → RISK APPROVED → PAPER EXECUTED
- 10-12 18:00 GBPUSD SELL: AI DECISION → RISK APPROVED → PAPER EXECUTED
- 10-12 13:00 USDJPY BUY: AI DECISION → RISK APPROVED → PAPER EXECUTED
- 10-12 10:30 EURUSD SELL: AI DECISION → RISK APPROVED → PAPER EXECUTED

## Latest decisions, NO TRADE included (384 so far)

- 10-13 13:45 USDCHF NO_TRADE: Trader 1 (vision) gave no usable answer (UPSTREAM_ERROR: upstream error: JSON error injected into SSE stream): no decision on one trader alone
- 10-13 13:45 USDCAD NO_TRADE: Trader 1 (vision) gave no usable answer (INVALID: no JSON object in the reply): no decision on one trader alone
- 10-13 13:30 AUDUSD NO_TRADE: Trader 1 (vision) gave no usable answer (INVALID: no JSON object in the reply): no decision on one trader alone
- 10-13 13:30 USDJPY NO_TRADE: the traders disagree (Trader 1 BUY 75, Trader 2 SELL 70): no trade unless both choose the same side; the debate (apodex/apodex-1.1-mini:free) would have chosen SELL: followed forward in shadow, not tr
- 10-13 13:15 GBPUSD NO_TRADE: Trader 1 (vision) gave no usable answer (INVALID: no JSON object in the reply): no decision on one trader alone
- 10-13 13:15 EURUSD NO_TRADE: the traders disagree (Trader 1 BUY 75, Trader 2 SELL 70): no trade unless both choose the same side; the debate (apodex/apodex-1.1-mini:free) would have chosen BUY: followed forward in shadow, not tra
- 10-13 13:00 AUDJPY NO_TRADE: Trader 1 (vision) gave no usable answer (TIMEOUT: no answer within 420 s (last: INVALID: no JSON object in the reply)): no decision on one trader alone
- 10-13 13:00 EURCHF NO_TRADE: market unavailable for a decision: blocked before consulting the model: EXPOSURE: a EURCHF position is already open
- 10-13 12:45 GBPJPY NO_TRADE: Trader 1 (vision) gave no usable answer (NO_FREE_MODEL: no FREE vision model in the catalog): no decision on one trader alone
- 10-13 12:45 EURJPY NO_TRADE: Trader 1 (vision) gave no usable answer (RATE_LIMITED: HTTP 429: Provider returned error google/gemma-4-31b-it:free is temporarily rate-limited upstream. Please retry shortly, or add your own key to a
- 10-13 12:30 EURGBP NO_TRADE: Trader 1 (vision) gave no usable answer (NO_FREE_MODEL: no FREE vision model in the catalog): no decision on one trader alone
- 10-13 12:30 NZDUSD NO_TRADE: Trader 1 (vision) gave no usable answer (RATE_LIMITED: HTTP 429: Provider returned error google/gemma-4-31b-it:free is temporarily rate-limited upstream. Please retry shortly, or add your own key to a

## Open paper positions

| Symbol | Side | Qty | Entry | Stop | Target | P&L |
|---|---|---|---|---|---|---|
| EURCHF | BUY | 2.96 | 0.9312 | 0.9302 | 0.9327 | $216.74 |

## Closed paper trades (latest 20)

| Closed | Symbol | Side | Net | R | Costs | Exit | Source |
|---|---|---|---|---|---|---|---|
| 10-13 11:11 | EURUSD | SELL | $-422.48 | -0.85 | $80.75 | STOP | DUAL_AI |
| 10-13 10:48 | USDCAD | SELL | $73.61 | +0.30 | $46.17 | TIME | DUAL_AI |
| 10-13 06:48 | USDJPY | SELL | $228.86 | +0.92 | $42.21 | TARGET | DUAL_AI |
| 10-13 05:42 | AUDUSD | SELL | $-214.73 | -0.86 | $47.12 | STOP | DUAL_AI |
| 10-13 01:03 | EURUSD | SELL | $-431.70 | -0.86 | $87.38 | STOP | DUAL_AI |
| 10-13 01:04 | GBPUSD | SELL | $-355.19 | -0.71 | $110.84 | STOP | DUAL_AI |
| 10-12 21:01 | USDJPY | BUY | $-414.90 | -0.83 | $114.86 | STOP | DUAL_AI |
| 10-12 15:38 | EURUSD | SELL | $768.18 | +1.54 | $66.08 | TARGET | DUAL_AI |

## Dual AI desk (two free OpenRouter traders; a trade only when they agree)

OpenRouter `NO_FREE_MODEL` · key set · trader 1 `None` · trader 2 `None` · debate `None` · calls today 0/900

AI trades 8 (insufficient) · wins 3 · losses 5 · expectancy -0.170R · profit factor 0.58

Disagreements (not traded; the debate runs in shadow): 7 · the debate's pick if taken: 0 resolved (none) · the side it rejected if taken: 4 resolved (insufficient), expectancy +0.942R

| Time | Symbol | Trader 1 | Trader 2 | Debate (shadow) | Rule | Final | Risk |
|---|---|---|---|---|---|---|---|
| 10-13 13:45 | USDCHF | -  | -  | - | TRADER1_UNAVAILABLE | NO_TRADE | - |
| 10-13 13:45 | USDCAD | -  | -  | - | TRADER1_UNAVAILABLE | NO_TRADE | - |
| 10-13 13:30 | AUDUSD | -  | -  | - | TRADER1_UNAVAILABLE | NO_TRADE | - |
| 10-13 13:30 | USDJPY | BUY 75 | SELL 70 | SELL | DISAGREE | NO_TRADE | - |
| 10-13 13:15 | GBPUSD | -  | -  | - | TRADER1_UNAVAILABLE | NO_TRADE | - |
| 10-13 13:15 | EURUSD | BUY 75 | SELL 70 | BUY | DISAGREE | NO_TRADE | - |
| 10-13 13:00 | AUDJPY | -  | -  | - | TRADER1_UNAVAILABLE | NO_TRADE | - |
| 10-13 13:00 | EURCHF | -  | -  | - | MARKET_UNAVAILABLE | NO_TRADE | - |
| 10-13 12:45 | GBPJPY | -  | -  | - | TRADER1_UNAVAILABLE | NO_TRADE | - |
| 10-13 12:45 | EURJPY | -  | -  | - | TRADER1_UNAVAILABLE | NO_TRADE | - |
| 10-13 12:30 | EURGBP | -  | -  | - | TRADER1_UNAVAILABLE | NO_TRADE | - |
| 10-13 12:30 | NZDUSD | -  | -  | - | TRADER1_UNAVAILABLE | NO_TRADE | - |

The chart Trader 1 read last: `last_chart.png`.

Full figures: `paper_forward.json`. Rules: `docs/PAPER_FORWARD.md` on main.
