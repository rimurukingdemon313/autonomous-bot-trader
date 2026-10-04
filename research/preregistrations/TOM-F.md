# TOM-F: two turn-of-the-month variants, registered for FORWARD data only

**Registered after TOM-D's diagnostics (`docs/TOM_INVESTIGATION_REPORT.md`), from which they come.**
Because they were noticed on data already used to select TOM, those data cannot test them. **No
historical result may be cited as evidence for or against them.** They are judged only on index
closes dated from 2026-10-05 onward.

| ID | Rule (`rc.tom`) | Why it is a hypothesis, not a result |
|---|---|---|
| TOM-F0 (control) | k_pre 1, k_post 3: E1 TOM unchanged | The reference |
| TOM-F1 | k_pre 2, k_post 3: enter one trading day earlier | Best of TOM-D's five calendar variants on both A (net t 2.48) and B (t 2.43). It was chosen from 5, so the selection is part of its history |
| TOM-F2 | k_pre 0, k_post 1: hold the first trading day of the month only | Post-hoc, from TOM-D's day profile: day +1 is the only window day with a large excess over the drift since 2009 (A +11 bps, B +13 bps a day) |

**Unchanged for all three:**

- universes A and B (26 index CFDs), 1/N notional each, no leverage;
- RC-EQ's retail costs (`retail.py`, frozen);
- the rule code itself (`rc.tom`, frozen in RC-EQ).

**Judged when 120 forward months exist**, as the mean monthly net:

1. t ≥ 2.13 (one-sided Bonferroni over 3);
2. it beats a drift control, the same number of exposure days on random non-window days, by a
   mean > 0.

**Power, stated now.** At the post-2009 Sharpe of about 0.2, 120 months gives t ≈ 0.6. These
hypotheses are recorded so they cannot be quietly promoted later. They are **not** a plan to wait
for a result.
