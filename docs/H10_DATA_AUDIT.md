# H.10 data audit: Federal Reserve daily exchange rates for RV-1 (DATA AUDIT ONLY)

**This is an audit only. Nothing else was computed:**

- no RV-1 hypothesis, registration, signal, IC, portfolio or trading result;
- no value dated on or after 2017-01-01 was read; only the existence of later rows is counted;
- no change to the live trading system.

| | |
|---|---|
| Reproduce | `python scripts/h10_audit.py fetch` then `python scripts/h10_audit.py audit` |
| Every number below | `data/h10/manifest.json` |
| Loader | `aitrader/data/h10.py` |
| Tests | `tests/unit/test_h10.py` |
| Raw files | kept unmodified under `data/h10/`, not committed |

## Verdict: **SUFFICIENT FOR RV-1**, on the conditions in the last section

## 1. Source and provenance

**The chain of custody:**

1. **Publisher.** Board of Governors of the Federal Reserve System, statistical release **H.10**:
   noon buying rates in New York for cable transfers payable in foreign currencies.
2. **Redistributor.** **FRED** (Federal Reserve Bank of St. Louis), category 158 "Daily Rates".
   The series are DEXUSEU, DEXUSUK, DEXUSAL, DEXUSNZ (USD per unit) and DEXJPUS, DEXSZUS, DEXCAUS
   (units per USD).
3. **Mirror.** `github.com/datasets/exchange-rates`, the datahub "core" dataset, licence ODC-PDDL.
   A script in that repository downloads the FRED series and writes `data/daily.csv`.
   - A GitHub Action has re-run it daily since 2026-03.
   - The scripts and their full git history are public. The series ids and every transformation
     were read from the scripts at each commit used.

**The official endpoints cannot be reached from this environment.** fred.stlouisfed.org,
api.stlouisfed.org, alfred.stlouisfed.org, federalreserve.gov (H.10 pages and the Data Download
Program) and newyorkfed.org are all refused by the network policy (checked 2026-10-01).

**The mirror is therefore not treated as authoritative.** Instead it is:

1. used only at **pinned commits**, through immutable URLs;
2. **un-transformed** with its own documented code;
3. **verified** by four independent means:
   - exact recovery of the published decimal grid (§3);
   - agreement across three vintages written years apart (§6);
   - reconciliation with independent bid/ask data (§10);
   - triangulation with two other instruments (§10).

**Mirror defects found.**

- **Rounding.** The mirror stores EUR, GBP, AUD and NZD **inverted** (units per USD). The current
  vintage also **rounds the inverse to 4 decimals**, which loses the official value.
- **README.** The README states the opposite of what the files hold. The scripts and the data are
  authoritative; the README is wrong.

## 2. Files

| Vintage (mirror commit) | Immutable URL | sha256 | Bytes | Storage of EUR/GBP/AUD/NZD |
|---|---|---|---|---|
| 2017-12-08 (`4eb22d3e74d9…`) | `raw.githubusercontent.com/datasets/exchange-rates/4eb22d3e74d92fa1b37f98854fcaab3feccad055/data/daily.csv` | `7d421ce778bf364f9e10154215147a9dd0bdcf1c2ebcad4427f5f1d69d9514c9` | 1,888,584 | `round(1/x, 4)`, wide format |
| **2018-10-17 (`8a6dec28a0af…`), PRIMARY** | `…/8a6dec28a0affdf7eaf455a43be8db862fd9aa09/data/daily.csv` | `0791b898faf23541d0dea5038bd5634f7df42f52e0dd776a1be26672bfa9fb77` | 6,887,034 | **`str(1/x)` at full float precision** |
| 2026-09-29 (`0947c2304370…`) | `…/0947c2304370a5a4dd8db74cdacb8486e7d85cbe/data/daily.csv` | `944c4937703177bdc5e82ced55b6e50ffcd1f89fef4bbca29785ac7cce8bd6c4` | 7,636,183 | `round(1/x, 4)`, long format |

- Each downloaded file is byte-identical to the same commit in a git clone of the mirror.
- Each file contains exactly one row per (currency, date); no duplicates.

## 3. Transformation undone, and verified

- In the primary vintage, the official FRED value is **1/x** for EUR, GBP, AUD and NZD, and **x**
  for JPY, CHF and CAD.
- Every recovered value 1999-01-04 → 2016-12-30 lies on FRED's published grid (4 decimals; JPY 2)
  to within 10⁻⁶ of a grid unit: **4,524 of 4,524 per currency, 0 off the grid.**
- An exact inverse of a published 4-decimal number can do this; a rounded or altered file cannot.
- The loader **refuses** any off-grid value, so a rounded vintage can never be loaded as the
  primary.

## 4. Coverage

USD is the numeraire: every series is quoted against it.

| Currency | FRED series (pair) | First valid | Last valid, primary vintage | Last valid, 2026 vintage |
|---|---|---|---|---|
| EUR | DEXUSEU (EURUSD) | **1999-01-04** | 2018-10-12 | 2026-09-25 |
| GBP | DEXUSUK (GBPUSD) | 1971-01-04 | 2018-10-12 | 2026-09-25 |
| AUD | DEXUSAL (AUDUSD) | 1971-01-04 | 2018-10-12 | 2026-09-25 |
| NZD | DEXUSNZ (NZDUSD) | 1971-01-04 | 2018-10-12 | 2026-09-25 |
| JPY | DEXJPUS (USDJPY) | 1971-01-04 | 2018-10-12 | 2026-09-25 |
| CHF | DEXSZUS (USDCHF) | 1971-01-04 | 2018-10-12 | 2026-09-25 |
| CAD | DEXCAUS (USDCAD) | 1971-01-04 | 2018-10-12 | 2026-09-25 |

- **EUR exists from 1999-01-04 only.** The mirror has no daily legacy currencies such as DEM, so
  an eight-currency cross-section begins on 1999-01-04.
- **1999-01-04 → 2016-12-30:** 4,695 weekdays, every one present as a row in every series. A day
  without a rate is an empty value, never a missing row.
- The primary vintage holds 447 rows per currency on or after the holdout start. They were
  counted, not read; the loader seals them.

## 5. Missing dates, holidays, duplicates

**Duplicates:** none.

**No-rate days, 1999–2016.** 171 weekdays have no rate in **all seven** series at once, and no
weekday is missing in only some of them. All 171 are explained by the observed calendar
(`aitrader/data/h10.fed_holidays`):

- Federal Reserve holidays; a Sunday holiday moves to Monday.
- **Fridays before a Saturday holiday have no rate from 2010 onward:**

  | Friday | Rate on H.10? |
  |---|---|
  | 1999-12-24, 1999-12-31 | yes |
  | 2004-12-24, 2004-12-31 | yes |
  | 2000-11-10, 2006-11-10 | yes |
  | 2009-07-03 | yes |
  | 2010-12-24, 2010-12-31 | **no** |
  | 2015-07-03 | **no** |

  This is consistent with certification moving to the Board, which follows the federal schedule
  rather than the Reserve Banks'. The cause is inferred; the rule is observed.
- Two special closures: **2001-09-11** (the attacks) and **2014-12-26** (federal closure by
  executive order).

**Carried-forward values.** On three federal holidays in 2007 (09-03, 10-08, 11-22), FRED shows a
value for every currency, and **every one equals the previous business day's rate**. These are
copies, not observations. The loader drops any value on a no-rate day.

## 6. Revisions and backfills

| Comparison | Values compared per currency (1999–2016) | Different |
|---|---|---|
| 2018-10-17 vs 2017-12-08 | 4,524 | **0** (all seven) |
| 2018-10-17 vs 2026-09-29 | 4,524 | **0** (all seven) |

- The rounded vintages are compared through the mirror's own rounding.
- **Limit:** this detects revisions between December 2017 and September 2026 only. ALFRED's
  vintages, which would show earlier ones, are unreachable.
- The independent reconciliation (§10) bounds any error that does exist.

## 7. Timestamp and timezone

H.10 describes its rates as **noon New York (12:00 ET)**. This was tested, not assumed.

**Method.** For each H.10 date, the H.10 value was compared with the Dukascopy bid/ask mid at the
close of each 15-minute bar from 07:00 to 17:00 New York, 2008–2016.

**Result.** The median absolute difference is smallest at exactly **12:00** for every currency
and **every year**, 2008–2016. The one exception is AUD in 2008, whose Dukascopy series is
faulty (§10).

| Time (New York) | 11:00 | **12:00** | 13:00 | 17:00 |
|---|---|---|---|---|
| EUR median absolute difference (bp) | 8.1 | **0.58** | 6.6 | 11.3 |

**Off-noon fixings.** On a handful of dates, H.10 matches the market at another time of day, for
every currency at once (`third_source.days_three_or_more_currencies_over_20bp`):

| Date(s) | H.10 matches the market at |
|---|---|
| 2009-07-28, 2009-08-18, 2009-08-25, 2010-06-24, 2010-07-08 | about 09:15 New York |
| 2010-06-23 | about 16:00 New York |
| 2008-10-24, 2010-01-26, 2010-01-28, 2010-04-13 | mixed morning times |

- These are genuine timing irregularities in the published rates: about 6–14 days of 2,258 per
  currency.
- They are documented and **not corrected**.

## 8. Point in time, and the 17:00 New York decision

**When is the value known?**

- The rate is a sample of the market at noon. The market price was observable to any participant
  at noon.
- The certified figure's own publication time cannot be verified from here.

**Rule (the loader's `available_at`).** The rate dated *t* is used only from **17:00 New York on
the next business day** after *t*: a weekday that is not a no-rate day. This is conservative by
up to one business day.

**Is the 17:00 New York decision timing defensible?** Yes, under this rule.

- A decision at 17:00 New York on day *t*+1 uses the rate of *t* and earlier, never the rate of
  *t*+1.
- Any forward return must be measured from a **later** fixing: the first fixing after the decision
  is noon of *t*+2. It is never measured from the fixing the decision used.
- The comparison in §10 shows why the timing matters:
  - H.10 daily returns correlate **0.996–0.998** with noon-to-noon market returns;
  - they correlate only **0.78–0.88** with 17:00-to-17:00 returns.
  - Mixing the two clocks would add noise. Using a fixing before its time would add look-ahead.

## 9. Currency definitions and discontinuities

**Currency definitions.** No currency changed definition 1999–2016. The euro begins on 1999-01-04;
no synthetic pre-euro series is used or available.

**Large moves.** Every daily move of 4% or more, 1999–2016, falls on a known market event:

| Event | Date(s) | Currencies |
|---|---|---|
| Financial crisis | 2008-10/11/12 | several |
| Fed QE announcement | 2009-03-19 | several |
| SNB minimum rate introduced | 2011-09-06 | CHF +8.9% |
| SNB floor removed | 2015-01-15 and 01-16 | CHF −13.0% and −5.1% |
| Brexit vote | 2016-06-24 | GBP −8.2% |
| — | 2007-08-16, 2000-01-28 | AUD, NZD |

No jump looks like a quote flip or a scaling error. The largest move in any series is CHF's 13%.

**Unchanged days.** A day equal to the previous rate occurs 29–44 times per currency in 4,500 days.

- At 4-decimal resolution, with typical daily moves of about 60 ticks, chance predicts about 30.
- The only run of 3 or more is NZD 0.6717 on 2004-01-05 to 01-07, while AUD, EUR and JPY moved.
  Chance predicts about 1.4 such runs across seven series, so it is **flagged, not classified as a
  defect**.

**JPY policy rate.** The BIS series used by `aitrader/data/rates.py`, under its staleness rule, has
no Japanese policy **rate**:

| Gap | Weekdays | Context |
|---|---|---|
| 1999-02-19 → 2000-08-10 | 385 | zero-rate policy |
| 2001-03-26 → 2006-03-08 | 1,293 | quantitative easing: a reserves target, not a rate |
| 2013-04-11 → 2016-09-20 | 899 | QQE |

- That is **2,577 of 4,695 weekdays**.
- All other currencies, and USD, have a policy rate on every weekday 1999–2016. EUR's starts on
  1999-01-01.
- Nothing may be filled. **RV-1's carry signal must state in advance how a currency without a
  rate is treated.** Excluding JPY from the carry ranking would remove the classic funding
  currency for most of 2001–2006.

## 10. Cross-source validation, 2008-01-02 → 2016-12-30 (prices only)

**Method.**

- **H.10:** the primary vintage, official values, in the pair's market quote.
- **Dukascopy:** the repository's M15 bid/ask bars (`DataStore`, holdout-truncated). The mid is
  taken at the close of the bar ending at the stated New York time, and only a bar closing exactly
  then is used.
- **Statistics, per currency:**
  - the level difference in bp, 1e4·ln(H.10 / mid);
  - the timing scan (§7);
  - daily returns: H.10 against noon-to-noon and 17:00-to-17:00 mids;
  - weekly returns: each ISO week's last H.10 date;
  - currency values relative to the eight-currency mean (USD = 0), weekly change.
- **Third source:** AUD, EUR and GBP against the pair **implied** by two other Dukascopy
  instruments, CCYJPY / USDJPY at noon.
- No signal, ranking, portfolio or trading statistic was computed.

| Currency | H.10 dates | Best time | Level median (signed / abs, bp) | p95 abs (bp) | Days > 20 bp | Daily corr vs noon / vs 17:00 | Weekly corr | Weekly RMS diff (bp) |
|---|---|---|---|---|---|---|---|---|
| EUR | 2,258 | 12:00 | +0.54 / 0.58 | 2.1 | 8 | 0.9975 / 0.835 | 0.99995 | 1.5 |
| GBP | 2,258 | 12:00 | +0.69 / 0.72 | 2.1 | 9 | 0.9964 / 0.877 | 0.9982 | 9.1 |
| JPY | 2,258 | 12:00 | −0.61 / 0.64 | 1.7 | 6 | 0.9956 / 0.838 | 0.9977 | 10.8 |
| CHF | 2,258 | 12:00 | −0.94 / 0.96 | 2.4 | 6 | 0.9982 / 0.845 | 0.9992 | 7.2 |
| CAD | 2,258 | 12:00 | −0.72 / 0.75 | 2.3 | 10 | 0.9975 / 0.777 | 0.99994 | 1.6 |
| NZD | 2,258 | 12:00 | +1.72 / 1.74 | 6.0 | 14 | 0.9978 / 0.797 | 0.9996 | 5.7 |
| AUD | 2,258 | 12:00 * | +0.95 / 1.07 | **26.6** | **139** | 0.9776 / 0.799 | 0.9974 | 14.7 |

Currency values relative to the eight-currency mean, weekly changes over 459 weeks, correlation
H.10 vs Dukascopy: AUD 0.9954, CAD 0.9997, CHF 0.9985, EUR 0.9996, GBP 0.9960, JPY 0.9982,
NZD 0.9989, **USD 0.9998**.

**Do returns reconcile?** Yes.

- Daily returns: 0.996–0.998 against the noon market price.
- Weekly returns: 0.9977–0.99995.
- The relative-value series RV-1 would use: 0.995–0.9998.

**Is there a systematic difference?** Yes, a small one.

- H.10 values the foreign currency slightly **higher** than the bid/ask mid, in every pair: +0.5
  to +1.7 bp.
  - For XXXUSD pairs (EUR, GBP, AUD, NZD), H.10 is above the mid.
  - For USDXXX pairs (JPY, CHF, CAD), H.10 is below it.
- That is a near-constant offset of about half a spread, consistent with a "buying rate". It
  cancels out of returns.

**Are the differences caused by fixing time?**

- The differences shrink to a minimum at exactly noon, every year.
- Moving the market clock by one hour multiplies them about tenfold.
- The few large differences are the off-noon fixings of §7.

**\* AUD: the fault is in the repository's Dukascopy AUDUSD, not in H.10.**

| AUD, median absolute difference (bp) | 2008 | 2009 | 2010–2016 |
|---|---|---|---|
| H.10 vs the AUDJPY/USDJPY implied rate | 1.24 | 1.58 | 0.8–1.3 |
| Dukascopy AUDUSD vs that same implied rate | **7.08** | 0.99 | 0.10–0.24 |

- Month by month, Dukascopy's AUDUSD departs from its own AUDJPY/USDJPY in 2008-01 → 2008-09 and
  2009-04 → 2009-09 (monthly medians 7–30 bp; maxima about 140 bp).
- In exactly those months it also departs from H.10, by the same amount.
- **This is a defect in the bar data that the earlier research rounds traded.** It is reported
  here; it is outside this audit's scope to repair.

## 11. Limitations

1. **No direct access to the official files.** The data is a third-party redistribution, verified
   rather than trusted.
   - If the official FRED or Board CSVs can be supplied, they can be byte-compared against the
     recovered values and would replace the mirror.
2. **Revisions before December 2017 cannot be detected.** ALFRED is unreachable.
3. **1999–2007 has no second source.** The repository's bid/ask bars start in 2007-03. That period
   relies on:
   - the same publisher and process;
   - the exact-grid check;
   - the vintage agreement;
   - every no-rate day being explained;
   - every large move being a known event.
4. **Mid-market only.** H.10 has no bid/ask, so it measures information, not tradable cost. Costs
   for any later stage must come from measured spreads (2008 onward).
5. **Noon timing,** with about 0.3–0.6% of days fixed at another time (§7).
6. **JPY has no policy rate** for 2,577 of 4,695 weekdays (§9).

## Conditions for RV-1

1. **The data.** Use only the primary vintage through `H10Store`:
   - sha-verified;
   - exact-grid checked;
   - no-rate days and carried copies dropped;
   - holdout-sealed.

   The 2026 vintage is for revision checks only.
2. **Point in time.** A rate is usable from 17:00 New York on the next business day. Forward
   returns start at a later fixing.
3. **No repairs.** Do not repair the off-noon fixings or the NZD 2004 run. If they matter, the
   preregistration states a rule in advance.
4. **JPY carry.** The preregistration must state how JPY is treated in the carry signal while it
   has no policy rate. It may not be filled.
5. **The euro.** The eight-currency cross-section starts on 1999-01-04, and later where a
   lookback requires it.
6. **Dukascopy AUDUSD.** Do not use the 2008–2009 Dukascopy AUDUSD for any purpose that depends on
   its level.
