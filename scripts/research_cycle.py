"""One autonomous research cycle (docs/AUTONOMOUS_RESEARCH_SYSTEM.md): integrity, ideas, the research report.

    python scripts/research_cycle.py --state <dir>    # GitHub's runner, daily: .github/workflows/research-cycle.yml

RESEARCH ONLY: no broker, no order, no trading rule touched. The state directory holds the permanent ideas ledger
(ideas.jsonl), the cycle log (cycles.jsonl) and the report written from them (RESEARCH_REPORT.md and .json). The
workflow carries it on the `research-data` branch from run to run.

Exit codes:
- 0: the cycle ran, or its ideas step failed for a reason the next run retries (the report says which);
- 1: the permanent record failed an integrity check;
- 2: no successful ideas step for over 72 hours (stalled).
The report is written whatever the result.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from scripts import research_report  # noqa: E402
from scripts.research_engine import Engine, openrouter_ask, read_jsonl  # noqa: E402


def cycle(state: Path, now: datetime, ask, root: Path = ROOT) -> int:
    res = Engine(root, state, ask, now).run()
    research_report.write(root, now.date(), now, out=state, ideas=read_jsonl(state / "ideas.jsonl"),
                          cycles=read_jsonl(state / "cycles.jsonl"))
    print(json.dumps({"cycle": res.cycle, "integrity": res.integrity or "OK", "ideas": res.ideas,
                      "new": [(i["decision"], i["title"]) for i in res.new_ideas], "stalled": res.stalled,
                      "exit": res.exit_code}, indent=1))
    return res.exit_code


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--state", required=True, type=Path)
    args = ap.parse_args()
    now = datetime.now(timezone.utc)  # the command line's clock: the engine takes it as an argument
    return cycle(args.state, now, openrouter_ask())


if __name__ == "__main__":
    raise SystemExit(main())
