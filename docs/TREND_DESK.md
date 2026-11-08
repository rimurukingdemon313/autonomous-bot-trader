# The trend desk: TRND-1 traded by the system itself

**PAPER ONLY · NOT REAL MONEY.** A $200,000 paper account (`TRND1-PAPER-200K`), separate from every other account
here. It started at the close of 2026-11-09. After each weekday's closes, on GitHub's runner, the system:

- reads the day's final bars;
- decides what TRND-1 says;
- sizes each entry in the risk engine;
- passes each order and each stop move through the hard risk gate;
- fills it on the paper broker.

No person enters a trade. The report and the account are on the `trend-desk-data` branch: `REPORT.md` (with an Arabic
summary), `state.json` and `desk.db.gz`.

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
| The size | The risk engine's, never the desk's: at most $1,500 lost at the stop, all costs included (0.75% of the starting balance). With a 6% stop that is about $25,000 of each index, a quarter of half the account: FUNDED-P's HALF size. It never grows after a win, and the engine's own rule halves it after runs of losses (rule 2: risk only ever decreases) |
| The one-day stop | FUNDED-P's HALF stop: 6% below each close, moved after every close through the gate. A move toward the price is always allowed. A move away from it (after a down day) must fit the $1,500, so after a large rise the stop can sit closer than 6%. After it is hit, the index is flat until the next month-end decision |
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
| The risk engine's own limits | 0.75% per trade, but only for a VALIDATED rule (anything else stays at 0.25%); 4% open; 5% a day; no new entry while equity is 10% or more below its peak; four positions, one per index; at most 1x exposure |

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

The gate's stop permits are in `tests/unit/test_hard_gate.py`, and the VALIDATED risk cap in `tests/unit/test_risk.py`.
`scripts/mutation_audit.py` removes each of these guards in turn and requires a test to fail.

Versions: `trend-desk-1.0.0`, `risk-1.16.0`, `hard-gate-1.3.0`, `hard-profile-1.2.0`, `paper-1.5.0`, `exec-1.9.0`,
`edge-status-1.4.0`. Every event the desk records carries `aitrader.version.stamp()`.
