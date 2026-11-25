# The owner's SOVEREIGN package, as received (2026-11-24)

The owner uploaded `Claude_Handoff_Top3_Strategies.md` in the session on 2026-11-24 (about 22:30 UTC) and asked for
its three strategies (SOVEREIGN-TITAN-MAX, SOVEREIGN-TITAN-7, SEC-TSMOM-4) to be implemented in this repository and
replayed on real daily bars. **Nothing here is edited.** The specification names no person; it is stored as sent.

| File | sha256 | |
|---|---|---|
| `Claude_Handoff_Top3_Strategies.md` | `7245616e279b9582245db08c5733c2b5172dedcb2833a09220932634bf9a131a` | as received |
| `sovereign_top3_suite.py` | `4cc68b2adba0c5359f23942240165537ca47334a18f949d8ca581950f81ae42b` | the specification's section 5, byte for byte |

`tests/unit/test_sovereign_data.py` checks that the module is the specification's own code block and that both
hashes are the ones above.

## Status

- **EXPERIMENTAL, NOT VALIDATED.** The figures in the specification (its section 3) are its author's own backtest. No
  preregistered test on unread data has judged any of the three rules, so none is eligible for DEMO or live
  trading, and none is sized above what the risk engine allows an unvalidated rule.
- **The specification's own caveat 1:** before 2025 its series are bars of about 12 to 15 trading days (about 100
  points per five or six years), not daily bars; only its last 252 rows are daily closes.
- **Short selling and leverage, stated plainly** (the owner's Islamic condition asks for it): all three rules sell
  short (SEC-TSMOM-4 and SOVEREIGN-TITAN-7 in every sector; SOVEREIGN-TITAN-MAX in oil and bitcoin always, and in
  equities and metals behind its 90-day guards), and their weights can sum to more than the equity. The weights the
  specification prints for 2026-11-20 are all short: QQQ, SLV, USO and IBIT.
- **The gold and silver seal:** GLD and SLV from 2017 are in the sealed market periods (`research/holdout.json`;
  `docs/ORIGINAL_EDGE_HUNT_2.md`, section 1). Before any replay reads them, the decision on that seal is
  recorded in `research/director/log.jsonl`.

The replay on real daily bars is `scripts/sovereign_redteam.py`; its data come from `scripts/sovereign_data.py`
(the `sovereign-data` branch).

**What the replay showed (2026-11-24):** `docs/SOVEREIGN.md` and `research/results/SOVEREIGN-redteam.md`. Its last
year and its printed weights reproduce; before 2025 its profits do not, on daily bars; over 2008-2026 its best rule
earns 2.3% a year at t 1.46, and its own live layer would have stopped it in March 2008. No paper desk is built.

**Tried on everything (2026-11-25):** `docs/SOVEREIGN.md` (its last section) and `research/results/SOVEREIGN-everything.md`. Every setting the specification names and the other markets the owner trades, descriptively: on the seven funds no rule reaches t 1.6; the package's drawdown brake holds the account at half size or less on 87% to 97% of days from 2008; and what profit the other markets add is bitcoin's and ether's trend, the family the lab's registered XTS-1 already failed. Still not validated; no paper desk.
