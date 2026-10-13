# PAPER FORWARD TEST — NOT REAL MONEY

Updated 2026-10-13 06:34 UTC · mode `PAPER_FORWARD` · profile `PAPER-FORWARD-200K` · shift started 2026-10-13 02:49 UTC · decision system `dual_ai`

Research status (historical, unchanged): **NO EDGE — DO NOT TRADE (historical research; this test measures forward)**. This run measures the system forward; it is not evidence of an edge until it has a sample and the forward-eligibility rules say so.

| Account | Equity | P&L today | Total P&L | Drawdown | Open | Trades | Win rate | Expectancy | Profit factor | Risk | Bot |
|---|---|---|---|---|---|---|---|---|---|---|---|
| $200,000.00 | $199,324.30 | $-1,028.99 | $-675.70 | $-675.70 | 1 | 5 (insufficient) | 20.0% | -0.346R | 0.54 | ACTIVE | RUNNING |

## Last decisions (decision → risk → paper execution)

- 10-13 02:45 USDCAD SELL: AI DECISION → RISK APPROVED → PAPER EXECUTED
- 10-13 01:30 AUDUSD SELL: AI DECISION → RISK APPROVED → PAPER EXECUTED
- 10-12 21:45 EURUSD SELL: AI DECISION → RISK APPROVED → PAPER EXECUTED
- 10-12 18:00 GBPUSD SELL: AI DECISION → RISK APPROVED → PAPER EXECUTED
- 10-12 13:00 USDJPY BUY: AI DECISION → RISK APPROVED → PAPER EXECUTED
- 10-12 10:30 EURUSD SELL: AI DECISION → RISK APPROVED → PAPER EXECUTED

## Latest decisions, NO TRADE included (340 so far)

- 10-13 05:15 GBPUSD NO_TRADE: market unavailable for a decision: risk engine: currency_exposure (2 open positions share a currency, max 2): the model was not consulted
- 10-13 04:00 EURUSD NO_TRADE: market unavailable for a decision: risk engine: currency_exposure (2 open positions share a currency, max 2): the model was not consulted
- 10-13 02:45 USDCAD SELL: SELL USDCAD on M15: AGREE: Trader 1 (dots-studio/dots-3-note-preview:free) SELL 65: The M15 structure is bearish with a recent break of low, and price is reacting to a tested supply order block. Selli
- 10-13 01:30 AUDUSD SELL: SELL AUDUSD on M15: DEBATE: Trader 1 (dots-studio/dots-3-note-preview:free) BUY 75: The higher timeframe bias is bullish, and the price is testing a strong support zone at the previous day low (0.6957
- 10-13 00:15 USDJPY NO_TRADE: market unavailable for a decision: risk engine: currency_exposure (2 open positions share a currency, max 2): the model was not consulted
- 10-12 23:00 GBPUSD NO_TRADE: market unavailable for a decision: blocked before consulting the model: DATA_QUALITY: latest bar closed 120 minutes ago; STALE_DATA: last closed bar is 120 minutes old; EXPOSURE: a GBPUSD position is  [data: latest bar closed 120 minutes ago]
- 10-12 21:45 EURUSD SELL: SELL EURUSD on M15: DEBATE: Trader 1 (dots-studio/dots-3-note-preview:free) BUY 65: The price is at the bottom of the H4 range and major support confluence (PDL/PWL 1.11557) following a bullish liquid
- 10-12 20:30 AUDUSD NO_TRADE: market unavailable for a decision: risk engine: currency_exposure (2 open positions share a currency, max 2): the model was not consulted
- 10-12 19:15 USDJPY NO_TRADE: market unavailable for a decision: blocked before consulting the model: EXPOSURE: a USDJPY position is already open
- 10-12 18:00 GBPUSD SELL: SELL GBPUSD on M15: DEBATE: Trader 1 (dots-studio/dots-3-note-preview:free) BUY 65: The H4 trend is bullish, and the price is testing a major support confluence at 1.3203 (EQL, HL, and multi-touch S/R
- 10-12 16:45 EURUSD NO_TRADE: Trader 1 (vision) gave no usable answer (TIMEOUT: no answer within 420 s (last: INVALID: the reply was cut at max_tokens before its JSON (a reasoning model spent the budget thinking))): no decision on
- 10-12 15:30 USDCAD NO_TRADE: market unavailable for a decision: risk engine: currency_exposure (2 open positions share a currency, max 2): the model was not consulted

## Open paper positions

| Symbol | Side | Qty | Entry | Stop | Target | P&L |
|---|---|---|---|---|---|---|
| USDCAD | SELL | 2.44 | 1.426515 | 1.4276 | 1.4245 | $-27.37 |

## Closed paper trades (latest 20)

| Closed | Symbol | Side | Net | R | Costs | Exit | Source |
|---|---|---|---|---|---|---|---|
| 10-13 05:42 | AUDUSD | SELL | $-214.73 | -0.86 | $47.12 | STOP | DUAL_AI |
| 10-13 01:03 | EURUSD | SELL | $-431.70 | -0.86 | $87.38 | STOP | DUAL_AI |
| 10-13 01:04 | GBPUSD | SELL | $-355.19 | -0.71 | $110.84 | STOP | DUAL_AI |
| 10-12 21:01 | USDJPY | BUY | $-414.90 | -0.83 | $114.86 | STOP | DUAL_AI |
| 10-12 15:38 | EURUSD | SELL | $768.18 | +1.54 | $66.08 | TARGET | DUAL_AI |

## Dual AI desk (two free OpenRouter traders; a debate when they disagree)

OpenRouter `READY` · key set · trader 1 `nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free` · trader 2 `nvidia/nemotron-3-ultra-550b-a55b:free` · debate `dots-studio/dots-3-note-preview:free` · calls today 8/900

AI trades 5 (insufficient) · wins 1 · losses 4 · expectancy -0.346R · profit factor 0.54

| Time | Symbol | Trader 1 | Trader 2 | Debate | Rule | Final | Risk |
|---|---|---|---|---|---|---|---|
| 10-13 05:15 | GBPUSD | -  | -  | - | MARKET_UNAVAILABLE | NO_TRADE | - |
| 10-13 04:00 | EURUSD | -  | -  | - | MARKET_UNAVAILABLE | NO_TRADE | - |
| 10-13 02:45 | USDCAD | SELL 65 | SELL 60 | - | AGREE | SELL | APPROVED |
| 10-13 01:30 | AUDUSD | BUY 75 | SELL 70 | SELL | DEBATE | SELL | APPROVED |
| 10-13 00:15 | USDJPY | -  | -  | - | MARKET_UNAVAILABLE | NO_TRADE | - |
| 10-12 23:00 | GBPUSD | -  | -  | - | MARKET_UNAVAILABLE | NO_TRADE | - |
| 10-12 21:45 | EURUSD | BUY 65 | SELL 55 | SELL | DEBATE | SELL | APPROVED |
| 10-12 20:30 | AUDUSD | -  | -  | - | MARKET_UNAVAILABLE | NO_TRADE | - |
| 10-12 19:15 | USDJPY | -  | -  | - | MARKET_UNAVAILABLE | NO_TRADE | - |
| 10-12 18:00 | GBPUSD | BUY 65 | SELL 60 | SELL | DEBATE | SELL | APPROVED |
| 10-12 16:45 | EURUSD | -  | -  | - | TRADER1_UNAVAILABLE | NO_TRADE | - |
| 10-12 15:30 | USDCAD | -  | -  | - | MARKET_UNAVAILABLE | NO_TRADE | - |

The chart Trader 1 read last: `last_chart.png`.

Full figures: `paper_forward.json`. Rules: `docs/PAPER_FORWARD.md` on main.
