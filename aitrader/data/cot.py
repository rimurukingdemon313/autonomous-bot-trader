"""CFTC Traders in Financial Futures (TFF, Futures-Only), point in time.

Source: the two official CFTC bulk files the user supplied, kept byte-for-byte under data/cot/ and
verified against data/cot/manifest.json (written by scripts/cot_audit.py; docs/COT_DATA_AUDIT.md).
Nothing here is fetched, interpolated or repaired.

Point in time. Positions are as of a Tuesday and normally released the following Friday at 15:30
New York; the file carries no release date. A report is therefore used only from 17:00 New York on
the first weekday on or after as-of + 6 days (the Monday after a normal release, which also covers
the one-business-day holiday delays). Reports whose release was disrupted by the October 2013 US
government shutdown (as-of 2013-10-01 to 2013-12-24) have no verifiable release date: they are
dropped entirely, never given a guessed date and never used as history.

The holdout is enforced in the loader like the bar store: a report that becomes available on or
after the holdout start is not served without the holdout key.
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
import zipfile
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

import numpy as np

COT_VERSION = "cot-1.0.0"
NY = ZoneInfo("America/New_York")
FILES = {"fin_fut_txt_2006_2016.zip": "F_TFF_2006_2016.txt", "fut_fin_txt_2017.zip": "FinFutYY.txt"}
#: the seven currency futures of the universe's direct USD pairs (CME), by CFTC contract code
CONTRACTS = {"099741": "EUR", "097741": "JPY", "096742": "GBP", "092741": "CHF", "090741": "CAD", "232741": "AUD",
             "112741": "NZD"}
LAG_DAYS = 6
AVAILABLE_HOUR = 17
UNAVAILABLE = (date(2013, 10, 1), date(2013, 12, 24))
#: TFF columns read (all positions in contracts); spreads are not part of a category's net position
FIELDS = {
    "oi": "Open_Interest_All",
    "dealer_long": "Dealer_Positions_Long_All", "dealer_short": "Dealer_Positions_Short_All",
    "am_long": "Asset_Mgr_Positions_Long_All", "am_short": "Asset_Mgr_Positions_Short_All",
    "lev_long": "Lev_Money_Positions_Long_All", "lev_short": "Lev_Money_Positions_Short_All",
    "other_long": "Other_Rept_Positions_Long_All", "other_short": "Other_Rept_Positions_Short_All",
    "nonrept_long": "NonRept_Positions_Long_All", "nonrept_short": "NonRept_Positions_Short_All",
}


def available_on(as_of: date) -> date | None:
    """The New York date from whose 17:00 an as-of observation may be used, or None if unavailable."""
    if UNAVAILABLE[0] <= as_of <= UNAVAILABLE[1]:
        return None
    d = as_of + timedelta(days=LAG_DAYS)
    while d.weekday() >= 5:
        d += timedelta(days=1)
    return d


def available_at(as_of: date) -> int | None:
    """UTC epoch seconds at which the report is taken to be public, or None."""
    d = available_on(as_of)
    if d is None:
        return None
    return int(datetime(d.year, d.month, d.day, AVAILABLE_HOUR, tzinfo=NY).timestamp())


def _epoch(d: date) -> int:
    return int(datetime(d.year, d.month, d.day, tzinfo=timezone.utc).timestamp())


@dataclass(frozen=True)
class CotSeries:
    """One currency future's reports, ordered by as-of date; only reports with a release time."""

    currency: str
    as_of: np.ndarray  # epoch seconds of the as-of date, 00:00 UTC
    available_at: np.ndarray  # epoch seconds, non-decreasing
    fields: dict  # name -> float array

    def __len__(self) -> int:
        return len(self.as_of)

    def net(self, category: str) -> np.ndarray:
        return self.fields[f"{category}_long"] - self.fields[f"{category}_short"]

    def truncated(self, t: int) -> "CotSeries":
        """Only the reports public at time `t`."""
        keep = self.available_at <= t
        return CotSeries(self.currency, self.as_of[keep], self.available_at[keep],
                         {k: v[keep] for k, v in self.fields.items()})


def _as_of(r: dict) -> date:
    return datetime.strptime(r["As_of_Date_In_Form_YYMMDD"].strip(), "%y%m%d").date()


def parse(members: dict[str, bytes]) -> dict[str, CotSeries]:
    """The seven currencies from the extracted TFF member files (any order, any subset)."""
    rows: dict[str, dict[date, dict]] = {c: {} for c in CONTRACTS.values()}
    for name, raw in sorted(members.items()):
        for r in csv.DictReader(io.StringIO(raw.decode("latin-1"), newline="")):
            ccy = CONTRACTS.get(r["CFTC_Contract_Market_Code"].strip())
            if ccy is None:
                continue
            if r.get("FutOnly_or_Combined", "").strip() != "FutOnly":
                raise ValueError(f"{name}: a {ccy} row is not futures-only; refusing a mixed report type")
            d = _as_of(r)
            if d in rows[ccy]:
                raise ValueError(f"{name}: duplicate {ccy} report for {d}")
            vals = {}
            for k, col in FIELDS.items():
                v = float(r[col])  # a missing or malformed value raises: never filled
                if not np.isfinite(v) or v < 0:
                    raise ValueError(f"{name}: {ccy} {d} {col} = {r[col]!r}")
                vals[k] = v
            rows[ccy][d] = vals
    out = {}
    for ccy, by_date in rows.items():
        ds = [d for d in sorted(by_date) if available_at(d) is not None]
        out[ccy] = CotSeries(ccy, np.array([_epoch(d) for d in ds], np.int64),
                             np.array([available_at(d) for d in ds], np.int64),
                             {k: np.array([by_date[d][k] for d in ds], float) for k in FIELDS})
    return out


class CotStore:
    """Reads the untouched ZIPs, checks them against the manifest, truncates at the holdout."""

    def __init__(self, root: Path | str, holdout=None) -> None:
        self.root = Path(root)
        self.holdout = holdout
        mf = self.root / "manifest.json"
        self.manifest = json.loads(mf.read_text()) if mf.exists() else {}

    def load(self, key=None) -> dict[str, CotSeries]:
        members = {}
        for zname, member in FILES.items():
            zb = (self.root / zname).read_bytes()
            want = self.manifest.get("files", {}).get(zname, {}).get("zip_sha256")
            if want is None or hashlib.sha256(zb).hexdigest() != want:
                raise ValueError(f"{zname}: does not match data/cot/manifest.json; refusing unverified data")
            with zipfile.ZipFile(io.BytesIO(zb)) as z:
                members[member] = z.read(member)
        out = parse(members)
        if self.holdout is not None and key is None:
            seal = _epoch(self.holdout.start)
            out = {k: v.truncated(seal - 1) for k, v in out.items()}
        return out


__all__ = ["AVAILABLE_HOUR", "CONTRACTS", "COT_VERSION", "CotSeries", "CotStore", "FIELDS", "LAG_DAYS",
           "UNAVAILABLE", "available_at", "available_on", "parse"]
