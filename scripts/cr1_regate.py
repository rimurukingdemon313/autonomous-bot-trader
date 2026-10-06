"""CR-1 validation re-check (does not change the recorded verdict). Two gate implementations in scripts/cr1.py
were wrong against the preregistered text, and the period end drops positions open at the seal:

1. `years` read a 2025 entry (the ledger runs 7 days past the period end, into the sealed period where no bar
   exists, and records 0.0) as a losing year; the preregistered gate names 2023 and 2024 only.
2. `monte_carlo` used `x or 1`, so P(total <= 0) = 0.0 (the best value) was read as 1.
3. Positions still open at 2025-01-01 cannot be closed (no bar exists before the seal is opened): counted here.

    python scripts/cr1_regate.py      # writes research/results/CR-1-regate.json
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location("cr1", ROOT / "scripts" / "cr1.py")
m = importlib.util.module_from_spec(spec)
sys.modules["cr1"] = m
spec.loader.exec_module(m)

val = json.loads((ROOT / "research" / "knowledge" / "CR-1-val.json").read_text())
p = val["results"]["CARRY-k3-in1.0"]
s = p["summary"]
recorded = val["gates"]["CARRY"]["gates"]
years = {y: v for y, v in s["by_year_ann_pct"].items() if y in ("2023", "2024")}
corrected = dict(recorded)
corrected["years"] = len(years) == 2 and all(v > 0 for v in years.values())
corrected["monte_carlo"] = p["monte_carlo"]["prob_total_le_0"] <= 0.05
a, b = m._ep(m.VAL[0]), m._ep(m.VAL[1])
open_at_end = {}
for sym in m.SYMBOLS:
    c = m.load(sym, m.VAL[1])
    pos, skipped = m.C.carry_positions(c, costs=m.COSTS, start=a, end=b, **m.CONFIGS["CARRY-k3-in1.0"][1])
    open_at_end[sym] = skipped
out = {"recorded_gates": recorded, "corrected_gates": corrected,
       "corrected_failed": [k for k, v in corrected.items() if not v],
       "verdict_after_correction": "PASSED" if all(corrected.values()) else "FAILED",
       "years_ann_pct": years, "positions_dropped_open_at_seal": open_at_end,
       "note": "the recorded registry verdict (FAILED) stands; this file documents the implementation errors"}
(ROOT / "research" / "results" / "CR-1-regate.json").write_text(json.dumps(out, indent=1) + "\n")
print(json.dumps(out, indent=1))
