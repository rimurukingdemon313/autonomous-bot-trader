# Round 2 results, family by family

Every family was preregistered and committed before it ran, and was judged once on
2008-07-11 → 2017-01-01. The plan is [ROUND2_PLAN.md](ROUND2_PLAN.md) and the data audit is
[ROUND2_DATA_AUDIT.md](ROUND2_DATA_AUDIT.md). The per-hypothesis direction and cost reports
are `research/results/R2?-report.json` (descriptive). The verdicts are the programs':
`research/knowledge/R2?.json`.

## R2A: carry, conditional on the risk regime — FAILED

| | R2A-1: long carry while VIX < 20 (D4) | R2A-2: short carry after VIX rises > 10% in 5 closes (D3) |
|---|---|---|
| Trades | 263 | 475 |
| P(direction correct), gross | 45.3% | 46.7% |
| Gross R per trade | −0.099 | −0.029 |
| Costs: spread / commission / slippage / swap | 0.016 / 0.003 / 0.001 / 0 | 0.022 / 0.004 / 0.001 / 0 |
| Net R: lower / normal / higher cost | −0.113 / −0.119 / −0.130 | −0.046 / −0.056 / −0.068 |
| Net R with the standard D1 swap charged | −0.193 | −0.081 |
| t (required 3.279) | −1.78 | −1.12 |
| Mean MFE / mean MAE / worst MAE | +0.67 / −0.70 / −2.67 R | +0.62 / −0.59 / −2.09 R |
| Mean holding | 16.7 days | 4.7 days |
| Instruments | all 3 negative | all 3 negative |
| Years positive | 3 of 9 (2 of them with 3 trades) | 3 of 9 |
| Battery | 10 of 12 checks failed | 10 of 12 checks failed |

### Reading

1. **The problem is direction, not cost.**
   - Costs are 0.02R per trade at this horizon, so they are not the problem.
   - In calm markets, AUD and NZD fell more often than they rose over the next month: 45% of
     trades were right before costs. In 2013–2015, the end of the commodity boom, the spot
     move overwhelmed any calm-market drift.
2. **The carry income is missing, and it does not rescue the result.**
   - The test leaves out the interest earned on a long high-yield position; that data is
     unavailable.
   - An **inferred estimate**, not a measurement: a 2–3% annual differential over the 17-day
     mean hold, against a 3-ATR stop of about 2.4% of price, is roughly +0.05 to +0.08R per
     trade.
   - R2A-1 would still be about −0.04 to −0.07R.
3. **The documented carry premium is a portfolio result over many currencies, including the
   minor, high-yield and expensive ones.** Three majors' spot legs in the post-2008 era of
   low rates did not show it.
4. **R2A-2 found no forced-unwind continuation.** After VIX rises, carry currencies did not
   keep falling over the next week (P = 47%).

**Family conclusion.** No conditional carry edge is detectable in the spot moves of the three
positive-carry majors. The carry family is **not closed**: its core ingredient, the interest
differential, could not be measured. It needs rate data (ROUND2_DATA_AUDIT.md).

## R2B: US rate-differential changes — FAILED

| | R2B-1: buy the pair last month's US-yield change favours (D4) | R2B-2: sell the pair it disfavours (D4) |
|---|---|---|
| Trades (7 USD pairs) | 396 | 381 |
| P(direction correct), gross | 46.5% | 50.7% |
| Gross R per trade | −0.019 | +0.028 |
| Costs: spread / commission / slippage / swap | 0.011 / 0.002 / 0.001 / **0.075** | 0.011 / 0.002 / 0.001 / **0.076** |
| Net R: lower / normal / higher cost | −0.103 / −0.108 / −0.150 | −0.056 / −0.061 / −0.107 |
| t (required 3.291) | −1.81 | −0.94 |
| Mean MFE / MAE / worst MAE | +0.75 / −0.68 / −2.86 R | +0.79 / −0.64 / −2.39 R |
| Instruments positive | 1 of 7 | 1 of 7 |
| Years positive | 2 of 9 | 3 of 9 |

### Reading

1. **Direction carries no information.** After a 10bp monthly move in US yields, the pair the
   move favoured went the favoured way 46–51% of the time. That is a coin flip.
2. **The forward-premium anomaly is documented at the level of the differential, not in the
   next month's response to its change.** Measured this way it is absent from the majors in
   2008–2016.
3. **A modelling caveat.** On month-long holds most of the cost is the declared swap
   approximation (0.01 ATR per night, always charged). Real swap is a credit on the high-yield
   side and a debit on the other. Without any swap, R2B-2 would be about +0.015R, which is
   noise-level and far below the detectable 0.2R. The verdict does not depend on this
   approximation.

**Family conclusion.** No edge from US rate changes. Only the US side of the differential
was observable, which is a real limitation; ROUND2_DATA_AUDIT.md lists what would lift it.

## R2C: cross-asset, oil and the Canadian dollar — FAILED

| | R2C-1: buy USDCAD after Brent fell > 5% in 20 obs (D3) | R2C-2: sell USDCAD after Brent rose > 5% (D3) |
|---|---|---|
| Trades | 169 | 147 |
| P(direction correct), gross | **55.6%** | 48.3% |
| Gross R per trade | +0.099 | −0.038 |
| Costs: spread / commission / slippage / swap | 0.021 / 0.004 / 0.001 / 0.027 | (split not reported: the cost variants changed the position schedule) |
| Net R: lower / normal / higher cost | +0.050 / **+0.047** / +0.023 | −0.079 / −0.088 / −0.112 |
| t (required 3.302) | 0.77 | −1.61 |
| Beats random entries | no | no |
| Years positive | 4 of 9, with +0.29R in 2014 and 2015 | 1 of 8 with ≥ 20 trades |
| Mean MFE / MAE / worst MAE | +0.66 / −0.52 / −1.62 R | +0.51 / −0.57 / −1.99 R |

### Reading

- **R2C-1 is the first Round 2 result above zero after costs, and it survives the cost stress.**
  - It is not significant: t 0.77 against 3.30 required.
  - It does not beat random USDCAD entries.
  - Its gain comes from the 2014–15 oil collapse, when selling CAD after oil fell kept working.
  - That is the signature of **one episode, not a rule**. Its evidence falls short of PROMISING,
    which needs t ≥ 2.
- **The documented evidence predicted this.** Ferraro, Rogoff & Rossi (2015) find the oil–CAD
  link contemporaneous, not lagged.

The result is recorded as an **UNCERTAIN CONCLUSION**:

- the lagged oil→CAD effect may exist in large, persistent oil moves;
- it is not distinguishable from luck on this sample;
- testing it needs new data recorded from now on.

**Family conclusion.** No cross-asset edge, oil→CAD, at the required level.
