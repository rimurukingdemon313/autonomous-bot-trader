# Autonomous AI Trader

**A closed-loop trading-intelligence system: five agents, memory, evidence
synthesis, a deterministic risk engine, and learning from outcomes that
is measured, never assumed.**

> **Status: RESEARCH, no edge.** The system is built, tested and
> deployable in PAPER or DEMO. Its pre-registered test, **PR-001, FAILED**.
> Over 2010-2016, after costs, the full system averaged **−0.07 R per trade
> (t −2.9): it loses money.** It starts paused. `MODE=LIVE` is refused by
> the software. Nothing here claims or implies profitability.

---

## What it does

Every fourth hourly close (the cadence it was tested at), for each of 12 FX pairs:

1. **Features.** 23 causal features are computed on complete bars.
2. **Context.** A regime and familiarity check. An unfamiliar state means
   NO_TRADE.
3. **Memory.** The *k* nearest past situations **whose outcomes had already
   resolved at that moment** are retrieved, with the realised R of each
   action.
4. **Five agents** read the same evidence:
   - **Market**: regime, familiarity.
   - **Setup**: which actions are worth considering.
   - **Risk**: cost and spread against the stop.
   - **Adversary**: the case against, from a closed list of objections.
   - **Reviewer**: how far the evidence can be trusted: analogue sample,
     noise, age and concentration, template agreement, validated lessons,
     the family's track record. It runs before synthesis and never sees
     the decision.

   An optional language model can only add objections.
5. **Evidence synthesis, not a vote.** A trade needs the analogue
   expectancy's *lower bound* to clear a bar. Each MAJOR objection raises
   the bar by its measured penalty. Any BLOCKING objection means NO_TRADE.
6. **Risk engine.** The only code that sizes or approves a trade.
7. **Execution.** Intent is recorded before the order. A write is never
   resent. Positions are reconciled on restart.
8. **Outcomes.** Every candidate gets an outcome, including the ones
   *skipped*: a shadow outcome is what the same order would have returned.
9. **Learning** from those outcomes:
   - post-mortems and reflections;
   - objection penalties measured from a track record;
   - lessons that act only after out-of-sample confirmation.

   One win or one loss changes nothing.

```
data → features → regime → memory → 5 agents → synthesis → RISK → execution → broker
  ↑                                                                               │
  └──────── outcomes (real + shadow) → post-mortem → lessons → knowledge v+1 ────┘
```

Details: [ARCHITECTURE.md](ARCHITECTURE.md), and its implementation map.

## Safety, in one table

| Guarantee | Where | Proven by |
|---|---|---|
| Risk per trade ≤ 1 % whatever the config; risk falls after losses, never rises | `aitrader/risk/engine.py` | `tests/unit/test_risk.py` |
| Drawdown 8 % halts until a person clears it | risk engine | same |
| No order unless the account is **positively** verified demo/paper (two signals; a name can only fail) | `execution/engine.py`, `broker/tradelocker/demo_guard.py` | `test_execution.py`, `test_tradelocker_adapter.py` |
| An unknown write outcome is resolved by querying the broker, **never by resending** | `execution/engine.py` | `test_execution.py` |
| An unreadable kill switch counts as active | same | same |
| Any agent failure, missing input or malformed model reply means NO_TRADE | `decision/synthesis.py` | `test_agents.py` |
| The knowledge base loads only if it matches its card's SHA-256 | `service/runtime.py` | `test_service.py` |
| Stop and pause need no token; resume, clear, scan and revert need `DASHBOARD_TOKEN` | `service/server.py` | `test_service.py` (real HTTP) |
| History (decisions, trades, episodes, lessons) is immutable and hash-chained | `memory/db.py` | `test_db.py` |

Every row was checked by **removing the guard and watching a test fail**:
62 of 62 mutants were killed ([docs/MUTATION_AUDIT.md](docs/MUTATION_AUDIT.md)).

## Evidence

- **Data.** Dukascopy tick data, bid **and** ask, 2007-03 → 2018 (EURUSD to
  2022), aggregated to M15 with measured spreads
  ([data/manifest.json](data/manifest.json)). That is about 11 years, not
  20: no longer bid/ask history was reachable, and quality came first.
- **Sealed holdout.** From 2017-01-01. The loader cannot read it without the
  key that only a pre-registered final test holds.
- **Registry.** Every test on this universe is counted, including the 16
  verdicts of the [archive](docs/HISTORICAL_ARCHIVE.md), in the append-only
  [research/registry.jsonl](research/registry.jsonl). The next test needs
  |t| > 3.02.
- **PR-001.** Does the full system have an edge after costs, out of sample,
  and does each part (agents, memory, learning) add value? The rules were
  committed before any run. Result:
  [RESULTS](research/preregistrations/PR-001-multi-agent-ablation.md#results).

**PR-001 result.** All four verdicts failed (H1 edge, H2 learning, H3
memory, H4 agents vs random). Every variant stopped in early 2010 at the
8 % drawdown halt, or, for the memory-free baseline, at a self-lock the
run exposed. The exploratory arm without the halt (no verdict) shows:

| 2010-2016, after costs | Trades | Mean R | t | Return at 0.5 %/trade |
|---|---|---|---|---|
| Full system (C) | 2,928 | −0.072 | −2.90 | −53.5 % |
| Memory, no learning (B) | 2,577 | −0.053 | −1.99 | −47.4 % |
| Random direction, same risk engine (R) | 3,143 | −0.159 | −7.38 | −87.1 % |

The analogue memory filters: it loses half as much as random. It does
not produce an edge, and learning added nothing measurable. **The sealed
holdout was not opened.** It is saved for a future candidate that earns it.

## The AI trader (optional)

`DECISION_MODE=llm_trader`: a language model (any provider behind one key,
for example OpenRouter) analyses H1/H4/D1 and proposes trades. Before each
decision it reads its own past trades and its reviews of them, and after
each close it writes a new review. The risk engine still sizes and may
refuse every trade. PAPER/DEMO only, never backtested, and its win rate is
measured live on the dashboard. See [docs/AI_MODELS.md](docs/AI_MODELS.md)
and MODEL_CONTRACT §10.

`DECISION_INTERVAL_MIN=N` makes either model mode decide every N minutes,
also reading M5/M15, with `SYMBOLS_PER_CYCLE` pairs per cycle in rotation.
The evidence system keeps its tested 4-hour cadence.

`DECISION_MODE=trading_room`: one team with one mind per provider, each
with a role: TREND, PRICE, NEWS (the economic calendar) and RISK. They
discuss in turn, each building on what the others said, and one of them
writes the team's joint decision. The models choose their own style, timeframe, stop and
target. The quantitative system's view of the market reaches them as
information, not as a veto. The risk engine still sizes every trade, and
bad data still stops a decision. Each model's record is kept separately.
MODEL_CONTRACT §10.1 and §10.3.

## Research lab: how the system looks for something new

PR-001 tested a fixed design. Finding a *new* relationship is the
research lab's job (`aitrader/research/lab.py`, `scripts/research_lab.py`,
[docs/GAP_REPORT.md](docs/GAP_REPORT.md)):

```
observe (fit-data scan, reflection, lessons, optional LLM drafts)
  → hypothesis inside a DECLARED space (instruments, H1/H4/D1, features incl. a 667-candidate grammar,
    ridge / logistic / k-NN models, action templates)
  → REGISTER (threshold frozen from the registry)  → purged, embargoed walk-forward
  → vs random and vs the k-NN analogue baseline  → robustness (costs, one-bar delay)
  → PASS / FAIL recorded  → a PASS writes a hashed artifact OUTSIDE production
```

What the code enforces:

- nothing runs before it is registered;
- a failed hypothesis cannot be re-run with a new threshold or new dates;
- a leaky candidate feature is rejected before evaluation;
- a language-model hypothesis is never judged on data the model may have
  read;
- the holdout is out of reach;
- the live decision path cannot import the lab.

**Status: built and tested on constructed markets; no real-data
experiment has been run with it yet.** The next hypothesis is designed
and pre-registered first.

The language-model layer is **not** in any backtest. A model trained on
data after a historical date knows what happened next, so its value can
only be measured forward, in paper or demo ([docs/AI_MODELS.md](docs/AI_MODELS.md),
[docs/RESEARCH_LOG.md](docs/RESEARCH_LOG.md)).

## Run it

```bash
pip install -r requirements.txt            # numpy only
MODE=PAPER DATA_DIR=./state DASHBOARD_TOKEN=$(openssl rand -hex 24) python -m aitrader
# dashboard: http://localhost:8080   health: /healthz
```

Without TradeLocker credentials it starts, serves the dashboard, and
reports `DATA: NOT CONNECTED`. It makes no decision on invented prices.

**Railway** (Dockerfile + `railway.json` included): add a Volume at `/data`,
set the variables from [.env.example](.env.example) under Railway →
Variables (never in the repository), deploy. Step by step:
[docs/OPERATIONS.md](docs/OPERATIONS.md).

Research machine:

```bash
pip install -r requirements-research.txt
python scripts/ingest_dukascopy.py     # data → data/processed + data/manifest.json
python scripts/build_knowledge.py      # models/artifacts (memory, regime, card)
python scripts/run_pr001.py            # the pre-registered experiment
python scripts/judge_pr001.py          # verdicts by the pre-registered rules
bash scripts/check.sh                  # the test suite
python scripts/mutation_audit.py       # remove each guard, require a failing test
```

## Repository

| Path | What |
|---|---|
| `aitrader/` | all code: `data`, `features`, `regime`, `memory`, `agents`, `llm`, `decision`, `risk`, `execution`, `broker`, `orchestrator`, `learning`, `research`, `backtest`, `service` |
| `tests/` | unit and integration tests ([tests/README.md](tests/README.md)) |
| `scripts/` | ingestion, knowledge build, experiments, judging, audits |
| `research/` | registry, sealed holdout, pre-registrations, results |
| `models/` | the knowledge base and its card ([models/README.md](models/README.md)) |
| `data/` | the data manifest (bars themselves are not committed) |
| top-level `backtest/`, `broker/`, … | one guide per layer, pointing to its code |

## Documents

| Document | What it fixes |
|---|---|
| [PROJECT_SPEC.md](PROJECT_SPEC.md) | What the system is for, and what it is not |
| [ARCHITECTURE.md](ARCHITECTURE.md) | Layers, authority, implementation map, bounded runtime learning |
| [ROADMAP.md](ROADMAP.md) | Phases, and where each gate stands with its evidence |
| [ENGINEERING_RULES.md](ENGINEERING_RULES.md) | Non-negotiable rules for every change |
| [RESEARCH_CONTRACT.md](RESEARCH_CONTRACT.md) · [VALIDATION_CONTRACT.md](VALIDATION_CONTRACT.md) | Registration, splits, walk-forward, holdout |
| [DATA_CONTRACT.md](DATA_CONTRACT.md) · [MODEL_CONTRACT.md](MODEL_CONTRACT.md) | Data provenance; models and the language-model rules |
| [RISK_CONTRACT.md](RISK_CONTRACT.md) · [EXECUTION_CONTRACT.md](EXECUTION_CONTRACT.md) · [SECURITY_CONTRACT.md](SECURITY_CONTRACT.md) | Capital protection, order safety, secrets |
| [docs/OPERATIONS.md](docs/OPERATIONS.md) | Deploying and operating on Railway |
| [docs/AI_MODELS.md](docs/AI_MODELS.md) | The optional language-model layer and which free models to use |
| [docs/RESEARCH_LOG.md](docs/RESEARCH_LOG.md) | Sources reviewed, adopted, rejected, and why |
| [docs/AUDIT.md](docs/AUDIT.md) | Security, leakage, risk and architecture audit |
| [docs/GAP_REPORT.md](docs/GAP_REPORT.md) | Intended research system vs. what is built: IMPLEMENTED / PARTIAL / SCAFFOLD / NOT IMPLEMENTED |
| [docs/](docs/) | Lifecycle, research process, testing, failure policy, versioning, archive |

## Historical research archive

The predecessor, a DEMO-only TradeLocker bot, found **no edge in 13
strategy families** under pre-registered rules. It is kept as a read-only
archive. Its TradeLocker client was transferred after review, with one
safety change. Everything else stayed there.
[docs/HISTORICAL_ARCHIVE.md](docs/HISTORICAL_ARCHIVE.md).
