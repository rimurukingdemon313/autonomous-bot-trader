# FXT-1: time-series momentum in the major currencies, on the untouched 1975-1989 years

**Pre-registered 2026-11-09, before any FXT-1 outcome was computed.**

| | |
|---|---|
| Frozen spec | `research/specs/FXT-1.json`, sha256 `1d02f6017da3c6761b065d20d0eb5b5b2c383647df7a1026b29070ba36874f96` |
| Code | `scripts/fxt1.py`, sha256 `663880df6355406274124ce475814d42335534d83fbb56adf8c9cf93daf09a4b` |
| Threshold | t ≥ **3.6294**: Bonferroni over every test the registry records on FX data, whatever its years (175), plus this one |

## Why

- **The mission.** The owner's FX mission of 2026-11-09 (`docs/FX_MISSION.md`) asks for every horizon, position
  trading included.
- **The rule's best-documented years.** Trend-following profits in currencies were documented in the 1970s and 1980s
  (Sweeney 1986; Levich & Thomas 1993). Time-series momentum is their cleanest form (Moskowitz, Ooi & Pedersen 2012).
- **Fresh data.** No test in this registry has read FX before 1990. RC-FX starts in 1990, DIV-2's trend portfolio in
  1990, RV-1 in 1999.
- **Its modern record is poor.** The archive's trend rules (Donchian, TSMOM, SMA) failed on 2017-2022
  (archive-trend-3). So a pass here describes those years. Before anything is called validated, the sealed modern
  years must agree.

## The rule

- **Each month, for each currency.** At the month's first business day, take the currency's own return against the
  dollar over the past 12 months, from the last business day 13 months back to the last business day of the
  previous month. Hold it long against the dollar if that return was positive, short if negative.
- **Size.** 10% annual volatility from its last 60 daily returns, at most 3x, divided equally among the currencies
  traded that month.
- **Rebalancing.** Monthly, sizes included.
- **Currencies.** GBP, JPY, CHF and CAD for the whole period. AUD from January 1985 and NZD from April 1986: a
  currency is traded only when its whole 12-month look-back lies after its float (AUD 12 December 1983, NZD 4 March
  1985). EUR does not exist before 1999.
- **Point in time.** H.10 noon New York rates, each usable only from 17:00 New York on the next business day. The
  month's decision is taken at 17:00 New York on its first business day and filled at the next noon rate after it.
  The month's return runs from that fill to the next month's.

## Data and costs

| | |
|---|---|
| Rates | H.10 via the pinned 2018-10-17 vintage (`data/h10/manifest.json`, sha256 `0791b898…`), loaded through `H10Store`, which truncates at the 2017 seal |
| Costs | the rates are mid rates with no bid and ask, so a retail cost is declared: 2 bp of notional each way per unit traded (spread, commission and slippage together), x1.5 and x2 |
| Financing | none. The judge is a swap-free account's, spot only. There are no policy rates here before 1988, so a standard account's swaps cannot be computed for these years |

## The test

| | |
|---|---|
| Statistic | t of the mean monthly net return, 1975-01..1989-12 (180 months) |
| Development / validation | 1975-1982 / 1983-1989 |
| Random control | the same sizes with random signs per currency and month (seeds 11, 12, 13) |
| Uncertainty | 95% interval of the mean monthly net, 12-month block bootstrap, 10,000 draws |
| Delay | the book again with every signal one month old |
| The volatility forecast | the same book at equal notional (no volatility sizing), reported. It answers whether the size rule adds anything |

**Gates (all required):**

1. Monthly net t ≥ 3.6294.
2. Mean monthly net > 0 in development, and > 0 in validation.
3. Mean monthly net > 0 at costs x2. Costs x1.5 are reported.
4. Beats the random-sign control by a Welch t of 2.0 or more.
5. At least 60% of the currencies traded contribute positively.
6. No calendar year holds more than 50% of the total net.
7. The bootstrap interval lies above zero.
8. Mean monthly net > 0 with one-month-old signals.

## Power, stated before the test

- **The bar's size.** It needs an annual net Sharpe ratio of about 0.94 over 15 years.
- **The published evidence.** It suggests currency trend books of that era came near it, perhaps a little above or
  below. Nothing here was measured on these years.
- **Chance of passing:** perhaps one in three.

## The holdout

Only if every gate passes: 2017-01..2026-09, from the H.10 2026-09-29 vintage, with EUR as a seventh currency,
opened once as FXT-1-H.

- **Gates:** mean monthly net > 0 in a swap-free account, and > 0 at costs x2.
- **Also reported:** a standard account's swaps (BIS policy rates plus a 1.5% a year markup).
- **VALIDATED:** the edge registry calls it validated only at a holdout t of 2.5 or more.

## After the verdict

- **FAILED:** recorded as it is.
- **PASSED:** the holdout above, once.
- **Never:** nothing reaches production, live execution or the risk settings within this mission.

## Result (2026-11-09): FAILED, on t alone

Judged once (`research/knowledge/FXT-1.json`, `research/results/fxt1-judge.log`). The holdout stays sealed.

| | |
|---|---|
| 1975-1989, swap-free | **+5.79% a year net** (+5.91% gross), volatility 8.3%, Sharpe 0.70, Sortino 1.31, worst fall 15.9%; monthly t **2.71** against 3.6294 |
| Development, 1975-1982 | +4.26% a year, t 1.36 |
| Validation, 1983-1989 | +7.53% a year, t 2.65, Sharpe 1.00 |
| Costs x1.5 / x2 | +5.73% / +5.66% a year: the monthly turnover costs about 0.1% a year |
| One month late | +4.12% a year, t 2.03 |
| Equal notional (no volatility sizing) | +3.70% a year, Sharpe 0.54: the size rule raised the Sharpe ratio from 0.54 to 0.70, not tested for significance |
| Random signs, same sizes | −0.05% a month; Welch t 2.71 against them |
| Bootstrap 95% | +0.15% to +0.88% a month |
| Years | 11 of 15 positive; the best (1977, +23.4%) is 27% of the total; worst −7.5% (1981) |
| By currency | GBP t 3.22, JPY t 2.00, CHF t 1.02, CAD t 0.79, NZD t 0.46 (45 months), AUD −0.01 (60 months) |
| Activity | about 5.4 position flips a year, gross exposure 1.5x |

**What it says:**

- **The strongest FX result in this registry.** Currency trends paid in 1975-1989 in every way the gates check: both
  halves, double costs, a month's delay, random signs, no single year. Only significance at this bar failed.
- **It cannot be confirmed.** At t 2.71 it falls short of the bar set by 176 FX tests, and short of the floor of 3.0.
  Its Sharpe ratio of 0.70 is the size the literature reports, and 15 years cannot confirm that size at this bar.
- **The seal stays closed.** By the registered rule, the 2017+ holdout opens only for a passer. The archive's trend
  rules had already failed on 2017-2022 (archive-trend-3).
- **One defect in the artifact.** The gate `top_year` is stored as the string "True" (a numpy boolean serialized by
  `default=str`). It passed, and the verdict, computed from the booleans themselves, is unaffected.
