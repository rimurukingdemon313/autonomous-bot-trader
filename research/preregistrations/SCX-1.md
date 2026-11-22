# SCX-1: do stablecoins drift from par while their primary market is shut, and come back when it opens?

Preregistered on 2026-11-22, before any of SCX-1's figures is computed, and before anyone in this project has read
a stablecoin pair's price. Only the probe has run: file names (section 7).

| | |
|---|---|
| Program | SCX-1, stages `dev`, `validation`, `forward`, judged once each, in that order |
| Code sha256 | `d8a58f9cd4dc1a39c963d40691053d1ec67aafce885c648882b44214177ee8e4` (`python scripts/scx1.py hash`, first value; it covers `aitrader/research/events/stablecoin.py`, `scripts/scx1.py`, and the frozen readers it reuses unchanged: `cascade.py` for its Newey-West t, `sqz1.py` for the archive's listing and months, `exfunding.py` for the archive's zip files) |
| Spec sha256 | `c05a229f495fdb41d2a4078c0f21ed2d82f0b3bea17e22e85fdc8b9113e00f2b` (the `SPEC` in `scripts/scx1.py`; second value) |
| Universe | `stablecoin-pairs-weekend`: new. Bar max(3.0, Bonferroni over every test on it): 3.0 |
| Instrument | a **spot exchange of one stablecoin for another, from a stock of both**, hand to hand: no leverage, no borrowing, no short sale, no interest received or paid |
| Source | docs/ORIGINAL_EDGE_HUNT_2.md, hypothesis C1 (chosen second of twenty by the rule fixed before scoring) |

## 1. The mechanism

A dollar stablecoin's price on an exchange is held near $1 by arbitrageurs who mint and redeem with its issuer, and
issuers move dollars only on US banking days (the Federal Reserve's note on the SVB weekend: Circle's redemptions
were "constrained by working hours of the U.S. banking systems"). At weekends the peg rests on market makers' stock
alone, so an order flow can push a pair further from par and keep it there longer; on Monday the primary market
reopens and the pair is pulled back. Whoever needs the other coin at once on a Sunday pays for it; whoever waits for
Monday is paid.

**The opposite forces.** Market makers hold large stocks; most weekend deviations are a tick or two and need no
primary market to close; a deviation can be the start of a real depeg (an issuer in trouble), which does not revert.

## 2. What is known, and how this differs

Searches of 2026-11-22 (search results only; `research/results/ROUND2-sources.md`):

- Ma, Zeng & Zhang, "Stablecoin runs and the centralization of arbitrage" (NBER/ECB conference paper): six
  arbitrageurs redeem USDT in an average month, 521 for USDC; average deviations of 41.9 bp and 1.7 bp. The structure
  of arbitrage, not its weekly clock.
- Federal Reserve FEDS Note of 2025-12-17: the SVB weekend. One crisis.
- S&P Global, stablecoin depegging report: leaving out weekends almost halves some stablecoins' volatility.
  Volatility, not a dated trade.
- Lyons & Viswanath-Natraj (2023, JIMF) and Gorton et al. (2022), from memory: primary-market arbitrage holds the
  peg; deviations track leverage demand. No weekend timing.
- No test of a Sunday-to-Monday reversion trade in stablecoin pairs was found.

## 3. Declared prior

About one chance in four that it passes in development; much lower that it is worth much. For: the closure of the
primary market at weekends is a fact, and the noise in a stablecoin pair is tiny, so a small effect is measurable.
Against: Binance's pairs have a 1 bp tick, deviations of one or two ticks are mostly the bid-ask bounce of the last
trade, and makers who are paid to hold stock do it at weekends too.

**Its size is small, and said before the test:** even if it passes every gate, a few basis points a weekend on
stablecoin capital is a real edge of small capacity. It does not come near $4,000 a month on a small account.

## 4. Definitions (frozen in the code)

- **Pairs.** USDCUSDT, TUSDUSDT, USDPUSDT (PAXUSDT before its renaming), BUSDUSDT and FDUSDUSDT on Binance spot:
  every month each pair has in the archive (BUSD and TUSD are kept for the weeks they traded, depegs included).
- **Entry.** At 22:00 UTC on Sunday (the close of the hourly bar opening at 21:00): the log deviation from par
  `delta = ln(price)`; if `|delta| >= theta`, swap from the dear coin into the cheap one, from a stock of both.
- **Exit.** 23 hours later, at 21:00 UTC on Monday (the close of the bar opening at 20:00), after the US banking day.
- **Net.** `-sign(delta) * (ln p_exit - ln p_entry)` less 2 bp a round trip (1 bp a fill: a tick of spread and
  Coinbase's stable-pair fee of 0 to 0.1 bp, or Binance's zero-fee USD stablecoin pairs; Coinbase's blog and Binance's
  announcement, search results). Reported beside it, never gated: the same swaps at Binance's standard 10 bp a fill.
- **Statistic.** The mean over weeks of each week's mean net, with a Newey-West t (lag 1).
- **Contrast (the mechanism's own test).** The same rule on Wednesday 22:00 to Thursday 21:00 UTC, with the primary
  market open throughout: Sundays must do better.
- **Placebo.** For each entry, the same pair at up to 20 random hours within 14 days either side, at least two days
  away, whose deviation also reached theta, inside the stage's own hours; 1,000 draws of the weekly mean; the real
  mean must exceed their 95th percentile.

## 5. Stages

| Stage | Trial | Decisions (Sundays) | Choices | Minimum | Runs only after |
|---|---|---|---|---|---|
| dev | SCX-1 | 2018-12-16 to 2023-06-25 | theta 3 bp and 10 bp (2 tests) | 40 entries in 40 weeks | registration |
| validation | SCX-1-V | 2023-07-02 to 2026-10-25 | the theta dev chose | 30 in 25 weeks | SCX-1 PASSED |
| forward | SCX-1-F | 2026-12-06 to 2027-05-30 | the same | 10 in 8 weeks | SCX-1-V PASSED, on or after 2027-06-10 |

No bar that closes after a stage's last exit (an hour late) reaches it.

## 6. Gates (every one required)

t >= 3.0; costs doubled; both halves of the weeks; the five best entries removed; the best week removed; the best
pair removed; entered an hour later; above the placebo's 95th percentile; above the Wednesdays. Too few entries or
weeks is INCONCLUSIVE, never a pass.

## 7. The probe, and power

The probe (2026-11-22, 02:47 UTC; `research/results/SCX-1-probe.json`; file names only, no price read) found hourly bars for six pair names: USDCUSDT from 2018-12 to 2026-10 (90 months), TUSDUSDT 2018-05 to 2026-10 (97), PAXUSDT 2018-10 to 2021-09 (36) and, after its renaming, USDPUSDT 2021-09 to 2026-09 (56), BUSDUSDT 2019-09 to 2023-12 (52) and FDUSDUSDT 2023-07 to 2026-10 (40). Development holds 237 Sundays with up to five pairs (USDC 50 months, TUSD 50, BUSD 46, PAX 34, USDP 17); validation holds 174 Sundays with USDC, TUSD and FDUSD (40 months each), USDP (39) and BUSD's last 6.

Power: the noise in a stablecoin pair's 23-hour change is a few basis points. With about 230 Sundays in
development, of which perhaps a third reach 3 bp, t 3.0 needs about +1 bp net a week at a weekly standard deviation
near 3 bp.

## 8. What follows

dev FAILED or INCONCLUSIVE: recorded, nothing later. dev PASSED: SCX-1-V once on prices no study here has read, then
the forward stage. A rule that passes all three is proposed to the owner as a paper strategy of small capacity, with
its real size stated.

## 9. Limits, declared

- **Last trades, not quotes.** The archive has bars, not the bid and ask: a deviation of a tick can be the bounce
  between them. The 3 bp threshold and the costs doubled are the guards.
- **A real depeg does not revert.** It is in the data (TUSD and BUSD are kept) and counts against the rule.
- **US bank holidays** on a Monday leave the primary market shut for a third day; they are not removed.
- **Costs are declared, not measured.** 1 bp a fill; Binance's standard fees are reported beside the result.
