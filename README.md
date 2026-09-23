# Autonomous AI Trader

**An autonomous AI trading research and decision system.**

> **Current status: PHASE 0 — ARCHITECTURE / SPECIFICATION**
>
> This repository contains documentation and contracts only. There is no
> trading code, no model, no strategy, no broker connection and no
> backtester. It is **not** ready for trading, and nothing here claims or
> implies that it is profitable.

---

## Objective

Build a system that can:

- search market data for relationships and patterns;
- state them as hypotheses and test them honestly;
- tell when an edge exists and, much more often, when it does not;
- decide **BUY**, **SELL** or **NO_TRADE**, with its reasoning recorded;
- learn from outcomes in a way that is versioned and testable.

Its freedom to research and decide is real. It is also bounded:
**capital protection is independent of the AI and cannot be bypassed by it.**

## What this project is not

- Not an "RSI bot", an "SMC bot", or an "ICT bot". No method is built in.
  Any method may be used once the data shows it helps, and dropped when the
  data shows it does not.
- Not a language model that opens trades. A language model may help with
  research, explanation and vetoes. It never has an unvalidated say over a
  trade, for the reason given in [MODEL_CONTRACT.md](MODEL_CONTRACT.md).
- Not a promise of income. There is no monthly target, no win-rate target
  and no minimum number of trades.

## Architecture

```
MARKET DATA → DATA VALIDATION → MARKET STATE → FEATURES → REGIME / CONTEXT
  → AI RESEARCH / MODELS → OPPORTUNITY → TRADE DECISION
  → RISK ENGINE → EXECUTION → BROKER
  → RESULT → JOURNAL → LEARNING / RESEARCH  (offline, versioned, gated)
```

The AI proposes and the risk engine disposes. There is no path from a model
to the broker that avoids the risk engine and the execution engine. See
[ARCHITECTURE.md](ARCHITECTURE.md).

## Research philosophy

```
Observation → Hypothesis → Experiment → Validation → Out-of-sample test
  → Robustness test → Version → Deployment candidate
```

This loop is forbidden:

```
Loss → change random parameters → backtest again → repeat until profitable
```

It always "succeeds" in the end, and what it produces is a curve fit.
Every experiment is registered before it runs, failed experiments are
kept, and each result is judged against the number of things tried before
it. See [RESEARCH_CONTRACT.md](RESEARCH_CONTRACT.md) and
[VALIDATION_CONTRACT.md](VALIDATION_CONTRACT.md).

## Safety philosophy

- **A decision at time T may only use information that was genuinely
  available at or before time T.** No exceptions.
- **No fabricated data.** A missing value stays missing and is labelled as
  missing.
- **NO_TRADE is a valid outcome.** It is often the correct one.
- **Risk may be reduced by adverse conditions. It may never be increased
  by them.** No martingale, no revenge sizing, no "recover the loss".
- **Fail closed.** If safety-critical state cannot be read, the system
  does not trade.
- **Nothing reaches LIVE automatically.** Every step up the lifecycle needs
  evidence and explicit human approval.

## Development phases

| Phase | Name | Status |
|---|---|---|
| 0 | Repository + specification | **current** |
| 1 | Data foundation | not started |
| 2 | Feature foundation | not started |
| 3 | Research framework | not started |
| 4 | Validation / walk-forward | not started |
| 5 | AI research layer | not started |
| 6 | Regime detection | not started |
| 7 | Decision engine | not started |
| 8 | Risk integration | not started |
| 9 | Execution | not started |
| 10 | Paper trading | not started |
| 11 | Demo | not started |
| 12 | Live readiness | not started |

Details and the exit gate for each phase: [ROADMAP.md](ROADMAP.md).

## Documents

| Document | What it fixes |
|---|---|
| [PROJECT_SPEC.md](PROJECT_SPEC.md) | What the system is for, and what it is not |
| [ARCHITECTURE.md](ARCHITECTURE.md) | Layers, responsibilities, authority boundaries |
| [ROADMAP.md](ROADMAP.md) | Phases and their exit gates |
| [ENGINEERING_RULES.md](ENGINEERING_RULES.md) | Non-negotiable rules for every change |
| [RESEARCH_CONTRACT.md](RESEARCH_CONTRACT.md) | How an experiment is registered, run and recorded |
| [VALIDATION_CONTRACT.md](VALIDATION_CONTRACT.md) | Splits, walk-forward, final holdout, pass/fail |
| [DATA_CONTRACT.md](DATA_CONTRACT.md) | Data provenance, time, quality, what may not be invented |
| [MODEL_CONTRACT.md](MODEL_CONTRACT.md) | Model identity, versioning, inference limits, LLM rules |
| [RISK_CONTRACT.md](RISK_CONTRACT.md) | The risk engine's authority and protections |
| [EXECUTION_CONTRACT.md](EXECUTION_CONTRACT.md) | Order safety, idempotency, recovery |
| [SECURITY_CONTRACT.md](SECURITY_CONTRACT.md) | Secrets, credentials, access |
| [docs/](docs/) | Overview, lifecycle, research process, testing, failure policy, versioning, archive |

## Historical research archive

This project has a predecessor. It was a working, DEMO-only TradeLocker bot
with a substantial body of pre-registered research, kept as a **Historical
Research Archive**. No code has been copied from it. What it taught, and
the rule for transferring anything from it, are in
[docs/HISTORICAL_ARCHIVE.md](docs/HISTORICAL_ARCHIVE.md).

## Current phase

**Phase 0.** The contracts in this repository are waiting for review. No
Phase 1 work starts until they are approved.
