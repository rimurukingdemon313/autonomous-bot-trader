# NE-1: the overnight premium and overnight-to-intraday reversal in US index CFDs (preregistration)

| | |
|---|---|
| Frozen spec | `research/specs/NE-1.json` |
| Spec sha256 | `798129936d897fe2295fd2a50d2a1c39adb5684e2fac473a8e5f8c23bd7a66d6` |
| Code | `aitrader/research/canon/engine.py` (canon-1.0.0), `validate.py`, `sessions.py`, `scripts/ne1.py` |
| Tests that prove the code | `tests/unit/test_canon.py`, `tests/unit/test_canon_sessions.py`, `tests/unit/test_ne1_runner.py` |
| Run | `python scripts/ne1.py develop` once; `validate` once, promoted primaries only |
| Counted tests | 12 configurations (all count) |
| Validation threshold | t ≥ **3.6784**: Bonferroni over every test registered (FT-1 included) plus these 12 |

Written after the data audit (`docs/NEW_EDGE_AUDIT.md`) and before any NE trade was simulated on real data.
The runner was proven only on synthetic random walks with and without a planted effect.

## Why these two, and not others

The audit leaves one clean, executable bid/ask dataset whose main economic effects have not been
searched: **US index CFD hours, 2014–2020**. In it:

- the moves are large relative to the spread: overnight and intraday standard deviations are about
  60–90 bp against a 1–4 bp round trip;
- the spread is cheapest exactly at the cash-session boundaries (§3 of the audit).

**Rejected before any data, with the reason:**

| Candidate | Why rejected |
|---|---|
| FOMC pre-announcement drift | About 56 events in 2014–2020, below any trade-count criterion. Needs an external calendar not in the repository |
| Volatility compression → expansion | Predicts the size of a move, not its sign. A CFD has no straddle |
| Abnormal volume | No traded volume exists for CFDs or spot FX |
| More FX intraday families | 160+ registered FX tests already. Cost is 10–23% of a one-hour move |
| Daily trend / longer holds | DIV-2 measured the trend premium near zero since 2008, and negative after the retail financing markup |
| Cross-index relative value | Two legs double the cost, and no mechanism predicts the sign |
| Asian and Australian indices | Their "overnight" contains the US session. The mechanisms below are documented for US equities |

## NE-ON: the overnight premium

**Mechanism.** Holding equity risk over the closed period earns most of the equity premium:

- Cooper, Cliff & Gulen (2008); Kelly & Clark (2011); Lou, Polk & Skouras (2019);
- Boyarchenko, Larsen & Whelan (2023) attribute part of it to dealer inventory risk taken on at the
  close.

**Why it might persist.** It is compensation for bearing overnight inventory and gap risk, which
intraday-only capital does not carry.

**Why it is not arbitraged away.** It is a risk premium, not a mispricing. Collecting it means holding
gap risk and paying financing.

**Expected size.**

- Holding: about 17 hours; 65 hours over a weekend.
- Expected gross: if all of the S&P 500's roughly 7% a year of 2014–2016 price return accrued overnight,
  about +2.8 bp a night.
- Expected cost: about 3–4.5 bp. That is half-spreads at 16:00 and 09:00 (USA500 about 1.9, USATECH
  2.3, USA30 1.0 bp), slippage of about 0.5–1.1 bp, and financing of about 1.1 bp a trade at 2014–2016
  rates. Higher in 2017–2020.
- **The prior expectation is FAIL.** It is tested because it is the largest documented session effect
  and sits in the cheapest-cost window.

**Rules:**

| | |
|---|---|
| Instruments | USA500IDXUSD, USATECHIDXUSD, USA30IDXUSD (H1 bid/ask, Dukascopy datafeed) |
| Decision | at the close of the 15:00 New York bar (the rule is unconditional: no price is used) |
| Entry | market buy at the 16:00 New York bar's open, at the ask plus slippage |
| Exit | market sell at the first valid open at or after 09:00 New York on the next weekday (Friday → Monday), at the bid less slippage |
| Stop | catastrophic only: 3 × the standard deviation of the previous 60 completed overnight mid returns |
| Primary | ON-16-09 |
| Neighbours (all count) | entry 15:00 or 16:00 × exit 08:00, 09:00 or 10:00 (5 more) |

## NE-GAP: overnight-to-intraday reversal

**Mechanism.** Overnight price moves are driven disproportionately by retail and attention-driven
orders at the open. During the cash session, institutional liquidity partially reverses them:

- Berkman, Koch, Tuttle & Zhang (2012), "Paying attention: overnight returns and the hidden cost of
  buying at the open";
- Lou, Polk & Skouras (2019), "A tug of war": overnight and intraday returns move in opposite
  directions.

**Why it might persist.** It is compensation for intraday liquidity provision against a predictable,
attention-driven imbalance.

**Why it is not arbitraged away.** The reversal is partial and noisy, and trading it means fading the
crowd on its largest days.

**Expected size.**

- Holding: 6 hours.
- Expected gross: a few bp on days with |gap| > 1 σ. That is a hypothesis, not a measured number here.
- Expected cost: about 2.4 bp (USA500, USATECH) and 1.1 bp (USA30) round trip with slippage. No
  financing.

**Rules:**

| | |
|---|---|
| Signal | g = mid close of the 09:00 bar (09:59 New York) / mid open of the previous weekday's 16:00 bar − 1. It is known at the 09:00 bar's close |
| Filter | \|g\| > z × the standard deviation of the previous 60 values of g (strictly earlier days) |
| Direction | against g (fade) |
| Entry | the 10:00 open, at the ask or bid plus slippage |
| Exit | the first valid open at or after 16:00 |
| Stop | catastrophic: 3 × the standard deviation of the previous 60 completed 10:00→16:00 mid returns |
| Primary | GAP-z1.00-v60 |
| Neighbours (all count) | z 0.75, 1.25, 0 (every day) at v60; v40 and v80 at z 1.0 (5 more) |

## Common to both

### Data and periods

| | |
|---|---|
| Warm-up | 2013-09-01 → 2013-12-31, mid prices only, for the first volatilities. No 2013 price is ever a fill (audit §3: 2013 quotes are partly one-sided) |
| Development (select) | 2014-01-01 → 2017-01-01 |
| Validation (judge) | 2017-01-01 → 2021-01-01, promoted primaries and their neighbours only, once |
| Holdout | 2021-01-01 → 2025-01-01: sealed, never fetched, not used |
| Extra unseen period | 2025-01 → 2026-09: only for a configuration that passes validation, under its own registration |

### Engine and costs (declared, never tuned)

- **Executable prices:** buys at the ask, sells at the bid. The spread is the bar's own quoted spread.
- **Slippage:** ¼ of the bar's spread per market fill.
- **Stops:** fill half a spread through the level, or at a gapping open.
- **Commission:** 0 (index CFDs are spread-only).
- **Financing:** the BIS US policy rate public at the rollover, plus 2.5%/yr, day count 360, a Friday
  counting 3 days. A short over a rollover also pays 2%/yr in dividends.
- **Approximations:** slippage, the markup and the dividend yield are declared approximations. No
  broker history exists (audit §12).

Every trade carries its ledger: gross, spread, slippage, through-fill, commission, financing and net.

### Position sizing

Research measures bp per unit of notional. A live trade would be sized only by `aitrader/risk/engine.py`,
from the stop distance. Nothing here sizes anything.

### Statistics

The unit is the **daily book**: the equal-weight mean of the trades entered on a New York date. The
three US CFDs are correlated, and the daily book does not count them as independent.

### Promotion from development (the primary of each family; all required)

| Gate | Requirement |
|---|---|
| min_trades | ≥ 300 |
| net_bp | > 0 |
| t_day | ≥ 2.0 |
| costs_x1.25 | net > 0 |
| costs_x1.5 | net > 0 |
| latency_1bar | net > 0 with entry one bar (an hour) later |
| vs_random_window | Welch t ≥ 2.0 against random entries with the same side, holding time and stop, within ±10 trading days (seeds 1, 2, 3) |
| mechanism | ON: overnight gross minus the next session's 10:00→16:00 long gross, paired by day, mean > 0 and t ≥ 2.0. GAP: block permutation of sides (2,000, block 5, seed 0) p ≤ 0.05, and Welch t ≥ 2.0 against random sides |
| without_top5 | net > 0 without the five best trades |
| neighbours | every other configuration of the family net > 0 |
| halves | both chronological halves net > 0 |

### Validation (all required)

Every development gate applies, with **t_day ≥ 3.6784**, plus:

- ≥ 3 of the 4 years net > 0;
- net > 0 in ≥ 2 of 3 volatility terciles (cuts fixed on development);
- the five best trades < 50% of the total;
- ≥ 2 of 3 instruments net > 0;
- block-bootstrap P(total ≤ 0) ≤ 0.05 (5,000, 10-day blocks, seed 0);
- total net / maximum daily-book drawdown ≥ 1.0.

### Reported, never gated

- costs × 2;
- buy-and-hold (16:00 → 16:00 long), the intraday long (10:00 → 16:00) and no-signal (0) baselines;
- GAP's price-direction baseline (follow instead of fade);
- splits by weekday and instrument;
- exit reasons;
- exposure, turnover, the worst 5% of trades, and the Monte Carlo drawdown distribution.

### Power, stated before any result

- **NE-ON.** The overnight standard deviation is about 70 bp, and about 740 development days pool the
  three CFDs.
  - The daily-book standard error is about 2.6 bp, so t ≥ 2 needs about **+5 bp net** a night.
  - That is roughly the whole documented premium net of costs. A pass is unlikely unless the premium
    was unusually large in 2014–2016.
- **NE-GAP.** The intraday standard deviation is about 80 bp, and at z = 1 about 30% of days qualify
  (about 225).
  - t ≥ 2 needs about **+10 bp net**.
- A FAIL with a small positive net means "not detectable in this sample", not "proven absent". It
  will be reported that way.

### Labels (decided now)

| Label | Requires | Meaning |
|---|---|---|
| ROBUST EDGE FOUND | validation passes **and** a forward paper test passes | not claimable from history alone |
| PROMISING BUT NOT YET PROVEN | validation passes | a frozen release candidate goes to a forward paper test |
| NO ROBUST EDGE FOUND | anything else | final for these rules |

### Forbidden, by this document

- changing a rule, a parameter, a cost or a gate after any result;
- adding configurations;
- choosing instruments or years after seeing them;
- reading 2021–2024;
- a second development or validation run.

A failed family is not re-run with variations. A genuinely different idea gets a new ID and counts.
