# data/

**Status: empty. Phase 1.**

## Purpose
Data acquisition, validation, conversion and versioning. Raw data files
are **not** committed to Git; manifests, versions, hashes and quality
reports are.

## Responsibilities (when built)
- A sourcing study: which history exists, from which providers, at what
  resolution, quality and licence, and how many years per instrument.
- Ingestion with a measured (not assumed) time convention, converted to UTC.
- Validation and a data-quality report per instrument.
- Choosing and sealing the **final holdout** before any research.

## Boundaries
- Never invent volume, spread, swap, order book, news, sentiment or
  liquidity.
- Never fill gaps silently.
- Never rewrite history after the fact. Corrections create a new version.

## Binding contracts
[DATA_CONTRACT.md](../DATA_CONTRACT.md) · [VALIDATION_CONTRACT.md](../VALIDATION_CONTRACT.md) §8
