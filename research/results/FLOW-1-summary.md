# FLOW-1 results: scheduled order flow at the Tokyo and London fixes

Preregistered in commit `c9eddd3` before any outcome was computed (research/preregistrations/FLOW-1.md).
Judged once on 2007-04..2016-12; threshold t >= 3.4305 (Bonferroni over the registry). **Verdict: FAILED.**
No hypothesis passed, so the sealed 2017+ holdout was **not** opened.

Units: basis points of the entry mid per observation, after the measured bid/ask spread, 0.1 pip slippage per fill and 0.7 pip commission per round trip.

| Hypothesis | n | Gross bps (t) | Cost bps | Net bps (t) | Dev net | Val net | Net, costs x2 | Failed gates |
|---|---|---|---|---|---|---|---|---|
| FLOW1-H1-GOTOBI-PRE | 696 | +0.71 (+0.90) | 2.04 | -1.33 (-1.68) | -1.04 | -1.59 | -3.37 | t, development, validation, years, costs_x2, top_year, specificity |
| FLOW1-H2-GOTOBI-POST | 696 | +2.46 (+2.27) | 1.81 | +0.65 (+0.60) | +0.60 | +0.69 | -1.16 | t, costs_x2, specificity |
| FLOW1-H3-FIX-MONTHEND | 117 | -0.17 (-0.23) | 2.27 | -2.44 (-3.13) | -4.13 | -0.84 | -4.71 | t, development, validation, years, costs_x2, top_year, leave_one_pair_out |
| FLOW1-H4-FIX-DAILY | 2419 | +0.06 (+0.31) | 2.26 | -2.20 (-11.59) | -2.57 | -1.84 | -4.46 | t, development, validation, years, costs_x2, top_year, leave_one_pair_out |

## Reading

- **London 4 p.m. fix (H3, H4): no effect at all.** The gross fade is +0.06 bps a day (t 0.3) and −0.17 bps at month-end. The strongly negative net t (−11.6) is the certainty of paying about 2.3 bps of costs on a zero-mean trade, not a reversed effect.
- **Tokyo fix, before (H1): tiny and not specific.** +0.71 bps gross (t 0.9). The same window on non-gotobi days nets -2.17 bps; the gotobi-vs-other Welch t is 0.933. 
- **Tokyo fix, after (H2): the only real-looking signal, and costs take it.** +2.46 bps gross (t 2.27) as the literature predicts. But 1.81 bps of costs leave +0.65 (t 0.6), it is negative with costs doubled, and it is not specific to gotobi days (Welch t 0.575).
- **Data finding.** The source mirror has no hour-00 UTC tick files for 12 of 13 instruments: 09:00–10:00 Tokyo, the hour of the fix itself, is missing. H1/H2 were defined around it. The finding is recorded in docs/FINAL_ENGINEERING_AUDIT.md.

Per the preregistration, none of these is re-run with other windows.
