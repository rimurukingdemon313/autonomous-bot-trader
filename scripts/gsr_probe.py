"""Which public source can give GSR-1 daily gold and silver prices? Metadata only: for each candidate source, whether
it answers, how many daily rows it has, and its first and last dates. It computes nothing from the prices and
writes no price; GSR-1 is frozen only after this, on the source chosen here. Run on GitHub's runner (the sources
are blocked here)."""

from __future__ import annotations

import json
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

UA = {"User-Agent": "Mozilla/5.0 (research; aitrader GSR-1 probe)"}
OUT = Path(__file__).resolve().parent.parent / "research" / "results" / "GSR-probe.json"


def get(url: str) -> tuple[int | None, bytes]:
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60) as r:
            return r.status, r.read()
    except urllib.error.HTTPError as exc:
        return exc.code, b""
    except Exception as exc:  # noqa: BLE001 - reported
        return None, str(exc).encode()


def csv_meta(body: bytes) -> dict:
    lines = [ln for ln in body.decode("utf-8", "replace").splitlines() if ln.strip()]
    dates = [ln.split(",")[0] for ln in lines[1:] if ln[:1].isdigit()]
    return {"header": lines[0][:80] if lines else None, "rows": len(dates), "first": min(dates, default=None),
            "last": max(dates, default=None)}


def lbma_meta(body: bytes) -> dict:
    try:
        rows = json.loads(body)
    except Exception as exc:  # noqa: BLE001 - reported
        return {"error": str(exc)[:200], "head": body[:120].decode("utf-8", "replace")}
    dates = [r.get("d") for r in rows if isinstance(r, dict) and r.get("d")]
    return {"rows": len(dates), "first": min(dates, default=None), "last": max(dates, default=None),
            "fields": sorted(rows[0].keys()) if rows and isinstance(rows[0], dict) else None}


def yahoo_meta(body: bytes) -> dict:
    try:
        res = json.loads(body)["chart"]["result"][0]
    except Exception as exc:  # noqa: BLE001 - reported
        return {"error": str(exc)[:200]}
    ts = res.get("timestamp") or []
    f = lambda t: datetime.fromtimestamp(t, timezone.utc).date().isoformat()  # noqa: E731
    return {"rows": len(ts), "first": f(ts[0]) if ts else None, "last": f(ts[-1]) if ts else None}


def main() -> int:
    out = {"probed": datetime.now(timezone.utc).isoformat(), "sources": {}}
    for name, url, meta in (
        ("stooq-xauusd", "https://stooq.com/q/d/l/?s=xauusd&i=d", csv_meta),
        ("stooq-xagusd", "https://stooq.com/q/d/l/?s=xagusd&i=d", csv_meta),
        ("lbma-gold-pm", "https://prices.lbma.org.uk/json/gold_pm.json", lbma_meta),
        ("lbma-silver", "https://prices.lbma.org.uk/json/silver.json", lbma_meta),
        ("yahoo-GC=F", "https://query1.finance.yahoo.com/v8/finance/chart/GC=F?period1=0&period2=1790000000&interval=1d",
         yahoo_meta),
        ("yahoo-SI=F", "https://query1.finance.yahoo.com/v8/finance/chart/SI=F?period1=0&period2=1790000000&interval=1d",
         yahoo_meta),
    ):
        status, body = get(url)
        out["sources"][name] = {"url": url, "status": status, "bytes": len(body),
                                **(meta(body) if status == 200 else {"head": body[:160].decode("utf-8", "replace")})}
        print(name, json.dumps(out["sources"][name])[:300], flush=True)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, indent=1, sort_keys=True) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
