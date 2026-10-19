# PAPER FORWARD TEST — NOT REAL MONEY

Updated 2026-10-19 10:09 UTC · mode `PAPER_FORWARD` · profile `PAPER-FORWARD-200K` · shift started 2026-10-19 05:24 UTC · decision system `dual_ai`

Research status (historical, unchanged): **NO EDGE — DO NOT TRADE (historical research; this test measures forward)**. This run measures the system forward; it is not evidence of an edge until it has a sample and the forward-eligibility rules say so.

## The rule that trades: a trade only when both AIs agree

| Trades | Wins | Losses | Win rate | Net P&L | Expectancy | Profit factor | Max drawdown |
|---|---|---|---|---|---|---|---|
| 48 (adequate) | 23 | 25 | 47.9% | $442.02 | +0.010R | 1.05 | $2,833.88 |

The 4 trade(s) of the old DEBATE rule, stopped in dual-ai-1.2.0, were removed from the paper account at the operator's request: their net $-1,416.51 was put back by a declared adjustment ($1,416.51). They stay in the journal (append-only), in none of the account's figures below.

## Paper account

| Account | Equity | P&L today | Total P&L | Drawdown | Open | Trades | Win rate | Expectancy | Profit factor | Risk | Bot |
|---|---|---|---|---|---|---|---|---|---|---|---|
| $200,000.00 | $200,205.08 | $-1,707.55 | $205.08 | $0.00 | 3 | 48 (adequate) | 47.9% | +0.010R | 1.05 | ACTIVE | RUNNING |

Equity includes declared operator adjustments of $1,416.51 (without them: $198,788.56); P&L today excludes them. `remove-retired-debate-rule-trades-2026-10-15`: operator: the 4 trades of the retired debate rule (dual-ai 1.1.0, stopped in 1.2.0) are removed from the paper account; they stay in the journal.

## Last decisions (decision → risk → paper execution)

- 10-19 09:15 EURGBP SELL: AI DECISION → RISK APPROVED → PAPER EXECUTED
- 10-19 09:00 USDCAD SELL: AI DECISION → RISK APPROVED → PAPER EXECUTED
- 10-19 08:45 USDJPY SELL: AI DECISION → RISK APPROVED → PAPER EXECUTED
- 10-19 08:30 EURUSD SELL: AI DECISION → RISK APPROVED → PAPER EXECUTED
- 10-19 08:15 AUDJPY SELL: AI DECISION → RISK REJECTED — cost_to_risk: round-trip cost is 30.3% of the stop (max 25%): spread 0.018 + commission and slippage
- 10-19 08:15 EURCHF SELL: AI DECISION → RISK APPROVED → PAPER EXECUTED
- 10-19 07:45 EURGBP SELL: AI DECISION → RISK REJECTED — reward_risk: 0.62 vs minimum 1.2; currency_conflict: SELL EURGBP would bet against an open position: EURJPY BUY is long EUR
- 10-19 07:45 NZDUSD BUY: AI DECISION → RISK REJECTED — cost_to_risk: round-trip cost is 25.0% of the stop (max 25%): spread 0.00015 + commission and slippage
- 10-19 07:15 AUDUSD BUY: AI DECISION → RISK REJECTED — reward_risk: 1.00 vs minimum 1.2
- 10-19 06:45 AUDJPY SELL: AI DECISION → RISK REJECTED — cost_to_risk: round-trip cost is 27.6% of the stop (max 25%): spread 0.018 + commission and slippage; currency_conflict: SELL AUDJPY would bet against an open position: EURJPY BUY is short JPY
- 10-19 06:30 GBPJPY BUY: AI DECISION → RISK REJECTED — spread: spread is 31.1% of the stop (max 25%); cost_to_risk: round-trip cost is 42.2% of the stop (max 25%): spread 0.025 + commission and slippage; currency_conflict: BUY GBPJPY would bet against an 
- 10-19 04:30 GBPUSD SELL: AI DECISION → RISK APPROVED → PAPER EXECUTED
- 10-19 04:00 GBPJPY BUY: AI DECISION → RISK REJECTED — currency_conflict: BUY GBPJPY would bet against an open position: EURGBP BUY is short GBP
- 10-19 03:45 EURGBP BUY: AI DECISION → RISK APPROVED → PAPER EXECUTED
- 10-19 03:45 NZDUSD BUY: AI DECISION → RISK REJECTED — reward_risk: 1.00 vs minimum 1.2
- 10-19 03:30 USDCHF SELL: AI DECISION → RISK REJECTED — reward_risk: 0.74 vs minimum 1.2
- 10-19 03:15 USDJPY BUY: AI DECISION → RISK REJECTED — currency_conflict: BUY USDJPY would bet against an open position: AUDUSD BUY is short USD
- 10-19 03:00 GBPUSD SELL: AI DECISION → RISK REJECTED — reward_risk: 1.06 vs minimum 1.2; currency_conflict: SELL GBPUSD would bet against an open position: AUDUSD BUY is short USD
- 10-19 01:00 EURJPY BUY: AI DECISION → RISK APPROVED → PAPER EXECUTED
- 10-19 00:45 EURGBP BUY: AI DECISION → RISK REJECTED — reward_risk: 1.02 vs minimum 1.2; currency_conflict: BUY EURGBP would bet against an open position: GBPUSD BUY is long GBP

## Latest decisions, NO TRADE included (1468 so far)

- 10-19 10:00 GBPUSD NO_TRADE: market unavailable for a decision: risk engine: open_positions (3 open, max 3); currency_exposure (2 open positions share a currency, max 2): the model was not consulted
- 10-19 10:00 EURUSD NO_TRADE: market unavailable for a decision: risk engine: open_positions (3 open, max 3); currency_exposure (2 open positions share a currency, max 2): the model was not consulted
- 10-19 09:45 AUDJPY NO_TRADE: market unavailable for a decision: risk engine: open_positions (3 open, max 3): the model was not consulted
- 10-19 09:45 EURCHF NO_TRADE: market unavailable for a decision: risk engine: open_positions (3 open, max 3): the model was not consulted
- 10-19 09:30 GBPJPY NO_TRADE: market unavailable for a decision: risk engine: open_positions (3 open, max 3): the model was not consulted
- 10-19 09:30 EURJPY NO_TRADE: market unavailable for a decision: risk engine: open_positions (3 open, max 3): the model was not consulted
- 10-19 09:15 EURGBP SELL: SELL EURGBP on M15: AGREE: Trader 1 (nvidia/nemotron-3.5-super-vl:free) SELL 68: M15 structure is decisively bearish with consecutive LH/LL and four bearish BOS/CHoCH breaks, while H4 shows a bearish 
- 10-19 09:15 NZDUSD NO_TRADE: market unavailable for a decision: risk engine: currency_exposure (2 open positions share a currency, max 2): the model was not consulted
- 10-19 09:00 USDCHF NO_TRADE: market unavailable for a decision: risk engine: currency_exposure (2 open positions share a currency, max 2): the model was not consulted
- 10-19 09:00 USDCAD SELL: SELL USDCAD on M15: AGREE: Trader 1 (nvidia/nemotron-3.5-super-vl:free) SELL 72: Both timeframes align bearish with LH+LL structure and a confirmed bearish CHoCH at 1.4114. Price is at the bottom of M
- 10-19 08:45 AUDUSD NO_TRADE: the traders disagree (Trader 1 BUY 55, Trader 2 SELL 65): no trade unless both choose the same side; the debate (dots-studio/dots-3-note-preview:free) would have chosen SELL: followed forward in shado
- 10-19 08:45 USDJPY SELL: SELL USDJPY on M15: AGREE: Trader 1 (dots-studio/dots-3-note-preview:free) SELL 65: The double liquidity sweep of the highs at 158.147 near strong resistance (158.188, 6 touches) suggests a bearish re

## Open paper positions

| Symbol | Side | Qty | Entry | Stop | Target | P&L |
|---|---|---|---|---|---|---|
| EURGBP | SELL | 1.29 | 0.84103 | 0.84224 | 0.8396 | $-22.35 |
| USDCAD | SELL | 1.84 | 1.409115 | 1.4106 | 1.4071 | $-20.89 |
| USDJPY | SELL | 2.4 | 158.134 | 158.25 | 157.87 | n/a |

## Closed paper trades (latest 20)

| Closed | Symbol | Side | Net | R | Costs | Exit | Source | Rule |
|---|---|---|---|---|---|---|---|---|
| 10-19 08:42 | EURUSD | SELL | $-202.17 | -0.81 | $34.34 | STOP | DUAL_AI | AGREE |
| 10-19 08:41 | EURCHF | SELL | $-212.36 | -0.86 | $32.82 | STOP | DUAL_AI | AGREE |
| 10-19 07:55 | EURJPY | BUY | $-212.66 | -0.86 | $24.44 | STOP | DUAL_AI | AGREE |
| 10-19 07:01 | GBPUSD | SELL | $-422.19 | -0.85 | $83.37 | STOP | DUAL_AI | AGREE |
| 10-19 06:28 | EURGBP | BUY | $-419.53 | -0.84 | $88.51 | STOP | DUAL_AI | AGREE |
| 10-19 03:31 | AUDUSD | BUY | $200.64 | +0.80 | $41.04 | TARGET | DUAL_AI | AGREE |
| 10-19 02:46 | GBPUSD | BUY | $-202.34 | -0.81 | $36.33 | STOP | DUAL_AI | AGREE |
| 10-16 16:02 | NZDUSD | BUY | $-453.45 | -0.91 | $66.00 | STOP | DUAL_AI | AGREE |
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

## Dual AI desk (two free OpenRouter traders; a trade only when they agree)

OpenRouter `READY` · key set · trader 1 `nvidia/nemotron-3.5-super-vl:free` · trader 2 `nvidia/nemotron-3-ultra-550b-a55b:free` · debate `dots-studio/dots-3-note-preview:free` · calls today 64/900

Agreement trades 48 (adequate) · wins 23 · losses 25 · net $442.02 · expectancy +0.010R · profit factor 1.05 · old DEBATE rule (stopped in dual-ai-1.2.0): 4 trade(s), net $-1,416.51, removed from the account

Disagreements (not traded; the debate runs in shadow): 74 · the debate's pick if taken: 63 resolved (adequate), expectancy -0.148R · the side it rejected if taken: 68 resolved (adequate), expectancy -0.240R

Exits in shadow (the same trades, followed again; measured, never traded): break-even at +1R +0.092R vs +0.237R as taken (31, adequate) · held 24 h +0.512R vs +0.300R as taken (28, insufficient) · stop and target twice as far +0.190R vs +0.300R as taken (28, insufficient)

Trades taken by session (UTC): ASIA 22 resolved (insufficient), expectancy +0.194R · LONDON 9 resolved (insufficient), expectancy +0.225R · OVERLAP 8 resolved (insufficient), expectancy -0.382R · NEW_YORK 6 resolved (insufficient), expectancy +0.792R · LATE 3 resolved (insufficient), expectancy -1.106R

| Time | Symbol | Trader 1 | Trader 2 | Debate (shadow) | Rule | Final | Risk |
|---|---|---|---|---|---|---|---|
| 10-19 10:00 | GBPUSD | -  | -  | - | MARKET_UNAVAILABLE | NO_TRADE | - |
| 10-19 10:00 | EURUSD | -  | -  | - | MARKET_UNAVAILABLE | NO_TRADE | - |
| 10-19 09:45 | AUDJPY | -  | -  | - | MARKET_UNAVAILABLE | NO_TRADE | - |
| 10-19 09:45 | EURCHF | -  | -  | - | MARKET_UNAVAILABLE | NO_TRADE | - |
| 10-19 09:30 | GBPJPY | -  | -  | - | MARKET_UNAVAILABLE | NO_TRADE | - |
| 10-19 09:30 | EURJPY | -  | -  | - | MARKET_UNAVAILABLE | NO_TRADE | - |
| 10-19 09:15 | EURGBP | SELL 68 | SELL 60 | - | AGREE | SELL | APPROVED |
| 10-19 09:15 | NZDUSD | -  | -  | - | MARKET_UNAVAILABLE | NO_TRADE | - |
| 10-19 09:00 | USDCHF | -  | -  | - | MARKET_UNAVAILABLE | NO_TRADE | - |
| 10-19 09:00 | USDCAD | SELL 72 | SELL 68 | - | AGREE | SELL | APPROVED |
| 10-19 08:45 | AUDUSD | BUY 55 | SELL 65 | SELL | DISAGREE | NO_TRADE | - |
| 10-19 08:45 | USDJPY | SELL 65 | SELL 60 | - | AGREE | SELL | APPROVED |

The chart Trader 1 read last: `last_chart.png`. (numbers): no free vision model answered, so Trader 1 read the same chart from its numbers.

Full figures: `paper_forward.json`. Rules: `docs/PAPER_FORWARD.md` on main.
