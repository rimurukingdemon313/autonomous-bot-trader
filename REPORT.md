# PAPER FORWARD TEST — NOT REAL MONEY

Updated 2026-10-23 07:58 UTC · mode `PAPER_FORWARD` · profile `PAPER-FORWARD-200K` · shift started 2026-10-23 04:28 UTC · decision system `dual_ai`

Research status (historical, unchanged): **NO EDGE — DO NOT TRADE (historical research; this test measures forward)**. This run measures the system forward; it is not evidence of an edge until it has a sample and the forward-eligibility rules say so.

## The rule that trades: a trade only when both AIs agree

| Trades | Wins | Losses | Win rate | Net P&L | Expectancy | Profit factor | Max drawdown |
|---|---|---|---|---|---|---|---|
| 95 (adequate) | 40 | 55 | 42.1% | $-2,214.50 | -0.071R | 0.88 | $5,490.40 |

The 4 trade(s) of the old DEBATE rule, stopped in dual-ai-1.2.0, were removed from the paper account at the operator's request: their net $-1,416.51 was put back by a declared adjustment ($1,416.51). They stay in the journal (append-only), in none of the account's figures below.

## Paper account

| Account | Equity | P&L today | Total P&L | Drawdown | Open | Trades | Win rate | Expectancy | Profit factor | Risk | Bot |
|---|---|---|---|---|---|---|---|---|---|---|---|
| $200,000.00 | $197,785.50 | $-1,884.76 | $-2,214.50 | $-2,214.50 | 0 | 95 (adequate) | 42.1% | -0.071R | 0.88 | ACTIVE | RUNNING |

Equity includes declared operator adjustments of $1,416.51 (without them: $196,368.98); P&L today excludes them. `remove-retired-debate-rule-trades-2026-10-15`: operator: the 4 trades of the retired debate rule (dual-ai 1.1.0, stopped in 1.2.0) are removed from the paper account; they stay in the journal.

**WARNING: the hard risk gate refused 1 of the last 20 decisions: FINANCING_EXCEEDS_RISK x1.** A refusal by the gate after the risk engine approved is never routine. The latest at 10-23 01:45 UTC; 19 decision(s) since, none refused by the gate.

## Last decisions (decision → risk → paper execution)

- 10-23 07:45 USDJPY SELL: AI DECISION → RISK REJECTED — structure: H1 structure is range (mixed swings): no new position without a clear H1 trend (up HH+HL or down LH+LL)
- 10-23 07:30 GBPUSD SELL: AI DECISION → RISK REJECTED — cost_to_risk: round-trip cost is 27.6% of the stop (max 25%): spread 0.00012 + commission and slippage
- 10-23 07:15 AUDJPY SELL: AI DECISION → RISK REJECTED — structure: H1 structure is range (mixed swings): no new position without a clear H1 trend (up HH+HL or down LH+LL)
- 10-23 07:00 GBPJPY SELL: AI DECISION → RISK REJECTED — currency_conflict: SELL GBPJPY would bet against an open position: EURGBP SELL is long GBP; structure: H1 structure is range (mixed swings): no new position without a clear H1 trend (up HH+HL or down 
- 10-23 06:45 NZDUSD SELL: AI DECISION → RISK REJECTED — reward_risk: 1.14 vs minimum 1.2; currency_conflict: SELL NZDUSD would bet against an open position: USDCHF SELL is short USD
- 10-23 05:30 EURJPY SELL: AI DECISION → RISK APPROVED → PAPER EXECUTED
- 10-23 05:15 NZDUSD BUY: AI DECISION → RISK REJECTED — structure: H1 structure is range (mixed swings): no new position without a clear H1 trend (up HH+HL or down LH+LL)
- 10-23 04:40 GBPUSD SELL: AI DECISION → RISK REJECTED — currency_conflict: SELL GBPUSD would bet against an open position: USDCHF SELL is short USD; EURGBP SELL is long GBP
- 10-23 04:15 NZDUSD BUY: AI DECISION → RISK REJECTED — structure: H1 structure is range (mixed swings): no new position without a clear H1 trend (up HH+HL or down LH+LL)
- 10-23 03:50 AUDUSD BUY: AI DECISION → RISK REJECTED — cost_to_risk: round-trip cost is 33.9% of the stop (max 25%): spread 0.0001 + commission and slippage; structure: H1 structure is range (mixed swings): no new position without a clear H1 trend (up HH+
- 10-23 03:33 GBPUSD SELL: AI DECISION → RISK REJECTED — reward_risk: 1.01 vs minimum 1.2; currency_conflict: SELL GBPUSD would bet against an open position: USDCHF SELL is short USD; EURGBP SELL is long GBP
- 10-23 03:30 EURUSD SELL: AI DECISION → RISK REJECTED — currency_conflict: SELL EURUSD would bet against an open position: USDCHF SELL is short USD
- 10-23 03:00 EURJPY SELL: AI DECISION → RISK REJECTED — structure: H1 structure is range (mixed swings): no new position without a clear H1 trend (up HH+HL or down LH+LL)
- 10-23 02:51 EURGBP SELL: AI DECISION → RISK APPROVED → PAPER EXECUTED
- 10-23 02:45 NZDUSD BUY: AI DECISION → RISK REJECTED — reward_risk: 0.96 vs minimum 1.2; structure: H1 structure is range (mixed swings): no new position without a clear H1 trend (up HH+HL or down LH+LL)
- 10-23 02:35 USDCHF SELL: AI DECISION → RISK APPROVED → PAPER EXECUTED
- 10-23 02:23 AUDUSD SELL: AI DECISION → RISK REJECTED — structure: H1 structure is range (mixed swings): no new position without a clear H1 trend (up HH+HL or down LH+LL)
- 10-23 02:05 GBPUSD SELL: AI DECISION → RISK REJECTED — structure: H1 structure is range (mixed swings): no new position without a clear H1 trend (up HH+HL or down LH+LL)
- 10-23 02:00 EURUSD SELL: AI DECISION → RISK REJECTED — reward_risk: 0.83 vs minimum 1.2; structure: H1 structure is range (mixed swings): no new position without a clear H1 trend (up HH+HL or down LH+LL)
- 10-23 01:45 AUDJPY SELL: AI DECISION → RISK APPROVED → RISK REJECTED — hard risk gate: RISK_GATE_REJECTED reason=FINANCING_EXCEEDS_RISK equity_conservative=198716.07 daily_pnl=-954.19 daily_limit=-10000.00 total_pnl=-1283.93 total_limit=-20000.00 open_risk=998.43 max_los

## Latest decisions, NO TRADE included (2194 so far)

- 10-23 07:48 AUDUSD NO_TRADE: the traders disagree (Trader 1 SELL 68, Trader 2 BUY 60): no trade unless both choose the same side; the debate (nvidia/nemotron-3.5-lightning:free) would have chosen BUY: followed forward in shadow, 
- 10-23 07:45 USDJPY SELL: SELL USDJPY on M15: AGREE: Trader 1 (dots-studio/dots-3-note-preview:free) SELL 65: The H4 trend remains bearish (LH+LL), favoring sells on pullbacks, while the M15 is in a range with the price curren
- 10-23 07:30 GBPUSD SELL: SELL GBPUSD on M15: AGREE: Trader 1 (dots-studio/dots-3-note-preview:free) SELL 70: The M15 chart shows a clear bearish structure with lower highs, lower lows, and recent bearish liquidity sweeps, ind
- 10-23 07:30 EURUSD NO_TRADE: risk engine: news (Medium-impact release EUR French Flash Manufacturing PMI 16 min ago; Medium-impact release EUR French Flash Services PMI 16 min ago; Medium-impact release EUR German Flash Manufactu
- 10-23 07:15 AUDJPY SELL: SELL AUDJPY on M15: AGREE: Trader 1 (dots-studio/dots-3-note-preview:free) SELL 72: The triple liquidity sweep of the highs at 110.32 with bearish signals indicates a fake breakout and smart money dis
- 10-23 07:15 EURCHF NO_TRADE: risk engine: news (Medium-impact release EUR French Flash Manufacturing PMI 1 min ago; Medium-impact release EUR French Flash Services PMI 1 min ago; Medium-impact release EUR German Flash Manufacturi
- 10-23 07:00 GBPJPY SELL: SELL GBPJPY on M15: AGREE: Trader 1 (dots-studio/dots-3-note-preview:free) SELL 75: The M15 trend is down (LH+LL) and the recent sweep of highs at 210.241 is a classic bearish liquidity grab. The H4 t
- 10-23 07:00 EURJPY NO_TRADE: risk engine: news (Medium-impact release EUR French Flash Manufacturing PMI in 14 min; Medium-impact release EUR French Flash Services PMI in 14 min; Medium-impact release EUR German Flash Manufacturi
- 10-23 06:49 EURGBP NO_TRADE: blocked before consulting the model: EXPOSURE: a EURGBP position is already open
- 10-23 06:45 NZDUSD SELL: SELL NZDUSD on M15: AGREE: Trader 1 (dots-studio/dots-3-note-preview:free) SELL 75: The M15 structure is bearish (LH+LL) with a bearish sweep of highs, and the price is pulling back to a demand zone n
- 10-23 06:35 USDCHF NO_TRADE: blocked before consulting the model: EXPOSURE: a USDCHF position is already open
- 10-23 06:30 USDCAD NO_TRADE: the traders disagree (Trader 1 BUY 72, Trader 2 SELL 65): no trade unless both choose the same side; the debate (xingchen-agi/xing4.0-29b-a4b:free) would have chosen SELL: followed forward in shadow, 

## Open paper positions

| Symbol | Side | Qty | Entry | Stop | Target | P&L |
|---|---|---|---|---|---|---|

## Closed paper trades (latest 20)

| Closed | Symbol | Side | Net | R | Costs | Exit | Source | Rule |
|---|---|---|---|---|---|---|---|---|
| 10-23 07:01 | EURGBP | SELL | $-207.52 | -0.84 | $43.74 | STOP | DUAL_AI | AGREE |
| 10-23 06:46 | USDCHF | SELL | $-417.00 | -0.84 | $61.13 | STOP | DUAL_AI | AGREE |
| 10-23 06:22 | EURJPY | SELL | $-171.48 | -0.70 | $37.01 | STOP | DUAL_AI | AGREE |
| 10-23 02:42 | EURCHF | SELL | $-402.83 | -0.81 | $81.83 | STOP | DUAL_AI | AGREE |
| 10-23 02:01 | GBPJPY | SELL | $-457.54 | -0.92 | $25.74 | STOP | DUAL_AI | AGREE |
| 10-23 01:35 | AUDJPY | SELL | $-431.20 | -0.86 | $45.54 | STOP | DUAL_AI | AGREE |
| 10-22 22:40 | USDJPY | SELL | $428.74 | +1.73 | $51.43 | TARGET | DUAL_AI | AGREE |
| 10-22 17:32 | USDJPY | SELL | $-198.17 | -0.79 | $25.98 | STOP | DUAL_AI | AGREE |
| 10-22 16:52 | EURCHF | BUY | $-430.76 | -0.86 | $62.40 | STOP | DUAL_AI | AGREE |
| 10-22 16:05 | GBPUSD | SELL | $-435.09 | -0.87 | $56.70 | STOP | DUAL_AI | AGREE |
| 10-22 14:07 | USDCAD | BUY | $-438.56 | -0.88 | $54.88 | STOP | DUAL_AI | AGREE |
| 10-22 11:06 | GBPJPY | SELL | $631.22 | +1.27 | $57.92 | TARGET | DUAL_AI | AGREE |
| 10-22 11:02 | AUDJPY | SELL | $574.01 | +1.16 | $75.68 | TARGET | DUAL_AI | AGREE |
| 10-22 10:56 | EURUSD | SELL | $530.48 | +1.07 | $55.84 | TARGET | DUAL_AI | AGREE |
| 10-22 09:41 | EURGBP | SELL | $482.66 | +0.97 | $81.60 | TARGET | DUAL_AI | AGREE |
| 10-22 08:28 | AUDUSD | SELL | $-494.07 | -0.99 | $82.84 | STOP | DUAL_AI | AGREE |
| 10-22 05:34 | GBPJPY | SELL | $724.37 | +1.46 | $84.17 | TARGET | DUAL_AI | AGREE |
| 10-22 05:30 | USDCAD | BUY | $-395.16 | -0.79 | $92.71 | STOP | DUAL_AI | AGREE |
| 10-22 03:06 | EURGBP | SELL | $-430.18 | -0.86 | $79.35 | STOP | DUAL_AI | AGREE |
| 10-22 03:14 | USDCHF | SELL | $561.26 | +1.13 | $100.15 | TARGET | DUAL_AI | AGREE |

## Dual AI desk (two free OpenRouter traders; a trade only when they agree)

OpenRouter `READY` · key set · trader 1 `dots-studio/dots-3-note-preview:free` · trader 2 `nvidia/nemotron-3-ultra-550b-a55b:free` · debate `recursive/flint-v1.0:free` · calls today 51/900

Agreement trades 95 (adequate) · wins 40 · losses 55 · net $-2,214.50 · expectancy -0.071R · profit factor 0.88 · old DEBATE rule (stopped in dual-ai-1.2.0): 4 trade(s), net $-1,416.51, removed from the account

Disagreements (not traded; the debate runs in shadow): 114 · the debate's pick if taken: 93 resolved (adequate), expectancy -0.180R · the side it rejected if taken: 98 resolved (adequate), expectancy -0.237R

Exits in shadow (the same trades, followed again; measured, never traded): break-even at +1R -0.099R vs -0.032R as taken (68, adequate) · held 24 h +0.113R vs -0.032R as taken (68, adequate) · stop and target twice as far +0.057R vs -0.032R as taken (68, adequate) · closed at 8 h (the exit before dual-ai 1.7.0) -0.279R vs -0.214R as taken (14, insufficient)

Trades taken by session (UTC): ASIA 39 resolved (adequate), expectancy -0.075R · LONDON 21 resolved (insufficient), expectancy +0.045R · OVERLAP 8 resolved (insufficient), expectancy -0.382R · NEW_YORK 14 resolved (insufficient), expectancy +0.248R · LATE 3 resolved (insufficient), expectancy -1.106R

| Time | Symbol | Trader 1 | Trader 2 | Debate (shadow) | Rule | Final | Risk |
|---|---|---|---|---|---|---|---|
| 10-23 07:48 | AUDUSD | SELL 68 | BUY 60 | BUY | DISAGREE | NO_TRADE | - |
| 10-23 07:45 | USDJPY | SELL 65 | SELL 70 | - | AGREE | SELL | REJECTED |
| 10-23 07:30 | GBPUSD | SELL 70 | SELL 65 | - | AGREE | SELL | REJECTED |
| 10-23 07:30 | EURUSD | -  | -  | - | NOT_ASKED | NO_TRADE | - |
| 10-23 07:15 | AUDJPY | SELL 72 | SELL 68 | - | AGREE | SELL | REJECTED |
| 10-23 07:15 | EURCHF | -  | -  | - | NOT_ASKED | NO_TRADE | - |
| 10-23 07:00 | GBPJPY | SELL 75 | SELL 65 | - | AGREE | SELL | REJECTED |
| 10-23 07:00 | EURJPY | -  | -  | - | NOT_ASKED | NO_TRADE | - |
| 10-23 06:49 | EURGBP | -  | -  | - | NOT_ASKED | NO_TRADE | - |
| 10-23 06:45 | NZDUSD | SELL 75 | SELL 70 | - | AGREE | SELL | REJECTED |
| 10-23 06:35 | USDCHF | -  | -  | - | NOT_ASKED | NO_TRADE | - |
| 10-23 06:30 | USDCAD | BUY 72 | SELL 65 | SELL | DISAGREE | NO_TRADE | - |

The chart Trader 1 read last: `last_chart.png`. (numbers): no free vision model answered, so Trader 1 read the same chart from its numbers.

Full figures: `paper_forward.json`. Rules: `docs/PAPER_FORWARD.md` on main.
