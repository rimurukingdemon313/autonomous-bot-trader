"""NE audit: measure the index-CFD bid/ask datasets this program may use, instead of assuming their properties.

    python scripts/ne_audit.py      # writes research/results/NE-audit.json

Reads only data/ix (H1 2012-2020 for six index CFDs; Nasdaq-100 M5 2012-2017). Never reads the fx-majors
holdout (2017+) or anything dated 2021-2024: every array is cut at 2021-01-01 before any statistic.

Measured per file:
- range, bar count, duplicate and out-of-order timestamps, crossed quotes (ask < bid), impossible OHLC;
- coverage: share of expected weekday hours present, by year;
- timezone: the hour of the daily CFD maintenance break in UTC, winter vs summer. A US index CFD pauses
  around 17:00 New York, so in UTC the empty hour must move by one hour with US daylight saving if the
  timestamps are true UTC (DATA_CONTRACT §3: measured, not assumed);
- alignment: share of US-index hours present in all three US CFDs;
- spread at the bar open in index points and in bp of the mid, by year and by New York hour;
- contract rolls: the mean absolute 1-hour return on the Monday-Friday of quarterly futures roll weeks
  versus other weeks. A CFD that tracks a rolled future without adjustment would show a jump there.
"""

from __future__ import annotations

import json
import sys
from collections import defaultdict
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from aitrader.data.bars import BarSeries  # noqa: E402

DATA = ROOT / "data" / "ix"
OUT = ROOT / "research" / "results" / "NE-audit.json"
CUT = int(datetime(2021, 1, 1, tzinfo=timezone.utc).timestamp())
NY = ZoneInfo("America/New_York")
US = ("USA500IDXUSD", "USATECHIDXUSD", "USA30IDXUSD")
ALL = US + ("JPNIDXJPY", "HKGIDXHKD", "AUSIDXAUD")


def load(pattern: str) -> BarSeries:
    parts = [BarSeries.load(p) for p in sorted(DATA.glob(pattern))]
    s = BarSeries.concat(parts)
    return s.take(s.open_time < CUT)


def third_friday(y: int, m: int) -> date:
    d = date(y, m, 15)
    return d + timedelta(days=(4 - d.weekday()) % 7)


def roll_weeks(years) -> set[date]:
    """Mondays of the weeks containing the quarterly expiry (third Friday of Mar/Jun/Sep/Dec)."""
    out = set()
    for y in years:
        for m in (3, 6, 9, 12):
            f = third_friday(y, m)
            out.add(f - timedelta(days=4))
    return out


def audit(s: BarSeries) -> dict:
    t = np.asarray(s.open_time)
    bo, ao, bc, ac = (np.asarray(x, float) for x in (s.bid_open, s.ask_open, s.bid_close, s.ask_close))
    bh, bl, ah, al = (np.asarray(x, float) for x in (s.bid_high, s.bid_low, s.ask_high, s.ask_low))
    d = np.diff(t)
    mid = (bo + ao) / 2
    sp_pts = ao - bo
    sp_bp = sp_pts / mid * 1e4
    dt = [datetime.fromtimestamp(int(x), timezone.utc) for x in t]
    years = sorted({x.year for x in dt})
    out: dict = {
        "symbol": s.symbol, "timeframe": s.timeframe, "bars": int(len(t)),
        "first": dt[0].isoformat(), "last": dt[-1].isoformat(),
        "duplicates": int((d == 0).sum()), "out_of_order": int((d < 0).sum()),
        "crossed_open": int((ao < bo).sum()), "crossed_close": int((ac < bc).sum()),
        "impossible_ohlc": int(((bh < bl) | (ah < al) | (bh < np.maximum(bo, bc) - 1e-9)
                                | (bl > np.minimum(bo, bc) + 1e-9)).sum()),
        "nonpositive": int(((bo <= 0) | (ao <= 0)).sum()),
    }
    period = s.period
    nyh_all = np.array([x.astimezone(NY).hour for x in dt])
    wd_all = np.array([x.astimezone(NY).weekday() for x in dt])
    cov, spy = {}, {}
    for y in years:
        m = np.array([x.year == y for x in dt])
        start = max(datetime(y, 1, 1, tzinfo=timezone.utc), dt[0])
        end = min(datetime(y + 1, 1, 1, tzinfo=timezone.utc), datetime.fromtimestamp(CUT, timezone.utc), dt[-1])
        n_exp = 0
        cur = start
        step = timedelta(seconds=period)
        while cur < end:  # weekdays only, every slot; CFD sessions are ~23 h, so coverage < 1 is expected
            if cur.weekday() < 5:
                n_exp += 1
            cur += step
        cov[str(y)] = round(float(m.sum()) / max(n_exp, 1), 3)
        ok = m & (sp_pts >= 0)
        rthy = m & (nyh_all >= 10) & (nyh_all <= 15) & (wd_all < 5)
        spy[str(y)] = {"zero_spread_share": round(float((sp_pts[m] <= 0).mean()), 4),
                       "zero_spread_share_rth": round(float((sp_pts[rthy] <= 0).mean()), 4) if rthy.any() else None,
                       "median_pts": round(float(np.median(sp_pts[ok])), 4),
                       "median_bp": round(float(np.median(sp_bp[ok])), 3),
                       "p90_bp": round(float(np.percentile(sp_bp[ok], 90)), 3)}
    out["weekday_slot_coverage_by_year"] = cov
    # regular New York hours (10:00-15:59 bar opens) present per weekday, by year: the hours a US session
    # strategy needs. Expected 6 H1 bars (or 72 M5 bars) a day.
    per_day = 3600 // period * 6
    days = defaultdict(int)
    for x, h, w in zip(dt, nyh_all, wd_all):
        if 10 <= h <= 15 and w < 5:
            days[x.astimezone(NY).date()] += 1
    out["rth_complete_day_share_by_year"] = {str(y): round(float(np.mean([v == per_day for k, v in days.items()
                                                                          if k.year == y])), 3) for y in years
                                             if any(k.year == y for k in days)}
    out["spread_open_by_year"] = spy
    # spread by New York hour (whole period)
    nyh = np.array([x.astimezone(NY).hour for x in dt])
    out["spread_bp_median_by_ny_hour"] = {str(h): round(float(np.median(sp_bp[(nyh == h) & (sp_pts >= 0)])), 3)
                                          for h in range(24) if ((nyh == h) & (sp_pts >= 0)).sum() >= 50}
    # timezone: least-populated UTC hour on weekdays (Mon-Thu), January vs July
    if period == 3600:
        utch = np.array([x.hour for x in dt])
        mon = np.array([x.month for x in dt])
        wd = np.array([x.weekday() for x in dt])
        brk = {}
        for name, mm in (("january", 1), ("july", 7)):
            sel = (mon == mm) & (wd <= 3)
            counts = np.bincount(utch[sel], minlength=24)
            brk[name] = {"emptiest_utc_hour": int(np.argmin(counts)), "bars_in_that_hour": int(counts.min()),
                         "median_bars_per_hour": int(np.median(counts))}
        out["daily_break"] = brk
    # contract rolls: mean |1-bar mid return| in roll weeks vs other weeks, regular New York hours only
    r = np.full(len(t), np.nan)
    cont = np.r_[False, d == period]
    r[cont] = np.abs(np.diff(np.log(mid)))[cont[1:]]
    monday = np.array([(x.date() - timedelta(days=x.weekday())) for x in dt])
    rw = roll_weeks(years)
    inroll = np.array([mo in rw for mo in monday])
    rth = (nyh >= 10) & (nyh <= 15)
    a, b = r[inroll & rth & cont], r[~inroll & rth & cont]
    out["roll_check"] = {"mean_abs_ret_bp_roll_weeks": round(float(np.nanmean(a)) * 1e4, 3),
                         "mean_abs_ret_bp_other_weeks": round(float(np.nanmean(b)) * 1e4, 3),
                         "max_abs_ret_bp_roll_weeks": round(float(np.nanmax(a)) * 1e4, 1) if len(a) else None,
                         "max_abs_ret_bp_other_weeks": round(float(np.nanmax(b)) * 1e4, 1) if len(b) else None}
    return out


def main() -> int:
    res: dict = {"scope": "data/ix cut at 2021-01-01; fx-majors and 2021+ never read", "files": {}}
    h1 = {}
    for sym in ALL:
        s = load(f"{sym}_H1_*.npz")
        h1[sym] = s
        res["files"][f"{sym} H1"] = audit(s)
        print(sym, "H1 done", flush=True)
    m5 = load("USATECHIDXUSD_M5_*.npz")
    res["files"]["USATECHIDXUSD M5"] = audit(m5)
    # alignment of the three US CFDs
    sets = [set(map(int, h1[s].open_time)) for s in US]
    union = set().union(*sets)
    res["us_alignment"] = {"hours_in_any": len(union), "hours_in_all_three": len(sets[0] & sets[1] & sets[2]),
                           "share": round(len(sets[0] & sets[1] & sets[2]) / len(union), 4)}
    # M5 vs H1 consistency: the M5 mid open at each full hour equals the H1 mid open (same source)
    h = h1["USATECHIDXUSD"]
    hidx = {int(x): i for i, x in enumerate(h.open_time)}
    diffs = []
    for i, x in enumerate(m5.open_time):
        j = hidx.get(int(x))
        if j is not None:
            diffs.append(abs((m5.bid_open[i] + m5.ask_open[i]) / 2 - (h.bid_open[j] + h.ask_open[j]) / 2))
    diffs = np.array(diffs)
    res["m5_vs_h1_open_points"] = {"n": int(len(diffs)), "median": round(float(np.median(diffs)), 4),
                                   "p99": round(float(np.percentile(diffs, 99)), 4)}
    OUT.write_text(json.dumps(res, indent=1, default=str) + "\n")
    print(json.dumps({k: v for k, v in res.items() if k != "files"}, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
