# BAS-1: does the arbitrage that high funding attracts lift the spot price?

Preregistered on 2026-11-15, after SQZ-1 and CASC-1 failed and before any price of BAS-1's validation window is read.

| | |
|---|---|
| Program | BAS-1, stages `dev`, `validation`, `forward`, judged once each, in that order |
| Code sha256 | `3daad78fc56ab66890df96f5951eb1ea551fed99d43aee7014962d7e5f010c52` (`python scripts/bas1.py hash`, first value; it covers SQZ-1's frozen `squeeze.py` and `sqz1.py`, whose signal, benchmark, judge and readers it uses unchanged) |
| Spec sha256 | `47def52bde2a79d0ee551a777f8b499437b5da29f05d23678b1a9a1c74d21100` (the `SPEC` in `scripts/bas1.py`; second value) |
| Universe | `crypto-spot-high-funding`: new in the registry. Bar max(3.0, Bonferroni): 3.0 |
| Instrument | **spot, bought outright**, long only: no leverage, no short, no funding paid or received |

## 1. The mechanism, and why now

High funding is what leveraged longs pay shorts to keep their positions. It is also the yield of cash and carry:
an arbitrageur earns it by buying the coin's spot and shorting its perpetual, so high funding draws arbitrage
capital whose first leg is a spot purchase. The leveraged demand that pushes funding up is itself trend-following
(Schmeling, Schrimpf & Todorov's account of crypto carry, known here from search results: small trend-chasing
investors seeking leverage, and arbitrage capital limited by margin frictions). Both should lift the coin's spot
against the market while funding stays high. **The opposite force:** crowded longs end in liquidations; crypto
carry is crash-prone.

**Why now (declared, because it shaped the choice):** today's four failures all point the same way. New listings
kept falling (NEWL-1, median), crowded shorts were right (SQZ-1), liquidation-led falls kept falling (CASC-1), and
the price passed on funding payments (EXF-1). Pressure in crypto has continued rather than reverted. This is the
long side of that observation, the only side the Islamic condition allows. It was formed after seeing those
results, so it is judged where none of them read: its validation window, 2025-03-08 to 2026-10-24, holds spot
prices no study here has read.

## 2. What is known, and how this differs

- The carry programs CR-1 to CR-5 earned the funding itself, delta-neutral: FAILED. BAS-1 earns no funding; it
  holds the spot that carry capital buys.
- FND-1 and FND-1A stood aside in BTC and ETH when longs were crowded and lost to holding (the timing was negative):
  the crowded-long periods paid. BAS-1 asks whether that holds across every seasoned coin, long only.
- A 2025 study of crypto asset pricing is reported (search result only, not read) to use the carry strategy with
  Binance funding as one input; whether high-funding coins then beat the market on spot is not known here.

## 3. Declared prior

About one chance in five. The direction is suggested by today's failures, which is a reason for caution: a story
fitted to what was just seen is the cheapest kind.

## 4. Definitions (frozen in the code)

SQZ-1's, on the other tail: the seasoned coins of SQZ-1's probe (480 with spot pairs); at 00:00 UTC of day d the
funding settled over the 72 hours before, per 8 hours; if it is at least +theta (0.03%, 0.05% or 0.1%; dev chooses),
buy spot at the close of d-1 and sell at the close of d+6; one position per coin; 0.15% a side; against the
equal-weight spot return of every seasoned coin over the same days; weekly cohorts, Newey-West t (lag 2); the
placebo is the same coin on days within 30 whose signal was below theta/2.

## 5. Stages

| Stage | Trial | Entries | Thresholds | Minimum | Runs only after |
|---|---|---|---|---|---|
| dev | BAS-1 | 2021-01-01 to 2025-02-28 (spot prices SQZ-1 and CASC-1 read for other signals; declared) | 0.03%, 0.05%, 0.1% (3 tests) | 300 entries, 52 weeks | registration |
| validation | BAS-1-V | 2025-03-08 to 2026-10-24 (no study has read these prices) | the one dev chose | 150, 40 | BAS-1 PASSED |
| forward | BAS-1-F | 2026-12-01 to 2027-05-24 | the same | 60, 10 | BAS-1-V PASSED, on or after 2027-06-10 |

## 6. Gates (every one required)

SQZ-1's: t >= 3.0; costs doubled; both halves; the five best entries, the best year and the best coin removed; a day
later; above the 95th percentile of the placebo. Too few is INCONCLUSIVE, never a pass.

## 7. Power

The EXF-1 probe counted, among settlements whose previous rate was at least 0.05% in absolute value, 30,464 in
2021, 6,789 in 2022, 7,561 in 2023, 21,107 in 2024 and 45,095 in 2025 (both signs; most are positive). Entries are
far fewer (seven-day holds, one per coin), but dev should hold thousands at 0.03% and hundreds at 0.1%. With a
seven-day excess standard deviation near 12% and many entries a week, t 3.0 needs roughly 0.5% to 1% a week net.

## 8. What follows

dev FAILED or INCONCLUSIVE: recorded, nothing later. dev PASSED: BAS-1-V once on unread prices, then the forward
stage. Only a rule that passes all three is proposed to the owner, as a paper strategy on spot.

## 9. Limits, declared

Dev's prices were read by SQZ-1 (2021-01 to 2023-07, daily closes) and CASC-1 (2023-06 to 2025-03, hourly bars)
for other signals; only the validation and forward stages are blind. Survivorship and costs as in SQZ-1.
