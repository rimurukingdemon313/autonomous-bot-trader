# NEWL-1: do newly listed perpetuals underperform seasoned listings in their first month? (preregistration)

**Written on 2026-11-15, after a probe of file names and before any price of any listing was read.** Research only:
nothing here trades, and no system changes because of it.

| | |
|---|---|
| Code | `aitrader/research/events/listings.py` (newl-1.0.0), `scripts/newl1.py` |
| Code sha256 | `93b172270747d50807d7c7ff0443e64e9b12e10aef57f9b15e328fee703b3b44` (`python scripts/newl1.py hash`, first value) |
| Spec sha256 | `ee2fc3d6b82d0060560ffacd7c116db18861b0324edb9e2e5b6a0aaae1590930` (the `SPEC` in `scripts/newl1.py`; second value) |
| Runs | `.github/workflows/newl1.yml` on GitHub's runner; data on the `newl-data` branch |
| Tests | `tests/unit/test_newl1.py`: markets built so the answer is known |
| Data | Binance USDT-M daily klines and funding settlements from data.binance.vision, delisted contracts included |
| Universe | `crypto-perp-new-listings`; counted tests: 1 for this stage; bar t >= 3.0 (the registry's floor) |

## Why this, and why now

The owner's order of 2026-11-15 asks for a new source of edge with a mechanism. Read together
(`docs/RESEARCH_META_ANALYSIS.md`), the record says the panels already held have been searched: 88 hypotheses, 660
rules, nothing beyond the one validated trend rule. None of it looked at listings. The lab's perpetuals panel is the
55 contracts that existed by September 2020, chosen by age so that later deaths stayed in it; by the same choice it
contains no new listing. The archive holds 915 first contracts on a coin, 854 of them first seen after September 2020. (Its monthly files begin in 2020-01: 11 contracts listed before then show 2020-01 as their first month. They are too old to be events or seasoned members in this stage.)

## The mechanism, and what it predicts

At listing, a perpetual's coin often carries supply that was not trading before: tokens unlocking for early backers
and teams, airdrops, the market maker's borrowed inventory. Its listing brings attention. Shorting the coin elsewhere
is often hard or impossible, so the people who think it is overpriced cannot act on it except here. When pessimists
cannot short, prices reflect the optimists (Miller, 1977); new issues of shares underperform for years after their
first day (Ritter, 1991). Neither paper was read in this project: they are the reason for the question, and no figure
is taken from them.

The prediction is directional and comes first: a new contract, held short from the close of its first full day for
30 days and hedged with seasoned listings, **earns** after funding and costs. A rise refutes it as surely as noise.

## What I believed before (declared)

Practitioners' accounts, and my own prior from them, describe large falls in many contracts listed in 2024. So the
validation stage is not blind to beliefs; it is blind only in that no figure of it has been computed here. That is
why a forward stage, on listings that do not exist yet, is the test that follows if both stages pass.

## Definitions, frozen by the code

- **A listing** is the first contract on a coin among Binance's USDT-M contracts in the archive, read in the order the
  contracts appeared. Excluded: delivery contracts, index and basket contracts, dollar-pegged coins, and any contract
  on a coin that already had one (a 1000-unit re-denomination, a USDC or BUSD twin, a re-listing).
- **Listing day L**: the contract's first daily kline. **Entry**: short at the close of L+1. **Exit**: the close of
  L+31, or the last close if it stopped trading first (kept, never dropped).
- **The short leg**: the price move, funding on the position's notional each day (a short receives what a long pays),
  and two fills of 15 bp (5 bp taker fee, 10 bp spread and slippage).
- **The hedge**: an equal-weight long basket of every listing aged 181 to 365 days at the entry, held over the same
  window with the same funding and fills; at least 3 members, else the event is shown and left unhedged.
- **The outcome of an event** is the short leg plus the basket: dollar-neutral, per unit of short notional.
- **Cohorts**: the events entered in each calendar month are averaged. The statistic is the mean of the monthly
  cohorts, and its t uses a Newey-West standard error with one lag.

## The stages

| Stage | Trial | Entries | Last price read | Listings in it (probe, by first month) | Registered |
|---|---|---|---|---|---|
| History | `NEWL-1` | 2021-01-01 to 2026-09-30 | 2026-10-31 | 812 (180 in 2021-2023, 632 from 2024 to 2026-09) | now |
| Forward | `NEWL-1-F` | 2026-11-16 to 2027-05-30 | 2027-06-30 | listings that do not exist yet | only if the history passes; judged once, on or after 2027-07-11 |

**A change of design, made before any return was read.** The first draft split the history into a development stage
(2021-2023) and a validation stage (2024 to 2026-09). It was dropped for two reasons. The development stage would hold
180 listings in 34 months, too few to pass a real effect of about 5% a month at t 3.0, so a true effect would most
likely have been thrown away. And the later period is not blind to my priors (below), so calling it an independent
validation would overstate it. Nothing in the rule is fitted, so the whole history is one confirmatory test of a
rule fixed in advance; its "both halves" gate splits it into the two regimes (2021-2023 and 2024-2026), each of which
must be positive. The independent validation is the forward stage, on listings no one has seen.

## The gates (every one is required)

| Gate | Condition |
|---|---|
| t | t of the mean cohort outcome >= 3.0 |
| Costs doubled | the mean is still positive with 30 bp a fill |
| Both halves | the first and the second half of the stage's months are each positive |
| Five best removed | the mean is positive without the five events that earned most |
| A day late | entering at the close of L+2 instead is still positive |
| Beats random | the mean exceeds the 95th percentile of 1,000 placebos in which each new contract is replaced by a random seasoned one |
| No single year | the mean is positive without the year that earned most |

Fewer than 60 hedged events or 18 months with an event: **INCONCLUSIVE**, never a pass.

## Power (from the probe's counts; no return was read)

No return was read to make this estimate; the spread of the cohort means is a guess. The probe counts 812 listings
in the stage, in about 67 months with at least one entry. If the monthly cohort means spread by 15 to 25%, their
standard error over 67 months is about 2 to 3%, and t 3.0 asks for a mean of about 6 to 9% per event, after costs. An
effect of 5% would most likely fail the bar even if real; an effect of 10% or more would most likely pass it. The
gates other than t are about the shape of the result, not its size.

## What follows

- PASSED: `NEWL-1-F` is registered with the same code and spec before its first listing, and judged once on or after
  2027-07-11. Until then the result is a candidate, never a validated edge, and nothing trades on it, on paper or
  otherwise. A forward paper record of the rule can be kept beside it; it decides nothing.
- FAILED or INCONCLUSIVE: the hypothesis is closed on these data, recorded as it came out, and not rerun under another
  name. In particular, no other holding period, entry day or hedge is tried on the same listings.

## Known limits of the data and of the measurement

- Survivorship: the archive holds 875 of the 915 eligible contracts at 2026-10 and 40 that stopped earlier. Whether
  it keeps every contract Binance ever listed cannot be checked from the archive itself. A contract missing because it
  died would have been a gain for the short: the bias, if any, is against the hypothesis.
- Execution: the short is assumed open at the close of its first full day at 15 bp a fill, with margin enough never to
  be liquidated. Binance limits position sizes and leverage on new contracts, so the capacity is small and is not
  modelled. The worst single event is reported.
- Daily closes only: a squeeze inside a day is not seen.

## What was seen before this was written

The probe's file names (which months exist for each contract), and nothing else of these contracts. No figure of any
listing's price, funding or volume was computed in this project.
