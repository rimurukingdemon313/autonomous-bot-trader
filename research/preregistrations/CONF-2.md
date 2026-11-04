# CONF-2: does the strongest model's judgement pick the H1 agreements that win? (preregistration)

**Written, frozen and committed on 2026-11-04, before the senior trader had judged any agreement in shadow.** The
owner, 2026-11-04: "change everything if you must; the most important thing is a profit; don't fool me with promises;
the budget can be $100".

| | |
|---|---|
| Frozen spec | `research/specs/CONF-2.json` |
| Spec sha256 | `71fd5c61eca84b56fa87c4f7b94cbb35278b8d6fa7ee6f40490fba6e99f03f6d` |
| Code | `scripts/conf2.py`, sha256 `340af4fd003d1bcfe5e2b23823702389c5edebe1b470cfc8fd37584d56ce40c1` (it refuses to run if either hash changes) |
| Data | the shift database (`aitrader.db.gz`, branch `paper-forward-data`) published on or after each look's date |
| Units | every H1 agreement below the floor (`DUAL_AI_LOW_CONFIDENCE`) decided in a look's window, that the senior judged in shadow with a usable answer, its outcome recorded by the look's date, once |

## Why this question

On H1 the two traders state their confidence out of habit, so the floor of 65 refuses nearly every agreement
(CONF-1). The question that matters is whether anything at the desk can tell the agreements that win from the ones
that lose.

The strongest model on the catalog sits at the desk as the senior trader: `anthropic/claude-opus-5.5`, intelligence
index 58.4. Until now it was asked only on the rare agreement at the floor, and it vetoed the first two
(2026-11-04: USDCHF and GBPUSD). Since dual-ai 1.20.0 it also judges, **in shadow only**, every agreement below the
floor:

- It reviews the trade the agreement would have been, exactly as it would be placed.
- It sees everything the desk knows: the chart, the data, both analyses, the journal, the time machine and the
  playbook.
- Its system prompt tells it the desk will not take the trade, whatever it answers, and asks it to judge as if it
  would.
- Its verdict is recorded before the outcome (`senior_shadow`). The decision stays NO_TRADE: the verdict can never
  cause, change or size a trade.

## The groups

| Group | |
|---|---|
| APPROVED | verdict APPROVE with confidence of 50 or more (the live rule's even odds) |
| REST | verdict VETO, or APPROVE below 50 |

An agreement without a usable review is not a unit: no answer, a malformed one, or not asked because today's budget
was kept for real reviews. These are counted and reported.

## The looks

| Look | Decided | Judged on | Passes if |
|---|---|---|---|
| LEARNING | 2026-11-05 to 2026-11-16 UTC | 2026-11-20 00:00 UTC | 30+ approved and 30+ rest; the approved trades' mean net R +0.10 or more, with t of 2.0 or more over trades **and** over the days' own means; and they beat the rest by 0.20 R or more with Welch t of 2.0 or more: QUALIFIED |
| EVALUATION | 2026-11-16 to 2026-11-23 UTC | 2026-11-27 00:00 UTC | only after QUALIFIED: 15+ approved and 15+ rest; the approved trades' mean net R above 0 with t of 2.0 or more; the days' mean above 0; and they beat the rest: CONFIRMED |

- A group short of its minimum is **INCONCLUSIVE**. Nothing changes.
- LEARNING not qualified is **FAILED**. EVALUATION is then not judged.
- An outcome counts only if the ledger recorded it by the look's date (its row's `ts`).
- **Both conditions are needed.** Approved trades that pay but do not beat the rest mean the market paid, not the
  judgement. Approved trades that beat losing vetoes but lose themselves pay nothing.

## After the result

- **CONFIRMED.** On H1 the senior's approval replaces the confidence floor for the agreements it judges, in a new
  dual-ai version, the owner told first. The lesson check, the risk engine and the always-sure seat rule stay as
  they are. Its vetoes stay followed forward.
- **Anything else.** Nothing changes. The result is reported as it is.

## Cost, declared

- A review cost about $0.10 on 2026-11-04 (two for $0.21). About 60 agreements a day comes to about $6.30 a day.
- The funded period (paid-trial 1.4.0, `senior-2026-11-04`) allows $95 in all and $7.50 a day, inside the owner's
  $100.
- A review in shadow is paid for only while today's spend leaves room for two more reviews of real trade candidates
  (`room_for_shadow_review`). A day that runs out of room loses shadow reviews, never a real one.
- What the key holds bounds every call. If it runs out (402), the period ends and the desk takes no trade that a
  senior must review.

## What was seen before freezing

- **No shadow review.** None existed.
- The senior's two reviews of real trade candidates (both vetoes; their outcomes not yet known).
- CONF-1's blind counts, the desk's whole forward record (no edge on M15; on H1, one morning of resolved agreements
  under the floor), and the project's historical research (no edge after costs since 2008).

## Known limits

- **Power.** The senior may approve few agreements. If it approves one in five, LEARNING holds about 80. A real but
  small skill may well FAIL here, and that would be reported as it is.
- **Units overlap with CONF-1.** Every unit here is also one of CONF-1's. The two answer different questions: CONF-1
  asks whether the agreements under the floor pay at all, and CONF-2 asks whether the senior picks the ones that do.
- **What a CONFIRMED result means.** Each approved trade still meets the lesson check and the risk engine, which can
  only refuse. So the units are an upper bound on what trading them would add.
- **The model can change.** If OpenRouter stops serving `anthropic/claude-opus-5.5` at its declared price, the
  senior is not asked. The units record the model.
