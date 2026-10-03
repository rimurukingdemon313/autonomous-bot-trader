"""Audit the Federal Reserve H.10 daily rates (via FRED, via the datahub mirror): DATA AUDIT ONLY.

    python scripts/h10_audit.py fetch    # the pinned vintages -> data/h10/ (verified against the manifest if present)
    python scripts/h10_audit.py audit    # every check below -> data/h10/manifest.json (and a printed summary)

No signal, return forecast, portfolio or trading result is computed. The cross-source section
compares PRICES (levels and the returns of the same series) with the repository's Dukascopy bars,
2008-01-02 -> 2016-12-30, to establish timing and fidelity only. Values dated on or after the
holdout start (2017-01-01) are never read; for later dates only their existence is counted.

Raw files are kept unmodified under data/h10/ and are not committed; the manifest is.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import urllib.request
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from aitrader.data.h10 import (H10_VERSION, MIRROR_URL, PRIMARY, SERIES, VINTAGES, NY, available_at,  # noqa: E402
                               fed_holidays, official_series, official_value, on_grid, parse_mirror, vintage_file)

OUT = ROOT / "data" / "h10"
H10_AUDIT_VERSION = "h10-audit-1.0.0"
START = date(1999, 1, 4)  # the euro's first H.10 rate; RV-1 needs all eight currencies
VALUE_END = date(2017, 1, 1)  # the sealed holdout: no value on or after it is read
XS_START, XS_END = date(2008, 1, 2), date(2016, 12, 31)
JUMP = 0.04  # a daily log move of 4% or more is listed for review
STALE_RUN = 3  # this many identical consecutive values is listed
SCAN = [(h, m) for h in range(7, 18) for m in (0, 15, 30, 45) if (h, m) <= (17, 0)]
LEVEL_FLAG_BP = 20.0
SOURCE = {
    "publisher": "Board of Governors of the Federal Reserve System, statistical release H.10 (Foreign Exchange "
                 "Rates): noon buying rates in New York for cable transfers payable in foreign currencies",
    "redistributor": "FRED, Federal Reserve Bank of St. Louis, category 158 (Daily Rates): DEXUSEU, DEXUSUK, DEXUSAL, "
                     "DEXUSNZ, DEXJPUS, DEXSZUS, DEXCAUS",
    "mirror": "github.com/datasets/exchange-rates (datahub 'core' dataset, licence ODC-PDDL), data/daily.csv, "
              "regenerated from FRED by the mirror's own script; used at pinned commits only",
    "official_endpoints_reachable": {"fred.stlouisfed.org": False, "api.stlouisfed.org": False,
                                     "alfred.stlouisfed.org": False, "www.federalreserve.gov": False,
                                     "www.newyorkfed.org": False, "checked": "2026-10-01, connection refused by the "
                                     "environment's network policy"},
    "mirror_transformation": {"2017-12-08": "FRED legacy .txt; EUR/GBP/AUD/NZD stored as round(1/x, 4); wide format",
                              "2018-10-17": "FRED legacy .txt (scripts/process.py); EUR/GBP/AUD/NZD stored as "
                                            "str(1/x) at full float precision -> the official value is recovered "
                                            "exactly as 1/x; long format",
                              "2026-09-29": "FRED fredgraph.csv (scripts/main.py); EUR/GBP/AUD/NZD stored as "
                                            "round(1/x, 4); long format"},
    "mirror_readme_error": "the mirror's README says AUD, EUR, NZD, GBP are stored as USD/currency; the data and the "
                           "scripts store currency/USD (the inverse). The data, not the README, is authoritative",
}


def _sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def cmd_fetch() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    mf = json.loads((OUT / "manifest.json").read_text()) if (OUT / "manifest.json").exists() else {}
    for name, (commit, _) in VINTAGES.items():
        url = MIRROR_URL.format(commit=commit)
        raw = urllib.request.urlopen(url, timeout=120).read()
        want = mf.get("files", {}).get(vintage_file(name), {}).get("sha256")
        if want is not None and _sha(raw) != want:
            raise SystemExit(f"{url} no longer matches the recorded sha256; refusing")
        (OUT / vintage_file(name)).write_bytes(raw)
        print(vintage_file(name), _sha(raw), len(raw))


def weekdays(a: date, b: date) -> list[date]:
    out, d = [], a
    while d < b:
        if d.weekday() < 5:
            out.append(d)
        d += timedelta(days=1)
    return out


def audit_files() -> tuple[dict, dict]:
    files, parsed = {}, {}
    for name, (commit, kind) in VINTAGES.items():
        raw = (OUT / vintage_file(name)).read_bytes()
        p = parse_mirror(raw)  # refuses duplicates
        parsed[name] = p
        files[vintage_file(name)] = {
            "vintage": name, "commit": commit, "url": MIRROR_URL.format(commit=commit), "sha256": _sha(raw),
            "bytes": len(raw), "storage": kind, "header": raw.split(b"\n", 1)[0].decode().strip()[:60],
            "duplicates": 0}
    return files, parsed


def coverage(parsed: dict) -> dict:
    out = {}
    for name, p in parsed.items():
        out[name] = {}
        for ccy, by in p.items():
            valid = sorted(d for d, v in by.items() if v != "")
            out[name][ccy] = {"first_valid": valid[0].isoformat() if valid else None,
                              "last_valid": valid[-1].isoformat() if valid else None,
                              "valid_rows": len(valid),
                              "valid_from_holdout_start": sum(d >= VALUE_END for d in valid)}  # counted, not read
    return out


def transformation_check(p: dict) -> dict:
    """In the full-precision vintage every recovered value must sit on FRED's published decimal grid."""
    out = {}
    for ccy, by in p.items():
        dec = SERIES[ccy][4]
        n = off = 0
        for d, v in by.items():
            if v == "" or not (START <= d < VALUE_END):
                continue
            n += 1
            off += not on_grid(official_value(v, ccy), dec)
        out[ccy] = {"checked": n, "off_grid": off, "decimals": dec, "inverted_by_mirror": SERIES[ccy][2]}
    return out


def gaps(p: dict) -> dict:
    days = weekdays(START, VALUE_END)
    missing = {c: {d for d in days if p[c].get(d, "") == ""} for c in p}
    absent = {c: sum(d not in p[c] for d in days) for c in p}
    every = set.intersection(*missing.values())
    some = set.union(*missing.values()) - every
    hol = {d for y in range(START.year, VALUE_END.year) for d in fed_holidays(y)}
    return {"weekdays": len(days), "weekday_rows_absent": absent,
            "missing_on_all": len(every), "missing_on_all_fed_holiday": len(every & hol),
            "missing_on_all_not_holiday": sorted(d.isoformat() for d in every - hol),
            "missing_on_some_only": {d.isoformat(): sorted(c for c in p if d in missing[c]) for d in sorted(some)},
            "no_rate_days_with_a_value": {d.isoformat(): {
                "currencies": sorted(c for c in p if d not in missing[c]),
                "identical_to_previous_rate": sorted(c for c in p if d not in missing[c] and p[c][d] == _prev(p[c], d))}
                for d in sorted(hol) if START <= d < VALUE_END and d.weekday() < 5 and d not in every}}


def _prev(by: dict, d: date) -> str | None:
    k = d - timedelta(days=1)
    while k >= START:
        if by.get(k, "") != "":
            return by[k]
        k -= timedelta(days=1)
    return None


def revisions(parsed: dict) -> dict:
    """Do the values of 1999..2016 differ between vintages? A full-precision vintage gives the official
    value; a rounded one is compared through the mirror's own rounding (round(1/official, 4))."""
    prim = parsed[PRIMARY]
    out = {}
    for name, p in parsed.items():
        if name == PRIMARY:
            continue
        res = {}
        for ccy in SERIES:
            dec, inv = SERIES[ccy][4], SERIES[ccy][2]
            n = diff = only_here = only_there = 0
            examples = []
            for d in sorted(set(prim[ccy]) | set(p[ccy])):
                if not (START <= d < VALUE_END):
                    continue
                a, b = prim[ccy].get(d, ""), p[ccy].get(d, "")
                if a == "" and b == "":
                    continue
                if (a == "") != (b == ""):
                    only_here += a != ""
                    only_there += b != ""
                    continue
                n += 1
                off = official_value(a, ccy)
                o = float(f"{off:.{dec}f}")
                expect = round(1 / o, 4) if inv else o
                if abs(float(b) - expect) > 1e-12:
                    diff += 1
                    if len(examples) < 3:
                        examples.append([d.isoformat(), b, expect])
            res[ccy] = {"compared": n, "different": diff, "rate_only_in_primary": only_here,
                        "rate_only_in_other": only_there, "examples": examples}
        out[f"{PRIMARY} vs {name}"] = res
    return out


def jumps_and_stale(series: dict) -> dict:
    out = {}
    for ccy, s in series.items():
        ds = [d for d in s.dates if START <= d < VALUE_END]
        v = s.value[: len(ds)] if s.dates[: len(ds)] == tuple(ds) else np.array([x for d, x in zip(s.dates, s.value)
                                                                                    if START <= d < VALUE_END])
        r = np.diff(np.log(v))
        big = [{"date": ds[i + 1].isoformat(), "from": float(v[i]), "to": float(v[i + 1]), "log_move": round(float(r[i]), 4)}
               for i in np.flatnonzero(np.abs(r) >= JUMP)]
        runs, k = [], 1
        for i in range(1, len(v)):
            k = k + 1 if v[i] == v[i - 1] else 1
            if k == STALE_RUN:
                runs.append(ds[i - STALE_RUN + 1].isoformat())
        same = np.flatnonzero(v[1:] == v[:-1])
        out[ccy] = {"daily_moves_ge_4pct": big, "identical_runs_ge_3": runs,
                    "days_identical_to_previous": int(len(same)),
                    "identical_examples": [ds[i + 1].isoformat() for i in same[:10]],
                    "max_abs_daily_log_move": round(float(np.max(np.abs(r))), 4)}
    return out


def policy_gaps() -> dict:
    """Days 1999..2016 on which a currency has no usable policy rate (rates.py staleness rule)."""
    from aitrader.data.rates import RateStore
    from aitrader.research.registry import Holdout
    rs = RateStore(ROOT / "data" / "rates", Holdout.load(ROOT / "research" / "holdout.json")).load()
    days = weekdays(START, VALUE_END)
    t = np.array([int(datetime(d.year, d.month, d.day, 17, tzinfo=NY).timestamp()) for d in days], np.int64)
    out = {}
    for ccy in ("USD",) + tuple(SERIES):
        s = rs.get((ccy, "POLICY"))
        if s is None:
            out[ccy] = {"status": "no series"}
            continue
        ok = np.isfinite(s.asof(t))
        spans, i = [], 0
        while i < len(days):
            if not ok[i]:
                j = i
                while j + 1 < len(days) and not ok[j + 1]:
                    j += 1
                spans.append([days[i].isoformat(), days[j].isoformat(), j - i + 1])
                i = j + 1
            else:
                i += 1
        out[ccy] = {"weekdays_without_rate": int((~ok).sum()), "gaps": spans}
    return out


def cross_source(series: dict) -> dict:
    """H.10 against the Dukascopy bid/ask mid, 2008-01-02 .. 2016-12-30. Prices only."""
    from aitrader.data.store import DataStore
    from aitrader.research.registry import Holdout
    store = DataStore(ROOT / "data" / "processed", Holdout.load(ROOT / "research" / "holdout.json"))
    out, rel = {}, {}
    for ccy, s in series.items():
        bars = store.load(s.pair, "M15")
        t_bar = np.asarray(bars.available_at, np.int64)
        mid = np.asarray(bars.mid_close, float)
        sel = [(d, x) for d, x in zip(s.dates, s.value) if XS_START <= d <= XS_END]
        ds = [d for d, _ in sel]
        h = np.array([x for _, x in sel])

        def at(hh, mm):
            ep = np.array([int(datetime(d.year, d.month, d.day, hh, mm, tzinfo=NY).timestamp()) for d in ds], np.int64)
            k = np.searchsorted(t_bar, ep)
            ok = (k < len(t_bar)) & (t_bar[np.minimum(k, len(t_bar) - 1)] == ep)
            v = np.full(len(ds), np.nan)
            v[ok] = mid[k[ok]]
            return v

        scan = {}
        for hh, mm in SCAN:
            m = at(hh, mm)
            ok = np.isfinite(m)
            scan[f"{hh:02d}:{mm:02d}"] = round(float(np.median(np.abs(1e4 * np.log(h[ok] / m[ok])))), 3)
        best = min(scan, key=scan.get)
        noon, close = at(12, 0), at(17, 0)
        diff = 1e4 * np.log(h / noon)
        ok = np.isfinite(diff)
        years = np.array([d.year for d in ds])
        by_year = {}
        for y in sorted(set(years.tolist())):
            yk = years == y
            ys = {}
            for hh, mm in SCAN:
                m = at(hh, mm)[yk]
                okm = np.isfinite(m)
                ys[f"{hh:02d}:{mm:02d}"] = float(np.median(np.abs(1e4 * np.log(h[yk][okm] / m[okm]))))
            by_year[str(y)] = {"best_time": min(ys, key=ys.get), "median_abs_bp_at_noon": round(ys["12:00"], 3)}

        def rets(a):
            r = np.full(len(a), np.nan)
            r[1:] = np.log(a[1:] / a[:-1])
            return r

        rh, rn, rc = rets(h), rets(noon), rets(close)
        okn, okc = np.isfinite(rh) & np.isfinite(rn), np.isfinite(rh) & np.isfinite(rc)
        week = np.array([d.isocalendar()[:2] for d in ds])
        last = [i for i in range(len(ds)) if i == len(ds) - 1 or tuple(week[i]) != tuple(week[i + 1])]
        wh, wn = h[last], noon[last]
        rwh, rwn = np.log(wh[1:] / wh[:-1]), np.log(wn[1:] / wn[:-1])
        okw = np.isfinite(rwh) & np.isfinite(rwn)
        flagged = np.flatnonzero(ok & (np.abs(diff) > LEVEL_FLAG_BP))
        top = sorted(flagged, key=lambda i: -abs(diff[i]))[:5]
        out[ccy] = {
            "pair": s.pair, "h10_dates": len(ds), "dukascopy_noon_bar_found": int(ok.sum()),
            "timing_scan_median_abs_bp": scan, "best_matching_time_ny": best,
            "best_time_by_year": by_year,
            "level_at_noon_bp": {"median_signed": round(float(np.median(diff[ok])), 3),
                                 "median_abs": round(float(np.median(np.abs(diff[ok]))), 3),
                                 "p95_abs": round(float(np.percentile(np.abs(diff[ok]), 95)), 3),
                                 "p99_abs": round(float(np.percentile(np.abs(diff[ok]), 99)), 3),
                                 "max_abs": round(float(np.max(np.abs(diff[ok]))), 3),
                                 f"days_over_{int(LEVEL_FLAG_BP)}bp": int(len(flagged)),
                                 "largest": [[ds[i].isoformat(), round(float(diff[i]), 1)] for i in top]},
            "daily_returns": {"n": int(okn.sum()),
                              "corr_vs_noon": round(float(np.corrcoef(rh[okn], rn[okn])[0, 1]), 5),
                              "rms_diff_bp_vs_noon": round(float(1e4 * np.sqrt(np.mean((rh[okn] - rn[okn]) ** 2))), 3),
                              "beta_vs_noon": round(float(np.polyfit(rn[okn], rh[okn], 1)[0]), 4),
                              "corr_vs_17h_close": round(float(np.corrcoef(rh[okc], rc[okc])[0, 1]), 5),
                              "rms_diff_bp_vs_17h_close": round(float(1e4 * np.sqrt(np.mean((rh[okc] - rc[okc]) ** 2))),
                                                                3)},
            "weekly_returns": {"n": int(okw.sum()), "corr_vs_noon": round(float(np.corrcoef(rwh[okw], rwn[okw])[0, 1]), 5),
                               "rms_diff_bp": round(float(1e4 * np.sqrt(np.mean((rwh[okw] - rwn[okw]) ** 2))), 3)},
        }
        # the currency's own value in USD, log, at each week's last H.10 date (for the 8-currency check)
        sign = 1.0 if s.pair.endswith("USD") else -1.0
        rel[ccy] = {ds[i]: (sign * np.log(h[i]), sign * np.log(noon[i])) for i in last}
    # numeraire-free currency values (each minus the mean of all eight, USD = 0): do both sources agree?
    common = sorted(set.intersection(*(set(v) for v in rel.values())))
    hv = np.array([[rel[c][d][0] for c in SERIES] for d in common])
    dv = np.array([[rel[c][d][1] for c in SERIES] for d in common])
    okr = np.isfinite(dv).all(axis=1)
    hv, dv = hv[okr], dv[okr]
    hrel = hv - np.hstack([hv, np.zeros((len(hv), 1))]).mean(axis=1, keepdims=True)
    drel = dv - np.hstack([dv, np.zeros((len(dv), 1))]).mean(axis=1, keepdims=True)
    dh, dd = np.diff(hrel, axis=0), np.diff(drel, axis=0)
    usd_h, usd_d = -hv.mean(axis=1) * 7 / 8, -dv.mean(axis=1) * 7 / 8
    out["eight_currency_relative_weekly"] = {
        "weeks": int(len(dh)),
        "corr": {c: round(float(np.corrcoef(dh[:, i], dd[:, i])[0, 1]), 5) for i, c in enumerate(SERIES)} | {
            "USD": round(float(np.corrcoef(np.diff(usd_h), np.diff(usd_d))[0, 1]), 5)},
        "note": "currency value in USD minus the mean of the eight (USD = 0), weekly change; a data-agreement "
                "check only, nothing is ranked or traded"}
    return out


TRIANGLES = {"AUD": ("AUDUSD", "AUDJPY"), "EUR": ("EURUSD", "EURJPY"), "GBP": ("GBPUSD", "GBPJPY")}


def third_source(series: dict) -> dict:
    """Arbitration where H.10 and the Dukascopy pair disagree: each against the pair IMPLIED by two other
    Dukascopy instruments (CCYJPY / USDJPY) at noon New York; and, for days where three or more of the six
    non-AUD currencies differ from Dukascopy by > 20 bp, the New York time at which H.10 matches best."""
    from aitrader.data.store import DataStore
    from aitrader.research.registry import Holdout
    store = DataStore(ROOT / "data" / "processed", Holdout.load(ROOT / "research" / "holdout.json"))
    need = {SERIES[c][3] for c in SERIES} | {x for v in TRIANGLES.values() for x in v} | {"USDJPY"}
    mids = {}
    for sym in sorted(need):
        b = store.load(sym, "M15")
        mids[sym] = dict(zip(np.asarray(b.available_at, np.int64).tolist(), np.asarray(b.mid_close, float).tolist()))

    def ep(d, hh, mm=0):
        return int(datetime(d.year, d.month, d.day, hh, mm, tzinfo=NY).timestamp())

    tri = {}
    for ccy, (pair, cross) in TRIANGLES.items():
        yr: dict[int, list] = {}
        for d, v in zip(series[ccy].dates, series[ccy].value):
            if not (XS_START <= d <= XS_END):
                continue
            e = ep(d, 12)
            if e in mids[cross] and e in mids["USDJPY"] and e in mids[pair]:
                imp = mids[cross][e] / mids["USDJPY"][e]
                a = yr.setdefault(d.year, [[], []])
                a[0].append(abs(1e4 * np.log(v / imp)))
                a[1].append(abs(1e4 * np.log(mids[pair][e] / imp)))
        tri[ccy] = {str(y): {"h10_vs_implied_median_abs_bp": round(float(np.median(a)), 3),
                             "dukascopy_direct_vs_implied_median_abs_bp": round(float(np.median(b)), 3)}
                    for y, (a, b) in sorted(yr.items())}
    flagged: dict[date, list] = {}
    for ccy in SERIES:
        if ccy == "AUD":
            continue  # its Dukascopy series is the faulty side in 2008-2009 (see the triangle)
        pair = SERIES[ccy][3]
        for d, v in zip(series[ccy].dates, series[ccy].value):
            e = ep(d, 12)
            if XS_START <= d <= XS_END and e in mids[pair] and abs(1e4 * np.log(v / mids[pair][e])) > LEVEL_FLAG_BP:
                flagged.setdefault(d, []).append(ccy)
    irregular = {}
    for d in sorted(k for k, v in flagged.items() if len(v) >= 3):
        best = {}
        for ccy in SERIES:
            if ccy == "AUD":
                continue
            pair, v = SERIES[ccy][3], dict(zip(series[ccy].dates, series[ccy].value)).get(d)
            cand = [(abs(1e4 * np.log(v / mids[pair][ep(d, hh, mm)])), f"{hh:02d}:{mm:02d}")
                    for hh in range(6, 18) for mm in (0, 15, 30, 45) if ep(d, hh, mm) in mids[pair]]
            if v is not None and cand:
                b = min(cand)
                best[ccy] = [b[1], round(b[0], 2)]
        irregular[d.isoformat()] = best
    return {"triangulation": tri, "days_three_or_more_currencies_over_20bp": irregular}


def cmd_audit() -> None:
    files, parsed = audit_files()
    primary_raw = (OUT / vintage_file(PRIMARY)).read_bytes()
    series = official_series(primary_raw)  # raises if any value is off the published grid
    series = {c: s.truncated(int(datetime(VALUE_END.year, 1, 1, tzinfo=timezone.utc).timestamp()) - 1)
              for c, s in series.items()}
    m = {
        "version": H10_AUDIT_VERSION, "loader": H10_VERSION, "source": SOURCE, "files": files,
        "primary_vintage": PRIMARY, "value_window": [START.isoformat(), VALUE_END.isoformat()],
        "transformation_check": transformation_check(parsed[PRIMARY]),
        "coverage": coverage(parsed),
        "gaps": {name: gaps(p) for name, p in parsed.items()},
        "revisions": revisions(parsed),
        "discontinuities": jumps_and_stale({c: s for c, s in series.items()}),
        "policy_rate_gaps": policy_gaps(),
        "point_in_time": {"observation": "noon buying rate in New York (12:00 ET) on the observation date",
                          "rule": "usable from 17:00 New York on the next business day (weekday, not a Federal "
                                  "Reserve holiday): the certified figure's publication time cannot be verified here",
                          "example": {"2015-07-02": datetime.fromtimestamp(available_at(date(2015, 7, 2)), NY)
                                      .isoformat()}},
        "cross_source": cross_source(series),
        "third_source": third_source(series),
    }
    (OUT / "manifest.json").write_text(json.dumps(m, indent=1, sort_keys=True) + "\n")
    print(json.dumps({"transformation_check": m["transformation_check"],
                      "gaps_primary": m["gaps"][PRIMARY],
                      "revisions": {k: {c: (x["compared"], x["different"]) for c, x in v.items()}
                                    for k, v in m["revisions"].items()}}, indent=1))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=("fetch", "audit"))
    a = ap.parse_args()
    {"fetch": cmd_fetch, "audit": cmd_audit}[a.cmd]()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
