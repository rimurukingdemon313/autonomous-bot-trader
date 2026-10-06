# CR-1: funding-rate carry and time-series momentum on Binance USDT-M perpetuals (preregistration)

| | |
|---|---|
| Frozen spec | `research/specs/CR-1.json` |
| Spec sha256 | `ef6707fb6892abf113234a14aeef32be5533eaeca3316268d392e8fd7d60e2b6` |
| Code | `aitrader/research/crypto/cr.py` (cr-1.0.0), `aitrader/research/canon/validate.py`, `scripts/cr1.py`, `scripts/ingest_binance.py` |
| Tests that prove the code | `tests/unit/test_cr.py` (13), `tests/unit/test_cr1_runner.py` (2: noise promotes nothing, a planted premium is found) |
| Run | `python scripts/cr1.py develop` once; `validate` once, promoted families only |
| Counted tests | 8 configurations |
| Validation threshold | t ≥ **3.6878**: Bonferroni over every registered test plus these 8 |

Written before any Binance price or funding value was downloaded. The probe (`research/results/cr-probe.json`)
read only symbol names, first and last months, and file formats.

## Why crypto perpetuals, after everything else failed

Every earlier program failed on the same arithmetic: a retail round trip in FX or index CFDs is 3–20% of the
move a short-horizon signal can predict.

Two things are different here:

1. **The carry's cash flow is observed, not predicted.** Funding is paid every 8 hours by one side of the
   perpetual to the other. It is published, so financing needs no approximation.
2. **Holding periods are long relative to the cost.**
   - The carry pays about 38–42 bp per round trip (two legs) against funding that has historically averaged
     ~10–30% a year in bull phases.
   - Momentum pays about 7–8 bp per flip against daily moves of 300–500 bp.

Neither family has been tested in this repository. The universe `crypto-binance-usdtm` has never been
loaded.

## Family CARRY: funding-rate carry (cash-and-carry)

**Mechanism.** Leveraged retail demand for long perpetual exposure keeps perpetuals above spot. The funding
mechanism transfers that premium from longs to shorts. A delta-neutral holder (long spot, short perpetual)
collects it.

- He, Manela, Ross & von Wachter, "Fundamentals of Perpetual Futures" (2022–2024), report large Sharpe
  ratios even at the highest Binance fee tier.
- They also report that deviations **diminish over time**, so decay is a live risk and is what the
  2023–2024 validation and the sealed 2025–2026 holdout test.

**Why it may persist (limits to arbitrage).** Capital is locked in two venues' margin, there is exchange
counterparty risk, liquidation risk on the short leg, and regulatory restrictions on who can hold both legs.

**Expected size and cost.**

- Gross: the funding collected minus basis drift, with positive expectancy only while funding is positive.
- Cost: 2 × (10 fee + 2 half-spread + 1 slippage) on spot plus 2 × (5 + 2 + 1) on the perpetual = 42 bp
  per round trip; 38 bp for BTC and ETH.
- A forced rebalance (the perpetual rising 80% above entry) costs one more full round trip.

**Rules:**

| | |
|---|---|
| Signal | at each funding settlement T, the mean of the last k funding rates (including T's), known at T |
| Open | if flat and the mean ≥ θ_in: long spot and short perpetual, equal notional N, at the first hour bar at or after T + 1 h on which both legs have a bar |
| Close | if open and the mean < θ_out (0): both legs at the first common bar at or after T + 1 h |
| Funding | every settlement strictly between entry and exit, at the published rate (positive is received by the short) |
| Capital | 2N per coin (spot N, perpetual margin N: 1× short) |
| Primary | k = 3, θ_in = 0.01% per settlement (1 bp, Binance's default interest component) |
| Neighbours (all count) | k = 1 and k = 9 at θ_in 0.01%; θ_in 0.005% and 0.02% at k = 3 |

## Family TSMOM: time-series momentum on the perpetual

**Mechanism.** In crypto, time-series momentum at 1–8-week horizons is documented (Liu & Tsyvinski 2021;
later trend-following studies). The attributed cause is slow diffusion of information to a retail-dominated
investor base with no fundamental anchor.

**The honest counter-evidence.** Several studies find momentum profits shrink after transaction costs and
out of sample. This test pays the actual funding a long or short position paid.

**Expected size and cost.** Gross is unknown. Cost is 2 × (5 + 2 + 1) = 16 bp per position (2 × 7 bp for
BTC and ETH), plus funding paid while long in bull markets (often 10–30% a year).

**Rules:**

| | |
|---|---|
| Signal | at each 00:00 UTC, the sign of the perpetual's return from its 00:00 open L days earlier to today's 00:00 open |
| Trade | hold the perpetual in that direction. A change of sign closes and reopens at the first bar at or after 01:00 UTC |
| Funding | a long pays and a short receives the published rate at every settlement held |
| Capital | N per coin (1×) |
| Primary | L = 28 days |
| Neighbours | L = 14, 56 |

## Common to both

### Universe (point-in-time, decided by a rule before any price was seen)

The USDT-M perpetuals whose funding archive begins in the archive's first month (2020-01):

ADA, BCH, BTC, EOS, ETC, ETH, LINK, LTC, TRX, XLM, XRP.

None was delisted, so there is no survivorship gap. Coins listed later are excluded by the rule, not by
their outcomes.

### Data

Binance public archives (data.binance.vision), monthly files verified against their published SHA-256:

- 1-hour spot klines;
- 1-hour USDT-M perpetual klines;
- funding settlements.

Fetched on a GitHub runner, **2020-01 → 2024-12 only**.

### Periods

| Period | Role | Dates |
|---|---|---|
| Development | select | 2020-01-01 → 2023-01-01 (includes the 2021 bull, the 2022 crash and FTX) |
| Validation | judge | 2023-01-01 → 2025-01-01: promoted families and their neighbours, once |
| Sealed holdout | not fetched | 2025-01-01 → 2026-10-01 |

**Holdout rule** for validation passers only, under a separate registration, with the data fetched only
then:

- net > 0;
- costs × 1.5 net > 0;
- latency net > 0;
- t ≥ 1.645.

### Costs (declared; stressed ×1.25, ×1.5 and ×2)

| Cost | Value |
|---|---|
| Fees (Binance VIP 0, taker) | spot 10 bp, perpetual 5 bp per side. The perpetual taker fee was 4 bp in part of 2020–2021, so 5 bp is conservative there |
| Half-spread | 1 bp for BTC and ETH, 2 bp otherwise. No public historical bid/ask exists: a declared approximation |
| Slippage | 1 bp per fill |
| Latency stress | every fill one more hour late |
| Funding | exact |
| Idle capital | earns nothing (conservative) |

### Accounting

- A daily mark-to-market at 00:00 UTC per coin, as a fraction of the coin's capital.
- The portfolio is equal capital per coin.
- Statistics are on the daily portfolio return; positions are reported too.

### Promotion from development (the primary of each family; all required)

| Gate | Requirement |
|---|---|
| min_days | ≥ 500 |
| min_positions | ≥ 100 |
| net | annualised net return > 0 |
| t_day | ≥ 2.0 |
| costs_x1.25 | net > 0 |
| costs_x1.5 | net > 0 |
| latency | net > 0 |
| vs_placebo | CARRY: Welch t ≥ 2.0 of position net against random-timing positions with the same per-coin count and durations (seeds 1–3). TSMOM: Welch t ≥ 2.0 of daily returns against random daily sides (seeds 1–3), and block permutation of sides p ≤ 0.05 |
| without_top5_days | net > 0 |
| neighbours | every other configuration of the family net > 0 |
| halves | both chronological halves net > 0 |

### Validation (all required)

All the development gates, with **t ≥ 3.6878**, plus:

- 2023 and 2024 each net > 0;
- ≥ 6 of 11 coins net > 0;
- block-bootstrap P(total ≤ 0) ≤ 0.05;
- total / maximum drawdown ≥ 1.0.

### Reported, never gated

- always-on carry;
- equal-weight spot buy-and-hold;
- no signal;
- costs × 2;
- position statistics: funding, basis, cost, win rate and median holding period;
- forced rebalances;
- per-coin and per-year results;
- the Monte Carlo distribution.

### Execution, honestly

No crypto broker adapter exists in this repository. A passing family is **PROMISING BUT NOT YET PROVEN**
until:

- a paper adapter on Binance's public market data and testnet records real quotes and fills, forward, for
  a preregistered period;
- the sealed holdout passes.

Nothing here sizes a live trade: the risk engine remains the only sizing authority.

### Forbidden, by this document

- changing a rule, a cost, a coin or a gate after any result;
- adding configurations;
- fetching 2025 or later before validation passes;
- a second run.
