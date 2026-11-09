# The FX mission: is there a demonstrable Forex edge in the data this project has?

**Started 2026-11-09.** The owner's brief: find the highest risk-adjusted **net** profit that survives rigorous,
reproducible out-of-sample testing. Start from an audit of everything already tried, and look across every horizon
and every credible source of edge. Use realistic costs at x1, x1.5 and x2, preregistered tests and an untouched
holdout. Fabricate nothing and lower no bar. If nothing passes, say **NO VALIDATED FOREX EDGE FOUND**.

This file holds the plan, the audit and the list of steps. The hourly check-in continues it, one step at a time.
The final answer will be `docs/FX_MISSION_REPORT.md`.

**Research only.** Production trading logic, live execution and the risk settings are not touched. Nothing is
deployed. Nothing trades real money.

## 1. The audit (done 2026-11-09)

### The data

| Data | Where | Span | Notes |
|---|---|---|---|
| M5 bid/ask bars: EURUSD, GBPUSD, USDJPY, AUDUSD, USDCAD, USDCHF, NZDUSD, XAUUSD | `data/m5/*_M5_2009_2016.npz` | 2009-2016 | Dukascopy ticks via the FX-Data mirror; measured spread per bar; tick count as activity, no volume (`data/README.md`, `docs/DATA_QUALITY_REPORT.md`) |
| M15 bid/ask, 12 pairs and XAUUSD | FX-Data mirror, built by `scripts/ingest_dukascopy.py` | 2007-03 → 2018 (EURUSD to 2022-07) | 2017 on is sealed |
| H.10 noon New York rates (the Federal Reserve), daily | pinned commits of the `datasets/exchange-rates` mirror (`data/h10/manifest.json`, `aitrader/data/h10.py`) | 1971 → 2026-09 | AUD, CAD, CHF, DKK, EUR (1999 on), GBP, JPY, NOK, NZD, SEK and emerging currencies. No DEM, FRF or other pre-euro currencies in the mirror. Point in time: usable from 17:00 New York the next business day |
| BIS policy rates | `data/div2/policy_rates.csv` | 1988 → 2026-09 | USD, AUD, CAD, CHF, GBP, JPY, NZD; EUR from 1999. Nothing before 1988, so carry cannot be tested earlier |

Not available here, and not simulated: order flow or traded volume, FX forwards and cross-currency basis, option
implied volatilities, consensus forecasts for economic releases, a broker's historical swap tables.

### The seal and the budget

- **The seal.** `research/holdout.json` seals fx-majors (XAUUSD included) from 2017-01-01. Loaders truncate there
  unless given the key that only a preregistered final test holds. The archive project's 16 simple-rule verdicts
  touched 2017-2022 before the seal (counted in every threshold). This project never has. EURUSD 2022-04..2022-12
  was never seen by anyone.
- **The budget.** 174 tests have been judged on fx-majors. Each year from 2009 to 2016 was read by 141-164 of them.
  The next FX test needs **t ≥ 3.628** (Bonferroni, `research/registry.jsonl`).
- **Fresh FX data.** No test here has read FX before 1990. RC-FX judged 1990-2016. RV-1 read 1999-2007, and
  DIV-2's trend portfolio read 1990-2007 among other markets. The H.10 rates of 1971-1989 are untouched. But before
  1988 there are no policy rates, the euro's forerunners are missing from the mirror, and AUD and NZD were pegged
  until 1983 and 1985.

### What was tried, and why it failed

174 FX tests, each preregistered and judged once (`docs/TRADING_EDGE_REGISTRY.md`). They fall into these families:

| Family | Programs | Horizon | What happened |
|---|---|---|---|
| Liquidity, SMC and ICT patterns: sweeps of the previous day's or Asia's high and low, equal highs, BOS + FVG, CHoCH, order blocks, failed breakouts, the Quarters theories, true opens | ID-1, QT-1, QT-2, archive SMC | M5-H1 | Net −0.04 to −0.21 R a trade, t down to −26. No directional information. The cost of each trade (0.1-0.2 R) was the whole result |
| Classic intraday rules: opening range, squeeze, momentum, mean reversion, session opens | ID-1, ID-2 rules, WF-001-003, SL-002 | M5-H1 | The same: gross near zero, net negative |
| Machine learning: ridge and gradient-boosted trees ranking every candidate on cost, momentum, reversion, structure, liquidity, session, higher timeframes and cross-market inputs, fitted walk-forward by year | ID-2 (18 configurations) | M5, M15, H1 | **The one real finding.** Its selections beat matched random entries by Welch t 3-7, with +0.10 to +0.19 R gross a trade. That is the size of the costs (0.10-0.13 R). The best configurations netted +0.04 to +0.09 R at t 0.7-1.6. Most of the ranking was cost avoidance: a model given only cost-to-stop ranked better than the full model. Every directional family alone had IC ≤ 0.07 |
| Daily price rules, cross-asset lead-lag (gold for AUD, VIX for the crosses), macro (CPI) | R2A-D, R3, R4, CP-001, SL-001, XS-001 | D1 | t between −2.9 and +1.0. No information |
| Positioning: CFTC COT, eleven variants | COT-1 | D1-W1 | t between −2.1 and +0.4 |
| Flows: the Gotobi days, the London 4 pm fix, month-end hedging | FLOW-1, MEH-1 | M15 | Negative or nil: the fix rule lost (t −11.6), month-end hedging +1.2 bp net (t 1.04) |
| Exploratory session and order-flow screens: Asian-session USD drift, illiquid-hours reversal, session momentum, activity-conditioned continuation, momentum into the futures settlement | EX-1 (21 looks), EX-2 (4) | M15 | Gross intraday predictability of 2.2 bp or less against 2.6-3.1 bp of cost in every family |
| Cross-sectional currency factors, weekly: carry, momentum, reversal, value, volatility-scaled | RV-1 | W1 | Carry ranked currencies in 2000-2007 (IC t 3.09), but earned nothing from 2008: the interest income equalled the spot loss. Momentum, volatility-scaled: t 2.1. The rest near 0 |
| Composite of rate, momentum and positioning | RC-FX | D1 | t 1.72 over 1990-2016 |
| Trend following: Donchian, TSMOM, SMA | archive-trend-3 | D1 and longer | Failed on 2017-2022 |
| Multi-asset trend at futures-style costs (currencies among 23 markets) | DIV-2 | MN | Passed and validated as a futures portfolio. At a retail CFD's financing it would have lost 5.7% a year. Its currency leg was never judged alone |
| The live AI desk: two language models agree on H1/M15 trades | DESK-1, the forward record | M15-H1 | −0.069 R an agreement over 375 (LEARNING) and −0.357 R over 109 (EVALUATION, t −3.2). Costs were the loss: +0.06 R before them, 0.19 R in them |

**The common cause.** On these majors, at a retail account's costs:

- simple directional information is about zero intraday, and weak at daily and weekly horizons;
- the one documented premium, carry, stopped paying after 2008;
- the one model that found real information found about as much as a trade costs.

## 2. Hypotheses for this mission

The brief lists twelve sources of edge. Each was set against the data that exists, the tests already judged and a
power check at this project's bar (t ≥ 3.63 on 2009-2016).

| # | Source | Status | Why |
|---|---|---|---|
| 1 | FX forward points and cross-currency basis | NOT TESTABLE | No forward or basis history here, and a spot or CFD account cannot trade the basis. Forward points reach a retail account only as swaps, which is carry (#3) |
| 2 | Cross-currency relative value (crosses, cointegration) | DROPPED: no power | Single-pair and cross-sectional reversion failed (ID-1 B4, RV-1 H3, R3). A daily cross-pair reversion book would need a net Sharpe ratio of about 1.3 to reach 3.63 in 8 years, against the 0.3-0.5 the literature reports |
| 3 | Carry and momentum together | REJECTED earlier | RV-1 (W1) and RC-FX (D1) judged them. There are no rates before 1988, so no fresh years exist. A swap-free account also earns no carry by construction |
| 4 | Volatility risk premia | NOT TESTABLE | FX options cannot be traded from a spot or CFD account, and no implied-volatility history is here. As a timing filter it was tested (R4-XA-VIX, RV-1 H5) |
| 5 | Macro divergence and repricing | REJECTED in part, rest not testable | R4-MACRO-CPI failed. Point-in-time macro vintages (revisions) are not reachable from here |
| 6 | Order flow and liquidity | NOT TESTABLE beyond ID-2 | No order flow or traded volume exists, only tick counts, which ID-2 used |
| 7 | Session transitions | REJECTED as price patterns, **one structural form open** | Session-open and true-open rules failed (ID-1 B6, QT-1 T2/T3, FLOW-1). EX-1's exploratory screen (2007-2012) looked at an Asian-session USD drift among 21 session families: gross ≤ 2.2 bp against 2.6-3.1 bp of cost. The European and US home-currency windows were never tested: a currency weakens during its own country's working hours and firms in foreign hours (Ranaldo 2009; Breedon & Ranaldo 2013, who tie it to order flow). → **FXS-1** |
| 8 | Lead-lag with related markets | REJECTED | C1-USD-LAG (M5), R4-XA-GOLD and R4-XA-VIX (D1), and ID-2's cross-market inputs. For oil and the commodity currencies, the published lead runs the other way: currencies predict commodity prices (Chen, Rogoff & Rossi 2010) |
| 9 | Event-driven | NOT TESTABLE as surprises | No history of consensus forecasts. FOMC and CPI days were tested on other markets |
| 10 | Regime-dependent | Partly tested | Volatility-scaled carry and momentum (RV-1 H5/H6), ID-2's regime inputs. A new regime split of the same data would mostly be curve-fitting |
| 11 | Statistical arbitrage and mean reversion | REJECTED | ID-1 B4, ID-2 R-MR, RV-1 H3, R3 |
| 12 | Machine learning, with leakage controls | REJECTED (ID-2), evidence kept | Real information about the size of a trade's cost. A successor needs measured costs from today's broker, recorded over months. Retuning on the same data would be curve-fitting |
| 13 | Trend in currencies on the untouched 1974-1989 years | **FXT-1** | The best-documented currency return of those years (Sweeney 1986; Levich & Thomas 1993), on data no test here has read. Its modern record is poor (archive-trend-3 failed on 2017-2022). A pass would be checked against the sealed modern years before anything is called validated |

## 3. Steps

1. ~~Audit~~ (done).
2. ~~Hypotheses and power~~ (done; section 2).
3. ~~**FXS-1**~~ (done 2026-11-09): **FAILED**. Before costs the pattern was there, +0.76 bp a trade (t 2.88),
   but a round trip cost 1.66 bp: −0.90 bp net, daily t −2.47 against 3.6158. EURUSD in European hours netted
   +1.3 bp, a post-hoc lead. The Tokyo window was never traded, because the mirror has no 00:00 UTC bars for
   USDJPY (`research/preregistrations/FXS-1.md`).
4. ~~**FXT-1**~~ (done 2026-11-09): **FAILED, on t alone**. +5.79% a year net, Sharpe 0.70, t 2.71 against
   3.6294. Every other gate passed: both halves, costs x2, a month late, random signs, the bootstrap
   (`research/preregistrations/FXT-1.md`).
5. ~~The sealed holdout~~: not opened. No candidate passed its judge, so the seal stays closed.
6. ~~`docs/FX_MISSION_REPORT.md`~~ (done 2026-11-09): **NO VALIDATED FOREX EDGE FOUND**.

## The $4,000-a-month question (2026-11-09)

The owner's updated mission set the target: $4,000 a month net on $200,000 (2% a month). `docs/FX_TARGET_REPORT.md`
scales the judged books to fixed risk levels (`scripts/fx_target.py`, `research/results/FX-TARGET.json`).

**Not credible.** The best candidate, FXT-1, would have averaged about $580 a month at a capital-preserving 5%
volatility. On the target it needs 6.3x leverage: a 66% drawdown on its own history and a 38% chance of ruin in five
years, and close to certain ruin if its edge halved. FXT-F is not run: the open-ended 2017 seal would be spent
on it (`docs/FX_TARGET_REPORT.md`, correction). The next FX evidence is the broker's measured costs.
