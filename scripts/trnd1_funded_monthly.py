"""Descriptive only: TRND-1's rule on a $200,000 funded account, month by month, 1990-01..2026-10, with FUNDED-P's
own pieces (the rule's decisions, its costs, HALF's one-day stop). The account is treated as already funded, with no
phases or targets; a day losing $10,000, or $20,000 lost since an account's start, marks where that account would
have ended, and a new one is counted from there. The years 1990-2020 were judged by RC-EQ (its E4, the same rule)
and 2021-2026 by TRND-1-H. This is not a test, and the past is not a forecast.

    python scripts/trnd1_funded_monthly.py <the TRND-1 data folder>   # -> research/results/TRND-1-funded-monthly.json
"""

from __future__ import annotations

import json
import statistics
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import scripts.funded_paper as P  # noqa: E402
import scripts.trnd1 as T  # noqa: E402

OUT = ROOT / "research" / "results" / "TRND-1-funded-monthly.json"
START, END = date(1990, 1, 1), date(2026, 10, 31)


def daily_pl(data: dict, expo: float, stop: float | None) -> tuple[list[tuple[date, float]], int]:
    """Each day's P&L in dollars, and the number of trades (entries, exits and stops)."""
    syms = list(data)
    notional = expo * P.BALANCE / len(syms)
    dec = {s: P.decisions(data[s]) for s in syms}
    dates = sorted({d for s in syms for d in data[s] if START <= d <= END})
    held = {s: False for s in syms}
    last: dict = {s: None for s in syms}
    stopped: dict = {}
    out, trades = [], 0
    for d in dates:
        pl = 0.0
        for s in syms:
            c = data[s].get(d)
            if c is None:
                continue
            want = dec[s].get((d.year, d.month)) or False
            if stopped.get(s) == (d.year, d.month):
                want = False
            if last[s] is not None and want != held[s]:
                pl -= notional * T.COST_SIDE
                trades += 1
            if last[s] is None and want:
                pl -= notional * T.COST_SIDE
                trades += 1
            elif last[s] is not None and want:
                move = c / last[s] - 1.0
                if stop and move <= -stop:
                    pl -= notional * (stop + P.STOP_SLIPPAGE) + notional * T.COST_SIDE
                    stopped[s], want, trades = (d.year, d.month), False, trades + 1
                else:
                    pl += notional * move
            held[s], last[s] = want, c
        out.append((d, pl))
    return out, trades


def summary(days: list[tuple[date, float]], trades: int) -> dict:
    months: dict = {}
    years: dict = {}
    eq = peak = worst = since = 0.0
    ended = []
    for d, pl in days:
        eq += pl
        since += pl
        peak, worst = max(peak, eq), max(worst, max(peak, eq) - eq)
        if pl <= -P.DAILY_LOSS or since <= -P.MAX_LOSS:
            ended.append({"date": str(d), "day": round(pl), "since_start": round(since)})
            since = 0.0
        months[f"{d.year}-{d.month:02d}"] = months.get(f"{d.year}-{d.month:02d}", 0.0) + pl
        years[d.year] = years.get(d.year, 0.0) + pl
    mv = list(months.values())
    decades = {f"{a}-{b - 1}": round(statistics.mean(v for k, v in months.items() if a <= int(k[:4]) < b))
               for a, b in ((1990, 2000), (2000, 2010), (2010, 2020), (2020, 2027))}
    return {"months": len(mv), "trades": trades, "total": round(eq), "mean_month": round(statistics.mean(mv)),
            "median_month": round(statistics.median(mv)), "positive_months": round(sum(m > 0 for m in mv) / len(mv), 3),
            "best_month": round(max(mv)), "worst_month": round(min(mv)), "mean_year": round(statistics.mean(years.values())),
            "worst_year": [min(years, key=years.get), round(min(years.values()))],
            "best_year": [max(years, key=years.get), round(max(years.values()))], "worst_fall_from_peak": round(worst),
            "accounts_ended": ended, "mean_month_by_decade": decades,
            "by_month": {k: round(v) for k, v in months.items()}}


def main() -> int:
    T.DATA = Path(sys.argv[1])
    data = T.load(T.HOLDOUT_INDICES, date(1984, 1, 1), date(2026, 11, 1))
    report = {"note": "descriptive, on data already judged (RC-EQ 1990-2020, TRND-1-H 2021-2026); not a test",
              "runs": {}}
    for name, expo, stop in (("HALF with its stop", P.TRACKS["HALF"]["expo"], P.TRACKS["HALF"]["stop"]),
                             ("FULL", P.TRACKS["FULL"]["expo"], P.TRACKS["FULL"]["stop"])):
        report["runs"][name] = summary(*daily_pl(data, expo, stop))
        r = report["runs"][name]
        print(name, {k: r[k] for k in r if k not in ("by_month", "accounts_ended")}, "ended:", r["accounts_ended"])
    OUT.write_text(json.dumps(report, indent=1, sort_keys=True) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
