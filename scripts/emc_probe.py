"""Which public sources can give EMC-1 its currencies and its policy rates? Metadata only: for each source, whether it
answers, and for each series how many rows it has and its first and last dates. It computes nothing from a price or a
rate. EMC-1 is frozen only after this, on the sources chosen here. Run on GitHub's runner (the sources are blocked
here)."""

from __future__ import annotations

import csv
import io
import json
import sys
import urllib.request
import zipfile
from datetime import datetime, timezone
from pathlib import Path

UA = {"User-Agent": "Mozilla/5.0 (research; aitrader EMC-1 probe)"}
OUT = Path(__file__).resolve().parent.parent / "research" / "results" / "EMC-probe.json"
PAIRS = ("MXN=X", "ZAR=X", "TRY=X", "PLN=X", "HUF=X", "CZK=X")
AREAS = ("US", "MX", "ZA", "TR", "PL", "HU", "CZ")
BIS_BULK = "https://data.bis.org/static/bulk/WS_CBPOL_csv_flat.zip"


def get(url: str) -> tuple[int | None, bytes]:
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=120) as r:
            return r.status, r.read()
    except urllib.error.HTTPError as exc:
        return exc.code, b""
    except Exception as exc:  # noqa: BLE001 - reported
        return None, str(exc).encode()


def yahoo_meta(sym: str) -> dict:
    status, body = get(f"https://query1.finance.yahoo.com/v8/finance/chart/{sym}?period1=0&period2=1790000000"
                       "&interval=1d")
    if status != 200:
        return {"status": status, "head": body[:160].decode("utf-8", "replace")}
    res = json.loads(body)["chart"]["result"][0]
    ts = res.get("timestamp") or []
    closes = res["indicators"]["quote"][0]["close"]
    f = lambda t: datetime.fromtimestamp(t, timezone.utc).date().isoformat()  # noqa: E731
    return {"status": status, "rows": len(ts), "with_close": sum(1 for c in closes if c is not None),
            "first": f(ts[0]) if ts else None, "last": f(ts[-1]) if ts else None,
            "timezone": res.get("meta", {}).get("exchangeTimezoneName")}


def bis_meta() -> dict:
    status, body = get(BIS_BULK)
    if status != 200:
        return {"status": status, "head": body[:160].decode("utf-8", "replace")}
    z = zipfile.ZipFile(io.BytesIO(body))
    name = z.namelist()[0]
    seen: dict = {}
    with z.open(name) as f:
        reader = csv.DictReader(io.TextIOWrapper(f, encoding="utf-8"))
        cols = reader.fieldnames
        code = lambda r, k: (r.get(k) or r.get(next((c for c in cols if c.startswith(k + ":")), k)) or "").split(":")[0]  # noqa: E731
        for r in reader:
            area, freq = code(r, "REF_AREA"), code(r, "FREQ")
            t = (r.get("TIME_PERIOD") or r.get("TIME_PERIOD:Time period or range") or "").strip()
            if area in AREAS and freq == "D" and t:
                s = seen.setdefault(area, {"rows": 0, "first": t, "last": t})
                s["rows"] += 1
                s["first"], s["last"] = min(s["first"], t), max(s["last"], t)
    return {"status": status, "bytes": len(body), "member": name, "columns": cols, "daily": seen}


def main() -> int:
    out = {"probed": datetime.now(timezone.utc).isoformat(), "yahoo": {}, "bis": None}
    for sym in PAIRS:
        out["yahoo"][sym] = yahoo_meta(sym)
        print(sym, json.dumps(out["yahoo"][sym]), flush=True)
    out["bis"] = bis_meta()
    print("BIS", json.dumps({k: v for k, v in out["bis"].items() if k != "columns"})[:1500], flush=True)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, indent=1, sort_keys=True) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
