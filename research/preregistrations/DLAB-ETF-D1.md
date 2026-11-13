# DLAB-ETF-D1: a directed test on us-etf-broad-daily (preregistration)

**Written 2026-11-13 by the discovery lab's worker, before any check row was read.** Research only: nothing here trades.

- Spec sha256: `0d832f98e2b0056a1206548174fc2354b156a8957b761f47a14a2565da612bdb` (`research/specs/DLAB-ETF-D1.json`)
- Code sha256: `c98348b52e94a9267b9df9935fd020e3963a3f710525eb878eaa1a0c8f503786` (the lab: `scripts/dlab.py`, `aitrader/research/dlab/`)
- Submission `lab-coverage-etf-daily-2026-11-13` (sha256 `a63e49d65a35cceb23fdf86749ee3706702a0610e8f3c799c8d87c2c2981e4bd`), written by the lab (none (deterministic code), through the lab's worker, lab-cycle-1.1.0)
- Protocol: `docs/DISCOVERY_LAB.md`, `docs/RESEARCH_INSTITUTION.md`

## The hypothesis

**The cross-sectional rankings of etf-daily no scan has looked at out of sample**

Among the instruments of this panel, a ranking on one of the features below separates the next rows' returns after costs. Each ranking is a separate, simple claim; none was chosen because it looked strong: they are the rankings the scans' places did not reach.

Mechanism: None is claimed in advance. These are the remaining cells of a declared space (absret(), ret(10), ret(20), ret(5), ret(60), vol(20), volr(5,60); held 1, 5, 20 rows), looked at so that the space is covered and a missing result is not mistaken for a negative one.

Why now: 14 of the 27 ranking-and-holding-period cells of this panel have no classed rule: the scans gave their places to the rankings strongest on the fit rows.

What would refute it: A book that is not positive on the check rows in both halves, or that cannot be told from the noise of every look already taken at those rows.

Comes from: docs/DISCOVERY_LAB.md section 11, aitrader/research/dlab/coverage.py

## The rules, frozen

| Id | Family | The rule | Why |
|---|---|---|---|
| `5609de5f1a446b5d` | cross-sectional | across 31 instruments: short the top 20% and long the bottom 20% by ret(5), equal weights, no net exposure; each row's book is held 20 rows (pointed by the fit rows) | no rule ranking the instruments on ret(5) and held 20 rows has been looked at out of sample |
| `130f35bbe22688c2` | cross-sectional | across 31 instruments: short the top 20% and long the bottom 20% by ret(10), equal weights, no net exposure; each row's book is held 5 rows (pointed by the fit rows) | no rule ranking the instruments on ret(10) and held 5 rows has been looked at out of sample |
| `03f5f05b321104f6` | cross-sectional | across 31 instruments: long the top 20% and short the bottom 20% by ret(10), equal weights, no net exposure; each row's book is held 20 rows (pointed by the fit rows) | no rule ranking the instruments on ret(10) and held 20 rows has been looked at out of sample |
| `82ce5f23128dae21` | cross-sectional | across 31 instruments: short the top 20% and long the bottom 20% by ret(20), equal weights, no net exposure; each row's book is held 5 rows (pointed by the fit rows) | no rule ranking the instruments on ret(20) and held 5 rows has been looked at out of sample |
| `aac20b0a1631c95d` | cross-sectional | across 31 instruments: short the top 20% and long the bottom 20% by ret(20), equal weights, no net exposure; each row's book is held 20 rows (pointed by the fit rows) | no rule ranking the instruments on ret(20) and held 20 rows has been looked at out of sample |
| `1dbd49ab0e1a4a46` | cross-sectional | across 31 instruments: short the top 20% and long the bottom 20% by ret(60), equal weights, no net exposure; each row's book is held 1 rows (pointed by the fit rows) | no rule ranking the instruments on ret(60) and held 1 rows has been looked at out of sample |
| `5650c1bb3f03ef7e` | cross-sectional | across 31 instruments: long the top 20% and short the bottom 20% by vol(20), equal weights, no net exposure; each row's book is held 1 rows (pointed by the fit rows) | no rule ranking the instruments on vol(20) and held 1 rows has been looked at out of sample |
| `59aa2eaa980c6ad1` | cross-sectional | across 31 instruments: long the top 20% and short the bottom 20% by vol(20), equal weights, no net exposure; each row's book is held 5 rows (pointed by the fit rows) | no rule ranking the instruments on vol(20) and held 5 rows has been looked at out of sample |
| `7d8022da9eba11d6` | cross-sectional | across 31 instruments: long the top 20% and short the bottom 20% by vol(20), equal weights, no net exposure; each row's book is held 20 rows (pointed by the fit rows) | no rule ranking the instruments on vol(20) and held 20 rows has been looked at out of sample |
| `7480312c3e6b11aa` | cross-sectional | across 31 instruments: long the top 20% and short the bottom 20% by volr(5,60), equal weights, no net exposure; each row's book is held 20 rows (pointed by the fit rows) | no rule ranking the instruments on volr(5,60) and held 20 rows has been looked at out of sample |
| `c427f2b78cf67bf0` | cross-sectional | across 31 instruments: long the top 20% and short the bottom 20% by absret(), equal weights, no net exposure; each row's book is held 1 rows (pointed by the fit rows) | no rule ranking the instruments on absret() and held 1 rows has been looked at out of sample |
| `2e45e060edf062b8` | cross-sectional | across 31 instruments: long the top 20% and short the bottom 20% by absret(), equal weights, no net exposure; each row's book is held 20 rows (pointed by the fit rows) | no rule ranking the instruments on absret() and held 20 rows has been looked at out of sample |

Refused before this registration, on the fit rows alone, and not tested (no test is charged for them):

- across 31 instruments: long the top 20% and short the bottom 20% by ret(60), equal weights, no net exposure; each row's book is held 5 rows: on the fit rows it behaves as cross-sectional momentum (the 6-month winners against the losers: SEC-1) (correlation 0.77), judged and closed
- across 31 instruments: long the top 20% and short the bottom 20% by ret(60), equal weights, no net exposure; each row's book is held 20 rows: on the fit rows it behaves as cross-sectional momentum (the 6-month winners against the losers: SEC-1) (correlation 0.82), judged and closed

## The rows

| Rows | From | To (exclusive) | Use |
|---|---|---|---|
| Fit | 2007-01-01 | 2015-01-01 | a rule that asked was pointed by these; nothing else was read |
| Check | 2015-01-01 | 2020-01-01 | each rule is evaluated here once |
| Validation | 2020-01-01 | 2026-11-01 | **not loaded.** Read once, by `DLAB-ETF-D1-V`, if a rule is promising |

## What is counted

- The test is charged 12 tests against its fit and check rows (role select): one for each rule.
- Each rule is classed against every look earlier scans and tests took at the same check rows, not only against this test's own rules.
- The validation rows are charged only for the rules later judged on them.

## What follows

- At most 12 rules go to `DLAB-ETF-D1-V`: frozen, and judged once on the validation rows at max(3.0, Bonferroni over every test on those rows), with every other gate (doubled costs, a late entry for a slow rule, both halves, 1,000 time-shifted books, no one year carrying it).
- The verdict is PASSED if the test proposes such a batch and FAILED if it does not. Neither is a result about any rule: no rule is validated or disproved here. No model approves anything: a rule is validated only by that separate test.
