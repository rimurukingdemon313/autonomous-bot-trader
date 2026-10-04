# RC-EQ2: replicate RC-EQ's PROMISING candidates on universe B; Halloween on universe A (preregistration)

**Written, frozen and committed after RC-EQ's result and before any universe-B price or any
Halloween outcome was computed.**

| | |
|---|---|
| Frozen spec | `research/specs/RC-EQ2.json` |
| Spec sha256 | `e786d11852f8ee5b55c8b380a9db33a398de7c5756af46365d94267b4229dcb6` |
| Code | `aitrader/research/discovery/rc2.py`, `scripts/rc_eq2.py`, plus RC-EQ's frozen code (`retail.py`, `rc.py`, `scripts/rc_eq.py`), all hashed in the spec. The runner refuses if RC-EQ's code hash changed |
| Run | `.github/workflows/rc-eq2-run.yml`: `fetch` (A again), `judge` (E8 on A), `replicate` (opens B once) |

## Why this study exists, and the one declared change of plan

RC-EQ FAILED: no hypothesis reached t ≥ 3.0 on universe A (`research/knowledge/RC-EQ.json`). Two
were classified PROMISING, failing only that significance gate:

| | Net, annual | t | Sharpe | Before the broker (t) | 1990–2005 / 2006–2020 (annual) |
|---|---|---|---|---|---|
| E1 TOM | +2.59% | 2.24 | 0.40 | 3.12 | +4.49% / +0.57% |
| E7 ENSEMBLE | +2.00% | 2.02 | 0.36 | 3.35 | +2.47% / +1.50% |

**The change of plan, declared.**

- RC-EQ's preregistration said PROMISING hypotheses are never sent to RC-EQ's holdout, and the
  universe-B seal (`research/holdout-rc-eq.json`) names trial RC-EQ-H as its user.
- RC-EQ-H was never registered, because nothing passed. **Universe B has never been fetched.**
- B is the only untouched equity-index data left. The brief this program answers says that when a
  candidate has no clean validation data, a genuinely new universe must be used. Universe B is
  that.
- So this new, separately registered study spends B on an **independent replication** of the two
  PROMISING candidates.
- **The cost of this choice:** no clean equity data remains after it.
- **What a pass can and cannot mean.** E1 and E7 failed their own significance gate on A, so a pass
  on B makes them **PROMISING_REPLICATED**, never VALIDATED. That is the strongest label the
  evidence could support, and the most it can earn is controlled PAPER/DEMO testing.

## E8 HALLOWEEN (new; judged on universe A, 1990–2020, with RC-EQ's nine gates unchanged)

**Rule.** Long each index (1/10 of equity) from the last close of October to the last close of
April, flat May–October. It reads the calendar only (Bouman & Jacobsen 2002, "Sell in May and go
away"; documented in 37 markets).

- **Why it was not in RC-EQ:** an omission. It is a calendar flow like E1, with the lowest
  turnover of any rule here (one round trip a year per index).
- **What is already known that bears on it, declared.** RC-EQ's long-biased rules earned about
  2–6% a year gross on A, and its regime split showed long exposure earning in bull markets. E8 is
  also long-biased. Its gates are not relaxed, and its threshold counts RC-EQ's seven tests.
- **Grid:** enter at the end of {September, October, November} × exit at the end of
  {March, April, May}.

**Threshold.** t ≥ max(3.0, the registry's Bonferroni value), recorded in the spec. E8 goes to B
only if it passes all nine gates.

## Universe B (opened once by trial RC-EQ2-H)

The 16 indices listed in RC-EQ.md: 1990-01 → 2026-09, fetched for the first time in this run.

**Candidates:** E1 TOM and E7 ENSEMBLE, exactly as frozen in RC-EQ (spec `bbe20ccd…`), with
1/16 per index; plus E8 if it passes A.

**Gates (all required), with k the number of candidates:**

1. t of the mean monthly net over B ≥ z(1 − 0.05/k), one-sided Bonferroni (1.96 for k = 2,
   2.13 for k = 3);
2. mean net > 0 before 2021;
3. mean net > 0 from 2021;
4. mean net > 0 from 2009 (the modern era, where A showed decay);
5. mean net > 0 with every cost doubled;
6. mean net > 0 with every fill one close later.

**Classes.**

- E1 and E7: pass → PROMISING_REPLICATED, else REJECTED.
- E8: A and B pass → VALIDATED, else REJECTED.

B shares calendar time with markets already studied: it is an instrument replication, not a time
holdout. Its 2021+ part shares calendar time with the period DIV-2-H opened for trend following,
on different instruments and a different hypothesis. It is reported separately.

## What a PROMISING_REPLICATED result would and would not justify

- **It would justify** controlled PAPER/DEMO forward testing of index CFDs, labelled EXPERIMENTAL
  by the forward ledger. That needs index instruments and a calendar path through the risk engine,
  built only after this evidence.
- **It would not justify** LIVE trading, any increase in risk, or a claim of future profit. A's
  2006–2020 decay is on record and is not erased by B.
