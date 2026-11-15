# SQZ-1: do crowded shorts pay the spot buyer?

Preregistered on 2026-11-15, before any spot price of the study is read. The funding rates were read (they are the
signal; the probe, below); no spot close was.

| | |
|---|---|
| Program | SQZ-1, stages `dev`, `validation`, `holdout`, `forward`, judged once each, in that order |
| Code sha256 | `9dcbb3a0d417e17d2ed9f211311d906cd6b58166597f28c0a4d0673132c0b18d` (`python scripts/sqz1.py hash`, first value) |
| Spec sha256 | `b1b4842c3df838d26dd99ee3c247a46e4da5ad7efb1dbdd919c64718e4a10875` (the `SPEC` in `scripts/sqz1.py`; second value) |
| Code | `aitrader/research/events/squeeze.py`, `scripts/sqz1.py`, run by `.github/workflows/sqz1.yml` |
| Universe | `crypto-spot-crowded-shorts`: new in the registry. Bar max(3.0, Bonferroni): 3.0 |
| Instrument | **spot, bought outright**: no leverage, no short selling, no funding paid or received. The perpetual's funding is information only (the owner's Islamic condition, `research/QUEUE.md`) |

## 1. The mechanism

A perpetual's funding is what one side pays the other to keep its position. When it is deeply negative for days,
shorts are paying longs every settlement to stay short: short positioning is crowded, or hedging demand is heavy.
Crowded shorts are fragile. A rise forces their liquidations and stops, which buy at any price, and every
settlement charges them again, so time works against them. A spot buyer pays and receives nothing and cannot be
liquidated. If crowded shorts are, on average, forced out faster than they are proved right, the coin's spot price
beats the market over the following days, and the gain is skewed to the right (a few squeezes, many small losses).

**Who is forced to trade at a bad price.** Leveraged shorts near their liquidation prices, whose positions the
exchange's engine closes at market. **Why competition may not remove it.** Capturing it means holding, unhedged, a
coin the market is shorting heavily, usually after a fall: risk-averse capital avoids it, the timing of a squeeze
is unpredictable, and small coins cap the size. **The opposite force.** Some shorts are informed or are hedges of
tokens about to be unlocked and sold; in equities, heavily shorted stocks underperform (short interest predicts low
returns). Which force dominates in crypto perpetuals is what the test decides. **When it should appear:** funding
deeply negative for several days in a coin whose perpetual is no longer new. **When it should disappear:** when
shorts are hedges of coming supply or are informed, and as the squeeze trade becomes crowded itself. **Holding and
risk:** seven days, long only, the coin's own price and the crypto market's.

**Relation to expected return.** With a = the entry close and b seven days later,

    E[excess] = E[r_coin(a, b) - r_market(a, b) | signal <= -theta] - 2c

is positive only if squeeze gains outweigh what informed shorts are right about, by more than two fills.

## 2. What is known, and how this differs

- **In this registry:** FND-1 and FND-1A used funding as a crowding signal for BTC and ETH only (stand aside when
  longs are crowded): FAILED. The carry programs CR-1 to CR-5 harvested funding: FAILED. SQZ-1 uses the opposite
  tail (crowded shorts), across every seasoned coin, long spot only, and earns no funding.
- **Commentary seen only as search results, not read:** K33 Research and VanEck are reported to find that Bitcoin
  did well after its funding turned negative; a Brave New Coin test is reported to find the link loose at 8 hours.
  None tested the cross-section of altcoins. A search found no academic study of it.
- **Equities:** short interest predicts low returns (Asquith, Pathak & Ritter 2005, among others; known here by
  title). That is the contradiction this test must overcome.

What would refute it: an excess return at or below zero, or one that the same coins earn on days their shorts were
not crowded (the placebo).

## 3. Declared prior

About one chance in seven of a pass. The equity evidence points the other way, and crowded shorts in crypto are
often hedges of unlocks.

## 4. The probe (file names, and the funding rates only)

The probe (run 1 of `sqz1.yml`, 2026-11-15 21:13 UTC; `research/results/SQZ-1-probe.json`) found **480** USDT-M
perpetuals whose coin Binance lists on spot against USDT, 103 of them with spot files that stop before 2026-10
(delisted pairs are kept, so survivorship is smaller than feared, though not shown to be absent). It read 11,098
funding files of 2020-12 to 2025-06, none failed, and counted the coin-days on which the signal reaches each
threshold (seasoned coins with spot files):

| Year | Coin-days with a signal | at most -0.03% | -0.05% | -0.1% |
|---|---|---|---|---|
| 2021 | 27,217 | 1,084 | 607 | 148 |
| 2022 | 45,368 | 2,951 | 1,432 | 531 |
| 2023 | 55,170 | 1,578 | 1,008 | 524 |
| 2024 | 79,824 | 1,399 | 887 | 447 |
| 2025 (to June) | 47,152 | 2,546 | 1,639 | 887 |

Only 30 coins are seasoned by 2021-01 and 159 by 2023-06. No spot close was read.

## 5. Definitions (frozen in the code)

- **Coins.** Every USDT-M perpetual (EXF-1's probe) whose coin Binance also lists on spot against USDT
  (`1000PEPEUSDT` is bought as `PEPEUSDT`). A coin counts from the first day its perpetual is seven months old.
- **Signal** at 00:00 UTC of day d: the funding settled in the 72 hours before (from d-72h on, strictly before d),
  per 8 hours; none when the settlements cover less than 48 of those hours.
- **Rule.** If the signal is at most -theta, buy the coin's spot at the close of day d-1 (00:00 UTC of d) and sell
  it at the close of day d+6. One position per coin at a time. Costs: 0.15% a side (0.10% taker fee, 0.05% spread
  and slippage).
- **Measured against** the equal-weight spot return of every seasoned coin over the same seven days (the excess).
  The long-only net is reported beside it.
- **Statistic.** The mean over ISO weeks of each week's mean excess; its t with a Newey-West error (lag 2).
- **Placebo.** The same coin, the same holding, from every day within 30 days on which its signal was above
  -theta/2 (shorts not crowded), drawn once per entry, 1,000 times.

## 6. Stages

| Stage | Trial | Entries | Thresholds | Minimum | Runs only after |
|---|---|---|---|---|---|
| dev | SQZ-1 | 2021-01-01 to 2023-06-30 | 0.03%, 0.05%, 0.1% per 8 h (3 tests) | 300 entries, 52 weeks | registration |
| validation | SQZ-1-V | 2023-07-08 to 2025-06-30 | the one dev chose | 300, 52 | SQZ-1 PASSED |
| holdout | SQZ-1-H | 2025-07-08 to 2026-10-24 (sealed) | the same | 100, 20 | SQZ-1-V PASSED |
| forward | SQZ-1-F | 2026-12-01 to 2027-05-24 (did not exist when registered) | the same | 60, 10 | SQZ-1-H PASSED, on or after 2027-06-10 |

Dev chooses the threshold among those that pass every gate (the highest t). Each stage starts after the one before
it last exits. Every window can reach its own minimum (a test asserts it).

## 7. Gates (every one required)

t >= 3.0; costs doubled above zero; both halves of the weeks above zero; the five best entries removed above zero;
entering one day later above zero; above the 95th percentile of the placebo; the best year removed above zero; the
best coin removed above zero. Too few entries or weeks is INCONCLUSIVE, never a pass.

## 8. Power

Entries are fewer than signal days (one position per coin for seven days). Dev should hold roughly 1,500, 900
and 400 entries at the three thresholds, about 130 weeks. A seven-day excess return of a small coin has a standard
deviation near 12% (an assumption: no close has been read); with about 7 to 12 entries a week the error of the
statistic is near 0.3% to 0.4%, so t 3.0 needs about 1% a week net of the 0.3% round trip. A squeeze effect of that
size is plausible; one of a quarter of it would not be seen.

## 9. What follows

- dev FAILED or INCONCLUSIVE: recorded; nothing later is registered; no variant is judged on 2021-2023.
- dev PASSED: SQZ-1-V, then the holdout, then the forward stage, each once, each only after the one before passed.
  A rule that passes all four is proposed to the owner as a paper strategy on spot, never real money first.

## 10. Limits, declared

- **Survivorship favours the hypothesis here.** A coin delisted after a collapse its shorts foresaw may be missing
  from the archive's spot files, which would remove losing entries. The probe counts the coins whose spot files
  stop before 2026-10; the forward stage is the only stage free of it.
- Costs are assumed: spreads of small coins can be wider than 0.05%; the doubled-cost gate is there for that.
- The benchmark is a measurement, not a position: a long-only buyer also carries the crypto market's return,
  reported beside the excess.
