# PAPER FORWARD TEST — NOT REAL MONEY

Updated 2026-10-20 18:43 UTC · mode `PAPER_FORWARD` · profile `PAPER-FORWARD-200K` · shift started 2026-10-20 14:57 UTC · decision system `dual_ai`

Research status (historical, unchanged): **NO EDGE — DO NOT TRADE (historical research; this test measures forward)**. This run measures the system forward; it is not evidence of an edge until it has a sample and the forward-eligibility rules say so.

## The rule that trades: a trade only when both AIs agree

| Trades | Wins | Losses | Win rate | Net P&L | Expectancy | Profit factor | Max drawdown |
|---|---|---|---|---|---|---|---|
| 61 (adequate) | 31 | 30 | 50.8% | $2,039.50 | +0.051R | 1.21 | $3,637.77 |

The 4 trade(s) of the old DEBATE rule, stopped in dual-ai-1.2.0, were removed from the paper account at the operator's request: their net $-1,416.51 was put back by a declared adjustment ($1,416.51). They stay in the journal (append-only), in none of the account's figures below.

## Paper account

| Account | Equity | P&L today | Total P&L | Drawdown | Open | Trades | Win rate | Expectancy | Profit factor | Risk | Bot |
|---|---|---|---|---|---|---|---|---|---|---|---|
| $200,000.00 | $202,416.85 | $2,518.34 | $2,416.85 | $0.00 | 3 | 61 (adequate) | 50.8% | +0.051R | 1.21 | ACTIVE | RUNNING |

Equity includes declared operator adjustments of $1,416.51 (without them: $201,000.34); P&L today excludes them. `remove-retired-debate-rule-trades-2026-10-15`: operator: the 4 trades of the retired debate rule (dual-ai 1.1.0, stopped in 1.2.0) are removed from the paper account; they stay in the journal.

## Last decisions (decision → risk → paper execution)

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
- 10-20 09:15 EURGBP SELL: AI DECISION → RISK REJECTED — structure: H1 structure is range (mixed swings): no new position without a clear H1 trend (up HH+HL or down LH+LL)
- 10-20 04:45 NZDUSD BUY: AI DECISION → RISK APPROVED → PAPER EXECUTED
- 10-20 03:16 USDCHF SELL: AI DECISION → RISK APPROVED → PAPER EXECUTED
- 10-20 03:15 USDCAD SELL: AI DECISION → RISK REJECTED — structure: H1 structure is range (mixed swings): no new position without a clear H1 trend (up HH+HL or down LH+LL)
- 10-20 02:30 EURCHF SELL: AI DECISION → RISK APPROVED → PAPER EXECUTED
- 10-20 02:15 EURJPY BUY: AI DECISION → RISK REJECTED — structure: H1 structure is range (mixed swings): no new position without a clear H1 trend (up HH+HL or down LH+LL)
- 10-20 02:00 EURGBP SELL: AI DECISION → RISK REJECTED — structure: H1 structure is range (mixed swings): no new position without a clear H1 trend (up HH+HL or down LH+LL)

## Latest decisions, NO TRADE included (1726 so far)

- 10-20 18:30 USDCHF NO_TRADE: risk engine: open_positions (3 open, max 3); currency_exposure (2 open positions share a currency, max 2); gate_open_risk (the hard risk gate's open-risk room 343.75 is less than the next trade's risk
- 10-20 18:30 USDCAD NO_TRADE: risk engine: open_positions (3 open, max 3); currency_exposure (2 open positions share a currency, max 2); gate_open_risk (the hard risk gate's open-risk room 343.75 is less than the next trade's risk
- 10-20 18:15 AUDUSD NO_TRADE: risk engine: open_positions (3 open, max 3); currency_exposure (2 open positions share a currency, max 2); gate_open_risk (the hard risk gate's open-risk room 372.72 is less than the next trade's risk
- 10-20 18:15 USDJPY NO_TRADE: risk engine: open_positions (3 open, max 3); currency_exposure (2 open positions share a currency, max 2); gate_open_risk (the hard risk gate's open-risk room 372.72 is less than the next trade's risk
- 10-20 18:00 GBPUSD NO_TRADE: blocked before consulting the model: EXPOSURE: a GBPUSD position is already open
- 10-20 18:00 EURUSD NO_TRADE: blocked before consulting the model: EXPOSURE: a EURUSD position is already open
- 10-20 17:45 AUDJPY NO_TRADE: risk engine: open_positions (3 open, max 3); gate_open_risk (the hard risk gate's open-risk room 347.69 is less than the next trade's risk 500.00: it would refuse the trade): the model was not consult
- 10-20 17:45 EURCHF NO_TRADE: risk engine: open_positions (3 open, max 3); currency_exposure (2 open positions share a currency, max 2); gate_open_risk (the hard risk gate's open-risk room 347.69 is less than the next trade's risk
- 10-20 17:32 GBPJPY NO_TRADE: risk engine: open_positions (3 open, max 3); gate_open_risk (the hard risk gate's open-risk room 398.09 is less than the next trade's risk 500.00: it would refuse the trade): the model was not consult
- 10-20 17:30 EURJPY BUY: BUY EURJPY on M15: AGREE: Trader 1 (minimax/minimax-m3.1-flash:free) BUY 64: Buy the continuation above 177.721, targeting the clear liquidity pool at 177.918. The stop sits below the 177.581-177.607 
- 10-20 17:15 EURGBP SELL: SELL EURGBP on M15: AGREE: Trader 1 (minimax/minimax-m3.1-flash:free) SELL 58: The bearish higher-timeframe structure and sustained lower-timeframe momentum favor selling into weakness toward 0.83842.
- 10-20 17:15 NZDUSD NO_TRADE: risk engine: currency_exposure (2 open positions share a currency, max 2): the model was not consulted

## Open paper positions

| Symbol | Side | Qty | Entry | Stop | Target | P&L |
|---|---|---|---|---|---|---|
| EURJPY | BUY | 4.88 | 177.6765 | 177.56 | 177.918 | $104.53 |
| GBPUSD | BUY | 2.36 | 1.33757 | 1.3358 | 1.34086 | $158.12 |
| EURUSD | BUY | 3.7 | 1.12365 | 1.1226 | 1.12511 | $114.70 |

## Closed paper trades (latest 20)

| Closed | Symbol | Side | Net | R | Costs | Exit | Source | Rule |
|---|---|---|---|---|---|---|---|---|
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
| 10-19 07:55 | EURJPY | BUY | $-212.66 | -0.86 | $24.44 | STOP | DUAL_AI | AGREE |
| 10-19 07:01 | GBPUSD | SELL | $-422.19 | -0.85 | $83.37 | STOP | DUAL_AI | AGREE |
| 10-19 06:28 | EURGBP | BUY | $-419.53 | -0.84 | $88.51 | STOP | DUAL_AI | AGREE |
| 10-19 03:31 | AUDUSD | BUY | $200.64 | +0.80 | $41.04 | TARGET | DUAL_AI | AGREE |
| 10-19 02:46 | GBPUSD | BUY | $-202.34 | -0.81 | $36.33 | STOP | DUAL_AI | AGREE |

## Dual AI desk (two free OpenRouter traders; a trade only when they agree)

OpenRouter `READY` · key set · trader 1 `minimax/minimax-m3.1-flash:free` · trader 2 `nvidia/nemotron-3.5-super-vl:free` · debate `google/gemma-4-26b-a4b-it:free` · calls today 27/900

Agreement trades 61 (adequate) · wins 31 · losses 30 · net $2,039.50 · expectancy +0.051R · profit factor 1.21 · old DEBATE rule (stopped in dual-ai-1.2.0): 4 trade(s), net $-1,416.51, removed from the account

Disagreements (not traded; the debate runs in shadow): 89 · the debate's pick if taken: 83 resolved (adequate), expectancy -0.186R · the side it rejected if taken: 88 resolved (adequate), expectancy -0.226R

Exits in shadow (the same trades, followed again; measured, never traded): break-even at +1R -0.038R vs +0.089R as taken (47, adequate) · held 24 h +0.197R vs -0.006R as taken (41, adequate) · stop and target twice as far +0.150R vs -0.006R as taken (41, adequate)

Trades taken by session (UTC): ASIA 28 resolved (insufficient), expectancy +0.138R · LONDON 16 resolved (insufficient), expectancy -0.040R · OVERLAP 8 resolved (insufficient), expectancy -0.382R · NEW_YORK 9 resolved (insufficient), expectancy +0.515R · LATE 3 resolved (insufficient), expectancy -1.106R

| Time | Symbol | Trader 1 | Trader 2 | Debate (shadow) | Rule | Final | Risk |
|---|---|---|---|---|---|---|---|
| 10-20 18:30 | USDCHF | -  | -  | - | NOT_ASKED | NO_TRADE | - |
| 10-20 18:30 | USDCAD | -  | -  | - | NOT_ASKED | NO_TRADE | - |
| 10-20 18:15 | AUDUSD | -  | -  | - | NOT_ASKED | NO_TRADE | - |
| 10-20 18:15 | USDJPY | -  | -  | - | NOT_ASKED | NO_TRADE | - |
| 10-20 18:00 | GBPUSD | -  | -  | - | NOT_ASKED | NO_TRADE | - |
| 10-20 18:00 | EURUSD | -  | -  | - | NOT_ASKED | NO_TRADE | - |
| 10-20 17:45 | AUDJPY | -  | -  | - | NOT_ASKED | NO_TRADE | - |
| 10-20 17:45 | EURCHF | -  | -  | - | NOT_ASKED | NO_TRADE | - |
| 10-20 17:32 | GBPJPY | -  | -  | - | NOT_ASKED | NO_TRADE | - |
| 10-20 17:30 | EURJPY | BUY 64 | BUY 60 | - | AGREE | BUY | APPROVED |
| 10-20 17:15 | EURGBP | SELL 58 | SELL 58 | - | AGREE | SELL | REJECTED |
| 10-20 17:15 | NZDUSD | -  | -  | - | NOT_ASKED | NO_TRADE | - |

The chart Trader 1 read last: `last_chart.png`. (numbers): no free vision model answered, so Trader 1 read the same chart from its numbers.

Full figures: `paper_forward.json`. Rules: `docs/PAPER_FORWARD.md` on main.
