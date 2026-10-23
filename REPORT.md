# PAPER FORWARD TEST — NOT REAL MONEY

Updated 2026-10-23 01:38 UTC · mode `PAPER_FORWARD` · profile `PAPER-FORWARD-200K` · shift started 2026-10-22 22:52 UTC · decision system `dual_ai`

Research status (historical, unchanged): **NO EDGE — DO NOT TRADE (historical research; this test measures forward)**. This run measures the system forward; it is not evidence of an edge until it has a sample and the forward-eligibility rules say so.

## The rule that trades: a trade only when both AIs agree

| Trades | Wins | Losses | Win rate | Net P&L | Expectancy | Profit factor | Max drawdown |
|---|---|---|---|---|---|---|---|
| 89 (adequate) | 40 | 49 | 44.9% | $-126.94 | -0.020R | 0.99 | $4,943.76 |

The 4 trade(s) of the old DEBATE rule, stopped in dual-ai-1.2.0, were removed from the paper account at the operator's request: their net $-1,416.51 was put back by a declared adjustment ($1,416.51). They stay in the journal (append-only), in none of the account's figures below.

## Paper account

| Account | Equity | P&L today | Total P&L | Drawdown | Open | Trades | Win rate | Expectancy | Profit factor | Risk | Bot |
|---|---|---|---|---|---|---|---|---|---|---|---|
| $200,000.00 | $198,912.94 | $-757.32 | $-1,087.06 | $-1,087.06 | 3 | 89 (adequate) | 44.9% | -0.020R | 0.99 | ACTIVE | RUNNING |

Equity includes declared operator adjustments of $1,416.51 (without them: $197,496.43); P&L today excludes them. `remove-retired-debate-rule-trades-2026-10-15`: operator: the 4 trades of the retired debate rule (dual-ai 1.1.0, stopped in 1.2.0) are removed from the paper account; they stay in the journal.

## Last decisions (decision → risk → paper execution)

- 10-23 00:16 AUDJPY SELL: AI DECISION → RISK APPROVED → PAPER EXECUTED
- 10-23 00:15 EURCHF SELL: AI DECISION → RISK APPROVED → PAPER EXECUTED
- 10-23 00:08 GBPJPY SELL: AI DECISION → RISK APPROVED → PAPER EXECUTED
- 10-23 00:00 EURJPY SELL: AI DECISION → RISK REJECTED — reward_risk: 0.00 vs minimum 1.2; structure: H1 structure is range (mixed swings): no new position without a clear H1 trend (up HH+HL or down LH+LL)
- 10-22 18:41 USDCHF SELL: AI DECISION → RISK REJECTED — cost_to_risk: round-trip cost is 27.1% of the stop (max 25%): spread 0.00015 + commission and slippage
- 10-22 18:30 USDCAD BUY: AI DECISION → RISK REJECTED — currency_conflict: BUY USDCAD would bet against an open position: USDJPY SELL is short USD
- 10-22 18:11 AUDUSD BUY: AI DECISION → RISK REJECTED — reward_risk: 1.00 vs minimum 1.2; structure: H1 structure is range (mixed swings): no new position without a clear H1 trend (up HH+HL or down LH+LL)
- 10-22 18:00 USDJPY SELL: AI DECISION → RISK APPROVED → PAPER EXECUTED
- 10-22 17:43 GBPUSD BUY: AI DECISION → RISK REJECTED — reward_risk: 0.97 vs minimum 1.2; structure: H1 structure is range (mixed swings): no new position without a clear H1 trend (up HH+HL or down LH+LL)
- 10-22 17:00 USDJPY SELL: AI DECISION → RISK APPROVED → PAPER EXECUTED
- 10-22 16:00 EURCHF BUY: AI DECISION → RISK APPROVED → PAPER EXECUTED
- 10-22 11:46 GBPUSD SELL: AI DECISION → RISK APPROVED → PAPER EXECUTED
- 10-22 11:45 EURUSD SELL: AI DECISION → RISK REJECTED — reward_risk: 1.11 vs minimum 1.2
- 10-22 11:32 EURGBP SELL: AI DECISION → RISK REJECTED — reward_risk: 1.08 vs minimum 1.2
- 10-22 11:30 NZDUSD SELL: AI DECISION → RISK REJECTED — spread: spread is 26.1% of the stop (max 25%); cost_to_risk: round-trip cost is 41.7% of the stop (max 25%): spread 0.00015 + commission and slippage
- 10-22 11:17 USDCHF SELL: AI DECISION → RISK REJECTED — reward_risk: 0.85 vs minimum 1.2; currency_conflict: SELL USDCHF would bet against an open position: USDCAD BUY is long USD
- 10-22 11:15 USDCAD BUY: AI DECISION → RISK APPROVED → PAPER EXECUTED
- 10-22 10:18 GBPJPY SELL: AI DECISION → RISK APPROVED → PAPER EXECUTED
- 10-22 10:15 EURJPY SELL: AI DECISION → RISK REJECTED — reward_risk: 1.04 vs minimum 1.2; structure: H1 structure is range (mixed swings): no new position without a clear H1 trend (up HH+HL or down LH+LL)
- 10-22 09:45 USDCAD SELL: AI DECISION → RISK REJECTED — reward_risk: 0.95 vs minimum 1.2; currency_conflict: SELL USDCAD would bet against an open position: EURUSD SELL is long USD; structure: H1 structure is range (mixed swings): no new position without a

## Latest decisions, NO TRADE included (2144 so far)

- 10-23 01:30 GBPJPY NO_TRADE: blocked before consulting the model: EXPOSURE: a GBPJPY position is already open
- 10-23 01:30 EURJPY NO_TRADE: risk engine: open_positions (3 open, max 3); currency_exposure (2 open positions share a currency, max 2): the model was not consulted
- 10-23 01:15 EURGBP NO_TRADE: risk engine: open_positions (3 open, max 3): the model was not consulted
- 10-23 01:15 NZDUSD NO_TRADE: risk engine: open_positions (3 open, max 3): the model was not consulted
- 10-23 01:00 USDCHF NO_TRADE: risk engine: open_positions (3 open, max 3): the model was not consulted
- 10-23 01:00 USDCAD NO_TRADE: risk engine: open_positions (3 open, max 3): the model was not consulted
- 10-23 00:45 AUDUSD NO_TRADE: risk engine: open_positions (3 open, max 3); gate_open_risk (the hard risk gate's open-risk room 444.55 is less than the next trade's risk 499.45: it would refuse the trade): the model was not consult
- 10-23 00:45 USDJPY NO_TRADE: risk engine: open_positions (3 open, max 3); currency_exposure (2 open positions share a currency, max 2); gate_open_risk (the hard risk gate's open-risk room 444.55 is less than the next trade's risk
- 10-23 00:30 GBPUSD NO_TRADE: risk engine: open_positions (3 open, max 3); gate_open_risk (the hard risk gate's open-risk room 402.80 is less than the next trade's risk 499.80: it would refuse the trade): the model was not consult
- 10-23 00:30 EURUSD NO_TRADE: risk engine: open_positions (3 open, max 3); gate_open_risk (the hard risk gate's open-risk room 402.80 is less than the next trade's risk 499.80: it would refuse the trade): the model was not consult
- 10-23 00:16 AUDJPY SELL: SELL AUDJPY on M15: AGREE: Trader 1 (nvidia/nemotron-3.5-super-vl:free) SELL 65: M15 structure is bearish with a fresh bearish BOS at 109.809 and an LH/LL sequence; price sits below the untested suppl
- 10-23 00:15 EURCHF SELL: SELL EURCHF on M15: AGREE: Trader 1 (nvidia/nemotron-3.5-super-vl:free) SELL 68: Both M15 and H4 show bearish LH+LL structure with a fresh bearish BOS at 0.91981. Price is inside the untested supply o

## Open paper positions

| Symbol | Side | Qty | Entry | Stop | Target | P&L |
|---|---|---|---|---|---|---|
| AUDJPY | SELL | 2.3 | 109.607 | 109.888 | 109.1 | n/a |
| EURCHF | SELL | 2.61 | 0.9197 | 0.9209 | 0.91805 | $-219.57 |
| GBPJPY | SELL | 1.06 | 209.4575 | 210.12 | 208.36 | $-309.35 |

## Closed paper trades (latest 20)

| Closed | Symbol | Side | Net | R | Costs | Exit | Source | Rule |
|---|---|---|---|---|---|---|---|---|
| 10-22 22:40 | USDJPY | SELL | $428.74 | +1.73 | $51.43 | TARGET | DUAL_AI | AGREE |
| 10-22 17:32 | USDJPY | SELL | $-198.17 | -0.79 | $25.98 | STOP | DUAL_AI | AGREE |
| 10-22 16:52 | EURCHF | BUY | $-430.76 | -0.86 | $62.40 | STOP | DUAL_AI | AGREE |
| 10-22 16:05 | GBPUSD | SELL | $-435.09 | -0.87 | $56.70 | STOP | DUAL_AI | AGREE |
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

## Dual AI desk (two free OpenRouter traders; a trade only when they agree)

OpenRouter `READY` · key set · trader 1 `nvidia/nemotron-3.5-super-vl:free` · trader 2 `dots-studio/dots-3-note-preview:free` · debate `xingchen-agi/xing4.0-29b-a4b:free` · calls today 16/900

Agreement trades 89 (adequate) · wins 40 · losses 49 · net $-126.94 · expectancy -0.020R · profit factor 0.99 · old DEBATE rule (stopped in dual-ai-1.2.0): 4 trade(s), net $-1,416.51, removed from the account

Disagreements (not traded; the debate runs in shadow): 101 · the debate's pick if taken: 91 resolved (adequate), expectancy -0.210R · the side it rejected if taken: 96 resolved (adequate), expectancy -0.220R

Exits in shadow (the same trades, followed again; measured, never traded): break-even at +1R -0.099R vs -0.027R as taken (63, adequate) · held 24 h +0.130R vs -0.027R as taken (63, adequate) · stop and target twice as far +0.064R vs -0.027R as taken (63, adequate) · closed at 8 h (the exit before dual-ai 1.7.0) -0.376R vs -0.275R as taken (9, insufficient)

Trades taken by session (UTC): ASIA 35 resolved (adequate), expectancy -0.034R · LONDON 20 resolved (insufficient), expectancy -0.013R · OVERLAP 8 resolved (insufficient), expectancy -0.382R · NEW_YORK 14 resolved (insufficient), expectancy +0.248R · LATE 3 resolved (insufficient), expectancy -1.106R

| Time | Symbol | Trader 1 | Trader 2 | Debate (shadow) | Rule | Final | Risk |
|---|---|---|---|---|---|---|---|
| 10-23 01:30 | GBPJPY | -  | -  | - | NOT_ASKED | NO_TRADE | - |
| 10-23 01:30 | EURJPY | -  | -  | - | NOT_ASKED | NO_TRADE | - |
| 10-23 01:15 | EURGBP | -  | -  | - | NOT_ASKED | NO_TRADE | - |
| 10-23 01:15 | NZDUSD | -  | -  | - | NOT_ASKED | NO_TRADE | - |
| 10-23 01:00 | USDCHF | -  | -  | - | NOT_ASKED | NO_TRADE | - |
| 10-23 01:00 | USDCAD | -  | -  | - | NOT_ASKED | NO_TRADE | - |
| 10-23 00:45 | AUDUSD | -  | -  | - | NOT_ASKED | NO_TRADE | - |
| 10-23 00:45 | USDJPY | -  | -  | - | NOT_ASKED | NO_TRADE | - |
| 10-23 00:30 | GBPUSD | -  | -  | - | NOT_ASKED | NO_TRADE | - |
| 10-23 00:30 | EURUSD | -  | -  | - | NOT_ASKED | NO_TRADE | - |
| 10-23 00:16 | AUDJPY | SELL 65 | SELL 70 | - | AGREE | SELL | APPROVED |
| 10-23 00:15 | EURCHF | SELL 68 | SELL 65 | - | AGREE | SELL | APPROVED |

The chart Trader 1 read last: `last_chart.png`. (numbers): no free vision model answered, so Trader 1 read the same chart from its numbers.

Full figures: `paper_forward.json`. Rules: `docs/PAPER_FORWARD.md` on main.
