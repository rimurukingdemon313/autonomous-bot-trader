"""Interest rates, point in time: the data layer for genuine carry research (Round 3).

Every observation carries the fields the research plan requires:

    currency, rate_type, value (percent per year), effective (date the rate applies from),
    published (when the publisher released it, if known), source, revision, available_at

`available_at` is the earliest moment the value was public, chosen CONSERVATIVELY per rate type:

    POLICY        the rate in force on date d is taken as public at 17:00 New York on d. Every G10
                  decision is announced before that moment on its effective date or earlier (Fed 14:00
                  NY and effective the next day; ECB 13:45 CET; BoE 12:00 London; BoC 10:00 ET; SNB,
                  RBA, RBNZ and BoJ before the European open), so a decision is never used before it
                  was announced.
    INTERBANK_3M  a fixing dated d (Euribor: 11:00 CET) is taken as public at 12:00 CET on d.

A decision at time t sees only observations with available_at <= t, and a rate is NEVER
interpolated: between two observations the last one public is the value in force (a step), which
is what a policy rate is; a currency with no observation public at t has no rate at t (NaN).

Coverage is recorded per currency. A currency without an authoritative series is UNAVAILABLE and
every pair containing it is excluded: nothing is substituted, no maturity is mixed (a 3-month rate
against a 10-year yield is not a carry differential), and no broker swap is assumed.

Parsers accept the official formats as published, so an authoritative file placed in
data/rates/ (with its sha256 in data/rates/manifest.json) is used without code changes:

    bis_cbpol   BIS WS_CBPOL flat CSV (REF_AREA, TIME_PERIOD, OBS_VALUE; daily or monthly)
    fred        FRED graph CSV (DATE/observation_date, <series id>)
    euribor     the datahub.io/EMMI Euribor file (date, rate, maturity_level)
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
from dataclasses import dataclass
from datetime import date, datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

import numpy as np

RATES_VERSION = "rates-1.0.0"
NY, CET = ZoneInfo("America/New_York"), ZoneInfo("Europe/Brussels")
RATE_TYPES = ("POLICY", "INTERBANK_3M")
CURRENCIES = ("USD", "EUR", "GBP", "JPY", "AUD", "NZD", "CAD", "CHF")
BIS_AREA = {"US": "USD", "XM": "EUR", "GB": "GBP", "JP": "JPY", "AU": "AUD", "NZ": "NZD", "CA": "CAD", "CH": "CHF"}


def _epoch(d: date, hour: int, minute: int, tz: ZoneInfo) -> int:
    return int(datetime(d.year, d.month, d.day, hour, minute, tzinfo=tz).timestamp())


def available_at(rate_type: str, d: date) -> int:
    if rate_type == "POLICY":
        return _epoch(d, 17, 0, NY)
    if rate_type == "INTERBANK_3M":
        return _epoch(d, 12, 0, CET)
    raise ValueError(rate_type)


@dataclass(frozen=True)
class RateSeries:
    currency: str
    rate_type: str
    source: str
    revision: str
    effective: np.ndarray  # epoch seconds (00:00 UTC of the effective date)
    value: np.ndarray  # percent per year
    available_at: np.ndarray  # epoch seconds, non-decreasing
    published: np.ndarray | None = None  # epoch seconds when known, else None

    def asof(self, t) -> np.ndarray:
        """The rate in force and public at each time in t: the last observation public by then (a step,
        never an interpolation); NaN before the first."""
        t = np.asarray(t, np.int64)
        k = np.searchsorted(self.available_at, t, side="right") - 1
        out = np.full(len(t), np.nan)
        ok = k >= 0
        out[ok] = self.value[k[ok]]
        return out

    def value_days_ago(self, t, days: int) -> np.ndarray:
        """The rate that was in force and public `days` calendar days before each time in t."""
        return self.asof(np.asarray(t, np.int64) - days * 86400)

    def truncated(self, t: int) -> "RateSeries":
        keep = self.available_at <= t
        pub = self.published[keep] if self.published is not None else None
        return RateSeries(self.currency, self.rate_type, self.source, self.revision, self.effective[keep],
                          self.value[keep], self.available_at[keep], pub)


def _series(currency, rate_type, source, revision, rows) -> RateSeries:
    rows = sorted({d: v for d, v in rows}.items())
    eff = np.array([int(datetime(d.year, d.month, d.day, tzinfo=timezone.utc).timestamp()) for d, _ in rows], np.int64)
    val = np.array([v for _, v in rows], float)
    av = np.array([available_at(rate_type, d) for d, _ in rows], np.int64)
    return RateSeries(currency, rate_type, source, revision, eff, val, av)


def _float(x: str) -> float | None:
    try:
        v = float(x)
    except (TypeError, ValueError):
        return None
    return v if np.isfinite(v) else None


def parse_bis_cbpol(raw: bytes) -> dict[str, RateSeries]:
    """BIS central-bank policy rates (WS_CBPOL), flat CSV. Policy rates are not revised."""
    rows: dict[str, list] = {}
    for r in csv.DictReader(io.StringIO(raw.decode("utf-8-sig"))):
        area = (r.get("REF_AREA") or r.get("REF_AREA:Reference area") or "").split(":")[0].strip()
        ccy = BIS_AREA.get(area)
        tp, v = (r.get("TIME_PERIOD") or r.get("TIME_PERIOD:Time period or range") or "").strip(), \
            _float(r.get("OBS_VALUE") or r.get("OBS_VALUE:Observation Value"))
        if ccy is None or v is None or not tp:
            continue
        if len(tp) == 7:  # monthly (YYYY-MM): the rate at the END of the month is only known then
            y, m = int(tp[:4]), int(tp[5:7])
            d = date(y + (m == 12), m % 12 + 1, 1)
        else:
            d = date.fromisoformat(tp[:10])
        rows.setdefault(ccy, []).append((d, v))
    return {c: _series(c, "POLICY", "BIS WS_CBPOL (central-bank policy rates)", "not revised", r)
            for c, r in rows.items()}


def parse_fred(raw: bytes, currency: str, rate_type: str, series_id: str) -> RateSeries:
    rows = []
    for r in csv.DictReader(io.StringIO(raw.decode("utf-8-sig"))):
        ds = (r.get("DATE") or r.get("observation_date") or "").strip()
        v = _float(r.get(series_id))
        if ds and v is not None:
            rows.append((date.fromisoformat(ds[:10]), v))
    return _series(currency, rate_type, f"FRED {series_id}", "as published by FRED (check ALFRED vintages)", rows)


def parse_euribor(raw: bytes) -> RateSeries:
    """EMMI Euribor 3M, one fixing per month dated on its fixing day (the first business day). Not revised."""
    rows = []
    for r in csv.DictReader(io.StringIO(raw.decode("utf-8"))):
        if (r.get("maturity_level") or "").strip() != "3m":
            continue
        v = _float(r.get("rate"))
        if v is not None and r.get("date"):
            rows.append((date.fromisoformat(r["date"][:10]), v))
    return _series("EUR", "INTERBANK_3M", "EMMI Euribor 3M (monthly: first-business-day fixing), via datahub.io",
                   "not revised", rows)


PARSERS = {"bis_cbpol": parse_bis_cbpol, "euribor": parse_euribor}


class RateStore:
    """Rate series from data/rates/, verified against data/rates/manifest.json, truncated at the holdout.

    manifest.json: {"<file>": {"format": "bis_cbpol|euribor|fred", "sha256": ..., "source": ...,
                     ["currency", "rate_type", "series_id" for fred]}}
    """

    def __init__(self, root: Path | str, holdout=None) -> None:
        self.root = Path(root)
        mf = self.root / "manifest.json"
        self.manifest = json.loads(mf.read_text()) if mf.exists() else {}
        self.holdout = holdout

    def load(self) -> dict[tuple[str, str], RateSeries]:
        out: dict[tuple[str, str], RateSeries] = {}
        for fname, meta in sorted(self.manifest.items()):
            raw = (self.root / fname).read_bytes()
            if hashlib.sha256(raw).hexdigest() != meta.get("sha256"):
                raise ValueError(f"{fname}: does not match the manifest; refusing unverified rate data")
            fmt = meta["format"]
            if fmt == "fred":
                got = {meta["currency"]: parse_fred(raw, meta["currency"], meta["rate_type"], meta["series_id"])}
            else:
                parsed = PARSERS[fmt](raw)
                got = parsed if isinstance(parsed, dict) else {parsed.currency: parsed}
            for c, s in got.items():
                if self.holdout is not None:
                    h = self.holdout.start
                    s = s.truncated(int(datetime(h.year, h.month, h.day, tzinfo=timezone.utc).timestamp()) - 1)
                out[(c, s.rate_type)] = s
        return out


def coverage(series: dict[tuple[str, str], RateSeries], start: date, end: date) -> dict[str, dict]:
    """Per currency: which rate types exist and whether they cover [start, end] without a gap longer
    than their sampling (policy: continuous by construction of a step series; monthly fixings: 40 days)."""
    t0 = int(datetime(start.year, start.month, start.day, tzinfo=timezone.utc).timestamp())
    t1 = int(datetime(end.year, end.month, end.day, tzinfo=timezone.utc).timestamp())
    out = {}
    for c in CURRENCIES:
        types = {}
        for rt in RATE_TYPES:
            s = series.get((c, rt))
            if s is None or not len(s.value):
                continue
            inside = s.available_at[(s.available_at >= t0) & (s.available_at <= t1)]
            first_ok = s.available_at[0] <= t0
            gaps = np.diff(np.r_[t0, inside, t1]) / 86400 if len(inside) else np.array([(t1 - t0) / 86400])
            max_gap = float(gaps.max())
            types[rt] = {"first": datetime.fromtimestamp(int(s.effective[0]), timezone.utc).date().isoformat(),
                         "last": datetime.fromtimestamp(int(s.effective[-1]), timezone.utc).date().isoformat(),
                         "observations": int(len(s.value)), "covers_period": bool(first_ok and (
                             rt == "POLICY" or max_gap <= 40)), "max_gap_days": round(max_gap, 1),
                         "source": s.source, "revision": s.revision}
        out[c] = {"status": "AVAILABLE" if any(v["covers_period"] for v in types.values()) else "UNAVAILABLE",
                  "types": types}
    return out


def differential(series: dict[tuple[str, str], RateSeries], pair: str, rate_type: str, t) -> np.ndarray:
    """rate(base) - rate(quote), both of the SAME rate type, as public at each time in t. NaN when either
    side has no public value: a missing currency is never filled or substituted."""
    base, quote = pair[:3], pair[3:]
    a, b = series.get((base, rate_type)), series.get((quote, rate_type))
    t = np.asarray(t, np.int64)
    if a is None or b is None:
        return np.full(len(t), np.nan)
    return a.asof(t) - b.asof(t)


__all__ = ["CURRENCIES", "RATES_VERSION", "RATE_TYPES", "RateSeries", "RateStore", "available_at", "coverage",
           "differential", "parse_bis_cbpol", "parse_euribor", "parse_fred"]
