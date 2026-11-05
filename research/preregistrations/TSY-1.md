# TSY-1: the Treasury auction cycle (preregistration)

**Written, frozen and registered on 2026-11-05, before any TSY-1 price was fetched.**

The owner, 2026-11-05: "don't fixate on the AI trading; anything that makes us a profit; never stop".

| | |
|---|---|
| Frozen spec | `research/specs/TSY-1.json` |
| Spec sha256 | `9478e74f189851bbaa91758929366c57d645690cba95fa403621231da22cc399` |
| Code | `scripts/tsy1.py`, sha256 `88638611afef2809044ee24e88f5fb90a17db8b51943cdf55a4da956c395f26f`. Every command refuses to run if either hash changes |
| Run | `.github/workflows/tsy1-run.yml` on GitHub's runner, which can reach Yahoo and the Treasury's fiscaldata API (this environment cannot). It runs `fetch`, then `judge`, then `holdout` only if `judge` PASSED. It also prints the result and the registry line to its log, so a refused push cannot lose them, as LVOL-1's did |
| Threshold | t ≥ **3.065**. That is the Bonferroni value for 22 earlier tests plus this 1, and never below 3.0. The 22 are every test on the two universes that read Treasury prices or yields: multi-asset-etf (DIV-1's TLT and IEF, and the trials sharing its data: 12) and multi-asset-long (DIV-2's 10- and 5-year yields, and the trials sharing its data: 10). A trial on both is counted on each |

## Why this question

- **The finding.** Lou, Yan & Zhang (2013, Review of Financial Studies) found that Treasury prices fall in the few days
  before each auction and recover in the days after. This happens although every auction's date and size are announced
  in advance. They put the hidden cost at 9 to 18 basis points of each auction's size. Their sample was 1980-2008.
- **The mechanism.** Dealers must absorb each auction's new supply and hedge it before the auction. The investors who
  will finally hold the new notes arrive only slowly afterwards.
- **Later evidence.** Two sources are known here only through web-search summaries, because their hosts are blocked:
  - Fleming, Liu & Nguyen (Federal Reserve Bank of New York) still see yields rise in the hours before auctions and
    reverse afterwards, in recent intraday data.
  - A discussant's slides (Collin-Dufresne, 2011) report a 10-year note strategy around auctions with a Sharpe ratio
    of 1.44 before costs and 0.9 after, over the last ten years of the paper's sample.
- **The question.** Since 2009, outside the paper's sample, does the cycle around the 10-year note's auctions still
  pay? It is held the way a retail CFD holds the 7-10 year Treasury ETF (IEF).

**Known before freezing.** Each of these is said now, so that it cannot be explained away later.

- **Non-dealers absorb more.** They now buy more of each auction, and the New York Fed finds the price pressure has not
  grown. The effect may be smaller than in 1980-2008.
- **The papers were not read in full.** Their hosts are blocked here. The windows below come from the papers'
  abstracts: prices fall in the few days before and recover shortly after. They are fixed at five trading days each
  side, before any price was seen, and are not tuned.
- **Month-end is kept out.** The 2-, 5- and 7-year notes are auctioned in the last week of the month. Their recovery
  would overlap the month-end Treasury effect, which is TME-1's own question. Only the 10-year note's auctions are
  events. They fall in the second week of the month, and their windows end before the month's last week.
- **The calendar is known in advance.** The Treasury publishes a tentative quarterly schedule, and it announces each
  auction about a week ahead. The short leg opens at the close six trading days before the auction, which is
  sometimes before the formal announcement but never before the schedule.
- **The broker.** A CFD broker may quote a 10-year Treasury contract, IEF, or neither.

## The rule (fixed; nothing is tuned)

- **The events.** Every auction of a 10-year nominal note, new issue or reopening, from the Treasury's auction records
  (fiscaldata `auctions_query`). Only its date, term and type flags are read, never a yield, price or amount. TIPS and
  floating-rate notes are not events.
- **The trade.** For an auction on trading day a:
  - short IEF from the close of day a−6 to the close of day a−1 (five days);
  - flat on the auction day;
  - long from the close of day a to the close of day a+5 (five days).
- **Costs.** Each leg pays 0.03% a side for spread and slippage. The long leg pays the T-bill yield plus 2.5% a year
  for each night. The short leg is paid the T-bill yield minus 2.5% a year. The yield is the one last published
  (`^IRX`, at most 7 days old), with zero and negative yields kept.
- **No trade.** An auction whose day is not an IEF trading day, an event whose window overlaps the previous traded
  one, and an event whose financing is unknown are all no trade.
- **The statistic.** Each event's net return is its two legs together. The test is the mean over events with its t.

## Periods

| Role | Auctions | Events (about) |
|---|---|---|
| Development | 2009-01 → 2014-12 | 72 |
| Validation | 2015-01 → 2020-12 | 72 |
| Judged (significance) | 2009-01 → 2020-12 | 144 |
| Holdout | 2021-01 → 2026-09. The judge never reads it. It is opened once, only if TSY-1 PASSED, as its own registered trial (TSY-1-H) | 69 |

An event belongs to the period of its auction day, and its last close must fall inside that period.

## Gates (all required)

| Gate | |
|---|---|
| t | t of the mean net return per event over the judged period ≥ 3.065 |
| development | mean net per event > 0 in 2009 to 2014 |
| validation | mean net per event > 0 in 2015 to 2020 |
| costs ×2 | mean net per event > 0 with the cost per side and the markup doubled |
| both legs | the short leg's mean net > 0, and the long leg's mean net > 0 |
| top year | no calendar year supplies more than 50% of the total |

**Holdout rule.** Over 2021-01 to 2026-09, both of these must hold. Then it is VALIDATED; otherwise it is REJECTED.

- mean net per event > 0, with one-sided t ≥ 1.645;
- mean net per event > 0 with the costs doubled.

**Reported, never gates.** Each leg's gross and net mean, the hit rate, each year, the auctions traded, and every
auction left out, with the reason.

## After the result

- **PASSED and VALIDATED.** If the broker quotes a 10-year Treasury contract or IEF, it is proposed to the owner as a
  paper strategy of its own (CLAUDE.md rule 14). That would be about twelve events a year. The risk engine sizes it,
  and it is followed forward on paper apart from every other record. Never real money.
- **Anything else.** It is reported as it is, and nothing changes.

## Power, declared

- **The bar.** 144 events and t ≥ 3.065 need a mean of about a quarter of one event's own spread (3.065/√144). One
  event's two legs together move IEF by about 1.2% at one standard deviation, so the bar is about 0.3% net per event.
- **The costs.** The two legs pay about 0.12% in spread and about 0.1% in markup per event. The gross cycle must
  therefore be about 0.5% per event.
- **What that means.** That is about what the reported Sharpe ratio of 1.44 before costs implies: 0.42 of one event's
  spread, twelve times a year. TSY-1 can pass only if the cycle kept most of its old strength after 2008. A cycle at
  half its old size would FAIL. Its failure would then say only that the cycle is too small to pay a retail CFD, and
  that would be reported as it is.

## Result (run 2026-11-05 on GitHub's runner; `research/knowledge/TSY-1.json`)

**FAILED.** Five gates failed: t, validation, costs ×2, both legs and top year. The holdout (2021-01 to 2026-09) stays
unread, and nothing changes.

**The data.** IEF had 6,108 daily closes from 2002-07-30 and ^IRX 8,498, both to 2026-11-05. The Treasury's records
gave 1,650 note auctions from 2002, 268 of them 10-year nominal by the rule. All 144 judged events traded. Two 2019
auctions were left out as overlapping (below).

**The figures, 2009-01 to 2020-12 (144 events).** Each figure is per event, net unless it says gross.

| | Mean | t | Gate |
|---|---|---|---|
| Both legs, net | −0.017% | **−0.16** | t ≥ 3.065: **failed** |
| Development 2009-2014 | +0.119% | 0.73 | > 0: passed |
| Validation 2015-2020 | **−0.153%** | −1.23 | > 0: **failed** |
| Costs doubled | −0.235% | −2.28 | > 0: **failed** |
| Short leg, the five days before | +0.004% (gross +0.104%) | 0.06 (gross 1.48) | both > 0: **failed** |
| Long leg, the five days after | −0.021% (gross +0.098%) | −0.30 (gross 1.38) | |

- The hit rate was 46.5%.
- By year (the sum of its events): 2009 +9.4% and 2013 +4.7%; 2016 −7.4% and 2019 −6.1%.
- The total was negative, so no year's share is defined, and the top-year gate fails.

**Found after the verdict, disclosed, and changing nothing.**

- The rule counts an auction as a 10-year note's when its original term is 10 years. On 2019-11-05 the Treasury sold
  a 3-year note as a reopening of an old 10-year note, and the rule took it as November 2019's event. The real 10-year
  auction the next day was then left out as overlapping.
- A second June 2019 record of a 10-year reopening (2019-06-21) was also left out as overlapping.
- So one event in 144 was a day early. Even a 1% swing in that one event moves the mean by under 0.01% and t by under
  0.1, so the verdict stands.

**What it means, and no more.**

- In IEF since 2009, prices still fell a little before the 10-year auctions and rose a little after. Gross, that was
  about 0.1% each side, at t about 1.4 each. That is far smaller than the paper's 1980-2008 cycle.
- A retail CFD's spread and markup cost about 0.22% per event, more than the whole cycle. Net, it lost.
- It paid in 2009-2014 and lost in 2015-2020.
