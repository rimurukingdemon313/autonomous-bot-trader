# Trend desk: paper-trading performance

**PAPER TRADING · NOT REAL MONEY · NOT A BACKTEST.** TRND-1 traded by the system itself, forward from 2026-11-09, with simulated fills on each index's real daily close. Backtest and validated out-of-sample results are listed at the end and are never added to these figures.

**بالعربي:** هذا تقرير التداول الورقي وحده: فلوس مو حقيقية، ومو باكتيست، وما بيه ولا رقم من البحث. الرصيد هسه $200,000.00، يعني من البداية $0.00. بعد ما صارت ولا جلسة. بهالتشغيل صارت 2 مشكلة، مكتوبة تحت. الجلسة اللي بياناتها ناقصة ما تنطبق، وتنتظر لحد ما توصل كاملة. الصفقات المسكّرة: 0 (ربحت 0، خسرت 0). أكبر نزول من القمة: $0.00. الـ$4,000 بالشهر هدف مو إلزام: النظام ما يزيد المخاطرة ولا يفتح صفقة حتى يوصله.

Updated 2026-11-10 01:19 UTC · sessions run: 0 · recorded: 0 · last: none yet · desk-ledger-1.0.1

**Problems this run.** A session whose data is incomplete is not applied, and nothing is filled in for it: it waits, with every session after it, for the first run that reads it complete, and is then applied in order.

- GER40 2026-11-09: a price is missing, not finite or not positive ((25815.30078125, 26276.08984375, 25793.060546875, nan)): nothing from 2026-11-09 on is used
- UK100 2026-11-09: a price is missing, not finite or not positive ((10673.3603515625, 10785.240234375, 10654.3203125, nan)): nothing from 2026-11-09 on is used

## Daily

Each session day's closing equity less the day before's. The newest is first; every day is in equity.csv.

| Day | Equity at the close | Net | Return | Worst fall in the day | Trades opened | Closed: won / lost |
|---|---|---|---|---|---|---|
| no session yet | | | | | | |

## Cumulative (since 2026-11-09)

| | |
|---|---|
| Starting equity | $200,000.00 |
| Equity now | $200,000.00: $0.00 (+0.00%) |
| Realized net P&L (closed trades) | $0.00, from $0.00 gross |
| Unrealized P&L (open trades, at the last close) | $0.00 |
| Closed trades | 0: 0 won, 0 lost |
| Open trades | 0 |
| Costs paid on closed trades | spread $0.00 · commission $0.00 · slippage $0.00 · financing $0.00 (swap-free) |
| Open exposure | $0.00 notional, 0.00x the equity |
| Maximum drawdown (intraday lows included) | $0.00 (0.00% of the peak) |
| Below the peak now | $0.00 |
| Losing days / weeks / months | 0 of 0 · 0 of 0 · 0 of 0 |

## Monthly dashboard

The $4,000 a month is a target, never a quota: the desk does not trade more, or larger, to reach it (CLAUDE.md rule 8). A month in progress is marked so.

| Month | Starting equity | Ending equity | Net | Return | Max drawdown | Trades won / lost | Of $4,000 |
|---|---|---|---|---|---|---|---|
| none yet | | | | | | | |

## Every losing day, week and month

- **Days:** none yet
- **Weeks:** none yet
- **Months:** none yet

## Every trade: the permanent ledger, never reset, nothing excluded

| # | Status | Instrument | Side | Opened | Closed | Entry | Exit or mark | Lots | Notional at entry | Leverage at entry | Gross | Spread | Commission | Slippage | Financing | Net | Exit | Signal |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| none yet | | | | | | | | | | | | | | | | | | |

An open trade is marked at the last close's bid, so the spread and the slippage at its entry are already in its P&L; its commission is charged, and its costs itemized, when it closes. Each closed trade's gross less its costs equals its net, as the paper broker booked it.

## Risk limits in force (never raised after a loss)

| | |
|---|---|
| Per trade | at most $1,500 lost at its stop, all costs included (0.75% of the starting balance); a fixed amount, never raised after a win or a loss |
| All open trades | at most $8,000 at their stops together (4.0%) |
| Daily loss limit | $10,000 from the day's reference, each session's intraday lows included (5.0%) |
| Weekly loss limit | 10.0% from the week's opening equity |
| Maximum loss | $20,000 (10.0%): equity at $180,000 fails the account and closes everything |
| Positions | at most 4, one per index; long or flat, never short; leverage at most 1x |
| NO TRADE | an index whose rule says flat is not held; nothing is traded to meet a target |

## Kept apart: never added to the paper figures

| Kind | What it is | Result | Where |
|---|---|---|---|
| Paper trading (this report) | TRND-1 traded forward by the system, simulated fills on real closes | above | trend-desk-data |
| Backtest (descriptive, not a test) | The desk's own code at its own sizing, replayed on 2004-2026 bars already judged | +3.4% a year on average; 6 losing years of 22; worst year -6.78%; worst fall $28,038 | research/results/TREND-DESK-replay.json |
| Validated out-of-sample | TRND-1's sealed holdout: the four indices at equal weight and fully invested, 2021-01..2026-09 | +0.785% a month on the invested book (not on the desk's smaller sizing) | research/knowledge/TRND-1-H.json |
