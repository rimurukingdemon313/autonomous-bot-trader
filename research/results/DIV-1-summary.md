# DIV-1 results: diversified time-series momentum (multi-asset ETFs)

Preregistered and frozen in commit `48f84e2` before any data was fetched. Executed once on a GitHub Actions runner (the research container cannot reach market data): commit `a091344`, workflow `.github/workflows/div1-run.yml`, fetch log `research/results/div1-fetch.log`, judge log `research/results/div1-judge.log`. Data hashes: `data/div/manifest.json`.

**Verdict: FAILED.** Nothing passed, so the 2021+ holdout (`research/holdout-div.json`) is **still sealed**.

Judged period 2008-01 → 2020-12 (156 months); returns are monthly portfolio returns (fraction of capital), after costs.

| | H1 TSMOM12 | H2 BLEND |
|---|---|---|
| Months | 156 | 156 |
| Gross, annual (Sharpe, t) | +7.79% (0.451, 1.625) | +10.37% (0.606, 2.186) |
| Costs, annual | 8.86% | 9.65% |
| Net, annual (Sharpe, t) | -1.07% (-0.062, **-0.224**) | +0.72% (0.042, **0.152**) |
| Net, development 2008-14 (annual) | +3.95% | +5.80% |
| Net, validation 2015-20 (annual) | -6.93% | -5.21% |
| Net with costs x2 (annual) | -9.93% | -8.93% |
| Max drawdown (sum of monthly net) | 70.8% | 57.7% |
| Positive months | 48.1% | 47.4% |
| Failed gates | t, validation, costs_x2, leave_one_class_out | t, validation, costs_x2, leave_one_class_out |

## Diagnosis (descriptive, same period; `research/results/DIV-1-diagnosis.json`)

| | H1 | H2 |
|---|---|---|
| Average gross exposure | 3.545x | 3.54x |
| Cost: financing of leverage | 7.63%/yr | 7.62%/yr |
| Cost: turnover | 0.60%/yr | 1.36%/yr |
| Cost: short borrow | 0.62%/yr | 0.67%/yr |
| Gross, development / validation | +11.34% / +3.64% | +13.90% / +6.25% |
| Position-months held | 2957 | 2952 |
| Direction flips + entries/exits | 328 + 21 | 866 + 31 |

**Why it failed.**
1. **Leverage financing.** The 40% per-asset volatility target, applied to low-volatility bond and currency ETFs, implies about 3.5x gross exposure. The declared 3% financing on exposure above 1 costs about 7.6% a year, 86% of all costs. Trading costs were small.
2. **Power.** Without any financing, the net Sharpe would be about 0.5, a t of about 1.8 over 13 years: still short of 3.0. The gross premium is the size the literature reports (Sharpe 0.45–0.61) and positive in both halves, weaker in 2015–2020 (2016 and 2018 reversals). Thirteen years cannot prove an effect that size.
3. **Implication for a retail implementation.** Retail CFD brokers charge overnight financing of about the benchmark rate plus 2–3% on the full notional. That is the same order as the 3% declared here, so a leveraged trend portfolio carried in CFDs would face the same cost.

Per the preregistration, DIV-1 is not re-run with other parameters. Its 2021+ holdout stays sealed.
