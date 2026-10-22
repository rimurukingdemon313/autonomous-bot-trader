# PAPER FORWARD TEST — NOT REAL MONEY

Updated 2026-10-22 15:57 UTC · mode `PAPER_FORWARD` · profile `PAPER-FORWARD-200K` · shift started 2026-10-22 11:41 UTC · decision system `dual_ai`

Research status (historical, unchanged): **NO EDGE — DO NOT TRADE (historical research; this test measures forward)**. This run measures the system forward; it is not evidence of an edge until it has a sample and the forward-eligibility rules say so.

## The rule that trades: a trade only when both AIs agree

| Trades | Wins | Losses | Win rate | Net P&L | Expectancy | Profit factor | Max drawdown |
|---|---|---|---|---|---|---|---|
| 85 (adequate) | 39 | 46 | 45.9% | $508.34 | -0.012R | 1.03 | $4,943.76 |

The 4 trade(s) of the old DEBATE rule, stopped in dual-ai-1.2.0, were removed from the paper account at the operator's request: their net $-1,416.51 was put back by a declared adjustment ($1,416.51). They stay in the journal (append-only), in none of the account's figures below.

## Paper account

| Account | Equity | P&L today | Total P&L | Drawdown | Open | Trades | Win rate | Expectancy | Profit factor | Risk | Bot |
|---|---|---|---|---|---|---|---|---|---|---|---|
| $200,000.00 | $200,257.24 | $399.03 | $257.24 | $0.00 | 1 | 85 (adequate) | 45.9% | -0.012R | 1.03 | ACTIVE | RUNNING |

Equity includes declared operator adjustments of $1,416.51 (without them: $198,840.73); P&L today excludes them. `remove-retired-debate-rule-trades-2026-10-15`: operator: the 4 trades of the retired debate rule (dual-ai 1.1.0, stopped in 1.2.0) are removed from the paper account; they stay in the journal.

## Last decisions (decision → risk → paper execution)

- 10-22 11:46 GBPUSD SELL: AI DECISION → RISK APPROVED → PAPER EXECUTED
- 10-22 11:45 EURUSD SELL: AI DECISION → RISK REJECTED — reward_risk: 1.11 vs minimum 1.2
- 10-22 11:32 EURGBP SELL: AI DECISION → RISK REJECTED — reward_risk: 1.08 vs minimum 1.2
- 10-22 11:30 NZDUSD SELL: AI DECISION → RISK REJECTED — spread: spread is 26.1% of the stop (max 25%); cost_to_risk: round-trip cost is 41.7% of the stop (max 25%): spread 0.00015 + commission and slippage
- 10-22 11:17 USDCHF SELL: AI DECISION → RISK REJECTED — reward_risk: 0.85 vs minimum 1.2; currency_conflict: SELL USDCHF would bet against an open position: USDCAD BUY is long USD
- 10-22 11:15 USDCAD BUY: AI DECISION → RISK APPROVED → PAPER EXECUTED
- 10-22 10:18 GBPJPY SELL: AI DECISION → RISK APPROVED → PAPER EXECUTED
- 10-22 10:15 EURJPY SELL: AI DECISION → RISK REJECTED — reward_risk: 1.04 vs minimum 1.2; structure: H1 structure is range (mixed swings): no new position without a clear H1 trend (up HH+HL or down LH+LL)
- 10-22 09:45 USDCAD SELL: AI DECISION → RISK REJECTED — reward_risk: 0.95 vs minimum 1.2; currency_conflict: SELL USDCAD would bet against an open position: EURUSD SELL is long USD; structure: H1 structure is range (mixed swings): no new position without a
- 10-22 09:15 EURUSD SELL: AI DECISION → RISK APPROVED → PAPER EXECUTED
- 10-22 09:03 AUDJPY SELL: AI DECISION → RISK APPROVED → PAPER EXECUTED
- 10-22 09:00 EURCHF SELL: AI DECISION → RISK REJECTED — reward_risk: 0.88 vs minimum 1.2; structure: H1 structure is range (mixed swings): no new position without a clear H1 trend (up HH+HL or down LH+LL)
- 10-22 08:48 GBPJPY SELL: AI DECISION → RISK REJECTED — reward_risk: 1.08 vs minimum 1.2; currency_conflict: SELL GBPJPY would bet against an open position: EURGBP SELL is long GBP
- 10-22 08:30 NZDUSD BUY: AI DECISION → RISK REJECTED — structure: H1 structure is range (mixed swings): no new position without a clear H1 trend (up HH+HL or down LH+LL)
- 10-22 08:16 USDCHF SELL: AI DECISION → RISK REJECTED — currency_conflict: SELL USDCHF would bet against an open position: AUDUSD SELL is long USD
- 10-22 08:15 USDCAD SELL: AI DECISION → RISK REJECTED — currency_conflict: SELL USDCAD would bet against an open position: AUDUSD SELL is long USD; structure: H1 structure is range (mixed swings): no new position without a clear H1 trend (up HH+HL or down 
- 10-22 08:00 USDJPY SELL: AI DECISION → RISK REJECTED — currency_conflict: SELL USDJPY would bet against an open position: AUDUSD SELL is long USD; structure: H1 structure is range (mixed swings): no new position without a clear H1 trend (up HH+HL or down 
- 10-22 07:48 GBPUSD SELL: AI DECISION → RISK REJECTED — reward_risk: 1.06 vs minimum 1.2; currency_conflict: SELL GBPUSD would bet against an open position: EURGBP SELL is long GBP
- 10-22 07:45 EURUSD BUY: AI DECISION → RISK REJECTED — reward_risk: 1.08 vs minimum 1.2; currency_conflict: BUY EURUSD would bet against an open position: AUDUSD SELL is long USD; EURGBP SELL is short EUR
- 10-22 07:31 AUDJPY SELL: AI DECISION → RISK REJECTED — reward_risk: 1.19 vs minimum 1.2

## Latest decisions, NO TRADE included (2085 so far)

- 10-22 15:45 GBPJPY NO_TRADE: risk engine: trading_calendar (Thursday 15:45 UTC: no new position from 12:00 to 16:00 UTC): the model was not consulted
- 10-22 15:45 EURJPY NO_TRADE: risk engine: trading_calendar (Thursday 15:45 UTC: no new position from 12:00 to 16:00 UTC): the model was not consulted
- 10-22 15:30 EURGBP NO_TRADE: risk engine: trading_calendar (Thursday 15:30 UTC: no new position from 12:00 to 16:00 UTC): the model was not consulted
- 10-22 15:30 NZDUSD NO_TRADE: risk engine: trading_calendar (Thursday 15:30 UTC: no new position from 12:00 to 16:00 UTC): the model was not consulted
- 10-22 15:15 USDCHF NO_TRADE: risk engine: trading_calendar (Thursday 15:15 UTC: no new position from 12:00 to 16:00 UTC): the model was not consulted
- 10-22 15:15 USDCAD NO_TRADE: risk engine: trading_calendar (Thursday 15:15 UTC: no new position from 12:00 to 16:00 UTC): the model was not consulted
- 10-22 15:00 AUDUSD NO_TRADE: risk engine: trading_calendar (Thursday 15:00 UTC: no new position from 12:00 to 16:00 UTC): the model was not consulted
- 10-22 15:00 USDJPY NO_TRADE: risk engine: trading_calendar (Thursday 15:00 UTC: no new position from 12:00 to 16:00 UTC): the model was not consulted
- 10-22 14:45 GBPUSD NO_TRADE: blocked before consulting the model: EXPOSURE: a GBPUSD position is already open
- 10-22 14:45 EURUSD NO_TRADE: risk engine: trading_calendar (Thursday 14:45 UTC: no new position from 12:00 to 16:00 UTC): the model was not consulted
- 10-22 14:30 AUDJPY NO_TRADE: risk engine: trading_calendar (Thursday 14:30 UTC: no new position from 12:00 to 16:00 UTC): the model was not consulted
- 10-22 14:30 EURCHF NO_TRADE: risk engine: trading_calendar (Thursday 14:30 UTC: no new position from 12:00 to 16:00 UTC): the model was not consulted

## Open paper positions

| Symbol | Side | Qty | Entry | Stop | Target | P&L |
|---|---|---|---|---|---|---|
| GBPUSD | SELL | 2.7 | 1.33693 | 1.33845 | 1.33447 | $-251.10 |

## Closed paper trades (latest 20)

| Closed | Symbol | Side | Net | R | Costs | Exit | Source | Rule |
|---|---|---|---|---|---|---|---|---|
| 10-22 14:07 | USDCAD | BUY | $-438.56 | -0.88 | $54.88 | STOP | DUAL_AI | AGREE |
| 10-22 11:06 | GBPJPY | SELL | $631.22 | +1.27 | $57.92 | TARGET | DUAL_AI | AGREE |
| 10-22 11:02 | AUDJPY | SELL | $574.01 | +1.16 | $75.68 | TARGET | DUAL_AI | AGREE |
| 10-22 10:56 | EURUSD | SELL | $530.48 | +1.07 | $55.84 | TARGET | DUAL_AI | AGREE |
| 10-22 09:41 | EURGBP | SELL | $482.66 | +0.97 | $81.60 | TARGET | DUAL_AI | AGREE |
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

## Dual AI desk (two free OpenRouter traders; a trade only when they agree)

OpenRouter `READY` · key set · trader 1 `minimax/minimax-m3.1-flash:free` · trader 2 `nvidia/nemotron-3.5-super-vl:free` · debate `thinkingmachines/inkling-small:free` · calls today 9/900

Agreement trades 85 (adequate) · wins 39 · losses 46 · net $508.34 · expectancy -0.012R · profit factor 1.03 · old DEBATE rule (stopped in dual-ai-1.2.0): 4 trade(s), net $-1,416.51, removed from the account

Disagreements (not traded; the debate runs in shadow): 97 · the debate's pick if taken: 89 resolved (adequate), expectancy -0.221R · the side it rejected if taken: 94 resolved (adequate), expectancy -0.227R

Exits in shadow (the same trades, followed again; measured, never traded): break-even at +1R -0.109R vs -0.016R as taken (60, adequate) · held 24 h +0.149R vs -0.016R as taken (60, adequate) · stop and target twice as far +0.051R vs -0.016R as taken (60, adequate) · closed at 8 h (the exit before dual-ai 1.7.0) -0.199R vs -0.294R as taken (6, insufficient)

Trades taken by session (UTC): ASIA 34 resolved (adequate), expectancy -0.003R · LONDON 20 resolved (insufficient), expectancy -0.013R · OVERLAP 8 resolved (insufficient), expectancy -0.382R · NEW_YORK 12 resolved (insufficient), expectancy +0.257R · LATE 3 resolved (insufficient), expectancy -1.106R

| Time | Symbol | Trader 1 | Trader 2 | Debate (shadow) | Rule | Final | Risk |
|---|---|---|---|---|---|---|---|
| 10-22 15:45 | GBPJPY | -  | -  | - | NOT_ASKED | NO_TRADE | - |
| 10-22 15:45 | EURJPY | -  | -  | - | NOT_ASKED | NO_TRADE | - |
| 10-22 15:30 | EURGBP | -  | -  | - | NOT_ASKED | NO_TRADE | - |
| 10-22 15:30 | NZDUSD | -  | -  | - | NOT_ASKED | NO_TRADE | - |
| 10-22 15:15 | USDCHF | -  | -  | - | NOT_ASKED | NO_TRADE | - |
| 10-22 15:15 | USDCAD | -  | -  | - | NOT_ASKED | NO_TRADE | - |
| 10-22 15:00 | AUDUSD | -  | -  | - | NOT_ASKED | NO_TRADE | - |
| 10-22 15:00 | USDJPY | -  | -  | - | NOT_ASKED | NO_TRADE | - |
| 10-22 14:45 | GBPUSD | -  | -  | - | NOT_ASKED | NO_TRADE | - |
| 10-22 14:45 | EURUSD | -  | -  | - | NOT_ASKED | NO_TRADE | - |
| 10-22 14:30 | AUDJPY | -  | -  | - | NOT_ASKED | NO_TRADE | - |
| 10-22 14:30 | EURCHF | -  | -  | - | NOT_ASKED | NO_TRADE | - |

The chart Trader 1 read last: `last_chart.png`. (numbers): no free vision model answered, so Trader 1 read the same chart from its numbers.

Full figures: `paper_forward.json`. Rules: `docs/PAPER_FORWARD.md` on main.
