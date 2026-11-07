# FUNDED-P: a funded-account paper track of TRND-1

**PAPER ONLY · NOT REAL MONEY.** No broker, no account, no order and no key. Public daily closes and fixed rules,
recomputed from the same start (2026-11-09) after every weekday's closes, on GitHub's runner. The report is on the
`funded-paper-data` branch (`REPORT.md`, with an Arabic summary, and `state.json`).

## Why it exists

- **The owner, 2026-11-07.** The $200K account is a funded (prop-firm) account. Everything is on paper first ("we want
  to make sure"), and only then a real account.
- **TRND-1 is the only rule here that passed its test and its holdout** (`research/preregistrations/TRND-1.md`). This
  track measures, forward, how that rule fares against a funded account's limits.
- **It is not an edge over the market.** Month by month the rule earned slightly less than holding the index. What it
  had was about half the worst fall.

## The rules (`scripts/funded_paper.py`)

| | |
|---|---|
| The rule | TRND-1's, unchanged: hold an index for a month if the last month-end close before it is above the mean of the ten month-end closes before it; never short. A decision that cannot be computed is flat |
| Instruments | US 500, US Tech 100, GER 40, UK 100 (^GSPC, ^NDX, ^GDAXI, ^FTSE) |
| Tracks | Two $200,000 accounts. HALF: $25,000 in each index the rule holds. FULL: $50,000 in each |
| Costs | 0.05% of the position for each switch; no swap (an Islamic account); no dividends |
| Failure | A day losing $10,000 (5%), or equity at or below $180,000 (10%). The track stops |
| Phases | +10% passes phase 1. Phase 2 is a fresh $200,000 with a +5% target. Then FUNDED: no target, same limits |
| Four trading days | A phase passes no earlier than its 4th day. Each phase's first 4 days carry one minimal same-day trade at $5: what a trader does to meet FTMO's minimum, since the rule trades a few times a year |
| Data | A close counts 30 minutes after its exchange closes. If the closes cannot be read, nothing is published |

## What the history says (descriptive, not a test)

`scripts/trnd1_funded_sim.py` replays this same engine from the first trading day of every month on the data TRND-1
already judged (`research/results/TRND-1-funded.json`). This was computed after TRND-1's verdict, and it changes no
verdict.

| Data | Track | Starts | Phase 1 passed | Failed | Unresolved | Reached FUNDED | Median trading days to pass phase 1 |
|---|---|---|---|---|---|---|---|
| S&P 500, 1929-1989 | HALF | 732 | 627 (86%) | 95 (13%) | 10 | 568 (78%) | 438 (about 1 year 9 months) |
| S&P 500, 1929-1989 | FULL | 732 | 539 (74%) | 191 (26%) | 2 | 406 (55%) | 174 (about 8 months) |
| Four index CFDs, 2021-2026 | HALF | 69 | 47 (68%) | 0 | 22 (the data ended) | 40 | 389 |
| Four index CFDs, 2021-2026 | FULL | 69 | 55 (80%) | 2 (3%) | 12 (the data ended) | 48 | 176 |

- **One crash day can end the account at either size.** Each run continues until its data end, through phase 2 and
  FUNDED. The fall of about 20% on 1987-10-19 ended 547 of the 732 HALF runs, in whatever phase each was then.
  On the S&P 500 the whole exposure is one index, so HALF holds $100,000 of it, and a 20% day is a $20,000 day.
- **Other failures were spread out.** HALF's other failures came in 1929-1934, 1939-1941, 1948, 1960 and 1979-1980.
  FULL's came in most decades. In 2021-2026, FULL failed in December 2022 (4 runs) and on 2025-04-07 (3), each at
  the maximum loss. HALF never failed.
- **A swap breaks it.** The same replay with an illustrative 6.5% yearly swap on the position, as a non-Islamic
  account charges:

  | Data | Track | Phase 1 passed, swap-free | Phase 1 passed, with the swap |
  |---|---|---|---|
  | S&P 500, 1929-1989 | HALF | 86% | 56% |
  | S&P 500, 1929-1989 | FULL | 74% | 59% |
  | Four index CFDs, 2021-2026 | HALF | 47 of 69 starts, 40 reached FUNDED | 31, and none reached FUNDED |

  The live tracks are swap-free.

## What it does not model

- **The firm's own rules.** Weekend holding, news trading and inactivity can each forbid or end a months-long hold:
  some firms allow holding over the weekend only on a "swing" account, and some close an account with no trade for 30
  days. It also assumes the account is swap-free.
- **Falls inside the day.** It reads closes only, so an intraday fall that recovers by the close is not seen. The
  daily loss is measured close to close, not from midnight in Prague.
- **What a payout would be.** In the FUNDED phase, the firm's profit split is not computed.

It is not a promise. A pass on paper would say the rule behaved as it did in history; the next crash can be the one
that fails it.
