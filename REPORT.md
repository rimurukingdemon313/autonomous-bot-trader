# PAPER FORWARD TEST — NOT REAL MONEY

Updated 2026-10-14 20:40 UTC · mode `PAPER_FORWARD` · profile `PAPER-FORWARD-200K` · shift started 2026-10-14 19:09 UTC · decision system `dual_ai`

Research status (historical, unchanged): **NO EDGE — DO NOT TRADE (historical research; this test measures forward)**. This run measures the system forward; it is not evidence of an edge until it has a sample and the forward-eligibility rules say so.

| Account | Equity | P&L today | Total P&L | Drawdown | Open | Trades | Win rate | Expectancy | Profit factor | Risk | Bot |
|---|---|---|---|---|---|---|---|---|---|---|---|
| $200,000.00 | $198,652.25 | $-1,269.73 | $-1,347.75 | $-1,347.75 | 2 | 17 (insufficient) | 41.2% | -0.162R | 0.61 | ACTIVE | RUNNING |

**WARNING: the hard risk gate refused 14 of the last 20 decisions: PROFILE_CHANGED x14.** A refusal by the gate after the risk engine approved is never routine.

## Last decisions (decision → risk → paper execution)

- 10-14 19:45 USDCAD SELL: AI DECISION → RISK APPROVED → PAPER EXECUTED
- 10-14 19:30 USDJPY SELL: AI DECISION → RISK APPROVED → PAPER EXECUTED
- 10-14 19:15 EURUSD BUY: AI DECISION → RISK REJECTED — cost_to_risk: round-trip cost is 25.0% of the stop (max 25%): spread 8e-05 + commission and slippage
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

## Latest decisions, NO TRADE included (619 so far)

- 10-14 20:30 AUDJPY NO_TRADE: market unavailable for a decision: risk engine: quiet_hours (16:30 New York: no new position from 16:00 to 20:00 New York (the rollover to the Tokyo open: the thinnest liquidity of the day)): the mode
- 10-14 20:30 EURCHF NO_TRADE: market unavailable for a decision: risk engine: quiet_hours (16:30 New York: no new position from 16:00 to 20:00 New York (the rollover to the Tokyo open: the thinnest liquidity of the day)): the mode
- 10-14 20:15 GBPJPY NO_TRADE: market unavailable for a decision: risk engine: quiet_hours (16:15 New York: no new position from 16:00 to 20:00 New York (the rollover to the Tokyo open: the thinnest liquidity of the day)): the mode
- 10-14 20:15 EURJPY NO_TRADE: market unavailable for a decision: risk engine: quiet_hours (16:15 New York: no new position from 16:00 to 20:00 New York (the rollover to the Tokyo open: the thinnest liquidity of the day)): the mode
- 10-14 20:00 EURGBP NO_TRADE: market unavailable for a decision: risk engine: quiet_hours (16:00 New York: no new position from 16:00 to 20:00 New York (the rollover to the Tokyo open: the thinnest liquidity of the day)): the mode
- 10-14 20:00 NZDUSD NO_TRADE: market unavailable for a decision: risk engine: quiet_hours (16:00 New York: no new position from 16:00 to 20:00 New York (the rollover to the Tokyo open: the thinnest liquidity of the day)); currency
- 10-14 19:45 USDCHF NO_TRADE: market unavailable for a decision: risk engine: currency_exposure (2 open positions share a currency, max 2): the model was not consulted
- 10-14 19:45 USDCAD SELL: SELL USDCAD on M15: AGREE: Trader 1 (dots-studio/dots-3-note-preview:free) SELL 75: The USDCAD exhibits a clear bearish structure on both the M15 and H4 charts, characterized by lower highs and lower 
- 10-14 19:30 AUDUSD NO_TRADE: the traders disagree (Trader 1 BUY 75, Trader 2 SELL 70): no trade unless both choose the same side; the debate (nvidia/nemotron-3.5-lightning:free) would have chosen SELL: followed forward in shadow,
- 10-14 19:30 USDJPY SELL: SELL USDJPY on M15: AGREE: Trader 1 (nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free) SELL 78: Strong bearish structure on M15 with price below the untouched supply zone; H4 shows range but no clea
- 10-14 19:15 GBPUSD NO_TRADE: the traders disagree (Trader 1 BUY 70, Trader 2 SELL 75): no trade unless both choose the same side; the debate (dots-studio/dots-3-note-preview:free) would have chosen SELL: followed forward in shado
- 10-14 19:15 EURUSD BUY: BUY EURUSD on M15: AGREE: Trader 1 (nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free) BUY 65: The M15 shows a bullish BOS and CHOCH within the entry zone, while the H4 remains down, giving a higher 

## Open paper positions

| Symbol | Side | Qty | Entry | Stop | Target | P&L |
|---|---|---|---|---|---|---|
| USDCAD | SELL | 4.1 | 1.4242149999999998 | 1.4255 | 1.421 | $155.51 |
| USDJPY | SELL | 1.94 | 158.294 | 158.654 | 157.851 | $-41.55 |

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

OpenRouter `READY` · key set · trader 1 `dots-studio/dots-3-note-preview:free` · trader 2 `nvidia/nemotron-3-ultra-550b-a55b:free` · debate `nvidia/nemotron-3.5-lightning:free` · calls today 21/900

AI trades 17 (insufficient) · wins 7 · losses 10 · expectancy -0.162R · profit factor 0.61

Disagreements (not traded; the debate runs in shadow): 44 · the debate's pick if taken: 27 resolved (insufficient), expectancy +0.102R · the side it rejected if taken: 32 resolved (adequate), expectancy -0.304R

Exits in shadow (the same trades, followed again; measured, never traded): break-even at +1R none resolved yet · held 24 h none resolved yet · stop and target twice as far none resolved yet

Trades taken by session (UTC): ASIA 6 resolved (insufficient), expectancy +0.005R · LONDON 3 resolved (insufficient), expectancy +0.542R · OVERLAP 3 resolved (insufficient), expectancy -0.479R · NEW_YORK 2 resolved (insufficient), expectancy +0.212R · LATE 3 resolved (insufficient), expectancy -1.106R

| Time | Symbol | Trader 1 | Trader 2 | Debate (shadow) | Rule | Final | Risk |
|---|---|---|---|---|---|---|---|
| 10-14 20:30 | AUDJPY | -  | -  | - | MARKET_UNAVAILABLE | NO_TRADE | - |
| 10-14 20:30 | EURCHF | -  | -  | - | MARKET_UNAVAILABLE | NO_TRADE | - |
| 10-14 20:15 | GBPJPY | -  | -  | - | MARKET_UNAVAILABLE | NO_TRADE | - |
| 10-14 20:15 | EURJPY | -  | -  | - | MARKET_UNAVAILABLE | NO_TRADE | - |
| 10-14 20:00 | EURGBP | -  | -  | - | MARKET_UNAVAILABLE | NO_TRADE | - |
| 10-14 20:00 | NZDUSD | -  | -  | - | MARKET_UNAVAILABLE | NO_TRADE | - |
| 10-14 19:45 | USDCHF | -  | -  | - | MARKET_UNAVAILABLE | NO_TRADE | - |
| 10-14 19:45 | USDCAD | SELL 75 | SELL 70 | - | AGREE | SELL | APPROVED |
| 10-14 19:30 | AUDUSD | BUY 75 | SELL 70 | SELL | DISAGREE | NO_TRADE | - |
| 10-14 19:30 | USDJPY | SELL 78 | SELL 75 | - | AGREE | SELL | APPROVED |
| 10-14 19:15 | GBPUSD | BUY 70 | SELL 75 | SELL | DISAGREE | NO_TRADE | - |
| 10-14 19:15 | EURUSD | BUY 65 | BUY 60 | - | AGREE | BUY | REJECTED |

The chart Trader 1 read last: `last_chart.png`. (numbers): no free vision model answered, so Trader 1 read the same chart from its numbers.

Full figures: `paper_forward.json`. Rules: `docs/PAPER_FORWARD.md` on main.
