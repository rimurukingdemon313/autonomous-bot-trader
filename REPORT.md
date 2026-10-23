# PAPER FORWARD TEST — NOT REAL MONEY

Updated 2026-10-23 02:53 UTC · mode `PAPER_FORWARD` · profile `PAPER-FORWARD-200K` · shift started 2026-10-22 22:52 UTC · decision system `dual_ai`

Research status (historical, unchanged): **NO EDGE — DO NOT TRADE (historical research; this test measures forward)**. This run measures the system forward; it is not evidence of an edge until it has a sample and the forward-eligibility rules say so.

## The rule that trades: a trade only when both AIs agree

| Trades | Wins | Losses | Win rate | Net P&L | Expectancy | Profit factor | Max drawdown |
|---|---|---|---|---|---|---|---|
| 92 (adequate) | 40 | 52 | 43.5% | $-1,418.51 | -0.048R | 0.92 | $4,943.76 |

The 4 trade(s) of the old DEBATE rule, stopped in dual-ai-1.2.0, were removed from the paper account at the operator's request: their net $-1,416.51 was put back by a declared adjustment ($1,416.51). They stay in the journal (append-only), in none of the account's figures below.

## Paper account

| Account | Equity | P&L today | Total P&L | Drawdown | Open | Trades | Win rate | Expectancy | Profit factor | Risk | Bot |
|---|---|---|---|---|---|---|---|---|---|---|---|
| $200,000.00 | $198,565.34 | $-1,104.92 | $-1,434.66 | $-1,434.66 | 1 | 92 (adequate) | 43.5% | -0.048R | 0.92 | ACTIVE | RUNNING |

Equity includes declared operator adjustments of $1,416.51 (without them: $197,148.83); P&L today excludes them. `remove-retired-debate-rule-trades-2026-10-15`: operator: the 4 trades of the retired debate rule (dual-ai 1.1.0, stopped in 1.2.0) are removed from the paper account; they stay in the journal.

**WARNING: the hard risk gate refused 1 of the last 20 decisions: FINANCING_EXCEEDS_RISK x1.** A refusal by the gate after the risk engine approved is never routine. The latest at 10-23 01:45 UTC; 5 decision(s) since, none refused by the gate.

## Last decisions (decision → risk → paper execution)

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
- 10-22 18:30 USDCAD BUY: AI DECISION → RISK REJECTED — currency_conflict: BUY USDCAD would bet against an open position: USDJPY SELL is short USD
- 10-22 18:11 AUDUSD BUY: AI DECISION → RISK REJECTED — reward_risk: 1.00 vs minimum 1.2; structure: H1 structure is range (mixed swings): no new position without a clear H1 trend (up HH+HL or down LH+LL)
- 10-22 18:00 USDJPY SELL: AI DECISION → RISK APPROVED → PAPER EXECUTED
- 10-22 17:43 GBPUSD BUY: AI DECISION → RISK REJECTED — reward_risk: 0.97 vs minimum 1.2; structure: H1 structure is range (mixed swings): no new position without a clear H1 trend (up HH+HL or down LH+LL)
- 10-22 17:00 USDJPY SELL: AI DECISION → RISK APPROVED → PAPER EXECUTED
- 10-22 16:00 EURCHF BUY: AI DECISION → RISK APPROVED → PAPER EXECUTED
- 10-22 11:46 GBPUSD SELL: AI DECISION → RISK APPROVED → PAPER EXECUTED
- 10-22 11:45 EURUSD SELL: AI DECISION → RISK REJECTED — reward_risk: 1.11 vs minimum 1.2
- 10-22 11:32 EURGBP SELL: AI DECISION → RISK REJECTED — reward_risk: 1.08 vs minimum 1.2

## Latest decisions, NO TRADE included (2153 so far)

- 10-23 02:45 NZDUSD BUY: BUY NZDUSD on M15: AGREE: Trader 1 (nvidia/nemotron-3.5-super-vl:free) BUY 62: M15 shows a clear bullish structure (CHoCH then repeated BOS, HH/HL) with an untested demand order block at 0.56896-0.569
- 10-23 02:35 USDCHF SELL: SELL USDCHF on M15: AGREE: Trader 1 (nvidia/nemotron-3.5-super-vl:free) SELL 58: H4 downtrend and price at the top of today's range argue for a rejection into the open bearish FVG/H4 bearish BOS at 0.
- 10-23 02:30 USDCAD NO_TRADE: the traders disagree (Trader 1 BUY 62, Trader 2 SELL 65): no trade unless both choose the same side; the debate (nvidia/nemotron-3-ultra-550b-a55b:free) would have chosen SELL: followed forward in sha
- 10-23 02:23 AUDUSD SELL: SELL AUDUSD on M15: AGREE: Trader 1 (dots-studio/dots-3-note-preview:free) SELL 72: The M15 chart displays a well-defined bearish structure with lower highs, lower lows, and a fresh CHoCH bearish brea
- 10-23 02:15 USDJPY NO_TRADE: the traders disagree (Trader 1 BUY 60, Trader 2 SELL 65): no trade unless both choose the same side; the debate (nvidia/nemotron-3-ultra-550b-a55b:free) would have chosen SELL: followed forward in sha
- 10-23 02:05 GBPUSD SELL: SELL GBPUSD on M15: AGREE: Trader 1 (nvidia/nemotron-3.5-super-vl:free) SELL 58: M15 structure just flipped bearish with a CHoCH at 1.34018 and bearish displacement on the completed bar, while the unt
- 10-23 02:00 EURUSD SELL: SELL EURUSD on M15: AGREE: Trader 1 (nvidia/nemotron-3.5-super-vl:free) SELL 55: H4 trend is bearish and M15 just printed a bearish CHoCH at 1.12221, ending the short-term uptrend. Price is below the 
- 10-23 01:45 AUDJPY SELL: SELL AUDJPY on M15: AGREE: Trader 1 (nvidia/nemotron-3.5-super-vl:free) SELL 55: M15 structure shows a clear downtrend with consecutive lower lows and bearish BOS breaks. Price swept lows at 109.809 b
- 10-23 01:45 EURCHF NO_TRADE: blocked before consulting the model: EXPOSURE: a EURCHF position is already open
- 10-23 01:30 GBPJPY NO_TRADE: blocked before consulting the model: EXPOSURE: a GBPJPY position is already open
- 10-23 01:30 EURJPY NO_TRADE: risk engine: open_positions (3 open, max 3); currency_exposure (2 open positions share a currency, max 2): the model was not consulted
- 10-23 01:15 EURGBP NO_TRADE: risk engine: open_positions (3 open, max 3): the model was not consulted

## Open paper positions

| Symbol | Side | Qty | Entry | Stop | Target | P&L |
|---|---|---|---|---|---|---|
| USDCHF | SELL | 2.21 | 0.821115 | 0.8226 | 0.81912 | $-16.15 |

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

OpenRouter `READY` · key set · trader 1 `nvidia/nemotron-3.5-super-vl:free` · trader 2 `nvidia/nemotron-3-ultra-550b-a55b:free` · debate `dots-studio/dots-3-note-preview:free` · calls today 43/900

Agreement trades 92 (adequate) · wins 40 · losses 52 · net $-1,418.51 · expectancy -0.048R · profit factor 0.92 · old DEBATE rule (stopped in dual-ai-1.2.0): 4 trade(s), net $-1,416.51, removed from the account

Disagreements (not traded; the debate runs in shadow): 103 · the debate's pick if taken: 91 resolved (adequate), expectancy -0.210R · the side it rejected if taken: 96 resolved (adequate), expectancy -0.220R

Exits in shadow (the same trades, followed again; measured, never traded): break-even at +1R -0.114R vs -0.043R as taken (64, adequate) · held 24 h +0.112R vs -0.043R as taken (64, adequate) · stop and target twice as far +0.047R vs -0.043R as taken (64, adequate) · closed at 8 h (the exit before dual-ai 1.7.0) -0.445R vs -0.354R as taken (10, insufficient)

Trades taken by session (UTC): ASIA 36 resolved (adequate), expectancy -0.063R · LONDON 20 resolved (insufficient), expectancy -0.013R · OVERLAP 8 resolved (insufficient), expectancy -0.382R · NEW_YORK 14 resolved (insufficient), expectancy +0.248R · LATE 3 resolved (insufficient), expectancy -1.106R

| Time | Symbol | Trader 1 | Trader 2 | Debate (shadow) | Rule | Final | Risk |
|---|---|---|---|---|---|---|---|
| 10-23 02:45 | NZDUSD | BUY 62 | BUY 68 | - | AGREE | BUY | REJECTED |
| 10-23 02:35 | USDCHF | SELL 58 | SELL 60 | - | AGREE | SELL | APPROVED |
| 10-23 02:30 | USDCAD | BUY 62 | SELL 65 | SELL | DISAGREE | NO_TRADE | - |
| 10-23 02:23 | AUDUSD | SELL 72 | SELL 65 | - | AGREE | SELL | REJECTED |
| 10-23 02:15 | USDJPY | BUY 60 | SELL 65 | SELL | DISAGREE | NO_TRADE | - |
| 10-23 02:05 | GBPUSD | SELL 58 | SELL 68 | - | AGREE | SELL | REJECTED |
| 10-23 02:00 | EURUSD | SELL 55 | SELL 65 | - | AGREE | SELL | REJECTED |
| 10-23 01:45 | AUDJPY | SELL 55 | SELL 65 | - | AGREE | SELL | APPROVED |
| 10-23 01:45 | EURCHF | -  | -  | - | NOT_ASKED | NO_TRADE | - |
| 10-23 01:30 | GBPJPY | -  | -  | - | NOT_ASKED | NO_TRADE | - |
| 10-23 01:30 | EURJPY | -  | -  | - | NOT_ASKED | NO_TRADE | - |
| 10-23 01:15 | EURGBP | -  | -  | - | NOT_ASKED | NO_TRADE | - |

The chart Trader 1 read last: `last_chart.png`. (numbers): no free vision model answered, so Trader 1 read the same chart from its numbers.

Full figures: `paper_forward.json`. Rules: `docs/PAPER_FORWARD.md` on main.
