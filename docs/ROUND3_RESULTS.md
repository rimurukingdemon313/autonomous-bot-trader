# Round 3 results: genuine interest-rate information and carry — FAILED

The frozen design (`research/specs/R3.json`, unchanged) was run once on real policy-rate data.
The verdicts are the program's (`research/knowledge/R3.json`). The decomposition is
descriptive (`research/results/R3-report.json`, `scripts/r3_report.py`).

## Data

| Item | Value |
|---|---|
| Source | BIS WS_CBPOL, central-bank policy rates. The official bulk file `WS_CBPOL_csv_flat.zip` was supplied by the user and extracted unmodified |
| SHA256 | ZIP `74c91ec036c342c1c645df841e067e7dfc833fb75b6e67052beee79aed272065`; CSV `4f7e117017ce7fda7775c9a4f63753115a30b24a2a3bb18270ead31791708e5a` (475,488,467 bytes; ZIP member dated 2026-09-23) |
| Validation | PASSED: AUD 7.25, NZD 8.25, EUR 1.00, GBP 0.50, JPY 0.10 and CAD 0.25 matched the published rates on their check dates. USD and CHF were inside their target ranges (BIS publishes the midpoint: 0.125) |
| Coverage, 2007-04 → 2017-01 | USD, EUR, GBP, AUD, NZD, CAD and CHF are complete, with a largest gap of 3–6 days. **JPY is not covered.** BIS publishes no Japanese policy rate from 2013-04-04 to 2016-09, because the BoJ targeted the monetary base under QQE. Under the staleness rule (a daily rate older than 7 days is not carried forward) that gap stays a gap |
| Qualifying pairs | **8**: EURUSD, GBPUSD, AUDUSD, USDCAD, USDCHF, NZDUSD, EURGBP, EURCHF. The four JPY pairs are excluded by the frozen coverage rule |
| Judged | 2008-07-11 → 2017-01-01, once; threshold t ≥ 3.351 (the registry, 8 new tests). The holdout stays sealed |

## Results

Columns, all in R per trade:

- **P(dir):** share of trades whose price move before costs went the traded way.
- **Gross spot:** the price move before costs.
- **Carry:** the RATE-DIFFERENTIAL CARRY PROXY.
- **Costs:** spread + commission + slippage.
- **Financing:** the 0.5% a year markup.

| ID | Condition | Side | n | P(dir) | Gross spot | Carry | Gross | Costs | Financing | **Net** | t | Status |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| R3-A | carry long, ≥ 1pp | BUY | 341 | 41.1% | −0.101 | +0.045 | −0.056 | 0.018 | 0.009 | **−0.083** | −1.50 | REJECTED |
| R3-B | carry via the quote, ≥ 1pp | SELL | 12 | 16.7% | −0.621 | +0.013 | −0.608 | 0.013 | 0.006 | **−0.627** | −5.06 | REJECTED (12 trades < 100) |
| R3-C | differential widening | BUY | 149 | 40.3% | −0.159 | +0.025 | −0.134 | 0.017 | 0.010 | **−0.160** | −2.08 | REJECTED |
| R3-D | differential narrowing | SELL | 218 | 43.6% | −0.049 | −0.028 | −0.077 | 0.018 | 0.013 | **−0.108** | −1.80 | REJECTED |
| R3-E | differential accelerating | BUY | 249 | 46.6% | +0.015 | +0.025 | +0.040 | 0.018 | 0.014 | **+0.007** | 0.10 | REJECTED |
| R3-F | policy move favouring the base, within 30 days | BUY | 95 | 44.2% | −0.149 | +0.024 | −0.125 | 0.017 | 0.009 | **−0.151** | −1.48 | REJECTED (95 < 100) |
| R3-G | carry long while VIX < 20 | BUY | 198 | 42.9% | −0.138 | +0.053 | −0.085 | 0.021 | 0.011 | **−0.117** | −1.70 | REJECTED |
| R3-H | carry long, no policy move in 30 days | BUY | 272 | 43.4% | −0.064 | +0.048 | −0.016 | 0.018 | 0.009 | **−0.044** | −0.72 | REJECTED |

**Cost and financing sensitivity** (net R):

| ID | Cost: lower / normal / higher | Markup: 0% / 0.5% / 1.0% |
|---|---|---|
| R3-A | −0.074 / −0.083 / −0.099 | −0.074 / −0.083 / −0.092 |
| R3-E | +0.013 / +0.007 / −0.002 | +0.022 / +0.007 / −0.007 |
| R3-H | −0.039 / −0.044 / −0.060 | −0.035 / −0.044 / −0.053 |

No hypothesis is positive at every cost level and every markup. Only R3-E is positive at
normal costs, and at t = 0.10 it is noise.

**Robustness.** Every hypothesis failed 10 or 11 of the 12 battery checks: significance, beats
random, permutation, cost stress, delay stress, years, instruments, leave-one-out, regimes and
outliers. R3-B and R3-F also failed the minimum of 100 trades. **The board rejected all 8.**

## What the data says

1. **Interest-rate information did not improve directional prediction.** P(direction correct)
   was 40–47% in every hypothesis with enough trades, below a coin flip for the carry-long
   hypotheses. Buying the higher-yielding currency meant, more often than not, buying the
   currency that then fell (AUD and NZD in 2013–15, GBP after 2016).
2. **Carry income is real, but smaller than the spot losses.**
   - The proxy added +0.045R per trade to carry-long trades (R3-A), and +0.05R under calm VIX
     (R3-G).
   - The spot move cost more: −0.10R and −0.14R respectively.
   - This is the classic carry-crash profile on the majors in 2008–2016: collect the
     differential, lose it on the currency.
3. **R3-H is the least bad carry form** (−0.044R net; −0.016R gross). Avoiding the 30 days
   after a policy move removed part of the spot loss, but it is not an edge.
4. **Comparisons.**
   - Price-only: the gross-spot column is the price-only component of the same trades.
   - Random direction: failed by every hypothesis.
   - Previously rejected: R2A-1 (−0.119R, spot legs only by VIX) and R3-G (−0.117R with the
     true differential and its income) agree.

## Status

**VALIDATED 0. PROMISING 0. REJECTED 8. BLOCKED 0.** Round 3 is complete.

## Remaining data problems and limits

- **JPY has no policy rate for 2013-04 → 2016-09** (QQE). The four JPY pairs could not be tested
  under the frozen rule; nothing was substituted. A JPY test would need a declared short-rate
  series such as the call rate (a different rate type), which means a new preregistration.
- **The carry proxy is not broker swap.** Real retail swap differs by broker and markup; the
  markup sensitivity above brackets it.
- **Gap risk is understated by the simulator.**
  - A stop is filled at the stop price when the gap happens inside a daily bar.
  - One R3-E trade (EURCHF, long from 2014-12-18) reached −73.9R of adverse excursion at the
    SNB floor removal, but was booked at −1.06R.
  - Realistic fills would make every affected result worse, not better; no verdict depends
    on it.
