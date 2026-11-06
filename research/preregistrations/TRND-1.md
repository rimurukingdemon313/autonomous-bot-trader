# TRND-1: the long-only 10-month trend filter, swap-free (preregistration)

**Written, frozen and registered on 2026-11-06, before any TRND-1 price was kept or computed.** A dates-only probe
ran the fetch first (below).

The owner, 2026-11-06: "everything is allowed; test everything; try everything", and "the most important thing is
Islamic".

| | |
|---|---|
| Frozen spec | `research/specs/TRND-1.json` |
| Spec sha256 | `cdd2f51e5ab655516550eff14efb10fe61e97d490cc215008ed5e65561047aa0` |
| Code | `scripts/trnd1.py`, sha256 `2d9db914f337f5e2a1d2e28523ba8a1ce97980f587c518ce3825250187114384`. Every command refuses to run if either hash changes |
| Run | `.github/workflows/trnd1-run.yml` on GitHub's runner, which can reach Yahoo (this environment cannot). It runs `fetch`, then `judge`, then `holdout` only if `judge` PASSED. It also prints the result and the registry line to its log, so a refused push cannot lose them |
| Probe | `scripts/trnd_probe.py` ran TRND-1's own fetch on GitHub's runner before freezing, and recorded dates only (`research/results/TRND-probe.json`). ^GSPC has 24,831 daily closes from 1927-12-30, ^NDX from 1985-10-01, ^GDAXI from 1987-12-30 and ^FTSE from 1984-01-03, and none of them has a month without a close. No price was printed, kept or computed |
| Threshold | t ≥ **3.376**. That is the Bonferroni value for 67 earlier tests plus this 1, and never below 3.0. The 67 are every test on stock-index or US equity data: multi-asset-etf (12), multi-asset-long (10), equity-index-b (2), equity-index-forward (3), index-cfd-intraday (32), us-equity-etf (6) and us-vol-etp (2). The intraday index tests count too. RBL-1 left them out; its t of 1.57 fails either bar |

## Why this question

- **The owner's condition.** Islamic: no interest paid or earned (a swap-free account), long only, no leverage. Most
  ideas in this registry need shorts, leverage or months of financing. This one needs none of them.
- **The cost lesson.** Real effects here keep showing before costs and vanishing after them. For an index held for
  months, the largest cost was the financing: RC-EQ measured the same rule (its E4) on ten index CFDs over 1990-2020
  at 5.76% a year before any cost, and 2.42% (t 1.66) after a CFD's financing of 3.30% a year. A swap-free account
  has no financing. Those years are already judged, are not re-tested, and are quoted only as the reason to ask.
- **The rule.** Faber (2007, "A Quantitative Approach to Tactical Asset Allocation"): hold the index while its
  month-end close is above its 10-month average, and step aside otherwise.
- **The mechanism.** Large bear markets have usually unfolded over months, and prices fall below their long average
  before the deepest losses. The rule is a way to own the market with an exit, not a prediction. Its documented
  benefit is smaller crashes, at about the market's own return.
- **The question.** On data no test here has read, the S&P 500 from 1929 to 1989, did it earn a positive return
  clearly enough, with a smaller worst fall than holding the index all the time, at a swap-free account's costs?

**Known before freezing.** Each of these is said now, so that it cannot be explained away later.

- **This is a replication on the data the rule was found on.** Faber published it in 2007 from the S&P 500's history
  since 1901, which contains every judged year, and moving averages of about this length were in use long before.
  No test *here* has read 1929-1989, so the data are fresh for this registry, but not for the rule. A pass would
  confirm the published result at the owner's costs. It would not show that the rule lasts. The evidence after
  publication is RC-EQ's years after 2007, the holdout below, and the paper desk.
- **It is not an edge over the market.** Most of what it earns is the stock market's own premium. The queue's power
  ceiling (2026-11-06) says a candidate is built only when its effect is several times the equity premium's, and this
  one is not. It is built anyway, for two reasons: the judged sample is 61 years, about twice the 1988-2020 one that
  note measured, and the filter's t comes from cutting the spread of returns, not from a larger mean. Its chance of
  passing is declared below.
- **The data.** Yahoo's ^GSPC daily closes from late 1927. Before March 1957 the series is, by S&P's own history, its
  90-stock predecessor. It is a price index: dividends, about 4% a year over these decades, are not counted, though a
  long index CFD is paid them. While flat, the rule earns nothing, where Faber's version earned Treasury bills; an
  Islamic account earns no interest. Both make the test harder to pass, not easier.
- **The signal and the trade use the same month-end close.** In practice the bot would act minutes before the close.
  In RC-EQ, acting a full day later cost the same rule about 0.2% a year before costs (5.55% against 5.76%).
- **Two Islamic questions are for the owner, not for this test.** The whole S&P 500 includes banks and other
  businesses that a Shariah screen leaves out. Whether an index CFD is permissible at all is for the owner's own
  scholar. Some swap-free accounts charge a fixed fee on long holds instead of a swap, so the judge reports the yearly
  fee that would have taken the whole return.
- **The holdout is not untouched.** DIV-2-H read the S&P 500, DAX and FTSE 100 index levels from 2021 for a different
  trend rule: twelve-month momentum, long and short, over 23 markets. FOMC-1 read the US 500 CFD's intraday bars in
  2021, and FT-1 the US 500's and US Tech 100's hour bars in 2025-2026. None of them computed this rule on these
  indices, and this rule was fixed from the literature, so they could not have shaped it. The holdout's 69 months
  cannot show significance either. It can only catch a rule that has stopped earning, or stopped protecting, on the
  broker's own instruments.

## The rule (fixed; nothing is tuned)

- **The month-end.** Each calendar month's last daily close.
- **The decision.** At each month-end close, the index is held for the next month if the close is above the mean of
  the last 10 month-end closes, this one included. Otherwise it is not held for that month, and the month earns
  nothing.
- **Costs.** Each switch in or out pays 0.05% for spread and slippage. There is no financing (swap-free) and no
  interest while flat.
- **No bridging.** A calendar month without a close is never bridged: no return spans it, and no decision is taken on
  ten month-ends that include it.
- **The statistic.** The mean net return per month, with its t.

## Periods

A month belongs to the period of the month it is held.

| Role | Months held | Months |
|---|---|---|
| Development | 1929-01 → 1958-12 | 360 |
| Validation | 1959-01 → 1989-12 | 372 |
| Judged (significance) | 1929-01 → 1989-12 | 732 |
| Holdout | 2021-01 → 2026-09: the US 500, US Tech 100, GER 40 and UK 100 (^GSPC, ^NDX, ^GDAXI, ^FTSE). The judge never reads it. It is opened once, only if TRND-1 PASSED, as its own registered trial (TRND-1-H) | 69 |

The first decision needs ten month-ends. The judge reads ^GSPC from its first close in late 1927 and no close after
1989. The holdout reads 2020's closes for its first decisions, and uses no 2020 return.

## Gates (all required)

| Gate | |
|---|---|
| complete | every one of the 732 judged months has its close and its decision |
| t | t of the mean net return per month over the judged months ≥ 3.376 |
| development | mean net per month > 0, 1929 to 1958 |
| validation | mean net per month > 0, 1959 to 1989 |
| costs ×2 | mean net per month > 0 with the switching cost doubled |
| smaller crash | the worst peak-to-trough fall is smaller than holding the index all the time |
| top year | no calendar year supplies more than 50% of the total |

**Holdout rule.** The four indices at equal weight, each with its own filter, over all 69 months 2021-01 to 2026-09.
All of these must hold, and then it is VALIDATED; otherwise it is REJECTED:

- mean net per month > 0;
- mean net per month > 0 with the cost doubled;
- a worst fall smaller than holding all four all the time;
- every month present for every index.

**Reported, never gates.** Holding the index all the time (its mean and t), the time in the market, the number of
switches, the yearly holding fee that would have taken the whole return, and each year.

## After the result

- **PASSED and VALIDATED.** It is proposed to the owner as a paper strategy of its own (CLAUDE.md rule 14), on the four
  index CFDs, with one decision a month. It is described as owning the market with an exit rule, not as an edge. It is
  followed forward on paper, apart from every other record, and never with real money. It holds for months with no
  stop, which the bot's sizing does not handle as it stands, so how the risk engine would size it is a design
  question for the owner first.
- **Anything else.** It is reported as it is, and nothing changes.

## Power, declared

Estimated, not measured: no TRND-1 price has been read.

- **A rough model.** Studies of the rule on the S&P 500's long history put it in the market about 70% of months, and
  its held months are calmer than the rest. Suppose a held month earns 0.6-0.7% in price on average, with a spread of
  3.7-4%, and a flat month earns nothing. Then the rule earns about 0.42-0.49% a month with a spread of about
  3.1-3.4%. Over 732 months, t is about 3.4 to 4.3.
- **The one measured figure.** RC-EQ's own numbers for the same rule on ten index CFDs, 1990-2020, before any cost or
  financing: 5.76% a year, with a monthly spread of 2.34% over 372 months, about t 4.0. A basket of ten is calmer than
  one index.
- **What that means.** The bar of 3.376 sits at the low end of that range. TRND-1 passes only if the rule did about as
  well as those studies imply, which gives it roughly a two-in-three chance. A weaker result would FAIL. A failure
  would say that on price alone, earning nothing while flat, the filter did not pay clearly enough even on the data it
  was found on.
- **What a pass would be worth.** In that model the rule earned about 5-6% a year in price, before dividends. That is
  the stock market's own return made calmer. It is not high profit, and the past is not a forecast.
