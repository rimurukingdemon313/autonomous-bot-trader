# PAPER FORWARD TEST — NOT REAL MONEY

Updated 2026-10-14 09:32 UTC · mode `PAPER_FORWARD` · profile `PAPER-FORWARD-200K` · shift started 2026-10-14 06:46 UTC · decision system `dual_ai`

Research status (historical, unchanged): **NO EDGE — DO NOT TRADE (historical research; this test measures forward)**. This run measures the system forward; it is not evidence of an edge until it has a sample and the forward-eligibility rules say so.

| Account | Equity | P&L today | Total P&L | Drawdown | Open | Trades | Win rate | Expectancy | Profit factor | Risk | Bot |
|---|---|---|---|---|---|---|---|---|---|---|---|
| $200,000.00 | $198,647.75 | $-1,274.23 | $-1,352.25 | $-1,352.25 | 1 | 16 (insufficient) | 37.5% | -0.216R | 0.52 | ACTIVE | RUNNING |

## Last decisions (decision → risk → paper execution)

- 10-14 09:15 NZDUSD SELL: AI DECISION → RISK APPROVED → RISK REJECTED — hard risk gate: RISK_GATE_REJECTED reason=PROFILE_CHANGED  detail='this evaluation run was started under profile PAPER-FORWARD-200K (98db6393b13e); the gate now holds PAPER-FORWARD-200K (3ceb1c2bcf85)
- 10-14 09:00 USDCHF BUY: AI DECISION → RISK APPROVED → RISK REJECTED — hard risk gate: RISK_GATE_REJECTED reason=PROFILE_CHANGED  detail='this evaluation run was started under profile PAPER-FORWARD-200K (98db6393b13e); the gate now holds PAPER-FORWARD-200K (3ceb1c2bcf85)
- 10-14 08:30 EURUSD SELL: AI DECISION → RISK REJECTED — reward_risk: 0.70 vs minimum 1.2
- 10-14 08:00 EURJPY SELL: AI DECISION → RISK REJECTED — cost_to_risk: round-trip cost is 26.8% of the stop (max 25%): spread 0.015 + commission and slippage
- 10-14 07:45 EURGBP SELL: AI DECISION → RISK APPROVED → RISK REJECTED — hard risk gate: RISK_GATE_REJECTED reason=PROFILE_CHANGED  detail='this evaluation run was started under profile PAPER-FORWARD-200K (98db6393b13e); the gate now holds PAPER-FORWARD-200K (3ceb1c2bcf85)
- 10-14 07:30 USDCAD SELL: AI DECISION → RISK REJECTED — reward_risk: 0.49 vs minimum 1.2
- 10-14 07:15 AUDUSD BUY: AI DECISION → RISK REJECTED — reward_risk: 0.94 vs minimum 1.2
- 10-14 07:15 USDJPY SELL: AI DECISION → RISK REJECTED — reward_risk: 1.04 vs minimum 1.2
- 10-14 02:45 AUDJPY BUY: AI DECISION → RISK APPROVED → PAPER EXECUTED
- 10-14 02:00 USDCAD SELL: AI DECISION → RISK APPROVED → PAPER EXECUTED
- 10-14 00:00 EURCHF SELL: AI DECISION → RISK APPROVED → PAPER EXECUTED
- 10-13 22:30 AUDJPY SELL: AI DECISION → RISK APPROVED → PAPER EXECUTED
- 10-13 22:30 EURCHF BUY: AI DECISION → RISK REJECTED — reward_risk: 1.10 vs minimum 1.2
- 10-13 22:15 GBPJPY BUY: AI DECISION → RISK REJECTED — reward_risk: 1.19 vs minimum 1.2
- 10-13 22:15 EURJPY SELL: AI DECISION → RISK REJECTED — reward_risk: 0.91 vs minimum 1.2
- 10-13 22:00 EURGBP SELL: AI DECISION → RISK REJECTED — cost_to_risk: round-trip cost is 28.4% of the stop (max 25%): spread 0.00012 + commission and slippage
- 10-13 21:15 EURUSD SELL: AI DECISION → RISK APPROVED → PAPER EXECUTED
- 10-13 18:15 EURJPY SELL: AI DECISION → RISK APPROVED → PAPER EXECUTED
- 10-13 15:00 EURGBP BUY: AI DECISION → RISK APPROVED → PAPER EXECUTED
- 10-13 15:00 NZDUSD SELL: AI DECISION → RISK APPROVED → PAPER EXECUTED

## Latest decisions, NO TRADE included (534 so far)

- 10-14 09:15 EURGBP NO_TRADE: the traders disagree (Trader 1 BUY 65, Trader 2 SELL 70): no trade unless both choose the same side; the debate (nvidia/nemotron-3-super-120b-a12b:free) would have chosen SELL: followed forward in sha
- 10-14 09:15 NZDUSD SELL: SELL NZDUSD on M15: AGREE: Trader 1 (dots-studio/dots-3-note-preview:free) SELL 72: The M15 structure shows a fresh bearish BOS at 0.56211 and a pattern of lower highs/lows, while the price is capped 
- 10-14 09:00 USDCHF BUY: BUY USDCHF on M15: AGREE: Trader 1 (dots-studio/dots-3-note-preview:free) BUY 75: The M15 and H4 trends are firmly bullish with higher highs, higher lows, and consecutive bullish BOS breaks. Price is 
- 10-14 09:00 USDCAD NO_TRADE: the traders disagree (Trader 1 BUY 65, Trader 2 SELL 70): no trade unless both choose the same side; the debate (nvidia/nemotron-3.5-lightning:free) would have chosen SELL: followed forward in shadow,
- 10-14 08:45 AUDUSD NO_TRADE: the traders disagree (Trader 1 BUY 75, Trader 2 SELL 55): no trade unless both choose the same side; the debate (nvidia/nemotron-3.5-lightning:free) would have chosen SELL: followed forward in shadow,
- 10-14 08:45 USDJPY NO_TRADE: the traders disagree (Trader 1 BUY 72, Trader 2 SELL 65): no trade unless both choose the same side; the debate (nvidia/nemotron-3.5-lightning:free) would have chosen BUY: followed forward in shadow, 
- 10-14 08:30 GBPUSD NO_TRADE: the traders disagree (Trader 1 BUY 60, Trader 2 SELL 65): no trade unless both choose the same side; the debate (nvidia/nemotron-3.5-lightning:free) would have chosen BUY: followed forward in shadow, 
- 10-14 08:30 EURUSD SELL: SELL EURUSD on M15: AGREE: Trader 1 (dots-studio/dots-3-note-preview:free) SELL 70: The bearish trend is confirmed on both M15 and H4, with price trading below the key supply order block and recent re
- 10-14 08:15 AUDJPY NO_TRADE: market unavailable for a decision: blocked before consulting the model: EXPOSURE: a AUDJPY position is already open
- 10-14 08:15 EURCHF NO_TRADE: the traders disagree (Trader 1 BUY 75, Trader 2 SELL 55): no trade unless both choose the same side; the debate (nvidia/nemotron-3.5-lightning:free) would have chosen BUY: followed forward in shadow, 
- 10-14 08:00 GBPJPY NO_TRADE: the traders disagree (Trader 1 BUY 65, Trader 2 SELL 55): no trade unless both choose the same side; the debate (nvidia/nemotron-3.5-lightning:free) would have chosen BUY: followed forward in shadow, 
- 10-14 08:00 EURJPY SELL: SELL EURJPY on M15: AGREE: Trader 1 (dots-studio/dots-3-note-preview:free) SELL 72: The H4 trend is down with bearish breaks, and the M15 shows a bearish CHOCH, lower low, and bearish displacement. Li

## Open paper positions

| Symbol | Side | Qty | Entry | Stop | Target | P&L |
|---|---|---|---|---|---|---|
| AUDJPY | BUY | 2.71 | 110.799 | 110.548 | 111.15 | $457.56 |

## Closed paper trades (latest 20)

| Closed | Symbol | Side | Net | R | Costs | Exit | Source |
|---|---|---|---|---|---|---|---|
| 10-14 08:08 | EURCHF | SELL | $-272.22 | -0.55 | $92.73 | TIME | DUAL_AI |
| 10-14 07:07 | USDCAD | SELL | $-392.79 | -0.79 | $96.71 | STOP | DUAL_AI |
| 10-14 02:42 | EURUSD | SELL | $-426.65 | -0.86 | $74.63 | STOP | DUAL_AI |
| 10-14 00:34 | AUDJPY | SELL | $-411.49 | -0.83 | $98.39 | STOP | DUAL_AI |
| 10-13 23:06 | NZDUSD | SELL | $13.40 | +0.03 | $100.00 | TIME | DUAL_AI |
| 10-13 21:26 | EURGBP | BUY | $-439.21 | -0.88 | $101.27 | STOP | DUAL_AI |
| 10-13 21:01 | EURJPY | SELL | $517.15 | +1.04 | $118.81 | TARGET | DUAL_AI |
| 10-13 18:06 | EURCHF | BUY | $370.36 | +0.74 | $91.83 | TIME | DUAL_AI |
| 10-13 11:11 | EURUSD | SELL | $-422.48 | -0.85 | $80.75 | STOP | DUAL_AI |
| 10-13 10:48 | USDCAD | SELL | $73.61 | +0.30 | $46.17 | TIME | DUAL_AI |
| 10-13 06:48 | USDJPY | SELL | $228.86 | +0.92 | $42.21 | TARGET | DUAL_AI |
| 10-13 05:42 | AUDUSD | SELL | $-214.73 | -0.86 | $47.12 | STOP | DUAL_AI |
| 10-13 01:03 | EURUSD | SELL | $-431.70 | -0.86 | $87.38 | STOP | DUAL_AI |
| 10-13 01:04 | GBPUSD | SELL | $-355.19 | -0.71 | $110.84 | STOP | DUAL_AI |
| 10-12 21:01 | USDJPY | BUY | $-414.90 | -0.83 | $114.86 | STOP | DUAL_AI |
| 10-12 15:38 | EURUSD | SELL | $768.18 | +1.54 | $66.08 | TARGET | DUAL_AI |

## Dual AI desk (two free OpenRouter traders; a trade only when they agree)

OpenRouter `READY` · key set · trader 1 `dots-studio/dots-3-note-preview:free` · trader 2 `nvidia/nemotron-3-ultra-550b-a55b:free` · debate `nvidia/nemotron-3-super-120b-a12b:free` · calls today 56/900

AI trades 16 (insufficient) · wins 6 · losses 10 · expectancy -0.216R · profit factor 0.52

Disagreements (not traded; the debate runs in shadow): 21 · the debate's pick if taken: 10 resolved (insufficient), expectancy -0.275R · the side it rejected if taken: 15 resolved (insufficient), expectancy +0.247R

Exits in shadow (the same trades, followed again; measured, never traded): break-even at +1R none resolved yet · held 24 h none resolved yet · stop and target twice as far none resolved yet

Trades taken by session (UTC): ASIA 4 resolved (insufficient), expectancy +0.107R · LONDON 3 resolved (insufficient), expectancy +0.542R · OVERLAP 3 resolved (insufficient), expectancy -0.479R · NEW_YORK 2 resolved (insufficient), expectancy +0.212R · LATE 3 resolved (insufficient), expectancy -1.106R

| Time | Symbol | Trader 1 | Trader 2 | Debate (shadow) | Rule | Final | Risk |
|---|---|---|---|---|---|---|---|
| 10-14 09:15 | EURGBP | BUY 65 | SELL 70 | SELL | DISAGREE | NO_TRADE | - |
| 10-14 09:15 | NZDUSD | SELL 72 | SELL 70 | - | AGREE | SELL | APPROVED |
| 10-14 09:00 | USDCHF | BUY 75 | BUY 70 | - | AGREE | BUY | APPROVED |
| 10-14 09:00 | USDCAD | BUY 65 | SELL 70 | SELL | DISAGREE | NO_TRADE | - |
| 10-14 08:45 | AUDUSD | BUY 75 | SELL 55 | SELL | DISAGREE | NO_TRADE | - |
| 10-14 08:45 | USDJPY | BUY 72 | SELL 65 | BUY | DISAGREE | NO_TRADE | - |
| 10-14 08:30 | GBPUSD | BUY 60 | SELL 65 | BUY | DISAGREE | NO_TRADE | - |
| 10-14 08:30 | EURUSD | SELL 70 | SELL 65 | - | AGREE | SELL | REJECTED |
| 10-14 08:15 | AUDJPY | -  | -  | - | MARKET_UNAVAILABLE | NO_TRADE | - |
| 10-14 08:15 | EURCHF | BUY 75 | SELL 55 | BUY | DISAGREE | NO_TRADE | - |
| 10-14 08:00 | GBPJPY | BUY 65 | SELL 55 | BUY | DISAGREE | NO_TRADE | - |
| 10-14 08:00 | EURJPY | SELL 72 | SELL 65 | - | AGREE | SELL | REJECTED |

The chart Trader 1 read last: `last_chart.png`. (numbers): no free vision model answered, so Trader 1 read the same chart from its numbers.

Full figures: `paper_forward.json`. Rules: `docs/PAPER_FORWARD.md` on main.
