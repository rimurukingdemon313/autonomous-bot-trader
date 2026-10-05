"""Availability probe for the intraday program (ID-1): can the Dukascopy datafeed be read from this
runner, in what format, for which instruments and from when, and how fast. Records file sizes,
record counts, the decoded price RANGE of single days (a format check) and timings only."""

from __future__ import annotations

import json
import lzma
import struct
import sys
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
URL = "https://datafeed.dukascopy.com/datafeed/{sym}/{y}/{m:02d}/{d:02d}/{side}_candles_min_1.bi5"
UA = {"User-Agent": "Mozilla/5.0 (research; aitrader ID probe)"}
SYMS = ["EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "USDCAD", "USDCHF", "NZDUSD", "XAUUSD", "EURJPY", "GBPJPY",
        "USA500IDXUSD", "USATECHIDXUSD", "DEUIDXEUR", "GBRIDXGBP", "JPNIDXJPY"]


def get(sym, d, side="BID"):
    url = URL.format(sym=sym, y=d.year, m=d.month - 1, d=d.day, side=side)
    t0 = time.time()
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=30) as r:
            raw = r.read()
    except Exception as exc:  # noqa: BLE001
        return {"error": f"{type(exc).__name__}: {exc}"[:120], "secs": round(time.time() - t0, 2)}
    out = {"bytes": len(raw), "secs": round(time.time() - t0, 2)}
    if raw:
        data = lzma.decompress(raw)
        n = len(data) // 24
        recs = [struct.unpack(">5if", data[i * 24:(i + 1) * 24]) for i in range(n)]
        live = [r for r in recs if r[5] > 0]
        out.update(records=n, with_volume=len(live), first_offset_s=recs[0][0] if recs else None,
                   price_int_range=[min(r[3] for r in live), max(r[4] for r in live)] if live else None)
    return out


def main() -> int:
    res = {}
    for s in SYMS:
        res[s] = {str(d): get(s, d) for d in (date(2009, 3, 3), date(2012, 3, 6), date(2016, 6, 7), date(2024, 6, 4))}
        print(s, json.dumps(res[s]), flush=True)
    days = [date(2010, 1, 4) + timedelta(days=i) for i in range(120)]
    t0 = time.time()
    with ThreadPoolExecutor(24) as ex:
        out = list(ex.map(lambda d: get("EURUSD", d), days))
    res["throughput"] = {"files": len(days), "secs": round(time.time() - t0, 1),
                         "errors": sum("error" in o for o in out), "empty": sum(o.get("bytes") == 0 for o in out)}
    print("throughput", res["throughput"])
    (ROOT / "research" / "results" / "id-probe.json").write_text(json.dumps(res, indent=1) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
