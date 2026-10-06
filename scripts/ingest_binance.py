"""Ingest Binance public archives for the CR programs: 1h spot klines, 1h USDT-M perpetual klines and funding
settlements, monthly files, each verified against its published .CHECKSUM (sha256).

    python scripts/ingest_binance.py --symbols BTCUSDT,ETHUSDT --from 2020-01 --to 2024-12 --out data/cr

Writes <out>/<SYM>.npz (spot_t, spot_o, perp_t, perp_o, fund_t, fund_r) and <out>/manifest_<SYM>.json. A month
that cannot be fetched is recorded as failed, never filled. Kline open times in microseconds (Binance spot from
2025) are converted to seconds.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import time
import urllib.error
import urllib.request
import zipfile
from pathlib import Path

import numpy as np

BASE = "https://data.binance.vision/data"
UA = {"User-Agent": "Mozilla/5.0 (research; aitrader binance ingest)"}
KINDS = {
    "spot": "spot/monthly/klines/{s}/1h/{s}-1h-{m}.zip",
    "perp": "futures/um/monthly/klines/{s}/1h/{s}-1h-{m}.zip",
    "fund": "futures/um/monthly/fundingRate/{s}/{s}-fundingRate-{m}.zip",
}


def get(url: str, tries: int = 6) -> bytes | None:
    for k in range(tries):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60) as r:
                return r.read()
        except urllib.error.HTTPError as exc:
            if exc.code == 404:
                return None
        except Exception:  # noqa: BLE001 - retried, then recorded as failed
            pass
        time.sleep(min(60, 2 * 2 ** k))
    return None


def months(a: str, b: str) -> list[str]:
    y, m = map(int, a.split("-"))
    out = []
    while f"{y:04d}-{m:02d}" <= b:
        out.append(f"{y:04d}-{m:02d}")
        y, m = (y + 1, 1) if m == 12 else (y, m + 1)
    return out


def rows(data: bytes) -> list[list[str]]:
    z = zipfile.ZipFile(io.BytesIO(data))
    with z.open(z.namelist()[0]) as f:
        r = list(csv.reader(io.TextIOWrapper(f)))
    return [x for x in r if x and x[0][:1].isdigit()]  # drop a header row if present


def to_s(v: str) -> int:
    x = int(float(v))
    if x > 10 ** 14:  # microseconds
        return x // 1_000_000
    return x // 1000


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--symbols", required=True)
    p.add_argument("--from", dest="a", required=True)
    p.add_argument("--to", dest="b", required=True)
    p.add_argument("--out", required=True)
    args = p.parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    for s in args.symbols.split(","):
        cols: dict[str, list] = {"spot_t": [], "spot_o": [], "perp_t": [], "perp_o": [], "fund_t": [], "fund_r": []}
        man: dict = {"symbol": s, "from": args.a, "to": args.b, "files": {}, "failed": [], "checksum_mismatch": []}
        for kind, pat in KINDS.items():
            for m in months(args.a, args.b):
                path = pat.format(s=s, m=m)
                data = get(f"{BASE}/{path}")
                if data is None:
                    man["failed"].append(path)
                    continue
                chk = get(f"{BASE}/{path}.CHECKSUM")
                digest = hashlib.sha256(data).hexdigest()
                if chk is not None and chk.decode().split()[0] != digest:
                    man["checksum_mismatch"].append(path)
                    continue
                man["files"][path] = digest
                for r in rows(data):
                    if kind == "fund":
                        cols["fund_t"].append(to_s(r[0]))
                        cols["fund_r"].append(float(r[2]))
                    else:
                        cols[f"{kind}_t"].append(to_s(r[0]))
                        cols[f"{kind}_o"].append(float(r[1]))
                time.sleep(0.2)
        arrays = {}
        for k in ("spot", "perp", "fund"):
            t = np.array(cols[f"{k}_t"], np.int64)
            v = np.array(cols[f"{k}_o" if k != "fund" else "fund_r"], float)
            order = np.argsort(t, kind="stable")
            t, v = t[order], v[order]
            keep = np.r_[True, np.diff(t) > 0]
            man[f"{k}_duplicates_dropped"] = int((~keep).sum())
            arrays[f"{k}_t"], arrays[f"{k}_o" if k != "fund" else "fund_r"] = t[keep], v[keep]
            man[f"{k}_rows"] = int(keep.sum())
        np.savez_compressed(out / f"{s}.npz", **arrays)
        man["npz_sha256"] = hashlib.sha256((out / f"{s}.npz").read_bytes()).hexdigest()
        (out / f"manifest_{s}.json").write_text(json.dumps(man, indent=1) + "\n")
        print(s, {k: v for k, v in man.items() if k not in ("files",)}, flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
