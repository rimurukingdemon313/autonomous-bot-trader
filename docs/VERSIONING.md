# Versioning

A result is only interpretable if the exact system that produced it is
known.

## Versioned components

| Component | Changes that require a new version |
|---|---|
| Data | new source, new range, new cleaning or conversion rule |
| Features | any change to a definition, window, input or output |
| Labels | horizon, barriers, cost treatment |
| Regime | definitions, boundaries, familiarity measure |
| Model | retraining, new data, new features, new hyperparameters, new threshold |
| Decision | how model output becomes BUY / SELL / NO_TRADE |
| Risk engine | any limit, rule or sizing formula |
| Execution | order handling, checks, reconciliation |
| Prompts | any change to an LLM prompt or its parsing |
| Research | registry entries: each experiment is its own version reference |

Each component has its own version string. The system version identifies
the set.

## Rules

- **A behaviour change always bumps a version.** A silent change under an
  unchanged version makes history uninterpretable.
- **Every decision and every trade records the full version stamp**:
  system, data, features, labels, regime, model, decision, risk, execution,
  prompt, and the code commit.
- **Performance is analysed per version.** Results from different versions,
  or from different models or modes, are never averaged into one number.
- **Tuning is fingerprinted.** Any configuration override that changes
  what is traded is recorded as a fingerprint, so that an experiment and
  its control can be told apart afterwards.
- **Artifacts are immutable.** A model or dataset version, once recorded,
  always refers to the same bytes (content hash).
- **Change one meaningful thing at a time**, so its effect can be
  measured.

## Format

`component-MAJOR.MINOR.PATCH`

- **MAJOR**: changes what decisions are made in a way that invalidates
  comparison with earlier results.
- **MINOR**: changes behaviour in a way that is still comparable.
- **PATCH**: no behaviour change (documentation, refactoring proven
  equivalent by test).
