# The autonomous research system

The owner's final directive (2026-11-09) asked for research that runs by itself:

- it proposes new hypotheses, tests them under strict rules, learns from failures and publishes reports;
- it never touches real money;
- it never confuses activity with progress.

This file says what was built, how each requirement is met, what was verified and what is still missing.

**RESEARCH AND PAPER TRADING ONLY.** Nothing here can place a real order, change a live trading rule or change a
production risk setting.

## What runs, and where

The system uses the infrastructure the project already had: GitHub Actions, data branches and the scheduled
check-ins of this Claude Code session. Nothing new is hosted.

| Part | Runs | Where it runs | What it does | Where its output goes |
|---|---|---|---|---|
| Research cycle | Daily at 04:47 UTC, a backup at 16:17, or on demand | GitHub Actions: `research-cycle.yml` → `scripts/research_cycle.py` → `scripts/research_engine.py` | Integrity of the research record, then new hypotheses (a proposer model, a critic model, a power gate), then the research report | `research-data` branch: `RESEARCH_REPORT.md`, `RESEARCH_REPORT.json`, `ideas.jsonl`, `cycles.jsonl` |
| Trend desk | Weekdays at 22:40 UTC, backups at 01:13 and 06:43 | GitHub Actions: `trend-desk.yml` → `scripts/trend_desk.py` → `scripts/desk_ledger.py` | TRND-1 traded by the system on its $200,000 paper account, then the permanent ledger and the trading report | `trend-desk-data` branch: `TRADING_REPORT.md`, `ledger.csv`, `equity.csv`, `REPORT.md`, `desk.db.gz` |
| Research loop | 11:26 and 23:26 UTC | Claude Code scheduled task "Never-stop research queue" (this session) | Builds the engine's queued ideas: checks each claim at its source, preregisters it, collects the data and judges it once; then reports to the owner | `main`: preregistrations, `research/registry.jsonl`, `research/knowledge/`, `research/QUEUE.md`, `docs/RESEARCH_REPORT.md` |
| Existing tracks | Unchanged | `funded-paper.yml`, `paper-forward.yml`, `radar.yml` | As before | Their own branches |

## The loop

The loop the owner set out (DISCOVER → … → GENERATE NEW HYPOTHESES), step by step:

| Step | Who does it | How |
|---|---|---|
| Discover, generate a hypothesis | The proposer model (research cycle) | It is given every family already tested or dropped, each market's bar, the lessons of the record and the owner's conditions (swap-free, no interest-bearing instrument). It must answer in a strict schema: mechanism, market, horizon, an exact rule, data source, evidence, the claimed net Sharpe ratio and the years of fresh data. Up to three a day |
| Challenge | The critic, a different model | It can only reject: a repeat, no mechanism, an overstated claim, a leak, a breach of the owner's conditions. The engine refuses a critic answering as the proposer's own model |
| Power gate | Arithmetic, no model | At the claimed strength over the claimed fresh years, the expected t against that market's Bonferroni bar. An idea that cannot reach the bar is dropped. A claimed net Sharpe above 2 is dropped as a likely error or leak |
| Remember | `ideas.jsonl` (append-only) | Every idea with its fingerprint, both models, the critic's reason, the power figures and the decision. A fingerprint is never recorded twice |
| Verify, preregister, collect data, test | The research loop | The claim is checked at its source first. Then the frozen spec and code hashes are quoted in a preregistration and the trial is registered with a bar counting every earlier test on its data. The test has development, validation and a holdout, costs ×1, ×1.5 and ×2, a matched random baseline and a block bootstrap. It is judged once |
| Validate | The registry and each program's preregistered gates | `aitrader/research/registry.py` refuses back-filling, reused ids and a second look at the sealed holdout. Only the edge classification can say VALIDATED, and only a person promotes |
| Analyse, learn | The research loop, the knowledge base | Every verdict's evidence file and its hash; the lessons fed back to the proposer |

**AI never approves its own result.**

- The proposer only proposes.
- The critic can only reject.
- The power gate is arithmetic.
- Every verdict comes from gates fixed before the data were read.

This is the project's rule 5 ("AI can only subtract") applied to research.

## Recovery, persistence, no duplicates

- **Persistent state.** Each run starts on a fresh runner and restores its state from its data branch, so every run
  is a restart. The research cycle restores `ideas.jsonl` and `cycles.jsonl` from `research-data`, and the trend
  desk restores `desk.db` from `trend-desk-data`.
- **Checkpoints.** `cycles.jsonl` records every step of every cycle. A cycle's ideas step that succeeded is skipped
  when the cycle is run again. Ideas are written with their cycle id, so a crash after the write cannot write them
  twice. The trend desk applies each session once and records its equity once.
- **Retries.**
  - A model call is a read with no side effect: the OpenRouter client retries with bounded backoff and falls back
    across free models.
  - A model that answers out of schema is not repaired: the next model is asked, three at most.
  - A step that still fails is recorded as FAILED and retried by the next run.
  - Pushes to the data branches are retried five times.
  - A broker write is never retried (CLAUDE.md rule 3).
- **Failure detection.**
  - A run fails, and GitHub shows it, when the research record fails its integrity check. The checks:
    - the registry loads in order;
    - every verdict's evidence matches its recorded hash;
    - every spec hash is quoted in its preregistration;
    - the seal is byte for byte the one pinned in the engine.
  - A run also fails when no ideas step has succeeded for 72 hours.
  - The schedule re-enables itself on every run, so GitHub's 60-day inactivity rule cannot switch it off.
- **No silent stop.** Each research report shows its engine's last cycle, its last successful ideas step and the
  integrity result.

## Reports, kept apart

| Report | Where | What | Never contains |
|---|---|---|---|
| Trading | `trend-desk-data`: `TRADING_REPORT.md`, `ledger.csv`, `equity.csv` | The paper account: daily and cumulative, kept apart. Realized and unrealized P&L, closed trades, costs by kind, open exposure, drawdown with intraday lows, losing days, weeks and months, the monthly dashboard against $4,000, every trade with its signal | A backtest or research figure. Those are named in their own section and never added |
| Research | `research-data` (daily, by the engine) and `docs/RESEARCH_REPORT.md` (by the research loop) | New hypotheses, verdicts, ideas dropped before building, validation status, the bar on each market, the evidence checks, the engine's ideas | Any paper-trading figure |

## The acceptance test

| # | Requirement | How it is met | Evidence |
|---|---|---|---|
| 1 | Automatic research-cycle execution | `research-cycle.yml`, daily schedule with a backup, and on demand | On demand: five runs, each a success. On schedule: first due 2026-11-10 04:47 UTC, **not yet observed** |
| 2 | Autonomous hypothesis generation | The proposer and critic models in every cycle; nobody supplies an idea | Tested (`test_research_engine.py`). In production: **first observed 2026-11-10 00:13 UTC** (run 42726657914), after four failed cycles (below) |
| 3 | Permanent experiment history | `research/registry.jsonl` (append-only, enforced), knowledge files whose hashes every cycle re-checks, `ideas.jsonl` and `cycles.jsonl` (append-only), the desk's hash-chained events | `test_research_report.py`, `test_desk_ledger.py` |
| 4 | Automated statistical validation | The integrity checks and the power gate run every cycle. The preregistered gates and Bonferroni bars of each program judge it | `test_research_engine.py`, `test_research_report.py`, each program's tests |
| 5 | Automatic report generation | The research report every cycle, the trading report every weekday session | `test_the_cycle_writes_its_report_with_the_engine_kept_apart`, `test_desk_ledger.py` |
| 6 | Persistent operation after restart | State restored from the data branches on each run | `test_the_state_restored_elsewhere_carries_on_as_if_never_stopped`, `test_each_session_is_recorded_once_and_a_rerun_records_nothing_more` |
| 7 | Recovery from simulated failures | Simulated: a provider down, a crash inside the step, a crash after the write, a model out of schema, a critic out of schema, a ledger failure | `test_after_a_failure_the_next_run_retries_and_completes` and the failure tests beside it; `test_a_ledger_failure_never_stops_the_desk_and_is_said` |
| 8 | No duplicate experiment execution | Fingerprints; the cycle-id guard; registry ids never reused; desk sessions applied once and recorded once | `test_a_rerun_the_same_day_asks_no_model_and_records_nothing_twice`, `test_the_same_idea_another_day_is_never_recorded_again_however_it_is_worded`, `test_each_session_is_recorded_once_and_a_rerun_records_nothing_more` |
| 9 | No real-money trading | The engine imports no broker, execution, position, risk or service module, and calls no order, register or verdict method. The desk is paper only, behind the demo guard, the risk engine and the hard gate | `test_the_engine_cannot_trade_register_or_judge`; the desk's existing tests |
| 10 | A verified deployment and operational status | GitHub Actions runs and data branches | Partly: the deployment and the first run are confirmed; the scheduled runs and a production ideas step are not yet |

`scripts/mutation_audit.py` removes each of the engine's and the ledger's guards in turn and requires a test to fail
(`docs/MUTATION_AUDIT.md`).

## Deployment and operational status (confirmed on GitHub, 2026-11-09)

**Deployed.** The research cycle, the engine and the trend desk's ledger reached `main` at commits `b7144b2`,
`80614fa` and `44d3cd6`.

**The research cycle ran five times on demand.** Every run succeeded as a job.

| | Run 1 (11-09 18:02 UTC) | Run 2 (18:32) | Run 3 (18:51) | Run 4 (23:52) | Run 5 (11-10 00:13) |
|---|---|---|---|---|---|
| Engine | 1.0.0 | 1.0.1 | 1.0.2 | 1.1.0 | 1.1.1 |
| Integrity | OK | OK | OK | OK | OK |
| Report published to `research-data` | yes (`b78d778`, the branch created) | yes (`cab5b58`) | yes (`557f034c`) | yes (`921138c`) | yes (`9cd3aef`) |
| Ideas step | **FAILED** | **FAILED** | **FAILED** | **FAILED** | **OK** |
| Why | The client spent its whole 10-minute deadline waiting on one rate-limited model | Three models: one timed out; two reasoning models were cut at the 6,000-token limit while still thinking | Three models: one timed out, one was cut at 20,000 tokens while thinking, one was rate-limited | Four models, then none left (below) | The first model answered in schema, and so did the critic (below) |

Each failure was recorded in `cycles.jsonl`, with every model tried. Nothing was invented, and the step is retried by
the next run. The fixes, one at a time:

- **1.0.1:** a call is bounded, and a failing model is passed over for the next.
- **1.0.2:** 20,000 tokens and 240 seconds a call.
- **1.1.0, after run 3** (with openrouter 1.15.0):
  - Both roles now read the judge's ranking, which puts the strongest FREE text models first. They had the verifier's
    ranking, which leaves out the two strongest by design. It offered the same three small models in runs 2 and 3:
    `xingchen-agi/xing4.0-29b-a4b`, `nvidia/nemotron-3-nano-omni-30b-a3b-reasoning` and `recursive/flint-v1.0`.
  - Up to five models are asked a role, and the job may run 55 minutes.
  - Both roles stay FREE only. Neither is a paid seat, and the client refuses to start if one ever is. A test checks
    that a trial paying for the judge changes nothing for them.

**Run 4, with 1.1.0 (run 42723863971).** The client tried every FREE text model it had, then reported none left:

| Model | Result |
|---|---|
| `dots-studio/dots-3-note-preview` | timed out |
| `nvidia/nemotron-3-nano-omni-30b-a3b-reasoning` | cut at 20,000 tokens while thinking |
| `recursive/flint-v1.0` | **answered**, but with a claimed Sharpe ratio outside (0, 10], and was refused |
| `xingchen-agi/xing4.0-29b-a4b` | rate-limited |
| none | NO_FREE_MODEL |

So the judge's ranking held only these four FREE text models. In four cycles, none of the models offered gave a
usable answer. Ranking so few models differently cannot make them answer.

- **1.1.1:** the prompt now states each number's type and range, from the same constants the validator enforces.
  The prompt had never stated the range. The validator is unchanged and nothing is repaired.
- A paid model for these two roles would cost little: about 8,000 tokens in and 4,000 out a day. It needs the owner's
  explicit approval, and none is used.

**Run 5, with 1.1.1 (run 42726657914, 2026-11-10 00:13 UTC): the first ideas step to succeed in production.** It
took three minutes.

| | |
|---|---|
| Proposer | `nvidia/nemotron-3.5-super-vl`: three hypotheses, each claiming a net Sharpe ratio of 0.5 |
| Critic | `nvidia/nemotron-3-nano-omni-30b-a3b-reasoning` |
| EM currency intervention follow-through | rejected by the critic |
| Same-day reversal after the EIA crude inventory report | rejected by the critic |
| Central-bank gold buying | passed by the critic, then **dropped by the power gate**: expected t 1.0 against a bar of 2.24 over its 4 fresh years |

Nothing was queued for building. Two weaknesses show already:
- Both rejections say short selling breaks the swap-free condition, which it does not: the conditions forbid
  financing and interest-bearing instruments, not short positions. A wrong rejection only loses an idea; it can never
  add one.
- The two models are different, as the engine requires, but both are NVIDIA's. Models from one lab share training and
  biases.

**Confirmed: the probes and ENG-1's judge on GitHub's runner.**
- The ENG-1 and LIQ-1 probes: runs 42666526034 and 42666716125, success.
- ENG-1's judge: run 42670396500, success. It recorded a FAILED verdict (`research/preregistrations/ENG-1.md`).

**The trend desk's first evening: no session applied yet.**
- GitHub's schedule did not start the 22:40 UTC run (nor the funded-paper track's 22:20). Both were started by hand at
  23:31 UTC: runs 42721181436 and 42721196248, success.
- Yahoo served GER40's bar for 2026-11-09 without a close. So the desk applied no session. It never fills a price in:
  the session waits for the first run that reads it complete.
- `TRADING_REPORT.md`, `ledger.csv` and `equity.csv` are on `trend-desk-data` (commit `2bbd4a1`). The account is at
  $200,000 with no trade. Since desk-ledger 1.0.1, the report also says why.

**GitHub's schedule is best-effort.** This repository's schedules have fired hours late or not at all.
- The trend desk now has backup times at 01:13 and 06:43 UTC, and the funded-paper track at 01:23 and 06:53. Each run
  applies only what is new.
- The research cycle has a backup at 16:17 UTC. It retries only an ideas step that failed that day, and the day's
  cap of three ideas holds across both runs.
- The research loop's check-ins (11:26 and 23:26 UTC) verify each of these and start a missed run by hand.

**Not yet observed** (each is checked at the next check-in and reported):
- the first **scheduled** research cycle (2026-11-10 04:47 UTC) and the first **scheduled** trend-desk run;
- the trend desk's first applied session.

## What is missing, and why

- **Forex.** No validated Forex edge exists (`docs/FX_MISSION_REPORT.md`). Under the project's rules three things
  stand in the way.
  - The FX majors' data before 2017 carries 176 tests, so the next FX test needs t ≥ 3.63.
  - Every month from 2017 on is sealed, open-ended, for one final test of a passer. So no forward FX test can run.
    Changing that would mean closing the seal at a date, say 2026-11-30, so that later data forms a fresh forward
    universe. That changes the project's protection of its holdout, and only the owner can decide it.
  - Realistic costs need measured spreads from the owner's broker. That needs a read-only recorder and the demo
    account's credentials, which the owner must add as secrets themselves. They must never be pasted into a
    conversation.
- **Railway.** The live service's configuration could not be inspected from here: only the repository's
  `Dockerfile` and `railway.json`. Nothing was deployed to Railway. Everything above runs on GitHub Actions and in
  this session's scheduled task.
- **The engine does not build tests.** A new test needs new code and often new data. The engine queues an idea that
  can pass; the research loop builds it. An idea queued while the loop is not running waits in `ideas.jsonl`.
- **The $4,000 a month.** No strategy validated so far supports it at acceptable risk (`docs/FX_TARGET_REPORT.md`).
  The system never raises risk to reach it (CLAUDE.md rule 8).
