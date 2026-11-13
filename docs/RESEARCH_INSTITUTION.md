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
| Through what interface? | A persistent Claude Code session with a scheduled routine (11:26 and 23:26 UTC). It fires without the owner opening anything | The routine fired on 2026-11-12 at 11:26 and 23:26 and on 2026-11-13 at 11:26 |
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
| Knowledge update | ledger, lessons, coverage map, the director's log | running |

## 5. What is not done

- The idea engine still writes text. Its ideas must arrive as rules in the inbox, or be recorded as needing new code.
- No finding is extracted from a source's text. Titles and abstracts are filed, and nothing is claimed from them.
- No workflow calls Fable 5.2 (section 3). The director runs as a scheduled session, twice a day.
- No rule has passed a validation. Nothing here is a trading system.
