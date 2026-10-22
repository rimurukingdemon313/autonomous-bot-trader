# PAPER FORWARD TEST — NOT REAL MONEY

Updated 2026-10-22 23:07 UTC · mode `PAPER_FORWARD` · profile `PAPER-FORWARD-200K` · shift started 2026-10-22 22:52 UTC · decision system `dual_ai`

Research status (historical, unchanged): **NO EDGE — DO NOT TRADE (historical research; this test measures forward)**. This run measures the system forward; it is not evidence of an edge until it has a sample and the forward-eligibility rules say so.

## The rule that trades: a trade only when both AIs agree

| Trades | Wins | Losses | Win rate | Net P&L | Expectancy | Profit factor | Max drawdown |
|---|---|---|---|---|---|---|---|
| 89 (adequate) | 40 | 49 | 44.9% | $-126.94 | -0.020R | 0.99 | $4,943.76 |

The 4 trade(s) of the old DEBATE rule, stopped in dual-ai-1.2.0, were removed from the paper account at the operator's request: their net $-1,416.51 was put back by a declared adjustment ($1,416.51). They stay in the journal (append-only), in none of the account's figures below.

## Paper account

| Account | Equity | P&L today | Total P&L | Drawdown | Open | Trades | Win rate | Expectancy | Profit factor | Risk | Bot |
|---|---|---|---|---|---|---|---|---|---|---|---|
| $200,000.00 | $199,873.06 | $202.80 | $-126.94 | $-126.94 | 0 | 89 (adequate) | 44.9% | -0.020R | 0.99 | ACTIVE | RUNNING |

Equity includes declared operator adjustments of $1,416.51 (without them: $198,456.55); P&L today excludes them. `remove-retired-debate-rule-trades-2026-10-15`: operator: the 4 trades of the retired debate rule (dual-ai 1.1.0, stopped in 1.2.0) are removed from the paper account; they stay in the journal.

## Last decisions (decision → risk → paper execution)

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
- 10-22 09:15 EURUSD SELL: AI DECISION → RISK APPROVED → PAPER EXECUTED
- 10-22 09:03 AUDJPY SELL: AI DECISION → RISK APPROVED → PAPER EXECUTED
- 10-22 09:00 EURCHF SELL: AI DECISION → RISK REJECTED — reward_risk: 0.88 vs minimum 1.2; structure: H1 structure is range (mixed swings): no new position without a clear H1 trend (up HH+HL or down LH+LL)
- 10-22 08:48 GBPJPY SELL: AI DECISION → RISK REJECTED — reward_risk: 1.08 vs minimum 1.2; currency_conflict: SELL GBPJPY would bet against an open position: EURGBP SELL is long GBP

## Latest decisions, NO TRADE included (2124 so far)

- 10-22 23:00 GBPUSD NO_TRADE: blocked before consulting the model: DATA_QUALITY: latest bar closed 120 minutes ago; STALE_DATA: last closed bar is 120 minutes old [data: latest bar closed 120 minutes ago]
- 10-22 23:00 EURUSD NO_TRADE: blocked before consulting the model: DATA_QUALITY: latest bar closed 120 minutes ago; STALE_DATA: last closed bar is 120 minutes old [data: latest bar closed 120 minutes ago]
- 10-22 22:45 EURGBP NO_TRADE: risk engine: quiet_hours (18:45 New York: no new position from 16:00 to 20:00 New York (the rollover to the Tokyo open: the thinnest liquidity of the day)): the model was not consulted
- 10-22 22:45 NZDUSD NO_TRADE: risk engine: quiet_hours (18:45 New York: no new position from 16:00 to 20:00 New York (the rollover to the Tokyo open: the thinnest liquidity of the day)): the model was not consulted
- 10-22 22:30 USDCHF NO_TRADE: risk engine: quiet_hours (18:30 New York: no new position from 16:00 to 20:00 New York (the rollover to the Tokyo open: the thinnest liquidity of the day)): the model was not consulted
- 10-22 22:30 USDCAD NO_TRADE: risk engine: quiet_hours (18:30 New York: no new position from 16:00 to 20:00 New York (the rollover to the Tokyo open: the thinnest liquidity of the day)): the model was not consulted
- 10-22 22:15 AUDUSD NO_TRADE: risk engine: quiet_hours (18:15 New York: no new position from 16:00 to 20:00 New York (the rollover to the Tokyo open: the thinnest liquidity of the day)): the model was not consulted
- 10-22 22:15 USDJPY NO_TRADE: blocked before consulting the model: EXPOSURE: a USDJPY position is already open
- 10-22 22:00 GBPUSD NO_TRADE: risk engine: quiet_hours (18:00 New York: no new position from 16:00 to 20:00 New York (the rollover to the Tokyo open: the thinnest liquidity of the day)): the model was not consulted
- 10-22 22:00 EURUSD NO_TRADE: risk engine: quiet_hours (18:00 New York: no new position from 16:00 to 20:00 New York (the rollover to the Tokyo open: the thinnest liquidity of the day)): the model was not consulted
- 10-22 21:45 AUDJPY NO_TRADE: risk engine: quiet_hours (17:45 New York: no new position from 16:00 to 20:00 New York (the rollover to the Tokyo open: the thinnest liquidity of the day)): the model was not consulted
- 10-22 21:45 EURCHF NO_TRADE: risk engine: quiet_hours (17:45 New York: no new position from 16:00 to 20:00 New York (the rollover to the Tokyo open: the thinnest liquidity of the day)): the model was not consulted

## Open paper positions

| Symbol | Side | Qty | Entry | Stop | Target | P&L |
|---|---|---|---|---|---|---|

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

OpenRouter `CATALOG_NOT_READ_YET` · key set · trader 1 `None` · trader 2 `None` · debate `None` · calls today 0/900

Agreement trades 89 (adequate) · wins 40 · losses 49 · net $-126.94 · expectancy -0.020R · profit factor 0.99 · old DEBATE rule (stopped in dual-ai-1.2.0): 4 trade(s), net $-1,416.51, removed from the account

Disagreements (not traded; the debate runs in shadow): 101 · the debate's pick if taken: 90 resolved (adequate), expectancy -0.231R · the side it rejected if taken: 95 resolved (adequate), expectancy -0.211R

Exits in shadow (the same trades, followed again; measured, never traded): break-even at +1R -0.083R vs -0.010R as taken (62, adequate) · held 24 h +0.150R vs -0.010R as taken (62, adequate) · stop and target twice as far +0.056R vs -0.010R as taken (62, adequate) · closed at 8 h (the exit before dual-ai 1.7.0) -0.286R vs -0.173R as taken (8, insufficient)

Trades taken by session (UTC): ASIA 34 resolved (adequate), expectancy -0.003R · LONDON 20 resolved (insufficient), expectancy -0.013R · OVERLAP 8 resolved (insufficient), expectancy -0.382R · NEW_YORK 14 resolved (insufficient), expectancy +0.248R · LATE 3 resolved (insufficient), expectancy -1.106R

| Time | Symbol | Trader 1 | Trader 2 | Debate (shadow) | Rule | Final | Risk |
|---|---|---|---|---|---|---|---|
| 10-22 23:00 | GBPUSD | -  | -  | - | NOT_ASKED | NO_TRADE | - |
| 10-22 23:00 | EURUSD | -  | -  | - | NOT_ASKED | NO_TRADE | - |
| 10-22 22:45 | EURGBP | -  | -  | - | NOT_ASKED | NO_TRADE | - |
| 10-22 22:45 | NZDUSD | -  | -  | - | NOT_ASKED | NO_TRADE | - |
| 10-22 22:30 | USDCHF | -  | -  | - | NOT_ASKED | NO_TRADE | - |
| 10-22 22:30 | USDCAD | -  | -  | - | NOT_ASKED | NO_TRADE | - |
| 10-22 22:15 | AUDUSD | -  | -  | - | NOT_ASKED | NO_TRADE | - |
| 10-22 22:15 | USDJPY | -  | -  | - | NOT_ASKED | NO_TRADE | - |
| 10-22 22:00 | GBPUSD | -  | -  | - | NOT_ASKED | NO_TRADE | - |
| 10-22 22:00 | EURUSD | -  | -  | - | NOT_ASKED | NO_TRADE | - |
| 10-22 21:45 | AUDJPY | -  | -  | - | NOT_ASKED | NO_TRADE | - |
| 10-22 21:45 | EURCHF | -  | -  | - | NOT_ASKED | NO_TRADE | - |

The chart Trader 1 read last: `last_chart.png`. (numbers): no free vision model answered, so Trader 1 read the same chart from its numbers.

Full figures: `paper_forward.json`. Rules: `docs/PAPER_FORWARD.md` on main.
