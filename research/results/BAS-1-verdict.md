# BAS-1: the verdict

**FAILED, as registered** (dev stage, entries 2021-01-01 to 2025-02-28, judged once on 2026-11-15 by run 2 of
`bas1.yml`; record `research/knowledge/BAS-1.json`). Spot bought outright, seven days, against the equal-weight spot
return of every seasoned coin; 0.15% a side.

| Funding over 72 hours, per 8 h | Entries | Weeks | Mean excess a week | t | Median | Positive | Long-only net | Placebo 95th pct |
|---|---|---|---|---|---|---|---|---|
| at least +0.03% | 3,372 | 76 | **-1.04%** | -2.24 | -3.87% | 34% | +1.50% | +1.42% |
| at least +0.05% | 1,771 | 50 | -0.51% | -0.63 | | | | (INCONCLUSIVE: 52 weeks needed) |
| at least +0.1% | 419 | 23 | -0.51% | -0.22 | | | | (INCONCLUSIVE) |

**Why it failed.** Crowded longs were wrong: coins with high funding fell behind the market, the typical one by
nearly 4% in a week, and the same coins did better on days their funding was normal. The long-only net was
positive only because the market rose.

**Read with today's other results.** SQZ-1 (crowded shorts), CASC-1 (liquidation-led falls), NEWL-1 (new listings)
and BAS-1 (crowded longs) agree: a coin under leverage stress of either sign does worse than the market for days to
weeks. That information is on the short side. For altcoins the Islamic condition excludes it (a perpetual short
pays or receives funding; a borrowed coin pays interest), and long-only it can only steer a portfolio away from
stressed coins: the market's return plus a small excess, not an edge of its own.

**A mistake of design, declared.** The 0.05% and 0.1% thresholds could not reach 52 weeks with an entry in dev (50
and 23). The minimum counts weeks that hold an entry; the test that every stage can reach its minimum counted
calendar weeks only, and missed it.
