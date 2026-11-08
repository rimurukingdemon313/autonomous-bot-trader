"""Descriptive: the trend desk's own code (aitrader/position/trend_desk.py) replayed on the four indices' real daily
bars, 2004-2026. The data were already judged (RC-EQ 1990-2020, TRND-1-H 2021-2026), so this is not a test and changes
no verdict. The past is not a forecast.

What it shows that FUNDED-P's replay could not:
- the stops hit by the day's low, and gaps filled at the open;
- the risk engine's sizes and the hard gate's refusals;
- the one-day-late switches after holidays;
- each session's intraday low against the daily limit;
- costs at the spread, slippage and commission.

A failed account (a limit breached) is recorded, and a fresh $200,000 account starts at the next session, as a trader
would buy a new challenge. Positions are not carried over.

    python scripts/trend_desk_replay.py fetch   # GitHub's runner (it reaches Yahoo): -> data/trend_replay/*.json
    python scripts/trend_desk_replay.py run     # -> research/results/TREND-DESK-replay.json
"""

from __future__ import annotations

import hashlib
import json
import re
import statistics
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import scripts.trend_desk as R  # noqa: E402
from aitrader.data.instruments import INDEX_CFDS  # noqa: E402
from aitrader.memory.db import Database  # noqa: E402
from aitrader.position.trend_desk import (INDICES, DailyFeed, DeskClock, TrendDesk, close_time,  # noqa: E402
                                          load_promoted_rules, sessions)
from aitrader.version import stamp  # noqa: E402

DATA = ROOT / "data" / "trend_replay"
OUT = ROOT / "research" / "results" / "TREND-DESK-replay.json"
FROM = date(2003, 1, 1)  # ten month-ends before the first decision
START = date(2004, 1, 2)  # Yahoo's EUR/USD and GBP/USD start in December 2003
UNTIL = date(2026, 11, 6)
FUNDED = ROOT / "research" / "results" / "TRND-1-funded-monthly.json"


def cmd_fetch(now: datetime) -> None:
    DATA.mkdir(parents=True, exist_ok=True)
    for s in INDICES:
        (DATA / f"{s}.json").write_text(json.dumps(R._chart(INDEX_CFDS[s].source, FROM, now)))
    for pair, sym in R.RATES.items():
        (DATA / f"{pair}.json").write_text(json.dumps(R._chart(sym, FROM, now)))
    print("fetched", sorted(p.name for p in DATA.glob("*.json")))


def load(now: datetime):
    bars, problems = {}, []
    for s in INDICES:
        bs, pr = R.parse_bars(s, json.loads((DATA / f"{s}.json").read_text()), now, since=FROM)
        bars[s] = [b for b in bs if b.day <= UNTIL]
        problems += pr
    rates = {pair: R.parse_rates(json.loads((DATA / f"{pair}.json").read_text())) for pair in R.RATES}
    return bars, rates, problems


def new_desk(feed, t0: int, rules, note) -> TrendDesk:
    return TrendDesk.build(Database(":memory:"), feed, DeskClock(t0), rules, note)


def replay(bars, rates) -> dict:
    rules, note = load_promoted_rules()
    feed = DailyFeed(bars, rates)
    by_day = {s: {b.day: b for b in bs} for s, bs in bars.items()}
    first = min(close_time(s, START) for s in INDICES) - 1
    desk = new_desk(feed, first, rules, note)
    accounts = [{"start": str(START), "end": None, "why": None, "pnl": None}]
    refused_entries, stop_codes = [], {}
    years: dict[str, dict] = {}
    equity, prev, peak, worst_dd = [], None, 200_000.0, 0.0

    def year(d: date) -> dict:
        return years.setdefault(str(d.year), {"pnl": 0.0, "failures": 0, "entries": 0, "entries_refused": 0,
                                              "stops": 0, "rule_exits": 0, "stop_moves": 0, "stop_moves_refused": 0,
                                              "late_switches": 0, "fees": 0.0})

    for t, day, syms in sessions(bars, after=first, until=max(close_time(s, UNTIL) for s in INDICES)):
        if any(day not in by_day[s] for s in syms):
            continue
        evs = desk.session(day, {s: by_day[s][day] for s in syms})
        y = year(day)
        for e in evs:
            k = e["kind"]
            if k == "DESK_DECISION" and e.get("action") == "BUY":
                y["entries" if e.get("result") == "FILLED" else "entries_refused"] += 1
                if e.get("result") != "FILLED":
                    refused_entries.append({"day": e.get("day"), "symbol": e.get("symbol"), "result": e.get("result"),
                                            "detail": str(e.get("detail") or "")[:300],
                                            "risk": (e.get("risk") or {}).get("reasons")})
            if k == "DESK_DECISION" and e.get("late"):
                y["late_switches"] += 1
            if k == "DESK_TRADE_CLOSED":
                y["stops" if e.get("reason") == "STOP" else "rule_exits"] += e.get("reason") in ("STOP", "RULE")
                y["fees"] += sum(e.get(x) or 0.0 for x in ("commission", "slippage_cost", "spread_cost"))
            if k == "DESK_STOP":
                y["stop_moves" if e.get("status") == "MOVED" else "stop_moves_refused"] += 1
                if e.get("status") != "MOVED":
                    m = re.search(r"reason=(\w+)", str(e.get("detail") or ""))
                    code = m.group(1) if m else str(e.get("status"))
                    stop_codes[code] = stop_codes.get(code, 0) + 1
        eq = desk.broker.account().equity
        if prev is not None:
            y["pnl"] += eq - prev
        prev = eq
        peak = max(peak, eq)
        worst_dd = max(worst_dd, peak - eq)
        if syms[-1] in ("US500", "NAS100"):  # once a day, after the last close
            equity.append((str(day), round(eq, 2)))
        if desk.state().get("failed"):
            y["failures"] += 1
            accounts[-1].update(end=str(day), why=(desk.state()["failed"].get("lock") or {}).get("code"),
                                pnl=round(eq - 200_000.0, 2))
            accounts.append({"start": str(day), "end": None, "why": None, "pnl": None})
            desk = new_desk(feed, t, rules, note)  # a new challenge from the next session
            prev, peak = 200_000.0, 200_000.0
    accounts[-1].update(end=str(UNTIL), why="the data end", pnl=round(prev - 200_000.0, 2))
    return {"years": years, "accounts": accounts, "equity": equity, "worst_fall_from_peak": round(worst_dd, 2),
            "refused_entries": refused_entries, "stop_refusals_by_code": stop_codes}


def funded_half_by_year() -> dict[str, float]:
    bm = json.loads(FUNDED.read_text())["runs"]["HALF with its stop"]["by_month"]
    out: dict[str, float] = {}
    for k, v in bm.items():
        out[k[:4]] = out.get(k[:4], 0.0) + v
    return out


def cmd_run(now: datetime) -> None:
    bars, rates, problems = load(now)
    r = replay(bars, rates)
    half = funded_half_by_year()
    full = {y: v for y, v in r["years"].items() if START.year <= int(y) < UNTIL.year}
    pct = [v["pnl"] / 2_000 for v in full.values()]
    report = {
        "note": "descriptive: the trend desk's own code on the four indices' real daily bars, on data already judged "
                "(RC-EQ 1990-2020, TRND-1-H 2021-2026); not a test, and the past is not a forecast",
        "period": [str(START), str(UNTIL)], "versions": stamp(), "problems": problems,
        "data_sha256": {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(DATA.glob("*.json"))},
        "summary": {"full_years": len(pct), "mean_year_pct": round(statistics.mean(pct), 2),
                    "median_year_pct": round(statistics.median(pct), 2),
                    "losing_years": sum(p < 0 for p in pct), "worst_year_pct": round(min(pct), 2),
                    "best_year_pct": round(max(pct), 2),
                    "failures": sum(v["failures"] for v in r["years"].values()),
                    "worst_fall_from_peak": r["worst_fall_from_peak"],
                    "entries": sum(v["entries"] for v in r["years"].values()),
                    "entries_refused": sum(v["entries_refused"] for v in r["years"].values()),
                    "stops": sum(v["stops"] for v in r["years"].values()),
                    "stop_moves_refused": sum(v["stop_moves_refused"] for v in r["years"].values())},
        "by_year": {y: {**{k: (round(x, 2) if isinstance(x, float) else x) for k, x in v.items()},
                        "pct": round(v["pnl"] / 2_000, 2),
                        "funded_p_half_pct": round(half.get(y, 0.0) / 2_000, 2) if y in half else None}
                    for y, v in sorted(r["years"].items())},
        "accounts": r["accounts"], "refused_entries": r["refused_entries"],
        "stop_refusals_by_code": r["stop_refusals_by_code"], "equity_daily": r["equity"]}
    OUT.write_text(json.dumps(report, indent=1, sort_keys=True) + "\n")
    print(json.dumps(report["summary"], indent=1))
    for y, v in report["by_year"].items():
        print(y, v["pct"], "FUNDED-P HALF", v["funded_p_half_pct"], "stops", v["stops"], "failures", v["failures"],
              "refused", v["entries_refused"], v["stop_moves_refused"])
    for a in r["accounts"]:
        print("account", a)
    print("stop refusals by code:", r["stop_refusals_by_code"])
    for x in r["refused_entries"]:
        print("refused entry:", x)


def main() -> int:
    now = datetime.now(timezone.utc)
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    {"fetch": lambda: cmd_fetch(now), "run": lambda: cmd_run(now)}.get(cmd, lambda: print(__doc__))()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
