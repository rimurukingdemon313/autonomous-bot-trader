# PAPER FORWARD TEST — NOT REAL MONEY

Updated 2026-10-20 05:46 UTC · mode `PAPER_FORWARD` · profile `PAPER-FORWARD-200K` · shift started 2026-10-20 03:46 UTC · decision system `dual_ai`

Research status (historical, unchanged): **NO EDGE — DO NOT TRADE (historical research; this test measures forward)**. This run measures the system forward; it is not evidence of an edge until it has a sample and the forward-eligibility rules say so.

## The rule that trades: a trade only when both AIs agree

| Trades | Wins | Losses | Win rate | Net P&L | Expectancy | Profit factor | Max drawdown |
|---|---|---|---|---|---|---|---|
| 56 (adequate) | 26 | 30 | 46.4% | $-361.87 | -0.030R | 0.96 | $3,637.77 |

The 4 trade(s) of the old DEBATE rule, stopped in dual-ai-1.2.0, were removed from the paper account at the operator's request: their net $-1,416.51 was put back by a declared adjustment ($1,416.51). They stay in the journal (append-only), in none of the account's figures below.

## Paper account

| Account | Equity | P&L today | Total P&L | Drawdown | Open | Trades | Win rate | Expectancy | Profit factor | Risk | Bot |
|---|---|---|---|---|---|---|---|---|---|---|---|
| $200,000.00 | $199,661.63 | $-236.89 | $-338.37 | $-338.37 | 3 | 56 (adequate) | 46.4% | -0.030R | 0.96 | ACTIVE | RUNNING |

Equity includes declared operator adjustments of $1,416.51 (without them: $198,245.11); P&L today excludes them. `remove-retired-debate-rule-trades-2026-10-15`: operator: the 4 trades of the retired debate rule (dual-ai 1.1.0, stopped in 1.2.0) are removed from the paper account; they stay in the journal.

## Last decisions (decision → risk → paper execution)

- 10-20 04:45 NZDUSD BUY: AI DECISION → RISK APPROVED → PAPER EXECUTED
- 10-20 03:16 USDCHF SELL: AI DECISION → RISK APPROVED → PAPER EXECUTED
- 10-20 03:15 USDCAD SELL: AI DECISION → RISK REJECTED — structure: H1 structure is range (mixed swings): no new position without a clear H1 trend (up HH+HL or down LH+LL)
- 10-20 02:30 EURCHF SELL: AI DECISION → RISK APPROVED → PAPER EXECUTED
- 10-20 02:15 EURJPY BUY: AI DECISION → RISK REJECTED — structure: H1 structure is range (mixed swings): no new position without a clear H1 trend (up HH+HL or down LH+LL)
- 10-20 02:00 EURGBP SELL: AI DECISION → RISK REJECTED — structure: H1 structure is range (mixed swings): no new position without a clear H1 trend (up HH+HL or down LH+LL)
- 10-20 01:46 USDCHF SELL: AI DECISION → RISK REJECTED — structure: H1 structure is range (mixed swings): no new position without a clear H1 trend (up HH+HL or down LH+LL)
- 10-20 01:45 USDCAD SELL: AI DECISION → RISK REJECTED — structure: H1 structure is range (mixed swings): no new position without a clear H1 trend (up HH+HL or down LH+LL)
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

## Latest decisions, NO TRADE included (1624 so far)

- 10-20 05:45 AUDUSD NO_TRADE: risk engine: open_positions (3 open, max 3); currency_exposure (2 open positions share a currency, max 2); gate_open_risk (the hard risk gate's open-risk room 322.90 is less than the next trade's risk
- 10-20 05:45 USDJPY NO_TRADE: risk engine: open_positions (3 open, max 3); currency_exposure (2 open positions share a currency, max 2); gate_open_risk (the hard risk gate's open-risk room 322.90 is less than the next trade's risk
- 10-20 05:30 GBPUSD NO_TRADE: risk engine: news (Medium-impact release GBP Average Earnings Index 3m/y in 29 min: no new position from 30 min before to 30 min after); open_positions (3 open, max 3); currency_exposure (2 open posit
- 10-20 05:30 EURUSD NO_TRADE: risk engine: open_positions (3 open, max 3); currency_exposure (2 open positions share a currency, max 2); gate_open_risk (the hard risk gate's open-risk room 318.00 is less than the next trade's risk
- 10-20 05:15 AUDJPY NO_TRADE: risk engine: open_positions (3 open, max 3); gate_open_risk (the hard risk gate's open-risk room 318.05 is less than the next trade's risk 499.17: it would refuse the trade): the model was not consult
- 10-20 05:15 EURCHF NO_TRADE: blocked before consulting the model: EXPOSURE: a EURCHF position is already open
- 10-20 05:00 GBPJPY NO_TRADE: risk engine: open_positions (3 open, max 3); gate_open_risk (the hard risk gate's open-risk room 205.77 is less than the next trade's risk 499.68: it would refuse the trade): the model was not consult
- 10-20 05:00 EURJPY NO_TRADE: risk engine: open_positions (3 open, max 3); gate_open_risk (the hard risk gate's open-risk room 205.77 is less than the next trade's risk 499.68: it would refuse the trade): the model was not consult
- 10-20 04:46 EURGBP NO_TRADE: risk engine: open_positions (3 open, max 3); gate_open_risk (the hard risk gate's open-risk room 318.00 is less than the next trade's risk 499.25: it would refuse the trade): the model was not consult
- 10-20 04:45 NZDUSD BUY: BUY NZDUSD on M15: AGREE: Trader 1 (minimax/minimax-m3.1-flash:free) BUY 66: Buy at the executable ask while M15 structure and momentum remain bullish. The stop is below the 0.56668-0.56676 support cl
- 10-20 04:30 USDCHF NO_TRADE: blocked before consulting the model: EXPOSURE: a USDCHF position is already open
- 10-20 04:30 USDCAD NO_TRADE: risk engine: open_positions (3 open, max 3); gate_open_risk (the hard risk gate's open-risk room 281.26 is less than the next trade's risk 499.58: it would refuse the trade): the model was not consult

## Open paper positions

| Symbol | Side | Qty | Entry | Stop | Target | P&L |
|---|---|---|---|---|---|---|
| NZDUSD | BUY | 3.26 | 0.567885 | 0.5666 | 0.5695 | $45.64 |
| USDCHF | SELL | 3.08 | 0.825415 | 0.82645 | 0.82401 | $126.93 |
| EURCHF | SELL | 2.51 | 0.9262 | 0.9275 | 0.92464 | $-149.08 |

## Closed paper trades (latest 20)

| Closed | Symbol | Side | Net | R | Costs | Exit | Source | Rule |
|---|---|---|---|---|---|---|---|---|
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
| 10-16 16:02 | NZDUSD | BUY | $-453.45 | -0.91 | $66.00 | STOP | DUAL_AI | AGREE |
| 10-16 12:36 | EURJPY | BUY | $-432.45 | -0.87 | $48.70 | STOP | DUAL_AI | AGREE |
| 10-16 12:38 | EURUSD | BUY | $-477.37 | -0.96 | $35.53 | STOP | DUAL_AI | AGREE |
| 10-16 10:25 | EURJPY | BUY | $422.27 | +0.85 | $64.90 | TARGET | DUAL_AI | AGREE |
| 10-16 10:04 | EURUSD | BUY | $459.54 | +0.92 | $53.28 | TARGET | DUAL_AI | AGREE |

## Dual AI desk (two free OpenRouter traders; a trade only when they agree)

OpenRouter `READY` · key set · trader 1 `minimax/minimax-m3.1-flash:free` · trader 2 `nvidia/nemotron-3.5-super-vl:free` · debate `thinkingmachines/inkling-small:free` · calls today 2/900

Agreement trades 56 (adequate) · wins 26 · losses 30 · net $-361.87 · expectancy -0.030R · profit factor 0.96 · old DEBATE rule (stopped in dual-ai-1.2.0): 4 trade(s), net $-1,416.51, removed from the account

Disagreements (not traded; the debate runs in shadow): 87 · the debate's pick if taken: 83 resolved (adequate), expectancy -0.186R · the side it rejected if taken: 88 resolved (adequate), expectancy -0.226R

Exits in shadow (the same trades, followed again; measured, never traded): break-even at +1R -0.092R vs +0.017R as taken (42, adequate) · held 24 h +0.334R vs +0.154R as taken (33, adequate) · stop and target twice as far +0.207R vs +0.154R as taken (33, adequate)

Trades taken by session (UTC): ASIA 24 resolved (insufficient), expectancy +0.083R · LONDON 15 resolved (insufficient), expectancy -0.149R · OVERLAP 8 resolved (insufficient), expectancy -0.382R · NEW_YORK 9 resolved (insufficient), expectancy +0.515R · LATE 3 resolved (insufficient), expectancy -1.106R

| Time | Symbol | Trader 1 | Trader 2 | Debate (shadow) | Rule | Final | Risk |
|---|---|---|---|---|---|---|---|
| 10-20 05:45 | AUDUSD | -  | -  | - | NOT_ASKED | NO_TRADE | - |
| 10-20 05:45 | USDJPY | -  | -  | - | NOT_ASKED | NO_TRADE | - |
| 10-20 05:30 | GBPUSD | -  | -  | - | NOT_ASKED | NO_TRADE | - |
| 10-20 05:30 | EURUSD | -  | -  | - | NOT_ASKED | NO_TRADE | - |
| 10-20 05:15 | AUDJPY | -  | -  | - | NOT_ASKED | NO_TRADE | - |
| 10-20 05:15 | EURCHF | -  | -  | - | NOT_ASKED | NO_TRADE | - |
| 10-20 05:00 | GBPJPY | -  | -  | - | NOT_ASKED | NO_TRADE | - |
| 10-20 05:00 | EURJPY | -  | -  | - | NOT_ASKED | NO_TRADE | - |
| 10-20 04:46 | EURGBP | -  | -  | - | NOT_ASKED | NO_TRADE | - |
| 10-20 04:45 | NZDUSD | BUY 66 | BUY 60 | - | AGREE | BUY | APPROVED |
| 10-20 04:30 | USDCHF | -  | -  | - | NOT_ASKED | NO_TRADE | - |
| 10-20 04:30 | USDCAD | -  | -  | - | NOT_ASKED | NO_TRADE | - |

The chart Trader 1 read last: `last_chart.png`. (numbers): no free vision model answered, so Trader 1 read the same chart from its numbers.

Full figures: `paper_forward.json`. Rules: `docs/PAPER_FORWARD.md` on main.
