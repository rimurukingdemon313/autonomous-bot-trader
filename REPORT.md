# PAPER FORWARD TEST — NOT REAL MONEY

Updated 2026-10-19 05:04 UTC · mode `PAPER_FORWARD` · profile `PAPER-FORWARD-200K` · shift started 2026-10-18 23:48 UTC · decision system `dual_ai`

Research status (historical, unchanged): **NO EDGE — DO NOT TRADE (historical research; this test measures forward)**. This run measures the system forward; it is not evidence of an edge until it has a sample and the forward-eligibility rules say so.

## The rule that trades: a trade only when both AIs agree

| Trades | Wins | Losses | Win rate | Net P&L | Expectancy | Profit factor | Max drawdown |
|---|---|---|---|---|---|---|---|
| 43 (adequate) | 23 | 20 | 53.5% | $1,910.93 | +0.109R | 1.27 | $1,928.96 |

The 4 trade(s) of the old DEBATE rule, stopped in dual-ai-1.2.0, were removed from the paper account at the operator's request: their net $-1,416.51 was put back by a declared adjustment ($1,416.51). They stay in the journal (append-only), in none of the account's figures below.

## Paper account

| Account | Equity | P&L today | Total P&L | Drawdown | Open | Trades | Win rate | Expectancy | Profit factor | Risk | Bot |
|---|---|---|---|---|---|---|---|---|---|---|---|
| $200,000.00 | $202,063.75 | $151.12 | $2,063.75 | $0.00 | 3 | 43 (adequate) | 53.5% | +0.109R | 1.27 | ACTIVE | RUNNING |

Equity includes declared operator adjustments of $1,416.51 (without them: $200,647.23); P&L today excludes them. `remove-retired-debate-rule-trades-2026-10-15`: operator: the 4 trades of the retired debate rule (dual-ai 1.1.0, stopped in 1.2.0) are removed from the paper account; they stay in the journal.

## Last decisions (decision → risk → paper execution)

- 10-19 04:30 GBPUSD SELL: AI DECISION → RISK APPROVED → PAPER EXECUTED
- 10-19 04:00 GBPJPY BUY: AI DECISION → RISK REJECTED — currency_conflict: BUY GBPJPY would bet against an open position: EURGBP BUY is short GBP
- 10-19 03:45 EURGBP BUY: AI DECISION → RISK APPROVED → PAPER EXECUTED
- 10-19 03:45 NZDUSD BUY: AI DECISION → RISK REJECTED — reward_risk: 1.00 vs minimum 1.2
- 10-19 03:30 USDCHF SELL: AI DECISION → RISK REJECTED — reward_risk: 0.74 vs minimum 1.2
- 10-19 03:15 USDJPY BUY: AI DECISION → RISK REJECTED — currency_conflict: BUY USDJPY would bet against an open position: AUDUSD BUY is short USD
- 10-19 03:00 GBPUSD SELL: AI DECISION → RISK REJECTED — reward_risk: 1.06 vs minimum 1.2; currency_conflict: SELL GBPUSD would bet against an open position: AUDUSD BUY is short USD
- 10-19 01:00 EURJPY BUY: AI DECISION → RISK APPROVED → PAPER EXECUTED
- 10-19 00:45 EURGBP BUY: AI DECISION → RISK REJECTED — reward_risk: 1.02 vs minimum 1.2; currency_conflict: BUY EURGBP would bet against an open position: GBPUSD BUY is long GBP
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

## Latest decisions, NO TRADE included (1428 so far)

- 10-19 05:00 USDCHF NO_TRADE: market unavailable for a decision: risk engine: open_positions (3 open, max 3): the model was not consulted
- 10-19 05:00 USDCAD NO_TRADE: market unavailable for a decision: risk engine: open_positions (3 open, max 3): the model was not consulted
- 10-19 04:45 AUDUSD NO_TRADE: market unavailable for a decision: risk engine: open_positions (3 open, max 3): the model was not consulted
- 10-19 04:45 USDJPY NO_TRADE: market unavailable for a decision: risk engine: open_positions (3 open, max 3): the model was not consulted
- 10-19 04:30 GBPUSD SELL: SELL GBPUSD on M15: AGREE: Trader 1 (nvidia/nemotron-3.5-super-vl:free) SELL 57: M15 shows a fresh bearish structure break with LH at 1.3331 and price testing the 1.333-1.33364 supply order block; an 
- 10-19 04:30 EURUSD NO_TRADE: market unavailable for a decision: risk engine: currency_exposure (2 open positions share a currency, max 2): the model was not consulted
- 10-19 04:15 AUDJPY NO_TRADE: the traders disagree (Trader 1 BUY 65, Trader 2 SELL 60): no trade unless both choose the same side; the debate (dots-studio/dots-3-note-preview:free) would have chosen SELL: followed forward in shado
- 10-19 04:15 EURCHF NO_TRADE: market unavailable for a decision: risk engine: currency_exposure (2 open positions share a currency, max 2): the model was not consulted
- 10-19 04:00 GBPJPY BUY: BUY GBPJPY on M15: AGREE: Trader 1 (nvidia/nemotron-3.5-super-vl:free) BUY 67: Both timeframes trend up with a fresh bullish BOS at 210.667 and an untested demand OB at 210.479-210.570 supporting cont
- 10-19 04:00 EURJPY NO_TRADE: market unavailable for a decision: blocked before consulting the model: EXPOSURE: a EURJPY position is already open
- 10-19 03:45 EURGBP BUY: BUY EURGBP on M15: AGREE: Trader 1 (nvidia/nemotron-3.5-super-vl:free) BUY 55: M15 structure is bullish with a fresh higher low and bullish CHoCH; the tested demand order block is holding price above 
- 10-19 03:45 NZDUSD BUY: BUY NZDUSD on M15: AGREE: Trader 1 (nvidia/nemotron-3.5-super-vl:free) BUY 61: H4 uptrend and fresh M15 bullish BOS favor longs; price is at an untested demand OB with an open bullish FVG, offering a 

## Open paper positions

| Symbol | Side | Qty | Entry | Stop | Target | P&L |
|---|---|---|---|---|---|---|
| GBPUSD | SELL | 3.97 | 1.33273 | 1.33364 | 1.33144 | $-51.61 |
| EURGBP | BUY | 3.45 | 0.8425699999999999 | 0.84172 | 0.84365 | $-13.79 |
| EURJPY | BUY | 1.38 | 177.2825 | 177.05 | 177.603 | $218.22 |

## Closed paper trades (latest 20)

| Closed | Symbol | Side | Net | R | Costs | Exit | Source | Rule |
|---|---|---|---|---|---|---|---|---|
| 10-19 03:31 | AUDUSD | BUY | $200.64 | +0.80 | $41.04 | TARGET | DUAL_AI | AGREE |
| 10-19 02:46 | GBPUSD | BUY | $-202.34 | -0.81 | $36.33 | STOP | DUAL_AI | AGREE |
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

## Dual AI desk (two free OpenRouter traders; a trade only when they agree)

OpenRouter `READY` · key set · trader 1 `nvidia/nemotron-3.5-super-vl:free` · trader 2 `nvidia/nemotron-3-ultra-550b-a55b:free` · debate `dots-studio/dots-3-note-preview:free` · calls today 51/900

Agreement trades 43 (adequate) · wins 23 · losses 20 · net $1,910.93 · expectancy +0.109R · profit factor 1.27 · old DEBATE rule (stopped in dual-ai-1.2.0): 4 trade(s), net $-1,416.51, removed from the account

Disagreements (not traded; the debate runs in shadow): 68 · the debate's pick if taken: 61 resolved (adequate), expectancy -0.199R · the side it rejected if taken: 66 resolved (adequate), expectancy -0.213R

Exits in shadow (the same trades, followed again; measured, never traded): break-even at +1R +0.103R vs +0.300R as taken (28, insufficient) · held 24 h +0.512R vs +0.300R as taken (28, insufficient) · stop and target twice as far +0.190R vs +0.300R as taken (28, insufficient)

Trades taken by session (UTC): ASIA 19 resolved (insufficient), expectancy +0.279R · LONDON 9 resolved (insufficient), expectancy +0.225R · OVERLAP 8 resolved (insufficient), expectancy -0.382R · NEW_YORK 6 resolved (insufficient), expectancy +0.792R · LATE 3 resolved (insufficient), expectancy -1.106R

| Time | Symbol | Trader 1 | Trader 2 | Debate (shadow) | Rule | Final | Risk |
|---|---|---|---|---|---|---|---|
| 10-19 05:00 | USDCHF | -  | -  | - | MARKET_UNAVAILABLE | NO_TRADE | - |
| 10-19 05:00 | USDCAD | -  | -  | - | MARKET_UNAVAILABLE | NO_TRADE | - |
| 10-19 04:45 | AUDUSD | -  | -  | - | MARKET_UNAVAILABLE | NO_TRADE | - |
| 10-19 04:45 | USDJPY | -  | -  | - | MARKET_UNAVAILABLE | NO_TRADE | - |
| 10-19 04:30 | GBPUSD | SELL 57 | SELL 58 | - | AGREE | SELL | APPROVED |
| 10-19 04:30 | EURUSD | -  | -  | - | MARKET_UNAVAILABLE | NO_TRADE | - |
| 10-19 04:15 | AUDJPY | BUY 65 | SELL 60 | SELL | DISAGREE | NO_TRADE | - |
| 10-19 04:15 | EURCHF | -  | -  | - | MARKET_UNAVAILABLE | NO_TRADE | - |
| 10-19 04:00 | GBPJPY | BUY 67 | BUY 68 | - | AGREE | BUY | REJECTED |
| 10-19 04:00 | EURJPY | -  | -  | - | MARKET_UNAVAILABLE | NO_TRADE | - |
| 10-19 03:45 | EURGBP | BUY 55 | BUY 50 | - | AGREE | BUY | APPROVED |
| 10-19 03:45 | NZDUSD | BUY 61 | BUY 58 | - | AGREE | BUY | REJECTED |

The chart Trader 1 read last: `last_chart.png`. (numbers): no free vision model answered, so Trader 1 read the same chart from its numbers.

Full figures: `paper_forward.json`. Rules: `docs/PAPER_FORWARD.md` on main.
