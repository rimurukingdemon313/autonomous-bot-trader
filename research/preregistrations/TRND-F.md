# TRND-F: TRND-1's rule followed forward, judged once (preregistration)

**Written, frozen and registered on 2026-11-06, before any of its months exists.** It is judged once, on or after
2029-12-03.

| | |
|---|---|
| Frozen spec | `research/specs/TRND-F.json` |
| Spec sha256 | `181670d7a9be9d0fd30e6d96dcabd7e5b375cc86c67726309dae773815cc7b04` |
| Code | `scripts/trndf.py`, with TRND-1's own `scripts/trnd1.py` (its rule, unchanged). Their joint sha256 is `d59e42040767c703a83a7447d664a73e114ea5c04c7654c3780532319306dd32`. Every command refuses to run if either file or the spec changes |
| Run | Nothing runs now. On or after 2029-12-03, `fetch` then `judge` on GitHub's runner (Yahoo is blocked here). Both refuse to run earlier |
| Threshold | No t gate (below) |

## Why this question

- **TRND-1 passed** (`research/preregistrations/TRND-1.md`). Its judged years (1929-1989) and its holdout (2021-01 to
  2026-09) both existed when the rule was chosen, and the rule was published in 2007 from data that include the
  first. The holdout was also not untouched.
- **Months that do not exist yet** are the only evidence no one can have looked at. TRND-F fixes now how they will be
  read, so that no later result can be chosen after the fact. It is recorded whatever the owner decides about TRND-1
  as a paper strategy, and it changes nothing in the bot.

## The rule (TRND-1's, unchanged)

- **The instruments.** The US 500, US Tech 100, GER 40 and UK 100 (^GSPC, ^NDX, ^GDAXI, ^FTSE), at equal weight.
- **The decision.** At each month-end close, each index is held for the next month if the close is above the mean of
  its last 10 month-end closes, this one included. Otherwise it is not held for that month.
- **Costs.** 0.05% each switch in or out, no financing (swap-free) and no dividends (price indices).
- **No bridging.** A calendar month without a close is never bridged.

## The months

| Role | Months held |
|---|---|
| Judged | December 2026 → November 2029 (36) |
| Warm-up only | The closes from January 2026 feed the first decisions; no return before December 2026 is used |

## Gates (all required)

| Gate | |
|---|---|
| complete | all 36 months for all four indices |
| mean | mean net monthly return of the basket > 0 |
| costs ×2 | mean net monthly return > 0 with the switching cost doubled |
| smaller crash | a worst fall smaller than holding all four all the time |

**No t gate.** Thirty-six months cannot show significance, as its holdout's 69 could not. The check is whether the
validated rule still earns and still protects. A pass is not new proof of an edge, and TRND-1 is not one.

**Reported, never gates.** Holding all four (its mean and t), each index's growth against holding it, and each year.

## After the result

- **PASSED.** Reported as a forward confirmation of TRND-1. It changes nothing by itself.
- **FAILED.** Reported as it is. If TRND-1 is a paper strategy by then, the owner is told it failed forward, and it is
  stopped unless they decide otherwise.

## Known before freezing

- **The decision at the October 2026 close is not in it.** That close existed at registration, and so did part of
  November's return. The first judged month is December 2026, decided at November 2026's close.
- **Its power is that of its holdout.** It would catch a rule that has stopped earning or stopped protecting. It
  cannot measure whether the rule beats holding the market: TRND-1 did not, month by month, in either sample.
