# PAPER FORWARD TEST — NOT REAL MONEY

Updated 2026-10-15 17:31 UTC · mode `PAPER_FORWARD` · profile `PAPER-FORWARD-200K` · shift started 2026-10-15 11:56 UTC · decision system `dual_ai`

Research status (historical, unchanged): **NO EDGE — DO NOT TRADE (historical research; this test measures forward)**. This run measures the system forward; it is not evidence of an edge until it has a sample and the forward-eligibility rules say so.

| Account | Equity | P&L today | Total P&L | Drawdown | Open | Trades | Win rate | Expectancy | Profit factor | Risk | Bot |
|---|---|---|---|---|---|---|---|---|---|---|---|
| $200,000.00 | $199,030.78 | $396.84 | $-969.22 | $-969.22 | 3 | 33 (adequate) | 45.5% | -0.042R | 0.86 | ACTIVE | RUNNING |

**WARNING: the hard risk gate refused 1 of the last 20 decisions: MARKET_DATA_STALE x1.** A refusal by the gate after the risk engine approved is never routine. The latest at 10-15 12:15 UTC; 13 decision(s) since, none refused by the gate.

## Last decisions (decision → risk → paper execution)

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
- 10-15 12:00 GBPUSD BUY: AI DECISION → RISK REJECTED — cost_to_risk: round-trip cost is 31.8% of the stop (max 25%): spread 0.00012 + commission and slippage
- 10-15 12:00 EURUSD SELL: AI DECISION → RISK REJECTED — cost_to_risk: round-trip cost is 25.4% of the stop (max 25%): spread 8e-05 + commission and slippage
- 10-15 08:45 EURGBP SELL: AI DECISION → RISK APPROVED → PAPER EXECUTED
- 10-15 08:30 USDCHF SELL: AI DECISION → RISK REJECTED — cost_to_risk: round-trip cost is 31.0% of the stop (max 25%): spread 0.00015 + commission and slippage
- 10-15 08:30 USDCAD BUY: AI DECISION → RISK REJECTED — reward_risk: 1.03 vs minimum 1.2

## Latest decisions, NO TRADE included (784 so far)

- 10-15 17:30 GBPJPY NO_TRADE: market unavailable for a decision: risk engine: open_positions (3 open, max 3); currency_exposure (2 open positions share a currency, max 2): the model was not consulted
- 10-15 17:30 EURJPY NO_TRADE: market unavailable for a decision: risk engine: open_positions (3 open, max 3); currency_exposure (2 open positions share a currency, max 2): the model was not consulted
- 10-15 17:15 EURGBP NO_TRADE: market unavailable for a decision: risk engine: open_positions (3 open, max 3): the model was not consulted
- 10-15 17:15 NZDUSD NO_TRADE: market unavailable for a decision: risk engine: open_positions (3 open, max 3); currency_exposure (2 open positions share a currency, max 2): the model was not consulted
- 10-15 17:00 USDCHF NO_TRADE: market unavailable for a decision: risk engine: open_positions (3 open, max 3); currency_exposure (2 open positions share a currency, max 2): the model was not consulted
- 10-15 17:00 USDCAD SELL: SELL USDCAD on M15: AGREE: Trader 1 (nvidia/nemotron-3.5-super-vl:free) SELL 60: Price sits at the base of a tested supply order block (1.4198–1.42152) after a bearish sweep of highs at 1.42039 and th
- 10-15 16:45 AUDUSD NO_TRADE: market unavailable for a decision: risk engine: open_positions (3 open, max 3): the model was not consulted
- 10-15 16:45 USDJPY SELL: SELL USDJPY on M15: AGREE: Trader 1 (nvidia/nemotron-3.5-super-vl:free) SELL 62: Selling the range-top rejection after the demand OB broke and highs were swept, with the H4 bearish CHoCH just above pr
- 10-15 16:30 GBPUSD NO_TRADE: market unavailable for a decision: blocked before consulting the model: EXPOSURE: a GBPUSD position is already open
- 10-15 16:30 EURUSD NO_TRADE: market unavailable for a decision: risk engine: open_positions (3 open, max 3): the model was not consulted
- 10-15 16:15 AUDJPY NO_TRADE: market unavailable for a decision: blocked before consulting the model: EXPOSURE: a AUDJPY position is already open
- 10-15 16:15 EURCHF NO_TRADE: market unavailable for a decision: risk engine: open_positions (3 open, max 3): the model was not consulted

## Open paper positions

| Symbol | Side | Qty | Entry | Stop | Target | P&L |
|---|---|---|---|---|---|---|
| USDCAD | SELL | 3.15 | 1.4198149999999998 | 1.4216 | 1.4174 | $75.45 |
| USDJPY | SELL | 1.75 | 158.094 | 158.26 | 157.84 | $-127.89 |
| AUDJPY | BUY | 2.83 | 109.32300000000001 | 109.1 | 109.8 | $48.14 |

## Closed paper trades (latest 20)

| Closed | Symbol | Side | Net | R | Costs | Exit | Source |
|---|---|---|---|---|---|---|---|
| 10-15 16:48 | EURGBP | SELL | $155.71 | +0.63 | $42.44 | TIME | DUAL_AI |
| 10-15 16:44 | GBPUSD | SELL | $-385.57 | -0.77 | $81.90 | STOP | DUAL_AI |
| 10-15 14:11 | USDCAD | BUY | $-399.97 | -0.80 | $77.26 | STOP | DUAL_AI |
| 10-15 14:01 | EURUSD | SELL | $-453.65 | -0.91 | $54.91 | STOP | DUAL_AI |
| 10-15 13:59 | USDCAD | SELL | $650.69 | +1.31 | $88.09 | TARGET | DUAL_AI |
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

## Dual AI desk (two free OpenRouter traders; a trade only when they agree)

OpenRouter `READY` · key set · trader 1 `nvidia/nemotron-3.5-super-vl:free` · trader 2 `dots-studio/dots-3-note-preview:free` · debate `nvidia/nemotron-3-super-120b-a12b:free` · calls today 69/900

AI trades 33 (adequate) · wins 15 · losses 18 · expectancy -0.042R · profit factor 0.86

Disagreements (not traded; the debate runs in shadow): 57 · the debate's pick if taken: 51 resolved (adequate), expectancy -0.146R · the side it rejected if taken: 56 resolved (adequate), expectancy -0.164R

Exits in shadow (the same trades, followed again; measured, never traded): break-even at +1R +0.246R vs +0.393R as taken (10, insufficient) · held 24 h none resolved yet · stop and target twice as far none resolved yet

Trades taken by session (UTC): ASIA 14 resolved (insufficient), expectancy +0.001R · LONDON 3 resolved (insufficient), expectancy +0.542R · OVERLAP 3 resolved (insufficient), expectancy -0.479R · NEW_YORK 4 resolved (insufficient), expectancy +1.091R · LATE 3 resolved (insufficient), expectancy -1.106R

| Time | Symbol | Trader 1 | Trader 2 | Debate (shadow) | Rule | Final | Risk |
|---|---|---|---|---|---|---|---|
| 10-15 17:30 | GBPJPY | -  | -  | - | MARKET_UNAVAILABLE | NO_TRADE | - |
| 10-15 17:30 | EURJPY | -  | -  | - | MARKET_UNAVAILABLE | NO_TRADE | - |
| 10-15 17:15 | EURGBP | -  | -  | - | MARKET_UNAVAILABLE | NO_TRADE | - |
| 10-15 17:15 | NZDUSD | -  | -  | - | MARKET_UNAVAILABLE | NO_TRADE | - |
| 10-15 17:00 | USDCHF | -  | -  | - | MARKET_UNAVAILABLE | NO_TRADE | - |
| 10-15 17:00 | USDCAD | SELL 60 | SELL 60 | - | AGREE | SELL | APPROVED |
| 10-15 16:45 | AUDUSD | -  | -  | - | MARKET_UNAVAILABLE | NO_TRADE | - |
| 10-15 16:45 | USDJPY | SELL 62 | SELL 65 | - | AGREE | SELL | APPROVED |
| 10-15 16:30 | GBPUSD | -  | -  | - | MARKET_UNAVAILABLE | NO_TRADE | - |
| 10-15 16:30 | EURUSD | -  | -  | - | MARKET_UNAVAILABLE | NO_TRADE | - |
| 10-15 16:15 | AUDJPY | -  | -  | - | MARKET_UNAVAILABLE | NO_TRADE | - |
| 10-15 16:15 | EURCHF | -  | -  | - | MARKET_UNAVAILABLE | NO_TRADE | - |

The chart Trader 1 read last: `last_chart.png`. (numbers): no free vision model answered, so Trader 1 read the same chart from its numbers.

Full figures: `paper_forward.json`. Rules: `docs/PAPER_FORWARD.md` on main.
