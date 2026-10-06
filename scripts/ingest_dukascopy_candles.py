"""Ingest Dukascopy minute BID and ASK candles (the datafeed, not the FX-Data tick mirror) into bid/ask bars.

Research tooling for instruments the FX-Data mirror does not carry (index CFDs, commodities). It runs on
CI runners: this container cannot reach the datafeed.

Rules, as for the tick ingestion (data/README.md):

- nothing is invented: a minute with no quotes on either side is dropped, not filled; a day that cannot
  be fetched after its retries is recorded in the manifest as failed, never interpolated;
- the price scale is derived: exactly one power of ten must put the median inside the declared band;
- requests are paced and retried with exponential backoff, because the datafeed answers bursts with 503;
- `ticks` counts minutes that had quotes (an activity proxy). It is not traded volume.

Usage:
    python scripts/ingest_dukascopy_candles.py --symbol USA500IDXUSD --band 500,9000 --years 2012-2016 \
        --timeframe M5 --out out
"""

from __future__ import annotations

import argparse
import json
import lzma
import struct
import sys
import time
import urllib.error
import urllib.request
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from aitrader.data.bars import PERIOD_SECONDS, BarSeries  # noqa: E402

URL = "https://datafeed.dukascopy.com/datafeed/{sym}/{y}/{m:02d}/{d:02d}/{side}_candles_min_1.bi5"
URL_HOUR = "https://datafeed.dukascopy.com/datafeed/{sym}/{y}/{m:02d}/{side}_candles_hour_1.bi5"
URL_DAY = "https://datafeed.dukascopy.com/datafeed/{sym}/{y}/{side}_candles_day_1.bi5"
UA = {"User-Agent": "Mozilla/5.0 (research; aitrader candle ingest)"}
SOURCE = "dukascopy-datafeed-candles"


def fetch(sym: str, d: date, side: str, tries: int = 7, pace: float = 1.0, hourly: bool = False,
          daily: bool = False) -> np.ndarray | None:
    """Decoded records (offset_s, open, close, low, high, volume) of one day's minute candles, or of one
    MONTH's hour candles (`hourly`, offsets from the month start), or None if the fetch failed. An empty
    file (no quotes) is an empty array, not a failure."""
    url = (URL_DAY.format(sym=sym, y=d.year, side=side) if daily
           else URL_HOUR.format(sym=sym, y=d.year, m=d.month - 1, side=side) if hourly
           else URL.format(sym=sym, y=d.year, m=d.month - 1, d=d.day, side=side))
    for k in range(tries):
        time.sleep(pace)
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=40) as r:
                raw = r.read()
            if not raw:
                return np.zeros((0, 6))
            data = lzma.decompress(raw)
            n = len(data) // 24
            return np.array([struct.unpack(">5if", data[i * 24:(i + 1) * 24]) for i in range(n)], dtype=float)
        except urllib.error.HTTPError as exc:
            if exc.code == 404:
                return np.zeros((0, 6))
        except Exception:  # noqa: BLE001 - retried, then recorded as a failed day
            pass
        time.sleep(min(90, 4 * 2 ** k))
    return None


def day_minutes(sym: str, d: date, pace: float) -> tuple[np.ndarray | None, str]:
    """Rows (epoch, bid o,h,l,c, ask o,h,l,c) for minutes quoted on both sides."""
    bid = fetch(sym, d, "BID", pace=pace)
    ask = fetch(sym, d, "ASK", pace=pace)
    if bid is None or ask is None:
        return None, "failed"
    if not len(bid) or not len(ask):
        return np.zeros((0, 9)), "empty"
    base = int(datetime(d.year, d.month, d.day, tzinfo=timezone.utc).timestamp())
    b = {int(r[0]): r for r in bid if r[5] > 0}
    a = {int(r[0]): r for r in ask if r[5] > 0}
    keys = sorted(set(b) & set(a))
    rows = [(base + k, b[k][1], b[k][4], b[k][3], b[k][2], a[k][1], a[k][4], a[k][3], a[k][2]) for k in keys]
    return np.array(rows, dtype=float).reshape(-1, 9), "ok"


def month_hours(sym: str, d: date, pace: float, daily: bool = False) -> tuple[np.ndarray | None, str]:
    """Rows (epoch, bid o,h,l,c, ask o,h,l,c) for the hours of d's month (or, `daily`, the days of d's
    year) quoted on both sides."""
    bid = fetch(sym, d, "BID", pace=pace, hourly=not daily, daily=daily)
    ask = fetch(sym, d, "ASK", pace=pace, hourly=not daily, daily=daily)
    if bid is None or ask is None:
        return None, "failed"
    if not len(bid) or not len(ask):
        return np.zeros((0, 9)), "empty"
    base = int(datetime(d.year, 1 if daily else d.month, 1, tzinfo=timezone.utc).timestamp())
    b = {int(r[0]): r for r in bid if r[5] > 0}
    a = {int(r[0]): r for r in ask if r[5] > 0}
    keys = sorted(set(b) & set(a))
    rows = [(base + k, b[k][1], b[k][4], b[k][3], b[k][2], a[k][1], a[k][4], a[k][3], a[k][2]) for k in keys]
    return np.array(rows, dtype=float).reshape(-1, 9), "ok"


def to_bars(m: np.ndarray, period: int) -> dict:
    t = m[:, 0].astype(np.int64)
    bucket = t - t % period
    starts = np.flatnonzero(np.r_[True, bucket[1:] != bucket[:-1]])
    ends = np.r_[starts[1:], len(t)]
    spread = m[:, 8] - m[:, 4]
    cols = {f: [] for f in ("open_time", "bid_open", "bid_high", "bid_low", "bid_close", "ask_open", "ask_high",
                            "ask_low", "ask_close", "ticks", "spread_mean", "spread_max")}
    for s, e in zip(starts, ends):
        cols["open_time"].append(bucket[s])
        cols["bid_open"].append(m[s, 1]); cols["bid_high"].append(m[s:e, 2].max())
        cols["bid_low"].append(m[s:e, 3].min()); cols["bid_close"].append(m[e - 1, 4])
        cols["ask_open"].append(m[s, 5]); cols["ask_high"].append(m[s:e, 6].max())
        cols["ask_low"].append(m[s:e, 7].min()); cols["ask_close"].append(m[e - 1, 8])
        cols["ticks"].append(e - s)
        cols["spread_mean"].append(float(spread[s:e].mean())); cols["spread_max"].append(float(spread[s:e].max()))
    return {k: np.asarray(v) for k, v in cols.items()}


def scale_for(median_raw: float, band: tuple[float, float]) -> float:
    fits = [10.0 ** k for k in range(-6, 7) if band[0] <= median_raw * 10.0 ** k <= band[1]]
    if len(fits) != 1:
        raise ValueError(f"raw median {median_raw:g} fits {len(fits)} scales in band {band}; refusing to guess")
    return fits[0]


def write(args, out: Path, chunks: list, band, period: int, first: int, last: int, ok: int, empty: int,
          failed: list, t0: float, complete: bool) -> None:
    """Write the bars fetched so far and their manifest. Called once a month as a checkpoint (complete=False)
    so a job stopped by its time limit still leaves everything it fetched, and once at the end."""
    m = np.concatenate(chunks)
    if not len(m):
        return
    m = m[np.argsort(m[:, 0], kind="stable")]
    keep = np.r_[True, np.diff(m[:, 0]) > 0]
    m = m[keep]
    scale = scale_for(float(np.median(m[:, 4])), band)
    m[:, 1:] *= scale
    cols = to_bars(m, period)
    series = BarSeries.from_columns(args.symbol, args.timeframe, SOURCE, **cols)
    tag = f"{args.from_date or first}_{args.to_date or last}".replace("-", "")
    path = out / f"{args.symbol}_{args.timeframe}_{tag}.npz"
    digest = series.save(path)
    crossed = int((series.ask_close < series.bid_close).sum())
    manifest = {
        "symbol": args.symbol, "timeframe": args.timeframe, "source": SOURCE, "file": path.name,
        "content_sha256": digest, "bars": len(series), "minutes": int(len(m)), "price_scale": scale,
        "first": datetime.fromtimestamp(int(series.open_time[0]), timezone.utc).isoformat(),
        "last": datetime.fromtimestamp(int(series.open_time[-1]), timezone.utc).isoformat(),
        "units": "years" if args.daily else "months" if args.hourly else "days", "days_ok": ok,
        "days_empty": empty, "failed_days": failed, "crossed_bars": crossed, "complete": complete,
        "duplicate_minutes_dropped": int((~keep).sum()), "seconds": round(time.time() - t0, 1),
    }
    (out / f"manifest_{args.symbol}_{args.timeframe}_{tag}.json").write_text(json.dumps(manifest, indent=1))
    if complete:
        print(json.dumps({k: v for k, v in manifest.items() if k != "failed_days"} | {"failed": len(failed)}),
              flush=True)


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--symbol", required=True)
    p.add_argument("--band", required=True, help="plausible price band lo,hi used to derive the scale")
    p.add_argument("--years", required=True, help="first-last, inclusive")
    p.add_argument("--from-date", default="", help="optional first day (YYYY-MM-DD), minute mode only")
    p.add_argument("--to-date", default="", help="optional last day (YYYY-MM-DD), minute mode only")
    p.add_argument("--timeframe", default="M5", choices=sorted(PERIOD_SECONDS))
    p.add_argument("--out", required=True)
    p.add_argument("--pace", type=float, default=1.0)
    p.add_argument("--hourly", action="store_true", help="monthly hour-candle files (timeframe becomes H1)")
    p.add_argument("--daily", action="store_true", help="yearly day-candle files (timeframe becomes D1)")
    args = p.parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    first, last = (int(x) for x in args.years.split("-"))
    band = tuple(float(x) for x in args.band.split(","))
    if args.hourly:
        args.timeframe = "H1"
    if args.daily:
        args.timeframe = "D1"
    period = PERIOD_SECONDS[args.timeframe]
    t0 = time.time()
    chunks, failed, empty, ok = [], [], 0, 0
    d = date(first, 1, 1)
    while (args.hourly or args.daily) and d <= date(last, 12, 31):
        rows, status = month_hours(args.symbol, d, args.pace, daily=args.daily)
        if status == "failed":
            failed.append(str(d))
        elif status == "empty":
            empty += 1
        elif not len(rows):
            empty += 1
        else:
            ok += 1
            chunks.append(rows)
        print(f"{args.symbol} {d}: {status}, {time.time() - t0:.0f}s", flush=True)
        d = date(d.year + 1, 1, 1) if args.daily else date(d.year + (d.month == 12), d.month % 12 + 1, 1)
    stop_day = date.fromisoformat(args.to_date) if args.to_date else date(last, 12, 31)
    if args.from_date and not (args.hourly or args.daily):
        d = date.fromisoformat(args.from_date)
    while not (args.hourly or args.daily) and d <= stop_day:
        if d.weekday() != 5:  # Saturday has no quotes
            rows, status = day_minutes(args.symbol, d, args.pace)
            if status == "failed":
                failed.append(str(d))
            elif status == "empty":
                empty += 1
            elif not len(rows):  # quoted but never traded (a market holiday): empty, not data
                empty += 1
            else:
                ok += 1
                chunks.append(rows)
        if d.day == 1 and chunks:
            write(args, out, chunks, band, period, first, last, ok, empty, failed, t0, complete=False)
        if d.day == 1:
            print(f"{args.symbol} {d}: ok {ok}, empty {empty}, failed {len(failed)}, {time.time() - t0:.0f}s", flush=True)
        d += timedelta(days=1)
    if not chunks:
        print("no data", flush=True)
        (out / f"manifest_{args.symbol}.json").write_text(json.dumps(
            {"symbol": args.symbol, "error": "no data", "failed_days": failed, "empty_days": empty}, indent=1))
        return 1
    write(args, out, chunks, band, period, first, last, ok, empty, failed, t0, complete=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
