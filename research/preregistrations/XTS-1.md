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
