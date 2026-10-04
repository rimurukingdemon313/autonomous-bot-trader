# TOM-D: diagnostics of the turn-of-the-month candidate (analysis plan)

**Written, frozen and committed before any diagnostic was computed.** It concerns RC-EQ's E1 TOM:
PROMISING on universe A (1990–2020, net t 2.24) and PROMISING_REPLICATED on universe B
(1990–2026, net t 2.18).

| | |
|---|---|
| Frozen plan | `research/specs/TOM-D.json` |
| Plan sha256 | `84e6029567431916cfbed9eee60e62ed69c348554406f170390d9ad9bcb7dbcb` |
| Code | `aitrader/research/discovery/tomdiag.py`, `scripts/tom_diag.py`, and RC-EQ's frozen `retail.py`, `rc.py`, `rc_eq.py` (hashed) |
| Run | `.github/workflows/tom-diag.yml` on a GitHub runner |

## What this is, and what it is not

- **It is descriptive.** It re-reads data already used:
  - universe A, 1990–2020, never loaded after 2020;
  - universe B, 1990–2026, whose seal RC-EQ2-H spent.

  It is registered with role `select` and **0 tests**, so it adds nothing to any significance
  claim and validates nothing.
- **The rule is not changed.** Every headline number uses `rc.tom(k_pre=1, k_post=3)`, equal
  weight 1/N, RC-EQ's costs.
- **Variants are fixed here:** the calendar neighbourhood, the cost grid, the universe subsets and
  inverse-volatility weighting. If one of them looks better, it is recorded as a **new hypothesis
  for forward data only**. It is never declared validated from these data, which were already
  used to select TOM.
- No other strategy is examined.

## The analysis, fixed in advance

1. **Trade ledger.** For A and B: every trade's entry/exit date and close, trading and calendar
   days, weight, and its gross, spread, slippage, commission, benchmark financing, markup,
   dividends and net. Written to `research/results/TOM-D-trades-{A,B}.csv`.
2. **Decomposition.**
   - **Contributions:** by index, year and entry month, and by relative trading day (−5…+6,
     pooled close-to-close returns).
   - **Concentration:** the best 1/3/5 indices and the best 5 years as a share of the total net,
     and the best 10% of trades.
   - **Leave-outs:** each index alone, then every pair. The five worst pairs, and how many pairs
     leave a net ≤ 0.
3. **Decay.** Before 2009 versus from 2009:
   - the cost components, to separate **gross signal decay** from **cost decay**;
   - TOM days minus other days (the drift), by five-year block;
   - per-index price return per trade;
   - the price return when the benchmark rate is below 1% versus at least 1%;
   - the price return when the entry's 60-day volatility is above versus below its own past median;
   - the relative-day profile before and after 2009 (whether the effect moved earlier).
4. **Cost grid.** Every cost ×1, ×1.25, ×1.5, ×2, ×3. Reports CAGR, mean annual, Sharpe, t,
   compounded max drawdown and profit factor, plus the post-2009 annual and t.
5. **Broker economics.**
   - **Annual cost lines**, bps of equity a year: spread, slippage, commission (zero on index
     CFDs), benchmark financing and markup. There are no shorts, so short financing and short
     dividends are zero by construction.
   - **Break-even values:** the break-even markup (overall and post-2009), the break-even
     multiplier on all broker costs, and the mean benchmark rate paid while positions were held.
6. **Calendar neighbourhood.** Original (k_pre 1, k_post 3), entry one day earlier (2, 3), entry
   one day later (0, 3), exit one day earlier (1, 2), exit one day later (1, 4). Five variants, no
   others.
7. **Index robustness, pooled 1990–2020** (A has no data after 2020):
   - all 26;
   - developed (A plus B without IND50, KOR200, MEX35, BRA60, MYS30, IDN, the MSCI emerging
     markets);
   - the 8 major CFDs (US500, NAS100, JPN225, UK100, GER40, FRA40, AUS200, EU50);
   - A only, B only, B developed, B emerging;
   - all 26 without each major, one at a time.
8. **Portfolio construction.** Equal weight versus inverse volatility. The same windows and the
   same total notional; weight ∝ 1/sd of the last 60 daily returns at entry, fixed for the window.
9. **Holding time.** Mean and median trading and calendar days, exposure days per index per year,
   financing per trade, the markup per calendar day, and the return per relative day against the
   cost of holding it.
10. **Uncertainty.** A 12-month moving-block bootstrap of the mean monthly net (full, before 2009,
    from 2009): 95% interval and P(mean ≤ 0).
11. **Implementation facts.**
    - Close-to-close worst move inside each window, giving the share of trades a 3% / 5% / 10%
      protective stop would have hit (relevant because the risk engine requires a stop).
    - How often the data's last trading day of a month is not its last weekday.

## Classification, after the diagnostics (the brief's categories)

**A.** strong promising edge. **B.** weak promising edge. **C.** cost-destroyed edge.
**D.** statistical artifact. **E.** implementation-infeasible.

The report states which numbers decide it.
