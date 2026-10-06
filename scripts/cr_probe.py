"""CR probe (metadata only): which Binance USDT-M perpetuals have public funding history, from which month,
and the formats of funding, perpetual kline and spot kline files. No price or funding value is summarised:
only names, first/last months and the header plus first row of one 2020-01 file per type.

    python scripts/cr_probe.py OUT.json
"""

from __future__ import annotations

import io
import json
import re
import sys
import time
import urllib.parse
import urllib.request
import zipfile

S3 = "https://s3-ap-northeast-1.amazonaws.com/data.binance.vision"
DATA = "https://data.binance.vision/"
UA = {"User-Agent": "Mozilla/5.0 (research; aitrader cr probe)"}


def get(url: str) -> bytes:
    for k in range(5):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60) as r:
                return r.read()
        except Exception as exc:  # noqa: BLE001
            err = exc
            time.sleep(2 * 2 ** k)
    raise RuntimeError(f"{url}: {err}")


def listing(prefix: str, delimiter: bool = True) -> tuple[list[str], list[str]]:
    keys, prefixes, marker = [], [], ""
    while True:
        url = f"{S3}?prefix={urllib.parse.quote(prefix)}" + ("&delimiter=/" if delimiter else "") + (f"&marker={urllib.parse.quote(marker)}" if marker else "")
        x = get(url).decode()
        keys += re.findall(r"<Key>([^<]+)</Key>", x)
        prefixes += re.findall(r"<Prefix>([^<]+)</Prefix>", x)[1:] if delimiter else []
        if "<IsTruncated>true</IsTruncated>" not in x:
            break
        marker = (keys or prefixes)[-1]
    return keys, prefixes


def head_rows(url: str, n: int = 2) -> list[str]:
    z = zipfile.ZipFile(io.BytesIO(get(url)))
    with z.open(z.namelist()[0]) as f:
        return [f.readline().decode().strip() for _ in range(n)]


def main(out: str) -> int:
    _, syms = listing("data/futures/um/monthly/fundingRate/")
    syms = sorted(p.rstrip("/").split("/")[-1] for p in syms)
    res: dict = {"n_symbols": len(syms), "funding": {}}
    for s in syms:
        if not s.endswith("USDT"):
            continue
        keys, _ = listing(f"data/futures/um/monthly/fundingRate/{s}/", delimiter=False)
        months = sorted(m.group(1) for k in keys if (m := re.search(r"(\d{4}-\d{2})\.zip$", k)))
        if months:
            res["funding"][s] = {"first": months[0], "last": months[-1], "n": len(months)}
    early = sorted(s for s, v in res["funding"].items() if v["first"] <= "2019-12")
    res["usdt_perps_with_funding_before_2020"] = early
    spot = {}
    for s in early:
        keys, _ = listing(f"data/spot/monthly/klines/{s}/1h/", delimiter=False)
        months = sorted(m.group(1) for k in keys if (m := re.search(r"(\d{4}-\d{2})\.zip$", k)))
        spot[s] = {"first": months[0], "last": months[-1], "n": len(months)} if months else None
    res["spot_1h_for_early"] = spot
    res["formats"] = {
        "funding": head_rows(f"{DATA}data/futures/um/monthly/fundingRate/BTCUSDT/BTCUSDT-fundingRate-2020-01.zip"),
        "perp_1h": head_rows(f"{DATA}data/futures/um/monthly/klines/BTCUSDT/1h/BTCUSDT-1h-2020-01.zip"),
        "spot_1h": head_rows(f"{DATA}data/spot/monthly/klines/BTCUSDT/1h/BTCUSDT-1h-2020-01.zip"),
    }
    open(out, "w").write(json.dumps(res, indent=1) + "\n")
    print(json.dumps({k: v for k, v in res.items() if k != "funding"}, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1]))
