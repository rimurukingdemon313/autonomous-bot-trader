"""Availability probe for index-CFD / commodity intraday research (IX program): which Dukascopy
instruments have minute bid/ask candles, from which year, and at what success rate when requests are
paced. Records only availability metadata: byte counts, record counts, first offset, a decoded price
RANGE of single days (a format and scale check) and timings. No return or statistic is computed."""

from __future__ import annotations

import json
import lzma
import struct
import sys
import time
import urllib.request
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
URL = "https://datafeed.dukascopy.com/datafeed/{sym}/{y}/{m:02d}/{d:02d}/{side}_candles_min_1.bi5"
UA = {"User-Agent": "Mozilla/5.0 (research; aitrader IX probe)"}
SYMS = ["USA500IDXUSD", "USATECHIDXUSD", "USA30IDXUSD", "USSC2000IDXUSD", "DEUIDXEUR", "GBRIDXGBP", "FRAIDXEUR",
        "EUSIDXEUR", "JPNIDXJPY", "HKGIDXHKD", "AUSIDXAUD", "CHEIDXCHF", "ESPIDXEUR", "NLDIDXEUR",
        "BRENTCMDUSD", "LIGHTCMDUSD", "GASCMDUSD", "XAGUSD", "BUNDTREUR", "USTBONDTRUSD", "COPPERCMDUSD"]
PACE_S = 2.0


def get(sym: str, d: date, side: str = "BID", tries: int = 6) -> dict:
    url = URL.format(sym=sym, y=d.year, m=d.month - 1, d=d.day, side=side)
    t0 = time.time()
    last = ""
    for k in range(tries):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=40) as r:
                raw = r.read()
            out = {"bytes": len(raw), "secs": round(time.time() - t0, 2), "attempts": k + 1}
            if raw:
                data = lzma.decompress(raw)
                n = len(data) // 24
                recs = [struct.unpack(">5if", data[i * 24:(i + 1) * 24]) for i in range(n)]
                live = [r for r in recs if r[5] > 0]
                out.update(records=n, with_volume=len(live),
                           price_int_range=[min(r[3] for r in live), max(r[4] for r in live)] if live else None)
            return out
        except urllib.error.HTTPError as exc:
            last = f"HTTP {exc.code}"
            if exc.code == 404:
                return {"error": last, "secs": round(time.time() - t0, 2), "attempts": k + 1}
        except Exception as exc:  # noqa: BLE001
            last = f"{type(exc).__name__}"
        time.sleep(min(60, 5 * 2 ** k))
    return {"error": last, "secs": round(time.time() - t0, 2), "attempts": tries}


def main() -> int:
    res: dict = {}
    for s in SYMS:
        res[s] = {}
        for y in range(2008, 2025):
            d = date(y, 6, 11)
            while d.weekday() != 1:  # a Tuesday
                d += timedelta(days=1)
            res[s][str(d)] = get(s, d)
            time.sleep(PACE_S)
        print(s, {k: ("ok" if "records" in v else v.get("error", "empty")) for k, v in res[s].items()}, flush=True)
    days = [date(2015, 1, 5) + timedelta(days=i) for i in range(60)]
    t0 = time.time()
    out = []
    for d in days:
        out.append(get("USA500IDXUSD", d, "ASK"))
        time.sleep(PACE_S)
    res["throughput_paced"] = {"files": len(days), "secs": round(time.time() - t0, 1),
                               "errors": sum("error" in o for o in out),
                               "attempts_total": sum(o.get("attempts", 0) for o in out)}
    print("throughput", res["throughput_paced"], flush=True)
    (ROOT / "research" / "results" / "ix-probe.json").write_text(json.dumps(res, indent=1) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
