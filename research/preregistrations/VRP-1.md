# VRP-1: the volatility risk premium, short VIX futures in contango (preregistration)

**Written, frozen and registered on 2026-11-05, before any VRP-1 data was fetched.** The owner, 2026-11-05: "don't
fixate on the AI trading; anything that makes us a profit; never stop".

| | |
|---|---|
| Frozen spec | `research/specs/VRP-1.json` |
| Spec sha256 | `c5020c0a17df388762cd18baeb7ac049fa5b11beb08ccdc170fe4d788f1c5734` |
| Code | `scripts/vrp1.py` and `scripts/xts1.py` (whose statistics it reuses), sha256 `6d8fff5ad62f74adcd880dbf70fcf8b0a6b4e07ebb6ba5a1d6158d067482d015` |
| Run | `.github/workflows/vrp1-run.yml` on GitHub's runner (Yahoo is blocked here): `fetch`, `judge`, and `holdout` only if `judge` PASSED |
| Threshold | t ≥ **3.0**: a new universe (`us-vol-etp`) with no earlier test, so the floor of 3.0 applies; its Bonferroni value for 2 tests is lower |

## Why this question

About 58 programs here asked whether some signal **predicts** a price. None survived costs since 2008. VRP-1 asks
about a **premium**:

- Buyers of crash insurance pay for it. Short-term VIX futures usually trade above the VIX (contango) and roll down
  toward it, so a holder of them loses, on average, what an insurance seller earns. See Whaley 2013, and Simon &
  Campasano 2014, "The VIX futures basis".
- The seller's cost is rare, violent losses when volatility spikes. Short-volatility ETPs have lost most of their
  value in a day (5 February 2018).
- The rule holds the short only while the VIX's term structure is in contango, and stands aside when it inverts,
  which is when spikes usually run.
- **No program here ever traded volatility itself.** VIX appears in R4 and COT-1 only as a predictor of FX.

## The rule (fixed; nothing is tuned)

- **Instrument.** VIXY: 1x the S&P 500 VIX Short-Term Futures index, an ETF since 2011-01.
- **Signal.** For each trading day, the position over (previous close, today's close] is short VIXY if VIX / VIX3M
  < 1 (contango) at the close **before** the previous one, and flat otherwise. The lag is one day, so the 15 minutes
  between the indices' 16:15 and the ETF's 16:00 close can never be read early.
- **Sizing.** The short is held at a constant notional, resized each day.
- **Costs.** A change of exposure and each day's resizing pay 0.10% of the notional traded. The short pays a borrow
  fee of 3% a year on the notional.
- **Data.** Yahoo daily closes (VIXY adjusted for its splits; the indices as published), each file's sha256 in the
  manifest. A day without its prices is no trade, never filled.

## Periods

| Role | Period |
|---|---|
| Development | 2011-02-01 → 2016-12-31 |
| Validation | 2017-01-01 → 2021-12-31 |
| Judged (significance) | 2011-02-01 → 2021-12-31 |
| Holdout | 2022-01-01 → 2026-09-30. The judge cuts its data there. Opened once, only if VRP-1 PASSED, as its own trial (VRP-1-H) |

## Gates (all required)

| Gate | |
|---|---|
| t | t of the mean daily net return ≥ 3.0 |
| development | mean daily net > 0 in 2011-02 to 2016 |
| validation | mean daily net > 0 in 2017 to 2021 |
| costs ×2 | mean daily net > 0 with the trading cost and the borrow fee both doubled |
| top year | no calendar year supplies more than 50% of the total net |
| timing | the rule beats an always-held short at its own average exposure: mean daily difference > 0 with t ≥ 2.0 |

The timing gate asks whether the contango filter is worth anything beyond the premium itself.

**Reported, never gates.** The worst day, the maximum drawdown, the share of days short, and the always-held short's
own record, worst day and drawdown included.

**Holdout rule.** Over 2022-01 to 2026-09:

- mean daily net > 0, with one-sided t ≥ 1.645;
- mean daily net > 0 with costs doubled;
- the timing difference's mean > 0.

## After the result

- **PASSED and VALIDATED.** It is proposed to the owner as a paper strategy of its own (CLAUDE.md rule 14), followed
  forward on paper. The risk engine sizes it for its tail, small enough that a day like 5 February 2018 cannot sink
  the account. Never real money.
- **Anything else.** It is reported as it is. Nothing changes.

## Known before freezing, said now

- **The premium is famous.** Shorting VIX futures earned a great deal over 2011-2017 and then lost catastrophically
  in February 2018 and March 2020. Those years are inside the judged period.
- **The holdout covers known shocks.** 2022 to 2026 includes the shocks of August 2024 and April 2025, which are
  public knowledge. The rule was fixed before any of this data was read, and nothing in it can be tuned to them.
- **Even a pass is not a guarantee.** A strategy that sells insurance can look excellent for years and then lose
  much of it in days. The drawdown and the worst day are reported for that reason.

## Result (run 2026-11-05 on GitHub's runner, `vrp1-run` `7b92c8a`; `research/knowledge/VRP-1.json`)

**FAILED.** Two gates failed, so the holdout stays unread and nothing changes.

- Data: VIXY from 2011-01-04, and the VIX and VIX3M from 2010, all to 2026-11-04.
- The judged period was 2011-02 to 2021 (2,749 days). The rule was short on 91% of them.

| | Mean a day | Annual (arithmetic) | Sharpe | t | Gate |
|---|---|---|---|---|---|
| The rule, net | 0.168% | +61% | 0.85 | **2.33** | t ≥ 3.0: **failed** |
| Development 2011-02 to 2016 | 0.172% | +63% | 0.90 | 1.83 | > 0: passed |
| Validation 2017 to 2021 | 0.164% | +60% | 0.79 | 1.46 | > 0: passed |
| Costs doubled | 0.150% | +55% | 0.75 | 2.07 | > 0: passed |
| **Timing** (beyond an always-held short at the same exposure) | 0.018% | +7% | 0.17 | **0.46** | t ≥ 2.0: **failed** |
| Reported: the short always held | 0.164% | +60% | 0.71 | 1.95 | never a gate |

**The tail.** The rule's worst day was −34% and its worst drawdown −77%. The always-held short's were −39% and −92%.

**By year** (sum of daily net): 2011 −22%, 2012 +124%, 2013 +66%, 2014 +3%, 2015 +3%, 2016 +82%, 2017 +109%,
**2018 −106%**, 2019 +75%, 2020 +16%, 2021 +111%.

**What it means, and no more.**

- **The premium is there,** positive in both halves. But its swings are so large that 11 years do not show it at
  t 3.0. At full size a single bad year (2018) wipes out more than it earned in one good one.
- **The contango filter added almost nothing** (t 0.46). It did not step aside in time for the worst days. A
  one-day lag is the price of not reading the close early, and on these days that is the whole loss.
- A strategy with a −77% drawdown at 1x would have to run at a small fraction of capital to be survivable. That
  makes its return small too. Not a candidate.
