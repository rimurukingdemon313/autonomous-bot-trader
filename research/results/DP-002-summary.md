# DP-002 — result

**Verdict: FAILED.** This is a valid negative result.

- Preregistered in commit `8575918` before the run.
- Registry trial `DP-002`. Artifact: [`research/knowledge/DP-002.json`](../knowledge/DP-002.json).

| Stage | Result |
|---|---|
| Features | 29 daily features. All passed the truncation leakage test on real D1 bars. |
| Discovery screen (fit, 2007-06 → 2011-01, D1 bars) | **0 discoveries in 966 tests** at BH q ≤ 0.10. 956 cells were testable, with a median of 404 trades each. |
| Validation | No drafts to validate. The stumps model: 0 of 30 configurations passed; its best was −0.04R (t −0.74). |
| Confirmation (2013-07 → 2017-01) | Never reached. No outcome in this segment was read. |

**What changed from the hourly horizon.** On H1 (DP-001) no cell at all had a positive net mean.
On D1, 14.9% of cells did. Moving to the daily horizon did cut the cost burden. But the
best-looking cell had t = 2.87 (`usd_corr=high & range_contraction=high`, SELL, +0.23R, n = 347),
and among 966 tests that is about what luck alone produces. After the false-discovery control,
nothing is distinguishable from noise.

**Taken together.** DP-001 and DP-002 searched 2,700 declared cells and two model families
across two horizons. Neither found an edge in price-derived features on these 12 pairs that
survives costs and multiple testing.
