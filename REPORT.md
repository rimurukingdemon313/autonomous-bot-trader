# PAPER FORWARD TEST — NOT REAL MONEY

Updated 2026-10-27 09:03 UTC · mode `PAPER_FORWARD` · profile `PAPER-FORWARD-200K` · shift started 2026-10-27 03:33 UTC · decision system `dual_ai`

Research status (historical, unchanged): **NO EDGE — DO NOT TRADE (historical research; this test measures forward)**. This run measures the system forward; it is not evidence of an edge until it has a sample and the forward-eligibility rules say so.

## The rule that trades: a trade only when both AIs agree

| Trades | Wins | Losses | Win rate | Net P&L | Expectancy | Profit factor | Max drawdown |
|---|---|---|---|---|---|---|---|
| 111 (adequate) | 46 | 65 | 41.4% | $-3,663.13 | -0.087R | 0.83 | $7,377.98 |

The 4 trade(s) of the old DEBATE rule, stopped in dual-ai-1.2.0, were removed from the paper account at the operator's request: their net $-1,416.51 was put back by a declared adjustment ($1,416.51). They stay in the journal (append-only), in none of the account's figures below.

## Paper account

| Account | Equity | P&L today | Total P&L | Drawdown | Open | Trades | Win rate | Expectancy | Profit factor | Risk | Bot |
|---|---|---|---|---|---|---|---|---|---|---|---|
| $200,000.00 | $196,265.86 | $-184.05 | $-3,734.14 | $-3,734.14 | 2 | 111 (adequate) | 41.4% | -0.087R | 0.83 | ACTIVE | RUNNING |

Equity includes declared operator adjustments of $1,416.51 (without them: $194,849.34); P&L today excludes them. `remove-retired-debate-rule-trades-2026-10-15`: operator: the 4 trades of the retired debate rule (dual-ai 1.1.0, stopped in 1.2.0) are removed from the paper account; they stay in the journal.

## Who lost it: the market or us

Losses 65, $-21,482.55: **the market 65** (at the stop, within the plan 59, by the time exit 5, stopped beyond the plan (a gap or the spread at the stop) 1) · **us 0**. Every closed trade is checked: the rules and the gate approved it, its data and the fill's quote were fresh, it was sized within the per-trade risk, both traders chose its side, it closed on time and not over a weekend, its costs were as planned. A check that cannot be read counts as ours.

Beyond the plan, the market's: 10-21 21:05 GBPJPY BUY lost $644.82 against a planned $498.95 in the rollover.

The 4 trade(s) taken out of the account, checked the same way: 4 ours (DESK: not both traders' choice (rule DEBATE, traders ['BUY', 'SELL'])).

## Last decisions (decision → risk → paper execution)

- 10-27 09:00 NZDUSD SELL: AI DECISION → RISK REJECTED — reward_risk: 0.91 vs minimum 1.2; structure: H1 structure is range (mixed swings): no new position without a clear H1 trend (up HH+HL or down LH+LL)
- 10-27 07:00 USDJPY BUY: AI DECISION → RISK APPROVED → PAPER EXECUTED
- 10-27 06:45 EURUSD SELL: AI DECISION → RISK APPROVED → PAPER EXECUTED
- 10-27 06:30 AUDJPY BUY: AI DECISION → RISK REJECTED — structure: H1 structure is range (mixed swings): no new position without a clear H1 trend (up HH+HL or down LH+LL)
- 10-27 05:30 USDJPY SELL: AI DECISION → RISK APPROVED → PAPER EXECUTED
- 10-27 02:00 EURJPY SELL: AI DECISION → RISK APPROVED → PAPER EXECUTED
- 10-27 01:46 EURGBP SELL: AI DECISION → RISK REJECTED — currency_conflict: SELL EURGBP would bet against an open position: GBPUSD SELL is short GBP
- 10-27 01:32 USDCHF SELL: AI DECISION → RISK REJECTED — currency_conflict: SELL USDCHF would bet against an open position: GBPUSD SELL is long USD
- 10-26 17:45 AUDJPY SELL: AI DECISION → RISK APPROVED → PAPER EXECUTED
- 10-26 17:45 EURCHF SELL: AI DECISION → RISK APPROVED → PAPER EXECUTED
- 10-26 17:30 GBPJPY SELL: AI DECISION → RISK REJECTED — structure: H1 structure is range (mixed swings): no new position without a clear H1 trend (up HH+HL or down LH+LL)
- 10-26 17:30 EURJPY SELL: AI DECISION → RISK REJECTED — structure: H1 structure is range (mixed swings): no new position without a clear H1 trend (up HH+HL or down LH+LL)
- 10-26 17:15 EURGBP SELL: AI DECISION → RISK REJECTED — currency_conflict: SELL EURGBP would bet against an open position: GBPUSD SELL is short GBP; structure: H1 structure is range (mixed swings): no new position without a clear H1 trend (up HH+HL or down
- 10-26 16:32 GBPUSD SELL: AI DECISION → RISK APPROVED → PAPER EXECUTED
- 10-26 16:30 EURUSD SELL: AI DECISION → RISK REJECTED — structure: H1 structure is range (mixed swings): no new position without a clear H1 trend (up HH+HL or down LH+LL)
- 10-26 16:02 USDCHF BUY: AI DECISION → RISK APPROVED → PAPER EXECUTED
- 10-26 16:00 USDCAD SELL: AI DECISION → RISK REJECTED — reward_risk: 0.97 vs minimum 1.2; structure: H1 structure is range (mixed swings): no new position without a clear H1 trend (up HH+HL or down LH+LL)
- 10-26 11:48 EURGBP BUY: AI DECISION → RISK APPROVED → PAPER EXECUTED
- 10-26 11:45 NZDUSD SELL: AI DECISION → RISK REJECTED — cost_to_risk: round-trip cost is 31.0% of the stop (max 25%): spread 0.00015 + commission and slippage; currency_conflict: SELL NZDUSD would bet against an open position: USDCAD SELL is short USD
- 10-26 11:30 USDCHF BUY: AI DECISION → RISK REJECTED — currency_conflict: BUY USDCHF would bet against an open position: USDCAD SELL is short USD

## Latest decisions, NO TRADE included (2964 so far)

- 10-27 09:01 EURGBP NO_TRADE: the traders disagree (Trader 1 BUY 56, Trader 2 SELL 52): no trade unless both choose the same side; the debate (dots-studio/dots-3-note-preview:free) would have chosen BUY: followed forward in shadow
- 10-27 09:00 NZDUSD SELL: SELL NZDUSD on M15: AGREE: Trader 1 (xiaomi/mimo-v2.6-pro) SELL 55: Sell the retest of the tested supply OB inside the entry zone against the M15 downtrend. Stop above the open bearish FVG high and th
- 10-27 08:45 USDCHF NO_TRADE: risk engine: open_positions (3 open, max 3); currency_exposure (2 open positions share a currency, max 2): the model was not consulted
- 10-27 08:45 USDCAD NO_TRADE: risk engine: open_positions (3 open, max 3); currency_exposure (2 open positions share a currency, max 2): the model was not consulted
- 10-27 08:30 AUDUSD NO_TRADE: risk engine: open_positions (3 open, max 3); currency_exposure (2 open positions share a currency, max 2): the model was not consulted
- 10-27 08:30 USDJPY NO_TRADE: blocked before consulting the model: EXPOSURE: a USDJPY position is already open
- 10-27 08:15 GBPUSD NO_TRADE: risk engine: open_positions (3 open, max 3); currency_exposure (2 open positions share a currency, max 2): the model was not consulted
- 10-27 08:15 EURUSD NO_TRADE: blocked before consulting the model: EXPOSURE: a EURUSD position is already open
- 10-27 08:00 AUDJPY NO_TRADE: risk engine: open_positions (3 open, max 3): the model was not consulted
- 10-27 08:00 EURCHF NO_TRADE: blocked before consulting the model: EXPOSURE: a EURCHF position is already open
- 10-27 07:45 GBPJPY NO_TRADE: risk engine: open_positions (3 open, max 3): the model was not consulted
- 10-27 07:45 EURJPY NO_TRADE: risk engine: open_positions (3 open, max 3); currency_exposure (2 open positions share a currency, max 2): the model was not consulted

## Open paper positions

| Symbol | Side | Qty | Entry | Stop | Target | P&L |
|---|---|---|---|---|---|---|
| USDJPY | BUY | 2.37 | 157.825 | 157.543 | 158.254 | $-156.78 |
| EURCHF | SELL | 0.64 | 0.9251 | 0.92635 | 0.92293 | $85.76 |

## Closed paper trades (latest 20)

| Closed | Symbol | Side | Net | R | Costs | Exit | Source | Rule | Lost to |
|---|---|---|---|---|---|---|---|---|---|
| 10-27 08:51 | EURUSD | SELL | $438.96 | +0.90 | $59.52 | TARGET | DUAL_AI | AGREE | - |
| 10-27 06:30 | EURJPY | SELL | $-98.35 | -0.81 | $17.00 | STOP | DUAL_AI | AGREE | the market |
| 10-27 06:15 | USDJPY | SELL | $-418.51 | -0.85 | $50.09 | STOP | DUAL_AI | AGREE | the market |
| 10-27 05:23 | GBPUSD | SELL | $278.49 | +1.14 | $38.75 | TARGET | DUAL_AI | AGREE | - |
| 10-27 01:27 | AUDJPY | SELL | $-104.31 | -0.86 | $25.69 | STOP | DUAL_AI | AGREE | the market |
| 10-26 17:23 | USDCHF | BUY | $-207.12 | -0.85 | $38.59 | STOP | DUAL_AI | AGREE | the market |
| 10-26 13:06 | USDCAD | SELL | $-407.76 | -0.82 | $73.23 | STOP | DUAL_AI | AGREE | the market |
| 10-26 12:54 | EURGBP | BUY | $-420.89 | -0.85 | $86.86 | STOP | DUAL_AI | AGREE | the market |
| 10-26 12:55 | EURCHF | BUY | $-410.98 | -0.83 | $77.46 | STOP | DUAL_AI | AGREE | the market |
| 10-26 10:45 | GBPJPY | SELL | $-395.13 | -0.80 | $70.90 | STOP | DUAL_AI | AGREE | the market |
| 10-26 09:11 | AUDUSD | SELL | $-473.61 | -0.96 | $80.56 | STOP | DUAL_AI | AGREE | the market |
| 10-26 07:44 | USDCHF | BUY | $582.71 | +1.18 | $82.56 | TARGET | DUAL_AI | AGREE | - |
| 10-23 20:03 | EURUSD | SELL | $37.41 | +0.31 | $14.79 | TIME | DUAL_AI | AGREE | - |
| 10-23 20:02 | GBPUSD | SELL | $33.15 | +0.27 | $17.85 | TIME | DUAL_AI | AGREE | - |
| 10-23 12:36 | GBPJPY | SELL | $220.25 | +1.80 | $20.57 | TARGET | DUAL_AI | AGREE | - |
| 10-23 10:06 | EURUSD | SELL | $-102.94 | -0.84 | $15.30 | STOP | DUAL_AI | AGREE | the market |
| 10-23 07:01 | EURGBP | SELL | $-207.52 | -0.84 | $43.74 | STOP | DUAL_AI | AGREE | the market |
| 10-23 06:46 | USDCHF | SELL | $-417.00 | -0.84 | $61.13 | STOP | DUAL_AI | AGREE | the market |
| 10-23 06:22 | EURJPY | SELL | $-171.48 | -0.70 | $37.01 | STOP | DUAL_AI | AGREE | the market |
| 10-23 02:42 | EURCHF | SELL | $-402.83 | -0.81 | $81.83 | STOP | DUAL_AI | AGREE | the market |

## Dual AI desk (two OpenRouter traders: free, or the paid trial while it runs; a trade only when they agree)

OpenRouter `READY` · key set · trader 1 `nvidia/nemotron-3.5-super-vl:free` · trader 2 `thinkingmachines/inkling-small:free` · debate `google/gemma-4-26b-a4b-it:free` · calls today 26/900

Paid trial `paid-trial-2026-10-26` (2026-10-23T14:00:00Z to 2026-10-31T00:00:00Z): ACTIVE · trader 1 `xiaomi/mimo-v2.6-pro` asked first · trader 2 `anthropic/claude-haiku-5.5` asked first · spent $0.34 of $9.00, today $0.10 of $1.80 (the key's own reading)

Agreement trades 111 (adequate) · wins 46 · losses 65 · net $-3,663.13 · expectancy -0.087R · profit factor 0.83 · old DEBATE rule (stopped in dual-ai-1.2.0): 4 trade(s), net $-1,416.51, removed from the account

Disagreements (not traded; the debate runs in shadow): 123 · the debate's pick if taken: 112 resolved (adequate), expectancy -0.145R · the side it rejected if taken: 117 resolved (adequate), expectancy -0.221R

Exits in shadow (the same trades, followed again; measured, never traded): break-even at +1R -0.122R vs -0.082R as taken (90, adequate) · held 24 h +0.001R vs -0.082R as taken (90, adequate) · stop and target twice as far +0.009R vs -0.082R as taken (90, adequate) · closed at 8 h (the exit before dual-ai 1.7.0) -0.178R vs -0.228R as taken (36, adequate)

Trader 2's own levels in shadow (a trade is on Trader 1's since dual-ai 1.10.0; measured, never traded): +0.208R vs +0.154R as taken (2, insufficient)

Trades taken by session (UTC): ASIA 48 resolved (adequate), expectancy -0.209R · LONDON 31 resolved (adequate), expectancy +0.124R · OVERLAP 8 resolved (insufficient), expectancy -0.382R · NEW_YORK 17 resolved (insufficient), expectancy +0.147R · LATE 3 resolved (insufficient), expectancy -1.106R

| Time | Symbol | Trader 1 | Trader 2 | Debate (shadow) | Rule | Final | Risk |
|---|---|---|---|---|---|---|---|
| 10-27 09:01 | EURGBP | BUY 56 | SELL 52 | BUY | DISAGREE | NO_TRADE | - |
| 10-27 09:00 | NZDUSD | SELL 55 | SELL 50 | - | AGREE | SELL | REJECTED |
| 10-27 08:45 | USDCHF | -  | -  | - | NOT_ASKED | NO_TRADE | - |
| 10-27 08:45 | USDCAD | -  | -  | - | NOT_ASKED | NO_TRADE | - |
| 10-27 08:30 | AUDUSD | -  | -  | - | NOT_ASKED | NO_TRADE | - |
| 10-27 08:30 | USDJPY | -  | -  | - | NOT_ASKED | NO_TRADE | - |
| 10-27 08:15 | GBPUSD | -  | -  | - | NOT_ASKED | NO_TRADE | - |
| 10-27 08:15 | EURUSD | -  | -  | - | NOT_ASKED | NO_TRADE | - |
| 10-27 08:00 | AUDJPY | -  | -  | - | NOT_ASKED | NO_TRADE | - |
| 10-27 08:00 | EURCHF | -  | -  | - | NOT_ASKED | NO_TRADE | - |
| 10-27 07:45 | GBPJPY | -  | -  | - | NOT_ASKED | NO_TRADE | - |
| 10-27 07:45 | EURJPY | -  | -  | - | NOT_ASKED | NO_TRADE | - |

The chart Trader 1 read last: `last_chart.png`. (numbers): no free vision model answered, so Trader 1 read the same chart from its numbers.

Full figures: `paper_forward.json`. Rules: `docs/PAPER_FORWARD.md` on main.
