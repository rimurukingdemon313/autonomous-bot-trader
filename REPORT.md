# PAPER FORWARD TEST — NOT REAL MONEY

Updated 2026-10-15 03:00 UTC · mode `PAPER_FORWARD` · profile `PAPER-FORWARD-200K` · shift started 2026-10-15 00:45 UTC · decision system `dual_ai`

Research status (historical, unchanged): **NO EDGE — DO NOT TRADE (historical research; this test measures forward)**. This run measures the system forward; it is not evidence of an edge until it has a sample and the forward-eligibility rules say so.

| Account | Equity | P&L today | Total P&L | Drawdown | Open | Trades | Win rate | Expectancy | Profit factor | Risk | Bot |
|---|---|---|---|---|---|---|---|---|---|---|---|
| $200,000.00 | $200,226.27 | $1,592.33 | $226.27 | $0.00 | 0 | 23 (insufficient) | 47.8% | +0.028R | 1.05 | ACTIVE | RUNNING |

**WARNING: the hard risk gate refused 7 of the last 20 decisions: PROFILE_CHANGED x7.** A refusal by the gate after the risk engine approved is never routine.

## Last decisions (decision → risk → paper execution)

- 10-15 02:30 EURUSD SELL: AI DECISION → RISK APPROVED → PAPER EXECUTED
- 10-15 02:15 EURCHF SELL: AI DECISION → RISK REJECTED — cost_to_risk: round-trip cost is 27.3% of the stop (max 25%): spread 0.00018 + commission and slippage
- 10-15 02:00 GBPJPY SELL: AI DECISION → RISK APPROVED → PAPER EXECUTED
- 10-15 01:30 USDCAD SELL: AI DECISION → RISK REJECTED — cost_to_risk: round-trip cost is 27.4% of the stop (max 25%): spread 0.00015 + commission and slippage
- 10-15 00:30 NZDUSD BUY: AI DECISION → RISK APPROVED → PAPER EXECUTED
- 10-15 00:15 USDCHF SELL: AI DECISION → RISK APPROVED → PAPER EXECUTED
- 10-15 00:15 USDCAD SELL: AI DECISION → RISK REJECTED — reward_risk: 1.12 vs minimum 1.2
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

## Latest decisions, NO TRADE included (666 so far)

- 10-15 02:45 AUDUSD NO_TRADE: market unavailable for a decision: risk engine: open_positions (3 open, max 3); currency_exposure (2 open positions share a currency, max 2): the model was not consulted
- 10-15 02:45 USDJPY NO_TRADE: market unavailable for a decision: risk engine: open_positions (3 open, max 3); currency_exposure (2 open positions share a currency, max 2): the model was not consulted
- 10-15 02:30 GBPUSD NO_TRADE: market unavailable for a decision: risk engine: open_positions (3 open, max 3); currency_exposure (2 open positions share a currency, max 2): the model was not consulted
- 10-15 02:30 EURUSD SELL: SELL EURUSD on M15: AGREE: Trader 1 (dots-studio/dots-3-note-preview:free) SELL 68: The H4 trend is down (LH+LL) and price is testing the H4 resistance zone (1.12174-1.12265), while bearish liquidity 
- 10-15 02:15 AUDJPY NO_TRADE: the traders disagree (Trader 1 SELL 75, Trader 2 BUY 60): no trade unless both choose the same side; the debate (nvidia/nemotron-3.5-lightning:free) would have chosen BUY: followed forward in shadow, 
- 10-15 02:15 EURCHF SELL: SELL EURCHF on M15: AGREE: Trader 1 (dots-studio/dots-3-note-preview:free) SELL 75: The M15 chart shows a clear bearish structure with lower lows and multiple bearish BOS, while the H4 timeframe shows
- 10-15 02:00 GBPJPY SELL: SELL GBPJPY on M15: AGREE: Trader 1 (dots-studio/dots-3-note-preview:free) SELL 75: The M15 chart shows a bearish structure with a lower high and a tested supply order block, while H4 shows a bearish 
- 10-15 02:00 EURJPY NO_TRADE: the traders disagree (Trader 1 BUY 72, Trader 2 SELL 65): no trade unless both choose the same side; the debate (nvidia/nemotron-3.5-lightning:free) would have chosen BUY: followed forward in shadow, 
- 10-15 01:45 EURGBP NO_TRADE: the traders disagree (Trader 1 BUY 65, Trader 2 SELL 55): no trade unless both choose the same side; the debate (nvidia/nemotron-3.5-lightning:free) would have chosen BUY: followed forward in shadow, 
- 10-15 01:45 NZDUSD NO_TRADE: market unavailable for a decision: blocked before consulting the model: EXPOSURE: a NZDUSD position is already open
- 10-15 01:30 USDCHF NO_TRADE: the traders disagree (Trader 1 BUY 65, Trader 2 SELL 70): no trade unless both choose the same side; the debate (nvidia/nemotron-3.5-lightning:free) would have chosen SELL: followed forward in shadow,
- 10-15 01:30 USDCAD SELL: SELL USDCAD on M15: AGREE: Trader 1 (dots-studio/dots-3-note-preview:free) SELL 65: The M15 structure is bearish with a recent BOS down and lower highs/lows, while the H4 shows bearish breaks. Selling

## Open paper positions

| Symbol | Side | Qty | Entry | Stop | Target | P&L |
|---|---|---|---|---|---|---|

## Closed paper trades (latest 20)

| Closed | Symbol | Side | Net | R | Costs | Exit | Source |
|---|---|---|---|---|---|---|---|
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
| 10-13 11:11 | EURUSD | SELL | $-422.48 | -0.85 | $80.75 | STOP | DUAL_AI |
| 10-13 10:48 | USDCAD | SELL | $73.61 | +0.30 | $46.17 | TIME | DUAL_AI |
| 10-13 06:48 | USDJPY | SELL | $228.86 | +0.92 | $42.21 | TARGET | DUAL_AI |
| 10-13 05:42 | AUDUSD | SELL | $-214.73 | -0.86 | $47.12 | STOP | DUAL_AI |
| 10-13 01:03 | EURUSD | SELL | $-431.70 | -0.86 | $87.38 | STOP | DUAL_AI |

## Dual AI desk (two free OpenRouter traders; a trade only when they agree)

OpenRouter `READY` · key set · trader 1 `dots-studio/dots-3-note-preview:free` · trader 2 `nvidia/nemotron-3-ultra-550b-a55b:free` · debate `nvidia/nemotron-3.5-lightning:free` · calls today 38/900

AI trades 23 (insufficient) · wins 11 · losses 12 · expectancy +0.028R · profit factor 1.05

Disagreements (not traded; the debate runs in shadow): 51 · the debate's pick if taken: 42 resolved (adequate), expectancy -0.010R · the side it rejected if taken: 47 resolved (adequate), expectancy -0.172R

Exits in shadow (the same trades, followed again; measured, never traded): break-even at +1R none resolved yet · held 24 h none resolved yet · stop and target twice as far none resolved yet

Trades taken by session (UTC): ASIA 6 resolved (insufficient), expectancy +0.005R · LONDON 3 resolved (insufficient), expectancy +0.542R · OVERLAP 3 resolved (insufficient), expectancy -0.479R · NEW_YORK 2 resolved (insufficient), expectancy +0.212R · LATE 3 resolved (insufficient), expectancy -1.106R

| Time | Symbol | Trader 1 | Trader 2 | Debate (shadow) | Rule | Final | Risk |
|---|---|---|---|---|---|---|---|
| 10-15 02:45 | AUDUSD | -  | -  | - | MARKET_UNAVAILABLE | NO_TRADE | - |
| 10-15 02:45 | USDJPY | -  | -  | - | MARKET_UNAVAILABLE | NO_TRADE | - |
| 10-15 02:30 | GBPUSD | -  | -  | - | MARKET_UNAVAILABLE | NO_TRADE | - |
| 10-15 02:30 | EURUSD | SELL 68 | SELL 72 | - | AGREE | SELL | APPROVED |
| 10-15 02:15 | AUDJPY | SELL 75 | BUY 60 | BUY | DISAGREE | NO_TRADE | - |
| 10-15 02:15 | EURCHF | SELL 75 | SELL 70 | - | AGREE | SELL | REJECTED |
| 10-15 02:00 | GBPJPY | SELL 75 | SELL 65 | - | AGREE | SELL | APPROVED |
| 10-15 02:00 | EURJPY | BUY 72 | SELL 65 | BUY | DISAGREE | NO_TRADE | - |
| 10-15 01:45 | EURGBP | BUY 65 | SELL 55 | BUY | DISAGREE | NO_TRADE | - |
| 10-15 01:45 | NZDUSD | -  | -  | - | MARKET_UNAVAILABLE | NO_TRADE | - |
| 10-15 01:30 | USDCHF | BUY 65 | SELL 70 | SELL | DISAGREE | NO_TRADE | - |
| 10-15 01:30 | USDCAD | SELL 65 | SELL 65 | - | AGREE | SELL | REJECTED |

The chart Trader 1 read last: `last_chart.png`. (numbers): no free vision model answered, so Trader 1 read the same chart from its numbers.

Full figures: `paper_forward.json`. Rules: `docs/PAPER_FORWARD.md` on main.
