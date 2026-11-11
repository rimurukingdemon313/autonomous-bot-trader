# Trend desk: paper-trading performance

**PAPER TRADING · NOT REAL MONEY · NOT A BACKTEST.** TRND-1 traded by the system itself, forward from 2026-11-09, with simulated fills on each index's real daily close. Backtest and validated out-of-sample results are listed at the end and are never added to these figures.

**بالعربي:** هذا تقرير التداول الورقي وحده: فلوس مو حقيقية، ومو باكتيست، وما بيه ولا رقم من البحث. الرصيد هسه $199,753.93، يعني من البداية -$246.07. آخر يوم (2026-11-10) طلع -$238.67. الصفقات المسكّرة: 0 (ربحت 0، خسرت 0). أكبر نزول من القمة: $741.41. الـ$4,000 بالشهر هدف مو إلزام: النظام ما يزيد المخاطرة ولا يفتح صفقة حتى يوصله.

Updated 2026-11-11 02:14 UTC · sessions run: 4 · recorded: 4 · last: 2026-11-10 · desk-ledger-1.0.1

## Daily

Each session day's closing equity less the day before's. The newest is first; every day is in equity.csv.

| Day | Equity at the close | Net | Return | Worst fall in the day | Trades opened | Closed: won / lost |
|---|---|---|---|---|---|---|
| 2026-11-10 | $199,753.93 | -$238.67 | -0.12% | $738.11 | 0 | 0 / 0 |
| 2026-11-09 | $199,992.60 | -$7.40 | -0.00% | $21.81 | 4 | 0 / 0 |

## Cumulative (since 2026-11-09)

| | |
|---|---|
| Starting equity | $200,000.00 |
| Equity now | $199,753.93: -$246.07 (-0.12%) |
| Realized net P&L (closed trades) | $0.00, from $0.00 gross |
| Unrealized P&L (open trades, at the last close) | -$246.07 |
| Closed trades | 0: 0 won, 0 lost |
| Open trades | 4 |
| Costs paid on closed trades | spread $0.00 · commission $0.00 · slippage $0.00 · financing $0.00 (swap-free) |
| Open exposure | $98,219.79 notional, 0.49x the equity |
| Maximum drawdown (intraday lows included) | $741.41 (0.37% of the peak) |
| Below the peak now | $246.07 |
| Losing days / weeks / months | 2 of 2 · 1 of 1 · 1 of 1 |

## Monthly dashboard

The $4,000 a month is a target, never a quota: the desk does not trade more, or larger, to reach it (CLAUDE.md rule 8). A month in progress is marked so.

| Month | Starting equity | Ending equity | Net | Return | Max drawdown | Trades won / lost | Of $4,000 |
|---|---|---|---|---|---|---|---|
| 2026-11 (in progress) | $200,000.00 | $199,753.93 | -$246.07 | -0.12% | $741.41 (0.37%) | 0 / 0 | -6.2% |

## Every losing day, week and month

- **Days:** 2026-11-09 -$7.40, 2026-11-10 -$238.67
- **Weeks:** 2026-W46 -$246.07
- **Months:** 2026-11 -$246.07

## Every trade: the permanent ledger, never reset, nothing excluded

| # | Status | Instrument | Side | Opened | Closed | Entry | Exit or mark | Lots | Notional at entry | Leverage at entry | Gross | Spread | Commission | Slippage | Financing | Net | Exit | Signal |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | OPEN | GER40 | LONG | 2026-11-09 16:30 UTC | — | 26,268.04 | 26,346.70 | 0.84 | $24,773.82 | 0.124x | open +$73.65 | | | | | | | TRND-1 BUY for 2026-11: the 2026-10-30 month-end close 25,818.21 was above the mean of its last ten month-end closes, 24,980.08 |
| 2 | OPEN | UK100 | LONG | 2026-11-09 16:30 UTC | — | 10,783.50 | 10,751.10 | 1.70 | $24,665.05 | 0.123x | open -$73.59 | | | | | | | TRND-1 BUY for 2026-11: the 2026-10-30 month-end close 10,729.80 was above the mean of its last ten month-end closes, 10,562.40 |
| 3 | OPEN | US500 | LONG | 2026-11-09 21:00 UTC | — | 7,550.29 | 7,520.68 | 3.25 | $24,536.49 | 0.123x | open -$96.23 | | | | | | | TRND-1 BUY for 2026-11: the 2026-10-30 month-end close 7,580.07 was above the mean of its last ten month-end closes, 7,304.23 |
| 4 | OPEN | NAS100 | LONG | 2026-11-09 21:00 UTC | — | 27,908.47 | 27,740.04 | 0.89 | $24,837.12 | 0.124x | open -$149.90 | | | | | | | TRND-1 BUY for 2026-11: the 2026-10-30 month-end close 28,384.85 was above the mean of its last ten month-end closes, 27,883.88 |

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
