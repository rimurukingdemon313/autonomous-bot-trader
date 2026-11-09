"""LIQ-1 data probe (docs/DISCOVERY_PROGRAM.md, H2): which Binance USDT-M futures open-interest and kline files exist on
data.binance.vision, from when to when, and with what gaps. LIQ-1 is specified only after this.

Dates only. For BTCUSDT and ETHUSDT it reports:
- the daily "metrics" files (open interest every 5 minutes) and the monthly 1h klines: their count, first and last
  dates, and the missing days or months;
- the column names of one metrics file and of one kline file.
No value is read, kept or computed. Run on GitHub's runner (Binance is blocked here): .github/workflows/liq-probe.yml.
"""

from __future__ import annotations

import csv
import io
import json
import re
import urllib.parse
import urllib.request
import zipfile
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "research" / "results" / "LIQ-probe.json"
UA = {"User-Agent": "Mozilla/5.0 (research; aitrader LIQ-1 data probe)"}
LIST = "https://s3-ap-northeast-1.amazonaws.com/data.binance.vision"
FILES = "https://data.binance.vision/"
SYMBOLS = ("BTCUSDT", "ETHUSDT")
PREFIXES = {"metrics_daily": "data/futures/um/daily/metrics/{s}/", "klines_1h_monthly": "data/futures/um/monthly/klines/{s}/1h/"}
STAMP = re.compile(r"(\d{4}-\d{2}(?:-\d{2})?)\.zip$")


def keys_from_listing(xml: str) -> tuple[list[str], bool]:
    """The object keys of one S3 listing page, and whether it was truncated."""
    keys = re.findall(r"<Key>([^<]+)</Key>", xml)
    return keys, "<IsTruncated>true</IsTruncated>" in xml


def stamps(keys: list[str]) -> list[str]:
    """The dates (YYYY-MM-DD) or months (YYYY-MM) of the data files, checksums left out."""
    return sorted({m.group(1) for k in keys for m in [STAMP.search(k)] if m and not k.endswith(".CHECKSUM")})


def gaps(stamps_: list[str]) -> list[str]:
    """The days (or months) between the first and the last with no file."""
    if not stamps_:
        return []
    if len(stamps_[0]) == 10:
        have = {date.fromisoformat(s) for s in stamps_}
        d, end, out = min(have), max(have), []
        while d <= end:
            if d not in have:
                out.append(str(d))
            d += timedelta(days=1)
        return out
    have, (y, m) = set(stamps_), map(int, stamps_[0].split("-"))
    out = []
    while f"{y:04d}-{m:02d}" <= stamps_[-1]:
        if f"{y:04d}-{m:02d}" not in have:
            out.append(f"{y:04d}-{m:02d}")
        y, m = (y + 1, 1) if m == 12 else (y, m + 1)
    return out


def header(raw_zip: bytes) -> list[str]:
    """The first row of the zip's one CSV: its column names (or the first row, when the file has none)."""
    with zipfile.ZipFile(io.BytesIO(raw_zip)) as z:
        with z.open(z.namelist()[0]) as f:
            first = next(csv.reader(io.TextIOWrapper(f, "utf-8")))
    return [c if not re.fullmatch(r"-?[\d.]+", c) else "<a number>" for c in first]


def _get(url: str, timeout: int = 60) -> bytes:
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=timeout) as r:
        return r.read()


def listing(prefix: str) -> list[str]:
    keys, marker = [], ""
    while True:
        q = {"prefix": prefix} | ({"marker": marker} if marker else {})
        page, more = keys_from_listing(_get(f"{LIST}?{urllib.parse.urlencode(q)}").decode())
        keys += page
        if not more or not page:
            return keys
        marker = page[-1]


def main() -> int:
    out = {"probe": "LIQ-1", "run": datetime.now(timezone.utc).isoformat(), "symbols": {},
           "note": "dates and column names only: no value was read, kept or computed"}
    for s in SYMBOLS:
        out["symbols"][s] = {}
        for name, pre in PREFIXES.items():
            entry: dict = {"prefix": pre.format(s=s)}
            try:
                keys = listing(pre.format(s=s))
                st = stamps(keys)
                miss = gaps(st)
                entry |= {"files": len(st), "first": st[0] if st else None, "last": st[-1] if st else None,
                          "missing": len(miss), "missing_list": miss[:60]}
                if st:
                    k = next(k for k in keys if k.endswith(f"{st[-1]}.zip"))
                    entry["columns"] = header(_get(FILES + k))
            except Exception as e:  # noqa: BLE001 - reported, the probe continues
                entry["error"] = f"{type(e).__name__}: {e}"
            out["symbols"][s][name] = entry
            print(s, name, json.dumps({k: v for k, v in entry.items() if k != "missing_list"}), flush=True)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, indent=1, sort_keys=True) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
