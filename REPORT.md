# PAPER FORWARD TEST — NOT REAL MONEY

Updated 2026-10-12 14:03 UTC · mode `PAPER_FORWARD` · profile `PAPER-FORWARD-200K` · shift started 2026-10-12 10:02 UTC · decision system `dual_ai`

Research status (historical, unchanged): **NO EDGE — DO NOT TRADE (historical research; this test measures forward)**. This run measures the system forward; it is not evidence of an edge until it has a sample and the forward-eligibility rules say so.

| Account | Equity | P&L today | Total P&L | Drawdown | Open | Trades | Win rate | Expectancy | Profit factor | Risk | Bot |
|---|---|---|---|---|---|---|---|---|---|---|---|
| $200,000.00 | $200,461.14 | $461.14 | $461.14 | $0.00 | 2 | 0 (none) | n/a | n/a | n/a | ACTIVE | RUNNING |

## Last decisions (decision → risk → paper execution)

- 10-12 13:00 USDJPY BUY: AI DECISION → RISK APPROVED → PAPER EXECUTED
- 10-12 10:30 EURUSD SELL: AI DECISION → RISK APPROVED → PAPER EXECUTED

## Latest decisions, NO TRADE included (327 so far)

- 10-12 13:00 USDJPY BUY: BUY USDJPY on M15: DEBATE: Trader 1 (dots-studio/dots-3-note-preview:free) SELL 65: The price swept the highs at 158.641 with a bearish liquidity signal, indicating a stop hunt and distribution. Enter
- 10-12 11:45 GBPUSD NO_TRADE: Trader 1 (vision) gave no usable answer (INVALID: no JSON object in the reply): no decision on one trader alone
- 10-12 10:30 EURUSD SELL: SELL EURUSD on M15: AGREE: Trader 1 (dots-studio/dots-3-note-preview:free) SELL 72: The M15 chart shows a well-established down trend with consecutive bearish BOS and lower lows, breaking key support 
- 10-12 08:01 AUDJPY NO_TRADE: blocked: UNFAMILIAR_STATE (risk): familiarity distance inf
- 10-12 08:01 EURCHF NO_TRADE: blocked: UNFAMILIAR_STATE (risk): familiarity distance inf
- 10-12 08:01 GBPJPY NO_TRADE: blocked: UNFAMILIAR_STATE (risk): familiarity distance inf
- 10-12 08:01 EURJPY NO_TRADE: blocked: UNFAMILIAR_STATE (risk): familiarity distance inf
- 10-12 08:01 EURGBP NO_TRADE: blocked: UNFAMILIAR_STATE (risk): familiarity distance inf
- 10-12 08:01 NZDUSD NO_TRADE: blocked: UNFAMILIAR_STATE (risk): familiarity distance inf
- 10-12 08:01 USDCHF NO_TRADE: blocked: UNFAMILIAR_STATE (risk): familiarity distance inf
- 10-12 08:01 USDCAD NO_TRADE: blocked: UNFAMILIAR_STATE (risk): familiarity distance inf
- 10-12 08:01 AUDUSD NO_TRADE: blocked: UNFAMILIAR_STATE (risk): familiarity distance inf

## Open paper positions

| Symbol | Side | Qty | Entry | Stop | Target | P&L |
|---|---|---|---|---|---|---|
| USDJPY | BUY | 6.35 | 158.641 | 158.555 | 158.75 | $44.01 |
| EURUSD | SELL | 4.13 | 1.11875 | 1.11957 | 1.11682 | $417.13 |

## Closed paper trades (latest 20)

| Closed | Symbol | Side | Net | R | Costs | Exit | Source |
|---|---|---|---|---|---|---|---|

## Dual AI desk (two free OpenRouter traders; a debate when they disagree)

OpenRouter `READY` · key set · trader 1 `dots-studio/dots-3-note-preview:free` · trader 2 `nvidia/nemotron-3-ultra-550b-a55b:free` · debate `apodex/apodex-1.1-mini:free` · calls today 16/900

AI trades 0 (none) · wins 0 · losses 0 · expectancy n/a · profit factor n/a

| Time | Symbol | Trader 1 | Trader 2 | Debate | Rule | Final | Risk |
|---|---|---|---|---|---|---|---|
| 10-12 13:00 | USDJPY | SELL 65 | BUY 70 | BUY | DEBATE | BUY | APPROVED |
| 10-12 11:45 | GBPUSD | -  | -  | - | TRADER1_UNAVAILABLE | NO_TRADE | - |
| 10-12 10:30 | EURUSD | SELL 72 | SELL 68 | - | AGREE | SELL | APPROVED |

The chart Agent 1 read last: `last_chart.png`.

Full figures: `paper_forward.json`. Rules: `docs/PAPER_FORWARD.md` on main.
