# Experiment log

Each experiment has one entry, in order. Every entry was pre-registered before its judged
data was read, and ran once. The machine-readable record is `research/registry.jsonl`, and
the per-hypothesis numbers are in `research/knowledge/edge_registry.json`.

**Costs.** Unless an entry says otherwise, costs are the standard ones
([RESEARCH_PROTOCOL.md](RESEARCH_PROTOCOL.md) §3):

- the measured spread;
- slippage of 0.1 pip per fill;
- commission of 0.7 pip per round trip;
- swap of 0.05 × ATR24(H1), or 0.01 × ATR24(D1), per night.

**Universe.** 12 FX pairs: EURUSD, GBPUSD, USDJPY, AUDUSD, USDCAD, USDCHF, NZDUSD, EURGBP,
EURJPY, GBPJPY, EURCHF and AUDJPY. Dukascopy bid/ask bars.

## Archive, before this repository's registry

These six trials came from `claude-bot-trade-backoff-symbolfix`: SMC ×2, trend, reversion,
the SMC UTC rerun and the 8-family edge program. They add up to 16 tests, several of them on
2017–2022.

The archive's own documents give the results. None found a durable edge. Those trials are why
the holdout's prior exposure is declared in the registry.

## PR-001: the multi-agent pipeline ablation

| Field | Value |
|---|---|
| Hypotheses | H1: variant C has an edge. H2: learning adds value. H3: memory adds value. H4: the agents beat random |
| Pre-registration | `research/preregistrations/PR-001-multi-agent-ablation.md` |
| Periods | Fit 2007–2009; judge 2010–2016 |
| Tests / threshold | 4; t ≥ 3.023 |
| Result | All four FAIL. Every variant hit its drawdown halt during 2010 |
| Exploratory, no halt | B −0.053R (n 2,577); C −0.072R (n 2,928); R −0.159R (n 3,143). C beat R by +0.087R (t 2.65) |
| Conclusion | The filters beat random entries, but stay negative after costs |

## DP-001: discovery on H1

| Field | Value |
|---|---|
| Hypothesis | Some cell of a declared state × trigger grid, or a boosted-stumps model, has positive net expectancy on H1 |
| Commits | Pre-registered `907bb8e`; result `1325226` |
| Periods | Fit 2007-06 to 2011-01; select 2011-01 to 2013-07; judge 2013-07 to 2017-01 |
| Tests | 1,734 screened cells, 48 model configurations, and 6 judged tests (t ≥ 3.078) |
| Result | **FAILED.** 0 discoveries. Every cell was negative net of costs, the best at −0.089R |
| Conclusion | Gross expectancy is within ±0.03R; costs are 0.09–0.21R. Costs are the binding constraint on H1 |

## DP-002: discovery on D1

| Field | Value |
|---|---|
| Hypothesis | As DP-001, on daily bars with exits D1–D5 |
| Commits | Infrastructure `16c4100`; pre-registered `8575918`; result `aa86e9b` |
| Tests | 966 cells, 30 configurations, and 6 judged tests (t ≥ 3.144) |
| Result | **FAILED.** 0 discoveries. 14.9% of cells were positive net, against 0% on H1. The best t was 2.87 among 966 tests |
| Conclusion | Costs matter less on D1, but no signal survives multiple testing |

## CP-001: published trend following

| Field | Value |
|---|---|
| Hypotheses | Time-series momentum (r120 terciles) and moving-average trend (ma_slope terciles), BUY and SELL, D1, exit D4 (20 days) |
| Commits | Pre-registered `adf6d36`; result `4e6b3fc` |
| Periods | Fit 2007-03 to 2013-07; judge 2013-07 to 2017-01 |
| Tests / threshold | 4; t ≥ 3.180 |
| Result | **FAILED.** Longs about 0. Shorts +0.19R and +0.21R, both t ≈ 1.0 and concentrated in 2014 |
| Conclusion | Not distinguishable from luck after publication. The short side is recorded as an UNCERTAIN CONCLUSION |

## WF-002: stumps model on H1, the current architecture

| Field | Value |
|---|---|
| Hypothesis | Boosted stumps on the 23 production features predict the net R of exit template T2 (1.5/3.0 ATR, 48 bars). Trading where the prediction is positive has positive net expectancy |
| Commits | Pre-registered `329f701`; result `e13ae38` |
| Method | Decisions every 4 H1 bars (the 4-hour cycle). Expanding yearly walk-forward over 2011–2016; purge by resolve time; 5-day embargo |
| Tests / threshold | 1; t ≥ 3.197 |
| Result | **FAIL.** n 1,328, −0.126R, t −3.31. Versus random: Welch t 0.25. Positive in 2 of 6 folds. Costs ×1.5: −0.095R. One bar late: −0.106R |
| Conclusion | The model is no better than random on H1 |

## WF-001: k-NN analog on H1

| Field | Value |
|---|---|
| Hypothesis | The production analog estimator (k-NN, 18 features) predicts T2 net R. This is PR-001's only lead, moved to the lower-cost exit |
| Commit | Pre-registered `329f701` |
| Tests / threshold | 1; t ≥ 3.189 |
| Result | **FAIL.** n 22,539, −0.116R, t −12.6. Negative in every fold and on all 12 instruments. Costs ×1.5: −0.163R. One bar late: −0.127R |
| Against random | It **beats random entries** (−0.138R; Welch t 2.25). This is the only check it passes |
| Conclusion | PR-001's lead is confirmed and closed. The analog estimator carries real but tiny information, about +0.02R per trade over random, against about 0.1R of cost per trade. No exit or threshold choice made after this result could bridge a gap five times its size without being curve-fitting |

## WF-003: the M15 architecture

| Field | Value |
|---|---|
| Hypothesis | The same model as WF-002, deciding at every M15 close, on M15 features plus H1/H4 context from the last closed bar. Everything else identical to WF-002 |
| Commit | Pre-registered `e13ae38` |
| Tests / threshold | 1; t ≥ 3.205 |
| Result | **FAIL.** n 359, −0.199R, t −2.73. Versus random: Welch t 0.89. Positive in 1 of 6 folds, and that one only at +0.001R. Costs ×1.5: −0.42R. One bar late: −0.20R |
| Against WF-002 | **Not better, by every measure.** It is worse per trade (−0.199R against −0.126R) and has fewer trades. Its random baseline is much worse (−0.265R against −0.135R): the same 1.5/3.0-ATR exit on M15 is a smaller move, so the spread is a larger share of the risk. Fold stability is no better. The M15 architecture is therefore **not** adopted as a source of edge. It stays available as a scan cadence for the edge engine, which abstains without a promoted edge |

## SL-001: strategy library, daily forms

| Field | Value |
|---|---|
| Hypotheses | Donchian breakout, trend pullback and narrow-range breakout, each BUY and SELL, D1 |
| Commits | Pre-registered `8224ac5`; result `ce0d0c8` |
| Tests / threshold | 6; t ≥ 3.248 |
| Result | **FAILED.** Best: Donchian short +0.17R, t 0.65, failing permutation, years and instruments. Narrow-range long −0.16R, t −2.9 |
| Conclusion | Practitioner breakout and pullback rules do not survive costs on our data |

## SL-002: strategy library, hourly form

| Field | Value |
|---|---|
| Hypothesis | Breedon–Ranaldo local-hours depreciation: SELL EUR and GBP during European hours, H1, exit E3 |
| Commits | Pre-registered `8224ac5`; result `ce0d0c8` |
| Tests / threshold | 1; t ≥ 3.254 |
| Result | **FAILED.** n 8,901, −0.105R, t −8.0 |
| Conclusion | The documented effect is real in the literature but far smaller than an H1 trade's costs |

## XS-001: cross-sectional currency momentum

| Field | Value |
|---|---|
| Hypotheses | Menkhoff et al. (JFE 2012). Rank the 7 USD-pair currencies by their 24-day move against the dollar (the new causal primitive `xs_mom`). BUY the top tercile (XS-001-L), SELL the bottom (XS-001-S). D1, exit D4 |
| Commits | Pre-registered `e01114f`; result in the commit that adds this entry |
| Periods | Fit 2007-06 to 2013-07; judge 2013-07 to 2017-01 |
| Tests / threshold | 2; t ≥ 3.267 |
| Costs | Standard D1 costs |
| Result | **FAILED.** L −0.130R (n 203, t −2.13); S −0.112R (n 188, t −1.74). Every battery check failed |
| Conclusion | No cross-sectional momentum on the majors after costs. The negative sign is not significant, and it is **not** turned into a reversal hypothesis: doing so after seeing it would be a selection the registry never counted |

## Round 2: R2A–R2D (new information, conditional hypotheses)

The plan is [ROUND2_PLAN.md](ROUND2_PLAN.md) and the data is described in
[ROUND2_DATA_AUDIT.md](ROUND2_DATA_AUDIT.md). The full results are in
[ROUND2_RESULTS.md](ROUND2_RESULTS.md) and the ledger in [ROUND2_LEDGER.md](ROUND2_LEDGER.md).

Common to all four programs:

| Field | Value |
|---|---|
| Periods | Fit 2007-04 to 2008-07 (regime medians only); judge 2008-07-11 to 2017-01-01 |
| States | Fixed levels; nothing fitted |
| Costs | Standard D1 costs, except R2A, where swap is not charged (declared) |

| Program | Hypotheses | Threshold | Result |
|---|---|---|---|
| R2A: carry × risk regime (VIX, policy-rate signs) | 2 | t ≥ 3.279 | **FAILED.** −0.119R (n 263), −0.056R (n 475) |
| R2B: US rate-differential change (Fed H.15) | 2 | t ≥ 3.291 | **FAILED.** −0.108R (n 396), −0.061R (n 381) |
| R2C: oil → CAD (EIA Brent) | 2 | t ≥ 3.302 | **FAILED.** +0.047R (n 169, t 0.77), −0.088R (n 147) |
| R2D: momentum × calm (VIX) | 2 | t ≥ 3.312 | **FAILED.** −0.040R (n 593), +0.077R (n 581, t 0.85; outliers) |

Each program was preregistered and pushed before it ran; the commits are in the git history,
"Preregister R2A" to "Preregister R2D". Round 2 made 8 tests: 0 validated, 0 promising.

## R3: genuine interest-rate information and carry (BIS policy rates)

| Field | Value |
|---|---|
| Hypotheses | 8, frozen in `research/specs/R3.json` before the data existed here: carry level (A, B), differential widening and narrowing (C, D), acceleration (E), policy move (F), carry while VIX < 20 (G), carry without a recent policy move (H) |
| Data | BIS WS_CBPOL, daily; the official file supplied by the user, CSV sha256 `4f7e1170…`. 8 pairs qualify; JPY is not covered (no BoJ policy rate 2013-04 → 2016-09) |
| Periods | Judged 2008-07-11 → 2017-01-01 |
| Tests / threshold | 8; t ≥ 3.351 |
| Costs | Spread, 0.1 pip slippage, 0.7 pip commission. Swap replaced by the RATE-DIFFERENTIAL CARRY PROXY and a 0.5% a year financing markup |
| Result | **FAILED.** All 8 REJECTED. The best, R3-E, is +0.007R (t 0.10). Carry long: −0.083R, with +0.045R of carry and −0.101R of gross spot |
| Conclusion | Interest-rate information did not improve direction (P 40–47%). Carry income is real, but smaller than the spot losses on the majors, 2008–2016. See [ROUND3_RESULTS.md](ROUND3_RESULTS.md) |

## R4: directional information from outside the FX pair

| Field | Value |
|---|---|
| Hypotheses | 5, each requiring the pair NOT to have already moved: gold → AUD catch-up (×2), a VIX spike → safe-haven catch-up, US inflation acceleration → USD (×2) |
| Data | Dukascopy gold, Cboe VIX, BLS CPI-U (unrevised). COT, consensus surprises and decision surprises are DATA-BLOCKED ([ROUND4_AUDIT.md](ROUND4_AUDIT.md)) |
| Periods | Judged 2008-07-11 → 2017-01-01 (gold from 2011-05) |
| Tests / threshold | 5; t ≥ 3.372 |
| Costs | Standard D1 |
| Result | **FAILED.** All 5 REJECTED. The best, GOLD-A, is +0.015R (t 0.16): +0.10R over its price-only control, but negative at neighbouring thresholds and without its best trade |
| Defect | The program judged R4-XA-VIX-A on 11 pairs instead of its 5 registered pairs. It was fixed in confirm-1.1.0; on the registered pairs the result is −0.134R, t −2.07, still rejected (`research/knowledge/corrections.json`) |
| Conclusion | No outside source tested here adds directional information to FX after costs. See [ROUND4_RESULTS.md](ROUND4_RESULTS.md) |

## COT data audit (no hypothesis)

| Field | Value |
|---|---|
| Data | CFTC TFF Futures-Only bulk files supplied by the user: `fin_fut_txt_2006_2016.zip` (sha256 `c3a8d017…`) and `fut_fin_txt_2017.zip` (`e6e2dd53…`), kept unmodified and not committed |
| Coverage | 2006-06-13 → 2017-12-26 for EUR, JPY, GBP, CHF, CAD, AUD and the ICE USD index (603 reports). NZD has 600: 3 reports are missing in June–July 2006. 2017 is the sealed holdout |
| Checks | Futures-only on every row. The open-interest and category identities hold on all 4,821 FX rows. No missing or negative values, no duplicates |
| Timing rule | Usable from 17:00 New York on the first weekday ≥ as-of + 6 days. The 2013 shutdown reports (as-of 2013-10-01 → 12-24) are UNAVAILABLE |
| Result | Data sufficient for one small preregistered study on the 7 direct USD pairs. Crosses are derived only. No test has been run. See [COT_DATA_AUDIT.md](COT_DATA_AUDIT.md) |

## COT-1: CFTC positioning as directional information

| Field | Value |
|---|---|
| Hypotheses | 11, frozen in `research/specs/COT-1.json` and [the preregistration](../research/preregistrations/COT-1.md) (commit `a3201c9`) before any outcome: Leveraged Money extremes against / with (P), with a price extreme (C), without one (I), 4-week flow (F), unwind (U), VIX ≥ 20 (V), crowded-trend veto (X); 7 price-only controls on the same decision bars |
| Data | CFTC TFF Futures-Only (the user's files), used from 17:00 New York on the first weekday ≥ as-of + 6; 2013 shutdown reports dropped; 7 direct USD pairs, USD-quote pairs inverted |
| Periods | Development 2008-07-11 → 2014; validation 2014 → 2016; judged 2008-07-11 → 2016. The 2016 confirmation and the sealed 2017 holdout were computed only for what earned them: nothing did |
| Tests / threshold | 11; t ≥ 3.4136 |
| Costs | Standard D1; D3 exit (one week, 2 × ATR stop). Cost about 0.047R per trade |
| Result | **FAILED.** All 11 REJECTED, 0 PROMISING. The best, C-CONT, is +0.017R (t 0.37), carried by EURUSD and 2008. COT over price adds +0.007R. Crowded trend trades equal uncrowded ones. Selection walk-forward: −0.055R |
| Conclusion | Positioning restates price at a one-week horizon; it adds no tradable information as a signal, confirmation, filter or veto. See [COT1_RESULTS.md](COT1_RESULTS.md) |

## H.10 data audit (no hypothesis)

| Field | Value |
|---|---|
| Data | Federal Reserve H.10 noon rates via FRED via the datahub mirror (`github.com/datasets/exchange-rates`). Pinned vintages 2017-12-08, **2018-10-17 (primary, full precision)** and 2026-09-29. The official endpoints are unreachable here |
| Checks | The official values are recovered exactly (0 of 4,524 off the decimal grid per currency). 0 revisions across three vintages (1999–2016). All 171 no-rate days are explained; the 3 carried copies in 2007 are dropped. Best-matching time is 12:00 New York every year |
| Cross-source | Against Dukascopy 2008–2016: noon level median 0.6–1.7 bp; daily return correlation 0.996–0.998; weekly ≥ 0.9977. AUD triangulation shows the **repository's Dukascopy AUDUSD** is faulty in 2008-01..09 and 2009-04..09 |
| Verdict | **SUFFICIENT FOR RV-1**, on conditions (point in time: next business day 17:00 New York; JPY has no policy rate for 2,577 of 4,695 weekdays). See [H10_DATA_AUDIT.md](H10_DATA_AUDIT.md). No RV-1 test run |
