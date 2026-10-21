# PAPER FORWARD TEST — NOT REAL MONEY

Updated 2026-10-21 11:14 UTC · mode `PAPER_FORWARD` · profile `PAPER-FORWARD-200K` · shift started 2026-10-21 07:43 UTC · decision system `dual_ai`

Research status (historical, unchanged): **NO EDGE — DO NOT TRADE (historical research; this test measures forward)**. This run measures the system forward; it is not evidence of an edge until it has a sample and the forward-eligibility rules say so.

## The rule that trades: a trade only when both AIs agree

| Trades | Wins | Losses | Win rate | Net P&L | Expectancy | Profit factor | Max drawdown |
|---|---|---|---|---|---|---|---|
| 71 (adequate) | 32 | 39 | 45.1% | $206.38 | -0.033R | 1.02 | $3,637.77 |

The 4 trade(s) of the old DEBATE rule, stopped in dual-ai-1.2.0, were removed from the paper account at the operator's request: their net $-1,416.51 was put back by a declared adjustment ($1,416.51). They stay in the journal (append-only), in none of the account's figures below.

## Paper account

| Account | Equity | P&L today | Total P&L | Drawdown | Open | Trades | Win rate | Expectancy | Profit factor | Risk | Bot |
|---|---|---|---|---|---|---|---|---|---|---|---|
| $200,000.00 | $200,543.38 | $-1,202.01 | $543.38 | $0.00 | 2 | 71 (adequate) | 45.1% | -0.033R | 1.02 | ACTIVE | RUNNING |

Equity includes declared operator adjustments of $1,416.51 (without them: $199,126.86); P&L today excludes them. `remove-retired-debate-rule-trades-2026-10-15`: operator: the 4 trades of the retired debate rule (dual-ai 1.1.0, stopped in 1.2.0) are removed from the paper account; they stay in the journal.

## Last decisions (decision → risk → paper execution)

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
- 10-21 02:45 USDCAD SELL: AI DECISION → RISK APPROVED → PAPER EXECUTED
- 10-21 02:31 AUDUSD BUY: AI DECISION → RISK APPROVED → PAPER EXECUTED
- 10-21 02:30 USDJPY SELL: AI DECISION → RISK REJECTED — currency_conflict: SELL USDJPY would bet against an open position: GBPJPY BUY is short JPY
- 10-21 01:00 EURCHF BUY: AI DECISION → RISK APPROVED → PAPER EXECUTED
- 10-21 00:46 GBPJPY BUY: AI DECISION → RISK APPROVED → PAPER EXECUTED
- 10-21 00:45 EURJPY BUY: AI DECISION → RISK APPROVED → PAPER EXECUTED

## Latest decisions, NO TRADE included (1858 so far)

- 10-21 11:00 AUDUSD NO_TRADE: blocked before consulting the model: EXPOSURE: a AUDUSD position is already open
- 10-21 11:00 USDJPY NO_TRADE: risk engine: currency_exposure (2 open positions share a currency, max 2): the model was not consulted
- 10-21 10:45 GBPUSD NO_TRADE: risk engine: currency_exposure (2 open positions share a currency, max 2): the model was not consulted
- 10-21 10:45 EURUSD NO_TRADE: risk engine: currency_exposure (2 open positions share a currency, max 2): the model was not consulted
- 10-21 10:32 AUDJPY BUY: BUY AUDJPY on M15: AGREE: Trader 1 (minimax/minimax-m3.1-flash:free) BUY 61: Buy the pullback after the bullish sweep of 111.046, using the tested demand block and 110.923 invalidation. The H4 uptrend
- 10-21 10:30 EURCHF SELL: SELL EURCHF on M15: AGREE: Trader 1 (minimax/minimax-m3.1-flash:free) SELL 62: Sell the rebound from tested supply while M15 structure and the H4 bearish breaks remain intact. The stop is beyond the 0
- 10-21 10:16 GBPJPY BUY: BUY GBPJPY on M15: AGREE: Trader 1 (nvidia/nemotron-3.5-super-vl:free) BUY 68: Both timeframes trend up with a fresh bullish BOS at 211.831 and CHoCH at 211.702; price is inside the entry zone after b
- 10-21 10:15 EURJPY SELL: SELL EURJPY on M15: AGREE: Trader 1 (minimax/minimax-m3.1-flash:free) SELL 62: Sell the confirmed M15 bearish break and continuation, targeting the prior-day low after the 177.298 equal-low pool. The 
- 10-21 10:00 EURGBP SELL: SELL EURGBP on M15: AGREE: Trader 1 (minimax/minimax-m3.1-flash:free) SELL 68: The aligned bearish M15/H4 structure and repeated BOS failures below resistance give the short side higher probability. E
- 10-21 10:00 NZDUSD NO_TRADE: blocked before consulting the model: EXPOSURE: a NZDUSD position is already open
- 10-21 09:45 USDCHF NO_TRADE: risk engine: currency_exposure (2 open positions share a currency, max 2): the model was not consulted
- 10-21 09:45 USDCAD NO_TRADE: risk engine: currency_exposure (2 open positions share a currency, max 2): the model was not consulted

## Open paper positions

| Symbol | Side | Qty | Entry | Stop | Target | P&L |
|---|---|---|---|---|---|---|
| AUDUSD | BUY | 4.04 | 0.7028599999999999 | 0.7019 | 0.7043 | $278.76 |
| NZDUSD | BUY | 0.91 | 0.568485 | 0.56737 | 0.56987 | $58.24 |

## Closed paper trades (latest 20)

| Closed | Symbol | Side | Net | R | Costs | Exit | Source | Rule |
|---|---|---|---|---|---|---|---|---|
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
| 10-20 00:08 | USDCHF | SELL | $105.23 | +0.21 | $94.45 | TIME | DUAL_AI | AGREE |
| 10-19 18:21 | USDCAD | SELL | $-389.37 | -0.78 | $87.65 | STOP | DUAL_AI | AGREE |
| 10-19 12:49 | EURGBP | SELL | $-218.72 | -0.88 | $33.09 | STOP | DUAL_AI | AGREE |

## Dual AI desk (two free OpenRouter traders; a trade only when they agree)

OpenRouter `READY` · key set · trader 1 `minimax/minimax-m3.1-flash:free` · trader 2 `nvidia/nemotron-3-ultra-550b-a55b:free` · debate `google/gemma-4-26b-a4b-it:free` · calls today 27/900

Agreement trades 71 (adequate) · wins 32 · losses 39 · net $206.38 · expectancy -0.033R · profit factor 1.02 · old DEBATE rule (stopped in dual-ai-1.2.0): 4 trade(s), net $-1,416.51, removed from the account

Disagreements (not traded; the debate runs in shadow): 90 · the debate's pick if taken: 85 resolved (adequate), expectancy -0.206R · the side it rejected if taken: 90 resolved (adequate), expectancy -0.244R

Exits in shadow (the same trades, followed again; measured, never traded): break-even at +1R -0.088R vs +0.015R as taken (54, adequate) · held 24 h +0.287R vs +0.089R as taken (47, adequate) · stop and target twice as far +0.263R vs +0.089R as taken (47, adequate) · closed at 8 h (the exit before dual-ai 1.7.0) none resolved yet

Trades taken by session (UTC): ASIA 31 resolved (adequate), expectancy +0.022R · LONDON 17 resolved (insufficient), expectancy +0.042R · OVERLAP 8 resolved (insufficient), expectancy -0.382R · NEW_YORK 12 resolved (insufficient), expectancy +0.257R · LATE 3 resolved (insufficient), expectancy -1.106R

| Time | Symbol | Trader 1 | Trader 2 | Debate (shadow) | Rule | Final | Risk |
|---|---|---|---|---|---|---|---|
| 10-21 11:00 | AUDUSD | -  | -  | - | NOT_ASKED | NO_TRADE | - |
| 10-21 11:00 | USDJPY | -  | -  | - | NOT_ASKED | NO_TRADE | - |
| 10-21 10:45 | GBPUSD | -  | -  | - | NOT_ASKED | NO_TRADE | - |
| 10-21 10:45 | EURUSD | -  | -  | - | NOT_ASKED | NO_TRADE | - |
| 10-21 10:32 | AUDJPY | BUY 61 | BUY 55 | - | AGREE | BUY | REJECTED |
| 10-21 10:30 | EURCHF | SELL 62 | SELL 63 | - | AGREE | SELL | REJECTED |
| 10-21 10:16 | GBPJPY | BUY 68 | BUY 62 | - | AGREE | BUY | REJECTED |
| 10-21 10:15 | EURJPY | SELL 62 | SELL 55 | - | AGREE | SELL | REJECTED |
| 10-21 10:00 | EURGBP | SELL 68 | SELL 62 | - | AGREE | SELL | REJECTED |
| 10-21 10:00 | NZDUSD | -  | -  | - | NOT_ASKED | NO_TRADE | - |
| 10-21 09:45 | USDCHF | -  | -  | - | NOT_ASKED | NO_TRADE | - |
| 10-21 09:45 | USDCAD | -  | -  | - | NOT_ASKED | NO_TRADE | - |

The chart Trader 1 read last: `last_chart.png`. (numbers): no free vision model answered, so Trader 1 read the same chart from its numbers.

Full figures: `paper_forward.json`. Rules: `docs/PAPER_FORWARD.md` on main.
