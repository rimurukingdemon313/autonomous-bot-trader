# PAPER FORWARD TEST — NOT REAL MONEY

Updated 2026-10-19 00:33 UTC · mode `PAPER_FORWARD` · profile `PAPER-FORWARD-200K` · shift started 2026-10-18 23:48 UTC · decision system `dual_ai`

Research status (historical, unchanged): **NO EDGE — DO NOT TRADE (historical research; this test measures forward)**. This run measures the system forward; it is not evidence of an edge until it has a sample and the forward-eligibility rules say so.

## The rule that trades: a trade only when both AIs agree

| Trades | Wins | Losses | Win rate | Net P&L | Expectancy | Profit factor | Max drawdown |
|---|---|---|---|---|---|---|---|
| 41 (adequate) | 22 | 19 | 53.7% | $1,912.63 | +0.115R | 1.28 | $1,928.96 |

The 4 trade(s) of the old DEBATE rule, stopped in dual-ai-1.2.0, were removed from the paper account at the operator's request: their net $-1,416.51 was put back by a declared adjustment ($1,416.51). They stay in the journal (append-only), in none of the account's figures below.

## Paper account

| Account | Equity | P&L today | Total P&L | Drawdown | Open | Trades | Win rate | Expectancy | Profit factor | Risk | Bot |
|---|---|---|---|---|---|---|---|---|---|---|---|
| $200,000.00 | $201,766.76 | $-145.87 | $1,766.76 | $0.00 | 2 | 41 (adequate) | 53.7% | +0.115R | 1.28 | ACTIVE | RUNNING |

Equity includes declared operator adjustments of $1,416.51 (without them: $200,350.25); P&L today excludes them. `remove-retired-debate-rule-trades-2026-10-15`: operator: the 4 trades of the retired debate rule (dual-ai 1.1.0, stopped in 1.2.0) are removed from the paper account; they stay in the journal.

## Last decisions (decision → risk → paper execution)

- 10-19 00:15 AUDUSD BUY: AI DECISION → RISK APPROVED → PAPER EXECUTED
- 10-19 00:00 GBPUSD BUY: AI DECISION → RISK APPROVED → PAPER EXECUTED
- 10-16 19:45 AUDJPY BUY: AI DECISION → RISK REJECTED — reward_risk: 1.19 vs minimum 1.2; weekend_carry: held up to 480 min it could still be open at the Friday close (Fri 17:00 New York)
- 10-16 19:45 EURCHF SELL: AI DECISION → RISK REJECTED — weekend_carry: held up to 480 min it could still be open at the Friday close (Fri 17:00 New York)
- 10-16 19:15 EURJPY BUY: AI DECISION → RISK REJECTED — weekend_carry: held up to 480 min it could still be open at the Friday close (Fri 17:00 New York)
- 10-16 19:00 EURGBP BUY: AI DECISION → RISK REJECTED — weekend_carry: held up to 480 min it could still be open at the Friday close (Fri 17:00 New York)
- 10-16 19:00 NZDUSD SELL: AI DECISION → RISK REJECTED — weekend_carry: held up to 480 min it could still be open at the Friday close (Fri 17:00 New York)
- 10-16 18:45 USDCAD SELL: AI DECISION → RISK REJECTED — weekend_carry: held up to 480 min it could still be open at the Friday close (Fri 17:00 New York)
- 10-16 18:30 AUDUSD SELL: AI DECISION → RISK REJECTED — cost_to_risk: round-trip cost is 31.7% of the stop (max 25%): spread 0.0001 + commission and slippage; weekend_carry: held up to 480 min it could still be open at the Friday close (Fri 17:00 New York)
- 10-16 18:30 USDJPY SELL: AI DECISION → RISK REJECTED — cost_to_risk: round-trip cost is 30.2% of the stop (max 25%): spread 0.01 + commission and slippage; weekend_carry: held up to 480 min it could still be open at the Friday close (Fri 17:00 New York)
- 10-16 18:15 GBPUSD SELL: AI DECISION → RISK REJECTED — reward_risk: 0.97 vs minimum 1.2; weekend_carry: held up to 480 min it could still be open at the Friday close (Fri 17:00 New York)
- 10-16 18:15 EURUSD SELL: AI DECISION → RISK REJECTED — weekend_carry: held up to 480 min it could still be open at the Friday close (Fri 17:00 New York)
- 10-16 17:45 AUDJPY BUY: AI DECISION → RISK REJECTED — stop_distance: stop 0.046 vs 3.0 x spread 0.018; spread: spread is 39.1% of the stop (max 25%); cost_to_risk: round-trip cost is 58.7% of the stop (max 25%): spread 0.018 + commission and slippage; we
- 10-16 17:30 GBPJPY BUY: AI DECISION → RISK REJECTED — reward_risk: 0.68 vs minimum 1.2; weekend_carry: held up to 480 min it could still be open at the Friday close (Fri 17:00 New York)
- 10-16 17:30 EURJPY SELL: AI DECISION → RISK REJECTED — weekend_carry: held up to 480 min it could still be open at the Friday close (Fri 17:00 New York)
- 10-16 17:15 EURGBP SELL: AI DECISION → RISK REJECTED — weekend_carry: held up to 480 min it could still be open at the Friday close (Fri 17:00 New York)
- 10-16 17:15 NZDUSD SELL: AI DECISION → RISK REJECTED — cost_to_risk: round-trip cost is 27.4% of the stop (max 25%): spread 0.00015 + commission and slippage; weekend_carry: held up to 480 min it could still be open at the Friday close (Fri 17:00 New York
- 10-16 16:45 USDCHF SELL: AI DECISION → RISK REJECTED — reward_risk: 0.72 vs minimum 1.2; weekend_carry: held up to 480 min it could still be open at the Friday close (Fri 17:00 New York)
- 10-16 16:30 AUDUSD SELL: AI DECISION → RISK REJECTED — weekend_carry: held up to 480 min it could still be open at the Friday close (Fri 17:00 New York)
- 10-16 16:30 USDJPY BUY: AI DECISION → RISK REJECTED — reward_risk: 0.25 vs minimum 1.2; weekend_carry: held up to 480 min it could still be open at the Friday close (Fri 17:00 New York)

## Latest decisions, NO TRADE included (1392 so far)

- 10-19 00:30 USDCHF NO_TRADE: market unavailable for a decision: risk engine: currency_exposure (2 open positions share a currency, max 2): the model was not consulted
- 10-19 00:30 USDCAD NO_TRADE: market unavailable for a decision: risk engine: currency_exposure (2 open positions share a currency, max 2): the model was not consulted
- 10-19 00:15 AUDUSD BUY: BUY AUDUSD on M15: AGREE: Trader 1 (nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free) BUY 70: Strong bullish BOS and untested demand zone on M15 suggest continuation upward; stop at 0.69609 would br
- 10-19 00:15 USDJPY NO_TRADE: the traders disagree (Trader 1 BUY 55, Trader 2 SELL 65): no trade unless both choose the same side; the debate (dots-studio/dots-3-note-preview:free) would have chosen BUY: followed forward in shadow
- 10-19 00:00 GBPUSD BUY: BUY GBPUSD on M15: AGREE: Trader 1 (nvidia/nemotron-3.5-super-vl:free) BUY 60: A fresh bullish CHoCH at 1.333 with bullish displacement shifts M15 momentum upward despite the prior downtrend. Entry at
- 10-19 00:00 EURUSD NO_TRADE: the traders disagree (Trader 1 SELL 56, Trader 2 BUY 65): no trade unless both choose the same side; the debate (dots-studio/dots-3-note-preview:free) would have chosen SELL: followed forward in shado
- 10-18 23:45 GBPJPY NO_TRADE: market unavailable for a decision: blocked before consulting the model: DATA_QUALITY: latest bar closed 2985 minutes ago; DATA_QUALITY: features missing: bar_body; STALE_DATA: last closed bar is 2985  [data: latest bar closed 2985 minutes ago]
- 10-18 23:45 EURJPY NO_TRADE: market unavailable for a decision: blocked before consulting the model: DATA_QUALITY: latest bar closed 2985 minutes ago; STALE_DATA: last closed bar is 2985 minutes old [data: latest bar closed 2985 minutes ago]
- 10-18 23:30 EURGBP NO_TRADE: market unavailable for a decision: blocked before consulting the model: DATA_QUALITY: latest bar closed 2970 minutes ago; DATA_QUALITY: features missing: bar_body; STALE_DATA: last closed bar is 2970  [data: latest bar closed 2970 minutes ago]
- 10-18 23:30 NZDUSD NO_TRADE: market unavailable for a decision: blocked before consulting the model: DATA_QUALITY: latest bar closed 2970 minutes ago; DATA_QUALITY: features missing: bar_body; STALE_DATA: last closed bar is 2970  [data: latest bar closed 2970 minutes ago]
- 10-18 23:15 USDCHF NO_TRADE: market unavailable for a decision: blocked before consulting the model: DATA_QUALITY: latest bar closed 3015 minutes ago; STALE_DATA: last closed bar is 3015 minutes old [data: latest bar closed 3015 minutes ago]
- 10-18 23:15 USDCAD NO_TRADE: market unavailable for a decision: blocked before consulting the model: DATA_QUALITY: latest bar closed 2955 minutes ago; STALE_DATA: last closed bar is 2955 minutes old [data: latest bar closed 2955 minutes ago]

## Open paper positions

| Symbol | Side | Qty | Entry | Stop | Target | P&L |
|---|---|---|---|---|---|---|
| AUDUSD | BUY | 2.28 | 0.6968599999999999 | 0.69605 | 0.69781 | $-2.28 |
| GBPUSD | BUY | 1.73 | 1.33367 | 1.33259 | 1.335 | $-143.59 |

## Closed paper trades (latest 20)

| Closed | Symbol | Side | Net | R | Costs | Exit | Source | Rule |
|---|---|---|---|---|---|---|---|---|
| 10-16 16:02 | NZDUSD | BUY | $-453.45 | -0.91 | $66.00 | STOP | DUAL_AI | AGREE |
| 10-16 12:36 | EURJPY | BUY | $-432.45 | -0.87 | $48.70 | STOP | DUAL_AI | AGREE |
| 10-16 12:38 | EURUSD | BUY | $-477.37 | -0.96 | $35.53 | STOP | DUAL_AI | AGREE |
| 10-16 10:25 | EURJPY | BUY | $422.27 | +0.85 | $64.90 | TARGET | DUAL_AI | AGREE |
| 10-16 10:04 | EURUSD | BUY | $459.54 | +0.92 | $53.28 | TARGET | DUAL_AI | AGREE |
| 10-16 08:05 | EURGBP | SELL | $129.31 | +0.26 | $81.01 | TIME | DUAL_AI | AGREE |
| 10-16 07:02 | AUDUSD | BUY | $840.45 | +1.68 | $77.58 | TARGET | DUAL_AI | AGREE |
| 10-16 03:49 | USDCAD | SELL | $451.28 | +0.91 | $77.18 | TARGET | DUAL_AI | AGREE |
| 10-16 02:05 | USDJPY | SELL | $494.39 | +0.99 | $77.59 | TARGET | DUAL_AI | AGREE |
| 10-16 01:09 | USDCAD | SELL | $-57.07 | -0.11 | $79.25 | TIME | DUAL_AI | AGREE |
| 10-16 00:47 | USDJPY | SELL | $-49.61 | -0.20 | $39.69 | TIME | DUAL_AI | AGREE |
| 10-15 22:53 | AUDJPY | BUY | $133.74 | +0.27 | $76.64 | TIME | DUAL_AI | AGREE |
| 10-15 16:48 | EURGBP | SELL | $155.71 | +0.63 | $42.44 | TIME | DUAL_AI | AGREE |
| 10-15 16:44 | GBPUSD | SELL | $-385.57 | -0.77 | $81.90 | STOP | DUAL_AI | AGREE |
| 10-15 14:11 | USDCAD | BUY | $-399.97 | -0.80 | $77.26 | STOP | DUAL_AI | AGREE |
| 10-15 14:01 | EURUSD | SELL | $-453.65 | -0.91 | $54.91 | STOP | DUAL_AI | AGREE |
| 10-15 13:59 | USDCAD | SELL | $650.69 | +1.31 | $88.09 | TARGET | DUAL_AI | AGREE |
| 10-15 12:02 | NZDUSD | SELL | $225.96 | +0.91 | $38.64 | TARGET | DUAL_AI | AGREE |
| 10-15 11:34 | EURJPY | BUY | $29.16 | +0.06 | $32.94 | TIME | DUAL_AI | AGREE |
| 10-15 08:05 | USDJPY | BUY | $-216.31 | -0.87 | $18.93 | STOP | DUAL_AI | AGREE |

## Dual AI desk (two free OpenRouter traders; a trade only when they agree)

OpenRouter `READY` · key set · trader 1 `nvidia/nemotron-3.5-super-vl:free` · trader 2 `nvidia/nemotron-3-ultra-550b-a55b:free` · debate `dots-studio/dots-3-note-preview:free` · calls today 17/900

Agreement trades 41 (adequate) · wins 22 · losses 19 · net $1,912.63 · expectancy +0.115R · profit factor 1.28 · old DEBATE rule (stopped in dual-ai-1.2.0): 4 trade(s), net $-1,416.51, removed from the account

Disagreements (not traded; the debate runs in shadow): 65 · the debate's pick if taken: 61 resolved (adequate), expectancy -0.199R · the side it rejected if taken: 66 resolved (adequate), expectancy -0.213R

Exits in shadow (the same trades, followed again; measured, never traded): break-even at +1R +0.103R vs +0.300R as taken (28, insufficient) · held 24 h +0.512R vs +0.300R as taken (28, insufficient) · stop and target twice as far +0.190R vs +0.300R as taken (28, insufficient)

Trades taken by session (UTC): ASIA 19 resolved (insufficient), expectancy +0.279R · LONDON 9 resolved (insufficient), expectancy +0.225R · OVERLAP 8 resolved (insufficient), expectancy -0.382R · NEW_YORK 6 resolved (insufficient), expectancy +0.792R · LATE 3 resolved (insufficient), expectancy -1.106R

| Time | Symbol | Trader 1 | Trader 2 | Debate (shadow) | Rule | Final | Risk |
|---|---|---|---|---|---|---|---|
| 10-19 00:30 | USDCHF | -  | -  | - | MARKET_UNAVAILABLE | NO_TRADE | - |
| 10-19 00:30 | USDCAD | -  | -  | - | MARKET_UNAVAILABLE | NO_TRADE | - |
| 10-19 00:15 | AUDUSD | BUY 70 | BUY 60 | - | AGREE | BUY | APPROVED |
| 10-19 00:15 | USDJPY | BUY 55 | SELL 65 | BUY | DISAGREE | NO_TRADE | - |
| 10-19 00:00 | GBPUSD | BUY 60 | BUY 65 | - | AGREE | BUY | APPROVED |
| 10-19 00:00 | EURUSD | SELL 56 | BUY 65 | SELL | DISAGREE | NO_TRADE | - |
| 10-18 23:45 | GBPJPY | -  | -  | - | MARKET_UNAVAILABLE | NO_TRADE | - |
| 10-18 23:45 | EURJPY | -  | -  | - | MARKET_UNAVAILABLE | NO_TRADE | - |
| 10-18 23:30 | EURGBP | -  | -  | - | MARKET_UNAVAILABLE | NO_TRADE | - |
| 10-18 23:30 | NZDUSD | -  | -  | - | MARKET_UNAVAILABLE | NO_TRADE | - |
| 10-18 23:15 | USDCHF | -  | -  | - | MARKET_UNAVAILABLE | NO_TRADE | - |
| 10-18 23:15 | USDCAD | -  | -  | - | MARKET_UNAVAILABLE | NO_TRADE | - |

The chart Trader 1 read last: `last_chart.png`. (numbers): no free vision model answered, so Trader 1 read the same chart from its numbers.

Full figures: `paper_forward.json`. Rules: `docs/PAPER_FORWARD.md` on main.
