# CR-3: cross-sectional funding carry over the point-in-time Binance universe (preregistration)

| | |
|---|---|
| Frozen spec | `research/specs/CR-3.json` |
| Spec sha256 | `f90a63a59bc454377b0ce087a2f3f0a70a12cb096fb7f0b6960aa285ff4c9d9f` |
| Code | `aitrader/research/crypto/xs.py` (xs-1.0.0), `cr.py` (cr-1.0.0), `scripts/cr3.py`, `scripts/ingest_binance_xs.py` |
| Tests | `tests/unit/test_xs.py` (7), `tests/unit/test_cr3_runner.py` (noise promotes nothing; a planted premium beats cash) |
| Counted tests | 5 configurations |
| Validation threshold | t ≥ **3.6957** on daily excess returns |

Written before any price or funding value of the coins outside CR-1's eleven was downloaded.

## Why, after CR-1 and CR-2

CR-1 and CR-2 found that funding on the **eleven oldest perpetuals** paid well only in 2020–2021. Since
then it has roughly matched cash.

Those eleven are the most arbitraged contracts on the exchange. A strong carry, if it exists after 2022,
should be where leverage demand is highest and arbitrage capital is thinnest: **the coins whose
perpetuals currently pay the most funding**, typically newer and smaller listings. CR-3 tests that.

This is a different hypothesis, not a variation of CR-1:

| | CR-1 / CR-2 | CR-3 |
|---|---|---|
| Universe | 11 coins fixed by listing date | every perpetual with a spot pair, eligible point-in-time |
| What it bets on | funding level on fixed coins | cross-sectional selection: the top funding payers |
| Costs | 2 cost tiers | a third, wider tier for small coins |

It is judged on **excess return over the risk-free rate** from the start.

## Rules

**Universe (point-in-time):**

- Every USDT-M perpetual with a matching spot pair in the Binance archives
  (`research/results/cr-probe2.json`). A perpetual quoted per 1000 units maps to its plain spot pair.
- A coin is eligible at T only if both its perpetual and its spot have a bar at T and have traded at
  least 30 days.
- Delisted coins are included while they traded. A coin delisted while held is closed at its last
  common bar.

**Score.** At each 00:00, 08:00 and 16:00 UTC, the funding its perpetual paid over the previous 24 hours:
the sum of the settlements in (T − 24 h, T].

**Book:**

- **Slots:** up to `slots` delta-neutral positions (long spot, short perpetual, equal notional), with
  2N capital per slot.
- **Keep:** a held coin is kept while it is eligible, its score is ≥ 0 and it ranks in the top
  2 × `slots`.
- **Fill:** an empty slot takes the best-scored eligible coin not held whose score is ≥ θ_in.
- **Execution:** fills at the first common hour bar ≥ T + 1 h.

**Costs** (declared, stressed ×1.25, ×1.5 and ×2):

| | Half-spread | Slippage |
|---|---|---|
| BTC, ETH | 1 bp | 1 bp |
| CR-1's other 9 coins | 2 bp | 1 bp |
| Every other coin | 5 bp | 3 bp |

- **Fees:** spot 10 bp, perpetual 5 bp per fill.
- **Forced rebalance:** one more full round trip each time the perpetual reaches 1.8× its reference
  price.
- **Funding:** exact.

**Accounting:**

- The daily return on the whole book's capital (2N × slots). Empty slots earn nothing.
- **Excess** = return − US policy rate (BIS, public that day) / 365.

**Configurations:**

| | slots | θ_in (24 h funding) |
|---|---|---|
| **Primary** | 5 | 3 bp |
| Neighbours | 3, 10 | 3 bp |
| Neighbours | 5 | 1.5 bp, 6 bp |

## Periods

| Period | Role | Dates |
|---|---|---|
| Development | select | 2020-01-01 → 2023-01-01 |
| Validation | judge | 2023-01-01 → 2025-01-01, once, only if development promotes |
| Holdout | sealed | 2025-01-01 → 2026-09-29, never fetched. Opened once, only if validation passes |

## Gates (primary configuration)

### Development (all required)

- ≥ 100 positions;
- annualised excess > 0;
- t ≥ 2.0 on daily excess;
- excess > 0 at costs × 1.5;
- excess > 0 with fills one hour later;
- Welch t ≥ 2.0 against **random coin selection** at the same times (seeds 1–3);
- every neighbour's excess > 0;
- ≥ 2 of 3 years with excess > 0;
- maximum drawdown of cumulative excess ≤ 15%;
- excess > 0 without the five best days.

### Validation (all required)

All the development gates, plus:

- t ≥ 3.6957;
- 2023 and 2024 each with excess > 0;
- block-bootstrap P(total excess ≤ 0) ≤ 0.05.

### Holdout (all required)

- excess > 0;
- t ≥ 1.645;
- excess > 0 at costs × 1.5;
- drawdown ≤ 15%.

## Labels

| Label | Requires |
|---|---|
| PROMISING BUT NOT YET PROVEN | holdout passes; then a forward paper test on live quotes with recorded fills |
| NO ROBUST EDGE FOUND | anything else |

## Risks a backtest cannot capture (stated, not modelled)

- exchange default (FTX, 2022);
- withdrawal freezes;
- borrow and short restrictions;
- auto-deleveraging on the perpetual;
- listing and delisting announcements arriving faster than one hour.

## Forbidden

- changing any rule, cost, threshold, coin rule or gate after a result;
- fetching 2025+ early;
- a second run of any stage.
