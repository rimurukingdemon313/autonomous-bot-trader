# SPL-1: does a rally that spot buyers led keep going?

Preregistered on 2026-11-16, before any of SPL-1's figures is computed and before any price of its validation window is
read.

| | |
|---|---|
| Program | SPL-1, stages `dev`, `validation`, `forward`, judged once each, in that order |
| Code sha256 | `fea4d05f39ed31973348bd0d8425422004d6c75c3702b56cf3c3ec259d64a5f3` (`python scripts/spl1.py hash`, first value; it covers CASC-1's frozen `cascade.py`, `casc1.py` and `sqz1.py`, whose panel, readers and judge it reuses unchanged) |
| Spec sha256 | `b57245caa008f7ce4fb59112a5397566242f4e4bca3b21222f4d44785701d53c` (the `SPEC` in `scripts/spl1.py`; second value) |
| Universe | `crypto-spot-spot-led-rallies`: new. CASC-1 read the same hourly panel over the development window, so its tests count too (`crypto-spot-liquidation-falls`). Bar max(3.0, Bonferroni): 3.0 |
| Instrument | **spot, bought outright**, long only: no leverage, no short, no funding paid or received. The perpetual's price is information only |

## 1. The mechanism, and why now

A coin can be pushed up by two kinds of buyer. Leveraged buyers bid its perpetual: it trades at a premium to spot and
arbitrageurs carry the premium into spot. Their demand is borrowed and comes back out when the positions are closed or
liquidated. Spot buyers pay in full and owe nothing: a rise they lead, with the perpetual no richer than spot,
reflects new holders, does not have to be unwound, and the slower holders it draws in should carry it further.
**The opposite force:** spot-led pumps of thin coins are often coordinated and dumped within hours.

**Why now (declared, because it shaped the choice):** SQZ-1, BAS-1 and CASC-1 (2026-11-15) found that a coin under
leverage stress does worse than the market for days to weeks, and that this information sits on the short side,
which the Islamic condition excludes for altcoins. This is the long side of the same distinction: the rise without
leverage. It was formed after seeing those results, so it is judged where none of them looked: its validation
window, 2025-03-08 to 2026-10-29, holds hourly prices no study here has read.

## 2. What is known, and how this differs

- **Momentum in crypto** (Liu & Tsyvinski 2021; this record's XTS-1 on BTC and ETH over weeks, and XSM-1 across the
  20 largest coins) is a family that failed here. SPL-1's claim is conditional: rises the perpetual led are its
  contrast and must NOT continue. Unconditional momentum would fail that gate.
- **Pump-and-dump studies** (Kamps & Kleinberg 2018; Xu & Livshits 2019) find that coordinated pumps of thin coins
  reverse fast. SPL-1 trades seasoned coins with perpetuals only, and must pass a late entry and a placebo.
- **CASC-1's contrast:** falls led by spot ended flat (+0.01% net over 24 hours, 4,953 falls of 8% or more). Those
  were falls; this asks the same question of rises.
- No study of what follows a rise according to which market led it was found (search results only).

## 3. Declared prior

About one chance in eight. The direction rests on this record's leverage findings and on the theory of unlevered
demand. Against it: pumps reverse, and a rise of 8% in four hours is where late retail buys.

## 4. Definitions (frozen in the code)

The panel, readers and judge are CASC-1's, unchanged: hourly Binance spot and USDT-M perpetual closes of the coins in
`research/results/CASC-1-probe.json` (seasoned, with both files: 347 in development, 437 in validation, file names
only). At the close of hour h: the spot rose at least X over four hours (X = 8% or 15%; development chooses), and at
every one of the five closes from h-4 to h the perpetual stood no more than 0.25% above spot (a missing close means
the rise is not shown to be spot-led). Buy spot at that close, sell 24 hours later; one position per coin at a time;
0.25% a side. The statistic is the mean over days of each day's mean net return, with a Newey-West t (lag 1).
**Contrast:** the same rises with the perpetual at least 0.5% above spot at hour h. **Placebo:** the same coin's
24-hour net from up to 40 random hours within a week either side, at least 24 hours away, without a rise (four-hour
return below X/3). **Market:** the equal-weight spot return of every seasoned coin over the same hours.

## 5. Stages

| Stage | Trial | Decisions | Choices | Minimum | Runs only after |
|---|---|---|---|---|---|
| dev | SPL-1 | 2023-07-01 to 2025-02-28 (hourly prices CASC-1 read for falls; declared) | 8% and 15% (2 tests) | 150 entries on 40 days | registration |
| validation | SPL-1-V | 2025-03-08 to 2026-10-29 (no study has read these prices) | the one dev chose | 150, 40 | SPL-1 PASSED |
| forward | SPL-1-F | 2026-12-01 to 2027-05-29 | the same | 40, 10 | SPL-1-V PASSED, on or after 2027-06-10 |

## 6. Gates (every one required)

CASC-1's: t >= 3.0; costs doubled; both halves; the five best entries, the best day and the best coin removed; an
hour later; above the placebo's 95th percentile; above the perpetual-led rises. And one more: **above the market**
over the same hours (mean excess > 0). Too few entries is INCONCLUSIVE, never a pass.

## 7. Power

CASC-1's development found 4,953 falls of 8% or more led by spot and 326 led by liquidations: four-hour moves of this
size are common in this panel, and rises are no rarer, so both stages should hold thousands of entries on hundreds of
days. CASC-1's daily cohorts of 8% falls had a standard deviation near 12% on 183 days; with many more entries a day,
about 6% is a fair guess. Over about 600 days, t 3.0 then needs about +0.7% net a trade, +1.2% before the fills.

## 8. What follows

dev FAILED or INCONCLUSIVE: recorded, nothing later. dev PASSED: SPL-1-V once on unread prices, then the forward
stage. Only a rule that passes all three is proposed to the owner, as a paper strategy on spot.

## 9. Limits, declared

The development window's hourly prices were read by CASC-1, for falls; only the validation and forward stages are
blind. Coins delisted before a probe are missing (survivorship). 0.25% a side is CASC-1's cost; a seasoned coin's
book can be thinner after a rise.
