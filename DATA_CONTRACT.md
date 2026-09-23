# Data contract

Data is the foundation that every other layer inherits errors from. A wrong
timestamp or a wrong price scale does not raise an error; it produces a
complete, normal-looking result that measures nothing. This contract exists
to make such errors visible.

---

## 1. Requirements

All data must be:

- **timestamped**, with a documented convention;
- **versioned**, so that the exact data behind a result can be identified;
- **auditable**, with its origin and every transformation recorded;
- **reproducible**, so the same inputs always produce the same dataset.

## 2. Required metadata

Every dataset and every record carries, or can be traced to:

| Field | Meaning |
|---|---|
| Source | where it came from (provider, endpoint or file) and under what licence |
| Timestamp | the moment the value describes, in UTC |
| Availability time | the moment the value could first have been known (for a bar, its **close**) |
| Instrument | the broker's symbol and the canonical symbol |
| Timeframe | the bar period, or "tick" or "quote" |
| Availability | where the data exists and where it does not: gaps, sessions, closures |
| Data quality | validation results and flags |
| Version | an identifier or content hash of the dataset |

## 3. Time

- All timestamps are stored in **UTC**. The source's own clock (for example
  a broker server clock that follows another zone's daylight saving) is
  identified, **measured rather than assumed**, and converted.
- A bar is labelled by its **open** time and becomes **available at its
  close**. Mixing these up is a one-bar look-ahead leak.
- A bar that is still forming is never treated as closed.
- Resampling (for example building H4 from H1) only emits **complete**
  higher-timeframe bars.

## 4. Forbidden: inventing data

The following may **never be invented** when they are not genuinely
available:

- volume (spot FX has no centralised volume; tick counts are not volume and
  are labelled as tick counts);
- order-book depth;
- news;
- sentiment;
- swap / financing rates;
- spread;
- liquidity.

When a quantity is needed but not available historically, there are only
two honest options:

1. **do without it**, and state that it is missing; or
2. use a **declared approximation**, when it is scientifically justified.
   The approximation is written down, versioned, marked as an
   approximation in every result that uses it, and tested with pessimistic
   values as well.

A gap is never filled by interpolation, forward-filling or a default, for
anything a model or the risk engine will read.

## 5. Validation

Before use, data is checked for: duplicates, out-of-order timestamps, gaps
(against the instrument's trading calendar), impossible prices
(high < low, non-positive values, spikes beyond a plausible bound), price
scale (the divisor from raw to real prices must be unambiguous, or the load
fails), timezone consistency, and stale or frozen feeds.

Failures are reported per instrument in a **data-quality report**. Data
that fails validation is excluded or flagged, never silently repaired.

## 6. The future-information rule

> **A decision at time T may only use information that was genuinely
> available at or before time T.**

For data this means: no revised values presented as if they were known
earlier, no statistics over periods that end after T, no use of the
current constituent list of anything for past dates (survivorship), and no
external data (news, calendars, sentiment) unless its historical
availability time is known.

## 7. What is known today about available data

Recorded so that Phase 1 starts from facts rather than hopes.

- **The predecessor project's research dataset**: a public OHLC dataset
  (ejtraderLabs/historical-data) covering **2012-11 → 2022-03** for 11 FX
  pairs and XAUUSD, at M15, M30, H1, H4 and D1, with **tick volume only**,
  in broker server time. It has **no spread history, no swap history and no
  order book**. It has already been used heavily for research, so it is
  **not unseen** ([docs/HISTORICAL_ARCHIVE.md](docs/HISTORICAL_ARCHIVE.md)).
- **Broker history** (TradeLocker) is available through the broker API
  for the account's symbols. Its depth must be measured, not assumed. The
  predecessor sealed its history from **2022-04-01** onward as an unused
  holdout.
- **Live quotes** provide real bid/ask spreads going forward only.

**The long-history goal.** The owner's goal is to train on about twenty
years of market history. That much history does not exist in the data
described above, which covers under ten years. Phase 1 therefore begins
with a sourcing study: which providers have longer histories, at what
resolution, with what quality and licence, and whether they include real
bid/ask. The study reports the years that genuinely exist per instrument.
It does not assume twenty. Longer history is valuable for covering more
regimes, but older data can also describe a market structure that no
longer exists, and the validation design must allow for that.

## 8. Storage and versioning

Raw data is stored immutably. Every derived dataset records the raw
version and the transformation version it came from. Large data files are
not committed to Git; their versions and hashes are.
