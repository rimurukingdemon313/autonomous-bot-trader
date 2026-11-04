# FND-1A: FND-1 amended before any outcome (preregistration)

**Written, frozen and registered on 2026-11-04, after FND-1's run stopped at its data guard and before any FND-1 or
FND-1A outcome was computed.**

| | |
|---|---|
| Frozen spec | `research/specs/FND-1A.json` |
| Spec sha256 | `caffd4e7e05d92748acdea60534bc8751f8b965258af993f82489d7271a4e802` |
| Code | `scripts/fnd1a.py` and `scripts/xts1.py`, sha256 `bb24132f1a2e712d5fd5702766bfeb419db9bdf33b42d102345e08ee4a2e0233` |
| Data | the archives FND-1's run fetched on GitHub's runner (branch `fnd1-run`, `ab13f67`), each month checked against its published sha256 there; each file checked against the run's manifest before it is read |
| Threshold | t ≥ **3.13**: the Bonferroni value for the 27 crypto tests already registered, abandoned FND-1's two included, plus these 2 |

## What happened, and the one change

FND-1's judge stopped before computing anything:

- Binance's USDT-M funding archive begins in 2020-01. CR-1 had already recorded that, and it was missed here.
- FND-1's guard required the 2019-12 month, for the first week of 2020's signal, so it refused to run, as built:
  nothing is filled.
- No outcome was read. FND-1 is recorded as ABANDONED in the registry, with that reason.

FND-1A is FND-1 with one change: **the guard reads funding months from the archive's first month, 2020-01**. The
first days of January 2020, before 18 settlements exist, have no signal and so no trade. FND-1 already said that of
any day without its settlements.

**Unchanged:** the rule (flat above 0.03% a settlement, otherwise long), the costs, the periods (development
2020-01 to 2022-06, validation 2022-07 to 2024-06, holdout 2024-07 to 2026-09 opened once and only after a pass), the
seven gates and the holdout rule. They are all in `research/preregistrations/FND-1.md`.

**Raised:** the threshold, from 3.11 to 3.13, because FND-1's registration still counts.

## Result (run 2026-11-04, locally on the runner's fetched archives; `research/knowledge/FND-1A.json`)

**FAILED.** Two gates failed, so the holdout stays unread and nothing changes. The judged period was 2020-01 to
2024-06 (1,637 days). The book stood aside on 12.7% of BTC's days and 16.0% of ETH's.

| | Mean a day | Annual (arithmetic) | Sharpe | t | Gate |
|---|---|---|---|---|---|
| The book, net | 0.185% | +68% | 1.04 | **2.20** | t ≥ 3.13: **failed** |
| Development 2020-01 to 2022-06 | 0.169% | +62% | 0.83 | 1.31 | > 0: passed |
| Validation 2022-07 to 2024-06 | 0.205% | +75% | 1.45 | 2.05 | > 0: passed |
| Cost doubled | 0.182% | +66% | 1.02 | 2.16 | > 0: passed |
| BTC alone / ETH alone | 0.163% / 0.208% | +59% / +76% | 0.98 / 0.99 | 2.08 / 2.11 | > 0: passed |
| **Timing** (beyond each coin's average exposure) | **−0.023%** | **−8%** | −0.30 | **−0.64** | t ≥ 2.0: **failed** |

**By year** (sum of daily net): 2020 +144%, 2021 +97%, 2022 −78%, 2023 +91%, 2024 H1 +49%. The worst drawdown was
−75%.

**What it means, and no more.**

- **The book's return is the coins' own rise, not the rule.** Standing aside when funding was crowded did worse
  than holding the same average exposure (−8% a year, t −0.64). Crowded funding was not followed by weaker returns
  here; if anything, the rule missed gains.
- **The contrarian reading of extreme funding is not supported** for BTC and ETH in 2020 to 2024-06, at a daily
  horizon.
