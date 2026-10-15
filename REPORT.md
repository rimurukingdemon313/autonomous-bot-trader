# PAPER FORWARD TEST — NOT REAL MONEY

Updated 2026-10-15 08:21 UTC · mode `PAPER_FORWARD` · profile `PAPER-FORWARD-200K` · shift started 2026-10-15 06:21 UTC · decision system `dual_ai`

Research status (historical, unchanged): **NO EDGE — DO NOT TRADE (historical research; this test measures forward)**. This run measures the system forward; it is not evidence of an edge until it has a sample and the forward-eligibility rules say so.

| Account | Equity | P&L today | Total P&L | Drawdown | Open | Trades | Win rate | Expectancy | Profit factor | Risk | Bot |
|---|---|---|---|---|---|---|---|---|---|---|---|
| $200,000.00 | $199,249.55 | $615.61 | $-750.45 | $-750.45 | 2 | 26 (insufficient) | 42.3% | -0.070R | 0.86 | ACTIVE | RUNNING |

**WARNING: the hard risk gate refused 3 of the last 20 decisions: PROFILE_CHANGED x2, MARKET_DATA_STALE x1.** A refusal by the gate after the risk engine approved is never routine. The latest at 10-15 06:15 UTC; 1 decision(s) since, none refused by the gate.

## Last decisions (decision → risk → paper execution)

- 10-15 06:45 USDJPY BUY: AI DECISION → RISK APPROVED → PAPER EXECUTED
- 10-15 06:15 EURGBP SELL: AI DECISION → RISK APPROVED → RISK REJECTED — hard risk gate: RISK_GATE_REJECTED reason=MARKET_DATA_STALE equity_conservative=199578.57 daily_pnl=944.63 daily_limit=-10000.00 total_pnl=-421.43 total_limit=-20000.00 open_risk=910.95 detail='quote 
- 10-15 04:45 NZDUSD SELL: AI DECISION → RISK APPROVED → PAPER EXECUTED
- 10-15 04:30 USDCHF SELL: AI DECISION → RISK REJECTED — reward_risk: 1.13 vs minimum 1.2
- 10-15 03:30 EURJPY BUY: AI DECISION → RISK APPROVED → PAPER EXECUTED
- 10-15 03:15 EURGBP SELL: AI DECISION → RISK REJECTED — reward_risk: 1.08 vs minimum 1.2
- 10-15 03:00 USDCHF SELL: AI DECISION → RISK APPROVED → PAPER EXECUTED
- 10-15 03:00 USDCAD SELL: AI DECISION → RISK APPROVED → PAPER EXECUTED
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

## Latest decisions, NO TRADE included (709 so far)

- 10-15 08:15 USDJPY NO_TRADE: the traders disagree (Trader 1 BUY 68, Trader 2 SELL 70): no trade unless both choose the same side; the debate (dots-studio/dots-3-note-preview:free) would have chosen SELL: followed forward in shado
- 10-15 08:00 GBPUSD NO_TRADE: market unavailable for a decision: risk engine: open_positions (3 open, max 3); currency_exposure (2 open positions share a currency, max 2): the model was not consulted
- 10-15 08:00 EURUSD NO_TRADE: market unavailable for a decision: risk engine: open_positions (3 open, max 3); currency_exposure (2 open positions share a currency, max 2): the model was not consulted
- 10-15 07:45 AUDJPY NO_TRADE: market unavailable for a decision: risk engine: open_positions (3 open, max 3); currency_exposure (2 open positions share a currency, max 2): the model was not consulted
- 10-15 07:45 EURCHF NO_TRADE: market unavailable for a decision: risk engine: open_positions (3 open, max 3): the model was not consulted
- 10-15 07:30 GBPJPY NO_TRADE: market unavailable for a decision: risk engine: open_positions (3 open, max 3); currency_exposure (2 open positions share a currency, max 2): the model was not consulted
- 10-15 07:30 EURJPY NO_TRADE: market unavailable for a decision: blocked before consulting the model: EXPOSURE: a EURJPY position is already open
- 10-15 07:15 EURGBP NO_TRADE: market unavailable for a decision: risk engine: open_positions (3 open, max 3): the model was not consulted
- 10-15 07:15 NZDUSD NO_TRADE: market unavailable for a decision: blocked before consulting the model: EXPOSURE: a NZDUSD position is already open
- 10-15 07:00 USDCHF NO_TRADE: market unavailable for a decision: risk engine: open_positions (3 open, max 3); currency_exposure (2 open positions share a currency, max 2): the model was not consulted
- 10-15 07:00 USDCAD NO_TRADE: market unavailable for a decision: risk engine: open_positions (3 open, max 3); currency_exposure (2 open positions share a currency, max 2): the model was not consulted
- 10-15 06:45 AUDUSD NO_TRADE: market unavailable for a decision: risk engine: open_positions (3 open, max 3); currency_exposure (2 open positions share a currency, max 2): the model was not consulted

## Open paper positions

| Symbol | Side | Qty | Entry | Stop | Target | P&L |
|---|---|---|---|---|---|---|
| NZDUSD | SELL | 1.68 | 0.561915 | 0.5631 | 0.5605 | $40.32 |
| EURJPY | BUY | 1.86 | 177.0055 | 176.635 | 177.562 | $-3.52 |

## Closed paper trades (latest 20)

| Closed | Symbol | Side | Net | R | Costs | Exit | Source |
|---|---|---|---|---|---|---|---|
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
| 10-13 11:11 | EURUSD | SELL | $-422.48 | -0.85 | $80.75 | STOP | DUAL_AI |
| 10-13 10:48 | USDCAD | SELL | $73.61 | +0.30 | $46.17 | TIME | DUAL_AI |

## Dual AI desk (two free OpenRouter traders; a trade only when they agree)

OpenRouter `READY` · key set · trader 1 `nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free` · trader 2 `nvidia/nemotron-3-ultra-550b-a55b:free` · debate `dots-studio/dots-3-note-preview:free` · calls today 13/900

AI trades 26 (insufficient) · wins 11 · losses 15 · expectancy -0.070R · profit factor 0.86

Disagreements (not traded; the debate runs in shadow): 52 · the debate's pick if taken: 45 resolved (adequate), expectancy -0.121R · the side it rejected if taken: 50 resolved (adequate), expectancy -0.151R

Exits in shadow (the same trades, followed again; measured, never traded): break-even at +1R +1.970R vs +1.970R as taken (2, insufficient) · held 24 h none resolved yet · stop and target twice as far none resolved yet

Trades taken by session (UTC): ASIA 6 resolved (insufficient), expectancy +0.005R · LONDON 3 resolved (insufficient), expectancy +0.542R · OVERLAP 3 resolved (insufficient), expectancy -0.479R · NEW_YORK 4 resolved (insufficient), expectancy +1.091R · LATE 3 resolved (insufficient), expectancy -1.106R

| Time | Symbol | Trader 1 | Trader 2 | Debate (shadow) | Rule | Final | Risk |
|---|---|---|---|---|---|---|---|
| 10-15 08:15 | USDJPY | BUY 68 | SELL 70 | SELL | DISAGREE | NO_TRADE | - |
| 10-15 08:00 | GBPUSD | -  | -  | - | MARKET_UNAVAILABLE | NO_TRADE | - |
| 10-15 08:00 | EURUSD | -  | -  | - | MARKET_UNAVAILABLE | NO_TRADE | - |
| 10-15 07:45 | AUDJPY | -  | -  | - | MARKET_UNAVAILABLE | NO_TRADE | - |
| 10-15 07:45 | EURCHF | -  | -  | - | MARKET_UNAVAILABLE | NO_TRADE | - |
| 10-15 07:30 | GBPJPY | -  | -  | - | MARKET_UNAVAILABLE | NO_TRADE | - |
| 10-15 07:30 | EURJPY | -  | -  | - | MARKET_UNAVAILABLE | NO_TRADE | - |
| 10-15 07:15 | EURGBP | -  | -  | - | MARKET_UNAVAILABLE | NO_TRADE | - |
| 10-15 07:15 | NZDUSD | -  | -  | - | MARKET_UNAVAILABLE | NO_TRADE | - |
| 10-15 07:00 | USDCHF | -  | -  | - | MARKET_UNAVAILABLE | NO_TRADE | - |
| 10-15 07:00 | USDCAD | -  | -  | - | MARKET_UNAVAILABLE | NO_TRADE | - |
| 10-15 06:45 | AUDUSD | -  | -  | - | MARKET_UNAVAILABLE | NO_TRADE | - |

The chart Trader 1 read last: `last_chart.png`. (numbers): no free vision model answered, so Trader 1 read the same chart from its numbers.

Full figures: `paper_forward.json`. Rules: `docs/PAPER_FORWARD.md` on main.
