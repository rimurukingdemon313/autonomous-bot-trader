# Round 2 data audit: what the system knows, what it cannot know yet

Round 1 searched transformations of one information set: bid/ask bars for 12 FX pairs, plus gold
from 2011. Every Round 1 feature, the analog model and every documented rule were functions of
those bars. Round 2 starts from what those bars **cannot** contain.

## What the system had (Round 1)

| Information | Source | Span |
|---|---|---|
| Bid/ask M15 bars, 12 FX pairs | Dukascopy ticks via the FX-Data mirrors (`data/manifest.json`) | 2007-03-30 → holdout (2017-01-01) |
| XAUUSD bars | same | 2011-05 → holdout |
| Economic calendar | ForexFactory, live only (no history) | — |

## What is missing, and whether Round 2 could obtain it

| Information | Needed for | Authoritative source | Obtained? |
|---|---|---|---|
| Central-bank policy rates, G10 | carry, rate-differential changes | FRED, BIS WS_CBPOL, national central banks | **No.** The environment's network policy refuses every source tried: FRED, the ECB data API, BIS, the Fed, BoJ, RBA, BoE, SNB, BoC, OECD and DBnomics |
| Short-term market rates (3M), G10 | carry magnitude | FRED, OECD MEI | **No** (same refusal). Euribor monthly is reachable but its date semantics are ambiguous, so it is not used |
| Forward points or historical broker swaps | carry income per trade | broker or Bloomberg | **No.** None reachable, and none is fabricated |
| **VIX daily close** | risk-on/risk-off regime | Cboe (via the datahub.io mirror) | **Yes**, 1990 → |
| **Brent spot, daily** | cross-asset: oil and CAD | U.S. EIA (via the datahub.io mirror) | **Yes**, 1987 → |
| **US 10-year yield, monthly average** | US rate changes | Federal Reserve H.15 (via the datahub.io mirror) | **Yes**, 1953 → |
| **US CPI-U, not seasonally adjusted** | US inflation regime | BLS (via the datahub.io mirror) | **Yes**, 1913 → (ingested; no hypothesis uses it yet, see below) |
| **S&P 500, monthly average** | equity risk regime | Shiller's dataset | **Yes**, 1871 → (ingested; monthly granularity is too coarse beside VIX) |
| Foreign CPI or activity, monthly | Taylor-rule fundamentals | national statistics offices, OECD | **No.** Only annual World Bank figures are reachable, which gives 3–8 observations in the judged period: too few |
| Positioning (CFTC COT) and order flow | flow-based hypotheses | CFTC; interbank | **No** |

The mirrors are the datahub.io "core" packages. They republish the named publisher's series,
and each README names that original source. `scripts/ingest_external.py` checks every file
against well-known published values before accepting it. Two examples:

- VIX 80.86 on 2008-11-20;
- Brent $143.95 on 2008-07-03.

The sha256 of the exact bytes used is recorded in `data/external/manifest.json`. As with the
bars, the raw files themselves are not committed.

## Timestamp rules

When each value became public (`aitrader/data/external.py`, `available_at`):

| Series | Observation | Taken as public at | Why |
|---|---|---|---|
| VIX | close of date d | 16:45 New York on d | Cboe publishes the close at 16:15 New York. Our D1 bar closes at 17:00 New York, so the value is known at every D1 decision in both DST regimes (tested) |
| Brent | spot assessment of date d | 17:00 New York on **d+1** | the EIA spot is assessed after the London close; one full day of lag is conservative |
| US 10y | average of month m | 17:00 New York on the 2nd day of m+1 | the average exists only once the month ends |
| CPI-U | month m | 17:00 New York on the **last** day of m+1 | BLS normally releases between the 10th and 17th of m+1. The 2013 shutdown delayed one release to the 30th; the rule covers it |
| S&P 500 | average of month m | 17:00 New York on the 2nd day of m+1 | as for the US 10y |

**Revisions.** Only unrevised series are admitted:

- VIX, the H.15 yields, EIA spot assessments and the S&P 500 level are not revised.
- CPI-U NSA is not revised; only seasonal factors change, and those are not used.

No revised series (GDP, payrolls) is used. Their real-time vintages are not reachable, and
the final revised values would leak information the market did not have.

**Holdout.** The loader truncates every external series at the sealed holdout exactly like
the bars (`test_unverified_files_are_refused_and_the_holdout_is_sealed`).

## What this means for carry

The Round 2 plan puts carry first. It cannot be tested properly here, because no
interest-rate series outside the US is reachable. Round 2 uses only what is solid:

- **The sign of the carry differential.** It is known for the pairs where it never changed
  over the judged period. AUD and NZD out-yielded USD and JPY at every date from 2008-07 to
  2016-12: the RBA's cash rate never went below 1.50% and the RBNZ OCR never below 1.75%,
  against a Fed target at most 2.00% and a BoJ rate at most 0.50%. This is a **documented
  fact from prior knowledge**; the primary sources could not be re-opened here.
- **The risk regime (VIX)** under which carry is documented to pay or crash.

**What is missing is the carry income itself**, the interest differential earned while the
position is held. The R2A tests judge the spot move only, without charging or crediting swap.
That biases them **against** long carry.

A proper carry test needs:

- rate data: allow `fred.stlouisfed.org`, `data-api.ecb.europa.eu` or `stats.bis.org`;
- or a committed file of historical policy rates from an authoritative source.
