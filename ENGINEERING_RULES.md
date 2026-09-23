# Engineering rules

These rules apply to every change, by anyone, human or AI. They are not
style preferences. Each one exists because breaking it produces a specific,
known failure, and most of them were learned the expensive way in the
predecessor project ([docs/HISTORICAL_ARCHIVE.md](docs/HISTORICAL_ARCHIVE.md)).

A change that breaks one of these rules is not merged, whatever else it
achieves.

---

## 1. Tests before trust
Nothing is described as working until a test shows it working. A test
asserts **behaviour**, not shape. When a test fails, first decide which side
is wrong. **A production check is never weakened to make a test pass.**
Market scenarios in tests are built so the correct answer is known by
construction; a random walk proves nothing.

## 2. No look-ahead
A decision at time T uses only information genuinely available at or
before T ([PROJECT_SPEC.md](PROJECT_SPEC.md) §9). Every feature, label
consumer, normalization, selection step and model is covered by a causality
test: the output computed on full history must equal the output computed on
history truncated at T. An injected one-step leak must make that test fail.
A causality test that never exercises the code path it guards is a failure
in its own right.

## 3. No fabricated data
If a value cannot be read, it is `missing`/`unknown`, with a reason. A
plausible-looking zero is worse than a visible gap, because it looks like
information. This covers prices, volume, spread, swap, balances, P/L,
broker state and statistics. A statistic over too small a sample is
labelled insufficient rather than reported as a finding.

## 4. No hidden assumptions
Every approximation (a modelled spread, an assumed swap, a fill rule) is
**declared**: written down, versioned, justified, and reported alongside any
result that depends on it. Results are also shown with the approximation
made pessimistic.

## 5. No deleting failed research
Failed experiments stay in the registry and the repository. Deleting them
shrinks the count of things tried, which makes every later result look more
significant than it is.

## 6. No unversioned model changes
Any change to features, labels, models, thresholds, decision logic, risk
logic, execution logic or prompts bumps the relevant version
([docs/VERSIONING.md](docs/VERSIONING.md)). Every decision and trade records
its version stamp. A behaviour change under an unchanged version makes
history uninterpretable.

## 7. No direct AI → broker path
The only route to the broker is decision → risk engine → execution →
broker. No model, agent, prompt or tool call holds broker credentials or
can place, modify or close an order.

## 8. The risk engine cannot be bypassed
It is the only code that approves a trade or computes a size. There is no
override flag, no "trusted" caller, and no configuration that disables it.
Risk may be reduced by adverse state and **never increased by it**.

## 9. Production and research remain auditable
Any result can be traced to the exact code commit, data version, feature
version, model version, parameters and registry entry that produced it.
Journals are append-only.

## 10. No claim of profitability without evidence
No document, commit, dashboard or message says or implies "profitable",
"works" or "ready" without evidence that meets the validation contract.
Small samples are called inconclusive. "No edge found" is reported plainly.

---

## Supporting rules

These follow from the ten above, and are listed separately because each
one has its own history of failure.

- **Pin the clock.** Nothing reads the system clock directly. Every
  time-dependent component takes an injectable `now`, so tests control
  time.
- **Fail closed** on safety-critical state ([ARCHITECTURE.md](ARCHITECTURE.md),
  "Failure behaviour").
- **Writes are never retried.** A broker write with an unknown outcome is
  resolved by querying the broker, never by resending
  ([EXECUTION_CONTRACT.md](EXECUTION_CONTRACT.md)).
- **One source of truth** for each concern: one feature definition, one
  risk engine, one version table. A second copy always drifts from the
  first.
- **Do not add complexity for its own sake.** An indicator, parameter or
  model earns its place only by adding independent information *and*
  improving out-of-sample robustness. Every parameter is one more degree of
  freedom for a backtest to curve-fit against. Where a simpler model is as
  robust as a complex one, use the simpler one.
- **Change one meaningful thing at a time**, so its effect can be measured.
- **No secrets in the repository**, ever ([SECURITY_CONTRACT.md](SECURITY_CONTRACT.md)).
- **Unknown names are refused.** An unknown model, strategy or
  configuration value is an error, never silently replaced with a default.
