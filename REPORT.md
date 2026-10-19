# PAPER FORWARD TEST — NOT REAL MONEY

Updated 2026-10-19 23:41 UTC · mode `PAPER_FORWARD` · profile `PAPER-FORWARD-200K` · shift started 2026-10-19 22:10 UTC · decision system `dual_ai`

Research status (historical, unchanged): **NO EDGE — DO NOT TRADE (historical research; this test measures forward)**. This run measures the system forward; it is not evidence of an edge until it has a sample and the forward-eligibility rules say so.

## The rule that trades: a trade only when both AIs agree

| Trades | Wins | Losses | Win rate | Net P&L | Expectancy | Profit factor | Max drawdown |
|---|---|---|---|---|---|---|---|
| 53 (adequate) | 24 | 29 | 45.3% | $-211.16 | -0.033R | 0.98 | $3,487.06 |

The 4 trade(s) of the old DEBATE rule, stopped in dual-ai-1.2.0, were removed from the paper account at the operator's request: their net $-1,416.51 was put back by a declared adjustment ($1,416.51). They stay in the journal (append-only), in none of the account's figures below.

## Paper account

| Account | Equity | P&L today | Total P&L | Drawdown | Open | Trades | Win rate | Expectancy | Profit factor | Risk | Bot |
|---|---|---|---|---|---|---|---|---|---|---|---|
| $200,000.00 | $199,797.17 | $-101.35 | $-202.83 | $-202.83 | 2 | 53 (adequate) | 45.3% | -0.033R | 0.98 | ACTIVE | RUNNING |

Equity includes declared operator adjustments of $1,416.51 (without them: $198,380.65); P&L today excludes them. `remove-retired-debate-rule-trades-2026-10-15`: operator: the 4 trades of the retired debate rule (dual-ai 1.1.0, stopped in 1.2.0) are removed from the paper account; they stay in the journal.

## Last decisions (decision → risk → paper execution)

- 10-19 19:36 AUDJPY BUY: AI DECISION → RISK REJECTED — reward_risk: 1.17 vs minimum 1.2
- 10-19 19:00 NZDUSD BUY: AI DECISION → RISK APPROVED → PAPER EXECUTED
- 10-19 18:45 USDCAD SELL: AI DECISION → RISK REJECTED — reward_risk: 1.02 vs minimum 1.2
- 10-19 18:34 AUDUSD SELL: AI DECISION → RISK REJECTED — reward_risk: 1.17 vs minimum 1.2; currency_conflict: SELL AUDUSD would bet against an open position: USDCHF SELL is short USD
- 10-19 18:30 USDJPY BUY: AI DECISION → RISK REJECTED — currency_conflict: BUY USDJPY would bet against an open position: USDCHF SELL is short USD
- 10-19 17:15 USDCAD SELL: AI DECISION → RISK APPROVED → PAPER EXECUTED
- 10-19 17:06 AUDUSD SELL: AI DECISION → RISK REJECTED — currency_conflict: SELL AUDUSD would bet against an open position: USDCHF SELL is short USD
- 10-19 16:53 GBPUSD SELL: AI DECISION → RISK REJECTED — currency_conflict: SELL GBPUSD would bet against an open position: USDCHF SELL is short USD; structure: H1 structure is range (mixed swings): no new position without a clear H1 trend (up HH+HL or down
- 10-19 16:15 EURGBP SELL: AI DECISION → RISK REJECTED — cost_to_risk: round-trip cost is 28.4% of the stop (max 25%): spread 0.00012 + commission and slippage
- 10-19 16:15 NZDUSD SELL: AI DECISION → RISK REJECTED — currency_conflict: SELL NZDUSD would bet against an open position: USDCHF SELL is short USD
- 10-19 16:00 USDCHF SELL: AI DECISION → RISK APPROVED → PAPER EXECUTED
- 10-19 16:00 USDCAD SELL: AI DECISION → RISK REJECTED — cost_to_risk: round-trip cost is 27.4% of the stop (max 25%): spread 0.00015 + commission and slippage
- 10-19 11:45 NZDUSD BUY: AI DECISION → RISK REJECTED — reward_risk: 1.18 vs minimum 1.2
- 10-19 10:30 USDCHF SELL: AI DECISION → RISK APPROVED → PAPER EXECUTED
- 10-19 09:15 EURGBP SELL: AI DECISION → RISK APPROVED → PAPER EXECUTED
- 10-19 09:00 USDCAD SELL: AI DECISION → RISK APPROVED → PAPER EXECUTED
- 10-19 08:45 USDJPY SELL: AI DECISION → RISK APPROVED → PAPER EXECUTED
- 10-19 08:30 EURUSD SELL: AI DECISION → RISK APPROVED → PAPER EXECUTED
- 10-19 08:15 AUDJPY SELL: AI DECISION → RISK REJECTED — cost_to_risk: round-trip cost is 30.3% of the stop (max 25%): spread 0.018 + commission and slippage
- 10-19 08:15 EURCHF SELL: AI DECISION → RISK APPROVED → PAPER EXECUTED

## Latest decisions, NO TRADE included (1574 so far)

- 10-19 23:30 AUDJPY NO_TRADE: blocked before consulting the model: DATA_QUALITY: latest bar closed 270 minutes ago; STALE_DATA: last closed bar is 270 minutes old [data: latest bar closed 270 minutes ago]
- 10-19 23:30 EURCHF NO_TRADE: blocked before consulting the model: DATA_QUALITY: latest bar closed 270 minutes ago; STALE_DATA: last closed bar is 270 minutes old [data: latest bar closed 270 minutes ago]
- 10-19 23:15 GBPJPY NO_TRADE: blocked before consulting the model: DATA_QUALITY: latest bar closed 255 minutes ago; STALE_DATA: last closed bar is 255 minutes old [data: latest bar closed 255 minutes ago]
- 10-19 23:15 EURJPY NO_TRADE: blocked before consulting the model: DATA_QUALITY: latest bar closed 255 minutes ago; STALE_DATA: last closed bar is 255 minutes old [data: latest bar closed 255 minutes ago]
- 10-19 23:00 EURGBP NO_TRADE: blocked before consulting the model: DATA_QUALITY: latest bar closed 240 minutes ago; STALE_DATA: last closed bar is 240 minutes old [data: latest bar closed 240 minutes ago]
- 10-19 23:00 NZDUSD NO_TRADE: blocked before consulting the model: DATA_QUALITY: latest bar closed 240 minutes ago; STALE_DATA: last closed bar is 240 minutes old; EXPOSURE: a NZDUSD position is already open [data: latest bar closed 240 minutes ago]
- 10-19 22:45 USDCHF NO_TRADE: blocked before consulting the model: EXPOSURE: a USDCHF position is already open
- 10-19 22:45 USDCAD NO_TRADE: risk engine: quiet_hours (18:45 New York: no new position from 16:00 to 20:00 New York (the rollover to the Tokyo open: the thinnest liquidity of the day)); currency_exposure (2 open positions share a
- 10-19 22:30 AUDUSD NO_TRADE: risk engine: quiet_hours (18:30 New York: no new position from 16:00 to 20:00 New York (the rollover to the Tokyo open: the thinnest liquidity of the day)); currency_exposure (2 open positions share a
- 10-19 22:30 USDJPY NO_TRADE: risk engine: quiet_hours (18:30 New York: no new position from 16:00 to 20:00 New York (the rollover to the Tokyo open: the thinnest liquidity of the day)); currency_exposure (2 open positions share a
- 10-19 22:15 GBPUSD NO_TRADE: risk engine: quiet_hours (18:15 New York: no new position from 16:00 to 20:00 New York (the rollover to the Tokyo open: the thinnest liquidity of the day)); currency_exposure (2 open positions share a
- 10-19 22:15 EURUSD NO_TRADE: risk engine: quiet_hours (18:15 New York: no new position from 16:00 to 20:00 New York (the rollover to the Tokyo open: the thinnest liquidity of the day)); currency_exposure (2 open positions share a

## Open paper positions

| Symbol | Side | Qty | Entry | Stop | Target | P&L |
|---|---|---|---|---|---|---|
| NZDUSD | BUY | 2.02 | 0.566385 | 0.5654 | 0.5676 | $28.28 |
| USDCHF | SELL | 2.75 | 0.826815 | 0.828 | 0.82399 | $-19.96 |

## Closed paper trades (latest 20)

| Closed | Symbol | Side | Net | R | Costs | Exit | Source | Rule |
|---|---|---|---|---|---|---|---|---|
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
| 10-16 07:02 | AUDUSD | BUY | $840.45 | +1.68 | $77.58 | TARGET | DUAL_AI | AGREE |
| 10-16 03:49 | USDCAD | SELL | $451.28 | +0.91 | $77.18 | TARGET | DUAL_AI | AGREE |

## Dual AI desk (two free OpenRouter traders; a trade only when they agree)

OpenRouter `CATALOG_NOT_READ_YET` · key set · trader 1 `None` · trader 2 `None` · debate `None` · calls today 0/900

Agreement trades 53 (adequate) · wins 24 · losses 29 · net $-211.16 · expectancy -0.033R · profit factor 0.98 · old DEBATE rule (stopped in dual-ai-1.2.0): 4 trade(s), net $-1,416.51, removed from the account

Disagreements (not traded; the debate runs in shadow): 87 · the debate's pick if taken: 70 resolved (adequate), expectancy -0.182R · the side it rejected if taken: 75 resolved (adequate), expectancy -0.195R

Exits in shadow (the same trades, followed again; measured, never traded): break-even at +1R -0.068R vs +0.050R as taken (38, adequate) · held 24 h +0.512R vs +0.300R as taken (28, insufficient) · stop and target twice as far +0.190R vs +0.300R as taken (28, insufficient)

Trades taken by session (UTC): ASIA 24 resolved (insufficient), expectancy +0.083R · LONDON 14 resolved (insufficient), expectancy -0.082R · OVERLAP 8 resolved (insufficient), expectancy -0.382R · NEW_YORK 6 resolved (insufficient), expectancy +0.792R · LATE 3 resolved (insufficient), expectancy -1.106R

| Time | Symbol | Trader 1 | Trader 2 | Debate (shadow) | Rule | Final | Risk |
|---|---|---|---|---|---|---|---|
| 10-19 23:30 | AUDJPY | -  | -  | - | NOT_ASKED | NO_TRADE | - |
| 10-19 23:30 | EURCHF | -  | -  | - | NOT_ASKED | NO_TRADE | - |
| 10-19 23:15 | GBPJPY | -  | -  | - | NOT_ASKED | NO_TRADE | - |
| 10-19 23:15 | EURJPY | -  | -  | - | NOT_ASKED | NO_TRADE | - |
| 10-19 23:00 | EURGBP | -  | -  | - | NOT_ASKED | NO_TRADE | - |
| 10-19 23:00 | NZDUSD | -  | -  | - | NOT_ASKED | NO_TRADE | - |
| 10-19 22:45 | USDCHF | -  | -  | - | NOT_ASKED | NO_TRADE | - |
| 10-19 22:45 | USDCAD | -  | -  | - | NOT_ASKED | NO_TRADE | - |
| 10-19 22:30 | AUDUSD | -  | -  | - | NOT_ASKED | NO_TRADE | - |
| 10-19 22:30 | USDJPY | -  | -  | - | NOT_ASKED | NO_TRADE | - |
| 10-19 22:15 | GBPUSD | -  | -  | - | NOT_ASKED | NO_TRADE | - |
| 10-19 22:15 | EURUSD | -  | -  | - | NOT_ASKED | NO_TRADE | - |

The chart Trader 1 read last: `last_chart.png`. (numbers): no free vision model answered, so Trader 1 read the same chart from its numbers.

Full figures: `paper_forward.json`. Rules: `docs/PAPER_FORWARD.md` on main.
