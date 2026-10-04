# DIV-1: diversified time-series momentum (preregistration)

**Written, frozen and committed before any DIV-1 data was fetched.** This research container
cannot reach public market data (Yahoo, Stooq, FRED and Dukascopy are blocked). Nobody in this
project has seen these series.

| | |
|---|---|
| Frozen spec | `research/specs/DIV-1.json` |
| Spec sha256 | `fa14c08919c8c514546aabe999f659bbfe0ed6cf2b393636bfe309dd1ae19254` |
| Code | `aitrader/research/discovery/trend.py` and `scripts/div1.py` (hash in the spec; `judge` refuses to run if either changed) |
| Run | `python scripts/div1.py fetch && python scripts/div1.py judge`, on any machine with internet access. Then `holdout`, only if `judge` PASSED |

## Why this, after 58 rejections on FX

Every FX test here failed for one of two reasons.

1. **No information.** Gross edges were within ±0.03R on H1. Even with free trading, the best
   gross t across all judged hypotheses is 2.27, against a threshold of about 3.4.
2. **Too little power.** About 10 years of 12 correlated currency pairs: a real effect of normal
   professional size (annual Sharpe 0.5) would be confirmed only about 3% of the time at the
   registry's threshold.

Time-series momentum is different on both counts:

- **It is the most replicated anomaly on record.** It is positive across 58 futures markets
  (Moskowitz, Ooi & Pedersen 2012) and in every decade from 1880 (Hurst, Ooi & Pedersen 2017).
- **Its source is diversification.** It earns through many weakly correlated asset classes, which
  this repository's FX-only data could not provide. CP-001, single-pair FX trend, had a gross t of
  about 1.5.

## Universe (19 ETFs, all listed by the end of 2007)

| Asset class | ETFs |
|---|---|
| Equity | SPY, QQQ, IWM, EFA, EEM, EWJ |
| Bonds | TLT, IEF, LQD, TIP |
| Commodities | GLD, SLV, USO, DBC, DBA |
| Currencies | UUP, FXE, FXY |
| Real estate | VNQ |

Adjusted daily closes (dividends and splits). Each file's sha256 is recorded at fetch.

## Rules (from the literature; nothing is tuned)

- **Rebalance:** monthly, at month-end closes. An asset needs 13 months of history.
- **H1 TSMOM12:** sign of the trailing 12-month total return.
- **H2 BLEND:** sign of the mean of the signs of the 1-, 3- and 12-month returns.
- **Sizing:** each position targets 40% annualised volatility, from an EWMA of daily log returns
  with a 60-day centre of mass. Positions are averaged over the assets present. The return is the
  next month's simple return.
- **Costs:**
  - 5 bps per unit of weight traded;
  - financing of gross exposure above 1 at 3% a year;
  - borrowing on short exposure at 0.5% a year.
- **Costs ×2 stress:** all of the above doubled.
- **Risk-free excess:** not subtracted. This is declared: it understates nothing in a test against
  zero, because the financing charge is already paid.

## Periods

- **Development:** 2008-01 → 2014-12.
- **Validation:** 2015-01 → 2020-12.
- **Judged together:** 2008-01 → 2020-12 (156 months).
- **Sealed holdout:** 2021-01 onward (`research/holdout-div.json`, single-use key).

## Gates (all required, over 2008-2020)

1. **t ≥ 3.0** on the mean monthly net return. This is fixed and stricter than the registry's
   ≈2.24 for 2 tests on a fresh universe, because this project has searched widely before.
2. Mean net > 0 in development **and** in validation.
3. Mean net > 0 with costs ×2.
4. Mean net > 0 when leaving out any one asset class.
5. No single year supplies more than 50% of the total net.

## Holdout rule, stated in advance

The holdout is opened once, by trial DIV-1-H, only for the passers. A passer must show:

- mean net > 0; and
- mean net > 0 with costs ×2.

About 68 months is a **sign check**, not a significance test: a Sharpe of 0.5 gives an expected
t of about 1.2 over that span.

## Power, stated in advance

Over 156 months the gate t ≥ 3.0 needs an annual net Sharpe of about 0.83. The literature's
diversified long-run Sharpe is about 0.7–1.0 gross. The 2009–2019 decade was weak for trend
followers. **A failure is a real possibility and would be reported as such.** It would mean the
effect was not strong enough in 2008–2020 to clear the bar, not that trend following is impossible.

## What a pass would mean

A pass followed by a holdout pass makes DIV-1 a VALIDATED edge for **multi-asset** portfolios. To
trade it, the live system would need broker instruments for those asset classes (index,
commodity, bond and FX CFDs), and a portfolio-rebalancing execution path through the same risk
engine. Neither is built until the evidence exists.
