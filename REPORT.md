# PAPER FORWARD TEST — NOT REAL MONEY

Updated 2026-10-21 02:53 UTC · mode `PAPER_FORWARD` · profile `PAPER-FORWARD-200K` · shift started 2026-10-21 02:08 UTC · decision system `dual_ai`

Research status (historical, unchanged): **NO EDGE — DO NOT TRADE (historical research; this test measures forward)**. This run measures the system forward; it is not evidence of an edge until it has a sample and the forward-eligibility rules say so.

## The rule that trades: a trade only when both AIs agree

| Trades | Wins | Losses | Win rate | Net P&L | Expectancy | Profit factor | Max drawdown |
|---|---|---|---|---|---|---|---|
| 66 (adequate) | 31 | 35 | 47.0% | $875.66 | -0.000R | 1.08 | $3,637.77 |

The 4 trade(s) of the old DEBATE rule, stopped in dual-ai-1.2.0, were removed from the paper account at the operator's request: their net $-1,416.51 was put back by a declared adjustment ($1,416.51). They stay in the journal (append-only), in none of the account's figures below.

## Paper account

| Account | Equity | P&L today | Total P&L | Drawdown | Open | Trades | Win rate | Expectancy | Profit factor | Risk | Bot |
|---|---|---|---|---|---|---|---|---|---|---|---|
| $200,000.00 | $200,752.91 | $-992.47 | $752.91 | $0.00 | 3 | 66 (adequate) | 47.0% | -0.000R | 1.08 | ACTIVE | RUNNING |

Equity includes declared operator adjustments of $1,416.51 (without them: $199,336.40); P&L today excludes them. `remove-retired-debate-rule-trades-2026-10-15`: operator: the 4 trades of the retired debate rule (dual-ai 1.1.0, stopped in 1.2.0) are removed from the paper account; they stay in the journal.

## Last decisions (decision → risk → paper execution)

- 10-21 02:45 USDCAD SELL: AI DECISION → RISK APPROVED → PAPER EXECUTED
- 10-21 02:31 AUDUSD BUY: AI DECISION → RISK APPROVED → PAPER EXECUTED
- 10-21 02:30 USDJPY SELL: AI DECISION → RISK REJECTED — currency_conflict: SELL USDJPY would bet against an open position: GBPJPY BUY is short JPY
- 10-21 01:00 EURCHF BUY: AI DECISION → RISK APPROVED → PAPER EXECUTED
- 10-21 00:46 GBPJPY BUY: AI DECISION → RISK APPROVED → PAPER EXECUTED
- 10-21 00:45 EURJPY BUY: AI DECISION → RISK APPROVED → PAPER EXECUTED
- 10-21 00:30 EURGBP SELL: AI DECISION → RISK REJECTED — cost_to_risk: round-trip cost is 27.6% of the stop (max 25%): spread 0.00012 + commission and slippage; currency_conflict: SELL EURGBP would bet against an open position: EURUSD BUY is long EUR
- 10-20 17:30 EURJPY BUY: AI DECISION → RISK APPROVED → PAPER EXECUTED
- 10-20 17:15 EURGBP SELL: AI DECISION → RISK REJECTED — reward_risk: 0.88 vs minimum 1.2; currency_conflict: SELL EURGBP would bet against an open position: EURUSD BUY is long EUR
- 10-20 16:35 GBPUSD BUY: AI DECISION → RISK APPROVED → PAPER EXECUTED
- 10-20 16:30 EURUSD BUY: AI DECISION → RISK APPROVED → PAPER EXECUTED
- 10-20 16:15 EURCHF BUY: AI DECISION → RISK REJECTED — structure: H1 structure is range (mixed swings): no new position without a clear H1 trend (up HH+HL or down LH+LL)
- 10-20 16:00 EURJPY BUY: AI DECISION → RISK REJECTED — structure: H1 structure is range (mixed swings): no new position without a clear H1 trend (up HH+HL or down LH+LL)
- 10-20 11:31 USDCHF SELL: AI DECISION → RISK APPROVED → PAPER EXECUTED
- 10-20 11:30 USDCAD SELL: AI DECISION → RISK REJECTED — structure: H1 structure is range (mixed swings): no new position without a clear H1 trend (up HH+HL or down LH+LL)
- 10-20 11:17 AUDUSD SELL: AI DECISION → RISK REJECTED — currency_conflict: SELL AUDUSD would bet against an open position: NZDUSD BUY is short USD
- 10-20 11:15 USDJPY SELL: AI DECISION → RISK REJECTED — cost_to_risk: round-trip cost is 25.3% of the stop (max 25%): spread 0.01 + commission and slippage; currency_conflict: SELL USDJPY would bet against an open position: GBPJPY BUY is short JPY; structu
- 10-20 10:33 GBPJPY BUY: AI DECISION → RISK APPROVED → PAPER EXECUTED
- 10-20 10:30 EURJPY SELL: AI DECISION → RISK REJECTED — structure: H1 structure is range (mixed swings): no new position without a clear H1 trend (up HH+HL or down LH+LL)
- 10-20 10:15 EURGBP SELL: AI DECISION → RISK REJECTED — cost_to_risk: round-trip cost is 25.9% of the stop (max 25%): spread 0.00012 + commission and slippage; structure: H1 structure is range (mixed swings): no new position without a clear H1 trend (up HH

## Latest decisions, NO TRADE included (1792 so far)

- 10-21 02:46 USDCHF NO_TRADE: risk engine: open_positions (3 open, max 3); currency_exposure (2 open positions share a currency, max 2): the model was not consulted
- 10-21 02:45 USDCAD SELL: SELL USDCAD on M15: AGREE: Trader 1 (minimax/minimax-m3.1-flash:free) SELL 63: Sell the rebound from the tested supply zone because the aligned M15/H4 bearish structures dominate. The stop is beyond t
- 10-21 02:31 AUDUSD BUY: BUY AUDUSD on M15: AGREE: Trader 1 (minimax/minimax-m3.1-flash:free) BUY 72: The aligned M15/H4 bullish structure and open bullish FVGs favor continuation buys, while price is retracing into a valid d
- 10-21 02:30 USDJPY SELL: SELL USDJPY on M15: AGREE: Trader 1 (minimax/minimax-m3.1-flash:free) SELL 58: The fresh M15 bearish structure break and sustained selling favor continuation toward the previous-day low, with the unte
- 10-21 02:15 GBPUSD NO_TRADE: blocked before consulting the model: STALE_DATA: quote is 417s old
- 10-21 02:15 EURUSD NO_TRADE: blocked before consulting the model: STALE_DATA: quote is 415s old
- 10-21 02:00 EURGBP NO_TRADE: risk engine: open_positions (3 open, max 3); currency_exposure (2 open positions share a currency, max 2): the model was not consulted
- 10-21 02:00 NZDUSD NO_TRADE: risk engine: open_positions (3 open, max 3): the model was not consulted
- 10-21 01:45 USDCHF NO_TRADE: risk engine: open_positions (3 open, max 3): the model was not consulted
- 10-21 01:45 USDCAD NO_TRADE: risk engine: open_positions (3 open, max 3): the model was not consulted
- 10-21 01:30 AUDUSD NO_TRADE: risk engine: open_positions (3 open, max 3): the model was not consulted
- 10-21 01:30 USDJPY NO_TRADE: risk engine: open_positions (3 open, max 3); currency_exposure (2 open positions share a currency, max 2): the model was not consulted

## Open paper positions

| Symbol | Side | Qty | Entry | Stop | Target | P&L |
|---|---|---|---|---|---|---|
| USDCAD | SELL | 2.54 | 1.4061149999999998 | 1.4071 | 1.40472 | $-10.84 |
| AUDUSD | BUY | 1.52 | 0.70246 | 0.7013 | 0.7043 | $-62.32 |
| EURCHF | BUY | 1.05 | 0.9273 | 0.9257 | 0.9295 | $-49.59 |

## Closed paper trades (latest 20)

| Closed | Symbol | Side | Net | R | Costs | Exit | Source | Rule |
|---|---|---|---|---|---|---|---|---|
| 10-21 02:33 | GBPJPY | BUY | $-202.37 | -0.81 | $41.78 | STOP | DUAL_AI | AGREE |
| 10-21 02:24 | EURJPY | BUY | $-196.89 | -0.79 | $43.04 | STOP | DUAL_AI | AGREE |
| 10-21 00:39 | GBPUSD | BUY | $-40.32 | -0.08 | $63.92 | TIME | DUAL_AI | AGREE |
| 10-21 00:35 | EURUSD | BUY | $-302.29 | -0.60 | $80.29 | TIME | DUAL_AI | AGREE |
| 10-20 21:01 | EURJPY | BUY | $-421.96 | -0.84 | $112.99 | STOP | DUAL_AI | AGREE |
| 10-20 12:47 | NZDUSD | BUY | $182.56 | +0.37 | $78.24 | TIME | DUAL_AI | AGREE |
| 10-20 12:42 | GBPJPY | BUY | $734.40 | +1.47 | $88.38 | TARGET | DUAL_AI | AGREE |
| 10-20 12:25 | USDCHF | SELL | $523.45 | +1.05 | $85.16 | TARGET | DUAL_AI | AGREE |
| 10-20 11:14 | USDCHF | SELL | $503.61 | +1.01 | $81.37 | TARGET | DUAL_AI | AGREE |
| 10-20 09:04 | EURCHF | SELL | $457.35 | +0.92 | $75.41 | TARGET | DUAL_AI | AGREE |
| 10-20 04:32 | GBPJPY | BUY | $-443.93 | -0.89 | $58.82 | STOP | DUAL_AI | AGREE |
| 10-20 03:08 | NZDUSD | BUY | $187.98 | +0.75 | $54.42 | TIME | DUAL_AI | AGREE |
| 10-20 00:08 | USDCHF | SELL | $105.23 | +0.21 | $94.45 | TIME | DUAL_AI | AGREE |
| 10-19 18:21 | USDCAD | SELL | $-389.37 | -0.78 | $87.65 | STOP | DUAL_AI | AGREE |
| 10-19 12:49 | EURGBP | SELL | $-218.72 | -0.88 | $33.09 | STOP | DUAL_AI | AGREE |
| 10-19 12:37 | USDCHF | SELL | $-101.96 | -0.82 | $19.31 | STOP | DUAL_AI | AGREE |
| 10-19 11:44 | USDCAD | SELL | $250.58 | +1.00 | $33.80 | TARGET | DUAL_AI | AGREE |
| 10-19 10:05 | USDJPY | SELL | $-193.70 | -0.78 | $34.94 | STOP | DUAL_AI | AGREE |
| 10-19 08:42 | EURUSD | SELL | $-202.17 | -0.81 | $34.34 | STOP | DUAL_AI | AGREE |
| 10-19 08:41 | EURCHF | SELL | $-212.36 | -0.86 | $32.82 | STOP | DUAL_AI | AGREE |

## Dual AI desk (two free OpenRouter traders; a trade only when they agree)

OpenRouter `READY` · key set · trader 1 `minimax/minimax-m3.1-flash:free` · trader 2 `nvidia/nemotron-3.5-super-vl:free` · debate `thinkingmachines/inkling-small:free` · calls today 6/900

Agreement trades 66 (adequate) · wins 31 · losses 35 · net $875.66 · expectancy -0.000R · profit factor 1.08 · old DEBATE rule (stopped in dual-ai-1.2.0): 4 trade(s), net $-1,416.51, removed from the account

Disagreements (not traded; the debate runs in shadow): 89 · the debate's pick if taken: 85 resolved (adequate), expectancy -0.206R · the side it rejected if taken: 90 resolved (adequate), expectancy -0.244R

Exits in shadow (the same trades, followed again; measured, never traded): break-even at +1R -0.031R vs +0.078R as taken (51, adequate) · held 24 h +0.213R vs +0.019R as taken (44, adequate) · stop and target twice as far +0.219R vs +0.019R as taken (44, adequate) · closed at 8 h (the exit before dual-ai 1.7.0) none resolved yet

Trades taken by session (UTC): ASIA 28 resolved (insufficient), expectancy +0.138R · LONDON 17 resolved (insufficient), expectancy +0.042R · OVERLAP 8 resolved (insufficient), expectancy -0.382R · NEW_YORK 12 resolved (insufficient), expectancy +0.257R · LATE 3 resolved (insufficient), expectancy -1.106R

| Time | Symbol | Trader 1 | Trader 2 | Debate (shadow) | Rule | Final | Risk |
|---|---|---|---|---|---|---|---|
| 10-21 02:46 | USDCHF | -  | -  | - | NOT_ASKED | NO_TRADE | - |
| 10-21 02:45 | USDCAD | SELL 63 | SELL 63 | - | AGREE | SELL | APPROVED |
| 10-21 02:31 | AUDUSD | BUY 72 | BUY 67 | - | AGREE | BUY | APPROVED |
| 10-21 02:30 | USDJPY | SELL 58 | SELL 55 | - | AGREE | SELL | REJECTED |
| 10-21 02:15 | GBPUSD | -  | -  | - | NOT_ASKED | NO_TRADE | - |
| 10-21 02:15 | EURUSD | -  | -  | - | NOT_ASKED | NO_TRADE | - |
| 10-21 02:00 | EURGBP | -  | -  | - | NOT_ASKED | NO_TRADE | - |
| 10-21 02:00 | NZDUSD | -  | -  | - | NOT_ASKED | NO_TRADE | - |
| 10-21 01:45 | USDCHF | -  | -  | - | NOT_ASKED | NO_TRADE | - |
| 10-21 01:45 | USDCAD | -  | -  | - | NOT_ASKED | NO_TRADE | - |
| 10-21 01:30 | AUDUSD | -  | -  | - | NOT_ASKED | NO_TRADE | - |
| 10-21 01:30 | USDJPY | -  | -  | - | NOT_ASKED | NO_TRADE | - |

The chart Trader 1 read last: `last_chart.png`. (numbers): no free vision model answered, so Trader 1 read the same chart from its numbers.

Full figures: `paper_forward.json`. Rules: `docs/PAPER_FORWARD.md` on main.
