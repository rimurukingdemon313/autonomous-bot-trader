# PAPER FORWARD TEST — NOT REAL MONEY

Updated 2026-10-30 09:16 UTC · mode `PAPER_FORWARD` · profile `PAPER-FORWARD-200K` · shift started 2026-10-30 04:16 UTC · decision system `dual_ai`

Research status (historical, unchanged): **NO EDGE — DO NOT TRADE (historical research; this test measures forward)**. This run measures the system forward; it is not evidence of an edge until it has a sample and the forward-eligibility rules say so.

## The new account: the setup trading now (from 2026-10-26 16:22 UTC)

dual-ai 1.10.0 (a trade on Trader 1's levels) with both traders paid (paid-trial 1.2.0: Trader 1 xiaomi/mimo-v2.6-pro, Trader 2 anthropic/claude-haiku-5.5). Opened at the owner's request (2026-10-27): owner: a new account for the new setup, from the first shift that ran it; the account before it is kept and reported apart.

| Start | Equity | Total P&L | Closed | Open | Trades | Win rate | Expectancy | Profit factor |
|---|---|---|---|---|---|---|---|---|
| $200,000.00 | $197,144.42 | $-2,855.58 | $-2,983.24 | 3 ($127.66) | 28 (insufficient) | 35.7% | -0.191R | 0.53 |

Before it, kept and apart (not in the figures above): 106 trades, net $-3,759.41. The whole paper journal, which the hard gate and the risk engine still guard, is under Paper account below; nothing in it was moved or removed.

## The rule that trades: a trade only when both AIs agree

| Trades | Wins | Losses | Win rate | Net P&L | Expectancy | Profit factor | Max drawdown |
|---|---|---|---|---|---|---|---|
| 134 (adequate) | 54 | 80 | 40.3% | $-6,742.65 | -0.108R | 0.75 | $10,585.05 |

The 4 trade(s) of the old DEBATE rule, stopped in dual-ai-1.2.0, were removed from the paper account at the operator's request: their net $-1,416.51 was put back by a declared adjustment ($1,416.51). They stay in the journal (append-only), in none of the account's figures below.

## Paper account

| Account | Equity | P&L today | Total P&L | Drawdown | Open | Trades | Win rate | Expectancy | Profit factor | Risk | Bot |
|---|---|---|---|---|---|---|---|---|---|---|---|
| $200,000.00 | $193,385.01 | $-613.46 | $-6,614.99 | $-6,614.99 | 3 | 134 (adequate) | 40.3% | -0.108R | 0.75 | ACTIVE | RUNNING |

Equity includes declared operator adjustments of $1,416.51 (without them: $191,968.49); P&L today excludes them. `remove-retired-debate-rule-trades-2026-10-15`: operator: the 4 trades of the retired debate rule (dual-ai 1.1.0, stopped in 1.2.0) are removed from the paper account; they stay in the journal.

## Who lost it: the market or us

Losses 80, $-27,144.48: **the market 80** (at the stop, within the plan 73, by the time exit 5, stopped beyond the plan (a gap or the spread at the stop) 2) · **us 0**. Every closed trade is checked: the rules and the gate approved it, its data and the fill's quote were fresh, it was sized within the per-trade risk, both traders chose its side, it closed on time and not over a weekend, its costs were as planned. A check that cannot be read counts as ours.

Beyond the plan, the market's: 10-21 21:05 GBPJPY BUY lost $644.82 against a planned $498.95 in the rollover.

Beyond the plan, the market's: 10-28 13:35 GBPUSD SELL lost $509.02 against a planned $489.30.

The 4 trade(s) taken out of the account, checked the same way: 4 ours (DESK: not both traders' choice (rule DEBATE, traders ['BUY', 'SELL'])).

## Last decisions (decision → risk → paper execution)

- 10-30 07:30 GBPUSD BUY: AI DECISION → RISK APPROVED → PAPER EXECUTED
- 10-30 06:36 USDCHF SELL: AI DECISION → RISK APPROVED → PAPER EXECUTED
- 10-30 06:17 AUDUSD SELL: AI DECISION → RISK REJECTED — quote: age 100s at opening (max 90s), bid 0.70305, ask 0.7031499999999999
- 10-30 06:00 GBPUSD SELL: AI DECISION → RISK REJECTED — currency_conflict: SELL GBPUSD would bet against an open position: EURGBP SELL is long GBP
- 10-30 04:45 USDJPY SELL: AI DECISION → RISK APPROVED → PAPER EXECUTED
- 10-30 04:30 GBPUSD SELL: AI DECISION → RISK REJECTED — currency_conflict: SELL GBPUSD would bet against an open position: EURGBP SELL is long GBP
- 10-30 04:00 NZDUSD SELL: AI DECISION → RISK REJECTED — cost_to_risk: round-trip cost is 27.4% of the stop (max 25%): spread 0.00015 + commission and slippage
- 10-30 03:15 GBPUSD BUY: AI DECISION → RISK APPROVED → PAPER EXECUTED
- 10-30 03:00 EURCHF SELL: AI DECISION → RISK APPROVED → PAPER EXECUTED
- 10-30 02:30 NZDUSD SELL: AI DECISION → RISK REJECTED — cost_to_risk: round-trip cost is 32.2% of the stop (max 25%): spread 0.00015 + commission and slippage
- 10-30 02:16 USDCHF SELL: AI DECISION → RISK REJECTED — quote: age 128s at opening (max 90s), bid 0.821125, ask 0.8212750000000001
- 10-30 02:15 USDCAD SELL: AI DECISION → RISK REJECTED — quote: age 94s at opening (max 90s), bid 1.396525, ask 1.396675
- 10-30 01:00 EURGBP SELL: AI DECISION → RISK APPROVED → PAPER EXECUTED
- 10-29 17:02 GBPJPY BUY: AI DECISION → RISK APPROVED → PAPER EXECUTED
- 10-29 17:00 EURJPY BUY: AI DECISION → RISK REJECTED — reward_risk: 1.19 vs minimum 1.2; currency_conflict: BUY EURJPY would bet against an open position: EURUSD SELL is short EUR
- 10-29 16:46 EURGBP SELL: AI DECISION → RISK REJECTED — reward_risk: 0.98 vs minimum 1.2
- 10-29 16:45 NZDUSD SELL: AI DECISION → RISK APPROVED → PAPER EXECUTED
- 10-29 16:34 USDCHF SELL: AI DECISION → RISK REJECTED — cost_to_risk: round-trip cost is 27.4% of the stop (max 25%): spread 0.00015 + commission and slippage; currency_conflict: SELL USDCHF would bet against an open position: EURUSD SELL is long USD
- 10-29 16:15 USDJPY SELL: AI DECISION → RISK REJECTED — currency_conflict: SELL USDJPY would bet against an open position: EURUSD SELL is long USD
- 10-29 16:00 EURUSD SELL: AI DECISION → RISK APPROVED → PAPER EXECUTED

## Latest decisions, NO TRADE included (3540 so far)

- 10-30 09:15 AUDUSD NO_TRADE: risk engine: open_positions (3 open, max 3); currency_exposure (2 open positions share a currency, max 2): the model was not consulted
- 10-30 09:15 USDJPY NO_TRADE: risk engine: open_positions (3 open, max 3); currency_exposure (2 open positions share a currency, max 2): the model was not consulted
- 10-30 09:00 GBPUSD NO_TRADE: blocked before consulting the model: EXPOSURE: a GBPUSD position is already open
- 10-30 09:00 EURUSD NO_TRADE: risk engine: news (Medium-impact release EUR German Prelim GDP q/q 1 min ago: no new position from 30 min before to 30 min after); open_positions (3 open, max 3); currency_exposure (2 open positions s
- 10-30 08:45 AUDJPY NO_TRADE: risk engine: open_positions (3 open, max 3): the model was not consulted
- 10-30 08:45 EURCHF NO_TRADE: blocked before consulting the model: EXPOSURE: a EURCHF position is already open
- 10-30 08:30 GBPJPY NO_TRADE: risk engine: open_positions (3 open, max 3): the model was not consulted
- 10-30 08:30 EURJPY NO_TRADE: risk engine: news (Medium-impact release EUR German Prelim GDP q/q in 29 min: no new position from 30 min before to 30 min after); open_positions (3 open, max 3): the model was not consulted
- 10-30 08:15 EURGBP NO_TRADE: risk engine: open_positions (3 open, max 3): the model was not consulted
- 10-30 08:15 NZDUSD NO_TRADE: risk engine: open_positions (3 open, max 3); currency_exposure (2 open positions share a currency, max 2): the model was not consulted
- 10-30 08:00 USDCHF NO_TRADE: blocked before consulting the model: EXPOSURE: a USDCHF position is already open
- 10-30 08:00 USDCAD NO_TRADE: risk engine: open_positions (3 open, max 3); currency_exposure (2 open positions share a currency, max 2): the model was not consulted

## Open paper positions

| Symbol | Side | Qty | Entry | Stop | Target | P&L |
|---|---|---|---|---|---|---|
| GBPUSD | BUY | 1.78 | 1.34117 | 1.33885 | 1.3445 | $172.66 |
| USDCHF | SELL | 0.46 | 0.822415 | 0.8242 | 0.8201 | $24.63 |
| EURCHF | SELL | 0.97 | 0.9195 | 0.9212 | 0.91705 | $-69.63 |

## Closed paper trades (latest 20)

| Closed | Symbol | Side | Net | R | Costs | Exit | Source | Rule | Lost to |
|---|---|---|---|---|---|---|---|---|---|
| 10-30 07:24 | EURGBP | SELL | $566.51 | +1.17 | $78.92 | TARGET | DUAL_AI | AGREE | - |
| 10-30 05:23 | USDJPY | SELL | $-203.12 | -0.85 | $19.07 | STOP | DUAL_AI | AGREE | the market |
| 10-30 03:45 | GBPUSD | BUY | $-201.68 | -0.84 | $30.66 | STOP | DUAL_AI | AGREE | the market |
| 10-30 03:12 | GBPJPY | BUY | $-462.07 | -0.95 | $43.29 | STOP | DUAL_AI | AGREE | the market |
| 10-30 02:07 | NZDUSD | SELL | $-440.75 | -0.91 | $100.15 | STOP | DUAL_AI | AGREE | the market |
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

## Dual AI desk (two OpenRouter traders: free, or the paid trial while it runs; a trade only when they agree)

OpenRouter `READY` · key set · trader 1 `nvidia/nemotron-3.5-super-vl:free` · trader 2 `google/gemma-4-31b-it:free` · debate `dots-studio/dots-3-note-preview:free` · calls today 25/900

Paid trial `paid-trial-2026-10-26` (2026-10-23T14:00:00Z to 2026-10-31T00:00:00Z): ACTIVE · trader 1 `xiaomi/mimo-v2.6-pro` asked first · trader 2 `anthropic/claude-haiku-5.5` asked first · spent $0.96 of $9.00, today $0.11 of $1.80 (the key's own reading)

Agreement trades 134 (adequate) · wins 54 · losses 80 · net $-6,742.65 · expectancy -0.108R · profit factor 0.75 · old DEBATE rule (stopped in dual-ai-1.2.0): 4 trade(s), net $-1,416.51, removed from the account

Disagreements (not traded; the debate runs in shadow): 149 · the debate's pick if taken: 141 resolved (adequate), expectancy -0.190R · the side it rejected if taken: 146 resolved (adequate), expectancy -0.202R

Exits in shadow (the same trades, followed again; measured, never traded): break-even at +1R -0.164R vs -0.124R as taken (114, adequate) · held 24 h -0.059R vs -0.124R as taken (114, adequate) · stop and target twice as far -0.011R vs -0.124R as taken (114, adequate) · closed at 8 h (the exit before dual-ai 1.7.0) -0.307R vs -0.249R as taken (60, adequate)

Trader 2's own levels in shadow (a trade is on Trader 1's since dual-ai 1.10.0; measured, never traded): -0.091R vs -0.157R as taken (21, insufficient)

Trades taken by session (UTC): ASIA 55 resolved (adequate), expectancy -0.239R · LONDON 40 resolved (adequate), expectancy -0.048R · OVERLAP 8 resolved (insufficient), expectancy -0.382R · NEW_YORK 25 resolved (insufficient), expectancy +0.184R · LATE 3 resolved (insufficient), expectancy -1.106R

| Time | Symbol | Trader 1 | Trader 2 | Debate (shadow) | Rule | Final | Risk |
|---|---|---|---|---|---|---|---|
| 10-30 09:15 | AUDUSD | -  | -  | - | NOT_ASKED | NO_TRADE | - |
| 10-30 09:15 | USDJPY | -  | -  | - | NOT_ASKED | NO_TRADE | - |
| 10-30 09:00 | GBPUSD | -  | -  | - | NOT_ASKED | NO_TRADE | - |
| 10-30 09:00 | EURUSD | -  | -  | - | NOT_ASKED | NO_TRADE | - |
| 10-30 08:45 | AUDJPY | -  | -  | - | NOT_ASKED | NO_TRADE | - |
| 10-30 08:45 | EURCHF | -  | -  | - | NOT_ASKED | NO_TRADE | - |
| 10-30 08:30 | GBPJPY | -  | -  | - | NOT_ASKED | NO_TRADE | - |
| 10-30 08:30 | EURJPY | -  | -  | - | NOT_ASKED | NO_TRADE | - |
| 10-30 08:15 | EURGBP | -  | -  | - | NOT_ASKED | NO_TRADE | - |
| 10-30 08:15 | NZDUSD | -  | -  | - | NOT_ASKED | NO_TRADE | - |
| 10-30 08:00 | USDCHF | -  | -  | - | NOT_ASKED | NO_TRADE | - |
| 10-30 08:00 | USDCAD | -  | -  | - | NOT_ASKED | NO_TRADE | - |

The chart Trader 1 read last: `last_chart.png`. (numbers): no free vision model answered, so Trader 1 read the same chart from its numbers.

Full figures: `paper_forward.json`. Rules: `docs/PAPER_FORWARD.md` on main.
