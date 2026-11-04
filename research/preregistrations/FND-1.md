# FND-1: extreme perpetual funding as crowded leverage (preregistration)

**Written, frozen and registered on 2026-11-04, before any FND-1 data was fetched.** The owner, 2026-11-04: "change
everything if you must; the most important thing is a profit; don't stop; don't fool me with promises".

| | |
|---|---|
| Frozen spec | `research/specs/FND-1.json` |
| Spec sha256 | `86590f1005d9460547071f73432db17671081da872d38a234b2f9771d8e17ddc` |
| Code | `scripts/fnd1.py` and `scripts/xts1.py` (whose fetch and statistics it reuses), sha256 `8dd89162717fe12dca104b65465cde64da454231acce61cdda5f6fade9e0f519` (every command refuses to run if either changes) |
| Run | `.github/workflows/fnd1-run.yml` on GitHub's runner (this environment cannot reach Binance): `fetch`, `judge`, and `holdout` only if `judge` PASSED |
| Threshold | t ≥ **3.11**: the Bonferroni value for the 25 earlier crypto tests in the registry (XTS-1 included) plus these 2 |

## Why this question

CR-1 to CR-5 harvested funding, either delta-neutral carry or the spread between venues. None used funding as a
signal for the coins' direction (their preregistrations, and `research/registry.jsonl`).

- Funding is what leveraged longs pay shorts at each settlement. Binance's baseline is 0.01% a settlement (about 11%
  a year).
- When it runs far above that, long leverage is crowded, and crowded leverage unwinds in liquidations. Schmeling,
  Schrimpf & Todorov (2023, "Crypto Carry") find high carry comes with crash risk.
- The rule stands aside then.
- The mechanism is not momentum. Crowding is a reason a rise ends, not a reason it continues.

## The rule (fixed; nothing is tuned)

- **Signal.** Each day at the daily close (00:00 UTC), for BTCUSDT and ETHUSDT: F is the mean of the coin's USDT-M
  funding settlements published in the 7 days before that close, the settlement at the decision time excluded. It
  needs at least 18 of the usual 21 settlements.
- **Exposure.** F above **0.03%** a settlement (three times the baseline, about 33% a year): flat over the next day.
  Otherwise long. Never short.
- **Returns.** Spot close to close. Each coin gets half the capital.
- **Costs.** A change of exposure pays 0.15% of the notional traded, as in XTS-1.
- **Missing data.** A day without its prices or its settlements is no trade, never filled.
- **Data.** Binance spot daily klines and USDT-M funding settlements (`data.binance.vision`), each monthly archive
  checked against its published sha256. A month that cannot be fetched or checked stops the judge.

## Periods

| Role | Period |
|---|---|
| Development | 2020-01-01 → 2022-06-30 |
| Validation | 2022-07-01 → 2024-06-30 |
| Judged (significance) | 2020-01-01 → 2024-06-30 |
| Holdout | 2024-07-01 → 2026-09-30. The judge cuts its data there. Opened once, only if FND-1 PASSED, as its own trial (FND-1-H) |

## Gates (all required)

The same gates as XTS-1, so the two can be read side by side.

| Gate | |
|---|---|
| t | t of the mean daily net return of the two-coin book ≥ 3.11 |
| development | mean daily net > 0 in 2020-01 to 2022-06 |
| validation | mean daily net > 0 in 2022-07 to 2024-06 |
| costs ×2 | mean daily net > 0 with the cost doubled |
| leave one coin out | mean daily net > 0 for BTC alone and for ETH alone |
| top year | no calendar year supplies more than 50% of the total net |
| timing | the book beats holding each coin at its own average exposure: mean daily difference > 0 with t ≥ 2.0 |

The timing gate is the one that tells skill from the market's rise.

**Holdout rule.** Over 2024-07 to 2026-09:

- mean daily net > 0, with one-sided t ≥ 1.645;
- mean daily net > 0 with the cost doubled;
- the timing difference's mean > 0.

## After the result

- **PASSED and VALIDATED.** It is proposed to the owner as a paper strategy of its own (CLAUDE.md rule 14), sized by
  the risk engine and followed forward on paper. Never real money.
- **Anything else.** It is reported as it is. Nothing changes.

## Known before freezing, said now

- **Power.** The rule is long most days, so its own t will be close to buy and hold's. XTS-1 measured that at about
  1.8 for each coin, from 2018. The t gate may well fail even if the timing is real, and it is kept, because a profit
  is the question.
- **Exposure to these years.** XTS-1 has already been judged on these coins and years (2018-2024), with momentum.
  These years are not unseen data, and FND-1's threshold counts it.
