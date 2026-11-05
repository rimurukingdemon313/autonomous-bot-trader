# XSM-1: cross-sectional momentum among the 20 largest Binance spot coins (preregistration)

**Written, frozen and registered on 2026-11-05, before any XSM-1 data was fetched.**

The owner, 2026-11-05: "don't fixate on the AI trading; anything that makes us a profit; never stop".

| | |
|---|---|
| Frozen spec | `research/specs/XSM-1.json` |
| Spec sha256 | `a02eb4a23cde9759643c8425f8712f0102fd7d571849b0ab4e6c6d02bedec8f7` |
| Code | `scripts/xsm1.py` and `scripts/xts1.py`, sha256 `5a4df02339a6243771152ff86dcbb1119af7729ada08c82b4746b2fad8a29a64`. Every command refuses to run if either hash changes |
| Run | `.github/workflows/xsm1-run.yml` on GitHub's runner, which can reach Binance's archive (this environment cannot). It runs `fetch`, then `judge`, then `holdout` only if `judge` PASSED |
| Threshold | t ≥ **3.144**. That is the Bonferroni value for the 29 earlier crypto tests in the registry plus this 1, and never below 3.0 |

## Why this question

XTS-1 asked whether bitcoin and ether trend over time, and it failed (t 2.87 against 3.09). CR-1's time-series
momentum on perpetuals failed too. XSM-1 asks a different question: **among the large coins, do the ones that rose
most lately beat the others next week?**

- **The finding.** Liu, Tsyvinski & Wu (2022, "Common Risk Factors in Cryptocurrency", Journal of Finance) found a
  strong cross-sectional momentum factor in coins. It was built on past three-week returns and rebalanced weekly.
- **What is new here.** Their sample was mostly many small coins, in 2014 to 2018. XSM-1 asks whether the effect holds
  among the 20 largest coins a retail trader can trade, after costs, since 2018.
- **The mechanism usually given.** Attention and retail flows arrive late and in waves.

**Known before freezing.** Each of these is said now, so that it cannot be explained away later.

- Momentum published in 2018 to 2022 may have faded since: XTS-1's validation (2022 to 2024) was much weaker than its
  development.
- The book holds only 4 coins, and they are the ones that rose most. It will carry crypto's crashes in full: 2018,
  May 2021, 2022. That is why the question is the difference from the 20, and why the book must also pay on its own.
- Volume ranks the universe. A coin in the news trades more, so the universe itself leans toward what moved. That is
  part of what a trader could actually do, and it is known at the close.

## The rule (fixed; nothing is tuned)

- **The universe.** Every Sunday at the daily close (00:00 UTC Monday), it is the 20 Binance spot USDT pairs with the
  largest USDT volume over the 28 days to that close.
  - Only pairs with a close on each of the 90 days to that close count.
  - Stablecoins, fiat and leveraged tokens are not coins here: any base with "USD" in its name, the fiat and
    stablecoins listed in the spec, and the UP/DOWN/BULL/BEAR tokens.
  - With fewer than 12 such pairs, there is no trade that week.
- **The book.** It holds, equally weighted, the 4 of those 20 whose close rose most over the 21 days to that close
  (ties by name). It holds them from that close to the next Sunday's.
- **Endings.** A coin with no close that next Sunday is valued at its last close in the week, so a delisting's loss is
  kept. One with no later close at all is valued at its entry.
- **The benchmark.** It holds all 20, equally weighted, the same way.
- **Costs.** Every trade pays 0.15% of the notional traded (a 0.10% taker fee, plus 0.05% of spread and slippage). That
  includes trading back the week's drift.
- **The question.** The weekly difference: the book's net minus the benchmark's net.
- **Data.** Binance spot daily klines (`data.binance.vision`), for every USDT pair the archive lists, delisted ones
  included. Each monthly archive is checked against its published sha256. A month that cannot be fetched or checked
  stops the judge; it is never filled.

## Periods

| Role | Period | Weeks |
|---|---|---|
| Development | 2018-10-01 → 2021-12-31 | |
| Validation | 2022-01-01 → 2024-06-30 | |
| Judged (significance) | 2018-10-01 → 2024-06-30 | 299 |
| Holdout | 2024-07-01 → 2026-09-30. The judge cuts its data there and never reads it. It is opened once, only if XSM-1 PASSED, as its own registered trial (XSM-1-H) | 116 |

## Gates (all required)

| Gate | |
|---|---|
| t | t of the mean weekly difference over the judged period ≥ 3.144 |
| development | mean weekly difference > 0 in 2018-10 to 2021 |
| validation | mean weekly difference > 0 in 2022 to 2024-06 |
| costs ×2 | mean weekly difference > 0 with the cost doubled |
| book pays | the book's own mean weekly net > 0 over the judged period |
| top year | no calendar year supplies more than 50% of the total difference |

**Holdout rule.** Over 2024-07 to 2026-09, all three of these must hold. Then it is VALIDATED; otherwise it is
REJECTED.

- the mean weekly difference > 0, with one-sided t ≥ 1.645;
- the mean weekly difference > 0 with the cost doubled;
- the book's own mean weekly net > 0.

**Reported, never gates.**

- The book's and the benchmark's own statistics, with their annual figures and worst drawdowns.
- Each year.
- The coins held most often.
- The weeks without a trade, and the coin-weeks that ended early.

## After the result

- **PASSED and VALIDATED.** It is proposed to the owner as a paper strategy of its own (CLAUDE.md rule 14). The risk
  engine sizes it, and it is followed forward on paper apart from every other record. Never real money.
- **Anything else.** It is reported as it is, and nothing changes.

## Power, declared

- **The bar.** With 299 weeks, t ≥ 3.144 needs a weekly mean of about 0.18 times the difference's weekly standard
  deviation. That is a Sharpe ratio of about 1.3 a year on the difference.
- **What that means.** If the difference moves about 6% a week, the book must beat the 20 by about 1.1% a week.
- **The likely outcome.** Only an effect near the published one, surviving among large coins, can pass. A smaller real
  effect would FAIL here, and that would be reported as it is.
