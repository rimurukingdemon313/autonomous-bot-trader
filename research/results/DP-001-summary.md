# DP-001: result

**Verdict: FAILED.** This is a valid negative result, recorded in the registry on
2026-09-29 and counted in every later threshold.

- Preregistration: commit `907bb8e`, pushed before the run.
- Registry trial `DP-001`: design sha256 `2761915f…`, code sha256 `0dbca65d…`.
- Artifact: [`research/knowledge/DP-001.json`](../knowledge/DP-001.json), sha256 `fd9c62f2…`.
- Full screen table: [`DP-001-screen.json`](../knowledge/DP-001-screen.json).

## What the preregistered procedure found

| Stage | Result |
|---|---|
| Features | 35 catalogued. Every one passed the truncation leakage test on real bars (72 decision rows each, other instruments cut as well). |
| Discovery screen (fit, 2007-06 → 2011-01) | **0 discoveries in 1,734 tests** at BH q ≤ 0.10. All 1,734 cells were testable (n ≥ 1,933 trades each). |
| Validation (select, 2011-01 → 2013-07) | No drafts to validate. The boosted-stumps model: **0 of 48 configurations passed**. The best had mean +0.008R, t = 0.16. The median across configurations was −0.074R. |
| Confirmation (judge, 2013-07 → 2017-01) | No finalist, so no outcome in this segment was read. The registry still counts the 6 reserved tests, which is conservative. |

### The screen, in numbers (exit E1, net of costs)

- **Every one of the 1,734 cells had a negative mean net R.**
  - The best was −0.089R (`session=low & smc_sweep=high`, SELL).
  - The median was −0.157R.
  - The largest t-statistic was −3.68: every cell lost *significantly*.
- By side:
  - BUY cells: median −0.170R, 95th percentile −0.135R.
  - SELL cells: median −0.144R, 95th percentile −0.110R.
- Best single-feature cells: `usd_corr=low` SELL −0.113R, `range_pos24=low` SELL −0.123R, and
  `d1_trend=low` SELL −0.124R.
- Standard errors are clustered by week (median 188 weeks per cell).

## Why (descriptive, after the fact, discovery segment only)

This was not a preregistered test and decides nothing. It explains the verdict. Every decision
row of the discovery segment was traded with each exit, one position per instrument:

| Exit | Cost per trade (R) | Gross mean R, BUY / SELL | Net mean R, BUY / SELL |
|---|---|---|---|
| E1 barrier 1.0/1.5 ATR, 24 bars | 0.139 | −0.024 / −0.002 | −0.164 / −0.141 |
| E2 barrier 1.5/3.0 ATR, 48 bars | 0.105 | −0.028 / +0.021 | −0.133 / −0.084 |
| E4 time, 24 bars, 2 ATR stop | 0.087 | −0.021 / +0.030 | −0.108 / −0.058 |
| E5 trailing 1.5 ATR, 48 bars | 0.102 | −0.025 / +0.015 | −0.127 / −0.088 |
| E8 structure stop, 2R target | 0.214 | −0.026 / −0.001 | −0.236 / −0.218 |

On H1 bars:

- The **gross** expectancy of every exit is within ±0.03R of zero.
- **Costs are 0.09–0.21R per trade.** That is spread, slippage, commission and swap relative to
  an H1-ATR stop.
- A conditional pattern would need a gross edge of roughly 0.1–0.2R per trade just to break even.
  No declared cell came close, and neither did the model's top-scored 5%.

## What this does and does not show

- **It shows** that within the declared space nothing survives costs at the H1 horizon on these
  12 pairs in 2007–2010. The declared space is 19 price-derived features in terciles, pairs of
  them, both sides, and a 35-feature additive model. The absence is not marginal: no cell reached
  a positive net mean at all.
- **It does not show** that no edge exists:
  - at other horizons (daily decisions pay far less cost per unit of risk);
  - in data the system does not have (order flow, positioning, interest-rate carry);
  - in interactions deeper than the two-term cells and the additive model.
- **Nothing in production changed**, and nothing would have if the result had been positive.

The next experiment to register is given in the final report and in
[`docs/DISCOVERY.md`](../../docs/DISCOVERY.md).
