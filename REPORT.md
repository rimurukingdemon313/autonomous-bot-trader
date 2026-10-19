# PAPER FORWARD TEST — NOT REAL MONEY

Updated 2026-10-19 18:05 UTC · mode `PAPER_FORWARD` · profile `PAPER-FORWARD-200K` · shift started 2026-10-19 16:35 UTC · decision system `dual_ai`

Research status (historical, unchanged): **NO EDGE — DO NOT TRADE (historical research; this test measures forward)**. This run measures the system forward; it is not evidence of an edge until it has a sample and the forward-eligibility rules say so.

## The rule that trades: a trade only when both AIs agree

| Trades | Wins | Losses | Win rate | Net P&L | Expectancy | Profit factor | Max drawdown |
|---|---|---|---|---|---|---|---|
| 52 (adequate) | 24 | 28 | 46.2% | $178.21 | -0.019R | 1.02 | $3,097.68 |

The 4 trade(s) of the old DEBATE rule, stopped in dual-ai-1.2.0, were removed from the paper account at the operator's request: their net $-1,416.51 was put back by a declared adjustment ($1,416.51). They stay in the journal (append-only), in none of the account's figures below.

## Paper account

| Account | Equity | P&L today | Total P&L | Drawdown | Open | Trades | Win rate | Expectancy | Profit factor | Risk | Bot |
|---|---|---|---|---|---|---|---|---|---|---|---|
| $200,000.00 | $200,308.52 | $-1,604.11 | $308.52 | $0.00 | 2 | 52 (adequate) | 46.2% | -0.019R | 1.02 | ACTIVE | RUNNING |

Equity includes declared operator adjustments of $1,416.51 (without them: $198,892.00); P&L today excludes them. `remove-retired-debate-rule-trades-2026-10-15`: operator: the 4 trades of the retired debate rule (dual-ai 1.1.0, stopped in 1.2.0) are removed from the paper account; they stay in the journal.

## Last decisions (decision → risk → paper execution)

- 10-19 17:15 USDCAD SELL: AI DECISION → RISK APPROVED → PAPER EXECUTED
- 10-19 17:06 AUDUSD SELL: AI DECISION → RISK REJECTED — currency_conflict: SELL AUDUSD would bet against an open position: USDCHF SELL is short USD
- 10-19 16:53 GBPUSD SELL: AI DECISION → RISK REJECTED — currency_conflict: SELL GBPUSD would bet against an open position: USDCHF SELL is short USD; structure: H1 structure is range (mixed swings): no new position without a clear H1 trend (up HH+HL or down
- 10-19 16:15 EURGBP SELL: AI DECISION → RISK REJECTED — cost_to_risk: round-trip cost is 28.4% of the stop (max 25%): spread 0.00012 + commission and slippage
- 10-19 16:15 NZDUSD SELL: AI DECISION → RISK REJECTED — currency_conflict: SELL NZDUSD would bet against an open position: USDCHF SELL is short USD
- 10-19 16:00 USDCHF SELL: AI DECISION → RISK APPROVED → PAPER EXECUTED
- 10-19 16:00 USDCAD SELL: AI DECISION → RISK REJECTED — cost_to_risk: round-trip cost is 27.4% of the stop (max 25%): spread 0.00015 + commission and slippage
- 10-19 11:45 NZDUSD BUY: AI DECISION → RISK REJECTED — reward_risk: 1.18 vs minimum 1.2
- 10-19 10:30 USDCHF SELL: AI DECISION → RISK APPROVED → PAPER EXECUTED
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

## Latest decisions, NO TRADE included (1529 so far)

- 10-19 18:00 EURCHF NO_TRADE: the traders disagree (Trader 1 BUY 60, Trader 2 SELL 65): no trade unless both choose the same side; the debate (dots-studio/dots-3-note-preview:free) would have chosen SELL: followed forward in shado
- 10-19 17:49 GBPJPY NO_TRADE: the traders disagree (Trader 1 SELL 68, Trader 2 BUY 62): no trade unless both choose the same side; the debate (minimax/minimax-m3.1-flash:free) would have chosen SELL: followed forward in shadow, no
- 10-19 17:45 EURJPY NO_TRADE: the traders disagree (Trader 1 BUY 65, Trader 2 SELL 58): no trade unless both choose the same side; the debate (dots-studio/dots-3-note-preview:free) would have chosen SELL: followed forward in shado
- 10-19 17:30 EURGBP NO_TRADE: the traders disagree (Trader 1 BUY 60, Trader 2 SELL 55): no trade unless both choose the same side; the debate (dots-studio/dots-3-note-preview:free) would have chosen SELL: followed forward in shado
- 10-19 17:30 NZDUSD NO_TRADE: market unavailable for a decision: risk engine: currency_exposure (2 open positions share a currency, max 2): the model was not consulted
- 10-19 17:17 USDCHF NO_TRADE: market unavailable for a decision: blocked before consulting the model: EXPOSURE: a USDCHF position is already open
- 10-19 17:15 USDCAD SELL: SELL USDCAD on M15: AGREE: Trader 1 (nvidia/nemotron-3.5-super-vl:free) SELL 67: Both M15 and H4 are trending down with confirmed LH+LL structure, and the most recent structure break is a bearish BOS 
- 10-19 17:06 AUDUSD SELL: SELL AUDUSD on M15: AGREE: Trader 1 (nvidia/nemotron-3.5-super-vl:free) SELL 64: M15 printed a bearish BOS at 0.69823 and a 3-bar-ago LL at 0.69779, with price now below that low. An untested supply O
- 10-19 17:00 USDJPY NO_TRADE: the traders disagree (Trader 1 BUY 60, Trader 2 SELL 55): no trade unless both choose the same side; the debate (dots-studio/dots-3-note-preview:free) would have chosen SELL: followed forward in shado
- 10-19 16:53 GBPUSD SELL: SELL GBPUSD on M15: AGREE: Trader 1 (nvidia/nemotron-3.5-super-vl:free) SELL 65: M15 structure is bearish with a fresh LL and consecutive bearish BOS breaks. The untested supply order block at 1.33117
- 10-19 16:45 EURUSD NO_TRADE: the traders disagree (Trader 1 BUY 60, Trader 2 SELL 65): no trade unless both choose the same side; the debate (dots-studio/dots-3-note-preview:free) would have chosen BUY: followed forward in shadow
- 10-19 16:15 EURGBP SELL: SELL EURGBP on M15: AGREE: Trader 1 (nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free) SELL 68: The higher timeframe H4 is bearish with a recent bearish BOS and lower highs, and the M15 chart shows 

## Open paper positions

| Symbol | Side | Qty | Entry | Stop | Target | P&L |
|---|---|---|---|---|---|---|
| USDCAD | SELL | 4.6 | 1.4093149999999999 | 1.4104 | 1.4075 | $-182.72 |
| USDCHF | SELL | 2.75 | 0.826815 | 0.828 | 0.82399 | $313.02 |

## Closed paper trades (latest 20)

| Closed | Symbol | Side | Net | R | Costs | Exit | Source | Rule |
|---|---|---|---|---|---|---|---|---|
| 10-19 12:49 | EURGBP | SELL | $-218.72 | -0.88 | $33.09 | STOP | DUAL_AI | AGREE |
| 10-19 12:37 | USDCHF | SELL | $-101.96 | -0.82 | $19.31 | STOP | DUAL_AI | AGREE |
| 10-19 11:44 | USDCAD | SELL | $250.58 | +1.00 | $33.80 | TARGET | DUAL_AI | AGREE |
| 10-19 10:05 | USDJPY | SELL | $-193.70 | -0.78 | $34.94 | STOP | DUAL_AI | AGREE |
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

## Dual AI desk (two free OpenRouter traders; a trade only when they agree)

OpenRouter `READY` · key set · trader 1 `nvidia/nemotron-3.5-super-vl:free` · trader 2 `nvidia/nemotron-3-ultra-550b-a55b:free` · debate `dots-studio/dots-3-note-preview:free` · calls today 38/900

Agreement trades 52 (adequate) · wins 24 · losses 28 · net $178.21 · expectancy -0.019R · profit factor 1.02 · old DEBATE rule (stopped in dual-ai-1.2.0): 4 trade(s), net $-1,416.51, removed from the account

Disagreements (not traded; the debate runs in shadow): 82 · the debate's pick if taken: 70 resolved (adequate), expectancy -0.182R · the side it rejected if taken: 75 resolved (adequate), expectancy -0.195R

Exits in shadow (the same trades, followed again; measured, never traded): break-even at +1R -0.068R vs +0.050R as taken (38, adequate) · held 24 h +0.512R vs +0.300R as taken (28, insufficient) · stop and target twice as far +0.190R vs +0.300R as taken (28, insufficient)

Trades taken by session (UTC): ASIA 24 resolved (insufficient), expectancy +0.083R · LONDON 14 resolved (insufficient), expectancy -0.082R · OVERLAP 8 resolved (insufficient), expectancy -0.382R · NEW_YORK 6 resolved (insufficient), expectancy +0.792R · LATE 3 resolved (insufficient), expectancy -1.106R

| Time | Symbol | Trader 1 | Trader 2 | Debate (shadow) | Rule | Final | Risk |
|---|---|---|---|---|---|---|---|
| 10-19 18:00 | EURCHF | BUY 60 | SELL 65 | SELL | DISAGREE | NO_TRADE | - |
| 10-19 17:49 | GBPJPY | SELL 68 | BUY 62 | SELL | DISAGREE | NO_TRADE | - |
| 10-19 17:45 | EURJPY | BUY 65 | SELL 58 | SELL | DISAGREE | NO_TRADE | - |
| 10-19 17:30 | EURGBP | BUY 60 | SELL 55 | SELL | DISAGREE | NO_TRADE | - |
| 10-19 17:30 | NZDUSD | -  | -  | - | MARKET_UNAVAILABLE | NO_TRADE | - |
| 10-19 17:17 | USDCHF | -  | -  | - | MARKET_UNAVAILABLE | NO_TRADE | - |
| 10-19 17:15 | USDCAD | SELL 67 | SELL 70 | - | AGREE | SELL | APPROVED |
| 10-19 17:06 | AUDUSD | SELL 64 | SELL 70 | - | AGREE | SELL | REJECTED |
| 10-19 17:00 | USDJPY | BUY 60 | SELL 55 | SELL | DISAGREE | NO_TRADE | - |
| 10-19 16:53 | GBPUSD | SELL 65 | SELL 65 | - | AGREE | SELL | REJECTED |
| 10-19 16:45 | EURUSD | BUY 60 | SELL 65 | BUY | DISAGREE | NO_TRADE | - |
| 10-19 16:15 | EURGBP | SELL 68 | SELL 70 | - | AGREE | SELL | REJECTED |

The chart Trader 1 read last: `last_chart.png`. (numbers): no free vision model answered, so Trader 1 read the same chart from its numbers.

Full figures: `paper_forward.json`. Rules: `docs/PAPER_FORWARD.md` on main.
