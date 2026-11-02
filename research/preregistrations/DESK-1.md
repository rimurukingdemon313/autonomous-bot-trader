# DESK-1: would a rule fixed at the entry have made the desk's agreements pay? (preregistration)

**Written, frozen and committed before any DESK-1 outcome was computed.** The owner, 2026-11-02: "make it
profitable; try everything, test everything". This tests, honestly, the simplest rules the desk's own record
suggests, and adopts nothing that does not hold where it was not chosen.

| | |
|---|---|
| Frozen spec | `research/specs/DESK-1.json` |
| Spec sha256 | `65b1c3e2c4f2a2297296d44101777e441c51753564f8f0c095437270723fc1a9` |
| Code | `scripts/desk1.py`, sha256 `a78595fe984d65c0899924de9ebc0f735ee50a5111c52b1723cd8f3dd15fa5c5` (it refuses to run if either hash changes) |
| Data | the forward ledger of the shift that ended 2026-11-02 10:33 UTC: branch `paper-forward-data` at `7400c72`, `aitrader.db.gz` (sha256 `ab94c198…bc033`), unzipped `aitrader.db` (sha256 `bd186d91…16051`) |
| Units | every `DUAL_AI` agreement as proposed (taken, or refused by the risk engine), RESOLVED, once: 375 in LEARNING weeks, 109 in EVALUATION weeks, all on M15 |

## Why these rules

Each comes from what the LEARNING record already showed:

- **A nearer take-profit.** The first winners all reached +1.2 R or more, and two gave much of it back before their
  time exit. The losers went wrong at once. The desk won 42% where it needed 50%.
- **Skipping costly trades.** Costs were the loss on M15: +0.06 R a trade before costs, 0.19 R in them.
- **Skipping the London/New York overlap.** It lost -0.43 R (54) in the analysis of 2 November.

A filter by side (BUYs lost in October) is left out on purpose. It would be a bet on one month's trend, not a
structure (CLAUDE.md rule 12).

## The rules tested (all five, all reported)

| Candidate | Rule |
|---|---|
| TP-0.75, TP-1.0, TP-1.25 | take profit at 0.75, 1 or 1.25 R from the fill, or at the trader's own target when that is nearer |
| SKIP-COST-0.20 | no trade when the planned round trip, (spread + 2 x slippage + commission) / risk, exceeds 0.20 R |
| SKIP-OVERLAP | no trade in the London/New York overlap |

**How a take-profit is counted** (from the stored best point and its time; exact, and conservative where it cannot be):

- A trade that reached its own target beyond k took k first.
- A trade closed by its time exit took k if its best point reached k.
- A stopped trade took k only if its best point reached k in a bar before the one that stopped it. On the stopping
  bar itself the order of its high and low is unknown, so it stays a stop.
- A take-profit exit pays the commission and no exit slippage, as the forward walk's target exits do.

A skipped trade is no trade: 0 R.

## Selection, on LEARNING only

- **Measure.** For each agreement, d = the candidate's net R minus the agreement's own net R, with paired t.
- **Qualify.** Mean d of at least 0.05 R, with t of 2.0 or more.
- **Selected.** The qualifier with the largest mean d.
- **If none qualifies,** DESK-1 is FAILED and EVALUATION is not judged.

## Judgement, on EVALUATION, the selected rule only

- **CONFIRMED** if its mean d > 0 with paired t of 2.0 or more.
- **PROFITABLE** if, in addition, its own net R over the trades it takes is > 0 with t of 2.0 or more.

## After the result

- **FAILED or NOT CONFIRMED.** Nothing in the bot changes. The result is reported as it is.
- **CONFIRMED or PROFITABLE.** The rule is followed forward on the H1 desk as a shadow (measured, never traded)
  before it can become one. These agreements were all on M15, with nearer stops than H1's, so a rule that held there
  must hold on H1 too.

## What was seen of this data before freezing

- **LEARNING:** the analysis of 2 November (the overlap, costs, BUYs) and the first winners' best points. That is
  what suggested these rules, as LEARNING is for.
- **EVALUATION:** only its split by the model in each seat, reported in docs/DUAL_AI.md (the paid week, 26-30
  October). No rule here was computed on it.
- **Power:** 109 agreements are few. A real but small improvement may well fail to reach t 2.0 there, and that would
  be reported as NOT CONFIRMED, not explained away.
