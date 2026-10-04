"""Availability probe for the RC programs (research/preregistrations/RC-EQ.md).

Records, per Yahoo ticker, ONLY what is needed to fix the universe before any outcome is read: the
exchange time zone, the currency, the first and last local dates, the number of closes, and how
many are missing. No price level, return or statistic of any series is written or printed.
Also records whether the CFTC bulk-file host answers (COT for 2017+).
"""

from __future__ import annotations

import json
import socket
import sys
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

socket.setdefaulttimeout(30)
ROOT = Path(__file__).resolve().parent.parent
UA = {"User-Agent": "Mozilla/5.0 (research; aitrader RC probe)"}
TICKERS = ["^GSPC", "^SP500TR", "^NDX", "^N225", "^FTSE", "^GDAXI", "^HSI", "^GSPTSE", "^FCHI", "^SSMI", "^AXJO",
           "^RUT", "^IBEX", "^AEX", "^STOXX50E", "^OMX", "FTSEMIB.MI", "^BFX", "^ATX", "PSI20.LS", "^NSEI",
           "^KS11", "^NZ50", "^MXX", "^BVSP", "^OSEAX", "^OMXC25", "^TA125.TA", "^SET.BK", "^KLSE", "^JKSE",
           "PSEI.PS", "WIG20.WA", "^BUX.BU"]


def probe(sym: str) -> dict:
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{sym}?period1=0&period2={int(time.time())}&interval=1d"
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60) as r:
        res = json.loads(r.read())["chart"]["result"][0]
    tz = ZoneInfo(res["meta"]["exchangeTimezoneName"])
    closes = res["indicators"]["quote"][0]["close"]
    days = [datetime.fromtimestamp(t, timezone.utc).astimezone(tz).date() for t in res["timestamp"]]
    ok = [d for d, c in zip(days, closes) if c is not None and c > 0]
    before = [d for d in ok if d.year < 2021]
    return {"tz": res["meta"]["exchangeTimezoneName"], "currency": res["meta"].get("currency"),
            "first": str(ok[0]) if ok else None, "last": str(ok[-1]) if ok else None, "closes": len(ok),
            "missing": len(days) - len(ok), "years_before_2021": round(len(before) / 252, 1)}


def main() -> int:
    out = {}
    for s in TICKERS:
        try:
            out[s] = probe(s)
        except Exception as exc:  # noqa: BLE001 - a probe records failures, it does not stop
            out[s] = {"error": f"{type(exc).__name__}: {exc}"[:200]}
        print(s, out[s], flush=True)
    try:
        with urllib.request.urlopen(urllib.request.Request(
                "https://www.cftc.gov/files/dea/history/fut_fin_txt_2018.zip", headers=UA, method="HEAD"), timeout=30) as r:
            out["CFTC"] = {"status": r.status}
    except Exception as exc:  # noqa: BLE001
        out["CFTC"] = {"error": f"{type(exc).__name__}: {exc}"[:200]}
    print("CFTC", out["CFTC"])
    (ROOT / "research" / "results" / "rc-probe.json").write_text(json.dumps(out, indent=1, sort_keys=True) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
