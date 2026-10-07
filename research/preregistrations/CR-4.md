# CR-4: cross-venue funding differential, Hyperliquid vs Binance (preregistration)

| | |
|---|---|
| Frozen spec | `research/specs/CR-4.json` |
| Spec sha256 | `d28442f73f4e70e2b93fae176a1cd26fd1d5b401fc0b9ce67f758ae129b9f6f4` |
| Code | `aitrader/research/crypto/xv.py` (xv-1.0.0), `scripts/cr4.py`, `scripts/ingest_xv.py` |
| Tests | `tests/unit/test_xv.py` (8), `tests/unit/test_cr4_runner.py` (no gap promotes nothing; a planted gap beats cash) |
| Counted tests | 5 configurations |
| Validation threshold | t ≥ **3.7012** on daily excess returns |

Written before any Hyperliquid funding rate or price was downloaded. The probe
(`research/results/cr-probe-hl.json`) read only coin names, listing times and record counts.

## Why

CR-1 to CR-3 showed that **one venue's** funding premium has been competed down to about the risk-free rate
since 2022.

The same coin's perpetual on **two venues** can still pay different funding:

- different premium formulas (Hyperliquid's impact price vs Binance's top of book);
- different funding intervals (hourly vs 8-hourly);
- different user bases (on-chain vs centralised);
- capital that cannot move freely between a decentralised exchange and a centralised one.

Practitioner write-ups report 6–11% APR on BTC and ETH between these two venues. Those are marketing
sources, not evidence; this test exists to check them. Both legs are perpetuals on the same coin, so the
book is **market-neutral**.

## Rules

**Universe (point-in-time):**

- Every Hyperliquid perpetual, delisted ones included, whose coin also trades as a Binance USDT-M
  perpetual. Name mapping: X → XUSDT, else 1000XUSDT; Hyperliquid's kX (per 1000) → 1000XUSDT.
- Eligible at 00:00 UTC on day D when both venues have a daily candle at D and 30 days of prices and
  funding.

**Signal.** diff(D) = the mean over the last 7 complete days of (Hyperliquid funding paid that day −
Binance funding paid that day).

- A day counts only with ≥ 20 of Hyperliquid's 24 hourly settlements and ≥ 2 of Binance's. Otherwise the
  coin has no signal that day.
- Missing data is never read as zero.

**Book:**

| | Rule |
|---|---|
| Size | up to `slots` positions |
| Open | best \|diff\| first, if \|diff\| ≥ θ_in. Side: diff > 0 means short Hyperliquid and long Binance; diff < 0 the reverse |
| Close | \|diff\| < θ_out (1 bp a day), or the sign of diff flips, or the data ends (closed at the last common daily open) |
| Fills | the next daily open (one full day of latency) |

**P&L:**

- **Funding:** both venues' actual settlements while held.
- **Basis:** the difference of the two perpetuals' returns.
- **Costs per fill and leg:**
  - Hyperliquid taker 4.5 bp, Binance taker 5 bp;
  - half-spread and slippage 1 bp + 1 bp for BTC and ETH, 3 bp + 2 bp otherwise (declared);
  - stressed ×1.25, ×1.5 and ×2.
- **Forced rebalance:** either leg's price at 1.8× its reference adds one full round trip.
- **Capital:** 2N per position (1× margin on each venue). Returns are also reported at 3×, never gated.

**Excess** = return − US policy rate (BIS, public that day) / 365.

**Configurations:**

| | slots | θ_in (per day) | θ_out | lookback |
|---|---|---|---|---|
| **Primary** | 10 | 3 bp | 1 bp | 7 days |
| Neighbours | 5 and 20 | 3 bp | 1 bp | 7 days |
| Neighbours | 10 | 1.5 bp and 6 bp | 1 bp | 7 days |

## Periods

| Period | Role | Dates |
|---|---|---|
| Development | select | 2023-06-01 → 2024-07-01 |
| Validation | judge | 2024-07-01 → 2025-07-01, once, only if development promotes |
| Holdout | sealed | 2025-07-01 → 2026-09-29, never fetched. Opened once, only if validation passes |

## Gates (primary)

### Development (all required)

- ≥ 100 positions;
- excess > 0;
- t ≥ 2.0;
- excess > 0 at costs × 1.5;
- excess > 0 with one more day of latency;
- Welch t ≥ 2.0 against a random coin and side at the same times (seeds 1–3);
- every neighbour's excess > 0;
- both halves' excess > 0;
- maximum drawdown of cumulative excess ≤ 15%;
- excess > 0 without the five best days.

### Validation (all required)

All of the above, plus:

- t ≥ 3.7012;
- block-bootstrap P(total ≤ 0) ≤ 0.05.

### Holdout (all required)

- excess > 0;
- t ≥ 1.645;
- excess > 0 at costs × 1.5;
- drawdown ≤ 15%.

## Labels

| Label | Requires |
|---|---|
| PROMISING BUT NOT YET PROVEN | holdout passes; then a forward paper test on live quotes and fills |
| NO ROBUST EDGE FOUND | anything else |

## Risks no backtest captures (stated, not modelled)

- Hyperliquid smart-contract or bridge failure;
- exchange insolvency;
- auto-deleveraging;
- oracle manipulation on small coins;
- withdrawal limits that stop rebalancing between venues.

## Forbidden

- changing any rule, cost, coin rule, threshold or gate after a result;
- fetching 2025-07 or later before validation passes;
- a second run of any stage.
