# TOM investigation: is the turn-of-the-month rule a useful edge for this retail CFD bot?

**Verdict: B. WEAK PROMISING EDGE: interesting but insufficient economics.**
**No PAPER implementation spec is issued; that requires category A.**

## Sources

| Item | Path |
|---|---|
| Plan, frozen before any number | `research/preregistrations/TOM-D.md` (spec `84e60295…`) |
| Results | `research/results/TOM-D.json` |
| Trade ledgers | `research/results/TOM-D-trades-A.csv` (3,452 trades) and `-B.csv` (5,440) |
| Run log | `research/results/tomd-run.log` |
| Code | `aitrader/research/discovery/tomdiag.py` and `scripts/tom_diag.py` |

**How the run was done.** The run re-uses RC-EQ's frozen simulator and rule unchanged, and
reproduces RC-EQ's headline numbers exactly:

- **A:** +2.59%, t 2.24.
- **B:** +1.87%, t 2.18.

Both universes are data already used (A 1990–2020, never loaded after 2020; B 1990–2026). The
run is registered as descriptive (role `select`, 0 tests). Nothing below validates anything.

## The answer in four numbers

1. **Before 2009, TOM was a real, broad calendar effect.**
   - The days in the window beat all other days by 12.5 bps a day on A (Welch t 7.6) and by
     16.0 bps on B (t 8.9).
   - A trade grossed 49 bps (A) or 63 bps (B) per unit of notional, against about 17 / 25 bps of
     retail cost.
2. **From 2009, on the developed indices the bot can trade, the calendar effect is gone.**
   - On A, window days beat other days by **0.6 bps a day (t 0.36)**.
   - About 85% of what a post-2009 TOM trade earns gross is the ordinary equity drift that any
     long position earned in the 2009–2020 bull market.
3. **What is left of the calendar effect does not pay for its own costs.**
   - The excess over the drift per trade from 2009 is about 2.6 bps (A) and 16 bps (B).
   - Retail costs per trade (spread, slippage and financing) are 10.3 bps (A) and 19.2 bps (B).
4. **Statistically, the post-2009 net is indistinguishable from zero.**
   - A: +1.06% a year, t 0.58, P(mean ≤ 0) = 56%.
   - B: +1.17% a year, t 0.81, P(mean ≤ 0) = 41% (12-month block bootstrap).
   - With costs doubled it is −0.02% (A) and −0.55% (B).

**So the +1.87% is mostly a decayed historical effect plus equity drift. It is not a current edge.**

It is not a statistical artifact: it is broad, not concentrated, and not a magic date (§2, §6, §7).
It is not primarily cost-destroyed: costs per trade did not rise, and financing fell (§3).

---

## 1. The exact strategy, reconstructed (rules unchanged)

| Item | Exactly what the backtest does |
|---|---|
| Rule | `rc.tom(k_pre=1, k_post=3)`, frozen in `research/specs/RC-EQ.json` |
| Entry time | The official close (Yahoo, exchange-local date) of the **second-to-last** trading day of each month, on each index's own calendar |
| Entry price | That close. Each fill pays half the spread plus 1 bp of slippage, so the effective entry is close × (1 + spread/2 + 1 bp) |
| Exit time | The close of the **third** trading day of the next month |
| Exit price | That close, less half the spread and 1 bp |
| Holding period | The returns of days −1, +1, +2, +3: **4.0 trading days** (median 4), **6.1 calendar days** (median 6; most windows include a weekend) |
| Sizing | 1/N of account equity in notional per index; N = 10 (A) or 16 (B). No leverage |
| Simultaneous positions | Up to N. The windows of all indices nearly coincide, so up to 10 (A) or 16 (B) positions open together, at up to 1× equity in total. Average exposure is 0.18× (A) and 0.15× (B); time in market 23% / 27% |
| Instruments | Fixed lists (RC-EQ.md); never chosen by performance |
| Holidays | Taken from the data: a day with no close is not a trading day, so the window moves to the actual last trading days. 4.5% (A) and 7.6% (B) of index-months had a last trading day that was not the last weekday of the month |
| Missing data | A vendor gap is indistinguishable from a holiday and is treated the same way (declared). Two misprint/stale-feed rules removed 1 spike and 13 stale closes in B, none in A |
| Different calendars | Each index uses its own trading days and its own month end; P&L is in the index's own currency (FX translation not modelled) |
| Partial trading days | Treated as full days (closes only; half-days cannot be identified) |
| Spread | Full spread 2 bps (major CFDs), 5 bps (minor), 10 bps (others); half paid per fill |
| Commission | None (index CFDs are spread-only at the modelled broker) |
| Slippage | 1 bp per fill |
| Financing | Long: (policy rate + 2.5%) / 360 per calendar day held. Not held where the rate is unknown, stale (> 7 days) or above 25% |
| Shorts | None: the rule is long-only, so short financing and short dividends are zero |
| Dividends | Not credited to longs on price-return indices (conservative). US500 (S&P 500 TR) and GER40 (DAX) are total-return series and include them |

**Information available at the time.** The rule reads **no price at all**, only the calendar
(`test_turn_of_the_month_reads_the_calendar_only_and_covers_days_minus_one_to_plus_three`
changes every price and gets identical positions).

The one thing it must know in advance is which day is the second-to-last trading day of the
month. That is the exchange holiday calendar, which is published ahead. The backtest takes it
from the data, so an unannounced vendor gap would shift a window. That is a data imperfection,
not look-ahead in the signal. **No price, return, volatility or rate enters a decision.**

## 2. Where the +1.87% (B) and +2.59% (A) come from

### Annual components (bps of equity a year)

| | Gross price | Spread | Slippage | Commission | Benchmark financing | Markup | Dividends | **Net** |
|---|---|---|---|---|---|---|---|---|
| A 1990–2020 | +417.7 | −32.0 | −22.3 | 0 | −54.6 | −47.3 | 0 | **+261.5** |
| A before 2009 | +532.8 | −30.6 | −21.6 | 0 | −80.8 | −45.7 | 0 | +354.1 |
| A from 2009 | +235.5 | −34.2 | −23.4 | 0 | −13.2 | −49.8 | 0 | +114.8 |
| B 1990–2026 | +382.4 | −74.0 | −18.5 | 0 | −63.5 | −39.5 | 0 | **+186.9** |
| B before 2009 | +411.0 | −53.4 | −13.2 | 0 | −67.6 | −27.9 | 0 | +248.9 |
| B from 2009 | +351.9 | −96.1 | −24.2 | 0 | −59.0 | −52.0 | 0 | +120.6 |

### By index (sum of net over the period, fraction of equity)

- **A:** NAS100 +0.143, GER40 +0.128, HK50 +0.113, SWI20 +0.100, US500 +0.079, UK100 +0.077,
  CAN60 +0.073, FRA40 +0.070, AUS200 +0.029, JPN225 −0.002.
  - 9 of 10 positive.
  - The best index supplies **18%** of the total, the best 3 supply **48%**, the best 5 **70%**.
- **B:** KOR200 +0.090, AUT20 +0.087, MEX35 +0.073, BRA60 +0.071, BEL20 +0.069, ISR125 +0.061,
  NETH25 +0.060, NZL50 +0.058, ESP35 +0.041, US2000 +0.040, IND50 +0.034, ITA40 +0.022,
  IDN +0.018, EU50 −0.002, SWE30 −0.007, MYS30 −0.029.
  - 13 of 16 positive.
  - Best 1: **13%**, best 3: **36%**, best 5: **57%**.

**Leaving indices out (re-simulated):**

- **Any single index removed:** A stays at t 2.10–2.39, B at t 2.03–2.34.
- **Every pair removed:** 0 of 45 (A) and 0 of 120 (B) pairs leave a net ≤ 0. The worst pairs
  are NAS100 + HK50 (A: +1.77%, t 1.93) and KOR200 + NZL50 (B: +1.46%, t 1.87).
- **No one or two instruments carry the result.**

### By year

- 20 of 32 years positive (A) and 25 of 38 (B).
- The best year supplies 21% (A) and 17% (B); the **best 5 years supply 71%** (both).
- Since 2011 the record alternates: in A, 2011, 2013–2016, 2018 and 2019 are negative.

### By trade

- 56% of trades win (A and B).
- **The best 10% of trades supply 203% (A) and 252% (B) of the total net.** The other 90% lose
  money in aggregate. That is the profile of a small mean on fat-tailed equity moves: the result
  depends on a minority of large month-end rallies.

### By entry month (flag)

- **October windows (end of October to early November) supply 39% (A) and 45% (B) of the total
  net.**
  - The largest are 1998, 2000, 2001, 2008, 2020 and 2023.
  - Without every October window the net falls to +1.59% (A) and +1.03% (B) a year.
- July and August windows lose in both.

### By relative trading day (mean close-to-close return, bps, pooled over indices)

| Day | −5 | −4 | −3 | −2 | **−1** | **+1** | **+2** | **+3** | +4 | +5 | +6 | all other days |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| A before 2009 | 8.0 | 11.8 | 8.7 | 8.5 | **14.4** | **20.1** | **15.3** | **1.6** | −3.3 | 0.0 | −6.3 | 0.4 |
| A from 2009 | −2.5 | 12.1 | 9.5 | 3.7 | **−5.1** | **15.0** | **−1.3** | **9.2** | 2.2 | 3.9 | 2.4 | 3.8 |
| B before 2009 | 3.1 | 7.0 | 12.4 | 9.5 | **21.9** | **25.5** | **19.4** | **2.8** | 6.7 | 3.6 | −2.6 | 1.4 |
| B from 2009 | 1.0 | 5.3 | 5.8 | 5.5 | **−0.9** | **16.5** | **3.9** | **9.2** | 0.8 | 3.7 | 1.0 | 3.1 |

- **Entry day (−1).** It was the second-best day before 2009. It has been **negative** in both
  universes since.
- **Day +1** is the only window day still well above the drift since 2009: +11 bps (A), +13 bps
  (B).
- **Exit day (+3).** Weak before 2009 (+1.6 / +2.8), positive since.

## 3. Why it decayed after 2009: signal versus costs

### Change in annual net, before 2009 to from 2009 (bps a year)

| | Net change | Gross price | Spread + slippage | Benchmark | Markup |
|---|---|---|---|---|---|
| A | **−239** | **−297** | −5 | **+68** (rates fell) | −4 |
| B | **−128** | −59 | −54 | +9 | −24 |

### Per trade, per unit of notional (removes the effect of B gaining indices over time)

| | Gross | Spread + slippage | Financing |
|---|---|---|---|
| A before / from 2009 | 49.2 / **20.2** bps | 4.8 / 4.9 | 11.7 / **5.4** |
| B before / from 2009 | 62.9 / **29.1** bps | 10.1 / 10.0 | 14.5 / **9.2** |

**The deterioration is entirely gross signal decay.**

- Per-trade trading cost is constant by construction, and real retail spreads narrowed over the
  period, so the model if anything overstates modern costs.
- Financing per trade fell by about half with near-zero policy rates.
- B's higher annual costs from 2009 come from composition: more indices in the data (trades a year
  rose from 106 to 193), several of them 10 bp-spread markets.

### Separating the calendar effect from the equity drift (window days minus all other days)

| Five-year block | 1990 | 1995 | 2000 | 2005 | 2010 | 2015 | 2020 | 2025 |
|---|---|---|---|---|---|---|---|---|
| A, bps a day (t) | 11.0 (4.1) | 12.2 (3.9) | 18.7 (5.1) | 8.1 (2.4) | **1.7 (0.6)** | **−6.5 (−2.8)** | 18.9 (2.2; 2020 only) | — |
| B, bps a day (t) | 5.5 (1.2) | 20.4 (5.2) | 16.5 (5.4) | 18.5 (6.1) | 4.2 (1.8) | **−2.9 (−1.6)** | 5.1 (2.3) | 8.8 (2.1) |

**Explanations tested.**

| Explanation | Evidence | Reading |
|---|---|---|
| Calendar-effect decay (arbitrage, anticipation) | The excess fell from 8–19 bps to −7…+4 bps in 2010–2019. Day −1 turned negative while days −4/−3 stayed positive. The effect survives more in emerging B indices (B emerging from 2009: net t 1.29) than in developed ones (net t 0.45; majors t 0.41) | **Consistent:** the best-known, most liquid markets lost it first. This is post-hoc and cannot be confirmed on these data |
| Volatility | Windows entered above their own past median volatility gross 49 bps per trade (A) / 53 (B), against 24 / 30 below | Part of TOM is compensation for risk taken in turbulent months. The calm 2012–2019 period explains some of the weak decade |
| Central-bank regime | Trades entered with the benchmark below 1% gross 21 bps (A) / 10 (B), against 45 / 50 at ≥ 1% | Coincides with the post-2009 period, so it is not separable from time. It lowered financing, which helped the net |
| Financing changes | The benchmark cost fell 68 bps a year (A) | **Rules out** costs as the cause |
| Spread changes | Constant in the model; real spreads narrowed | **Rules out** costs as the cause |
| Market structure / ETF / index composition / algorithmic trading | No point-in-time constituent, flow or order-book data here | **Untested.** The anticipation pattern above is the only observable trace |
| Index-specific | Per-index gross per trade fell in 19 of 26 indices; US500 stayed at 34 bps. It rose in NAS100 (50 → 53), JPN225 and 5 B indices (IND50, ISR125, MYS30, NZL50, SWE30). The US post-2009 gross is the strong US drift (other days 3.8 bps a day) | Not one index; broad |

## 4. Cost sensitivity (the rule unchanged; every cost × k)

| Cost × | A CAGR | A Sharpe | A t | A max DD | A PF | A from 2009 (annual, t) | B CAGR | B Sharpe | B t | B max DD | B PF | B from 2009 (annual, t) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | +2.46% | 0.40 | 2.24 | 21.8% | 1.28 | +1.06%, 0.58 | +1.76% | 0.36 | 2.18 | 22.1% | 1.23 | +1.17%, 0.81 |
| 1.25 | +2.20% | 0.36 | 2.02 | 23.6% | 1.25 | +0.79%, 0.43 | +1.43% | 0.30 | 1.79 | 25.1% | 1.18 | +0.74%, 0.51 |
| 1.5 | +1.94% | 0.32 | 1.80 | 25.4% | 1.22 | +0.52%, 0.28 | +1.09% | 0.23 | 1.41 | 28.0% | 1.14 | +0.31%, 0.21 |
| 2 | +1.43% | 0.25 | 1.36 | 28.9% | 1.17 | **−0.02%**, −0.01 | +0.43% | 0.11 | 0.64 | 35.7% | 1.06 | **−0.55%**, −0.39 |
| 3 | +0.40% | 0.09 | 0.49 | 35.5% | 1.06 | −1.09%, −0.59 | **−0.89%** | −0.15 | −0.90 | 49.9% | 0.92 | −2.27%, −1.58 |

**Break-even multiplier on all broker costs (full sample):** 3.6× (A), 2.4× (B). **From 2009, about
2×** in both.

## 5. Broker economics

**What the 2.5% markup is.** It is a declared assumption, not broker data: typical published
retail index-CFD financing is benchmark ± 2.5% a year (some brokers 2–3%). TradeLocker financing
tables are not read by this code (§11).

### What TOM actually spends (bps of equity a year, full sample)

| Line | A | B |
|---|---|---|
| Long benchmark financing | 54.6 | 63.5 |
| Long markup (2.5%) | 47.3 | 39.5 |
| Short financing | 0 (no shorts) | 0 |
| Spread | 32.0 | 74.0 |
| Commission | 0 | 0 |
| Slippage | 22.3 | 18.5 |
| **Total broker** (excluding the benchmark) | **101.6** | **132.0** |

- **Per trade, per unit:** financing 9.2 bps (A) and 11.1 bps (B), at 0.69 bp of markup per
  calendar day.
- **Mean benchmark rate paid while holding:** 2.9% (A), 4.0% (B).

### Maximum tolerable financing, where the expected net reaches zero

| | A | B |
|---|---|---|
| Full sample: break-even markup | 16.3% | 14.3% |
| Full sample: all-in rate (break-even markup + mean benchmark) | ≈ 19% | ≈ 18% |
| **From 2009: break-even markup** | **8.3%** | **8.3%** |

**Financing is not TOM's binding constraint**, because it holds notional only 6 calendar days a
month. The binding constraints are the decayed signal and, for minor indices, the spread (B pays
74 bps a year in spread, more than its markup).

## 6. Calendar neighbourhood (five variants fixed in the plan; nothing else run)

| Variant (k_pre, k_post) | A net | A t | A before the broker (t) | A from 2009 (t) | B net | B t | B before the broker (t) | B from 2009 (t) |
|---|---|---|---|---|---|---|---|---|
| **Original** (1, 3) | +2.59% | 2.24 | 3.12 | +1.06% (0.58) | +1.87% | 2.18 | 3.71 | +1.17% (0.81) |
| Entry one day earlier (2, 3) | +3.16% | 2.48 | 3.36 | +1.39% (0.71) | +2.27% | 2.43 | 3.94 | +1.62% (1.07) |
| Entry one day later (0, 3) | +2.12% | 1.93 | 2.77 | +1.77% (0.99) | +1.42% | 1.71 | 3.20 | +1.48% (1.07) |
| Exit one day earlier (1, 2) | +2.22% | 2.27 | 3.20 | +0.09% (0.06) | +1.61% | 2.16 | 3.82 | +0.30% (0.24) |
| Exit one day later (1, 4) | +2.32% | 1.86 | 2.76 | +1.22% (0.61) | +1.76% | 1.87 | 3.37 | +1.02% (0.64) |

- **All five are positive** on both universes, with t 1.71–2.48 net and 2.76–3.94 before the
  broker. **It is a region, not a magic date.**
- **No variant is significant from 2009 (t ≤ 1.07).**
- Entering one day earlier was best on both, and is registered as a forward-only hypothesis
  (TOM-F1). It is not adopted.

## 7. Index robustness (1990–2020, pooled; A has no data after 2020)

| Universe | Members | Net annual | t | From 2009 (annual, t) |
|---|---|---|---|---|
| All | 26 | +2.25% | 2.28 | +1.19%, 0.65 |
| Developed | 20 | +2.24% | 2.09 | +0.89%, 0.45 |
| **8 major CFDs** (US500, NAS100, JPN225, UK100, GER40, FRA40, AUS200, EU50) | 8 | +2.09% | 1.79 | **+0.81%, 0.41** |
| A only | 10 | +2.59% | 2.24 | +1.06%, 0.58 |
| B only | 16 | +2.04% | 2.19 | +1.27%, 0.69 |
| B developed | 10 | +1.89% | 1.79 | +0.72%, 0.33 |
| B emerging | 6 | +2.29% | 2.32 | **+2.19%, 1.29** |
| All 26 without one major (range) | 25 | +2.16% … +2.35% | 2.22 … 2.35 | +1.03% … +1.32%, 0.56 … 0.71 |

- TOM is a broad calendar phenomenon, not one or two special indices: no major's removal moves t
  outside 2.22–2.35.
- But on the **majors the bot would actually trade, the post-2009 net is +0.81% a year at t 0.41.**
- The only modern residue is in emerging indices, which are rarely offered as retail CFDs and
  carry the widest spreads.

## 8. Portfolio construction

| | A equal | A inverse-vol | B equal | B inverse-vol |
|---|---|---|---|---|
| Net annual | +2.59% | +2.48% | +1.87% | +1.75% |
| t | 2.24 | 2.29 | 2.18 | 2.23 |
| Sharpe | 0.40 | 0.41 | 0.36 | 0.37 |
| Max DD | 21.8% | 22.0% | 22.1% | **18.8%** |
| Turnover | 22.3× | 22.6× | 18.5× | 18.7× |
| Financing | −1.02% | −1.05% | −1.03% | −1.01% |
| From 2009 (t) | 0.58 | 0.52 | 0.81 | 0.93 |

Volatility normalisation changes Sharpe by +0.01, with the same turnover and financing. **Not
material.** Equal weight stays.

## 9. Holding-time economics

| Measure | A | B |
|---|---|---|
| Mean / median holding | 4.0 / 4 trading days; 6.1 / 6 calendar days | same |
| Exposure days per index a year | 68.1 | 56.9 |
| Financing per trade per unit | 9.2 bps | 11.1 bps |
| Total cost per trade per unit (spread, slippage, financing): before 2009 / from 2009 | 16.5 / 10.3 bps | 24.6 / 19.2 bps |
| Gross per window day: before 2009 | 12.9 bps | 17.4 bps |
| Gross per window day: from 2009 | 4.5 bps, of which 3.8 is drift | 7.2 bps, of which 3.1 is drift |

**Can less exposure help?** From 2009 only day +1 clearly beats the drift (+11 / +13 bps). A
one-day hold still pays a full round trip (4–20 bps) plus 1–3 calendar days of financing. It is
registered as a forward-only hypothesis (TOM-F2), not adopted. Its expected excess is about the
size of its cost.

## 10. Out-of-sample discipline

- **Nothing was re-tuned.** Every headline is the frozen rule.
- **Both data sets were already used.** TOM-D is registered as descriptive with 0 tests. Universe
  B's seal was already spent, and A after 2020 was not loaded.
- **The two variants that looked better** (TOM-F1 enter a day earlier; TOM-F2 day +1 only) are
  registered **for forward data only** (`research/preregistrations/TOM-F.md`, trial `TOM-F`).
  They come with a control, a t threshold and a stated power: about t 0.6 after 120 months at
  Sharpe 0.2. They are a record, not a promise.

## 11. Can it be executed through the target account? (as the code stands)

| Requirement | Current state | What it would take |
|---|---|---|
| Index CFDs as instruments | `canonical_symbol` resolves only currency/metal pairs. US500 and NAS100 resolve to None; the client falls back to the raw name | An index symbol table per broker (US500, GER40, …) with explicit identity, failing closed when unknown |
| Contract sizes, min lot, tick value | `adapter.spec()` reads contract size, tick size and value generically: usable | Verify per index on the demo account |
| Sizing by notional | The risk engine sizes from the stop distance (0.5% risk). TOM sizes 1/N of equity notional | Notional sizing would have to remain **inside** the engine, e.g. a protective stop at 10% (hit by 0.3% of trades on closes; 5%: 3.6–3.9%; 3%: 11–12%) so that risk-based sizing reproduces about 1/N notional. Not a new sizing authority |
| Stop and target | The engine requires both, with reward/risk ≥ 1.2. TOM has a calendar exit and no target | A time-exit decision type the engine understands, without relaxing the stop requirement |
| Cost check | `cost_to_risk` uses FX pip constants (`pip_size`, commission 0.7 pip) | An index cost model (spread in points, no pip commission) |
| Position limits | `max_open_positions` 3; currency limits parse `instrument[:3]/[3:]`, which is meaningless for "US500" | 8–26 simultaneous positions would need a deliberate, reviewed limit change plus an index-aware correlation limit |
| Market hours, holidays, half days | None for indices | Per-exchange holiday calendars (the rule needs the last trading day known in advance), session times, half-day handling |
| Overnight financing | Not read from TradeLocker | Read the broker's swap/financing table per index and charge it in paper fills |

**Feasible in principle, not now.** It would take several weeks of engineering across the symbol,
risk and execution layers. That is not justified by a verdict-B edge, and no fake implementation
was added.

## 12. AI

No LLM was added. There is no current deterministic edge for it to improve: the calendar excess
since 2009 is about zero on the major indices.

## 13. Final verdict

**B. WEAK PROMISING EDGE: interesting but insufficient economics.**

**Why not the other categories.**

- **Not A (strong).** The post-2009 net is +1.06% (A) / +1.17% (B) a year at t 0.58 / 0.81, with
  P(mean ≤ 0) of 56% / 41%. On the 8 major CFDs it is +0.81% at t 0.41. Doubling costs makes it
  zero or negative. Expected return about 1% a year with drawdowns above 20%: that is not
  economically meaningful for this account.
- **Not D (artifact).** It passes every robustness and concentration test:
  - 9/10 and 13/16 indices positive;
  - no pair removal kills it;
  - all 5 calendar variants positive;
  - before 2009, window days beat other days at t 7.6–8.9.
- **Not C (cost-destroyed).**
  - Costs per trade did not rise and financing fell.
  - Break-even is 2.4–3.6× costs over the full sample.
  - What disappeared is the gross calendar excess itself.
  - The remaining modern calendar excess (2.6 / 16 bps per trade) is smaller than retail cost per
    trade (10 / 19 bps). That is a cost-destroyed residue on top of a decayed signal.
- **Not E.** The account could be made to trade it with the engineering in §11. The economics do
  not justify building it.

**Answer to the central question.** +1.87% is **mostly a weak, decaying statistical effect**:

- a turn-of-month calendar premium that was real and broad until about 2008, and has since
  vanished in developed markets;
- plus ordinary equity drift collected 23–27% of the time.

It is not a genuinely useful edge for this retail CFD bot today.

**What would change the verdict (no waiting implied):**

- an instrument with roughly a third of the per-trade cost (index futures: about 1–2 bps round
  trip, no markup). The full-sample "before broker" t is 3.1 / 3.7;
- or forward evidence (TOM-F) that the calendar excess over the drift has returned in developed
  indices.

## Tests and commit

- Full suite: **726 passed, 0 failed**.
- Mutation audit: **152 of 152 killed**, including 3 new guards: the ledger's markup split, the
  break-even arithmetic, and the inverse-volatility weights reading only past closes.
- **Registry:** TOM-D (descriptive, 0 tests) and TOM-F (forward-only hypotheses, judged after 120
  forward months).
