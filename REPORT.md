# PAPER FORWARD TEST — NOT REAL MONEY

Updated 2026-10-22 02:00 UTC · mode `PAPER_FORWARD` · profile `PAPER-FORWARD-200K` · shift started 2026-10-22 00:30 UTC · decision system `dual_ai`

Research status (historical, unchanged): **NO EDGE — DO NOT TRADE (historical research; this test measures forward)**. This run measures the system forward; it is not evidence of an edge until it has a sample and the forward-eligibility rules say so.

## The rule that trades: a trade only when both AIs agree

| Trades | Wins | Losses | Win rate | Net P&L | Expectancy | Profit factor | Max drawdown |
|---|---|---|---|---|---|---|---|
| 74 (adequate) | 33 | 41 | 44.6% | $-825.05 | -0.050R | 0.94 | $4,100.95 |

The 4 trade(s) of the old DEBATE rule, stopped in dual-ai-1.2.0, were removed from the paper account at the operator's request: their net $-1,416.51 was put back by a declared adjustment ($1,416.51). They stay in the journal (append-only), in none of the account's figures below.

## Paper account

| Account | Equity | P&L today | Total P&L | Drawdown | Open | Trades | Win rate | Expectancy | Profit factor | Risk | Bot |
|---|---|---|---|---|---|---|---|---|---|---|---|
| $200,000.00 | $198,939.75 | $-918.46 | $-1,060.25 | $-1,060.25 | 2 | 74 (adequate) | 44.6% | -0.050R | 0.94 | ACTIVE | RUNNING |

Equity includes declared operator adjustments of $1,416.51 (without them: $197,523.24); P&L today excludes them. `remove-retired-debate-rule-trades-2026-10-15`: operator: the 4 trades of the retired debate rule (dual-ai 1.1.0, stopped in 1.2.0) are removed from the paper account; they stay in the journal.

## Last decisions (decision → risk → paper execution)

- 10-22 00:15 EURGBP SELL: AI DECISION → RISK APPROVED → PAPER EXECUTED
- 10-21 17:05 USDCHF SELL: AI DECISION → RISK APPROVED → PAPER EXECUTED
- 10-21 17:00 USDCAD SELL: AI DECISION → RISK REJECTED — cost_to_risk: round-trip cost is 31.0% of the stop (max 25%): spread 0.00015 + commission and slippage; structure: H1 structure is range (mixed swings): no new position without a clear H1 trend (up HH
- 10-21 16:09 GBPJPY BUY: AI DECISION → RISK APPROVED → PAPER EXECUTED
- 10-21 11:50 GBPJPY SELL: AI DECISION → RISK REJECTED — structure: H1 structure is range (mixed swings): no new position without a clear H1 trend (up HH+HL or down LH+LL)
- 10-21 11:30 EURGBP SELL: AI DECISION → RISK REJECTED — reward_risk: 1.08 vs minimum 1.2; structure: H1 structure is range (mixed swings): no new position without a clear H1 trend (up HH+HL or down LH+LL)
- 10-21 10:32 AUDJPY BUY: AI DECISION → RISK REJECTED — reward_risk: 1.03 vs minimum 1.2
- 10-21 10:30 EURCHF SELL: AI DECISION → RISK REJECTED — structure: H1 structure is range (mixed swings): no new position without a clear H1 trend (up HH+HL or down LH+LL)
- 10-21 10:16 GBPJPY BUY: AI DECISION → RISK REJECTED — structure: H1 structure is range (mixed swings): no new position without a clear H1 trend (up HH+HL or down LH+LL)
- 10-21 10:15 EURJPY SELL: AI DECISION → RISK REJECTED — structure: H1 structure is range (mixed swings): no new position without a clear H1 trend (up HH+HL or down LH+LL)
- 10-21 10:00 EURGBP SELL: AI DECISION → RISK REJECTED — structure: H1 structure is range (mixed swings): no new position without a clear H1 trend (up HH+HL or down LH+LL)
- 10-21 08:45 EURJPY BUY: AI DECISION → RISK APPROVED → PAPER EXECUTED
- 10-21 08:30 EURGBP SELL: AI DECISION → RISK REJECTED — structure: H1 structure is range (mixed swings): no new position without a clear H1 trend (up HH+HL or down LH+LL)
- 10-21 08:05 AUDUSD BUY: AI DECISION → RISK APPROVED → PAPER EXECUTED
- 10-21 07:31 EURGBP SELL: AI DECISION → RISK REJECTED — reward_risk: 1.03 vs minimum 1.2; structure: H1 structure is range (mixed swings): no new position without a clear H1 trend (up HH+HL or down LH+LL)
- 10-21 07:30 NZDUSD BUY: AI DECISION → RISK APPROVED → PAPER EXECUTED
- 10-21 07:15 USDCHF SELL: AI DECISION → RISK REJECTED — reward_risk: 1.15 vs minimum 1.2
- 10-21 07:01 AUDUSD BUY: AI DECISION → RISK REJECTED — reward_risk: 0.97 vs minimum 1.2; currency_conflict: BUY AUDUSD would bet against an open position: AUDJPY SELL is short AUD
- 10-21 07:00 USDJPY SELL: AI DECISION → RISK REJECTED — structure: H1 structure is range (mixed swings): no new position without a clear H1 trend (up HH+HL or down LH+LL)
- 10-21 05:00 AUDJPY SELL: AI DECISION → RISK APPROVED → PAPER EXECUTED

## Latest decisions, NO TRADE included (1974 so far)

- 10-22 01:45 GBPJPY NO_TRADE: risk engine: open_positions (3 open, max 3): the model was not consulted
- 10-22 01:45 EURJPY NO_TRADE: risk engine: open_positions (3 open, max 3): the model was not consulted
- 10-22 01:30 EURGBP NO_TRADE: blocked before consulting the model: EXPOSURE: a EURGBP position is already open
- 10-22 01:30 NZDUSD NO_TRADE: risk engine: open_positions (3 open, max 3); currency_exposure (2 open positions share a currency, max 2): the model was not consulted
- 10-22 01:15 USDCHF NO_TRADE: blocked before consulting the model: EXPOSURE: a USDCHF position is already open
- 10-22 01:15 USDCAD NO_TRADE: risk engine: open_positions (3 open, max 3); currency_exposure (2 open positions share a currency, max 2); gate_open_risk (the hard risk gate's open-risk room 401.85 is less than the next trade's risk
- 10-22 01:00 AUDUSD NO_TRADE: blocked before consulting the model: EXPOSURE: a AUDUSD position is already open
- 10-22 01:00 USDJPY NO_TRADE: risk engine: open_positions (3 open, max 3); currency_exposure (2 open positions share a currency, max 2); gate_open_risk (the hard risk gate's open-risk room 321.17 is less than the next trade's risk
- 10-22 00:45 GBPUSD NO_TRADE: risk engine: open_positions (3 open, max 3); currency_exposure (2 open positions share a currency, max 2): the model was not consulted
- 10-22 00:45 EURUSD NO_TRADE: risk engine: open_positions (3 open, max 3); currency_exposure (2 open positions share a currency, max 2): the model was not consulted
- 10-22 00:15 EURGBP SELL: SELL EURGBP on M15: AGREE: Trader 1 (minimax/minimax-m3.1-flash:free) SELL 72: The higher-probability side is short because both timeframes retain bearish structure and liquidity remains clustered abo
- 10-22 00:15 NZDUSD NO_TRADE: risk engine: currency_exposure (2 open positions share a currency, max 2): the model was not consulted

## Open paper positions

| Symbol | Side | Qty | Entry | Stop | Target | P&L |
|---|---|---|---|---|---|---|
| EURGBP | SELL | 3.08 | 0.8384300000000001 | 0.83941 | 0.83712 | $-218.53 |
| USDCHF | SELL | 2.29 | 0.824415 | 0.82592 | 0.8222 | $-16.67 |

## Closed paper trades (latest 20)

| Closed | Symbol | Side | Net | R | Costs | Exit | Source | Rule |
|---|---|---|---|---|---|---|---|---|
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
| 10-20 09:04 | EURCHF | SELL | $457.35 | +0.92 | $75.41 | TARGET | DUAL_AI | AGREE |
| 10-20 04:32 | GBPJPY | BUY | $-443.93 | -0.89 | $58.82 | STOP | DUAL_AI | AGREE |
| 10-20 03:08 | NZDUSD | BUY | $187.98 | +0.75 | $54.42 | TIME | DUAL_AI | AGREE |

## Dual AI desk (two free OpenRouter traders; a trade only when they agree)

OpenRouter `READY` · key set · trader 1 `minimax/minimax-m3.1-flash:free` · trader 2 `nvidia/nemotron-3.5-super-vl:free` · debate `thinkingmachines/inkling-small:free` · calls today 1/900

Agreement trades 74 (adequate) · wins 33 · losses 41 · net $-825.05 · expectancy -0.050R · profit factor 0.94 · old DEBATE rule (stopped in dual-ai-1.2.0): 4 trade(s), net $-1,416.51, removed from the account

Disagreements (not traded; the debate runs in shadow): 93 · the debate's pick if taken: 85 resolved (adequate), expectancy -0.206R · the side it rejected if taken: 90 resolved (adequate), expectancy -0.244R

Exits in shadow (the same trades, followed again; measured, never traded): break-even at +1R -0.088R vs +0.015R as taken (54, adequate) · held 24 h +0.198R vs +0.015R as taken (54, adequate) · stop and target twice as far +0.126R vs +0.015R as taken (54, adequate) · closed at 8 h (the exit before dual-ai 1.7.0) none resolved yet

Trades taken by session (UTC): ASIA 31 resolved (adequate), expectancy +0.022R · LONDON 17 resolved (insufficient), expectancy +0.042R · OVERLAP 8 resolved (insufficient), expectancy -0.382R · NEW_YORK 12 resolved (insufficient), expectancy +0.257R · LATE 3 resolved (insufficient), expectancy -1.106R

| Time | Symbol | Trader 1 | Trader 2 | Debate (shadow) | Rule | Final | Risk |
|---|---|---|---|---|---|---|---|
| 10-22 01:45 | GBPJPY | -  | -  | - | NOT_ASKED | NO_TRADE | - |
| 10-22 01:45 | EURJPY | -  | -  | - | NOT_ASKED | NO_TRADE | - |
| 10-22 01:30 | EURGBP | -  | -  | - | NOT_ASKED | NO_TRADE | - |
| 10-22 01:30 | NZDUSD | -  | -  | - | NOT_ASKED | NO_TRADE | - |
| 10-22 01:15 | USDCHF | -  | -  | - | NOT_ASKED | NO_TRADE | - |
| 10-22 01:15 | USDCAD | -  | -  | - | NOT_ASKED | NO_TRADE | - |
| 10-22 01:00 | AUDUSD | -  | -  | - | NOT_ASKED | NO_TRADE | - |
| 10-22 01:00 | USDJPY | -  | -  | - | NOT_ASKED | NO_TRADE | - |
| 10-22 00:45 | GBPUSD | -  | -  | - | NOT_ASKED | NO_TRADE | - |
| 10-22 00:45 | EURUSD | -  | -  | - | NOT_ASKED | NO_TRADE | - |
| 10-22 00:15 | EURGBP | SELL 72 | SELL 61 | - | AGREE | SELL | APPROVED |
| 10-22 00:15 | NZDUSD | -  | -  | - | NOT_ASKED | NO_TRADE | - |

The chart Trader 1 read last: `last_chart.png`. (numbers): no free vision model answered, so Trader 1 read the same chart from its numbers.

Full figures: `paper_forward.json`. Rules: `docs/PAPER_FORWARD.md` on main.
