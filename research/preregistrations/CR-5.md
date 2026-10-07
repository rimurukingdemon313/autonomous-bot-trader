# CR-5: static BTC/ETH cross-venue carry, short Hyperliquid / long Binance (preregistration)

| | |
|---|---|
| Frozen spec | `research/specs/CR-5.json` |
| Spec sha256 | `0e52b84552f3e2b8f694fa66a16c77f2b10e2c0ab288a31dd1aabd95aa262689` |
| Code | `scripts/cr5.py`, `aitrader/research/crypto/xv.py` (xv-1.0.0), `scripts/ingest_xv_window.py` |
| Tests | `tests/unit/test_cr5.py`: a steady gap beats cash at 3×, no gap does not; a large move rolls the position |
| Counted tests | 1 |

## How this hypothesis was formed (stated plainly)

CR-4 FAILED validation:

- its signal-driven book, across 100+ coins, lost money to small-coin tails (MAVIA, ORBS, FTT) and costs;
- the funding gap per position shrank by three-quarters.

**After that verdict**, as declared exploration of data already seen (2023-06 → 2025-06), the gap between the
two venues' funding on the largest coins was measured.

| | HL above Binance, 2023-06 → 2024-06 | 2024-07 → 2025-06 | Share of days positive |
|---|---|---|---|
| BTC | +10.7%/yr | +8.0%/yr | 72%, then 87% |
| ETH | +12.8%/yr | +4.6%/yr | 77%, then 66% |

So 2023-06 → 2025-06 is **"select"** here. It cannot judge this hypothesis.

**The judge is 2025-07-01 → 2026-09-29.** No price or funding value of that period has been fetched by this
project. BTC and ETH were chosen because they are the predefined "majors" tier of the cost model, fixed
before any data existed, not because of their numbers. SOL, BNB and DOGE showed similar gaps, and XRP was
negative in 2023–24. They are excluded by that rule, not added.

## Mechanism

Hyperliquid's funding formula and user base differ from Binance's:

- an impact-price premium;
- hourly accrual;
- an on-chain, long-biased clientele.

The same leverage demand is priced higher there. Capital that would arbitrage it must sit on an on-chain venue,
with bridge and smart-contract risk. That is a limit to arbitrage, and the persistent gap is its price.

## Rules

| | |
|---|---|
| Position | on BTC and ETH, always short the Hyperliquid perpetual and long the Binance USDT-M perpetual, equal notional N |
| Start | the first common daily open in the period |
| Rolls | when either leg's price is ≥ 25% away from its value at the position's last (re)open, close and reopen at that daily open: one full round trip on both legs |
| End | the last common daily open in the period |
| Funding | both venues' actual settlements |
| Costs | per fill: Hyperliquid taker 4.5 bp, Binance taker 5 bp, half-spread 1 bp, slippage 1 bp; ×1.5 stress |
| Capital | 2N / 3 per coin: 3× margin on each venue, the standard for a hedged position. Returns at 1× are reported, never gated |
| Excess | return on capital − US policy rate (BIS, public that day) / 365 |

## Development (2023-06-01 → 2025-07-01, already seen; all required)

- excess > 0;
- t ≥ 2.0;
- excess > 0 at costs × 1.5;
- both 12-month halves excess > 0;
- drawdown ≤ 15%.

Development is a consistency check of the rules on the data that suggested them. **Passing it proves
nothing.**

## Holdout (2025-07-01 → 2026-09-29, fetched only if development passes; all required)

- excess > 0;
- t ≥ 2.0;
- excess > 0 at costs × 1.5;
- drawdown ≤ 15%;
- block-bootstrap P(total ≤ 0) ≤ 0.05.

## Labels

| Label | Requires |
|---|---|
| PROMISING BUT NOT YET PROVEN | the holdout passes; then a forward paper test with live quotes and recorded fills on both venues |
| NO ROBUST EDGE FOUND | anything else |

## Risks no backtest captures

- Hyperliquid failure (bridge, contract, validator set);
- Binance insolvency or withdrawal freeze;
- auto-deleveraging;
- a regime where the gap reverses for months;
- the cost of moving collateral between venues during a fast market.

## Forbidden

- changing coins, side, leverage, roll rule, costs or gates after any result;
- fetching 2025-07 or later before development passes;
- a second run.
