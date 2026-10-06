# New-edge mission: report

## Final verdict: NO ROBUST EDGE FOUND

**No robust edge was found under the available data and execution conditions.**

- Nothing is promoted.
- The bot stays PAPER, with no strategy enabled for execution.
- The 2021–2024 index-CFD holdout and the fx-majors 2017+ holdout are untouched.

Every number below is reproducible from the commit and command listed with it.

## 1. Repository and data audit

The full audit is in `docs/NEW_EDGE_AUDIT.md`. Its measurements come from `scripts/ne_audit.py`, which
writes `research/results/NE-audit.json`.

**Findings that change what research can claim:**

1. **Index-CFD quotes before 2014 are not bid/ask.**
   - 100% of 2012 bars have bid = ask, and in 2013 up to 26% (US regular hours: 19–20%).
   - IX-2, IX-3 and IX-4 priced 2012 trades "at the real bid/ask" and so paid no spread that year. All
     three failed anyway, and IX-4's only positive year (2012) is explained.
   - New research starts on 2014-01-01.
2. **Timestamps are true UTC.** This was measured: the CFD's daily break sits at 17:00 New York in both
   winter and summer.
3. **No contract-roll jumps** appear in quarterly-expiry weeks. Dividends are not adjusted, which is
   conservative for longs.
4. **Six simulators coexist with different fill rules.** One canonical engine now exists for all new
   work (section 4).
5. **The fx-majors holdout is isolated only logically.** Its bars are inside the M15 files, and the
   loader truncates them.
   - The audit disclosed one metadata read: the maximum timestamp of one file, and no price.

## 2. Data deficiencies

Each item is followed by how the research is downgraded.

| Deficiency | Consequence |
|---|---|
| **No executable broker** (PAPER only) | Nothing can be called executable through a broker. A historical pass could at most be PROMISING BUT NOT YET PROVEN |
| **No broker spread, slippage, latency or swap history** | Dukascopy quoted spreads are a proxy. Slippage (¼ spread a fill) and financing (BIS rate + 2.5% markup) are declared approximations, and every result is stressed ×1.25, ×1.5 and ×2 |
| **Index-CFD bid/ask exists only from 2014** before the sealed holdout | 7 usable years |
| **No traded volume or order-book depth** | Volume hypotheses are untestable |
| **No historical event calendar in the repository** | federalreserve.gov and bls.gov are unreachable from this container |
| **FX files miss hour 00 UTC** in 19 of 21 files | Measured bias ≤ 0.0034R |
| **H1 bars do not align with the 09:30 cash open** | Session rules can use only the 09:00, 10:00 and 16:00 opens |

## 3. Hypotheses preregistered in this mission

| ID | Mechanism | Preregistration | Tests counted |
|---|---|---|---|
| NE-1 / NE-ON | The overnight equity premium (Cooper–Cliff–Gulen; Kelly–Clark; Lou–Polk–Skouras; Boyarchenko et al.) | `research/preregistrations/NE-1.md`, spec sha256 `7981299…`, committed in `3733d90` before any NE trade was simulated on real data | 6 |
| NE-1 / NE-GAP | Overnight-to-intraday reversal (Berkman et al. 2012; Lou–Polk–Skouras "tug of war") | same | 6 |
| FT-1 | IX-2's frozen last-hour momentum at 2025–2026 spreads. Registered just before this mission; under its rules it is a cost-regime re-test of a failed hypothesis, so it is reported but cannot establish an edge alone | `research/preregistrations/FT-1.md`, committed in `fc2ef3d` before its data was fetched | 2 |

**Rejected before any data,** with reasons in NE-1.md:

- FOMC pre-announcement drift: about 56 events, plus a missing calendar;
- volatility compression → expansion: predicts size, not sign;
- abnormal volume: no volume exists;
- more FX intraday families: 160+ tests already;
- daily trend: near zero since 2008 (DIV-2);
- cross-index relative value: two legs of cost and no sign mechanism;
- Asian and Australian overnight windows: they contain the US session.

## 4. Research infrastructure built (Phase 2)

| Requirement | Where |
|---|---|
| One canonical event-driven bid/ask backtester | `aitrader/research/canon/engine.py` (canon-1.0.0) |
| Separate bid/ask execution | Buys at the ask, sells at the bid. One-sided bars are never fill prices but still trigger stops |
| Spread and slippage | The bar's own quoted spread, widened around the mid under stress. Slippage is a fraction of that spread |
| Stops and targets | A stop fills half a spread through its level, or at a gapping open. A target fills at its level, never better. A bar touching both counts as a stop |
| Financing | Per 17:00 New York rollover, from the point-in-time BIS rate + markup; a Friday counts 3 days. An unknown rate skips the trade |
| Per-trade cost ledger | gross, spread, slippage, through-fill, commission, financing and net, with an identity asserted on every trade |
| Point-in-time signals; no-look-ahead tests | `canon/sessions.py`; `tests/unit/test_canon_sessions.py` cuts at every decision bar, and a planted one-bar leak is caught |
| Placebos | Random windows (same side, holding time and stop) and random sides |
| Permutation test | Block permutation of sides |
| Parameter perturbation | Every neighbour configuration is run and gated |
| Walk-forward | Non-overlapping yearly windows (the rules fit nothing) |
| Monte Carlo | Moving-block bootstrap of the daily book |
| Multiple-testing control | Bonferroni over every registered test (217 after NE-1): t ≥ 3.6784 |
| Automatic rejection | `dev_gates` / `val_gates` in `scripts/ne1.py`: any failed gate rejects |
| Report fields | Gross, every cost, net, CI, t, win rate, profit factor, drawdown, exposure, turnover, the worst 5%, best-trade removal, exit reasons |
| Execution-bug detection | On a driftless random walk built from a fine path, no exit rule may show a gross edge (`tests/unit/test_canon.py`). The detector is proven: switching the through-fill off on a coarse path produces the false edge, and the test sees it |

**Placebo audit of the simulators** (`scripts/ne_placebo_audit.py` → `research/results/NE-placebo-audit.json`):

| Simulator | Path finer than the spread | Path coarser than the spread |
|---|---|---|
| canon (new) | no edge (\|t\| ≤ 1.91) | no edge (t ≤ 0.63) |
| `intraday.simulate` (ID-1, ID-2) | no edge (t ≤ −0.97) | **+0.025R gross, t 3.08** (stops filled at the level) |

The `intraday.simulate` bias can only have flattered ID-1 and ID-2, which failed anyway. Their verdicts
stand, and the defect is recorded rather than patched, because the code is frozen by their hashes.

## 5. Results: NE-1, development 2014-01-01 → 2017-01-01 (run once)

Run with `python scripts/ne1.py develop` (commit `9042912`). The output is
`research/knowledge/NE-1-dev.json`.

Units: basis points of the entry mid per trade. The t-statistic is on the daily book.

| Config | Trades | Gross | Spread | Slip | Through | Fin | **Net** | 95% CI (daily book) | t | ×1.25 | ×1.5 | +1 bar | vs random t |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| **ON-16-09** (primary) | 2207 | +2.67 | 2.45 | 1.23 | 0.03 | 1.05 | **−2.09** | −5.8 to +1.7 | −1.07 | −3.24 | −4.39 | −1.86 | −0.95 |
| ON-16-08 | 2207 | +3.17 | 2.47 | 1.24 | 0.03 | 1.05 | −1.63 | −5.2 to +2.0 | −0.86 | −2.83 | −4.06 | −1.15 | −0.60 |
| ON-16-10 | 2210 | +2.40 | 2.39 | 1.20 | 0.02 | 1.05 | −2.26 | −6.4 to +1.9 | −1.04 | −3.40 | −4.57 | −1.72 | −0.79 |
| ON-15-08 | 2216 | +2.91 | 2.34 | 1.17 | 0.03 | 1.07 | −1.70 | −6.0 to +2.5 | −0.81 | −2.83 | −3.94 | −1.55 | +0.25 |
| ON-15-09 | 2216 | +2.01 | 2.32 | 1.16 | 0.03 | 1.07 | −2.56 | −7.0 to +1.8 | −1.17 | −3.69 | −4.79 | −2.14 | −0.26 |
| ON-15-10 | 2216 | +1.67 | 2.26 | 1.13 | 0.03 | 1.07 | −2.81 | −7.6 to +2.1 | −1.12 | −3.90 | −5.03 | −2.30 | −0.18 |
| **GAP-z1.00-v60** (primary) | 645 | −9.19 | 2.36 | 1.18 | 0.03 | 0.04 | **−12.80** | −20.9 to −4.1 | −2.92 | −13.68 | −14.56 | −12.36 | −2.46 |
| GAP-z0.75-v60 | 883 | −6.67 | 2.40 | 1.20 | 0.02 | 0.07 | −10.36 | −16.6 to −2.4 | −2.63 | −11.26 | −12.16 | −11.80 | −1.78 |
| GAP-z1.25-v60 | 454 | −9.51 | 2.40 | 1.20 | 0.03 | 0.05 | −13.19 | −21.5 to −0.3 | −2.01 | −14.08 | −14.98 | −11.48 | −1.81 |
| GAP-z1.00-v40 | 665 | −8.00 | 2.35 | 1.17 | 0.03 | 0.05 | −11.61 | −21.1 to −4.8 | −3.10 | −12.52 | −13.39 | −11.45 | −1.80 |
| GAP-z1.00-v80 | 614 | −9.00 | 2.43 | 1.22 | 0.04 | 0.05 | −12.74 | −21.0 to −3.7 | −2.81 | −13.65 | −14.55 | −12.76 | −2.12 |
| GAP-z0.00-v60 | 2222 | −1.99 | 2.39 | 1.20 | 0.01 | 0.08 | −5.67 | −9.9 to −1.6 | −2.72 | −6.58 | −7.48 | −7.06 | −0.26 |

### Baselines (same engine, same costs)

| Baseline | Trades | Gross | Cost | Net | t |
|---|---|---|---|---|---|
| Intraday long, 10:00 → 16:00 | 2290 | +0.58 | 3.64 | −3.06 | −1.31 |
| Buy-and-hold, 16:00 → 16:00 | 1296 | +0.81 | 5.01 | −4.20 | −1.23 |
| No signal | — | — | — | 0.00 | — |
| GAP "follow" (price-direction baseline; reported, never promoted) | 645 | +8.28 | 3.60 | +4.68 | 1.06 |

### NE-ON primary (ON-16-09) in detail

- **Sizes:** 61 trades a month; exposure 74%. Win rate 48.4%; profit factor 0.89.
- **Tail:** the worst 5% of trades lose −81.7 bp or more. The maximum daily-book drawdown is 2,168 bp.
- **Walk-forward** (yearly windows), net bp: 2014 −1.57, 2015 −2.60, 2016 −2.07. Gross is positive
  every year (+4.25, +1.62, +2.21).
- **Halves:** −2.58 / −1.61.
- **Instruments:** USA30 −1.56, USA500 −2.00, USATECH −2.68.
- **Volatility terciles:** −3.15 / −1.99 / −1.13.
- **Mechanism:** overnight minus intraday gross is +2.18 bp (t 1.22). The direction matches the
  literature, but it is not significant.
- **vs random 17-hour long windows:** −2.09 vs −0.34 bp (Welch t −0.95). Random windows pay cheaper
  daytime spreads.
- **Monte Carlo:** P(total ≤ 0) = 0.91. Median maximum drawdown 2,238 bp; 95th percentile 3,857 bp.

**Failed gates:** net, t, costs ×1.25, costs ×1.5, latency, vs random, mechanism, without the top 5,
neighbours, halves. **Every gate.**

**What it means.** The premium exists at the size the literature predicts (+2.7 bp a night). The CFD
round trip costs 4.8 bp: 2.45 spread, 1.23 slippage and 1.05 financing. **Even with zero slippage and
zero financing it would net about +0.2 bp, which is not tradable.**

### NE-GAP primary (GAP-z1.00-v60) in detail

- **Sizes:** 18 trades a month; exposure 5%. Win rate 37.2%; profit factor 0.63.
- **Fade gross:** −9.19 bp. **Overnight moves continued rather than reversed.**
- **Permutation:** p = 0.999 for fading.
- **By year:** the continuation is concentrated in 2014–2015 (fade −21.2, −16.0 net) and gone in 2016
  (−1.26).
- **The opposite rule** (follow, a reported baseline): +4.68 bp net, t 1.06.
  - Not robust: t 0.34–1.22 at the neighbour settings, and −2.02 bp net on every day (z = 0).
  - It was not hypothesised, so promoting it now would be selecting after the result. **It is not
    promoted** and is recorded as a baseline.

**Validation (2017–2020):** not run. Nothing passed development, and the protocol forbids judging
failures on fresh data.

## 6. FT-1 (IX-2's frozen rule at 2025–2026 spreads)

Run with `python scripts/ft1.py run`, once, after `python scripts/ft1_refill.py`. The output is
`research/knowledge/FT-1.json`.

**Data:** Dukascopy H1 bid/ask, 2025-01-01 → 2026-09-30, fetched on a runner after FT-1 was committed
(`fc2ef3d`).

- The first fetch lost three months: JPN 2025-04 and 2025-06, USATECH 2025-07.
- A refill rule was committed **before any FT-1 result** (`b3a37d4`). It re-fetched them, and all
  10,272 bars present in both fetches agree exactly (`research/results/FT-1-refill.json`).
- No 2021–2024 bar was fetched.

**Median quoted spread, 2025–2026, in bp:**

| USA500 | USATECH | USA30 | JPN225 | HK50 | AUS200 |
|---|---|---|---|---|---|
| 0.87 | 0.50 | 0.45 | 1.43 | 4.32 | 5.45 |

The cost-compression premise is **confirmed**. Mean round-trip cost fell from 4.2–4.3 bp (2012–2020) to
2.6–3.0 bp.

**Results** (bp per trade; t on the daily book):

| Test | Trades | Gross | Cost | Net | t | ×1.5 | ×2 | Late entry | Halves |
|---|---|---|---|---|---|---|---|---|---|
| EQ-ALL | 2257 | **−1.48** | 2.56 | −4.04 | −5.96 | −5.38 | −6.73 | −3.61 | −3.43 / −4.63 |
| EQ-STRONG | 624 | **−1.56** | 3.01 | −4.57 | −4.60 | −5.88 | −7.12 | −4.15 | −4.73 / −4.41 |

- The US-only subset was reported, never gated: ALL −1.19, STRONG +0.10 bp.
- In 2012–2020 IX-2's gross was +1.07 (ALL) and +2.61 (STRONG).
- **Verdict: FAILED.** Both tests fail nine of ten gates; only the trade-count gate passes.
- **The signal itself reversed in 2025–2026**, so cheaper spreads cannot help. The hypothesis is
  rejected as stated in its preregistration.

## 7. Bugs and invalid assumptions found

1. **One-sided 2012–2013 index quotes priced as bid/ask** in IX-2, IX-3 and IX-4. The bias favoured
   those studies. Recorded in the audit, verdicts unchanged.
2. **`intraday.simulate` fills stops at the level.** It shows +0.025R gross on paths coarser than the
   spread (t 3.1). Recorded, verdicts unchanged.
3. **Two look-ahead flaws in this mission's own order builders**, both caught before any real-data run.
   Each let the existence of a future bar decide whether an order existed:
   - the overnight rule keyed days on the entry bar;
   - the gap rule required the 16:00 bar.
   The fix keys days on the decision bar. The truncation test was strengthened to cut exactly at
   every decision bar, because the first version cut at arbitrary bars and missed a planted leak.
4. **Two test fixtures in the canon tests were wrong, not the engine:**
   - a bar helper whose closes equal the next opens cannot build a gap;
   - the last bar ended the data before the stop was checked.
   The fixtures were fixed, and no production check was weakened.

## 8. Files changed in this mission

**Added:**

- `docs/NEW_EDGE_AUDIT.md`, `docs/NEW_EDGE_REPORT.md`;
- `aitrader/research/canon/__init__.py`, `engine.py`, `validate.py`, `sessions.py`;
- `scripts/ne_audit.py`, `scripts/ne_placebo_audit.py`, `scripts/ne1.py`;
- `tests/unit/test_canon.py`, `tests/unit/test_canon_sessions.py`, `tests/unit/test_ne1_runner.py`;
- `research/preregistrations/NE-1.md`, `research/specs/NE-1.json`;
- `research/knowledge/NE-1-dev.json`;
- `research/results/NE-audit.json`, `research/results/NE-placebo-audit.json`.

**Modified:**

- `research/registry.jsonl`: NE-1 trial and verdict, appended;
- `research_status.json` and `README.md`: regenerated.

**FT-1** (registered just before the mission):

- `scripts/ft1.py`, `research/preregistrations/FT-1.md`, `research/specs/FT-1.json`;
- `.github/workflows/ft1-ingest.yml`, on branch `ft1-ingest` only;
- `scripts/ft1_refill.py`, `research/results/FT-1-refill.json`;
- `research/knowledge/FT-1.json`;
- `.github/workflows/ft1-refetch.yml`, on branch `ft1-refetch` only.

No earlier report, registration, result or frozen study file was modified.

## 9. Commands executed

```
python scripts/ne_audit.py
python scripts/ne_placebo_audit.py
python -m pytest -q tests/unit/test_canon.py tests/unit/test_canon_sessions.py tests/unit/test_ne1_runner.py
bash scripts/check.sh                      # ruff + full suite
python scripts/ne1.py spec
python scripts/ne1.py preregister
python scripts/ne1.py develop              # once
python scripts/research_status.py && python scripts/research_status.py --check
python -m ruff check .
python scripts/ft1.py spec && python scripts/ft1.py preregister      # before the data was fetched
python scripts/ft1_refill.py <re-fetched dir>                         # the committed refill rule
python scripts/ft1.py run                                             # once
```

## 10. Test results

- `bash scripts/check.sh`: **857 passed**, ruff clean, before the NE-1 registration commit.
- `tests/unit/test_ne1_runner.py`: 2 passed. On synthetic data, noise promotes nothing and a planted
  overnight premium is found.

- Final `bash scripts/check.sh` after FT-1: **859 passed**, ruff clean, research status fresh.
- `research_status.json`: final status **NO EDGE**. NE-1 and FT-1 are recorded FAILED.

## 11. Next action for the operator

1. **Do not trade any strategy from this repository.**
   - Keep `MODE=PAPER`, with the bot paused or in observation only.
   - No configuration change is needed: nothing is promoted, and execution of unvalidated trades
     stays refused.
2. **The binding constraint is cost, not signal.** The one effect this mission found at its documented
   size, the overnight premium (+2.7 bp), costs 4.8 bp to hold through a retail CFD. More historical
   mining of the same quotes cannot change that.
   - Cheaper spreads alone do not fix it. In 2025–2026 the US index spreads fell to 0.45–0.87 bp
     (FT-1), but financing rose with policy rates. At about 4.3% plus the 2.5% markup, an overnight long
     pays about 1.9 bp a night, and about 2.6 bp averaged over weekends. So the round trip would still
     be roughly 3.5 bp against +2.7 bp gross.
   - This is arithmetic from measured inputs, not a test. Re-running NE-ON on 2025 data would be
     re-testing a failed hypothesis under a new cost regime, which this mission forbids.
   - The next evidence must be **measured execution cost at the broker you would actually use**.
   - When the MetaTrader 5 demo account exists, run the spread recorder on US500/US100/US30 for at
     least 4 weeks, at 09:00, 10:00, 16:00 and 17:00 New York.
   - Record the swap the broker charges.
   - Only if spread plus swap for an overnight long is **below about 1.5 bp** is a new, preregistered
     forward test of NE-ON worth running. It would get a new ID, and its data would be the future.
3. **Do not reopen any holdout to look for another answer.** The 2021–2024 index holdout stays sealed
   for a candidate that passes development and validation, if one ever does.

## Addendum: crypto perpetual futures (CR-1, CR-2)

After the CFD and FX programs, the search moved to the one liquid market where the carry is an observed
cash flow and costs are small relative to holding periods: **Binance USDT-M perpetuals**.

**Data:**

- Binance public archives, every file verified against its published SHA-256: 1,980 files, 0 failures,
  0 checksum mismatches.
- Point-in-time universe: the 11 perpetuals present when the funding archive starts (2020-01). None was
  delisted.
- 2025 onward is sealed and was never fetched.

### CR-1 (`research/preregistrations/CR-1.md`, committed `335d741` before any data was downloaded)

| | Development 2020–2022 | Validation 2023–2024 (t ≥ 3.6878) |
|---|---|---|
| CARRY, timed (k 3, entry at mean funding ≥ 1 bp) | **+8.43%/yr** on capital, t 11.5, Sharpe 6.6, max drawdown 2.4%. **Every development gate passed** | **+1.97%/yr**, t 6.46, but did **not** beat random timing (Welch t 1.60) and the k = 1 neighbour lost (−3.6%/yr): **FAILED** |
| CARRY by year | 2020 +10.3%, 2021 +17.5%, 2022 −2.3% | 2023 +1.37%, 2024 +2.60% |
| TSMOM-28 (momentum on the perpetual) | +68.8%/yr but t 1.19 and max drawdown 135%; does not beat random sides: **FAILED** | not run |

Position economics (development carry): funding +177 bp, basis +5 bp, cost 46 bp, net +137 bp per
position. Win rate 27%; median holding 4.7 days.

**Gate-code bugs found after validation** (`scripts/cr1_regate.py` → `research/results/CR-1-regate.json`):

1. **years:** a 2025 ledger stub of 0.0 counted as a losing year.
2. **monte_carlo:** `0.0 or 1` read the best possible probability as 1.

Corrected, both gates pass, and the verdict is **still FAILED** on placebo and neighbours. Ten
positions still open at the seal could not be closed and are counted, not estimated.

### CR-2 (`research/preregistrations/CR-2.md`, committed `58b9352`)

**Question:** does the plain always-on carry beat **cash** (the US policy rate)?

- Development is a walk-forward over 2020–2024: one position per coin per year.
- Overall excess over cash is **+3.0%/yr, t 5.6** (costs ×1.5: +2.9%).
- By year:

| 2020 | 2021 | 2022 | 2023 | 2024 |
|---|---|---|---|---|
| +2.4% | **+18.3%** | −2.6% | −2.6% | +0.0% |

The gate needed 4 of 5 years positive and got 2. **FAILED.** The 2025–2026 holdout stays sealed.

Eight perpetuals listed during January 2020 hold no 2020 position. Their idle capital was charged the
risk-free rate, which is conservative.

### What the crypto evidence says

- The funding premium is real: it is a cash flow, measured exactly. But it was large in **one regime**:
  zero interest rates and the 2021 leverage boom.
- Since 2022 it has been about equal to what Treasury bills pay. The arbitrage has been competed down to
  the risk-free rate, as He–Manela–Ross–von Wachter warned ("deviations diminish over time").
- **Crypto time-series momentum** did not beat random direction once funding is paid.

### Verdict after every program in this mission

**NO ROBUST EDGE FOUND UNDER THE AVAILABLE DATA AND EXECUTION CONDITIONS.**

The registry now counts every test, including CR-1 (8) and CR-2 (1).
