# Research pipeline report

**RESEARCH ONLY · NO MONEY · NOT A TRADING RESULT.** Every figure here is a test of an idea on history (a backtest), judged once against rules fixed before it ran, or a sealed out-of-sample check. Paper-trading results are in the trend desk's TRADING_REPORT.md (`trend-desk-data` branch) and are never added here.

**بالعربي:** هذا تقرير البحث وحده: اختبارات أفكار على بيانات تاريخية، مو أرباح تداول، وما بيه ولا رقم من الحساب الورقي. اليوم: 0 فرضية جديدة انسجلت، 0 انحكمت (0 نجحت)، و5 فحص قبل البناء رفض 5 فكرة من غير ما نصرف عليها اختبار. المجموع من البداية: 97 فرضية مسجلة، 74 فشلت. المعتمد (VALIDATED): TRND-1.

Generated 2026-11-25 13:49 UTC from the committed record · research-report-1.1.0

## Today (2026-11-25, UTC)

**New hypotheses registered** (each preregistered before any data was read):

- none

**Verdicts recorded** (each judged once):

- none

**Ideas checked and dropped before building** (no test spent; the reasons are in `research/QUEUE.md`):

- Checked on 2026-11-25, 01:49 UTC (the edge hunt), and dropped before building: BRV-1: bitcoin's rebound after a burst of aggressive selling on spot.
- Checked on 2026-11-25, 04:49 UTC (the edge hunt), and dropped before building: ORW-1: a weekend risk premium in crude oil, Friday's close to Monday's, on Brent.
- Checked on 2026-11-25, 07:49 UTC (the edge hunt), and dropped before building: PAXG-1: tokenized gold while the gold market is shut.
- Checked on 2026-11-25, 10:49 UTC (the edge hunt), and dropped before building: TMB-1: bitcoin after large Tether mints.
- Checked on 2026-11-25, 13:49 UTC (the edge hunt), and dropped before building: DVS-1: bitcoin after spikes of its implied volatility (DVOL).

## Cumulative (since the registry began)

| | |
|---|---|
| Hypotheses registered | 97 |
| Verdicts | 87: ABANDONED 2, FAILED 74, INCONCLUSIVE 1, PASSED 10 |
| Ideas dropped before building (no test spent) | 127 in the tables of 53 dated checks, on 12 days |
| Status of every judged hypothesis (the edge classification) | PROMISING 4, REJECTED 153, UNCERTAIN 5, VALIDATED 1 |
| Evidence files that still match their verdict | 67 of 67 checked |
| Specs whose hash is missing from their preregistration | none |

## Validation status

Every judged hypothesis not rejected, as the edge classification states it. Only VALIDATED may be promoted, and only by a person; PROMISING did not reach its bar and is not traded.

| Edge | Status | t (bar) | Out-of-sample | The classification's note | Source |
|---|---|---|---|---|---|
| BAS-1@0.0005 | **UNCERTAIN** | -0.633 (3.0) | — | event study (spot_event_study, stage dev): expectancies are the per-entry `mean_excess` averaged over its cohorts, a fraction of notional, not R | `research/knowledge/BAS-1.json` |
| BAS-1@0.001 | **UNCERTAIN** | -0.215 (3.0) | — | event study (spot_event_study, stage dev): expectancies are the per-entry `mean_excess` averaged over its cohorts, a fraction of notional, not R | `research/knowledge/BAS-1.json` |
| CASC-1@0.15 | **UNCERTAIN** | -0.277 (3.0) | — | event study (spot_event_study, stage dev): expectancies are the per-entry `mean_net` averaged over its cohorts, a fraction of notional, not R | `research/knowledge/CASC-1.json` |
| DAY-1 | **PROMISING** | None (3.388) | — | single-program verdict: its statistic is named in its artifact and preregistration; a near miss: it failed on the bar alone, with t 2.482 on its `days` against 3.388. Not validated: evidence for a fresh preregistered test on new data | `research/knowledge/DAY-1.json` |
| FXT-1 | **PROMISING** | 2.712 (3.629) | — | single-program verdict: expectancies are monthly net returns, not R; a near miss: it failed on the bar alone, with t 2.712 on its `months` against 3.629. Not validated: evidence for a fresh preregistered test on new data | `research/knowledge/FXT-1.json` |
| KRP-1@0.1 | **UNCERTAIN** | -0.919 (3.0) | — | event study (spot_event_study, stage dev): expectancies are the per-entry `mean_net` averaged over its cohorts, a fraction of notional, not R | `research/knowledge/KRP-1.json` |
| RCEQ-E1-TOM | **PROMISING** | 2.24 (3.0) | +0.16% a month | retail CFD: monthly net account returns after spread, slippage, financing and dividends, not R; replication/holdout PROMISING_REPLICATED: 441 months, net t 2.175 | `research/knowledge/RC-EQ.json` |
| SQZ-1@0.001 | **UNCERTAIN** | 0.068 (3.0) | — | event study (spot_event_study, stage dev): expectancies are the per-entry `mean_excess` averaged over its cohorts, a fraction of notional, not R | `research/knowledge/SQZ-1.json` |
| TME-1 | **PROMISING** | None (3.078) | — | single-program verdict: its statistic is named in its artifact and preregistration; a near miss: it failed on the bar alone, with t 2.239 on its `month_ends` against 3.078. Not validated: evidence for a fresh preregistered test on new data | `research/knowledge/TME-1.json` |
| TRND-1 | **VALIDATED** | 3.834 (3.376) | +0.79% a month | single-program verdict: expectancies are monthly net returns, not R; holdout 69 months, net t 2.737 | `research/knowledge/TRND-1.json` |

**Forward tests running, each judged once at its preregistered end** (nothing is concluded before):

- TOM-F (registered 2026-10-04; data to an open end (see its preregistration)): TOM-F: two TOM variants for forward data only
- RADAR-1 (registered 2026-10-07; data to 2027-02-15): RADAR-1: live cross-venue funding radar, paper forward test
- TRND-F (registered 2026-11-06; data to 2029-12-01): TRND-F: TRND-1's rule forward, 2026-12..2029-11

Also registered without a verdict here, and counted in every bar: archive-smc-h1 (archive record); archive-smc-h2 (archive record); archive-trend-3 (archive record); archive-reversion (archive record); archive-smc-utc-rerun (archive record); archive-edge-program-8 (archive record); TOM-D (design only).

## The bar each market's next test must clear

Bonferroni over every test already counted on the rows a new test would read, and never below 3.0. The more those rows have been read, the higher the bar: discovery never lowers it. A test is charged to the rows it read. A discovery scan charges hundreds of tests to its own discovery rows, which can then judge nothing at an ordinary bar; that charge does not touch the rows it never loaded.

| Market data | Judged tests | Discovery charges | Bar over its whole history (t) | Tests on its last five years | Bar there (t) |
|---|---|---|---|---|---|
| crypto-perp-daily | 0 | 614 | 3.941 | 614 | 3.941 |
| us-etf-broad-daily | 0 | 612 | 3.940 | 0 | 3.000 |
| energy-futures-eia | 1 | 400 | 3.837 | 0 | 3.000 |
| fx-majors | 151 | 25 | 3.631 | 16 | 3.000 |
| index-cfd-intraday | 10 | 22 | 3.172 | 6 | 3.000 |
| multi-asset-etf | 12 | 0 | 2.890 | 2 | 3.000 |
| crypto-binance-usdtm | 1 | 10 | 2.865 | 11 | 3.000 |
| multi-asset-long | 10 | 0 | 2.838 | 0 | 3.000 |
| crypto-xvenue-hl-binance | 2 | 6 | 2.773 | 8 | 3.000 |
| crypto-binance-spot | 7 | 0 | 2.734 | 7 | 3.000 |
| us-equity-etf | 6 | 0 | 2.690 | 3 | 3.000 |
| crypto-binance-usdtm-all | 0 | 5 | 2.638 | 5 | 3.000 |
| crypto-perp-funding-settlements | 4 | 0 | 2.576 | 4 | 3.000 |
| crypto-perp-live-xvenue | 3 | 0 | 2.498 | 3 | 3.000 |
| crypto-spot-crowded-shorts | 3 | 0 | 2.498 | 3 | 3.000 |
| crypto-spot-high-funding | 3 | 0 | 2.498 | 3 | 3.000 |
| equity-index-forward | 3 | 0 | 2.498 | 3 | 3.000 |
| equity-index-monthly | 3 | 0 | 2.498 | 2 | 3.000 |
| stablecoin-pairs-weekend | 3 | 0 | 2.498 | 3 | 3.000 |
| crypto-spot-korean-premium | 2 | 0 | 2.394 | 2 | 3.000 |
| crypto-spot-liquidation-falls | 2 | 0 | 2.394 | 2 | 3.000 |
| crypto-spot-spot-led-rallies | 2 | 0 | 2.394 | 2 | 3.000 |
| equity-index-b | 2 | 0 | 2.394 | 2 | 3.000 |
| us-treasury-daily | 2 | 0 | 2.394 | 0 | 3.000 |
| us-vol-etp | 2 | 0 | 2.394 | 2 | 3.000 |
| crypto-perp-new-listings | 1 | 0 | 2.241 | 1 | 3.000 |
| em-fx-daily | 1 | 0 | 2.241 | 0 | 3.000 |
| equity-index-daily | 1 | 0 | 2.241 | 0 | 3.000 |
| metals-futures-daily | 1 | 0 | 2.241 | 0 | 3.000 |

The sealed holdout: fx-majors from 2017-01-01 (sealed 2026-09-26). It is opened once, by a preregistered final test of a candidate that has passed, and never for discovery.

## The last 25 verdicts, with their evidence

| Recorded | Hypothesis | Verdict | Preregistration | Spec hash quoted | Evidence file | Matches |
|---|---|---|---|---|---|---|
| 2026-11-22 | KRP-1 | FAILED | `research/preregistrations/KRP-1.md` | yes | `research/knowledge/KRP-1.json` | yes |
| 2026-11-22 | SCX-1-V | FAILED | `research/preregistrations/SCX-1.md` | yes | `research/knowledge/SCX-1-V.json` | yes |
| 2026-11-22 | SCX-1 | PASSED | `research/preregistrations/SCX-1.md` | yes | `research/knowledge/SCX-1.json` | yes |
| 2026-11-16 | SPL-1 | FAILED | `research/preregistrations/SPL-1.md` | yes | `research/knowledge/SPL-1.json` | yes |
| 2026-11-15 | BAS-1 | FAILED | `research/preregistrations/BAS-1.md` | yes | `research/knowledge/BAS-1.json` | yes |
| 2026-11-15 | CASC-1 | FAILED | `research/preregistrations/CASC-1.md` | yes | `research/knowledge/CASC-1.json` | yes |
| 2026-11-15 | SQZ-1 | FAILED | `research/preregistrations/SQZ-1.md` | yes | `research/knowledge/SQZ-1.json` | yes |
| 2026-11-15 | EXF-1 | FAILED | `research/preregistrations/EXF-1.md` | yes | `research/knowledge/EXF-1.json` | yes |
| 2026-11-15 | NEWL-1 | FAILED | `research/preregistrations/NEWL-1.md` | yes | `research/knowledge/NEWL-1.json` | yes |
| 2026-11-14 | RADX-1 | FAILED | `research/preregistrations/RADX-1.md` | — | `research/knowledge/RADX-1.json` | — |
| 2026-11-13 | DLAB-CRD-D1 | FAILED | `research/preregistrations/DLAB-CRD-D1.md` | yes | `research/knowledge/DLAB-CRD-D1.json` | yes |
| 2026-11-13 | DLAB-ETF-D1 | FAILED | `research/preregistrations/DLAB-ETF-D1.md` | yes | `research/knowledge/DLAB-ETF-D1.json` | yes |
| 2026-11-12 | DLAB-CRD-1 | FAILED | `research/preregistrations/DLAB-CRD-1.md` | yes | `research/knowledge/DLAB-CRD-1.json` | yes |
| 2026-11-12 | DLAB-ETF-1 | FAILED | `research/preregistrations/DLAB-ETF-1.md` | yes | `research/knowledge/DLAB-ETF-1.json` | yes |
| 2026-11-10 | DLAB-ENG-1 | FAILED | `research/preregistrations/DLAB-ENG-1.md` | yes | `research/knowledge/DLAB-ENG-1.json` | yes |
| 2026-11-10 | LIQ-1 | FAILED | `research/preregistrations/LIQ-1.md` | yes | `research/knowledge/LIQ-1.json` | yes |
| 2026-11-09 | ENG-1 | FAILED | `research/preregistrations/ENG-1.md` | yes | `research/knowledge/ENG-1.json` | yes |
| 2026-11-09 | FXT-1 | FAILED | `research/preregistrations/FXT-1.md` | yes | `research/knowledge/FXT-1.json` | yes |
| 2026-11-09 | FXS-1 | FAILED | `research/preregistrations/FXS-1.md` | yes | `research/knowledge/FXS-1.json` | yes |
| 2026-11-08 | DAY-1 | FAILED | `research/preregistrations/DAY-1.md` | yes | `research/knowledge/DAY-1.json` | yes |
| 2026-11-06 | TRND-1-H | PASSED | `research/preregistrations/TRND-1.md` | yes | `research/knowledge/TRND-1-H.json` | yes |
| 2026-11-06 | TRND-1 | PASSED | `research/preregistrations/TRND-1.md` | yes | `research/knowledge/TRND-1.json` | yes |
| 2026-11-05 | RBL-1 | FAILED | `research/preregistrations/RBL-1.md` | yes | `research/knowledge/RBL-1.json` | yes |
| 2026-11-05 | TME-1 | FAILED | `research/preregistrations/TME-1.md` | yes | `research/knowledge/TME-1.json` | yes |
| 2026-11-05 | TSY-1 | FAILED | `research/preregistrations/TSY-1.md` | yes | `research/knowledge/TSY-1.json` | yes |

**Matches**: the evidence file's own hash equals the one recorded with its verdict; where none was recorded, the file names the spec (and code) hashes registered before the test. Every verdict is in `research/registry.jsonl`. Each program's command and frozen spec are in its preregistration, and the program refuses to judge if its spec or code no longer match the hashes recorded at registration.
