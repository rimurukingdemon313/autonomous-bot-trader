# PAPER FORWARD TEST — NOT REAL MONEY

Updated 2026-10-13 23:06 UTC · mode `PAPER_FORWARD` · profile `PAPER-FORWARD-200K` · shift started 2026-10-13 19:35 UTC · decision system `dual_ai`

Research status (historical, unchanged): **NO EDGE — DO NOT TRADE (historical research; this test measures forward)**. This run measures the system forward; it is not evidence of an edge until it has a sample and the forward-eligibility rules say so.

| Account | Equity | P&L today | Total P&L | Drawdown | Open | Trades | Win rate | Expectancy | Profit factor | Risk | Bot |
|---|---|---|---|---|---|---|---|---|---|---|---|
| $200,000.00 | $199,725.45 | $-196.54 | $-274.55 | $-274.55 | 3 | 11 (insufficient) | 45.5% | -0.042R | 0.86 | ACTIVE | RUNNING |

## Last decisions (decision → risk → paper execution)

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
- 10-12 18:00 GBPUSD SELL: AI DECISION → RISK APPROVED → PAPER EXECUTED

## Latest decisions, NO TRADE included (456 so far)

- 10-13 23:00 AUDUSD NO_TRADE: market unavailable for a decision: blocked before consulting the model: DATA_QUALITY: latest bar closed 120 minutes ago; STALE_DATA: last closed bar is 120 minutes old [data: latest bar closed 120 minutes ago]
- 10-13 23:00 USDJPY NO_TRADE: market unavailable for a decision: blocked before consulting the model: DATA_QUALITY: latest bar closed 120 minutes ago; STALE_DATA: last closed bar is 120 minutes old [data: latest bar closed 120 minutes ago]
- 10-13 22:45 GBPUSD NO_TRADE: market unavailable for a decision: risk engine: open_positions (3 open, max 3); currency_exposure (2 open positions share a currency, max 2): the model was not consulted
- 10-13 22:45 EURUSD NO_TRADE: market unavailable for a decision: blocked before consulting the model: EXPOSURE: a EURUSD position is already open
- 10-13 22:30 AUDJPY SELL: SELL AUDJPY on M15: AGREE: Trader 1 (dots-studio/dots-3-note-preview:free) SELL 65: The price is rejecting the tested supply order block near the top of the range, accompanied by a recent bearish liqu
- 10-13 22:30 EURCHF BUY: BUY EURCHF on M15: AGREE: Trader 1 (dots-studio/dots-3-note-preview:free) BUY 75: The M15 chart displays a clear uptrend with a tested demand order block and a recent bullish liquidity sweep at 0.9317
- 10-13 22:15 GBPJPY BUY: BUY GBPJPY on M15: AGREE: Trader 1 (dots-studio/dots-3-note-preview:free) BUY 75: The H4 trend is bullish, and the M15 price completed a liquidity sweep of the lows at 209.689 before holding the key s
- 10-13 22:15 EURJPY SELL: SELL EURJPY on M15: AGREE: Trader 1 (nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free) SELL 78: The H4 downtrend and recent bearish CHOCH at 177.281, together with the tested supply zone 177.305‑331
- 10-13 22:00 EURGBP SELL: SELL EURGBP on M15: AGREE: Trader 1 (dots-studio/dots-3-note-preview:free) SELL 75: The M15 structure is clearly bearish with a fresh sweep of highs at 0.84509 followed by consecutive bearish BOS brea
- 10-13 22:00 NZDUSD NO_TRADE: market unavailable for a decision: blocked before consulting the model: EXPOSURE: a NZDUSD position is already open
- 10-13 21:45 USDCHF NO_TRADE: market unavailable for a decision: risk engine: currency_exposure (2 open positions share a currency, max 2): the model was not consulted
- 10-13 21:45 USDCAD NO_TRADE: market unavailable for a decision: risk engine: currency_exposure (2 open positions share a currency, max 2): the model was not consulted

## Open paper positions

| Symbol | Side | Qty | Entry | Stop | Target | P&L |
|---|---|---|---|---|---|---|
| AUDJPY | SELL | 5.02 | 110.55199999999999 | 110.67 | 110.4 | $-60.09 |
| EURUSD | SELL | 4.39 | 1.12035 | 1.1212 | 1.119 | $92.19 |
| NZDUSD | SELL | 3.78 | 0.561515 | 0.5625 | 0.56 | n/a |

## Closed paper trades (latest 20)

| Closed | Symbol | Side | Net | R | Costs | Exit | Source |
|---|---|---|---|---|---|---|---|
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

OpenRouter `READY` · key set · trader 1 `dots-studio/dots-3-note-preview:free` · trader 2 `nvidia/nemotron-3-ultra-550b-a55b:free` · debate `nvidia/nemotron-3.5-lightning:free` · calls today 22/900

AI trades 11 (insufficient) · wins 5 · losses 6 · expectancy -0.042R · profit factor 0.86

Disagreements (not traded; the debate runs in shadow): 8 · the debate's pick if taken: 8 resolved (insufficient), expectancy -0.066R · the side it rejected if taken: 13 resolved (insufficient), expectancy +0.276R

| Time | Symbol | Trader 1 | Trader 2 | Debate (shadow) | Rule | Final | Risk |
|---|---|---|---|---|---|---|---|
| 10-13 23:00 | AUDUSD | -  | -  | - | MARKET_UNAVAILABLE | NO_TRADE | - |
| 10-13 23:00 | USDJPY | -  | -  | - | MARKET_UNAVAILABLE | NO_TRADE | - |
| 10-13 22:45 | GBPUSD | -  | -  | - | MARKET_UNAVAILABLE | NO_TRADE | - |
| 10-13 22:45 | EURUSD | -  | -  | - | MARKET_UNAVAILABLE | NO_TRADE | - |
| 10-13 22:30 | AUDJPY | SELL 65 | SELL 70 | - | AGREE | SELL | APPROVED |
| 10-13 22:30 | EURCHF | BUY 75 | BUY 65 | - | AGREE | BUY | REJECTED |
| 10-13 22:15 | GBPJPY | BUY 75 | BUY 65 | - | AGREE | BUY | REJECTED |
| 10-13 22:15 | EURJPY | SELL 78 | SELL 65 | - | AGREE | SELL | REJECTED |
| 10-13 22:00 | EURGBP | SELL 75 | SELL 70 | - | AGREE | SELL | REJECTED |
| 10-13 22:00 | NZDUSD | -  | -  | - | MARKET_UNAVAILABLE | NO_TRADE | - |
| 10-13 21:45 | USDCHF | -  | -  | - | MARKET_UNAVAILABLE | NO_TRADE | - |
| 10-13 21:45 | USDCAD | -  | -  | - | MARKET_UNAVAILABLE | NO_TRADE | - |

The chart Trader 1 read last: `last_chart.png`. (numbers): no free vision model answered, so Trader 1 read the same chart from its numbers.

Full figures: `paper_forward.json`. Rules: `docs/PAPER_FORWARD.md` on main.
