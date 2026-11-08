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
| One-day stop (HALF only, from funded-paper-1.1.0) | An index that closes 6% or more below its previous close is out, booked at -8% (2 points of slippage, since closes cannot show the fill), and flat until the next month's decision. A crash day then costs HALF about $8,000, inside the $10,000 limit. FULL has none: its limit is 5% of its position, which only a stop near 3% could keep, and that would be hit every few months |
| Costs | 0.05% of the position for each switch; no swap (an Islamic account); no dividends |
| Failure | A day losing $10,000 (5%), or equity at or below $180,000 (10%). The track stops |
| Phases | +10% passes phase 1. Phase 2 is a fresh $200,000 with a +5% target. Then FUNDED: no target, same limits |
| Four trading days | A phase passes no earlier than its 4th day. Each phase's first 4 days carry one minimal same-day trade at $5: what a trader does to meet FTMO's minimum, since the rule trades a few times a year |
| Data | A close counts 30 minutes after its exchange closes. If the closes cannot be read, nothing is published |

## What the history says (descriptive, not a test)

`scripts/trnd1_funded_sim.py` replays this same engine from the first trading day of every month on the data TRND-1
already judged (`research/results/TRND-1-funded.json`). This was computed after TRND-1's verdict, and it changes no
verdict.

| Data | Track | Starts | Phase 1 passed | Failed | Unresolved | Reached FUNDED | Median trading days to pass phase 1 | Alive when the data end |
|---|---|---|---|---|---|---|---|---|
| S&P 500, 1929-1989 | HALF, with its stop | 732 | 635 (87%) | 81 (11%) | 16 | 571 (78%) | 464 (about 1 year 10 months) | 548 (75%) |
| S&P 500, 1929-1989 | HALF without the stop | 732 | 627 (86%) | 95 (13%) | 10 | 568 (78%) | 438 | 26 (4%) |
| S&P 500, 1929-1989 | FULL | 732 | 539 (74%) | 191 (26%) | 2 | 406 (55%) | 174 (about 8 months) | 2 |
| Four index CFDs, 2021-2026 | HALF, with its stop | 69 | 47 (68%) | 0 | 22 (the data ended) | 40 | 389 | 69 |
| Four index CFDs, 2021-2026 | FULL | 69 | 55 (80%) | 2 (3%) | 12 (the data ended) | 48 | 176 | 62 |

- **Without a stop, one crash day ends the account at either size.** Each run continues until its data end, through
  phase 2 and FUNDED.
  - The fall of about 20% on 1987-10-19 ended 547 of the 732 HALF runs that had no stop, in whatever phase each was
    then.
  - On the S&P 500 the whole exposure is one index, so HALF holds $100,000 of it, and a 20% day is a $20,000 day.
- **With the one-day stop, 10 ended in 1987 and 9 in 1988, and 548 runs were still alive at the end of 1989.** The
  stop changed the pass rate little (87% against 86%). The median run hit it twice in its life. This is why the stop
  was added, on 2026-11-07, before the record's first day. Its level was set from the daily limit's arithmetic, not
  chosen from this replay, which only shows its effect.
- **Other failures were spread out.** HALF's other failures came in 1929-1934, 1939-1942, 1948, 1960 and 1979-1980.
  FULL's came in most decades. In 2021-2026, FULL failed in December 2022 (4 runs) and on 2025-04-07 (3), each at
  the maximum loss. HALF never failed.
- **A swap breaks it.** The same replay with an illustrative 6.5% yearly swap on the position, as a non-Islamic
  account charges:

  | Data | Track | Phase 1 passed, swap-free | Phase 1 passed, with the swap |
  |---|---|---|---|
  | S&P 500, 1929-1989 | HALF, with its stop | 87% | 56% |
  | S&P 500, 1929-1989 | FULL | 74% | 59% |
  | Four index CFDs, 2021-2026 | HALF | 47 of 69 starts, 40 reached FUNDED | 31, and none reached FUNDED |

  The live tracks are swap-free.

## Month by month on a $200,000 funded account, 1990-2026 (descriptive, not a test)

`scripts/trnd1_funded_monthly.py` (`research/results/TRND-1-funded-monthly.json`) runs the same rule, costs and stop
from 1990-01 to 2026-10. The account is treated as already funded: no phases and no target. RC-EQ judged 1990-2020
with the same rule, and TRND-1-H judged 2021-2026, so these are already-used data. The figures are in dollars,
before any profit split.

| | HALF, with its stop | FULL |
|---|---|---|
| Mean month | $650 | $1,364 |
| Median month | $374 | $747 |
| Months positive | 57% | 57% |
| Best month | +$12,518 | +$25,036 |
| Worst month | -$15,501 | -$31,280 |
| Mean year | $7,763 | $16,290 |
| Worst year | -$18,660 (1990) | -$37,321 (1990) |
| Best year | +$31,240 (1999) | +$62,481 (1999) |
| Trades | 254 in 37 years | 244 |
| Accounts the limits would have ended | 1 (1990-08-21) | 3 (1990-08-03, 1990-08-21, 2000-04-14) |
| Mean month by decade | $955, $502, $422, $754 | $1,986, $1,053, $943, $1,523 |

These are the rule's real figures, and they are modest. Many trades were not found to pay: every program here that
traded often lost after its costs (`research/QUEUE.md`).

## What it does not model

- **The firm's own rules.** Weekend holding, news trading and inactivity can each forbid or end a months-long hold:
  some firms allow holding over the weekend only on a "swing" account, and some close an account with no trade for 30
  days. It also assumes the account is swap-free.
- **Falls inside the day.** It reads closes only, so an intraday fall that recovers by the close is not seen. The
  daily loss is measured close to close, not from midnight in Prague. The one-day stop is judged on closes too: a real
  stop can be hit inside a day that closes above it, and a gap through it fills worse than the 2 points assumed.
- **What a payout would be.** In the FUNDED phase, the firm's profit split is not computed.

It is not a promise. A pass on paper would say the rule behaved as it did in history; the next crash can be the one
that fails it.

## If it is used on a funded account later (decided 2026-11-07)

The owner, 2026-11-07: "everything is allowed; don't ask me; you are the brain". These are the choices made for that
day, so that it needs no new decision. None of them is a promise.

- **The account is chosen to fit the rule.** It must be swap-free (Islamic), and it must allow positions held for
  months, over weekends and through news; some firms call this a "swing" account. Index CFDs on the US 500,
  US Tech 100, GER 40 and UK 100 must be quoted. An account without these is not used for this rule.
- **The size is HALF:** $25,000 of each index the rule holds, $100,000 at most in all. In the replay HALF failed least,
  and it never failed in 2021-2026. FULL stays on paper only, as the comparison.
- **The month-end decision:** on the month's last trading day, a few minutes before each exchange's close.
  - **When:** the US 500 and US Tech 100 at about 15:55 New York, the GER 40 at about 17:25 Berlin, the UK 100 at about
    16:25 London.
  - **The rule:** hold the index if its price then is above the mean of the ten month-end closes, the current month's
    included; otherwise close it.
  - **The approximation:** acting minutes before the close, instead of at it, is declared. In RC-EQ, acting a full day
    later cost the same rule about 0.2% a year.
- **A phase's first days:** a minimal trade on each of its first four trading days, to meet the four-day minimum.
- **Inactivity:** where the firm closes inactive accounts, a minimal trade each month.
- **The one-day stop:** for each index held, a stop order 6% below the previous day's close, moved each evening after
  the close. After it is hit, the index is flat until the next month-end decision.
- **Nothing added after a loss.** No martingale, no doubling, no "winning it back" (CLAUDE.md rule 2).
- **The bot does not trade it.** The bot is DEMO-only by its own permanent rule (CLAUDE.md rule 1), and nothing here
  changes that. The rule needs one decision a month, which this report gives, so a person can follow it by hand.
