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
| Result | *Running.* Recorded here when it finishes |

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
