"""Which stock indices have a long daily history from before 1990 that no test here has read? Dates only: for each
symbol, from Yahoo (through TRND-1's own fetch) and from Stooq, the number of closes, the first and last dates, the
closes per decade (to tell daily from monthly history), and every calendar month before 1990 without a close. No
price, return or mean is printed, kept or computed. A TRND-2 candidate is designed only after this. Run on GitHub's
runner (both sources are blocked here)."""

from __future__ import annotations

import csv
import io
import json
import sys
import urllib.parse
import urllib.request
from collections import Counter
from datetime import date, datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import scripts.trnd1 as T  # noqa: E402
from scripts.trnd_probe import missing_months  # noqa: E402

OUT = ROOT / "research" / "results" / "TRND2-probe.json"
YAHOO = ("^N225", "^HSI", "^GSPTSE", "^AORD", "^FCHI", "^SSMI", "^AEX", "^STI", "^TWII", "^KS11", "^BSESN", "^MXX",
         "^IBEX", "^BFX", "^ATX", "^NZ50", "^MERV", "^OMXSPI", "^IXIC", "^DJI")
STOOQ = ("^dji", "^spx", "^ndq", "^dax", "^nkx", "^hsi", "^ukx", "^cac", "^aex", "^smi", "^aor", "^tsx", "^kospi",
         "^twse", "^sti", "^ibex", "^bel20", "^atx", "^omxs", "^mxx")


def stooq_days(sym: str) -> list[date]:
    url = f"https://stooq.com/q/d/l/?s={urllib.parse.quote(sym)}&i=d"
    with urllib.request.urlopen(urllib.request.Request(url, headers=T.UA), timeout=60) as r:
        body = r.read().decode("utf-8", "replace")
    rows = list(csv.reader(io.StringIO(body)))
    if not rows or not rows[0] or rows[0][0].strip().lower() != "date":
        raise ValueError(f"not a price file: {body[:80]!r}")
    return sorted({date.fromisoformat(r[0]) for r in rows[1:] if r and r[0][:4].isdigit()})


def describe(days: list[date]) -> dict:
    before = [d for d in days if d < date(1990, 1, 1)]
    return {"rows": len(days), "first": str(days[0]), "last": str(days[-1]),
            "per_decade": dict(sorted(Counter(f"{d.year // 10 * 10}s" for d in days).items())),
            "rows_before_1990": len(before),
            "missing_months_before_1990": missing_months(before) if before else []}


def main() -> int:
    now = datetime.now(timezone.utc)
    report = {"probed": now.isoformat(), "yahoo": {}, "stooq": {}}
    for src, syms, get in (("yahoo", YAHOO, lambda s: [date.fromisoformat(d) for d, _ in T._yahoo(s, now)]),
                           ("stooq", STOOQ, stooq_days)):
        for sym in syms:
            try:
                report[src][sym] = describe(get(sym))
            except Exception as exc:  # noqa: BLE001 - reported, never hidden
                report[src][sym] = {"error": f"{type(exc).__name__}: {exc}"[:200]}
            r = report[src][sym]
            print(src, sym, json.dumps({k: r[k] for k in r if k != "missing_months_before_1990"}),
                  "missing<1990:", len(r.get("missing_months_before_1990", [])), r.get("missing_months_before_1990", [])[:6])
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, indent=1, sort_keys=True) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
