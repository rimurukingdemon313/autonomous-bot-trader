# KRP-1: does a coin's Korean premium lift its global price the next day?

Preregistered on 2026-11-22, before any of KRP-1's figures is computed, and before anyone in this project has read a
single Upbit price. Only the probe has run: names and file names (section 7).

| | |
|---|---|
| Program | KRP-1, stages `dev`, `validation`, `forward`, judged once each, in that order |
| Code sha256 | `42c9b2ed917ac9892b0abe472b7841d1913ee1c8a449305ae5ea62ec52a193ce` (`python scripts/krp1.py hash`, first value; it covers `aitrader/research/events/korea.py`, `scripts/krp1.py`, and the frozen readers it reuses unchanged: `cascade.py` for its Newey-West t, `sqz1.py` for the archive's listing and months, `exfunding.py` for the archive's zip files) |
| Spec sha256 | `cce3027552604309f82e5addc0d9296c2ef43da9ecf8a2fd96b3e3edd86e0809` (the `SPEC` in `scripts/krp1.py`; second value) |
| Universe | `crypto-spot-korean-premium`: new. Bar max(3.0, Bonferroni over every test on it): 3.0 |
| Instrument | the coin's **spot, bought outright** on Binance, against a **short of bitcoin through a swap-free CFD** over the same hours. One short sale (bitcoin's, through a CFD), stated; no leverage, no funding paid or received, no interest. Upbit's prices are information only: the owner cannot trade there |
| Source | docs/ORIGINAL_EDGE_HUNT_2.md, hypothesis A1 (chosen first of twenty by the rule fixed before scoring) |

## 1. The mechanism

Korean residents trade on KRW venues (Upbit, Bithumb) that foreigners cannot use, and capital controls make moving
KRW abroad slow and capped. Korean retail concentrates on altcoins. When Korean demand lifts a coin's price in KRW
above its price abroad by more than bitcoin's own Korean premium, the coin-relative gap can be closed without moving
any KRW across the border: sell the coin on Upbit, buy bitcoin there, withdraw the bitcoin, sell it abroad for the
coin, deposit the coin. That round trip buys the coin and sells bitcoin on the global venue. So a fresh coin-relative
premium should be followed by the coin rising against bitcoin abroad over the following hours.

**The opposite forces.** The gap can close on the Korean side alone (Upbit's price falls back) with no pressure
abroad; withdrawals and deposits may be suspended (no arbitrage at all); the arbitrage may finish within the hour
before the entry; and a Korean spike can mark a retail top that falls everywhere.

## 2. What is known, and how this differs

Searches of 2026-11-22 (search results only; `research/results/ROUND2-sources.md`):

- Makarov & Schoar (2020, JFE): cross-country bitcoin premia track buying pressure and persist because capital is
  segmented. Country level, bitcoin only; no coin-level prediction of the global price.
- Choi, Lehar & Stauffer (SNB seminar 2019): asymmetric capital controls keep bitcoin's Korean premium positive. The
  level of bitcoin's premium, not a cross-section.
- Finance Research Letters 2022 (vol. 50): foreign arbitrageurs took most of the premium's profit. Who profits from
  the gap, not what it predicts.
- Crépellière, Pelster & Zeisberger: cross-exchange arbitrage shrank after April 2018 and does not pay once
  implemented. Here the gap is a signal for an outright position abroad that needs no Korean account.
- 4Pillars: Korean flow peaks near altcoin tops. Descriptive, no baseline.
- No test of coin-relative Korean premia against the next day's global price was found in three searches.

## 3. Declared prior

About one chance in six. For: the channel (Korean flow moves global prices) is documented, and small coins with a
large Korean share have the price impact the mechanism needs. Against: arbitrage is fast, much of it may finish
before an entry an hour after the close, and 0.6% a round trip is a high bar for a one-day trade.

## 4. Definitions (frozen in the code)

- **Premium.** At the 00:00 UTC daily close, `rho = ln(U_coin / U_btc) - ln(B_coin / B_btc)`: Upbit's daily candle
  close (the candle that opens at 00:00 UTC) over Binance's close at 00:00 UTC (the close of the hourly bar opening
  at 23:00). The KRW exchange rate cancels; so does bitcoin's own Korean premium.
- **Entry: a fresh spike.** `rho >= theta`, with `|rho| <= 1` (a renamed or redenominated asset, or a data
  mismatch, is not an entry), and the median of rho over the 30 days before below theta/2 (a persistent gap is a
  blocked arbitrage, not the mechanism; at least 15 of those days must have a premium).
- **Eligible coin-day.** Not bitcoin and not a stablecoin; listed at least 30 days on both venues; Upbit's KRW
  turnover that day at least 500 million won; Binance's quote volume that day at least $1 million.
- **Trade.** Buy the coin on Binance at the close of the hour 00:00-01:00 UTC (an hour after the signal's close),
  short bitcoin at the same close, close both 24 hours later. Net = coin return - bitcoin return - 0.6% (0.25% a side
  on the coin, 0.05% a side on the bitcoin CFD). One position per coin at a time. A missing price is recorded as
  missing, never filled.
- **Statistic.** The mean over days of each day's mean net, with a Newey-West t (lag 1).
- **Contrast (the mechanism's own test).** The same fresh spike with the opposite sign (a Korean discount of at least
  theta): arbitrage would sell the coin abroad, so discounts must not do as well.
- **Placebo.** For each entry, the same coin's net from up to 20 random ordinary days (|rho| below theta/3, eligible,
  at least two days from the entry) within 30 days either side, **inside the stage's own decision window**; 1,000
  draws of the daily-cohort mean; the real mean must exceed their 95th percentile.

## 5. Stages

| Stage | Trial | Decisions (signal days) | Choices | Minimum | Runs only after |
|---|---|---|---|---|---|
| dev | KRP-1 | 2018-01-01 to 2025-02-28 | theta 5% and 10% (2 tests) | 150 entries on 60 days | registration |
| validation | KRP-1-V | 2025-03-08 to 2026-10-29 | the theta dev chose | 80 entries on 30 days | KRP-1 PASSED |
| forward | KRP-1-F | 2026-12-01 to 2027-05-29 | the same | 30 on 10 | KRP-1-V PASSED, on or after 2027-06-10 |

Each stage reads nothing past its own last exit: Upbit's candles are asked for up to the last decision day only (its
`to` bound is exclusive), Binance's grid ends at the last exit an hour late, and placebo days stay inside the window.

## 6. Gates (every one required)

t >= 3.0; costs doubled; both halves of the days; the five best entries removed; the best day removed; the best coin
removed; entered an hour later; above the placebo's 95th percentile; above the Korean discounts. Too few entries or
days is INCONCLUSIVE, never a pass.

## 7. The probe, and power

The probe (2026-11-22, 02:48 UTC; `research/results/KRP-1-probe.json`; names and file names only, no price read) found 300 coins Upbit quotes in KRW today, 204 of them with hourly USDT spot bars in Binance's archive. Of those, 142 have bars in the development window and 200 in the validation window; bitcoin's bars run from 2017-08 to 2026-10. No delisted Upbit code could be added: UDL-1's probe found Upbit's notice pages closed to GitHub's runner (HTTP 403), so the universe is the coins Upbit lists now (survivorship, section 9).

Power: a coin's 24-hour return against bitcoin has a standard deviation of a few percent; averaged over the entries
of a day, about 3% is a fair guess. Over about 300 days with an entry, t 3.0 needs about +0.5% net a trade, about
+1.1% before costs: a tenth to a fifth of a 5% to 10% gap moving the global price.

## 8. What follows

dev FAILED or INCONCLUSIVE: recorded, nothing later. dev PASSED: KRP-1-V once on prices no study here has
conditioned on a Korean premium, then the forward stage. Only a rule that passes all three is proposed to the owner,
as a paper strategy on spot with a bitcoin CFD hedge.

## 9. Limits, declared

- **Survivorship.** Upbit's API serves the markets it lists now, and UDL-1's probe could not read which coins it
  delisted (its notice pages refuse GitHub's runner): a coin Upbit has since removed is missing, and such coins are
  likely to have fallen. The bias can favour the rule: a coin pumped in Korea and later delisted may have
  done worse after its spikes than the survivors did. A pass is read with that in mind; the forward stage has the
  same limit for any coin Upbit removes before it is judged.
- **Prices read before.** CASC-1 read Binance's hourly spot prices of 2023-07 to 2025-02 (for falls), and the lab's
  daily rules read daily crypto prices of 2020 to 2026. No study here has read Upbit's prices or conditioned on a
  Korean premium.
- **Closing prices are last trades.** A thin market's close can be stale: the turnover floors are the guard.
- **Unobserved.** Deposit and withdrawal suspensions are not in the data; the fresh-spike rule removes most of them.
- **Costs are declared, not measured.** 0.25% a side for the coin and 0.05% a side for the bitcoin CFD.
