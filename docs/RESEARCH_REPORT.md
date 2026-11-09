# Research pipeline report

**RESEARCH ONLY · NO MONEY · NOT A TRADING RESULT.** Every figure here is a test of an idea on history (a backtest), judged once against rules fixed before it ran, or a sealed out-of-sample check. Paper-trading results are in the trend desk's TRADING_REPORT.md (`trend-desk-data` branch) and are never added here.

**بالعربي:** هذا تقرير البحث وحده: اختبارات أفكار على بيانات تاريخية، مو أرباح تداول، وما بيه ولا رقم من الحساب الورقي. اليوم: 3 فرضية جديدة انسجلت، 2 انحكمت (0 نجحت)، و10 فحص قبل البناء رفض 27 فكرة من غير ما نصرف عليها اختبار. المجموع من البداية: 81 فرضية مسجلة، 58 فشلت. المعتمد (VALIDATED): TRND-1.

Generated 2026-11-09 17:53 UTC from the committed record · research-report-1.0.0

## Today (2026-11-09, UTC)

**New hypotheses registered** (each preregistered before any data was read):

- **FXS-1**: FXS-1: the time-of-day effect (home currencies weaken in their own working hours). Do EURUSD, GBPUSD, USDCHF and USDJPY move as the time-of-day hypothesis says inside its windows, net of measured bid/ask, commission and slippage? (`research/preregistrations/FXS-1.md`, 1 test counted)
- **FXT-1**: FXT-1: time-series momentum in the major currencies, 1975-1989. Did each major currency's own 12-month trend, traded monthly at equal risk against the dollar, earn a positive net return over 1975-1989? (`research/preregistrations/FXT-1.md`, 1 test counted)
- **ENG-1**: ENG-1: the energy futures term-structure premium, swap-free. Does holding WTI, heating oil, RBOB and natural gas futures only while contract 2 is above contract 3 earn a positive net return, and more than holding them always? (`research/preregistrations/ENG-1.md`, 1 test counted)

**Verdicts recorded** (each judged once):

- **FXS-1: FAILED** (t -2.466, net_bp_per_trade -0.8994); failed gates: t, development, validation, costs_x1.5, pairs, top_year, bootstrap, profit_factor, delay. Evidence: `research/knowledge/FXS-1.json`; matches its verdict: yes
- **FXT-1: FAILED** (t 2.712, a_year_pct 5.786); failed gates: t. Evidence: `research/knowledge/FXT-1.json`; matches its verdict: yes

**Ideas checked and dropped before building** (no test spent; the reasons are in `research/QUEUE.md`):

- Checked on 2026-11-09, 00:30 UTC, and dropped before building: CRY-1 (row 17).
- Checked on 2026-11-09, 03:30 UTC (a web search for rules that trade every day), and dropped before building: Bitcoin's evening hours: long BTC from 21:00 to 23:00 UTC every day (Quantpedia, hourly Gemini data 2015-10..2022-02: 33% a year gross at 20.9% volatility); An intraday breakout of the "noise area" on GER 40 and UK 100, whose intraday bars are fresh (Zarattini, Aziz & Barbon 2024: a Sharpe ratio of 1.33 net on SPY, 2007-2024, in sample, long and short); Gold's overnight drift: long from the US close to the next open (Blose & Gondhalekar: COMEX overnight returns positive and day returns negative, 1985-2012); Daily technical rules (moving-average and breakout) on the index CFDs.
- Checked on 2026-11-09, 05:50 UTC (a search for newer out-of-sample work), and nothing new to build.
- Checked on 2026-11-09, 06:30 UTC, and dropped before building: Price pressure around the crypto perpetuals' funding times (00:00, 08:00 and 16:00 UTC); The European closing-auction reversal. Auctions are 40-55% of the day's volume on the FTSE, DAX and CAC, and about 14% of a stock's auction return reverses overnight; The end-of-day reversal across US stocks (Soebhag, Baltussen & Da; second at the 2025 Quantpedia Awards): intraday losers rebound in the last 30 minutes.
- Checked on 2026-11-09, 09:30 UTC (a search for 2025-2026 work on index futures, gold and crypto), and dropped: A trend-momentum regime signal in gold futures, walk-forward 2015-2025 ("Forecast-to-Fill", arXiv 2511.08571, 2025); Intraday lead-lag across liquid ETFs from lagged cross-sectional returns (a 2025 *Management Science* paper); Exchange flows of USDT and BTC as intraday signals (arXiv 2411.06327); Spot-BTC ETF flows as a daily signal (since 2024).
- Checked on 2026-11-09, 10:30 UTC, and dropped before building: the options-expiration calendar: Holding the US 500 in the week of monthly options expiration (Stivers & Sun: large caps +0.45% a week in expiration weeks against +0.12% otherwise, 1996-2008; the S&P 500 only from 1983); The week after expiration (a partial reversal), triple-witching weeks, the Santa Claus rally, the first trading days of a year.
- Checked on 2026-11-09, 11:30 UTC (work published from mid-2026), and dropped before building: The noise-area intraday breakout adapted to Nasdaq-100 futures (2026); Calendar seasonality in commodity futures by regression and singular spectrum analysis (arXiv 2609.12227, September 2026); AI-assisted replications of nine published equity anomalies (a July 2026 roundup).
- Checked on 2026-11-09, 12:30 UTC, and dropped before building: Retail-broker client positioning as a contrarian signal (the share of a broker's clients long the US 500 or gold, read against them).
- Checked on 2026-11-09, 13:30 UTC, and dropped before building (power and earlier verdicts, no new data needed): The US 500 inside and outside companies' share-buyback blackout windows (the weeks before earnings, when buybacks stop); Flows from volatility-targeting funds: holding or avoiding the indices after volatility spikes, when such funds cut exposure.
- Checked on 2026-11-09, 17:30 UTC (the discovery program: `docs/DISCOVERY_PROGRAM.md`), and dropped before building: XAS-1: past bond returns as a timing signal for the index CFDs (Pitkäjärvi, Suominen & Vaittinen, JFE 2020); MAX-1: lottery demand in the crypto cross-section; CMEG-1: bitcoin reverting toward the CME Friday settlement after a weekend move; OFI-1: order-flow imbalance in bitcoin, hourly; ATT-1: Wikipedia attention and next-week bitcoin returns; STB-1: stablecoin issuance and later bitcoin returns; FCI-1: holding the indices only while financial conditions are easy (NFCI); EVT-1: drift in natural gas after the weekly storage report.

## Cumulative (since the registry began)

| | |
|---|---|
| Hypotheses registered | 81 |
| Verdicts | 70: ABANDONED 2, FAILED 58, INCONCLUSIVE 1, PASSED 9 |
| Ideas dropped before building (no test spent) | 53 in the tables of 18 dated checks, on 5 days |
| Status of every judged hypothesis (the edge classification) | PROMISING 1, REJECTED 140, VALIDATED 1 |
| Evidence files that still match their verdict | 51 of 51 checked |
| Specs whose hash is missing from their preregistration | none |

## Validation status

Every judged hypothesis not rejected, as the edge classification states it. Only VALIDATED may be promoted, and only by a person; PROMISING did not reach its bar and is not traded.

| Edge | Status | t (bar) | Out-of-sample | The classification's note | Source |
|---|---|---|---|---|---|
| RCEQ-E1-TOM | **PROMISING** | 2.24 (3.0) | +0.16% a month | retail CFD: monthly net account returns after spread, slippage, financing and dividends, not R; replication/holdout PROMISING_REPLICATED: 441 months, net t 2.175 | `research/knowledge/RC-EQ.json` |
| TRND-1 | **VALIDATED** | 3.834 (3.376) | +0.79% a month | single-program verdict: expectancies are monthly net returns, not R; holdout 69 months, net t 2.737 | `research/knowledge/TRND-1.json` |

**Forward tests running, each judged once at its preregistered end** (nothing is concluded before):

- TOM-F (registered 2026-10-04; data to an open end (see its preregistration)): TOM-F: two TOM variants for forward data only
- RADAR-1 (registered 2026-10-07; data to 2027-02-15): RADAR-1: live cross-venue funding radar, paper forward test
- TRND-F (registered 2026-11-06; data to 2029-12-01): TRND-F: TRND-1's rule forward, 2026-12..2029-11

Also registered without a verdict here, and counted in every bar: archive-smc-h1 (archive record); archive-smc-h2 (archive record); archive-trend-3 (archive record); archive-reversion (archive record); archive-smc-utc-rerun (archive record); archive-edge-program-8 (archive record); TOM-D (design only); ENG-1 (due).

## The bar each market's next test must clear

Bonferroni over every test already counted on that market's data. The more an idea's data has been read, the higher its bar: discovery never lowers it.

| Market data | Tests counted | Next bar (t) |
|---|---|---|
| fx-majors | 176 | 3.631 |
| index-cfd-intraday | 32 | 3.172 |
| multi-asset-etf | 12 | 2.890 |
| crypto-binance-usdtm | 10 | 2.838 |
| multi-asset-long | 10 | 2.838 |
| crypto-xvenue-hl-binance | 8 | 2.773 |
| crypto-binance-spot | 7 | 2.734 |
| us-equity-etf | 6 | 2.690 |
| crypto-binance-usdtm-all | 5 | 2.638 |
| equity-index-forward | 3 | 2.498 |
| equity-index-monthly | 3 | 2.498 |
| equity-index-b | 2 | 2.394 |
| us-treasury-daily | 2 | 2.394 |
| us-vol-etp | 2 | 2.394 |
| crypto-perp-live-xvenue | 1 | 2.241 |
| em-fx-daily | 1 | 2.241 |
| energy-futures-eia | 1 | 2.241 |
| equity-index-daily | 1 | 2.241 |
| metals-futures-daily | 1 | 2.241 |

The sealed holdout: fx-majors from 2017-01-01 (sealed 2026-09-26). It is opened once, by a preregistered final test of a candidate that has passed, and never for discovery.

## The last 25 verdicts, with their evidence

| Recorded | Hypothesis | Verdict | Preregistration | Spec hash quoted | Evidence file | Matches |
|---|---|---|---|---|---|---|
| 2026-11-09 | FXT-1 | FAILED | `research/preregistrations/FXT-1.md` | yes | `research/knowledge/FXT-1.json` | yes |
| 2026-11-09 | FXS-1 | FAILED | `research/preregistrations/FXS-1.md` | yes | `research/knowledge/FXS-1.json` | yes |
| 2026-11-08 | DAY-1 | FAILED | `research/preregistrations/DAY-1.md` | yes | `research/knowledge/DAY-1.json` | yes |
| 2026-11-06 | TRND-1-H | PASSED | `research/preregistrations/TRND-1.md` | yes | `research/knowledge/TRND-1-H.json` | yes |
| 2026-11-06 | TRND-1 | PASSED | `research/preregistrations/TRND-1.md` | yes | `research/knowledge/TRND-1.json` | yes |
| 2026-11-05 | RBL-1 | FAILED | `research/preregistrations/RBL-1.md` | yes | `research/knowledge/RBL-1.json` | yes |
| 2026-11-05 | TME-1 | FAILED | `research/preregistrations/TME-1.md` | yes | `research/knowledge/TME-1.json` | yes |
| 2026-11-05 | TSY-1 | FAILED | `research/preregistrations/TSY-1.md` | yes | `research/knowledge/TSY-1.json` | yes |
| 2026-11-05 | LVOL-1 | FAILED | `research/preregistrations/LVOL-1.md` | yes | `research/knowledge/LVOL-1.json` | yes |
| 2026-11-05 | EMC-1 | FAILED | `research/preregistrations/EMC-1.md` | yes | `research/knowledge/EMC-1.json` | yes |
| 2026-11-05 | PHD-1 | FAILED | `research/preregistrations/PHD-1.md` | yes | `research/knowledge/PHD-1.json` | yes |
| 2026-11-05 | SEC-1 | FAILED | `research/preregistrations/SEC-1.md` | yes | `research/knowledge/SEC-1.json` | yes |
| 2026-11-05 | GSR-1 | FAILED | `research/preregistrations/GSR-1.md` | yes | `research/knowledge/GSR-1.json` | yes |
| 2026-11-05 | VOLM-1 | FAILED | `research/preregistrations/VOLM-1.md` | yes | `research/knowledge/VOLM-1.json` | yes |
| 2026-11-05 | XSM-1 | FAILED | `research/preregistrations/XSM-1.md` | yes | `research/knowledge/XSM-1.json` | yes |
| 2026-11-05 | FOMC-1A | FAILED | `research/preregistrations/FOMC-1A.md` | yes | `research/knowledge/FOMC-1A.json` | yes |
| 2026-11-05 | FOMC-1 | ABANDONED | `research/preregistrations/FOMC-1.md` | yes | — | — |
| 2026-11-05 | VRP-1 | FAILED | `research/preregistrations/VRP-1.md` | yes | `research/knowledge/VRP-1.json` | yes |
| 2026-11-04 | FND-1A | FAILED | `research/preregistrations/FND-1A.md` | yes | `research/knowledge/FND-1A.json` | yes |
| 2026-11-04 | FND-1 | ABANDONED | `research/preregistrations/FND-1.md` | yes | — | — |
| 2026-11-04 | MEH-1 | FAILED | `research/preregistrations/MEH-1.md` | yes | `research/knowledge/MEH-1.json` | yes |
| 2026-11-04 | XTS-1 | FAILED | `research/preregistrations/XTS-1.md` | yes | `research/knowledge/XTS-1.json` | yes |
| 2026-10-30 | QT-2 | FAILED | `research/preregistrations/QT-2.md` | yes | `research/knowledge/QT-2.json` | yes |
| 2026-10-30 | QT-1 | FAILED | `research/preregistrations/QT-1.md` | yes | `research/knowledge/QT-1.json` | yes |
| 2026-10-07 | CR-5-H | FAILED | `research/preregistrations/CR-5.md` | — | — | — |

**Matches**: the evidence file's own hash equals the one recorded with its verdict; where none was recorded, the file names the spec (and code) hashes registered before the test. Every verdict is in `research/registry.jsonl`. Each program's command and frozen spec are in its preregistration, and the program refuses to judge if its spec or code no longer match the hashes recorded at registration.
