# research/

**Status: empty. Phase 3 and later.**

## Purpose
The home of experiment definitions, pre-registrations, the experiment
registry, and research results.

## Responsibilities (when built)
- Hold the append-only **experiment registry**: every hypothesis, the data
  ranges it used and their roles (fit, select, judge), the number of
  configurations run, and every verdict.
- Hold pre-registration documents, committed before their experiments run.
- Keep every result reproducible from its commit, data version and registry
  entry.

## Boundaries
- Research never changes the running system. It produces **candidate**
  versions, which go through the lifecycle.
- Failed experiments are never deleted.
- The final holdout is used only by the documented final test.

## Binding contracts
[RESEARCH_CONTRACT.md](../RESEARCH_CONTRACT.md) ·
[VALIDATION_CONTRACT.md](../VALIDATION_CONTRACT.md) ·
[docs/RESEARCH_PROCESS.md](../docs/RESEARCH_PROCESS.md)
