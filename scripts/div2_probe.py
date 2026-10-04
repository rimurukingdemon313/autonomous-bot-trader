"""Availability probe for DIV-2 candidates: first date, last date and row count only (no prices,
no returns). Yahoo chart API for index levels; FRED graph CSV (no key) for FX, rates, commodities."""

import json
import socket
import urllib.request

socket.setdefaulttimeout(20)

UA = {"User-Agent": "Mozilla/5.0 (research; aitrader DIV-2 probe)"}
YAHOO = ["^GSPC", "^IXIC", "^N225", "^FTSE", "^GDAXI", "^HSI", "^GSPTSE", "^FCHI", "^AXJO", "^SSMI", "^STOXX50E",
         "GC=F", "CL=F", "SI=F", "HG=F", "ZN=F", "ZB=F"]
FRED = ["DEXJPUS", "DEXUSUK", "DEXSZUS", "DEXCAUS", "DEXUSAL", "DEXUSNZ", "DEXUSEU", "DEXGEUS", "DGS10", "DGS2",
        "DTB3", "DCOILWTICO", "DCOILBRENTEU", "GOLDAMGBD228NLBM", "DHHNGSP", "IRLTLT01DEM156N", "IRLTLT01JPM156N"]


def yahoo(sym):
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{sym}?period1=0&period2=1800000000&interval=1d"
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=30) as r:
        res = json.loads(r.read())["chart"]["result"][0]
    ts = [t for t, c in zip(res["timestamp"], res["indicators"]["quote"][0]["close"]) if c is not None]
    import datetime as dt
    f = lambda t: dt.datetime.utcfromtimestamp(t).date().isoformat()  # noqa: E731
    return f(ts[0]), f(ts[-1]), len(ts)


def fred(sid):
    url = f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={sid}"
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60) as r:
        rows = [l.split(",") for l in r.read().decode().splitlines()[1:]]
    rows = [x for x in rows if len(x) == 2 and x[1] not in (".", "")]
    return rows[0][0], rows[-1][0], len(rows)


out = {}
for kind, items, fn in (("yahoo", YAHOO, yahoo), ("fred", FRED, fred)):
    for s in items:
        try:
            out[s] = fn(s)
        except Exception as e:
            out[s] = f"ERROR {type(e).__name__}: {e}"[:120]
        print(s, out[s], flush=True)
        open("research/results/DIV-2-probe.json", "w").write(json.dumps(out, indent=1) + "\n")  # partial results kept
