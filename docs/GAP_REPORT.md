# Gap report: intended research system vs. what is built

Written 2026-09-27, after PR-001 failed. It was written **before** the
changes it motivates, against commit `78595a0`. The rules for this work:

- PR-001 stays FAILED.
- The sealed holdout stays sealed.
- No parameter changes because PR-001 failed.
- No LIVE.

Status words used below:

- **IMPLEMENTED:** works, and a test proves it.
- **PARTIAL:** works for part of what is required.
- **SCAFFOLD:** the interface exists and is tested; the research itself has
  not been run.
- **NOT IMPLEMENTED:** absent.

## A. What the current system genuinely does

A **bounded, analogue-memory decision system**:

1. **Features.** 23 fixed, hand-written, causal features on H1 bars.
2. **Setup.** Four hard-coded setup families (TREND_PULLBACK, BREAKOUT,
   MEAN_REVERSION, SWEEP_REVERSAL) propose candidates. So does
   ANALOG_DISCOVERY: "the nearest past situations favoured this action".
   Every candidate uses one of **two fixed action templates**:
   - T1: stop 1.0 ATR, target 1.5 ATR, 24 bars;
   - T2: stop 1.5 ATR, target 3.0 ATR, 48 bars.
3. **Analogue expectancy.** Each candidate's expectancy is the mean
   realised R of its k=100 nearest past situations, point-in-time.
4. **Agents.** Market, Setup, Risk and Adversary produce evidence and
   objections. The **"Reviewer" is not an agent.** `Brain.think` builds it
   *after* synthesis from the decision's own thesis, so it repeats the
   decision. The work a reviewer should do (judging the analogue evidence,
   matching validated lessons, the family's track record) is done inside
   the Adversary.
5. **Synthesis.** Trade only if the analogue lower bound is at least the
   required edge. Each MAJOR objection raises the required edge by a
   measured penalty. Not a vote.
6. **Language models.** They can add objections from a closed vocabulary.
   Their directional opinion can only raise the bar, weighted by a forward
   reliability that starts at 0. They cannot propose a trade, a feature, a
   hypothesis or anything else.
7. **Learning.** Lessons of the form "context (family, direction, regime,
   vol) has negative expectancy" go through a Bonferroni-gated
   out-of-sample lifecycle (CANDIDATE → VALIDATED / REJECTED → RETIRED).
   A validated lesson can only block. Reflection writes "hypotheses" as
   **free text only**. Nothing turns them into experiments, and the
   database's `experiments` table exists but **nothing writes to it**.
8. **Research.**
   - An experiment registry with fit/select/judge roles and Bonferroni
     thresholds.
   - A sealed holdout.
   - Cost-aware labels.
   - A walk-forward backtester of the whole system.

   There is no component that generates, runs or judges a *new*
   hypothesis. PR-001 was designed, pre-registered and judged by hand.

## B. What PROJECT_SPEC requires

§3 says the AI may choose the instrument, the timeframe, the regime
description, the features, the model, entry / stop / target / exit logic,
and NO_TRADE. Each choice must be drawn from **a declared and counted
space**, and widening a space goes through registered research.

RESEARCH_CONTRACT §5 fixes the autonomous research path:

1. register;
2. define the data;
3. test on training data;
4. then on validation data;
5. then out of sample;
6. record;
7. reject on failure.

It also requires a declared test budget, and forbids re-running a
failed hypothesis with small variations.

## C. Exact gaps

| # | Requirement | Current state | Status before this work |
|---|---|---|---|
| 1 | Choose the instrument | a fixed universe of 12 is always traded; nothing is selected by evidence | NOT IMPLEMENTED |
| 2 | Choose the timeframe | H1 only; H4 and D1 bars exist in the data layer but no decision path uses them | NOT IMPLEMENTED |
| 3 | Choose the features | 23 fixed features, with no way to propose, test or adopt a new one | NOT IMPLEMENTED |
| 4 | Choose the model | one estimator, k-nearest-neighbour analogue averaging. It is a non-parametric lookup, **not a trained model**. No statistical or ML model family exists | NOT IMPLEMENTED |
| 5 | Entry logic | 4 hand-written trigger families plus analogue discovery | PARTIAL (a bounded baseline, not discovery) |
| 6 | Stop / target / exit logic | two fixed templates | PARTIAL (a declared set of 2) |
| 7 | NO_TRADE | implemented and dominant | IMPLEMENTED |
| 8 | Five independent agents | four; the Reviewer is a label written after the decision | PARTIAL |
| 9 | LLM beyond vetoes | vetoes only | PARTIAL, by design |
| 10 | Generate new testable hypotheses | text-only reflection hypotheses; no experiment is ever generated | NOT IMPLEMENTED |
| 11 | Run the research loop (register → walk-forward → OOS → robustness → baseline → accept/reject → version) | only by hand (PR-001) | NOT IMPLEMENTED as software |
| 12 | Learning produces experiment proposals | no | NOT IMPLEMENTED |
| 13 | Failed experiments cannot affect production | true today, but only because no experiment code exists | IMPLEMENTED (vacuously) |

## D. Critical gaps

- **10-11, research loop.** Without it, the system cannot do what it
  exists to do: find, and more often reject, relationships under
  statistical control. Everything else in §3 depends on it.
- **3-4, features and models.** Without them, the research loop could
  only re-test the same space, which is exactly what failed.
- **8, Reviewer.** It is mislabelled today. The architecture claims five
  analysts, and one of them is an echo.

## E. Implement now

1. **An independent Reviewer agent** that runs before synthesis and
   judges the *quality of the evidence*:
   - analogue sample size, noise, age and concentration;
   - agreement between the templates;
   - validated lessons;
   - the family's track record.

   The evidence-quality checks move from the Adversary to the Reviewer
   (same codes, same severities, so decisions do not change). The new
   quality checks enter as **MINOR**. They are recorded and their
   predictive value is measured before anything may act on them.
2. **A research lab** (`aitrader/research/lab.py`), research-machine only:
   - a declared, finite hypothesis space: instrument set, timeframe,
     feature set, model family, action template, decision threshold;
   - registration before any evaluation, refused otherwise;
   - purged, embargoed walk-forward evaluation on cost-aware labels;
   - comparison against the unconditional and random baselines;
   - a robustness battery: costs ×1.5, one-bar delay, sign by instrument;
   - Bonferroni thresholds taken from the registry;
   - a frozen, hashed artifact written only on a PASS, and never to the
     directory production loads from.
3. **Model families** implemented in numpy. No production dependency is
   added:
   - ridge regression on R;
   - logistic regression on win;
   - the analogue k-NN as a baseline family.

   Tree or boosting families are a registered *plug-in point* that needs a
   research-only dependency. They are **not** implemented.
4. **Feature discovery.** Candidate features come from a small declared
   grammar of transforms of existing columns, so they can be counted.
   Each candidate passes the same truncation (look-ahead) checker the
   production features pass, or it is rejected before evaluation. It is
   then judged by its **incremental** out-of-sample value.
5. **Hypothesis generation**:
   - from observation: the fit-period information scan, with its own
     multiple-testing correction;
   - from reflection and lessons: experiment proposals written to the
     database `experiments` table as PROPOSED and shown on the dashboard.

   Proposals are only proposals. They run only through the lab, and are
   counted there.
6. **The language model as a hypothesis source.** It may *propose* in the
   lab, never decide. Its hypotheses may only be judged on data after the
   model's declared training cutoff: a model that has read about 2008
   cannot be tested on 2008.

## F. Research-only (built as interfaces or documented, not run now)

- Running any new experiment on real data. The next hypothesis is designed
  and pre-registered **after** this work, as instructed.
- Instrument and timeframe selection *in production*. The lab can
  evaluate across instruments and timeframes; production still trades the
  configured universe on H1.
- Tree and boosting models, time-series models (ARIMA/GARCH-style) and
  Bayesian models.
- Exit logic beyond the declared templates (trailing stops, partials,
  learned exits).
- Promoting a lab artifact into production. That is a manual, documented
  step that needs a PASS, the robustness battery, and the single-use
  holdout test.

## G. Safety systems not touched

- The risk engine: sole sizing and approval, the 1 % ceiling, the
  drawdown halt, streak reduction.
- The execution engine: intent first, no resend, reconciliation, the cycle
  lock.
- The demo guard: two signals, where a name can only fail.
- The holdout seal, the registry rules and PR-001's verdict.
- Immutable, hash-chained journals.
- The knowledge-base hash check, the paused first start, and LIVE refusal.
- Point-in-time memory, and a language model that can only subtract in
  live decisions.
- The mutation audit: all 28 guards must stay killed.

---

## H. After this work: status of every requirement

Commits `1373d0c` → the current head. Each line names its evidence.

| Requirement | Status | What exists | What does not |
|---|---|---|---|
| Five independent analysts before synthesis | **IMPLEMENTED** | `ReviewerAnalyst` runs beside Risk and Adversary, before synthesis, and never sees the decision. It is required: its failure is NO_TRADE. Decisions were shown unchanged by the move (identical trades on the constructed market) | — |
| Reviewer produces its own evidence | **IMPLEMENTED** | analogue sample, noise, age, instrument concentration, template agreement, lessons, track record (`test_the_reviewer_grades_…`) | The 4 new quality checks are MINOR: their predictive value must be measured first |
| No majority vote | **IMPLEMENTED** (unchanged) | analogue lower bound vs required edge | — |
| Learning: observations → hypotheses → validated/rejected/retired lessons → experiment proposals | **IMPLEMENTED** | the lesson lifecycle; reflection → PROPOSED experiments in the immutable journal and on the dashboard | Proposals are not run automatically; the lab runs them when a person, or a scheduled research job not built here, registers them |
| Learning statistics honest about overlap | **IMPLEMENTED** (defect found and fixed) | effective sample size for overlap and templates; known-answer test | — |
| Research loop: hypothesis → register → walk-forward → OOS → robustness → baseline → accept/reject → version | **IMPLEMENTED as software, not yet run on real data** | `aitrader/research/lab.py` with 23 known-answer tests; `scripts/research_lab.py` | No real-data experiment has been run with it: the next hypothesis is to be designed and pre-registered first, as instructed |
| Choose the instrument | **PARTIAL** | the lab evaluates any declared subset and reports each instrument's result | Production trades the configured universe; nothing selects instruments live |
| Choose the timeframe | **PARTIAL** | the lab resamples to H1, H4 or D1 on complete bars | Production decides on H1 only |
| Choose the features | **SCAFFOLD** | a declared grammar of 667 candidates over the 23 base features, the leakage gate, incremental judging | Only grammar expressions over existing features; no raw-data feature synthesis; an accepted feature reaches production only by a reviewed FEATURE_VERSION change |
| Choose the model | **SCAFFOLD** | ridge, logistic and k-NN (numpy), judged against k-NN and random | Tree/boosting, time-series and Bayesian families: NOT IMPLEMENTED. A lab PASS writes an artifact; no production path loads it (promotion is manual and requires the holdout) |
| Entry logic | **PARTIAL** | the lab's entry is "model predicts R above a declared threshold", learned from features; production still uses the 4 families + analogue discovery | Learned entries are not in production |
| Stop / target / exit logic | **PARTIAL** | a declared choice between 2 templates in both production and the lab | Trailing, partial or learned exits: NOT IMPLEMENTED |
| NO_TRADE | **IMPLEMENTED** | — | — |
| LLM role | **PARTIAL, by design** | Live: objections only, and an opposing opinion weighted by forward-measured reliability (starts at 0). Research: may DRAFT hypotheses from the closed vocabulary. The lab refuses to fit or judge them on data before the model's training cutoff | An LLM never proposes a live trade, a size, or a parameter. Expanding its live role is not justified until its forward reliability is measured (MODEL_CONTRACT §9) |
| Failed experiments cannot affect production | **IMPLEMENTED** | no artifact on FAIL; the lab cannot write under `models/artifacts`; the live path cannot import the lab (`test_architecture.py`) | — |
| Risk engine sole authority; broker isolated | **IMPLEMENTED** (unchanged, now also checked in the import graph) | `test_architecture.py`; mutation audit | — |
| PR-001 | **unchanged: FAILED** | verdict, results and holdout untouched | — |

**Plainly:** the system can now conduct disciplined research within a
declared space. It has not yet *discovered* anything. Discovery is what
the next pre-registered hypothesis will test.
