# EMC-1: emerging-market currency carry (preregistration)

**Written, frozen and registered on 2026-11-05, before any EMC-1 price or rate was read.**

The owner, 2026-11-05: "don't fixate on the AI trading; anything that makes us a profit; never stop".

| | |
|---|---|
| Frozen spec | `research/specs/EMC-1.json` |
| Spec sha256 | `68c72e40e032a937a2d42249fe6f859e96d1151b8b2eea4600ff0edec773510e` |
| Code | `scripts/emc1.py`, sha256 `9f7746ecde0cc3e83ce149282097ed19caa162fe0464799ebfc9ad17d7cf0052`. Every command refuses to run if either hash changes |
| Source probe | `scripts/emc_probe.py` on GitHub's runner (`emc-probe` branch, `research/results/EMC-probe.json`). Metadata only: no price or rate was read |
| Run | `.github/workflows/emc1-run.yml` on GitHub's runner, which can reach Yahoo and the BIS (this environment cannot). It runs `fetch`, then `judge`, then `holdout` only if `judge` PASSED |
| Threshold | t ≥ **3.0**. No test here has used emerging currencies, so its universe has no earlier test and the floor applies |

## Why this question

- **The finding.** A currency whose interest rate is high does not, on average, fall by as much as its rate
  differential. Holding it against the dollar has paid the differential on average, as pay for the risk that it
  crashes in a crisis (Lustig & Verdelhan 2007; Burnside, Eichenbaum, Kleshchelski & Rebelo 2011; Menkhoff, Sarno,
  Schmeling & Schrimpf 2012).
- **The question.** Did the carry of the six emerging currencies a CFD broker usually quotes pay since 2005, at a
  CFD's costs?

**Known before freezing.** Each of these is said now, so that it cannot be explained away later.

- **Carry crashes.** It lost heavily in 2008, in the 2013 taper tantrum, in the 2015 commodity slump and in
  Turkey's crises of 2018 and 2021.
- **TRY.** Turkey's lira has had the largest differential most of the time, and fell the most. The leave-one-out
  gate exists so that no single currency decides the result.
- **The rate is a proxy.** The BIS policy rate stands in for what a forward or a CFD swap pays. In crises the funding
  rate and the offshore rate can differ from it (Turkey 2018 to 2021).
- **Costs.** CFD swaps on exotic pairs usually carry a markup, so 2.5% a year is assumed. The spreads are assumed too,
  per currency, because the daily source has no bid or ask.

## The rule (fixed; nothing is tuned)

- **The currencies.** MXN, ZAR, TRY, PLN, HUF and CZK against the dollar (Yahoo's daily closes, in units per dollar).
- **The ranking.** At each month's last close common to all six, the differential of each is its central bank's
  policy rate minus the Fed's. Both are as the BIS publishes them (WS_CBPOL daily, the value in force that day, at
  most 10 days old).
- **The book.** It holds the three with the largest differential (ties by name), long against the dollar, a third
  each, until the next month's common last close.
- **Earnings.** It earns the spot move, and the differential known at the month's start, by calendar days.
- **Costs.** It pays a CFD's swap markup of 2.5% a year on what it holds. On what it trades, the month's drift
  included, it pays each currency's spread: MXN 0.03%, ZAR 0.06%, TRY 0.15%, PLN 0.05%, HUF 0.06% and CZK 0.05% each
  side.
- **Missing data.** A month with a rate unknown for any of the seven areas is no trade, never filled.

## Periods

| Role | Period | Months |
|---|---|---|
| Development | 2005-02 → 2012-12 | 95 |
| Validation | 2013-01 → 2019-12 | 84 |
| Judged (significance) | 2005-02 → 2019-12 | 179 |
| Holdout | 2020-01 → 2026-09. The judge never reads it. It is opened once, only if EMC-1 PASSED, as its own registered trial (EMC-1-H) | 81 |

TRY's Yahoo history begins on 2005-01-03, so the first common month-end is January 2005.

## Gates (all required)

| Gate | |
|---|---|
| t | t of the mean monthly net return of the carry book over the judged period ≥ 3.0 |
| development | mean monthly net > 0 in 2005-02 to 2012 |
| validation | mean monthly net > 0 in 2013 to 2019 |
| costs ×2 | mean monthly net > 0 with the spreads and the markup doubled |
| leave one out | the rule run without any one of the six currencies still earns a mean monthly net > 0 |
| top year | no calendar year supplies more than 50% of the total net |

**Holdout rule.** Over 2020-01 to 2026-09, both of these must hold. Then it is VALIDATED; otherwise it is REJECTED.

- mean monthly net > 0, with one-sided t ≥ 1.645;
- mean monthly net > 0 with the spreads and the markup doubled.

**Reported, never gates.**

- The spot part and the carry part of the return.
- The worst drawdown and the worst month.
- How many months each currency was held.
- Each year.

## After the result

- **PASSED and VALIDATED.** It is proposed to the owner as a paper strategy of its own (CLAUDE.md rule 14), on the
  broker's USD pairs. The risk engine sizes it, and it is followed forward on paper apart from every other record.
  Never real money.
- **Anything else.** It is reported as it is, and nothing changes.

## Power, declared

- **The bar.** With 179 months, t ≥ 3.0 needs a Sharpe ratio of about 0.78 a year.
- **What that means.** Emerging-market carry has been reported at about 0.3 to 0.6 over long samples, with its worst
  years in this very period. A real but ordinary carry premium would FAIL here, and that would be reported as it is.

## Result (run 2026-11-05 on GitHub's runner; `research/knowledge/EMC-1.json`)

**FAILED.** Five gates failed: t, validation, costs ×2, leave one out and top year. The holdout (2020-01 to 2026-09)
stays unread, and nothing changes.

**The data.** The six currencies had 5,679 to 5,971 daily closes each, to 2026-11-05. The BIS file had daily policy
rates for all seven areas to November 2026. All 179 judged months traded.

**The figures, 2005-02 to 2019-12.** Monthly figures are net; the annual figures are the monthly mean × 12.

| | Annual | Sharpe | t | Gate |
|---|---|---|---|---|
| Net | −0.63% | −0.05 | **−0.19** | t ≥ 3.0: **failed** |
| Development 2005-2012 | +3.15% | 0.22 | 0.63 | > 0: passed |
| Validation 2013-2019 | **−4.91%** | −0.45 | −1.19 | > 0: **failed** |
| Costs doubled | −3.17% | −0.25 | −0.96 | > 0: **failed** |
| Reported: the carry part | +6.71% | | | never a gate |
| Reported: the spot part | −4.81% | −0.38 | −1.47 | never a gate |

- **Leave one out.** Without any one currency, the mean stayed negative: from −0.05% to −0.11% a month.
- **What it held.** TRY in all 179 months, ZAR 173, MXN 97, HUF 88. PLN and CZK never ranked in the top three.
- **Drawdown.** The worst was −50.3%; the worst month was −14.9%.
- **By year.** 2007 +15.1% and 2009 +16.0%; 2008 −11.3%, 2011 −13.4%, 2013 −10.0% and 2015 −19.4%.

**What it means, and no more.**

- The differential was real and large: +6.7% a year.
- The high-yielding currencies fell by about 4.8% a year against the dollar. The swap markup and the spreads took the
  rest.
- Before 2013 the carry paid a little (t 0.63), and from 2013 it lost.
- As registered, the holdout is not opened for a hypothesis that failed.
