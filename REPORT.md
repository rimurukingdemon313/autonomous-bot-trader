# PAPER FORWARD TEST — NOT REAL MONEY

Updated 2026-10-13 10:24 UTC · mode `PAPER_FORWARD` · profile `PAPER-FORWARD-200K` · shift started 2026-10-13 08:24 UTC · decision system `dual_ai`

Research status (historical, unchanged): **NO EDGE — DO NOT TRADE (historical research; this test measures forward)**. This run measures the system forward; it is not evidence of an edge until it has a sample and the forward-eligibility rules say so.

| Account | Equity | P&L today | Total P&L | Drawdown | Open | Trades | Win rate | Expectancy | Profit factor | Risk | Bot |
|---|---|---|---|---|---|---|---|---|---|---|---|
| $200,000.00 | $199,704.80 | $-648.49 | $-295.20 | $-295.20 | 3 | 6 (insufficient) | 33.3% | -0.135R | 0.70 | ACTIVE | RUNNING |

## Last decisions (decision → risk → paper execution)

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

## Latest decisions, NO TRADE included (356 so far)

- 10-13 10:15 GBPUSD NO_TRADE: market unavailable for a decision: risk engine: open_positions (3 open, max 3); currency_exposure (2 open positions share a currency, max 2): the model was not consulted
- 10-13 10:15 EURUSD SELL: SELL EURUSD on M15: AGREE: Trader 1 (dots-studio/dots-3-note-preview:free) SELL 70: The higher timeframe H4 is clearly bearish with a LH+LL structure and bearish BOS. On the execution timeframe, a low
- 10-13 10:00 AUDJPY NO_TRADE: the traders disagree (Trader 1 BUY 72, Trader 2 SELL 65): no trade unless both choose the same side; the debate (apodex/apodex-1.1-mini:free) would have chosen SELL: followed forward in shadow, not tr
- 10-13 10:00 EURCHF BUY: BUY EURCHF on M15: AGREE: Trader 1 (dots-studio/dots-3-note-preview:free) BUY 75: The M15 chart displays a strong bullish structure with higher highs and higher lows, currently pulling back into a tes
- 10-13 09:45 GBPJPY NO_TRADE: the traders disagree (Trader 1 BUY 75, Trader 2 SELL 60): no trade unless both choose the same side; the debate (apodex/apodex-1.1-mini:free) would have chosen BUY: followed forward in shadow, not tra
- 10-13 09:45 EURJPY SELL: SELL EURJPY on M15: AGREE: Trader 1 (dots-studio/dots-3-note-preview:free) SELL 78: The M15 trend is clearly bearish with a structure of lower highs and lower lows, and the recent sharp drop shows str
- 10-13 09:30 EURGBP NO_TRADE: market unavailable for a decision: blocked before consulting the model: STALE_DATA: quote is 191s old
- 10-13 09:30 NZDUSD NO_TRADE: market unavailable for a decision: blocked before consulting the model: STALE_DATA: quote is 289s old
- 10-13 09:15 USDCHF SELL: SELL USDCHF on M15: AGREE: Trader 1 (nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free) SELL 68: Bearish BOS and open FVG above current price, supply zone tested, and price near resistance at 0.83329
- 10-13 09:15 USDCAD NO_TRADE: market unavailable for a decision: blocked before consulting the model: EXPOSURE: a USDCAD position is already open
- 10-13 08:45 AUDUSD NO_TRADE: the traders disagree (Trader 1 BUY 85, Trader 2 SELL 65): no trade unless both choose the same side; the debate (apodex/apodex-1.1-mini:free) would have chosen SELL: followed forward in shadow, not tr
- 10-13 08:45 USDJPY NO_TRADE: the traders disagree (Trader 1 BUY 68, Trader 2 SELL 62): no trade unless both choose the same side; the debate (dots-studio/dots-3-note-preview:free) would have chosen SELL: followed forward in shado

## Open paper positions

| Symbol | Side | Qty | Entry | Stop | Target | P&L |
|---|---|---|---|---|---|---|
| EURUSD | SELL | 4.75 | 1.11855 | 1.11932 | 1.11757 | $-42.75 |
| EURCHF | BUY | 2.96 | 0.9312 | 0.9302 | 0.9327 | $74.62 |
| USDCAD | SELL | 2.44 | 1.426515 | 1.4276 | 1.4245 | $92.40 |

## Closed paper trades (latest 20)

| Closed | Symbol | Side | Net | R | Costs | Exit | Source |
|---|---|---|---|---|---|---|---|
| 10-13 06:48 | USDJPY | SELL | $228.86 | +0.92 | $42.21 | TARGET | DUAL_AI |
| 10-13 05:42 | AUDUSD | SELL | $-214.73 | -0.86 | $47.12 | STOP | DUAL_AI |
| 10-13 01:03 | EURUSD | SELL | $-431.70 | -0.86 | $87.38 | STOP | DUAL_AI |
| 10-13 01:04 | GBPUSD | SELL | $-355.19 | -0.71 | $110.84 | STOP | DUAL_AI |
| 10-12 21:01 | USDJPY | BUY | $-414.90 | -0.83 | $114.86 | STOP | DUAL_AI |
| 10-12 15:38 | EURUSD | SELL | $768.18 | +1.54 | $66.08 | TARGET | DUAL_AI |

## Dual AI desk (two free OpenRouter traders; a trade only when they agree)

OpenRouter `READY` · key set · trader 1 `dots-studio/dots-3-note-preview:free` · trader 2 `nvidia/nemotron-3-ultra-550b-a55b:free` · debate `apodex/apodex-1.1-mini:free` · calls today 37/900

AI trades 6 (insufficient) · wins 2 · losses 4 · expectancy -0.135R · profit factor 0.70

Disagreements (not traded; the debate runs in shadow): 4 · the debate's pick if taken: 0 resolved (none) · the side it rejected if taken: 4 resolved (insufficient), expectancy +0.942R

| Time | Symbol | Trader 1 | Trader 2 | Debate (shadow) | Rule | Final | Risk |
|---|---|---|---|---|---|---|---|
| 10-13 10:15 | GBPUSD | -  | -  | - | MARKET_UNAVAILABLE | NO_TRADE | - |
| 10-13 10:15 | EURUSD | SELL 70 | SELL 75 | - | AGREE | SELL | APPROVED |
| 10-13 10:00 | AUDJPY | BUY 72 | SELL 65 | SELL | DISAGREE | NO_TRADE | - |
| 10-13 10:00 | EURCHF | BUY 75 | BUY 65 | - | AGREE | BUY | APPROVED |
| 10-13 09:45 | GBPJPY | BUY 75 | SELL 60 | BUY | DISAGREE | NO_TRADE | - |
| 10-13 09:45 | EURJPY | SELL 78 | SELL 63 | - | AGREE | SELL | APPROVED |
| 10-13 09:30 | EURGBP | -  | -  | - | MARKET_UNAVAILABLE | NO_TRADE | - |
| 10-13 09:30 | NZDUSD | -  | -  | - | MARKET_UNAVAILABLE | NO_TRADE | - |
| 10-13 09:15 | USDCHF | SELL 68 | SELL 62 | - | AGREE | SELL | REJECTED |
| 10-13 09:15 | USDCAD | -  | -  | - | MARKET_UNAVAILABLE | NO_TRADE | - |
| 10-13 08:45 | AUDUSD | BUY 85 | SELL 65 | SELL | DISAGREE | NO_TRADE | - |
| 10-13 08:45 | USDJPY | BUY 68 | SELL 62 | SELL | DISAGREE | NO_TRADE | - |

The chart Trader 1 read last: `last_chart.png`.

Full figures: `paper_forward.json`. Rules: `docs/PAPER_FORWARD.md` on main.
