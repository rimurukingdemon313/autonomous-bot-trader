# DLAB-ETF-1: a discovery scan of us-etf-broad-daily (preregistration)

**Written 2026-11-12 by the discovery lab, before the scan ran.** Research only: nothing here trades.

- Spec sha256: `317b73cdd931f61e6c928b469821ea1684a10b4dd55a86a10e04c791a95458d4` (`research/specs/DLAB-ETF-1.json`)
- Code sha256: `e38782c9e1536e0f72c425efd077eed22ed92b2d1309d55d2225d2d584fa1d81` (the lab: `scripts/dlab.py`, `aitrader/research/dlab/`)
- Protocol: `docs/DISCOVERY_LAB.md`

## What a scan does

It asks significance of nothing. Independent methods read the fit rows and emit their strongest rules: lead-lag with a causal screen, information theory, ordinal patterns, regimes by clustering, anomalies, an evolutionary search, combinations across families and, on a broad panel, rules traded on every instrument at once (cross-sectional books and pooled rules). Each rule is then evaluated once on the check rows, which no method read, and classed with its reason. Every rule is kept in `research/dlab/candidates.jsonl`.

Instruments and data: dataset `etf-daily` (`aitrader/research/dlab/datasets.py`). The validation window's bar also counts the earlier tests on: multi-asset-etf, us-equity-etf, equity-index-daily, equity-index-monthly, us-vol-etp.

## The rows

| Rows | From | To (exclusive) | Use |
|---|---|---|---|
| Fit | 2007-01-01 | 2015-01-01 | the methods read these and nothing later |
| Check | 2015-01-01 | 2020-01-01 | each emitted rule is evaluated here once |
| Validation | 2020-01-01 | 2026-11-01 | **not loaded.** Read once, by `DLAB-ETF-1-V`, if a rule is promising |

## What is counted

- The scan is charged 600 tests and 100000 configurations against its fit and check rows (role select), its limits on what it may emit and look at. Those rows can no longer judge anything at an ordinary bar: they are a discovery set.
- The validation rows are charged only for the rules later judged on them.

## What follows

- At most 12 rules (at most 3 a family and 4 an instrument) go to `DLAB-ETF-1-V`: frozen, and judged once on the validation rows at max(3.0, Bonferroni over every test on those rows). They are the rules classed PROMISING_UNCONFIRMED and, while the bar with them added is still 3.0, the next strongest rules that are positive in both halves of the check rows: a place that costs the bar nothing is not withheld.
- The scan's verdict is PASSED if it proposes such a batch and FAILED if it does not. Neither is a result about any rule: no rule is validated or disproved by a scan.
