# tests/

**Status: empty.** No trading tests exist in Phase 0, because there is no
code to test. This file defines what will be required.

## Required categories

| Category | What it proves |
|---|---|
| **Unit** | each component behaves correctly in isolation, on inputs whose correct output is known by construction |
| **Integration** | components work together along the real path: data → features → decision → risk → execution, against a fake broker |
| **Causality** | every feature, label consumer and decision gives the same value at T on full history and on history truncated at T |
| **Leakage** | injected leaks are detected: future close, high, low, volume, label, normalization statistics, and future-selected parameters; plus timestamp, resampling, rolling-window, normalization, feature-selection, hyperparameter and model-selection leakage |
| **Data integrity** | the time convention, price scale, gaps, duplicates, ordering and quality flags; that nothing is invented |
| **Model** | calibration, abstention on unfamiliar states, artifact hash verification, that a missing artifact means NO_TRADE |
| **Risk** | every limit; risk never increases after losses; no path bypasses the risk engine; fail-closed behaviour |
| **Execution** | idempotency, duplicate refusal, ambiguous outcomes resolved by query and never by resend, final pre-submission checks |
| **Persistence** | journals are append-only; state survives restart; nothing is lost or duplicated |
| **Recovery** | restart mid-order, lost connection, partial state: reconciliation before any new order |
| **Adversarial** | deliberate attempts to break guarantees: injected leaks, malformed model or LLM output, contradictory evidence, stale data, clock skew |

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
