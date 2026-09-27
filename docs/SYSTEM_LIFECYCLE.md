# System lifecycle

How a candidate moves from an idea to real money, and why it rarely should.

```
RESEARCH → BACKTEST → OUT-OF-SAMPLE → ROBUSTNESS → FINAL HOLDOUT → PAPER → DEMO → LIVE
```

| Stage | What happens | Gate to leave it | Who decides |
|---|---|---|---|
| RESEARCH | hypothesis registered, data defined, test built | pre-registration committed | process |
| BACKTEST | train and validation segments evaluated, walk-forward | validation criteria met | process |
| OUT-OF-SAMPLE | concatenated walk-forward test windows judged | significance after multiple-testing correction; beats baselines | process |
| ROBUSTNESS | costs, delay, missing data, perturbations, Monte Carlo | survives the battery | process |
| FINAL HOLDOUT | frozen candidate run once on sealed data | PASS | process, then **owner approval** |
| PAPER | live data, simulated fills, every decision recorded | results within the predicted range over the pre-registered period | **owner approval** |
| DEMO | real broker, demo account | consistent with paper; execution quality acceptable | **owner approval** |
| LIVE | real money | continuing monitoring | **owner, explicitly** |

## Rules

- **No automatic transition to LIVE, under any circumstances.**
- Every transition from PAPER onwards requires explicit owner approval,
  recorded with the evidence it was based on.
- The system may **demote** itself (reduce risk, pause, or stop a model)
  automatically. It may never **promote** itself.
- A failure at any stage returns the candidate to RESEARCH, as a new
  version, and the failure is recorded ([FAILURE_POLICY.md](FAILURE_POLICY.md)).
- Skipping a stage is not allowed. A candidate whose final holdout was
  INCONCLUSIVE has not passed.

## Operating states of the running system

| State | Meaning |
|---|---|
| PAUSED | running, recording, not deciding to trade |
| NO_TRADE | deciding, and deciding not to trade |
| PAPER | deciding and simulating |
| DEMO | deciding and executing on a demo account |
| HALTED | stopped by the risk engine or the kill switch, and needing human action |

The system's reported status is one of: RESEARCH, PAPER_READY, PAPER,
DEMO_READY, DEMO, LIVE_READY. LIVE_READY is used only when the evidence
genuinely supports it.

## Amendment 1 — forward testing of an unvalidated candidate

Running an unvalidated system in PAPER, or on a broker DEMO account, is
allowed as a **forward test**: no money is at risk, and it produces the only
evidence no one could have seen in advance. It is recorded under the
system's version stamp, labelled on the dashboard as unvalidated, and never
counted as validation of a historical claim. It does not move the candidate
up the lifecycle: LIVE still requires every gate above, and `MODE=LIVE` is
refused by the software.

## Amendment 2 — forward testing of a FAILED candidate

PR-001 failed. The knowledge base on the card is marked `FAILED`. A
forward test of it in PAPER, or on a broker DEMO account, is still allowed.
No money is at risk, and forward data is the only evidence the historical
record cannot contaminate. The expected result is a loss (−0.07 R per
trade historically). Because of that, **nothing trades until an operator
decides it should**: the service starts paused, and only an authenticated
resume starts it. The dashboard shows the card's status next to KNOWLEDGE.
