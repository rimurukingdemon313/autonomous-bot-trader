"""Can TRND-1's frozen fetch get what its judge needs? Dates only: for each index, through TRND-1's own `_yahoo`, the
number of daily closes, the first and last dates, the closes per decade, and every calendar month between the first
and the last that has no close. No price, return or mean is printed, kept or computed. TRND-1 is frozen only after
this. Run on GitHub's runner (Yahoo is blocked here)."""

from __future__ import annotations

import json
import sys
from collections import Counter
from datetime import date, datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import scripts.trnd1 as T  # noqa: E402

OUT = ROOT / "research" / "results" / "TRND-probe.json"


def missing_months(days: list[date]) -> list[str]:
    have = {(d.year, d.month) for d in days}
    out, (y, m) = [], (days[0].year, days[0].month)
    while (y, m) <= (days[-1].year, days[-1].month):
        if (y, m) not in have:
            out.append(f"{y}-{m:02d}")
        y, m = (y + 1, 1) if m == 12 else (y, m + 1)
    return out


def main() -> int:
    now = datetime.now(timezone.utc)
    report = {"probed": now.isoformat(), "series": {}}
    for sym in T.HOLDOUT_INDICES:
        try:
            days = [date.fromisoformat(d) for d, _ in T._yahoo(sym, now)]
        except Exception as exc:  # noqa: BLE001 - reported, never hidden
            report["series"][sym] = {"error": f"{type(exc).__name__}: {exc}"[:300]}
            print(sym, "ERROR", report["series"][sym]["error"])
            continue
        report["series"][sym] = {"rows": len(days), "first": str(days[0]), "last": str(days[-1]),
                                 "per_decade": dict(sorted(Counter(f"{d.year // 10 * 10}s" for d in days).items())),
                                 "missing_months": missing_months(days)}
        print(sym, json.dumps(report["series"][sym]))
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, indent=1, sort_keys=True) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
