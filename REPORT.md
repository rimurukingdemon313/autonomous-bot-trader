# PAPER FORWARD TEST — NOT REAL MONEY

Updated 2026-10-16 03:08 UTC · mode `PAPER_FORWARD` · profile `PAPER-FORWARD-200K` · shift started 2026-10-15 23:07 UTC · decision system `dual_ai`

Research status (historical, unchanged): **NO EDGE — DO NOT TRADE (historical research; this test measures forward)**. This run measures the system forward; it is not evidence of an edge until it has a sample and the forward-eligibility rules say so.

## The rule that trades: a trade only when both AIs agree

| Trades | Wins | Losses | Win rate | Net P&L | Expectancy | Profit factor | Max drawdown |
|---|---|---|---|---|---|---|---|
| 33 (adequate) | 17 | 16 | 51.5% | $973.05 | +0.086R | 1.18 | $1,928.96 |

The account below is the real paper account. It also holds the 4 trade(s) of the old DEBATE rule, stopped in dual-ai-1.2.0 (opposite sides: one debate picked the side and the trade was taken): net $-1,416.51, 0 won, expectancy -0.817R. They stay in the journal, listed as theirs, and are never averaged with the agreement figures.

## Paper account (every trade)

| Account | Equity | P&L today | Total P&L | Drawdown | Open | Trades | Win rate | Expectancy | Profit factor | Risk | Bot |
|---|---|---|---|---|---|---|---|---|---|---|---|
| $200,000.00 | $199,904.36 | $547.30 | $-95.64 | $-95.64 | 3 | 37 (adequate) | 46.0% | -0.012R | 0.94 | ACTIVE | RUNNING |

**WARNING: the hard risk gate refused 1 of the last 20 decisions: MARKET_DATA_STALE x1.** A refusal by the gate after the risk engine approved is never routine. The latest at 10-15 12:15 UTC; 18 decision(s) since, none refused by the gate.

## Last decisions (decision → risk → paper execution)

- 10-16 02:45 AUDUSD BUY: AI DECISION → RISK APPROVED → PAPER EXECUTED
- 10-16 02:45 USDJPY SELL: AI DECISION → RISK REJECTED — reward_risk: 1.02 vs minimum 1.2
- 10-16 01:15 USDCAD SELL: AI DECISION → RISK APPROVED → PAPER EXECUTED
- 10-16 01:00 USDJPY SELL: AI DECISION → RISK APPROVED → PAPER EXECUTED
- 10-16 00:00 EURGBP SELL: AI DECISION → RISK APPROVED → PAPER EXECUTED
- 10-15 17:00 USDCAD SELL: AI DECISION → RISK APPROVED → PAPER EXECUTED
- 10-15 16:45 USDJPY SELL: AI DECISION → RISK APPROVED → PAPER EXECUTED
- 10-15 15:00 GBPUSD SELL: AI DECISION → RISK APPROVED → PAPER EXECUTED
- 10-15 14:45 AUDJPY BUY: AI DECISION → RISK APPROVED → PAPER EXECUTED
- 10-15 14:45 EURCHF SELL: AI DECISION → RISK REJECTED — reward_risk: 1.07 vs minimum 1.2
- 10-15 14:30 EURJPY SELL: AI DECISION → RISK REJECTED — stop_distance: stop 0.0275 vs 3.0 x spread 0.015; spread: spread is 54.5% of the stop (max 25%); cost_to_risk: round-trip cost is 87.3% of the stop (max 25%): spread 0.015 + commission and slippage
- 10-15 14:15 NZDUSD SELL: AI DECISION → RISK REJECTED — cost_to_risk: round-trip cost is 31.8% of the stop (max 25%): spread 0.00015 + commission and slippage
- 10-15 14:00 USDCAD BUY: AI DECISION → RISK APPROVED → PAPER EXECUTED
- 10-15 13:30 EURUSD SELL: AI DECISION → RISK APPROVED → PAPER EXECUTED
- 10-15 13:15 EURCHF SELL: AI DECISION → RISK REJECTED — reward_risk: 0.87 vs minimum 1.2
- 10-15 13:00 EURJPY SELL: AI DECISION → RISK REJECTED — cost_to_risk: round-trip cost is 35.0% of the stop (max 25%): spread 0.015 + commission and slippage
- 10-15 12:30 USDCHF BUY: AI DECISION → RISK REJECTED — cost_to_risk: round-trip cost is 27.4% of the stop (max 25%): spread 0.00015 + commission and slippage
- 10-15 12:30 USDCAD SELL: AI DECISION → RISK APPROVED → PAPER EXECUTED
- 10-15 12:15 AUDUSD SELL: AI DECISION → RISK APPROVED → RISK REJECTED — hard risk gate: RISK_GATE_REJECTED reason=MARKET_DATA_STALE equity_conservative=199493.64 daily_pnl=859.70 daily_limit=-10000.00 total_pnl=-506.36 total_limit=-20000.00 open_risk=276.38 detail='quote 
- 10-15 12:15 USDJPY BUY: AI DECISION → RISK REJECTED — cost_to_risk: round-trip cost is 27.9% of the stop (max 25%): spread 0.01 + commission and slippage

## Latest decisions, NO TRADE included (858 so far)

- 10-16 03:00 USDCHF NO_TRADE: market unavailable for a decision: risk engine: open_positions (3 open, max 3); currency_exposure (2 open positions share a currency, max 2): the model was not consulted
- 10-16 03:00 USDCAD NO_TRADE: market unavailable for a decision: blocked before consulting the model: EXPOSURE: a USDCAD position is already open
- 10-16 02:45 AUDUSD BUY: BUY AUDUSD on M15: AGREE: Trader 1 (nvidia/nemotron-3.5-super-vl:free) BUY 60: M15 just confirmed a bullish BOS at 0.69286 with an HL at 0.69238 and an untested demand OB below, while displacement is 
- 10-16 02:45 USDJPY SELL: SELL USDJPY on M15: AGREE: Trader 1 (nvidia/nemotron-3.5-super-vl:free) SELL 62: H4 is in a downtrend (LH/LL) and the latest M15 structure is a bearish CHoCH at 158.052, with price now below the untes
- 10-16 02:15 GBPUSD NO_TRADE: Trader 2 (independent) gave no usable answer (TIMEOUT: no answer within 420 s (last: INVALID: no JSON object in the reply)): no decision on one trader alone
- 10-16 02:15 EURUSD NO_TRADE: Trader 2 (independent) gave no usable answer (TIMEOUT: no answer within 420 s (last: INVALID: no JSON object in the reply)): no decision on one trader alone
- 10-16 02:00 AUDJPY NO_TRADE: market unavailable for a decision: risk engine: open_positions (3 open, max 3): the model was not consulted
- 10-16 02:00 EURCHF NO_TRADE: market unavailable for a decision: risk engine: open_positions (3 open, max 3): the model was not consulted
- 10-16 01:45 GBPJPY NO_TRADE: market unavailable for a decision: risk engine: open_positions (3 open, max 3): the model was not consulted
- 10-16 01:45 EURJPY NO_TRADE: market unavailable for a decision: risk engine: open_positions (3 open, max 3): the model was not consulted
- 10-16 01:30 EURGBP NO_TRADE: market unavailable for a decision: blocked before consulting the model: EXPOSURE: a EURGBP position is already open
- 10-16 01:30 NZDUSD NO_TRADE: market unavailable for a decision: risk engine: open_positions (3 open, max 3); currency_exposure (2 open positions share a currency, max 2): the model was not consulted

## Open paper positions

| Symbol | Side | Qty | Entry | Stop | Target | P&L |
|---|---|---|---|---|---|---|
| AUDUSD | BUY | 4.31 | 0.69326 | 0.69238 | 0.69528 | $38.79 |
| USDCAD | SELL | 4.22 | 1.4194149999999999 | 1.42065 | 1.4178 | $279.66 |
| EURGBP | SELL | 3.16 | 0.8447300000000001 | 0.84568 | 0.8435 | $29.38 |

## Closed paper trades (latest 20)

| Closed | Symbol | Side | Net | R | Costs | Exit | Source | Rule |
|---|---|---|---|---|---|---|---|---|
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
| 10-15 06:02 | USDCAD | SELL | $-390.68 | -0.78 | $81.34 | STOP | DUAL_AI | AGREE |
| 10-15 04:19 | USDCHF | SELL | $-406.54 | -0.81 | $73.98 | STOP | DUAL_AI | AGREE |
| 10-15 02:46 | EURUSD | SELL | $-392.94 | -0.79 | $69.53 | STOP | DUAL_AI | AGREE |
| 10-15 02:55 | GBPJPY | SELL | $-402.78 | -0.81 | $75.39 | STOP | DUAL_AI | AGREE |
| 10-15 02:52 | NZDUSD | BUY | $528.67 | +1.06 | $85.33 | TARGET | DUAL_AI | AGREE |
| 10-15 01:06 | USDCHF | SELL | $631.35 | +1.27 | $83.09 | TARGET | DUAL_AI | AGREE |
| 10-15 00:13 | USDJPY | SELL | $496.41 | +1.00 | $58.47 | TARGET | DUAL_AI | AGREE |
| 10-14 23:46 | USDCAD | SELL | $827.26 | +1.67 | $146.34 | TARGET | DUAL_AI | AGREE |

## Dual AI desk (two free OpenRouter traders; a trade only when they agree)

OpenRouter `READY` · key set · trader 1 `nvidia/nemotron-3.5-super-vl:free` · trader 2 `nvidia/nemotron-3-super-120b-a12b:free` · debate `dots-studio/dots-3-note-preview:free` · calls today 29/900

Agreement trades 33 (adequate) · wins 17 · losses 16 · net $973.05 · expectancy +0.086R · profit factor 1.18 · old DEBATE rule (stopped in dual-ai-1.2.0): 4 trade(s), net $-1,416.51, apart

Disagreements (not traded; the debate runs in shadow): 57 · the debate's pick if taken: 56 resolved (adequate), expectancy -0.166R · the side it rejected if taken: 61 resolved (adequate), expectancy -0.202R

Exits in shadow (the same trades, followed again; measured, never traded): break-even at +1R +0.001R vs +0.204R as taken (16, insufficient) · held 24 h +0.333R vs +0.333R as taken (8, insufficient) · stop and target twice as far +0.444R vs +0.333R as taken (8, insufficient)

Trades taken by session (UTC): ASIA 15 resolved (insufficient), expectancy -0.068R · LONDON 4 resolved (insufficient), expectancy +0.630R · OVERLAP 7 resolved (insufficient), expectancy -0.279R · NEW_YORK 4 resolved (insufficient), expectancy +1.091R · LATE 3 resolved (insufficient), expectancy -1.106R

| Time | Symbol | Trader 1 | Trader 2 | Debate (shadow) | Rule | Final | Risk |
|---|---|---|---|---|---|---|---|
| 10-16 03:00 | USDCHF | -  | -  | - | MARKET_UNAVAILABLE | NO_TRADE | - |
| 10-16 03:00 | USDCAD | -  | -  | - | MARKET_UNAVAILABLE | NO_TRADE | - |
| 10-16 02:45 | AUDUSD | BUY 60 | BUY 55 | - | AGREE | BUY | APPROVED |
| 10-16 02:45 | USDJPY | SELL 62 | SELL 58 | - | AGREE | SELL | REJECTED |
| 10-16 02:15 | GBPUSD | BUY 58 | -  | - | TRADER2_UNAVAILABLE | NO_TRADE | - |
| 10-16 02:15 | EURUSD | SELL 70 | -  | - | TRADER2_UNAVAILABLE | NO_TRADE | - |
| 10-16 02:00 | AUDJPY | -  | -  | - | MARKET_UNAVAILABLE | NO_TRADE | - |
| 10-16 02:00 | EURCHF | -  | -  | - | MARKET_UNAVAILABLE | NO_TRADE | - |
| 10-16 01:45 | GBPJPY | -  | -  | - | MARKET_UNAVAILABLE | NO_TRADE | - |
| 10-16 01:45 | EURJPY | -  | -  | - | MARKET_UNAVAILABLE | NO_TRADE | - |
| 10-16 01:30 | EURGBP | -  | -  | - | MARKET_UNAVAILABLE | NO_TRADE | - |
| 10-16 01:30 | NZDUSD | -  | -  | - | MARKET_UNAVAILABLE | NO_TRADE | - |

The chart Trader 1 read last: `last_chart.png`. (numbers): no free vision model answered, so Trader 1 read the same chart from its numbers.

Full figures: `paper_forward.json`. Rules: `docs/PAPER_FORWARD.md` on main.
