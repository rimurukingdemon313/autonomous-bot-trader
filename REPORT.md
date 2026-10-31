# PAPER FORWARD TEST — NOT REAL MONEY

Updated 2026-10-31 11:29 UTC · mode `PAPER_FORWARD` · profile `PAPER-FORWARD-200K` · shift started 2026-10-31 08:13 UTC · decision system `dual_ai`

Research status (historical, unchanged): **NO EDGE — DO NOT TRADE (historical research; this test measures forward)**. This run measures the system forward; it is not evidence of an edge until it has a sample and the forward-eligibility rules say so.

## The new account: the setup trading now (from 2026-11-01 22:00 UTC)

dual-ai 1.12.0: the H1 chart, held up to 48 h (1.11.0), and a trade only when both traders state a confidence of 65 or more (1.12.0), on the free models (the paid trial ended 2026-10-31 00:00 UTC). Opened at the owner's request (2026-10-31): owner: a longer timeframe and only very confident entries; a new account for the new setup, as the owner chose on 2026-10-27; the accounts before it are kept and reported apart.

| Start | Equity | Total P&L | Closed | Open | Trades | Win rate | Expectancy | Profit factor |
|---|---|---|---|---|---|---|---|---|
| $200,000.00 | $200,000.00 | $0.00 | $0.00 | 0 ($0.00) | 0 (none) | n/a | n/a | n/a |

Before it, kept and apart (not in the figures above): 137 trades, net $-7,414.98. The whole paper journal, which the hard gate and the risk engine still guard, is under Paper account below; nothing in it was moved or removed.

## The rule that trades: a trade only when both AIs agree

| Trades | Wins | Losses | Win rate | Net P&L | Expectancy | Profit factor | Max drawdown |
|---|---|---|---|---|---|---|---|
| 137 (adequate) | 54 | 83 | 39.4% | $-7,414.98 | -0.123R | 0.73 | $10,690.88 |

The 4 trade(s) of the old DEBATE rule, stopped in dual-ai-1.2.0, were removed from the paper account at the operator's request: their net $-1,416.51 was put back by a declared adjustment ($1,416.51). They stay in the journal (append-only), in none of the account's figures below.

## Paper account

| Account | Equity | P&L today | Total P&L | Drawdown | Open | Trades | Win rate | Expectancy | Profit factor | Risk | Bot |
|---|---|---|---|---|---|---|---|---|---|---|---|
| $200,000.00 | $192,585.02 | $0.00 | $-7,414.98 | $-7,414.98 | 0 | 137 (adequate) | 39.4% | -0.123R | 0.73 | ACTIVE | RUNNING |

Equity includes declared operator adjustments of $1,416.51 (without them: $191,168.50); P&L today excludes them. `remove-retired-debate-rule-trades-2026-10-15`: operator: the 4 trades of the retired debate rule (dual-ai 1.1.0, stopped in 1.2.0) are removed from the paper account; they stay in the journal.

## Who lost it: the market or us

Losses 83, $-27,816.82: **the market 83** (at the stop, within the plan 75, by the time exit 6, stopped beyond the plan (a gap or the spread at the stop) 2) · **us 0**. Every closed trade is checked: the rules and the gate approved it, its data and the fill's quote were fresh, it was sized within the per-trade risk, both traders chose its side, it closed on time and not over a weekend, its costs were as planned. A check that cannot be read counts as ours.

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

## Latest decisions, NO TRADE included (3748 so far)

- 10-31 11:15 GBPUSD NO_TRADE: blocked before consulting the model: DATA_QUALITY: latest bar closed 795 minutes ago; DATA_QUALITY: features missing: bar_body; STALE_DATA: quote is 49534s old [data: latest bar closed 795 minutes ago]
- 10-31 11:15 EURUSD NO_TRADE: blocked before consulting the model: DATA_QUALITY: latest bar closed 795 minutes ago; DATA_QUALITY: features missing: bar_body; STALE_DATA: quote is 49533s old [data: latest bar closed 795 minutes ago]
- 10-31 11:00 AUDJPY NO_TRADE: blocked before consulting the model: DATA_QUALITY: latest bar closed 780 minutes ago; DATA_QUALITY: features missing: bar_body; STALE_DATA: quote is 48694s old [data: latest bar closed 780 minutes ago]
- 10-31 11:00 EURCHF NO_TRADE: blocked before consulting the model: DATA_QUALITY: latest bar closed 780 minutes ago; STALE_DATA: quote is 48693s old; STALE_DATA: last closed bar is 780 minutes old [data: latest bar closed 780 minutes ago]
- 10-31 10:45 GBPJPY NO_TRADE: blocked before consulting the model: DATA_QUALITY: latest bar closed 765 minutes ago; DATA_QUALITY: features missing: bar_body; STALE_DATA: quote is 47768s old [data: latest bar closed 765 minutes ago]
- 10-31 10:45 EURJPY NO_TRADE: blocked before consulting the model: DATA_QUALITY: latest bar closed 765 minutes ago; STALE_DATA: quote is 47796s old; STALE_DATA: last closed bar is 765 minutes old [data: latest bar closed 765 minutes ago]
- 10-31 10:30 EURGBP NO_TRADE: blocked before consulting the model: DATA_QUALITY: latest bar closed 750 minutes ago; DATA_QUALITY: features missing: bar_body; STALE_DATA: quote is 47018s old [data: latest bar closed 750 minutes ago]
- 10-31 10:30 NZDUSD NO_TRADE: blocked before consulting the model: DATA_QUALITY: latest bar closed 630 minutes ago; DATA_QUALITY: features missing: bar_body; STALE_DATA: quote is 16774s old [data: latest bar closed 630 minutes ago]
- 10-31 10:15 USDCHF NO_TRADE: blocked before consulting the model: DATA_QUALITY: latest bar closed 615 minutes ago; DATA_QUALITY: features missing: bar_body; STALE_DATA: quote is 17650s old [data: latest bar closed 615 minutes ago]
- 10-31 10:15 USDCAD NO_TRADE: blocked before consulting the model: DATA_QUALITY: latest bar closed 615 minutes ago; DATA_QUALITY: features missing: bar_body; STALE_DATA: quote is 17649s old [data: latest bar closed 615 minutes ago]
- 10-31 10:00 AUDUSD NO_TRADE: blocked before consulting the model: DATA_QUALITY: latest bar closed 600 minutes ago; DATA_QUALITY: features missing: bar_body; STALE_DATA: quote is 14973s old [data: latest bar closed 600 minutes ago]
- 10-31 10:00 USDJPY NO_TRADE: blocked before consulting the model: DATA_QUALITY: latest bar closed 780 minutes ago; STALE_DATA: quote is 46845s old; STALE_DATA: last closed bar is 780 minutes old [data: latest bar closed 780 minutes ago]

## Open paper positions

| Symbol | Side | Qty | Entry | Stop | Target | P&L |
|---|---|---|---|---|---|---|

## Closed paper trades (latest 20)

| Closed | Symbol | Side | Net | R | Costs | Exit | Source | Rule | Lost to |
|---|---|---|---|---|---|---|---|---|---|
| 10-30 20:00 | EURCHF | SELL | $-124.56 | -0.52 | $30.34 | TIME | DUAL_AI | AGREE | the market |
| 10-30 13:46 | GBPUSD | BUY | $-444.37 | -0.92 | $37.38 | STOP | DUAL_AI | AGREE | the market |
| 10-30 13:50 | USDCHF | SELL | $-103.41 | -0.87 | $12.71 | STOP | DUAL_AI | AGREE | the market |
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

## Dual AI desk (two OpenRouter traders: free, or the paid trial while it runs; a trade only when they agree, both at 65 or more)

OpenRouter `CATALOG_NOT_READ_YET` · key set · trader 1 `None` · trader 2 `None` · debate `None` · calls today 0/900

Paid trial `paid-trial-2026-10-26` (2026-10-23T14:00:00Z to 2026-10-31T00:00:00Z): not active · trader 1 `xiaomi/mimo-v2.6-pro` asked first · trader 2 `anthropic/claude-haiku-5.5` asked first · spent n/a of $9.00, today n/a of $1.80 (the key's own reading)

Agreement trades 137 (adequate) · wins 54 · losses 83 · net $-7,414.98 · expectancy -0.123R · profit factor 0.73 · old DEBATE rule (stopped in dual-ai-1.2.0): 4 trade(s), net $-1,416.51, removed from the account

Disagreements (not traded; the debate runs in shadow): 149 · the debate's pick if taken: 143 resolved (adequate), expectancy -0.183R · the side it rejected if taken: 148 resolved (adequate), expectancy -0.213R

Exits in shadow (the same trades, followed again; measured, never traded): break-even at +1R -0.182R vs -0.154R as taken (124, adequate) · held 24 h -0.070R vs -0.133R as taken (118, adequate) · stop and target twice as far -0.033R vs -0.133R as taken (118, adequate) · closed at 8 h (the exit before dual-ai 1.7.0) -0.304R vs -0.283R as taken (70, adequate)

Trader 2's own levels in shadow (a trade is on Trader 1's since dual-ai 1.10.0; measured, never traded): -0.235R vs -0.264R as taken (31, adequate)

Agreements below the confidence floor (both traders at 65 or more since dual-ai 1.12.0; not traded, followed forward as the trades they would have been): 0 · if taken: 0 resolved (none)

Trades taken by session (UTC): ASIA 60 resolved (adequate), expectancy -0.257R · LONDON 42 resolved (adequate), expectancy -0.032R · OVERLAP 8 resolved (insufficient), expectancy -0.382R · NEW_YORK 28 resolved (insufficient), expectancy +0.050R · LATE 3 resolved (insufficient), expectancy -1.106R

| Time | Symbol | Trader 1 | Trader 2 | Debate (shadow) | Rule | Final | Risk |
|---|---|---|---|---|---|---|---|
| 10-31 11:15 | GBPUSD | -  | -  | - | NOT_ASKED | NO_TRADE | - |
| 10-31 11:15 | EURUSD | -  | -  | - | NOT_ASKED | NO_TRADE | - |
| 10-31 11:00 | AUDJPY | -  | -  | - | NOT_ASKED | NO_TRADE | - |
| 10-31 11:00 | EURCHF | -  | -  | - | NOT_ASKED | NO_TRADE | - |
| 10-31 10:45 | GBPJPY | -  | -  | - | NOT_ASKED | NO_TRADE | - |
| 10-31 10:45 | EURJPY | -  | -  | - | NOT_ASKED | NO_TRADE | - |
| 10-31 10:30 | EURGBP | -  | -  | - | NOT_ASKED | NO_TRADE | - |
| 10-31 10:30 | NZDUSD | -  | -  | - | NOT_ASKED | NO_TRADE | - |
| 10-31 10:15 | USDCHF | -  | -  | - | NOT_ASKED | NO_TRADE | - |
| 10-31 10:15 | USDCAD | -  | -  | - | NOT_ASKED | NO_TRADE | - |
| 10-31 10:00 | AUDUSD | -  | -  | - | NOT_ASKED | NO_TRADE | - |
| 10-31 10:00 | USDJPY | -  | -  | - | NOT_ASKED | NO_TRADE | - |

The chart Trader 1 read last: `last_chart.png`. (numbers): no free vision model answered, so Trader 1 read the same chart from its numbers.

Full figures: `paper_forward.json`. Rules: `docs/PAPER_FORWARD.md` on main.
