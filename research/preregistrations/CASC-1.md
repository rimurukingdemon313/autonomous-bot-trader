# CASC-1: is a liquidation-led crash bought back?

Preregistered on 2026-11-15, before any price of the study is read (the probe read file names only).

| | |
|---|---|
| Program | CASC-1, stages `dev`, `validation`, `forward`, judged once each, in that order |
| Code sha256 | `dfc687fd990236224315109af391193839d87e59dc78128fa1dc10d96050c43c` (`python scripts/casc1.py hash`, first value; it covers `scripts/sqz1.py`, whose readers it uses) |
| Spec sha256 | `970a58518a60f4afea3a167f6c6f0d2304be0fab436effe2cf9ff8306de04da3` (the `SPEC` in `scripts/casc1.py`; second value) |
| Code | `aitrader/research/events/cascade.py`, `scripts/casc1.py`, run by `.github/workflows/casc1.yml` |
| Universe | `crypto-spot-liquidation-falls`: new in the registry. Bar max(3.0, Bonferroni): 3.0 |
| Instrument | **spot, bought outright**, long only: no leverage, no short, no funding. The perpetual's price is information only |
| Data | hourly spot and perpetual bars of 2023-06 onwards: no earlier study here has read an hourly bar of these coins |

## 1. The mechanism

When leveraged longs are liquidated, the exchange's engine sells their perpetuals at market, whatever the price. The
perpetual drops below its own spot price, and arbitrageurs who buy the cheap perpetual and sell spot carry the fall
into spot. That selling is forced, not informed. When it ends, spot should recover part of the fall, and the
long-only spot buyer who bought from the forced sellers is paid for the liquidity.

**Who trades at a bad price:** liquidated longs, sold by the engine at market. **Why competition may not remove it:**
the buyer catches a falling price in the middle of a cascade, when every risk limit says stand aside, in small coins
whose books are thin; capital that could absorb it is itself being deleveraged. **The opposite force:** a crash can
be the market learning bad news, which is not bought back. The perpetual's discount separates the two: a fall in
which the perpetual leads (closes below spot) carries the liquidation signature; a fall in which it never trades at
a discount is led by spot sellers and should not recover. **When it should appear:** after leverage has built up
and a shock trips it. **When it should disappear:** as liquidation engines and market makers absorb cascades better.
**Holding and risk:** 24 hours, long only; the risk is that the cascade continues.

**Relation to expected return.** E[net] = E[r(h, h+24) | the four-hour fall at least X, the perpetual at least
0.5% below spot at h] - 2c. It must exceed both the same coin at hours it had not fallen and falls led by spot.

## 2. What is known, and how this differs

- **In this registry:** LIQ-1 bought BTC and ETH after open interest and price fell beyond their 1st percentiles,
  for 24 hours: FAILED (-0.63% a trade over 83 trades). CASC-1 differs in the instrument (spot, not the contract),
  in the cross-section (every seasoned coin, where cascades move thinner books far more), and in the signature (the
  perpetual's discount to spot, measured at the decision, against falls led by spot).
- **SQZ-1 (2026-11-15):** coins with crowded shorts kept falling over a week. CASC-1 is about hours, forced longs
  and the end of a cascade, not about crowded positions.
- **Commentary seen only as search results, not read:** reports of the 2025-10-10 cascade (K33: Binance's BTCUSDT
  perpetual 5.1% below spot; analysts disagreeing whether rebounds are spot buying or short covering). No
  systematic study of altcoin rebounds after perpetual-led falls was found.

## 3. Declared prior

About one chance in six. Buying falls in crypto has often been a losing trade over days; the hope is in the hours
right after forced selling, where the discount marks it.

## 4. The probe (file names only)

The probe (run 1 of `casc1.yml`, 2026-11-15 22:09 UTC; `research/results/CASC-1-probe.json`) listed the
hourly files of SQZ-1's 480 seasoned coins: **347** have both spot and perpetual hourly bars inside the dev window
(5,115 coin-months) and 437 inside the validation window; 159 coins are seasoned by 2023-07 and 288 by 2025-02.
No price was read.

## 5. Definitions (frozen in the code)

- **Coins.** The seasoned coins of SQZ-1's probe (a USDT-M perpetual seven months old, with a USDT spot pair), with
  hourly bars of both.
- **Decision** at the close of hour h: the spot fell at least X (8% or 15%) over the last four hours, and the
  perpetual closed at least 0.5% below spot at h.
- **Trade.** Buy spot at the close of h, sell at the close of h+24. One position per coin at a time. Costs 0.25% a
  side (a taker fee and the spread of a falling market).
- **Judged** on the trade's own net return: in a market-wide cascade the market's rebound is part of the mechanism.
  The return against the equal-weight market is reported beside it.
- **Statistic.** The mean over UTC days of each day's mean net (cascades come in days); its t with a Newey-West
  error (lag 1).
- **Placebo.** The same coin from up to 40 random hours within a week on either side on which it had not fallen
  (four-hour return above -X/3), drawn once per trade, 1,000 times.
- **Contrast (the mechanism).** Falls of the same size in which the perpetual never closed more than 0.25% below
  spot at any hour of the fall: they must earn less.

## 6. Stages

| Stage | Trial | Decisions | Falls | Minimum | Runs only after |
|---|---|---|---|---|---|
| dev | CASC-1 | 2023-07-01 to 2025-02-28 | 8%, 15% (2 tests) | 150 trades, 40 days | registration |
| validation | CASC-1-V | 2025-03-08 to 2026-10-29 | the one dev chose | 150, 40 | CASC-1 PASSED |
| forward | CASC-1-F | 2026-12-01 to 2027-05-29 (did not exist when registered) | the same | 40, 10 | CASC-1-V PASSED, on or after 2027-06-10 |

## 7. Gates (every one required)

t >= 3.0; costs doubled above zero; both halves of the days above zero; the five best trades removed above zero;
entering one hour later above zero; above the 95th percentile of the placebo; the best day removed above zero (one
cascade must not carry it); the best coin removed above zero; above the falls led by spot. Too few trades or days is
INCONCLUSIVE, never a pass.

## 8. Power

How many falls qualify is unknown until the bars are read. If dev holds a few hundred trades on 100 to 200
days, a 24-hour net return of a falling small coin has a standard deviation near 8% to 10% (an assumption), a day's
mean near 6%, and the statistic's error near 0.45% to 0.6%: t 3.0 needs about 1.5% to 2% a trade net of the 0.5%
round trip. A rebound of that size after forced selling is plausible; one of a third of it would not be seen.

## 9. What follows

- dev FAILED or INCONCLUSIVE: recorded; nothing later is registered.
- dev PASSED: CASC-1-V once on 2025-03 to 2026-10, then the forward stage. A rule that passes all three is proposed
  to the owner as a paper strategy on spot.

## 10. Limits, declared

- The entry is the close of the decision hour; in a cascade the next minutes can be far from it. The one-hour-late
  gate and the 0.25% side cost are there for that, and may not be enough.
- Delisted pairs may be missing; a coin that collapsed and was delisted would remove losing trades (the forward
  stage is free of it).
- Hourly closes hide the low inside the hour: the rule never buys a wick it could not have bought.
