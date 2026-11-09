# FX mission report

## Verdict: NO VALIDATED FOREX EDGE FOUND

**Completed 2026-11-09.** The brief: find the highest risk-adjusted net profit in FX that survives rigorous,
reproducible out-of-sample testing, or say plainly that none does. The plan and the audit are in
`docs/FX_MISSION.md`.

This report covers:

- **176 FX tests**, each preregistered and judged once. Two of them are new in this mission (FXS-1, FXT-1).
- **About 2,700 screened cells** (DP-001, DP-002).
- **Every horizon the data supports:** M5 to monthly.

**No candidate passed every preregistered gate. None is VALIDATED.** Nothing here may be traded, deployed, or used to
change production logic, live execution or risk settings. Nothing was changed.

**The pattern behind every result.** On these majors, at a retail account's costs, the information found is about
the size of a trade's cost or smaller:

- intraday: a few tenths of an R, or about 1 bp per trade;
- daily and weekly: weak.

**The only clearly positive net evidence is old.** Currency trends at the monthly horizon earned +5.8% a year in
1975-1989 (FXT-1). It falls short of the significance bar, and the archive's trend rules failed on 2017-2022.

---

## 1. Every hypothesis investigated

### 1a. The new tests in this mission

| Id | Horizon | Hypothesis | Data | Net result | t (bar) | Status |
|---|---|---|---|---|---|---|
| FXS-1 | Intraday (holds of about 4.4 h) | A currency weakens during its own working hours (Ranaldo 2009; Breedon & Ranaldo 2013) | M5 bid/ask 2009-2016 | −0.90 bp a trade (+0.76 gross, 1.66 cost) | −2.47 (3.6158) | **REJECTED** |
| FXT-1 | Position (monthly) | Time-series momentum in GBP, JPY, CHF, CAD, AUD and NZD against the dollar (Moskowitz, Ooi & Pedersen 2012) | H.10 1975-1989, never read before | +5.79% a year | 2.71 (3.6294) | **REJECTED** as preregistered (t only). By this brief's labels: **PROMISING — NOT VALIDATED** |

### 1b. The twelve sources of edge in the brief

| # | Source | Status | Why |
|---|---|---|---|
| 1 | Forward points, cross-currency basis | NOT TESTABLE | No forward or basis history here. A spot or CFD account cannot trade the basis |
| 2 | Cross-currency relative value | REJECTED (earlier), no power for more | ID-1 B4, RV-1 H3 and R3 failed. A new reversion book would need a net Sharpe ratio of about 1.3 over 8 years |
| 3 | Carry and momentum | REJECTED | RV-1: carry ranked currencies in 2000-2007 (IC t 3.10) and earned nothing after 2008. RC-FX: t 1.72. A swap-free account earns no carry |
| 4 | Volatility risk premia | NOT TESTABLE | No FX options from a spot or CFD account, and no implied-volatility history. As a filter: R4-XA-VIX, RV-1 H5 |
| 5 | Macro divergence | REJECTED / NOT TESTABLE | R4-MACRO-CPI failed. No point-in-time macro vintages are reachable |
| 6 | Order flow and liquidity | NOT TESTABLE | No order flow or traded volume, only tick counts (ID-2 used them) |
| 7 | Session transitions | REJECTED | Price patterns at session opens failed (ID-1 B6, QT-1, FLOW-1). EX-1 screened 21 session families, an Asian-session USD drift among them (gross ≤ 2.2 bp against 2.6-3.1 bp of cost). The European and US home-currency windows, new here, failed as **FXS-1** |
| 8 | Lead-lag with related markets | REJECTED | C1-USD-LAG (M5), R4-XA-GOLD and R4-XA-VIX (D1), and ID-2's cross-market inputs |
| 9 | Event-driven | NOT TESTABLE as surprises | No consensus-forecast history |
| 10 | Regime-dependent | REJECTED (earlier) | RV-1 H5/H6 (volatility-scaled), ID-2's regime inputs |
| 11 | Statistical arbitrage and mean reversion | REJECTED | ID-1 B4, ID-2 R-MR, RV-1 H3, R3 |
| 12 | Machine learning, leakage-controlled | REJECTED | ID-2 (section 6) |
| + | Trend on untouched years | PROMISING — NOT VALIDATED | **FXT-1** |

### 1c. Every earlier FX program (from `research/registry.jsonl` and `docs/TRADING_EDGE_REGISTRY.md`)

| Program | Horizon | What it tested | Judged | Best hypothesis: net, t | Status |
|---|---|---|---|---|---|
| ID-1 | M5 | Sweeps, BOS+FVG, CHoCH, order blocks, opening range, squeeze, momentum, reversion, failed breakouts, session opens, USD lag, hybrids | 16 | D3 squeeze + H1 trend: −0.095 R, t −1.79 | REJECTED |
| ID-2 | M5-H1 | Ridge and tree models over every family, and 12 simple rules | 30 | ridge S15 τ 0.05: +0.054 R, t 1.56 | REJECTED |
| QT-1, QT-2 | M5 | Quarter levels, daily AMD, New York and London true opens | 6 | London true open: −0.054 R, t −1.73 | REJECTED |
| WF-001-003 | H1, M15 | Walk-forward rule sets | 3 | −0.13 to −0.20 R | REJECTED |
| SL-002 | H1 | Structural levels | 1 | −0.105 R, t −8.02 | REJECTED |
| FLOW-1 | M15 | Gotobi days, the London 4 pm fix | 4 | Gotobi after: +0.65 R, t 0.60 | REJECTED |
| EX-1 | M15 | Exploratory, 2007-2012: Asian-session USD drift, reversal of illiquid-hours moves, session momentum and reversal, activity-conditioned continuation | 21 (every look counted) | gross ≤ 2.2 bp against 2.6-3.1 bp of cost in every family | REJECTED |
| EX-2 | M15 | Exploratory: momentum into the futures settlement, FX and gold | 4 | FX gross +0.06 / +0.28 bp against 2.8 bp of cost | REJECTED |
| IX-1 | M5 | Gold and silver momentum into the COMEX settlement, 2013-2016 | 2 | −10.9 / −8.4 bp net, t −20.4 / −7.5 | REJECTED |
| MEH-1 | Fix | Month-end hedge rebalancing | 2 | +1.2 bp net, t 1.04 | REJECTED |
| R2A-D, R3, R4 | D1 | Carry by regime, rate changes, oil and CAD, regime momentum, rate information, CPI, gold and VIX lead-lag | 21 | R2D-2: +0.077 R, t 0.85 | REJECTED |
| CP-001, SL-001, XS-001 | D1 | Daily rules and cross-sectional books | 12 | CP-001-T2: +0.19 R, t 1.03 | REJECTED |
| COT-1 | D1-W1 | CFTC positioning, 11 variants | 11 | +0.017 R, t 0.37 | REJECTED |
| RC-FX | D1 | Composite of rate, momentum and positioning, 1990-2016 | 2 | t 1.72 | REJECTED |
| RV-1 | W1 | Cross-sectional carry, momentum, reversal, value, volatility-scaled | 7 | carry: IC t 3.10 (2000-2007), net ≈ 0 after 2008 | REJECTED |
| DP-001, DP-002 | H1, D1 | State × trigger discovery screens | 12 (6 each; 1,734 and 966 cells screened) | none survived the screen | REJECTED |
| PR-001 | H1 | The multi-agent system and its ablation | 4 | — | REJECTED |
| archive (6 programs) | M15-D1 | SMC, trend (Donchian, TSMOM, SMA), reversion, an eight-family program, judged 2017-2022 | 16 | all failed | REJECTED |
| DIV-2 | MN | Trend across 23 markets, currencies among them, at futures-style costs | 2 | t 4.38. Validated as a futures portfolio. A retail CFD's financing turns it to −5.7% a year, and its currency leg was never judged alone | Not an FX-only strategy |

---

## 2. The five strongest candidates, by validated performance

None is validated, so they are ranked by the strength of their out-of-sample net evidence. Figures are from each
program's artifact; a figure the artifact does not hold is shown as —.

| Rank | Candidate | Horizon | Net | Net t (bar) | Cost x1.5 / x2 | Status |
|---|---|---|---|---|---|---|
| 1 | **FXT-1**: currency TSMOM, 1975-1989 | Position, monthly | +5.79% a year; Sharpe 0.70; worst fall 15.9% | 2.71 (3.63) | +5.73% / +5.66% a year | PROMISING — NOT VALIDATED |
| 2 | RV-1 H1: cross-sectional carry | Weekly | ranking information 2000-2007 (IC t 3.10); net about 0 on 2008-2016 bid/ask | — | net −0.0013% a week at x2 | REJECTED |
| 3 | ID-2: ridge S15 τ 0.05 | M15 scanner | +0.054 R a trade (+0.10-0.19 R gross, beating random by t 3-7) | 1.56 (3.55) | +0.02-0.06 R at x1.25, t ≤ 1.1 | REJECTED |
| 4 | RV-1 H6: momentum, volatility-scaled | Weekly | — | 2.10 (2.81) | — | REJECTED |
| 5 | FXS-1: time of day | Intraday | −0.90 bp a trade (+0.76 gross, t 2.88) | −2.47 (3.62) | −1.73 / −2.56 bp | REJECTED |

**On the same capital and risk (10% annual volatility):**

| | FXT-1 | FXS-1 |
|---|---|---|
| Net a year | **+7.0%** | −8.6% |
| Worst fall | 19.2% | 96% (not compounded) |

The earlier programs did not record annualized account figures in comparable form, so they are not restated here.

---

## 3. The best candidate across all timeframes

**FXT-1: monthly time-series momentum in the majors against the dollar.** It is not validated:

- **The bar.** Its t of 2.71 is short of the bar set by 176 FX tests (3.6294), and short of this project's floor of
  3.0.
- **The evidence.** It is from 1975-1989, and the closest modern evidence is negative: the archive's trend rules
  failed on 2017-2022.

It is the strongest demonstrable FX evidence in the data here, not a demonstrated edge.

---

## 4. Scalping, intraday, swing and position

| Style | Horizon here | Programs | Best net result | What decides it |
|---|---|---|---|---|
| **Scalping** | M5, minutes (M1 does not exist here: the finest bars are M5) | ID-1, ID-2, QT-1, QT-2 | +0.054 R a trade, t 1.56 (ID-2); rules −0.04 to −0.21 R | Costs: 0.10-0.19 R a trade, as large as all the gross information found |
| **Intraday** | M15-H1, holds of hours | WF-001-003, SL-002, FLOW-1, EX-1, EX-2, IX-1, FXS-1, the AI desk (DESK-1) | FXS-1 +0.76 bp gross and −0.90 bp net; FLOW-1 Gotobi t 0.60 | Costs again: a round trip costs about twice the time-of-day move |
| **Swing** | D1, days to weeks | R2A-D, R3, R4, CP-001, SL-001, XS-001, COT-1, RC-FX | RC-FX t 1.72; CP-001-T2 +0.19 R, t 1.03 | No information: costs matter little at this horizon, and the signals' t stay within ±2.9 |
| **Position** | W1-MN, weeks to months | RV-1, FXT-1, archive-trend-3 | **FXT-1 +5.79% a year, t 2.71** | Real but modest premia, and too few years to confirm them |

**The more often a strategy trades here, the more it loses to costs.** The only positive net evidence is at the
position horizon, and it is not significant at the bar.

---

## 5. Complete net-performance statistics (the two new tests)

### FXS-1 (time of day, M5 bid/ask, 2009-2016)

| | |
|---|---|
| Trades | 14,542, about 1,800 a year, 4.4 h each. Seven a day: the Tokyo window could not be traded (section 9) |
| Per trade | gross +0.757 bp, cost 1.657 bp, **net −0.899 bp**; 46.6% won; profit factor 0.91 |
| The book | daily net mean −6.29 bp (one unit per trade); t −2.47; Sharpe −0.86; Sortino −1.18 |
| Account, one unit of equity per trade | −15.8% a year at 18.5% volatility |
| Account at 10% volatility | −8.6% a year |
| Exposure | up to four positions at once (the US window); about 30 position-hours a day across four pairs |
| By pair (net bp, t) | EURUSD +0.62 (1.39), GBPUSD −0.33 (−0.73), USDCHF −1.95 (−3.18), USDJPY −3.00 (−5.86) |
| By window (net bp, t) | EUROPE −0.35 (−0.68), US −1.32 (−5.08) |
| Years | 2 of 8 positive |
| Against random sides | the random sides lost −1.63 bp; Welch t 2.39 |
| By leg, gross (descriptive, after the verdict) | EURUSD Europe +2.47 bp (t 3.41), EURUSD US +1.08 (2.03), GBPUSD US +1.51 (3.33), GBPUSD Europe +0.65 (0.83), USDCHF +0.64 / +0.18, USDJPY US **−1.24** (−2.43) |

### FXT-1 (currency TSMOM, H.10, 1975-1989, swap-free)

| | |
|---|---|
| Months | 180 |
| Net | **+5.79% a year** (gross +5.91%) at 8.26% volatility; Sharpe 0.70; Sortino 1.31 |
| Mean monthly net | +0.48%, t 2.71 |
| Monthly profit factor | 1.71; 52.8% of months won; best +10.3%, worst −5.6% |
| Activity | about 5.4 position flips a year plus monthly resizing; gross exposure 1.5x; long 49.7% of position-months |
| By currency (contribution t) | GBP 3.22, JPY 2.00, CHF 1.02, CAD 0.79, NZD 0.46, AUD −0.01 |
| Against random signs | random signs −0.05% a month; Welch t 2.71 |

---

## 6. Drawdown, risk and the AI question

### Drawdown

| | FXS-1 | FXT-1 |
|---|---|---|
| Worst fall | 178% of equity at one unit per trade (it would have ended the account); 96% at 10% volatility | **15.85%**, August 1979 → December 1981 (28 months); 19.2% at 10% volatility |
| Worst year | 2011: −58.1% at one unit per trade | 1981: −7.5% |
| Longest losing run | — | 5 months |
| Losing years | 6 of 8 | 4 of 15 |

### Did AI add measurable value over a non-AI baseline?

- **As a BUY or SELL predictor: no.**
  - ID-2's models beat matched random entries by Welch t 3-7 before costs. After costs they netted +0.04 to
    +0.09 R at t ≤ 1.6.
  - Most of their ranking was cost avoidance: a model given only the cost-to-stop ratio ranked better than the full
    model.
  - Every directional input alone had IC ≤ 0.07 (`docs/ACTIVE_INTRADAY_REPORT.md`).
- **As trade filtering and regime classification: no.**
  - ID-2's filters (τ thresholds) and regime inputs did not raise the net to significance.
  - The live language-model desk lost −0.069 R per agreement over 375 agreements, and −0.357 R over 109
    (EVALUATION, t −3.2). No exit or filter rule repaired it (DESK-1).
- **As volatility forecasting for sizing: some value, unconfirmed.**
  - In FXT-1, sizing by a 60-day volatility forecast raised the Sharpe ratio from 0.54 (equal notional) to 0.70.
  - It is consistent with the literature: volatility is forecastable, direction much less so.
  - The difference was not tested for significance and is not a validated result.

---

## 7. Out-of-sample and walk-forward results

- **Development, validation and late signals.**
  - Neither new rule has a fitted parameter, so development and validation are consistency gates on unseen
    sub-periods.
  - FXS-1: −1.32 / −0.19 bp a trade. FXT-1: +4.26% / +7.53% a year (t 1.36 / 2.65).
  - Every year is reported (FXS-1 2 of 8 positive; FXT-1 11 of 15).
  - Both were rerun with late signals: FXS-1 one bar late −1.22 bp; FXT-1 one month late +4.12% a year.
- **ID-2's walk-forward.** Each year 2011-2013 was predicted by models fitted only on trades that had exited before
  it.
- **The sealed holdout (fx-majors from 2017-01-01) was not opened.**
  - No candidate passed its judge, and the registered rule opens it only for a passer. It stays available, unspent.
  - The archive's 16 verdicts on 2017-2022, all failed, came before the seal and are counted in every threshold.

---

## 8. Cost sensitivity

| | Costs x1 | x1.5 | x2 |
|---|---|---|---|
| FXS-1, net bp a trade (daily t) | −0.90 (−2.47) | −1.73 (−4.74) | −2.56 (−7.00) |
| FXT-1, net % a year (t) | +5.79 (2.71) | +5.73 (2.68) | +5.66 (2.66) |
| ID-2 positive configurations, net R | +0.04 to +0.09 | x1.25: +0.02 to +0.06, t ≤ 1.1 | — |
| RV-1 H1 carry, net a week | ≈ 0 | — | −0.0013% |

**Intraday results swing with costs, position results barely move.** FXS-1 at zero cost would have earned +0.76 bp a
trade. That is the information there is, and a retail round trip costs about twice that.

---

## 9. Data quality and leakage audits

### Point in time

- **FXS-1.** Every decision comes from the clock alone; no price chooses a trade. Fills are at the bars' own bid and
  ask.
- **FXT-1.** It uses H.10 rates only from 17:00 New York on the next business day, decides at the month's first
  business day, and fills at the next noon rate.
- **Tests.** Both test suites check that a later price changes nothing before it: `tests/unit/test_fxs1.py` and
  `test_fxt1.py`, 20 tests on markets built so the answer is known.

### The seal

- **The loaders refuse it.** `scripts/id1.py`'s `load` refuses 2017 on without the final test's key. `H10Store`
  truncates at 2016-12-29. Neither judge read a 2017 rate.
- **Disclosure: two downloads during the audit.**
  - To list each H.10 currency's first and last dates, the 2017-12-08 vintage was downloaded to the session's
    scratchpad (outside the repository). Only dates were printed, and the local copy was cut at 2016-12-31 at once.
  - The 2018-10-17 vintage was streamed through a filter that kept only pre-2017 rows.
- **The primary vintage on disk.** It is in `data/h10/`, which git ignores, as the repository's design has always had
  it. Its store truncates it.

### Data defects found

- **No 00:00-00:59 UTC bars for USDJPY in the M5 mirror** (`docs/DATA_QUALITY_REPORT.md`). FXS-1's Tokyo window
  opens at 00:00 UTC, so all of its windows were skipped by the preregistered 10-minute rule. That part of the
  hypothesis is untested.
- **The H.10 mirror holds no DEM, FRF or other pre-euro currencies**, so FXT-1's 1975-1989 book has no euro-area
  currency. CHF moved with the Deutsche mark in those years.
- **No bid and ask before 2009.** FXT-1's costs are declared (2 bp each way), not measured. The x2 result shows they
  barely matter at its turnover.
- **No policy rates before 1988.** FXT-1 is a swap-free account's result. A standard account's swaps for those years
  cannot be computed.
- **A cosmetic artifact defect.** FXT-1's stored `top_year` gate is the string "True" (a numpy boolean serialized as
  text). The verdict is unaffected.

### Survivorship and selection

- **Fixed in the spec before any outcome.**
  - FXS-1 trades the four pairs and three windows the published hypothesis names.
  - FXT-1 trades the H.10 majors that existed, each from its float date.
- **Nothing was removed after the fact.** No pair or currency was dropped. FXS-1's per-leg breakdown is labelled
  post hoc and claims nothing.

### Multiple testing and uncertainty

- **Thresholds.** Bonferroni over every FX test, 3.6158 and 3.6294.
- **Baselines and intervals.** Matched random baselines (random sides, random signs); month-block (FXS-1) and
  12-month-block (FXT-1) bootstrap intervals.

---

## 10. Reproducible scripts and configurations

| | |
|---|---|
| FXS-1 | `scripts/fxs1.py spec|preregister|judge`. Spec `research/specs/FXS-1.json` (sha256 `f5b338b5…`), code `3c2ad232…`. Preregistration `research/preregistrations/FXS-1.md`. Result `research/knowledge/FXS-1.json`, `research/results/fxs1-judge.log`, `research/results/fxs1-breakdown.txt` |
| FXT-1 | `scripts/fxt1.py spec|preregister|judge`. Spec `research/specs/FXT-1.json` (sha256 `1d02f601…`), code `663880df…`. Preregistration `research/preregistrations/FXT-1.md`. Result `research/knowledge/FXT-1.json`, `research/results/fxt1-judge.log` |
| Data | M5: `data/m5/*_M5_2009_2016.npz` (the `id-data` branch; `scripts/ingest_dukascopy.py`). H.10: `python scripts/h10_audit.py fetch`, checked against `data/h10/manifest.json` |
| Registry | `research/registry.jsonl` (both trials and verdicts); `python scripts/edge_registry.py` regenerates `docs/TRADING_EDGE_REGISTRY.md` (140 rejected, 1 validated: TRND-1, an index rule) |
| Tests | `python -m pytest tests/unit/test_fxs1.py tests/unit/test_fxt1.py` |

A judge refuses to run twice, and refuses if its spec or code differs from what was registered.

---

## 11. Final recommendation

**NO VALIDATED FOREX EDGE FOUND.** On the evidence, the FX desk's correct output stays **NO TRADE**. Nothing from this
mission is fit for paper or demo trading as a strategy, and nothing was changed in production.

**What could still change the answer.** Each step gathers evidence, and none is a promise:

1. **FXT-1's rule, forward.** Preregister it, unchanged, on months that do not exist yet, judged once at a fixed
   date, paper only (as TRND-F does for TRND-1). At a Sharpe ratio of 0.7, three years would give a t of only about
   1.2. It is slow evidence, but the only kind that cannot be fitted.
2. **Measured costs.** The intraday information found here (ID-2's selections, FXS-1's EURUSD European-hours leg) is
   about the size of the costs assumed.
   - What it needs: the funded account's real spreads and commissions, recorded for months.
   - Why: whether that information is tradable at all depends on them.
   - Then: a successor could be preregistered on data no one has read.
3. **Not this.** More rules or features on 2009-2016. Those years carry 176 tests, so a new pass there would
   most likely be a fitted one. And no opening of the seal for a candidate that failed its judge.
