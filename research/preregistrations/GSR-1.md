# GSR-1: gold/silver ratio mean reversion (preregistration)

**Written, frozen and registered on 2026-11-05, before any GSR-1 price was read.**

The owner, 2026-11-05: "don't fixate on the AI trading; anything that makes us a profit; never stop".

| | |
|---|---|
| Frozen spec | `research/specs/GSR-1.json` |
| Spec sha256 | `f12af81e026a889ca4843d24714d1fc4290e1316eba6f95e7a93a151c62afd98` |
| Code | `scripts/gsr1.py`, sha256 `9ade6758879667c0e3eaadaf2c4c230118722d2fb59a033dbc0c2e4f7295e337`. Every command refuses to run if either hash changes |
| Source probe | `scripts/gsr_probe.py` on GitHub's runner (`gsr-probe` branch, `research/results/GSR-probe.json`). Metadata only: no price was read |
| Run | `.github/workflows/gsr1-run.yml` on GitHub's runner, which can reach Yahoo (this environment cannot). It runs `fetch`, then `judge`, then `holdout` only if `judge` PASSED |
| Threshold | t ≥ **3.0**. Its universe (daily metals futures) has no earlier test in the registry, so the floor applies. The fx-majors tests that used intraday XAUUSD asked other questions, of another instrument and frequency, and are not counted |

## Why this question

Gold and silver share their drivers: the dollar, real rates and the demand for a store of value. Silver adds
industrial demand and about twice the swings. Their ratio has swung between about 30 and 120.

- **The trade.** Traders have long bought the cheap metal against the dear one when the ratio stretched.
- **The question.** Does that pay as a rule: a pair against a ratio stretched to two standard deviations from its
  year's mean, held until it is back, at a retail CFD's costs?

**Known before freezing.** Each of these is said now, so that it cannot be explained away later.

- The ratio has had long regimes without reversion. It went from about 45 in 2011 to about 85 in 2019, and spent
  2020 to 2025 mostly between 70 and 100. A stretch can be the start of a new level. The year's mean follows it, and
  a trade against it pays financing while it waits.
- **The source.** The probe of 2026-11-05 found only Yahoo usable:
  - stooq answered a page without data;
  - LBMA refused (403);
  - Yahoo's front-month futures (GC=F, SI=F) had 6,622 daily rows each, from 2000-08-30.
- **Roll jumps.** Those futures series are not roll-adjusted. Each roll moves the series by the next contract's
  premium, about the short rate over two months (up to about 0.8%). Gold and silver roll in different months, so
  the ratio carries small jumps on those days, against a yearly standard deviation of about 10 to 15%. They are
  part of the data; nothing corrects them.
- **Costs.** A CFD pair pays financing on both legs while held, so a long wait for reversion is expensive.

## The rule (fixed; nothing is tuned)

- **The stretch.** At each day's close, L = ln(gold / silver), and z = (L − the mean of L over the 252 trading days to
  that close) / their standard deviation.
- **In.** Flat and z ≥ 2 (the ratio stretched high): at the NEXT day's close, buy silver and sell gold, one dollar
  each. Flat and z ≤ −2: buy gold and sell silver.
- **Out.** At the next day's close after z crosses back through 0, or after 252 trading days held, whichever comes
  first.
- **Positions.** One trade at a time. A day without both closes is no trade. A position never runs across a period's
  edge.
- **Costs, each side.** 0.03% on gold and 0.10% on silver (spread and slippage).
- **Financing.** The long leg pays the short rate plus 2.5% a year, and the short leg receives the short rate minus
  2.5%. So the pair pays 5% a year while held.

## Periods

| Role | Period |
|---|---|
| Development | 2002-01-01 → 2010-12-31 |
| Validation | 2011-01-01 → 2019-12-31 |
| Judged (significance) | 2002-01-01 → 2019-12-31 |
| Holdout | 2020-01-01 → 2026-09-30. The judge never reads it. It is opened once, only if GSR-1 PASSED, as its own registered trial (GSR-1-H) |

## Gates (all required)

| Gate | |
|---|---|
| t | t of the mean daily net return over the judged period (flat days count as zero) ≥ 3.0 |
| development | mean daily net > 0 in 2002 to 2010 |
| validation | mean daily net > 0 in 2011 to 2019 |
| costs ×2 | mean daily net > 0 with every cost and the financing doubled |
| both sides | the trades against a high ratio, and those against a low one, each net > 0 in total |
| top year | no calendar year supplies more than 50% of the total net |

**Holdout rule.** Over 2020-01 to 2026-09, both of these must hold. Then it is VALIDATED; otherwise it is REJECTED.

- mean daily net > 0, with one-sided t ≥ 1.645;
- mean daily net > 0 with every cost and the financing doubled.

**Reported, never gates.** Every trade (side, entry, exit, days, net), the trades per side, the share of days held,
the worst drawdown, and each year.

## After the result

- **PASSED and VALIDATED.** It is proposed to the owner as a paper strategy of its own (CLAUDE.md rule 14), on XAUUSD
  and XAGUSD. The risk engine sizes it, and it is followed forward on paper apart from every other record. Never real
  money.
- **Anything else.** It is reported as it is, and nothing changes.

## Power, declared

- **Few trades.** With a two-standard-deviation entry and a wait for the mean, the rule may trade only a few times a
  year.
- **The bar.** t ≥ 3.0 over 18 years needs a Sharpe ratio of about 0.7 a year on the daily series, flat days
  included.
- **What that means.** A real but modest reversion would FAIL here, and that would be reported as it is.

## Result (run 2026-11-05 on GitHub's runner; `research/knowledge/GSR-1.json`)

**FAILED.** Every gate failed: t, development, validation, costs ×2, both sides and top year. The holdout (2020-01 to
2026-09) stays unread, and nothing changes.

**The data.** GC=F had 6,572 daily closes and SI=F 6,573, from 2000-08-30 to 2026-11-05, dated by the exchange's own
calendar.

**The figures, 2002 to 2019.** The judged period had 4,516 days with both closes. The rule held a pair on 53.5% of
them, over 19 trades.

| | Mean a day (annual) | Sharpe | t | Gate |
|---|---|---|---|---|
| Net | −0.0046% (−1.16%) | −0.07 | **−0.31** | t ≥ 3.0: **failed** |
| Development 2002-2010 | −1.12% a year | −0.07 | −0.20 | > 0: **failed** |
| Validation 2011-2019 | −1.20% a year | −0.08 | −0.25 | > 0: **failed** |
| Costs and financing doubled | −4.11% a year | −0.26 | −1.10 | > 0: **failed** |

- **By side.** The 11 trades against a high ratio netted −1.3% in total, and the 8 against a low ratio −19.5%.
- **One trade decided it.** Long gold and short silver from 2010-09-30 to 2011-09-15 lost 40.3% in 242 days, as
  silver doubled into its April 2011 peak and the ratio kept falling.
- **Drawdown.** The worst was −53%.
- **By year.** 9 of the 18 years were negative, and the total was below zero.

**What it means, and no more.**

- A ratio two standard deviations from its year's mean did not come back reliably enough to pay a pair's costs and
  financing.
- The worst case was the one feared before freezing: a stretch that was the start of a new move, not its end.
- As registered, the holdout is not opened for a hypothesis that failed.
