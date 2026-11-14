# Discovery lab: the autonomous research report

**RESEARCH ONLY · NOT TRADING · NOTHING HERE IS A PROFIT CLAIM.** Written by the lab's own worker on GitHub's runner, with no person and no open conversation in the loop. A rule is validated only by a preregistered test on rows no scan has read, at the registry's bar; everything short of that is a candidate.

**بالعربي:** هذا تقرير المختبر الذاتي: بحث فقط، ما بيه تداول ولا وعد بربح. لحد هسه المختبر سوّى 3 فحص اكتشاف وصنّف 660 قاعدة، وكلها محفوظة ويا سبب تصنيفها. القواعد اللي وصلت اختبار التحقق المستقل: 0، ونجح منها 0. بالطابور هسه 0 مهمة. سجل البحث سليم.

Updated 2026-11-14 01:25 UTC · lab-cycle-1.1.0 · dlab-1.2.0 · cycles so far: 8

## This cycle

No task ran: nothing was due, or nothing could run yet (see the queue).

**Why nothing is queued.** The lab does not invent work. As things stand:

- `crypto-daily`: scanned once under dlab-1.1.0; of its 39 ranking-and-holding-period cells, 27 have a classed rule, 12 are set aside as closed families, and 0 are holes
- `etf-daily`: scanned once under dlab-1.1.0; of its 27 ranking-and-holding-period cells, 25 have a classed rule, 2 are set aside as closed families, and 0 are holes
- no submission is waiting in `research/director/inbox`
- the next experiment starts with a submission (the research director's, or the idea engine's), a new panel or method (a new version of the lab), or a new month of data

## The queue

| Task | State | Attempts | Priority | Waiting for |
|---|---|---|---|---|
| (empty) | | | | |

Done so far: 7 tasks. A task is known by its id and never runs twice. A failed task is retried by later cycles, three times at most; a new version of the worker gives a failed task its attempts back, once.

## Discovery scans

| Scan | Market | Instruments | Rules kept | Statistics looked at | Promising | Verdict |
|---|---|---|---|---|---|---|
| `DLAB-CRD-1` | crypto-perp-daily | 55 | 266 | 29218 | 0 | FAILED |
| `DLAB-ENG-1` | energy-futures-eia | 2 | 102 | 2015 | 0 | FAILED |
| `DLAB-ETF-1` | us-etf-broad-daily | 31 | 266 | 15349 | 0 | FAILED |

## Directed tests: hypotheses submitted as rules

| Test | Asked by | Hypothesis | Rules tested | Refused before the test | Promising | Verdict |
|---|---|---|---|---|---|---|
| `DLAB-CRD-D1` | lab (none (deterministic code)) | The cross-sectional rankings of crypto-daily no scan has looked at out of sample | 14 | 12 | 0 | FAILED |
| `DLAB-ETF-D1` | lab (none (deterministic code)) | The cross-sectional rankings of etf-daily no scan has looked at out of sample | 12 | 2 | 0 | FAILED |

A scan's or a test's verdict says only whether it proposed rules for validation. It validates and disproves nothing.

## Every candidate, by class (cumulative)

| Class | Rules |
|---|---|
| SCIENTIFICALLY_INVALID | 0 |
| REPEATS_CLOSED_FAMILY | 18 |
| INSUFFICIENT_DATA | 58 |
| NEGATIVE_EXPECTANCY | 235 |
| OVERFIT | 159 |
| DUPLICATE | 42 |
| INSUFFICIENT_POWER | 148 |
| PROMISING_UNCONFIRMED | 0 |

| Family | Rules | Positive out of sample | Promising |
|---|---|---|---|
| anomaly | 56 | 8 | 0 |
| combination | 97 | 18 | 0 |
| cross-asset lead-lag | 58 | 17 | 0 |
| cross-sectional | 74 | 7 | 0 |
| evolved rule | 72 | 19 | 0 |
| information (non-linear) | 107 | 31 | 0 |
| ordinal pattern | 53 | 9 | 0 |
| own-lag | 24 | 5 | 0 |
| pooled book | 18 | 1 | 0 |
| pooled time-series | 48 | 16 | 0 |
| regime | 53 | 17 | 0 |

### The strongest candidates not yet judged

| Scan | Rule | Family | Check-row t | Class | Its plan |
|---|---|---|---|---|---|
| DLAB-CRD-1 | ONTUSDT: rev for 5 rows after a multivariate shock of mkt(1), disp(1), ret(ONTUSDT,1) beyond 11.9 | anomaly | 2.756 | INSUFFICIENT_POWER | its family's book across instruments (d0c5c831fcc740e5) is INSUFFICIENT_POWER too; it cannot be told from noise yet: about 0.4 more years of discovery rows at this strength would tell; if real, about 1.9 more years after the validation window reach half power |
| DLAB-CRD-1 | XMRUSDT: against the sign of z250[ret(XMRUSDT,1)] beyond 0.5 | own-lag | 2.148 | INSUFFICIENT_POWER | its family's book across instruments (2d1190355297b547) is DUPLICATE too; it cannot be told from noise yet: about 1.9 more years of discovery rows at this strength would tell; if real, the same mechanism on about 3 independent instruments reaches half power in |
| DLAB-CRD-1 | BNBUSDT: by 2 regimes of 1 state features, map [1.0, 0.0] | regime | 2.025 | INSUFFICIENT_POWER | its family's book across instruments (4b30cfc0360f5001) is OVERFIT too; it cannot be told from noise yet: about 2.4 more years of discovery rows at this strength would tell; if real, the same mechanism on about 4 independent instruments reaches half power in t |
| DLAB-CRD-1 | XMRUSDT: rev for 5 rows after a multivariate shock of mkt(1), disp(1), ret(XMRUSDT,1) beyond 13.2 | anomaly | 1.889 | INSUFFICIENT_POWER | its family's book across instruments (d0c5c831fcc740e5) is INSUFFICIENT_POWER too; it cannot be told from noise yet: about 3.0 more years of discovery rows at this strength would tell; if real, the same mechanism on about 4 independent instruments reaches half |
| DLAB-CRD-1 | BCHUSDT: by the rank bins of ret(BCHUSDT,1) x aux(BCHUSDT.fund7), map [0.0, 1.0, 1.0, 0.0, -1.0, -1.0, 0.0, 0.0, 0.0] | information (non-linear) | 1.822 | INSUFFICIENT_POWER | its family's book across instruments (050c3cd2ab036db9) is NEGATIVE_EXPECTANCY too; it cannot be told from noise yet: about 3.4 more years of discovery rows at this strength would tell; if real, the same mechanism on about 5 independent instruments reaches hal |
| DLAB-ETF-1 | book of 31: long SPY for 5 rows while rank250[disp(20)] < 0.2; long QQQ for 5 rows while rank250[disp(20)] < 0.2; long IWM for 5 rows while rank250[di | pooled time-series | 1.701 | INSUFFICIENT_POWER | it cannot be told from noise yet: about 10.5 more years of discovery rows at this strength would tell; if real, the same mechanism on about 5 independent instruments reaches half power in the window |
| DLAB-CRD-1 | IOTAUSDT: and of IOTAUSDT: by the ordering of IOTAUSDT's last 3 1-row returns, map [0.0, 0.0, -1.0, 0.0, 1.0, 1.0] | IOTAUSDT: with the sign of z250[r | combination | 1.652 | INSUFFICIENT_POWER | it cannot be told from noise yet: about 4.6 more years of discovery rows at this strength would tell; if real, the same mechanism on about 6 independent instruments reaches half power in the window |
| DLAB-CRD-1 | AVAXUSDT: with the sign of z250[ret(EGLDUSDT,5)] beyond 0.5 | cross-asset lead-lag | 1.617 | INSUFFICIENT_POWER | its family's book across instruments (745a635c7d141dee) is OVERFIT too; it cannot be told from noise yet: about 4.9 more years of discovery rows at this strength would tell; if real, the same mechanism on about 6 independent instruments reaches half power in t |
| DLAB-CRD-1 | BCHUSDT: by the rank bins of ret(BCHUSDT,1) x volr(BCHUSDT,5,60), map [-1.0, 1.0, 1.0, -1.0, -1.0, -1.0, 0.0, 1.0, -1.0] | information (non-linear) | 1.613 | INSUFFICIENT_POWER | its family's book across instruments (050c3cd2ab036db9) is NEGATIVE_EXPECTANCY too; it cannot be told from noise yet: about 4.9 more years of discovery rows at this strength would tell; if real, the same mechanism on about 6 independent instruments reaches hal |
| DLAB-ETF-1 | EWY: and of EWY: by the rank bins of rel(EWY,20) x disp(20), map [1.0, -1.0, 1.0, 0.0, 1.0, -1.0, 0.0, 0.0, 0.0] | EWY: against the sign of z250[ret(X | combination | 1.597 | INSUFFICIENT_POWER | it cannot be told from noise yet: about 12.6 more years of discovery rows at this strength would tell; if real, the same mechanism on about 6 independent instruments reaches half power in the window |

## Independent validation

No rule has reached a registered validation yet.

## Validated rules, marked forward on paper

None: no rule has passed its validation. Nothing is traded, on paper or otherwise, from this lab.

## What the record has taught so far

- crypto-perp-daily: 280 rules from data-driven discovery; 0 promising; 72 positive out of sample but not told from noise; 83 lost out of sample (52 of them only after costs); 60 overfit; 0 passed validation and 0 failed it
- crypto-perp-daily: combination rules overfit most often (14 of 36)
- crypto-perp-daily: 6 combination rules were positive before costs and negative after: this market's costs, not its information, stopped them
- crypto-perp-daily: 5 cross-asset lead-lag rules were positive before costs and negative after: this market's costs, not its information, stopped them
- crypto-perp-daily: 12 cross-sectional rules were positive before costs and negative after: this market's costs, not its information, stopped them
- crypto-perp-daily: 11 information (non-linear) rules were positive before costs and negative after: this market's costs, not its information, stopped them
- crypto-perp-daily: 6 ordinal pattern rules were positive before costs and negative after: this market's costs, not its information, stopped them
- crypto-perp-daily: 4 own-lag rules were positive before costs and negative after: this market's costs, not its information, stopped them
- crypto-perp-daily: 3 pooled time-series rules were positive before costs and negative after: this market's costs, not its information, stopped them
- crypto-perp-daily: the information audit found 44 of 982 feature-instrument pairs with z >= 2 about the next return (12 of them with no linear trace); chance alone gives about 22.6
- energy-futures-eia: 102 rules from data-driven discovery; 0 promising; 25 positive out of sample but not told from noise; 43 lost out of sample (10 of them only after costs); 21 overfit; 0 passed validation and 0 failed it
- energy-futures-eia: 3 evolved rule rules were positive before costs and negative after: this market's costs, not its information, stopped them
- energy-futures-eia: the information audit found 3 of 46 feature-instrument pairs with z >= 2 about the next return (1 of them with no linear trace); chance alone gives about 1.1
- us-etf-broad-daily: 278 rules from data-driven discovery; 0 promising; 51 positive out of sample but not told from noise; 109 lost out of sample (56 of them only after costs); 78 overfit; 0 passed validation and 0 failed it
- us-etf-broad-daily: own-lag rules overfit most often (7 of 8)
- us-etf-broad-daily: 9 combination rules were positive before costs and negative after: this market's costs, not its information, stopped them
- us-etf-broad-daily: 4 cross-asset lead-lag rules were positive before costs and negative after: this market's costs, not its information, stopped them
- us-etf-broad-daily: 15 cross-sectional rules were positive before costs and negative after: this market's costs, not its information, stopped them
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

- `crypto_daily`: 55 instruments, to 2026-10-31; 95 missing days in all; 62 one-day moves beyond 50% (flagged, never removed); retrieved 2026-11-12T23:38 UTC; 44 priced and funded on the last day, 10 delisted before it (their later prices make no return)
- `etf_daily`: 32 instruments, to 2026-11-11; 6461 missing days in all; 8 one-day moves beyond 50% (flagged, never removed); retrieved 2026-11-12T15:47 UTC

## Alerts

None.

## Budget

| Cycle | Seconds | Tasks run | Failed |
|---|---|---|---|
| 2026-11-12T23:51 | 0.2 | 0 | 0 |
| 2026-11-13T01:48 | 0.3 | 0 | 0 |
| 2026-11-13T11:31 | 0.2 | 0 | 0 |
| 2026-11-13T17:41 | 0.2 | 0 | 0 |
| 2026-11-13T21:36 | 5.6 | 2 | 0 |
| 2026-11-14T01:25 | 0.9 | 0 | 0 |

No model call and no paid service is used by a cycle. Its data come from public archives.
