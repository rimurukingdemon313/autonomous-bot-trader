# Testing philosophy

## Principles

- **Tests before trust.** Nothing is "working" until a test shows it.
- **Behaviour, not shape.** A test checks what the system does, not that
  a function exists or returns the right type.
- **Known answers.** Market scenarios are constructed so that the correct
  result is known by construction. A random walk proves nothing.
- **Never mock the logic under test.** A fake broker replaces the network,
  not the engine.
- **Pin the clock.** Time is injected; tests control it.
- **Never weaken a production check to pass a test.** Decide which side is
  wrong first.
- **Tests that guard must be able to fail.** A guard test is checked by
  mutation: remove the guard, and the test must fail. A test that
  passes whether or not the guard exists guards nothing.

## Look-ahead and leakage tests

These are the most important tests in the project, because leakage
produces results that look like success.

- **Truncation (causality) test.** For every feature, label consumer and
  decision: the value at T computed on full history must equal the value
  computed on history truncated at T.
- **Adversarial injection.** Deliberately inject a leak, and require the
  test suite to detect it. At minimum: future close, future high, future
  low, future volume, future label, future normalization statistics, and
  future-selected parameters.
- **Leakage classes covered:** timestamp leakage (open time vs close
  time), resampling leakage (incomplete higher-timeframe bars),
  rolling-window leakage (centred or forward windows), normalization
  leakage (statistics from later data), feature-selection leakage,
  hyperparameter leakage, and model-selection leakage.
- **Invariance tests.** Every choice made from training and validation data
  (selected features, hyperparameters, model, threshold) must stay the
  same when the test-period data is altered. If changing the test data
  changes the choice, the test data leaked into the choice.
- **If any leakage test fails, work stops** until it is fixed.

## Test categories (details in [tests/README.md](../tests/README.md))

unit · integration · causality · leakage · data integrity · model · risk ·
execution · persistence · recovery · adversarial

## Reporting

Every change reports the exact command run, the number of tests passed and
failed, and, when the count changes, the old count, the new count and why.
