# XTS-1: time-series momentum in bitcoin and ether (preregistration)

**Written, frozen and registered on 2026-11-04, before any XTS-1 data was fetched.** The owner, 2026-11-04: "change
everything if you must; the most important thing is a profit; don't stop; don't fool me with promises".

| | |
|---|---|
| Frozen spec | `research/specs/XTS-1.json` |
| Spec sha256 | `6c92d8b532457536ae16ea1d866c556339cef350f47e248e11523815e049ae0a` |
| Code | `scripts/xts1.py`, sha256 `629138aff11632cbfef3c12725e5a75c2885150bc31f6cb240b7fdb7eae83632` (every command refuses to run if either changes) |
| Run | `.github/workflows/xts1-run.yml` on GitHub's runner (this environment cannot reach Binance): `fetch`, `judge`, and `holdout` only if `judge` PASSED |
| Threshold | t ≥ **3.09**: the Bonferroni value for the 23 earlier crypto tests in the registry plus these 2, and never below 3.0 |

## Why this question

The project has tested about 50 ideas, on FX, equity indices and crypto funding carry. None survived costs since
2008 (`research/registry.jsonl`). Momentum in crypto prices was never tested here:

- The literature finds it strong at horizons of one to four weeks (Liu & Tsyvinski 2021, "Risks and Returns of
  Cryptocurrency", RFS).
- A market dominated by retail flows is where such an effect could last.
- The two coins are the largest, in 2018 and now, so choosing them is not survivorship.

**Known before freezing, said now so it cannot be explained away later.**

- Both coins rose a great deal over 2018 to 2024. A long-or-flat rule can show a positive return from that rise
  alone, which is why the timing gate exists.
- Trend rules in other markets faded after their publication (DIV-2: about zero since 2008). This one may have too.

## The rule (fixed; nothing is tuned)

- **Exposure.** Each day at the daily close (00:00 UTC), for BTCUSDT and ETHUSDT, the exposure held over the next day
  is the share of the lookbacks 7, 14 and 28 days over which the close rose: 0, 1/3, 2/3 or 1. It is long or flat,
  never short.
- **Capital.** Each coin gets half the capital.
- **Costs.** A change of exposure pays 0.15% of the notional traded: a 0.10% taker fee, plus 0.05% of spread and
  slippage.
- **Missing prices.** A day without its prices (that day's close, or a lookback's) is no trade, never filled. The next
  day traded pays to enter again.
- **Data.** Binance spot daily klines (`data.binance.vision`), each monthly archive checked against its published
  sha256. A month that cannot be fetched or checked stops the judge; it is never filled.

## Periods

| Role | Period |
|---|---|
| Development | 2018-01-01 → 2021-12-31 |
| Validation | 2022-01-01 → 2024-06-30 |
| Judged (significance) | 2018-01-01 → 2024-06-30 |
| Holdout | 2024-07-01 → 2026-09-30. The judge cuts its data there and never reads these prices. Opened once, only if XTS-1 PASSED, as its own registered trial (XTS-1-H) |

## Gates (all required)

| Gate | |
|---|---|
| t | t of the mean daily net return of the two-coin book over the judged period ≥ 3.09 |
| development | mean daily net > 0 in 2018 to 2021 |
| validation | mean daily net > 0 in 2022-01 to 2024-06 |
| costs ×2 | mean daily net > 0 with the cost doubled |
| leave one coin out | mean daily net > 0 for BTC alone and for ETH alone |
| top year | no calendar year supplies more than 50% of the total net |
| timing | the book beats holding each coin at its own average exposure: mean daily difference > 0 with t ≥ 2.0 |

The timing gate is the one that tells skill from the market's rise. The book may earn money only because the coins
rose, but holding them at the same average exposure would have earned that too.

**Holdout rule.** Over 2024-07 to 2026-09:

- mean daily net > 0, with one-sided t ≥ 1.645;
- mean daily net > 0 with the cost doubled;
- the timing difference's mean > 0.

Met, it is VALIDATED; otherwise REJECTED.

**Reported, never gates.**

- Annual return, Sharpe and maximum drawdown.
- Buy and hold.
- Each year.
- The book with a retail CFD's overnight financing of 20% a year on the exposure held.

## After the result

- **PASSED and VALIDATED.** It is proposed to the owner as a paper strategy of its own (CLAUDE.md rule 14). The risk
  engine sizes it, and it is followed forward on paper, apart from every other record. Never real money.
- **Anything else.** It is reported as it is. Nothing changes.
- **Power.** 6.5 years of daily returns is a short sample for a volatile asset. A real but modest effect may well
  fail t ≥ 3.09, and that would be reported, not explained away.

## Result (run 2026-11-04 on GitHub's runner; `research/knowledge/XTS-1.json`)

**FAILED.** Two gates failed, so the holdout stays unread and nothing changes.

- Data: 3,317 days per coin (2017-09-01 to 2026-09-30), and every monthly archive matched its sha256.
- The judged period was 2018-01 to 2024-06 (2,373 days).

| | Mean a day | Annual (arithmetic) | Sharpe | t | Gate |
|---|---|---|---|---|---|
| The book, net | 0.140% | +51% | 1.13 | **2.87** | t ≥ 3.09: **failed** |
| Development 2018-2021 | 0.190% | +69% | 1.35 | 2.71 | > 0: passed |
| Validation 2022-01 to 2024-06 | 0.060% | +22% | 0.65 | 1.03 | > 0: passed |
| Cost doubled | 0.123% | +45% | 0.99 | 2.52 | > 0: passed |
| BTC alone / ETH alone | 0.113% / 0.167% | +41% / +61% | 0.96 / 1.06 | 2.46 / 2.71 | > 0: passed |
| Timing (beyond each coin's average exposure) | 0.059% | +22% | 0.73 | **1.87** | t ≥ 2.0: **failed** |
| Reported: with a CFD's 20% a year financing | 0.111% | +41% | 0.90 | 2.28 | never a gate |
| Reported: buy and hold BTC / ETH | 0.132% / 0.177% | +48% / +64% | 0.69 / 0.72 | 1.76 / 1.84 | never a gate |

**By year** (sum of daily net): 2018 −31%, 2019 +46%, 2020 +150%, 2021 +114%, 2022 −22%, 2023 +52%, 2024 H1 +25%. The
top year supplied 45% of the total. The worst drawdown was −54%.

**What it means, and no more.**

- The rule earned a lot, but the evidence that it beats chance at the registered bar is not there: t 2.87 against
  3.09.
- The timing gate also failed. Timing added 22% a year over holding each coin at the same average exposure, but at
  t 1.87.
- The effect was much weaker in validation (Sharpe 0.65) than in development (1.35), the pattern of an effect that
  fades.
- A drawdown of 54% would have been very hard to hold.
- As registered, the holdout (2024-07 to 2026-09) is not opened for a hypothesis that failed. Testing the same rule
  on it now would have to be registered as a new trial, and it would be biased: what is publicly known of that
  period's market favours a long-or-flat rule. So it is not done.
