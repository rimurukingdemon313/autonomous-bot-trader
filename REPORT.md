# PAPER FORWARD TEST — NOT REAL MONEY

Updated 2026-10-28 22:43 UTC · mode `PAPER_FORWARD` · profile `PAPER-FORWARD-200K` · shift started 2026-10-28 18:42 UTC · decision system `dual_ai`

Research status (historical, unchanged): **NO EDGE — DO NOT TRADE (historical research; this test measures forward)**. This run measures the system forward; it is not evidence of an edge until it has a sample and the forward-eligibility rules say so.

## The new account: the setup trading now (from 2026-10-26 16:22 UTC)

dual-ai 1.10.0 (a trade on Trader 1's levels) with both traders paid (paid-trial 1.2.0: Trader 1 xiaomi/mimo-v2.6-pro, Trader 2 anthropic/claude-haiku-5.5). Opened at the owner's request (2026-10-27): owner: a new account for the new setup, from the first shift that ran it; the account before it is kept and reported apart.

| Start | Equity | Total P&L | Closed | Open | Trades | Win rate | Expectancy | Profit factor |
|---|---|---|---|---|---|---|---|---|
| $200,000.00 | $198,735.79 | $-1,264.21 | $-1,493.67 | 3 ($229.46) | 14 (insufficient) | 35.7% | -0.225R | 0.51 |

Before it, kept and apart (not in the figures above): 106 trades, net $-3,759.41. The whole paper journal, which the hard gate and the risk engine still guard, is under Paper account below; nothing in it was moved or removed.

## The rule that trades: a trade only when both AIs agree

| Trades | Wins | Losses | Win rate | Net P&L | Expectancy | Profit factor | Max drawdown |
|---|---|---|---|---|---|---|---|
| 120 (adequate) | 49 | 71 | 40.8% | $-5,253.08 | -0.103R | 0.78 | $8,528.98 |

The 4 trade(s) of the old DEBATE rule, stopped in dual-ai-1.2.0, were removed from the paper account at the operator's request: their net $-1,416.51 was put back by a declared adjustment ($1,416.51). They stay in the journal (append-only), in none of the account's figures below.

## Paper account

| Account | Equity | P&L today | Total P&L | Drawdown | Open | Trades | Win rate | Expectancy | Profit factor | Risk | Bot |
|---|---|---|---|---|---|---|---|---|---|---|---|
| $200,000.00 | $194,976.37 | $-1,944.08 | $-5,023.63 | $-5,023.63 | 3 | 120 (adequate) | 40.8% | -0.103R | 0.78 | ACTIVE | RUNNING |

Equity includes declared operator adjustments of $1,416.51 (without them: $193,559.86); P&L today excludes them. `remove-retired-debate-rule-trades-2026-10-15`: operator: the 4 trades of the retired debate rule (dual-ai 1.1.0, stopped in 1.2.0) are removed from the paper account; they stay in the journal.

## Who lost it: the market or us

Losses 71, $-23,909.79: **the market 71** (at the stop, within the plan 64, by the time exit 5, stopped beyond the plan (a gap or the spread at the stop) 2) · **us 0**. Every closed trade is checked: the rules and the gate approved it, its data and the fill's quote were fresh, it was sized within the per-trade risk, both traders chose its side, it closed on time and not over a weekend, its costs were as planned. A check that cannot be read counts as ours.

Beyond the plan, the market's: 10-21 21:05 GBPJPY BUY lost $644.82 against a planned $498.95 in the rollover.

Beyond the plan, the market's: 10-28 13:35 GBPUSD SELL lost $509.02 against a planned $489.30.

The 4 trade(s) taken out of the account, checked the same way: 4 ours (DESK: not both traders' choice (rule DEBATE, traders ['BUY', 'SELL'])).

## Last decisions (decision → risk → paper execution)

- 10-28 19:15 USDCAD SELL: AI DECISION → RISK APPROVED → PAPER EXECUTED
- 10-28 18:30 EURGBP SELL: AI DECISION → RISK REJECTED — reward_risk: 0.98 vs minimum 1.2
- 10-28 17:00 NZDUSD BUY: AI DECISION → RISK APPROVED → PAPER EXECUTED
- 10-28 16:47 USDCHF SELL: AI DECISION → RISK REJECTED — structure: H1 structure is range (mixed swings): no new position without a clear H1 trend (up HH+HL or down LH+LL)
- 10-28 16:32 AUDUSD BUY: AI DECISION → RISK REJECTED — quote: age 116s at opening (max 90s), bid 0.70435, ask 0.70445
- 10-28 16:01 AUDJPY BUY: AI DECISION → RISK APPROVED → PAPER EXECUTED
- 10-28 16:00 EURCHF SELL: AI DECISION → RISK APPROVED → PAPER EXECUTED
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

## Latest decisions, NO TRADE included (3263 so far)

- 10-28 22:30 EURGBP NO_TRADE: risk engine: quiet_hours (18:30 New York: no new position from 16:00 to 20:00 New York (the rollover to the Tokyo open: the thinnest liquidity of the day)); open_positions (3 open, max 3): the model w
- 10-28 22:30 NZDUSD NO_TRADE: blocked before consulting the model: EXPOSURE: a NZDUSD position is already open
- 10-28 22:15 USDCHF NO_TRADE: risk engine: quiet_hours (18:15 New York: no new position from 16:00 to 20:00 New York (the rollover to the Tokyo open: the thinnest liquidity of the day)); open_positions (3 open, max 3); currency_ex
- 10-28 22:15 USDCAD NO_TRADE: blocked before consulting the model: EXPOSURE: a USDCAD position is already open
- 10-28 22:00 AUDUSD NO_TRADE: risk engine: quiet_hours (18:00 New York: no new position from 16:00 to 20:00 New York (the rollover to the Tokyo open: the thinnest liquidity of the day)); open_positions (3 open, max 3); currency_ex
- 10-28 22:00 USDJPY NO_TRADE: risk engine: quiet_hours (18:00 New York: no new position from 16:00 to 20:00 New York (the rollover to the Tokyo open: the thinnest liquidity of the day)); open_positions (3 open, max 3); currency_ex
- 10-28 21:45 GBPUSD NO_TRADE: risk engine: quiet_hours (17:45 New York: no new position from 16:00 to 20:00 New York (the rollover to the Tokyo open: the thinnest liquidity of the day)); open_positions (3 open, max 3); currency_ex
- 10-28 21:45 EURUSD NO_TRADE: risk engine: quiet_hours (17:45 New York: no new position from 16:00 to 20:00 New York (the rollover to the Tokyo open: the thinnest liquidity of the day)); open_positions (3 open, max 3); currency_ex
- 10-28 21:30 AUDJPY NO_TRADE: risk engine: quiet_hours (17:30 New York: no new position from 16:00 to 20:00 New York (the rollover to the Tokyo open: the thinnest liquidity of the day)); open_positions (3 open, max 3): the model w
- 10-28 21:30 EURCHF NO_TRADE: blocked before consulting the model: EXPOSURE: a EURCHF position is already open
- 10-28 21:15 GBPJPY NO_TRADE: risk engine: quiet_hours (17:15 New York: no new position from 16:00 to 20:00 New York (the rollover to the Tokyo open: the thinnest liquidity of the day)); open_positions (3 open, max 3): the model w
- 10-28 21:15 EURJPY NO_TRADE: risk engine: quiet_hours (17:15 New York: no new position from 16:00 to 20:00 New York (the rollover to the Tokyo open: the thinnest liquidity of the day)); open_positions (3 open, max 3): the model w

## Open paper positions

| Symbol | Side | Qty | Entry | Stop | Target | P&L |
|---|---|---|---|---|---|---|
| USDCAD | SELL | 0.77 | 1.400415 | 1.4022 | 1.397 | $84.75 |
| NZDUSD | BUY | 1.12 | 0.562885 | 0.56103 | 0.5658 | $-51.52 |
| EURCHF | SELL | 1.24 | 0.9246 | 0.92592 | 0.92262 | $196.23 |

## Closed paper trades (latest 20)

| Closed | Symbol | Side | Net | R | Costs | Exit | Source | Rule | Lost to |
|---|---|---|---|---|---|---|---|---|---|
| 10-28 18:01 | AUDJPY | BUY | $-200.91 | -0.83 | $44.30 | STOP | DUAL_AI | AGREE | the market |
| 10-28 13:35 | GBPUSD | SELL | $-509.02 | -1.04 | $49.98 | STOP | DUAL_AI | AGREE | the market |
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

## Dual AI desk (two OpenRouter traders: free, or the paid trial while it runs; a trade only when they agree)

OpenRouter `READY` · key set · trader 1 `nvidia/nemotron-3.5-super-vl:free` · trader 2 `thinkingmachines/inkling-small:free` · debate `google/gemma-4-31b-it:free` · calls today 10/900

Paid trial `paid-trial-2026-10-26` (2026-10-23T14:00:00Z to 2026-10-31T00:00:00Z): ACTIVE · trader 1 `xiaomi/mimo-v2.6-pro` asked first · trader 2 `anthropic/claude-haiku-5.5` asked first · spent $0.65 of $9.00, today $0.30 of $1.80 (the key's own reading)

Agreement trades 120 (adequate) · wins 49 · losses 71 · net $-5,253.08 · expectancy -0.103R · profit factor 0.78 · old DEBATE rule (stopped in dual-ai-1.2.0): 4 trade(s), net $-1,416.51, removed from the account

Disagreements (not traded; the debate runs in shadow): 138 · the debate's pick if taken: 119 resolved (adequate), expectancy -0.143R · the side it rejected if taken: 124 resolved (adequate), expectancy -0.227R

Exits in shadow (the same trades, followed again; measured, never traded): break-even at +1R -0.132R vs -0.087R as taken (102, adequate) · held 24 h -0.014R vs -0.087R as taken (102, adequate) · stop and target twice as far +0.023R vs -0.087R as taken (102, adequate) · closed at 8 h (the exit before dual-ai 1.7.0) -0.239R vs -0.202R as taken (48, adequate)

Trader 2's own levels in shadow (a trade is on Trader 1's since dual-ai 1.10.0; measured, never traded): +0.484R vs +0.309R as taken (10, insufficient)

Trades taken by session (UTC): ASIA 51 resolved (adequate), expectancy -0.216R · LONDON 36 resolved (adequate), expectancy +0.063R · OVERLAP 8 resolved (insufficient), expectancy -0.382R · NEW_YORK 21 resolved (insufficient), expectancy +0.168R · LATE 3 resolved (insufficient), expectancy -1.106R

| Time | Symbol | Trader 1 | Trader 2 | Debate (shadow) | Rule | Final | Risk |
|---|---|---|---|---|---|---|---|
| 10-28 22:30 | EURGBP | -  | -  | - | NOT_ASKED | NO_TRADE | - |
| 10-28 22:30 | NZDUSD | -  | -  | - | NOT_ASKED | NO_TRADE | - |
| 10-28 22:15 | USDCHF | -  | -  | - | NOT_ASKED | NO_TRADE | - |
| 10-28 22:15 | USDCAD | -  | -  | - | NOT_ASKED | NO_TRADE | - |
| 10-28 22:00 | AUDUSD | -  | -  | - | NOT_ASKED | NO_TRADE | - |
| 10-28 22:00 | USDJPY | -  | -  | - | NOT_ASKED | NO_TRADE | - |
| 10-28 21:45 | GBPUSD | -  | -  | - | NOT_ASKED | NO_TRADE | - |
| 10-28 21:45 | EURUSD | -  | -  | - | NOT_ASKED | NO_TRADE | - |
| 10-28 21:30 | AUDJPY | -  | -  | - | NOT_ASKED | NO_TRADE | - |
| 10-28 21:30 | EURCHF | -  | -  | - | NOT_ASKED | NO_TRADE | - |
| 10-28 21:15 | GBPJPY | -  | -  | - | NOT_ASKED | NO_TRADE | - |
| 10-28 21:15 | EURJPY | -  | -  | - | NOT_ASKED | NO_TRADE | - |

The chart Trader 1 read last: `last_chart.png`. (numbers): no free vision model answered, so Trader 1 read the same chart from its numbers.

Full figures: `paper_forward.json`. Rules: `docs/PAPER_FORWARD.md` on main.
