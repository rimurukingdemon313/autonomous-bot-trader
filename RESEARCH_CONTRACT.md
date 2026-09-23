# Research contract

How every experiment in this project is defined, registered, run and
recorded, whether a person or the AI proposes it.

---

## 1. Why a contract

Searching past data for patterns always finds some. The question is never
"did something look good?" but "how many things were tried before this one
looked good, and would it still look good on data that played no part in
choosing it?". The first question can only be answered if every attempt is
written down. The second can only be answered if some data is never used
to choose anything.

## 2. The experiment record

Every experiment has a registry entry containing:

| Field | Content |
|---|---|
| Experiment ID | unique, never reused |
| Hypothesis | the claim, stated so that data can refute it |
| Reason | why this is worth testing: prior evidence, literature, an error analysis or an observation |
| Data period | the full span of data the experiment touches |
| Training period | exact start and end |
| Validation period | exact start and end |
| Test period | exact start and end (out-of-sample) |
| Data used, per range | the role each range plays: fit, select or judge |
| Features | names and feature version |
| Model | family and version |
| Parameters | every parameter, and which were searched over |
| Configurations evaluated | how many variants were actually run, including ones that decided nothing |
| Costs | spread, slippage, commission and financing assumptions, each marked measured or approximated |
| Pass rule | written **before** the experiment runs |
| Result | the numbers |
| Statistical metrics | per the validation contract |
| Conclusion | PASSED / FAILED / INCONCLUSIVE / INVALID / ABANDONED, with the reason |
| Versions | code commit, data version, feature version |

## 3. Pre-registration

1. The hypothesis, data ranges, pass rule and parameters are **committed
   before** the experiment runs. The commit time is the evidence.
2. Clarifications found while implementing are committed **before** any
   result is seen.
3. Registering an experiment is what counts it. An experiment that ran
   without being registered is still counted when it is discovered, and
   the discovery is recorded.
4. A result is recorded as a new entry that references the experiment. A
   registration is never edited after the fact.

## 4. The registry

- **Append-only.** No entry is deleted or rewritten. Out-of-order or
  duplicate entries are refused.
- **Role-aware.** A range of data used to fit, select or judge anything is
  *contaminated* for any later experiment that wants to treat it as unseen.
  A design-period look counts as a use.
- **The denominator.** The registry provides the number of hypotheses
  already judged on each dataset. Every significance threshold is computed
  from it ([VALIDATION_CONTRACT.md](VALIDATION_CONTRACT.md) §6).
- **Inherited counts.** Data that was already used in the predecessor
  project is **not** unseen because this repository is new. Those uses are
  imported into the registry before any new experiment runs on that data
  ([docs/HISTORICAL_ARCHIVE.md](docs/HISTORICAL_ARCHIVE.md)).

## 5. Autonomous research

The AI may propose hypotheses (for example, "this relationship appears
only in a particular regime"). An AI-proposed hypothesis follows exactly
the same path as a human one:

1. register the hypothesis;
2. define the data;
3. build the test;
4. evaluate it on training data;
5. evaluate it on validation data;
6. evaluate it out of sample;
7. record the result;
8. reject it if it failed.

On top of that:

- **Budget.** Autonomous search runs inside a declared hypothesis space and
  a declared budget of tests. Each test raises the bar for every later one,
  and the system knows this, because the registry tells it.
- **No retrying until it looks good.** A failed hypothesis is not re-run
  with small variations to rescue it. A genuinely new hypothesis must be
  materially different, is registered as new, and is counted.
- **Learning from a loss** means an error analysis that produces a
  hypothesis, which enters this process like any other. It never means
  adjusting live parameters.

## 6. Forbidden practices

- Changing parameters after seeing out-of-sample results, then reporting
  the new result as out-of-sample.
- Choosing a period, instrument or cost assumption because it makes the
  result look better.
- Reporting the best of many variants without counting the others.
- Dropping trades, periods or instruments after seeing them, unless the
  rule for dropping them was pre-registered.
- Deleting or hiding failed experiments.
- Touching the final holdout outside its documented procedure
  ([VALIDATION_CONTRACT.md](VALIDATION_CONTRACT.md) §8).
- Using a language model's judgement on historical dates it may remember
  ([MODEL_CONTRACT.md](MODEL_CONTRACT.md) §7).

## 7. Reproducibility

Every recorded result can be regenerated from its commit, its data version
and its registry entry. A result that cannot be reproduced is marked
INVALID, and it stays in the registry.
