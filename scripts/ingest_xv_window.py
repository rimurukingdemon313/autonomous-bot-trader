"""Fetch Hyperliquid + Binance perpetual funding and daily opens for given coins over a window [start, end):
CR-5's holdout data, fetched only after its development passes.

    python scripts/ingest_xv_window.py --coins BTC,ETH --start 2025-07-01 --end 2026-09-29 --out out

Same sources, checksums and formats as scripts/ingest_xv.py (whose functions are reused unchanged).
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

_s = importlib.util.spec_from_file_location("ixv", Path(__file__).resolve().parent / "ingest_xv.py")
IXV = importlib.util.module_from_spec(_s)
_s.loader.exec_module(IXV)
IB = IXV.IB


def ms(s: str) -> int:
    return int(datetime.fromisoformat(s).replace(tzinfo=timezone.utc).timestamp() * 1000)


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--coins", required=True)
    p.add_argument("--start", required=True)
    p.add_argument("--end", required=True)
    p.add_argument("--out", required=True)
    a = p.parse_args()
    s_ms, e_ms = ms(a.start), ms(a.end)
    IXV.END_MS = e_ms
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    first_m, last_m = a.start[:7], datetime.fromtimestamp((e_ms - 1) / 1000, timezone.utc).strftime("%Y-%m")
    for coin in a.coins.split(","):
        bn = f"{coin}USDT"
        man = {"hl": coin, "binance": bn, "window": [a.start, a.end], "bn_files": 0, "bn_failed": [],
               "bn_checksum_mismatch": []}
        ft, fr = IXV.hl_funding(coin, s_ms)
        cs = IXV.post({"type": "candleSnapshot", "req": {"coin": coin, "interval": "1d", "startTime": s_ms,
                                                          "endTime": e_ms - 1}})
        ht = [int(x["t"]) // 1000 for x in cs if s_ms <= int(x["t"]) < e_ms]
        ho = [float(x["o"]) for x in cs if s_ms <= int(x["t"]) < e_ms]
        bt, bo, bft, bfr = [], [], [], []
        for m in IB.months(first_m, last_m):
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
                    t = IB.to_s(r[0])
                    if not (s_ms // 1000 <= t < e_ms // 1000):
                        continue
                    if kind == "k":
                        bt.append(t)
                        bo.append(float(r[1]))
                    else:
                        bft.append(t)
                        bfr.append(float(r[2]))
                time.sleep(0.1)
        arr = {}
        for key_t, key_v, t, v in (("hl_t", "hl_o", ht, ho), ("bn_t", "bn_o", bt, bo), ("hl_ft", "hl_fr", ft, fr),
                                   ("bn_ft", "bn_fr", bft, bfr)):
            t, v = np.array(t, np.int64), np.array(v, float)
            o = np.argsort(t, kind="stable")
            t, v = t[o], v[o]
            k = np.r_[True, np.diff(t) > 0] if len(t) else np.array([], bool)
            arr[key_t], arr[key_v] = t[k], v[k]
            man[f"{key_t}_rows"] = int(k.sum())
        np.savez_compressed(out / f"{coin}.npz", **arr)
        (out / f"manifest_{coin}.json").write_text(json.dumps(man, indent=1) + "\n")
        print(coin, {k: v for k, v in man.items() if k.endswith("_rows")}, man["bn_failed"], flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
