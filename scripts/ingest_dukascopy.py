"""Ingest Dukascopy bid/ask ticks (mirrored on GitHub by FX-Data) into M15 bars.

    python scripts/ingest_dukascopy.py --out data/processed --symbols EURUSD,GBPUSD
    python scripts/ingest_dukascopy.py --out data/processed            # everything

Research tooling (needs pandas). Source: https://github.com/FX-Data/FX-Data-<PAIR>-DS,
one branch per year, one CSV per hour: `time, bid, ask, bid_volume, ask_volume`
in UTC. Every branch's commit SHA is written to the manifest, so the exact raw
input of every bar can be fetched again (DATA_CONTRACT.md §1).

Raw ticks are processed one year at a time and deleted: only bars are kept.
"""

from __future__ import annotations

import argparse
import io
import json
import shutil
import subprocess
import sys
import tempfile
import time
from concurrent.futures import ProcessPoolExecutor
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from aitrader.data import instruments  # noqa: E402
from aitrader.data.bars import PERIOD_SECONDS, BarSeries  # noqa: E402
from aitrader.data.ticks import TickAudit, aggregate, week_openings  # noqa: E402
from aitrader.data.validate import validate  # noqa: E402

REPO = "https://github.com/FX-Data/FX-Data-{pair}-DS"
SOURCE = "dukascopy-via-fx-data"


def _run(*cmd: str, cwd: Path | None = None) -> str:
    return subprocess.run(cmd, cwd=cwd, check=True, capture_output=True, text=True).stdout


def available_years(pair: str) -> dict[int, str]:
    """Year -> branch commit SHA, straight from the remote."""
    out = _run("git", "ls-remote", REPO.format(pair=pair))
    years = {}
    for line in out.splitlines():
        sha, ref = line.split("\t")
        prefix = f"refs/heads/{pair}-"
        if ref.startswith(prefix) and ref[len(prefix):].isdigit():
            years[int(ref[len(prefix):])] = sha
    return dict(sorted(years.items()))


def _read_ticks(files: list[Path]):
    import pandas as pd

    buf = io.BytesIO()
    for f in files:
        data = f.read_bytes()
        buf.write(data)
        if data and not data.endswith(b"\n"):
            buf.write(b"\n")
    buf.seek(0)
    df = pd.read_csv(buf, header=None, names=["time", "c1", "c2", "v1", "v2"],
                     dtype={"time": str}, on_bad_lines="skip", engine="c")
    t = pd.to_datetime(df["time"], format="%Y.%m.%d %H:%M:%S.%f", utc=True, errors="coerce")
    ok = t.notna().to_numpy()
    # Explicit unit: pandas 3 may store microseconds, pandas 2 nanoseconds.
    # Dividing a raw int64 by an assumed factor silently compressed a year
    # of ticks into 36 bars the first time this ran.
    t_ms = ((t[ok] - pd.Timestamp(0, tz="UTC")) // pd.Timedelta(milliseconds=1)).to_numpy(dtype="int64")
    return t_ms, df["c1"].to_numpy(float)[ok], df["c2"].to_numpy(float)[ok], int((~ok).sum())


def ingest_year(pair: str, year: int, sha: str, period: int = 900) -> dict:
    tmp = Path(tempfile.mkdtemp(prefix=f"ing-{pair}-{year}-"))
    try:
        _run("git", "init", "-q", "--bare", str(tmp / "g"))
        _run("git", "fetch", "-q", "--depth", "1", REPO.format(pair=pair),
             f"refs/heads/{pair}-{year}:refs/heads/y", cwd=tmp / "g")
        got = _run("git", "rev-parse", "refs/heads/y", cwd=tmp / "g").strip()
        if got != sha:
            raise RuntimeError(f"{pair} {year}: branch moved ({got} != {sha}); re-run to pick up the new SHA")
        archive = subprocess.run(["git", "archive", "refs/heads/y", pair], cwd=tmp / "g",
                                 check=True, capture_output=True).stdout
        (tmp / "x").mkdir()
        subprocess.run(["tar", "-x", "-C", str(tmp / "x")], input=archive, check=True)
        files = sorted((tmp / "x").rglob("*.csv"))
        # One month at a time: a 15-minute bar never straddles a month
        # boundary, so per-month aggregation is exact, and a whole year of
        # ticks in memory at once was enough to be OOM-killed.
        by_month: dict[str, list[Path]] = {}
        for f in files:
            by_month.setdefault(f.parent.name, []).append(f)
        parts, audit, bad_time, orders, open_t = [], TickAudit(), 0, set(), []
        last_t = None
        for month in sorted(by_month):
            t_ms, c1, c2, bad = _read_ticks(by_month[month])
            bad_time += bad
            if not len(t_ms):
                continue
            # Column order is MEASURED, never assumed: bid <= ask on
            # essentially every tick identifies which column is which.
            # 95%, not 99%: a month can hold a few percent of crossed quotes
            # (AUDUSD 2007-07: 2%). Those ticks are dropped and counted by
            # `aggregate`; they do not make the column order ambiguous.
            le = float(np.mean(c1 <= c2))
            if le >= 0.95:
                bid, ask, order = c1, c2, "c1=bid,c2=ask"
            elif le <= 0.05:
                bid, ask, order = c2, c1, "c1=ask,c2=bid"
            else:
                raise RuntimeError(f"{pair} {year}-{month}: cannot tell bid from ask ({le:.3f} have c1<=c2)")
            orders.add(order)
            res = aggregate(t_ms, bid, ask, period)
            audit.add(res.audit)
            parts.append(res.columns)
            srt = np.sort(t_ms)
            if last_t is not None:
                srt = np.concatenate(([last_t], srt))
            open_t.append(week_openings(srt))
            last_t = int(srt[-1])
        if len(orders) > 1:
            raise RuntimeError(f"{pair} {year}: column order changed between months: {orders}")
        columns = {k: np.concatenate([c[k] for c in parts]) for k in parts[0]} if parts else aggregate(
            np.array([], dtype=np.int64), np.array([]), np.array([]), period).columns
        opens = np.concatenate(open_t) if open_t else np.array([], dtype=np.int64)
        return {
            "pair": pair, "year": year, "sha": sha, "files": len(files),
            "bad_timestamps": bad_time, "columns": next(iter(orders), "none"),
            "audit": audit.as_dict(), "columns_data": columns,
            "week_open_hours_utc": [int((o % 86400) // 3600) for o in opens],
            "week_open_weekdays": [int(((o // 86400) + 3) % 7) for o in opens],  # 0=Mon
        }
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def ingest_pair(pair: str, out: Path, timeframe: str = "M15", first: int | None = None, last: int | None = None,
                tag: str = "") -> dict:
    t0 = time.time()
    years = {y: s for y, s in available_years(pair).items()
             if (first is None or y >= first) and (last is None or y <= last)}
    period = PERIOD_SECONDS[timeframe]
    parts, meta, audit = [], [], TickAudit()
    open_hours, open_days = [], []
    for year, sha in years.items():
        r = ingest_year(pair, year, sha, period)
        cols = r.pop("columns_data")
        # A year's branch is authoritative only for bars inside that year:
        # branches overlap at their edges, and taking both copies produced
        # out-of-order timestamps (EURUSD, 4 times).
        lo, hi = int(datetime(year, 1, 1, tzinfo=timezone.utc).timestamp()), int(datetime(year + 1, 1, 1, tzinfo=timezone.utc).timestamp())
        inside = (cols["open_time"] >= lo) & (cols["open_time"] < hi)
        r["bars_outside_year_dropped"] = int((~inside).sum())
        cols = {k: v[inside] for k, v in cols.items()}
        if len(cols["open_time"]):
            parts.append(BarSeries.from_columns(pair, timeframe, SOURCE, **cols))
        a = TickAudit(**r.pop("audit"))
        audit.add(a)
        open_hours += r.pop("week_open_hours_utc")
        open_days += r.pop("week_open_weekdays")
        meta.append({**r, "ticks_kept": a.kept, "ticks_received": a.received})
        print(f"  {pair} {year}: {a.kept:,} ticks, {len(cols['open_time']):,} bars", flush=True)

    series = BarSeries.concat(parts)
    order = np.argsort(series.open_time, kind="stable")
    series = series.take(order)
    # Price scale is derived, never assumed: this source stores JPY pairs and
    # gold divided by 100 (USDJPY 0.772 for 77.2).
    scale = instruments.price_scale(pair, float(np.median(series.mid_close)))
    if scale != 1.0:
        series = BarSeries.from_columns(pair, timeframe, SOURCE, **{
            f: (getattr(series, f) * scale if f not in ("open_time", "ticks") else getattr(series, f))
            for f in ("open_time", "bid_open", "bid_high", "bid_low", "bid_close", "ask_open", "ask_high",
                      "ask_low", "ask_close", "ticks", "spread_mean", "spread_max")})
    # Years are separate branches; an overlap at a boundary would be a
    # duplicate bar. Keep the first occurrence and count the rest.
    keep = np.concatenate(([True], np.diff(series.open_time) > 0))
    dup = int((~keep).sum())
    if dup:
        series = series.take(keep)
    path = out / f"{pair}_{timeframe}{tag}.npz"
    digest = series.save(path)
    report = validate(series, instruments.get(pair))
    hours = {h: open_hours.count(h) for h in sorted(set(open_hours))}
    days = {d: open_days.count(d) for d in sorted(set(open_days))}
    return {
        "symbol": pair, "timeframe": timeframe, "source": SOURCE,
        "source_repo": REPO.format(pair=pair), "years": meta,
        "file": path.name, "content_sha256": digest, "bars": len(series), "price_scale": scale,
        "duplicate_bars_dropped": dup, "tick_audit": audit.as_dict(),
        "week_open_hour_utc_histogram": hours, "week_open_weekday_histogram": days,
        "quality": report.as_dict(), "seconds": round(time.time() - t0, 1),
    }


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--out", default=str(ROOT / "data" / "processed"))
    p.add_argument("--symbols", default=",".join(instruments.UNIVERSE))
    p.add_argument("--workers", type=int, default=3)
    p.add_argument("--timeframe", default="M15", choices=sorted(PERIOD_SECONDS))
    p.add_argument("--years", default="", help="first-last, e.g. 2009-2016 (default: every year the mirror has)")
    p.add_argument("--tag", default="", help="file-name suffix, e.g. _2009_2016")
    p.add_argument("--manifest", default=str(ROOT / "data" / "manifest.json"))
    args = p.parse_args()

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    symbols = [s.strip().upper() for s in args.symbols.split(",") if s.strip()]
    manifest_path = Path(args.manifest)
    manifest = json.loads(manifest_path.read_text()) if manifest_path.exists() else {"datasets": {}}

    with ProcessPoolExecutor(max_workers=args.workers) as pool:
        first, last = (int(x) for x in args.years.split("-")) if args.years else (None, None)
        futures = {s: pool.submit(ingest_pair, s, out, args.timeframe, first, last, args.tag) for s in symbols}
        for s, fut in futures.items():
            try:
                entry = fut.result()
            except Exception as exc:  # recorded, never hidden
                entry = {"symbol": s, "error": f"{type(exc).__name__}: {exc}"}
            manifest["datasets"][s] = entry
            manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True))
            print(f"{s}: {'ERROR ' + entry['error'] if 'error' in entry else str(entry['bars']) + ' bars'}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
