# PAPER FORWARD TEST — NOT REAL MONEY

Updated 2026-10-20 04:01 UTC · mode `PAPER_FORWARD` · profile `PAPER-FORWARD-200K` · shift started 2026-10-20 03:46 UTC · decision system `dual_ai`

Research status (historical, unchanged): **NO EDGE — DO NOT TRADE (historical research; this test measures forward)**. This run measures the system forward; it is not evidence of an edge until it has a sample and the forward-eligibility rules say so.

## The rule that trades: a trade only when both AIs agree

| Trades | Wins | Losses | Win rate | Net P&L | Expectancy | Profit factor | Max drawdown |
|---|---|---|---|---|---|---|---|
| 55 (adequate) | 26 | 29 | 47.3% | $82.06 | -0.015R | 1.01 | $3,487.06 |

The 4 trade(s) of the old DEBATE rule, stopped in dual-ai-1.2.0, were removed from the paper account at the operator's request: their net $-1,416.51 was put back by a declared adjustment ($1,416.51). They stay in the journal (append-only), in none of the account's figures below.

## Paper account

| Account | Equity | P&L today | Total P&L | Drawdown | Open | Trades | Win rate | Expectancy | Profit factor | Risk | Bot |
|---|---|---|---|---|---|---|---|---|---|---|---|
| $200,000.00 | $199,927.68 | $29.17 | $-72.32 | $-72.32 | 3 | 55 (adequate) | 47.3% | -0.015R | 1.01 | ACTIVE | RUNNING |

Equity includes declared operator adjustments of $1,416.51 (without them: $198,511.17); P&L today excludes them. `remove-retired-debate-rule-trades-2026-10-15`: operator: the 4 trades of the retired debate rule (dual-ai 1.1.0, stopped in 1.2.0) are removed from the paper account; they stay in the journal.

## Last decisions (decision → risk → paper execution)

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
- 10-19 19:00 NZDUSD BUY: AI DECISION → RISK APPROVED → PAPER EXECUTED

## Latest decisions, NO TRADE included (1610 so far)

- 10-20 04:00 GBPUSD NO_TRADE: risk engine: open_positions (3 open, max 3); gate_open_risk (the hard risk gate's open-risk room 356.06 is less than the next trade's risk 499.67: it would refuse the trade): the model was not consult
- 10-20 04:00 EURUSD NO_TRADE: risk engine: open_positions (3 open, max 3); gate_open_risk (the hard risk gate's open-risk room 356.06 is less than the next trade's risk 499.67: it would refuse the trade): the model was not consult
- 10-20 03:45 GBPJPY NO_TRADE: blocked before consulting the model: STALE_DATA: quote is 182s old; EXPOSURE: a GBPJPY position is already open
- 10-20 03:45 EURJPY NO_TRADE: blocked before consulting the model: STALE_DATA: quote is 181s old
- 10-20 03:30 EURGBP NO_TRADE: risk engine: open_positions (3 open, max 3): the model was not consulted
- 10-20 03:30 NZDUSD NO_TRADE: risk engine: open_positions (3 open, max 3): the model was not consulted
- 10-20 03:16 USDCHF SELL: SELL USDCHF on M15: AGREE: Trader 1 (minimax/minimax-m3.1-flash:free) SELL 64: Sell the rebound into bearish M15 structure because the recent bearish BOS and H4 context outweigh the range classificati
- 10-20 03:15 USDCAD SELL: SELL USDCAD on M15: AGREE: Trader 1 (minimax/minimax-m3.1-flash:free) SELL 72: The aligned bearish M15/H4 structure and fresh break below 1.40860 favor continuation toward 1.40670. A move above the be
- 10-20 03:00 AUDUSD NO_TRADE: risk engine: open_positions (3 open, max 3): the model was not consulted
- 10-20 03:00 USDJPY NO_TRADE: risk engine: open_positions (3 open, max 3): the model was not consulted
- 10-20 02:45 GBPUSD NO_TRADE: risk engine: open_positions (3 open, max 3): the model was not consulted
- 10-20 02:45 EURUSD NO_TRADE: risk engine: open_positions (3 open, max 3): the model was not consulted

## Open paper positions

| Symbol | Side | Qty | Entry | Stop | Target | P&L |
|---|---|---|---|---|---|---|
| USDCHF | SELL | 3.08 | 0.825415 | 0.82645 | 0.82401 | $164.29 |
| EURCHF | SELL | 2.51 | 0.9262 | 0.9275 | 0.92464 | $-57.81 |
| GBPJPY | BUY | 2.45 | 211.1505 | 210.875 | 211.5 | $-260.85 |

## Closed paper trades (latest 20)

| Closed | Symbol | Side | Net | R | Costs | Exit | Source | Rule |
|---|---|---|---|---|---|---|---|---|
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
| 10-16 08:05 | EURGBP | SELL | $129.31 | +0.26 | $81.01 | TIME | DUAL_AI | AGREE |

## Dual AI desk (two free OpenRouter traders; a trade only when they agree)

OpenRouter `CATALOG_NOT_READ_YET` · key set · trader 1 `None` · trader 2 `None` · debate `None` · calls today 0/900

Agreement trades 55 (adequate) · wins 26 · losses 29 · net $82.06 · expectancy -0.015R · profit factor 1.01 · old DEBATE rule (stopped in dual-ai-1.2.0): 4 trade(s), net $-1,416.51, removed from the account

Disagreements (not traded; the debate runs in shadow): 87 · the debate's pick if taken: 76 resolved (adequate), expectancy -0.187R · the side it rejected if taken: 81 resolved (adequate), expectancy -0.177R

Exits in shadow (the same trades, followed again; measured, never traded): break-even at +1R -0.118R vs -0.006R as taken (41, adequate) · held 24 h +0.381R vs +0.195R as taken (32, adequate) · stop and target twice as far +0.178R vs +0.195R as taken (32, adequate)

Trades taken by session (UTC): ASIA 24 resolved (insufficient), expectancy +0.083R · LONDON 15 resolved (insufficient), expectancy -0.149R · OVERLAP 8 resolved (insufficient), expectancy -0.382R · NEW_YORK 8 resolved (insufficient), expectancy +0.460R · LATE 3 resolved (insufficient), expectancy -1.106R

| Time | Symbol | Trader 1 | Trader 2 | Debate (shadow) | Rule | Final | Risk |
|---|---|---|---|---|---|---|---|
| 10-20 04:00 | GBPUSD | -  | -  | - | NOT_ASKED | NO_TRADE | - |
| 10-20 04:00 | EURUSD | -  | -  | - | NOT_ASKED | NO_TRADE | - |
| 10-20 03:45 | GBPJPY | -  | -  | - | NOT_ASKED | NO_TRADE | - |
| 10-20 03:45 | EURJPY | -  | -  | - | NOT_ASKED | NO_TRADE | - |
| 10-20 03:30 | EURGBP | -  | -  | - | NOT_ASKED | NO_TRADE | - |
| 10-20 03:30 | NZDUSD | -  | -  | - | NOT_ASKED | NO_TRADE | - |
| 10-20 03:16 | USDCHF | SELL 64 | SELL 60 | - | AGREE | SELL | APPROVED |
| 10-20 03:15 | USDCAD | SELL 72 | SELL 68 | - | AGREE | SELL | REJECTED |
| 10-20 03:00 | AUDUSD | -  | -  | - | NOT_ASKED | NO_TRADE | - |
| 10-20 03:00 | USDJPY | -  | -  | - | NOT_ASKED | NO_TRADE | - |
| 10-20 02:45 | GBPUSD | -  | -  | - | NOT_ASKED | NO_TRADE | - |
| 10-20 02:45 | EURUSD | -  | -  | - | NOT_ASKED | NO_TRADE | - |

The chart Trader 1 read last: `last_chart.png`. (numbers): no free vision model answered, so Trader 1 read the same chart from its numbers.

Full figures: `paper_forward.json`. Rules: `docs/PAPER_FORWARD.md` on main.
