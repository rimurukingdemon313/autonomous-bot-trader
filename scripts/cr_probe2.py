"""CR probe 2 (metadata only): for every USDT-M perpetual with a funding archive, the matching spot pair's 1h kline
archive (first/last month), and the perpetual 1h kline archive (first/last month). Perpetuals quoted per 1000 or
1,000,000 units (1000SHIBUSDT) map to the spot pair without the prefix. No price or funding value is read.

    python scripts/cr_probe2.py research/results/cr-probe.json OUT.json
"""

from __future__ import annotations

import json
import re
import sys
import time
import urllib.parse
import urllib.request

S3 = "https://s3-ap-northeast-1.amazonaws.com/data.binance.vision"
UA = {"User-Agent": "Mozilla/5.0 (research; aitrader cr probe 2)"}


def get(url: str) -> str:
    err = None
    for k in range(5):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60) as r:
                return r.read().decode()
        except Exception as exc:  # noqa: BLE001
            err = exc
            time.sleep(2 * 2 ** k)
    raise RuntimeError(f"{url}: {err}")


def months(prefix: str) -> list[str]:
    keys, marker = [], ""
    while True:
        url = f"{S3}?prefix={urllib.parse.quote(prefix)}" + (f"&marker={urllib.parse.quote(marker)}" if marker else "")
        x = get(url)
        ks = re.findall(r"<Key>([^<]+)</Key>", x)
        keys += ks
        if "<IsTruncated>true</IsTruncated>" not in x or not ks:
            break
        marker = ks[-1]
    return sorted(m.group(1) for k in keys if (m := re.search(r"(\d{4}-\d{2})\.zip$", k)))


def spot_of(perp: str) -> str:
    for p in ("1000000", "1000", "1M"):
        if perp.startswith(p) and perp[len(p):].endswith("USDT"):
            return perp[len(p):]
    return perp


def main(src: str, out: str) -> int:
    funding = json.load(open(src))["funding"]
    res = {}
    for s in sorted(funding):
        if not s.endswith("USDT") or not s.isascii():
            continue
        sp = spot_of(s)
        pm = months(f"data/futures/um/monthly/klines/{s}/1h/")
        sm = months(f"data/spot/monthly/klines/{sp}/1h/")
        res[s] = {"spot": sp, "funding": funding[s],
                  "perp_1h": {"first": pm[0], "last": pm[-1], "n": len(pm)} if pm else None,
                  "spot_1h": {"first": sm[0], "last": sm[-1], "n": len(sm)} if sm else None}
    json.dump(res, open(out, "w"), indent=1)
    both = [s for s, v in res.items() if v["perp_1h"] and v["spot_1h"]]
    print(json.dumps({"usdt_perps": len(res), "with_spot_and_perp_1h": len(both)}, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1], sys.argv[2]))
