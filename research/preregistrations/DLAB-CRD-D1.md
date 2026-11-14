# DLAB-CRD-D1: a directed test on crypto-perp-daily (preregistration)

**Written 2026-11-13 by the discovery lab's worker, before any check row was read.** Research only: nothing here trades.

- Spec sha256: `25c40c0ee1090770a63284a8e42497207445bb3a1f064ae037dcb76d9b0edfc9` (`research/specs/DLAB-CRD-D1.json`)
- Code sha256: `c98348b52e94a9267b9df9935fd020e3963a3f710525eb878eaa1a0c8f503786` (the lab: `scripts/dlab.py`, `aitrader/research/dlab/`)
- Submission `lab-coverage-crypto-daily-2026-11-13` (sha256 `9f4d6bfe1da145e5a6db3f9e96a8e5e7e8f434efd5b71137c516dad088ca06d5`), written by the lab (none (deterministic code), through the lab's worker, lab-cycle-1.1.0)
- Protocol: `docs/DISCOVERY_LAB.md`, `docs/RESEARCH_INSTITUTION.md`

## The hypothesis

**The cross-sectional rankings of crypto-daily no scan has looked at out of sample**

Among the instruments of this panel, a ranking on one of the features below separates the next rows' returns after costs. Each ranking is a separate, simple claim; none was chosen because it looked strong: they are the rankings the scans' places did not reach.

Mechanism: None is claimed in advance. These are the remaining cells of a declared space (absret(), ret(1), ret(10), ret(2), ret(20), ret(5), ret(60), vol(20), volr(5,60); held 1, 5, 20 rows), looked at so that the space is covered and a missing result is not mistaken for a negative one.

Why now: 26 of the 39 ranking-and-holding-period cells of this panel have no classed rule: the scans gave their places to the rankings strongest on the fit rows.

What would refute it: A book that is not positive on the check rows in both halves, or that cannot be told from the noise of every look already taken at those rows.

Comes from: docs/DISCOVERY_LAB.md section 11, aitrader/research/dlab/coverage.py

## The rules, frozen

| Id | Family | The rule | Why |
|---|---|---|---|
| `730d483fbfa11ecf` | cross-sectional | across 55 instruments: long the top 20% and short the bottom 20% by ret(1), equal weights, no net exposure; each row's book is held 1 rows (pointed by the fit rows) | no rule ranking the instruments on ret(1) and held 1 rows has been looked at out of sample |
| `e6ca32144c730fd4` | cross-sectional | across 55 instruments: long the top 20% and short the bottom 20% by ret(1), equal weights, no net exposure; each row's book is held 5 rows (pointed by the fit rows) | no rule ranking the instruments on ret(1) and held 5 rows has been looked at out of sample |
| `2a5e9afea2d2c24b` | cross-sectional | across 55 instruments: long the top 20% and short the bottom 20% by ret(2), equal weights, no net exposure; each row's book is held 1 rows (pointed by the fit rows) | no rule ranking the instruments on ret(2) and held 1 rows has been looked at out of sample |
| `85a3b779bb3ade96` | cross-sectional | across 55 instruments: long the top 20% and short the bottom 20% by ret(2), equal weights, no net exposure; each row's book is held 5 rows (pointed by the fit rows) | no rule ranking the instruments on ret(2) and held 5 rows has been looked at out of sample |
| `a253c276de6b7fbf` | cross-sectional | across 55 instruments: long the top 20% and short the bottom 20% by ret(5), equal weights, no net exposure; each row's book is held 1 rows (pointed by the fit rows) | no rule ranking the instruments on ret(5) and held 1 rows has been looked at out of sample |
| `74d563fd691cec7a` | cross-sectional | across 55 instruments: long the top 20% and short the bottom 20% by ret(60), equal weights, no net exposure; each row's book is held 20 rows (pointed by the fit rows) | no rule ranking the instruments on ret(60) and held 20 rows has been looked at out of sample |
| `9a6433c07d59144f` | cross-sectional | across 55 instruments: short the top 20% and long the bottom 20% by vol(20), equal weights, no net exposure; each row's book is held 1 rows (pointed by the fit rows) | no rule ranking the instruments on vol(20) and held 1 rows has been looked at out of sample |
| `e3a06caa743cbc11` | cross-sectional | across 55 instruments: short the top 20% and long the bottom 20% by vol(20), equal weights, no net exposure; each row's book is held 5 rows (pointed by the fit rows) | no rule ranking the instruments on vol(20) and held 5 rows has been looked at out of sample |
| `870ee5080bf6fc3d` | cross-sectional | across 55 instruments: short the top 20% and long the bottom 20% by vol(20), equal weights, no net exposure; each row's book is held 20 rows (pointed by the fit rows) | no rule ranking the instruments on vol(20) and held 20 rows has been looked at out of sample |
| `8cbe86b7052d8f02` | cross-sectional | across 55 instruments: long the top 20% and short the bottom 20% by volr(5,60), equal weights, no net exposure; each row's book is held 5 rows (pointed by the fit rows) | no rule ranking the instruments on volr(5,60) and held 5 rows has been looked at out of sample |
| `a44c805f53451be3` | cross-sectional | across 55 instruments: short the top 20% and long the bottom 20% by volr(5,60), equal weights, no net exposure; each row's book is held 20 rows (pointed by the fit rows) | no rule ranking the instruments on volr(5,60) and held 20 rows has been looked at out of sample |
| `b91fd26f72d8ca63` | cross-sectional | across 55 instruments: long the top 20% and short the bottom 20% by absret(), equal weights, no net exposure; each row's book is held 1 rows (pointed by the fit rows) | no rule ranking the instruments on absret() and held 1 rows has been looked at out of sample |
| `ebe918c106d88651` | cross-sectional | across 55 instruments: long the top 20% and short the bottom 20% by absret(), equal weights, no net exposure; each row's book is held 5 rows (pointed by the fit rows) | no rule ranking the instruments on absret() and held 5 rows has been looked at out of sample |
| `81563b62131957db` | cross-sectional | across 55 instruments: short the top 20% and long the bottom 20% by absret(), equal weights, no net exposure; each row's book is held 20 rows (pointed by the fit rows) | no rule ranking the instruments on absret() and held 20 rows has been looked at out of sample |

Refused before this registration, on the fit rows alone, and not tested (no test is charged for them):

- across 55 instruments: long the top 20% and short the bottom 20% by ret(1), equal weights, no net exposure; each row's book is held 20 rows: on the fit rows it behaves as cross-coin momentum (the 7-day winners against the losers: XSM-1) (correlation 0.73), judged and closed
- across 55 instruments: long the top 20% and short the bottom 20% by ret(2), equal weights, no net exposure; each row's book is held 20 rows: on the fit rows it behaves as cross-coin momentum (the 7-day winners against the losers: XSM-1) (correlation 0.75), judged and closed
- across 55 instruments: long the top 20% and short the bottom 20% by ret(5), equal weights, no net exposure; each row's book is held 5 rows: on the fit rows it behaves as cross-coin momentum (the 7-day winners against the losers: XSM-1) (correlation 0.87), judged and closed
- across 55 instruments: long the top 20% and short the bottom 20% by ret(5), equal weights, no net exposure; each row's book is held 20 rows: on the fit rows it behaves as cross-coin momentum (the 7-day winners against the losers: XSM-1) (correlation 0.74), judged and closed
- across 55 instruments: long the top 20% and short the bottom 20% by ret(10), equal weights, no net exposure; each row's book is held 1 rows: on the fit rows it behaves as cross-coin momentum (the 7-day winners against the losers: XSM-1) (correlation 0.87), judged and closed
- across 55 instruments: long the top 20% and short the bottom 20% by ret(10), equal weights, no net exposure; each row's book is held 5 rows: on the fit rows it behaves as cross-coin momentum (the 7-day winners against the losers: XSM-1) (correlation 0.95), judged and closed
- across 55 instruments: long the top 20% and short the bottom 20% by ret(10), equal weights, no net exposure; each row's book is held 20 rows: on the fit rows it behaves as cross-coin momentum (the 14-day winners against the losers: XSM-1) (correlation 0.87), judged and closed
- across 55 instruments: long the top 20% and short the bottom 20% by ret(20), equal weights, no net exposure; each row's book is held 1 rows: on the fit rows it behaves as cross-coin momentum (the 7-day winners against the losers: XSM-1) (correlation 0.76), judged and closed
- across 55 instruments: long the top 20% and short the bottom 20% by ret(20), equal weights, no net exposure; each row's book is held 5 rows: on the fit rows it behaves as cross-coin momentum (the 7-day winners against the losers: XSM-1) (correlation 0.75), judged and closed
- across 55 instruments: long the top 20% and short the bottom 20% by ret(20), equal weights, no net exposure; each row's book is held 20 rows: on the fit rows it behaves as cross-coin momentum (the 21-day winners against the losers: XSM-1) (correlation 0.81), judged and closed
- across 55 instruments: long the top 20% and short the bottom 20% by ret(60), equal weights, no net exposure; each row's book is held 1 rows: on the fit rows it behaves as cross-coin momentum (the 28-day winners against the losers: XSM-1) (correlation 0.77), judged and closed
- across 55 instruments: long the top 20% and short the bottom 20% by ret(60), equal weights, no net exposure; each row's book is held 5 rows: on the fit rows it behaves as cross-coin momentum (the 28-day winners against the losers: XSM-1) (correlation 0.78), judged and closed

## The rows

| Rows | From | To (exclusive) | Use |
|---|---|---|---|
| Fit | 2020-05-01 | 2022-07-01 | a rule that asked was pointed by these; nothing else was read |
| Check | 2022-07-01 | 2024-07-01 | each rule is evaluated here once |
| Validation | 2024-07-01 | 2026-11-01 | **not loaded.** Read once, by `DLAB-CRD-D1-V`, if a rule is promising |

## What is counted

- The test is charged 14 tests against its fit and check rows (role select): one for each rule.
- Each rule is classed against every look earlier scans and tests took at the same check rows, not only against this test's own rules.
- The validation rows are charged only for the rules later judged on them.

## What follows

- At most 12 rules go to `DLAB-CRD-D1-V`: frozen, and judged once on the validation rows at max(3.0, Bonferroni over every test on those rows), with every other gate (doubled costs, a late entry for a slow rule, both halves, 1,000 time-shifted books, no one year carrying it).
- The verdict is PASSED if the test proposes such a batch and FAILED if it does not. Neither is a result about any rule: no rule is validated or disproved here. No model approves anything: a rule is validated only by that separate test.
