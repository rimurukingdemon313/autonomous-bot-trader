# New-edge mission, Phase 1: repository and data audit

Written before any new strategy code exists. No earlier report was modified. Measurements come from
`python scripts/ne_audit.py`, which writes `research/results/NE-audit.json`. That script reads only
`data/ix/`, cut at 2021-01-01.

## 0. Scope, method, and one disclosure

**Read:**

- the contracts: DATA, RESEARCH, VALIDATION, EXECUTION, RISK, ENGINEERING_RULES;
- the reports named in the mission;
- the registry (45 trials, 201 counted tests);
- `research_status.json`;
- the simulators in `aitrader/research/discovery/` and `aitrader/backtest/`;
- the data loaders and the test inventory.

**Measured:** everything the index-CFD program may use.

**Disclosure.** While inventorying ranges, the auditor loaded `data/processed/EURUSD_M15.npz` and read
the maximum of its timestamp column. That file physically contains sealed fx-majors bars from 2017
onward.

- What it revealed: the file's last bar is 2022-07-08. No price, return or statistic of the sealed
  period was read or printed.
- It is recorded here because the contract says every access is auditable.
- Every later read in this mission goes through `DataStore` (which truncates at the seal) or the index
  files.

## 1. Instruments and date ranges

| Dataset | Instruments | Bars | Range on disk | Usable for new research |
|---|---|---|---|---|
| `data/processed/*_M15.npz` (FX-Data mirror of Dukascopy ticks) | 12 FX pairs, XAU, XAG | M15 bid/ask | 2007-03 → 2022-07 | 2007–2016 only: 2017+ is the sealed fx-majors holdout, isolated **logically** by `DataStore`, physically present |
| `data/m5/*_M5_2009_2016.npz` | 7 FX majors, XAU, XAG | M5 bid/ask | 2009 (XAG 2010) → 2016 | yes; already judged by ID-1, ID-2, EX-1, EX-2 and IX-1 |
| `data/ix/*_H1_2012_2020.npz` (Dukascopy datafeed hour candles) | USA500, USATECH, USA30, JPN225, HK50, AUS200 index CFDs | H1 bid/ask | 2012-01 (USA30 2013-09, AUS 2013-01) → 2020-12 | yes; judged by IX-2 and IX-3 |
| `data/ix/USATECHIDXUSD_M5_*` | Nasdaq-100 CFD | M5 bid/ask | 2012-01 → 2017-12 locally; 2018–2020 on branch `ix4d-data` | 2012–2016 was used as "select" by IX-4 |
| Index CFD 2021-01 → 2024-12 | — | — | **never fetched** | sealed holdout: not fetched, not touched |
| Index CFD 2025-01 → 2026-09 | the six CFDs above | H1 bid/ask | being fetched for FT-1 (branch `ft1-data`) | judged by FT-1 (registered before the fetch) |
| Daily long-history series (RC-*, DIV-*, TOM-D) | indices, ETFs, futures | D1 | on runners only; manifests in `data/rc`, `data/div*` | judged by RC/DIV/TOM programs; holdouts opened |
| `data/external/` | Brent, US CPI, S&P 500, US 10y, VIX | daily or monthly | to 2026 | point-in-time with documented lags |
| `data/rc/policy_rates.csv` (BIS) | 24 central-bank areas | daily | 1985 → 2026 | yes: financing benchmark, with availability times |

**Asset classes:**

- spot FX, gold and silver;
- equity-index CFDs (cash-index CFDs, below);
- daily multi-asset series for portfolio research only.

## 2. Time and daylight saving (measured, not assumed)

A US index CFD pauses around 17:00 New York every day. On Monday–Thursday the least-populated UTC hour
is:

- **22:00 UTC in January** (EST = UTC−5);
- **21:00 UTC in July** (EDT = UTC−4).

That is the same pattern for USA500, USATECH, USA30 and JPN225. The break therefore sits at 17:00
New York all year: **the timestamps are true UTC** and the New York session must be converted with
`zoneinfo`, not with a fixed offset. Every index program in this repository already does so.

A bar is labelled by its open and is available at its close (`BarSeries`).

## 3. Bid/ask availability: a defect that invalidates part of the history

The median quoted spread at the bar open, in basis points of the mid:

| Year | USA500 | USATECH | USA30 | JPN225 | HK50 | AUS200 |
|---|---|---|---|---|---|---|
| 2012 | **0.00** | **0.00** | — | **0.00** | **0.00** | — |
| 2013 | 2.59 | 6.93 | 2.67 | 5.39 | 6.47 | 3.88 |
| 2014 | 2.32 | 5.70 | 2.53 | 5.11 | 6.26 | 3.66 |
| 2015 | 2.07 | 2.47 | 1.29 | 4.84 | 3.28 | 5.31 |
| 2016 | 2.55 | 2.20 | 1.15 | 5.84 | 3.97 | 3.82 |
| 2017 | 2.18 | 1.81 | 1.00 | 4.11 | 3.86 | 3.56 |
| 2018 | 1.73 | 4.01 | 1.14 | 2.73 | 3.86 | 3.71 |
| 2019 | 1.58 | 3.73 | 1.12 | 2.81 | 4.01 | 3.73 |
| 2020 | 1.65 | 2.87 | 1.46 | 3.09 | 4.40 | 6.86 |

**Zero-spread bars:** the share of bars with ask ≤ bid at the open.

| Instrument | 2012 | 2013, all hours | 2013, New York 10:00–15:59 |
|---|---|---|---|
| USA500 | **100%** | 7.9% | 18.7% |
| USATECH | **100%** | 8.6% | 19.9% |
| JPN225 | **100%** | 8.3% | — |
| HK50 | **100%** | 26.0% | — |
| USATECH M5 | **100%** | 7.2% | 20.5% |

From 2014, every instrument has 0%.

**Interpretation.** Before 2014 the datafeed's index-CFD candles carry one price on both sides, so
they are not executable bid/ask.

**Invalid assumption found in earlier work:**

- IX-2, IX-3 and IX-4 judged 2012–2013 trades "at the real bid/ask". Their 2012 trades paid **no
  spread**, and IX-4's slippage was a quarter of a median that included zeros.
- The bias favours those strategies. All three FAILED anyway, so no verdict changes, but their 2012
  figures overstate what was tradable. IX-4's TCLOSE exit was positive only in 2012, which is now
  explained.
- The defect is recorded here. The old reports are not edited.

**Consequence for this mission:**

- index-CFD research uses **2014-01-01 onward** only;
- a bar with ask ≤ bid is never an entry or exit price. It is a missing quote, never repaired.

**Spread by New York hour.** The median spread in bp, 2012–2020, on bars with a positive spread:

| Hour (New York) | 02 | 09 | 10–15 | 16 | 17 | 20 |
|---|---|---|---|---|---|---|
| USA500 | 2.27 | 2.15 | 1.63–1.64 | 1.69 | 2.41 | 2.22 |
| USATECH | 3.62 | 2.96 | 1.56–1.60 | 1.60 | 5.87 | 4.20 |
| USA30 | 1.58 | 1.18 | 0.71 | 0.81 | 2.60 | 1.74 |

The spread is cheapest in the cash session and roughly doubles around the 17:00 break. Any timing
choice therefore changes the cost materially, and the real per-bar spread must be used, never a constant.

## 4. Missing and duplicate bars; sessions

**Integrity:** 0 duplicates and 0 out-of-order timestamps in every index file. Crossed closes (ask < bid
at the close): 0–3 per file. Impossible OHLC: 0.

**Coverage.** The share of weekday hour slots present is 0.35–0.94 by year. It is low in 2012–2013 and
2015–2017, because the CFD does not quote around its daily break and the datafeed omits hours with one
side missing.

What matters is the regular US session. The share of New York weekdays with all six 10:00–15:59 hour
bars present:

| | 2014 | 2015 | 2016 | 2017 | 2018 | 2019 | 2020 |
|---|---|---|---|---|---|---|---|
| USA500 | 0.95 | 0.97 | 0.97 | 0.97 | 0.97 | 0.97 | 0.97 |
| USATECH | 0.95 | 0.97 | 0.97 | 0.97 | 0.96 | 0.97 | 0.97 |
| USA30 | 0.95 | 0.97 | 0.97 | 0.97 | 0.97 | 0.97 | 0.97 |

The remaining 3% are US holidays and half-days.

**M5 Nasdaq coverage.** The same measure on 5-minute bars is only 0.55 in 2013 and 0.61 in 2014, then
0.95–0.97. A 5-minute program would lose many 2014 days.

**FX.** 19 of 21 FX bar files lack 00:00–00:59 UTC (docs/DATA_QUALITY_REPORT.md; measured bias
≤ 0.0034R).

**Sessions.** The US cash session (09:30–16:00 New York) does not align with hour bars:

- the 09:00 bar straddles the cash open;
- the 16:00 bar opens at the cash close.

A program on H1 bars may therefore use only:

- the 16:00 open (the cash close);
- the 10:00 open (the first bar wholly inside the session);
- the 09:00 open (the last pre-open quote).

## 5. Corporate actions, rolls, dividends

- **Rolls.** These are cash-index CFDs, not rolled futures. In regular hours, the mean absolute 1-hour
  return in quarterly-expiry weeks is close to other weeks: USA500 19.8 vs 17.8 bp, USATECH 24.3 vs
  22.3. The maximum single-hour move in those weeks is no larger than elsewhere (309 vs 313 bp), so
  there is no roll jump. The small excess is consistent with expiry-week volatility.
- **Dividends.** The price series is not adjusted: the index drops on ex-dividend days. A real CFD
  credits longs and debits shorts. Treatment:
  - long returns are understated, which is conservative;
  - short returns are overstated, so a short-holding strategy is charged a declared dividend
    yield (as `retail.py` does);
  - intraday strategies flat by the close are unaffected.
- **FX.** No corporate actions. Rollover financing is handled in `intraday.Costs`.

## 6. Alignment between instruments

Of the 40,770 hours present in any US CFD, 84.4% are present in all three. A cross-instrument rule must
therefore require every leg's bar to exist and skip otherwise, never forward-fill.

The M5 and H1 Nasdaq files come from the same source: on all 21,945 full hours, the M5 mid open equals
the H1 mid open exactly.

## 7. Execution assumptions in the existing simulators

There is **no single canonical backtester**. Six simulators coexist, each with its own fill rules:

| Simulator | Entry | Stop | Target | Slippage | Spread | Financing |
|---|---|---|---|---|---|---|
| `discovery/intraday.simulate` (ID-1, ID-2) | next bar open, ask or bid | triggered on the executable side; fills at `min(open, stop)` less 0.1 pip | at the level, never better; a stop+target bar is a stop | 0.1 pip per market fill | per-bar measured, stressable | per 21:00 UTC rollover from BIS rates + 1.5% markup |
| `discovery/ixmom.trades` (IX-1/2/3; frozen) | bar open, ask or bid | **at the stop level** (the optimistic convention found later) | — | ¼ median spread | per-bar measured | none (flat intraday) |
| `discovery/ixopen.simulate` (IX-4; frozen) | next open | **half a spread through** the level, or the gap open | at the level | ¼ median spread | per-bar measured | none |
| `discovery/rc.py` + `retail.py` (RC, TOM) | daily close | none | none | bps per unit traded | declared bp per instrument | BIS + 2.5% markup, day count 360 |
| `research/labels.CostModel` (DP/SL/CP/WF/R2–R4/COT/FLOW/PR-001) | label rules | at the level | at the level | 0.1 pip | measured | **swap approximated as 0.05 × ATR24 per night**: a crude declared approximation |
| `backtest/runner` + `broker/paper` (whole system) | paper broker | paper broker | paper broker | 0.1 pip | live bid/ask (Yahoo mode: a **fixed estimated** spread) | per 21:00 UTC rollover |

**Problems:**

- Results from different programs are not comparable to the basis point.
- The stop convention differs: at the level in `ixmom` and `labels`; through the level in `ixopen`.
- A cost ledger per trade exists only in `intraday.Trade`, which records spread, slippage, commission
  and financing separately.

Phase 2 builds one canonical bid/ask event engine for every new hypothesis. It runs a random-walk
placebo test against the old simulators as well.

## 8. Position sizing

- Research measures returns per unit of notional (bp of the entry mid) and in R.
- `aitrader/risk/engine.py` (risk-1.2.0) is the only sizing authority in the live path, and nothing in
  this mission changes it.
- The bot is PAPER only:
  - `max_risk_per_trade_pct_while_unvalidated` = 0.25;
  - live risk = 0.

## 9. Financing and overnight costs

There is **no broker swap or financing history**. No broker is integrated, and the TradeLocker adapter
was removed at the owner's request.

The only honest option is a **declared approximation**:

- benchmark = the BIS policy rate of the index's currency, public at the time;
- a long pays the benchmark plus a 2.5%/yr markup;
- a short receives the benchmark minus the markup;
- day count 360, charged per calendar day spanned by each 17:00 New York rollover crossed, so a Friday
  rollover counts three days.

This is the convention of `retail.py`, reused rather than reinvented. Results are reported with the
markup at ×1.5 and ×2.

## 10. Look-ahead and leakage protection that exists

The test suite contains:

- truncation-equality tests for every feature and primitive, including cross-instrument ones;
- tests that inject a one-bar leak and must catch it;
- a leakage gate that refuses a leaky feature at preregistration;
- a loader that truncates at the seal;
- resampling that never emits a forming bar;
- planted-edge vs random-walk tests for the labs, TOM, ID-2 and IX-4.

**Gap:** there is no test that runs **every** simulator on a driftless random walk with random entries
and asserts zero gross edge. That is the class of bug that made IX-4's first stop convention profitable
on noise. Phase 2 adds it.

## 11. Isolation of the splits

| Period | Physical isolation | Logical isolation |
|---|---|---|
| fx-majors 2017+ (sealed 2026-09-26) | **none**: inside the M15 files | `DataStore` truncates without a key; only a sole first post-seal registrant may open it; the registry refuses other uses |
| Index CFD 2021–2024 | **absent**: never downloaded | every ingest workflow names its years; none names 2021–2024 |
| Index CFD 2025-01 → 2026-09 | separate branch `ft1-data`, being fetched | registered as FT-1's judge period before the fetch |
| Multi-asset / equity-index-b holdouts | opened once each (DIV-2-H, RC-EQ2-H) | spent; recorded as OPENED |

## 12. Data deficiencies

Each item says how the research is downgraded.

1. **No executable broker.**
   - Fact: the build is PAPER only.
   - Consequence: criterion 2 of the mission ("executable through the broker/API already supported") can
     only be met in the paper engine. A candidate is at most **PROMISING BUT NOT YET PROVEN** until a
     broker adapter exists and its real costs are recorded forward.
2. **No broker spread history.**
   - Fact: Dukascopy's quoted spread is the only historical bid/ask.
   - Consequence: it is a proxy for whichever broker is eventually used. It is stressed ×1.25, ×1.5
     and ×2, never replaced by a constant.
3. **No slippage history.**
   - Fact: slippage is a declared approximation of ¼ of the bar's own spread per market fill.
   - Consequence: it is stressed.
4. **No latency data.**
   - Fact: latency is modelled as whole-bar delay only. One H1 bar is far harsher than real latency.
   - Consequence: it is reported, not tuned.
5. **No swap or financing history.** See section 9.
6. **No index-CFD bid/ask before 2014.** See section 3: about 7 usable years (2014–2020) before the
   holdout.
7. **No order-book depth, no traded volume.** Spot FX and CFD tick counts are not volume, so
   "abnormal volume" hypotheses cannot be tested honestly.
8. **No historical event calendar.**
   - Facts: the repository has none (FOMC, CPI, payrolls), and this container cannot reach
     federalreserve.gov or bls.gov (proxy 403).
   - Consequence: event-driven hypotheses need a runner fetch and a dated, versioned calendar. The
     FOMC calendar would give at most about 56 scheduled events in 2014–2020, below any meaningful
     trade-count criterion.
9. **Missing hour 00 UTC in 19 FX files** (measured bias ≤ 0.0034R).
10. **No cash-session-aligned bars at H1.** The US open is 09:30 and the bars open on the hour.

## 13. What this means for the search

The FX intraday space is exhausted on its usable history:

- 160+ registered tests;
- every family's gross edge is below a cost of 10–23% of a one-hour move.

The daily trend premium has been near zero since 2008 (DIV-2), and the retail financing markup makes it
negative.

The one dataset with clean, measured, executable bid/ask that has **not** been searched for its main
economic effects is the US index-CFD hour series, 2014–2020:

- moves are large relative to the spread: overnight and intraday standard deviations are about
  60–90 bp against a 1–4 bp round trip;
- the cash-session spread is the cheapest of the day.

New hypotheses are therefore restricted to US index CFDs from 2014, as follows:

| Period | Role |
|---|---|
| Development | 2014-01-01 → 2017-01-01 |
| Validation | 2017-01-01 → 2021-01-01 |
| Sealed holdout | 2021–2024, untouched |
| Extra unseen period | 2025-01 → 2026-09, only for validation passers |

Their thresholds count all 201+ registered tests.

**FT-1** (registered just before this mission) re-tests IX-2's frozen rule at 2025–2026 spreads. Under
this mission's rules it is a re-test of a failed hypothesis under a different cost regime. It stays
registered and will be run and reported, because deleting a registration hides a test. It cannot by
itself establish an edge.
