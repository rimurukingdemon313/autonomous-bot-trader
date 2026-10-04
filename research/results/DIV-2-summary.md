# DIV-2 results: DIV-1's frozen trend rules on long-history excess returns

Preregistered and frozen in commit `ef3be68` before any DIV-2 data was fetched (spec sha256
`cb440fbd…`). Judged once on a GitHub Actions runner (commit `024fb3a`, `.github/workflows/div2-run.yml`).
The holdout's reduced universe was declared **before** it was opened (`research/results/DIV-2-H-declaration.md`,
commit `bd819ae`). The holdout was then opened once (commit `b2ecc60`, `.github/workflows/div2-holdout.yml`).
Logs: `research/results/div2-*.log`, `research/results/div2h-*.log`.
Artifacts: `research/knowledge/DIV-2.json`, `research/knowledge/DIV-2-H.json`.

Returns are monthly portfolio returns (a fraction of capital), net of 2 bps per unit traded, on
futures-style excess returns (funding is inside the return). Gates and the holdout rule are in
`research/preregistrations/DIV-2.md`.

## Judge, 1990-01 → 2007-12 (216 months): PASSED, both hypotheses, every gate

| | H1 TSMOM12 | H2 BLEND |
|---|---|---|
| Net, annual (Sharpe, **t**) | +19.9% (1.02, **4.34**) | +18.5% (1.03, **4.38**) |
| Gross, annual | +20.1% | +19.0% |
| Costs, annual | 0.25% | 0.55% |
| Development 1990–98 (annual, t) | +17.1% (2.70) | +18.4% (3.20) |
| Validation 1999–2007 (annual, t) | +22.7% (3.42) | +18.5% (2.98) |
| Costs ×2 (annual, t) | +19.6% (4.29) | +17.9% (4.25) |
| Max drawdown (sum of monthly net) | 27.3% | 17.0% |
| Positive months | 61.6% | 65.3% |
| Leave one class out (mean monthly) | worst +0.81% (no equity) | worst +0.85% (no equity) |
| Contribution by class (mean monthly) | equity 0.84%, FX 0.61%, commodities 0.12%, bonds 0.11% | equity 0.69%, FX 0.59%, bonds 0.19%, commodities 0.11% |
| Average assets held / gross exposure | 19.6 / 4.0× | 19.6 / 4.0× |
| Retail CFD (+2.5%/yr on gross notional; reported only) | +9.8% (t 2.15) | +8.4% (t 2.00) |

## Already-seen period 2008-01 → 2020-12 (156 months; descriptive, never a gate)

| | H1 | H2 |
|---|---|---|
| Net, annual (Sharpe, t) | +1.9% (0.11, 0.38) | +7.2% (0.37, 1.34) |
| Max drawdown | 59.5% | 36.8% |
| Retail CFD, annual (t) | −7.3% (−1.48) | −2.0% (−0.36) |

## Sealed holdout 2021-01 → 2026-09 (70 months, opened once)

Frozen rule: mean net > 0 **and** mean net with costs ×2 > 0. As declared in advance, the pinned
H.10 vintage ends in 2018, so the holdout holds **no currencies** (16 assets).

| | H1 TSMOM12 | H2 BLEND |
|---|---|---|
| Net, annual (Sharpe, t) | +2.3% (0.11, **0.26**) | −4.6% (−0.26, −0.64) |
| Costs ×2, annual | +2.1% | −5.1% |
| Max drawdown (sum of monthly net) | 43.9% | 63.4% |
| Positive months | 57.1% | 48.6% |
| Retail CFD, annual (t) | **−5.7%** (−0.65) | −12.5% (−1.76) |
| Frozen holdout verdict | **VALIDATED** (by the sign rule) | **REJECTED** |

## What this means

1. **The trend premium was real and large in 1990–2007.** t 4.3–4.4 on 18 years nobody here had
   examined, positive in both halves, across classes, robust to doubled costs. That matches the
   literature's ~1.0 Sharpe for that era.
2. **It has been close to zero since 2008.** In the 13 seen years and the 70 holdout months
   together (226 months), H1 earned a Sharpe of about 0.1. H1 meets the frozen holdout rule only
   because that rule asks for a positive sign, not significance: its holdout t is 0.26, and a
   coin-flip strategy would "pass" it about half the time. **It is VALIDATED by the letter of the
   rule and not by the weight of the evidence.** It is recorded as the rule says, and described as
   this paragraph says. The weak holdout rule is a design flaw of this preregistration, declared here
   and not repaired after the fact.
3. **At a retail CFD broker it loses money.** The 4× gross exposure carried at about +2.5% a year
   financing costs about 10% a year. That turns every post-2008 period negative: −7.3% (2008–20) and
   −5.7% (2021+).
4. **Nothing is promoted to the live system.** Live promotion is a manual, operator-only file
   (`models/artifacts/promoted_edges.json`); research never writes it. A monthly multi-asset
   portfolio also has no path through the FX risk engine today. The evidence does not justify building
   one for a retail CFD account: the only cost model under which it is positive since 2008 is
   futures-style funding.
