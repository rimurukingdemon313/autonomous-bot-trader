# PAPER FORWARD TEST — NOT REAL MONEY

Updated 2026-10-12 21:43 UTC · mode `PAPER_FORWARD` · profile `PAPER-FORWARD-200K` · shift started 2026-10-12 21:13 UTC · decision system `dual_ai`

Research status (historical, unchanged): **NO EDGE — DO NOT TRADE (historical research; this test measures forward)**. This run measures the system forward; it is not evidence of an edge until it has a sample and the forward-eligibility rules say so.

| Account | Equity | P&L today | Total P&L | Drawdown | Open | Trades | Win rate | Expectancy | Profit factor | Risk | Bot |
|---|---|---|---|---|---|---|---|---|---|---|---|
| $200,000.00 | $200,296.34 | $296.34 | $296.34 | $0.00 | 2 | 1 (insufficient) | 100.0% | +1.540R | n/a | ACTIVE | RUNNING |

## Last decisions (decision → risk → paper execution)

- 10-12 18:00 GBPUSD SELL: AI DECISION → RISK APPROVED → PAPER EXECUTED
- 10-12 13:00 USDJPY BUY: AI DECISION → RISK APPROVED → PAPER EXECUTED
- 10-12 10:30 EURUSD SELL: AI DECISION → RISK APPROVED → PAPER EXECUTED

## Latest decisions, NO TRADE included (333 so far)

- 10-12 20:30 AUDUSD NO_TRADE: market unavailable for a decision: risk engine: currency_exposure (2 open positions share a currency, max 2): the model was not consulted
- 10-12 19:15 USDJPY NO_TRADE: market unavailable for a decision: blocked before consulting the model: EXPOSURE: a USDJPY position is already open
- 10-12 18:00 GBPUSD SELL: SELL GBPUSD on M15: DEBATE: Trader 1 (dots-studio/dots-3-note-preview:free) BUY 65: The H4 trend is bullish, and the price is testing a major support confluence at 1.3203 (EQL, HL, and multi-touch S/R
- 10-12 16:45 EURUSD NO_TRADE: Trader 1 (vision) gave no usable answer (TIMEOUT: no answer within 420 s (last: INVALID: the reply was cut at max_tokens before its JSON (a reasoning model spent the budget thinking))): no decision on
- 10-12 15:30 USDCAD NO_TRADE: market unavailable for a decision: risk engine: currency_exposure (2 open positions share a currency, max 2): the model was not consulted
- 10-12 14:15 AUDUSD NO_TRADE: market unavailable for a decision: risk engine: currency_exposure (2 open positions share a currency, max 2): the model was not consulted
- 10-12 13:00 USDJPY BUY: BUY USDJPY on M15: DEBATE: Trader 1 (dots-studio/dots-3-note-preview:free) SELL 65: The price swept the highs at 158.641 with a bearish liquidity signal, indicating a stop hunt and distribution. Enter
- 10-12 11:45 GBPUSD NO_TRADE: Trader 1 (vision) gave no usable answer (INVALID: no JSON object in the reply): no decision on one trader alone
- 10-12 10:30 EURUSD SELL: SELL EURUSD on M15: AGREE: Trader 1 (dots-studio/dots-3-note-preview:free) SELL 72: The M15 chart shows a well-established down trend with consecutive bearish BOS and lower lows, breaking key support 
- 10-12 08:01 AUDJPY NO_TRADE: blocked: UNFAMILIAR_STATE (risk): familiarity distance inf
- 10-12 08:01 EURCHF NO_TRADE: blocked: UNFAMILIAR_STATE (risk): familiarity distance inf
- 10-12 08:01 GBPJPY NO_TRADE: blocked: UNFAMILIAR_STATE (risk): familiarity distance inf

## Open paper positions

| Symbol | Side | Qty | Entry | Stop | Target | P&L |
|---|---|---|---|---|---|---|
| GBPUSD | SELL | 4.38 | 1.32083 | 1.32138 | 1.31855 | $-56.94 |
| USDJPY | BUY | 6.35 | 158.641 | 158.555 | 158.75 | n/a |

## Closed paper trades (latest 20)

| Closed | Symbol | Side | Net | R | Costs | Exit | Source |
|---|---|---|---|---|---|---|---|
| 10-12 15:38 | EURUSD | SELL | $768.18 | +1.54 | $66.08 | TARGET | DUAL_AI |

## Dual AI desk (two free OpenRouter traders; a debate when they disagree)

OpenRouter `NO_FREE_MODEL` · key set · trader 1 `None` · trader 2 `None` · debate `None` · calls today 0/900

AI trades 1 (insufficient) · wins 1 · losses 0 · expectancy +1.540R · profit factor n/a

| Time | Symbol | Trader 1 | Trader 2 | Debate | Rule | Final | Risk |
|---|---|---|---|---|---|---|---|
| 10-12 20:30 | AUDUSD | -  | -  | - | MARKET_UNAVAILABLE | NO_TRADE | - |
| 10-12 19:15 | USDJPY | -  | -  | - | MARKET_UNAVAILABLE | NO_TRADE | - |
| 10-12 18:00 | GBPUSD | BUY 65 | SELL 60 | SELL | DEBATE | SELL | APPROVED |
| 10-12 16:45 | EURUSD | -  | -  | - | TRADER1_UNAVAILABLE | NO_TRADE | - |
| 10-12 15:30 | USDCAD | -  | -  | - | MARKET_UNAVAILABLE | NO_TRADE | - |
| 10-12 14:15 | AUDUSD | -  | -  | - | MARKET_UNAVAILABLE | NO_TRADE | - |
| 10-12 13:00 | USDJPY | SELL 65 | BUY 70 | BUY | DEBATE | BUY | APPROVED |
| 10-12 11:45 | GBPUSD | -  | -  | - | TRADER1_UNAVAILABLE | NO_TRADE | - |
| 10-12 10:30 | EURUSD | SELL 72 | SELL 68 | - | AGREE | SELL | APPROVED |

The chart Trader 1 read last: `last_chart.png`.

Full figures: `paper_forward.json`. Rules: `docs/PAPER_FORWARD.md` on main.
