# Discovery lab: the autonomous research report

**RESEARCH ONLY · NOT TRADING · NOTHING HERE IS A PROFIT CLAIM.** Written by the lab's own worker on GitHub's runner, with no person and no open conversation in the loop. A rule is validated only by a preregistered test on rows no scan has read, at the registry's bar; everything short of that is a candidate.

**بالعربي:** هذا تقرير المختبر الذاتي: بحث فقط، ما بيه تداول ولا وعد بربح. لحد هسه المختبر سوّى 2 فحص اكتشاف وصنّف 368 قاعدة، وكلها محفوظة ويا سبب تصنيفها. القواعد اللي وصلت اختبار التحقق المستقل: 0، ونجح منها 0. بالطابور هسه 2 مهمة. سجل البحث سليم.

Updated 2026-11-12 15:47 UTC · lab-cycle-1.0.0 · dlab-1.1.0 · cycles so far: 2

## This cycle

| Task | Result |
|---|---|
| `data:crypto_daily:2026-10` | **FAILED** · RuntimeError: crypto_daily: 8 instruments are priced to the end of 2026-09 and have no whole 2026-10 (the first: BALUSDT, BLZUSDT, FTMUSDT, ICXUSDT, MKRUSDT): the month looks half-published. What arrived is kept. The data are not complete: nothing is scanned, judged or marked on them |
| `data:etf_daily:2026-11` | **DONE** · {"feed": "etf_daily", "instruments": 31, "usable_in_the_fit_rows": {"etf-daily": 31}, "last_day": "2026-11-11", "missing_days": 6461, "moves_beyond_50pct": 8, "not_served": [], "fetched_now": null} |
| `scan:etf-daily:dlab-1.1.0:7` | **DONE** · {"run": "DLAB-ETF-1", "verdict": "FAILED", "universe": "us-etf-broad-daily", "instruments": 31, "rules": 266, "by_class": {"DUPLICATE": 18, "INSUFFICIENT_DATA": 19, "INSUFFICIENT_POWER": 49, "NEGATIVE_EXPECTANCY": 102, "OVERFIT": 78}, "batch": 0, "scanned": 15349} |
| `sources:2026-W46` | **DONE** · {"new": 85, "query": "intraday periodicity volume volatility return predictability", "by_origin": {"arxiv": 60, "openalex": 25}} |

## The queue

| Task | State | Attempts | Priority | Waiting for |
|---|---|---|---|---|
| `data:crypto_daily:2026-10` | FAILED | 1 | 4.0 |  |
| `scan:crypto-daily:dlab-1.1.0:7` | QUEUED | 0 | 2.0 | its data (crypto_daily) are not completely on file yet |

Done so far: 3 tasks. A task is known by its id and never runs twice. A failed task is retried by later cycles, three times at most.

## Discovery scans

| Scan | Market | Instruments | Rules kept | Statistics looked at | Promising | Verdict |
|---|---|---|---|---|---|---|
| `DLAB-ENG-1` | energy-futures-eia | 2 | 102 | 2015 | 0 | FAILED |
| `DLAB-ETF-1` | us-etf-broad-daily | 31 | 266 | 15349 | 0 | FAILED |

A scan's verdict says only whether it proposed rules for validation. It validates and disproves nothing.

## Every candidate, by class (cumulative)

| Class | Rules |
|---|---|
| SCIENTIFICALLY_INVALID | 0 |
| REPEATS_CLOSED_FAMILY | 0 |
| INSUFFICIENT_DATA | 30 |
| NEGATIVE_EXPECTANCY | 145 |
| OVERFIT | 99 |
| DUPLICATE | 20 |
| INSUFFICIENT_POWER | 74 |
| PROMISING_UNCONFIRMED | 0 |

| Family | Rules | Positive out of sample | Promising |
|---|---|---|---|
| anomaly | 32 | 5 | 0 |
| combination | 61 | 5 | 0 |
| cross-asset lead-lag | 34 | 9 | 0 |
| cross-sectional | 24 | 2 | 0 |
| evolved rule | 48 | 11 | 0 |
| information (non-linear) | 59 | 17 | 0 |
| ordinal pattern | 29 | 3 | 0 |
| own-lag | 16 | 2 | 0 |
| pooled book | 12 | 0 | 0 |
| pooled time-series | 24 | 10 | 0 |
| regime | 29 | 10 | 0 |

### The strongest candidates not yet judged

| Scan | Rule | Family | Check-row t | Class | Its plan |
|---|---|---|---|---|---|
| DLAB-ETF-1 | book of 31: long SPY for 5 rows while rank250[disp(20)] < 0.2; long QQQ for 5 rows while rank250[disp(20)] < 0.2; long IWM for 5 rows while rank250[di | pooled time-series | 1.701 | INSUFFICIENT_POWER | it cannot be told from noise yet: about 10.5 more years of discovery rows at this strength would tell; if real, the same mechanism on about 5 independent instruments reaches half power in the window |
| DLAB-ETF-1 | EWY: and of EWY: by the rank bins of rel(EWY,20) x disp(20), map [1.0, -1.0, 1.0, 0.0, 1.0, -1.0, 0.0, 0.0, 0.0] | EWY: against the sign of z250[ret(X | combination | 1.597 | INSUFFICIENT_POWER | it cannot be told from noise yet: about 12.6 more years of discovery rows at this strength would tell; if real, the same mechanism on about 6 independent instruments reaches half power in the window |
| DLAB-ETF-1 | book of 31: long SPY for 5 rows while rank250[aux(VIX,5)] > 0.8; long QQQ for 5 rows while rank250[aux(VIX,5)] > 0.8; long IWM for 5 rows while rank25 | pooled time-series | 1.487 | INSUFFICIENT_POWER | it cannot be told from noise yet: about 15.3 more years of discovery rows at this strength would tell; if real, the same mechanism on about 6 independent instruments reaches half power in the window |
| DLAB-ENG-1 | NATGAS: by the rank bins of absret(NATGAS), map [0.0, 0.0, 0.0, 0.0, -1.0] | information (non-linear) | 1.431 | INSUFFICIENT_POWER | its family's book across instruments (cf30b58b44983653) is OVERFIT too; it cannot be told from noise yet: about 26.3 more years of discovery rows at this strength would tell; if real, the same mechanism on about 5 independent instruments reaches half power in  |
| DLAB-ETF-1 | across 31 instruments: short the top 34% and long the bottom 34% by ret(2), equal weights, no net exposure; each row's book is held 20 rows | cross-sectional | 1.365 | INSUFFICIENT_POWER | it cannot be told from noise yet: about 19.1 more years of discovery rows at this strength would tell; if real, the same mechanism on about 8 independent instruments reaches half power in the window |
| DLAB-ETF-1 | book of 31: long SPY for 1 rows while rank250[rel(SPY,20)] < 0.1; long QQQ for 1 rows while rank250[rel(QQQ,20)] < 0.1; long IWM for 1 rows while rank | pooled time-series | 1.353 | INSUFFICIENT_POWER | it cannot be told from noise yet: about 19.5 more years of discovery rows at this strength would tell; if real, the same mechanism on about 8 independent instruments reaches half power in the window |
| DLAB-ETF-1 | EWG: by the rank bins of mkt(5) x rel(EWG,20), map [0.0, 0.0, 0.0, 1.0, 0.0, 1.0, 1.0, -1.0, 0.0] | information (non-linear) | 1.282 | INSUFFICIENT_POWER | its family's book across instruments (8dca81d95cb63a0d) is NEGATIVE_EXPECTANCY too; it cannot be told from noise yet: about 22.3 more years of discovery rows at this strength would tell; if real, the same mechanism on about 8 independent instruments reaches ha |
| DLAB-ETF-1 | FXI: by 3 regimes of 1 state features, map [0.0, 0.0, 1.0] | regime | 1.269 | INSUFFICIENT_POWER | its family's book across instruments (22c335210501683b) is DUPLICATE too; it cannot be told from noise yet: about 22.9 more years of discovery rows at this strength would tell; if real, the same mechanism on about 9 independent instruments reaches half power i |
| DLAB-ETF-1 | USO: by 3 regimes of 1 state features, map [-1.0, 0.0, 1.0] | regime | 1.251 | INSUFFICIENT_POWER | its family's book across instruments (22c335210501683b) is DUPLICATE too; it cannot be told from noise yet: about 23.7 more years of discovery rows at this strength would tell; if real, the same mechanism on about 9 independent instruments reaches half power i |
| DLAB-ETF-1 | EEM: by the rank bins of mkt(5), map [1.0, 0.0, 0.0, 0.0, -1.0] | information (non-linear) | 1.228 | INSUFFICIENT_POWER | its family's book across instruments (8dca81d95cb63a0d) is NEGATIVE_EXPECTANCY too; it cannot be told from noise yet: about 24.8 more years of discovery rows at this strength would tell; if real, the same mechanism on about 9 independent instruments reaches ha |

## Independent validation

No rule has reached a registered validation yet.

## Validated rules, marked forward on paper

None: no rule has passed its validation. Nothing is traded, on paper or otherwise, from this lab.

## What the record has taught so far

- energy-futures-eia: 102 rules from data-driven discovery; 0 promising; 25 positive out of sample but not told from noise; 43 lost out of sample (10 of them only after costs); 21 overfit; 0 passed validation and 0 failed it
- energy-futures-eia: 3 evolved rule rules were positive before costs and negative after: this market's costs, not its information, stopped them
- energy-futures-eia: the information audit found 3 of 46 feature-instrument pairs with z >= 2 about the next return (1 of them with no linear trace); chance alone gives about 1.1
- us-etf-broad-daily: 266 rules from data-driven discovery; 0 promising; 49 positive out of sample but not told from noise; 102 lost out of sample (55 of them only after costs); 78 overfit; 0 passed validation and 0 failed it
- us-etf-broad-daily: own-lag rules overfit most often (7 of 8)
- us-etf-broad-daily: 9 combination rules were positive before costs and negative after: this market's costs, not its information, stopped them
- us-etf-broad-daily: 4 cross-asset lead-lag rules were positive before costs and negative after: this market's costs, not its information, stopped them
- us-etf-broad-daily: 14 cross-sectional rules were positive before costs and negative after: this market's costs, not its information, stopped them
- us-etf-broad-daily: 4 evolved rule rules were positive before costs and negative after: this market's costs, not its information, stopped them
- us-etf-broad-daily: 8 information (non-linear) rules were positive before costs and negative after: this market's costs, not its information, stopped them
- us-etf-broad-daily: 7 ordinal pattern rules were positive before costs and negative after: this market's costs, not its information, stopped them
- us-etf-broad-daily: 6 pooled time-series rules were positive before costs and negative after: this market's costs, not its information, stopped them
- us-etf-broad-daily: the information audit found 30 of 434 feature-instrument pairs with z >= 2 about the next return (9 of them with no linear trace); chance alone gives about 10.0

## The research-source database

85 sources on file. Each has its link, its date and a status. A source's status is UNREAD until its claim is checked: nothing is claimed about a paper from its abstract.

| Published | Source | Title |
|---|---|---|
| 2026-11-10 | [arxiv](http://arxiv.org/abs/2611.14325v1) | Point-in-Time Encoders for Earnings Calls |
| 2026-11-10 | [arxiv](http://arxiv.org/abs/2611.14245v1) | Deep Learning for Operator Maps in Optimal Liquidation |
| 2026-11-10 | [arxiv](http://arxiv.org/abs/2611.14117v1) | Fine-Tuning an Order-Flow Foundation Model for Sub-Second Forecasting |
| 2026-11-10 | [arxiv](http://arxiv.org/abs/2611.13962v1) | Deceleration without identification: testing a power-law trend in Bitcoin prices under persistent noise |
| 2026-11-10 | [arxiv](http://arxiv.org/abs/2611.13616v1) | Optimal Trading Speed on Blockchain |
| 2026-11-10 | [arxiv](http://arxiv.org/abs/2611.13550v1) | Tabular Foundation Models in Financial Predictions |
| 2026-11-09 | [arxiv](http://arxiv.org/abs/2611.13365v1) | Making sense of rule 605 |
| 2026-11-09 | [arxiv](http://arxiv.org/abs/2611.12389v1) | Diversification Across Predictors: Heterogeneous Ensemble Learning for Cross-Sectional Return Prediction |
| 2026-11-08 | [arxiv](http://arxiv.org/abs/2611.11652v1) | Adjoint Kernel Sensitivity of the Rough Heston Characteristic Exponent |
| 2026-11-08 | [arxiv](http://arxiv.org/abs/2611.11436v1) | Retrospective Analysis of Team-Following Trading Profitability in Pumpfun Meme Coins Using Funding Networks |

## Data on file

- `crypto_daily`: 55 instruments, to 2026-10-31; 95 missing days in all; 62 one-day moves beyond 50% (flagged, never removed); retrieved 2026-11-12T15:47 UTC · **NOT COMPLETE: 8 instruments are priced to the end of 2026-09 and have no whole 2026-10 (the first: BALUSDT, BLZUSDT, FTMUSDT, ICXUSDT, MKRUSDT): the month looks half-published. What arrived is kept**
- `etf_daily`: 32 instruments, to 2026-11-11; 6461 missing days in all; 8 one-day moves beyond 50% (flagged, never removed); retrieved 2026-11-12T15:47 UTC

## Alerts

None.

## Budget

| Cycle | Seconds | Tasks run | Failed |
|---|---|---|---|
| 2026-11-12T15:47 | 639.6 | 4 | 1 |

No model call and no paid service is used by a cycle. Its data come from public archives.
