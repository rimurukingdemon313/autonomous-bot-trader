# DLAB-CRD-1: a discovery scan of crypto-perp-daily (preregistration)

**Written 2026-11-12 by the discovery lab, before the scan ran.** Research only: nothing here trades.

- Spec sha256: `5a853e94360713b135cb00f487b0216918168ac9b8cb3af518dc8cfc0ddc30f8` (`research/specs/DLAB-CRD-1.json`)
- Code sha256: `b59d17f8702e0b7c25cf8d5a00e02342fe769667bf26510f11e7a595b72f4065` (the lab: `scripts/dlab.py`, `aitrader/research/dlab/`)
- Protocol: `docs/DISCOVERY_LAB.md`

## What a scan does

It asks significance of nothing. Independent methods read the fit rows and emit their strongest rules: lead-lag with a causal screen, information theory, ordinal patterns, regimes by clustering, anomalies, an evolutionary search, combinations across families and, on a broad panel, rules traded on every instrument at once (cross-sectional books and pooled rules). Each rule is then evaluated once on the check rows, which no method read, and classed with its reason. Every rule is kept in `research/dlab/candidates.jsonl`.

Instruments and data: dataset `crypto-daily` (`aitrader/research/dlab/datasets.py`). The validation window's bar also counts the earlier tests on: crypto-binance-usdtm, crypto-binance-usdtm-all, crypto-binance-spot, crypto-xvenue-hl-binance, crypto-perp-live-xvenue.

## The rows

| Rows | From | To (exclusive) | Use |
|---|---|---|---|
| Fit | 2020-05-01 | 2022-07-01 | the methods read these and nothing later |
| Check | 2022-07-01 | 2024-07-01 | each emitted rule is evaluated here once |
| Validation | 2024-07-01 | 2026-11-01 | **not loaded.** Read once, by `DLAB-CRD-1-V`, if a rule is promising |

## What is counted

- The scan is charged 600 tests and 100000 configurations against its fit and check rows (role select), its limits on what it may emit and look at. Those rows can no longer judge anything at an ordinary bar: they are a discovery set.
- The validation rows are charged only for the rules later judged on them.

## What follows

- At most 12 rules (at most 3 a family and 4 an instrument) go to `DLAB-CRD-1-V`: frozen, and judged once on the validation rows at max(3.0, Bonferroni over every test on those rows). They are the rules classed PROMISING_UNCONFIRMED and, while the bar with them added is still 3.0, the next strongest rules that are positive in both halves of the check rows: a place that costs the bar nothing is not withheld.
- The scan's verdict is PASSED if it proposes such a batch and FAILED if it does not. Neither is a result about any rule: no rule is validated or disproved by a scan.
