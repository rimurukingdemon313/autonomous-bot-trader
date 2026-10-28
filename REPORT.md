# PAPER FORWARD TEST — NOT REAL MONEY

Updated 2026-10-28 13:22 UTC · mode `PAPER_FORWARD` · profile `PAPER-FORWARD-200K` · shift started 2026-10-28 13:06 UTC · decision system `dual_ai`

Research status (historical, unchanged): **NO EDGE — DO NOT TRADE (historical research; this test measures forward)**. This run measures the system forward; it is not evidence of an edge until it has a sample and the forward-eligibility rules say so.

## The new account: the setup trading now (from 2026-10-26 16:22 UTC)

dual-ai 1.10.0 (a trade on Trader 1's levels) with both traders paid (paid-trial 1.2.0: Trader 1 xiaomi/mimo-v2.6-pro, Trader 2 anthropic/claude-haiku-5.5). Opened at the owner's request (2026-10-27): owner: a new account for the new setup, from the first shift that ran it; the account before it is kept and reported apart.

| Start | Equity | Total P&L | Closed | Open | Trades | Win rate | Expectancy | Profit factor |
|---|---|---|---|---|---|---|---|---|
| $200,000.00 | $198,994.93 | $-1,005.07 | $-783.73 | 1 ($-221.34) | 12 (insufficient) | 41.7% | -0.107R | 0.66 |

Before it, kept and apart (not in the figures above): 106 trades, net $-3,759.41. The whole paper journal, which the hard gate and the risk engine still guard, is under Paper account below; nothing in it was moved or removed.

## The rule that trades: a trade only when both AIs agree

| Trades | Wins | Losses | Win rate | Net P&L | Expectancy | Profit factor | Max drawdown |
|---|---|---|---|---|---|---|---|
| 118 (adequate) | 49 | 69 | 41.5% | $-4,543.14 | -0.089R | 0.80 | $7,819.04 |

The 4 trade(s) of the old DEBATE rule, stopped in dual-ai-1.2.0, were removed from the paper account at the operator's request: their net $-1,416.51 was put back by a declared adjustment ($1,416.51). They stay in the journal (append-only), in none of the account's figures below.

## Paper account

| Account | Equity | P&L today | Total P&L | Drawdown | Open | Trades | Win rate | Expectancy | Profit factor | Risk | Bot |
|---|---|---|---|---|---|---|---|---|---|---|---|
| $200,000.00 | $195,235.52 | $-1,684.94 | $-4,764.48 | $-4,764.48 | 1 | 118 (adequate) | 41.5% | -0.089R | 0.80 | ACTIVE | RUNNING |

Equity includes declared operator adjustments of $1,416.51 (without them: $193,819.00); P&L today excludes them. `remove-retired-debate-rule-trades-2026-10-15`: operator: the 4 trades of the retired debate rule (dual-ai 1.1.0, stopped in 1.2.0) are removed from the paper account; they stay in the journal.

## Who lost it: the market or us

Losses 69, $-23,199.86: **the market 69** (at the stop, within the plan 63, by the time exit 5, stopped beyond the plan (a gap or the spread at the stop) 1) · **us 0**. Every closed trade is checked: the rules and the gate approved it, its data and the fill's quote were fresh, it was sized within the per-trade risk, both traders chose its side, it closed on time and not over a weekend, its costs were as planned. A check that cannot be read counts as ours.

Beyond the plan, the market's: 10-21 21:05 GBPJPY BUY lost $644.82 against a planned $498.95 in the rollover.

The 4 trade(s) taken out of the account, checked the same way: 4 ours (DESK: not both traders' choice (rule DEBATE, traders ['BUY', 'SELL'])).

## Last decisions (decision → risk → paper execution)

- 10-28 11:30 EURGBP SELL: AI DECISION → RISK REJECTED — currency_conflict: SELL EURGBP would bet against an open position: GBPUSD SELL is short GBP; structure: H1 structure is range (mixed swings): no new position without a clear H1 trend (up HH+HL or down
- 10-28 11:30 NZDUSD SELL: AI DECISION → RISK REJECTED — structure: H1 structure is range (mixed swings): no new position without a clear H1 trend (up HH+HL or down LH+LL)
- 10-28 10:47 GBPUSD SELL: AI DECISION → RISK APPROVED → PAPER EXECUTED
- 10-28 10:32 AUDJPY SELL: AI DECISION → RISK APPROVED → PAPER EXECUTED
- 10-28 10:01 EURGBP BUY: AI DECISION → RISK REJECTED — currency_conflict: BUY EURGBP would bet against an open position: EURJPY SELL is short EUR; structure: H1 structure is range (mixed swings): no new position without a clear H1 trend (up HH+HL or down 
- 10-28 10:00 NZDUSD SELL: AI DECISION → RISK REJECTED — structure: H1 structure is range (mixed swings): no new position without a clear H1 trend (up HH+HL or down LH+LL)
- 10-28 09:46 USDCHF BUY: AI DECISION → RISK REJECTED — cost_to_risk: round-trip cost is 27.4% of the stop (max 25%): spread 0.00015 + commission and slippage; structure: H1 structure is range (mixed swings): no new position without a clear H1 trend (up HH
- 10-28 09:45 USDCAD BUY: AI DECISION → RISK REJECTED — cost_to_risk: round-trip cost is 29.1% of the stop (max 25%): spread 0.00015 + commission and slippage; structure: H1 structure is range (mixed swings): no new position without a clear H1 trend (up HH
- 10-28 09:32 AUDUSD BUY: AI DECISION → RISK REJECTED — quote: age 114s at opening (max 90s), bid 0.70355, ask 0.70365
- 10-28 09:15 GBPUSD SELL: AI DECISION → RISK REJECTED — currency_conflict: SELL GBPUSD would bet against an open position: EURGBP SELL is long GBP
- 10-28 08:45 EURJPY SELL: AI DECISION → RISK APPROVED → PAPER EXECUTED
- 10-28 08:30 NZDUSD SELL: AI DECISION → RISK REJECTED — cost_to_risk: round-trip cost is 25.9% of the stop (max 25%): spread 0.00015 + commission and slippage
- 10-28 08:17 USDCHF BUY: AI DECISION → RISK REJECTED — structure: H1 structure is range (mixed swings): no new position without a clear H1 trend (up HH+HL or down LH+LL)
- 10-28 08:00 USDJPY SELL: AI DECISION → RISK REJECTED — reward_risk: 1.19 vs minimum 1.2; currency_conflict: SELL USDJPY would bet against an open position: EURUSD SELL is long USD
- 10-28 07:45 GBPUSD SELL: AI DECISION → RISK REJECTED — currency_conflict: SELL GBPUSD would bet against an open position: EURGBP SELL is long GBP
- 10-28 07:15 NZDUSD SELL: AI DECISION → RISK REJECTED — quote: age 92s at opening (max 90s), bid 0.561425, ask 0.561575
- 10-28 06:30 EURUSD SELL: AI DECISION → RISK APPROVED → PAPER EXECUTED
- 10-28 06:16 AUDJPY SELL: AI DECISION → RISK REJECTED — reward_risk: 1.12 vs minimum 1.2; currency_conflict: SELL AUDJPY would bet against an open position: USDJPY BUY is short JPY
- 10-28 06:15 EURCHF BUY: AI DECISION → RISK REJECTED — currency_conflict: BUY EURCHF would bet against an open position: EURGBP SELL is short EUR
- 10-28 06:00 GBPJPY SELL: AI DECISION → RISK REJECTED — currency_conflict: SELL GBPJPY would bet against an open position: USDJPY BUY is short JPY; EURGBP SELL is long GBP

## Latest decisions, NO TRADE included (3189 so far)

- 10-28 13:15 GBPUSD NO_TRADE: blocked before consulting the model: EXPOSURE: a GBPUSD position is already open
- 10-28 13:15 EURUSD NO_TRADE: risk engine: trading_calendar (Wednesday 13:15 UTC: no new position from 12:00 to 16:00 UTC): the model was not consulted
- 10-28 13:00 EURGBP NO_TRADE: risk engine: trading_calendar (Wednesday 13:00 UTC: no new position from 12:00 to 16:00 UTC): the model was not consulted
- 10-28 13:00 NZDUSD NO_TRADE: risk engine: trading_calendar (Wednesday 13:00 UTC: no new position from 12:00 to 16:00 UTC): the model was not consulted
- 10-28 12:45 USDCHF NO_TRADE: risk engine: trading_calendar (Wednesday 12:45 UTC: no new position from 12:00 to 16:00 UTC): the model was not consulted
- 10-28 12:45 USDCAD NO_TRADE: risk engine: trading_calendar (Wednesday 12:45 UTC: no new position from 12:00 to 16:00 UTC): the model was not consulted
- 10-28 12:30 AUDUSD NO_TRADE: risk engine: trading_calendar (Wednesday 12:30 UTC: no new position from 12:00 to 16:00 UTC): the model was not consulted
- 10-28 12:30 USDJPY NO_TRADE: risk engine: trading_calendar (Wednesday 12:30 UTC: no new position from 12:00 to 16:00 UTC): the model was not consulted
- 10-28 12:15 GBPUSD NO_TRADE: blocked before consulting the model: EXPOSURE: a GBPUSD position is already open
- 10-28 12:15 EURUSD NO_TRADE: risk engine: trading_calendar (Wednesday 12:15 UTC: no new position from 12:00 to 16:00 UTC): the model was not consulted
- 10-28 12:00 AUDJPY NO_TRADE: risk engine: trading_calendar (Wednesday 12:00 UTC: no new position from 12:00 to 16:00 UTC): the model was not consulted
- 10-28 12:00 EURCHF NO_TRADE: risk engine: trading_calendar (Wednesday 12:00 UTC: no new position from 12:00 to 16:00 UTC): the model was not consulted

## Open paper positions

| Symbol | Side | Qty | Entry | Stop | Target | P&L |
|---|---|---|---|---|---|---|
| GBPUSD | SELL | 2.38 | 1.32793 | 1.32968 | 1.32561 | $-221.34 |

## Closed paper trades (latest 20)

| Closed | Symbol | Side | Net | R | Costs | Exit | Source | Rule | Lost to |
|---|---|---|---|---|---|---|---|---|---|
| 10-28 11:53 | EURJPY | SELL | $-440.02 | -0.90 | $42.86 | STOP | DUAL_AI | AGREE | the market |
| 10-28 11:26 | AUDJPY | SELL | $-417.29 | -0.85 | $77.22 | STOP | DUAL_AI | AGREE | the market |
| 10-28 09:43 | EURGBP | SELL | $-441.48 | -0.90 | $79.74 | STOP | DUAL_AI | AGREE | the market |
| 10-28 08:24 | EURUSD | SELL | $-418.52 | -0.85 | $74.12 | STOP | DUAL_AI | AGREE | the market |
| 10-28 07:01 | USDJPY | BUY | $144.06 | +0.29 | $47.06 | TIME | DUAL_AI | AGREE | - |
| 10-28 05:56 | EURUSD | SELL | $534.59 | +1.09 | $41.57 | TARGET | DUAL_AI | AGREE | - |
| 10-27 09:39 | EURCHF | SELL | $158.64 | +1.30 | $23.59 | TARGET | DUAL_AI | AGREE | - |
| 10-27 08:51 | EURUSD | SELL | $438.96 | +0.90 | $59.52 | TARGET | DUAL_AI | AGREE | - |
| 10-27 06:30 | EURJPY | SELL | $-98.35 | -0.81 | $17.00 | STOP | DUAL_AI | AGREE | the market |
| 10-27 06:15 | USDJPY | SELL | $-418.51 | -0.85 | $50.09 | STOP | DUAL_AI | AGREE | the market |
| 10-27 05:23 | GBPUSD | SELL | $278.49 | +1.14 | $38.75 | TARGET | DUAL_AI | AGREE | - |
| 10-27 01:27 | AUDJPY | SELL | $-104.31 | -0.86 | $25.69 | STOP | DUAL_AI | AGREE | the market |
| 10-26 17:23 | USDCHF | BUY | $-207.12 | -0.85 | $38.59 | STOP | DUAL_AI | AGREE | the market |
| 10-26 13:06 | USDCAD | SELL | $-407.76 | -0.82 | $73.23 | STOP | DUAL_AI | AGREE | the market |
| 10-26 12:54 | EURGBP | BUY | $-420.89 | -0.85 | $86.86 | STOP | DUAL_AI | AGREE | the market |
| 10-26 12:55 | EURCHF | BUY | $-410.98 | -0.83 | $77.46 | STOP | DUAL_AI | AGREE | the market |
| 10-26 10:45 | GBPJPY | SELL | $-395.13 | -0.80 | $70.90 | STOP | DUAL_AI | AGREE | the market |
| 10-26 09:11 | AUDUSD | SELL | $-473.61 | -0.96 | $80.56 | STOP | DUAL_AI | AGREE | the market |
| 10-26 07:44 | USDCHF | BUY | $582.71 | +1.18 | $82.56 | TARGET | DUAL_AI | AGREE | - |
| 10-23 20:03 | EURUSD | SELL | $37.41 | +0.31 | $14.79 | TIME | DUAL_AI | AGREE | - |

## Dual AI desk (two OpenRouter traders: free, or the paid trial while it runs; a trade only when they agree)

OpenRouter `CATALOG_NOT_READ_YET` · key set · trader 1 `None` · trader 2 `None` · debate `None` · calls today 0/900

Paid trial `paid-trial-2026-10-26` (2026-10-23T14:00:00Z to 2026-10-31T00:00:00Z): ACTIVE · trader 1 `xiaomi/mimo-v2.6-pro` asked first · trader 2 `anthropic/claude-haiku-5.5` asked first · spent n/a of $9.00, today n/a of $1.80 (the key's own reading)

Agreement trades 118 (adequate) · wins 49 · losses 69 · net $-4,543.14 · expectancy -0.089R · profit factor 0.80 · old DEBATE rule (stopped in dual-ai-1.2.0): 4 trade(s), net $-1,416.51, removed from the account

Disagreements (not traded; the debate runs in shadow): 132 · the debate's pick if taken: 117 resolved (adequate), expectancy -0.146R · the side it rejected if taken: 122 resolved (adequate), expectancy -0.218R

Exits in shadow (the same trades, followed again; measured, never traded): break-even at +1R -0.132R vs -0.087R as taken (102, adequate) · held 24 h -0.014R vs -0.087R as taken (102, adequate) · stop and target twice as far +0.023R vs -0.087R as taken (102, adequate) · closed at 8 h (the exit before dual-ai 1.7.0) -0.239R vs -0.202R as taken (48, adequate)

Trader 2's own levels in shadow (a trade is on Trader 1's since dual-ai 1.10.0; measured, never traded): +0.484R vs +0.309R as taken (10, insufficient)

Trades taken by session (UTC): ASIA 51 resolved (adequate), expectancy -0.216R · LONDON 36 resolved (adequate), expectancy +0.063R · OVERLAP 8 resolved (insufficient), expectancy -0.382R · NEW_YORK 21 resolved (insufficient), expectancy +0.168R · LATE 3 resolved (insufficient), expectancy -1.106R

| Time | Symbol | Trader 1 | Trader 2 | Debate (shadow) | Rule | Final | Risk |
|---|---|---|---|---|---|---|---|
| 10-28 13:15 | GBPUSD | -  | -  | - | NOT_ASKED | NO_TRADE | - |
| 10-28 13:15 | EURUSD | -  | -  | - | NOT_ASKED | NO_TRADE | - |
| 10-28 13:00 | EURGBP | -  | -  | - | NOT_ASKED | NO_TRADE | - |
| 10-28 13:00 | NZDUSD | -  | -  | - | NOT_ASKED | NO_TRADE | - |
| 10-28 12:45 | USDCHF | -  | -  | - | NOT_ASKED | NO_TRADE | - |
| 10-28 12:45 | USDCAD | -  | -  | - | NOT_ASKED | NO_TRADE | - |
| 10-28 12:30 | AUDUSD | -  | -  | - | NOT_ASKED | NO_TRADE | - |
| 10-28 12:30 | USDJPY | -  | -  | - | NOT_ASKED | NO_TRADE | - |
| 10-28 12:15 | GBPUSD | -  | -  | - | NOT_ASKED | NO_TRADE | - |
| 10-28 12:15 | EURUSD | -  | -  | - | NOT_ASKED | NO_TRADE | - |
| 10-28 12:00 | AUDJPY | -  | -  | - | NOT_ASKED | NO_TRADE | - |
| 10-28 12:00 | EURCHF | -  | -  | - | NOT_ASKED | NO_TRADE | - |

The chart Trader 1 read last: `last_chart.png`. (numbers): no free vision model answered, so Trader 1 read the same chart from its numbers.

Full figures: `paper_forward.json`. Rules: `docs/PAPER_FORWARD.md` on main.
