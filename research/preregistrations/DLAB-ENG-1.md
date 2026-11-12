# DLAB-ENG-1: a discovery scan of energy-futures-eia (preregistration)

**Written 2026-11-10 by the discovery lab, before the scan ran.** Research only: nothing here trades.

- Spec sha256: `836973189636e87e52be4575eb50a09bc9ee96d35de1b0122c59454bd19e8ef3` (`research/specs/DLAB-ENG-1.json`)
- Code sha256: `c9998fbc39edb384cafa03346a2cba4956f922384b5c5228d5a71740f989475c` (the lab: `scripts/dlab.py`, `aitrader/research/dlab/`)
- Protocol: `docs/DISCOVERY_LAB.md`

## What a scan does

It asks significance of nothing. Seven independent methods read the fit rows and emit their strongest rules: lead-lag with a causal screen, information theory, ordinal patterns, regimes by clustering, anomalies, an evolutionary search, and combinations across families. Each rule is then evaluated once on the check rows, which no method read, and classed with its reason. Every rule is kept in `research/dlab/candidates.jsonl`.

## The rows

| Rows | From | To (exclusive) | Use |
|---|---|---|---|
| Fit | 1994-03-01 | 2004-01-01 | the methods read these and nothing later |
| Check | 2004-01-01 | 2012-01-01 | each emitted rule is evaluated here once |
| Validation | 2012-01-01 | 2024-04-06 | **not loaded.** Read once, by `DLAB-ENG-1-V`, if a rule is promising |

## What is counted

- The scan is charged 400 tests and 20000 configurations against its fit and check rows (role select), its limits on what it may emit and look at. Those rows can no longer judge anything at an ordinary bar: they are a discovery set.
- The validation rows are charged only for the rules later judged on them.

## What follows

- At most 12 rules classed PROMISING_UNCONFIRMED (at most 3 a family and 4 an instrument) go to `DLAB-ENG-1-V`: frozen, and judged once on the validation rows at max(3.0, Bonferroni over every test on those rows).
- The scan's verdict is PASSED if it proposes such a batch and FAILED if it does not. Neither is a result about any rule: no rule is validated or disproved by a scan.
