# Research protocol

These are the rules every hypothesis follows, from idea to promotion. The procedure behind
them is in [RESEARCH_PROCESS.md](RESEARCH_PROCESS.md), and the contract is in
[RESEARCH_CONTRACT.md](../RESEARCH_CONTRACT.md). This page gives the concrete values,
scripts and files, so a result can be checked by someone who was not there.

## 1. A hypothesis is written so it can fail

A hypothesis is a `Hypothesis` in `research/discovery/hypothesis.py`, or a `HypothesisSpec` in
`research/lab.py`. It states all of the following:

- the claim;
- the mechanism (conjectured unless documented);
- features;
- condition;
- side (BUY or SELL; each side is its own hypothesis);
- instruments;
- timeframe;
- a declared exit;
- the expected effect;
- the falsification rules;
- its origin: human, screen, model, LLM draft or loss lesson.

**It never carries a size.** This is enforced by `test_a_hypothesis_never_carries_a_size`.

## 2. Data roles are fixed in advance

| Role | Period | Used for |
|---|---|---|
| Lookback | from 2007-03-30 | Feature warm-up only |
| Fit | 2007-04/06 to 2011-01 (lab), or to 2013-07 (confirmatory) | Terciles, models and anything estimated |
| Select | 2011-01 to 2013-07 (discovery programs) | Choosing finalists |
| Judge | 2011-01 or 2013-07 to 2017-01 | The verdict. Nothing is fitted here |
| Holdout | 2017-01 onward | **Sealed.** One pre-registered final test of one candidate that passed everything else, with a single-use key |

- **Segment boundaries.** Rows whose outcome would cross a segment's end are purged. A 10-day
  embargo separates segments.
- **Walk-forward folds.** Each fold trains only on outcomes resolved before it, minus a 5-day
  embargo.

## 3. Costs are always charged

The cost model is `CostModel` in `research/labels.py`:

- the measured spread, paid on entry on the correct side of the book;
- slippage of 0.1 pip per fill;
- commission of 0.7 pip per round trip;
- swap per night of 0.05 × ATR24 on H1, or 0.01 × ATR24 on D1.

**Stress.** Spread and swap ×1.5, slippage ×2, and entry one bar late. The result must stay
positive under stress.

## 4. Pre-registration comes before any judged data is read

1. Write the document (`research/preregistrations/<ID>.md`) or the spec
   (`research/specs/<ID>.json`).
2. Register the trial with `Registry.register`. The record holds the design hash, the code
   hash, the periods used and the number of tests.
3. Freeze the threshold at `registry.threshold_for_next(universe, judge_start, judge_end,
   new_tests)`. This is a Bonferroni t over **every test ever run on that period**, the
   archive's included.
4. State the power: the smallest net mean the design can detect at that threshold.
5. Commit and push. Then run.

The thresholds so far:

| Trial | Threshold |
|---|---|
| DP-001 | t ≥ 3.078 |
| DP-002 | t ≥ 3.144 |
| CP-001 | t ≥ 3.180 |
| WF-001 | t ≥ 3.189 |
| WF-002 | t ≥ 3.197 |
| WF-003 | t ≥ 3.205 |
| SL-001 | t ≥ 3.248 |
| SL-002 | t ≥ 3.254 |
| XS-001 | t ≥ 3.267 |

The bar rises with every test. That is the point.

## 5. Each hypothesis runs once

The scripts are:

- `scripts/discover.py --program <ID>`
- `scripts/cp001.py run`
- `scripts/strategy_library.py run`
- `scripts/research_lab.py run <ID>`

A run is deterministic (fixed seeds) and resumable: a crash resumes, it does not re-draw. A
second run of the same trial reproduces the same numbers. A run with changed parameters is a
**new trial**, and it is counted.

## 6. What "passes" means

**Confirmatory and discovery programs.** Every check of the 12-check battery
(`research/discovery/battery.py`) must pass:

1. at least 100 trades;
2. t at or above the frozen threshold;
3. beats random entries, Welch t ≥ 2;
4. circular-shift permutation p < 0.05;
5. cost stress;
6. one-bar delay;
7. tercile perturbation;
8. at least 60% of years positive;
9. at least 60% of instruments positive;
10. leave-one-instrument-out;
11. no significantly negative regime cell;
12. the top 5% of trades carry less than half of the total R.

Then the five-analyst board must raise no blocking objection. There is no voting.

**Walk-forward lab** (`PassRules`). All of these must hold:

- positive mean;
- t at or above the threshold;
- at least 200 trades;
- beats random, t > 2;
- at least 60% of folds positive;
- positive under both robustness variants.

## 7. Recording, whatever the result

- **The registry verdict** goes in `research/registry.jsonl`, append-only.
- **The ledger lifecycle.** Each hypothesis moves through DRAFT → PREREGISTERED → JUDGED →
  VALIDATED or REJECTED (`research/discovery/ledger.jsonl`).
- **The knowledge artifact.** `research/knowledge/<ID>.json`, with the data, code and design
  hashes.
- **The edge registry** is rebuilt: `python scripts/edge_registry.py` →
  `research/knowledge/edge_registry.json`.
- **A summary** goes in `research/results/<ID>-summary.md` and a row in
  [EXPERIMENT_LOG.md](EXPERIMENT_LOG.md).

## 8. Forbidden

- Re-running a failed hypothesis with tweaked parameters under the same id.
- Choosing the exit, the threshold or the segment after seeing a result.
- Reading the holdout for anything but its one pre-registered final test.
- Repairing an AI draft, or letting an AI change a verdict. An AI may only draft hypotheses
  and object.
- Letting a strategy, an edge file or a research artifact carry a size, a risk amount or a
  limit. Only the risk engine sizes.
- Reporting a result without its sample size, its t, and the number of tests it competed
  with.

## 9. Promotion

Promotion is a person's decision:

1. VALIDATED in the edge registry;
2. passes the holdout;
3. the evidence has been read;
4. the edge is written to `models/artifacts/promoted_edges.json` with status `PAPER_TEST`
   or `DEMO_TEST`.

The edge then runs on paper or demo. Its live record is watched by `edge_health`:

- **DEGRADED**: more than 2 standard errors below the tested mean, after at least 20 trades.
- **RETIRED**: negative with 95% confidence, after at least 40 trades.

Live money is never enabled by any of this: the demo guard refuses live endpoints
(CLAUDE.md rule 1).
