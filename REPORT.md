# PAPER FORWARD TEST — NOT REAL MONEY

Updated 2026-10-14 19:09 UTC · mode `PAPER_FORWARD` · profile `PAPER-FORWARD-200K` · shift started 2026-10-14 19:09 UTC · decision system `dual_ai`

Research status (historical, unchanged): **NO EDGE — DO NOT TRADE (historical research; this test measures forward)**. This run measures the system forward; it is not evidence of an edge until it has a sample and the forward-eligibility rules say so.

| Account | Equity | P&L today | Total P&L | Drawdown | Open | Trades | Win rate | Expectancy | Profit factor | Risk | Bot |
|---|---|---|---|---|---|---|---|---|---|---|---|
| $200,000.00 | $198,538.30 | $-1,383.69 | $-1,461.70 | $-1,461.70 | 0 | 17 (insufficient) | 41.2% | -0.162R | 0.61 | ACTIVE | RUNNING |

**WARNING: the hard risk gate refused 16 of the last 20 decisions: PROFILE_CHANGED x16.** A refusal by the gate after the risk engine approved is never routine.

## Last decisions (decision → risk → paper execution)

- 10-14 19:00 GBPJPY SELL: AI DECISION → RISK APPROVED → RISK REJECTED — hard risk gate: RISK_GATE_REJECTED reason=PROFILE_CHANGED  detail='this evaluation run was started under profile PAPER-FORWARD-200K (98db6393b13e); the gate now holds PAPER-FORWARD-200K (3ceb1c2bcf85)
- 10-14 19:00 EURJPY BUY: AI DECISION → RISK APPROVED → RISK REJECTED — hard risk gate: RISK_GATE_REJECTED reason=PROFILE_CHANGED  detail='this evaluation run was started under profile PAPER-FORWARD-200K (98db6393b13e); the gate now holds PAPER-FORWARD-200K (3ceb1c2bcf85)
- 10-14 18:45 EURGBP BUY: AI DECISION → RISK REJECTED — cost_to_risk: round-trip cost is 28.4% of the stop (max 25%): spread 0.00012 + commission and slippage
- 10-14 18:45 NZDUSD SELL: AI DECISION → RISK APPROVED → RISK REJECTED — hard risk gate: RISK_GATE_REJECTED reason=PROFILE_CHANGED  detail='this evaluation run was started under profile PAPER-FORWARD-200K (98db6393b13e); the gate now holds PAPER-FORWARD-200K (3ceb1c2bcf85)
- 10-14 18:30 USDCHF BUY: AI DECISION → RISK APPROVED → RISK REJECTED — hard risk gate: RISK_GATE_REJECTED reason=PROFILE_CHANGED  detail='this evaluation run was started under profile PAPER-FORWARD-200K (98db6393b13e); the gate now holds PAPER-FORWARD-200K (3ceb1c2bcf85)
- 10-14 18:30 USDCAD SELL: AI DECISION → RISK APPROVED → RISK REJECTED — hard risk gate: RISK_GATE_REJECTED reason=PROFILE_CHANGED  detail='this evaluation run was started under profile PAPER-FORWARD-200K (98db6393b13e); the gate now holds PAPER-FORWARD-200K (3ceb1c2bcf85)
- 10-14 18:15 USDJPY SELL: AI DECISION → RISK REJECTED — reward_risk: 1.01 vs minimum 1.2
- 10-14 18:00 EURUSD SELL: AI DECISION → RISK APPROVED → RISK REJECTED — hard risk gate: RISK_GATE_REJECTED reason=PROFILE_CHANGED  detail='this evaluation run was started under profile PAPER-FORWARD-200K (98db6393b13e); the gate now holds PAPER-FORWARD-200K (3ceb1c2bcf85)
- 10-14 17:45 USDJPY SELL: AI DECISION → RISK REJECTED — spread: spread is 28.6% of the stop (max 25%); cost_to_risk: round-trip cost is 54.3% of the stop (max 25%): spread 0.01 + commission and slippage
- 10-14 17:30 GBPUSD SELL: AI DECISION → RISK APPROVED → RISK REJECTED — hard risk gate: RISK_GATE_REJECTED reason=PROFILE_CHANGED  detail='this evaluation run was started under profile PAPER-FORWARD-200K (98db6393b13e); the gate now holds PAPER-FORWARD-200K (3ceb1c2bcf85)
- 10-14 17:30 EURUSD SELL: AI DECISION → RISK APPROVED → RISK REJECTED — hard risk gate: RISK_GATE_REJECTED reason=PROFILE_CHANGED  detail='this evaluation run was started under profile PAPER-FORWARD-200K (98db6393b13e); the gate now holds PAPER-FORWARD-200K (3ceb1c2bcf85)
- 10-14 17:00 AUDJPY SELL: AI DECISION → RISK APPROVED → RISK REJECTED — hard risk gate: RISK_GATE_REJECTED reason=PROFILE_CHANGED  detail='this evaluation run was started under profile PAPER-FORWARD-200K (98db6393b13e); the gate now holds PAPER-FORWARD-200K (3ceb1c2bcf85)
- 10-14 16:45 EURJPY SELL: AI DECISION → RISK APPROVED → RISK REJECTED — hard risk gate: RISK_GATE_REJECTED reason=PROFILE_CHANGED  detail='this evaluation run was started under profile PAPER-FORWARD-200K (98db6393b13e); the gate now holds PAPER-FORWARD-200K (3ceb1c2bcf85)
- 10-14 16:30 EURGBP SELL: AI DECISION → RISK APPROVED → RISK REJECTED — hard risk gate: RISK_GATE_REJECTED reason=PROFILE_CHANGED  detail='this evaluation run was started under profile PAPER-FORWARD-200K (98db6393b13e); the gate now holds PAPER-FORWARD-200K (3ceb1c2bcf85)
- 10-14 16:30 NZDUSD SELL: AI DECISION → RISK APPROVED → RISK REJECTED — hard risk gate: RISK_GATE_REJECTED reason=PROFILE_CHANGED  detail='this evaluation run was started under profile PAPER-FORWARD-200K (98db6393b13e); the gate now holds PAPER-FORWARD-200K (3ceb1c2bcf85)
- 10-14 16:15 USDCHF BUY: AI DECISION → RISK APPROVED → RISK REJECTED — hard risk gate: RISK_GATE_REJECTED reason=PROFILE_CHANGED  detail='this evaluation run was started under profile PAPER-FORWARD-200K (98db6393b13e); the gate now holds PAPER-FORWARD-200K (3ceb1c2bcf85)
- 10-14 15:45 GBPUSD SELL: AI DECISION → RISK APPROVED → RISK REJECTED — hard risk gate: RISK_GATE_REJECTED reason=PROFILE_CHANGED  detail='this evaluation run was started under profile PAPER-FORWARD-200K (98db6393b13e); the gate now holds PAPER-FORWARD-200K (3ceb1c2bcf85)
- 10-14 15:45 EURUSD SELL: AI DECISION → RISK REJECTED — cost_to_risk: round-trip cost is 43.6% of the stop (max 25%): spread 8e-05 + commission and slippage
- 10-14 15:30 EURCHF SELL: AI DECISION → RISK APPROVED → RISK REJECTED — hard risk gate: RISK_GATE_REJECTED reason=PROFILE_CHANGED  detail='this evaluation run was started under profile PAPER-FORWARD-200K (98db6393b13e); the gate now holds PAPER-FORWARD-200K (3ceb1c2bcf85)
- 10-14 15:15 GBPJPY SELL: AI DECISION → RISK APPROVED → RISK REJECTED — hard risk gate: RISK_GATE_REJECTED reason=PROFILE_CHANGED  detail='this evaluation run was started under profile PAPER-FORWARD-200K (98db6393b13e); the gate now holds PAPER-FORWARD-200K (3ceb1c2bcf85)

## Latest decisions, NO TRADE included (607 so far)

- 10-14 19:00 GBPJPY SELL: SELL GBPJPY on M15: AGREE: Trader 1 (dots-studio/dots-3-note-preview:free) SELL 68: The M15 structure is heavily bearish with consecutive lower lows, bearish BOS, and open bearish FVGs, while the H4 c
- 10-14 19:00 EURJPY BUY: BUY EURJPY on M15: AGREE: Trader 1 (dots-studio/dots-3-note-preview:free) BUY 72: The price is trading near the bottom of a ranging market and has just executed a bullish liquidity sweep of the 176.38
- 10-14 18:45 EURGBP BUY: BUY EURGBP on M15: AGREE: Trader 1 (dots-studio/dots-3-note-preview:free) BUY 72: The M15 chart displays a strong bullish structure break sequence (CHOCH and multiple BOSs) with price holding above th
- 10-14 18:45 NZDUSD SELL: SELL NZDUSD on M15: AGREE: Trader 1 (dots-studio/dots-3-note-preview:free) SELL 72: The M15 chart shows a lower high at 0.5591 accompanied by a high sweep, while the H4 timeframe shows a bearish CHOCH
- 10-14 18:30 USDCHF BUY: BUY USDCHF on M15: AGREE: Trader 1 (dots-studio/dots-3-note-preview:free) BUY 75: The H4 trend is UP, and the M15 has pulled back to a major S/R cluster (0.8334-0.8348) inside the mitigated bullish FV
- 10-14 18:30 USDCAD SELL: SELL USDCAD on M15: AGREE: Trader 1 (dots-studio/dots-3-note-preview:free) SELL 75: The H4 trend is down, and the M15 has broken structure bearishly, currently pulling back to test strong resistance a
- 10-14 18:15 AUDUSD NO_TRADE: the traders disagree (Trader 1 SELL 75, Trader 2 BUY 58): no trade unless both choose the same side; the debate (nvidia/nemotron-3.5-lightning:free) would have chosen BUY: followed forward in shadow, 
- 10-14 18:15 USDJPY SELL: SELL USDJPY on M15: AGREE: Trader 1 (dots-studio/dots-3-note-preview:free) SELL 68: The M15 structure is clearly bearish with a sequence of lower highs and lower lows, confirmed by a recent bearish BO
- 10-14 18:00 GBPUSD NO_TRADE: the traders disagree (Trader 1 BUY 70, Trader 2 SELL 65): no trade unless both choose the same side; the debate (nvidia/nemotron-3.5-lightning:free) would have chosen SELL: followed forward in shadow,
- 10-14 18:00 EURUSD SELL: SELL EURUSD on M15: AGREE: Trader 1 (dots-studio/dots-3-note-preview:free) SELL 72: The dominant trend is bearish on both M15 and H4, and the current price is near the top of the pullback zone, offeri
- 10-14 17:45 AUDUSD NO_TRADE: the traders disagree (Trader 1 SELL 70, Trader 2 BUY 62): no trade unless both choose the same side; the debate (nvidia/nemotron-3.5-lightning:free) would have chosen SELL: followed forward in shadow,
- 10-14 17:45 USDJPY SELL: SELL USDJPY on M15: AGREE: Trader 1 (dots-studio/dots-3-note-preview:free) SELL 70: The M15 trend is clearly down with a sequence of lower highs and lower lows, and the recent bearish BOS at 158.654 c

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

OpenRouter `CATALOG_NOT_READ_YET` · key set · trader 1 `None` · trader 2 `None` · debate `None` · calls today 0/900

AI trades 17 (insufficient) · wins 7 · losses 10 · expectancy -0.162R · profit factor 0.61

Disagreements (not traded; the debate runs in shadow): 42 · the debate's pick if taken: 24 resolved (insufficient), expectancy -0.094R · the side it rejected if taken: 29 resolved (insufficient), expectancy +0.041R

Exits in shadow (the same trades, followed again; measured, never traded): break-even at +1R none resolved yet · held 24 h none resolved yet · stop and target twice as far none resolved yet

Trades taken by session (UTC): ASIA 6 resolved (insufficient), expectancy +0.005R · LONDON 3 resolved (insufficient), expectancy +0.542R · OVERLAP 3 resolved (insufficient), expectancy -0.479R · NEW_YORK 2 resolved (insufficient), expectancy +0.212R · LATE 3 resolved (insufficient), expectancy -1.106R

| Time | Symbol | Trader 1 | Trader 2 | Debate (shadow) | Rule | Final | Risk |
|---|---|---|---|---|---|---|---|
| 10-14 19:00 | GBPJPY | SELL 68 | SELL 68 | - | AGREE | SELL | APPROVED |
| 10-14 19:00 | EURJPY | BUY 72 | BUY 60 | - | AGREE | BUY | APPROVED |
| 10-14 18:45 | EURGBP | BUY 72 | BUY 75 | - | AGREE | BUY | REJECTED |
| 10-14 18:45 | NZDUSD | SELL 72 | SELL 70 | - | AGREE | SELL | APPROVED |
| 10-14 18:30 | USDCHF | BUY 75 | BUY 70 | - | AGREE | BUY | APPROVED |
| 10-14 18:30 | USDCAD | SELL 75 | SELL 68 | - | AGREE | SELL | APPROVED |
| 10-14 18:15 | AUDUSD | SELL 75 | BUY 58 | BUY | DISAGREE | NO_TRADE | - |
| 10-14 18:15 | USDJPY | SELL 68 | SELL 72 | - | AGREE | SELL | REJECTED |
| 10-14 18:00 | GBPUSD | BUY 70 | SELL 65 | SELL | DISAGREE | NO_TRADE | - |
| 10-14 18:00 | EURUSD | SELL 72 | SELL 75 | - | AGREE | SELL | APPROVED |
| 10-14 17:45 | AUDUSD | SELL 70 | BUY 62 | SELL | DISAGREE | NO_TRADE | - |
| 10-14 17:45 | USDJPY | SELL 70 | SELL 65 | - | AGREE | SELL | REJECTED |

The chart Trader 1 read last: `last_chart.png`. (numbers): no free vision model answered, so Trader 1 read the same chart from its numbers.

Full figures: `paper_forward.json`. Rules: `docs/PAPER_FORWARD.md` on main.
