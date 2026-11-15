# One research pipeline, directed by a model and judged by tests

**Research only. Nothing here trades, and no model approves anything.** This file says how the discovery lab and the
idea engine became one pipeline, who directs it, and what is still missing. Only what was confirmed is stated as done.

## 1. The audit that came first (2026-11-13)

Each finding the owner listed was checked against the repository before anything was changed.

| Finding | Checked against | Verdict |
|---|---|---|
| The discovery lab and the research cycle are separate systems | Two workflows, two state branches (`lab-data`, `research-data`); the only link was the lab's lessons in the engine's prompt | **True.** No idea ever became an experiment |
| The lab's scheduled execution is not verified | Actions: `lab-cycle.yml` run 4, event `schedule`, started 2026-11-13 01:47:58 UTC, every step green | **Outdated.** [Run 43347545811](https://github.com/rimurukingdemon313/autonomous-bot-trader/actions/runs/43347545811) was started by GitHub's schedule, not by a person |
| The research queue has been empty | `LAB_REPORT.md`: no task since run 2 | **True, and by construction.** Tasks came only from a fixed catalog: data, one scan a panel, sources. Nothing could submit a hypothesis |
| The hypothesis generator and the discovery engine are disconnected | `scripts/research_engine.py` wrote text to `ideas.jsonl`; nothing read it | **True** |
| AI-generated ideas have a high rejection rate | `ideas.jsonl`: 9 ideas, 8 rejected by the critic, 1 dropped for power, 0 built | **True** |
| Hundreds of discovered rules have not reached validation | `research/dlab/candidates.jsonl`: 634 rules, 143 positive and not told from noise, 0 validations | **True, and correct one rule at a time.** What was missing is a question about them as a whole |
| Research-source coverage is incomplete | 85 sources filed by the worker, all UNREAD; 21 read from search summaries only | **True** |
| Fable 5.2 is not the research intelligence | No model in the lab's loop; the engine used free models only | **True** |
| "84 registered hypotheses" | `research/registry.jsonl` | 85 on that day |

## 2. What changed

```
        the research director (a model session)          the idea engine (free models)        the lab's coverage map
                     |                                             |                                    |
                     +------------------  research/director/inbox/<id>.json  ----------------------------+
                                                         |   a hypothesis, written as rules
                                                 the lab's worker (deterministic code, no model)
                         ingest: taken as written, or refused with reasons (nothing is repaired)
                                                         |
                                  directed test: rules checked on the fit rows, frozen, preregistered,
                                  registered, looked at once on the check rows, classed (the scan's triage)
                                                         |
                                  validation: the promising rules, judged once on rows nothing has read
                                                         |
                       ledger, lessons, coverage map, LAB_REPORT.md, DIRECTOR_BRIEFING.md  ->  the next decisions
```

- **One queue.** Every experiment is a task with an id, a state (QUEUED, STARTED, DONE, FAILED), an owner (the worker),
  an origin (who asked: the lab, the director, the engine), a priority, at most three attempts, and its attempts back
  once under a new version of the worker. A task is never run twice. A submission that cannot be tested is answered
  once, as REFUSED, and is not a failure.
- **Directed tests** (`scripts/dlab.py`: `auto_directed`). A hypothesis arrives as rules in the lab's rule language
  (`aitrader/research/dlab/signals.py`). Before anything is registered, each rule is checked on the fit rows alone: it
  must be computable, causal, active, not already classed, and not a closed family by what it does. What survives is
  frozen and preregistered, charged one test for each rule, looked at once on the check rows, and classed against
  every look already taken at those rows. Promising rules go to the same validation a scan's batch meets.
- **The lab asks its own questions, and only justified ones** (`aitrader/research/dlab/coverage.py`). A scan gives its
  places by strength, which leaves holes. The worker maps a declared space (each ranking a cross-sectional book may be
  built on, at each holding period), and gives itself one task: a directed test of the cells no classed rule sits in.
  When the map has no hole it gives itself nothing, and the report says why the queue is empty.
- **An aggregate is a rule.** A book's parts may carry shares, so "every weak positive of a scan, held together" is one
  rule and one test (`aggregate_of`). Its rules were chosen on the check rows: it is flagged so, and only a validation
  can judge it.
- **The briefing** (`DIRECTOR_BRIEFING.md` on `lab-data`, written every cycle): what waits for a review, the coverage
  map, the record, the queue, the sources, and how to submit.

## 3. Who directs, stated exactly

| Question | Answer | Evidence |
|---|---|---|
| Which model directs? | Fable 5.2 (`claude-fable-5-2`) | `get_session` on 2026-11-13: `session_context.model` and `last_served_model` are both `claude-fable-5-2` |
| Through what interface? | A persistent Claude Code session with a scheduled routine (11:26 and 23:26 UTC). It fires without the owner opening anything | The routine fired on 2026-11-12 at 11:26 and 23:26, on 2026-11-13 at 11:26 and 23:26, and on 2026-11-14 at 11:26 and 23:26. A firing waits when the session's machine is restarting: those of 2026-11-13 23:26 and 2026-11-14 11:26 were read 19 and 7 hours late. The lab's worker does not depend on it |
| What does it do? | Reads the briefing and the record, reviews results, finds what was missed, writes hypotheses as rules into the inbox, and records each decision in `research/director/log.jsonl` | The first entries are in that file |
| Is the model called by the GitHub workflows? | **No.** There is no API key in the repository, and the owner's rule is that no money is spent without their word. A workflow cannot call Fable 5.2 today | A key as a repository secret and the owner's approval of the cost would change this; the inbox is already the interface such a caller would write to |
| What does the model never do? | Compute a statistic, change a registered spec, or approve a rule | Statistics are code; approval is a registered test on unread rows |
| Who reviews the director? | The worker's checks before registration, the triage, the validation's gates, and (through the idea engine) a critic model from another family that can only reject | |

## 4. The loop, and where each step lives

| Step | Where | State |
|---|---|---|
| Global research | `feeds.papers` (arXiv, OpenAlex), weekly, by the worker | running: 85 sources filed |
| Knowledge extraction | not built: sources are UNREAD until a finding is extracted from the text | **missing** |
| Gap detection | `coverage.py`; the briefing | running from lab-cycle-1.1.0 |
| Hypothesis generation | the director (inbox); the lab's coverage test; the idea engine (text only, for now) | the first two run |
| Mathematical specification | the rule language; the frozen spec of each directed test | running |
| Data validation | `directed_rules`: on the fit rows only | running |
| Experiment generation and execution | `ingest`, `coverage_tasks`, `do_directed` | running |
| Adversarial review | the triage (noise of every earlier look, duplicates, closed families), then the validation's gates | running |
| Independent validation | `auto_validate`: unread rows, the registry's bar | built and tested; no real rule has reached it yet |
| The same loop for the paper systems | `scripts/perf_cycle.py`: reconcile, attribute, name the weakness, replay the declared variants, judge on later hours | running from perf-1.0.0 (`docs/PERFORMANCE_ENGINEERING.md`) |
| Knowledge update | ledger, lessons, coverage map, the director's log | running |
| The record read together | `scripts/research_meta.py`: the 88 hypotheses, the 143 judged edges and the 660 classed rules, from the committed record alone; the director's reading beside it | `docs/RESEARCH_META_ANALYSIS.md` |

## 5. The first cycle that ran by itself

Everything in section 2 ran on GitHub's schedule two hours after it was pushed, with no dispatch and nobody watching:
run 7 of `lab-cycle.yml`, id 43512116913, event `schedule`, 2026-11-13 21:35 UTC
(<https://github.com/rimurukingdemon313/autonomous-bot-trader/actions/runs/43512116913>).

| Step | What happened in that run | Record |
|---|---|---|
| Gap detection | the coverage map of each panel: 14 and 12 cells with no classed rule | `DIRECTOR_BRIEFING.md` on `lab-data` |
| Hypothesis | the lab's own submission for each panel, one rule a hole | `research/specs/DLAB-CRD-D1.json`, `DLAB-ETF-D1.json` |
| Data validation, on the fit rows only | 14 rules refused before any test: 12 behave as cross-coin momentum (XSM-1), 2 as the funds' momentum (SEC-1). No test was charged for them | `refused_before_registration` in each evidence file |
| Registration | DLAB-CRD-D1 (14 tests) and DLAB-ETF-D1 (12 tests), each with its preregistration written before a check row was read | `research/registry.jsonl`, `research/preregistrations/` |
| Execution | each rule looked at once on the check rows | `research/knowledge/DLAB-CRD-D1.json`, `DLAB-ETF-D1.json` |
| Adversarial review | classed against 174 and 148 earlier distinct behaviours: 0 promising, 5 positive and not told from noise, 18 lost, 3 duplicates | the same files; `research/dlab/candidates.jsonl` |
| Independent validation | not reached: neither test proposed a rule, and a validation is never run for its own sake | |
| Knowledge update | 26 candidates added to the ledger (660 in all), the lessons and the map updated: no hole left | commit `a286851`, pushed by the worker |
| Next research | none queued, with the reasons written in the report. The three scheduled runs after it (8, 9, 10) did nothing and said why | `LAB_REPORT.md` on `lab-data` |
| The director's review | read on 2026-11-14: a review of both tests, and a decision **not** to submit the aggregate planned the day before, with its arithmetic | `research/director/log.jsonl` |

What this cycle did not show, because nothing earned it: a validation on unread rows. That code has run on built
markets (`tests/unit/test_dlab_directed.py`, `test_lab_cycle.py`) and in rehearsal, and on no real rule.

## 6. What is not done

- The idea engine still writes text. Its ideas must arrive as rules in the inbox, or be recorded as needing new code.
- No finding is extracted from a source's text. Titles and abstracts are filed, and nothing is claimed from them.
- The one experiment the collective reading of the record supports (costs charged on net trades, on the perpetuals:
  `docs/RESEARCH_META_ANALYSIS.md`, section 5) needs new code in the lab and is not built.
- No workflow calls Fable 5.2 (section 3). The director runs as a scheduled session, twice a day.
- No rule has passed a validation. Nothing here is a trading system.
