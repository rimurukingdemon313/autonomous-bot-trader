# PAPER FORWARD TEST — NOT REAL MONEY

Updated 2026-10-13 21:21 UTC · mode `PAPER_FORWARD` · profile `PAPER-FORWARD-200K` · shift started 2026-10-13 19:35 UTC · decision system `dual_ai`

Research status (historical, unchanged): **NO EDGE — DO NOT TRADE (historical research; this test measures forward)**. This run measures the system forward; it is not evidence of an edge until it has a sample and the forward-eligibility rules say so.

| Account | Equity | P&L today | Total P&L | Drawdown | Open | Trades | Win rate | Expectancy | Profit factor | Risk | Bot |
|---|---|---|---|---|---|---|---|---|---|---|---|
| $200,000.00 | $200,059.41 | $-293.87 | $59.41 | $0.00 | 3 | 10 (insufficient) | 50.0% | +0.042R | 1.06 | ACTIVE | RUNNING |

## Last decisions (decision → risk → paper execution)

- 10-13 21:15 EURUSD SELL: AI DECISION → RISK APPROVED → PAPER EXECUTED
- 10-13 18:15 EURJPY SELL: AI DECISION → RISK APPROVED → PAPER EXECUTED
- 10-13 15:00 EURGBP BUY: AI DECISION → RISK APPROVED → PAPER EXECUTED
- 10-13 15:00 NZDUSD SELL: AI DECISION → RISK APPROVED → PAPER EXECUTED
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

## Latest decisions, NO TRADE included (442 so far)

- 10-13 21:15 GBPUSD NO_TRADE: market unavailable for a decision: risk engine: open_positions (3 open, max 3); currency_exposure (2 open positions share a currency, max 2): the model was not consulted
- 10-13 21:15 EURUSD SELL: SELL EURUSD on M15: AGREE: Trader 1 (dots-studio/dots-3-note-preview:free) SELL 70: The higher timeframe (H4) is firmly bearish, and the M15 is testing a major resistance cluster at 1.12045–1.1207 (PD
- 10-13 21:00 AUDJPY NO_TRADE: market unavailable for a decision: risk engine: open_positions (3 open, max 3): the model was not consulted
- 10-13 21:00 EURCHF NO_TRADE: market unavailable for a decision: risk engine: open_positions (3 open, max 3); currency_exposure (2 open positions share a currency, max 2): the model was not consulted
- 10-13 20:45 GBPJPY NO_TRADE: market unavailable for a decision: risk engine: open_positions (3 open, max 3): the model was not consulted
- 10-13 20:45 EURJPY NO_TRADE: market unavailable for a decision: blocked before consulting the model: EXPOSURE: a EURJPY position is already open
- 10-13 20:30 EURGBP NO_TRADE: market unavailable for a decision: blocked before consulting the model: EXPOSURE: a EURGBP position is already open
- 10-13 20:30 NZDUSD NO_TRADE: market unavailable for a decision: blocked before consulting the model: EXPOSURE: a NZDUSD position is already open
- 10-13 20:15 USDCHF NO_TRADE: market unavailable for a decision: risk engine: open_positions (3 open, max 3): the model was not consulted
- 10-13 20:15 USDCAD NO_TRADE: market unavailable for a decision: risk engine: open_positions (3 open, max 3): the model was not consulted
- 10-13 20:00 AUDUSD NO_TRADE: market unavailable for a decision: risk engine: open_positions (3 open, max 3): the model was not consulted
- 10-13 20:00 USDJPY NO_TRADE: market unavailable for a decision: risk engine: open_positions (3 open, max 3): the model was not consulted

## Open paper positions

| Symbol | Side | Qty | Entry | Stop | Target | P&L |
|---|---|---|---|---|---|---|
| EURUSD | SELL | 4.39 | 1.12035 | 1.1212 | 1.119 | $4.39 |
| EURGBP | BUY | 3.54 | 0.8449699999999999 | 0.84412 | 0.84612 | $-154.86 |
| NZDUSD | SELL | 3.78 | 0.561515 | 0.5625 | 0.56 | $90.72 |

## Closed paper trades (latest 20)

| Closed | Symbol | Side | Net | R | Costs | Exit | Source |
|---|---|---|---|---|---|---|---|
| 10-13 21:01 | EURJPY | SELL | $517.15 | +1.04 | $118.81 | TARGET | DUAL_AI |
| 10-13 18:06 | EURCHF | BUY | $370.36 | +0.74 | $91.83 | TIME | DUAL_AI |
| 10-13 11:11 | EURUSD | SELL | $-422.48 | -0.85 | $80.75 | STOP | DUAL_AI |
| 10-13 10:48 | USDCAD | SELL | $73.61 | +0.30 | $46.17 | TIME | DUAL_AI |
| 10-13 06:48 | USDJPY | SELL | $228.86 | +0.92 | $42.21 | TARGET | DUAL_AI |
| 10-13 05:42 | AUDUSD | SELL | $-214.73 | -0.86 | $47.12 | STOP | DUAL_AI |
| 10-13 01:03 | EURUSD | SELL | $-431.70 | -0.86 | $87.38 | STOP | DUAL_AI |
| 10-13 01:04 | GBPUSD | SELL | $-355.19 | -0.71 | $110.84 | STOP | DUAL_AI |
| 10-12 21:01 | USDJPY | BUY | $-414.90 | -0.83 | $114.86 | STOP | DUAL_AI |
| 10-12 15:38 | EURUSD | SELL | $768.18 | +1.54 | $66.08 | TARGET | DUAL_AI |

## Dual AI desk (two free OpenRouter traders; a trade only when they agree)

OpenRouter `READY` · key set · trader 1 `nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free` · trader 2 `nvidia/nemotron-3-ultra-550b-a55b:free` · debate `dots-studio/dots-3-note-preview:free` · calls today 7/900

AI trades 10 (insufficient) · wins 5 · losses 5 · expectancy +0.042R · profit factor 1.06

Disagreements (not traded; the debate runs in shadow): 8 · the debate's pick if taken: 6 resolved (insufficient), expectancy +0.100R · the side it rejected if taken: 11 resolved (insufficient), expectancy +0.416R

| Time | Symbol | Trader 1 | Trader 2 | Debate (shadow) | Rule | Final | Risk |
|---|---|---|---|---|---|---|---|
| 10-13 21:15 | GBPUSD | -  | -  | - | MARKET_UNAVAILABLE | NO_TRADE | - |
| 10-13 21:15 | EURUSD | SELL 70 | SELL 65 | - | AGREE | SELL | APPROVED |
| 10-13 21:00 | AUDJPY | -  | -  | - | MARKET_UNAVAILABLE | NO_TRADE | - |
| 10-13 21:00 | EURCHF | -  | -  | - | MARKET_UNAVAILABLE | NO_TRADE | - |
| 10-13 20:45 | GBPJPY | -  | -  | - | MARKET_UNAVAILABLE | NO_TRADE | - |
| 10-13 20:45 | EURJPY | -  | -  | - | MARKET_UNAVAILABLE | NO_TRADE | - |
| 10-13 20:30 | EURGBP | -  | -  | - | MARKET_UNAVAILABLE | NO_TRADE | - |
| 10-13 20:30 | NZDUSD | -  | -  | - | MARKET_UNAVAILABLE | NO_TRADE | - |
| 10-13 20:15 | USDCHF | -  | -  | - | MARKET_UNAVAILABLE | NO_TRADE | - |
| 10-13 20:15 | USDCAD | -  | -  | - | MARKET_UNAVAILABLE | NO_TRADE | - |
| 10-13 20:00 | AUDUSD | -  | -  | - | MARKET_UNAVAILABLE | NO_TRADE | - |
| 10-13 20:00 | USDJPY | -  | -  | - | MARKET_UNAVAILABLE | NO_TRADE | - |

The chart Trader 1 read last: `last_chart.png`. (numbers): no free vision model answered, so Trader 1 read the same chart from its numbers.

Full figures: `paper_forward.json`. Rules: `docs/PAPER_FORWARD.md` on main.
