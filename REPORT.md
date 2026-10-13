# PAPER FORWARD TEST — NOT REAL MONEY

Updated 2026-10-13 13:10 UTC · mode `PAPER_FORWARD` · profile `PAPER-FORWARD-200K` · shift started 2026-10-13 08:24 UTC · decision system `dual_ai`

Research status (historical, unchanged): **NO EDGE — DO NOT TRADE (historical research; this test measures forward)**. This run measures the system forward; it is not evidence of an edge until it has a sample and the forward-eligibility rules say so.

| Account | Equity | P&L today | Total P&L | Drawdown | Open | Trades | Win rate | Expectancy | Profit factor | Risk | Bot |
|---|---|---|---|---|---|---|---|---|---|---|---|
| $200,000.00 | $199,128.48 | $-1,224.80 | $-871.52 | $-871.52 | 1 | 8 (insufficient) | 37.5% | -0.170R | 0.58 | ACTIVE | RUNNING |

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

## Latest decisions, NO TRADE included (378 so far)

- 10-13 13:00 AUDJPY NO_TRADE: Trader 1 (vision) gave no usable answer (TIMEOUT: no answer within 420 s (last: INVALID: no JSON object in the reply)): no decision on one trader alone
- 10-13 13:00 EURCHF NO_TRADE: market unavailable for a decision: blocked before consulting the model: EXPOSURE: a EURCHF position is already open
- 10-13 12:45 GBPJPY NO_TRADE: Trader 1 (vision) gave no usable answer (NO_FREE_MODEL: no FREE vision model in the catalog): no decision on one trader alone
- 10-13 12:45 EURJPY NO_TRADE: Trader 1 (vision) gave no usable answer (RATE_LIMITED: HTTP 429: Provider returned error google/gemma-4-31b-it:free is temporarily rate-limited upstream. Please retry shortly, or add your own key to a
- 10-13 12:30 EURGBP NO_TRADE: Trader 1 (vision) gave no usable answer (NO_FREE_MODEL: no FREE vision model in the catalog): no decision on one trader alone
- 10-13 12:30 NZDUSD NO_TRADE: Trader 1 (vision) gave no usable answer (RATE_LIMITED: HTTP 429: Provider returned error google/gemma-4-31b-it:free is temporarily rate-limited upstream. Please retry shortly, or add your own key to a
- 10-13 12:15 USDCHF NO_TRADE: Trader 1 (vision) gave no usable answer (NO_FREE_MODEL: no FREE vision model in the catalog): no decision on one trader alone
- 10-13 12:15 USDCAD NO_TRADE: Trader 1 (vision) gave no usable answer (RATE_LIMITED: HTTP 429: Provider returned error google/gemma-4-31b-it:free is temporarily rate-limited upstream. Please retry shortly, or add your own key to a
- 10-13 12:00 AUDUSD NO_TRADE: the traders disagree (Trader 1 BUY 85, Trader 2 SELL 65): no trade unless both choose the same side; the debate (apodex/apodex-1.1-mini:free) would have chosen SELL: followed forward in shadow, not tr
- 10-13 12:00 USDJPY NO_TRADE: Trader 1 (vision) gave no usable answer (RATE_LIMITED: HTTP 429: Provider returned error google/gemma-4-31b-it:free is temporarily rate-limited upstream. Please retry shortly, or add your own key to a
- 10-13 11:45 GBPUSD NO_TRADE: Trader 1 (vision) gave no usable answer (NO_FREE_MODEL: no FREE vision model in the catalog): no decision on one trader alone
- 10-13 11:45 EURUSD NO_TRADE: Trader 1 (vision) gave no usable answer (RATE_LIMITED: HTTP 429: Provider returned error google/gemma-4-31b-it:free is temporarily rate-limited upstream. Please retry shortly, or add your own key to a

## Open paper positions

| Symbol | Side | Qty | Entry | Stop | Target | P&L |
|---|---|---|---|---|---|---|
| EURCHF | BUY | 2.96 | 0.9312 | 0.9302 | 0.9327 | $-103.17 |

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

OpenRouter `READY` · key set · trader 1 `nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free` · trader 2 `nvidia/nemotron-3-ultra-550b-a55b:free` · debate `apodex/apodex-1.1-mini:free` · calls today 72/900

AI trades 8 (insufficient) · wins 3 · losses 5 · expectancy -0.170R · profit factor 0.58

Disagreements (not traded; the debate runs in shadow): 5 · the debate's pick if taken: 0 resolved (none) · the side it rejected if taken: 4 resolved (insufficient), expectancy +0.942R

| Time | Symbol | Trader 1 | Trader 2 | Debate (shadow) | Rule | Final | Risk |
|---|---|---|---|---|---|---|---|
| 10-13 13:00 | AUDJPY | -  | -  | - | TRADER1_UNAVAILABLE | NO_TRADE | - |
| 10-13 13:00 | EURCHF | -  | -  | - | MARKET_UNAVAILABLE | NO_TRADE | - |
| 10-13 12:45 | GBPJPY | -  | -  | - | TRADER1_UNAVAILABLE | NO_TRADE | - |
| 10-13 12:45 | EURJPY | -  | -  | - | TRADER1_UNAVAILABLE | NO_TRADE | - |
| 10-13 12:30 | EURGBP | -  | -  | - | TRADER1_UNAVAILABLE | NO_TRADE | - |
| 10-13 12:30 | NZDUSD | -  | -  | - | TRADER1_UNAVAILABLE | NO_TRADE | - |
| 10-13 12:15 | USDCHF | -  | -  | - | TRADER1_UNAVAILABLE | NO_TRADE | - |
| 10-13 12:15 | USDCAD | -  | -  | - | TRADER1_UNAVAILABLE | NO_TRADE | - |
| 10-13 12:00 | AUDUSD | BUY 85 | SELL 65 | SELL | DISAGREE | NO_TRADE | - |
| 10-13 12:00 | USDJPY | -  | -  | - | TRADER1_UNAVAILABLE | NO_TRADE | - |
| 10-13 11:45 | GBPUSD | -  | -  | - | TRADER1_UNAVAILABLE | NO_TRADE | - |
| 10-13 11:45 | EURUSD | -  | -  | - | TRADER1_UNAVAILABLE | NO_TRADE | - |

The chart Trader 1 read last: `last_chart.png`.

Full figures: `paper_forward.json`. Rules: `docs/PAPER_FORWARD.md` on main.
