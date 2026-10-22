# PAPER FORWARD TEST — NOT REAL MONEY

Updated 2026-10-22 08:36 UTC · mode `PAPER_FORWARD` · profile `PAPER-FORWARD-200K` · shift started 2026-10-22 06:05 UTC · decision system `dual_ai`

Research status (historical, unchanged): **NO EDGE — DO NOT TRADE (historical research; this test measures forward)**. This run measures the system forward; it is not evidence of an edge until it has a sample and the forward-eligibility rules say so.

## The rule that trades: a trade only when both AIs agree

| Trades | Wins | Losses | Win rate | Net P&L | Expectancy | Profit factor | Max drawdown |
|---|---|---|---|---|---|---|---|
| 80 (adequate) | 35 | 45 | 43.8% | $-1,271.48 | -0.058R | 0.91 | $4,943.76 |

The 4 trade(s) of the old DEBATE rule, stopped in dual-ai-1.2.0, were removed from the paper account at the operator's request: their net $-1,416.51 was put back by a declared adjustment ($1,416.51). They stay in the journal (append-only), in none of the account's figures below.

## Paper account

| Account | Equity | P&L today | Total P&L | Drawdown | Open | Trades | Win rate | Expectancy | Profit factor | Risk | Bot |
|---|---|---|---|---|---|---|---|---|---|---|---|
| $200,000.00 | $198,983.81 | $-874.41 | $-1,016.19 | $-1,016.19 | 1 | 80 (adequate) | 43.8% | -0.058R | 0.91 | ACTIVE | RUNNING |

Equity includes declared operator adjustments of $1,416.51 (without them: $197,567.29); P&L today excludes them. `remove-retired-debate-rule-trades-2026-10-15`: operator: the 4 trades of the retired debate rule (dual-ai 1.1.0, stopped in 1.2.0) are removed from the paper account; they stay in the journal.

## Last decisions (decision → risk → paper execution)

- 10-22 08:30 NZDUSD BUY: AI DECISION → RISK REJECTED — structure: H1 structure is range (mixed swings): no new position without a clear H1 trend (up HH+HL or down LH+LL)
- 10-22 08:16 USDCHF SELL: AI DECISION → RISK REJECTED — currency_conflict: SELL USDCHF would bet against an open position: AUDUSD SELL is long USD
- 10-22 08:15 USDCAD SELL: AI DECISION → RISK REJECTED — currency_conflict: SELL USDCAD would bet against an open position: AUDUSD SELL is long USD; structure: H1 structure is range (mixed swings): no new position without a clear H1 trend (up HH+HL or down 
- 10-22 08:00 USDJPY SELL: AI DECISION → RISK REJECTED — currency_conflict: SELL USDJPY would bet against an open position: AUDUSD SELL is long USD; structure: H1 structure is range (mixed swings): no new position without a clear H1 trend (up HH+HL or down 
- 10-22 07:48 GBPUSD SELL: AI DECISION → RISK REJECTED — reward_risk: 1.06 vs minimum 1.2; currency_conflict: SELL GBPUSD would bet against an open position: EURGBP SELL is long GBP
- 10-22 07:45 EURUSD BUY: AI DECISION → RISK REJECTED — reward_risk: 1.08 vs minimum 1.2; currency_conflict: BUY EURUSD would bet against an open position: AUDUSD SELL is long USD; EURGBP SELL is short EUR
- 10-22 07:31 AUDJPY SELL: AI DECISION → RISK REJECTED — reward_risk: 1.19 vs minimum 1.2
- 10-22 07:30 EURCHF SELL: AI DECISION → RISK REJECTED — reward_risk: 1.08 vs minimum 1.2; structure: H1 structure is range (mixed swings): no new position without a clear H1 trend (up HH+HL or down LH+LL)
- 10-22 07:18 GBPJPY SELL: AI DECISION → RISK REJECTED — currency_conflict: SELL GBPJPY would bet against an open position: EURGBP SELL is long GBP
- 10-22 07:15 EURJPY SELL: AI DECISION → RISK REJECTED — spread: spread is 32.3% of the stop (max 25%); cost_to_risk: round-trip cost is 51.6% of the stop (max 25%): spread 0.015 + commission and slippage; structure: H1 structure is range (mixed swings): no
- 10-22 07:03 EURGBP SELL: AI DECISION → RISK APPROVED → PAPER EXECUTED
- 10-22 07:00 NZDUSD BUY: AI DECISION → RISK REJECTED — cost_to_risk: round-trip cost is 31.0% of the stop (max 25%): spread 0.00015 + commission and slippage; currency_conflict: BUY NZDUSD would bet against an open position: AUDUSD SELL is long USD; struc
- 10-22 06:47 USDCHF SELL: AI DECISION → RISK REJECTED — currency_conflict: SELL USDCHF would bet against an open position: AUDUSD SELL is long USD
- 10-22 06:45 USDCAD SELL: AI DECISION → RISK REJECTED — reward_risk: 1.10 vs minimum 1.2; currency_conflict: SELL USDCAD would bet against an open position: AUDUSD SELL is long USD; structure: H1 structure is range (mixed swings): no new position without a
- 10-22 06:30 USDJPY SELL: AI DECISION → RISK REJECTED — currency_conflict: SELL USDJPY would bet against an open position: AUDUSD SELL is long USD; structure: H1 structure is range (mixed swings): no new position without a clear H1 trend (up HH+HL or down 
- 10-22 06:16 GBPUSD BUY: AI DECISION → RISK REJECTED — currency_conflict: BUY GBPUSD would bet against an open position: AUDUSD SELL is long USD
- 10-22 06:15 EURUSD SELL: AI DECISION → RISK REJECTED — reward_risk: 1.19 vs minimum 1.2
- 10-22 06:00 NZDUSD SELL: AI DECISION → RISK REJECTED — structure: H1 structure is range (mixed swings): no new position without a clear H1 trend (up HH+HL or down LH+LL)
- 10-22 05:49 USDCHF SELL: AI DECISION → RISK REJECTED — currency_conflict: SELL USDCHF would bet against an open position: AUDUSD SELL is long USD
- 10-22 05:45 USDCAD SELL: AI DECISION → RISK REJECTED — currency_conflict: SELL USDCAD would bet against an open position: AUDUSD SELL is long USD; structure: H1 structure is range (mixed swings): no new position without a clear H1 trend (up HH+HL or down 

## Latest decisions, NO TRADE included (2027 so far)

- 10-22 08:32 EURGBP NO_TRADE: blocked before consulting the model: EXPOSURE: a EURGBP position is already open
- 10-22 08:30 NZDUSD BUY: BUY NZDUSD on M15: AGREE: Trader 1 (minimax/minimax-m3.1-flash:free) BUY 66: Buy the retracement into established M15 support within the entry zone, using the session low at 0.56831 as the structural 
- 10-22 08:16 USDCHF SELL: SELL USDCHF on M15: AGREE: Trader 1 (minimax/minimax-m3.1-flash:free) SELL 67: Sell the continuation below 0.82184, with 0.82303 defining structural invalidation and the stop placed beyond it. The bea
- 10-22 08:15 USDCAD SELL: SELL USDCAD on M15: AGREE: Trader 1 (minimax/minimax-m3.1-flash:free) SELL 68: The higher-probability side is SELL because M15 has broken lower repeatedly and the current rally has reached tested supp
- 10-22 08:01 AUDUSD NO_TRADE: blocked before consulting the model: EXPOSURE: a AUDUSD position is already open
- 10-22 08:00 USDJPY SELL: SELL USDJPY on M15: AGREE: Trader 1 (minimax/minimax-m3.1-flash:free) SELL 68: Sell the rebound within the broader M15 downtrend and beneath the bearish H4 CHOCH. The stop is beyond the reclaimed bear
- 10-22 07:48 GBPUSD SELL: SELL GBPUSD on M15: AGREE: Trader 1 (minimax/minimax-m3.1-flash:free) SELL 59: Sell the repeated sweep of the 1.34081-1.34084 resistance cluster while price is inside the entry zone. The stop sits bey
- 10-22 07:45 EURUSD BUY: BUY EURUSD on M15: AGREE: Trader 1 (minimax/minimax-m3.1-flash:free) BUY 58: Buy the reaction from the 1.12397-1.12372 support and open bullish FVG area because it aligns with the higher-timeframe bul
- 10-22 07:31 AUDJPY SELL: SELL AUDJPY on M15: AGREE: Trader 1 (minimax/minimax-m3.1-flash:free) SELL 62: Sell the current M15 bearish continuation after the latest BOS and failed recovery, targeting the 109.950 low. The stop i
- 10-22 07:30 EURCHF SELL: SELL EURCHF on M15: AGREE: Trader 1 (minimax/minimax-m3.1-flash:free) SELL 68: Sell the countertrend rebound while M15 retains its bearish LH/LL structure and consecutive BOS sequence. The stop sits b
- 10-22 07:18 GBPJPY SELL: SELL GBPJPY on M15: AGREE: Trader 1 (minimax/minimax-m3.1-flash:free) SELL 68: Sell the continuing M15 bearish structure after the latest break of 210.458, targeting the visible low at 210.265. The st
- 10-22 07:15 EURJPY SELL: SELL EURJPY on M15: AGREE: Trader 1 (minimax/minimax-m3.1-flash:free) SELL 74: The M15 bearish structure and forceful displacement favor continuation toward 176.289 and 176.203. A reclaim of 176.651 w

## Open paper positions

| Symbol | Side | Qty | Entry | Stop | Target | P&L |
|---|---|---|---|---|---|---|
| EURGBP | SELL | 3.34 | 0.8387300000000001 | 0.83961 | 0.8376 | $255.28 |

## Closed paper trades (latest 20)

| Closed | Symbol | Side | Net | R | Costs | Exit | Source | Rule |
|---|---|---|---|---|---|---|---|---|
| 10-22 08:28 | AUDUSD | SELL | $-494.07 | -0.99 | $82.84 | STOP | DUAL_AI | AGREE |
| 10-22 05:34 | GBPJPY | SELL | $724.37 | +1.46 | $84.17 | TARGET | DUAL_AI | AGREE |
| 10-22 05:30 | USDCAD | BUY | $-395.16 | -0.79 | $92.71 | STOP | DUAL_AI | AGREE |
| 10-22 03:06 | EURGBP | SELL | $-430.18 | -0.86 | $79.35 | STOP | DUAL_AI | AGREE |
| 10-22 03:14 | USDCHF | SELL | $561.26 | +1.13 | $100.15 | TARGET | DUAL_AI | AGREE |
| 10-22 02:18 | AUDJPY | BUY | $-412.63 | -0.83 | $83.30 | STOP | DUAL_AI | AGREE |
| 10-22 01:54 | AUDUSD | BUY | $-506.27 | -1.01 | $123.62 | STOP | DUAL_AI | AGREE |
| 10-21 21:05 | GBPJPY | BUY | $-644.82 | -1.29 | $149.96 | STOP | DUAL_AI | AGREE |
| 10-21 16:42 | NZDUSD | BUY | $119.66 | +0.97 | $20.93 | TARGET | DUAL_AI | AGREE |
| 10-21 09:01 | EURJPY | BUY | $-388.21 | -0.78 | $94.39 | STOP | DUAL_AI | AGREE |
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

## Dual AI desk (two free OpenRouter traders; a trade only when they agree)

OpenRouter `READY` · key set · trader 1 `minimax/minimax-m3.1-flash:free` · trader 2 `nvidia/nemotron-3.5-super-vl:free` · debate `thinkingmachines/inkling-small:free` · calls today 34/900

Agreement trades 80 (adequate) · wins 35 · losses 45 · net $-1,271.48 · expectancy -0.058R · profit factor 0.91 · old DEBATE rule (stopped in dual-ai-1.2.0): 4 trade(s), net $-1,416.51, removed from the account

Disagreements (not traded; the debate runs in shadow): 95 · the debate's pick if taken: 89 resolved (adequate), expectancy -0.221R · the side it rejected if taken: 94 resolved (adequate), expectancy -0.227R

Exits in shadow (the same trades, followed again; measured, never traded): break-even at +1R -0.092R vs +0.002R as taken (59, adequate) · held 24 h +0.169R vs +0.002R as taken (59, adequate) · stop and target twice as far +0.070R vs +0.002R as taken (59, adequate) · closed at 8 h (the exit before dual-ai 1.7.0) -0.021R vs -0.136R as taken (5, insufficient)

Trades taken by session (UTC): ASIA 34 resolved (adequate), expectancy -0.003R · LONDON 19 resolved (insufficient), expectancy +0.043R · OVERLAP 8 resolved (insufficient), expectancy -0.382R · NEW_YORK 12 resolved (insufficient), expectancy +0.257R · LATE 3 resolved (insufficient), expectancy -1.106R

| Time | Symbol | Trader 1 | Trader 2 | Debate (shadow) | Rule | Final | Risk |
|---|---|---|---|---|---|---|---|
| 10-22 08:32 | EURGBP | -  | -  | - | NOT_ASKED | NO_TRADE | - |
| 10-22 08:30 | NZDUSD | BUY 66 | BUY 66 | - | AGREE | BUY | REJECTED |
| 10-22 08:16 | USDCHF | SELL 67 | SELL 66 | - | AGREE | SELL | REJECTED |
| 10-22 08:15 | USDCAD | SELL 68 | SELL 67 | - | AGREE | SELL | REJECTED |
| 10-22 08:01 | AUDUSD | -  | -  | - | NOT_ASKED | NO_TRADE | - |
| 10-22 08:00 | USDJPY | SELL 68 | SELL 68 | - | AGREE | SELL | REJECTED |
| 10-22 07:48 | GBPUSD | SELL 59 | SELL 57 | - | AGREE | SELL | REJECTED |
| 10-22 07:45 | EURUSD | BUY 58 | BUY 58 | - | AGREE | BUY | REJECTED |
| 10-22 07:31 | AUDJPY | SELL 62 | SELL 62 | - | AGREE | SELL | REJECTED |
| 10-22 07:30 | EURCHF | SELL 68 | SELL 63 | - | AGREE | SELL | REJECTED |
| 10-22 07:18 | GBPJPY | SELL 68 | SELL 66 | - | AGREE | SELL | REJECTED |
| 10-22 07:15 | EURJPY | SELL 74 | SELL 68 | - | AGREE | SELL | REJECTED |

The chart Trader 1 read last: `last_chart.png`. (numbers): no free vision model answered, so Trader 1 read the same chart from its numbers.

Full figures: `paper_forward.json`. Rules: `docs/PAPER_FORWARD.md` on main.
