# PAPER FORWARD TEST — NOT REAL MONEY

Updated 2026-10-16 20:09 UTC · mode `PAPER_FORWARD` · profile `PAPER-FORWARD-200K` · shift started 2026-10-16 15:54 UTC · decision system `dual_ai`

Research status (historical, unchanged): **NO EDGE — DO NOT TRADE (historical research; this test measures forward)**. This run measures the system forward; it is not evidence of an edge until it has a sample and the forward-eligibility rules say so.

## The rule that trades: a trade only when both AIs agree

| Trades | Wins | Losses | Win rate | Net P&L | Expectancy | Profit factor | Max drawdown |
|---|---|---|---|---|---|---|---|
| 41 (adequate) | 22 | 19 | 53.7% | $1,912.63 | +0.115R | 1.28 | $1,928.96 |

The 4 trade(s) of the old DEBATE rule, stopped in dual-ai-1.2.0, were removed from the paper account at the operator's request: their net $-1,416.51 was put back by a declared adjustment ($1,416.51). They stay in the journal (append-only), in none of the account's figures below.

## Paper account

| Account | Equity | P&L today | Total P&L | Drawdown | Open | Trades | Win rate | Expectancy | Profit factor | Risk | Bot |
|---|---|---|---|---|---|---|---|---|---|---|---|
| $200,000.00 | $201,912.63 | $1,139.05 | $1,912.63 | $0.00 | 0 | 41 (adequate) | 53.7% | +0.115R | 1.28 | ACTIVE | RUNNING |

Equity includes declared operator adjustments of $1,416.51 (without them: $200,496.12); P&L today excludes them. `remove-retired-debate-rule-trades-2026-10-15`: operator: the 4 trades of the retired debate rule (dual-ai 1.1.0, stopped in 1.2.0) are removed from the paper account; they stay in the journal.

## Last decisions (decision → risk → paper execution)

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
- 10-16 16:00 EURUSD SELL: AI DECISION → RISK REJECTED — reward_risk: 0.40 vs minimum 1.2; weekend_carry: held up to 480 min it could still be open at the Friday close (Fri 17:00 New York)
- 10-16 15:45 USDJPY SELL: AI DECISION → RISK REJECTED — stop_distance: stop 0.002 vs 3.0 x spread 0.01; spread: spread is 500.0% of the stop (max 25%); cost_to_risk: round-trip cost is 950.0% of the stop (max 25%): spread 0.01 + commission and slippage; we

## Latest decisions, NO TRADE included (972 so far)

- 10-16 20:00 GBPUSD NO_TRADE: market unavailable for a decision: risk engine: quiet_hours (16:00 New York: no new position from 16:00 to 20:00 New York (the rollover to the Tokyo open: the thinnest liquidity of the day)): the mode
- 10-16 20:00 EURUSD NO_TRADE: market unavailable for a decision: risk engine: quiet_hours (16:00 New York: no new position from 16:00 to 20:00 New York (the rollover to the Tokyo open: the thinnest liquidity of the day)): the mode
- 10-16 19:45 AUDJPY BUY: BUY AUDJPY on M15: AGREE: Trader 1 (nvidia/nemotron-3.5-super-vl:free) BUY 56: Multiple sweeps of the 109.66 lows with price holding and forming a higher low favor a bullish mean-reversion off taken l
- 10-16 19:45 EURCHF SELL: SELL EURCHF on M15: AGREE: Trader 1 (nvidia/nemotron-3.5-super-vl:free) SELL 60: H4 structure is decisively down (LH+LL) with bearish BOS at 0.92653, while M15 shows repeated bearish sweeps of highs a
- 10-16 19:15 GBPJPY NO_TRADE: the traders disagree (Trader 1 BUY 62, Trader 2 SELL 62): no trade unless both choose the same side; the shadow debate gave no usable answer (INVALID: no JSON object in the reply)
- 10-16 19:15 EURJPY BUY: BUY EURJPY on M15: AGREE: Trader 1 (dots-studio/dots-3-note-preview:free) BUY 65: The trade is a BUY on the confluence of the H4 bullish BOS at 177.59, the tested demand order block, and the bullish l
- 10-16 19:00 EURGBP BUY: BUY EURGBP on M15: AGREE: Trader 1 (nvidia/nemotron-3.5-super-vl:free) BUY 62: M15 structure is bullish (HH/HL) with a fresh bullish CHoCH at 0.8432 and a new HH at 0.8434, while price holds above the
- 10-16 19:00 NZDUSD SELL: SELL NZDUSD on M15: AGREE: Trader 1 (nvidia/nemotron-3.5-super-vl:free) SELL 65: M15 structure is bearish with fresh bearish BOS at 0.56484 and a new LL at 0.56424, while open bearish FVGs sit above p
- 10-16 18:45 USDCHF NO_TRADE: the traders disagree (Trader 1 BUY 62, Trader 2 SELL 65): no trade unless both choose the same side; the debate (nvidia/nemotron-3-super-120b-a12b:free) would have chosen BUY: followed forward in shad
- 10-16 18:45 USDCAD SELL: SELL USDCAD on M15: AGREE: Trader 1 (nvidia/nemotron-3.5-super-vl:free) SELL 65: Both M15 and H4 are trending down with lower highs and lower lows, and the most recent CHOCH at 1.4152 is bearish. Pric
- 10-16 18:30 AUDUSD SELL: SELL AUDUSD on M15: AGREE: Trader 1 (nvidia/nemotron-3.5-super-vl:free) SELL 60: Both timeframes show bearish structure with the most recent BOS at 0.69411 and LH at 0.69464. Price is at the top of a 
- 10-16 18:30 USDJPY SELL: SELL USDJPY on M15: AGREE: Trader 1 (nvidia/nemotron-3.5-super-vl:free) SELL 62: Price is at 158.041 five-touch resistance with open bearish FVGs above and H4 bearish CHoCH at 158.106; recent bullish 

## Open paper positions

| Symbol | Side | Qty | Entry | Stop | Target | P&L |
|---|---|---|---|---|---|---|

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

OpenRouter `READY` · key set · trader 1 `nvidia/nemotron-3.5-super-vl:free` · trader 2 `dots-studio/dots-3-note-preview:free` · debate `nvidia/nemotron-3-super-120b-a12b:free` · calls today 78/900

Agreement trades 41 (adequate) · wins 22 · losses 19 · net $1,912.63 · expectancy +0.115R · profit factor 1.28 · old DEBATE rule (stopped in dual-ai-1.2.0): 4 trade(s), net $-1,416.51, removed from the account

Disagreements (not traded; the debate runs in shadow): 63 · the debate's pick if taken: 57 resolved (adequate), expectancy -0.184R · the side it rejected if taken: 62 resolved (adequate), expectancy -0.219R

Exits in shadow (the same trades, followed again; measured, never traded): break-even at +1R +0.103R vs +0.300R as taken (28, insufficient) · held 24 h +0.390R vs +0.134R as taken (19, insufficient) · stop and target twice as far +0.159R vs +0.134R as taken (19, insufficient)

Trades taken by session (UTC): ASIA 19 resolved (insufficient), expectancy +0.279R · LONDON 9 resolved (insufficient), expectancy +0.225R · OVERLAP 8 resolved (insufficient), expectancy -0.382R · NEW_YORK 6 resolved (insufficient), expectancy +0.792R · LATE 3 resolved (insufficient), expectancy -1.106R

| Time | Symbol | Trader 1 | Trader 2 | Debate (shadow) | Rule | Final | Risk |
|---|---|---|---|---|---|---|---|
| 10-16 20:00 | GBPUSD | -  | -  | - | MARKET_UNAVAILABLE | NO_TRADE | - |
| 10-16 20:00 | EURUSD | -  | -  | - | MARKET_UNAVAILABLE | NO_TRADE | - |
| 10-16 19:45 | AUDJPY | BUY 56 | BUY 62 | - | AGREE | BUY | REJECTED |
| 10-16 19:45 | EURCHF | SELL 60 | SELL 62 | - | AGREE | SELL | REJECTED |
| 10-16 19:15 | GBPJPY | BUY 62 (numbers) | SELL 62 | - | DISAGREE | NO_TRADE | - |
| 10-16 19:15 | EURJPY | BUY 65 | BUY 62 | - | AGREE | BUY | REJECTED |
| 10-16 19:00 | EURGBP | BUY 62 | BUY 60 | - | AGREE | BUY | REJECTED |
| 10-16 19:00 | NZDUSD | SELL 65 | SELL 65 | - | AGREE | SELL | REJECTED |
| 10-16 18:45 | USDCHF | BUY 62 | SELL 65 | BUY | DISAGREE | NO_TRADE | - |
| 10-16 18:45 | USDCAD | SELL 65 | SELL 65 | - | AGREE | SELL | REJECTED |
| 10-16 18:30 | AUDUSD | SELL 60 | SELL 65 | - | AGREE | SELL | REJECTED |
| 10-16 18:30 | USDJPY | SELL 62 | SELL 65 | - | AGREE | SELL | REJECTED |

The chart Trader 1 read last: `last_chart.png`. (numbers): no free vision model answered, so Trader 1 read the same chart from its numbers.

Full figures: `paper_forward.json`. Rules: `docs/PAPER_FORWARD.md` on main.
