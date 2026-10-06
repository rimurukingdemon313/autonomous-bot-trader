"""FT-1 clarification (research/preregistrations/FT-1.md): add the re-fetched bars for the months the first
fetch lost, after checking that every month present in both fetches agrees exactly.

    python scripts/ft1_refill.py <dir with the re-fetched npz files>

Writes data/ft1/<SYM>_H1_2025refill.npz holding only the lost months, plus research/results/FT-1-refill.json.
FT-1's loader (scripts/ix2.py `load`) reads every <SYM>_H1_*.npz in data/ft1 and keeps one bar per timestamp.
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from aitrader.data.bars import FIELDS, BarSeries  # noqa: E402

FT1 = ROOT / "data" / "ft1"
LOST = {"JPNIDXJPY": ["2025-04", "2025-06"], "USATECHIDXUSD": ["2025-07"]}
OUT = ROOT / "research" / "results" / "FT-1-refill.json"


def month(t: np.ndarray) -> np.ndarray:
    return np.array([datetime.fromtimestamp(int(x), timezone.utc).strftime("%Y-%m") for x in t])


def main(src: Path) -> int:
    report = {}
    for sym, lost in LOST.items():
        first = BarSeries.load(FT1 / f"{sym}_H1_2025_2026.npz")
        again = BarSeries.load(src / f"{sym}_H1_2025_2025.npz")
        m1, m2 = month(first.open_time), month(again.open_time)
        both = sorted((set(m1) & set(m2)) - set(lost))
        common = np.intersect1d(first.open_time, again.open_time)
        i1 = np.searchsorted(first.open_time, common)
        i2 = np.searchsorted(again.open_time, common)
        mismatch = {f: int(np.sum(getattr(first, f)[i1] != getattr(again, f)[i2])) for f in FIELDS}
        if any(mismatch.values()):
            raise SystemExit(f"{sym}: the two fetches disagree on shared bars {mismatch}: the run stops")
        only_first = sorted(set(m1) - set(m2))
        keep = np.isin(m2, lost)
        refill = again.take(keep)
        got = sorted(set(month(refill.open_time)))
        if len(refill):
            refill.save(FT1 / f"{sym}_H1_2025refill.npz")
        report[sym] = {"lost": lost, "recovered": got, "still_missing": sorted(set(lost) - set(got)),
                       "bars_added": int(len(refill)), "shared_bars_checked": int(len(common)),
                       "shared_months": both, "months_only_in_first_fetch": only_first, "mismatches": 0}
    OUT.write_text(json.dumps(report, indent=1) + "\n")
    print(json.dumps(report, indent=1))
    return 0


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit(__doc__)
    raise SystemExit(main(Path(sys.argv[1])))
