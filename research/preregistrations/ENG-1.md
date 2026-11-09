# ENG-1: the energy futures term-structure premium (preregistration)

**Written 2026-11-09, before any energy price was read.** The EIA probe (`scripts/eng_probe.py`,
`research/results/ENG-probe.json` on branch `eng-probe`) read dates only. Research only: nothing here trades.

- Spec sha256: `e9fa99258143ec25d4e7056cd1482d304886701c55a4bee9c3ac9b2a679a329a` (`research/specs/ENG-1.json`)
- Code sha256: `92520ce39f76de80ac7af3a97c75a5dd6579aa21bf0bf0237b2d316591269595` (`scripts/eng1.py`)
- Threshold: t ≥ **3.0**. No test here has read energy futures curves, so Bonferroni gives 1.96; the program's floor
  of 3.0 applies.

## The question

Does holding an energy future only while its curve is backwardated earn a positive net return at a swap-free CFD's
costs, and more than holding it always? Backwardated means contract 2 above contract 3.

## Why it might pay

- **The theory of storage** (Kaldor, Working, Brennan). When inventories are scarce, the curve is backwardated and
  holders of the nearby contract earn a convenience yield.
- **Hedging pressure** (Keynes; de Roon, Nijman & Veld). Producers hedge short and pay a premium to the longs who carry
  their risk.

Both say a backwardated contract should, on average, roll up toward the spot price, and a contango one roll down. The
term-structure factor across commodities has a Sharpe ratio of about 0.41-0.49. That evidence is cross-sectional, long
and short; no single-energy, long-or-flat result was found (`docs/DISCOVERY_PROGRAM.md`, sources). This is the first
test of the mechanism here, and the first use of energy curves.

## The data

EIA's daily settlements of NYMEX contracts 1, 2 and 3. EIA stopped publishing them after 2024-04-05. The probe found
these spans:

| Energy | Series | All three contracts priced | Notes |
|---|---|---|---|
| WTI crude | RCLC1-3 | 1985-01-02 → 2024-04-05 | |
| NY Harbor heating oil | EER_EPD2F_PE1-3_Y35NY_DPG | 1994-02-08 → 2024-04-05 | about 30-37 weekdays a year without a price |
| NY Harbor RBOB gasoline | EER_EPMRR_PE1-3_Y35NY_DPG | 2005-10-03 → 2024-04-05 | |
| Henry Hub natural gas | RNGC1-3 | 1994-01-19 → 2024-04-05 | |

The series for conventional gasoline before RBOB (EER_EPMRU_*) answered 404, so it is not used. The data are fetched
on GitHub's runner by `python scripts/eng1.py fetch`, with every file's sha256 in `data/eng/manifest.json`.

## The book (frozen in the spec)

- **Decision days.** Each energy's last day of each month with contracts 1-3 priced.
- **Signal.** At month m−1's decision day t: 12 · ln(C2/C3). If it is above 0, the energy is held over month m;
  otherwise it is flat. Long or flat, never short.
- **The contract held** is the one that is contract 2 at t. Its price at month m's decision day is that same
  contract's. The exchange's expiry rules identify which of contracts 1-3 it has become:
  - WTI: three business days before the 25th of the month before delivery;
  - heating oil and RBOB: the last business day of the month before delivery;
  - natural gas: three business days before the delivery month.
  A roll never mixes two contracts. Holding contract 2 also avoids WTI's negative front-month price of 2020-04-20.
- **Weights.** For each energy, 10% a year divided by the volatility of its past 12 monthly returns of holding it
  always, known at t (at least 6 months), capped at 2.0. Divided by the number of energies with data that month.
- **Costs.** One way, in basis points of notional: WTI 3.5, heating oil 7, RBOB 7, natural gas 11. That is the CFD's
  half spread plus 1 bp of slippage. Charged on every change of exposure, and once more each month a position is held,
  for its roll. No financing: a swap-free account.

## The test (judged once)

The judged months are 1985-02 to 2018-12: development 1985-02..2001-12, validation 2002-01..2018-12. Nothing from 2019
on is read. ENG-1 passes only if every gate passes:

| Gate | Rule |
|---|---|
| t | The monthly net t over 1985-02..2018-12 ≥ 3.0 |
| development, validation | Mean net > 0 in each |
| costs ×2 | Mean net > 0 at twice the costs (×1.5 is reported) |
| one month late | Mean net > 0 with the signal a month old |
| beats always-long | The mean monthly difference to holding every energy always, at the same weights, is > 0 |
| beats random | The mean exceeds the 95th percentile of 2,000 books with each energy's long months shuffled among its own months (seed 41) |
| leave one out | Mean net > 0 with any one energy left out |
| top year | No year gives more than 25% of the total net |
| bootstrap | The 12-month block bootstrap's 95% interval of the mean is above 0 (5,000 draws, seed 43) |

The knowledge file reports:

- the net and gross means, the costs by kind and the Sharpe ratio;
- the worst fall, the months won, the exposure, the turnover and the long/flat switches a year;
- results by year and by energy;
- always-long and the shuffled baseline.

## The holdout

**2019-01..2024-03.** It is registered (ENG-1-H) and read only if ENG-1 passes. The same book, unchanged. It passes if
its mean net is above 0, and above 0 at twice the costs, with every energy present. It covers the 2020 crash and the
2021-2022 energy crisis.

## Power, written before the test

At the sourced Sharpe ratio of 0.41-0.55 over the 34 judged years, expected t is 2.4-3.2 against 3.0: it passes about
27-58% of the time. TRND-1 was built at about two in three, DAY-1 at one in three.

## What could make it fail, or mislead

- The premium may be small next to energy's volatility.
- 2005-2014 was dominated by contango.
- A broker's CFD may not pass the whole roll on. Before any paper desk, its contract specification is checked.
- Only WTI and natural gas are commonly quoted as CFDs. The leave-one-out gate keeps any single energy from carrying
  the result.
- Heating oil's missing days move its decision day earlier in some months. The exchange calendar keeps the contract
  identity right, and the tests check it on built curves.

## What follows

- **A FAIL** is recorded as such. The family is closed for these data.
- **A PASS** opens the holdout once.
- **A PASS in the holdout too** makes ENG-1 a candidate for the owner. It would trade only on the owner's word, as a
  paper desk through the risk engine, the hard gate and the paper broker, after the broker's roll terms are checked.

## Result (judged 2026-11-09 on GitHub's runner, run 42670396500): FAILED

**FAILED on 3 of 10 gates: t, top year and bootstrap.** EIA served all twelve series (`research/results/eng1-fetch.log`).
Full figures: `research/knowledge/ENG-1.json`. The data are on branch `eng1-run`, with every file's sha256.

| | |
|---|---|
| Net | +0.206% a month, **+2.48% a year**, 400 months (1985-02..2018-12) |
| t | **2.09** against 3.0 |
| Sharpe ratio | 0.36 |
| Volatility, worst fall | 6.8% a year; worst fall 26.4% |
| Gross, costs | +0.219% a month gross; costs 0.013% a month (0.004% trades, 0.008% rolls). At twice the costs: t 1.96 |
| Development, validation | 1985-2001: +3.55% a year (t 1.76). 2002-2018: +1.44% a year (t 1.13) |
| One month late | +0.80% a year (t 0.66) |
| Always long, same weights | +1.05% a year (t 0.56), worst fall 55.7%. The signal's margin over it: +1.4% a year (t 1.08) |
| Shuffled long months, 2,000 books | 95th percentile +0.134% a month. **Only 0.3% of the shuffled books did as well** |
| Leave one out | All positive. WTI carried most: without it, +0.09% a month |
| Bootstrap 95% | −0.006% to +0.434% a month: it touches zero |
| Top year | 1996 gave 26.5% of the total, against the 25% gate |
| By energy | WTI +0.17% a month, heating oil +0.09%; natural gas and RBOB about nothing |

**What it means.**

- **The curve's slope does carry information.** Timing energy by it beat 99.7% of random timings with the same
  exposure, and it beat holding always.
- **The premium is too small to be an edge.** +2.5% a year at 6.8% volatility. Half as large after 2002. Gone within
  a month. Its confidence interval reaches zero.
- At the $200,000 account, that would be about $400 a month at this volatility. The $4,000 target would need about ten
  times the risk.

**The rules.** The holdout (2019-01..2024-03) stays unread. The family is closed on these data, and no variant
(contract 1 against 2, other weights, other energies) is run on them.
