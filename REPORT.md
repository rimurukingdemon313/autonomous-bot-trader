# PAPER FORWARD TEST — NOT REAL MONEY

Updated 2026-10-23 06:13 UTC · mode `PAPER_FORWARD` · profile `PAPER-FORWARD-200K` · shift started 2026-10-23 04:28 UTC · decision system `dual_ai`

Research status (historical, unchanged): **NO EDGE — DO NOT TRADE (historical research; this test measures forward)**. This run measures the system forward; it is not evidence of an edge until it has a sample and the forward-eligibility rules say so.

## The rule that trades: a trade only when both AIs agree

| Trades | Wins | Losses | Win rate | Net P&L | Expectancy | Profit factor | Max drawdown |
|---|---|---|---|---|---|---|---|
| 92 (adequate) | 40 | 52 | 43.5% | $-1,418.51 | -0.048R | 0.92 | $4,943.76 |

The 4 trade(s) of the old DEBATE rule, stopped in dual-ai-1.2.0, were removed from the paper account at the operator's request: their net $-1,416.51 was put back by a declared adjustment ($1,416.51). They stay in the journal (append-only), in none of the account's figures below.

## Paper account

| Account | Equity | P&L today | Total P&L | Drawdown | Open | Trades | Win rate | Expectancy | Profit factor | Risk | Bot |
|---|---|---|---|---|---|---|---|---|---|---|---|
| $200,000.00 | $198,124.28 | $-1,545.99 | $-1,875.72 | $-1,875.72 | 3 | 92 (adequate) | 43.5% | -0.048R | 0.92 | ACTIVE | RUNNING |

Equity includes declared operator adjustments of $1,416.51 (without them: $196,707.76); P&L today excludes them. `remove-retired-debate-rule-trades-2026-10-15`: operator: the 4 trades of the retired debate rule (dual-ai 1.1.0, stopped in 1.2.0) are removed from the paper account; they stay in the journal.

**WARNING: the hard risk gate refused 1 of the last 20 decisions: FINANCING_EXCEEDS_RISK x1.** A refusal by the gate after the risk engine approved is never routine. The latest at 10-23 01:45 UTC; 14 decision(s) since, none refused by the gate.

## Last decisions (decision → risk → paper execution)

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
- 10-23 00:16 AUDJPY SELL: AI DECISION → RISK APPROVED → PAPER EXECUTED
- 10-23 00:15 EURCHF SELL: AI DECISION → RISK APPROVED → PAPER EXECUTED
- 10-23 00:08 GBPJPY SELL: AI DECISION → RISK APPROVED → PAPER EXECUTED
- 10-23 00:00 EURJPY SELL: AI DECISION → RISK REJECTED — reward_risk: 0.00 vs minimum 1.2; structure: H1 structure is range (mixed swings): no new position without a clear H1 trend (up HH+HL or down LH+LL)
- 10-22 18:41 USDCHF SELL: AI DECISION → RISK REJECTED — cost_to_risk: round-trip cost is 27.1% of the stop (max 25%): spread 0.00015 + commission and slippage

## Latest decisions, NO TRADE included (2180 so far)

- 10-23 06:00 GBPUSD NO_TRADE: risk engine: news (Medium-impact release GBP Retail Sales m/m 1 min ago: no new position from 30 min before to 30 min after); open_positions (3 open, max 3): the model was not consulted
- 10-23 06:00 EURUSD NO_TRADE: risk engine: open_positions (3 open, max 3); currency_exposure (2 open positions share a currency, max 2): the model was not consulted
- 10-23 05:45 AUDJPY NO_TRADE: risk engine: open_positions (3 open, max 3): the model was not consulted
- 10-23 05:45 EURCHF NO_TRADE: risk engine: open_positions (3 open, max 3); currency_exposure (2 open positions share a currency, max 2): the model was not consulted
- 10-23 05:33 GBPJPY NO_TRADE: risk engine: news (Medium-impact release GBP Retail Sales m/m in 26 min: no new position from 30 min before to 30 min after); open_positions (3 open, max 3): the model was not consulted
- 10-23 05:30 EURJPY SELL: SELL EURJPY on M15: AGREE: Trader 1 (dots-studio/dots-3-note-preview:free) SELL 72: The H4 trend is down (LH+LL) and the M15 shows a local bearish break (CHOCH at 175.898, LL at 175.817). Price is tes
- 10-23 05:17 EURGBP NO_TRADE: blocked before consulting the model: EXPOSURE: a EURGBP position is already open
- 10-23 05:15 NZDUSD BUY: BUY NZDUSD on M15: AGREE: Trader 1 (dots-studio/dots-3-note-preview:free) BUY 65: The M15 trend remains bullish with higher highs and higher lows, and the recent CHoCH and sweep of highs at 0.56996 lo
- 10-23 05:07 USDCHF NO_TRADE: blocked before consulting the model: EXPOSURE: a USDCHF position is already open
- 10-23 05:00 USDCAD NO_TRADE: the traders disagree (Trader 1 BUY 75, Trader 2 SELL 70): no trade unless both choose the same side; the debate (nvidia/nemotron-3.5-lightning:free) would have chosen SELL: followed forward in shadow,
- 10-23 04:49 AUDUSD NO_TRADE: the traders disagree (Trader 1 BUY 68, Trader 2 SELL 70): no trade unless both choose the same side; the debate (dots-studio/dots-3-note-preview:free) would have chosen SELL: followed forward in shado
- 10-23 04:45 USDJPY NO_TRADE: the traders disagree (Trader 1 BUY 57, Trader 2 SELL 65): no trade unless both choose the same side; the debate (dots-studio/dots-3-note-preview:free) would have chosen SELL: followed forward in shado

## Open paper positions

| Symbol | Side | Qty | Entry | Stop | Target | P&L |
|---|---|---|---|---|---|---|
| EURJPY | SELL | 2.07 | 175.9325 | 176.05 | 175.6 | $-51.67 |
| EURGBP | SELL | 1.7 | 0.8369300000000001 | 0.83778 | 0.83593 | $-120.62 |
| USDCHF | SELL | 2.21 | 0.821115 | 0.8226 | 0.81912 | $-284.93 |

## Closed paper trades (latest 20)

| Closed | Symbol | Side | Net | R | Costs | Exit | Source | Rule |
|---|---|---|---|---|---|---|---|---|
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
| 10-22 02:18 | AUDJPY | BUY | $-412.63 | -0.83 | $83.30 | STOP | DUAL_AI | AGREE |
| 10-22 01:54 | AUDUSD | BUY | $-506.27 | -1.01 | $123.62 | STOP | DUAL_AI | AGREE |
| 10-21 21:05 | GBPJPY | BUY | $-644.82 | -1.29 | $149.96 | STOP | DUAL_AI | AGREE |

## Dual AI desk (two free OpenRouter traders; a trade only when they agree)

OpenRouter `READY` · key set · trader 1 `dots-studio/dots-3-note-preview:free` · trader 2 `nvidia/nemotron-3-ultra-550b-a55b:free` · debate `xingchen-agi/xing4.0-29b-a4b:free` · calls today 34/900

Agreement trades 92 (adequate) · wins 40 · losses 52 · net $-1,418.51 · expectancy -0.048R · profit factor 0.92 · old DEBATE rule (stopped in dual-ai-1.2.0): 4 trade(s), net $-1,416.51, removed from the account

Disagreements (not traded; the debate runs in shadow): 112 · the debate's pick if taken: 91 resolved (adequate), expectancy -0.210R · the side it rejected if taken: 96 resolved (adequate), expectancy -0.220R

Exits in shadow (the same trades, followed again; measured, never traded): break-even at +1R -0.119R vs -0.051R as taken (67, adequate) · held 24 h +0.096R vs -0.051R as taken (67, adequate) · stop and target twice as far +0.051R vs -0.051R as taken (67, adequate) · closed at 8 h (the exit before dual-ai 1.7.0) -0.394R vs -0.324R as taken (13, insufficient)

Trades taken by session (UTC): ASIA 39 resolved (adequate), expectancy -0.075R · LONDON 20 resolved (insufficient), expectancy -0.013R · OVERLAP 8 resolved (insufficient), expectancy -0.382R · NEW_YORK 14 resolved (insufficient), expectancy +0.248R · LATE 3 resolved (insufficient), expectancy -1.106R

| Time | Symbol | Trader 1 | Trader 2 | Debate (shadow) | Rule | Final | Risk |
|---|---|---|---|---|---|---|---|
| 10-23 06:00 | GBPUSD | -  | -  | - | NOT_ASKED | NO_TRADE | - |
| 10-23 06:00 | EURUSD | -  | -  | - | NOT_ASKED | NO_TRADE | - |
| 10-23 05:45 | AUDJPY | -  | -  | - | NOT_ASKED | NO_TRADE | - |
| 10-23 05:45 | EURCHF | -  | -  | - | NOT_ASKED | NO_TRADE | - |
| 10-23 05:33 | GBPJPY | -  | -  | - | NOT_ASKED | NO_TRADE | - |
| 10-23 05:30 | EURJPY | SELL 72 | SELL 70 | - | AGREE | SELL | APPROVED |
| 10-23 05:17 | EURGBP | -  | -  | - | NOT_ASKED | NO_TRADE | - |
| 10-23 05:15 | NZDUSD | BUY 65 | BUY 58 | - | AGREE | BUY | REJECTED |
| 10-23 05:07 | USDCHF | -  | -  | - | NOT_ASKED | NO_TRADE | - |
| 10-23 05:00 | USDCAD | BUY 75 | SELL 70 | SELL | DISAGREE | NO_TRADE | - |
| 10-23 04:49 | AUDUSD | BUY 68 | SELL 70 | SELL | DISAGREE | NO_TRADE | - |
| 10-23 04:45 | USDJPY | BUY 57 | SELL 65 | SELL | DISAGREE | NO_TRADE | - |

The chart Trader 1 read last: `last_chart.png`. (numbers): no free vision model answered, so Trader 1 read the same chart from its numbers.

Full figures: `paper_forward.json`. Rules: `docs/PAPER_FORWARD.md` on main.
