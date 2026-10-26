# PAPER FORWARD TEST — NOT REAL MONEY

Updated 2026-10-26 10:45 UTC · mode `PAPER_FORWARD` · profile `PAPER-FORWARD-200K` · shift started 2026-10-26 05:10 UTC · decision system `dual_ai`

Research status (historical, unchanged): **NO EDGE — DO NOT TRADE (historical research; this test measures forward)**. This run measures the system forward; it is not evidence of an edge until it has a sample and the forward-eligibility rules say so.

## The rule that trades: a trade only when both AIs agree

| Trades | Wins | Losses | Win rate | Net P&L | Expectancy | Profit factor | Max drawdown |
|---|---|---|---|---|---|---|---|
| 102 (adequate) | 44 | 58 | 43.1% | $-2,312.66 | -0.057R | 0.88 | $5,593.34 |

The 4 trade(s) of the old DEBATE rule, stopped in dual-ai-1.2.0, were removed from the paper account at the operator's request: their net $-1,416.51 was put back by a declared adjustment ($1,416.51). They stay in the journal (append-only), in none of the account's figures below.

## Paper account

| Account | Equity | P&L today | Total P&L | Drawdown | Open | Trades | Win rate | Expectancy | Profit factor | Risk | Bot |
|---|---|---|---|---|---|---|---|---|---|---|---|
| $200,000.00 | $197,734.02 | $-239.34 | $-2,265.98 | $-2,265.98 | 2 | 102 (adequate) | 43.1% | -0.057R | 0.88 | ACTIVE | RUNNING |

Equity includes declared operator adjustments of $1,416.51 (without them: $196,317.51); P&L today excludes them. `remove-retired-debate-rule-trades-2026-10-15`: operator: the 4 trades of the retired debate rule (dual-ai 1.1.0, stopped in 1.2.0) are removed from the paper account; they stay in the journal.

## Who lost it: the market or us

Losses 58, $-19,414.63: **the market 58** (at the stop, within the plan 52, by the time exit 5, stopped beyond the plan (a gap or the spread at the stop) 1) · **us 0**. Every closed trade is checked: the rules and the gate approved it, its data and the fill's quote were fresh, it was sized within the per-trade risk, both traders chose its side, it closed on time and not over a weekend, its costs were as planned. A check that cannot be read counts as ours.

Beyond the plan, the market's: 10-21 21:05 GBPJPY BUY lost $644.82 against a planned $498.95 in the rollover.

The 4 trade(s) taken out of the account, checked the same way: 4 ours (DESK: not both traders' choice (rule DEBATE, traders ['BUY', 'SELL'])).

## Last decisions (decision → risk → paper execution)

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
- 10-26 02:18 GBPJPY SELL: AI DECISION → RISK REJECTED — structure: H1 structure is range (mixed swings): no new position without a clear H1 trend (up HH+HL or down LH+LL)
- 10-26 02:15 EURJPY SELL: AI DECISION → RISK REJECTED — currency_conflict: SELL EURJPY would bet against an open position: EURCHF BUY is long EUR
- 10-26 02:03 EURGBP BUY: AI DECISION → RISK REJECTED — structure: H1 structure is range (mixed swings): no new position without a clear H1 trend (up HH+HL or down LH+LL)
- 10-26 02:00 NZDUSD BUY: AI DECISION → RISK REJECTED — reward_risk: 1.04 vs minimum 1.2; currency_conflict: BUY NZDUSD would bet against an open position: USDCHF BUY is long USD; structure: H1 structure is range (mixed swings): no new position without a c
- 10-26 01:51 USDCHF BUY: AI DECISION → RISK APPROVED → PAPER EXECUTED
- 10-26 01:34 AUDUSD BUY: AI DECISION → RISK REJECTED — cost_to_risk: round-trip cost is 29.2% of the stop (max 25%): spread 0.0001 + commission and slippage
- 10-26 01:30 USDJPY SELL: AI DECISION → RISK REJECTED — structure: H1 structure is range (mixed swings): no new position without a clear H1 trend (up HH+HL or down LH+LL)

## Latest decisions, NO TRADE included (2788 so far)

- 10-26 10:30 EURGBP NO_TRADE: risk engine: open_positions (3 open, max 3): the model was not consulted
- 10-26 10:30 NZDUSD NO_TRADE: risk engine: open_positions (3 open, max 3): the model was not consulted
- 10-26 10:18 USDCHF NO_TRADE: risk engine: open_positions (3 open, max 3); gate_open_risk (the hard risk gate's open-risk room 376.56 is less than the next trade's risk 495.29: it would refuse the trade): the model was not consult
- 10-26 10:15 USDCAD SELL: SELL USDCAD on M15: AGREE: Trader 1 (xiaomi/mimo-v2.6-pro) SELL 58: Both timeframes are bearish and price is stalling at a heavy resistance cluster (1.40154 x5, 1.40183 x4) just below the H4 bearish B
- 10-26 10:02 AUDUSD BUY: BUY AUDUSD on M15: AGREE: Trader 1 (xiaomi/mimo-v2.6-pro) BUY 62: Both timeframes align bullish after a clean CHoCH and two bullish BOS, with an untested demand OB and stacked bullish FVGs below as su
- 10-26 10:00 USDJPY BUY: BUY USDJPY on M15: AGREE: Trader 1 (xiaomi/mimo-v2.6-pro) BUY 62: M15 shows a clean bullish structure with successive BOS and a tested demand block, and price has reclaimed the H4 bullish CHoCH level 
- 10-26 09:47 GBPUSD SELL: SELL GBPUSD on M15: AGREE: Trader 1 (xiaomi/mimo-v2.6-pro) SELL 68: Both timeframes agree on bearish structure with a fresh M15 BOS and H4 CHoCH/BOS, and price sits just above the day low with unteste
- 10-26 09:45 EURUSD SELL: SELL EURUSD on M15: AGREE: Trader 1 (xiaomi/mimo-v2.6-pro) SELL 55: Both timeframes are bearish and price is stalling under the 1.12171/1.12183 resistance cluster right where the H4 bearish CHoCH flip
- 10-26 09:30 AUDJPY BUY: BUY AUDJPY on M15: AGREE: Trader 1 (xiaomi/mimo-v2.6-pro) BUY 62: Four consecutive bullish BOS and a bullish H4 CHoCH give buyers the higher-probability side, with untested demand and bullish FVGs bel
- 10-26 09:30 EURCHF NO_TRADE: blocked before consulting the model: EXPOSURE: a EURCHF position is already open
- 10-26 09:19 GBPJPY NO_TRADE: blocked before consulting the model: EXPOSURE: a GBPJPY position is already open
- 10-26 09:15 EURJPY BUY: BUY EURJPY on M15: AGREE: Trader 1 (xiaomi/mimo-v2.6-pro) BUY 55: Fresh bullish CHoCH on both M15 and H4 plus a higher-low sequence, untested demand OB and an open bullish FVG below give a clean long 

## Open paper positions

| Symbol | Side | Qty | Entry | Stop | Target | P&L |
|---|---|---|---|---|---|---|
| USDCAD | SELL | 3.83 | 1.4014149999999999 | 1.4028 | 1.3994 | $-16.40 |
| EURCHF | BUY | 2.48 | 0.9244 | 0.9231 | 0.9263 | $63.08 |

## Closed paper trades (latest 20)

| Closed | Symbol | Side | Net | R | Costs | Exit | Source | Rule | Lost to |
|---|---|---|---|---|---|---|---|---|---|
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
| 10-22 11:06 | GBPJPY | SELL | $631.22 | +1.27 | $57.92 | TARGET | DUAL_AI | AGREE | - |
| 10-22 11:02 | AUDJPY | SELL | $574.01 | +1.16 | $75.68 | TARGET | DUAL_AI | AGREE | - |

## Dual AI desk (two OpenRouter traders: free, or the paid trial while it runs; a trade only when they agree)

OpenRouter `READY` · key set · trader 1 `nvidia/nemotron-3.5-super-vl:free` · trader 2 `xingchen-agi/xing4.0-29b-a4b:free` · debate `dots-studio/dots-3-note-preview:free` · calls today 32/900

Paid trial `paid-trial-2026-10-26` (2026-10-23T14:00:00Z to 2026-10-31T00:00:00Z): ACTIVE · trader 1 `xiaomi/mimo-v2.6-pro` asked first · trader 2 `anthropic/claude-haiku-5.5` asked first · spent $0.16 of $9.00, today $0.16 of $1.80 (the key's own reading) · trader 2 not asked: anthropic/claude-haiku-5.5 lists web_search at 0.01, above the declared 0

Agreement trades 102 (adequate) · wins 44 · losses 58 · net $-2,312.66 · expectancy -0.057R · profit factor 0.88 · old DEBATE rule (stopped in dual-ai-1.2.0): 4 trade(s), net $-1,416.51, removed from the account

Disagreements (not traded; the debate runs in shadow): 118 · the debate's pick if taken: 111 resolved (adequate), expectancy -0.137R · the side it rejected if taken: 116 resolved (adequate), expectancy -0.241R

Exits in shadow (the same trades, followed again; measured, never traded): break-even at +1R -0.118R vs -0.065R as taken (86, adequate) · held 24 h +0.022R vs -0.065R as taken (86, adequate) · stop and target twice as far +0.001R vs -0.065R as taken (86, adequate) · closed at 8 h (the exit before dual-ai 1.7.0) -0.206R vs -0.199R as taken (32, adequate)

Trader 2's own levels in shadow (a trade is on Trader 1's since dual-ai 1.10.0; measured, never traded): none resolved yet

Trades taken by session (UTC): ASIA 45 resolved (adequate), expectancy -0.206R · LONDON 30 resolved (adequate), expectancy +0.163R · OVERLAP 8 resolved (insufficient), expectancy -0.382R · NEW_YORK 17 resolved (insufficient), expectancy +0.147R · LATE 3 resolved (insufficient), expectancy -1.106R

| Time | Symbol | Trader 1 | Trader 2 | Debate (shadow) | Rule | Final | Risk |
|---|---|---|---|---|---|---|---|
| 10-26 10:30 | EURGBP | -  | -  | - | NOT_ASKED | NO_TRADE | - |
| 10-26 10:30 | NZDUSD | -  | -  | - | NOT_ASKED | NO_TRADE | - |
| 10-26 10:18 | USDCHF | -  | -  | - | NOT_ASKED | NO_TRADE | - |
| 10-26 10:15 | USDCAD | SELL 58 | SELL 65 | - | AGREE | SELL | APPROVED |
| 10-26 10:02 | AUDUSD | BUY 62 | BUY 60 | - | AGREE | BUY | REJECTED |
| 10-26 10:00 | USDJPY | BUY 62 | BUY 68 | - | AGREE | BUY | REJECTED |
| 10-26 09:47 | GBPUSD | SELL 68 | SELL 65 | - | AGREE | SELL | REJECTED |
| 10-26 09:45 | EURUSD | SELL 55 | SELL 60 | - | AGREE | SELL | REJECTED |
| 10-26 09:30 | AUDJPY | BUY 62 | BUY 65 | - | AGREE | BUY | REJECTED |
| 10-26 09:30 | EURCHF | -  | -  | - | NOT_ASKED | NO_TRADE | - |
| 10-26 09:19 | GBPJPY | -  | -  | - | NOT_ASKED | NO_TRADE | - |
| 10-26 09:15 | EURJPY | BUY 55 | BUY 60 | - | AGREE | BUY | REJECTED |

The chart Trader 1 read last: `last_chart.png`. (numbers): no free vision model answered, so Trader 1 read the same chart from its numbers.

Full figures: `paper_forward.json`. Rules: `docs/PAPER_FORWARD.md` on main.
