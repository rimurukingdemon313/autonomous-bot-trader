# PAPER FORWARD TEST — NOT REAL MONEY

Updated 2026-10-21 08:29 UTC · mode `PAPER_FORWARD` · profile `PAPER-FORWARD-200K` · shift started 2026-10-21 07:43 UTC · decision system `dual_ai`

Research status (historical, unchanged): **NO EDGE — DO NOT TRADE (historical research; this test measures forward)**. This run measures the system forward; it is not evidence of an edge until it has a sample and the forward-eligibility rules say so.

## The rule that trades: a trade only when both AIs agree

| Trades | Wins | Losses | Win rate | Net P&L | Expectancy | Profit factor | Max drawdown |
|---|---|---|---|---|---|---|---|
| 70 (adequate) | 32 | 38 | 45.7% | $594.59 | -0.023R | 1.05 | $3,637.77 |

The 4 trade(s) of the old DEBATE rule, stopped in dual-ai-1.2.0, were removed from the paper account at the operator's request: their net $-1,416.51 was put back by a declared adjustment ($1,416.51). They stay in the journal (append-only), in none of the account's figures below.

## Paper account

| Account | Equity | P&L today | Total P&L | Drawdown | Open | Trades | Win rate | Expectancy | Profit factor | Risk | Bot |
|---|---|---|---|---|---|---|---|---|---|---|---|
| $200,000.00 | $200,720.49 | $-1,024.90 | $720.49 | $0.00 | 2 | 70 (adequate) | 45.7% | -0.023R | 1.05 | ACTIVE | RUNNING |

Equity includes declared operator adjustments of $1,416.51 (without them: $199,303.97); P&L today excludes them. `remove-retired-debate-rule-trades-2026-10-15`: operator: the 4 trades of the retired debate rule (dual-ai 1.1.0, stopped in 1.2.0) are removed from the paper account; they stay in the journal.

## Last decisions (decision → risk → paper execution)

- 10-21 08:05 AUDUSD BUY: AI DECISION → RISK APPROVED → PAPER EXECUTED
- 10-21 07:31 EURGBP SELL: AI DECISION → RISK REJECTED — reward_risk: 1.03 vs minimum 1.2; structure: H1 structure is range (mixed swings): no new position without a clear H1 trend (up HH+HL or down LH+LL)
- 10-21 07:30 NZDUSD BUY: AI DECISION → RISK APPROVED → PAPER EXECUTED
- 10-21 07:15 USDCHF SELL: AI DECISION → RISK REJECTED — reward_risk: 1.15 vs minimum 1.2
- 10-21 07:01 AUDUSD BUY: AI DECISION → RISK REJECTED — reward_risk: 0.97 vs minimum 1.2; currency_conflict: BUY AUDUSD would bet against an open position: AUDJPY SELL is short AUD
- 10-21 07:00 USDJPY SELL: AI DECISION → RISK REJECTED — structure: H1 structure is range (mixed swings): no new position without a clear H1 trend (up HH+HL or down LH+LL)
- 10-21 05:00 AUDJPY SELL: AI DECISION → RISK APPROVED → PAPER EXECUTED
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

## Latest decisions, NO TRADE included (1836 so far)

- 10-21 08:15 USDCHF NO_TRADE: risk engine: currency_exposure (2 open positions share a currency, max 2): the model was not consulted
- 10-21 08:15 USDCAD NO_TRADE: risk engine: currency_exposure (2 open positions share a currency, max 2): the model was not consulted
- 10-21 08:05 AUDUSD BUY: BUY AUDUSD on M15: AGREE: Trader 1 (minimax/minimax-m3.1-flash:free) BUY 64: The bullish case is supported by the H4 uptrend, bullish M15 CHoCH, repeated sell-side sweep at 0.70141, and strong short-t
- 10-21 08:00 USDJPY NO_TRADE: the traders disagree (Trader 1 BUY 62, Trader 2 SELL 55): no trade unless both choose the same side; the debate (dots-studio/dots-3-note-preview:free) would have chosen SELL: followed forward in shado
- 10-21 07:45 GBPUSD NO_TRADE: risk engine: currency_exposure (2 open positions share a currency, max 2): the model was not consulted
- 10-21 07:45 EURUSD NO_TRADE: risk engine: currency_exposure (2 open positions share a currency, max 2): the model was not consulted
- 10-21 07:31 EURGBP SELL: SELL EURGBP on M15: AGREE: Trader 1 (minimax/minimax-m3.1-flash:free) SELL 61: The higher-timeframe bearish structure and D1/H4 downside momentum outweigh the M15 recovery. Price is entering the teste
- 10-21 07:30 NZDUSD BUY: BUY NZDUSD on M15: AGREE: Trader 1 (minimax/minimax-m3.1-flash:free) BUY 68: Buy the confirmed M15 bullish structure break, supported by the bullish H4 context, recent low sweep, and upward momentum. 
- 10-21 07:15 USDCHF SELL: SELL USDCHF on M15: AGREE: Trader 1 (minimax/minimax-m3.1-flash:free) SELL 69: The H4 bearish trend and consecutive M15 bearish structure breaks favor selling after rejection from the supply order blo
- 10-21 07:15 USDCAD NO_TRADE: blocked before consulting the model: EXPOSURE: a USDCAD position is already open
- 10-21 07:01 AUDUSD BUY: BUY AUDUSD on M15: AGREE: Trader 1 (minimax/minimax-m3.1-flash:free) BUY 64: The higher-timeframe trend and repeated sell-side liquidity sweeps favor a long after the latest bullish M15 structure brea
- 10-21 07:00 USDJPY SELL: SELL USDJPY on M15: AGREE: Trader 1 (minimax/minimax-m3.1-flash:free) SELL 64: SELL has the stronger tactical setup because M15 bearish structure and repeated rejection from the 158.203-158.275 supply

## Open paper positions

| Symbol | Side | Qty | Entry | Stop | Target | P&L |
|---|---|---|---|---|---|---|
| AUDUSD | BUY | 4.04 | 0.7028599999999999 | 0.7019 | 0.7043 | $76.76 |
| NZDUSD | BUY | 0.91 | 0.568485 | 0.56737 | 0.56987 | $49.14 |

## Closed paper trades (latest 20)

| Closed | Symbol | Side | Net | R | Costs | Exit | Source | Rule |
|---|---|---|---|---|---|---|---|---|
| 10-21 07:49 | USDCAD | SELL | $234.40 | +0.94 | $46.70 | TARGET | DUAL_AI | AGREE |
| 10-21 07:01 | AUDJPY | SELL | $-108.91 | -0.88 | $14.11 | STOP | DUAL_AI | AGREE |
| 10-21 06:48 | EURCHF | BUY | $-212.22 | -0.85 | $32.80 | STOP | DUAL_AI | AGREE |
| 10-21 04:56 | AUDUSD | BUY | $-194.34 | -0.78 | $28.88 | STOP | DUAL_AI | AGREE |
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

## Dual AI desk (two free OpenRouter traders; a trade only when they agree)

OpenRouter `READY` · key set · trader 1 `minimax/minimax-m3.1-flash:free` · trader 2 `nvidia/nemotron-3.5-super-vl:free` · debate `nvidia/nemotron-3-ultra-550b-a55b:free` · calls today 11/900

Agreement trades 70 (adequate) · wins 32 · losses 38 · net $594.59 · expectancy -0.023R · profit factor 1.05 · old DEBATE rule (stopped in dual-ai-1.2.0): 4 trade(s), net $-1,416.51, removed from the account

Disagreements (not traded; the debate runs in shadow): 90 · the debate's pick if taken: 85 resolved (adequate), expectancy -0.206R · the side it rejected if taken: 90 resolved (adequate), expectancy -0.244R

Exits in shadow (the same trades, followed again; measured, never traded): break-even at +1R -0.031R vs +0.078R as taken (51, adequate) · held 24 h +0.258R vs +0.056R as taken (46, adequate) · stop and target twice as far +0.234R vs +0.056R as taken (46, adequate) · closed at 8 h (the exit before dual-ai 1.7.0) none resolved yet

Trades taken by session (UTC): ASIA 28 resolved (insufficient), expectancy +0.138R · LONDON 17 resolved (insufficient), expectancy +0.042R · OVERLAP 8 resolved (insufficient), expectancy -0.382R · NEW_YORK 12 resolved (insufficient), expectancy +0.257R · LATE 3 resolved (insufficient), expectancy -1.106R

| Time | Symbol | Trader 1 | Trader 2 | Debate (shadow) | Rule | Final | Risk |
|---|---|---|---|---|---|---|---|
| 10-21 08:15 | USDCHF | -  | -  | - | NOT_ASKED | NO_TRADE | - |
| 10-21 08:15 | USDCAD | -  | -  | - | NOT_ASKED | NO_TRADE | - |
| 10-21 08:05 | AUDUSD | BUY 64 | BUY 67 | - | AGREE | BUY | APPROVED |
| 10-21 08:00 | USDJPY | BUY 62 | SELL 55 | SELL | DISAGREE | NO_TRADE | - |
| 10-21 07:45 | GBPUSD | -  | -  | - | NOT_ASKED | NO_TRADE | - |
| 10-21 07:45 | EURUSD | -  | -  | - | NOT_ASKED | NO_TRADE | - |
| 10-21 07:31 | EURGBP | SELL 61 | SELL 60 | - | AGREE | SELL | REJECTED |
| 10-21 07:30 | NZDUSD | BUY 68 | BUY 55 | - | AGREE | BUY | APPROVED |
| 10-21 07:15 | USDCHF | SELL 69 | SELL 64 | - | AGREE | SELL | REJECTED |
| 10-21 07:15 | USDCAD | -  | -  | - | NOT_ASKED | NO_TRADE | - |
| 10-21 07:01 | AUDUSD | BUY 64 | BUY 63 | - | AGREE | BUY | REJECTED |
| 10-21 07:00 | USDJPY | SELL 64 | SELL 63 | - | AGREE | SELL | REJECTED |

The chart Trader 1 read last: `last_chart.png`. (numbers): no free vision model answered, so Trader 1 read the same chart from its numbers.

Full figures: `paper_forward.json`. Rules: `docs/PAPER_FORWARD.md` on main.
