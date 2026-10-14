# PAPER FORWARD TEST — NOT REAL MONEY

Updated 2026-10-14 08:31 UTC · mode `PAPER_FORWARD` · profile `PAPER-FORWARD-200K` · shift started 2026-10-14 06:46 UTC · decision system `dual_ai`

Research status (historical, unchanged): **NO EDGE — DO NOT TRADE (historical research; this test measures forward)**. This run measures the system forward; it is not evidence of an edge until it has a sample and the forward-eligibility rules say so.

| Account | Equity | P&L today | Total P&L | Drawdown | Open | Trades | Win rate | Expectancy | Profit factor | Risk | Bot |
|---|---|---|---|---|---|---|---|---|---|---|---|
| $200,000.00 | $198,582.88 | $-1,339.11 | $-1,417.12 | $-1,417.12 | 1 | 16 (insufficient) | 37.5% | -0.216R | 0.52 | ACTIVE | RUNNING |

## Last decisions (decision → risk → paper execution)

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
- 10-13 11:30 AUDJPY BUY: AI DECISION → RISK REJECTED — cost_to_risk: round-trip cost is 25.0% of the stop (max 25%): spread 0.018 + commission and slippage
- 10-13 10:15 EURUSD SELL: AI DECISION → RISK APPROVED → PAPER EXECUTED
- 10-13 10:00 EURCHF BUY: AI DECISION → RISK APPROVED → PAPER EXECUTED

## Latest decisions, NO TRADE included (526 so far)

- 10-14 08:15 AUDJPY NO_TRADE: market unavailable for a decision: blocked before consulting the model: EXPOSURE: a AUDJPY position is already open
- 10-14 08:15 EURCHF NO_TRADE: the traders disagree (Trader 1 BUY 75, Trader 2 SELL 55): no trade unless both choose the same side; the debate (nvidia/nemotron-3.5-lightning:free) would have chosen BUY: followed forward in shadow, 
- 10-14 08:00 GBPJPY NO_TRADE: the traders disagree (Trader 1 BUY 65, Trader 2 SELL 55): no trade unless both choose the same side; the debate (nvidia/nemotron-3.5-lightning:free) would have chosen BUY: followed forward in shadow, 
- 10-14 08:00 EURJPY SELL: SELL EURJPY on M15: AGREE: Trader 1 (dots-studio/dots-3-note-preview:free) SELL 72: The H4 trend is down with bearish breaks, and the M15 shows a bearish CHOCH, lower low, and bearish displacement. Li
- 10-14 07:45 EURGBP SELL: SELL EURGBP on M15: AGREE: Trader 1 (dots-studio/dots-3-note-preview:free) SELL 75: The recent sweep of highs at 0.8449 represents a classic bearish liquidity grab above the EQH levels, signaling a hi
- 10-14 07:45 NZDUSD NO_TRADE: the traders disagree (Trader 1 SELL 72, Trader 2 BUY 65): no trade unless both choose the same side; the debate (nvidia/nemotron-3.5-lightning:free) would have chosen BUY: followed forward in shadow, 
- 10-14 07:30 USDCHF NO_TRADE: the traders disagree (Trader 1 BUY 75, Trader 2 SELL 65): no trade unless both choose the same side; the debate (nvidia/nemotron-3.5-lightning:free) would have chosen BUY: followed forward in shadow, 
- 10-14 07:30 USDCAD SELL: SELL USDCAD on M15: AGREE: Trader 1 (dots-studio/dots-3-note-preview:free) SELL 65: The higher timeframe H4 is in a clear DOWN trend with a bearish BOS, and the M15 shows a bearish liquidity sweep of 
- 10-14 07:15 AUDUSD BUY: BUY AUDUSD on M15: AGREE: Trader 1 (nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free) BUY 85: The setup shows a clear bullish structure with demand zone untouched and higher timeframe uptrend, makin
- 10-14 07:15 USDJPY SELL: SELL USDJPY on M15: AGREE: Trader 1 (nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free) SELL 75: The higher timeframe is bearish and price is near a key resistance (158.279) with sell-side liquidity 
- 10-14 07:00 GBPUSD NO_TRADE: market unavailable for a decision: risk engine: open_positions (3 open, max 3): the model was not consulted
- 10-14 07:00 EURUSD NO_TRADE: market unavailable for a decision: risk engine: open_positions (3 open, max 3): the model was not consulted

## Open paper positions

| Symbol | Side | Qty | Entry | Stop | Target | P&L |
|---|---|---|---|---|---|---|
| AUDJPY | BUY | 2.71 | 110.799 | 110.548 | 111.15 | $392.68 |

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

OpenRouter `READY` · key set · trader 1 `dots-studio/dots-3-note-preview:free` · trader 2 `nvidia/nemotron-3-ultra-550b-a55b:free` · debate `nvidia/nemotron-3.5-lightning:free` · calls today 32/900

AI trades 16 (insufficient) · wins 6 · losses 10 · expectancy -0.216R · profit factor 0.52

Disagreements (not traded; the debate runs in shadow): 16 · the debate's pick if taken: 8 resolved (insufficient), expectancy -0.066R · the side it rejected if taken: 13 resolved (insufficient), expectancy +0.276R

Exits in shadow (the same trades, followed again; measured, never traded): break-even at +1R none resolved yet · held 24 h none resolved yet · stop and target twice as far none resolved yet

Trades taken by session (UTC): ASIA 4 resolved (insufficient), expectancy +0.107R · LONDON 3 resolved (insufficient), expectancy +0.542R · OVERLAP 3 resolved (insufficient), expectancy -0.479R · NEW_YORK 2 resolved (insufficient), expectancy +0.212R · LATE 3 resolved (insufficient), expectancy -1.106R

| Time | Symbol | Trader 1 | Trader 2 | Debate (shadow) | Rule | Final | Risk |
|---|---|---|---|---|---|---|---|
| 10-14 08:15 | AUDJPY | -  | -  | - | MARKET_UNAVAILABLE | NO_TRADE | - |
| 10-14 08:15 | EURCHF | BUY 75 | SELL 55 | BUY | DISAGREE | NO_TRADE | - |
| 10-14 08:00 | GBPJPY | BUY 65 | SELL 55 | BUY | DISAGREE | NO_TRADE | - |
| 10-14 08:00 | EURJPY | SELL 72 | SELL 65 | - | AGREE | SELL | REJECTED |
| 10-14 07:45 | EURGBP | SELL 75 | SELL 70 | - | AGREE | SELL | APPROVED |
| 10-14 07:45 | NZDUSD | SELL 72 | BUY 65 | BUY | DISAGREE | NO_TRADE | - |
| 10-14 07:30 | USDCHF | BUY 75 | SELL 65 | BUY | DISAGREE | NO_TRADE | - |
| 10-14 07:30 | USDCAD | SELL 65 | SELL 70 | - | AGREE | SELL | REJECTED |
| 10-14 07:15 | AUDUSD | BUY 85 | BUY 65 | - | AGREE | BUY | REJECTED |
| 10-14 07:15 | USDJPY | SELL 75 | SELL 68 | - | AGREE | SELL | REJECTED |
| 10-14 07:00 | GBPUSD | -  | -  | - | MARKET_UNAVAILABLE | NO_TRADE | - |
| 10-14 07:00 | EURUSD | -  | -  | - | MARKET_UNAVAILABLE | NO_TRADE | - |

The chart Trader 1 read last: `last_chart.png`. (numbers): no free vision model answered, so Trader 1 read the same chart from its numbers.

Full figures: `paper_forward.json`. Rules: `docs/PAPER_FORWARD.md` on main.
