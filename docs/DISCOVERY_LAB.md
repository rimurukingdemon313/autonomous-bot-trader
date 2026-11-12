# The discovery lab

**Research only. Nothing here trades, and nothing here is a profit claim.** The lab looks for rules in data, keeps
every rule it looks at, and sends the few worth it to a preregistered test. It is built to run by itself on GitHub's
runner (`.github/workflows/lab-cycle.yml`), with no person and no open conversation in the loop. What has actually
run there is in section 13, and nowhere else: a workflow file is not a running process.

Why it was built: `docs/DISCOVERY_AUDIT.md`. In short, the project had only ever tested ideas someone recalled, and
filtered most of them out before reading any data.

## 1. Two stages, kept apart

| | Discovery (a scan) | Validation (a judge) |
|---|---|---|
| Reads | The **fit** rows, then the **check** rows | The **validation** rows, which no scan has read |
| Asks | Which rules are worth a test? | Does this frozen rule earn a net return here? |
| Standard | None for significance. A rule must be causal, positive on the check rows, and distinct | t at least max(3.0, Bonferroni over every test on those rows), and every other gate |
| Registered as | role `select`, before it runs: `DLAB-<panel>-<n>` | role `judge`, before a validation row is loaded: `DLAB-<panel>-<n>-V` |
| Charged | 600 tests and 100,000 statistics against its own fit and check rows | One test for each rule judged, against the validation rows |
| Its verdict means | PASSED: it proposed rules. FAILED: it proposed none. Nothing about any rule | A rule passed, or it did not |

The statistical standard was not lowered. What changed is where it is applied. Asking significance of a discovery
screen (the earlier DP-001 and DP-002: 2,700 cells, none advanced) makes the screen blind. Asking nothing of it and
then judging its output on unread rows at the full bar keeps the test honest and lets the screen see.

**The firewall.** A panel's loader takes `last` and returns nothing at or after it. A scan loads with
`last = the check rows' end`: the validation rows are not in memory. `scan()` refuses a panel that holds one.

**What is frozen.** Each step freezes a spec and the sha256 of the lab's code, quotes both in a preregistration, and
registers before it runs. A scan or a judge whose code differs from what was registered refuses to run. Before a
batch is frozen, each of its rules is recomputed on the discovery rows and must give the figure the scan recorded
(`same_rules`): code that changed since the scan may not quietly turn a rule into another.

## 2. The panels and their rows

| Panel (universe) | Instruments | Fit | Check | Validation | Earlier tests counted on the validation rows | Bar |
|---|---|---|---|---|---|---|
| `energy-futures-eia` | WTI and natural gas, contract 2, rolled | 1994-03..2003 | 2004..2011 | 2012-01..2024-04 | 1 (ENG-1) | 3.0 |
| `crypto-perp-daily` | The 55 USDT-M perpetuals Binance listed by September 2020, with funding | 2020-05..2022-06 | 2022-07..2024-06 | 2024-07..2026-10 | 6 (funding carry: CR-1-V, CR-2, CR-4-V, CR-5, CR-5-H, RADAR-1) | 3.0 |
| `us-etf-broad-daily` | 31 US-listed funds that traded before 2007, across asset classes; the VIX as a state series | 2007..2014 | 2015..2019 | 2020-01..2026-10 | 21 (the multi-asset, US-equity, index and volatility programs) | 3.17 |

- A validation bar counts the tests of every universe that read the same market's returns under another name
  (`datasets.RELATED`), not only the panel's own.
- The crypto panel is chosen by listing date, not by what became of each coin: the coins that died are in it. A
  long's daily return is the price move less the funding it paid; a day whose funding is not on file has no return.
  Costs follow CR-3's: 7 basis points one way for BTC and ETH, 13 for the rest.
- XTS-1, FND-1 and XSM-1 reserved 2024-07..2026-09 as holdouts and failed before opening them. Those rows are unread,
  which is why the crypto validation window starts there.
- Funds: adjusted closes (total returns), 3 basis points one way. No bond fund is an instrument.

## 3. Eight ways of looking

Each method reads the fit rows only, emits its strongest rules oriented by those rows, and counts every statistic it
looked at.

| Method | What it looks for | Family |
|---|---|---|
| `leadlag` | One instrument's move followed by another's, after removing the follower's own past and the market (a partial correlation); the reverse direction is measured beside it | cross-asset lead-lag, own-lag |
| `info` | Information theory: what a feature's rank tells about the next return beyond the instrument's own last move (a transfer-entropy analogue, against circular shifts), and what two features tell only together (synergy) | information (non-linear) |
| `ordinal` | Whether the ordering of the last few returns changes the next one | ordinal pattern |
| `regimes` | Unsupervised learning: k-means regimes of the market's state, then each instrument's drift by regime | regime |
| `anomaly` | Rows whose joint shock is extreme (a Mahalanobis distance), then what follows | anomaly |
| `evolve` | An evolutionary search over small rule trees, with a penalty on size | evolved rule |
| `breadth` | **One rule traded on every instrument at once**: a cross-sectional book (the top of a ranking against its bottom, no net exposure); the same sign rule on each instrument's own feature; an evolutionary search whose fitness is the pooled book's | cross-sectional, pooled time-series |
| `combine` | Rules of different families joined on one instrument; one family's best rules pooled across instruments | combination, pooled book |

Why breadth matters: on one instrument's daily rows the lab can confirm only an edge with a gross Sharpe ratio of
about 1.5 or more (section 7). A real effect is rarely that large in one instrument. The same small effect in fifty
instruments, traded as one book, is one test with fifty times the data.

A rule is data, not code (`signals.py`): a plain JSON spec that gives a position at every row and can be recomputed on
rows it has never seen, with no parameter refitted. Every feature at row t reads rows up to t only, and every rule is
proved causal by truncation: its position at a row must be the same whether or not the later rows exist.

A position decided at a row's close earns the instrument's return to its next priced row, less the one-way cost on
every change of position and any holding cost (a futures roll). A missing price is never filled.

## 4. What becomes of every rule

Every emitted rule is evaluated once on the check rows and given the first class that applies. Nothing is deleted:
every rule, with its class, its reason, its figures and its plan, goes to `research/dlab/candidates.jsonl`.

| Class | It means | The mission's term |
|---|---|---|
| SCIENTIFICALLY_INVALID | It reads the future, or it only holds its instrument (no timing) | scientifically invalid |
| REPEATS_CLOSED_FAMILY | It behaves as a family the record has judged and closed, which is named | (a closed family under another name) |
| INSUFFICIENT_DATA | Too few rows in position, or too few entries, to estimate anything | insufficient data |
| NEGATIVE_EXPECTANCY | It lost on the check rows: before costs, or only after them (said which) | negative expectancy |
| OVERFIT | Strong on the rows that shaped it, gone on the rows that did not | overfitting |
| DUPLICATE | It behaves as a stronger rule already kept, which is named | (the diversity mechanism) |
| INSUFFICIENT_POWER | Positive on the check rows, but too small to pass its validation as it stands. **It gets a plan** | insufficient statistical power |
| PROMISING_UNCONFIRMED | Positive in both halves of the check rows, distinct, and at least 1 chance in 4 to pass | promising but unconfirmed |

Two estimates decide the last two classes. Both are estimates, never tests:

- **The chance a rule is real**: one less its false-discovery rate against the run's own noise, counting every
  *distinct behaviour* the run looked at (twenty variants of one behaviour are one look) and every look earlier scans
  took at the same rows.
- **Its strength if real**: three quarters of its check-row t (the winner's curse).

**The plan** of an INSUFFICIENT_POWER rule says what would make it testable: how many more years of rows, how many
independent instruments with the same mechanism, or whether its family's pooled book already carries it.

**A place that costs nothing is not withheld.** The bar is max(3.0, Bonferroni over every test on the validation
rows). While those tests are few (18 or fewer, the batch included), a rule added to the batch leaves the bar at 3.0.
Such a place goes to the next strongest rule that is positive in both halves of the check rows and has at least a 3%
estimated chance, promising or not. It keeps its class and its plan and is judged like any other. The calibration
study is why: real planted rules whose check-row t was a modest 2.0 to 2.7 went on to validate at t 3.8 to 4.6, and
a triage that withheld them would have spared the test nothing. The crypto panel has twelve such places; the fund
panel has none (21 tests are already counted on its validation rows).

## 5. What keeps the search diverse

- **Sameness is behaviour, not wording.** Two rules whose check-row returns correlate 0.7 or more are one behaviour;
  the stronger is kept and the other names it.
- **A batch is spread.** At most 12 rules go to a validation: at most 3 a family and 4 an instrument, whether a
  rule is there as promising or in a place that costs the bar nothing.
- **Closed families are recognised by what they do.** Each family the record has closed is stated as a rule
  (`datasets.closed`): trend following, single-coin and cross-coin momentum, funding carry, volatility-managed
  exposure, ENG-1, LIQ-1. A discovery that behaves like one is named and stopped, whatever it is called.
- **Effort follows the record and never reaches zero.** Each method's room in the next scan is drawn from its
  families' record on that market (Thompson sampling, `brain.py`): what validated gets more, what overfitted gets
  less, and none falls below a floor.
- **Later looks cost more.** A second scan of the same rows is judged against the first scan's looks too.

## 6. The validation

Each rule in a batch is judged once, on its own, and passes only if every gate holds:

| Gate | Rule |
|---|---|
| t | The Newey-West t of its net return on the validation rows is at least the bar |
| costs_x2 | Its mean net return is positive with every cost doubled |
| one_row_late | Its mean net return is positive entered one row late, for a rule that holds three rows or more on average. For a faster rule the figure is reported and is not a gate: entered a row late, a one-row rule is another rule |
| halves | Its mean net return is positive in each half of the validation rows |
| beats_random | It beats the 95th percentile of 1,000 books that hold its own positions shifted in time: the same exposure and turnover, no timing |
| top_year | No calendar year gives more than 35% of its total. Where a year holds so many of the window's rows that this cannot be asked, the limit is the year's share of the rows plus two standard errors of that share for a rule at t 3.0 (`year_cap`): 35% over twelve years, 65% for a year that is a third of the window, 76% for 2025 in the crypto window |

Also reported for each rule: the mean, the gross mean and the costs, the Sharpe ratio, a block-bootstrap 95% interval,
the worst fall, the exposure, the entries a year, and each year.

A rule that fails is REJECTED_BY_VALIDATION and its family is closed on those rows. A rule that passes is
VALIDATED_ON_UNREAD_ROWS: a candidate for the owner, marked forward on paper by the lab. It trades only on the
owner's word, on paper, through the risk engine, the hard gate and the paper broker.

## 7. What the lab can and cannot find

Measured on built markets, where the answer is known (`python scripts/dlab.py oc`, and `oc --broad`).

**One instrument at a time** (three instruments; ten years of fit rows, eight of check, twelve of validation; 12
runs each; `research/dlab/operating_characteristic.json`):

| Market | Runs that promoted a rule | Runs in which the planted rule validated | Noise rules validated |
|---|---|---|---|
| Nothing planted | 1 of 12 | — | 0 |
| Lead-lag, correlation 0.03 (gross Sharpe about 0.5) | 2 of 12 | 0 | 0 |
| Lead-lag 0.05 | 2 of 12 | 0 | 0 |
| Lead-lag 0.08 (about 1.3) | 8 of 12 | 2 | 0 |
| Lead-lag 0.12 (about 1.9) | 12 of 12 | 10 | 0 |
| A U-shape with no linear trace, 0.15 | 6 of 12 | 1 | 0 |
| A regime drift, 0.06 | 4 of 12 | 0 | 0 |
| A shock reversal, 0.5 | 2 of 12 | 0 | 0 |

No noise rule was validated in any run. On one instrument, only an edge of gross Sharpe about 1.5 or more is found
and confirmed.

**A broad panel** (24 instruments; 790 fit rows, 730 check rows and 850 validation rows, as the crypto panel has; 6
runs each; twelve places in each batch cost the bar nothing; `research/dlab/operating_characteristic_broad.json`).
The study plants one small effect in every instrument, a one-day cross-sectional reversal, which only a book of all
of them can carry:

| Market | One-way cost | Rules judged, by run | Runs in which a pooled rule validated | Noise rules validated |
|---|---|---|---|---|
| Nothing planted | 0.5 bp | 0, 2, 3, 2, 11, 1 | — | 0 |
| Correlation 0.01 in each instrument (the book's gross Sharpe about 0.8) | 0.5 bp | 5, 2, 1, 6, 7, 3 | 0 of 6 | 0 |
| Correlation 0.02 (about 1.6) | 0.5 bp | 8, 5, 2, 4, 12, 5 | 0 of 6 | 0 |
| Correlation 0.03 (about 2.3) | 0.5 bp | 12, 5, 4, 10, 12, 5 | 3 of 6 | 0 |
| Correlation 0.03, at a cost of 5 bp | 5 bp | 0, 2, 1, 0, 0, 2 | 0 of 6 | 0 |

What it says:

- No noise rule was validated in any of the 30 runs, although 132 rules were judged. The places that cost the bar
  nothing did not buy a false discovery.
- With three and a half years of validation rows, a pooled effect needs a gross Sharpe ratio above about 2 to be
  confirmed even half the time. At 1.6 it was confirmed in none of six runs.
- Costs decide. The same effect that validated in three runs of six validated in none at a one-way cost of 5 basis
  points: a book that must trade every day to earn a one-day effect pays more than the effect.
- The study changed the design before any real validation ran. The first version validated nothing even at 0.03: a
  flat 35% limit on one year's share failed real rules in a short window, and the triage withheld real rules whose
  check-row t was modest. Both were corrected (sections 4 and 6), and the same study then confirmed the effect.

## 8. The autonomous worker

```
GitHub's schedule (four slots a day)            workflow_dispatch (by hand)
              \                                   /
               .github/workflows/lab-cycle.yml
                 1. restore state/ from branch lab-data        (every run is a restart)
                 2. python scripts/lab_cycle.py --state state
                      integrity ─ fails ─► alert, report, stop: no experiment
                      queue what is due      data · scan · sources · forward
                      order it               brain.py: the record decides
                      run tasks              inside the budget; each marked STARTED then DONE or FAILED
                      learn                  research/dlab/lessons.json
                      alerts, report         an issue on the repository; LAB_REPORT.md
                 3. commit the record to main                 (registry, specs, preregistrations, evidence, ledger)
                 4. publish state/ and LAB_REPORT.md to lab-data
```

| Requirement | How it is met |
|---|---|
| Persistent database | Append-only tables of JSON lines, carried on `lab-data` (`store.py`): `queue`, `runs`, `sources`, `hypotheses`, `forward`, `alerts`, `budget`. Nothing is rewritten |
| Scheduled cycles | Four cron slots a day and a manual trigger. GitHub's cron is best-effort; a cycle with nothing due does nothing |
| Autonomous task queue | A task's state is the fold of its events. A task is known by its id and is queued, and run, once |
| Checkpointing | Each step and each task is logged as it finishes (`runs`); a scan registers before it runs and resumes if it died after registering |
| Recovery | A task STARTED six hours ago with nothing after it died with its machine and is taken up again. A failed task is retried by later cycles, three times at most, then reported. A scan whose record reached `main` while its queue entry did not is resumed, not repeated |
| Prioritization | Validation first, then data, forward marks, scans by breadth and by what the market's earlier rules were worth, then sources |
| Data acquisition | `feeds.py`: Binance's public archive (every file against its published checksum; only the months not yet held), Yahoo's chart endpoint, arXiv and OpenAlex. A file the archive did not answer for is counted and asked for again; what arrived is kept |
| Data quality | Each feed writes a manifest: content hash, rows, first and last day, missing days, one-day moves beyond 50% (flagged, never removed), and `incomplete`: why the files are not a whole panel, or nothing. A thin panel is refused, and so is one without the fit rows a scan needs |
| Budget | A cycle has a task count and a time budget; a task is not started without the time it may need. No model call and no paid service |
| Automatic experiments | A scan of each panel under each version of the lab; the validation of any batch it proposes |
| Automatic reporting | `LAB_REPORT.md` on `lab-data`, rewritten every cycle, with an Arabic summary |
| Alerts | An issue on the repository for a rule that passed its validation, a record that failed its integrity check, or a task that failed on every attempt. Raised once, sent once |
| Research-source database | `sources`: each paper's link, date, authors, abstract, the query that found it, and a status. A source is UNREAD until its claim is checked: nothing is claimed about a paper from its abstract |
| Hypothesis genealogy | A rule's `parents` are the rules it was built from (a combination, a book); a hypothesis's are the sources it came from |
| Duplicate detection | By id (the same spec is never classed twice) and by behaviour (section 5) |
| No self-approval | The lab approves nothing. A rule is validated only by a preregistered test on unread rows; the integrity check stops a cycle whose record no longer matches its hashes |

**Whole data, or a wait.** A scan and a validation each run once, so neither may start on data with a hole in them.
The worker waits (a wait is in the report and is not one of a task's three attempts) while:

- a file the archive did not answer for is still missing;
- the newest month is published for some instruments and not for the others: an instrument alive (priced and funded)
  on the last day of the month before, without the month's prices or without its funding. A month is asked for only
  from the tenth of the next one. A delisted contract is not waited for: the archive goes on printing its last price
  every day (nine of the fifty-five on 2026-11-12, one for 499 days), and those days make no return, because a day
  without funding has none. The worker's first run waited for eight of them; lab-cycle-1.0.1 does not;
- a fund was not served, or was served with a series that stops more than seven days before the calendar's last day.
  The fund panel on file is then left exactly as it was: it is never rewritten without one of its instruments;
- for a validation: the files stop more than five days before its window's end. The judge checks the loaded panel
  again and refuses it (`covers` in `scripts/dlab.py`): a batch judged on a shortened window could never be judged
  again.

The forward marks follow the same rule and one more: before a mark is written, each validated rule is recomputed on
its validation rows, exactly as its judge loaded them, and must give the t the judge recorded. If it does not, the
data or the code have changed since: no mark is written, and the task fails for a person to look (one alert a month,
not one a day).

**Rehearsed before it was deployed.** The whole cycle was run in a copy of the repository on built data of the real
panels' shape (55 perpetuals by month from 9,460 archive files, 31 funds and the VIX), through the real parsers, the
real registry and the real report: once on a market with nothing in it, where neither scan proposed a rule, and once
with an effect planted, where the scan proposed five rules and the validation passed three. A scan of either panel
takes under a minute. That rehearsal is what found the holes the list above closes. It says nothing about any real
market.

**Integrity, each cycle, before anything else.** The seal is the pinned one; the registry loads; every verdict's
evidence has the hash recorded with it; every preregistration quotes its spec; every run in the candidate ledger is a
registered, judged scan and holds exactly as many rules as its evidence. If any of these fails, no experiment runs.

**What a cycle may write to `main`:** `research/registry.jsonl`, `research/specs/DLAB-*.json`,
`research/preregistrations/DLAB-*.md`, `research/knowledge/DLAB-*.json` and `research/dlab/`. Nothing else.

## 9. The stages of a claim

| Stage | In this lab | Where it is recorded |
|---|---|---|
| An interesting hypothesis | A rule a method emitted | `candidates.jsonl`, any class |
| A promising result | PROMISING_UNCONFIRMED: positive on the check rows in both halves, distinct, 1 in 4 to pass | the scan's batch |
| A statistically credible edge | VALIDATED_ON_UNREAD_ROWS: every gate at the registry's bar | `research/knowledge/<run>-V.json` |
| A robust executable strategy | Not the lab's to declare: the forward paper marks, then a desk built through the risk engine | `forward` on `lab-data`; a paper desk only on the owner's word |
| A paper-trading system | As TRND-1's trend desk is | `docs/TREND_DESK.md` |

## 10. Limits, stated plainly

- **Crypto's history is short.** With 28 months of validation rows, only a rule with a net Sharpe ratio of about 2
  or more reaches t 3.0. Most real effects are smaller: they will be classed INSUFFICIENT_POWER and given a plan, not
  validated.
- **Costs decide.** At 13 basis points one way, a book that trades every day needs a large gross edge. Slow books
  (held 5 or 20 rows) are in the search for that reason.
- **Tradability is a separate question.** The owner's account is a swap-free CFD account. A book of fifty perpetuals,
  long and short, is not tradable there; it would need an exchange account, and until the owner says otherwise it is
  research and paper only.
- **Short selling a fund has a borrow cost** the fund panel's cost model does not carry. The doubled-cost gate is the
  margin for it.
- **One scan for each panel and each version of the lab.** The lab does not re-read the same rows under the same
  methods. New experiments come from new panels and new methods, which are code.
- **GitHub's schedule is best-effort.** A slot may fire hours late or not at all. The cycle is built so that this
  costs time and nothing else.
- **No model is in the loop.** The idea engine (`scripts/research_engine.py`) still proposes from recall once a day
  and is kept apart. From engine 1.2.0 the lab's lessons are in its proposer's context.

## 11. What is next

1. The perpetuals' scan, and the validation of anything it proposes (the lab's own queue). The funds' scan is done:
   it proposed nothing (section 13).
2. Volume in the crypto panel: each day's quote volume from the same archive, as a dollar-volume and an illiquidity
   state series. Nothing in this project has used volume (`docs/RESEARCH_SOURCES.md`, hypothesis H5).
3. More panels: the hours inside each crypto day; commodity and rate futures.
4. A deflated Sharpe ratio reported beside each validation (method M1 of the same document).

Done with the lab, from the same audit: the idea engine's critic and power gate, and near-misses recorded as
promising (`docs/DISCOVERY_AUDIT.md`).

## 12. Files

| File | What it holds |
|---|---|
| `aitrader/research/dlab/panel.py` | The panel and its causal features |
| `aitrader/research/dlab/signals.py` | Rules as data, their P&L, the causal proof |
| `aitrader/research/dlab/methods.py` | The eight methods |
| `aitrader/research/dlab/triage.py` | The classes, the two estimates, the plan, the ledger |
| `aitrader/research/dlab/datasets.py` | The panels, their windows, related universes, closed families |
| `aitrader/research/dlab/feeds.py` | What the lab fetches by itself |
| `aitrader/research/dlab/store.py` | The persistent tables and the task queue |
| `aitrader/research/dlab/brain.py` | What the record teaches: allocation, priorities, lessons |
| `scripts/dlab.py` | A scan, a validation, the calibration studies |
| `scripts/lab_cycle.py` | One cycle of the worker |
| `.github/workflows/lab-cycle.yml` | The schedule |
| `tests/unit/test_dlab_*.py`, `tests/unit/test_lab_cycle.py` | Built markets where each answer is known by construction |
| `research/dlab/candidates.jsonl` | Every rule ever classed |
| `research/dlab/lessons.json` | What the record has taught |

## 13. Deployment status

Only what was confirmed is written here.

| Date (UTC) | What | Evidence |
|---|---|---|
| 2026-11-10 | DLAB-ENG-1, the first scan, run by hand under dlab-1.0.0: 102 rules classed, none promising | `research/knowledge/DLAB-ENG-1.json` |
| 2026-11-12 | The worker rehearsed end to end in a copy of the repository, on built data of the real panels' shape (section 8) | not evidence about any market |
| 2026-11-12 15:46 | The worker's first run on GitHub's runner, started by hand (`workflow_dispatch`): run 1 of `lab-cycle.yml`, id 43251484761, every step green, 11 minutes | It fetched 8,384 archive files of the perpetuals (each against its checksum; 1,076 months do not exist) and the 31 funds with the VIX; registered, ran and recorded **DLAB-ETF-1**; filed 85 new papers as UNREAD; pushed commit `4c5db29` to `main` by itself (two registry lines, the spec, the preregistration, the evidence, 266 candidates, the lessons); created `lab-data` (`282274f`) with its memory, the data and `LAB_REPORT.md` |
| 2026-11-12 | The perpetuals' data in that run | **Refused by the worker, and rightly stopped, for the wrong reason.** Eight delisted contracts the archive still prices were taken for a half-published month. Nothing was scanned on them. Fixed in lab-cycle-1.0.1, and checked against the files that run fetched: none is waited for, 44 contracts are alive at 2026-10-31, all 55 have the fit rows a scan needs |
| | A run started by GitHub's schedule | **Not confirmed yet.** The workflow reached `main` at 15:46 UTC; its 21:11 slot had not fired by 23:30. This repository's other schedules run two to nine hours late. This line is replaced when a run with the event `schedule` is seen |

### Results so far

| Scan | Panel | Statistics looked at | Rules kept | Promising | Best check-row t | Verdict |
|---|---|---|---|---|---|---|
| DLAB-ENG-1 | WTI and natural gas, 1994-2011 | 2,015 | 102 | 0 | 1.43 | proposed nothing |
| DLAB-ETF-1 | 31 US-listed funds, 2007-2019 | 15,349 | 266 | 0 | 1.70 | proposed nothing |

No rule has reached a validation. Neither validation window has been loaded. In the funds' scan 102 rules lost on the
check rows, 55 of them only after costs, and the rules' check-row t are centred at -0.56: on that panel the average
rule the methods find loses after a 3 basis point cost.
