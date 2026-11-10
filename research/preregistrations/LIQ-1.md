# LIQ-1: buying after forced crypto deleveraging, stage 1 (preregistration)

**Written 2026-11-10, before any open-interest value or price of these data was read.** The probe
(`scripts/liq_probe.py`, `research/results/LIQ-probe.json`) read only file dates and column names. Research only:
nothing here trades.

- Spec sha256: `dc081492f097b0eaa20a067f9d00773d14324ed4aa64f49b32b9a927df4749b3` (`research/specs/LIQ-1.json`)
- Code sha256: `ab3771962dfcbd8952d131e9add50e6a1fbedd7835c3feff49f9ddb0293c55b0` (`scripts/liq1.py`, liq-1.0.0)
- Tests: `tests/unit/test_liq1.py` (16), on markets built so the answer is known, and the guards that keep stage 2's
  data out of stage 1.
- Run: `.github/workflows/liq1-run.yml`, once, on GitHub's runner (Binance is blocked here).

## The question

After an hour in which a perpetual's open interest and its price both fall below their own trailing 90-day 1st
percentile, does a long position held 24 hours earn a positive net return? And does it earn more than random entries
at the same hours?

## Why it might pay

- **A fire sale** (Coval & Stafford 2007; Brunnermeier & Pedersen 2009). Exchange margin engines liquidate leveraged
  positions mechanically, at any price. Forced, price-insensitive selling can push a price below its value, and
  whoever supplies liquidity in the cascade is paid when it reverses.
- **Visible in the data.** In a perpetual the forced selling shows as open interest collapsing while the price falls.
- **Why it might persist.** Leverage on perpetuals is high and liquidations are mechanical. Liquidity providers are
  thin in a cascade, and capital is slow to arrive.
- **The evidence is anecdotal for crypto.** No rigorous study of this rule was found (`docs/DISCOVERY_PROGRAM.md`,
  sources). It is the first use of open-interest data here.

## The data

Binance USDT-M futures, from data.binance.vision.
- Each file is checked against its published CHECKSUM. A file that fails stops the run; nothing is filled.
- A row that cannot be read leaves its hour missing. Such rows are counted in the manifest.

| | Development (stage 1) | The probe's spans |
|---|---|---|
| Open interest | daily metrics files, a snapshot every 5 minutes; the one exactly on each hour is used | BTCUSDT from 2020-09-01, ETHUSDT from 2021-12-01, no day missing |
| Prices | monthly 1h klines (open and close) | 2020-01 → 2026-10 for both, no month missing |

**Stage 1 fetches and reads nothing from 2024-01-01 on.** The fetch lists no later file, and both the fetch and the
loader refuse any later hour.

## The rule (frozen in the spec)

| | |
|---|---|
| Event at hour i | log(close/open) of hour i, and log(OI at its end / OI at its start), both below their own 1st percentile over the 2,160 hours before hour i (at least 1,800 values each) |
| Entry | long at the open of hour i + 2: one full hour after the event hour closes. That also covers a snapshot published up to 5 minutes late |
| Exit | the open 24 hours after the entry |
| Positions | one at a time per coin; an event while one is open is passed over |
| A missing price or snapshot | no event, or no trade, counted; never filled |
| Costs | 15 bp a side, as for XTS-1 and FND-1A's crypto CFDs; ×1, ×1.5 and ×2 |
| Financing | none: a swap-free account. 20% a year, about 5.5 bp a trade, is reported, never added |

Nothing is chosen in stage 1. The percentile, the window, the entry and the hold are fixed here, before any value is
read.

## Two stages, like CR-1

**Stage 1 (this registration, role select)** runs on the development data:

| Coin | Development |
|---|---|
| BTCUSDT | events from 2020-11-30, after a 90-day warm-up, to exits before 2024-01-01 |
| ETHUSDT | events from 2022-03-01, to exits before 2024-01-01 |

The program's plan said 2021-12..2023-12 for both coins. The probe then found BTCUSDT's open interest from 2020-09,
so its development starts there. This was decided before any value was read.

Stage 1 PASSES only if every gate holds:

| Gate | Rule |
|---|---|
| trades | at least 30, both coins together |
| mean | the mean net return a trade > 0 |
| each coin | > 0 for BTCUSDT alone and for ETHUSDT alone |
| costs ×2 | the mean > 0 with the cost doubled |
| one hour late | the mean > 0 with every entry one hour later |
| beats random | the mean above the 95th percentile of 2,000 random books (seed 47). Each trade is replaced by an entry from the same coin, calendar month and hour of the day, with the same hold and cost |
| projected t | the week-clustered t, scaled by √(stage 2's coin-years / stage 1's), ≥ 2.0. That is about one chance in six of reaching 3.0 if the true effect equals stage 1's. A stage 2 with less than that would spend a test on these data for little |

- **The t is week-clustered (CR1).** Trades in one ISO week, on either coin, are one cluster, so a cascade that hit both
  coins counts once.
- **The knowledge file also reports:**
  - the 95% interval of a 5,000-draw week bootstrap (seed 53);
  - costs ×1.5;
  - results by coin and by year;
  - the hit rate, and the best and worst trades;
  - the share of the total from the top week;
  - the exposure and the trades a year;
  - the event hours before the one-position rule;
  - the trades skipped for a missing price.

**A FAIL closes the family on these data.** Stage 2's data stay unfetched.

**Stage 2** is preregistered only after a PASS, with the rule unchanged. It runs on 2024-01..2026-10, entries whose
exit is before 2026-11-01. It passes only if all of these hold:
- the week-clustered t of the mean net return a trade reaches its threshold;
- the mean is > 0 for each coin, at costs ×2, and one hour late;
- the mean is above the matched random books' 95th percentile.

## The threshold

**Stage 2 would need t ≥ 3.0.** That is this program's floor; Bonferroni alone is lower.

- On `crypto-binance-usdtm` over 2024-01..2026-10, the registry counts 2 earlier tests (CR-1-V, CR-2).
- Counting the spot universe's 7 too (XTS-1, FND-1, FND-1A, XSM-1), since spot and perpetual prices move together,
  gives 10 with LIQ-1's stage 2. That is a Bonferroni bar of about 2.81.
- Stage 1 itself is a select use on 2020-09..2023-12, where the registry counts 10 earlier tests. It does not overlap
  stage 2.

**CR-1's unopened holdout.** CR-1 set 2025-01..2026-09 aside as a holdout for its validation passers. None passed, so
that holdout was never opened, and it has no further use for CR-1. Stage 2 would be its first reading, counted as above.

## Power, written before the test

| | Estimate |
|---|---|
| Hours that qualify | about 0.1-0.3%, if the two falls are as dependent as in a cascade |
| Trades in development | perhaps 25-60, after the one-position rule merges each cascade's hours |
| Mean needed to reach t 3.0 in stage 2 | about 0.4-0.5 standard deviations a trade: roughly +2% a day net, against a 24-hour standard deviation of 4-5% |

**That is a large effect.** Stage 1 may well fail on its trade count or on its projected t. That would be a real
answer: too few events, or too small an effect, to be worth a test.

## What could make it fail, or mislead

- **Cascades often continue.** A momentum crash can follow the first leg down.
- **The same leverage family as FND-1A**, which failed. That used funding, not open interest, so its information is
  different.
- **Only about 4.9 coin-years of development** and 5.7 of stage 2.
- **A CFD's spread widens in a cascade.** The ×2 gate tests that.
- **Weekends and exchange-specific outages.** A missing price is never filled, and its trade is counted.
- **A random book can hold the crash hours themselves.** A trade entered after a cascade never does. In real prices
  the month's crashes are part of its average return, so the comparison is fair. `tests/unit/test_liq1.py` checks
  both:
  - a market whose cascades arrive at random and are repaid by its drift fails the random gate;
  - one with a planted rebound passes it.

## What follows

- **A FAIL** is recorded as such, and the family is closed on these data.
- **A PASS** lets stage 2 be preregistered, with the rule unchanged and its threshold recorded then.
- **A stage-2 PASS** makes LIQ-1 a candidate for the owner. It would trade only on the owner's word, on paper, through
  the risk engine, the hard gate and the paper broker, after the broker's crypto CFD terms are checked.
