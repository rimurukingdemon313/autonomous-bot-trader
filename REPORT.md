# PAPER FORWARD TEST — NOT REAL MONEY

Updated 2026-10-14 14:52 UTC · mode `PAPER_FORWARD` · profile `PAPER-FORWARD-200K` · shift started 2026-10-14 12:22 UTC · decision system `dual_ai`

Research status (historical, unchanged): **NO EDGE — DO NOT TRADE (historical research; this test measures forward)**. This run measures the system forward; it is not evidence of an edge until it has a sample and the forward-eligibility rules say so.

| Account | Equity | P&L today | Total P&L | Drawdown | Open | Trades | Win rate | Expectancy | Profit factor | Risk | Bot |
|---|---|---|---|---|---|---|---|---|---|---|---|
| $200,000.00 | $198,538.30 | $-1,383.69 | $-1,461.70 | $-1,461.70 | 0 | 17 (insufficient) | 41.2% | -0.162R | 0.61 | ACTIVE | RUNNING |

## Last decisions (decision → risk → paper execution)

- 10-14 14:30 AUDUSD SELL: AI DECISION → RISK APPROVED → RISK REJECTED — hard risk gate: RISK_GATE_REJECTED reason=PROFILE_CHANGED  detail='this evaluation run was started under profile PAPER-FORWARD-200K (98db6393b13e); the gate now holds PAPER-FORWARD-200K (3ceb1c2bcf85)
- 10-14 14:30 USDJPY SELL: AI DECISION → RISK APPROVED → RISK REJECTED — hard risk gate: RISK_GATE_REJECTED reason=PROFILE_CHANGED  detail='this evaluation run was started under profile PAPER-FORWARD-200K (98db6393b13e); the gate now holds PAPER-FORWARD-200K (3ceb1c2bcf85)
- 10-14 14:15 GBPUSD SELL: AI DECISION → RISK APPROVED → RISK REJECTED — hard risk gate: RISK_GATE_REJECTED reason=PROFILE_CHANGED  detail='this evaluation run was started under profile PAPER-FORWARD-200K (98db6393b13e); the gate now holds PAPER-FORWARD-200K (3ceb1c2bcf85)
- 10-14 14:15 EURUSD SELL: AI DECISION → RISK APPROVED → RISK REJECTED — hard risk gate: RISK_GATE_REJECTED reason=PROFILE_CHANGED  detail='this evaluation run was started under profile PAPER-FORWARD-200K (98db6393b13e); the gate now holds PAPER-FORWARD-200K (3ceb1c2bcf85)
- 10-14 14:00 AUDJPY SELL: AI DECISION → RISK APPROVED → RISK REJECTED — hard risk gate: RISK_GATE_REJECTED reason=PROFILE_CHANGED  detail='this evaluation run was started under profile PAPER-FORWARD-200K (98db6393b13e); the gate now holds PAPER-FORWARD-200K (3ceb1c2bcf85)
- 10-14 13:45 GBPJPY BUY: AI DECISION → RISK REJECTED — cost_to_risk: round-trip cost is 28.5% of the stop (max 25%): spread 0.025 + commission and slippage
- 10-14 13:45 EURJPY SELL: AI DECISION → RISK APPROVED → RISK REJECTED — hard risk gate: RISK_GATE_REJECTED reason=PROFILE_CHANGED  detail='this evaluation run was started under profile PAPER-FORWARD-200K (98db6393b13e); the gate now holds PAPER-FORWARD-200K (3ceb1c2bcf85)
- 10-14 13:30 EURGBP SELL: AI DECISION → RISK REJECTED — cost_to_risk: round-trip cost is 27.6% of the stop (max 25%): spread 0.00012 + commission and slippage
- 10-14 13:30 NZDUSD BUY: AI DECISION → RISK REJECTED — reward_risk: 1.18 vs minimum 1.2
- 10-14 12:45 USDJPY SELL: AI DECISION → RISK APPROVED → RISK REJECTED — hard risk gate: RISK_GATE_REJECTED reason=PROFILE_CHANGED  detail='this evaluation run was started under profile PAPER-FORWARD-200K (98db6393b13e); the gate now holds PAPER-FORWARD-200K (3ceb1c2bcf85)
- 10-14 12:30 GBPUSD BUY: AI DECISION → RISK REJECTED — cost_to_risk: round-trip cost is 37.5% of the stop (max 25%): spread 0.00012 + commission and slippage
- 10-14 12:00 USDCHF SELL: AI DECISION → RISK REJECTED — cost_to_risk: round-trip cost is 35.6% of the stop (max 25%): spread 0.00015 + commission and slippage
- 10-14 12:00 USDCAD SELL: AI DECISION → RISK REJECTED — reward_risk: 1.04 vs minimum 1.2
- 10-14 11:45 USDJPY SELL: AI DECISION → RISK APPROVED → RISK REJECTED — hard risk gate: RISK_GATE_REJECTED reason=PROFILE_CHANGED  detail='this evaluation run was started under profile PAPER-FORWARD-200K (98db6393b13e); the gate now holds PAPER-FORWARD-200K (3ceb1c2bcf85)
- 10-14 11:30 GBPUSD BUY: AI DECISION → RISK APPROVED → RISK REJECTED — hard risk gate: RISK_GATE_REJECTED reason=PROFILE_CHANGED  detail='this evaluation run was started under profile PAPER-FORWARD-200K (98db6393b13e); the gate now holds PAPER-FORWARD-200K (3ceb1c2bcf85)
- 10-14 11:30 EURUSD SELL: AI DECISION → RISK REJECTED — reward_risk: 0.91 vs minimum 1.2
- 10-14 11:15 AUDJPY SELL: AI DECISION → RISK REJECTED — cost_to_risk: round-trip cost is 30.3% of the stop (max 25%): spread 0.018 + commission and slippage
- 10-14 11:15 EURCHF SELL: AI DECISION → RISK REJECTED — cost_to_risk: round-trip cost is 27.3% of the stop (max 25%): spread 0.00018 + commission and slippage
- 10-14 11:00 GBPJPY BUY: AI DECISION → RISK APPROVED → RISK REJECTED — hard risk gate: RISK_GATE_REJECTED reason=PROFILE_CHANGED  detail='this evaluation run was started under profile PAPER-FORWARD-200K (98db6393b13e); the gate now holds PAPER-FORWARD-200K (3ceb1c2bcf85)
- 10-14 11:00 EURJPY SELL: AI DECISION → RISK REJECTED — cost_to_risk: round-trip cost is 28.7% of the stop (max 25%): spread 0.015 + commission and slippage

## Latest decisions, NO TRADE included (574 so far)

- 10-14 14:45 USDCAD NO_TRADE: the traders disagree (Trader 1 SELL 75, Trader 2 BUY 65): no trade unless both choose the same side; the debate (nvidia/nemotron-3-super-120b-a12b:free) would have chosen SELL: followed forward in sha
- 10-14 14:30 AUDUSD SELL: SELL AUDUSD on M15: AGREE: Trader 1 (dots-studio/dots-3-note-preview:free) SELL 68: The M15 structure is strongly bearish with lower highs and lower lows, and the price is currently consolidating belo
- 10-14 14:30 USDJPY SELL: SELL USDJPY on M15: AGREE: Trader 1 (dots-studio/dots-3-note-preview:free) SELL 75: The higher timeframe trend on H4 is down, and M15 shows a liquidity sweep of the highs at 158.95 followed by strong 
- 10-14 14:15 GBPUSD SELL: SELL GBPUSD on M15: AGREE: Trader 1 (dots-studio/dots-3-note-preview:free) SELL 78: The M15 structure is clearly bearish with lower highs, lower lows, and recent bearish BOS breaks, while momentum rem
- 10-14 14:15 EURUSD SELL: SELL EURUSD on M15: AGREE: Trader 1 (dots-studio/dots-3-note-preview:free) SELL 85: The EURUSD is in a strong bearish trend across all analyzed timeframes, showing clear lower lows and lower highs wit
- 10-14 14:00 AUDJPY SELL: SELL AUDJPY on M15: AGREE: Trader 1 (nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free) SELL 65: The immediate M15 structure is bearish with a confirmed CHoCH and descending BOS, outweighing the high
- 10-14 14:00 EURCHF NO_TRADE: the traders disagree (Trader 1 SELL 68, Trader 2 BUY 60): no trade unless both choose the same side; the debate (nvidia/nemotron-3-super-120b-a12b:free) would have chosen BUY: followed forward in shad
- 10-14 13:45 GBPJPY BUY: BUY GBPJPY on M15: AGREE: Trader 1 (dots-studio/dots-3-note-preview:free) BUY 75: The H4 trend is bullish, and the M15 price has swept the lower liquidity (EQL 209.466) before holding the strong suppo
- 10-14 13:45 EURJPY SELL: SELL EURJPY on M15: AGREE: Trader 1 (dots-studio/dots-3-note-preview:free) SELL 75: The M15 trend is clearly bearish with a lower low at 176.578, and the current pullback is stalling at strong resista
- 10-14 13:30 EURGBP SELL: SELL EURGBP on M15: AGREE: Trader 1 (dots-studio/dots-3-note-preview:free) SELL 75: The M15 structure is strongly bearish with multiple lower lows and bearish BOS, and the H4 is breaking down. An unte
- 10-14 13:30 NZDUSD BUY: BUY NZDUSD on M15: AGREE: Trader 1 (dots-studio/dots-3-note-preview:free) BUY 65: We buy at the bottom of the H4 range within the designated entry zone, targeting a rebound toward the middle of the ra
- 10-14 13:00 USDCHF NO_TRADE: the traders disagree (Trader 1 BUY 75, Trader 2 SELL 55): no trade unless both choose the same side; the debate (nvidia/nemotron-3-super-120b-a12b:free) would have chosen BUY: followed forward in shad

## Open paper positions

| Symbol | Side | Qty | Entry | Stop | Target | P&L |
|---|---|---|---|---|---|---|

## Closed paper trades (latest 20)

| Closed | Symbol | Side | Net | R | Costs | Exit | Source |
|---|---|---|---|---|---|---|---|
| 10-14 10:59 | AUDJPY | BUY | $348.10 | +0.70 | $53.12 | TIME | DUAL_AI |
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

OpenRouter `READY` · key set · trader 1 `dots-studio/dots-3-note-preview:free` · trader 2 `nvidia/nemotron-3-ultra-550b-a55b:free` · debate `nvidia/nemotron-3-super-120b-a12b:free` · calls today 65/900

AI trades 17 (insufficient) · wins 7 · losses 10 · expectancy -0.162R · profit factor 0.61

Disagreements (not traded; the debate runs in shadow): 32 · the debate's pick if taken: 12 resolved (insufficient), expectancy -0.227R · the side it rejected if taken: 17 resolved (insufficient), expectancy +0.197R

Exits in shadow (the same trades, followed again; measured, never traded): break-even at +1R none resolved yet · held 24 h none resolved yet · stop and target twice as far none resolved yet

Trades taken by session (UTC): ASIA 6 resolved (insufficient), expectancy +0.005R · LONDON 3 resolved (insufficient), expectancy +0.542R · OVERLAP 3 resolved (insufficient), expectancy -0.479R · NEW_YORK 2 resolved (insufficient), expectancy +0.212R · LATE 3 resolved (insufficient), expectancy -1.106R

| Time | Symbol | Trader 1 | Trader 2 | Debate (shadow) | Rule | Final | Risk |
|---|---|---|---|---|---|---|---|
| 10-14 14:45 | USDCAD | SELL 75 | BUY 65 | SELL | DISAGREE | NO_TRADE | - |
| 10-14 14:30 | AUDUSD | SELL 68 | SELL 65 | - | AGREE | SELL | APPROVED |
| 10-14 14:30 | USDJPY | SELL 75 | SELL 70 | - | AGREE | SELL | APPROVED |
| 10-14 14:15 | GBPUSD | SELL 78 | SELL 70 | - | AGREE | SELL | APPROVED |
| 10-14 14:15 | EURUSD | SELL 85 | SELL 58 | - | AGREE | SELL | APPROVED |
| 10-14 14:00 | AUDJPY | SELL 65 | SELL 70 | - | AGREE | SELL | APPROVED |
| 10-14 14:00 | EURCHF | SELL 68 | BUY 60 | BUY | DISAGREE | NO_TRADE | - |
| 10-14 13:45 | GBPJPY | BUY 75 | BUY 68 | - | AGREE | BUY | REJECTED |
| 10-14 13:45 | EURJPY | SELL 75 | SELL 70 | - | AGREE | SELL | APPROVED |
| 10-14 13:30 | EURGBP | SELL 75 | SELL 60 | - | AGREE | SELL | REJECTED |
| 10-14 13:30 | NZDUSD | BUY 65 | BUY 60 | - | AGREE | BUY | REJECTED |
| 10-14 13:00 | USDCHF | BUY 75 | SELL 55 | BUY | DISAGREE | NO_TRADE | - |

The chart Trader 1 read last: `last_chart.png`. (numbers): no free vision model answered, so Trader 1 read the same chart from its numbers.

Full figures: `paper_forward.json`. Rules: `docs/PAPER_FORWARD.md` on main.
