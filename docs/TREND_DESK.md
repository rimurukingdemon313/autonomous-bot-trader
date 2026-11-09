# The trend desk: TRND-1 traded by the system itself

**PAPER ONLY · NOT REAL MONEY.** A $200,000 paper account (`TRND1-PAPER-200K`), separate from every other account
here. It started at the close of 2026-11-09. After each weekday's closes, on GitHub's runner, the system:

- reads the day's final bars;
- decides what TRND-1 says;
- sizes each entry in the risk engine;
- passes each order and each stop move through the hard risk gate;
- fills it on the paper broker.

No person enters a trade. The report and the account are on the `trend-desk-data` branch: `REPORT.md` (with an Arabic
summary), `state.json` and `desk.db.gz`, with the paper-trading ledger and its report beside them (below).

## The permanent ledger and the paper-trading report (2026-11-09)

The owner, 2026-11-09, asked for the trading report to be kept apart from research, with daily figures kept apart from
cumulative ones, and for a ledger that is never reset. `scripts/desk_ledger.py` writes three files to
`trend-desk-data` after every run. It only reads the desk's record and never trades, sizes or closes anything:

- **`TRADING_REPORT.md`** has these sections:
  - the last 30 days, each day's net on its own;
  - the cumulative figures: equity, realized and unrealized P&L, closed trades won and lost, costs by kind, open
    exposure and leverage, the maximum drawdown with every session's intraday lows included;
  - the monthly dashboard: starting and ending equity, net, return, maximum drawdown, trades won and lost, and
    progress toward $4,000;
  - every losing day, week and month;
  - every trade;
  - the risk limits in force, read from the profile;
  - the backtest and the validated out-of-sample result, named as such in their own section and never added to the
    paper figures.
- **`ledger.csv`** has one row per trade, closed or open: the entry and exit times, instrument, side, prices, lots,
  notional and leverage at entry, the risk the engine approved, the gross P&L, the spread, commission, slippage and
  financing, the net, the exit reason, and the TRND-1 signal that opened it. Each closed row checks that the gross
  less its costs equals the net, as the paper broker booked it.
- **`equity.csv`** has the account after every session: equity, balance, open P&L, gross exposure, leverage.

The record behind it:

- **The account after each session.** The runner writes it right after the desk acts (event `DESK_EQUITY`, once per
  session, never again).
- **The trades.** They come from the desk's own `DESK_TRADE_CLOSED` events, with the broker's gross and swap.
- **The signals.** They come from the `DESK_DECISION` that opened each trade.

The events are append-only and hash-chained, and the whole ledger is rebuilt from them on every run, so nothing can be
dropped or reset. A figure the record does not hold is shown as unknown.

If recording a session's equity fails, the desk still trades. The gap is named in `REPORT.md`'s problems and in
`TRADING_REPORT.md`. If the ledger itself fails, the desk's state and `REPORT.md` are still written,
`TRADING_REPORT.md` says what failed, and no CSV is left looking current.

## Why it exists

The owner, 2026-11-08: "النظام يتداول من وحده انتهى" ("the system trades by itself, done"). That was the answer to
TRND-1 being proposed for a funded account. Until then the rule was only followed in a paper simulation (FUNDED-P,
`docs/FUNDED_PAPER.md`). That simulation is a calculation from closes, and someone would have had to place its trades
by hand.

The trend desk runs the rule through the bot's own execution path, the same path a broker connection would use:

```
final daily bars → TRND-1's decision (aitrader/position/trend_desk.py)
  → RISK ENGINE: sizes it, approves or refuses it (aitrader/risk/engine.py)
  → execution checks: kill switch, pause, account type, VALIDATED only, stale decision, price drift
  → HARD RISK GATE: the funded-account limits; a single-use permit (aitrader/risk/hard_gate.py)
  → PAPER BROKER (aitrader/broker/paper.py)
```

It is the same rule as FUNDED-P's HALF track, with the same one-day stop and about the same size. The two should read
alike. Where they differ, the difference is what execution adds: real fills at the spread, a stop hit inside the day,
the gate's limits, and a switch one day late after a holiday.

## The rule (research/preregistrations/TRND-1.md, unchanged)

Each index is decided on its own:

- **Hold it.** If its month-end close is above the mean of its ten month-end closes (that one included), hold it for
  the next month.
- **Otherwise, hold nothing.** It is long or flat, never short.
- **A gap means flat.** A month whose ten month-ends are not ten consecutive calendar months is not decided.

The rule was **PASSED and VALIDATED**: +0.509% a month on the S&P 500, 1929-1989 (t 3.83 against a bar of 3.3761). On
the four indices, 2021-2026, it made +0.785% a month with a worst fall of 10.6%, against 22.2% for holding all four.

**It is not an edge over the market.** Month by month it earned slightly less than holding the index. What it had was
about half the worst fall.

It trades the US 500, US Tech 100, GER 40 and UK 100. Prices come from their cash indices on Yahoo: ^GSPC, ^NDX,
^GDAXI and ^FTSE.

## What the desk adds, each one declared

None of these was tested by TRND-1 itself.

| | |
|---|---|
| When it switches | At the close of the month's last weekday. If that day has no close (an exchange holiday: Xetra on 31 December, Good Friday, a UK bank holiday), it switches at the next close, one trading day late. RC-EQ put a full day's delay at about 0.2% a year, and here it happens a few times a year at most |
| The start | At its first close, each index takes the current month's decision (all four HOLD in November 2026) |
| The size | The risk engine's, never the desk's: at most $1,500 lost at the stop, all costs included (0.75% of the starting balance). With a 6% stop that is about $25,000 of each index, a quarter of half the account: FUNDED-P's HALF size. It never grows after a win. It does not shrink after a run of losing trades either (trend-desk-1.1.0): the rule was tested at a fixed size, and its small losses in choppy months are part of it |
| The one-day stop | FUNDED-P's HALF stop: 6% below each close, moved after every close through the gate. A move toward the price is always allowed. A move away from it (after a down day) must keep all the positions' losses to their stops within $8,000 together, and the worst case above the daily and total floors (hard-gate-1.4.0). After a long rise, when the positions have grown, that holds the stops closer than 6%. After it is hit, the index is flat until the next month-end decision |
| A day's range | The stop is hit by the day's low, not only by the close. A gap through it fills at the open |
| Costs | The bid/ask spread (US 500 0.5 points, US Tech 100 1.5, GER 40 1.5, UK 100 1.0: declared typical CFD spreads), 0.1 point of slippage per fill, and $7 per lot (one unit of the index) round trip. Swap-free, as the rule was judged and as the account must be. No dividends |
| Conversion | GER 40 is valued in euros and UK 100 in pounds, at the previous day's EUR/USD and GBP/USD close |

## The account's limits (TRND1-PAPER-200K, aitrader/risk/profile.py)

| | |
|---|---|
| Starting balance | $200,000 |
| Per position | at most $1,500 lost at its stop, all-in |
| All positions together | at most $8,000 at their stops |
| Daily loss | $10,000 from the day's reference (00:00 Prague), on equity. Each session's intraday low is shown to the gate before its close, so a fall inside the day counts even when the close recovers |
| Maximum loss | $20,000: equity at $180,000 |
| A breach | Fails the account, as a firm's rules do: the run locks, every position is closed at that close, and nothing more is opened. Only an explicit evaluation reset starts a new one |
| The risk engine's own limits | 0.75% per trade, but only for a VALIDATED rule (anything else stays at 0.25%); 4% open; 5% a day; no new entry at 10% or more below the starting balance (the firm's own reference: measured from the peak, a flat account below it could never trade again); four positions, one per index; at most 1x exposure |

The FX desk's timing rules are not the trend desk's: the weekend, quiet hours, the overlap and news windows. A rule
that holds for months is held over weekends and through releases, by design. It is judged on that.

## A rule nobody promoted is not traded

A decision is VALIDATED only if a person promoted the rule in `models/artifacts/promoted_rules.json`, with status
VALIDATED and health HEALTHY. TRND-1 was promoted on 2026-11-08, on the owner's word, for PAPER.

The file never carries a size. If the rule is absent, DEGRADED or retired, the execution engine refuses every entry
before the broker ("not VALIDATED"), and the desk trades nothing. It never trades a smaller size instead.

## What it does not model

- **Inside the day.** Only each session's low is seen, the four indices' lows at their own two closes. The real path
  of equity inside a day is not.
- **The fill.** It fills at the close. On a real account the order would go in minutes before it, at the price then.
- **The firm's other rules.** The minimum of four trading days, the payout cycle, inactivity rules and any ban on
  holding over weekends or news are not modelled. The phase targets (+$20,000, +$10,000) are reported, never
  pursued.
- **The future.** It says what the rule did on this account forward, not what it will do.

## Toward a funded account

The desk trades only on the paper broker. To trade a funded account by itself, the system needs:

1. **A broker connection for that account.** This build has none. The platform decides how: TradeLocker, cTrader,
   DXtrade and Match-Trader have APIs a server can reach. MetaTrader 4 or 5 needs its own terminal running on Windows.
2. **The DEMO rule, unchanged.** An account is used only if the broker itself reports it as a demo account (prop-firm
   challenge accounts usually are). The broker's report and our own check must agree. A live account is refused.
3. **Credentials only in the host's secret settings.** They are never in the repository, a report or a log.
4. **The same code path.** The risk engine, the gate, the execution checks, and the desk's stop moves and switches.

None of this changes what TRND-1 is: a rule with roughly the market's return, about half its worst fall, and a few
trades a year.

## The desk's own code, replayed on 2004-2026 (descriptive, not a test)

`scripts/trend_desk_replay.py` ran the desk itself on Yahoo's daily bars for the four indices, 2004-01-02 to
2026-11-06, on GitHub's runner (`research/results/TREND-DESK-replay.json`). Everything went through the same path as
the live desk: the risk engine, the gate, the paper broker, the stops on the day's low and each session's intraday low.
These data were already judged (RC-EQ 1990-2020, TRND-1-H 2021-2026). It changes no verdict, and the past is not a
forecast.

| | |
|---|---|
| A year on $200,000 | mean +3.4%, median +3.3% (22 full years); 6 losing years; worst -6.8% (2022), best +13.5% (2013) |
| The whole period | +$147,080 on the starting balance (fixed size, nothing compounded), no account failed |
| Lowest equity | $194,040 (2004-07-26); the $180,000 floor was never near |
| Worst fall from a peak | $28,038 (2016), after the account had grown |
| Trades | 88 entries; 18 stopped by the one-day stop, the rest closed by the rule |
| Refusals | 3 entries (the other positions had grown, and the $8,000 open risk was full: 2007, 2014, 2025); 383 stop moves away from the price, 355 for the open risk and 28 for the daily floor, all after long rises |

Against FUNDED-P's HALF track over the same years (closes only, booked at -8% on a stop day) it made a little less
(+3.4% a year against +3.6%). The difference is the real execution: a stop hit by a day's low that closed higher
(2015, 2016, 2025).

| Year | Desk | FUNDED-P HALF | Stops | Entries |
|---|---|---|---|---|
| 2004 | +1.8% | +2.5% | 0 | 9 |
| 2005 | +4.2% | +4.3% | 0 | 2 |
| 2006 | +8.2% | +6.0% | 0 | 1 |
| 2007 | +7.5% | +5.9% | 1 | 2 |
| 2008 | -5.0% | -5.0% | 1 | 1 |
| 2009 | +10.3% | +10.5% | 0 | 4 |
| 2010 | +2.0% | +2.8% | 2 | 6 |
| 2011 | -5.9% | -5.0% | 3 | 1 |
| 2012 | +3.2% | +3.2% | 0 | 6 |
| 2013 | +13.5% | +11.6% | 0 | 1 |
| 2014 | +3.2% | +2.2% | 1 | 3 |
| 2015 | -4.4% | -0.9% | 2 | 4 |
| 2016 | -0.1% | +2.0% | 2 | 8 |
| 2017 | +8.8% | +7.6% | 0 | 1 |
| 2018 | -3.8% | -2.0% | 1 | 5 |
| 2019 | +3.5% | +3.6% | 0 | 8 |
| 2020 | +3.7% | +3.5% | 2 | 6 |
| 2021 | +10.7% | +9.3% | 0 | 0 |
| 2022 | -6.8% | -5.4% | 0 | 6 |
| 2023 | +7.2% | +6.8% | 0 | 6 |
| 2024 | +10.2% | +8.7% | 0 | 0 |
| 2025 | +2.4% | +7.0% | 2 | 5 |
| 2026 (to 6 Nov) | -0.8% | +0.9% | 1 | 3 |

**What the replay found before the first session**, all fixed:

- **hard-gate-1.4.0.** A stop moved back down after a down day was held to the per-trade $1,500. That sizes a new
  position, and a position that has risen is worth more than it was sized at. So the one-day stop had become a stop
  trailing the highest close, which nobody had analysed: 389 refused moves in a three-year smoke test.
- **trend-desk-1.1.0.** The drawdown limit is now measured from the starting balance. Measured from the peak, a flat
  account below it could never trade again.
- **trend-desk-1.1.0.** The size no longer halves after losing runs.

## Tests

`tests/unit/test_trend_desk.py` builds each market so the right answer is known:

- the decision is TRND-1's own, and it reads only the months before it;
- the entry is sized by the risk engine and gets the gate's permit;
- the stop follows each close through the gate;
- a day through the stop closes the position at the stop (or at the open, on a gap), and the index waits for the
  month-end;
- a month-end FLAT closes the position by the rule;
- a holiday month-end switches one day late, on the right month-end close;
- an unpromoted or DEGRADED rule trades nothing;
- a session is applied once, and a restart replays nothing;
- each session's intraday low reaches the gate;
- a breach fails the account and closes what is left;
- the promotion file is strict;
- the runner waits for a late bar instead of skipping it.

`tests/unit/test_desk_ledger.py` checks the ledger through the same runner:

- each session is recorded once, and a re-run records nothing more;
- a trade stopped through a gap is booked with its signal, size and costs, and the costs add up to its net;
- the account's change equals the realized P&L plus the open P&L;
- the entry day shows its entry costs as a loss;
- each day's net is its own, and the months chain;
- an intraday fall that recovers by the close still counts in the drawdown;
- no research or backtest figure appears among the paper figures;
- before the first session nothing is invented;
- a failed ledger never stops the desk.

The gate's stop permits are in `tests/unit/test_hard_gate.py`, and the VALIDATED risk cap in `tests/unit/test_risk.py`.
`scripts/mutation_audit.py` removes each of these guards in turn and requires a test to fail.

Versions: `trend-desk-1.1.0`, `risk-1.16.0`, `hard-gate-1.4.0`, `hard-profile-1.2.0`, `paper-1.5.0`, `exec-1.9.0`,
`edge-status-1.4.0`. Every event the desk records carries `aitrader.version.stamp()`.
