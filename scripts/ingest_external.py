"""Fetch the external series once, verify them, and record exactly what was used.

    python scripts/ingest_external.py            # -> data/external/<key>.csv + data/external/manifest.json

The raw files are not committed (like the bars); the manifest is: source, mirror URL, retrieval
time, sha256, rows, first/last observation, and plausibility checks against well-known values.
A file that fails a check is not written.
"""

from __future__ import annotations

import hashlib
import json
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from aitrader.data.external import EXTERNAL_VERSION, SOURCES, parse  # noqa: E402

OUT = ROOT / "data" / "external"
#: well-known published values (date, value, tolerance): a wrong file, column or unit fails here
CHECKS = {
    "vix": [("2008-11-20", 80.86, 0.05), ("2015-08-24", 40.74, 0.05)],
    "brent": [("2008-07-03", 143.95, 0.5)],
    "us10y": [("2012-07-01", 1.53, 0.02)],
    "cpi_us": [("2015-01-01", 233.707, 0.01)],
    "sp500": [],
}


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    manifest = {}
    for key, src in SOURCES.items():
        raw = urllib.request.urlopen(src.url, timeout=60).read()
        s = parse(key, raw)
        idx = {datetime.fromtimestamp(int(o), timezone.utc).date().isoformat(): v for o, v in zip(s.obs_date, s.value)}
        failed = [(d, idx.get(d), v) for d, v, tol in CHECKS.get(key, []) if idx.get(d) is None or abs(idx[d] - v) > tol]
        if failed:
            print(f"{key}: plausibility check failed {failed}; not written")
            continue
        (OUT / f"{key}.csv").write_bytes(raw)
        first = datetime.fromtimestamp(int(s.obs_date.min()), timezone.utc).date().isoformat()
        last = datetime.fromtimestamp(int(s.obs_date.max()), timezone.utc).date().isoformat()
        manifest[key] = {"publisher": src.publisher, "url": src.url, "licence": src.licence,
                         "availability": src.availability, "revised": src.revised,
                         "retrieved": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                         "sha256": hashlib.sha256(raw).hexdigest(), "rows": int(len(s.value)), "first": first,
                         "last": last, "checks": CHECKS.get(key, []), "version": EXTERNAL_VERSION}
        print(key, manifest[key]["rows"], first, last)
    (OUT / "manifest.json").write_text(json.dumps(manifest, indent=1, sort_keys=True) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
