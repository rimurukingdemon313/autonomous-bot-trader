"""The trend desk's run (docs/TREND_DESK.md): TRND-1 traded by the system itself on its own $200,000 paper account,
through the risk engine, the hard risk gate and the paper broker (aitrader/position/trend_desk.py).

PAPER ONLY · NOT REAL MONEY. No broker, no account, no order outside this process, no key. Public Yahoo daily bars for
the four cash indices behind the CFDs (^GSPC, ^NDX, ^GDAXI, ^FTSE) and two conversion rates (EURUSD=X, GBPUSD=X).

- A bar counts 30 minutes after its exchange closes. A session (the indices closing at one moment) is processed once
  every index has a bar at or after it, so a late bar is waited for, never skipped. If a bar is malformed, nothing at
  or after it is processed, and the report says why.
- The account and its record are kept in `<state>/desk.db` and carried from run to run: what the desk did is never
  recomputed. Each session is applied once.

    python scripts/trend_desk.py --state <dir>      # GitHub's runner: fetch, replay the new sessions, write the report
"""

from __future__ import annotations

import argparse
import json
import math
import sys
import urllib.parse
import urllib.request
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from aitrader.data.instruments import INDEX_CFDS  # noqa: E402
from aitrader.memory.db import Database  # noqa: E402
from aitrader.position.trend_desk import (INDICES, RULE_ID, STATE_KEY, STOP_REL, TREND_DESK_VERSION,  # noqa: E402
                                          DailyBar, DailyFeed, DeskClock, TrendDesk, close_time, decision_for,
                                          is_last_weekday, load_promoted_rules, next_month, sessions)
from aitrader.version import stamp  # noqa: E402
from scripts import desk_ledger  # noqa: E402  - the ledger and the trading report: it reads, never trades

START = date(2026, 11, 9)
FETCH_FROM = date(2025, 9, 1)
FINAL_AFTER_S = 30 * 60
RATES = {"EURUSD": "EURUSD=X", "GBPUSD": "GBPUSD=X"}
UA = {"User-Agent": "Mozilla/5.0 (research; aitrader trend desk)"}


def _chart(sym: str, first: date, now: datetime) -> dict:
    p1 = int(datetime(first.year, first.month, first.day, tzinfo=timezone.utc).timestamp())
    url = (f"https://query1.finance.yahoo.com/v8/finance/chart/{urllib.parse.quote(sym)}?period1={p1}"
           f"&period2={int(now.timestamp())}&interval=1d")
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60) as r:
        return json.loads(r.read())["chart"]["result"][0]


def parse_bars(symbol: str, res: dict, now: datetime, since: date = FETCH_FROM) -> tuple[list[DailyBar], list[str]]:
    """The final daily bars of one index, in order, and the problems found. The first malformed bar ends the series:
    nothing at or after it is used."""
    tz = ZoneInfo(res["meta"]["exchangeTimezoneName"])
    q = res["indicators"]["quote"][0]
    bars, problems, seen = [], [], set()
    for i, ts in enumerate(res.get("timestamp") or []):
        day = datetime.fromtimestamp(ts, timezone.utc).astimezone(tz).date()
        if day < since or day in seen:
            continue
        if now.timestamp() < close_time(symbol, day) + FINAL_AFTER_S:
            continue  # not final yet
        o, h, lo, c = (q[k][i] for k in ("open", "high", "low", "close"))
        if all(v is None for v in (o, h, lo, c)):
            continue  # Yahoo's empty row for a closed day
        bar = DailyBar(day, *(float(v) if isinstance(v, (int, float)) else math.nan for v in (o, h, lo, c)))
        bad = bar.problems()
        if bad:
            problems.append(f"{symbol} {bad[0]}: nothing from {day} on is used")
            break
        seen.add(day)
        bars.append(bar)
    return bars, problems


def parse_rates(res: dict) -> dict[date, float]:
    """A conversion rate's daily closes by their own trading day. Yahoo stamps an FX day at 00:00 London, which is
    23:00 UTC the day before in summer: read in UTC, a day's close would be filed under the day before and used a day
    early (the desk uses a day's rate only from the next 00:00 UTC)."""
    tz = ZoneInfo(res["meta"].get("exchangeTimezoneName") or "Europe/London")
    closes = res["indicators"]["quote"][0]["close"]
    return {datetime.fromtimestamp(t, timezone.utc).astimezone(tz).date(): float(c)
            for t, c in zip(res.get("timestamp") or [], closes)
            if isinstance(c, (int, float)) and math.isfinite(c) and c > 0}


def fetch(now: datetime) -> tuple[dict[str, list[DailyBar]], dict[str, dict[date, float]], list[str]]:
    bars, problems = {}, []
    for s in INDICES:
        bs, pr = parse_bars(s, _chart(INDEX_CFDS[s].source, FETCH_FROM, now), now)
        bars[s], problems = bs, problems + pr
    rates = {pair: parse_rates(_chart(sym, FETCH_FROM - timedelta(days=10), now)) for pair, sym in RATES.items()}
    return bars, rates, problems


def ready_until(bars: dict[str, list[DailyBar]]) -> int | None:
    """Sessions before here can be processed: no index can still have a bar to come before it. Each index's next
    possible close is its next weekday's; a holiday, or a bar Yahoo has not published yet, holds every later session
    back until that index's next bar is in, so a late bar is waited for and never skipped."""
    if any(not bars.get(s) for s in INDICES):
        return None
    nxt = []
    for s in INDICES:
        d = bars[s][-1].day
        d += timedelta(days=3 if d.weekday() == 4 else 2 if d.weekday() == 5 else 1)
        nxt.append(close_time(s, d) - 1)
    return min(nxt)


def run(state_dir: Path, now: datetime, bars: dict[str, list[DailyBar]], rates: dict[str, dict[date, float]],
        problems: list[str] | None = None, rules_path: Path | None = None) -> dict:
    """Replay every new session since the desk's last one, then write the reports. Returns the state written.

    After each session its account is recorded for the ledger (DESK_EQUITY). The ledger and TRADING_REPORT.md only
    read the record: if either fails, the desk's own state and REPORT.md are still written, and the failure is said."""
    state_dir.mkdir(parents=True, exist_ok=True)
    problems = list(problems or [])
    db = Database(state_dir / "desk.db")
    rules, note = load_promoted_rules(rules_path) if rules_path else load_promoted_rules()
    feed = DailyFeed(bars, rates)
    st = db.get_kv(STATE_KEY, None) or {}
    first = min(close_time(s, START) for s in INDICES) - 1
    last = st.get("last_session")
    clock = DeskClock(last if last is not None else first)
    desk = TrendDesk.build(db, feed, clock, rules, note)
    until = ready_until(bars)
    done = []
    if until is not None:
        until = min(until, int(now.timestamp()) - FINAL_AFTER_S)
        by_day = {s: {b.day: b for b in bs} for s, bs in bars.items()}
        for t, day, symbols in sessions(bars, after=max(last or first, first), until=until):
            desk.session(day, {s: by_day[s][day] for s in symbols})
            done.append(f"{day} {datetime.fromtimestamp(t, timezone.utc):%H:%M} UTC {','.join(symbols)}")
            try:
                desk_ledger.record_session(db, desk, t, day, symbols)
            except Exception as e:  # a record for the report never stops the desk; the ledger lists the gap
                problems.append(f"the {day} session's equity was not recorded for the ledger: {type(e).__name__}: {e}")
    state = snapshot(desk, now, bars, problems, done)
    db.query("PRAGMA wal_checkpoint(TRUNCATE)")  # everything in desk.db itself: it is the file carried to the next run
    (state_dir / "state.json").write_text(json.dumps(state, indent=1, sort_keys=True, default=str) + "\n")
    (state_dir / "REPORT.md").write_text(report(state))
    try:
        desk_ledger.write(state_dir, db, desk, now)
    except Exception as e:  # the desk's state and REPORT.md are already written: the report says what failed
        desk_ledger.write_failure(state_dir, e, now)
    return state


# ── the record ──────────────────────────────────────────────────────────────

def _events(db: Database, kind: str) -> list[dict]:
    return [json.loads(r["payload"]) | {"_ref": r.get("ref")} for r in
            db.query("SELECT payload, ref FROM events WHERE type=? ORDER BY seq", (kind,))]


def snapshot(desk: TrendDesk, now: datetime, bars: dict[str, list[DailyBar]], problems: list[str],
             done: list[str]) -> dict:
    db, b = desk.db, desk.broker
    st = desk.state()
    acct = b.account()
    gate = desk.gate.status()
    positions = []
    for p in b.positions():
        q, spec = b.quote(p.symbol), b.spec(p.symbol)
        px = q.bid if q else None
        units = p.qty * spec.contract_size * spec.value_per_price_unit if spec else None
        positions.append({"symbol": p.symbol, "units": p.qty, "entry": round(p.entry, 2), "price": px,
                          "stop": p.stop, "opened": datetime.fromtimestamp(p.opened, timezone.utc).isoformat(),
                          "pnl": round((px - p.entry) * units, 2) if px is not None and units else None,
                          "notional_usd": round(px * units, 2) if px is not None and units else None})
    decisions = {}
    for e in _events(db, "DESK_DECISION"):
        decisions[e["symbol"]] = {k: e.get(k) for k in ("day", "for_month", "action", "result", "hold", "month_end",
                                                         "month_end_close", "mean_of_ten", "why", "late")}
    trades = [{k: e.get(k) for k in ("symbol", "entry", "exit", "qty", "opened", "closed", "reason", "pnl", "r")}
              for e in _events(db, "DESK_TRADE_CLOSED")]
    stops = _events(db, "DESK_STOP")
    refused = [e for e in stops if e.get("status") != "MOVED"]
    day = gate.get("day") or {}
    last = st.get("last_session")
    nxt = {}
    for s in INDICES:
        bs = bars.get(s) or []
        if bs:
            d = bs[-1].day
            m = (d.year, d.month)
            target = next_month(m) if is_last_weekday(d) else m
            nxt[s] = decision_for({x.day: x.close for x in bs}, target) | {"latest_close": bs[-1].close,
                                                                            "latest_day": str(d)}
    return {"version": TREND_DESK_VERSION, "rule": RULE_ID, "updated": now.isoformat(), "start": str(START),
            "paper_only": True, "real_money": False, "profile": desk.gate.profile.name,
            "promotion": desk.rules_note, "rule_status": next((r.status + "/" + r.health for r in desk.rules
                                                               if r.rule_id == RULE_ID), "not promoted"),
            "account": {"balance": round(acct.balance, 2), "equity": round(acct.equity, 2),
                        "pnl": round(acct.equity - desk.gate.profile.starting_balance, 2),
                        "today_reference": day.get("reference"), "day": day.get("id")},
            "gate": {k: gate.get(k) for k in ("state", "risk_status", "lock", "kill", "trading_days",
                                              "challenge_objective_met", "daily_limit_violations")},
            "failed": st.get("failed"), "last_session": (datetime.fromtimestamp(last, timezone.utc).isoformat()
                                                         if last else None),
            "positions": positions, "decisions": decisions, "rule_now": nxt, "trades": trades,
            "stop_moves": len(stops) - len(refused), "stops_refused": refused[-10:], "processed_this_run": done,
            "problems": problems, "versions": stamp()}


def _money(x) -> str:
    return "unknown" if x is None else f"${x:,.0f}" if x >= 0 else f"-${-x:,.0f}"


def _r(x) -> str:
    return "—" if x is None else f"{x:+.2f}"


def _px(x) -> str:
    return "—" if x is None else f"{x:,.2f}"


def report(s: dict) -> str:
    a, g = s["account"], s["gate"]
    held = [p["symbol"] for p in s["positions"]]
    failed = s.get("failed")
    lines = ["# TREND DESK · TRND-1 traded by the system itself · PAPER ONLY · NOT REAL MONEY", ""]
    status_ar = ("الحساب فشل (" + str((failed or {}).get("day")) + ") وتسكّرت كل صفقاته" if failed else
                 "الحساب شغّال" if g.get("state") == "ACTIVE" else
                 f"الحساب بعده ما بدا: أول جلسة عند إغلاق {s['start']}" if g.get("state") == "NOT_STARTED" else
                 f"الحساب {g.get('state')}")
    lines += ["**بالعربي:** هذا حساب ورقي بـ$200,000 يتداول بيه النظام قاعدة TRND-1 وحده، من غير ما أحد يدخل صفقة "
              f"بإيده. الرصيد الحالي (مع الصفقات المفتوحة) {_money(a['equity'])}، يعني الربح أو الخسارة من البداية "
              f"{_money(a['pnl'])}. {status_ar}. "
              + (f"الماسكهم هسه: {'، '.join(held)}." if held else "ما ماسك ولا مؤشر هسه.")
              + " كل مؤشر ماسكه عليه وقف تحت آخر إغلاق بـ6%، ويتحرك كل مساء. هذا ورق، مو فلوس حقيقية، والماضي "
                "ما يضمن المستقبل.", ""]
    lines += ["| | |", "|---|---|",
              f"| Account | {s['profile']}: $200,000 paper, from {s['start']} |",
              f"| Equity | {_money(a['equity'])} (P/L {_money(a['pnl'])}); balance {_money(a['balance'])} |",
              (f"| Today | reference {_money(a['today_reference'])} on {a['day']}; the day may lose $10,000 at most |"
               if a["day"] else f"| Today | not started: the first session is the close of {s['start']} |"),
              f"| Risk | {g.get('risk_status') or '—'} ({g.get('state')})"
              + (f"; FAILED on {failed['day']}" if failed else "") + " |",
              f"| Rule | {s['rule']}: {s['rule_status']} ({s['promotion']}) |",
              f"| Last session | {s['last_session'] or 'none yet'} |",
              f"| Updated | {s['updated']} |", ""]
    lines += ["## Positions", "", "| Index | Units | Entry | Last close | Stop | P/L | Notional |", "|---|---|---|---|---|---|---|"]
    for p in s["positions"]:
        lines.append(f"| {p['symbol']} | {p['units']} | {_px(p['entry'])} | {_px(p['price'])} | {_px(p['stop'])} | "
                     f"{_money(p['pnl'])} | {_money(p['notional_usd'])} |")
    if not s["positions"]:
        lines.append("| none | | | | | | |")
    lines += ["", "## The rule now", "",
              "| Index | For | Decision | Month-end close | Ten-month mean | Latest close | Its stop if held |",
              "|---|---|---|---|---|---|---|"]
    for sym, r in s["rule_now"].items():
        dec = "HOLD" if r["hold"] else "flat" if r["hold"] is False else "unknown: flat"
        mc = f"{r['month_end_close']:,.2f} ({r['month_end']})" if r["month_end_close"] else "—"
        mm = f"{r['mean_of_ten']:,.2f}" if r["mean_of_ten"] else "—"
        lines.append(f"| {sym} | {r['month']} | **{dec}** | {mc} | {mm} | {r['latest_close']:,.2f} ({r['latest_day']}) "
                     f"| {r['latest_close'] * (1 - STOP_REL):,.2f} |")
    lines += ["", "## Closed trades", "", "| Index | Opened | Closed | Entry | Exit | Why | P/L | R |",
              "|---|---|---|---|---|---|---|---|"]
    for t in s["trades"]:
        op = datetime.fromtimestamp(t["opened"], timezone.utc).date() if t.get("opened") else "—"
        cl = datetime.fromtimestamp(t["closed"], timezone.utc).date() if t.get("closed") else "—"
        lines.append(f"| {t['symbol']} | {op} | {cl} | {_px(t['entry'])} | {_px(t['exit'])} | {t['reason']} | "
                     f"{_money(t['pnl'])} | {_r(t.get('r'))} |")
    if not s["trades"]:
        lines.append("| none yet | | | | | | | |")
    lines += ["", f"Stops moved: {s['stop_moves']}. Refused or unknown: {len(s['stops_refused'])}."]
    if s["problems"]:
        lines += ["", "## Data problems", ""] + [f"- {p}" for p in s["problems"]]
    lines += ["", "## How it trades", "",
              "- TRND-1: an index is held for a month if its month-end close is above the mean of its ten month-end "
              "closes; otherwise nothing is held. Long or flat, never short.",
              "- The switch is at the close of the month's last weekday (the next close, if that day is a holiday).",
              "- Each entry is sized by the risk engine: at most $1,500 lost at its stop, all costs included. The hard "
              "gate checks every order and every stop move and issues the only permit the paper broker accepts.",
              "- The stop is 6% below each close and moves after every close. After it is hit, the index stays flat "
              "until the next month-end decision.",
              "- Limits: $10,000 in a day (each session's intraday low included), $20,000 in all. A breach fails the "
              "account and closes every position, as a firm would.",
              "", f"Versions: {', '.join(f'{k} {v}' for k, v in sorted(s['versions'].items()))}", ""]
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--state", required=True, type=Path)
    args = ap.parse_args()
    now = datetime.now(timezone.utc)  # the command line's clock: every function above takes it as an argument
    bars, rates, problems = fetch(now)
    s = run(args.state, now, bars, rates, problems)
    print(json.dumps({k: s[k] for k in ("account", "gate", "last_session", "processed_this_run", "problems")},
                     indent=1, default=str))
    for p in s["positions"]:
        print(p)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
