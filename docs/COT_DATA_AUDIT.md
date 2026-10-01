# COT data audit: CFTC Traders in Financial Futures (TFF), Futures-Only

**This is a DATA AUDIT ONLY.**

- No hypothesis has been written or run.
- No threshold has been chosen.
- Round 5 has not started.
- Every figure below is recomputed from the raw bytes by `scripts/cot_audit.py` and recorded in
  `data/cot/manifest.json`.
- The raw files are kept unmodified under `data/cot/` and are not committed.

## 1. Files

| ZIP (as supplied) | ZIP sha256 | Member | Member sha256 | Rows | As-of range |
|---|---|---|---|---|---|
| `fin_fut_txt_2006_2016.zip` (3,166,765 B) | `c3a8d01765133a24ce9c082de88933816497d06f1b03eec8c53750bdd818f14b` | `F_TFF_2006_2016.txt` (15,955,914 B, 2017-01-17) | `8b4bda8edd8e3524bcd192a22cd9332d38f69dcc5f580c84f52d19902e8d53d8` | 18,911 | 2006-06-13 → 2016-12-27 |
| `fut_fin_txt_2017.zip` (395,830 B) | `e6e2dd537efcc57cdd6cdcc4e45e567fd47e65d8afc8369d8383bf09195ae7f5` | `FinFutYY.txt` (1,641,420 B, 2017-12-28) | `1b4c732fa66be12acbb1c70234f2c46a1d8567d053c4f140f8aff0866cfd404d` | 2,110 | 2017-01-03 → 2017-12-26 |

**Integrity checks:**

- Each ZIP passes `testzip` and contains exactly one member.
- The extracted copies under `data/cot/extracted/` are byte-identical to the ZIP members.
- Both files have the same 87 columns.

## 2. Is it TFF Futures-Only?

**Yes.** `FutOnly_or_Combined` is `FutOnly` on every row of both files. The columns are the TFF
categories: Dealer, Asset Manager, Leveraged Money, Other Reportable and Non-reportable.

## 3. Date field

`As_of_Date_In_Form_YYMMDD` is authoritative.

`Report_Date_as_YYYY-MM-DD` mixes two formats (`YYYY-MM-DD` and `M/D/YYYY 12:00:00 AM`). Once
parsed, it agrees with the YYMMDD field on every FX row.

**The files contain no release date.**

## 4. FX contracts found and coverage

| Currency | Code | Market | First as-of | Last as-of | Reports | Judged period* | Usable in judged period | Holdout (2017) |
|---|---|---|---|---|---|---|---|---|
| EUR | 099741 | EURO FX – CME | 2006-06-13 | 2017-12-26 | 603 | 442 | 429 | 52 |
| JPY | 097741 | JAPANESE YEN – CME | 2006-06-13 | 2017-12-26 | 603 | 442 | 429 | 52 |
| GBP | 096742 | BRITISH POUND STERLING – CME | 2006-06-13 | 2017-12-26 | 603 | 442 | 429 | 52 |
| CHF | 092741 | SWISS FRANC – CME | 2006-06-13 | 2017-12-26 | 603 | 442 | 429 | 52 |
| CAD | 090741 | CANADIAN DOLLAR – CME | 2006-06-13 | 2017-12-26 | 603 | 442 | 429 | 52 |
| AUD | 232741 | AUSTRALIAN DOLLAR – CME | 2006-06-13 | 2017-12-26 | 603 | 442 | 429 | 52 |
| NZD | 112741 | NEW ZEALAND DOLLAR – CME | 2006-06-13 | 2017-12-26 | **600** | 442 | 429 | 52 |
| USD index | 098662 | U.S. DOLLAR INDEX – ICE | 2006-06-13 | 2017-12-26 | 603 | 442 | 429 | 52 |

\* The judged period is 2008-07-11 → 2017-01-01. "Usable" excludes the 13 reports from the 2013
shutdown (§6).

**The filename is not the coverage.** All the data starts on **2006-06-13**, the first TFF
report, not at the start of 2006.

**Cross-rate futures are not usable:**

| Contract | Coverage | Judged-period reports |
|---|---|---|
| EUR/GBP (CME) | 79 sparse reports, 2014-06-10 → 2017-12-26 | 38 |
| EUR/JPY (CME) | 6 reports, 2017 only | 0 |
| ICE small EUR/JPY | 2006–2007 only | 0 |
| ICE small EUR/GBP | 1 report | 0 |

## 5. Internal consistency (every FX row)

All of these hold on all 4,821 FX rows, with **zero exceptions**:

- **Total, long side:** total reportable longs + non-reportable longs = open interest.
- **Total, short side:** the same identity holds for shorts.
- **Categories:** the four categories' positions plus their spreads sum to total reportable, on
  each side.
- **Values:** no missing value and no negative value.
- **Duplicates:** no duplicate (contract, as-of) pair, and the two files do not overlap.

## 6. Missing periods and irregular weeks

- **NZD:** three early reports are absent: 2006-06-20, 2006-06-27 and 2006-07-03. They are
  recorded as missing and are not filled.
- **Holiday weeks:** every gap other than 7 days is a holiday week, where the as-of date moved off
  Tuesday. These are the 6- and 8-day gaps around:

  | Year | As-of dates moved |
  |---|---|
  | 2006 | 07-03 |
  | 2007 | 01-03, 12-24, 12-31 |
  | 2008 | 12-22 |
  | 2009 | 11-09 |
  | 2012 | 12-24, 12-31 |
  | 2017 | 07-03 |

  No week is missing for the seven currencies or the USD index, apart from the NZD reports above.
- **October 2013 US government shutdown:** the reports for as-of 2013-10-01 onwards were
  published late, on a catch-up schedule. That schedule is not in the file, and cftc.gov is
  unreachable from this environment.
  - All as-of dates from **2013-10-01 to 2013-12-24** (13 reports) are therefore marked
    **UNAVAILABLE** and must not be used.
  - The window is deliberately wide. Supplying the CFTC's published release dates for that period
    would let it be narrowed; until then, no date is guessed.

## 7. Publication-lag rule (binding on any future study)

- **Positions:** as of Tuesday.
- **Normal release:** Friday 15:30 New York. After a holiday, the release moves to the next
  business day.
- **Rule:** an observation may be used only from **17:00 New York on the first weekday on or after
  as-of + 6 calendar days**. That is the Monday after a normal Friday release, which is also the
  D1 close.

This rule:

- covers the one-business-day holiday delays without needing release dates the file does not
  contain;
- gives up the Friday-to-Monday window, which is deliberate conservatism.

The function is `available_on()` in `scripts/cot_audit.py`, and `tests/unit/test_cot_audit.py`
pins it. Two further rules apply:

- **No interpolation:** a missing week stays missing.
- **No future data:** a study may see a report only from its available-on date.

## 8. Constructible pairs (universe of 12)

| Pair | Construction | Status |
|---|---|---|
| EURUSD, GBPUSD, AUDUSD, NZDUSD | the currency's own CME future (long future = long the pair) | **direct** |
| USDJPY, USDCHF, USDCAD | the currency's CME future with the sign inverted (long JPY future = short USDJPY) | **direct, inverted** |
| EURGBP, EURJPY, GBPJPY, EURCHF, AUDJPY | no usable cross future (§4); only as a difference of two USD-based measures | **derived only**: a construction choice, not observed positioning. It must be fixed in a preregistration or excluded |
| (all USD pairs) | the ICE USD index as a USD-wide measure | available, 603 reports |

## 9. Is it sufficient for a preregistered COT study?

**Yes, for one small, preregistered study on the seven direct USD pairs, and with limited power.**

| Point | Detail |
|---|---|
| Sample | 429 usable weekly reports per currency in the judged period, 7 currencies. The currencies share a USD factor, so they are not 7 independent samples. |
| History before the judged period | 2006-06-13 → 2008-07-08, about 108 weeks. A 52-week trailing window is full before the judged period starts; a 104-week window is full at about its start. A 156-week window would remove about the first year of the judged period. That choice must be fixed before any result is seen. |
| Statistical bar | Unchanged and at least the current registry threshold (t ≥ 3.372 after 67 prior tests). It rises with every hypothesis registered. |
| Power | A condition that fires on extreme positioning in about 10% of weeks yields roughly 140–280 trades across the seven pairs. With a per-trade standard deviation of about 1.1R, only an edge of about **0.25–0.3R per trade or larger** would be detectable. A smaller real effect would be reported as not detected, not as absent. |
| Holdout | All of `fut_fin_txt_2017.zip` (52 reports) is inside the sealed holdout and stays sealed. |

**Before any test, the remaining decisions must be written down:**

- the measure (net positioning of which category, normalised how);
- the window;
- the levels;
- the side;
- the exit;
- the pairs.

Each must be fixed in a preregistration before any result is seen. None of them has been made.
