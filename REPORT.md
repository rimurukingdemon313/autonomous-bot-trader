# PAPER FORWARD TEST — NOT REAL MONEY

Updated 2026-10-22 10:36 UTC · mode `PAPER_FORWARD` · profile `PAPER-FORWARD-200K` · shift started 2026-10-22 06:05 UTC · decision system `dual_ai`

Research status (historical, unchanged): **NO EDGE — DO NOT TRADE (historical research; this test measures forward)**. This run measures the system forward; it is not evidence of an edge until it has a sample and the forward-eligibility rules say so.

## The rule that trades: a trade only when both AIs agree

| Trades | Wins | Losses | Win rate | Net P&L | Expectancy | Profit factor | Max drawdown |
|---|---|---|---|---|---|---|---|
| 81 (adequate) | 36 | 45 | 44.4% | $-788.81 | -0.045R | 0.95 | $4,943.76 |

The 4 trade(s) of the old DEBATE rule, stopped in dual-ai-1.2.0, were removed from the paper account at the operator's request: their net $-1,416.51 was put back by a declared adjustment ($1,416.51). They stay in the journal (append-only), in none of the account's figures below.

## Paper account

| Account | Equity | P&L today | Total P&L | Drawdown | Open | Trades | Win rate | Expectancy | Profit factor | Risk | Bot |
|---|---|---|---|---|---|---|---|---|---|---|---|
| $200,000.00 | $199,854.62 | $-3.59 | $-145.38 | $-145.38 | 3 | 81 (adequate) | 44.4% | -0.045R | 0.95 | ACTIVE | RUNNING |

Equity includes declared operator adjustments of $1,416.51 (without them: $198,438.11); P&L today excludes them. `remove-retired-debate-rule-trades-2026-10-15`: operator: the 4 trades of the retired debate rule (dual-ai 1.1.0, stopped in 1.2.0) are removed from the paper account; they stay in the journal.

## Last decisions (decision → risk → paper execution)

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
- 10-22 07:30 EURCHF SELL: AI DECISION → RISK REJECTED — reward_risk: 1.08 vs minimum 1.2; structure: H1 structure is range (mixed swings): no new position without a clear H1 trend (up HH+HL or down LH+LL)
- 10-22 07:18 GBPJPY SELL: AI DECISION → RISK REJECTED — currency_conflict: SELL GBPJPY would bet against an open position: EURGBP SELL is long GBP
- 10-22 07:15 EURJPY SELL: AI DECISION → RISK REJECTED — spread: spread is 32.3% of the stop (max 25%); cost_to_risk: round-trip cost is 51.6% of the stop (max 25%): spread 0.015 + commission and slippage; structure: H1 structure is range (mixed swings): no
- 10-22 07:03 EURGBP SELL: AI DECISION → RISK APPROVED → PAPER EXECUTED
- 10-22 07:00 NZDUSD BUY: AI DECISION → RISK REJECTED — cost_to_risk: round-trip cost is 31.0% of the stop (max 25%): spread 0.00015 + commission and slippage; currency_conflict: BUY NZDUSD would bet against an open position: AUDUSD SELL is long USD; struc
- 10-22 06:47 USDCHF SELL: AI DECISION → RISK REJECTED — currency_conflict: SELL USDCHF would bet against an open position: AUDUSD SELL is long USD

## Latest decisions, NO TRADE included (2043 so far)

- 10-22 10:30 AUDJPY NO_TRADE: blocked before consulting the model: EXPOSURE: a AUDJPY position is already open
- 10-22 10:30 EURCHF NO_TRADE: risk engine: open_positions (3 open, max 3); gate_open_risk (the hard risk gate's open-risk room 64.87 is less than the next trade's risk 499.19: it would refuse the trade): the model was not consulte
- 10-22 10:18 GBPJPY SELL: SELL GBPJPY on M15: AGREE: Trader 1 (minimax/minimax-m3.1-flash:free) SELL 58: The fresh M15 bearish BOS and aligned bearish momentum favor continuation toward 209.941 and then 209.805. The stop is be
- 10-22 10:15 EURJPY SELL: SELL EURJPY on M15: AGREE: Trader 1 (minimax/minimax-m3.1-flash:free) SELL 67: Sell the countertrend rebound while M15 structure and H4 momentum remain bearish. A stop above the 176.345 swing invalida
- 10-22 10:00 EURGBP NO_TRADE: risk engine: gate_open_risk (the hard risk gate's open-risk room 218.40 is less than the next trade's risk 500.00: it would refuse the trade): the model was not consulted
- 10-22 10:00 NZDUSD NO_TRADE: risk engine: gate_open_risk (the hard risk gate's open-risk room 218.40 is less than the next trade's risk 500.00: it would refuse the trade): the model was not consulted
- 10-22 09:46 USDCHF NO_TRADE: the traders disagree (Trader 1 SELL 64, Trader 2 BUY 62): no trade unless both choose the same side; the debate (nvidia/nemotron-3-ultra-550b-a55b:free) would have chosen BUY: followed forward in shad
- 10-22 09:45 USDCAD SELL: SELL USDCAD on M15: AGREE: Trader 1 (minimax/minimax-m3.1-flash:free) SELL 67: Sell from the bid inside the entry zone after bearish M15 BOS and a failed test of the supply order block. A stop above 1
- 10-22 09:30 AUDUSD NO_TRADE: risk engine: open_positions (3 open, max 3); gate_open_risk (the hard risk gate's open-risk room 59.70 is less than the next trade's risk 498.02: it would refuse the trade): the model was not consulte
- 10-22 09:30 USDJPY NO_TRADE: risk engine: open_positions (3 open, max 3); gate_open_risk (the hard risk gate's open-risk room 59.70 is less than the next trade's risk 498.02: it would refuse the trade): the model was not consulte
- 10-22 09:17 GBPUSD NO_TRADE: risk engine: open_positions (3 open, max 3); gate_open_risk (the hard risk gate's open-risk room 137.40 is less than the next trade's risk 497.53: it would refuse the trade): the model was not consult
- 10-22 09:15 EURUSD SELL: SELL EURUSD on M15: AGREE: Trader 1 (minimax/minimax-m3.1-flash:free) SELL 63: Sell the M15 lower-high rejection and bearish continuation, targeting the 1.12196 equal-low pool. The stop sits beyond th

## Open paper positions

| Symbol | Side | Qty | Entry | Stop | Target | P&L |
|---|---|---|---|---|---|---|
| GBPJPY | SELL | 2.45 | 210.0635 | 210.32 | 209.65 | $53.31 |
| EURUSD | SELL | 3.49 | 1.1235499999999998 | 1.12466 | 1.12196 | $352.49 |
| AUDJPY | SELL | 3.95 | 110.14399999999999 | 110.29 | 109.906 | $237.63 |

## Closed paper trades (latest 20)

| Closed | Symbol | Side | Net | R | Costs | Exit | Source | Rule |
|---|---|---|---|---|---|---|---|---|
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
| 10-21 02:24 | EURJPY | BUY | $-196.89 | -0.79 | $43.04 | STOP | DUAL_AI | AGREE |
| 10-21 00:39 | GBPUSD | BUY | $-40.32 | -0.08 | $63.92 | TIME | DUAL_AI | AGREE |
| 10-21 00:35 | EURUSD | BUY | $-302.29 | -0.60 | $80.29 | TIME | DUAL_AI | AGREE |
| 10-20 21:01 | EURJPY | BUY | $-421.96 | -0.84 | $112.99 | STOP | DUAL_AI | AGREE |

## Dual AI desk (two free OpenRouter traders; a trade only when they agree)

OpenRouter `READY` · key set · trader 1 `minimax/minimax-m3.1-flash:free` · trader 2 `nvidia/nemotron-3.5-super-vl:free` · debate `google/gemma-4-26b-a4b-it:free` · calls today 61/900

Agreement trades 81 (adequate) · wins 36 · losses 45 · net $-788.81 · expectancy -0.045R · profit factor 0.95 · old DEBATE rule (stopped in dual-ai-1.2.0): 4 trade(s), net $-1,416.51, removed from the account

Disagreements (not traded; the debate runs in shadow): 97 · the debate's pick if taken: 89 resolved (adequate), expectancy -0.221R · the side it rejected if taken: 94 resolved (adequate), expectancy -0.227R

Exits in shadow (the same trades, followed again; measured, never traded): break-even at +1R -0.109R vs -0.016R as taken (60, adequate) · held 24 h +0.149R vs -0.016R as taken (60, adequate) · stop and target twice as far +0.051R vs -0.016R as taken (60, adequate) · closed at 8 h (the exit before dual-ai 1.7.0) -0.199R vs -0.294R as taken (6, insufficient)

Trades taken by session (UTC): ASIA 34 resolved (adequate), expectancy -0.003R · LONDON 20 resolved (insufficient), expectancy -0.013R · OVERLAP 8 resolved (insufficient), expectancy -0.382R · NEW_YORK 12 resolved (insufficient), expectancy +0.257R · LATE 3 resolved (insufficient), expectancy -1.106R

| Time | Symbol | Trader 1 | Trader 2 | Debate (shadow) | Rule | Final | Risk |
|---|---|---|---|---|---|---|---|
| 10-22 10:30 | AUDJPY | -  | -  | - | NOT_ASKED | NO_TRADE | - |
| 10-22 10:30 | EURCHF | -  | -  | - | NOT_ASKED | NO_TRADE | - |
| 10-22 10:18 | GBPJPY | SELL 58 | SELL 55 | - | AGREE | SELL | APPROVED |
| 10-22 10:15 | EURJPY | SELL 67 | SELL 60 | - | AGREE | SELL | REJECTED |
| 10-22 10:00 | EURGBP | -  | -  | - | NOT_ASKED | NO_TRADE | - |
| 10-22 10:00 | NZDUSD | -  | -  | - | NOT_ASKED | NO_TRADE | - |
| 10-22 09:46 | USDCHF | SELL 64 | BUY 62 | BUY | DISAGREE | NO_TRADE | - |
| 10-22 09:45 | USDCAD | SELL 67 | SELL 67 | - | AGREE | SELL | REJECTED |
| 10-22 09:30 | AUDUSD | -  | -  | - | NOT_ASKED | NO_TRADE | - |
| 10-22 09:30 | USDJPY | -  | -  | - | NOT_ASKED | NO_TRADE | - |
| 10-22 09:17 | GBPUSD | -  | -  | - | NOT_ASKED | NO_TRADE | - |
| 10-22 09:15 | EURUSD | SELL 63 | SELL 62 | - | AGREE | SELL | APPROVED |

The chart Trader 1 read last: `last_chart.png`. (numbers): no free vision model answered, so Trader 1 read the same chart from its numbers.

Full figures: `paper_forward.json`. Rules: `docs/PAPER_FORWARD.md` on main.
