# PAPER FORWARD TEST — NOT REAL MONEY

Updated 2026-10-29 03:18 UTC · mode `PAPER_FORWARD` · profile `PAPER-FORWARD-200K` · shift started 2026-10-29 00:18 UTC · decision system `dual_ai`

Research status (historical, unchanged): **NO EDGE — DO NOT TRADE (historical research; this test measures forward)**. This run measures the system forward; it is not evidence of an edge until it has a sample and the forward-eligibility rules say so.

## The new account: the setup trading now (from 2026-10-26 16:22 UTC)

dual-ai 1.10.0 (a trade on Trader 1's levels) with both traders paid (paid-trial 1.2.0: Trader 1 xiaomi/mimo-v2.6-pro, Trader 2 anthropic/claude-haiku-5.5). Opened at the owner's request (2026-10-27): owner: a new account for the new setup, from the first shift that ran it; the account before it is kept and reported apart.

| Start | Equity | Total P&L | Closed | Open | Trades | Win rate | Expectancy | Profit factor |
|---|---|---|---|---|---|---|---|---|
| $200,000.00 | $198,225.01 | $-1,774.99 | $-1,476.23 | 3 ($-298.76) | 17 (insufficient) | 41.2% | -0.090R | 0.57 |

Before it, kept and apart (not in the figures above): 106 trades, net $-3,759.41. The whole paper journal, which the hard gate and the risk engine still guard, is under Paper account below; nothing in it was moved or removed.

## The rule that trades: a trade only when both AIs agree

| Trades | Wins | Losses | Win rate | Net P&L | Expectancy | Profit factor | Max drawdown |
|---|---|---|---|---|---|---|---|
| 123 (adequate) | 51 | 72 | 41.5% | $-5,235.64 | -0.087R | 0.78 | $8,528.98 |

The 4 trade(s) of the old DEBATE rule, stopped in dual-ai-1.2.0, were removed from the paper account at the operator's request: their net $-1,416.51 was put back by a declared adjustment ($1,416.51). They stay in the journal (append-only), in none of the account's figures below.

## Paper account

| Account | Equity | P&L today | Total P&L | Drawdown | Open | Trades | Win rate | Expectancy | Profit factor | Risk | Bot |
|---|---|---|---|---|---|---|---|---|---|---|---|
| $200,000.00 | $194,465.60 | $-455.89 | $-5,534.40 | $-5,534.40 | 3 | 123 (adequate) | 41.5% | -0.087R | 0.78 | ACTIVE | RUNNING |

Equity includes declared operator adjustments of $1,416.51 (without them: $193,049.09); P&L today excludes them. `remove-retired-debate-rule-trades-2026-10-15`: operator: the 4 trades of the retired debate rule (dual-ai 1.1.0, stopped in 1.2.0) are removed from the paper account; they stay in the journal.

## Who lost it: the market or us

Losses 72, $-24,326.80: **the market 72** (at the stop, within the plan 65, by the time exit 5, stopped beyond the plan (a gap or the spread at the stop) 2) · **us 0**. Every closed trade is checked: the rules and the gate approved it, its data and the fill's quote were fresh, it was sized within the per-trade risk, both traders chose its side, it closed on time and not over a weekend, its costs were as planned. A check that cannot be read counts as ours.

Beyond the plan, the market's: 10-21 21:05 GBPJPY BUY lost $644.82 against a planned $498.95 in the rollover.

Beyond the plan, the market's: 10-28 13:35 GBPUSD SELL lost $509.02 against a planned $489.30.

The 4 trade(s) taken out of the account, checked the same way: 4 ours (DESK: not both traders' choice (rule DEBATE, traders ['BUY', 'SELL'])).

## Last decisions (decision → risk → paper execution)

- 10-29 02:45 EURGBP SELL: AI DECISION → RISK APPROVED → PAPER EXECUTED
- 10-29 02:16 AUDUSD BUY: AI DECISION → RISK APPROVED → PAPER EXECUTED
- 10-29 02:00 GBPUSD SELL: AI DECISION → RISK REJECTED — currency_conflict: SELL GBPUSD would bet against an open position: NZDUSD BUY is short USD
- 10-29 02:00 EURUSD SELL: AI DECISION → RISK REJECTED — currency_conflict: SELL EURUSD would bet against an open position: NZDUSD BUY is short USD
- 10-29 01:31 GBPJPY BUY: AI DECISION → RISK APPROVED → PAPER EXECUTED
- 10-29 01:30 EURJPY BUY: AI DECISION → RISK REJECTED — currency_conflict: BUY EURJPY would bet against an open position: EURCHF SELL is short EUR
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

## Latest decisions, NO TRADE included (3301 so far)

- 10-29 03:15 AUDJPY NO_TRADE: risk engine: open_positions (3 open, max 3): the model was not consulted
- 10-29 03:15 EURCHF NO_TRADE: risk engine: open_positions (3 open, max 3): the model was not consulted
- 10-29 03:00 GBPJPY NO_TRADE: risk engine: open_positions (3 open, max 3): the model was not consulted
- 10-29 03:00 EURJPY NO_TRADE: risk engine: open_positions (3 open, max 3): the model was not consulted
- 10-29 02:45 EURGBP SELL: SELL EURGBP on M15: AGREE: Trader 1 (xiaomi/mimo-v2.6-pro) SELL 58: Both timeframes are bearish with fresh bearish BOS below 0.83662 and an untested supply block overhead at 0.8371-0.8372, so the sell
- 10-29 02:45 NZDUSD NO_TRADE: blocked before consulting the model: EXPOSURE: a NZDUSD position is already open
- 10-29 02:30 USDCHF NO_TRADE: risk engine: currency_exposure (2 open positions share a currency, max 2): the model was not consulted
- 10-29 02:30 USDCAD NO_TRADE: risk engine: currency_exposure (2 open positions share a currency, max 2): the model was not consulted
- 10-29 02:16 AUDUSD BUY: BUY AUDUSD on M15: AGREE: Trader 1 (xiaomi/mimo-v2.6-pro) BUY 62: Trend is up on both timeframes after a bullish CHoCH/BOS sequence, and price has pulled back into the tested demand order block and bu
- 10-29 02:15 USDJPY NO_TRADE: the traders disagree (Trader 1 BUY 58, Trader 2 SELL 52): no trade unless both choose the same side; the debate (dots-studio/dots-3-note-preview:free) would have chosen SELL: followed forward in shado
- 10-29 02:00 GBPUSD SELL: SELL GBPUSD on M15: AGREE: Trader 1 (xiaomi/mimo-v2.6-pro) SELL 58: Trade with the H4 downtrend: sell the retrace into the 1.3330-1.3338 supply band / PDH where equal highs and swept highs show trappe
- 10-29 02:00 EURUSD SELL: SELL EURUSD on M15: AGREE: Trader 1 (xiaomi/mimo-v2.6-pro) SELL 66: Both timeframes are bearish and the M15 just printed a bearish CHoCH/BOS sequence, so the bounce to 1.11582 is a sellable retrace in

## Open paper positions

| Symbol | Side | Qty | Entry | Stop | Target | P&L |
|---|---|---|---|---|---|---|
| EURGBP | SELL | 3.41 | 0.8366300000000001 | 0.83748 | 0.8356 | $-59.07 |
| AUDUSD | BUY | 3.77 | 0.7059599999999999 | 0.70495 | 0.7072 | $-154.57 |
| NZDUSD | BUY | 1.12 | 0.562885 | 0.56103 | 0.5658 | $-85.12 |

## Closed paper trades (latest 20)

| Closed | Symbol | Side | Net | R | Costs | Exit | Source | Rule | Lost to |
|---|---|---|---|---|---|---|---|---|---|
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
| 10-27 06:15 | USDJPY | SELL | $-418.51 | -0.85 | $50.09 | STOP | DUAL_AI | AGREE | the market |
| 10-27 05:23 | GBPUSD | SELL | $278.49 | +1.14 | $38.75 | TARGET | DUAL_AI | AGREE | - |
| 10-27 01:27 | AUDJPY | SELL | $-104.31 | -0.86 | $25.69 | STOP | DUAL_AI | AGREE | the market |
| 10-26 17:23 | USDCHF | BUY | $-207.12 | -0.85 | $38.59 | STOP | DUAL_AI | AGREE | the market |
| 10-26 13:06 | USDCAD | SELL | $-407.76 | -0.82 | $73.23 | STOP | DUAL_AI | AGREE | the market |
| 10-26 12:54 | EURGBP | BUY | $-420.89 | -0.85 | $86.86 | STOP | DUAL_AI | AGREE | the market |

## Dual AI desk (two OpenRouter traders: free, or the paid trial while it runs; a trade only when they agree)

OpenRouter `READY` · key set · trader 1 `nvidia/nemotron-3.5-super-vl:free` · trader 2 `thinkingmachines/inkling-small:free` · debate `google/gemma-4-31b-it:free` · calls today 17/900

Paid trial `paid-trial-2026-10-26` (2026-10-23T14:00:00Z to 2026-10-31T00:00:00Z): ACTIVE · trader 1 `xiaomi/mimo-v2.6-pro` asked first · trader 2 `anthropic/claude-haiku-5.5` asked first · spent $0.70 of $9.00, today $0.05 of $1.80 (the key's own reading)

Agreement trades 123 (adequate) · wins 51 · losses 72 · net $-5,235.64 · expectancy -0.087R · profit factor 0.78 · old DEBATE rule (stopped in dual-ai-1.2.0): 4 trade(s), net $-1,416.51, removed from the account

Disagreements (not traded; the debate runs in shadow): 139 · the debate's pick if taken: 119 resolved (adequate), expectancy -0.143R · the side it rejected if taken: 124 resolved (adequate), expectancy -0.227R

Exits in shadow (the same trades, followed again; measured, never traded): break-even at +1R -0.132R vs -0.087R as taken (102, adequate) · held 24 h -0.014R vs -0.087R as taken (102, adequate) · stop and target twice as far +0.023R vs -0.087R as taken (102, adequate) · closed at 8 h (the exit before dual-ai 1.7.0) -0.239R vs -0.202R as taken (48, adequate)

Trader 2's own levels in shadow (a trade is on Trader 1's since dual-ai 1.10.0; measured, never traded): +0.484R vs +0.309R as taken (10, insufficient)

Trades taken by session (UTC): ASIA 51 resolved (adequate), expectancy -0.216R · LONDON 36 resolved (adequate), expectancy +0.063R · OVERLAP 8 resolved (insufficient), expectancy -0.382R · NEW_YORK 21 resolved (insufficient), expectancy +0.168R · LATE 3 resolved (insufficient), expectancy -1.106R

| Time | Symbol | Trader 1 | Trader 2 | Debate (shadow) | Rule | Final | Risk |
|---|---|---|---|---|---|---|---|
| 10-29 03:15 | AUDJPY | -  | -  | - | NOT_ASKED | NO_TRADE | - |
| 10-29 03:15 | EURCHF | -  | -  | - | NOT_ASKED | NO_TRADE | - |
| 10-29 03:00 | GBPJPY | -  | -  | - | NOT_ASKED | NO_TRADE | - |
| 10-29 03:00 | EURJPY | -  | -  | - | NOT_ASKED | NO_TRADE | - |
| 10-29 02:45 | EURGBP | SELL 58 | SELL 55 | - | AGREE | SELL | APPROVED |
| 10-29 02:45 | NZDUSD | -  | -  | - | NOT_ASKED | NO_TRADE | - |
| 10-29 02:30 | USDCHF | -  | -  | - | NOT_ASKED | NO_TRADE | - |
| 10-29 02:30 | USDCAD | -  | -  | - | NOT_ASKED | NO_TRADE | - |
| 10-29 02:16 | AUDUSD | BUY 62 | BUY 55 | - | AGREE | BUY | APPROVED |
| 10-29 02:15 | USDJPY | BUY 58 | SELL 52 | SELL | DISAGREE | NO_TRADE | - |
| 10-29 02:00 | GBPUSD | SELL 58 | SELL 55 | - | AGREE | SELL | REJECTED |
| 10-29 02:00 | EURUSD | SELL 66 | SELL 55 | - | AGREE | SELL | REJECTED |

The chart Trader 1 read last: `last_chart.png`. (numbers): no free vision model answered, so Trader 1 read the same chart from its numbers.

Full figures: `paper_forward.json`. Rules: `docs/PAPER_FORWARD.md` on main.
