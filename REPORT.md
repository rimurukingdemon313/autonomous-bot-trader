# PAPER FORWARD TEST — NOT REAL MONEY

Updated 2026-10-28 07:30 UTC · mode `PAPER_FORWARD` · profile `PAPER-FORWARD-200K` · shift started 2026-10-28 01:55 UTC · decision system `dual_ai`

Research status (historical, unchanged): **NO EDGE — DO NOT TRADE (historical research; this test measures forward)**. This run measures the system forward; it is not evidence of an edge until it has a sample and the forward-eligibility rules say so.

## The new account: the setup trading now (from 2026-10-26 16:22 UTC)

dual-ai 1.10.0 (a trade on Trader 1's levels) with both traders paid (paid-trial 1.2.0: Trader 1 xiaomi/mimo-v2.6-pro, Trader 2 anthropic/claude-haiku-5.5). Opened at the owner's request (2026-10-27): owner: a new account for the new setup, from the first shift that ran it; the account before it is kept and reported apart.

| Start | Equity | Total P&L | Closed | Open | Trades | Win rate | Expectancy | Profit factor |
|---|---|---|---|---|---|---|---|---|
| $200,000.00 | $200,664.18 | $664.18 | $933.57 | 2 ($-269.39) | 8 (insufficient) | 62.5% | +0.277R | 2.50 |

Before it, kept and apart (not in the figures above): 106 trades, net $-3,759.41. The whole paper journal, which the hard gate and the risk engine still guard, is under Paper account below; nothing in it was moved or removed.

## The rule that trades: a trade only when both AIs agree

| Trades | Wins | Losses | Win rate | Net P&L | Expectancy | Profit factor | Max drawdown |
|---|---|---|---|---|---|---|---|
| 114 (adequate) | 49 | 65 | 43.0% | $-2,825.84 | -0.061R | 0.87 | $7,377.98 |

The 4 trade(s) of the old DEBATE rule, stopped in dual-ai-1.2.0, were removed from the paper account at the operator's request: their net $-1,416.51 was put back by a declared adjustment ($1,416.51). They stay in the journal (append-only), in none of the account's figures below.

## Paper account

| Account | Equity | P&L today | Total P&L | Drawdown | Open | Trades | Win rate | Expectancy | Profit factor | Risk | Bot |
|---|---|---|---|---|---|---|---|---|---|---|---|
| $200,000.00 | $196,904.77 | $-15.68 | $-3,095.23 | $-3,095.23 | 2 | 114 (adequate) | 43.0% | -0.061R | 0.87 | ACTIVE | RUNNING |

Equity includes declared operator adjustments of $1,416.51 (without them: $195,488.26); P&L today excludes them. `remove-retired-debate-rule-trades-2026-10-15`: operator: the 4 trades of the retired debate rule (dual-ai 1.1.0, stopped in 1.2.0) are removed from the paper account; they stay in the journal.

## Who lost it: the market or us

Losses 65, $-21,482.55: **the market 65** (at the stop, within the plan 59, by the time exit 5, stopped beyond the plan (a gap or the spread at the stop) 1) · **us 0**. Every closed trade is checked: the rules and the gate approved it, its data and the fill's quote were fresh, it was sized within the per-trade risk, both traders chose its side, it closed on time and not over a weekend, its costs were as planned. A check that cannot be read counts as ours.

Beyond the plan, the market's: 10-21 21:05 GBPJPY BUY lost $644.82 against a planned $498.95 in the rollover.

The 4 trade(s) taken out of the account, checked the same way: 4 ours (DESK: not both traders' choice (rule DEBATE, traders ['BUY', 'SELL'])).

## Last decisions (decision → risk → paper execution)

- 10-28 07:15 NZDUSD SELL: AI DECISION → RISK REJECTED — quote: age 92s at opening (max 90s), bid 0.561425, ask 0.561575
- 10-28 06:30 EURUSD SELL: AI DECISION → RISK APPROVED → PAPER EXECUTED
- 10-28 06:16 AUDJPY SELL: AI DECISION → RISK REJECTED — reward_risk: 1.12 vs minimum 1.2; currency_conflict: SELL AUDJPY would bet against an open position: USDJPY BUY is short JPY
- 10-28 06:15 EURCHF BUY: AI DECISION → RISK REJECTED — currency_conflict: BUY EURCHF would bet against an open position: EURGBP SELL is short EUR
- 10-28 06:00 GBPJPY SELL: AI DECISION → RISK REJECTED — currency_conflict: SELL GBPJPY would bet against an open position: USDJPY BUY is short JPY; EURGBP SELL is long GBP
- 10-28 06:00 EURJPY SELL: AI DECISION → RISK REJECTED — currency_conflict: SELL EURJPY would bet against an open position: USDJPY BUY is short JPY
- 10-27 10:00 EURGBP SELL: AI DECISION → RISK APPROVED → PAPER EXECUTED
- 10-27 09:15 EURUSD SELL: AI DECISION → RISK APPROVED → PAPER EXECUTED
- 10-27 09:00 NZDUSD SELL: AI DECISION → RISK REJECTED — reward_risk: 0.91 vs minimum 1.2; structure: H1 structure is range (mixed swings): no new position without a clear H1 trend (up HH+HL or down LH+LL)
- 10-27 07:00 USDJPY BUY: AI DECISION → RISK APPROVED → PAPER EXECUTED
- 10-27 06:45 EURUSD SELL: AI DECISION → RISK APPROVED → PAPER EXECUTED
- 10-27 06:30 AUDJPY BUY: AI DECISION → RISK REJECTED — structure: H1 structure is range (mixed swings): no new position without a clear H1 trend (up HH+HL or down LH+LL)
- 10-27 05:30 USDJPY SELL: AI DECISION → RISK APPROVED → PAPER EXECUTED
- 10-27 02:00 EURJPY SELL: AI DECISION → RISK APPROVED → PAPER EXECUTED
- 10-27 01:46 EURGBP SELL: AI DECISION → RISK REJECTED — currency_conflict: SELL EURGBP would bet against an open position: GBPUSD SELL is short GBP
- 10-27 01:32 USDCHF SELL: AI DECISION → RISK REJECTED — currency_conflict: SELL USDCHF would bet against an open position: GBPUSD SELL is long USD
- 10-26 17:45 AUDJPY SELL: AI DECISION → RISK APPROVED → PAPER EXECUTED
- 10-26 17:45 EURCHF SELL: AI DECISION → RISK APPROVED → PAPER EXECUTED
- 10-26 17:30 GBPJPY SELL: AI DECISION → RISK REJECTED — structure: H1 structure is range (mixed swings): no new position without a clear H1 trend (up HH+HL or down LH+LL)
- 10-26 17:30 EURJPY SELL: AI DECISION → RISK REJECTED — structure: H1 structure is range (mixed swings): no new position without a clear H1 trend (up HH+HL or down LH+LL)

## Latest decisions, NO TRADE included (3143 so far)

- 10-28 07:30 EURJPY NO_TRADE: risk engine: currency_exposure (2 open positions share a currency, max 2): the model was not consulted
- 10-28 07:16 EURGBP NO_TRADE: blocked before consulting the model: EXPOSURE: a EURGBP position is already open
- 10-28 07:15 NZDUSD SELL: SELL NZDUSD on M15: AGREE: Trader 1 (xiaomi/mimo-v2.6-pro) SELL 58: Higher-timeframe bearish CHoCH/BOS plus deep mitigated bearish FVGs overhead (0.56129-0.56818) keep the path of least resistance dow
- 10-28 07:00 USDCHF NO_TRADE: risk engine: open_positions (3 open, max 3); currency_exposure (2 open positions share a currency, max 2); gate_open_risk (the hard risk gate's open-risk room 270.99 is less than the next trade's risk
- 10-28 07:00 USDCAD NO_TRADE: risk engine: open_positions (3 open, max 3); currency_exposure (2 open positions share a currency, max 2); gate_open_risk (the hard risk gate's open-risk room 270.99 is less than the next trade's risk
- 10-28 06:45 AUDUSD NO_TRADE: risk engine: open_positions (3 open, max 3); currency_exposure (2 open positions share a currency, max 2): the model was not consulted
- 10-28 06:45 USDJPY NO_TRADE: blocked before consulting the model: EXPOSURE: a USDJPY position is already open
- 10-28 06:30 GBPUSD NO_TRADE: risk engine: open_positions (3 open, max 3); currency_exposure (2 open positions share a currency, max 2); gate_open_risk (the hard risk gate's open-risk room 370.79 is less than the next trade's risk
- 10-28 06:30 EURUSD SELL: SELL EURUSD on M15: AGREE: Trader 1 (xiaomi/mimo-v2.6-pro) SELL 58: Both timeframes are bearish with clean LH/LL structure and an open bearish FVG overhead at 1.11284-1.11297, so the path of least res
- 10-28 06:16 AUDJPY SELL: SELL AUDJPY on M15: AGREE: Trader 1 (nvidia/nemotron-3.5-super-vl:free) SELL 62: M15 structure just flipped bearish with lower highs and lower lows; price is retracing into a tested supply order block
- 10-28 06:15 EURCHF BUY: BUY EURCHF on M15: AGREE: Trader 1 (xiaomi/mimo-v2.6-pro) BUY 58: Bullish CHoCH plus BOS out of a swept-low demand OB gives the cleaner short-term path of least resistance, targeting the PDH/EQH liqui
- 10-28 06:00 GBPJPY SELL: SELL GBPJPY on M15: AGREE: Trader 1 (xiaomi/mimo-v2.6-pro) SELL 58: Fresh bearish structure breaks on M15 and a bearish H4 CHoCH/BOS outweigh the stale UP trend labels, so the higher-probability side 

## Open paper positions

| Symbol | Side | Qty | Entry | Stop | Target | P&L |
|---|---|---|---|---|---|---|
| EURUSD | SELL | 4.36 | 1.11225 | 1.1131 | 1.111 | $-39.24 |
| EURGBP | SELL | 2.75 | 0.8365300000000001 | 0.83765 | 0.8352 | $-230.15 |

## Closed paper trades (latest 20)

| Closed | Symbol | Side | Net | R | Costs | Exit | Source | Rule | Lost to |
|---|---|---|---|---|---|---|---|---|---|
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
| 10-23 20:02 | GBPUSD | SELL | $33.15 | +0.27 | $17.85 | TIME | DUAL_AI | AGREE | - |
| 10-23 12:36 | GBPJPY | SELL | $220.25 | +1.80 | $20.57 | TARGET | DUAL_AI | AGREE | - |
| 10-23 10:06 | EURUSD | SELL | $-102.94 | -0.84 | $15.30 | STOP | DUAL_AI | AGREE | the market |
| 10-23 07:01 | EURGBP | SELL | $-207.52 | -0.84 | $43.74 | STOP | DUAL_AI | AGREE | the market |

## Dual AI desk (two OpenRouter traders: free, or the paid trial while it runs; a trade only when they agree)

OpenRouter `READY` · key set · trader 1 `nvidia/nemotron-3.5-super-vl:free` · trader 2 `thinkingmachines/inkling-small:free` · debate `google/gemma-4-26b-a4b-it:free` · calls today 15/900

Paid trial `paid-trial-2026-10-26` (2026-10-23T14:00:00Z to 2026-10-31T00:00:00Z): ACTIVE · trader 1 `xiaomi/mimo-v2.6-pro` asked first · trader 2 `anthropic/claude-haiku-5.5` asked first · spent $0.40 of $9.00, today $0.05 of $1.80 (the key's own reading)

Agreement trades 114 (adequate) · wins 49 · losses 65 · net $-2,825.84 · expectancy -0.061R · profit factor 0.87 · old DEBATE rule (stopped in dual-ai-1.2.0): 4 trade(s), net $-1,416.51, removed from the account

Disagreements (not traded; the debate runs in shadow): 123 · the debate's pick if taken: 117 resolved (adequate), expectancy -0.146R · the side it rejected if taken: 122 resolved (adequate), expectancy -0.218R

Exits in shadow (the same trades, followed again; measured, never traded): break-even at +1R -0.136R vs -0.090R as taken (100, adequate) · held 24 h -0.015R vs -0.090R as taken (100, adequate) · stop and target twice as far +0.024R vs -0.090R as taken (100, adequate) · closed at 8 h (the exit before dual-ai 1.7.0) -0.251R vs -0.213R as taken (46, adequate)

Trader 2's own levels in shadow (a trade is on Trader 1's since dual-ai 1.10.0; measured, never traded): +0.552R vs +0.376R as taken (8, insufficient)

Trades taken by session (UTC): ASIA 51 resolved (adequate), expectancy -0.216R · LONDON 34 resolved (adequate), expectancy +0.064R · OVERLAP 8 resolved (insufficient), expectancy -0.382R · NEW_YORK 21 resolved (insufficient), expectancy +0.168R · LATE 3 resolved (insufficient), expectancy -1.106R

| Time | Symbol | Trader 1 | Trader 2 | Debate (shadow) | Rule | Final | Risk |
|---|---|---|---|---|---|---|---|
| 10-28 07:30 | EURJPY | -  | -  | - | NOT_ASKED | NO_TRADE | - |
| 10-28 07:16 | EURGBP | -  | -  | - | NOT_ASKED | NO_TRADE | - |
| 10-28 07:15 | NZDUSD | SELL 58 | SELL 55 | - | AGREE | SELL | REJECTED |
| 10-28 07:00 | USDCHF | -  | -  | - | NOT_ASKED | NO_TRADE | - |
| 10-28 07:00 | USDCAD | -  | -  | - | NOT_ASKED | NO_TRADE | - |
| 10-28 06:45 | AUDUSD | -  | -  | - | NOT_ASKED | NO_TRADE | - |
| 10-28 06:45 | USDJPY | -  | -  | - | NOT_ASKED | NO_TRADE | - |
| 10-28 06:30 | GBPUSD | -  | -  | - | NOT_ASKED | NO_TRADE | - |
| 10-28 06:30 | EURUSD | SELL 58 | SELL 55 | - | AGREE | SELL | APPROVED |
| 10-28 06:16 | AUDJPY | SELL 62 | SELL 56 | - | AGREE | SELL | REJECTED |
| 10-28 06:15 | EURCHF | BUY 58 | BUY 52 | - | AGREE | BUY | REJECTED |
| 10-28 06:00 | GBPJPY | SELL 58 | SELL 56 | - | AGREE | SELL | REJECTED |

The chart Trader 1 read last: `last_chart.png`. (numbers): no free vision model answered, so Trader 1 read the same chart from its numbers.

Full figures: `paper_forward.json`. Rules: `docs/PAPER_FORWARD.md` on main.
