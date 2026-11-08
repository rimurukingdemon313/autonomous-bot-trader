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

**A larger monthly figure from one account means a larger size, and the limits end it.** These sizes have no stop:

| Size of one $200,000 account | Mean month | Median month | Worst month | Accounts the limits would have ended, 1990-2026 |
|---|---|---|---|---|
| FULL (1x) | $1,364 | $747 | -$31,280 | 3 |
| 1.5x | $2,045 | $1,121 | -$46,921 | 13 |
| 2.2x (the size for a $3,000 mean) | $3,000 | $1,644 | -$68,817 | 69, about two a year |

The owner, 2026-11-07, asked for at least $3,000 a month. Raising one account's size cannot give that within the
limits, so the target is met by the number of accounts, never by their size (below).

## What a trader would have been paid (descriptive, not a test)

`scripts/funded_lifecycle.py` (`research/results/FUNDED-lifecycle.json`) follows each account's whole life, from every
start month on the four index CFDs, 1990-2026. These are already-used data, and the assumptions are declared in the
script:
- a $200,000 challenge costs $1,100, refunded with the first payout;
- the two phases come first: +10%, then +5%;
- each month's whole profit is paid out at an 80% split;
- an account lost at the limits is replaced by a new challenge.

Several accounts on the same rule win and fail together, so a plan of N accounts is N times one account.

| Plan | Over | Median net to the trader | Mean | 10th to 90th percentile | Starts that lost money | Starts paid nothing | Accounts lost, each (mean) |
|---|---|---|---|---|---|---|---|
| 3 accounts at FULL | 1 year | $-3,300 | $7,231 | $-6,600 to $37,972 | 67% | 66% | 0.19 |
| 3 accounts at FULL | 2 years | $30,384 | $39,331 | $-6,600 to $99,691 | 32% | 32% | 0.46 |
| 3 accounts at FULL | 3 years | $57,911 | $74,459 | $-3,300 to $171,309 | 10% | 10% | 0.76 |
| 6 accounts at HALF, with its stop | 1 year | $-6,600 | $-5,997 | $-6,600 to $-6,600 | 98% | 98% | 0.01 |
| 6 accounts at HALF, with its stop | 2 years | $-6,600 | $3,579 | $-6,600 to $29,678 | 82% | 82% | 0.02 |
| 6 accounts at HALF, with its stop | 3 years | $-6,600 | $22,940 | $-6,600 to $97,151 | 58% | 58% | 0.03 |
| 1 account at FULL | 1 year | $-1,100 | $2,410 | $-2,200 to $12,657 | 67% | 66% | 0.19 |
| 1 account at FULL | 2 years | $10,128 | $13,110 | $-2,200 to $33,230 | 32% | 32% | 0.46 |
| 1 account at FULL | 3 years | $19,304 | $24,820 | $-1,100 to $57,103 | 10% | 10% | 0.76 |

- **Most of the first year pays nothing.** The two phases come first: at FULL, two starts in three had no payout yet
  after a year. Half of those paid within three years had their first payout by about 16 months.
- **Over three years, three FULL accounts** gave a median of about $58,000 (about $1,600 a month across the three
  years), and lost money in 10% of starts. Six FULL accounts gave a median of about $116,000 (about $3,200 a month).
  That is $1.2M of funded capital, more than one firm usually allows.
- **HALF is too slow for a funded account.** It rarely lost an account, but over three years it lost money in 58% of
  starts, because its challenges took too long to pass.
- **The first four or five months, at FULL:**

  | | After 4 months | After 5 months |
  |---|---|---|
  | Still in phase 1 | 81% | 72% |
  | Phase 1 passed | 15% | 23% |
  | FUNDED reached | 4% | 7% |
  | Any payout | 1% | 2% |
  | Account lost | 5% | 6% |

  On 2021-2026 alone, after five months, 83% were still in phase 1 and none was FUNDED. A trial of four or five
  months therefore cannot show this rule's payouts. It can only show the account moving toward its target. These
  figures are in `first_months_at_FULL` of the same results file.
- **Keeping profit in the account as a cushion paid less.** With $10,000 kept back, three FULL accounts' three-year
  median fell to about $37,000; with $20,000, to about $13,000. Paying out all of it each month did best.

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
- **The size, for the owner's target of at least $3,000 a month:** FULL size, $50,000 of each index the rule holds in
  each account, and six funded accounts.
  - **Six, not three.** An earlier note here said three FULL accounts would give about $3,300 a month after the split.
    That was the accounts' raw average P&L. It left out the months spent in the two phases, the payouts that reset
    each account, and the accounts lost and replaced.
  - **What the whole life of an account gave:** with all of that counted (the section above), three FULL accounts
    paid a median of about $1,600 a month across three years, and six about $3,200.
  - **Why FULL, not HALF:** in the replay FULL passed a challenge sooner (a median of 174 trading days against 464),
    and HALF lost money over three years in 58% of starts.
  - **The accounts move together.** A crash day that ends one ends them all.
  - **The firm's cap:** $1.2M of funded capital is more than one firm usually allows, so the accounts would sit at
    more than one firm.
  - **Payouts:** take the whole profit each month; keeping a cushion paid less.
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
- **The system trades it itself, on paper (from 2026-11-09; the owner, 2026-11-08: "the system trades by itself").**
  The trend desk (`docs/TREND_DESK.md`) runs this HALF track's rule, size and stop through the bot's own execution
  path: the risk engine, the hard gate and the paper broker. It runs on its own $200,000 paper account, with no
  person placing a trade. A funded account would need a broker connection, which this build does not have. Under the
  permanent DEMO rule (CLAUDE.md rule 1), the account is used only if the broker itself reports it as demo.
