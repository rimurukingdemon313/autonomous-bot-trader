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
