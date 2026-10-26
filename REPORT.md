# PAPER FORWARD TEST — NOT REAL MONEY

Updated 2026-10-26 13:01 UTC · mode `PAPER_FORWARD` · profile `PAPER-FORWARD-200K` · shift started 2026-10-26 10:45 UTC · decision system `dual_ai`

Research status (historical, unchanged): **NO EDGE — DO NOT TRADE (historical research; this test measures forward)**. This run measures the system forward; it is not evidence of an edge until it has a sample and the forward-eligibility rules say so.

## The rule that trades: a trade only when both AIs agree

| Trades | Wins | Losses | Win rate | Net P&L | Expectancy | Profit factor | Max drawdown |
|---|---|---|---|---|---|---|---|
| 104 (adequate) | 44 | 60 | 42.3% | $-3,144.54 | -0.072R | 0.84 | $6,420.43 |

The 4 trade(s) of the old DEBATE rule, stopped in dual-ai-1.2.0, were removed from the paper account at the operator's request: their net $-1,416.51 was put back by a declared adjustment ($1,416.51). They stay in the journal (append-only), in none of the account's figures below.

## Paper account

| Account | Equity | P&L today | Total P&L | Drawdown | Open | Trades | Win rate | Expectancy | Profit factor | Risk | Bot |
|---|---|---|---|---|---|---|---|---|---|---|---|
| $200,000.00 | $196,702.48 | $-1,270.89 | $-3,297.52 | $-3,297.52 | 1 | 104 (adequate) | 42.3% | -0.072R | 0.84 | ACTIVE | RUNNING |

Equity includes declared operator adjustments of $1,416.51 (without them: $195,285.96); P&L today excludes them. `remove-retired-debate-rule-trades-2026-10-15`: operator: the 4 trades of the retired debate rule (dual-ai 1.1.0, stopped in 1.2.0) are removed from the paper account; they stay in the journal.

## Who lost it: the market or us

Losses 60, $-20,246.50: **the market 60** (at the stop, within the plan 54, by the time exit 5, stopped beyond the plan (a gap or the spread at the stop) 1) · **us 0**. Every closed trade is checked: the rules and the gate approved it, its data and the fill's quote were fresh, it was sized within the per-trade risk, both traders chose its side, it closed on time and not over a weekend, its costs were as planned. A check that cannot be read counts as ours.

Beyond the plan, the market's: 10-21 21:05 GBPJPY BUY lost $644.82 against a planned $498.95 in the rollover.

The 4 trade(s) taken out of the account, checked the same way: 4 ours (DESK: not both traders' choice (rule DEBATE, traders ['BUY', 'SELL'])).

## Last decisions (decision → risk → paper execution)

- 10-26 11:48 EURGBP BUY: AI DECISION → RISK APPROVED → PAPER EXECUTED
- 10-26 11:45 NZDUSD SELL: AI DECISION → RISK REJECTED — cost_to_risk: round-trip cost is 31.0% of the stop (max 25%): spread 0.00015 + commission and slippage; currency_conflict: SELL NZDUSD would bet against an open position: USDCAD SELL is short USD
- 10-26 11:30 USDCHF BUY: AI DECISION → RISK REJECTED — currency_conflict: BUY USDCHF would bet against an open position: USDCAD SELL is short USD
- 10-26 11:16 AUDUSD BUY: AI DECISION → RISK REJECTED — quote: age 100s at opening (max 90s), bid 0.70325, ask 0.70335
- 10-26 11:15 USDJPY BUY: AI DECISION → RISK REJECTED — currency_conflict: BUY USDJPY would bet against an open position: USDCAD SELL is short USD
- 10-26 11:02 GBPUSD SELL: AI DECISION → RISK REJECTED — currency_conflict: SELL GBPUSD would bet against an open position: USDCAD SELL is short USD; structure: H1 structure is range (mixed swings): no new position without a clear H1 trend (up HH+HL or down
- 10-26 11:00 EURUSD SELL: AI DECISION → RISK REJECTED — currency_conflict: SELL EURUSD would bet against an open position: EURCHF BUY is long EUR; USDCAD SELL is short USD
- 10-26 10:15 USDCAD SELL: AI DECISION → RISK APPROVED → PAPER EXECUTED
- 10-26 10:02 AUDUSD BUY: AI DECISION → RISK REJECTED — structure: H1 structure is range (mixed swings): no new position without a clear H1 trend (up HH+HL or down LH+LL)
- 10-26 10:00 USDJPY BUY: AI DECISION → RISK REJECTED — currency_conflict: BUY USDJPY would bet against an open position: GBPJPY SELL is long JPY
- 10-26 09:47 GBPUSD SELL: AI DECISION → RISK REJECTED — structure: H1 structure is range (mixed swings): no new position without a clear H1 trend (up HH+HL or down LH+LL)
- 10-26 09:45 EURUSD SELL: AI DECISION → RISK REJECTED — currency_conflict: SELL EURUSD would bet against an open position: EURCHF BUY is long EUR
- 10-26 09:30 AUDJPY BUY: AI DECISION → RISK REJECTED — currency_conflict: BUY AUDJPY would bet against an open position: GBPJPY SELL is long JPY
- 10-26 09:15 EURJPY BUY: AI DECISION → RISK REJECTED — currency_conflict: BUY EURJPY would bet against an open position: GBPJPY SELL is long JPY; structure: H1 structure is range (mixed swings): no new position without a clear H1 trend (up HH+HL or down L
- 10-26 07:46 GBPJPY SELL: AI DECISION → RISK APPROVED → PAPER EXECUTED
- 10-26 07:45 EURJPY SELL: AI DECISION → RISK REJECTED — currency_conflict: SELL EURJPY would bet against an open position: EURCHF BUY is long EUR
- 10-26 03:02 AUDUSD SELL: AI DECISION → RISK APPROVED → PAPER EXECUTED
- 10-26 03:00 USDJPY SELL: AI DECISION → RISK REJECTED — currency_conflict: SELL USDJPY would bet against an open position: USDCHF BUY is long USD; structure: H1 structure is range (mixed swings): no new position without a clear H1 trend (up HH+HL or down L
- 10-26 02:48 GBPUSD BUY: AI DECISION → RISK REJECTED — currency_conflict: BUY GBPUSD would bet against an open position: USDCHF BUY is long USD; structure: H1 structure is range (mixed swings): no new position without a clear H1 trend (up HH+HL or down LH
- 10-26 02:30 AUDJPY SELL: AI DECISION → RISK REJECTED — structure: H1 structure is range (mixed swings): no new position without a clear H1 trend (up HH+HL or down LH+LL)

## Latest decisions, NO TRADE included (2806 so far)

- 10-26 13:00 USDCHF NO_TRADE: risk engine: trading_calendar (Monday 13:00 UTC: no new position from 12:00 to 16:00 UTC): the model was not consulted
- 10-26 13:00 USDCAD NO_TRADE: blocked before consulting the model: EXPOSURE: a USDCAD position is already open
- 10-26 12:45 AUDUSD NO_TRADE: risk engine: trading_calendar (Monday 12:45 UTC: no new position from 12:00 to 16:00 UTC); open_positions (3 open, max 3): the model was not consulted
- 10-26 12:45 USDJPY NO_TRADE: risk engine: trading_calendar (Monday 12:45 UTC: no new position from 12:00 to 16:00 UTC); open_positions (3 open, max 3): the model was not consulted
- 10-26 12:30 GBPUSD NO_TRADE: risk engine: trading_calendar (Monday 12:30 UTC: no new position from 12:00 to 16:00 UTC); open_positions (3 open, max 3): the model was not consulted
- 10-26 12:30 EURUSD NO_TRADE: risk engine: trading_calendar (Monday 12:30 UTC: no new position from 12:00 to 16:00 UTC); open_positions (3 open, max 3); currency_exposure (2 open positions share a currency, max 2): the model was n
- 10-26 12:15 AUDJPY NO_TRADE: risk engine: trading_calendar (Monday 12:15 UTC: no new position from 12:00 to 16:00 UTC); open_positions (3 open, max 3); gate_open_risk (the hard risk gate's open-risk room 408.23 is less than the n
- 10-26 12:15 EURCHF NO_TRADE: blocked before consulting the model: EXPOSURE: a EURCHF position is already open
- 10-26 12:00 GBPJPY NO_TRADE: risk engine: trading_calendar (Monday 12:00 UTC: no new position from 12:00 to 16:00 UTC); open_positions (3 open, max 3); gate_open_risk (the hard risk gate's open-risk room 288.29 is less than the n
- 10-26 12:00 EURJPY NO_TRADE: risk engine: trading_calendar (Monday 12:00 UTC: no new position from 12:00 to 16:00 UTC); open_positions (3 open, max 3); currency_exposure (2 open positions share a currency, max 2): the model was n
- 10-26 11:48 EURGBP BUY: BUY EURGBP on M15: AGREE: Trader 1 (xiaomi/mimo-v2.6-pro) BUY 58: Price swept the heavily-touched equal-low cluster at 0.83835/0.83838 and is bouncing from the bottom of the M15 range with a bullish l
- 10-26 11:45 NZDUSD SELL: SELL NZDUSD on M15: AGREE: Trader 1 (xiaomi/mimo-v2.6-pro) SELL 52: M15 shows four consecutive bearish BOS with bearish displacement and price below today's low, confirming bearish intraday structure.

## Open paper positions

| Symbol | Side | Qty | Entry | Stop | Target | P&L |
|---|---|---|---|---|---|---|
| USDCAD | SELL | 3.83 | 1.4014149999999999 | 1.4028 | 1.3994 | $-152.99 |

## Closed paper trades (latest 20)

| Closed | Symbol | Side | Net | R | Costs | Exit | Source | Rule | Lost to |
|---|---|---|---|---|---|---|---|---|---|
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
| 10-23 06:46 | USDCHF | SELL | $-417.00 | -0.84 | $61.13 | STOP | DUAL_AI | AGREE | the market |
| 10-23 06:22 | EURJPY | SELL | $-171.48 | -0.70 | $37.01 | STOP | DUAL_AI | AGREE | the market |
| 10-23 02:42 | EURCHF | SELL | $-402.83 | -0.81 | $81.83 | STOP | DUAL_AI | AGREE | the market |
| 10-23 02:01 | GBPJPY | SELL | $-457.54 | -0.92 | $25.74 | STOP | DUAL_AI | AGREE | the market |
| 10-23 01:35 | AUDJPY | SELL | $-431.20 | -0.86 | $45.54 | STOP | DUAL_AI | AGREE | the market |
| 10-22 22:40 | USDJPY | SELL | $428.74 | +1.73 | $51.43 | TARGET | DUAL_AI | AGREE | - |
| 10-22 17:32 | USDJPY | SELL | $-198.17 | -0.79 | $25.98 | STOP | DUAL_AI | AGREE | the market |
| 10-22 16:52 | EURCHF | BUY | $-430.76 | -0.86 | $62.40 | STOP | DUAL_AI | AGREE | the market |
| 10-22 16:05 | GBPUSD | SELL | $-435.09 | -0.87 | $56.70 | STOP | DUAL_AI | AGREE | the market |
| 10-22 14:07 | USDCAD | BUY | $-438.56 | -0.88 | $54.88 | STOP | DUAL_AI | AGREE | the market |

## Dual AI desk (two OpenRouter traders: free, or the paid trial while it runs; a trade only when they agree)

OpenRouter `READY` · key set · trader 1 `nvidia/nemotron-3.5-super-vl:free` · trader 2 `dots-studio/dots-3-note-preview:free` · debate `xingchen-agi/xing4.0-29b-a4b:free` · calls today 21/900

Paid trial `paid-trial-2026-10-26` (2026-10-23T14:00:00Z to 2026-10-31T00:00:00Z): ACTIVE · trader 1 `xiaomi/mimo-v2.6-pro` asked first · trader 2 `anthropic/claude-haiku-5.5` asked first · spent $0.18 of $9.00, today $0.17 of $1.80 (the key's own reading) · trader 2 not asked: anthropic/claude-haiku-5.5 lists input_cache_write_1h at 2e-07, above the declared 0

Agreement trades 104 (adequate) · wins 44 · losses 60 · net $-3,144.54 · expectancy -0.072R · profit factor 0.84 · old DEBATE rule (stopped in dual-ai-1.2.0): 4 trade(s), net $-1,416.51, removed from the account

Disagreements (not traded; the debate runs in shadow): 118 · the debate's pick if taken: 111 resolved (adequate), expectancy -0.137R · the side it rejected if taken: 116 resolved (adequate), expectancy -0.241R

Exits in shadow (the same trades, followed again; measured, never traded): break-even at +1R -0.118R vs -0.065R as taken (86, adequate) · held 24 h +0.022R vs -0.065R as taken (86, adequate) · stop and target twice as far +0.001R vs -0.065R as taken (86, adequate) · closed at 8 h (the exit before dual-ai 1.7.0) -0.206R vs -0.199R as taken (32, adequate)

Trader 2's own levels in shadow (a trade is on Trader 1's since dual-ai 1.10.0; measured, never traded): none resolved yet

Trades taken by session (UTC): ASIA 45 resolved (adequate), expectancy -0.206R · LONDON 30 resolved (adequate), expectancy +0.163R · OVERLAP 8 resolved (insufficient), expectancy -0.382R · NEW_YORK 17 resolved (insufficient), expectancy +0.147R · LATE 3 resolved (insufficient), expectancy -1.106R

| Time | Symbol | Trader 1 | Trader 2 | Debate (shadow) | Rule | Final | Risk |
|---|---|---|---|---|---|---|---|
| 10-26 13:00 | USDCHF | -  | -  | - | NOT_ASKED | NO_TRADE | - |
| 10-26 13:00 | USDCAD | -  | -  | - | NOT_ASKED | NO_TRADE | - |
| 10-26 12:45 | AUDUSD | -  | -  | - | NOT_ASKED | NO_TRADE | - |
| 10-26 12:45 | USDJPY | -  | -  | - | NOT_ASKED | NO_TRADE | - |
| 10-26 12:30 | GBPUSD | -  | -  | - | NOT_ASKED | NO_TRADE | - |
| 10-26 12:30 | EURUSD | -  | -  | - | NOT_ASKED | NO_TRADE | - |
| 10-26 12:15 | AUDJPY | -  | -  | - | NOT_ASKED | NO_TRADE | - |
| 10-26 12:15 | EURCHF | -  | -  | - | NOT_ASKED | NO_TRADE | - |
| 10-26 12:00 | GBPJPY | -  | -  | - | NOT_ASKED | NO_TRADE | - |
| 10-26 12:00 | EURJPY | -  | -  | - | NOT_ASKED | NO_TRADE | - |
| 10-26 11:48 | EURGBP | BUY 58 | BUY 62 | - | AGREE | BUY | APPROVED |
| 10-26 11:45 | NZDUSD | SELL 52 | SELL 65 | - | AGREE | SELL | REJECTED |

The chart Trader 1 read last: `last_chart.png`. (numbers): no free vision model answered, so Trader 1 read the same chart from its numbers.

Full figures: `paper_forward.json`. Rules: `docs/PAPER_FORWARD.md` on main.
