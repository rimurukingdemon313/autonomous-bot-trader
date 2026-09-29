"""External explanatory data: macro, rates, risk and commodity series, point in time.

Round 1 searched transformations of the same OHLC bars. This module adds information the bars do
not contain, under three rules:

1. PROVENANCE. Every series names its original publisher, the mirror it was fetched from, the
   licence, and the sha256 of the exact bytes used (`data/external/manifest.json`). Raw files are
   not committed, like the bars; the manifest is.
2. POINT IN TIME. Every observation carries `available_at`: the earliest moment its value was
   public, chosen CONSERVATIVELY from the publisher's release practice (see each source's
   `availability`). A decision at time t sees only observations with available_at <= t.
3. NO REVISION LEAKAGE. Only series that are not revised after release are admitted (or whose
   revisions are immaterial and stated). A revised series would need its real-time vintages,
   which this environment cannot reach; such series are refused, not approximated.

The loader truncates at the sealed holdout exactly like the bar store: nothing dated inside the
holdout is served without its key.

What is NOT here, and why (docs/ROUND2_DATA_AUDIT.md): central-bank policy rates and short-term
interest rates outside the US and the euro area, forward points and historical broker swaps. Their
authoritative sources (FRED, BIS, ECB, central banks) are refused by this environment's network
policy. Nothing is fabricated in their place.
"""

from __future__ import annotations

import calendar
import csv
import hashlib
import io
import json
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

import numpy as np

EXTERNAL_VERSION = "external-1.0.0"
NY = ZoneInfo("America/New_York")
MIRROR = "https://raw.githubusercontent.com/datasets/{repo}/main/data/{file}"


@dataclass(frozen=True)
class Source:
    key: str
    publisher: str
    repo: str
    file: str
    date_col: str
    value_col: str
    frequency: str  # daily | monthly
    availability: str  # the rule, in words (implemented in `available_at`)
    revised: str  # how the publisher revises it, and why that is safe here
    licence: str

    @property
    def url(self) -> str:
        return MIRROR.format(repo=self.repo, file=self.file)


SOURCES: dict[str, Source] = {s.key: s for s in (
    Source("vix", "Cboe Global Markets (VIX index, daily close)", "finance-vix", "vix-daily.csv", "DATE", "CLOSE",
           "daily", "the close of date d is public at 16:15 New York; taken as available at 16:45 New York on d "
           "(before the 17:00 New York close that ends our D1 bar)",
           "not revised", "Cboe public historical data, mirrored by datahub.io core (PDDL)"),
    Source("brent", "U.S. EIA, Europe Brent Spot Price FOB (RBRTE), daily", "oil-prices", "brent-daily.csv", "Date",
           "Price", "daily", "the assessment for date d is taken as available at 17:00 New York on the NEXT "
           "calendar day (one full day of lag: the spot assessment is published after the London close)",
           "EIA spot assessments are not revised in practice", "U.S. government work (public domain), via datahub.io"),
    Source("us10y", "Federal Reserve H.15, 10-year Treasury constant maturity, monthly average", "bond-yields-us-10y",
           "monthly.csv", "Date", "Rate", "monthly",
           "the average for month m is known once m ends; taken as available at 17:00 New York on the 2nd "
           "calendar day of month m+1", "H.15 market yields are not revised", "Federal Reserve (public domain)"),
    Source("cpi_us", "U.S. BLS, CPI-U all items, not seasonally adjusted (1982-84=100)", "cpi-us", "cpiai.csv", "Date",
           "Index", "monthly", "BLS releases month m around the 10th-17th of m+1 (the 2013 shutdown delayed one to "
           "the 30th); taken as available at 17:00 New York on the LAST day of m+1",
           "the NSA index is never revised (only seasonal factors are, and they are not used)",
           "U.S. government work (public domain)"),
    Source("sp500", "S&P 500 monthly average level (R. Shiller's dataset)", "s-and-p-500", "data.csv", "Date", "SP500",
           "monthly", "the average for month m is known once m ends; available at 17:00 New York on the 2nd "
           "calendar day of m+1", "a published index level; not revised", "Shiller's public data via datahub.io"),
)}


def _ny(d: date, hour: int, minute: int = 0) -> int:
    return int(datetime(d.year, d.month, d.day, hour, minute, tzinfo=NY).timestamp())


def _month_after(d: date) -> tuple[int, int]:
    return (d.year + 1, 1) if d.month == 12 else (d.year, d.month + 1)


def available_at(key: str, d: date) -> int:
    """UTC epoch seconds at which the observation dated `d` of source `key` is taken to be public."""
    if key == "vix":
        return _ny(d, 16, 45)
    if key == "brent":
        return _ny(d + timedelta(days=1), 17)
    y, m = _month_after(d)
    if key in ("us10y", "sp500"):
        return _ny(date(y, m, 2), 17)
    if key == "cpi_us":
        return _ny(date(y, m, calendar.monthrange(y, m)[1]), 17)
    raise KeyError(key)


@dataclass(frozen=True)
class ExternalSeries:
    key: str
    obs_date: np.ndarray  # epoch seconds of the observation's own date (00:00 UTC)
    value: np.ndarray
    available_at: np.ndarray  # epoch seconds, non-decreasing

    def asof(self, t: np.ndarray) -> np.ndarray:
        """The latest value public at each time in `t` (NaN before the first)."""
        t = np.asarray(t, np.int64)
        k = np.searchsorted(self.available_at, t, side="right") - 1
        out = np.full(len(t), np.nan)
        ok = k >= 0
        out[ok] = self.value[k[ok]]
        return out

    def asof_lag(self, t: np.ndarray, lag: int) -> np.ndarray:
        """The value `lag` observations before the latest public one at each time (NaN if none)."""
        t = np.asarray(t, np.int64)
        k = np.searchsorted(self.available_at, t, side="right") - 1 - lag
        out = np.full(len(t), np.nan)
        ok = k >= 0
        out[ok] = self.value[k[ok]]
        return out

    def truncated(self, t: int) -> "ExternalSeries":
        keep = self.available_at <= t
        return ExternalSeries(self.key, self.obs_date[keep], self.value[keep], self.available_at[keep])


def parse(key: str, raw: bytes) -> ExternalSeries:
    src = SOURCES[key]
    rows = []
    for r in csv.DictReader(io.StringIO(raw.decode("utf-8"))):
        ds, vs = (r.get(src.date_col) or "").strip(), (r.get(src.value_col) or "").strip()
        if not ds or not vs:
            continue
        try:
            d = date.fromisoformat(ds[:10])
            v = float(vs)
        except ValueError:
            continue
        if not np.isfinite(v) or v <= 0:  # every admitted series is a positive level; 0 marks "missing" upstream
            continue
        rows.append((d, v))
    rows.sort()
    dedup = {}
    for d, v in rows:
        dedup[d] = v  # a repeated date keeps the last row, as published
    ds = sorted(dedup)
    obs = np.array([int(datetime(d.year, d.month, d.day, tzinfo=timezone.utc).timestamp()) for d in ds], np.int64)
    val = np.array([dedup[d] for d in ds], float)
    av = np.array([available_at(key, d) for d in ds], np.int64)
    order = np.argsort(av, kind="stable")
    return ExternalSeries(key, obs[order], val[order], av[order])


class ExternalStore:
    """Reads data/external/<key>.csv, checks it against the manifest, truncates at the holdout."""

    def __init__(self, root: Path | str, holdout=None) -> None:
        self.root = Path(root)
        self.holdout = holdout
        mf = self.root / "manifest.json"
        self.manifest = json.loads(mf.read_text()) if mf.exists() else {}

    def load(self, key: str) -> ExternalSeries:
        raw = (self.root / f"{key}.csv").read_bytes()
        want = self.manifest.get(key, {}).get("sha256")
        if want is None or hashlib.sha256(raw).hexdigest() != want:
            raise ValueError(f"{key}: the file does not match the manifest; refusing unverified data")
        s = parse(key, raw)
        if self.holdout is not None:
            seal = int(datetime(self.holdout.start.year, self.holdout.start.month, self.holdout.start.day,
                                tzinfo=timezone.utc).timestamp())
            s = s.truncated(seal - 1)
        return s


__all__ = ["EXTERNAL_VERSION", "ExternalSeries", "ExternalStore", "SOURCES", "Source", "available_at", "parse"]
