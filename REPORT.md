# PAPER FORWARD TEST — NOT REAL MONEY

Updated 2026-10-15 13:56 UTC · mode `PAPER_FORWARD` · profile `PAPER-FORWARD-200K` · shift started 2026-10-15 11:56 UTC · decision system `dual_ai`

Research status (historical, unchanged): **NO EDGE — DO NOT TRADE (historical research; this test measures forward)**. This run measures the system forward; it is not evidence of an edge until it has a sample and the forward-eligibility rules say so.

| Account | Equity | P&L today | Total P&L | Drawdown | Open | Trades | Win rate | Expectancy | Profit factor | Risk | Bot |
|---|---|---|---|---|---|---|---|---|---|---|---|
| $200,000.00 | $199,584.45 | $950.51 | $-415.55 | $-415.55 | 3 | 28 (insufficient) | 46.4% | -0.030R | 0.90 | ACTIVE | RUNNING |

**WARNING: the hard risk gate refused 2 of the last 20 decisions: MARKET_DATA_STALE x2.** A refusal by the gate after the risk engine approved is never routine. The latest at 10-15 12:15 UTC; 5 decision(s) since, none refused by the gate.

## Last decisions (decision → risk → paper execution)

- 10-15 13:30 EURUSD SELL: AI DECISION → RISK APPROVED → PAPER EXECUTED
- 10-15 13:15 EURCHF SELL: AI DECISION → RISK REJECTED — reward_risk: 0.87 vs minimum 1.2
- 10-15 13:00 EURJPY SELL: AI DECISION → RISK REJECTED — cost_to_risk: round-trip cost is 35.0% of the stop (max 25%): spread 0.015 + commission and slippage
- 10-15 12:30 USDCHF BUY: AI DECISION → RISK REJECTED — cost_to_risk: round-trip cost is 27.4% of the stop (max 25%): spread 0.00015 + commission and slippage
- 10-15 12:30 USDCAD SELL: AI DECISION → RISK APPROVED → PAPER EXECUTED
- 10-15 12:15 AUDUSD SELL: AI DECISION → RISK APPROVED → RISK REJECTED — hard risk gate: RISK_GATE_REJECTED reason=MARKET_DATA_STALE equity_conservative=199493.64 daily_pnl=859.70 daily_limit=-10000.00 total_pnl=-506.36 total_limit=-20000.00 open_risk=276.38 detail='quote 
- 10-15 12:15 USDJPY BUY: AI DECISION → RISK REJECTED — cost_to_risk: round-trip cost is 27.9% of the stop (max 25%): spread 0.01 + commission and slippage
- 10-15 12:00 GBPUSD BUY: AI DECISION → RISK REJECTED — cost_to_risk: round-trip cost is 31.8% of the stop (max 25%): spread 0.00012 + commission and slippage
- 10-15 12:00 EURUSD SELL: AI DECISION → RISK REJECTED — cost_to_risk: round-trip cost is 25.4% of the stop (max 25%): spread 8e-05 + commission and slippage
- 10-15 08:45 EURGBP SELL: AI DECISION → RISK APPROVED → PAPER EXECUTED
- 10-15 08:30 USDCHF SELL: AI DECISION → RISK REJECTED — cost_to_risk: round-trip cost is 31.0% of the stop (max 25%): spread 0.00015 + commission and slippage
- 10-15 08:30 USDCAD BUY: AI DECISION → RISK REJECTED — reward_risk: 1.03 vs minimum 1.2
- 10-15 08:15 AUDUSD SELL: AI DECISION → RISK REJECTED — cost_to_risk: round-trip cost is 33.9% of the stop (max 25%): spread 0.0001 + commission and slippage
- 10-15 06:45 USDJPY BUY: AI DECISION → RISK APPROVED → PAPER EXECUTED
- 10-15 06:15 EURGBP SELL: AI DECISION → RISK APPROVED → RISK REJECTED — hard risk gate: RISK_GATE_REJECTED reason=MARKET_DATA_STALE equity_conservative=199578.57 daily_pnl=944.63 daily_limit=-10000.00 total_pnl=-421.43 total_limit=-20000.00 open_risk=910.95 detail='quote 
- 10-15 04:45 NZDUSD SELL: AI DECISION → RISK APPROVED → PAPER EXECUTED
- 10-15 04:30 USDCHF SELL: AI DECISION → RISK REJECTED — reward_risk: 1.13 vs minimum 1.2
- 10-15 03:30 EURJPY BUY: AI DECISION → RISK APPROVED → PAPER EXECUTED
- 10-15 03:15 EURGBP SELL: AI DECISION → RISK REJECTED — reward_risk: 1.08 vs minimum 1.2
- 10-15 03:00 USDCHF SELL: AI DECISION → RISK APPROVED → PAPER EXECUTED

## Latest decisions, NO TRADE included (754 so far)

- 10-15 13:45 AUDUSD NO_TRADE: market unavailable for a decision: risk engine: open_positions (3 open, max 3); currency_exposure (2 open positions share a currency, max 2): the model was not consulted
- 10-15 13:45 USDJPY NO_TRADE: market unavailable for a decision: risk engine: open_positions (3 open, max 3); currency_exposure (2 open positions share a currency, max 2): the model was not consulted
- 10-15 13:30 GBPUSD NO_TRADE: market unavailable for a decision: risk engine: open_positions (3 open, max 3); currency_exposure (2 open positions share a currency, max 2): the model was not consulted
- 10-15 13:30 EURUSD SELL: SELL EURUSD on M15: AGREE: Trader 1 (dots-studio/dots-3-note-preview:free) SELL 72: The M15 trend is clearly bearish with a series of lower highs and lower lows, and the price is testing the strong PD
- 10-15 13:15 AUDJPY NO_TRADE: the traders disagree (Trader 1 BUY 55, Trader 2 SELL 58): no trade unless both choose the same side; the debate (nvidia/nemotron-3.5-lightning:free) would have chosen SELL: followed forward in shadow,
- 10-15 13:15 EURCHF SELL: SELL EURCHF on M15: AGREE: Trader 1 (nvidia/nemotron-3-ultra-550b-a55b:free) SELL 65: Bearish CHoCH and supply block define downside bias; stop above 0.93036 respects structure and risk-engine minimum
- 10-15 13:00 GBPJPY NO_TRADE: the traders disagree (Trader 1 BUY 70, Trader 2 SELL 60): no trade unless both choose the same side; the debate (nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free) would have chosen BUY: followed for
- 10-15 13:00 EURJPY SELL: SELL EURJPY on M15: AGREE: Trader 1 (dots-studio/dots-3-note-preview:free) SELL 65: The M15 chart shows a bearish structure break (CHOCH at 176.891 and BOS at 176.908), shifting the short-term trend d
- 10-15 12:45 EURGBP NO_TRADE: market unavailable for a decision: blocked before consulting the model: EXPOSURE: a EURGBP position is already open
- 10-15 12:45 NZDUSD NO_TRADE: the traders disagree (Trader 1 SELL 65, Trader 2 BUY 55): no trade unless both choose the same side; the debate (nvidia/nemotron-3-ultra-550b-a55b:free) would have chosen BUY: followed forward in shad
- 10-15 12:30 USDCHF BUY: BUY USDCHF on M15: AGREE: Trader 1 (dots-studio/dots-3-note-preview:free) BUY 65: The overall trend is UP on both M15 and H4, and the price is testing a major support confluence consisting of the dema
- 10-15 12:30 USDCAD SELL: SELL USDCAD on M15: AGREE: Trader 1 (dots-studio/dots-3-note-preview:free) SELL 75: The higher timeframe (H4) maintains a bearish structure, and the execution timeframe shows a recent bearish liquidit

## Open paper positions

| Symbol | Side | Qty | Entry | Stop | Target | P&L |
|---|---|---|---|---|---|---|
| EURUSD | SELL | 3.23 | 1.1210499999999999 | 1.1222 | 1.1194 | $-319.77 |
| USDCAD | SELL | 4.82 | 1.4213149999999999 | 1.4223 | 1.4193 | $420.95 |
| EURGBP | SELL | 1.66 | 0.8460300000000001 | 0.8469 | 0.84469 | $15.41 |

## Closed paper trades (latest 20)

| Closed | Symbol | Side | Net | R | Costs | Exit | Source |
|---|---|---|---|---|---|---|---|
| 10-15 12:02 | NZDUSD | SELL | $225.96 | +0.91 | $38.64 | TARGET | DUAL_AI |
| 10-15 11:34 | EURJPY | BUY | $29.16 | +0.06 | $32.94 | TIME | DUAL_AI |
| 10-15 08:05 | USDJPY | BUY | $-216.31 | -0.87 | $18.93 | STOP | DUAL_AI |
| 10-15 06:02 | USDCAD | SELL | $-390.68 | -0.78 | $81.34 | STOP | DUAL_AI |
| 10-15 04:19 | USDCHF | SELL | $-406.54 | -0.81 | $73.98 | STOP | DUAL_AI |
| 10-15 02:46 | EURUSD | SELL | $-392.94 | -0.79 | $69.53 | STOP | DUAL_AI |
| 10-15 02:55 | GBPJPY | SELL | $-402.78 | -0.81 | $75.39 | STOP | DUAL_AI |
| 10-15 02:52 | NZDUSD | BUY | $528.67 | +1.06 | $85.33 | TARGET | DUAL_AI |
| 10-15 01:06 | USDCHF | SELL | $631.35 | +1.27 | $83.09 | TARGET | DUAL_AI |
| 10-15 00:13 | USDJPY | SELL | $496.41 | +1.00 | $58.47 | TARGET | DUAL_AI |
| 10-14 23:46 | USDCAD | SELL | $827.26 | +1.67 | $146.34 | TARGET | DUAL_AI |
| 10-14 10:59 | AUDJPY | BUY | $348.10 | +0.70 | $53.12 | TIME | DUAL_AI |
| 10-14 08:08 | EURCHF | SELL | $-272.22 | -0.55 | $92.73 | TIME | DUAL_AI |
| 10-14 07:07 | USDCAD | SELL | $-392.79 | -0.79 | $96.71 | STOP | DUAL_AI |
| 10-14 02:42 | EURUSD | SELL | $-426.65 | -0.86 | $74.63 | STOP | DUAL_AI |
| 10-14 00:34 | AUDJPY | SELL | $-411.49 | -0.83 | $98.39 | STOP | DUAL_AI |
| 10-13 23:06 | NZDUSD | SELL | $13.40 | +0.03 | $100.00 | TIME | DUAL_AI |
| 10-13 21:26 | EURGBP | BUY | $-439.21 | -0.88 | $101.27 | STOP | DUAL_AI |
| 10-13 21:01 | EURJPY | SELL | $517.15 | +1.04 | $118.81 | TARGET | DUAL_AI |
| 10-13 18:06 | EURCHF | BUY | $370.36 | +0.74 | $91.83 | TIME | DUAL_AI |

## Dual AI desk (two free OpenRouter traders; a trade only when they agree)

OpenRouter `READY` · key set · trader 1 `dots-studio/dots-3-note-preview:free` · trader 2 `nvidia/nemotron-3-super-120b-a12b:free` · debate `nvidia/nemotron-3-ultra-550b-a55b:free` · calls today 46/900

AI trades 28 (insufficient) · wins 13 · losses 15 · expectancy -0.030R · profit factor 0.90

Disagreements (not traded; the debate runs in shadow): 55 · the debate's pick if taken: 51 resolved (adequate), expectancy -0.146R · the side it rejected if taken: 56 resolved (adequate), expectancy -0.164R

Exits in shadow (the same trades, followed again; measured, never traded): break-even at +1R +0.246R vs +0.393R as taken (10, insufficient) · held 24 h none resolved yet · stop and target twice as far none resolved yet

Trades taken by session (UTC): ASIA 14 resolved (insufficient), expectancy +0.001R · LONDON 3 resolved (insufficient), expectancy +0.542R · OVERLAP 3 resolved (insufficient), expectancy -0.479R · NEW_YORK 4 resolved (insufficient), expectancy +1.091R · LATE 3 resolved (insufficient), expectancy -1.106R

| Time | Symbol | Trader 1 | Trader 2 | Debate (shadow) | Rule | Final | Risk |
|---|---|---|---|---|---|---|---|
| 10-15 13:45 | AUDUSD | -  | -  | - | MARKET_UNAVAILABLE | NO_TRADE | - |
| 10-15 13:45 | USDJPY | -  | -  | - | MARKET_UNAVAILABLE | NO_TRADE | - |
| 10-15 13:30 | GBPUSD | -  | -  | - | MARKET_UNAVAILABLE | NO_TRADE | - |
| 10-15 13:30 | EURUSD | SELL 72 | SELL 66 | - | AGREE | SELL | APPROVED |
| 10-15 13:15 | AUDJPY | BUY 55 (numbers) | SELL 58 | SELL | DISAGREE | NO_TRADE | - |
| 10-15 13:15 | EURCHF | SELL 65 (numbers) | SELL 62 | - | AGREE | SELL | REJECTED |
| 10-15 13:00 | GBPJPY | BUY 70 | SELL 60 | BUY | DISAGREE | NO_TRADE | - |
| 10-15 13:00 | EURJPY | SELL 65 | SELL 68 | - | AGREE | SELL | REJECTED |
| 10-15 12:45 | EURGBP | -  | -  | - | MARKET_UNAVAILABLE | NO_TRADE | - |
| 10-15 12:45 | NZDUSD | SELL 65 | BUY 55 | BUY | DISAGREE | NO_TRADE | - |
| 10-15 12:30 | USDCHF | BUY 65 | BUY 60 | - | AGREE | BUY | REJECTED |
| 10-15 12:30 | USDCAD | SELL 75 | SELL 65 | - | AGREE | SELL | APPROVED |

The chart Trader 1 read last: `last_chart.png`. (numbers): no free vision model answered, so Trader 1 read the same chart from its numbers.

Full figures: `paper_forward.json`. Rules: `docs/PAPER_FORWARD.md` on main.
