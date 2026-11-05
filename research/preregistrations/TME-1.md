# TME-1: the Treasury month-end effect (preregistration)

**Written, frozen and registered on 2026-11-05, before any TME-1 price was fetched, and before TSY-1's result was
read.**

The owner, 2026-11-05: "don't fixate on the AI trading; anything that makes us a profit; never stop".

| | |
|---|---|
| Frozen spec | `research/specs/TME-1.json` |
| Spec sha256 | `dd838eccb0a08b9de0fe99df9abd6bf62f4c2b607c1281364e93cee38b7132ce` |
| Code | `scripts/tme1.py` and `scripts/phd1.py` (its NYSE calendar), sha256 `e5d338b44617c45dabe9054f91b3bb10bc173bfbe667d5233432ec864f2373b1`. Every command refuses to run if either hash changes |
| Run | `.github/workflows/tme1-run.yml` on GitHub's runner, which can reach Yahoo (this environment cannot). It runs `fetch`, then `judge`, then `holdout` only if `judge` PASSED. It also prints the result and the registry line to its log, so a refused push cannot lose them |
| Threshold | t ≥ **3.078**. That is the Bonferroni value for 23 earlier tests plus this 1, and never below 3.0. The 23 are every test on the universes that read Treasury prices or yields: multi-asset-etf (12), multi-asset-long (10) and us-treasury-daily (TSY-1: 1). A trial on two of them is counted on each |

## Why this question

- **The finding.** Hartley & Schwarz (2019) found that coupon Treasuries earned positive, significant excess returns in
  the last few days of each month, and about nothing on other days, over 1990-2018. A summary of the paper puts the
  10-year note's at about 0.25% over the last three trading days.
- **The mechanism.** Insurers buy more Treasuries at month-end than on any other day. Funds that track bond indices
  extend their duration when the indices rebalance at month-end. The New York Fed finds month-end Treasury trading has
  grown since 2020.
- **The question.** Does holding the 7-10 year Treasury ETF (IEF) over each month's last three trading days pay, held
  the way a retail CFD holds it?

**Known before freezing.** Each of these is said now, so that it cannot be explained away later.

- **The paper was not read in full.** Its host is blocked here, and the figures above come from search summaries. The
  three-day window is the one the summary quotes. It was fixed before any price was seen and is not tuned.
- **A test on TLT since 2002 did not find it** (CXO Advisory, as summarized).
- **Costs take a large share.** The two sides and three to five nights of markup cost about 0.1%. That is close to half
  of the reported effect.
- **The judged period lies inside the paper's sample.** 2003-2018 is new data here: no test in this registry has read
  Treasury returns at month-end. But it is not new to the paper. A pass there would be a replication on a tradable
  fund. The holdout, 2019-2026, is after the paper's sample, and it decides.
- **TSY-1 reads the same fund.** It is counted in the threshold. TME-1 was frozen before TSY-1's result was read.

## The rule (fixed; nothing is tuned)

- **The calendar.** Each month's last four NYSE trading days, T−3 to T, are computed from the NYSE's rules and its
  known unscheduled closures (`scripts/phd1.py`, checked against the NYSE's published calendars in PHD-1). A month is
  no trade unless IEF has a close on each of them.
- **The trade.** Long IEF from the close of T−3 to the close of T: the month's last three trading days.
- **Costs.** 0.03% a side for spread and slippage. Each night pays the T-bill yield plus 2.5% a year. The yield is the
  one last published (`^IRX`, at most 7 days old), with zero and negative yields kept.
- **No trade.** A month whose financing is unknown is no trade.
- **The statistic.** The mean net return per month-end, with its t.
- **The control, reported only.** Every other run of three trading days in the same period, back to back and held the
  same way.

## Periods

| Role | Month-ends | Count |
|---|---|---|
| Development | 2003-01 → 2010-12 | 96 |
| Validation | 2011-01 → 2018-12 | 96 |
| Judged (significance) | 2003-01 → 2018-12 | 192 |
| Holdout | 2019-01 → 2026-09, after the paper's sample. The judge never reads it. It is opened once, only if TME-1 PASSED, as its own registered trial (TME-1-H) | 93 |

## Gates (all required)

| Gate | |
|---|---|
| t | t of the mean net return per month-end over the judged period ≥ 3.078 |
| development | mean net per month-end > 0 in 2003 to 2010 |
| validation | mean net per month-end > 0 in 2011 to 2018 |
| costs ×2 | mean net per month-end > 0 with the cost per side and the markup doubled |
| top year | no calendar year supplies more than 50% of the total |

**Holdout rule.** Over 2019-01 to 2026-09, both of these must hold. Then it is VALIDATED; otherwise it is REJECTED.

- mean net per month-end > 0, with one-sided t ≥ 1.645;
- mean net per month-end > 0 with the costs doubled.

**Reported, never gates.** The control's mean, the hit rate, each year, and every month left out.

## After the result

- **PASSED and VALIDATED.** If the broker quotes a 10-year Treasury contract or IEF, it is proposed to the owner as a
  paper strategy of its own (CLAUDE.md rule 14). That would be twelve trades a year. The risk engine sizes it, and it is
  followed forward on paper apart from every other record. Never real money.
- **Anything else.** It is reported as it is, and nothing changes.

## Power, declared

- **The bar.** 192 month-ends and t ≥ 3.078 need a mean of about 0.22 of one hold's own spread (3.078/√192). IEF moves about
  0.7% over three days at one standard deviation, so the bar is about 0.15% net per month-end.
- **The costs.** The hold pays about 0.1%. The gross effect must therefore be about 0.25% per month-end.
- **What that means.** That is about the size the summary reports for 1990-2018. TME-1 can pass only if the effect in
  IEF over 2003-2018 was as large as the paper's average. A smaller one would FAIL. Its failure would then say only that
  the effect is too small to pay a retail CFD, and that would be reported as it is.

## Result (run 2026-11-05 on GitHub's runner; `research/knowledge/TME-1.json`)

**FAILED, on t alone.** Every other gate passed. As registered, the holdout (2019-01 to 2026-09) stays unread, and
nothing changes.

**The data.** IEF had 6,108 daily closes from 2002-07-30 and ^IRX 8,498, both to 2026-11-05. All 192 judged
month-ends traded: IEF had a close on each of the computed last four trading days of every month.

**The figures, 2003-01 to 2018-12 (192 month-ends).** Each figure is per month-end, net.

| | Mean | t | Gate |
|---|---|---|---|
| Net | **+0.106%** | **2.24** | t ≥ 3.078: **failed** |
| Development 2003-2010 | +0.099% | 1.29 | > 0: passed |
| Validation 2011-2018 | +0.113% | 2.03 | > 0: passed |
| Costs doubled | +0.019% | 0.40 | > 0: passed |
| Top year | 2010, 22.8% of the total | | ≤ 50%: passed |
| Control: every other three-day hold (1,090) | −0.075% | −3.56 | reported only |

- The hit rate was 57.8%, and 12 of the 16 years were positive.

**Described after the verdict, on the judged data only.** These figures are descriptions, not tests, and they change
nothing.

- Before the spread and the markup, the month-ends earned +0.194% over the T-bill (t 4.07).
- The other three-day holds earned +0.015% on the same basis (t 0.71).

**What it means, and no more.**

- The month-end effect Hartley & Schwarz found was there in IEF over 2003-2018. Those years lie inside their sample,
  so this is a replication on a tradable fund, not new evidence.
- A retail CFD's spread and markup, about 0.09% per month-end, took about half of it. What was left, +0.106% a month
  (about 1.3% a year on money held three days a month), does not clear the bar that 23 earlier tests on this data set.
- With the costs doubled, it earned almost nothing.
- Whether it lasted after 2018 is the holdout's question. As registered, the holdout is not opened for a hypothesis
  that failed.
- A cheaper instrument, such as Treasury futures, would keep more of it. That is a new question, for data not yet
  seen. TME-1's holdout stays sealed against it.
- Like VOLM-1, this is a real-looking but weak effect that this bar cannot confirm. Nothing is proposed.
