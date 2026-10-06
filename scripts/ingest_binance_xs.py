"""CR-3 data: every USDT-M perpetual with a matching spot pair (research/results/cr-probe2.json), 1h spot and
perpetual klines and funding, each month verified against its .CHECKSUM, from the coin's first archived month to
2024-12 at the latest (2025 onward is CR-3's sealed holdout).

    python scripts/ingest_binance_xs.py --probe research/results/cr-probe2.json --shard 0 --nshards 20 --out out

Reuses scripts/ingest_binance.py's fetch and parse (unchanged). Writes <out>/<PERP>.npz and manifest_<PERP>.json;
a perpetual quoted per 1000 units uses its plain spot pair (returns, not price levels, are used).
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import time
from pathlib import Path

import numpy as np

_s = importlib.util.spec_from_file_location("ib", Path(__file__).resolve().parent / "ingest_binance.py")
IB = importlib.util.module_from_spec(_s)
_s.loader.exec_module(IB)

LAST = "2024-12"
FIRST = "2020-01"


def fetch_kind(path_fmt: str, sym: str, months: list[str], man: dict) -> list[list[str]]:
    rows = []
    for m in months:
        path = path_fmt.format(s=sym, m=m)
        data = IB.get(f"{IB.BASE}/{path}")
        if data is None:
            man["failed"].append(path)
            continue
        chk = IB.get(f"{IB.BASE}/{path}.CHECKSUM")
        if chk is not None and chk.decode().split()[0] != hashlib.sha256(data).hexdigest():
            man["checksum_mismatch"].append(path)
            continue
        man["files"] += 1
        rows += IB.rows(data)
        time.sleep(0.1)
    return rows


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--probe", required=True)
    p.add_argument("--shard", type=int, required=True)
    p.add_argument("--nshards", type=int, required=True)
    p.add_argument("--out", required=True)
    a = p.parse_args()
    probe = json.load(open(a.probe))
    syms = sorted(s for s, v in probe.items() if v["perp_1h"] and v["spot_1h"] and v["funding"]
                  and max(v["perp_1h"]["first"], v["spot_1h"]["first"]) <= LAST)
    mine = [s for i, s in enumerate(syms) if i % a.nshards == a.shard]
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    for s in mine:
        v = probe[s]
        man = {"perp": s, "spot": v["spot"], "files": 0, "failed": [], "checksum_mismatch": []}
        rng = lambda d: IB.months(max(FIRST, d["first"]), min(LAST, d["last"]))  # noqa: E731
        spot = fetch_kind(IB.KINDS["spot"], v["spot"], rng(v["spot_1h"]), man)
        perp = fetch_kind(IB.KINDS["perp"], s, rng(v["perp_1h"]), man)
        fund = fetch_kind(IB.KINDS["fund"], s, rng(v["funding"]), man)
        arrays = {}
        for k, rows, col in (("spot", spot, 1), ("perp", perp, 1), ("fund", fund, 2)):
            t = np.array([IB.to_s(r[0]) for r in rows], np.int64)
            x = np.array([float(r[col]) for r in rows], float)
            o = np.argsort(t, kind="stable")
            t, x = t[o], x[o]
            keep = np.r_[True, np.diff(t) > 0] if len(t) else np.array([], bool)
            arrays[f"{k}_t"] = t[keep]
            arrays["fund_r" if k == "fund" else f"{k}_o"] = x[keep]
            man[f"{k}_rows"] = int(keep.sum())
        if min(man["spot_rows"], man["perp_rows"], man["fund_rows"]) == 0:
            man["skipped"] = "a leg has no rows in range"
        else:
            np.savez_compressed(out / f"{s}.npz", **arrays)
        (out / f"manifest_{s}.json").write_text(json.dumps(man, indent=1) + "\n")
        print(s, man["files"], len(man["failed"]), len(man["checksum_mismatch"]), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
