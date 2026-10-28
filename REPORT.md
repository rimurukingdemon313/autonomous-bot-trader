# PAPER FORWARD TEST — NOT REAL MONEY

Updated 2026-10-28 01:05 UTC · mode `PAPER_FORWARD` · profile `PAPER-FORWARD-200K` · shift started 2026-10-27 20:19 UTC · decision system `dual_ai`

Research status (historical, unchanged): **NO EDGE — DO NOT TRADE (historical research; this test measures forward)**. This run measures the system forward; it is not evidence of an edge until it has a sample and the forward-eligibility rules say so.

## The new account: the setup trading now (from 2026-10-26 16:22 UTC)

dual-ai 1.10.0 (a trade on Trader 1's levels) with both traders paid (paid-trial 1.2.0: Trader 1 xiaomi/mimo-v2.6-pro, Trader 2 anthropic/claude-haiku-5.5). Opened at the owner's request (2026-10-27): owner: a new account for the new setup, from the first shift that ran it; the account before it is kept and reported apart.

| Start | Equity | Total P&L | Closed | Open | Trades | Win rate | Expectancy | Profit factor |
|---|---|---|---|---|---|---|---|---|
| $200,000.00 | $200,949.22 | $949.22 | $254.92 | 3 ($694.30) | 6 (insufficient) | 50.0% | +0.138R | 1.41 |

Before it, kept and apart (not in the figures above): 106 trades, net $-3,759.41. The whole paper journal, which the hard gate and the risk engine still guard, is under Paper account below; nothing in it was moved or removed.

## The rule that trades: a trade only when both AIs agree

| Trades | Wins | Losses | Win rate | Net P&L | Expectancy | Profit factor | Max drawdown |
|---|---|---|---|---|---|---|---|
| 112 (adequate) | 47 | 65 | 42.0% | $-3,504.49 | -0.075R | 0.84 | $7,377.98 |

The 4 trade(s) of the old DEBATE rule, stopped in dual-ai-1.2.0, were removed from the paper account at the operator's request: their net $-1,416.51 was put back by a declared adjustment ($1,416.51). They stay in the journal (append-only), in none of the account's figures below.

## Paper account

| Account | Equity | P&L today | Total P&L | Drawdown | Open | Trades | Win rate | Expectancy | Profit factor | Risk | Bot |
|---|---|---|---|---|---|---|---|---|---|---|---|
| $200,000.00 | $197,189.82 | $269.36 | $-2,810.18 | $-2,810.18 | 3 | 112 (adequate) | 42.0% | -0.075R | 0.84 | ACTIVE | RUNNING |

Equity includes declared operator adjustments of $1,416.51 (without them: $195,773.30); P&L today excludes them. `remove-retired-debate-rule-trades-2026-10-15`: operator: the 4 trades of the retired debate rule (dual-ai 1.1.0, stopped in 1.2.0) are removed from the paper account; they stay in the journal.

## Who lost it: the market or us

Losses 65, $-21,482.55: **the market 65** (at the stop, within the plan 59, by the time exit 5, stopped beyond the plan (a gap or the spread at the stop) 1) · **us 0**. Every closed trade is checked: the rules and the gate approved it, its data and the fill's quote were fresh, it was sized within the per-trade risk, both traders chose its side, it closed on time and not over a weekend, its costs were as planned. A check that cannot be read counts as ours.

Beyond the plan, the market's: 10-21 21:05 GBPJPY BUY lost $644.82 against a planned $498.95 in the rollover.

The 4 trade(s) taken out of the account, checked the same way: 4 ours (DESK: not both traders' choice (rule DEBATE, traders ['BUY', 'SELL'])).

## Last decisions (decision → risk → paper execution)

- 10-27 10:00 EURGBP SELL: AI DECISION → RISK APPROVED → PAPER EXECUTED
- 10-27 09:15 EURUSD SELL: AI DECISION → RISK APPROVED → PAPER EXECUTED
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

## Latest decisions, NO TRADE included (3092 so far)

- 10-28 01:00 GBPUSD NO_TRADE: risk engine: open_positions (3 open, max 3); currency_exposure (2 open positions share a currency, max 2); gate_open_risk (the hard risk gate's open-risk room 17.62 is less than the next trade's risk 
- 10-28 01:00 EURUSD NO_TRADE: blocked before consulting the model: EXPOSURE: a EURUSD position is already open
- 10-28 00:45 AUDJPY NO_TRADE: risk engine: news (High-impact release AUD CPI m/m 16 min ago; High-impact release AUD CPI y/y 16 min ago; High-impact release AUD Trimmed Mean CPI m/m 16 min ago: no new position from 30 min before t
- 10-28 00:45 EURCHF NO_TRADE: risk engine: open_positions (3 open, max 3); currency_exposure (2 open positions share a currency, max 2); gate_open_risk (the hard risk gate's open-risk room 27.66 is less than the next trade's risk 
- 10-28 00:30 GBPJPY NO_TRADE: risk engine: open_positions (3 open, max 3); gate_open_risk (the hard risk gate's open-risk room 78.21 is less than the next trade's risk 492.45: it would refuse the trade): the model was not consulte
- 10-28 00:30 EURJPY NO_TRADE: risk engine: open_positions (3 open, max 3); currency_exposure (2 open positions share a currency, max 2); gate_open_risk (the hard risk gate's open-risk room 78.21 is less than the next trade's risk 
- 10-28 00:15 EURGBP NO_TRADE: blocked before consulting the model: EXPOSURE: a EURGBP position is already open
- 10-28 00:15 NZDUSD NO_TRADE: risk engine: open_positions (3 open, max 3); currency_exposure (2 open positions share a currency, max 2); gate_open_risk (the hard risk gate's open-risk room 111.39 is less than the next trade's risk
- 10-28 00:00 USDCHF NO_TRADE: risk engine: open_positions (3 open, max 3); currency_exposure (2 open positions share a currency, max 2); gate_open_risk (the hard risk gate's open-risk room -128.95 is less than the next trade's ris
- 10-28 00:00 USDCAD NO_TRADE: risk engine: open_positions (3 open, max 3); currency_exposure (2 open positions share a currency, max 2); gate_open_risk (the hard risk gate's open-risk room -128.95 is less than the next trade's ris
- 10-27 23:45 AUDUSD NO_TRADE: risk engine: quiet_hours (19:45 New York: no new position from 16:00 to 20:00 New York (the rollover to the Tokyo open: the thinnest liquidity of the day)); news (Medium-impact release AUD RBA Gov Bul
- 10-27 23:45 USDJPY NO_TRADE: blocked before consulting the model: EXPOSURE: a USDJPY position is already open

## Open paper positions

| Symbol | Side | Qty | Entry | Stop | Target | P&L |
|---|---|---|---|---|---|---|
| EURGBP | SELL | 2.75 | 0.8365300000000001 | 0.83765 | 0.8352 | $98.75 |
| EURUSD | SELL | 2.08 | 1.11475 | 1.11682 | 1.11207 | $459.68 |
| USDJPY | BUY | 2.37 | 157.825 | 157.543 | 158.254 | $135.87 |

## Closed paper trades (latest 20)

| Closed | Symbol | Side | Net | R | Costs | Exit | Source | Rule | Lost to |
|---|---|---|---|---|---|---|---|---|---|
| 10-27 09:39 | EURCHF | SELL | $158.64 | +1.30 | $23.59 | TARGET | DUAL_AI | AGREE | - |
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

## Dual AI desk (two OpenRouter traders: free, or the paid trial while it runs; a trade only when they agree)

OpenRouter `CATALOG_NOT_READ_YET` · key set · trader 1 `None` · trader 2 `None` · debate `None` · calls today 0/900

Paid trial `paid-trial-2026-10-26` (2026-10-23T14:00:00Z to 2026-10-31T00:00:00Z): ACTIVE · trader 1 `xiaomi/mimo-v2.6-pro` asked first · trader 2 `anthropic/claude-haiku-5.5` asked first · spent n/a of $9.00, today n/a of $1.80 (the key's own reading)

Agreement trades 112 (adequate) · wins 47 · losses 65 · net $-3,504.49 · expectancy -0.075R · profit factor 0.84 · old DEBATE rule (stopped in dual-ai-1.2.0): 4 trade(s), net $-1,416.51, removed from the account

Disagreements (not traded; the debate runs in shadow): 123 · the debate's pick if taken: 115 resolved (adequate), expectancy -0.150R · the side it rejected if taken: 120 resolved (adequate), expectancy -0.215R

Exits in shadow (the same trades, followed again; measured, never traded): break-even at +1R -0.134R vs -0.089R as taken (96, adequate) · held 24 h -0.011R vs -0.089R as taken (96, adequate) · stop and target twice as far +0.003R vs -0.089R as taken (96, adequate) · closed at 8 h (the exit before dual-ai 1.7.0) -0.244R vs -0.222R as taken (42, adequate)

Trader 2's own levels in shadow (a trade is on Trader 1's since dual-ai 1.10.0; measured, never traded): +1.073R vs +0.482R as taken (5, insufficient)

Trades taken by session (UTC): ASIA 48 resolved (adequate), expectancy -0.209R · LONDON 33 resolved (adequate), expectancy +0.051R · OVERLAP 8 resolved (insufficient), expectancy -0.382R · NEW_YORK 21 resolved (insufficient), expectancy +0.168R · LATE 3 resolved (insufficient), expectancy -1.106R

| Time | Symbol | Trader 1 | Trader 2 | Debate (shadow) | Rule | Final | Risk |
|---|---|---|---|---|---|---|---|
| 10-28 01:00 | GBPUSD | -  | -  | - | NOT_ASKED | NO_TRADE | - |
| 10-28 01:00 | EURUSD | -  | -  | - | NOT_ASKED | NO_TRADE | - |
| 10-28 00:45 | AUDJPY | -  | -  | - | NOT_ASKED | NO_TRADE | - |
| 10-28 00:45 | EURCHF | -  | -  | - | NOT_ASKED | NO_TRADE | - |
| 10-28 00:30 | GBPJPY | -  | -  | - | NOT_ASKED | NO_TRADE | - |
| 10-28 00:30 | EURJPY | -  | -  | - | NOT_ASKED | NO_TRADE | - |
| 10-28 00:15 | EURGBP | -  | -  | - | NOT_ASKED | NO_TRADE | - |
| 10-28 00:15 | NZDUSD | -  | -  | - | NOT_ASKED | NO_TRADE | - |
| 10-28 00:00 | USDCHF | -  | -  | - | NOT_ASKED | NO_TRADE | - |
| 10-28 00:00 | USDCAD | -  | -  | - | NOT_ASKED | NO_TRADE | - |
| 10-27 23:45 | AUDUSD | -  | -  | - | NOT_ASKED | NO_TRADE | - |
| 10-27 23:45 | USDJPY | -  | -  | - | NOT_ASKED | NO_TRADE | - |

The chart Trader 1 read last: `last_chart.png`. (numbers): no free vision model answered, so Trader 1 read the same chart from its numbers.

Full figures: `paper_forward.json`. Rules: `docs/PAPER_FORWARD.md` on main.
