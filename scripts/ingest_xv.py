"""CR-4 data: every Hyperliquid perpetual that also trades as a Binance USDT-M perpetual, from listing to
2025-06-30 (CR-4's holdout, 2025-07 onward, is not fetched).

    python scripts/ingest_xv.py --shard 0 --nshards 8 --out out

Hyperliquid: info API (fundingHistory paged from the listing; daily candleSnapshot). Binance: monthly archives of
funding and 1d perpetual klines, each verified against its .CHECKSUM. Name mapping: X -> XUSDT, else 1000XUSDT;
Hyperliquid's k-prefixed coins (kPEPE = 1000 PEPE) -> 1000XUSDT. Writes <out>/<COIN>.npz and a manifest.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

_s = importlib.util.spec_from_file_location("ib", Path(__file__).resolve().parent / "ingest_binance.py")
IB = importlib.util.module_from_spec(_s)
_s.loader.exec_module(IB)

API = "https://api.hyperliquid.xyz/info"
END_MS = int(datetime(2025, 7, 1, tzinfo=timezone.utc).timestamp() * 1000)
FIRST, LAST = "2023-05", "2025-06"
ROOT = Path(__file__).resolve().parent.parent


def post(body: dict):
    err = None
    for k in range(6):
        try:
            req = urllib.request.Request(API, data=json.dumps(body).encode(), headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=60) as r:
                return json.loads(r.read())
        except Exception as exc:  # noqa: BLE001
            err = exc
            time.sleep(2 * 2 ** k)
    raise RuntimeError(f"{body}: {err}")


def binance_name(hl: str, perps: set[str]) -> str | None:
    if hl.startswith("k") and hl[1:].isupper():
        n = f"1000{hl[1:]}USDT"
        return n if n in perps else None
    for n in (f"{hl}USDT", f"1000{hl}USDT"):
        if n in perps:
            return n
    return None


def hl_funding(coin: str, start_ms: int) -> tuple[list[int], list[float]]:
    t, r = [], []
    s = start_ms
    while s < END_MS:
        page = post({"type": "fundingHistory", "coin": coin, "startTime": s, "endTime": END_MS - 1})
        if not page:
            break
        for x in page:
            if x["time"] < END_MS:
                t.append(int(x["time"]) // 1000)
                r.append(float(x["fundingRate"]))
        nxt = int(page[-1]["time"]) + 1
        if nxt <= s or len(page) < 2:
            break
        s = nxt
        time.sleep(0.25)
    return t, r


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--shard", type=int, required=True)
    p.add_argument("--nshards", type=int, required=True)
    p.add_argument("--out", required=True)
    a = p.parse_args()
    hl = json.load(open(ROOT / "research" / "results" / "cr-probe-hl.json"))["coins"]
    perps = set(json.load(open(ROOT / "research" / "results" / "cr-probe.json"))["funding"])
    pairs = sorted((c, binance_name(c, perps)) for c in hl if hl[c]["first_funding_ms"]
                   and hl[c]["first_funding_ms"] < END_MS)
    pairs = [(c, b) for c, b in pairs if b]
    mine = [x for i, x in enumerate(pairs) if i % a.nshards == a.shard]
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    for coin, bn in mine:
        man = {"hl": coin, "binance": bn, "bn_files": 0, "bn_failed": [], "bn_checksum_mismatch": []}
        ft, fr = hl_funding(coin, int(hl[coin]["first_funding_ms"]))
        cs = post({"type": "candleSnapshot", "req": {"coin": coin, "interval": "1d",
                                                      "startTime": int(hl[coin]["first_funding_ms"]), "endTime": END_MS - 1}})
        ht = [int(x["t"]) // 1000 for x in cs if int(x["t"]) < END_MS]
        ho = [float(x["o"]) for x in cs if int(x["t"]) < END_MS]
        bt, bo, bft, bfr = [], [], [], []
        for m in IB.months(FIRST, LAST):
            for kind, path in (("k", f"futures/um/monthly/klines/{bn}/1d/{bn}-1d-{m}.zip"),
                               ("f", f"futures/um/monthly/fundingRate/{bn}/{bn}-fundingRate-{m}.zip")):
                data = IB.get(f"{IB.BASE}/{path}")
                if data is None:
                    man["bn_failed"].append(path)
                    continue
                chk = IB.get(f"{IB.BASE}/{path}.CHECKSUM")
                if chk is not None and chk.decode().split()[0] != hashlib.sha256(data).hexdigest():
                    man["bn_checksum_mismatch"].append(path)
                    continue
                man["bn_files"] += 1
                for r in IB.rows(data):
                    if kind == "k":
                        bt.append(IB.to_s(r[0]))
                        bo.append(float(r[1]))
                    else:
                        bft.append(IB.to_s(r[0]))
                        bfr.append(float(r[2]))
                time.sleep(0.1)

        def clean(t, v):
            t, v = np.array(t, np.int64), np.array(v, float)
            o = np.argsort(t, kind="stable")
            t, v = t[o], v[o]
            k = np.r_[True, np.diff(t) > 0] if len(t) else np.array([], bool)
            return t[k], v[k]

        arr = {}
        for name, (t, v) in {"hl": (ht, ho), "bn": (bt, bo), "hl_f": (ft, fr), "bn_f": (bft, bfr)}.items():
            ct, cv = clean(t, v)
            arr[{"hl": "hl_t", "bn": "bn_t", "hl_f": "hl_ft", "bn_f": "bn_ft"}[name]] = ct
            arr[{"hl": "hl_o", "bn": "bn_o", "hl_f": "hl_fr", "bn_f": "bn_fr"}[name]] = cv
            man[f"{name}_rows"] = int(len(ct))
        if min(man["hl_rows"], man["bn_rows"], man["hl_f_rows"], man["bn_f_rows"]) == 0:
            man["skipped"] = "a series has no rows"
        else:
            np.savez_compressed(out / f"{coin}.npz", **arr)
        (out / f"manifest_{coin}.json").write_text(json.dumps(man, indent=1) + "\n")
        print(coin, bn, {k: v for k, v in man.items() if k.endswith("_rows")}, len(man["bn_failed"]), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
