# PAPER FORWARD TEST — NOT REAL MONEY

Updated 2026-10-14 01:41 UTC · mode `PAPER_FORWARD` · profile `PAPER-FORWARD-200K` · shift started 2026-10-14 01:11 UTC · decision system `dual_ai`

Research status (historical, unchanged): **NO EDGE — DO NOT TRADE (historical research; this test measures forward)**. This run measures the system forward; it is not evidence of an edge until it has a sample and the forward-eligibility rules say so.

| Account | Equity | P&L today | Total P&L | Drawdown | Open | Trades | Win rate | Expectancy | Profit factor | Risk | Bot |
|---|---|---|---|---|---|---|---|---|---|---|---|
| $200,000.00 | $199,034.42 | $-887.57 | $-965.58 | $-965.58 | 2 | 13 (insufficient) | 46.2% | -0.097R | 0.73 | ACTIVE | RUNNING |

## Last decisions (decision → risk → paper execution)

- 10-14 00:00 EURCHF SELL: AI DECISION → RISK APPROVED → PAPER EXECUTED
- 10-13 22:30 AUDJPY SELL: AI DECISION → RISK APPROVED → PAPER EXECUTED
- 10-13 22:30 EURCHF BUY: AI DECISION → RISK REJECTED — reward_risk: 1.10 vs minimum 1.2
- 10-13 22:15 GBPJPY BUY: AI DECISION → RISK REJECTED — reward_risk: 1.19 vs minimum 1.2
- 10-13 22:15 EURJPY SELL: AI DECISION → RISK REJECTED — reward_risk: 0.91 vs minimum 1.2
- 10-13 22:00 EURGBP SELL: AI DECISION → RISK REJECTED — cost_to_risk: round-trip cost is 28.4% of the stop (max 25%): spread 0.00012 + commission and slippage
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

## Latest decisions, NO TRADE included (473 so far)

- 10-14 01:30 USDJPY NO_TRADE: the traders disagree (Trader 1 SELL 58, Trader 2 BUY 65): no trade unless both choose the same side; the debate (nvidia/nemotron-3-super-120b-a12b:free) would have chosen BUY: followed forward in shad
- 10-14 01:15 GBPUSD NO_TRADE: the traders disagree (Trader 1 BUY 78, Trader 2 SELL 60): no trade unless both choose the same side; the debate (dots-studio/dots-3-note-preview:free) would have chosen SELL: followed forward in shado
- 10-14 01:15 EURUSD NO_TRADE: market unavailable for a decision: blocked before consulting the model: EXPOSURE: a EURUSD position is already open
- 10-14 00:45 USDCHF NO_TRADE: the traders disagree (Trader 1 BUY 72, Trader 2 SELL 62): no trade unless both choose the same side; the debate (nvidia/nemotron-3.5-lightning:free) would have chosen BUY: followed forward in shadow, 
- 10-14 00:45 USDCAD NO_TRADE: Trader 2 (independent) gave no usable answer (TIMEOUT: no answer within 420 s (last: INVALID: no JSON object in the reply)): no decision on one trader alone
- 10-14 00:30 AUDUSD NO_TRADE: market unavailable for a decision: risk engine: open_positions (3 open, max 3): the model was not consulted
- 10-14 00:30 USDJPY NO_TRADE: market unavailable for a decision: risk engine: open_positions (3 open, max 3): the model was not consulted
- 10-14 00:15 GBPUSD NO_TRADE: market unavailable for a decision: risk engine: open_positions (3 open, max 3): the model was not consulted
- 10-14 00:15 EURUSD NO_TRADE: market unavailable for a decision: blocked before consulting the model: EXPOSURE: a EURUSD position is already open
- 10-14 00:00 AUDJPY NO_TRADE: market unavailable for a decision: blocked before consulting the model: EXPOSURE: a AUDJPY position is already open
- 10-14 00:00 EURCHF SELL: SELL EURCHF on M15: AGREE: Trader 1 (dots-studio/dots-3-note-preview:free) SELL 72: The price is at the EQH liquidity pool (0.93281) and PDH (0.9328) after bearish sweeps on highs, indicating distribu
- 10-13 23:45 GBPJPY NO_TRADE: market unavailable for a decision: blocked before consulting the model: DATA_QUALITY: latest bar closed 165 minutes ago; STALE_DATA: last closed bar is 165 minutes old [data: latest bar closed 165 minutes ago]

## Open paper positions

| Symbol | Side | Qty | Entry | Stop | Target | P&L |
|---|---|---|---|---|---|---|
| EURCHF | SELL | 2.99 | 0.9326 | 0.9337 | 0.931 | $-32.33 |
| EURUSD | SELL | 4.39 | 1.12035 | 1.1212 | 1.119 | $-215.11 |

## Closed paper trades (latest 20)

| Closed | Symbol | Side | Net | R | Costs | Exit | Source |
|---|---|---|---|---|---|---|---|
| 10-14 00:34 | AUDJPY | SELL | $-411.49 | -0.83 | $98.39 | STOP | DUAL_AI |
| 10-13 23:06 | NZDUSD | SELL | $13.40 | +0.03 | $100.00 | TIME | DUAL_AI |
| 10-13 21:26 | EURGBP | BUY | $-439.21 | -0.88 | $101.27 | STOP | DUAL_AI |
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

OpenRouter `READY` · key set · trader 1 `nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free` · trader 2 `nvidia/nemotron-3-ultra-550b-a55b:free` · debate `nvidia/nemotron-3.5-lightning:free` · calls today 15/900

AI trades 13 (insufficient) · wins 6 · losses 7 · expectancy -0.097R · profit factor 0.73

Disagreements (not traded; the debate runs in shadow): 11 · the debate's pick if taken: 8 resolved (insufficient), expectancy -0.066R · the side it rejected if taken: 13 resolved (insufficient), expectancy +0.276R

| Time | Symbol | Trader 1 | Trader 2 | Debate (shadow) | Rule | Final | Risk |
|---|---|---|---|---|---|---|---|
| 10-14 01:30 | USDJPY | SELL 58 | BUY 65 | BUY | DISAGREE | NO_TRADE | - |
| 10-14 01:15 | GBPUSD | BUY 78 | SELL 60 | SELL | DISAGREE | NO_TRADE | - |
| 10-14 01:15 | EURUSD | -  | -  | - | MARKET_UNAVAILABLE | NO_TRADE | - |
| 10-14 00:45 | USDCHF | BUY 72 | SELL 62 | BUY | DISAGREE | NO_TRADE | - |
| 10-14 00:45 | USDCAD | BUY 65 | -  | - | TRADER2_UNAVAILABLE | NO_TRADE | - |
| 10-14 00:30 | AUDUSD | -  | -  | - | MARKET_UNAVAILABLE | NO_TRADE | - |
| 10-14 00:30 | USDJPY | -  | -  | - | MARKET_UNAVAILABLE | NO_TRADE | - |
| 10-14 00:15 | GBPUSD | -  | -  | - | MARKET_UNAVAILABLE | NO_TRADE | - |
| 10-14 00:15 | EURUSD | -  | -  | - | MARKET_UNAVAILABLE | NO_TRADE | - |
| 10-14 00:00 | AUDJPY | -  | -  | - | MARKET_UNAVAILABLE | NO_TRADE | - |
| 10-14 00:00 | EURCHF | SELL 72 | SELL 68 | - | AGREE | SELL | APPROVED |
| 10-13 23:45 | GBPJPY | -  | -  | - | MARKET_UNAVAILABLE | NO_TRADE | - |

The chart Trader 1 read last: `last_chart.png`. (numbers): no free vision model answered, so Trader 1 read the same chart from its numbers.

Full figures: `paper_forward.json`. Rules: `docs/PAPER_FORWARD.md` on main.
