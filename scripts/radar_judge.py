"""Register the RADAR-1 forward test, and later record its verdict from the frozen look file.

    python scripts/radar_judge.py hash                       # code hash quoted by the preregistration
    python scripts/radar_judge.py register                   # once, before the first live run
    python scripts/radar_judge.py verdict RADAR-1-lookN.json  # once, from the `radar-data` branch

The verdict is never computed here: the hourly runner froze it at the look date (scripts/radar_run.py,
freeze_looks). This script only checks that the code that produced it is the code that was registered, and
writes the registry line.
"""

from __future__ import annotations

import hashlib
import json
import sys
from datetime import date, datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from aitrader.research.registry import Registry, Trial, Use, Verdict  # noqa: E402

PID = "RADAR-1"
DOC = "research/preregistrations/RADAR-1.md"
CODE = ("aitrader/radar/__init__.py", "aitrader/radar/core.py", "aitrader/radar/venues.py", "scripts/radar_run.py")
UNIVERSE = "crypto-perp-live-xvenue"
WINDOW = ("2026-10-07", "2027-02-15")  # live, forward only: covers the look (day 60) and the one extension (day 120)
LABELS = {"PASSED": "PROMISING BUT NOT YET PROVEN", "FAILED": "NO ROBUST EDGE FOUND",
          "INCONCLUSIVE": "NO ROBUST EDGE FOUND"}


def code_hash() -> str:
    h = hashlib.sha256()
    for f in CODE:
        h.update((ROOT / f).read_bytes())
    return h.hexdigest()


def registry() -> Registry:
    return Registry.load(ROOT / "research" / "registry.jsonl")


def main() -> int:
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    if cmd == "hash":
        print(code_hash())
        return 0
    reg = registry()
    if cmd == "register":
        h = code_hash()
        if h not in (ROOT / DOC).read_text():
            raise SystemExit(f"{DOC} must quote the code sha256 {h}")
        reg.register(Trial(id=PID, registered=datetime.now(timezone.utc),
                           title="RADAR-1: live cross-venue funding radar, paper forward test",
                           hypothesis="Same-coin perpetual funding differs between venues by more than the cost of "
                                      "crossing it often enough that a delta-neutral short-high/long-low book, run "
                                      "hourly on live public quotes, beats cash by 10%/yr on the capital it uses.",
                           uses=(Use(UNIVERSE, date.fromisoformat(WINDOW[0]), date.fromisoformat(WINDOW[1]), "judge"),),
                           tests=1, configurations=1, preregistration=DOC, design={"code_sha256": h}))
        print("registered", PID)
        return 0
    if cmd == "verdict":
        if reg.status_of(PID) != "PENDING":
            raise SystemExit("RADAR-1 already has a verdict")
        if reg.get(PID).design["code_sha256"] != code_hash():
            raise SystemExit("the radar code changed since registration: the frozen look cannot be attributed to it")
        look = json.loads(Path(sys.argv[2]).read_text())
        if look["status"] not in LABELS:
            raise SystemExit(f"not a verdict: {look['status']}")
        reg.record_verdict(Verdict(PID, datetime.now(timezone.utc), look["status"],
                                   {"label": LABELS[look["status"]], "gates": look["gates"], "perf": look["perf"],
                                    "look_t": look["t"]}))
        print(PID, look["status"], LABELS[look["status"]])
        return 0
    raise SystemExit(__doc__)


if __name__ == "__main__":
    raise SystemExit(main())
