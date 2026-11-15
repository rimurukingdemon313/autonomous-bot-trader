# Performance engineering of the paper systems

**PAPER ONLY · NOT REAL MONEY · NOTHING HERE IS A PROFIT CLAIM.** This is the record of the owner's order of
2026-11-13: audit the two paper systems, find where their profit and loss come from, and improve them by evidence
and never by cosmetics. Live trading stays disabled, no risk limit is raised, and no system is replaced by a variant
that had a few good trades.

**بالعربي:** هذا سجل تدقيق النظامين الورقيين وتحسينهم بالدليل. كل رقم بالحساب انعاد حسابه من مصدر ثاني وتطابق.
مكتب TRND-1 رابح $783 لحد 13/11 وكلها أرباح غير محققة (ولا صفقة مسكّرة بعد). رادار RADAR-1 خسران حوالي 2% من
رأس ماله الورقي، والسبب واضح بالأرقام: الصفقة تكسب بالمعدل 15.6 نقطة أساس وتدفع 34.4 نقطة عمولات. التجربة
المسجّلة RADX-1 فشلت بقاعدتها (جزء منها ثبت وجزء ما ثبت)، فما انسجّل أي منافس. ماكو أي نظام انتغيّر.

Code: `aitrader/perf/` (`perf-1.0.0`), `scripts/perf_cycle.py`, `scripts/radx1.py`. Workflow:
`.github/workflows/perf-cycle.yml`. Living report: `PERF_REPORT.md` on the `perf-data` branch. Tests:
`tests/unit/test_perf_*.py`, `tests/unit/test_radx1.py`.

## 1. What was built

| Asked for | What exists | Where |
|---|---|---|
| Both systems audited independently, every number reconciled against the ledger and the equity history | An audit that recomputes each figure by a second route and compares: 40 checks on the trend desk, 24 on the radar. Realized and unrealized are never added into one "profit" | `aitrader/perf/trend.py`, `radar.py` |
| Sources of profit and loss | Attribution of the radar's closed positions by source (funding, price, costs), by holding time, by exit reason, and by three classes known when a position is opened. The largest weakness is named only when it is told from noise | `radar.attribution` |
| An optimization engine that does not optimize history blindly | A replay of the radar's **frozen** decision code on the radar's own stored quotes under declared parameters; the best variant on the earlier half is judged on the later half only | `aitrader/perf/replay.py` |
| A challenger beside the original, never instead of it | A registered challenger starts empty at its registration hour, on the same quotes, fees and slots as the original, and is judged once at a date fixed with it | `replay.forward`, `replay.freeze`, `research/perf/challengers.json` |
| Each cycle: data, reconciliation, analysis, weakness, hypothesis, experiment, validation, challenger, report | One script, run by GitHub's schedule | `scripts/perf_cycle.py`, `perf-cycle.yml` |
| One fully tested optimization experiment | RADX-1: registered, judged once on later trades, **FAILED** (section 5) | `research/preregistrations/RADX-1.md`, `research/knowledge/RADX-1.json` |

## 2. TRND-1: the trend desk's paper account

Audit of the files published at 2026-11-14 13:46 UTC (last session 2026-11-13 21:00 UTC). **40 of 40 checks hold.**

| | |
|---|---|
| Initial capital | $200,000.00 |
| Equity | $200,783.01 |
| **Realized** P&L | $0.00: no trade has closed |
| **Unrealized** P&L | +$783.01: four open positions valued at the last close. A valuation, not a profit |
| Net return after all costs | +0.392% |
| Open positions / closed trades | 4 / 0 |
| Win rate, average win, average loss, profit factor | **undefined: no closed trade.** Not zero |
| Maximum drawdown | $506.09 on session closes; $1,052.51 with each session's lows (recomputed from the desk's database) |
| Gross exposure | $98,980.50, 0.49 times the equity |
| Loss if every stop were hit from here | $5,935.74 (limit $8,000) |
| Losing days | 4 of 5 |
| Of the $4,000 target for November | 19.6%, in five sessions. A target, never a quota |

| Index | Units | Entry | Mark | Move | Unrealized | Notional | Loss at its stop from here |
|---|---|---|---|---|---|---|---|
| GER40 | 0.84 | 26,268.04 | 26,749.20 | +1.83% | +$448.44 | $24,930.19 | $1,495.16 |
| UK100 | 1.70 | 10,783.50 | 10,902.10 | +1.10% | +$267.68 | $24,606.44 | $1,475.33 |
| US500 | 3.25 | 7,550.29 | 7,561.42 | +0.15% | +$36.17 | $24,574.61 | $1,473.71 |
| NAS100 | 0.89 | 27,908.47 | 27,942.99 | +0.12% | +$30.72 | $24,869.26 | $1,491.53 |

What the reconciliation covers:

- the balance moved by exactly the closed trades' net (nothing has closed, and the balance is $200,000.00);
- equity is the start plus realized plus unrealized, in the ledger, in every one of the ten session rows, and in the
  state file;
- each position's open P&L is its units times its move times the currency conversion the desk used;
- every position's risk at entry was within $1,500, and the four stops together within $8,000;
- the desk's permanent record is unbroken: 79 events and 41 risk-gate entries, each hash recomputed by a second
  implementation from the row before it;
- the drawdown inside a day, recomputed along the 20 equities the desk recorded, is the $1,052.51 its report prints.

**Concentration.** Four positions of a quarter of the gross each: by size, four; by risk, **one**. They are four
equity indices, all long. The desk holds one risk factor four times.

**Benchmark.** Cash at 3.875% a year would have made $88.91 on the starting balance in the same 4.2 days. The same
four indices simply bought on the same days and held show the same +$783.01: no trade has closed, so the rule has
not yet made one decision a holder would not have made. Nothing separates the desk from its benchmark yet, and
five days could not show it if something did.

**Sources of its P&L.** The whole of it is the move of two indices: GER40 (+$448) and UK100 (+$268), 91% of the
total. There is no entry timing, exit or cost to attribute before a trade closes.

### What can be improved, and what cannot

| Lever | What the evidence says | Decision |
|---|---|---|
| Position size | The desk risks a fixed $1,500 at a 6% stop, which is about $25,000 an index and half the account in all. The validated rule (TRND-1-H) was measured fully invested. At one times the account the same five days would show +$1,584.84 | **Not proposed.** It doubles the risk to double the result: the owner's rule is that risk is never raised to improve a headline. The limits are the profile's ($1,500 a trade, $8,000 together) |
| The 6% stop, the one-day trail | The desk's own additions. TRND-1 never tested them. The descriptive replay of 2004-2026 (`research/results/TREND-DESK-replay.json`) was run on bars already judged: it describes, it validates nothing | **Not proposed.** There is no untouched history for these four indices to judge a change on. A variant chosen on that replay would be chosen on its own test |
| The rule itself | Its forward test, TRND-F, is registered for December 2026 to November 2029 and is read once | **Left alone** |
| Expected result at this size | The replay's average is +3.4% a year on $200,000: about **$570 a month**, with six losing years in 22 | Stated so that $4,000 a month is not expected of it |

A challenger beside TRND-1 is kept for a rule that passes a registered validation. None has.

## 3. RADAR-1: the funding radar's paper ledger

Audit of `ledger.json` at commit `274a965` of `radar-data` (marks from 2026-10-07 20:00 to 2026-11-14 18:00 UTC,
37.92 days). **24 of 24 checks hold**, among them every performance figure the radar's own report prints, recomputed
by code that calls none of the radar's.

The radar has no cash account. Its capital is ten slots of two legs of notional N each. P&L is in basis points (bp)
of N; 2,000 bp summed over positions is 1% of the book. The dollar column applies the same percentages to a book of
$100,000 and is an illustration of scale.

| | bp of N | % of the book | On $100,000 |
|---|---|---|---|
| **Realized** (210 closed positions, every fill paid) | -3,953.5 | -1.977% | -$1,976.76 |
| **Unrealized** (2 open positions at their marks, entry fills paid) | -11.0 | -0.006% | -$5.49 |
| The book if both were closed now | -3,998.5 | -1.999% | -$1,999.25 |

| | |
|---|---|
| Closed positions | 210: 40 won, 170 lost |
| Win rate | 19.0% |
| Average win / average loss | +80.7 bp / -42.2 bp |
| Profit factor | 0.45 |
| Mean net a position | -18.8 bp (t -3.53) |
| Capital deployed | 21.7% of the slots on average; 2 of 10 now |
| Book excess over cash | -2.086% |
| Annualised excess on the capital deployed | -93.0% a year (-174% with costs at 1.5 times) |
| Maximum drawdown of the book | 2.199% |
| t of the daily excess | -3.37 |
| Best coin (INIT), and the book without it | -2.541% |

Its preregistered look is on 2026-12-06 at 20:00 UTC. It asks for +10% a year on the capital deployed at t 2.0. The
look is read as registered, whatever this audit says, and RADAR-1's code is untouched (its hash is pinned by
`tests/unit/test_perf_replay.py`).

### Where the loss comes from

**Funding received +3,072 bp. Price moves between the legs +201 bp. Fills -7,226 bp. Net -3,954 bp.**

The idea earns: every source of gross P&L is positive. A position earns 15.6 bp before costs and pays 34.4 bp for its
four fills. The costs are 2.2 times the gross.

| Held for | Positions | Won | Sum | Mean | t |
|---|---|---|---|---|---|
| 1 hour or less | 71 | 5 | -2,343 bp | -33.0 bp | -5.25 |
| 1 to 6 hours | 81 | 14 | -2,429 bp | -30.0 bp | -3.93 |
| 6 to 24 hours | 39 | 12 | +148 bp | +3.8 bp | 0.30 |
| 1 to 3 days | 17 | 8 | +693 bp | +40.8 bp | 1.16 |
| over 3 days | 2 | 1 | -22 bp | -10.9 bp | |

Half the positions were closed within three hours. A spread of 25% a year pays 0.29 bp an hour: the position has to
last five days at its entry spread to pay for its own round trip, and 152 of 210 did not last six hours.

| Closed for | Positions | Won | Sum | Mean | t |
|---|---|---|---|---|---|
| The current spread turned against it | 118 | 24 | -2,443 bp | -20.7 bp | -3.63 |
| The 24-hour spread decayed | 61 | 2 | -2,192 bp | -35.9 bp | -14.30 |
| A leg moved 25% (rebalance) | 31 | 14 | +682 bp | +22.0 bp | 0.80 |

| Known when the position was opened | Positions | Won | Sum | Mean | t |
|---|---|---|---|---|---|
| Entry spread under 50% a year | 122 | 18 | -3,363 bp | -27.6 bp | -6.58 |
| Entry spread 50 to 100% a year | 47 | 11 | -393 bp | -8.4 bp | -0.56 |
| Entry spread 100% a year or more | 41 | 11 | -198 bp | -4.8 bp | -0.28 |
| Short MEXC / long Gate | 161 | 31 | -3,406 bp | -21.2 bp | -3.81 |
| Within 6 hours of the coin's previous exit | 138 | 25 | -2,241 bp | -16.2 bp | -2.08 |
| A first entry, or later | 72 | 15 | -1,712 bp | -23.8 bp | -5.61 |

42 coins were traded and 35 of them lost. The most traded, AKE, is 10% of the positions; by count the book is 19
equal coins. Three quarters of the positions are short MEXC and long Gate.

### The improvement opportunities, measured

1. **Thin entries: 85% of the loss.** The 122 positions opened on a trailing spread under 50% a year lost 27.6 bp
   each (t -6.58), against -6.7 bp for the other 88: 2,543 bp more than the rest would have lost. This is the
   largest weakness and the only one that held out of sample (section 5).
2. **Even the thick entries do not earn.** Entries at 50% a year or more averaged -8.4 and -4.8 bp. Neither is told
   from zero, and neither is positive. **No class of entries known at the entry shows a profit.** Removing the thin
   entries stops most of the loss. It does not make the radar a strategy.
3. **Costs.** 34 bp a round trip on taker fees and declared slippage. Nothing in a paper ledger can lower a fee;
   only fewer, longer positions can.
4. **Luck.** INIT made +917 bp on 7 positions, one of them +573 bp. Without it the book is at -2.54%.

## 4. Why a remedy cannot be read off the ledger

Removing a class of entries changes which later entries happen: a coin that is not entered at one hour may be
entered at the next, and the ledger does not hold positions that were never opened. So the ledger can test a
**diagnosis** exactly, and cannot test a **remedy** at all. The remedy is measured by replaying the radar's rules on
its quotes (section 6).

## 5. RADX-1: the registered experiment

Preregistration: `research/preregistrations/RADX-1.md`. Evidence: `research/knowledge/RADX-1.json`. Registered and
judged on 2026-11-14; two counted tests on `crypto-perp-live-xvenue`.

The ledger was split by the hour a position was opened. Everything was stated from the 122 positions opened before
2026-10-30 11:00 UTC, and each prediction was computed once on the 88 opened after it. The preregistration was
pushed to the `dlab-wip` branch (commit `9ecad3e`, 19:17 UTC) before the later part was read.

| Prediction on the later positions | Design part | Later part | Bar | Held? |
|---|---|---|---|---|
| P1: entries on a spread under 50% a year lose | 81 positions, -27.6 bp, t -4.64 | 41 positions, **-27.5 bp, t -6.45**; 21 of 22 coins negative; -26.1 bp without the worst coin | t <= -3.0 | **yes** |
| P2: entries within 6 hours after the same coin's exit for a decayed spread lose | 27 positions, -34.6 bp, t -10.24 | 15 positions, **-17.7 bp, t -1.36**; 2 won | t <= -3.0 | **no** |

**Verdict: FAILED**, as registered: both predictions were required. The thin entries lost the same 27.5 bp in both
parts. The churn after a decayed spread did not repeat at the bar.

What follows, by the preregistration's own words: *no challenger is registered on it*. That rule was written before
the result and is kept. P2 was also not blind (the radar's public report had shown the last 30 closed rows), which the
preregistration declared.

On the later part the positions outside both classes averaged -10.6 bp. The diagnosis explains where most of the
loss is. It does not show a profit anywhere.

## 6. The optimization engine

`aitrader/perf/replay.py`. The radar's `step` is a pure function of its book and of one hour's quotes. The engine
imports it and passes it other `Rules`: the original and a variant then differ by declared numbers and by nothing
else. Same quotes, same fees and slippage, same ten slots.

**The archive.** The radar keeps 240 hours of quotes in the Actions cache and forgets the rest. Each cycle restores
that cache read-only and copies each finished day to `quotes/` on `perf-data`, once, with its hash. A day already
archived is never rewritten: a difference is reported. A day whose rows no longer match their hash is not replayed.

**The variants**, declared in code at 2026-11-14 20:00 UTC, before any replay was run:

| Variant | What changes | The weakness it answers |
|---|---|---|
| `original` | nothing | |
| `same-window` | the entry reads 24 hours, as the exit does | a spread that is already gone is entered and closed the next hour |
| `thick-entry` | the entry asks 50% a year, and 30% now | thin entries do not pay for their round trip |
| `patient-exit` | one hour at a reversed spread does not close a position unless it is below -100% a year | 118 exits on a single hour's reversal |
| `all-three` | the three together | |

A variant outside this list is refused. A new one is declared in code by the director, never invented by a run.

**The chronological validation.** Every variant is replayed on the same stored hours. The hours are cut in two at a
day boundary. The variant with the best excess over cash on the **earlier** part is the candidate; only the
**later** part judges it. Gates on the later part, all required:

| Gate | Threshold |
|---|---|
| Length | at least 30 days and 30 closed positions; otherwise INCONCLUSIVE and nothing is proposed |
| Excess over cash, by its own account | positive, t of the daily excess >= 3.0 |
| Against the original, on the same days | t of the daily difference >= 3.0 |
| Costs at 1.5 times | still positive |
| Without its best coin | still positive |

A variant that only loses less than the original fails the second gate and is not proposed
(`test_beating_the_original_by_losing_less_is_not_enough_to_pass`).

**Fidelity.** Before any variant is read, the replay of the original rules is compared with the radar's real ledger
on the same hours. If it does not reproduce it, the report says the table means nothing.

## 7. The challenger system

- A challenger is a variant **registered** with a preregistration, an hour and a look date: one line in
  `research/perf/challengers.json` and one in the registry. Today the list is empty (section 5).
- It is stepped beside the original every cycle. Both start from an empty book at the registration hour, and only
  hours after it count.
- It waits for its look (60 days). Then one verdict on every gate of section 6, plus the original's own: +10% a year
  on the capital deployed, a drawdown under 10%.
- The look is written once (`challenger-<id>-look.json`) and read back ever after, never recomputed on a later day.
- A challenger that passes is **proposed to the owner**. Nothing replaces RADAR-1 or TRND-1 by itself.

## 8. The cycle

`.github/workflows/perf-cycle.yml`: every three hours at :23, on GitHub's schedule (best-effort: runs start late or
are dropped). No person, no model, no key, no order.

1. reads `trend-desk-data` and `radar-data` (read only), and restores the radar's cache (restore only: the job
   contains no cache save and pushes to no branch but `perf-data`; both are pinned by tests);
2. reconciles both accounts;
3. attributes, names the largest weakness, and states the hypothesis the declared variants can test;
4. archives the quotes and replays (reused when the stored hours have not changed);
5. steps the registered challengers;
6. writes `PERF_REPORT.md`, `paper_audit.json`, `replay.json` and a line of `cycles.jsonl` to `perf-data`.

A cycle exits 1 after publishing when an account does not reconcile, a system's files are missing, the desk's
database cannot be read, or an archived day has changed. The run is red and the report says why.

## 9. What is not done, and what is not claimed

- No variant has been judged: the first replays are on about ten days of stored quotes, and the gates ask for thirty
  days on the later part alone. Until then the status is INCONCLUSIVE and nothing is proposed.
- A replay grows by five books a day of archive and is recomputed whole. At a few months of archive it needs a
  checkpoint.
- The radar's fees are the declared taker fees. A maker execution is not modelled and is not assumed.
- TRND-1 has no closed trade. Its trade statistics do not exist yet.
- Nothing here is a backtest result presented as validated, and no figure is added to a research result.
