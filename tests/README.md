# tests/

`bash scripts/check.sh` runs the whole suite; every commit is gated on its
exit code. `python scripts/mutation_audit.py` removes each safety guard in
turn and requires a test to fail (results: docs/MUTATION_AUDIT.md).

## Where each required category lives

| Category | What it proves | Tests |
|---|---|---|
| **Unit** | each component on inputs whose right answer is known by construction | `unit/*` |
| **Integration** | data → features → agents → synthesis → risk → execution → paper broker → outcome tracking → learning, on constructed markets | `integration/test_pipeline.py` |
| **Causality** | features at *i* equal features on history truncated at *i*; changing the future does not change any past decision | `unit/test_features.py`, `integration/test_pipeline.py` |
| **Leakage** | injected leaks (a one-bar-ahead close, future high, low and activity, whole-series normalisation, a centred window) are caught by the checker; memory counts an outcome (a label) only after it resolved; the regime model sees training rows only; the loader stops at the sealed holdout | `unit/test_features.py`, `unit/test_regime_and_patterns.py`, `unit/test_registry_and_store.py` |
| **Data integrity** | tick filtering and counting, the measured clock, price scale, ordering, grid, crossed quotes, complete-bar resampling at the New York close | `unit/test_data.py` |
| **Model** | abstention on unfamiliar and abnormal states; the knowledge base loads only if it matches its card; malformed or out-of-vocabulary language-model replies are discarded | `unit/test_agents.py`, `unit/test_regime_and_patterns.py`, `integration/test_service.py` |
| **Risk** | every limit; risk falls after losses and never rises; the 1 % ceiling | `unit/test_risk.py` |
| **Execution** | intent before order, duplicate refusal, ambiguous outcome resolved by query and never by resend, final pre-submission checks, reconcile on restart | `unit/test_execution.py`, `unit/test_tradelocker_adapter.py` |
| **Persistence** | immutable tables refuse update and delete; hash chains detect tampering; state survives restart | `unit/test_db.py`, `integration/test_service.py` |
| **Adversarial** | leaks, malformed model output, a crashing agent, a name that says "demo", contradictory demo evidence, a stale price beyond the stop | across the files above |

**Not covered.** Probability calibration is reported by the backtest, not
asserted by a test. The TradeLocker adapter runs against a fake transport;
it has not been run against the real API from here.

## Rules

- Tests assert **behaviour**, not shape.
- The fake broker replaces the network, **not** the logic under test.
- The clock is always injected and pinned.
- Every guard test is **mutation-checked**: with the guard removed, the test
  must fail.
- A failing leakage test stops all further work until it is fixed.
- Test counts are reported on every change: old count, new count, and the
  reason for any difference.

See [docs/TESTING_PHILOSOPHY.md](../docs/TESTING_PHILOSOPHY.md).
