# The owner's TRINITY-OMEGA package, as received (2026-11-21)

The owner uploaded `trinity_omega_complete_package.zip` in the session on 2026-11-21 and asked for its
specification to be implemented in this repository. Its three files are kept here so every claim about it can be
checked against what was actually sent. **Nothing here is edited**, with one declared exception below.

| File | sha256 | |
|---|---|---|
| `trinity_omega_suite.py` | `de0d1596b0cf69ba92fd93a610607ec1b18e1d17bca4430c87269b0390eebd1b` | as received |
| `trinity_master_trades_20yr.csv` | `f138ba35ee25856a40d2e03d4e781cc26d2f40e85c101eb632ca13f029afb32e` | as received |
| `CLAUDE_HANDOFF_SPEC.md` | `3b4d7f14645aed4c762d39c4b733989d8ef223b9056b310f8addc81205fc0ef9` | the original; **not stored** |
| `CLAUDE_HANDOFF_SPEC.redacted.md` | `774f4d5d8856a7139ee55bb5fe754a237b944bdcbbde1c205f2905e4f6efab9a` | the original with one line changed |

The one change: line 4 of the specification named the owner personally. This repository is public, so that line
reads "the repository owner" here. Every other byte is the original's.

What was done with the package, and what it showed, is in `docs/TRINITY.md`:

- its rules are ported to `aitrader/position/trinity.py`, and `tests/unit/test_trinity.py` checks the port against
  `trinity_omega_suite.py` itself, row by row;
- its claims were tested on real daily prices (`research/results/TRINITY-MASTER-redteam.json`);
- it runs on its own paper account (`aitrader/position/trinity_paper_desk.py`), sized by the risk engine.
