# PAPER FORWARD TEST — NOT REAL MONEY

Updated 2026-10-16 06:58 UTC · mode `PAPER_FORWARD` · profile `PAPER-FORWARD-200K` · shift started 2026-10-16 04:43 UTC · decision system `dual_ai`

Research status (historical, unchanged): **NO EDGE — DO NOT TRADE (historical research; this test measures forward)**. This run measures the system forward; it is not evidence of an edge until it has a sample and the forward-eligibility rules say so.

## The rule that trades: a trade only when both AIs agree

| Trades | Wins | Losses | Win rate | Net P&L | Expectancy | Profit factor | Max drawdown |
|---|---|---|---|---|---|---|---|
| 34 (adequate) | 18 | 16 | 52.9% | $1,424.33 | +0.110R | 1.26 | $1,928.96 |

The account below is the real paper account. It also holds the 4 trade(s) of the old DEBATE rule, stopped in dual-ai-1.2.0 (opposite sides: one debate picked the side and the trade was taken): net $-1,416.51, 0 won, expectancy -0.817R. They stay in the journal, listed as theirs, and are never averaged with the agreement figures.

## Paper account (every trade)

| Account | Equity | P&L today | Total P&L | Drawdown | Open | Trades | Win rate | Expectancy | Profit factor | Risk | Bot |
|---|---|---|---|---|---|---|---|---|---|---|---|
| $200,000.00 | $201,103.19 | $1,746.12 | $1,103.19 | $0.00 | 2 | 38 (adequate) | 47.4% | +0.012R | 1.00 | ACTIVE | RUNNING |

**WARNING: the hard risk gate refused 8 of the last 20 decisions: OPEN_RISK_LIMIT x7, FINANCING_EXCEEDS_RISK x1.** A refusal by the gate after the risk engine approved is never routine. The latest at 10-16 06:30 UTC; none after it yet.

## Last decisions (decision → risk → paper execution)

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

## Latest decisions, NO TRADE included (882 so far)

- 10-16 06:30 AUDJPY SELL: SELL AUDJPY on M15: AGREE: Trader 1 (nvidia/nemotron-3.5-super-vl:free) SELL 62: M15 is in a confirmed downtrend (LH+LL) with a fresh LH at 109.666 after today's HH 109.692, and price sits at the H4 b
- 10-16 06:30 EURCHF BUY: BUY EURCHF on M15: AGREE: Trader 1 (nvidia/nemotron-3.5-super-vl:free) BUY 62: Bullish BOS/CHoCH structure breaks and a tested demand order block support a long bias after price swept the 0.92781 lows
- 10-16 06:00 GBPJPY BUY: BUY GBPJPY on M15: AGREE: Trader 1 (nvidia/nemotron-3.5-super-vl:free) BUY 55: H4 trend is up and the M15 just printed a bullish CHoCH at 209.922 with bullish displacement, making the pullback to the 
- 10-16 06:00 EURJPY NO_TRADE: Trader 2 (independent) gave no usable answer (TIMEOUT: no answer within 420 s (last: INVALID: no JSON object in the reply)): no decision on one trader alone
- 10-16 05:45 EURGBP NO_TRADE: market unavailable for a decision: blocked before consulting the model: EXPOSURE: a EURGBP position is already open
- 10-16 05:45 NZDUSD BUY: BUY NZDUSD on M15: AGREE: Trader 1 (nvidia/nemotron-3.5-super-vl:free) BUY 57: Both timeframes trend up with HH+HL and multiple bullish BOS. Price is pulling back from HH 0.56583 into the open bullish
- 10-16 05:30 USDCHF SELL: SELL USDCHF on M15: AGREE: Trader 1 (nvidia/nemotron-3.5-super-vl:free) SELL 65: Bearish structure aligns on both timeframes with the most recent structure break bearish and price retesting a tested s
- 10-16 05:30 USDCAD SELL: SELL USDCAD on M15: AGREE: Trader 1 (nvidia/nemotron-3.5-super-vl:free) SELL 60: M15 and H4 are both trending down (LH+LL), and the latest confirmed break is a bearish CHoCH at 1.4181. Price is retest
- 10-16 05:00 AUDUSD NO_TRADE: market unavailable for a decision: blocked before consulting the model: EXPOSURE: a AUDUSD position is already open
- 10-16 05:00 USDJPY SELL: SELL USDJPY on M15: AGREE: Trader 1 (dots-studio/dots-3-note-preview:free) SELL 80: The chart shows a clear down trend on both M15 and H4 with a recent bearish BOS and a sweep of lows. Selling at the 
- 10-16 04:45 GBPUSD BUY: BUY GBPUSD on M15: AGREE: Trader 1 (nvidia/nemotron-3.5-super-vl:free) BUY 62: M15 shows a bullish HH/HL structure with fresh BOS breaks and bullish displacement, supported by an untested demand order
- 10-16 04:45 EURUSD BUY: BUY EURUSD on M15: AGREE: Trader 1 (nvidia/nemotron-3.5-super-vl:free) BUY 67: M15 and H4 structure are bullish with a fresh BOS above 1.12233 and an untested demand OB at 1.12133–1.12208; an open bul

## Open paper positions

| Symbol | Side | Qty | Entry | Stop | Target | P&L |
|---|---|---|---|---|---|---|
| AUDUSD | BUY | 4.31 | 0.69326 | 0.69238 | 0.69528 | $771.49 |
| EURGBP | SELL | 3.16 | 0.8447300000000001 | 0.84568 | 0.8435 | $323.88 |

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

OpenRouter `READY` · key set · trader 1 `nvidia/nemotron-3.5-super-vl:free` · trader 2 `dots-studio/dots-3-note-preview:free` · debate `nvidia/nemotron-3.5-lightning:free` · calls today 39/900

Agreement trades 34 (adequate) · wins 18 · losses 16 · net $1,424.33 · expectancy +0.110R · profit factor 1.26 · old DEBATE rule (stopped in dual-ai-1.2.0): 4 trade(s), net $-1,416.51, apart

Disagreements (not traded; the debate runs in shadow): 57 · the debate's pick if taken: 57 resolved (adequate), expectancy -0.184R · the side it rejected if taken: 62 resolved (adequate), expectancy -0.219R

Exits in shadow (the same trades, followed again; measured, never traded): break-even at +1R -0.050R vs +0.134R as taken (19, insufficient) · held 24 h +0.441R vs +0.393R as taken (10, insufficient) · stop and target twice as far +0.271R vs +0.393R as taken (10, insufficient)

Trades taken by session (UTC): ASIA 15 resolved (insufficient), expectancy -0.068R · LONDON 4 resolved (insufficient), expectancy +0.630R · OVERLAP 8 resolved (insufficient), expectancy -0.382R · NEW_YORK 6 resolved (insufficient), expectancy +0.792R · LATE 3 resolved (insufficient), expectancy -1.106R

| Time | Symbol | Trader 1 | Trader 2 | Debate (shadow) | Rule | Final | Risk |
|---|---|---|---|---|---|---|---|
| 10-16 06:30 | AUDJPY | SELL 62 | SELL 62 | - | AGREE | SELL | REJECTED |
| 10-16 06:30 | EURCHF | BUY 62 | BUY 65 | - | AGREE | BUY | APPROVED |
| 10-16 06:00 | GBPJPY | BUY 55 | BUY 75 | - | AGREE | BUY | REJECTED |
| 10-16 06:00 | EURJPY | BUY 72 | -  | - | TRADER2_UNAVAILABLE | NO_TRADE | - |
| 10-16 05:45 | EURGBP | -  | -  | - | MARKET_UNAVAILABLE | NO_TRADE | - |
| 10-16 05:45 | NZDUSD | BUY 57 | BUY 60 | - | AGREE | BUY | APPROVED |
| 10-16 05:30 | USDCHF | SELL 65 | SELL 72 | - | AGREE | SELL | REJECTED |
| 10-16 05:30 | USDCAD | SELL 60 | SELL 65 | - | AGREE | SELL | APPROVED |
| 10-16 05:00 | AUDUSD | -  | -  | - | MARKET_UNAVAILABLE | NO_TRADE | - |
| 10-16 05:00 | USDJPY | SELL 80 | SELL 75 | - | AGREE | SELL | APPROVED |
| 10-16 04:45 | GBPUSD | BUY 62 | BUY 65 | - | AGREE | BUY | APPROVED |
| 10-16 04:45 | EURUSD | BUY 67 | BUY 65 | - | AGREE | BUY | APPROVED |

The chart Trader 1 read last: `last_chart.png`. (numbers): no free vision model answered, so Trader 1 read the same chart from its numbers.

Full figures: `paper_forward.json`. Rules: `docs/PAPER_FORWARD.md` on main.
