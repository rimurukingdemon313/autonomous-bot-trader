# RADAR-1: live cross-venue funding radar, paper forward test (preregistration)

| | |
|---|---|
| Code | `aitrader/radar/{__init__,core,venues}.py` (radar-1.0.0, radar-venues-1.0.0), `scripts/radar_run.py` |
| Code sha256 | `d6690e181dbcd6a5e131a88b9b2b7912807429f8b6ea57a1e2dd1551e6112763` (`python scripts/radar_judge.py hash`) |
| Runs | `.github/workflows/radar.yml`, hourly on GitHub's runner; ledger and report on the `radar-data` branch |
| Tests | `tests/unit/test_radar.py`, `tests/unit/test_radar_run.py` |
| Counted tests | 1 |
| Data | live, forward only: nothing before the first run exists for this test, so nothing can have been seen |

## Why this, after CR-1 … CR-5

Every historical crypto carry test failed the same way. A funding premium visible in one period was competed down
to roughly the cost of capital within one or two years (`docs/NEW_EDGE_REPORT.md`, CR addenda). A backtest can
only find premiums that have already been arbitraged away.

The only version of the idea a backtest cannot refute is to catch **new** dislocations while they exist. That is
measured live, which is what this test does.

The live parser check (`research/results/radar-check.json`, 2026-10-07) showed the following, from one snapshot
of current rates and no P&L of any kind:
- the four venues parse correctly;
- 35 coins are liquid (≥ $10M a day) on two or more venues;
- 6 of them currently show a gap of 25%/yr or more.

The rules below were fixed before that snapshot and were not changed after it.

## Mechanism

Funding is set separately on each venue, from each venue's own order flow:
- Hyperliquid's long-biased on-chain clientele;
- Gate's and MEXC's retail flow;
- dYdX's oracle-based market.

Arbitrage between them needs:
- capital on both venues;
- margin management on two independent liquidation engines;
- willingness to carry venue risk.

The gap is the price of those frictions. When a new coin lists, or a narrative hits one venue's users, the gap
widens before capital moves.

## Rules (`Rules()` defaults in `aitrader/radar/core.py`; frozen by the code hash)

| | |
|---|---|
| Venues | Hyperliquid, Gate, MEXC, dYdX, through public endpoints only. Binance and Bybit refuse the runner (`research/results/radar-probe.json`) |
| Universe | every coin quoted on ≥ 2 venues; per venue the most traded contract; both legs ≥ $10M 24 h notional; prices within 2% after contract scale. A different token under the same ticker fails that check |
| Entry | the 72 h trailing spread (mean of the radar's own hourly snapshots, ≥ 80% coverage, watched for the full 72 h) is ≥ 25%/yr, and the current spread is ≥ 15%/yr. Short the venue paying more, long the other, equal notional N |
| Book | at most 10 positions, one per coin, best trailing spread first |
| Exit | the 24 h trailing spread falls below 5%/yr; or the current spread falls below −10%/yr; or the position is 30 days old; or either leg has moved 25% (margin must be rebalanced: close, may re-enter); or a leg's venue has been missing 24 h |
| Funding | accrued every run at the mean of the previous and current per-hour rate of each leg (a declared approximation of the settlements) |
| Price P&L | from both legs' marks, which are quoted live |
| Costs | per fill: the venue's taker fee (Hyperliquid 4.5, Gate 5, MEXC 2, dYdX 5 bp) plus 5 bp of spread and slippage. Entry and exit are both charged; open positions are valued as if closed now |
| Capital | 2N per slot × 10 slots (1× margin on each leg). Idle capital is assumed to earn the risk-free rate |
| Risk-free | 3.875%/yr (US policy rate, BIS, last value 2026-09-22), declared |

## The single look

The runner freezes the verdict **once**: at the first run 60 days after the first run, it writes
`RADAR-1-look1.json` on `radar-data`. It is never rewritten. Peeking at the hourly report changes nothing,
because no decision is taken from it.

If fewer than 30 positions have closed by the look, the result is INCONCLUSIVE. One extension to day 120 is
then allowed (`RADAR-1-look2.json`), with a stricter t ≥ 2.5. Otherwise the look at day 60 is final.

At the look, **every** gate is required:

| Gate | Threshold |
|---|---|
| Annualised excess over cash on the capital deployed (net of all costs, closing included) | ≥ 10%/yr |
| t-statistic of the book's daily excess | ≥ 2.0 (2.5 at the extension) |
| Excess on deployed capital with costs × 1.5 | > 0 |
| Book excess without the single best coin | > 0 |
| Max drawdown of the book (hourly marks, on total capital) | ≤ 10% |
| Hourly runs present | ≥ 90% |

`python scripts/radar_judge.py verdict RADAR-1-lookN.json` records the frozen look in the registry. It refuses
if the radar code no longer matches the hash above.

## Labels

| Label | Requires |
|---|---|
| PROMISING BUT NOT YET PROVEN | every gate passes. That is the best a paper test can earn: it has no real fills, no queue position, no margin calls and no transfers |
| ROBUST EDGE FOUND | PROMISING, then a second 60-day stage with **real** fills on the user's own accounts, at a size the user chooses, executed by the user. Same rules, same gates, net of the fees actually paid |
| NO ROBUST EDGE FOUND | anything else |

## Risks no paper ledger captures

- **Venue failure:** insolvency, a withdrawal freeze, a smart-contract or bridge hack. Delta-neutral across two
  venues means the **whole** margin on the failed venue is exposed. This is the main risk, and the reason the
  hurdle is cash + 10%, not cash.
- **Auto-deleveraging or liquidation of one leg in a fast move:** the 25% rebalance rule assumes it was done in
  time.
- **Funding caps and formula changes**, set by each venue at will.
- **Moving collateral** between venues costs time and fees. They are not modelled beyond the 25% rebalance.
- **Taker fees** are the base tier. Spreads on small coins can exceed 5 bp.

## Forbidden

- changing any rule, threshold, venue, cost or gate after the first run (the code hash enforces it);
- a second RADAR-1;
- reading a verdict from any day other than the frozen look;
- adding the paper result to anything as evidence of an edge before the real-fills stage.
