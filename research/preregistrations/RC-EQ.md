# RC-EQ: retail-CFD equity-index candidates (preregistration)

**Written, frozen and committed before any RC-EQ price was fetched.** Design and diagnosis:
`docs/RETAIL_RESEARCH_PROGRAM.md`.

| | |
|---|---|
| Frozen spec | `research/specs/RC-EQ.json` |
| Spec sha256 | `bbe20ccd5feb1d9e5ef27b833bdd86af306ad6c2438ebae4b179792a5f592646` |
| Code | `aitrader/research/discovery/retail.py`, `aitrader/research/discovery/rc.py`, `scripts/rc_eq.py` (hash in the spec) |
| Run | `.github/workflows/rc-eq-run.yml` on a GitHub runner: `fetch` (universe A only), then `judge`. `holdout` only if a hypothesis passes |
| Holdout | `research/holdout-rc-eq.json`: universe B, sealed before any of its prices was fetched |

## What was known before writing this

- **The availability probe** (`research/results/rc-probe.json`): dates, counts and time zones only.
- **Every earlier result in this repository.** In particular DIV-1/DIV-2, which used most of
  universe A's markets for trend following:
  - equity was trend's largest contributor in 1990–2007;
  - trend has earned about nothing since 2008.

  E4 (regime) and E6 (breakout) are trend-family rules. That knowledge is declared; their gates are
  not relaxed.
- **The published literature for each mechanism.** Every rule below is its standard published
  form with its standard parameter. No parameter was chosen from data.
- **No RC-EQ outcome, return or statistic of any series.**

## Universe A (judged), 10 index CFDs, exchange-local daily closes (Yahoo)

| CFD | Series | Financing rate (BIS policy) | Spread |
|---|---|---|---|
| US500 | S&P 500 **total return** (^SP500TR) | US | 2 bps |
| NAS100 | Nasdaq-100 (^NDX) | US | 2 bps |
| JPN225 | Nikkei 225 | JP (not held 1999-02→2000-08, 2001-03→2006-03, 2013-04→2016-09: no BoJ policy rate) | 2 bps |
| UK100 | FTSE 100 | GB | 2 bps |
| GER40 | DAX (total return by construction) | DE, then euro area from 1999 | 2 bps |
| FRA40 | CAC 40 | FR, then euro area | 2 bps |
| AUS200 | S&P/ASX 200 | AU | 2 bps |
| HK50 | Hang Seng | HK (from 1998-09) | 5 bps |
| CAN60 | S&P/TSX Composite | CA | 5 bps |
| SWI20 | SMI | CH | 5 bps |

**Periods.**

- Judged: 1990-01 → 2020-12. Development 1990–2005, validation 2006–2020, modern 2009–2020.
- Data is loaded from 1985 for warm-up and **never after 2020-12-31**. The 2021+ period opened
  by DIV-2-H is not used.

## Universe B (sealed instrument holdout), 16 indices never loaded by this project

US2000 (^RUT), ESP35 (^IBEX), NETH25 (^AEX), EU50 (^STOXX50E), SWE30 (^OMX), ITA40
(FTSEMIB.MI), BEL20 (^BFX), AUT20 (^ATX), IND50 (^NSEI), KOR200 (^KS11), NZL50 (^NZ50), MEX35
(^MXX), BRA60 (^BVSP), ISR125 (^TA125.TA), MYS30 (^KLSE), IDN (^JKSE).

**How B was chosen, mechanically and before any of its prices.**

- Inclusion: every probed index with at least 10 years of closes before 2021 and a BIS rate for
  its currency.
- Exclusion: near-duplicates of A (Dow, Nasdaq Composite).

Spreads are 5 bps for the commonly offered CFDs and 10 bps for the rest. Many of these indices are
offered as CFDs only by some brokers: **B tests the hypothesis, it is not a trading list.**

B shares calendar time with markets studied here, so it is an **instrument** holdout, not a time
holdout. Period: 1990-01 → 2026-09, reported before 2021 and from 2021.

## Rules (rc.py; positions are fractions of equity, 1/10 per index, so at most 1× in total)

| ID | Rule | Primary | Neighbourhood grid (robustness) |
|---|---|---|---|
| E1 TOM | Long the last `k_pre` trading days of each month and the first `k_post` of the next. Calendar only | 1, 3 | k_pre {1,2,3} × k_post {2,3,4} |
| E2 DIP | z = log(C_t / C_{t−L}) / (σ60 √L), σ60 the sd of the last 60 daily log returns (≥ 50 valid). Long at the close when z ≤ threshold; out when z ≥ 0 or after 10 closes | L 5, −1.0 | L {3,5,10} × threshold {−0.75, −1.0, −1.5} |
| E3 XSMOM | At the last trading date of each month, rank the eligible indices by their 12-month return skipping the last month. Long the top 3 (+1/6 each), short the bottom 3 (−1/6). Filled at each index's **next** close. Needs ≥ 6 eligible | 12, k 3 | lookback {6,9,12} × k {2,3,4} |
| E4 REGIME | At each month-end close, long if the close is above the mean of the last 10 month-end closes (incl. this one), else flat | 10 | {6,8,10,12,14} |
| E5 VOLMAN | At each month-end close, weight min(1.5, 15% / realised vol of the last 21 daily returns) / 10 | 15%, 21 | target {10,15,20%} × window {21,63} |
| E6 BREAKOUT | Long when the close exceeds the highest of the previous 100 closes; out when it is below the lowest of the previous 50 | 100, 0.5 | entry {50,100,150} × exit ratio {0.25,0.5} |
| E7 ENSEMBLE | Mean of the targets of E1–E6, run as one account | | none |

**Execution.**

- Own-price rules fill at the close their signal is computed on. A bot running at each market's
  close can do this on the CFD, which trades on after the cash close. Every fill pays half the
  spread plus 1 bp.
- The **delay** gate re-runs every rule one close later.
- **Data rules.** One-day 20% misprints and frozen feeds (5+ identical closes) are removed and
  never replaced. Dates are exchange-local. Missing data is reported per index, never filled.

## Costs

- The retail model in `docs/RETAIL_RESEARCH_PROGRAM.md` §C.
- Long financing at the benchmark + 2.5% a year; short at the benchmark − 2.5%.
- No dividend credit to longs on price-return indices; shorts pay 3%.
- **Costs ×2** doubles every assumption.

## Gates (all required on universe A, 1990–2020)

1. **t ≥ max(3.0, the registry's Bonferroni value)** on the mean monthly net return (the spec
   records the value).
2. Mean net > 0 in development **and** in validation.
3. Mean net > 0 in 2009–2020.
4. Mean net > 0 with costs ×2.
5. Mean net > 0 with every fill one close later.
6. Mean net > 0 leaving out any one index.
7. No year supplies more than 30% of the sum of positive years.
8. **No magic number:** at least 75% of the neighbourhood grid has a mean net > 0, and the grid's
   median t is ≥ 2.0.
9. Maximum drawdown (sum of monthly net, 1×) ≤ 30%.

**Classification.**

- **HOLDOUT_ELIGIBLE:** every gate passes.
- **PROMISING:** t ≥ 2.0 with development, validation and costs ×2 all > 0. Reported, never sent
  to the holdout.
- **REJECTED:** otherwise.

## Holdout (universe B, once, eligible hypotheses only)

**t ≥ z(1 − 0.05/k)** (one-sided Bonferroni over the k eligible hypotheses), plus mean net > 0:

- before 2021 **and** from 2021;
- with costs ×2;
- with a one-close delay.

That is stricter than DIV-2's sign-only holdout rule, whose weakness is on record.

## Reported for every hypothesis (not gates)

- **Returns and risk:** gross, trading costs, financing, dividends, net, annual return,
  volatility, Sharpe, Sortino, maximum drawdown (summed and compounded), rolling 36-month Sharpe.
- **Trades:** count, win rate, profit factor, expectancy, median holding period.
- **Activity:** turnover, return per unit of turnover, exposure, time in market.
- **Robustness:** by year, per index, the 1×/2×/3× table, bull/bear and volatility-regime
  splits, and the correlation of the monthly net between hypotheses.

## Power, stated in advance

Over 372 months, t ≥ 3.0 needs a net Sharpe of about 0.54 after retail costs. TOM's published
gross Sharpe on US data is of that order before costs. The other families' published Sharpes are
lower. **A fail is the likely outcome for most and will be reported as such.**

## What a pass would mean

A hypothesis that passes A and B is a candidate for **controlled PAPER/DEMO testing** of index
CFDs. That needs index instruments and a calendar-driven path through the risk engine, built only
after the evidence. It would not be a claim of future profit.
