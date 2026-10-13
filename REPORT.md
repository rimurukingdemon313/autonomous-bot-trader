# PAPER FORWARD TEST — NOT REAL MONEY

Updated 2026-10-13 15:45 UTC · mode `PAPER_FORWARD` · profile `PAPER-FORWARD-200K` · shift started 2026-10-13 14:00 UTC · decision system `dual_ai`

Research status (historical, unchanged): **NO EDGE — DO NOT TRADE (historical research; this test measures forward)**. This run measures the system forward; it is not evidence of an edge until it has a sample and the forward-eligibility rules say so.

| Account | Equity | P&L today | Total P&L | Drawdown | Open | Trades | Win rate | Expectancy | Profit factor | Risk | Bot |
|---|---|---|---|---|---|---|---|---|---|---|---|
| $200,000.00 | $199,464.56 | $-888.72 | $-535.44 | $-535.44 | 3 | 8 (insufficient) | 37.5% | -0.170R | 0.58 | ACTIVE | RUNNING |

## Last decisions (decision → risk → paper execution)

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

## Latest decisions, NO TRADE included (398 so far)

- 10-13 15:45 GBPUSD NO_TRADE: market unavailable for a decision: risk engine: open_positions (3 open, max 3): the model was not consulted
- 10-13 15:45 EURUSD NO_TRADE: market unavailable for a decision: risk engine: open_positions (3 open, max 3); currency_exposure (2 open positions share a currency, max 2): the model was not consulted
- 10-13 15:30 AUDJPY NO_TRADE: market unavailable for a decision: risk engine: open_positions (3 open, max 3): the model was not consulted
- 10-13 15:30 EURCHF NO_TRADE: market unavailable for a decision: blocked before consulting the model: EXPOSURE: a EURCHF position is already open
- 10-13 15:15 GBPJPY NO_TRADE: market unavailable for a decision: risk engine: open_positions (3 open, max 3): the model was not consulted
- 10-13 15:15 EURJPY NO_TRADE: market unavailable for a decision: risk engine: open_positions (3 open, max 3); currency_exposure (2 open positions share a currency, max 2): the model was not consulted
- 10-13 15:00 EURGBP BUY: BUY EURGBP on M15: AGREE: Trader 1 (dots-studio/dots-3-note-preview:free) BUY 65: The price is pulling back into a tested demand order block and a strong multi-touch support at 0.84480 within the entr
- 10-13 15:00 NZDUSD SELL: SELL NZDUSD on M15: AGREE: Trader 1 (dots-studio/dots-3-note-preview:free) SELL 72: The H4 trend is bearish, and the M15 shows a classic bearish liquidity sweep of highs followed by a bearish displace
- 10-13 14:45 USDCHF NO_TRADE: the traders disagree (Trader 1 BUY 68, Trader 2 SELL 62): no trade unless both choose the same side; the debate (apodex/apodex-1.1-mini:free) would have chosen SELL: followed forward in shadow, not tr
- 10-13 14:45 USDCAD NO_TRADE: Trader 1 (vision) gave no usable answer (INVALID: take_profit 1.4251 is on the wrong side for SELL (entry 1.42182, executable 1.421825)): no decision on one trader alone
- 10-13 14:30 AUDUSD NO_TRADE: Trader 1 (vision) gave no usable answer (UPSTREAM_ERROR: upstream error: JSON error injected into SSE stream): no decision on one trader alone
- 10-13 14:30 USDJPY NO_TRADE: Trader 1 (vision) gave no usable answer (INVALID: no JSON object in the reply): no decision on one trader alone

## Open paper positions

| Symbol | Side | Qty | Entry | Stop | Target | P&L |
|---|---|---|---|---|---|---|
| EURGBP | BUY | 3.54 | 0.8449699999999999 | 0.84412 | 0.84612 | $-107.84 |
| NZDUSD | SELL | 3.78 | 0.561515 | 0.5625 | 0.56 | $52.92 |
| EURCHF | BUY | 2.96 | 0.9312 | 0.9302 | 0.9327 | $287.83 |

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

OpenRouter `READY` · key set · trader 1 `dots-studio/dots-3-note-preview:free` · trader 2 `nvidia/nemotron-3-ultra-550b-a55b:free` · debate `apodex/apodex-1.1-mini:free` · calls today 31/900

AI trades 8 (insufficient) · wins 3 · losses 5 · expectancy -0.170R · profit factor 0.58

Disagreements (not traded; the debate runs in shadow): 8 · the debate's pick if taken: 0 resolved (none) · the side it rejected if taken: 4 resolved (insufficient), expectancy +0.942R

| Time | Symbol | Trader 1 | Trader 2 | Debate (shadow) | Rule | Final | Risk |
|---|---|---|---|---|---|---|---|
| 10-13 15:45 | GBPUSD | -  | -  | - | MARKET_UNAVAILABLE | NO_TRADE | - |
| 10-13 15:45 | EURUSD | -  | -  | - | MARKET_UNAVAILABLE | NO_TRADE | - |
| 10-13 15:30 | AUDJPY | -  | -  | - | MARKET_UNAVAILABLE | NO_TRADE | - |
| 10-13 15:30 | EURCHF | -  | -  | - | MARKET_UNAVAILABLE | NO_TRADE | - |
| 10-13 15:15 | GBPJPY | -  | -  | - | MARKET_UNAVAILABLE | NO_TRADE | - |
| 10-13 15:15 | EURJPY | -  | -  | - | MARKET_UNAVAILABLE | NO_TRADE | - |
| 10-13 15:00 | EURGBP | BUY 65 | BUY 62 | - | AGREE | BUY | APPROVED |
| 10-13 15:00 | NZDUSD | SELL 72 | SELL 68 | - | AGREE | SELL | APPROVED |
| 10-13 14:45 | USDCHF | BUY 68 | SELL 62 | SELL | DISAGREE | NO_TRADE | - |
| 10-13 14:45 | USDCAD | SELL 68 | -  | - | TRADER1_UNAVAILABLE | NO_TRADE | - |
| 10-13 14:30 | AUDUSD | -  | -  | - | TRADER1_UNAVAILABLE | NO_TRADE | - |
| 10-13 14:30 | USDJPY | -  | -  | - | TRADER1_UNAVAILABLE | NO_TRADE | - |

The chart Trader 1 read last: `last_chart.png`.

Full figures: `paper_forward.json`. Rules: `docs/PAPER_FORWARD.md` on main.
