# data/

**Status: implemented.** Code in [`aitrader/data/`](../aitrader/data/),
ingestion in [`scripts/ingest_dukascopy.py`](../scripts/ingest_dukascopy.py).

Raw ticks and processed bars are **not** committed (`data/processed/` is
ignored). [`manifest.json`](manifest.json) is: for every instrument, the
source repository and commit of every year, tick counts, dropped ticks by
reason, the measured price scale, the week-open clock, coverage, gaps,
spread statistics, the content hash of the bars, and the validation
verdict.

## Source

Dukascopy tick data (bid **and** ask) as mirrored on GitHub by the FX-Data
project, one branch per year. It is the only bid/ask history this
environment can reach (docs/RESEARCH_LOG.md).

| | |
|---|---|
| Instruments | 12 FX pairs, and XAUUSD |
| Coverage | 2007-03-30 → 2018 for the pairs (EURUSD to 2022-07); XAUUSD from 2011 |
| Clock | measured, not assumed: the week opens Sunday 21:00/22:00 UTC |
| Bars | M15 with bid and ask OHLC, tick count and measured spread; H1, H4 and D1 are built only from **complete** M15 buckets, H4/D1 aligned to the New York close |
| Final holdout | from 2017-01-01, **sealed**: `DataStore` truncates there unless it is given the key that only the pre-registered final test holds |

This is about **11 years, not 20**. No longer bid/ask history was
reachable, and quality comes before years.

## Rules the code enforces

- Invalid ticks (non-finite, non-positive, crossed) are **dropped and
  counted**, never repaired.
- The price scale is **derived**: exactly one power of ten must put the
  median inside the instrument's plausible band, or ingestion refuses. The
  source stores JPY pairs and gold divided by 100; this is how that was
  caught.
- Validation refuses wrong scale, non-increasing timestamps, off-grid
  times and ask below bid. Gaps are reported, never filled.
- Nothing is invented: no volume (tick count is labelled as activity), no
  swap history, no news.

Tests: `tests/unit/test_data.py`, `tests/unit/test_registry_and_store.py`.

## Binding contracts
[DATA_CONTRACT.md](../DATA_CONTRACT.md) · [VALIDATION_CONTRACT.md](../VALIDATION_CONTRACT.md) §8
