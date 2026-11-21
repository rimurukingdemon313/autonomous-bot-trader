"""The daily bars TRINITY-MASTER reads (docs/TRINITY.md): public Yahoo daily bars, fetched on GitHub's runner.

PAPER AND RESEARCH ONLY. No broker, no account, no key. The owner's package (2026-11-21) defines the strategy on the
closes of four US-listed funds and reads three more series as sensors that are never traded:

- signals: QQQ, SPY, GLD, DBC (its four assets);
- sensors: ^VIX, TLT, UUP (read, never traded: TLT holds bonds, which pay interest);
- the instruments a CFD account would trade instead (the package's own map): ^NDX for NAS100, ^GSPC for US500, and,
  for the two commodities, GLD's and USO's own returns (a swap-free CFD earns the spot or rolled-futures return, not a
  continuous futures series, which jumps at each roll). GC=F and CL=F are kept for reference only.

Each series is written as it was served: every final daily bar's open, high, low, close (not adjusted), the adjusted
close Yahoo computes, and the volume, by the exchange's own date. Nothing is filled, smoothed or adjusted here. A bar
counts only once its day has ended in UTC, so a partial bar of the day being fetched is never stored.

    python scripts/trinity_data.py --out <dir> [--first 2006-01-01]
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
import urllib.parse
import urllib.request
from datetime import date, datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

TRINITY_DATA_VERSION = "trinity-data-1.0.0"
SIGNALS = ("QQQ", "SPY", "GLD", "DBC")
SENSORS = ("^VIX", "TLT", "UUP")
PRICES = ("^NDX", "^GSPC", "USO")
REFERENCE = ("GC=F", "CL=F")
SYMBOLS = SIGNALS + SENSORS + PRICES + REFERENCE
FIRST = date(2006, 1, 1)
UA = {"User-Agent": "Mozilla/5.0 (research; aitrader trinity data)"}


def chart(sym: str, first: date, now: datetime, opener=urllib.request.urlopen) -> dict:
    p1 = int(datetime(first.year, first.month, first.day, tzinfo=timezone.utc).timestamp())
    url = (f"https://query1.finance.yahoo.com/v8/finance/chart/{urllib.parse.quote(sym)}?period1={p1}"
           f"&period2={int(now.timestamp())}&interval=1d&events=div%2Csplit")
    with opener(urllib.request.Request(url, headers=UA), timeout=60) as r:
        return json.loads(r.read())["chart"]["result"][0]


def _num(v) -> float | None:
    return float(v) if isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v) else None


def parse(res: dict, now: datetime) -> tuple[dict[str, dict], list[str]]:
    """{day: {o, h, l, c, adj, v}} by the exchange's own date, and the problems found. A row whose day has not ended
    in UTC at `now` is not final and is left out. A row with no close is left out and named; nothing is filled."""
    tz = ZoneInfo(res["meta"].get("exchangeTimezoneName") or "America/New_York")
    q = res["indicators"]["quote"][0]
    adj = ((res["indicators"].get("adjclose") or [{}])[0]).get("adjclose") or []
    out, problems = {}, []
    today = now.astimezone(timezone.utc).date()
    for i, ts in enumerate(res.get("timestamp") or []):
        day = datetime.fromtimestamp(ts, timezone.utc).astimezone(tz).date()
        if day >= today:
            continue  # the day being fetched: not final
        row = {k: _num(q.get(src, [None] * (i + 1))[i]) for k, src in
               (("o", "open"), ("h", "high"), ("l", "low"), ("c", "close"), ("v", "volume"))}
        row["adj"] = _num(adj[i]) if i < len(adj) else None
        if row["c"] is None or row["c"] <= 0:
            if any(row[k] is not None for k in ("o", "h", "l")):
                problems.append(f"{day}: no close ({row})")
            continue
        key = day.isoformat()
        if key in out:
            problems.append(f"{day}: a second row for the same day; the first is kept")
            continue
        out[key] = row
    return out, problems


def write(out_dir: Path, now: datetime, first: date = FIRST, fetch=chart) -> dict:
    """Fetch every series and write <out>/history/<symbol>.json and <out>/history/manifest.json. A series that cannot
    be fetched is named in the manifest; nothing is written in its place."""
    hist = out_dir / "history"
    hist.mkdir(parents=True, exist_ok=True)
    man = {"version": TRINITY_DATA_VERSION, "retrieved": now.isoformat(), "source": "query1.finance.yahoo.com v8 chart",
           "first_asked": first.isoformat(), "series": {}, "failed": {}}
    for sym in SYMBOLS:
        try:
            rows, problems = parse(fetch(sym, first, now), now)
        except Exception as e:  # noqa: BLE001 - named in the manifest, never replaced
            man["failed"][sym] = f"{type(e).__name__}: {e}"[:300]
            continue
        body = json.dumps(rows, sort_keys=True, separators=(",", ":"))
        name = sym.replace("^", "_").replace("=", "_")
        (hist / f"{name}.json").write_text(body)
        days = sorted(rows)
        man["series"][sym] = {"file": f"history/{name}.json", "rows": len(rows), "first": days[0] if days else None,
                              "last": days[-1] if days else None, "problems": problems[:20],
                              "sha256": hashlib.sha256(body.encode()).hexdigest()}
    (hist / "manifest.json").write_text(json.dumps(man, indent=1, sort_keys=True) + "\n")
    return man


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--out", required=True)
    ap.add_argument("--first", default=FIRST.isoformat())
    a = ap.parse_args(argv)
    man = write(Path(a.out), datetime.now(timezone.utc), date.fromisoformat(a.first))
    print(json.dumps({k: (v if k != "series" else {s: {kk: x[kk] for kk in ("rows", "first", "last")}
                                                       for s, x in v.items()}) for k, v in man.items()}, indent=1))
    return 1 if man["failed"] else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
