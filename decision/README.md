# decision/

**Status: implemented** in [`aitrader/decision/synthesis.py`](../aitrader/decision/synthesis.py)
and [`aitrader/agents/`](../aitrader/agents/).

Five agents give a point-in-time view of the same evidence packet:
**Market** (regime, familiarity), **Setup** (candidate action templates),
**Risk** (costs and spread against the stop), **Adversary** (the case
against, from a closed objection vocabulary) and **Reviewer** (the quality of
the evidence: analogue sample, noise, age and concentration, template agreement,
lessons and track record). All five report BEFORE synthesis; none sees the
decision. `brain.py` runs them; each has a deterministic core,
and an optional language-model layer can only add objections.

The synthesis is **not a vote**. It is anchored on the lower bound of the
historical-analogue expectancy (mean − 1.28 × SE over the k nearest
resolved situations). MAJOR objections subtract their measured penalty.
Any BLOCKING objection, an unfamiliar state, missing input or a malformed
model reply gives **NO_TRADE**.

The decision record carries the direction, entry, stop, target,
invalidation, expected R with its uncertainty, supporting and
contradicting evidence, the NO_TRADE reason and every version stamp. It
never carries a size: that is the risk engine's alone.

Modes `rules` and `random` exist for the PR-001 ablation (variants A and R).

Tests: `tests/unit/test_agents.py`, `tests/integration/test_pipeline.py`.

## Binding contracts
[ARCHITECTURE.md](../ARCHITECTURE.md) · [MODEL_CONTRACT.md](../MODEL_CONTRACT.md)
