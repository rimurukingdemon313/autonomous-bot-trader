# PAPER FORWARD TEST — NOT REAL MONEY

Updated 2026-10-22 05:00 UTC · mode `PAPER_FORWARD` · profile `PAPER-FORWARD-200K` · shift started 2026-10-22 00:30 UTC · decision system `dual_ai`

Research status (historical, unchanged): **NO EDGE — DO NOT TRADE (historical research; this test measures forward)**. This run measures the system forward; it is not evidence of an edge until it has a sample and the forward-eligibility rules say so.

## The rule that trades: a trade only when both AIs agree

| Trades | Wins | Losses | Win rate | Net P&L | Expectancy | Profit factor | Max drawdown |
|---|---|---|---|---|---|---|---|
| 77 (adequate) | 34 | 43 | 44.2% | $-1,106.61 | -0.055R | 0.92 | $4,943.76 |

The 4 trade(s) of the old DEBATE rule, stopped in dual-ai-1.2.0, were removed from the paper account at the operator's request: their net $-1,416.51 was put back by a declared adjustment ($1,416.51). They stay in the journal (append-only), in none of the account's figures below.

## Paper account

| Account | Equity | P&L today | Total P&L | Drawdown | Open | Trades | Win rate | Expectancy | Profit factor | Risk | Bot |
|---|---|---|---|---|---|---|---|---|---|---|---|
| $200,000.00 | $198,866.94 | $-991.28 | $-1,133.06 | $-1,133.06 | 3 | 77 (adequate) | 44.2% | -0.055R | 0.92 | ACTIVE | RUNNING |

Equity includes declared operator adjustments of $1,416.51 (without them: $197,450.42); P&L today excludes them. `remove-retired-debate-rule-trades-2026-10-15`: operator: the 4 trades of the retired debate rule (dual-ai 1.1.0, stopped in 1.2.0) are removed from the paper account; they stay in the journal.

## Last decisions (decision → risk → paper execution)

- 10-22 04:15 USDCAD BUY: AI DECISION → RISK APPROVED → PAPER EXECUTED
- 10-22 04:02 AUDUSD SELL: AI DECISION → RISK APPROVED → PAPER EXECUTED
- 10-22 03:47 GBPUSD BUY: AI DECISION → RISK REJECTED — currency_conflict: BUY GBPUSD would bet against an open position: GBPJPY SELL is short GBP
- 10-22 03:45 EURUSD BUY: AI DECISION → RISK REJECTED — structure: H1 structure is range (mixed swings): no new position without a clear H1 trend (up HH+HL or down LH+LL)
- 10-22 03:30 EURCHF SELL: AI DECISION → RISK REJECTED — structure: H1 structure is range (mixed swings): no new position without a clear H1 trend (up HH+HL or down LH+LL)
- 10-22 03:19 GBPJPY SELL: AI DECISION → RISK APPROVED → PAPER EXECUTED
- 10-22 03:15 EURJPY SELL: AI DECISION → RISK REJECTED — structure: H1 structure is range (mixed swings): no new position without a clear H1 trend (up HH+HL or down LH+LL)
- 10-22 03:00 NZDUSD BUY: AI DECISION → RISK REJECTED — structure: H1 structure is range (mixed swings): no new position without a clear H1 trend (up HH+HL or down LH+LL)
- 10-22 02:45 USDCAD BUY: AI DECISION → RISK REJECTED — currency_conflict: BUY USDCAD would bet against an open position: USDCHF SELL is short USD
- 10-22 02:31 AUDUSD SELL: AI DECISION → RISK REJECTED — reward_risk: 1.00 vs minimum 1.2; currency_conflict: SELL AUDUSD would bet against an open position: USDCHF SELL is short USD; structure: H1 structure is range (mixed swings): no new position without 
- 10-22 02:30 USDJPY SELL: AI DECISION → RISK REJECTED — reward_risk: 1.15 vs minimum 1.2
- 10-22 02:01 AUDJPY BUY: AI DECISION → RISK APPROVED → PAPER EXECUTED
- 10-22 02:00 EURCHF BUY: AI DECISION → RISK REJECTED — currency_conflict: BUY EURCHF would bet against an open position: USDCHF SELL is long CHF; EURGBP SELL is short EUR; structure: H1 structure is range (mixed swings): no new position without a clear H1
- 10-22 00:15 EURGBP SELL: AI DECISION → RISK APPROVED → PAPER EXECUTED
- 10-21 17:05 USDCHF SELL: AI DECISION → RISK APPROVED → PAPER EXECUTED
- 10-21 17:00 USDCAD SELL: AI DECISION → RISK REJECTED — cost_to_risk: round-trip cost is 31.0% of the stop (max 25%): spread 0.00015 + commission and slippage; structure: H1 structure is range (mixed swings): no new position without a clear H1 trend (up HH
- 10-21 16:09 GBPJPY BUY: AI DECISION → RISK APPROVED → PAPER EXECUTED
- 10-21 11:50 GBPJPY SELL: AI DECISION → RISK REJECTED — structure: H1 structure is range (mixed swings): no new position without a clear H1 trend (up HH+HL or down LH+LL)
- 10-21 11:30 EURGBP SELL: AI DECISION → RISK REJECTED — reward_risk: 1.08 vs minimum 1.2; structure: H1 structure is range (mixed swings): no new position without a clear H1 trend (up HH+HL or down LH+LL)
- 10-21 10:32 AUDJPY BUY: AI DECISION → RISK REJECTED — reward_risk: 1.03 vs minimum 1.2

## Latest decisions, NO TRADE included (2000 so far)

- 10-22 05:00 AUDJPY NO_TRADE: risk engine: open_positions (3 open, max 3); gate_open_risk (the hard risk gate's open-risk room 251.39 is less than the next trade's risk 497.12: it would refuse the trade): the model was not consult
- 10-22 05:00 EURCHF NO_TRADE: risk engine: open_positions (3 open, max 3); gate_open_risk (the hard risk gate's open-risk room 251.39 is less than the next trade's risk 497.12: it would refuse the trade): the model was not consult
- 10-22 04:45 GBPJPY NO_TRADE: blocked before consulting the model: EXPOSURE: a GBPJPY position is already open
- 10-22 04:45 EURJPY NO_TRADE: risk engine: open_positions (3 open, max 3); gate_open_risk (the hard risk gate's open-risk room 244.58 is less than the next trade's risk 497.36: it would refuse the trade): the model was not consult
- 10-22 04:30 EURGBP NO_TRADE: risk engine: open_positions (3 open, max 3); gate_open_risk (the hard risk gate's open-risk room 237.78 is less than the next trade's risk 497.37: it would refuse the trade): the model was not consult
- 10-22 04:30 NZDUSD NO_TRADE: risk engine: open_positions (3 open, max 3); currency_exposure (2 open positions share a currency, max 2); gate_open_risk (the hard risk gate's open-risk room 237.78 is less than the next trade's risk
- 10-22 04:16 USDCHF NO_TRADE: risk engine: open_positions (3 open, max 3); currency_exposure (2 open positions share a currency, max 2); gate_open_risk (the hard risk gate's open-risk room 169.74 is less than the next trade's risk
- 10-22 04:15 USDCAD BUY: BUY USDCAD on M15: AGREE: Trader 1 (minimax/minimax-m3.1-flash:free) BUY 58: Buy after the downside sweep and reclaim of 1.40345, targeting the untested supply zone at 1.40483. The 1.40260 low invalid
- 10-22 04:02 AUDUSD SELL: SELL AUDUSD on M15: AGREE: Trader 1 (minimax/minimax-m3.1-flash:free) SELL 64: The bearish M15 structure break below 0.70161 favors continuation after the prior-week high was taken as liquidity. A sto
- 10-22 04:00 USDJPY NO_TRADE: the traders disagree (Trader 1 SELL 68, Trader 2 BUY 60): no trade unless both choose the same side; the debate (nvidia/nemotron-3-ultra-550b-a55b:free) would have chosen SELL: followed forward in sha
- 10-22 03:47 GBPUSD BUY: BUY GBPUSD on M15: AGREE: Trader 1 (minimax/minimax-m3.1-flash:free) BUY 64: Buy the pullback into the open bullish FVG after the confirmed sweep and bullish M15 CHOCH. The stop sits below the 1.33905
- 10-22 03:45 EURUSD BUY: BUY EURUSD on M15: AGREE: Trader 1 (minimax/minimax-m3.1-flash:free) BUY 63: Buy the controlled pullback because consecutive bullish structure breaks and H4 acceptance above 1.12435 favor continuation

## Open paper positions

| Symbol | Side | Qty | Entry | Stop | Target | P&L |
|---|---|---|---|---|---|---|
| USDCAD | BUY | 4.85 | 1.403585 | 1.40255 | 1.40483 | $-89.86 |
| AUDUSD | SELL | 4.36 | 0.70154 | 0.7024 | 0.70018 | $-222.36 |
| GBPJPY | SELL | 3.6 | 211.4325 | 211.6 | 211.102 | $285.77 |

## Closed paper trades (latest 20)

| Closed | Symbol | Side | Net | R | Costs | Exit | Source | Rule |
|---|---|---|---|---|---|---|---|---|
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
| 10-20 12:42 | GBPJPY | BUY | $734.40 | +1.47 | $88.38 | TARGET | DUAL_AI | AGREE |
| 10-20 12:25 | USDCHF | SELL | $523.45 | +1.05 | $85.16 | TARGET | DUAL_AI | AGREE |
| 10-20 11:14 | USDCHF | SELL | $503.61 | +1.01 | $81.37 | TARGET | DUAL_AI | AGREE |

## Dual AI desk (two free OpenRouter traders; a trade only when they agree)

OpenRouter `READY` · key set · trader 1 `minimax/minimax-m3.1-flash:free` · trader 2 `nvidia/nemotron-3.5-super-vl:free` · debate `nvidia/nemotron-3-ultra-550b-a55b:free` · calls today 43/900

Agreement trades 77 (adequate) · wins 34 · losses 43 · net $-1,106.61 · expectancy -0.055R · profit factor 0.92 · old DEBATE rule (stopped in dual-ai-1.2.0): 4 trade(s), net $-1,416.51, removed from the account

Disagreements (not traded; the debate runs in shadow): 95 · the debate's pick if taken: 86 resolved (adequate), expectancy -0.191R · the side it rejected if taken: 91 resolved (adequate), expectancy -0.253R

Exits in shadow (the same trades, followed again; measured, never traded): break-even at +1R -0.080R vs +0.019R as taken (56, adequate) · held 24 h +0.195R vs +0.019R as taken (56, adequate) · stop and target twice as far +0.098R vs +0.019R as taken (56, adequate) · closed at 8 h (the exit before dual-ai 1.7.0) +0.132R vs +0.132R as taken (2, insufficient)

Trades taken by session (UTC): ASIA 33 resolved (adequate), expectancy +0.028R · LONDON 17 resolved (insufficient), expectancy +0.042R · OVERLAP 8 resolved (insufficient), expectancy -0.382R · NEW_YORK 12 resolved (insufficient), expectancy +0.257R · LATE 3 resolved (insufficient), expectancy -1.106R

| Time | Symbol | Trader 1 | Trader 2 | Debate (shadow) | Rule | Final | Risk |
|---|---|---|---|---|---|---|---|
| 10-22 05:00 | AUDJPY | -  | -  | - | NOT_ASKED | NO_TRADE | - |
| 10-22 05:00 | EURCHF | -  | -  | - | NOT_ASKED | NO_TRADE | - |
| 10-22 04:45 | GBPJPY | -  | -  | - | NOT_ASKED | NO_TRADE | - |
| 10-22 04:45 | EURJPY | -  | -  | - | NOT_ASKED | NO_TRADE | - |
| 10-22 04:30 | EURGBP | -  | -  | - | NOT_ASKED | NO_TRADE | - |
| 10-22 04:30 | NZDUSD | -  | -  | - | NOT_ASKED | NO_TRADE | - |
| 10-22 04:16 | USDCHF | -  | -  | - | NOT_ASKED | NO_TRADE | - |
| 10-22 04:15 | USDCAD | BUY 58 | BUY 55 | - | AGREE | BUY | APPROVED |
| 10-22 04:02 | AUDUSD | SELL 64 | SELL 60 | - | AGREE | SELL | APPROVED |
| 10-22 04:00 | USDJPY | SELL 68 | BUY 60 | SELL | DISAGREE | NO_TRADE | - |
| 10-22 03:47 | GBPUSD | BUY 64 | BUY 64 | - | AGREE | BUY | REJECTED |
| 10-22 03:45 | EURUSD | BUY 63 | BUY 58 | - | AGREE | BUY | REJECTED |

The chart Trader 1 read last: `last_chart.png`. (numbers): no free vision model answered, so Trader 1 read the same chart from its numbers.

Full figures: `paper_forward.json`. Rules: `docs/PAPER_FORWARD.md` on main.
