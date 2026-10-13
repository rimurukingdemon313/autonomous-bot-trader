# PAPER FORWARD TEST — NOT REAL MONEY

Updated 2026-10-13 01:44 UTC · mode `PAPER_FORWARD` · profile `PAPER-FORWARD-200K` · shift started 2026-10-12 21:13 UTC · decision system `dual_ai`

Research status (historical, unchanged): **NO EDGE — DO NOT TRADE (historical research; this test measures forward)**. This run measures the system forward; it is not evidence of an edge until it has a sample and the forward-eligibility rules say so.

| Account | Equity | P&L today | Total P&L | Drawdown | Open | Trades | Win rate | Expectancy | Profit factor | Risk | Bot |
|---|---|---|---|---|---|---|---|---|---|---|---|
| $200,000.00 | $199,613.52 | $-739.76 | $-386.48 | $-386.48 | 1 | 4 (insufficient) | 25.0% | -0.216R | 0.64 | ACTIVE | RUNNING |

## Last decisions (decision → risk → paper execution)

- 10-13 01:30 AUDUSD SELL: AI DECISION → RISK APPROVED → PAPER EXECUTED
- 10-12 21:45 EURUSD SELL: AI DECISION → RISK APPROVED → PAPER EXECUTED
- 10-12 18:00 GBPUSD SELL: AI DECISION → RISK APPROVED → PAPER EXECUTED
- 10-12 13:00 USDJPY BUY: AI DECISION → RISK APPROVED → PAPER EXECUTED
- 10-12 10:30 EURUSD SELL: AI DECISION → RISK APPROVED → PAPER EXECUTED

## Latest decisions, NO TRADE included (337 so far)

- 10-13 01:30 AUDUSD SELL: SELL AUDUSD on M15: DEBATE: Trader 1 (dots-studio/dots-3-note-preview:free) BUY 75: The higher timeframe bias is bullish, and the price is testing a strong support zone at the previous day low (0.6957
- 10-13 00:15 USDJPY NO_TRADE: market unavailable for a decision: risk engine: currency_exposure (2 open positions share a currency, max 2): the model was not consulted
- 10-12 23:00 GBPUSD NO_TRADE: market unavailable for a decision: blocked before consulting the model: DATA_QUALITY: latest bar closed 120 minutes ago; STALE_DATA: last closed bar is 120 minutes old; EXPOSURE: a GBPUSD position is  [data: latest bar closed 120 minutes ago]
- 10-12 21:45 EURUSD SELL: SELL EURUSD on M15: DEBATE: Trader 1 (dots-studio/dots-3-note-preview:free) BUY 65: The price is at the bottom of the H4 range and major support confluence (PDL/PWL 1.11557) following a bullish liquid
- 10-12 20:30 AUDUSD NO_TRADE: market unavailable for a decision: risk engine: currency_exposure (2 open positions share a currency, max 2): the model was not consulted
- 10-12 19:15 USDJPY NO_TRADE: market unavailable for a decision: blocked before consulting the model: EXPOSURE: a USDJPY position is already open
- 10-12 18:00 GBPUSD SELL: SELL GBPUSD on M15: DEBATE: Trader 1 (dots-studio/dots-3-note-preview:free) BUY 65: The H4 trend is bullish, and the price is testing a major support confluence at 1.3203 (EQL, HL, and multi-touch S/R
- 10-12 16:45 EURUSD NO_TRADE: Trader 1 (vision) gave no usable answer (TIMEOUT: no answer within 420 s (last: INVALID: the reply was cut at max_tokens before its JSON (a reasoning model spent the budget thinking))): no decision on
- 10-12 15:30 USDCAD NO_TRADE: market unavailable for a decision: risk engine: currency_exposure (2 open positions share a currency, max 2): the model was not consulted
- 10-12 14:15 AUDUSD NO_TRADE: market unavailable for a decision: risk engine: currency_exposure (2 open positions share a currency, max 2): the model was not consulted
- 10-12 13:00 USDJPY BUY: BUY USDJPY on M15: DEBATE: Trader 1 (dots-studio/dots-3-note-preview:free) SELL 65: The price swept the highs at 158.641 with a bearish liquidity signal, indicating a stop hunt and distribution. Enter
- 10-12 11:45 GBPUSD NO_TRADE: Trader 1 (vision) gave no usable answer (INVALID: no JSON object in the reply): no decision on one trader alone

## Open paper positions

| Symbol | Side | Qty | Entry | Stop | Target | P&L |
|---|---|---|---|---|---|---|
| AUDUSD | SELL | 2.48 | 0.69574 | 0.69651 | 0.6948 | $47.12 |

## Closed paper trades (latest 20)

| Closed | Symbol | Side | Net | R | Costs | Exit | Source |
|---|---|---|---|---|---|---|---|
| 10-13 01:03 | EURUSD | SELL | $-431.70 | -0.86 | $87.38 | STOP | DUAL_AI |
| 10-13 01:04 | GBPUSD | SELL | $-355.19 | -0.71 | $110.84 | STOP | DUAL_AI |
| 10-12 21:01 | USDJPY | BUY | $-414.90 | -0.83 | $114.86 | STOP | DUAL_AI |
| 10-12 15:38 | EURUSD | SELL | $768.18 | +1.54 | $66.08 | TARGET | DUAL_AI |

## Dual AI desk (two free OpenRouter traders; a debate when they disagree)

OpenRouter `READY` · key set · trader 1 `dots-studio/dots-3-note-preview:free` · trader 2 `nvidia/nemotron-3-ultra-550b-a55b:free` · debate `apodex/apodex-1.1-mini:free` · calls today 6/900

AI trades 4 (insufficient) · wins 1 · losses 3 · expectancy -0.216R · profit factor 0.64

| Time | Symbol | Trader 1 | Trader 2 | Debate | Rule | Final | Risk |
|---|---|---|---|---|---|---|---|
| 10-13 01:30 | AUDUSD | BUY 75 | SELL 70 | SELL | DEBATE | SELL | APPROVED |
| 10-13 00:15 | USDJPY | -  | -  | - | MARKET_UNAVAILABLE | NO_TRADE | - |
| 10-12 23:00 | GBPUSD | -  | -  | - | MARKET_UNAVAILABLE | NO_TRADE | - |
| 10-12 21:45 | EURUSD | BUY 65 | SELL 55 | SELL | DEBATE | SELL | APPROVED |
| 10-12 20:30 | AUDUSD | -  | -  | - | MARKET_UNAVAILABLE | NO_TRADE | - |
| 10-12 19:15 | USDJPY | -  | -  | - | MARKET_UNAVAILABLE | NO_TRADE | - |
| 10-12 18:00 | GBPUSD | BUY 65 | SELL 60 | SELL | DEBATE | SELL | APPROVED |
| 10-12 16:45 | EURUSD | -  | -  | - | TRADER1_UNAVAILABLE | NO_TRADE | - |
| 10-12 15:30 | USDCAD | -  | -  | - | MARKET_UNAVAILABLE | NO_TRADE | - |
| 10-12 14:15 | AUDUSD | -  | -  | - | MARKET_UNAVAILABLE | NO_TRADE | - |
| 10-12 13:00 | USDJPY | SELL 65 | BUY 70 | BUY | DEBATE | BUY | APPROVED |
| 10-12 11:45 | GBPUSD | -  | -  | - | TRADER1_UNAVAILABLE | NO_TRADE | - |

The chart Trader 1 read last: `last_chart.png`.

Full figures: `paper_forward.json`. Rules: `docs/PAPER_FORWARD.md` on main.
