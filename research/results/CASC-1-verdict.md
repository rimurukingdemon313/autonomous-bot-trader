# CASC-1: the verdict

**FAILED, as registered** (dev stage, decisions 2023-07-01 to 2025-02-28, judged once on 2026-11-15 by run 2 of
`casc1.yml`; record `research/knowledge/CASC-1.json`). Spot bought outright, held 24 hours, 0.25% a side.

| Fall over four hours, perpetual at least 0.5% below spot | Trades | Days | Net a trade | t | Against the market | Median | Positive | Falls led by spot |
|---|---|---|---|---|---|---|---|---|
| at least 8% | 326 | 183 | **-1.85%** | -2.07 | -2.60% | -1.15% | 46% | +0.01% (4,953) |
| at least 15% | 73 | 54 | -0.73% | -0.28 | | | | (INCONCLUSIVE: 150 trades needed) |

**Why it failed.** The mechanism ran the other way: falls in which the perpetual led (the liquidation signature)
kept falling for a day, while falls of the same size led by spot ended flat. Every placebo draw (the same coin at
hours it had not fallen) did better. Forced selling in crypto cascades continued past the hour the rule bought.

**What follows.** No later stage; the hourly prices of 2023-06 to 2025-03 are spent for rules about falls. Selling
into liquidation-led falls would be a new hypothesis, needs short selling and is not registered.
