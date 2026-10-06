# FT-1: IX-2's last-hour index momentum at 2025–2026 CFD spreads (preregistration)

| | |
|---|---|
| Frozen spec | `research/specs/FT-1.json` |
| Spec sha256 | `204ffab856337993cd69d8bd28189728ef6faf8085f0f6b5d0e6d3ad71e78d31` |
| Code | `aitrader/research/discovery/ixmom.py` (ix-1.0.0) and `scripts/ix2.py`, both unchanged; `scripts/ft1.py` |
| Run | `python scripts/ft1.py run`, once |
| Threshold | t ≥ **3.6635** on the daily equal-weight book: Bonferroni over every test this project has registered, plus these 2 |

## Why this test exists

IX-2 (FAILED) found last-hour momentum into the cash close with the predicted sign in six index CFDs,
2012–2020:

- ALL: gross +1.07 bp;
- STRONG: gross +2.61 bp, t about 5 on gross;
- cost: 4.3 bp, so net was negative.

Index-CFD spreads in basis points fell three to five times over that period (USATECH 6.6 bp in 2013,
1.3 bp in 2020) as index levels rose and quotes stayed in points. The edge report
(`docs/EDGE_SEARCH_REPORT.md`, section 4) named this as the one thing that could change the conclusion.

**Hypothesis:** at the spreads quoted in 2025–2026, the unchanged IX-2 rule is net positive.

Nothing about the rule is new. This is not a variation of a failed signal: the signal, the variants, the
stop, the slippage, the stresses and the gates are IX-2's, imported from its frozen code. The only
differences are:

- the period;
- the threshold, which counts every test registered since.

## Data and period

| | |
|---|---|
| Instruments | IX-2's six: USA500IDXUSD, USATECHIDXUSD, USA30IDXUSD, JPNIDXJPY, HKGIDXHKD, AUSIDXAUD |
| Bars | Dukascopy H1 bid/ask hour candles, fetched **only from 2025-01-01** (`data/ft1/`) |
| Judged | 2025-01-01 → 2026-10-01. The first 60 trading days build the volatility estimates, as in IX-2 |
| Never touched | The IX-2 holdout, 2021-01-01 → 2025-01-01. It is not fetched, not even for warm-up |

No 2025–2026 index bar has been fetched or seen by this project before this document was committed.

## Gates and labels (decided now)

The IX-2 gates apply unchanged to EQ-ALL and EQ-STRONG:

- ≥ 300 trades;
- net > 0;
- t ≥ 3.6635;
- costs × 1.5 and × 2;
- late entry;
- both halves;
- ≥ 60% of instruments;
- profit factor ≥ 1.05;
- top-year share.

| Label | Requires | Means |
|---|---|---|
| PASSED | every gate | VALIDATED candidate for the paper bot, then forward evidence before any broker |
| PROMISING | ≥ 300 trades, net > 0, costs × 1.5 > 0, late entry > 0 and t ≥ 2.0, but not PASSED | **not validated**. Admitted to the paper forward test only, labelled EXPERIMENTAL in the bot. Recorded in the registry as INCONCLUSIVE |
| FAILED | anything else | the cost-compression hypothesis is not supported; the rule is not run |

**Reported, never gated:**

- the US-only subset, which was positive in IX-2 and was noticed after seeing IX-2's results. It is
  therefore not a test;
- the median quoted spread per instrument.

## Power, stated before the result

IX-2 STRONG's standard error was about 0.53 bp over 1,322 trading days. Over about 380 judged days it is
about 1.0 bp. As a result:

- **PASSED** needs a net of roughly +3.6 bp per trade. That is more than IX-2's whole gross edge, so a
  pass is unlikely even if the hypothesis is true.
- **PROMISING** needs about +2 bp net.
- A FAIL at a net of about +1 bp would not prove the absence of a small edge. It would mean this window
  cannot show one, and the result would be reported that way.

## Forbidden, by this document

- changing the rule, the variants or the gates;
- choosing instruments after the result;
- fetching or reading 2021–2024;
- a second run.

## Clarification, committed before any FT-1 result was computed

The first fetch (run 37436760026) lost three months to datafeed failures:

- JPNIDXJPY 2025-04 and 2025-06;
- USATECHIDXUSD 2025-07.

No bar of FT-1's period had been simulated or summarised when this was found. The rule, fixed now:

1. The two instruments' 2025 hour candles are fetched once more.
2. A re-fetched month is used **only** for a month the first fetch lost.
3. Months present in both fetches must agree exactly, or the run stops.
4. Anything still missing stays missing: it is excluded and reported, never filled.

No other change to FT-1.
