# Round 4 audit: which information sources are new, available and point-in-time valid

Round 4 has one purpose: find a genuine source of **directional** information for FX. This
audit was written before any Round 4 code or outcome existed, so Round 4 does not repeat Rounds
1–3.

Budget: **62 tests** have already been judged on these FX outcomes (Rounds 1–3 and the archive).
The next family of 5 tests must clear **t ≥ 3.372**. That bar is unchanged.

## Source matrix

| Source | Historical data available here | Point-in-time valid | Already tested | New hypothesis possible |
|---|---|---|---|---|
| FX bid/ask bars, 12 pairs (Dukascopy) | yes, 2007-03 → 2017 | yes | **exhaustively**: 29 D1 and 23 H1 features, 2,700 screened cells, trend, breakout, reversion, momentum, cross-sectional, sessions, k-NN, stumps (R1) | no: this is the space Rounds 1–3 closed |
| CFTC Commitments of Traders (positioning) | **no.** cftc.gov, publicreporting.cftc.gov, Quandl and Nasdaq Data Link are refused (403). No mirror; PyPI has downloaders only | would be, with its Tuesday-data / Friday-release lag | no | **DATA-BLOCKED** |
| Economic consensus expectations (surprises) | **no.** ForexFactory, TradingEconomics and Investing.com are refused. Historical consensus is proprietary (Bloomberg, Reuters) | — | no | **DATA-BLOCKED** |
| Central-bank decision surprises | **no.** They need market-implied expectations (OIS or rate futures), which are not reachable | — | the policy moves themselves (R3-F) | **DATA-BLOCKED** |
| GDP, payrolls, retail sales, PMI (first releases) | **no.** Only revised series are reachable, and there are no real-time vintages | no: revised values would leak | no | **DATA-BLOCKED** |
| US CPI-U, not seasonally adjusted (BLS) | yes, monthly | **yes**: the NSA index is never revised; release lag ≤ 1 month | ingested in R2, **not tested** | **yes**: US inflation acceleration → USD direction. Only the US side; foreign monthly CPI is not reachable |
| VIX daily (Cboe) | yes | yes | as a *state* for carry (R2A, R3-G) and momentum (R2D); a rising VIX → selling carry currencies (R2A-2) | **yes**: a VIX *spike* → safe-haven (JPY, CHF) catch-up, controlling for the pair's own move |
| Gold (XAUUSD bars, Dukascopy) | yes, 2011-05 → 2017 | yes (same close as FX) | **never** | **yes**: a gold move → AUD catch-up, controlling for AUD's own move |
| Brent daily (EIA) | yes | yes (1-day lag) | oil → CAD (R2C) | no: the user excluded repeating the simple oil test |
| US 10y monthly (Fed H.15) | yes | yes | R2B | no |
| BIS policy rates, 8 of 12 pairs | yes | yes | R3, all forms | no |
| S&P 500 | monthly only | yes | no | no: monthly is too coarse for a lead-lag test against daily FX, and it overlaps VIX |
| Daily yields, curve, credit spreads, broad USD index | **no.** FRED, Fed, ECB and BIS markets are refused | — | — | **DATA-BLOCKED** |

## What Round 4 will test

It tests the three sources that are new, available and point-in-time valid:

1. **Gold → AUD.** Does a gold move that AUD has **not yet followed** predict AUD's next move?
   This is incremental to AUD's own price by construction, because the condition requires that
   AUD's own 5-day move disagrees with gold.
2. **VIX spike → safe havens.** After VIX jumps ≥ 20% in 5 days, do JPY and CHF strengthen next,
   **where the pair has not already moved** that way?
3. **US inflation acceleration → USD.** An unrevised, point-in-time macro series.

Each hypothesis is also compared with its **price-only control**: the same pairs, entered on
the own-move condition alone. The difference between the two is the information value of the
new source.

## What Round 4 will not test, and why

- **Positioning (COT) and macro surprises.** DATA-BLOCKED; see the matrix. They are the two
  highest-priority sources in the plan, and neither is obtainable here without fabrication.
- **Regime re-tests of rejected signals.** VIX regimes were already applied to carry (R2A, R3-G)
  and to momentum (R2D). Positioning extremes, the other regime asked for, are DATA-BLOCKED.
  More regime combinations of already-rejected signals would be the multiplying search the
  plan forbids.
