# CONF-1: on H1, would the agreements under the confidence floor have paid? (preregistration)

**Written, frozen and committed on 2026-11-03, before any H1 agreement had an outcome.** The first H1 agreements
(decided from 2 November 01:00 UTC) cannot resolve before 4 November 01:00 UTC: each is held up to 48 hours and
followed for its whole window. The owner, 2026-11-03: "do everything, I trust you".

| | |
|---|---|
| Frozen spec | `research/specs/CONF-1.json` |
| Spec sha256 | `34b07fa2acca4c6b6bbd56214dcf05ac48c721d20f59a204d3b07ac3ebd6dcb4` |
| Code | `scripts/conf1.py`, sha256 `b6e4780b09adc375965fa7453239c50c42524348bfa19dee478461f50b92fa68` (it refuses to run if either hash changes) |
| Data | the shift database (`aitrader.db.gz`, branch `paper-forward-data`) published on or after each look's date |
| Units | every H1 agreement under the floor (`DUAL_AI_LOW_CONFIDENCE`) decided in a look's window, its outcome recorded by the look's date, once |

## Why this question

The desk trades an agreement only when both traders state 65 or more (dual-ai 1.12.0, the owner's floor). On H1
its seat holders state their confidence out of habit. In the first two H1 days:

- Trader 1's model (`nemotron-3.5-super-vl`) stated 65 or more in 1 of its last 100 answers. It said 55 to 57 most
  of the time. On M15 it had stated 65 or more in about a third of its answers.
- Trader 2's model (`dots-3-note`) most often said exactly 65.
- So the floor refused 141 agreements and let 5 through. The 5 came from other models in Trader 1's seat.

The floor is choosing which model sat, not which setup to take.

The test registered on 2 November (`docs/DUAL_AI.md`, "a confidence judged against its own model's habit") cannot
be judged with these models. These counts are blind: confidences and models only, no outcome read.

- Of 136 H1 agreements whose two models had 30 or more earlier answers, **none** had both traders in their own
  model's top third.
- With the history read on H1 alone, also none of 131. The top half held 10.

That test is retired without a verdict: it is not failed and not adopted. The question that can be answered is the
simple one: did the agreements the floor refused pay?

## The rule and the looks

There is one rule (the units, followed forward as the trades they would have been) and two looks:

| Look | Decided | Judged on | Passes if |
|---|---|---|---|
| LEARNING | 2026-11-02 to 2026-11-16 UTC (ISO weeks 45, 46) | 2026-11-20 00:00 UTC | 100+ agreements, mean net R of +0.10 or more with t of 2.0 or more, **and** t of 2.0 or more over the days' own means: QUALIFIED |
| EVALUATION | 2026-11-16 to 2026-11-23 UTC (ISO week 47) | 2026-11-27 00:00 UTC | only after QUALIFIED: 50+ agreements, mean net R above 0 with t of 2.0 or more, and the days' mean above 0: CONFIRMED |

- Fewer agreements than a look needs is **INCONCLUSIVE**. Nothing changes.
- LEARNING not qualified is **FAILED**. EVALUATION is then not judged.
- An outcome counts only if the ledger recorded it by the look's date (its row's `ts`), so a later database gives
  the same answer.
- **Why the days.** The agreements of one day move together: one USD day is several pairs on the same side at once.
  A t over hundreds of agreements would count that day many times.

## After the result

- **CONFIRMED.** The floor stops refusing H1 agreements, in a new dual-ai version, the owner told first. The lesson
  check, the senior trader, the risk engine and the always-sure seat rule stay exactly as they are. The agreements
  stay followed forward.
- **Anything else.** The floor stays. The result is reported as it is.

## Reported, never judged

- The agreements the floor let through (`DUAL_AI`) in the same windows.
- The win rate and the profit factor.
- How many were decided but not resolved by the date.

## What was seen before freezing

- **No outcome of any H1 agreement.** None existed.
- The traders' stated confidences and models on H1, which give the blind counts above.
- The M15 record: DESK-1, and the analysis of 2 November in which neither the raw nor the relative confidence
  predicted a result.

## Known limits

- **The units stop at the floor.** The lesson check, the senior trader, and the risk engine's sizing and limits
  never saw them. Each of those can only refuse, so a confirmed result is an upper bound on what trading them would
  add.
- **Power.** About 50 to 80 agreements a day fall under the floor, so each look holds hundreds. Still, a t over 10
  days (LEARNING) or 5 days (EVALUATION) is weak. A real but small edge may well FAIL here, and that would be
  reported, not explained away.
- **Models.** The seats' models can change during the windows: a seat passes on when its holder is gone, absent
  or excluded. The units record their models, so a change is visible. It does not change the rule.
