"""CR-4 probe (metadata only): is the Hyperliquid info API reachable, which perpetuals it lists, and when each one's
funding history and daily candles begin. Only the FIRST funding record's time and the first daily candle's time
are kept per coin: no rate or price is summarised.

    python scripts/cr_probe_hl.py OUT.json
"""

from __future__ import annotations

import json
import sys
import time
import urllib.request

API = "https://api.hyperliquid.xyz/info"


def post(body: dict):
    err = None
    for k in range(5):
        try:
            req = urllib.request.Request(API, data=json.dumps(body).encode(), headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=60) as r:
                return json.loads(r.read())
        except Exception as exc:  # noqa: BLE001
            err = exc
            time.sleep(2 * 2 ** k)
    raise RuntimeError(f"{body}: {err}")


def main(out: str) -> int:
    meta = post({"type": "meta"})
    names = [u["name"] for u in meta["universe"]]
    delisted = [u["name"] for u in meta["universe"] if u.get("isDelisted")]
    res = {"n_perps": len(names), "delisted_flagged": delisted, "coins": {}}
    for n in names:
        f = post({"type": "fundingHistory", "coin": n, "startTime": 0})
        c = post({"type": "candleSnapshot", "req": {"coin": n, "interval": "1d", "startTime": 0,
                                                     "endTime": int(time.time() * 1000)}})
        res["coins"][n] = {"first_funding_ms": f[0]["time"] if f else None, "funding_page": len(f),
                           "first_candle_ms": c[0]["t"] if c else None, "n_daily_candles": len(c)}
        time.sleep(0.3)
    json.dump(res, open(out, "w"), indent=1)
    print(json.dumps({"n_perps": len(names), "with_funding": sum(1 for v in res["coins"].values()
                                                                   if v["first_funding_ms"])}, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1]))
