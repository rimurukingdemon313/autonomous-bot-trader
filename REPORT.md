# PAPER FORWARD TEST — NOT REAL MONEY

Updated 2026-10-29 21:05 UTC · mode `PAPER_FORWARD` · profile `PAPER-FORWARD-200K` · shift started 2026-10-29 17:04 UTC · decision system `dual_ai`

Research status (historical, unchanged): **NO EDGE — DO NOT TRADE (historical research; this test measures forward)**. This run measures the system forward; it is not evidence of an edge until it has a sample and the forward-eligibility rules say so.

## The new account: the setup trading now (from 2026-10-26 16:22 UTC)

dual-ai 1.10.0 (a trade on Trader 1's levels) with both traders paid (paid-trial 1.2.0: Trader 1 xiaomi/mimo-v2.6-pro, Trader 2 anthropic/claude-haiku-5.5). Opened at the owner's request (2026-10-27): owner: a new account for the new setup, from the first shift that ran it; the account before it is kept and reported apart.

| Start | Equity | Total P&L | Closed | Open | Trades | Win rate | Expectancy | Profit factor |
|---|---|---|---|---|---|---|---|---|
| $200,000.00 | $197,303.04 | $-2,696.96 | $-2,242.13 | 2 ($-454.83) | 23 (insufficient) | 39.1% | -0.129R | 0.55 |

Before it, kept and apart (not in the figures above): 106 trades, net $-3,759.41. The whole paper journal, which the hard gate and the risk engine still guard, is under Paper account below; nothing in it was moved or removed.

## The rule that trades: a trade only when both AIs agree

| Trades | Wins | Losses | Win rate | Net P&L | Expectancy | Profit factor | Max drawdown |
|---|---|---|---|---|---|---|---|
| 129 (adequate) | 53 | 76 | 41.1% | $-6,001.54 | -0.094R | 0.77 | $9,277.43 |

The 4 trade(s) of the old DEBATE rule, stopped in dual-ai-1.2.0, were removed from the paper account at the operator's request: their net $-1,416.51 was put back by a declared adjustment ($1,416.51). They stay in the journal (append-only), in none of the account's figures below.

## Paper account

| Account | Equity | P&L today | Total P&L | Drawdown | Open | Trades | Win rate | Expectancy | Profit factor | Risk | Bot |
|---|---|---|---|---|---|---|---|---|---|---|---|
| $200,000.00 | $193,543.63 | $-1,377.86 | $-6,456.37 | $-6,456.37 | 2 | 129 (adequate) | 41.1% | -0.094R | 0.77 | ACTIVE | RUNNING |

Equity includes declared operator adjustments of $1,416.51 (without them: $192,127.12); P&L today excludes them. `remove-retired-debate-rule-trades-2026-10-15`: operator: the 4 trades of the retired debate rule (dual-ai 1.1.0, stopped in 1.2.0) are removed from the paper account; they stay in the journal.

## Who lost it: the market or us

Losses 76, $-25,836.86: **the market 76** (at the stop, within the plan 69, by the time exit 5, stopped beyond the plan (a gap or the spread at the stop) 2) · **us 0**. Every closed trade is checked: the rules and the gate approved it, its data and the fill's quote were fresh, it was sized within the per-trade risk, both traders chose its side, it closed on time and not over a weekend, its costs were as planned. A check that cannot be read counts as ours.

Beyond the plan, the market's: 10-21 21:05 GBPJPY BUY lost $644.82 against a planned $498.95 in the rollover.

Beyond the plan, the market's: 10-28 13:35 GBPUSD SELL lost $509.02 against a planned $489.30.

The 4 trade(s) taken out of the account, checked the same way: 4 ours (DESK: not both traders' choice (rule DEBATE, traders ['BUY', 'SELL'])).

## Last decisions (decision → risk → paper execution)

- 10-29 17:02 GBPJPY BUY: AI DECISION → RISK APPROVED → PAPER EXECUTED
- 10-29 17:00 EURJPY BUY: AI DECISION → RISK REJECTED — reward_risk: 1.19 vs minimum 1.2; currency_conflict: BUY EURJPY would bet against an open position: EURUSD SELL is short EUR
- 10-29 16:46 EURGBP SELL: AI DECISION → RISK REJECTED — reward_risk: 0.98 vs minimum 1.2
- 10-29 16:45 NZDUSD SELL: AI DECISION → RISK APPROVED → PAPER EXECUTED
- 10-29 16:34 USDCHF SELL: AI DECISION → RISK REJECTED — cost_to_risk: round-trip cost is 27.4% of the stop (max 25%): spread 0.00015 + commission and slippage; currency_conflict: SELL USDCHF would bet against an open position: EURUSD SELL is long USD
- 10-29 16:15 USDJPY SELL: AI DECISION → RISK REJECTED — currency_conflict: SELL USDJPY would bet against an open position: EURUSD SELL is long USD
- 10-29 16:00 EURUSD SELL: AI DECISION → RISK APPROVED → PAPER EXECUTED
- 10-29 10:30 EURUSD SELL: AI DECISION → RISK APPROVED → PAPER EXECUTED
- 10-29 10:15 EURCHF SELL: AI DECISION → RISK REJECTED — cost_to_risk: round-trip cost is 26.0% of the stop (max 25%): spread 0.00018 + commission and slippage
- 10-29 07:19 AUDJPY BUY: AI DECISION → RISK APPROVED → PAPER EXECUTED
- 10-29 06:15 AUDUSD SELL: AI DECISION → RISK REJECTED — currency_conflict: SELL AUDUSD would bet against an open position: NZDUSD BUY is short USD
- 10-29 06:15 USDJPY BUY: AI DECISION → RISK REJECTED — currency_conflict: BUY USDJPY would bet against an open position: NZDUSD BUY is short USD
- 10-29 02:45 EURGBP SELL: AI DECISION → RISK APPROVED → PAPER EXECUTED
- 10-29 02:16 AUDUSD BUY: AI DECISION → RISK APPROVED → PAPER EXECUTED
- 10-29 02:00 GBPUSD SELL: AI DECISION → RISK REJECTED — currency_conflict: SELL GBPUSD would bet against an open position: NZDUSD BUY is short USD
- 10-29 02:00 EURUSD SELL: AI DECISION → RISK REJECTED — currency_conflict: SELL EURUSD would bet against an open position: NZDUSD BUY is short USD
- 10-29 01:31 GBPJPY BUY: AI DECISION → RISK APPROVED → PAPER EXECUTED
- 10-29 01:30 EURJPY BUY: AI DECISION → RISK REJECTED — currency_conflict: BUY EURJPY would bet against an open position: EURCHF SELL is short EUR
- 10-28 19:15 USDCAD SELL: AI DECISION → RISK APPROVED → PAPER EXECUTED
- 10-28 18:30 EURGBP SELL: AI DECISION → RISK REJECTED — reward_risk: 0.98 vs minimum 1.2

## Latest decisions, NO TRADE included (3443 so far)

- 10-29 21:00 EURGBP NO_TRADE: risk engine: quiet_hours (17:00 New York: no new position from 16:00 to 20:00 New York (the rollover to the Tokyo open: the thinnest liquidity of the day)): the model was not consulted
- 10-29 21:00 NZDUSD NO_TRADE: blocked before consulting the model: EXPOSURE: a NZDUSD position is already open
- 10-29 20:45 USDCHF NO_TRADE: risk engine: quiet_hours (16:45 New York: no new position from 16:00 to 20:00 New York (the rollover to the Tokyo open: the thinnest liquidity of the day)): the model was not consulted
- 10-29 20:45 USDCAD NO_TRADE: risk engine: quiet_hours (16:45 New York: no new position from 16:00 to 20:00 New York (the rollover to the Tokyo open: the thinnest liquidity of the day)): the model was not consulted
- 10-29 20:30 AUDUSD NO_TRADE: risk engine: quiet_hours (16:30 New York: no new position from 16:00 to 20:00 New York (the rollover to the Tokyo open: the thinnest liquidity of the day)); open_positions (3 open, max 3); currency_ex
- 10-29 20:30 USDJPY NO_TRADE: risk engine: quiet_hours (16:30 New York: no new position from 16:00 to 20:00 New York (the rollover to the Tokyo open: the thinnest liquidity of the day)); open_positions (3 open, max 3); currency_ex
- 10-29 20:15 GBPUSD NO_TRADE: risk engine: quiet_hours (16:15 New York: no new position from 16:00 to 20:00 New York (the rollover to the Tokyo open: the thinnest liquidity of the day)); open_positions (3 open, max 3); currency_ex
- 10-29 20:15 EURUSD NO_TRADE: blocked before consulting the model: EXPOSURE: a EURUSD position is already open
- 10-29 20:00 AUDJPY NO_TRADE: risk engine: quiet_hours (16:00 New York: no new position from 16:00 to 20:00 New York (the rollover to the Tokyo open: the thinnest liquidity of the day)); open_positions (3 open, max 3): the model w
- 10-29 20:00 EURCHF NO_TRADE: risk engine: quiet_hours (16:00 New York: no new position from 16:00 to 20:00 New York (the rollover to the Tokyo open: the thinnest liquidity of the day)); open_positions (3 open, max 3): the model w
- 10-29 19:45 GBPJPY NO_TRADE: blocked before consulting the model: EXPOSURE: a GBPJPY position is already open
- 10-29 19:45 EURJPY NO_TRADE: risk engine: open_positions (3 open, max 3): the model was not consulted

## Open paper positions

| Symbol | Side | Qty | Entry | Stop | Target | P&L |
|---|---|---|---|---|---|---|
| GBPJPY | BUY | 1.31 | 211.1455 | 210.62 | 211.988 | $-328.47 |
| NZDUSD | SELL | 3.51 | 0.563215 | 0.5643 | 0.5613 | $-126.36 |

## Closed paper trades (latest 20)

| Closed | Symbol | Side | Net | R | Costs | Exit | Source | Rule | Lost to |
|---|---|---|---|---|---|---|---|---|---|
| 10-29 20:34 | EURUSD | SELL | $-432.21 | -0.89 | $35.19 | STOP | DUAL_AI | AGREE | the market |
| 10-29 13:31 | AUDJPY | BUY | $-417.64 | -0.86 | $64.29 | STOP | DUAL_AI | AGREE | the market |
| 10-29 13:18 | EURUSD | SELL | $300.12 | +1.24 | $29.28 | TARGET | DUAL_AI | AGREE | - |
| 10-29 12:58 | EURGBP | SELL | $444.04 | +0.91 | $82.93 | TARGET | DUAL_AI | AGREE | - |
| 10-29 10:03 | NZDUSD | BUY | $-237.99 | -0.98 | $44.54 | STOP | DUAL_AI | AGREE | the market |
| 10-29 06:01 | AUDUSD | BUY | $-422.22 | -0.87 | $71.63 | STOP | DUAL_AI | AGREE | the market |
| 10-29 01:54 | GBPJPY | BUY | $-417.01 | -0.86 | $62.67 | STOP | DUAL_AI | AGREE | the market |
| 10-29 01:51 | EURCHF | SELL | $264.71 | +1.09 | $60.23 | TARGET | DUAL_AI | AGREE | - |
| 10-29 01:25 | USDCAD | SELL | $169.74 | +1.40 | $27.33 | TARGET | DUAL_AI | AGREE | - |
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

## Dual AI desk (two OpenRouter traders: free, or the paid trial while it runs; a trade only when they agree)

OpenRouter `CATALOG_NOT_READ_YET` · key set · trader 1 `None` · trader 2 `None` · debate `None` · calls today 0/900

Paid trial `paid-trial-2026-10-26` (2026-10-23T14:00:00Z to 2026-10-31T00:00:00Z): ACTIVE · trader 1 `xiaomi/mimo-v2.6-pro` asked first · trader 2 `anthropic/claude-haiku-5.5` asked first · spent n/a of $9.00, today n/a of $1.80 (the key's own reading)

Agreement trades 129 (adequate) · wins 53 · losses 76 · net $-6,001.54 · expectancy -0.094R · profit factor 0.77 · old DEBATE rule (stopped in dual-ai-1.2.0): 4 trade(s), net $-1,416.51, removed from the account

Disagreements (not traded; the debate runs in shadow): 147 · the debate's pick if taken: 133 resolved (adequate), expectancy -0.213R · the side it rejected if taken: 138 resolved (adequate), expectancy -0.160R

Exits in shadow (the same trades, followed again; measured, never traded): break-even at +1R -0.152R vs -0.110R as taken (110, adequate) · held 24 h -0.042R vs -0.110R as taken (110, adequate) · stop and target twice as far -0.016R vs -0.110R as taken (110, adequate) · closed at 8 h (the exit before dual-ai 1.7.0) -0.269R vs -0.230R as taken (56, adequate)

Trader 2's own levels in shadow (a trade is on Trader 1's since dual-ai 1.10.0; measured, never traded): +0.074R vs -0.005R as taken (18, insufficient)

Trades taken by session (UTC): ASIA 52 resolved (adequate), expectancy -0.233R · LONDON 39 resolved (adequate), expectancy -0.023R · OVERLAP 8 resolved (insufficient), expectancy -0.382R · NEW_YORK 25 resolved (insufficient), expectancy +0.184R · LATE 3 resolved (insufficient), expectancy -1.106R

| Time | Symbol | Trader 1 | Trader 2 | Debate (shadow) | Rule | Final | Risk |
|---|---|---|---|---|---|---|---|
| 10-29 21:00 | EURGBP | -  | -  | - | NOT_ASKED | NO_TRADE | - |
| 10-29 21:00 | NZDUSD | -  | -  | - | NOT_ASKED | NO_TRADE | - |
| 10-29 20:45 | USDCHF | -  | -  | - | NOT_ASKED | NO_TRADE | - |
| 10-29 20:45 | USDCAD | -  | -  | - | NOT_ASKED | NO_TRADE | - |
| 10-29 20:30 | AUDUSD | -  | -  | - | NOT_ASKED | NO_TRADE | - |
| 10-29 20:30 | USDJPY | -  | -  | - | NOT_ASKED | NO_TRADE | - |
| 10-29 20:15 | GBPUSD | -  | -  | - | NOT_ASKED | NO_TRADE | - |
| 10-29 20:15 | EURUSD | -  | -  | - | NOT_ASKED | NO_TRADE | - |
| 10-29 20:00 | AUDJPY | -  | -  | - | NOT_ASKED | NO_TRADE | - |
| 10-29 20:00 | EURCHF | -  | -  | - | NOT_ASKED | NO_TRADE | - |
| 10-29 19:45 | GBPJPY | -  | -  | - | NOT_ASKED | NO_TRADE | - |
| 10-29 19:45 | EURJPY | -  | -  | - | NOT_ASKED | NO_TRADE | - |

The chart Trader 1 read last: `last_chart.png`. (numbers): no free vision model answered, so Trader 1 read the same chart from its numbers.

Full figures: `paper_forward.json`. Rules: `docs/PAPER_FORWARD.md` on main.
