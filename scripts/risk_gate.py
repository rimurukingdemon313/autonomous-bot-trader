"""Operator view and controls of the hard risk gate (docs/HARD_RISK_GATE.md). Never exposed to a model or the dashboard.

    python scripts/risk_gate.py status                         [--data-dir DIR]
    python scripts/risk_gate.py log [N]                        [--data-dir DIR]   # the last N gate decisions
    python scripts/risk_gate.py clear-kill "REASON"            [--data-dir DIR]   # data/state kills only, never a lock
    python scripts/risk_gate.py reset-evaluation "REASON"      [--data-dir DIR]   # a new run; account must be flat at the start

The profile is the service's own (RISK_PROFILE / RISK_PROFILE_OVERRIDES), so the gate judges the run with the
profile it started under, or refuses.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from aitrader.broker.paper import PaperBroker  # noqa: E402
from aitrader.memory.db import Database  # noqa: E402
from aitrader.risk.hard_gate import CLEAR_KILL_CONFIRMATION, RESET_CONFIRMATION, HardRiskGate  # noqa: E402
from aitrader.service.config import ServiceConfig  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("command", choices=("status", "log", "clear-kill", "reset-evaluation"))
    ap.add_argument("arg", nargs="?")
    ap.add_argument("--data-dir", default=os.environ.get("DATA_DIR", "./runtime"))
    a = ap.parse_args()
    cfg = ServiceConfig.from_env()
    db_path = Path(a.data_dir) / "aitrader.db"
    if not db_path.exists():
        raise SystemExit(f"no database at {db_path}")
    db = Database(db_path)
    clock = lambda: int(time.time())  # noqa: E731
    gate = HardRiskGate(db, cfg.hard_profile, clock)
    if a.command == "status":
        print(json.dumps(gate.status(), indent=1, default=str))
    elif a.command == "log":
        rows = db.query("SELECT kind, decision_id, approved, payload FROM risk_gate_log ORDER BY seq DESC LIMIT ?",
                        (int(a.arg or 20),))
        for r in reversed(rows):
            p = json.loads(r["payload"])
            print(r["kind"], r["decision_id"] or "", p.get("line") or json.dumps(p, default=str)[:200])
    elif a.command == "clear-kill":
        if not a.arg:
            raise SystemExit("a reason is required")
        print("cleared" if gate.clear_kill(CLEAR_KILL_CONFIRMATION, a.arg) else
              "not cleared: no clearable kill (a lock or a corrupt state is cleared only by an evaluation reset)")
    else:
        if not a.arg:
            raise SystemExit("a reason is required")
        broker = PaperBroker(None, clock, db, start_balance=cfg.hard_profile.starting_balance)
        print(json.dumps(gate.reset_evaluation(broker, RESET_CONFIRMATION, a.arg)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
