# PAPER FORWARD TEST — NOT REAL MONEY

Updated 2026-10-16 13:49 UTC · mode `PAPER_FORWARD` · profile `PAPER-FORWARD-200K` · shift started 2026-10-16 10:18 UTC · decision system `dual_ai`

Research status (historical, unchanged): **NO EDGE — DO NOT TRADE (historical research; this test measures forward)**. This run measures the system forward; it is not evidence of an edge until it has a sample and the forward-eligibility rules say so.

## The rule that trades: a trade only when both AIs agree

| Trades | Wins | Losses | Win rate | Net P&L | Expectancy | Profit factor | Max drawdown |
|---|---|---|---|---|---|---|---|
| 40 (adequate) | 22 | 18 | 55.0% | $2,366.08 | +0.140R | 1.37 | $1,928.96 |

The 4 trade(s) of the old DEBATE rule, stopped in dual-ai-1.2.0, were removed from the paper account at the operator's request: their net $-1,416.51 was put back by a declared adjustment ($1,416.51). They stay in the journal (append-only), in none of the account's figures below.

## Paper account

| Account | Equity | P&L today | Total P&L | Drawdown | Open | Trades | Win rate | Expectancy | Profit factor | Risk | Bot |
|---|---|---|---|---|---|---|---|---|---|---|---|
| $200,000.00 | $202,157.08 | $1,383.50 | $2,157.08 | $0.00 | 1 | 40 (adequate) | 55.0% | +0.140R | 1.37 | ACTIVE | RUNNING |

Equity includes declared operator adjustments of $1,416.51 (without them: $200,740.56); P&L today excludes them. `remove-retired-debate-rule-trades-2026-10-15`: operator: the 4 trades of the retired debate rule (dual-ai 1.1.0, stopped in 1.2.0) are removed from the paper account; they stay in the journal.

**WARNING: the hard risk gate refused 1 of the last 20 decisions: OPEN_RISK_LIMIT x1.** A refusal by the gate after the risk engine approved is never routine. The latest at 10-16 06:45 UTC; 18 decision(s) since, none refused by the gate.

## Last decisions (decision → risk → paper execution)

- 10-16 13:45 EURUSD BUY: AI DECISION → RISK REJECTED — weekend_carry: held up to 480 min it could still be open at the Friday close (Fri 17:00 New York)
- 10-16 13:30 AUDJPY SELL: AI DECISION → RISK REJECTED — reward_risk: 1.13 vs minimum 1.2; weekend_carry: held up to 480 min it could still be open at the Friday close (Fri 17:00 New York)
- 10-16 13:30 EURCHF SELL: AI DECISION → RISK REJECTED — reward_risk: 1.10 vs minimum 1.2; weekend_carry: held up to 480 min it could still be open at the Friday close (Fri 17:00 New York)
- 10-16 13:00 GBPJPY BUY: AI DECISION → RISK REJECTED — reward_risk: 1.04 vs minimum 1.2; weekend_carry: held up to 480 min it could still be open at the Friday close (Fri 17:00 New York)
- 10-16 12:45 EURGBP BUY: AI DECISION → RISK REJECTED — cost_to_risk: round-trip cost is 28.4% of the stop (max 25%): spread 0.00012 + commission and slippage
- 10-16 11:30 EURJPY BUY: AI DECISION → RISK APPROVED → PAPER EXECUTED
- 10-16 11:15 EURGBP SELL: AI DECISION → RISK REJECTED — cost_to_risk: round-trip cost is 28.4% of the stop (max 25%): spread 0.00012 + commission and slippage
- 10-16 10:30 EURUSD BUY: AI DECISION → RISK APPROVED → PAPER EXECUTED
- 10-16 10:15 EURUSD BUY: AI DECISION → RISK REJECTED — reward_risk: 0.96 vs minimum 1.2
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

## Latest decisions, NO TRADE included (932 so far)

- 10-16 13:45 EURUSD BUY: BUY EURUSD on M15: AGREE: Trader 1 (nvidia/nemotron-3.5-super-vl:free) BUY 68: Bullish structure is intact with price reclaiming the 1.12511 BOS level from demand; a break below the 1.12435 higher low
- 10-16 13:30 AUDJPY SELL: SELL AUDJPY on M15: AGREE: Trader 1 (nvidia/nemotron-3.5-super-vl:free) SELL 56: Price is at the tested supply order block (109.91–109.958) after a bearish CHoCH at 109.897 and a fresh LL at 109.86, w
- 10-16 13:30 EURCHF SELL: SELL EURCHF on M15: AGREE: Trader 1 (nvidia/nemotron-3.5-super-vl:free) SELL 60: H4 is in a confirmed downtrend while M15's bullish CHoCH at 0.92724 was immediately rejected by bearish high sweeps, tr
- 10-16 13:00 GBPJPY BUY: BUY GBPJPY on M15: AGREE: Trader 1 (nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free) BUY 85: The chart shows a clear bullish structure with price inside the entry zone, strong upward momentum and s
- 10-16 13:00 EURJPY NO_TRADE: Trader 2 (independent) gave no usable answer (TIMEOUT: no answer within 420 s (last: INVALID: no JSON object in the reply)): no decision on one trader alone
- 10-16 12:45 EURGBP BUY: BUY EURGBP on M15: AGREE: Trader 1 (nvidia/nemotron-3.5-super-vl:free) BUY 55: Price is at the lower boundary of multiple timeframe ranges after sweeping lows at 0.84385, favoring a mean-reversion bou
- 10-16 12:45 NZDUSD NO_TRADE: market unavailable for a decision: blocked before consulting the model: EXPOSURE: a NZDUSD position is already open
- 10-16 12:30 USDCHF NO_TRADE: market unavailable for a decision: risk engine: open_positions (3 open, max 3); currency_exposure (2 open positions share a currency, max 2): the model was not consulted
- 10-16 12:30 USDCAD NO_TRADE: market unavailable for a decision: risk engine: open_positions (3 open, max 3); currency_exposure (2 open positions share a currency, max 2): the model was not consulted
- 10-16 12:15 AUDUSD NO_TRADE: market unavailable for a decision: risk engine: open_positions (3 open, max 3); currency_exposure (2 open positions share a currency, max 2): the model was not consulted
- 10-16 12:15 USDJPY NO_TRADE: market unavailable for a decision: risk engine: open_positions (3 open, max 3); currency_exposure (2 open positions share a currency, max 2): the model was not consulted
- 10-16 12:00 GBPUSD NO_TRADE: market unavailable for a decision: risk engine: open_positions (3 open, max 3); currency_exposure (2 open positions share a currency, max 2): the model was not consulted

## Open paper positions

| Symbol | Side | Qty | Entry | Stop | Target | P&L |
|---|---|---|---|---|---|---|
| NZDUSD | BUY | 2.75 | 0.566785 | 0.56525 | 0.569 | $-209.00 |

## Closed paper trades (latest 20)

| Closed | Symbol | Side | Net | R | Costs | Exit | Source | Rule |
|---|---|---|---|---|---|---|---|---|
| 10-16 12:36 | EURJPY | BUY | $-432.45 | -0.87 | $48.70 | STOP | DUAL_AI | AGREE |
| 10-16 12:38 | EURUSD | BUY | $-477.37 | -0.96 | $35.53 | STOP | DUAL_AI | AGREE |
| 10-16 10:25 | EURJPY | BUY | $422.27 | +0.85 | $64.90 | TARGET | DUAL_AI | AGREE |
| 10-16 10:04 | EURUSD | BUY | $459.54 | +0.92 | $53.28 | TARGET | DUAL_AI | AGREE |
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

## Dual AI desk (two free OpenRouter traders; a trade only when they agree)

OpenRouter `READY` · key set · trader 1 `nvidia/nemotron-3.5-super-vl:free` · trader 2 `dots-studio/dots-3-note-preview:free` · debate `nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free` · calls today 34/900

Agreement trades 40 (adequate) · wins 22 · losses 18 · net $2,366.08 · expectancy +0.140R · profit factor 1.37 · old DEBATE rule (stopped in dual-ai-1.2.0): 4 trade(s), net $-1,416.51, removed from the account

Disagreements (not traded; the debate runs in shadow): 58 · the debate's pick if taken: 57 resolved (adequate), expectancy -0.184R · the side it rejected if taken: 62 resolved (adequate), expectancy -0.219R

Exits in shadow (the same trades, followed again; measured, never traded): break-even at +1R +0.147R vs +0.386R as taken (23, insufficient) · held 24 h +0.372R vs +0.296R as taken (14, insufficient) · stop and target twice as far +0.252R vs +0.296R as taken (14, insufficient)

Trades taken by session (UTC): ASIA 19 resolved (insufficient), expectancy +0.279R · LONDON 4 resolved (insufficient), expectancy +0.630R · OVERLAP 8 resolved (insufficient), expectancy -0.382R · NEW_YORK 6 resolved (insufficient), expectancy +0.792R · LATE 3 resolved (insufficient), expectancy -1.106R

| Time | Symbol | Trader 1 | Trader 2 | Debate (shadow) | Rule | Final | Risk |
|---|---|---|---|---|---|---|---|
| 10-16 13:45 | EURUSD | BUY 68 | BUY 65 | - | AGREE | BUY | REJECTED |
| 10-16 13:30 | AUDJPY | SELL 56 | SELL 58 | - | AGREE | SELL | REJECTED |
| 10-16 13:30 | EURCHF | SELL 60 | SELL 65 | - | AGREE | SELL | REJECTED |
| 10-16 13:00 | GBPJPY | BUY 85 | BUY 78 | - | AGREE | BUY | REJECTED |
| 10-16 13:00 | EURJPY | SELL 75 | -  | - | TRADER2_UNAVAILABLE | NO_TRADE | - |
| 10-16 12:45 | EURGBP | BUY 55 | BUY 65 | - | AGREE | BUY | REJECTED |
| 10-16 12:45 | NZDUSD | -  | -  | - | MARKET_UNAVAILABLE | NO_TRADE | - |
| 10-16 12:30 | USDCHF | -  | -  | - | MARKET_UNAVAILABLE | NO_TRADE | - |
| 10-16 12:30 | USDCAD | -  | -  | - | MARKET_UNAVAILABLE | NO_TRADE | - |
| 10-16 12:15 | AUDUSD | -  | -  | - | MARKET_UNAVAILABLE | NO_TRADE | - |
| 10-16 12:15 | USDJPY | -  | -  | - | MARKET_UNAVAILABLE | NO_TRADE | - |
| 10-16 12:00 | GBPUSD | -  | -  | - | MARKET_UNAVAILABLE | NO_TRADE | - |

The chart Trader 1 read last: `last_chart.png`. (numbers): no free vision model answered, so Trader 1 read the same chart from its numbers.

Full figures: `paper_forward.json`. Rules: `docs/PAPER_FORWARD.md` on main.
