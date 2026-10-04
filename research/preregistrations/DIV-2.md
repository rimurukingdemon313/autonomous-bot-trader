# DIV-2: DIV-1's trend rules on long-history excess returns (preregistration)

**Written, frozen and committed before any DIV-2 market data was fetched or read.**

| | |
|---|---|
| Frozen spec | `research/specs/DIV-2.json` |
| Spec sha256 | `cb440fbd470e6747e22cb4bdb33624116e59ca5745495eee4ec85eaa4eaf9249` |
| Code | `aitrader/research/discovery/trend.py` (unchanged from DIV-1), `aitrader/research/discovery/excess.py`, `scripts/div2.py`, `aitrader/data/h10.py` (hash in the spec) |
| Run | `.github/workflows/div2-run.yml` on a GitHub runner: `fetch`, then `judge`. `holdout` only if `judge` PASSED |

## Why DIV-2, and what it does NOT change

DIV-1 failed for two **diagnosed** reasons (`research/results/DIV-1-summary.md`):

1. **Funding.** 86% of its costs were financing the ~3.5× leverage implied by a 40% per-asset
   volatility target funded as ETFs at a declared 3%. Its gross premium (Sharpe 0.45 / 0.61) was the
   size the literature reports.
2. **Power.** Even with no financing, 13 years gives t ≈ 1.8 for that premium, short of 3.0.

DIV-2 tests the **same frozen rules** (`trend.py`, untouched: the same signals, 40% volatility
target, 60-day EWMA, monthly rebalance and equal risk weights) where those two causes are absent.

- **Instruments as the literature measures them:** futures-style **excess** returns, in which
  funding is part of the return, so no leverage-financing line applies.
- **A long history this project has never examined:** 1990-01 → 2007-12, 216 months.

Nothing about the signal, the sizing or the gates is tuned. The cost model changes because the
instrument changes (futures, not ETFs). The retail-CFD cost the user's own broker would charge is
**reported** alongside, not hidden.

## Universe (daily)

| Class | Series | Source |
|---|---|---|
| Equity (10) | S&P 500, Nasdaq Composite, Nikkei 225, FTSE 100, DAX, Hang Seng, TSX, CAC 40, SMI, ASX 200 | Yahoo index levels |
| Bonds (2) | US 10-year and 5-year yields (^TNX, ^FVX) | Yahoo |
| Currencies (7) | AUD, CAD, CHF, GBP, JPY, NZD vs USD; EUR from 1999 | Federal Reserve H.10 (pinned, sha-verified vintage) |
| Commodities (4) | WTI, Brent, Henry Hub gas (EIA spot), gold (GC=F, from 2000) | datahub.io (EIA); Yahoo |

Funding and carry come from BIS policy rates (`data/div2/policy_rates.csv`, extracted unmodified
from the BIS file supplied by the user; sha256 in `data/div2/manifest.json`).

## Excess returns (`excess.py`; declared approximations)

- **Equity:** price return + 2% a year dividend yield − USD policy rate.
- **Bonds:** (yield − USD policy rate)/252 − D × Δyield, with D = 8 for the 10-year and 4.5 for the
  5-year.
- **Currencies:** spot return + (foreign − USD policy rate) × days/365, using rates public at the
  previous close.
  - A currency-day without a published rate is **excluded**, never filled: the euro before 1999,
    and the yen in the years the Bank of Japan published no policy rate.
- **Commodities:** spot return as a proxy for front futures. The roll yield is ignored (declared).
- **Calendar:** a short holiday gap (≤ 5 calendar days) is carried; a longer gap is never carried.
- **Yield quoting:** a series quoted at 10× (CBOE convention) is divided by 10; any other scale is
  refused. This rule was fixed before the data was read.

## Costs

- **Primary:** 2 bps per unit of weight traded. No financing line: excess returns already pay it.
- **Costs ×2:** 4 bps.
- **Reported, not gating:** retail-CFD financing, a 2.5% a year markup on the full gross notional.

## Periods

| Role | Period |
|---|---|
| Development | 1990-01 → 1998-12 |
| Validation | 1999-01 → 2007-12 |
| Judged (registry role `judge`) | 1990-01 → 2007-12 |
| Replication, descriptive only, already seen | 2008-01 → 2020-12. The same markets were seen through DIV-1's ETFs; it is reported, never a gate |
| Sealed holdout | 2021-01 onward (`research/holdout-div.json`, unused by DIV-1). Opened once, only for DIV-2 passers |

**Prior exposure, declared.** H.10 currencies 2000–2007 were read by RV-1 (cross-sectional
ranks). Brent 2007 was read in round 2. No equity index, bond yield or pre-2000 currency series
was read by this project before.

## Gates (identical to DIV-1; all required)

1. **t ≥ 3.0** on the mean monthly net return, 1990–2007. The registry's own Bonferroni value for
   2 tests on this fresh universe is 2.24; 3.0 is kept.
2. Mean net > 0 in development **and** in validation.
3. Mean net > 0 with costs ×2.
4. Mean net > 0 when leaving out any one asset class.
5. No single year supplies more than 50% of the total net.

**Holdout:** mean net > 0, and mean net > 0 with costs ×2, over 2021-01 onward.

## Power, stated in advance

Over 216 months, t ≥ 3.0 needs an annual net Sharpe of about 0.71. The literature reports roughly
1.0 for diversified trend following over 1985–2009 on 58 futures. This universe is smaller (23
series) and uses spot proxies, so a fail is plausible and would be reported as such.

## What a pass would mean, and what it would not

- **What it would mean.** A pass plus a holdout pass makes DIV-2 VALIDATED **as a futures-style
  diversified trend portfolio**.
- **What it would not mean.** It is not a validation of trading it through a retail CFD broker. The
  CFD-cost line will say whether that survives. It is not a single-pair FX signal for the existing
  bot.
- **Before trading.** Implementing it needs broker instruments across those asset classes and a
  monthly portfolio-rebalancing path through the risk engine, built only after the evidence.
