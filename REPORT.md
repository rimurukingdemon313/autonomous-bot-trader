# PAPER FORWARD TEST — NOT REAL MONEY

Updated 2026-10-16 04:42 UTC · mode `PAPER_FORWARD` · profile `PAPER-FORWARD-200K` · shift started 2026-10-15 23:07 UTC · decision system `dual_ai`

Research status (historical, unchanged): **NO EDGE — DO NOT TRADE (historical research; this test measures forward)**. This run measures the system forward; it is not evidence of an edge until it has a sample and the forward-eligibility rules say so.

## The rule that trades: a trade only when both AIs agree

| Trades | Wins | Losses | Win rate | Net P&L | Expectancy | Profit factor | Max drawdown |
|---|---|---|---|---|---|---|---|
| 34 (adequate) | 18 | 16 | 52.9% | $1,424.33 | +0.110R | 1.26 | $1,928.96 |

The account below is the real paper account. It also holds the 4 trade(s) of the old DEBATE rule, stopped in dual-ai-1.2.0 (opposite sides: one debate picked the side and the trade was taken): net $-1,416.51, 0 won, expectancy -0.817R. They stay in the journal, listed as theirs, and are never averaged with the agreement figures.

## Paper account (every trade)

| Account | Equity | P&L today | Total P&L | Drawdown | Open | Trades | Win rate | Expectancy | Profit factor | Risk | Bot |
|---|---|---|---|---|---|---|---|---|---|---|---|
| $200,000.00 | $200,975.83 | $1,618.77 | $975.83 | $0.00 | 2 | 38 (adequate) | 47.4% | +0.012R | 1.00 | ACTIVE | RUNNING |

**WARNING: the hard risk gate refused 3 of the last 20 decisions: OPEN_RISK_LIMIT x3.** A refusal by the gate after the risk engine approved is never routine. The latest at 10-16 04:30 UTC; none after it yet.

## Last decisions (decision → risk → paper execution)

- 10-16 04:30 USDCHF BUY: AI DECISION → RISK APPROVED → RISK REJECTED — hard risk gate: RISK_GATE_REJECTED reason=OPEN_RISK_LIMIT equity_conservative=200923.56 daily_pnl=1566.50 daily_limit=-10000.00 total_pnl=923.56 total_limit=-20000.00 open_risk=1930.99 max_loss=499.43
- 10-16 04:30 USDCAD SELL: AI DECISION → RISK REJECTED — reward_risk: 1.05 vs minimum 1.2
- 10-16 04:15 USDJPY SELL: AI DECISION → RISK APPROVED → RISK REJECTED — hard risk gate: RISK_GATE_REJECTED reason=OPEN_RISK_LIMIT equity_conservative=200666.99 daily_pnl=1309.93 daily_limit=-10000.00 total_pnl=666.99 total_limit=-20000.00 open_risk=1674.18 max_loss=499.59
- 10-16 04:00 GBPUSD BUY: AI DECISION → RISK REJECTED — reward_risk: 1.03 vs minimum 1.2
- 10-16 04:00 EURUSD BUY: AI DECISION → RISK APPROVED → RISK REJECTED — hard risk gate: RISK_GATE_REJECTED reason=OPEN_RISK_LIMIT equity_conservative=200585.10 daily_pnl=1228.04 daily_limit=-10000.00 total_pnl=585.10 total_limit=-20000.00 open_risk=1620.70 max_loss=498.17
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

## Latest decisions, NO TRADE included (870 so far)

- 10-16 04:30 USDCHF BUY: BUY USDCHF on M15: AGREE: Trader 1 (nvidia/nemotron-3.5-super-vl:free) BUY 55: Both timeframes trend down but price is at range extreme lows (H1 pos 0.10, M15 0.19) with EQL liquidity at 0.82595 likel
- 10-16 04:30 USDCAD SELL: SELL USDCAD on M15: AGREE: Trader 1 (dots-studio/dots-3-note-preview:free) SELL 75: The overall trend is bearish on both M15 and H4, with a recent lower low indicating continuation. The price is pulli
- 10-16 04:15 AUDUSD NO_TRADE: market unavailable for a decision: blocked before consulting the model: EXPOSURE: a AUDUSD position is already open
- 10-16 04:15 USDJPY SELL: SELL USDJPY on M15: AGREE: Trader 1 (nvidia/nemotron-3.5-super-vl:free) SELL 65: Both timeframes trend down with LH/LL structure; the most recent M15 break is bearish CHoCH at 158.052 and the latest s
- 10-16 04:00 GBPUSD BUY: BUY GBPUSD on M15: AGREE: Trader 1 (nvidia/nemotron-3.5-super-vl:free) BUY 65: M15 structure is bullish with consecutive BOS breaks and an untested demand order block below. Price is at the ask inside
- 10-16 04:00 EURUSD BUY: BUY EURUSD on M15: AGREE: Trader 1 (nvidia/nemotron-3.5-super-vl:free) BUY 66: H4 is up and M15 just confirmed a bullish BOS at 1.12233 with bullish displacement on the current bar, favoring continuat
- 10-16 03:45 AUDJPY NO_TRADE: market unavailable for a decision: risk engine: open_positions (3 open, max 3): the model was not consulted
- 10-16 03:45 EURCHF NO_TRADE: market unavailable for a decision: risk engine: open_positions (3 open, max 3): the model was not consulted
- 10-16 03:30 GBPJPY NO_TRADE: market unavailable for a decision: risk engine: open_positions (3 open, max 3): the model was not consulted
- 10-16 03:30 EURJPY NO_TRADE: market unavailable for a decision: risk engine: open_positions (3 open, max 3): the model was not consulted
- 10-16 03:15 EURGBP NO_TRADE: market unavailable for a decision: blocked before consulting the model: EXPOSURE: a EURGBP position is already open
- 10-16 03:15 NZDUSD NO_TRADE: market unavailable for a decision: risk engine: open_positions (3 open, max 3); currency_exposure (2 open positions share a currency, max 2): the model was not consulted

## Open paper positions

| Symbol | Side | Qty | Entry | Stop | Target | P&L |
|---|---|---|---|---|---|---|
| AUDUSD | BUY | 4.31 | 0.69326 | 0.69238 | 0.69528 | $728.39 |
| EURGBP | SELL | 3.16 | 0.8447300000000001 | 0.84568 | 0.8435 | $239.63 |

## Closed paper trades (latest 20)

| Closed | Symbol | Side | Net | R | Costs | Exit | Source | Rule |
|---|---|---|---|---|---|---|---|---|
| 10-16 03:49 | USDCAD | SELL | $451.28 | +0.91 | $77.18 | TARGET | DUAL_AI | AGREE |
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

## Dual AI desk (two free OpenRouter traders; a trade only when they agree)

OpenRouter `READY` · key set · trader 1 `nvidia/nemotron-3.5-super-vl:free` · trader 2 `nvidia/nemotron-3-super-120b-a12b:free` · debate `dots-studio/dots-3-note-preview:free` · calls today 40/900

Agreement trades 34 (adequate) · wins 18 · losses 16 · net $1,424.33 · expectancy +0.110R · profit factor 1.26 · old DEBATE rule (stopped in dual-ai-1.2.0): 4 trade(s), net $-1,416.51, apart

Disagreements (not traded; the debate runs in shadow): 57 · the debate's pick if taken: 57 resolved (adequate), expectancy -0.184R · the side it rejected if taken: 62 resolved (adequate), expectancy -0.219R

Exits in shadow (the same trades, followed again; measured, never traded): break-even at +1R -0.050R vs +0.134R as taken (19, insufficient) · held 24 h +0.341R vs +0.287R as taken (9, insufficient) · stop and target twice as far +0.417R vs +0.287R as taken (9, insufficient)

Trades taken by session (UTC): ASIA 15 resolved (insufficient), expectancy -0.068R · LONDON 4 resolved (insufficient), expectancy +0.630R · OVERLAP 8 resolved (insufficient), expectancy -0.382R · NEW_YORK 6 resolved (insufficient), expectancy +0.792R · LATE 3 resolved (insufficient), expectancy -1.106R

| Time | Symbol | Trader 1 | Trader 2 | Debate (shadow) | Rule | Final | Risk |
|---|---|---|---|---|---|---|---|
| 10-16 04:30 | USDCHF | BUY 55 | BUY 58 | - | AGREE | BUY | APPROVED |
| 10-16 04:30 | USDCAD | SELL 75 | SELL 70 | - | AGREE | SELL | REJECTED |
| 10-16 04:15 | AUDUSD | -  | -  | - | MARKET_UNAVAILABLE | NO_TRADE | - |
| 10-16 04:15 | USDJPY | SELL 65 | SELL 62 | - | AGREE | SELL | APPROVED |
| 10-16 04:00 | GBPUSD | BUY 65 | BUY 68 | - | AGREE | BUY | REJECTED |
| 10-16 04:00 | EURUSD | BUY 66 | BUY 68 | - | AGREE | BUY | APPROVED |
| 10-16 03:45 | AUDJPY | -  | -  | - | MARKET_UNAVAILABLE | NO_TRADE | - |
| 10-16 03:45 | EURCHF | -  | -  | - | MARKET_UNAVAILABLE | NO_TRADE | - |
| 10-16 03:30 | GBPJPY | -  | -  | - | MARKET_UNAVAILABLE | NO_TRADE | - |
| 10-16 03:30 | EURJPY | -  | -  | - | MARKET_UNAVAILABLE | NO_TRADE | - |
| 10-16 03:15 | EURGBP | -  | -  | - | MARKET_UNAVAILABLE | NO_TRADE | - |
| 10-16 03:15 | NZDUSD | -  | -  | - | MARKET_UNAVAILABLE | NO_TRADE | - |

The chart Trader 1 read last: `last_chart.png`. (numbers): no free vision model answered, so Trader 1 read the same chart from its numbers.

Full figures: `paper_forward.json`. Rules: `docs/PAPER_FORWARD.md` on main.
