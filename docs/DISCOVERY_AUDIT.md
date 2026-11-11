# Audit of the discovery process (2026-11-10)

**Research only.** This audit was ordered after the autonomous engine's first production cycle produced three
hypotheses and kept none: two were rejected by the critic and the third was dropped for power. It reads the actual
implementation, not its description. What was built in answer is `docs/DISCOVERY_LAB.md`.

## The finding, in one paragraph

Nothing in this project ever looked at data to find a hypothesis. Every idea came from recall: a language model's, or
a person's reading of the literature. Each idea then met three filters that could only subtract (a critic, an
arithmetic power gate, and a hand-kept queue), all of them final, all of them run before any data were read, and one of
them wrong on both of the occasions it was used. The one earlier attempt at a data-driven screen asked for statistical
significance at the discovery stage, where almost nothing can have it. So the process could only ever test what
someone had already written about, and it stopped most of that before testing it.

## What was inspected

| Part | Where | What it does |
|---|---|---|
| The idea engine | `scripts/research_engine.py` (`Engine.generate`, `decide`, `power`, `bars`, `fingerprint`) | Asks one model for at most three hypotheses a day, asks another to reject, drops what cannot reach its bar |
| The critic | the same file (`CRITIC`, `validate_review`) | A second model that can only reject |
| The hand-kept queue | `research/QUEUE.md` | Ideas from the literature, dropped or queued by a power estimate |
| The earlier screen | `aitrader/research/discovery/` (9,767 lines), programs DP-001 and DP-002 | A grid of cells screened with a false-discovery-rate threshold at discovery |
| The classifier | `aitrader/research/discovery/edges.py` (`build`, `from_single`) | Turns every verdict into an edge status |
| The record | `research/registry.jsonl`, the engine's `ideas.jsonl` on `research-data` | What was tested, and what was proposed |

## The weaknesses

### 1. The only source of ideas was recall

- `Engine.generate` sends one prompt to one model. `MAX_IDEAS = 3` a day. Its context is a list of what is closed and a
  fixed list of lessons (`LESSONS`), written by hand.
- No function anywhere computes anything from prices to propose a rule. The 53 ideas in `research/QUEUE.md` and the
  three in `ideas.jsonl` all restate a published or well-known effect.
- Consequence: the search space was the literature. Published effects are the most arbitraged ones, and a model's
  recall of them is the same every day. The first cycle's three ideas (central-bank intervention, the oil inventory
  surprise, central-bank gold buying) are all textbook.

### 2. The critic's verdict was final, and it was wrong both times

- A rejected idea is recorded `REJECTED_BY_CRITIC` and is never looked at again (`decide`).
- Both rejections of the first cycle gave the same reason: *"Violates owner's swap-free/no interest-bearing instrument
  condition (requires short selling and leverage)."* That is false. A swap-free account pays no overnight interest; it
  allows both short selling and leverage. The critic invented a constraint, and nothing could overrule it.
- The critic had no category to choose from and needed no evidence. Any sentence was accepted as a reason.

### 3. The power gate was final, used the idea's own guess, and wrote no plan

- `power()` is the claimed annual Sharpe ratio times the square root of the years of fresh data. Both numbers are the
  proposer's guesses.
- `bars()` asks the registry for a universe's bar over its whole life (`tests_on(u)` with no window). A test on rows
  from 1994 raises the bar of a test on rows from 2025. After the lab's first scan charged 400 tests to energy's
  discovery rows, this function would have shown an energy bar no idea could reach, on rows the scan never read.
- An idea below its bar became `DROPPED_POWER` and disappeared. Nothing said what would make it testable: more
  instruments, more years, or a pooled test.

### 4. The hand-kept queue dropped ideas on estimates that proved low

- 53 ideas were dropped before any test: 21 for power, 13 on prior evidence, 7 on cost, 5 on data, 3 as duplicates and
  4 as invalid.
- Two ideas first dropped for power were tested later anyway. They reached t 2.48 (DAY-1) and t 2.71 (FXT-1): short of
  3.0, but far above what their drop estimates had allowed. The estimates were not conservative; they were wrong, and
  they were the only gate between an idea and its data.

### 5. The one data-driven screen asked for significance at discovery

- DP-001 screened 1,734 cells and DP-002 966, and passed on a cell only at a false-discovery rate of 10% or less
  *within the screen*.
- Zero of 2,700 cells advanced. A real effect of ordinary size cannot clear a 2,700-way correction on one window.
  Discovery and validation were one step, held to validation's standard, so discovery found nothing.

### 6. The classifier erased near-misses

- `from_single` marks every single-program verdict that is not PASSED as REJECTED.
- DAY-1 (t 2.48), FXT-1 (t 2.71) and TME-1 (t 2.24) each failed on the t alone, with every other gate held. They are
  recorded exactly as a rule that lost money is.
- Consequence: the three results closest to an edge are invisible to anything that reads the classification.

### 7. Nothing kept the search diverse

- `fingerprint` is a hash of the universe, the horizon and the rule's sorted words. It stops the same sentence, not the
  same behaviour: two rules with different words and identical positions are two ideas.
- No quota across mechanisms, markets or methods. The registry shows the result: 176 of its tests are on the FX
  majors, and the families tested are few (carry, momentum, trend, calendar, session, funding).

## The hidden biases, named

| Bias | Where it came from | Its effect |
|---|---|---|
| Conventional concepts | Every idea was recalled, by a model or from the literature | Only published effects were ever candidates |
| Thresholds from the whole record | `bars()` ignored the window | A market's past tests blocked tests on rows they never touched |
| Explored markets | FX data were at hand from the start | 176 tests on one market; almost none on a broad panel of anything |
| Narrow categories | Rules were written as single-instrument timing rules | No cross-sectional rule, no pooled test, no rule found by search |
| Early stopping | Three final filters before any data | An idea's first estimate was its last |
| One instrument at a time | Each program tested one rule on one or two instruments | No use of breadth, which is what gives a small effect a test it can pass |

## What was changed

| Weakness | Answer | Where |
|---|---|---|
| 1. Recall only | Eight methods that read data and emit rules, none of which asks for significance | `aitrader/research/dlab/methods.py` |
| 5. Significance at discovery | Discovery and validation are separate, registered steps on separate rows | `scripts/dlab.py`, `docs/DISCOVERY_LAB.md` |
| 3, 6. Ideas that disappear | Every rule is kept for ever with one of eight classes and its reason; a rule that is positive but underpowered gets a written plan | `aitrader/research/dlab/triage.py`, `research/dlab/candidates.jsonl` |
| 7. No diversity | Duplicates are found by behaviour, not by words; a validation batch is capped by family and by instrument; closed families are recognised by behaviour; effort follows each family's record and never falls to zero | `triage.py`, `datasets.closed`, `brain.py` |
| One instrument at a time | Rules traded on every instrument of a broad panel at once | `methods.breadth` |
| No autonomous operation | A scheduled worker with a persistent queue, checkpoints, recovery and a report | `scripts/lab_cycle.py`, `.github/workflows/lab-cycle.yml` |

The statistical standard was not lowered. A rule is validated only by a preregistered test on rows no scan has read,
at the larger of 3.0 and the Bonferroni bar over every test on those rows.

## What this audit does not change yet

The idea engine itself (weaknesses 2 and 3) and the classifier (weakness 6) are still as described. Their fixes are
listed in `docs/DISCOVERY_LAB.md` under what is next: a critic whose rejection needs a category and can be overruled
when it contradicts the stated rules, a power gate that writes a plan and reads the window's bar, and near-misses
recorded as promising and unconfirmed.
