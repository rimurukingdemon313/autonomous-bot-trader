# Model contract

What every model must carry, how it is versioned, and what it may do in
production.

---

## 1. Model identity (the model card)

Every model artifact has a card containing:

| Field | Content |
|---|---|
| Model ID | unique and never reused |
| Version | per [docs/VERSIONING.md](docs/VERSIONING.md) |
| Purpose | what it estimates (for example: probability of hitting the target before the stop, or expected R after costs) and for which action set |
| Training period | exact start and end |
| Validation period | exact start and end |
| Out-of-sample period | exact start and end |
| Feature version | the exact feature definitions it consumes |
| Data version | the exact dataset it was trained on |
| Code version | the commit of the training code |
| Research version | the registry entry, or entries, that justify it |
| Hyperparameters | final values, and the search space they were chosen from |
| Validation results | as the validation contract requires, including baselines |
| Calibration | predicted against realised |
| Known limits | regimes, instruments or conditions where it is not valid |
| Status | CANDIDATE / VALIDATED / FROZEN / RETIRED / REJECTED |

**Any substantive change is a new version**, with a new card: retraining,
new data, new features, new hyperparameters or a new decision threshold.

## 2. Model selection principles

- **Simpler first.** Start with baselines and simple, regularised models.
  A more complex model has to beat a simpler one **out of sample**, and a
  model is never chosen because it sounds more like "AI".
- **Probabilities, not verdicts.** Models output probabilities or expected
  values **with uncertainty**. The decision layer acts on a conservative
  estimate, such as a lower confidence bound on expected R after costs,
  never on a point estimate alone.
- **Calibration is required.** A model whose probabilities do not match
  observed frequencies is not used for decisions until it is fixed.
- **Abstention is required.** Every model is paired with a familiarity
  (out-of-distribution) measure. When the current state is unlike the
  training data, the answer is NO_TRADE.

## 3. Artifacts

- A deployable model is a **frozen, immutable artifact**, identified by a
  content hash, with its card.
- Production loads only artifacts whose status is VALIDATED or FROZEN, and
  verifies the hash before use. A missing or mismatched artifact means
  NO_TRADE, never a fallback model.

## 4. Training and inference are separate

- Training runs in the research environment, and may use heavy tooling.
- Production performs **inference only**, with minimal dependencies.
- Both use the **same feature definitions**
  ([ARCHITECTURE.md](ARCHITECTURE.md), "Separation of environments").

## 5. No self-modification in production

A production model cannot retrain, re-tune, change its threshold or replace
itself. A change always follows:

```
NEW VERSION → TEST → VALIDATION → APPROVAL → DEPLOYMENT
```

Online learning in production is out of scope unless a future version of
this contract is specifically approved for it.

## 6. Monitoring

In production, predictions are compared with outcomes continuously. A run
of losses **inside** the predicted distribution is recorded as expected
variance. Sustained drift **outside** it flags the model for review. The
only automatic responses available are to reduce risk or stop the model.
Neither the model nor the monitor can increase risk.

## 7. Language models (LLMs)

A language model may assist with:

- research and hypothesis generation;
- explanation and summarisation;
- analysis of results and errors;
- a trade **veto**: it may cause a trade to be skipped, never cause one.

A language model may **not**:

- create a trade the validated pipeline did not produce;
- change direction, entry, stop, target, size or risk;
- be treated as knowing the future.

**Temporal leakage.** A language model trained on data up to its training
date *knows what happened* on most historical dates: rate decisions,
crises, the direction of major currencies. Asking it for a trading
judgement on a past date is look-ahead bias that no code can remove,
because the leak is in the model's weights. Therefore:

- a language model's trading judgement **cannot be validated on history
  before its training cutoff**, and an unvalidated component has no say
  over a trade;
- any LLM component used in a backtest must be **time-constrained**: it may
  only process information that existed at the decision time. Where its
  own knowledge cannot be excluded, its output on those dates is not
  evidence;
- a malformed, missing, contradictory or out-of-range LLM response
  resolves to NO_TRADE, and is never "repaired".

## 8. Decision threshold

The threshold that turns a model's estimate into BUY / SELL / NO_TRADE is
part of the model version. It is chosen on validation data only, and never
on out-of-sample or holdout data.

## 9. Amendment 1 — how an LLM opinion enters a decision (implemented)

An LLM's directional opinion is evidence with a weight equal to its
**measured forward reliability**: zero until, over at least 50 resolved
cases on each side, the outcomes of trades it opposed are shown to be worse
than those it agreed with (`ExperienceView.agent_reliability`). An opposing
opinion raises the required edge by that weight; an agreeing one lowers
nothing. LLM objections come from a closed vocabulary and may block a trade.
This keeps the LLM genuinely in the decision while keeping §7 true: nothing
it says is trusted before it has been measured on data it could not have
seen.

## 10. Amendment 2 — the language-model trader (owner decision, 2026-09-27)

The owner asked for a system that analyses and trades "like a professional
trader", not a fixed strategy. With `DECISION_MODE=llm_trader`, a language
model PROPOSES the trade: direction, timeframe (H1/H4/D1), stop, target and
maximum holding time. This amends §7 for that mode only. Everything else
stands:

- The risk engine sizes and approves every proposal, and may refuse it. The
  model never sees or sets a size or a limit.
- Execution, the demo guard, the kill switch and pause are unchanged. While
  trading is paused or stopped, the model is not consulted.
- A market-wide BLOCKING objection from the quantitative analysts
  (unfamiliar or abnormal market, bad data) stops the decision before the
  model is called.
- Any malformed, unsafe or out-of-range reply is NO_TRADE, never repaired.
  This covers a wrong-side stop, a stop closer than 0.3 or wider than 12
  H1-ATR, and an unknown timeframe or action.
- A validated lesson about its own trades in this context blocks the repeat.
- **It is never backtested.** The mode raises in BACKTEST. Its record is
  built forward, on prices no one has seen. Until it has at least 30 closed
  trades its win rate is labelled insufficient. It is PAPER/DEMO only;
  LIVE stays refused.
- It learns from every trade in two ways. It writes a review of each
  closed trade, stored immutably. Before each decision it reads its record,
  its most relevant past trades (losses first) with those reviews, and the
  validated lessons.

Code: `aitrader/agents/llm_trader.py`, `aitrader/memory/trade_memory.py`.
Tests: `tests/unit/test_llm_trader.py`, and the end-to-end test in
`tests/integration/test_service.py`.
