# models/

**Status: empty. Phase 5 and later.**

## Purpose
Model cards and references to frozen model artifacts. Large binary
artifacts are not committed to Git; their content hashes and cards are.

## Responsibilities (when built)
- One card per model version: ID, version, training / validation /
  out-of-sample periods, feature, data, code and research versions,
  hyperparameters, validation results, calibration, known limits, status.
- Artifacts are immutable and identified by content hash.

## Boundaries
- Production loads only VALIDATED or FROZEN artifacts, and verifies the
  hash. A missing or mismatched artifact means NO_TRADE, never a fallback.
- No model modifies itself in production.
- No model computes position size or risk.

## Binding contracts
[MODEL_CONTRACT.md](../MODEL_CONTRACT.md) · [docs/VERSIONING.md](../docs/VERSIONING.md)
