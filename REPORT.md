# PAPER FORWARD TEST — NOT REAL MONEY

Updated 2026-10-16 08:58 UTC · mode `PAPER_FORWARD` · profile `PAPER-FORWARD-200K` · shift started 2026-10-16 04:43 UTC · decision system `dual_ai`

Research status (historical, unchanged): **NO EDGE — DO NOT TRADE (historical research; this test measures forward)**. This run measures the system forward; it is not evidence of an edge until it has a sample and the forward-eligibility rules say so.

## The rule that trades: a trade only when both AIs agree

| Trades | Wins | Losses | Win rate | Net P&L | Expectancy | Profit factor | Max drawdown |
|---|---|---|---|---|---|---|---|
| 36 (adequate) | 20 | 16 | 55.6% | $2,394.08 | +0.158R | 1.43 | $1,928.96 |

The account below is the real paper account. It also holds the 4 trade(s) of the old DEBATE rule, stopped in dual-ai-1.2.0 (opposite sides: one debate picked the side and the trade was taken): net $-1,416.51, 0 won, expectancy -0.817R. They stay in the journal, listed as theirs, and are never averaged with the agreement figures.

## Paper account (every trade)

| Account | Equity | P&L today | Total P&L | Drawdown | Open | Trades | Win rate | Expectancy | Profit factor | Risk | Bot |
|---|---|---|---|---|---|---|---|---|---|---|---|
| $200,000.00 | $201,207.81 | $1,850.75 | $1,207.81 | $0.00 | 3 | 40 (adequate) | 50.0% | +0.060R | 1.14 | ACTIVE | RUNNING |

**WARNING: the hard risk gate refused 7 of the last 20 decisions: OPEN_RISK_LIMIT x6, FINANCING_EXCEEDS_RISK x1.** A refusal by the gate after the risk engine approved is never routine. The latest at 10-16 06:45 UTC; 9 decision(s) since, none refused by the gate.

## Last decisions (decision → risk → paper execution)

- 10-16 08:45 EURUSD BUY: AI DECISION → RISK APPROVED → PAPER EXECUTED
- 10-16 08:30 AUDJPY BUY: AI DECISION → RISK REJECTED — reward_risk: 0.93 vs minimum 1.2
- 10-16 08:30 EURCHF SELL: AI DECISION → RISK REJECTED — cost_to_risk: round-trip cost is 30.0% of the stop (max 25%): spread 0.00018 + commission and slippage
- 10-16 08:15 GBPJPY BUY: AI DECISION → RISK REJECTED — reward_risk: 1.17 vs minimum 1.2
- 10-16 08:15 EURJPY BUY: AI DECISION → RISK APPROVED → PAPER EXECUTED
- 10-16 08:00 NZDUSD BUY: AI DECISION → RISK APPROVED → PAPER EXECUTED
- 10-16 07:45 USDCHF SELL: AI DECISION → RISK REJECTED — reward_risk: 1.07 vs minimum 1.2
- 10-16 07:45 USDCAD SELL: AI DECISION → RISK REJECTED — reward_risk: 0.76 vs minimum 1.2
- 10-16 07:15 AUDUSD BUY: AI DECISION → RISK APPROVED → NOT EXECUTED (BLOCKED) — decision is 1103s old (max 900s): stale, not executed
- 10-16 06:45 GBPUSD BUY: AI DECISION → RISK APPROVED → RISK REJECTED — hard risk gate: RISK_GATE_REJECTED reason=OPEN_RISK_LIMIT equity_conservative=201051.93 daily_pnl=1694.87 daily_limit=-10000.00 total_pnl=1051.93 total_limit=-20000.00 open_risk=2059.57 max_loss=499.9
- 10-16 06:30 AUDJPY SELL: AI DECISION → RISK REJECTED — cost_to_risk: round-trip cost is 34.2% of the stop (max 25%): spread 0.018 + commission and slippage
- 10-16 06:30 EURCHF BUY: AI DECISION → RISK APPROVED → RISK REJECTED — hard risk gate: RISK_GATE_REJECTED reason=OPEN_RISK_LIMIT equity_conservative=200836.39 daily_pnl=1479.32 daily_limit=-10000.00 total_pnl=836.39 total_limit=-20000.00 open_risk=1843.96 max_loss=499.48
- 10-16 06:00 GBPJPY BUY: AI DECISION → RISK REJECTED — reward_risk: 0.54 vs minimum 1.2
- 10-16 05:45 NZDUSD BUY: AI DECISION → RISK APPROVED → RISK REJECTED — hard risk gate: RISK_GATE_REJECTED reason=FINANCING_EXCEEDS_RISK equity_conservative=200665.88 daily_pnl=1308.82 daily_limit=-10000.00 total_pnl=665.88 total_limit=-20000.00 open_risk=1673.00 max_loss
- 10-16 05:30 USDCHF SELL: AI DECISION → RISK REJECTED — reward_risk: 0.68 vs minimum 1.2
- 10-16 05:30 USDCAD SELL: AI DECISION → RISK APPROVED → RISK REJECTED — hard risk gate: RISK_GATE_REJECTED reason=OPEN_RISK_LIMIT equity_conservative=200751.02 daily_pnl=1393.95 daily_limit=-10000.00 total_pnl=751.02 total_limit=-20000.00 open_risk=1758.17 max_loss=499.37
- 10-16 05:00 USDJPY SELL: AI DECISION → RISK APPROVED → NOT EXECUTED (BLOCKED) — decision is 933s old (max 900s): stale, not executed
- 10-16 04:45 GBPUSD BUY: AI DECISION → RISK APPROVED → RISK REJECTED — hard risk gate: RISK_GATE_REJECTED reason=OPEN_RISK_LIMIT equity_conservative=200965.56 daily_pnl=1608.50 daily_limit=-10000.00 total_pnl=965.56 total_limit=-20000.00 open_risk=1972.92 max_loss=499.69
- 10-16 04:45 EURUSD BUY: AI DECISION → RISK APPROVED → RISK REJECTED — hard risk gate: RISK_GATE_REJECTED reason=OPEN_RISK_LIMIT equity_conservative=200923.53 daily_pnl=1566.46 daily_limit=-10000.00 total_pnl=923.53 total_limit=-20000.00 open_risk=1930.88 max_loss=499.79
- 10-16 04:30 USDCHF BUY: AI DECISION → RISK APPROVED → RISK REJECTED — hard risk gate: RISK_GATE_REJECTED reason=OPEN_RISK_LIMIT equity_conservative=200923.56 daily_pnl=1566.50 daily_limit=-10000.00 total_pnl=923.56 total_limit=-20000.00 open_risk=1930.99 max_loss=499.43

## Latest decisions, NO TRADE included (896 so far)

- 10-16 08:45 GBPUSD NO_TRADE: market unavailable for a decision: risk engine: open_positions (3 open, max 3); currency_exposure (2 open positions share a currency, max 2): the model was not consulted
- 10-16 08:45 EURUSD BUY: BUY EURUSD on M15: AGREE: Trader 1 (nvidia/nemotron-3.5-super-vl:free) BUY 60: H4 uptrend with a fresh M15 bullish BOS/HH and price retesting the tested demand order block (1.1236–1.1241) gives the lo
- 10-16 08:30 AUDJPY BUY: BUY AUDJPY on M15: AGREE: Trader 1 (nvidia/nemotron-3.5-super-vl:free) BUY 62: M15 shows four consecutive bullish BOS with the latest at 109.893 three bars ago and bullish displacement five bars ago; 
- 10-16 08:30 EURCHF SELL: SELL EURCHF on M15: AGREE: Trader 1 (dots-studio/dots-3-note-preview:free) SELL 75: The M15 chart displays a clear bearish trend with lower highs and lower lows, reinforced by recent bearish CHOCH and
- 10-16 08:15 GBPJPY BUY: BUY GBPJPY on M15: AGREE: Trader 1 (nvidia/nemotron-3.5-super-vl:free) BUY 68: Both timeframes trend up with fresh bullish structure breaks; untested demand OB and swept lows support bids; open bullis
- 10-16 08:15 EURJPY BUY: BUY EURJPY on M15: AGREE: Trader 1 (nvidia/nemotron-3.5-super-vl:free) BUY 64: M15 structure turned bullish with a CHOCH at 177.437 followed by bullish BOS at 177.552 and 177.59, leaving an untested d
- 10-16 08:00 EURGBP NO_TRADE: market unavailable for a decision: blocked before consulting the model: EXPOSURE: a EURGBP position is already open
- 10-16 08:00 NZDUSD BUY: BUY NZDUSD on M15: AGREE: Trader 1 (nvidia/nemotron-3.5-super-vl:free) BUY 70: Both timeframes are structurally bullish with a fresh BOS and price above the recent higher high. The untested demand blo
- 10-16 07:45 USDCHF SELL: SELL USDCHF on M15: AGREE: Trader 1 (nvidia/nemotron-3.5-super-vl:free) SELL 68: M15 and H4 are both trending down (LH+LL) with a fresh bearish BOS at 0.82595 just one bar ago and H4 bearish CHOCH/BOS
- 10-16 07:45 USDCAD SELL: SELL USDCAD on M15: AGREE: Trader 1 (nvidia/nemotron-3.5-super-vl:free) SELL 65: M15 and H4 are both trending down (LH+LL) with a fresh bearish BOS at 1.4167 breaking the prior LL. Price is testing th
- 10-16 07:15 AUDUSD BUY: BUY AUDUSD on M15: AGREE: Trader 1 (nvidia/nemotron-3.5-super-vl:free) BUY 65: M15 structure is bullish with a fresh BOS at 0.69502 and untested demand below; the overhead bearish FVG is mitigated. Bu
- 10-16 07:15 USDJPY NO_TRADE: the traders disagree (Trader 1 SELL 72, Trader 2 BUY 62): no trade unless both choose the same side; the shadow debate gave no usable answer (TIMEOUT: no answer within 420 s (last: UPSTREAM_ERROR))

## Open paper positions

| Symbol | Side | Qty | Entry | Stop | Target | P&L |
|---|---|---|---|---|---|---|
| EURUSD | BUY | 3.33 | 1.1245500000000002 | 1.1234 | 1.126 | $103.23 |
| EURJPY | BUY | 3.8 | 177.6615 | 177.505 | 177.849 | $33.52 |
| NZDUSD | BUY | 2.75 | 0.566785 | 0.56525 | 0.569 | $93.50 |

## Closed paper trades (latest 20)

| Closed | Symbol | Side | Net | R | Costs | Exit | Source | Rule |
|---|---|---|---|---|---|---|---|---|
| 10-16 08:05 | EURGBP | SELL | $129.31 | +0.26 | $81.01 | TIME | DUAL_AI | AGREE |
| 10-16 07:02 | AUDUSD | BUY | $840.45 | +1.68 | $77.58 | TARGET | DUAL_AI | AGREE |
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

## Dual AI desk (two free OpenRouter traders; a trade only when they agree)

OpenRouter `READY` · key set · trader 1 `nvidia/nemotron-3.5-super-vl:free` · trader 2 `nvidia/nemotron-3-super-120b-a12b:free` · debate `dots-studio/dots-3-note-preview:free` · calls today 69/900

Agreement trades 36 (adequate) · wins 20 · losses 16 · net $2,394.08 · expectancy +0.158R · profit factor 1.43 · old DEBATE rule (stopped in dual-ai-1.2.0): 4 trade(s), net $-1,416.51, apart

Disagreements (not traded; the debate runs in shadow): 58 · the debate's pick if taken: 57 resolved (adequate), expectancy -0.184R · the side it rejected if taken: 62 resolved (adequate), expectancy -0.219R

Exits in shadow (the same trades, followed again; measured, never traded): break-even at +1R -0.023R vs +0.152R as taken (20, insufficient) · held 24 h +0.404R vs +0.315R as taken (12, insufficient) · stop and target twice as far +0.236R vs +0.315R as taken (12, insufficient)

Trades taken by session (UTC): ASIA 16 resolved (insufficient), expectancy -0.034R · LONDON 4 resolved (insufficient), expectancy +0.630R · OVERLAP 8 resolved (insufficient), expectancy -0.382R · NEW_YORK 6 resolved (insufficient), expectancy +0.792R · LATE 3 resolved (insufficient), expectancy -1.106R

| Time | Symbol | Trader 1 | Trader 2 | Debate (shadow) | Rule | Final | Risk |
|---|---|---|---|---|---|---|---|
| 10-16 08:45 | GBPUSD | -  | -  | - | MARKET_UNAVAILABLE | NO_TRADE | - |
| 10-16 08:45 | EURUSD | BUY 60 | BUY 58 | - | AGREE | BUY | APPROVED |
| 10-16 08:30 | AUDJPY | BUY 62 | BUY 68 | - | AGREE | BUY | REJECTED |
| 10-16 08:30 | EURCHF | SELL 75 | SELL 66 | - | AGREE | SELL | REJECTED |
| 10-16 08:15 | GBPJPY | BUY 68 | BUY 72 | - | AGREE | BUY | REJECTED |
| 10-16 08:15 | EURJPY | BUY 64 | BUY 63 | - | AGREE | BUY | APPROVED |
| 10-16 08:00 | EURGBP | -  | -  | - | MARKET_UNAVAILABLE | NO_TRADE | - |
| 10-16 08:00 | NZDUSD | BUY 70 | BUY 68 | - | AGREE | BUY | APPROVED |
| 10-16 07:45 | USDCHF | SELL 68 | SELL 70 | - | AGREE | SELL | REJECTED |
| 10-16 07:45 | USDCAD | SELL 65 | SELL 62 | - | AGREE | SELL | REJECTED |
| 10-16 07:15 | AUDUSD | BUY 65 | BUY 60 | - | AGREE | BUY | APPROVED |
| 10-16 07:15 | USDJPY | SELL 72 | BUY 62 | - | DISAGREE | NO_TRADE | - |

The chart Trader 1 read last: `last_chart.png`. (numbers): no free vision model answered, so Trader 1 read the same chart from its numbers.

Full figures: `paper_forward.json`. Rules: `docs/PAPER_FORWARD.md` on main.
