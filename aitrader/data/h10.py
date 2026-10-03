"""Federal Reserve H.10 daily exchange rates (noon buying rates in New York), point in time.

Provenance chain (docs/H10_DATA_AUDIT.md):

    Board of Governors of the Federal Reserve System, statistical release H.10
      -> FRED (Federal Reserve Bank of St. Louis) daily series DEXUSEU, DEXUSUK, DEXUSAL, DEXUSNZ,
         DEXJPUS, DEXSZUS, DEXCAUS (category 158, "Daily Rates")
      -> github.com/datasets/exchange-rates (datahub "core" dataset), regenerated from FRED by a script

FRED, ALFRED and federalreserve.gov are refused by this environment's network policy, so the
mirror is the only reachable copy. It is used at PINNED commits only (immutable raw URLs), and
its transformation is undone and verified:

- the mirror stores every currency as units per USD, so it INVERTS the four FRED series quoted as
  USD per unit (EUR, GBP, AUD, NZD). The 2018-10-17 vintage stored the inverse at full float
  precision (`str(1 / float(value))`), so the official 4-decimal FRED value is recovered EXACTLY as
  1 / value -- and every recovered value is checked to sit on the 4-decimal grid. Later vintages
  round the inverse to 4 decimals (`round(1 / value, 4)`), which loses the official value: they are
  used only to check for revisions, never as the primary series;
- JPY, CHF and CAD are FRED's own values, unchanged.

A value FRED shows on a day without a noon rate (e.g. three US holidays in 2007) is the previous
day's value carried forward, not an observation: it is dropped.

Values are returned in FRED's (= the pair's market) quote convention: EURUSD, GBPUSD, AUDUSD,
NZDUSD in USD per unit; USDJPY, USDCHF, USDCAD in units per USD.

Point in time: the rate is a market rate sampled at noon New York. The certified figure's own
publication time cannot be verified from here, so a date's rate is used only from 17:00 New York
on the NEXT business day (a weekday that is not a Federal Reserve holiday). Holidays are missing
values, never filled. The holdout is enforced in the loader, like every other store.
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

import numpy as np

H10_VERSION = "h10-1.0.0"
NY = ZoneInfo("America/New_York")
MIRROR_URL = "https://raw.githubusercontent.com/datasets/exchange-rates/{commit}/data/daily.csv"
#: currency -> (mirror country name, FRED series, inverted by the mirror, market pair, decimals)
SERIES = {
    "EUR": ("Euro", "DEXUSEU", True, "EURUSD", 4),
    "GBP": ("United Kingdom", "DEXUSUK", True, "GBPUSD", 4),
    "AUD": ("Australia", "DEXUSAL", True, "AUDUSD", 4),
    "NZD": ("New Zealand", "DEXUSNZ", True, "NZDUSD", 4),
    "JPY": ("Japan", "DEXJPUS", False, "USDJPY", 2),
    "CHF": ("Switzerland", "DEXSZUS", False, "USDCHF", 4),
    "CAD": ("Canada", "DEXCAUS", False, "USDCAD", 4),
}
#: pinned vintages of the mirror's data/daily.csv: name -> (commit, how values are stored)
VINTAGES = {
    "2017-12-08": ("4eb22d3e74d92fa1b37f98854fcaab3feccad055", "rounded"),
    "2018-10-17": ("8a6dec28a0affdf7eaf455a43be8db862fd9aa09", "full"),
    "2026-09-29": ("0947c2304370a5a4dd8db74cdacb8486e7d85cbe", "rounded"),
}
PRIMARY = "2018-10-17"
GRID_TOL = 1e-6  # a recovered value must be within this many grid units of the published decimal grid


class H10Error(ValueError):
    pass


def vintage_file(name: str) -> str:
    return f"daily_{name}_{VINTAGES[name][0][:7]}.csv"


def parse_mirror(raw: bytes) -> dict[str, dict[date, str]]:
    """Each currency's raw mirror strings by date ('' = no rate that day). Reads the three formats the
    mirror has used: wide (`Data,<country>,...`), long `Date,Country,Value` and long
    `Date,Country,Exchange rate`. A duplicate (currency, date) is refused."""
    text = raw.decode("utf-8")
    rd = csv.reader(io.StringIO(text, newline=""))
    header = [h.strip() for h in next(rd)]
    by_country = {v[0]: k for k, v in SERIES.items()}
    out: dict[str, dict[date, str]] = {k: {} for k in SERIES}

    def put(ccy: str, ds: str, val: str) -> None:
        d = date.fromisoformat(ds.strip())
        if d in out[ccy]:
            raise H10Error(f"duplicate {ccy} observation on {d}")
        v = val.strip()
        out[ccy][d] = "" if v in ("", ".") else v  # FRED marks a day without a rate with "."

    if header[0] in ("Data", "Date") and "Country" not in header:  # wide
        cols = {i: by_country[h] for i, h in enumerate(header) if h in by_country}
        for row in rd:
            if not row:
                continue
            for i, ccy in cols.items():
                put(ccy, row[0], row[i] if i < len(row) else "")
    elif header[:2] == ["Date", "Country"] and len(header) == 3:
        for row in rd:
            if row and row[1].strip() in by_country:
                put(by_country[row[1].strip()], row[0], row[2] if len(row) > 2 else "")
    else:
        raise H10Error(f"unknown mirror format {header[:3]}")
    return out


def official_value(raw: str, ccy: str) -> float | None:
    """The FRED value in its own (market pair) quote convention, from a mirror string."""
    if raw == "":
        return None
    x = float(raw)
    if not np.isfinite(x) or x <= 0:
        raise H10Error(f"{ccy}: non-positive or non-finite value {raw!r}")
    return 1.0 / x if SERIES[ccy][2] else x


def on_grid(x: float, decimals: int) -> bool:
    """Whether `x` is a published decimal value (e.g. 1.5778), up to floating-point noise."""
    s = x * 10 ** decimals
    return abs(s - round(s)) < GRID_TOL


#: days H.10 has no noon rate besides the holiday calendar, verified against the data (docs/H10_DATA_AUDIT.md)
SPECIAL_CLOSURES = (date(2001, 9, 11), date(2014, 12, 26))  # the 9/11 attacks; federal closure by executive order
#: before this date H.10 HAD a rate on the Friday before a Saturday holiday (last seen 2009-07-03); from it, none
#: (first seen 2010-12-24). Any cutover between those two dates gives the same calendar on the data
SATURDAY_RULE_FROM = date(2010, 1, 1)


def fed_holidays(year: int) -> set[date]:
    """Weekdays of `year` on which H.10 has no noon rate: Federal Reserve holidays (a Sunday holiday moves
    to Monday; a Saturday holiday moves to Friday from 2010 only, as observed), Juneteenth from 2021,
    and the special closures."""

    def nth(y: int, month: int, weekday: int, n: int) -> date:
        d = date(y, month, 1)
        d += timedelta(days=(weekday - d.weekday()) % 7)
        return d + timedelta(weeks=n - 1)

    def last(y: int, month: int, weekday: int) -> date:
        d = date(y, month + 1, 1) - timedelta(days=1)
        return d - timedelta(days=(d.weekday() - weekday) % 7)

    out = {nth(year, 1, 0, 3), nth(year, 2, 0, 3), last(year, 5, 0), nth(year, 9, 0, 1), nth(year, 10, 0, 2),
           nth(year, 11, 3, 4)}
    fixed = [date(year, 1, 1), date(year, 7, 4), date(year, 11, 11), date(year, 12, 25), date(year + 1, 1, 1)]
    if year >= 2021:
        fixed.append(date(year, 6, 19))
    for d in fixed:
        if d.weekday() == 6:
            obs = d + timedelta(days=1)
        elif d.weekday() == 5:
            obs = d - timedelta(days=1) if d - timedelta(days=1) >= SATURDAY_RULE_FROM else None
        else:
            obs = d
        if obs is not None and obs.year == year:
            out.add(obs)
    out |= {d for d in SPECIAL_CLOSURES if d.year == year}
    return out


def next_business_day(d: date) -> date:
    n = d + timedelta(days=1)
    while n.weekday() >= 5 or n in fed_holidays(n.year):
        n += timedelta(days=1)
    return n


def available_at(d: date) -> int:
    """UTC epoch seconds from which the rate dated `d` may be used: 17:00 New York, next business day."""
    n = next_business_day(d)
    return int(datetime(n.year, n.month, n.day, 17, tzinfo=NY).timestamp())


@dataclass(frozen=True)
class H10Series:
    currency: str
    fred_id: str
    pair: str
    dates: tuple  # observation dates with a rate, ascending
    value: np.ndarray  # FRED value, market pair quote
    available_at: np.ndarray  # epoch seconds

    def truncated(self, t: int) -> "H10Series":
        keep = self.available_at <= t
        return H10Series(self.currency, self.fred_id, self.pair, tuple(d for d, k in zip(self.dates, keep) if k),
                         self.value[keep], self.available_at[keep])


def official_series(raw: bytes, require_grid: bool = True) -> dict[str, H10Series]:
    """The seven official series from a FULL-precision vintage. Any recovered value off the published
    decimal grid is refused: it would mean the vintage is rounded or the file is not what it claims."""
    parsed = parse_mirror(raw)
    out = {}
    for ccy, by_date in parsed.items():
        _, fred, _, pair, dec = SERIES[ccy]
        ds, vs = [], []
        for d in sorted(by_date):
            v = official_value(by_date[d], ccy)
            if v is None or d in fed_holidays(d.year):
                continue  # no noon rate that day; a value on a no-rate day is a carried-forward copy
            if require_grid and not on_grid(v, dec):
                raise H10Error(f"{ccy} {d}: recovered {v!r} is not a {dec}-decimal FRED value; refusing")
            ds.append(d)
            vs.append(round(v, dec))
        out[ccy] = H10Series(ccy, fred, pair, tuple(ds), np.asarray(vs, float),
                             np.asarray([available_at(d) for d in ds], np.int64))
    return out


class H10Store:
    """The primary vintage from data/h10/, verified against data/h10/manifest.json, holdout-truncated."""

    def __init__(self, root: Path | str, holdout=None) -> None:
        self.root = Path(root)
        mf = self.root / "manifest.json"
        self.manifest = json.loads(mf.read_text()) if mf.exists() else {}
        self.holdout = holdout

    def load(self, key=None) -> dict[str, H10Series]:
        fname = vintage_file(PRIMARY)
        raw = (self.root / fname).read_bytes()
        want = self.manifest.get("files", {}).get(fname, {}).get("sha256")
        if want is None or hashlib.sha256(raw).hexdigest() != want:
            raise H10Error(f"{fname}: does not match data/h10/manifest.json; refusing unverified data")
        out = official_series(raw)
        if self.holdout is not None and key is None:
            h = self.holdout.start
            seal = int(datetime(h.year, h.month, h.day, tzinfo=timezone.utc).timestamp())
            out = {k: v.truncated(seal - 1) for k, v in out.items()}
        return out


__all__ = ["H10Error", "H10Series", "H10Store", "H10_VERSION", "MIRROR_URL", "PRIMARY", "SERIES", "VINTAGES",
           "SATURDAY_RULE_FROM", "SPECIAL_CLOSURES", "available_at", "fed_holidays", "next_business_day", "official_series", "official_value", "on_grid",
           "parse_mirror", "vintage_file"]
