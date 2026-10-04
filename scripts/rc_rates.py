"""Extract the BIS policy rates the RC programs need into data/rc/policy_rates.csv (committed).

Source: data/rates/WS_CBPOL_csv_flat.csv (BIS WS_CBPOL, sha256 in data/rates/manifest.json), daily
rows only, values and dates copied unmodified. available_at follows aitrader/data/rates.py: a policy
rate in force on date d is public at 17:00 New York on d.
"""

from __future__ import annotations

import csv
import hashlib
import json
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from aitrader.data.rates import available_at  # noqa: E402

AREAS = ("US", "JP", "GB", "DE", "XM", "HK", "CA", "FR", "CH", "AU", "ES", "NL", "SE", "IT", "BE", "AT", "IN", "KR",
         "NZ", "MX", "BR", "IL", "MY", "ID")
SRC = ROOT / "data" / "rates" / "WS_CBPOL_csv_flat.csv"
OUT = ROOT / "data" / "rc" / "policy_rates.csv"


def main() -> int:
    raw = SRC.read_bytes()
    want = json.loads((ROOT / "data" / "rates" / "manifest.json").read_text())[SRC.name]["sha256"]
    if hashlib.sha256(raw).hexdigest() != want:
        raise SystemExit("the BIS file does not match its manifest; refusing")
    rows = []
    for r in csv.reader(raw.decode("utf-8-sig").splitlines()[1:]):
        if not r or not r[3].startswith("D"):
            continue
        area = r[4].split(":")[0].strip()
        if area not in AREAS or r[6].strip() == "":
            continue
        d = date.fromisoformat(r[5][:10])
        if d.year < 1985:
            continue
        rows.append((area, d.isoformat(), float(r[6]), available_at("POLICY", d)))
    rows.sort()
    body = "area,effective_date,value_pct,available_at_epoch\n" + "".join(f"{a},{d},{v!r},{t}\n" for a, d, v, t in rows)
    OUT.write_text(body)
    man = {"policy_rates.csv": {"rows": len(rows), "sha256": hashlib.sha256(body.encode()).hexdigest(),
                                "areas": list(AREAS), "derived_from": f"data/rates/{SRC.name}, sha256 {want}",
                                "method": "BIS WS_CBPOL daily rows from 1985, unmodified; available_at = 17:00 New York on the effective date (aitrader/data/rates.py)",
                                "licence": "BIS statistics, free reuse with attribution (Bank for International Settlements)"}}
    (OUT.parent / "manifest.json").write_text(json.dumps(man, indent=1, sort_keys=True) + "\n")
    print(len(rows), "rows")
    return 0


if __name__ == "__main__":
    sys.exit(main())
