"""The TRINITY desk's run (docs/TRINITY.md): the owner's TRINITY-MASTER on its own $200,000 paper account, through the
risk engine, the hard risk gate and the paper broker (aitrader/position/trinity_paper_desk.py).

PAPER ONLY · NOT REAL MONEY · AN UNVALIDATED RULE. No broker, no account, no order outside this process, no key.
Public Yahoo daily bars (scripts/trinity_data.py): the signals QQQ, SPY, GLD, DBC; the sensors ^VIX, TLT, UUP; the
prices ^NDX (NAS100), ^GSPC (US500), GLD (XAUUSD) and USO (USOIL); GC=F and CL=F, read once, for the level the gold
and oil proxies are quoted at.

- A bar counts 30 minutes after the New York close. A session is processed once every series has a bar at or after
  it, so a late bar is waited for, never skipped. Each session is applied once; the account is carried in
  `<state>/desk.db` from run to run, and what the desk did is never recomputed.
- The proxies' scale: at the desk's first session, XAUUSD = GLD x (GC=F / GLD) and USOIL = USO x (CL=F / USO) at that
  close, fixed for good and kept in desk.db. Returns are GLD's and USO's: what a swap-free spot gold or rolled oil
  CFD earns. A continuous futures series is not used for returns: it jumps at every roll.
- The design book: the package's own weights at their own size (no stops, its 8 bp cost, its additive equity on
  $200,000), from the anchor, marked every day on the four funds it was written for. It is a measurement of the
  package's claim going forward. It is never traded and never added to the desk's figures.
- The daily audit (`<state>/research/results/TRINITY-MASTER-daily-audit.json`, the spec's file): every session's
  positions, stops, the loss at the stops, the margin, and the package's three HardRiskGate checks, measured.

    python scripts/trinity_paper_desk.py --state <dir>                       # GitHub's runner: fetch, run, report
    python scripts/trinity_paper_desk.py --state <dir> --history <dir>       # the same from stored bars
    python scripts/trinity_paper_desk.py --replay <first> --history <dir> --state <dir>   # the desk's own code on
                                                                                         # history (descriptive)
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from aitrader.memory.db import Database  # noqa: E402
from aitrader.position import trinity as T  # noqa: E402
from aitrader.position.trend_desk import DailyBar, DeskClock, PromotedRule, load_promoted_rules  # noqa: E402
from aitrader.position.trinity_paper_desk import (INSTRUMENTS, PRICE_SOURCE, RULE_ID, SCALE_TO, START,  # noqa: E402
                                                  STATE_KEY, TRINITY_DESK_VERSION, TZ, TrinityFeed, TrinityPaperDesk,
                                                  close_time)
from aitrader.version import stamp  # noqa: E402
from scripts import desk_ledger  # noqa: E402  - the ledger: it reads, never trades
from scripts import trinity_data as TD  # noqa: E402

FETCH_FROM = date(2025, 1, 1)
FINAL_AFTER_S = 30 * 60
SIGNAL_SOURCE = {"QQQ": "QQQ", "SPY": "SPY", "GLD": "GLD", "DBC": "DBC", "VIX": "^VIX", "TLT": "TLT", "UUP": "UUP"}
NEEDED = sorted(set(SIGNAL_SOURCE.values()) | set(PRICE_SOURCE.values()) | set(SCALE_TO.values()))
SCALE_KEY = "trinity_scale"
AUDIT_PATH = Path("research") / "results" / "TRINITY-MASTER-daily-audit.json"
START_BALANCE = 200_000.0


# ── the bars ────────────────────────────────────────────────────────────────

def final(now: datetime):
    t = now.timestamp()
    return lambda day: t >= close_time(day) + FINAL_AFTER_S


def fetch(now: datetime, first: date = FETCH_FROM, chart=TD.chart) -> tuple[dict, list[str]]:
    """{symbol: {iso day: {o, h, l, c, adj, v}}} for every series the desk reads, final bars only, and problems."""
    series, problems = {}, []
    ok = final(now)
    for sym in NEEDED:
        rows, pr = TD.parse(chart(sym, first, now), now, is_final=ok)
        series[sym] = rows
        problems += [f"{sym} {p}" for p in pr]
    return series, problems


def load_history(history: Path, now: datetime) -> tuple[dict, list[str]]:
    """The same from stored history (scripts/trinity_data.py's files), cut at `now`'s final bars."""
    ok = final(now)
    out = {}
    for sym in NEEDED:
        name = sym.replace("^", "_").replace("=", "_")
        rows = json.loads((history / f"{name}.json").read_text())
        out[sym] = {d: r for d, r in rows.items() if ok(date.fromisoformat(d))}
    return out, []


def _bar(day: date, r: dict, k: float = 1.0) -> DailyBar | None:
    vals = [r.get(x) for x in ("o", "h", "l", "c")]
    if any(not isinstance(v, (int, float)) or not math.isfinite(v) or v <= 0 for v in vals):
        return None
    return DailyBar(day, *(float(v) * k for v in vals))


def signal_closes(series: dict) -> tuple[dict[str, dict[date, float]], list[date]]:
    """The closes the rule reads, by its own names, and the days on which every one of them closed."""
    closes = {name: {date.fromisoformat(d): float(r["c"]) for d, r in series[src].items()
                     if isinstance(r.get("c"), (int, float)) and r["c"] > 0}
              for name, src in SIGNAL_SOURCE.items()}
    days = sorted(set.intersection(*(set(c) for c in closes.values())))
    return closes, days


def scale_of(db: Database, series: dict, day: date) -> dict:
    """The scale of the two commodity proxies at `day`'s close, stored. `run` calls it once, at the desk's first
    session; it is never changed after."""
    out = {}
    for cfd, fut in SCALE_TO.items():
        proxy = PRICE_SOURCE[cfd]
        f, p = (series[fut].get(day.isoformat()) or {}).get("c"), (series[proxy].get(day.isoformat()) or {}).get("c")
        if not (isinstance(f, (int, float)) and isinstance(p, (int, float)) and f > 0 and p > 0):
            raise ValueError(f"{day}: no {fut} or {proxy} close to set {cfd}'s scale")
        out[cfd] = {"k": f / p, "day": day.isoformat(), "futures": fut, "futures_close": f, "proxy": proxy,
                    "proxy_close": p}
    db.set_kv(SCALE_KEY, out, reason=f"trinity desk: the proxies' scale, fixed at {day}")
    return out


def cfd_bars(series: dict, scale: dict) -> dict[str, list[DailyBar]]:
    out = {}
    for cfd in INSTRUMENTS:
        k = scale[cfd]["k"] if cfd in scale else 1.0
        bars = [_bar(date.fromisoformat(d), r, k) for d, r in sorted(series[PRICE_SOURCE[cfd]].items())]
        out[cfd] = [b for b in bars if b is not None]
    return out


def ready_until(bars: dict[str, list[DailyBar]], days: list[date]) -> int | None:
    """Sessions up to here can be processed: every price and signal series has a bar this late."""
    if not days or any(not bars.get(s) for s in INSTRUMENTS):
        return None
    return min([close_time(bars[s][-1].day) for s in INSTRUMENTS] + [close_time(days[-1])])


# ── the design book: the package's weights at their own size, measured ─────

def design_book(closes: dict, days: list[date], anchor: date, ohlc: dict[str, dict[date, tuple]]) -> dict:
    """From the anchor: each rebalance's weights (the package's, its drawdown brake on this book's own equity), held
    to the next rebalance and marked at every close and every low on QQQ, SPY, GLD and DBC; the package's 8 bp per unit
    of weight changed; equity in the package's additive kind, on $200,000. Never traded."""
    if anchor not in days:
        return {"rows": [], "why": f"the anchor {anchor} has no close yet"}
    g = T.grid(days, anchor)
    rows = T.rows_at(g, closes, days)
    at = next((i for i, r in enumerate(rows) if r["date"] == anchor), None)
    if at is None or at < T.WARMUP:
        return {"rows": [], "why": "not enough grid rows before the anchor"}
    dec = T.decide(T.features(rows), book_start=at)
    eq, prev, daily, rebal = 0.0, {a: 0.0 for a in T.ASSETS}, [], []
    for k, d in enumerate(dec):
        d0 = d["date"]
        w = d["weights"]
        eq -= sum(abs(w[a] - prev[a]) for a in T.ASSETS) * T.COST
        prev = dict(w)
        rebal.append({"day": str(d0), "weights": {a: round(w[a], 6) for a in T.ASSETS}, "buy": d["buy"]})
        d1 = dec[k + 1]["date"] if k + 1 < len(dec) else None
        entry = {a: closes[a][d0] for a in T.ASSETS}
        span = [x for x in days if x > d0 and (d1 is None or x <= d1)]
        mark = 0.0
        for x in span:
            mark = sum(w[a] * (ohlc[a][x][3] / entry[a] - 1) for a in T.ASSETS if x in ohlc[a])
            low = sum(w[a] * (ohlc[a][x][2] / entry[a] - 1) for a in T.ASSETS if x in ohlc[a])
            daily.append({"day": str(x), "equity": round(START_BALANCE * (1 + eq + mark), 2),
                          "equity_at_lows": round(START_BALANCE * (1 + eq + low), 2)})
        if d1 is not None:
            eq += sum(w[a] * (closes[a][d1] / entry[a] - 1) for a in T.ASSETS)
    worst, peak, fail_total, fail_daily, prev_close = 0.0, START_BALANCE, None, None, START_BALANCE
    for r in daily:
        peak = max(peak, r["equity"])
        worst = min(worst, r["equity_at_lows"] - peak)
        if fail_total is None and r["equity_at_lows"] <= START_BALANCE * 0.90:
            fail_total = r["day"]
        if fail_daily is None and r["equity_at_lows"] - prev_close <= -0.05 * START_BALANCE:
            fail_daily = r["day"]
        prev_close = r["equity"]
    last = daily[-1]["equity"] if daily else START_BALANCE
    return {"anchor": str(anchor), "rebalances": rebal, "daily": daily, "equity": last,
            "pnl": round(last - START_BALANCE, 2), "max_drawdown_at_lows_usd": round(worst, 2),
            "would_fail": {"max_loss_10pct": fail_total, "daily_loss_5pct": fail_daily}}


# ── the run ─────────────────────────────────────────────────────────────────

def run(state_dir: Path, now: datetime, series: dict, problems: list[str] | None = None,
        rules: list[PromotedRule] | None = None, rules_note: str | None = None, anchor: date = START) -> dict:
    state_dir.mkdir(parents=True, exist_ok=True)
    problems = list(problems or [])
    db = Database(state_dir / "desk.db")
    if rules is None:
        rules, rules_note = load_promoted_rules()
    closes, days = signal_closes(series)
    st = db.get_kv(STATE_KEY, None) or {}
    first = close_time(anchor) - 1
    last = st.get("last_session")
    clock = DeskClock(last if last is not None else first)
    done = []
    scale = db.get_kv(SCALE_KEY, None)
    first_day = next((d for d in days if d >= anchor), None)
    if not (isinstance(scale, dict) and all(s in scale for s in SCALE_TO)) and first_day is not None \
            and final(now)(first_day):
        try:
            scale = scale_of(db, series, first_day)
        except ValueError as e:
            problems.append(str(e))
            scale = None
    desk = None
    if isinstance(scale, dict):
        bars = cfd_bars(series, scale)
        feed = TrinityFeed(bars)
        desk = TrinityPaperDesk.build(db, feed, clock, rules, rules_note or "", anchor=anchor)
        until = ready_until(bars, days)
        if until is not None:
            until = min(until, int(now.timestamp()) - FINAL_AFTER_S)
            by_day = {s: {b.day: b for b in bs} for s, bs in bars.items()}
            signal_days = set(days)
            after = max(last or first, first)
            every = set(signal_days).union(*(set(v) for v in by_day.values()))
            for day in sorted(d for d in every if d >= anchor and after < close_time(d) <= until):
                missing = [s for s in INSTRUMENTS if day not in by_day[s]] + ([] if day in signal_days else
                                                                              ["a signal's close"])
                if missing:  # a hole in one series while others have the day: wait for it, never skip it
                    problems.append(f"{day}: no bar yet for {', '.join(missing)}: the desk waits at this day")
                    break
                desk.session(day, {s: by_day[s][day] for s in INSTRUMENTS}, closes, days)
                done.append(str(day))
                try:
                    desk_ledger.record_session(db, desk, close_time(day), day, list(INSTRUMENTS))
                except Exception as e:  # a record for the report never stops the desk
                    problems.append(f"the {day} session's equity was not recorded: {type(e).__name__}: {e}")
    ohlc = {a: {date.fromisoformat(d): (r["o"], r["h"], r["l"], r["c"]) for d, r in series[SIGNAL_SOURCE[a]].items()
                if all(isinstance(r.get(x), (int, float)) for x in ("o", "h", "l", "c"))} for a in T.ASSETS}
    book = design_book(closes, days, anchor, ohlc)
    state = snapshot(desk, db, now, days, anchor, problems, done, scale, book, rules_note)
    if desk is not None:
        db.query("PRAGMA wal_checkpoint(TRUNCATE)")
    (state_dir / "state.json").write_text(json.dumps(state, indent=1, sort_keys=True, default=str) + "\n")
    (state_dir / "design_book.json").write_text(json.dumps(book, indent=1, default=str) + "\n")
    audit = audit_file(db, state)
    (state_dir / AUDIT_PATH).parent.mkdir(parents=True, exist_ok=True)
    (state_dir / AUDIT_PATH).write_text(json.dumps(audit, indent=1, default=str) + "\n")
    (state_dir / "REPORT.md").write_text(report(state, book))
    if desk is not None:
        try:
            led = desk_ledger.ledger(db, desk, strategy=RULE_ID, signal=_signal)
            perf = desk_ledger.performance(led, START_BALANCE)
            _write_csvs(state_dir, led)
            (state_dir / "TRADING_REPORT.md").write_text(trading_report(perf, led, now, state))
        except Exception as e:  # the desk's own state and REPORT.md are written: say what failed, leave no stale CSV
            for name in ("ledger.csv", "equity.csv"):
                (state_dir / name).unlink(missing_ok=True)
            (state_dir / "TRADING_REPORT.md").write_text(
                f"# TRINITY desk: paper-trading performance\n\n**NOT WRITTEN** at {now:%Y-%m-%d %H:%M} UTC: "
                f"{type(e).__name__}: {e}. desk.db and REPORT.md are unaffected.\n")
    return state


def _signal(dec: dict | None) -> str:
    if not dec:
        return "unknown: no opening decision recorded"
    return (f"{RULE_ID} BUY at the {dec.get('for_rebalance')} rebalance: {dec.get('signal_asset')} weight "
            f"{dec.get('weight'):.4f} (EXPERIMENTAL: sized by the risk engine, not by the weight)")


def _write_csvs(state_dir: Path, led: dict) -> None:
    import csv
    with open(state_dir / "ledger.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=desk_ledger.CSV_COLUMNS, extrasaction="ignore")
        w.writeheader()
        for r in led["rows"]:
            w.writerow(r)
    with open(state_dir / "equity.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["session_utc", "day", "symbols", "equity", "balance", "open_pnl", "gross_exposure_usd", "leverage"])
        for s in led["snaps"]:
            w.writerow([desk_ledger._iso(s["t"]), s["day"], " ".join(s["symbols"]), s["equity"], s["balance"],
                        s["open_pnl"], s["gross_exposure_usd"], s["leverage"]])


def _events(db: Database, kind: str) -> list[dict]:
    return [json.loads(r["payload"]) | {"_ref": r.get("ref")} for r in
            db.query("SELECT payload, ref FROM events WHERE type=? ORDER BY seq", (kind,))]


def next_rebalance(days: list[date], anchor: date) -> date:
    """The next grid day after the last known close, counting weekdays beyond it: about, since a holiday moves it a
    day later (the desk itself counts real closes)."""
    base = [d for d in days if d >= anchor]
    if not base:
        return anchor
    left = T.STEP - (len(base) - 1) % T.STEP
    d = base[-1]
    while left:
        d += timedelta(days=1)
        if d.weekday() < 5:
            left -= 1
    return d


def snapshot(desk, db: Database, now: datetime, days: list[date], anchor: date, problems: list[str], done: list[str],
             scale, book: dict, rules_note) -> dict:
    base = {"version": TRINITY_DESK_VERSION, "rule": RULE_ID, "updated": now.isoformat(), "anchor": str(anchor),
            "paper_only": True, "real_money": False, "validated": False, "profile": "TRINITY-PAPER-200K",
            "promotion": rules_note, "processed_this_run": done, "problems": problems, "scale": scale,
            "versions": stamp(), "last_close_known": str(days[-1]) if days else None}
    if desk is None:
        return {**base, "account": None, "positions": [], "rebalances": [], "trades": [], "failed": None,
                "rule_status": "not started", "next_rebalance": str(next_rebalance(days, anchor)),
                "last_session": None, "gate": None}
    b, st = desk.broker, desk.state()
    acct, gate = b.account(), desk.gate.status()
    positions = []
    for p in b.positions():
        q, spec = b.quote(p.symbol), b.spec(p.symbol)
        px = q.bid if q else None
        units = p.qty * spec.contract_size * spec.value_per_price_unit if spec else None
        positions.append({"symbol": p.symbol, "qty": p.qty, "entry": round(p.entry, 4), "price": px, "stop": p.stop,
                          "opened": datetime.fromtimestamp(p.opened, timezone.utc).isoformat(),
                          "pnl": round((px - p.entry) * units, 2) if px is not None and units else None,
                          "notional_usd": round(px * units, 2) if px is not None and units else None})
    rebalances = [{k: e.get(k) for k in ("day", "decided", "why", "weights", "buy", "rule")}
                  for e in _events(db, "DESK_REBALANCE")]
    trades = [{k: e.get(k) for k in ("symbol", "entry", "exit", "qty", "opened", "closed", "reason", "pnl", "r")}
              for e in _events(db, "DESK_TRADE_CLOSED")]
    last = st.get("last_session")
    last_day = datetime.fromtimestamp(last, timezone.utc).astimezone(TZ).date() if last else None
    rule, why = desk.rule()
    return {**base, "account": {"balance": round(acct.balance, 2), "equity": round(acct.equity, 2),
                                "pnl": round(acct.equity - START_BALANCE, 2)},
            "gate": {k: gate.get(k) for k in ("state", "risk_status", "lock", "kill", "trading_days")},
            "failed": st.get("failed"), "positions": positions, "rebalances": rebalances[-12:], "trades": trades,
            "rule_status": why, "last_session": str(last_day) if last_day else None,
            "next_rebalance": str(next_rebalance(days, anchor))}


def audit_file(db: Database, state: dict) -> dict:
    rows = [{k: v for k, v in e.items() if k not in ("versions", "_ref")} for e in _events(db, "DESK_AUDIT")]
    bad = [r["day"] for r in rows if any(v is False for v in (r.get("checks") or {}).values())]
    unknown = [r["day"] for r in rows if any(v is None for v in (r.get("checks") or {}).values())]
    return {"rule": RULE_ID, "version": TRINITY_DESK_VERSION, "paper_only": True, "validated": False,
            "updated": state["updated"], "sessions": len(rows), "sessions_failing_a_check": bad,
            "sessions_with_a_check_unknown": unknown,
            "checks": {"every_position_has_a_stop": "the package's MISSING_STOP_LOSS",
                       "loss_at_stops_within_4pct": "the package's OPEN_RISK_LIMIT (4% of the starting balance)",
                       "margin_within_equity": "the package's MARGIN_UNAVAILABLE (margin at 1:10)"},
            "rows": rows}


# ── the reports ─────────────────────────────────────────────────────────────

def _money(x) -> str:
    return "unknown" if x is None else f"${x:,.0f}" if x >= 0 else f"-${-x:,.0f}"


def _px(x) -> str:
    return "—" if x is None else f"{x:,.2f}"


STATUS = ("**What this is.** The owner's TRINITY-MASTER (research/external/trinity/), traded on paper so its record "
          "starts now. It is **EXPERIMENTAL**: its 20-year figures come from a backtest on 288 dates its author chose, "
          "and on real daily prices they did not hold as stated (research/results/TRINITY-MASTER-redteam.json, "
          "docs/TRINITY.md). The risk engine sizes every position as it sizes any unvalidated rule: at most 0.25% of "
          "the starting balance lost at its stop. No DEMO, no live account, no real money.")


def report(s: dict, book: dict) -> str:
    a = s.get("account")
    L = ["# TRINITY DESK · TRINITY-MASTER on paper · PAPER ONLY · NOT REAL MONEY · NOT VALIDATED", ""]
    if a is None:
        L += ["**بالعربي:** حساب TRINITY الورقي ($200,000) بعده ما بدا: أول جلسة عند إغلاق "
              f"{s['anchor']}. هذا ورق، مو فلوس حقيقية، والقاعدة ما انعتمدت.", "", STATUS, "",
              f"Last close known: {s['last_close_known']}. Problems: {'; '.join(s['problems']) or 'none'}.", ""]
        return "\n".join(L)
    held = [p["symbol"] for p in s["positions"]]
    L += ["**بالعربي:** حساب ورقي بـ$200,000 يتداول بيه النظام قاعدة TRINITY-MASTER اللي بعثها المالك. القاعدة "
          "تجريبية ما انعتمدت، فمحرك المخاطر يحدد حجم كل صفقة بحد 0.25% من الرصيد. الرصيد الحالي "
          f"{_money(a['equity'])}، يعني من البداية {_money(a['pnl'])}. "
          + (f"الماسكهم هسه: {'، '.join(held)}." if held else "ما ماسك شي هسه.")
          + f" إعادة التوازن الجاية: {s['next_rebalance']}. هذا ورق، مو فلوس حقيقية.", "", STATUS, ""]
    g = s.get("gate") or {}
    L += ["| | |", "|---|---|",
          f"| Account | {s['profile']}: $200,000 paper, from {s['anchor']} |",
          f"| Equity | {_money(a['equity'])} (P/L {_money(a['pnl'])}); balance {_money(a['balance'])} |",
          f"| Risk | {g.get('risk_status') or '—'} ({g.get('state')})"
          + (f"; FAILED on {s['failed']['day']}" if s.get("failed") else "") + " |",
          f"| Rule | {s['rule_status']} |",
          f"| Last session | {s['last_session'] or 'none yet'}; next rebalance about {s['next_rebalance']} |",
          f"| Updated | {s['updated']} |", ""]
    L += ["## Positions", "", "| Instrument | Qty | Entry | Last close | Stop | P/L | Notional |",
          "|---|---|---|---|---|---|---|"]
    L += [f"| {p['symbol']} | {p['qty']} | {_px(p['entry'])} | {_px(p['price'])} | {_px(p['stop'])} | "
          f"{_money(p['pnl'])} | {_money(p['notional_usd'])} |" for p in s["positions"]] or ["| none | | | | | | |"]
    L += ["", "## Rebalances (the last twelve)", "", "| Day | Weights QQQ / SPY / GLD / DBC | Held after |",
          "|---|---|---|"]
    for r in s["rebalances"]:
        w = r.get("weights") or {}
        ws = " / ".join(f"{w.get(x, 0):.3f}" for x in T.ASSETS) if w else (r.get("why") or "not decided")
        L.append(f"| {r['day']} | {ws} | {', '.join(r.get('buy') or []) or 'nothing'} |")
    if not s["rebalances"]:
        L.append("| none yet | | |")
    L += ["", "## The design book: the package's weights at their own size (measured, never traded)", ""]
    if book.get("daily"):
        wf = book["would_fail"]
        L += [f"From {book['anchor']}: equity {_money(book['equity'])} (P/L {_money(book['pnl'])}), worst fall at the "
              f"lows {_money(book['max_drawdown_at_lows_usd'])}. A firm's 10% maximum loss: "
              f"{wf['max_loss_10pct'] or 'not reached'}; its 5% daily loss: {wf['daily_loss_5pct'] or 'not reached'}. "
              "This is what the package claims to do, measured on the four funds it was written for. It is kept "
              "apart from the account above and never added to it.", ""]
    else:
        L += [f"Not started: {book.get('why') or 'no session yet'}.", ""]
    if s["problems"]:
        L += ["## Data problems", ""] + [f"- {p}" for p in s["problems"]] + [""]
    L += ["## How it trades", "",
          "- Every 15th trading day from the anchor, at the New York close: TRINITY-MASTER's weights from QQQ, SPY, GLD "
          "and DBC, the VIX, TLT and UUP read at the previous close. A weight above 1e-4 is held: NAS100, US500, XAUUSD, "
          "USOIL. The others are closed.",
          "- Each entry is sized by the risk engine (0.25% of the starting balance at its stop for an unvalidated rule), "
          "with a stop 3.2% below the rebalance close. A stop hit leaves the instrument flat until the next rebalance.",
          "- The hard gate checks every order and stop move and issues the only permit the paper broker accepts. "
          "Limits: $10,000 in a day (intraday lows included), $20,000 in all; a breach fails the account and closes "
          "everything.", "", f"Versions: {', '.join(f'{k} {v}' for k, v in sorted(s['versions'].items()))}", ""]
    return "\n".join(L)


def trading_report(perf: dict, led: dict, now: datetime, s: dict) -> str:
    L = ["# TRINITY desk: paper-trading performance", "",
         "**PAPER TRADING · NOT REAL MONEY · NOT A BACKTEST · NOT VALIDATED.** TRINITY-MASTER traded forward by the "
         f"system from {s['anchor']}, sized by the risk engine as an unvalidated rule. Backtest figures, the design "
         "book and the red team are never added here.", "",
         f"**بالعربي:** الرصيد {_money(perf['equity'])}، من البداية {_money(perf['net_since_start'])}. المحقّق "
         f"{_money(perf['realized_net'])}، غير المحقّق {_money(perf['unrealized'])}. الصفقات المسكّرة "
         f"{perf['closed_trades']} (ربحت {perf['won']}، خسرت {perf['lost']}). أكبر نزول {_money(perf['max_drawdown_usd'])}.",
         "", f"Updated {now:%Y-%m-%d %H:%M} UTC · {TRINITY_DESK_VERSION} · {desk_ledger.LEDGER_VERSION}", "",
         "## Daily", "", "| Day | Equity at the close | Net | Closed: won / lost |", "|---|---|---|---|"]
    for d in reversed(perf["daily"]):
        L.append(f"| {d['period']} | {_money(d['end'])} | {_money(d['net'])} | {d['won']} / {d['lost']} |")
    if not perf["daily"]:
        L.append("| none yet | | | |")
    L += ["", "## Cumulative", "", "| | |", "|---|---|",
          f"| Starting equity | {_money(perf['start_equity'])} |",
          f"| Equity now | {_money(perf['equity'])} ({_money(perf['net_since_start'])}) |",
          f"| Realized (closed trades) | {_money(perf['realized_net'])} |",
          f"| Unrealized (open, at the last close) | {_money(perf['unrealized'])} |",
          f"| Closed trades | {perf['closed_trades']}: {perf['won']} won, {perf['lost']} lost |",
          f"| Maximum drawdown (intraday lows included) | {_money(perf['max_drawdown_usd'])} |", "",
          "## Monthly, against the $4,000 target (a target, never a quota)", "",
          "| Month | Net | Of $4,000 |", "|---|---|---|"]
    for m in perf["monthly"]:
        L.append(f"| {m['period']} | {_money(m['net'])} | {m['target_progress'] * 100:.1f}% |")
    if not perf["monthly"]:
        L.append("| none yet | | |")
    L += ["", "## Every trade (the permanent ledger, never reset)", "",
          "| Status | Instrument | Opened | Closed | Entry | Exit or mark | Qty | Net | Exit | Signal |",
          "|---|---|---|---|---|---|---|---|---|---|"]
    for r in led["rows"]:
        L.append(f"| {r['status']} | {r['instrument']} | {r['opened'] or '—'} | {r['closed'] or '—'} | "
                 f"{_px(r['entry'])} | {_px(r['exit'] if r['status'] == 'CLOSED' else r['mark'])} | {r['qty']} | "
                 f"{_money(r['net_pnl'] if r['status'] == 'CLOSED' else r['open_pnl'])} | {r['exit_reason'] or '—'} | "
                 f"{r['signal']} |")
    if not led["rows"]:
        L.append("| none yet | | | | | | | | | |")
    return "\n".join(L) + "\n"


# ── the replay: the desk's own code on history (descriptive) ──────────────

REPLAY_RULE = PromotedRule(RULE_ID, "EXPERIMENTAL", "HEALTHY", INSTRUMENTS, "PAPER", "the replay itself",
                           "replay", {"note": "a replay of the desk's own code on bars already read: descriptive"})


def replay(history: Path, state_dir: Path, first: date, now: datetime) -> dict:
    """The desk's own code from the first trading day on or after `first` with ten grid rows before it, on stored
    bars, to `now`: what this desk would have done. Descriptive: every one of these bars was read by the package's
    author and by the red team."""
    series, problems = load_history(history, now)
    _, days = signal_closes(series)
    anchor = next(d for i, d in enumerate(days) if d >= first and i >= (T.WARMUP + 1) * T.STEP)
    return run(state_dir, now, series, problems, rules=[REPLAY_RULE], rules_note="the replay's own rule",
               anchor=anchor)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--state", required=True, type=Path)
    ap.add_argument("--history", type=Path, help="stored bars (scripts/trinity_data.py) instead of fetching")
    ap.add_argument("--replay", type=date.fromisoformat, help="replay the desk's own code from this day (descriptive)")
    a = ap.parse_args()
    now = datetime.now(timezone.utc)  # the command line's clock: every function above takes it as an argument
    if a.replay:
        if not a.history:
            ap.error("--replay needs --history")
        s = replay(a.history, a.state, a.replay, now)
    else:
        series, problems = load_history(a.history, now) if a.history else fetch(now)
        s = run(a.state, now, series, problems)
    print(json.dumps({k: s.get(k) for k in ("account", "gate", "last_session", "next_rebalance",
                                            "processed_this_run", "problems")}, indent=1, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
