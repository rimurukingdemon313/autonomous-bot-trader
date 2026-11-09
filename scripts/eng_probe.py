"""ENG-1 data probe (docs/DISCOVERY_PROGRAM.md, H1): which EIA futures-price series exist, from when to when, and with
what gaps. ENG-1 is specified only after this.

Dates only. For contracts 1 to 4 of WTI crude, NY Harbor heating oil, NY Harbor RBOB and conventional gasoline, and
Henry Hub natural gas, it reports per series:
- the HTTP status, the rows, the first and last dates;
- the weekdays without a price, the longest gap;
- the file's sha256.
Per commodity it reports the first and last dates on which all four contracts are priced.

No price, return, spread or mean is printed, kept or computed: a value is only checked to be a number, so the test
stays blind. EIA stopped publishing NYMEX futures prices after 2024-04-05; the probe says where each series really ends.
Run on GitHub's runner (EIA is blocked here): .github/workflows/eng-probe.yml.
"""

from __future__ import annotations

import hashlib
import json
import urllib.error
import urllib.request
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "research" / "results" / "ENG-probe.json"
UA = {"User-Agent": "Mozilla/5.0 (research; aitrader ENG-1 data probe)"}
URL = {"pet": "https://www.eia.gov/dnav/pet/hist_xls/{sid}d.xls", "ng": "https://www.eia.gov/dnav/ng/hist_xls/{sid}d.xls"}
SERIES = {
    "WTI": ("pet", [f"RCLC{n}" for n in range(1, 5)]),
    "HEATING_OIL": ("pet", [f"EER_EPD2F_PE{n}_Y35NY_DPG" for n in range(1, 5)]),
    "RBOB": ("pet", [f"EER_EPMRR_PE{n}_Y35NY_DPG" for n in range(1, 5)]),
    "GASOLINE_CONVENTIONAL": ("pet", [f"EER_EPMRU_PE{n}_Y35NY_DPG" for n in range(1, 5)]),
    "NATGAS": ("ng", [f"RNGC{n}" for n in range(1, 5)]),
}
EXCEL_EPOCH = date(1899, 12, 30)


def priced_days(rows: list[tuple]) -> list[date]:
    """The dates that carry a number in a data sheet's rows of (date cell, value cell). A cell is (kind, value), the kind
    being "date", "number" or anything else. Header rows, blanks and non-numbers are skipped. The value itself is
    never kept."""
    days = set()
    for row in rows:
        if len(row) < 2:
            continue
        (ka, a), (kb, b) = row[0], row[1]
        if ka in ("date", "number") and isinstance(a, (int, float)) and 20000 < a < 80000 and kb == "number" \
                and isinstance(b, (int, float)):
            days.add(EXCEL_EPOCH + timedelta(days=int(a)))
    return sorted(days)


def weekdays(a: date, b: date) -> list[date]:
    out, d = [], a
    while d <= b:
        if d.weekday() < 5:
            out.append(d)
        d += timedelta(days=1)
    return out


def describe(days: list[date]) -> dict:
    """Rows, first and last dates, weekdays without a price between them (exchange holidays included), the longest
    gap in calendar days, and the rows per decade (to tell daily from sparser history)."""
    if not days:
        return {"rows": 0}
    have = set(days)
    missing = [d for d in weekdays(days[0], days[-1]) if d not in have]
    gaps = [(b - a).days for a, b in zip(days, days[1:])]
    decades: dict[str, int] = {}
    for d in days:
        k = f"{d.year // 10 * 10}s"
        decades[k] = decades.get(k, 0) + 1
    return {"rows": len(days), "first": str(days[0]), "last": str(days[-1]), "missing_weekdays": len(missing),
            "missing_weekdays_per_year": round(len(missing) / max(1e-9, (days[-1] - days[0]).days / 365.25), 1),
            "longest_gap_days": max(gaps) if gaps else 0, "per_decade": decades}


def common(series_days: list[list[date]]) -> dict:
    """The dates on which every contract is priced."""
    if not series_days or any(not s for s in series_days):
        return {"rows": 0}
    both = sorted(set.intersection(*(set(s) for s in series_days)))
    return {"rows": len(both), "first": str(both[0]) if both else None, "last": str(both[-1]) if both else None}


def xls_rows(raw: bytes) -> list[tuple]:
    import xlrd  # the runner installs it; EIA serves the old binary .xls format
    book = xlrd.open_workbook(file_contents=raw)
    names = book.sheet_names()
    sheet = book.sheet_by_name("Data 1") if "Data 1" in names else book.sheet_by_index(min(1, len(names) - 1))
    kind = {xlrd.XL_CELL_DATE: "date", xlrd.XL_CELL_NUMBER: "number"}
    return [tuple((kind.get(sheet.cell_type(r, c), "other"), sheet.cell_value(r, c)) for c in range(min(2, sheet.ncols)))
            for r in range(sheet.nrows)]


def fetch(url: str) -> tuple[int, bytes]:
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=90) as r:
            return r.status, r.read()
    except urllib.error.HTTPError as e:
        return e.code, b""


def main() -> int:
    out = {"probe": "ENG-1", "run": datetime.now(timezone.utc).isoformat(), "series": {}, "commodities": {},
           "note": "dates only: no price, return, spread or mean was computed or kept"}
    for name, (kind, sids) in SERIES.items():
        days_by = []
        for sid in sids:
            url = URL[kind].format(sid=sid)
            status, raw = fetch(url)
            entry = {"url": url, "status": status, "bytes": len(raw)}
            if status == 200 and raw:
                try:
                    days = priced_days(xls_rows(raw))
                    entry |= describe(days) | {"sha256": hashlib.sha256(raw).hexdigest()}
                    days_by.append(days)
                except Exception as e:  # noqa: BLE001 - reported, the probe continues
                    entry["error"] = f"{type(e).__name__}: {e}"
            out["series"][sid] = entry
            print(sid, json.dumps(entry, default=str), flush=True)
        out["commodities"][name] = common(days_by) if len(days_by) == len(sids) else {"rows": 0, "why": "a series is missing"}
        print(name, out["commodities"][name], flush=True)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, indent=1, sort_keys=True, default=str) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
