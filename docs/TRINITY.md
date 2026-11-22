# TRINITY-MASTER: the owner's package, tested on real prices and put on paper (2026-11-21)

**بالعربي:** المالك بعث حزمة TRINITY-OMEGA وطلب تنفيذ مواصفتها بالمستودع. انبنى كل اللي طلبته: مكتب ورقي
بحساب $200,000 يتداول TRINITY-MASTER بنفسه بعد كل إغلاق نيويورك. بس قبل ما ينبني انفحصت أرقامها على أسعار حقيقية،
والنتيجة: أرقامها الحلوة (t 4.24، صفر فشل بحساب الشركة، $1,847 بالشهر) طلعت من 288 تاريخ مختارة. على نفس
القاعدة بالضبط وبكل الـ15 يوم اللي ممكن يبدأ منها الدوران، الـt بين 1.55 و4.78، وكل واحدة منهن نزلت أكثر من 10%،
ومزيج ثابت بنفس متوسط أوزانها أعطى t أعلى. لهذا القاعدة **تجريبية (EXPERIMENTAL)**، تتداول على الورق بس، ومحرك
المخاطر يحدد حجمها مثل أي قاعدة ما انعتمدت (0.25% بالصفقة). ما راح لحساب تجريبي ولا حقيقي.

**PAPER ONLY · NOT REAL MONEY · NOT VALIDATED.** Every backtest figure on this page is descriptive: each bar was read
by the package's author, and again here. Nothing on this page is a validation, and none of it is added to the paper
desk's own record.

## What the owner sent

On 2026-11-21 the owner uploaded `trinity_omega_complete_package.zip` and asked: "read CLAUDE_HANDOFF_SPEC.md and
implement what it asks, in full, in the repository". The package is kept as received in `research/external/trinity/`
(sha256 of every file in its README; the specification's copy has one line changed, the owner's personal name,
because this repository is public).

- `trinity_omega_suite.py`: four rules on 288 three-weekly closes of QQQ, SPY, GLD and DBC (2007-03-02 to
  2026-11-13), with the VIX, TLT and UUP read as sensors that are never traded: TRND-1 PRO, NEXUS-ALPHA-4 PRO,
  OMEGA-APEX-1, and TRINITY-MASTER, a fixed blend of the three (20/40/40, scaled by 1.14).
- `trinity_master_trades_20yr.csv`: TRINITY-MASTER's 288 periods as its own code computes them.
- `CLAUDE_HANDOFF_SPEC.md`: the table below and a five-item checklist: a symbol map, the sensors at t-1, daily
  lookbacks (15 trading days a bar), a hard-gate order adapter (3.2% stop, open risk at most 4%), and a PAPER desk
  beside the trend desk, registered in `models/artifacts/promoted_rules.json`, with a daily audit.

What it claims for TRINITY-MASTER, 2007-2026, on $200,000:

| t (2007-16 / 2017-26) | Costs x2 t | Profit factor | Win rate | Max drawdown | Prop-firm failures (-10% from start / trailing) | Net, 20 years | 2021-26 a month |
|---|---|---|---|---|---|---|---|
| 4.24 (2.84 / 3.14) | 3.85 | 2.10 | 66.95% | -9.47% | 0 / 273, 0 / 273 | +$270,973 | +$1,847 |

## The red team (`research/results/TRINITY-MASTER-redteam.json`)

`scripts/trinity_redteam.py` runs the package's **own** weight functions, unchanged, through a copy of its own audit
loop. Any difference from the table comes from the data or the accounting, never from a re-implementation. Real
prices: Yahoo daily bars fetched on GitHub's runner (`trinity-desk-data`, `history/`, 2006-01 to 2026-11-20).

| Test | What it does | What it found |
|---|---|---|
| T0 | the package's code on the package's data | **reproduces the table exactly.** It also prints a figure the table leaves out: executed one bar later, TRINITY-MASTER's t is **1.81** (TRND-1 PRO's 0.89) |
| T1 | its hard-coded prices against real closes on the same dates | QQQ, SPY and GLD match on 299 of 299 dates; DBC, UUP and TLT on 298 of 299. **The VIX does not**: 158 of 299 (2007-13: 29 of 100; 2014-20: 97 of 99; 2021-26: 32 of 100). Most of the wrong values are the VIX of 5 to 10 trading days earlier |
| T2 | the same 288 dates, every series real | t 4.08 (2.80 / 2.97), drawdown -9.24%, +$254,796, 0 / 273, $1,731 a month 2021-26. The VIX error moved little (VIX alone corrected: t 4.10) |
| T3 | **the spec's own daily form**: a rebalance every 15th trading day, on each of the 15 possible starting days, the same span | **t from 1.55 to 4.78** (median 2.99); 7 of the 15 reach 3.0. 2007-16 alone: t 0.63 to 3.08. **Every grid's drawdown exceeds 10%** (-10.0% to -23.0%). 2021-26 a month: median $1,273 (from $394 to $2,418) |
| T4 | each grid held as the package holds it, **marked every day**, intraday lows included, judged by a firm's two rules (10% maximum loss from the start, 5% in a day), from every start date | worst fall inside a day **-25.5%**; **all 15 grids breach a rule**; 7,650 of 14,322 start dates fail by 2026; over one year, 11 to 166 of about 955 starts a grid. Median 20-year net $201,045; 2021-26 median $1,354 a month |
| T5 | as the spec would trade it: the adapter's caps and a **3.2% stop** below each rebalance close, on daily highs, lows and opens, on the CFD prices the map names (^NDX, ^GSPC, GLD, USO) | median net $164,088; 2021-26 median $1,248 a month; worst fall -19.0%; 13 of 15 grids breach a rule (2,712 of 14,322 starts). On the funds themselves: $149,653, $1,063, -20.2% |
| T6 | each of the **119 hand-set constants** in its rules moved by ±10%, one at a time and in 300 joint draws, on its own 288 dates | t stays between 4.02 and 4.47 one at a time, 3.77 to 4.76 jointly (5th to 95th percentile): not a knife edge for t. But **a quarter of the joint draws break "0 / 273"** (drawdown 5th percentile -11.2%): that claim sits on the edge the comment in its code says it was tuned to ("keeping Max DD < -9.0% and 0/273 failures") |
| T7 | a **fixed mix** holding its own average weights all the time (QQQ 0.18, SPY 0.19, GLD 0.13, DBC 0.03), its own dates | t 3.46, +$234,737, drawdown -23.4%, 23 / 273 failures |
| T9 | the same fixed mix on each of the 15 real grids | **median t 3.60 against TRINITY-MASTER's 2.99**; TRINITY-MASTER earns more in 7 of 15; its drawdown is smaller in 14 of 15 |
| T8 | the deflated Sharpe ratio | 0.94 at 100 trials, 0.82 at 1,000. It asks whether the mean beats zero, and the fixed mix answers that better: the comparison that matters is T9 |

**What this means.**

1. **The headline is a property of the 288 dates, not of the rule.** The spec itself turns the package into a
   15-trading-day rebalance. On the 15 ways to start that rebalance, the same code gives t from 1.55 to 4.78. Which
   one an account gets is luck.
2. **"0 failures" and "-9.47%" are measured three weeks apart.** A firm watches the account every moment. Marked every
   day, every grid breaches the 10% or the 5% rule somewhere between 2007 and 2026.
3. **What the rule adds is a smaller fall, not a larger return.** Holding its own average weights all the time gives a
   higher t. Its timing keeps the drawdown smaller on 14 of the 15 grids: the same lesson as TRND-1, which "earned
   slightly less than holding the index; what it had was about half the worst fall".
4. **The figures are in-sample.** The rules were written knowing 2007-2026. No period exists that their author had
   not seen, and nothing was preregistered.

So TRINITY-MASTER is **EXPERIMENTAL**: neither validated nor rejected. Its record starts on paper, forward.

## What was built: the spec's checklist, item by item

| Spec item | Built | Where it differs from the package, and why |
|---|---|---|
| 1. The symbol map | `aitrader/position/trinity.py` (`CFD_OF`): QQQ -> NAS100, SPY -> US500, GLD -> XAUUSD, DBC -> USOIL. USOIL is a new commodity CFD (`aitrader/data/instruments.py`: 100 barrels a lot, a 0.01 pip); the paper broker, the risk engine and the hard profile know it. XAUUSD keeps the metal rules it has | The cTrader connection stays dormant, as the spec says: the map is not added to `aitrader/broker/ctrader/symbols.py`, which only the DEMO desk reads, and an unvalidated rule never reaches DEMO |
| 2. The sensors at t-1 | `trinity.rows_at`: the VIX, TLT and UUP at the trading day before each grid day | The package read them on the grid day itself |
| 3. Daily bars | the package's own features, computed on a grid of every 15th trading day from the anchor (2026-11-23) | The spec lists "MA3 = 45 days" and so on. Those would be other rules. The desk keeps the package's features exactly (`tests/unit/test_trinity.py` checks every one of 24,749 feature values and all 288 weight vectors against the package's own code) and only changes what a bar is |
| 4. Mandatory stops and limits | the repository's own risk engine and hard gate, on a new profile `TRINITY-PAPER-200K`: a 3.2% stop on every position, at most 4% at all the stops, margin at 1:10, 5% a day and 10% in all from the start | **The size is the risk engine's, not the weight's** (CLAUDE.md rules 2 and 14). An unvalidated rule risks at most 0.25% of the starting balance at its stop. The package's 1.5% a position, and its weights of 0.3 to 1.2 of the account, are refused, whatever the backtest says |
| 5. A PAPER desk | `aitrader/position/trinity_paper_desk.py`, `scripts/trinity_paper_desk.py`, `.github/workflows/trinity-desk.yml` (weekdays 22:47 UTC, backups 01:17 and 06:47), its own branch `trinity-desk-data`, the daily audit `research/results/TRINITY-MASTER-daily-audit.json` on that branch, and the rule in `models/artifacts/promoted_rules.json` | The rule is registered as **EXPERIMENTAL**, a status added for this: a person put an unvalidated rule on paper for a forward test. The classifier never reads it as VALIDATED. A rule may not carry weights or any size (a test refuses it) |

How the desk trades, every session, at the New York close:

- every 15th trading day from 2026-11-23: TRINITY-MASTER's weights. An instrument whose weight is above 1e-4 (the
  package's own threshold) is held; the others are closed;
- each entry goes through the risk engine, the hard gate's single-use permit, and the paper broker, with a stop 3.2%
  below the close. A held position keeps its size; its stop moves to 3.2% below the new rebalance close. A stop hit
  leaves the instrument flat until the next rebalance;
- the intraday lows are observed before the close. A breach of the daily or total limit fails the account and closes
  everything, as a firm would;
- prices: NAS100 and US500 from the cash indices; XAUUSD from GLD and USOIL from USO, each scaled once, at the first
  session, to the level of its futures (GC=F, CL=F), and never rewritten. A continuous futures series jumps at every
  roll, and a swap-free CFD earns the spot or rolled return;
- a bar counts 30 minutes after the close, and a day missing any series' bar holds every later session back, named
  in the report, never skipped.

**The design book** sits beside the account: the package's weights at their own size, with no stops, its 8 bp cost,
marked every day on the four funds it was written for, from the same anchor. It measures the package's claim going
forward. It is never traded and never added to the account.

**Tests and mutants.** `tests/unit/test_trinity.py` (the port against the package itself), `test_trinity_paper_desk.py`
and `test_trinity_paper_desk_script.py` (built markets whose answer is known by construction: steady rises the
package holds, a stop through the day's low, a weight falling to nothing, a crash gap that fails the account, a late
bar, a hole in one series), `test_trinity_data.py`. Nineteen `trinity-` mutants in `scripts/mutation_audit.py`, all
killed.

## The desk's own code on 2008-2026 (`research/results/TRINITY-MASTER-desk-replay.json`)

Required before a desk goes to paper (docs/TREND_DESK.md): a replay of its own code on real bars. Descriptive, for
the same reason as the red team.

| | The account (risk engine sizing, 3.2% stops) | The design book (the package's weights, no stops) |
|---|---|---|
| $200,000 became | $259,204 (+$59,204) | $473,762 (+$273,762) |
| A month, on average | about $262 | about $1,210 |
| Worst fall | -$4,954 at the closes | -$39,802 at the lows |
| A firm's rules | never breached | 5% in a day breached on 2015-08-24 |
| Trades | 247 closed: 120 won, 127 lost; 155 stopped (-$4,626 together), 92 closed by the rule (+$63,829) | |
| Daily audits | 4,753 sessions, every check held | |

The account is small because the size is small: 0.25% at a 3.2% stop is about $15,000 a position. That is the price
of an unvalidated rule, and it is the same price every unvalidated rule here pays.

## What it would take to rely on it

- **Time.** The paper record from 2026-11-23, kept apart from TRND-1's, judged by nobody until it is long enough to
  mean something.
- **A test registered before it is run.** A forward test of the design book against the fixed mix of its own
  average weights, with its length and its pass rule fixed first, would be the honest one. It is not registered: at
  the gap T9 shows, three years would most likely end INCONCLUSIVE, and an experiment is not invented to keep a
  queue busy.
- **Never**: larger sizes because the backtest looked good, a DEMO or live account before it has passed a
  registered test, or the package's table repeated as if it had been verified.

## Reproduce

    python scripts/trinity_data.py --out <dir>                                   # the bars (GitHub's runner)
    python scripts/trinity_redteam.py research/external/trinity/trinity_omega_suite.py <dir>/history <out.json>
    python scripts/trinity_paper_desk.py --replay 2008-01-02 --history <dir>/history --state <state>
    python -m pytest tests/unit/test_trinity*.py
