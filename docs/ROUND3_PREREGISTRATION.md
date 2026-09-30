# Round 3: genuine FX carry and interest-rate information

**Status: RUN on 2026-09-30 with the official BIS WS_CBPOL file, then FAILED: 8 hypotheses, all REJECTED** ([ROUND3_RESULTS.md](ROUND3_RESULTS.md)). It was BLOCKED earlier the same day, until the file was supplied. The design is frozen and unchanged.

- VALIDATED = 0.
- Round 3 tests run: 0.
- Tests charged to the registry: 0.

The frozen design is `research/specs/R3.json`, sha256
`267cf64622a30e05c1f52000c00eef99a0a779d816e2ba8975c59eb5681445a2`. It was committed before any
Round 3 outcome could be computed. `scripts/round3.py` refuses to run anything that differs from
it (`tests/unit/test_round3.py`).

## 1. Data: what was tried, what was obtained

Interest-rate sources probed from this environment (2026-09-29):

| Source | Series wanted | Result |
|---|---|---|
| FRED (fredgraph CSV and API) | policy and 3M rates, all currencies | **refused** by the network policy |
| ECB Data Portal | ECB main refinancing rate, €STR, Euribor | **refused** |
| BIS (stats.bis.org, data.bis.org, bulk CSV) | WS_CBPOL: all G10 policy rates, daily | **refused** |
| Federal Reserve (H.15 data download) | fed funds, T-bills | **refused** |
| RBA, RBNZ, BoC (Valet), BoE (IADB), SNB, BoJ | each policy rate | **refused** (all six) |
| OECD SDMX, IMF, World Bank, Eurostat, DBnomics | 3M interbank / policy rates | **refused** |
| datahub.io mirror on GitHub (reachable) | EMMI **Euribor 3M**, monthly | **obtained**, see below |

**Euribor 3M.**

- Each monthly value is the fixing on the first business day of the month. This was verified
  against published fixings: 1.343% on 2012-01-02 and 5.291% on 2008-10-01.
- The series is not revised.
- Its sha256 is recorded in `data/rates/manifest.json`.
- It is public at 12:00 CET on the fixing day (the fixing is at 11:00 CET).

**Coverage, 2007-04 → 2017-01** (`python scripts/round3.py status`):

| Currency | Policy rate | 3M interbank | Status |
|---|---|---|---|
| EUR | — | Euribor 3M, 1999-01 → 2016-12, monthly, largest gap 34 days | available (3M only) |
| USD, GBP, JPY, AUD, NZD, CAD, CHF | — | — | **UNAVAILABLE** |

**No pair in the universe has both sides of a differential.** Under the rules, every pair is
excluded. Nothing was substituted for a missing rate:

- a US 10-year yield was not used against a 3-month Euribor;
- no broker swap was assumed;
- no rate was interpolated.

**Genuine historical broker swap or financing data: not available anywhere.** The design
therefore defines a **RATE-DIFFERENTIAL CARRY PROXY**, clearly labelled, never called swap.

## 2. The frozen design

| Aspect | Rule |
|---|---|
| Rate type | **POLICY** rates only. If the data obtained is another type, Round 3 is re-preregistered as a new version, never switched silently. Two rate types are never mixed within a pair |
| Universe | Every pair whose **both** currencies are covered for the whole period, decided from coverage alone before any outcome is read. The run needs at least **6 pairs** |
| Point in time | A policy rate in force on date d is used from 17:00 New York on d. It is a step, never interpolated (`aitrader/data/rates.py`) |
| States | Fixed levels, nothing fitted. `rate_level` ±1.00pp. `rate_change` over 91 days ±0.25pp. `rate_accel` ±0.25pp. `policy_move` within 30 days ±0.10pp. Each is signed so that 2 favours buying the pair (`aitrader/research/discovery/carry.py`) |
| Periods | Fit 2007-04 → 2008-07 (regime medians only). **Judged 2008-07-11 → 2017-01-01**, once. The holdout (2017–) stays sealed |
| Exit | D4: 20 trading days with a 3 ATR stop, because carry is a monthly premium |
| Return accounting | Each trade is split into **spot** (net of spread, commission and slippage), **carry** (the proxy: side × the daily differential × days/365 × price/risk) and **financing** (a declared 0.5% a year broker markup). **net = spot + carry − financing**, and each part is reported (`CarryStudy`) |
| Cost sensitivity | Costs lower / normal / higher; markup 0 / 0.5 / 1.0% |
| Judgement | The existing 12-check battery at the registry's frozen threshold (taken at registration), then the board |
| Comparisons | Random direction (the battery's baseline), price-only (the spot component of the same trades), and the previously rejected R2A-1 and CP-001 |

### Hypotheses, a budget of 8

| ID | Condition | Side | Claim | Rationale (source) |
|---|---|---|---|---|
| R3-A | `rate_level=high` | BUY | Carry long: base out-yields quote by ≥ 1pp | Forward-premium anomaly (Fama 1984); carry premium (Lustig & Verdelhan 2007) |
| R3-B | `rate_level=low` | SELL | Carry long through the quote | Mirror of R3-A |
| R3-C | `rate_change=high` | BUY | The differential widened ≥ 0.25pp in 91 days | Slow capital (Engel 1996) |
| R3-D | `rate_change=low` | SELL | The differential narrowed ≥ 0.25pp | Mirror of R3-C |
| R3-E | `rate_accel=high` | BUY | Accelerating divergence | Inferred: slow repricing |
| R3-F | `policy_move=high` | BUY | A policy move in the base's favour within 30 days | Inferred post-announcement drift |
| R3-G | `rate_level=high&vix_state=low` | BUY | Carry only while VIX < 20 | Carry crashes in risk-off (Brunnermeier et al. 2008; Menkhoff et al. 2012) |
| R3-H | `rate_level=high&policy_move=mid` | BUY | Carry only when no central bank moved in 30 days | Event filter |

**Not repeated.**

- R2A: the static carry *sign* on 3 pairs, conditioned on VIX.
- R2B: the US 10-year change alone.

Every Round 3 condition uses the measured two-sided differential, and the duplicate check in
the discovery ledger stays active.

Round 3 is in the permanent edge registry as 8 **HYPOTHESIS** records, with the failure reason
"not run: policy-rate data unavailable" (`docs/TRADING_EDGE_REGISTRY.md`).

## 3. Built and tested, ready for the data

- `aitrader/data/rates.py` records each observation's currency, rate type, value, effective
  date, publication time (when known), source, revision status and availability timestamp.
  - Parsers for the **official formats as published**: the BIS WS_CBPOL flat CSV, FRED CSV
    and EMMI Euribor.
  - Verification against the sha256 manifest, the holdout seal and a coverage report.
- `aitrader/research/discovery/carry.py` contains the rate states, the carry proxy and
  `CarryStudy`.
- The confirmatory program accepts a study factory, so the full battery judges the combined
  return.
- `tests/unit/test_rates_and_carry.py` and `tests/unit/test_round3.py` check that:
  - a decision is never seen before its announcement;
  - a monthly value waits until its month ends;
  - there is no interpolation and no substitution;
  - the states are signed to the pair and are blind to later decisions;
  - the carry proxy has the right size and sign;
  - every trade splits exactly into spot + carry − financing;
  - the design cannot be changed after freezing;
  - nothing runs without coverage.

## 4. What unblocks it

Either of these, then `python scripts/round3.py status`:

1. **Network.** Allow `stats.bis.org` (preferred: one file holds every G10 policy rate, daily)
   or `fred.stlouisfed.org` in the environment's network settings.
2. **A file.** Download the BIS "Central bank policy rates" bulk CSV (WS_CBPOL, daily) on a
   machine with access, place it in `data/rates/`, and add its sha256 and `"format":
   "bis_cbpol"` to `data/rates/manifest.json`.

With 6 or more covered pairs, Round 3 is registered, with its threshold frozen from the
registry at that moment. It is then committed, run once, and reported with gross, carry, spot,
costs, financing and net R, the direction accuracy, and all robustness checks.

## 5. Data access attempt, 2026-09-30: BLOCKED

| Host | Request | Result |
|---|---|---|
| `stats.bis.org` | WS_CBPOL, daily, 8 areas (SDMX v2 CSV) | 403 from the egress proxy (`connect_rejected`, organisation policy) |
| `data.bis.org` | the WS_CBPOL bulk flat CSV | 403 (`connect_rejected`) |
| `fred.stlouisfed.org` | DFF | 403 (`connect_rejected`) |
| `data-api.ecb.europa.eu` | ECB MRO, daily | 403 (`connect_rejected`) |

The proxy documentation says not to retry or route around policy denials, so none was retried.

Reachable mirrors were checked once for the exact WS_CBPOL dataset:

- **datahub.io core packages on GitHub.** No policy-rate package exists; 9 candidate names all
  returned 404.
- **PyPI.** Its search is behind a JavaScript challenge. The SDMX packages there (`sdmx1`,
  `pandasdmx`) are clients that fetch from `stats.bis.org`. They bundle no data.

No trustworthy source of the exact dataset is reachable. **Round 3 is BLOCKED.**

Nothing was substituted, and no synthetic rate exists in the data path. The only rate file
present is Euribor 3M; it is used for no pair.

Two changes were made to the data layer, neither touching the frozen design:

- **The BIS parser.** The official file carries daily and monthly rows for the same area; the
  parser keeps only the daily rows.
- **`round3.py`.** It now validates a supplied file against published single-value policy
  rates, plus plausibility ranges for the Fed and SNB target ranges. A file that fails is
  refused.
