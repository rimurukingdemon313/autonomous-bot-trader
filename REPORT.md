# PAPER FORWARD TEST — NOT REAL MONEY

Updated 2026-10-21 23:55 UTC · mode `PAPER_FORWARD` · profile `PAPER-FORWARD-200K` · shift started 2026-10-21 18:54 UTC · decision system `dual_ai`

Research status (historical, unchanged): **NO EDGE — DO NOT TRADE (historical research; this test measures forward)**. This run measures the system forward; it is not evidence of an edge until it has a sample and the forward-eligibility rules say so.

## The rule that trades: a trade only when both AIs agree

| Trades | Wins | Losses | Win rate | Net P&L | Expectancy | Profit factor | Max drawdown |
|---|---|---|---|---|---|---|---|
| 73 (adequate) | 33 | 40 | 45.2% | $-318.78 | -0.037R | 0.97 | $3,637.77 |

The 4 trade(s) of the old DEBATE rule, stopped in dual-ai-1.2.0, were removed from the paper account at the operator's request: their net $-1,416.51 was put back by a declared adjustment ($1,416.51). They stay in the journal (append-only), in none of the account's figures below.

## Paper account

| Account | Equity | P&L today | Total P&L | Drawdown | Open | Trades | Win rate | Expectancy | Profit factor | Risk | Bot |
|---|---|---|---|---|---|---|---|---|---|---|---|
| $200,000.00 | $199,784.27 | $-73.95 | $-215.73 | $-215.73 | 2 | 73 (adequate) | 45.2% | -0.037R | 0.97 | ACTIVE | RUNNING |

Equity includes declared operator adjustments of $1,416.51 (without them: $198,367.75); P&L today excludes them. `remove-retired-debate-rule-trades-2026-10-15`: operator: the 4 trades of the retired debate rule (dual-ai 1.1.0, stopped in 1.2.0) are removed from the paper account; they stay in the journal.

## Last decisions (decision → risk → paper execution)

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
- 10-21 02:45 USDCAD SELL: AI DECISION → RISK APPROVED → PAPER EXECUTED

## Latest decisions, NO TRADE included (1960 so far)

- 10-21 23:45 AUDUSD NO_TRADE: blocked before consulting the model: DATA_QUALITY: latest bar closed 225 minutes ago; STALE_DATA: last closed bar is 225 minutes old; EXPOSURE: a AUDUSD position is already open [data: latest bar closed 225 minutes ago]
- 10-21 23:45 USDJPY NO_TRADE: blocked before consulting the model: DATA_QUALITY: latest bar closed 225 minutes ago; STALE_DATA: last closed bar is 225 minutes old [data: latest bar closed 225 minutes ago]
- 10-21 23:30 GBPUSD NO_TRADE: blocked before consulting the model: DATA_QUALITY: latest bar closed 210 minutes ago; STALE_DATA: last closed bar is 210 minutes old [data: latest bar closed 210 minutes ago]
- 10-21 23:30 EURUSD NO_TRADE: blocked before consulting the model: DATA_QUALITY: latest bar closed 210 minutes ago; STALE_DATA: last closed bar is 210 minutes old [data: latest bar closed 210 minutes ago]
- 10-21 23:15 AUDJPY NO_TRADE: blocked before consulting the model: DATA_QUALITY: latest bar closed 195 minutes ago; STALE_DATA: quote is 246s old; STALE_DATA: last closed bar is 195 minutes old [data: latest bar closed 195 minutes ago]
- 10-21 23:15 EURCHF NO_TRADE: blocked before consulting the model: DATA_QUALITY: latest bar closed 195 minutes ago; STALE_DATA: quote is 245s old; STALE_DATA: last closed bar is 195 minutes old [data: latest bar closed 195 minutes ago]
- 10-21 23:00 GBPJPY NO_TRADE: blocked before consulting the model: DATA_QUALITY: latest bar closed 180 minutes ago; STALE_DATA: last closed bar is 180 minutes old [data: latest bar closed 180 minutes ago]
- 10-21 23:00 EURJPY NO_TRADE: blocked before consulting the model: DATA_QUALITY: latest bar closed 180 minutes ago; STALE_DATA: last closed bar is 180 minutes old [data: latest bar closed 180 minutes ago]
- 10-21 22:45 EURGBP NO_TRADE: risk engine: quiet_hours (18:45 New York: no new position from 16:00 to 20:00 New York (the rollover to the Tokyo open: the thinnest liquidity of the day)): the model was not consulted
- 10-21 22:45 NZDUSD NO_TRADE: risk engine: quiet_hours (18:45 New York: no new position from 16:00 to 20:00 New York (the rollover to the Tokyo open: the thinnest liquidity of the day)); currency_exposure (2 open positions share a
- 10-21 22:30 USDCHF NO_TRADE: blocked before consulting the model: EXPOSURE: a USDCHF position is already open
- 10-21 22:30 USDCAD NO_TRADE: risk engine: quiet_hours (18:30 New York: no new position from 16:00 to 20:00 New York (the rollover to the Tokyo open: the thinnest liquidity of the day)); currency_exposure (2 open positions share a

## Open paper positions

| Symbol | Side | Qty | Entry | Stop | Target | P&L |
|---|---|---|---|---|---|---|
| USDCHF | SELL | 2.29 | 0.824415 | 0.82592 | 0.8222 | $66.69 |
| AUDUSD | BUY | 4.04 | 0.7028599999999999 | 0.7019 | 0.7043 | $36.36 |

## Closed paper trades (latest 20)

| Closed | Symbol | Side | Net | R | Costs | Exit | Source | Rule |
|---|---|---|---|---|---|---|---|---|
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
| 10-20 00:08 | USDCHF | SELL | $105.23 | +0.21 | $94.45 | TIME | DUAL_AI | AGREE |

## Dual AI desk (two free OpenRouter traders; a trade only when they agree)

OpenRouter `CATALOG_NOT_READ_YET` · key set · trader 1 `None` · trader 2 `None` · debate `None` · calls today 0/900

Agreement trades 73 (adequate) · wins 33 · losses 40 · net $-318.78 · expectancy -0.037R · profit factor 0.97 · old DEBATE rule (stopped in dual-ai-1.2.0): 4 trade(s), net $-1,416.51, removed from the account

Disagreements (not traded; the debate runs in shadow): 93 · the debate's pick if taken: 85 resolved (adequate), expectancy -0.206R · the side it rejected if taken: 90 resolved (adequate), expectancy -0.244R

Exits in shadow (the same trades, followed again; measured, never traded): break-even at +1R -0.088R vs +0.015R as taken (54, adequate) · held 24 h +0.272R vs +0.078R as taken (51, adequate) · stop and target twice as far +0.194R vs +0.078R as taken (51, adequate) · closed at 8 h (the exit before dual-ai 1.7.0) none resolved yet

Trades taken by session (UTC): ASIA 31 resolved (adequate), expectancy +0.022R · LONDON 17 resolved (insufficient), expectancy +0.042R · OVERLAP 8 resolved (insufficient), expectancy -0.382R · NEW_YORK 12 resolved (insufficient), expectancy +0.257R · LATE 3 resolved (insufficient), expectancy -1.106R

| Time | Symbol | Trader 1 | Trader 2 | Debate (shadow) | Rule | Final | Risk |
|---|---|---|---|---|---|---|---|
| 10-21 23:45 | AUDUSD | -  | -  | - | NOT_ASKED | NO_TRADE | - |
| 10-21 23:45 | USDJPY | -  | -  | - | NOT_ASKED | NO_TRADE | - |
| 10-21 23:30 | GBPUSD | -  | -  | - | NOT_ASKED | NO_TRADE | - |
| 10-21 23:30 | EURUSD | -  | -  | - | NOT_ASKED | NO_TRADE | - |
| 10-21 23:15 | AUDJPY | -  | -  | - | NOT_ASKED | NO_TRADE | - |
| 10-21 23:15 | EURCHF | -  | -  | - | NOT_ASKED | NO_TRADE | - |
| 10-21 23:00 | GBPJPY | -  | -  | - | NOT_ASKED | NO_TRADE | - |
| 10-21 23:00 | EURJPY | -  | -  | - | NOT_ASKED | NO_TRADE | - |
| 10-21 22:45 | EURGBP | -  | -  | - | NOT_ASKED | NO_TRADE | - |
| 10-21 22:45 | NZDUSD | -  | -  | - | NOT_ASKED | NO_TRADE | - |
| 10-21 22:30 | USDCHF | -  | -  | - | NOT_ASKED | NO_TRADE | - |
| 10-21 22:30 | USDCAD | -  | -  | - | NOT_ASKED | NO_TRADE | - |

The chart Trader 1 read last: `last_chart.png`. (numbers): no free vision model answered, so Trader 1 read the same chart from its numbers.

Full figures: `paper_forward.json`. Rules: `docs/PAPER_FORWARD.md` on main.
