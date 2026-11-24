"""The daily bars the owner's SOVEREIGN package reads (research/external/sovereign/, 2026-11-24): public Yahoo daily
bars, fetched on GitHub's runner, for its red team (scripts/sovereign_redteam.py, docs/SOVEREIGN.md).

RESEARCH ONLY. No broker, no account, no key, no order. The package trades seven US-listed funds: QQQ, SPY, IWM (US
equities), GLD, SLV (gold, silver), USO (crude oil) and IBIT (spot bitcoin, which the package admits from 2024-11).
Each series is written as it was served, by the same parser as the TRINITY desk's fetcher (scripts/trinity_data.py):
every final daily bar's open, high, low, close, Yahoo's adjusted close and the volume, by the exchange's own date.
Nothing is filled, smoothed or adjusted here. A bar counts only once its day has ended in UTC.

    python scripts/sovereign_data.py --out <dir> [--first 2006-01-01]
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import date, datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.trinity_data import chart, parse  # noqa: E402  (one parser for every Yahoo fetch in this repository)

SOVEREIGN_DATA_VERSION = "sovereign-data-1.0.0"
SYMBOLS = ("QQQ", "SPY", "IWM", "GLD", "SLV", "USO", "IBIT")
FIRST = date(2006, 1, 1)


def write(out_dir: Path, now: datetime, first: date = FIRST, fetch=chart, symbols: tuple = SYMBOLS) -> dict:
    """Fetch every series and write <out>/history/<symbol>.json and <out>/history/manifest.json. A series that cannot
    be fetched is named in the manifest; nothing is written in its place."""
    hist = out_dir / "history"
    hist.mkdir(parents=True, exist_ok=True)
    man = {"version": SOVEREIGN_DATA_VERSION, "retrieved": now.isoformat(),
           "source": "query1.finance.yahoo.com v8 chart", "first_asked": first.isoformat(), "series": {},
           "failed": {}}
    for sym in symbols:
        try:
            rows, problems = parse(fetch(sym, first, now), now)
        except Exception as e:  # noqa: BLE001 - named in the manifest, never replaced
            man["failed"][sym] = f"{type(e).__name__}: {e}"[:300]
            continue
        if not rows:
            man["failed"][sym] = "no final daily bar was served"
            continue
        body = json.dumps(rows, sort_keys=True, separators=(",", ":"))
        (hist / f"{sym}.json").write_text(body)
        days = sorted(rows)
        man["series"][sym] = {"file": f"history/{sym}.json", "rows": len(rows), "first": days[0], "last": days[-1],
                              "problems": problems[:20], "sha256": hashlib.sha256(body.encode()).hexdigest()}
    (hist / "manifest.json").write_text(json.dumps(man, indent=1, sort_keys=True) + "\n")
    return man


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--out", required=True)
    ap.add_argument("--first", default=FIRST.isoformat())
    a = ap.parse_args(argv)
    man = write(Path(a.out), datetime.now(timezone.utc), date.fromisoformat(a.first))
    print(json.dumps({"retrieved": man["retrieved"], "failed": man["failed"],
                      "series": {s: {k: x[k] for k in ("rows", "first", "last")} for s, x in man["series"].items()}},
                     indent=1))
    return 1 if man["failed"] else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
