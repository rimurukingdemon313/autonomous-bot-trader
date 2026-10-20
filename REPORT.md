# PAPER FORWARD TEST — NOT REAL MONEY

Updated 2026-10-20 01:41 UTC · mode `PAPER_FORWARD` · profile `PAPER-FORWARD-200K` · shift started 2026-10-19 22:10 UTC · decision system `dual_ai`

Research status (historical, unchanged): **NO EDGE — DO NOT TRADE (historical research; this test measures forward)**. This run measures the system forward; it is not evidence of an edge until it has a sample and the forward-eligibility rules say so.

## The rule that trades: a trade only when both AIs agree

| Trades | Wins | Losses | Win rate | Net P&L | Expectancy | Profit factor | Max drawdown |
|---|---|---|---|---|---|---|---|
| 54 (adequate) | 25 | 29 | 46.3% | $-105.93 | -0.029R | 0.99 | $3,487.06 |

The 4 trade(s) of the old DEBATE rule, stopped in dual-ai-1.2.0, were removed from the paper account at the operator's request: their net $-1,416.51 was put back by a declared adjustment ($1,416.51). They stay in the journal (append-only), in none of the account's figures below.

## Paper account

| Account | Equity | P&L today | Total P&L | Drawdown | Open | Trades | Win rate | Expectancy | Profit factor | Risk | Bot |
|---|---|---|---|---|---|---|---|---|---|---|---|
| $200,000.00 | $199,738.41 | $-160.10 | $-261.59 | $-261.59 | 2 | 54 (adequate) | 46.3% | -0.029R | 0.99 | ACTIVE | RUNNING |

Equity includes declared operator adjustments of $1,416.51 (without them: $198,321.89); P&L today excludes them. `remove-retired-debate-rule-trades-2026-10-15`: operator: the 4 trades of the retired debate rule (dual-ai 1.1.0, stopped in 1.2.0) are removed from the paper account; they stay in the journal.

## Last decisions (decision → risk → paper execution)

- 10-20 01:33 AUDUSD SELL: AI DECISION → RISK REJECTED — currency_conflict: SELL AUDUSD would bet against an open position: NZDUSD BUY is short USD
- 10-20 01:30 USDJPY BUY: AI DECISION → RISK REJECTED — currency_conflict: BUY USDJPY would bet against an open position: NZDUSD BUY is short USD; structure: H1 structure is range (mixed swings): no new position without a clear H1 trend (up HH+HL or down L
- 10-20 01:16 GBPUSD BUY: AI DECISION → RISK REJECTED — structure: H1 structure is range (mixed swings): no new position without a clear H1 trend (up HH+HL or down LH+LL)
- 10-20 01:15 EURUSD BUY: AI DECISION → RISK REJECTED — structure: H1 structure is range (mixed swings): no new position without a clear H1 trend (up HH+HL or down LH+LL)
- 10-20 01:01 AUDJPY SELL: AI DECISION → RISK REJECTED — reward_risk: 0.98 vs minimum 1.2; currency_conflict: SELL AUDJPY would bet against an open position: GBPJPY BUY is short JPY
- 10-20 01:00 EURCHF SELL: AI DECISION → RISK REJECTED — cost_to_risk: round-trip cost is 27.0% of the stop (max 25%): spread 0.00018 + commission and slippage
- 10-20 00:50 GBPJPY BUY: AI DECISION → RISK APPROVED → PAPER EXECUTED
- 10-20 00:45 EURJPY BUY: AI DECISION → RISK REJECTED — reward_risk: 1.03 vs minimum 1.2; structure: H1 structure is range (mixed swings): no new position without a clear H1 trend (up HH+HL or down LH+LL)
- 10-20 00:30 EURGBP SELL: AI DECISION → RISK REJECTED — structure: H1 structure is range (mixed swings): no new position without a clear H1 trend (up HH+HL or down LH+LL)
- 10-20 00:16 USDCHF SELL: AI DECISION → RISK REJECTED — reward_risk: 1.05 vs minimum 1.2; structure: H1 structure is range (mixed swings): no new position without a clear H1 trend (up HH+HL or down LH+LL)
- 10-20 00:15 USDCAD SELL: AI DECISION → RISK REJECTED — structure: H1 structure is range (mixed swings): no new position without a clear H1 trend (up HH+HL or down LH+LL)
- 10-19 19:36 AUDJPY BUY: AI DECISION → RISK REJECTED — reward_risk: 1.17 vs minimum 1.2
- 10-19 19:00 NZDUSD BUY: AI DECISION → RISK APPROVED → PAPER EXECUTED
- 10-19 18:45 USDCAD SELL: AI DECISION → RISK REJECTED — reward_risk: 1.02 vs minimum 1.2
- 10-19 18:34 AUDUSD SELL: AI DECISION → RISK REJECTED — reward_risk: 1.17 vs minimum 1.2; currency_conflict: SELL AUDUSD would bet against an open position: USDCHF SELL is short USD
- 10-19 18:30 USDJPY BUY: AI DECISION → RISK REJECTED — currency_conflict: BUY USDJPY would bet against an open position: USDCHF SELL is short USD
- 10-19 17:15 USDCAD SELL: AI DECISION → RISK APPROVED → PAPER EXECUTED
- 10-19 17:06 AUDUSD SELL: AI DECISION → RISK REJECTED — currency_conflict: SELL AUDUSD would bet against an open position: USDCHF SELL is short USD
- 10-19 16:53 GBPUSD SELL: AI DECISION → RISK REJECTED — currency_conflict: SELL GBPUSD would bet against an open position: USDCHF SELL is short USD; structure: H1 structure is range (mixed swings): no new position without a clear H1 trend (up HH+HL or down
- 10-19 16:15 EURGBP SELL: AI DECISION → RISK REJECTED — cost_to_risk: round-trip cost is 28.4% of the stop (max 25%): spread 0.00012 + commission and slippage

## Latest decisions, NO TRADE included (1590 so far)

- 10-20 01:33 AUDUSD SELL: SELL AUDUSD on M15: AGREE: Trader 1 (minimax/minimax-m3.1-flash:free) SELL 64: The bearish M15 structure break and repeated downside displacement favor continuation toward 0.69725 and then 0.69643. A 
- 10-20 01:30 USDJPY BUY: BUY USDJPY on M15: AGREE: Trader 1 (minimax/minimax-m3.1-flash:free) BUY 63: BUY offers the stronger probability because price has reclaimed the latest M15 bullish break and aligns with the H4 bullish
- 10-20 01:16 GBPUSD BUY: BUY GBPUSD on M15: AGREE: Trader 1 (minimax/minimax-m3.1-flash:free) BUY 60: Both timeframes retain bullish HH/HL structure, and M15 printed successive bullish breaks plus bullish displacement after r
- 10-20 01:15 EURUSD BUY: BUY EURUSD on M15: AGREE: Trader 1 (minimax/minimax-m3.1-flash:free) BUY 57: The M15 HH/HL structure, bullish CHOCH, recent low sweep, and demand support favor the buy side despite the H4 range. The l
- 10-20 01:01 AUDJPY SELL: SELL AUDJPY on M15: AGREE: Trader 1 (minimax/minimax-m3.1-flash:free) SELL 63: Price is selling from a tested supply block beneath nearby resistance after a bearish M15 CHoCH. The 110.477 equal-low li
- 10-20 01:00 EURCHF SELL: SELL EURCHF on M15: AGREE: Trader 1 (minimax/minimax-m3.1-flash:free) SELL 66: Sell the rejection from the 0.92670-0.92730 supply zone because the latest bearish M15 CHoCH aligns with the bearish H4 t
- 10-20 00:50 GBPJPY BUY: BUY GBPJPY on M15: AGREE: Trader 1 (minimax/minimax-m3.1-flash:free) BUY 70: Buy the confirmed M15 bullish structure break above 211.082, aligned with the bullish H4 structure and strong recent moment
- 10-20 00:45 EURJPY BUY: BUY EURJPY on M15: AGREE: Trader 1 (minimax/minimax-m3.1-flash:free) BUY 66: Buy because bullish M15 structure confirmation aligns with the higher-timeframe uptrend and reclaimed liquidity. A stop bel
- 10-20 00:30 EURGBP SELL: SELL EURGBP on M15: AGREE: Trader 1 (minimax/minimax-m3.1-flash:free) SELL 72: Sell because the recent bearish structural transition, negative momentum, and repeated sweeps of 0.84280 outweigh the sti
- 10-20 00:30 NZDUSD NO_TRADE: blocked before consulting the model: EXPOSURE: a NZDUSD position is already open
- 10-20 00:16 USDCHF SELL: SELL USDCHF on M15: AGREE: Trader 1 (minimax/minimax-m3.1-flash:free) SELL 76: A bearish sweep of 0.82695 and rejection from tested supply favor continuation lower while M15 momentum is decisively neg
- 10-20 00:15 USDCAD SELL: SELL USDCAD on M15: AGREE: Trader 1 (minimax/minimax-m3.1-flash:free) SELL 67: The higher-probability side is SELL because H4 remains bearish while M15 has produced a fresh bearish CHoCH, negative mul

## Open paper positions

| Symbol | Side | Qty | Entry | Stop | Target | P&L |
|---|---|---|---|---|---|---|
| GBPJPY | BUY | 2.45 | 211.1505 | 210.875 | 211.5 | $-143.55 |
| NZDUSD | BUY | 2.02 | 0.566385 | 0.5654 | 0.5676 | $-12.12 |

## Closed paper trades (latest 20)

| Closed | Symbol | Side | Net | R | Costs | Exit | Source | Rule |
|---|---|---|---|---|---|---|---|---|
| 10-20 00:08 | USDCHF | SELL | $105.23 | +0.21 | $94.45 | TIME | DUAL_AI | AGREE |
| 10-19 18:21 | USDCAD | SELL | $-389.37 | -0.78 | $87.65 | STOP | DUAL_AI | AGREE |
| 10-19 12:49 | EURGBP | SELL | $-218.72 | -0.88 | $33.09 | STOP | DUAL_AI | AGREE |
| 10-19 12:37 | USDCHF | SELL | $-101.96 | -0.82 | $19.31 | STOP | DUAL_AI | AGREE |
| 10-19 11:44 | USDCAD | SELL | $250.58 | +1.00 | $33.80 | TARGET | DUAL_AI | AGREE |
| 10-19 10:05 | USDJPY | SELL | $-193.70 | -0.78 | $34.94 | STOP | DUAL_AI | AGREE |
| 10-19 08:42 | EURUSD | SELL | $-202.17 | -0.81 | $34.34 | STOP | DUAL_AI | AGREE |
| 10-19 08:41 | EURCHF | SELL | $-212.36 | -0.86 | $32.82 | STOP | DUAL_AI | AGREE |
| 10-19 07:55 | EURJPY | BUY | $-212.66 | -0.86 | $24.44 | STOP | DUAL_AI | AGREE |
| 10-19 07:01 | GBPUSD | SELL | $-422.19 | -0.85 | $83.37 | STOP | DUAL_AI | AGREE |
| 10-19 06:28 | EURGBP | BUY | $-419.53 | -0.84 | $88.51 | STOP | DUAL_AI | AGREE |
| 10-19 03:31 | AUDUSD | BUY | $200.64 | +0.80 | $41.04 | TARGET | DUAL_AI | AGREE |
| 10-19 02:46 | GBPUSD | BUY | $-202.34 | -0.81 | $36.33 | STOP | DUAL_AI | AGREE |
| 10-16 16:02 | NZDUSD | BUY | $-453.45 | -0.91 | $66.00 | STOP | DUAL_AI | AGREE |
| 10-16 12:36 | EURJPY | BUY | $-432.45 | -0.87 | $48.70 | STOP | DUAL_AI | AGREE |
| 10-16 12:38 | EURUSD | BUY | $-477.37 | -0.96 | $35.53 | STOP | DUAL_AI | AGREE |
| 10-16 10:25 | EURJPY | BUY | $422.27 | +0.85 | $64.90 | TARGET | DUAL_AI | AGREE |
| 10-16 10:04 | EURUSD | BUY | $459.54 | +0.92 | $53.28 | TARGET | DUAL_AI | AGREE |
| 10-16 08:05 | EURGBP | SELL | $129.31 | +0.26 | $81.01 | TIME | DUAL_AI | AGREE |
| 10-16 07:02 | AUDUSD | BUY | $840.45 | +1.68 | $77.58 | TARGET | DUAL_AI | AGREE |

## Dual AI desk (two free OpenRouter traders; a trade only when they agree)

OpenRouter `READY` · key set · trader 1 `minimax/minimax-m3.1-flash:free` · trader 2 `nvidia/nemotron-3.5-super-vl:free` · debate `google/gemma-4-26b-a4b-it:free` · calls today 26/900

Agreement trades 54 (adequate) · wins 25 · losses 29 · net $-105.93 · expectancy -0.029R · profit factor 0.99 · old DEBATE rule (stopped in dual-ai-1.2.0): 4 trade(s), net $-1,416.51, removed from the account

Disagreements (not traded; the debate runs in shadow): 87 · the debate's pick if taken: 74 resolved (adequate), expectancy -0.207R · the side it rejected if taken: 79 resolved (adequate), expectancy -0.161R

Exits in shadow (the same trades, followed again; measured, never traded): break-even at +1R -0.118R vs -0.006R as taken (41, adequate) · held 24 h +0.429R vs +0.237R as taken (31, adequate) · stop and target twice as far +0.217R vs +0.237R as taken (31, adequate)

Trades taken by session (UTC): ASIA 24 resolved (insufficient), expectancy +0.083R · LONDON 15 resolved (insufficient), expectancy -0.149R · OVERLAP 8 resolved (insufficient), expectancy -0.382R · NEW_YORK 8 resolved (insufficient), expectancy +0.460R · LATE 3 resolved (insufficient), expectancy -1.106R

| Time | Symbol | Trader 1 | Trader 2 | Debate (shadow) | Rule | Final | Risk |
|---|---|---|---|---|---|---|---|
| 10-20 01:33 | AUDUSD | SELL 64 | SELL 63 | - | AGREE | SELL | REJECTED |
| 10-20 01:30 | USDJPY | BUY 63 | BUY 62 | - | AGREE | BUY | REJECTED |
| 10-20 01:16 | GBPUSD | BUY 60 | BUY 54 | - | AGREE | BUY | REJECTED |
| 10-20 01:15 | EURUSD | BUY 57 | BUY 58 | - | AGREE | BUY | REJECTED |
| 10-20 01:01 | AUDJPY | SELL 63 | SELL 58 | - | AGREE | SELL | REJECTED |
| 10-20 01:00 | EURCHF | SELL 66 | SELL 60 | - | AGREE | SELL | REJECTED |
| 10-20 00:50 | GBPJPY | BUY 70 | BUY 60 | - | AGREE | BUY | APPROVED |
| 10-20 00:45 | EURJPY | BUY 66 | BUY 68 | - | AGREE | BUY | REJECTED |
| 10-20 00:30 | EURGBP | SELL 72 | SELL 65 | - | AGREE | SELL | REJECTED |
| 10-20 00:30 | NZDUSD | -  | -  | - | NOT_ASKED | NO_TRADE | - |
| 10-20 00:16 | USDCHF | SELL 76 | SELL 67 | - | AGREE | SELL | REJECTED |
| 10-20 00:15 | USDCAD | SELL 67 | SELL 67 | - | AGREE | SELL | REJECTED |

The chart Trader 1 read last: `last_chart.png`. (numbers): no free vision model answered, so Trader 1 read the same chart from its numbers.

Full figures: `paper_forward.json`. Rules: `docs/PAPER_FORWARD.md` on main.
