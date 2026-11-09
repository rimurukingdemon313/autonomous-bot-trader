"""The trend desk's permanent paper-trading ledger and its performance report (docs/TREND_DESK.md).

Presentation only (CLAUDE.md rule 11). It reads what the desk and its paper broker recorded in desk.db and writes
TRADING_REPORT.md, ledger.csv and equity.csv. It never trades, sizes, closes or resets anything, and every figure comes
from that record:

- each session's account right after the desk acted, written by the runner (`record_session`, event DESK_EQUITY);
- each session's account at its intraday lows, written by the desk itself (DESK_INTRADAY_LOW);
- each closed trade, from the desk's DESK_TRADE_CLOSED events (append-only, hash-chained), with the paper broker's own
  cost decomposition: gross - spread - commission - slippage - financing = net;
- each open position, from the broker at the last session's prices;
- the signal behind each trade, from the DESK_DECISION that opened it.

Nothing is excluded and nothing is reset: every losing trade, day, week and month is listed as it happened. A figure
the record does not hold is shown as unknown, never estimated (CLAUDE.md rule 6). Paper results are never added to
backtest or validated out-of-sample results: the report names each kind and keeps them apart.

Financing is zero by construction: the desk enters every position with swap_per_night 0.0, a swap-free account
(aitrader/position/trend_desk.py `_enter`). The broker's own swap figure is still read and shown.
"""

from __future__ import annotations

import csv
import json
from datetime import date, datetime, timezone
from pathlib import Path

LEDGER_VERSION = "desk-ledger-1.0.0"
TARGET_MONTH_USD = 4_000.0
STRATEGY = "TRND-1"
START_DAY = "2026-11-09"
CSV_COLUMNS = ["position", "status", "strategy", "signal", "decision_id", "instrument", "direction", "opened", "closed",
               "exit_reason", "entry", "exit", "mark", "qty", "entry_notional_usd", "entry_leverage", "risk_usd",
               "gross_pnl", "spread", "commission", "slippage", "financing", "net_pnl", "open_pnl", "r", "reconciles"]


# ── recording: called by the runner right after each session ─────────────

def open_positions(desk) -> list[dict]:
    """The broker's open positions at its current prices: what closing each now at the touch would give, before the
    commission that is charged at the close."""
    b, out = desk.broker, []
    for p in b.positions():
        q, spec = b.quote(p.symbol), b.spec(p.symbol)
        mark = (q.bid if p.side > 0 else q.ask) if q else None
        units = p.qty * spec.contract_size * spec.value_per_price_unit if spec else None
        known = mark is not None and units is not None
        out.append({"id": p.id, "symbol": p.symbol, "side": p.side, "qty": p.qty, "entry": p.entry, "mark": mark,
                    "stop": p.stop, "opened": p.opened,
                    "notional_usd": round(abs(mark * units), 2) if known else None,
                    "open_pnl": round((mark - p.entry) * p.side * units, 2) if known else None})
    return out


def session_payload(desk, t: int, day: date, symbols: list[str]) -> dict:
    acct = desk.broker.account()
    positions = open_positions(desk)
    gross = None if any(p["notional_usd"] is None for p in positions) else \
        round(sum(p["notional_usd"] for p in positions), 2)
    eq = round(acct.equity, 2)
    return {"t": int(t), "day": str(day), "symbols": list(symbols), "equity": eq, "balance": round(acct.balance, 2),
            "open_pnl": round(acct.equity - acct.balance, 2), "gross_exposure_usd": gross,
            "leverage": round(gross / eq, 4) if gross is not None and eq > 0 else None, "positions": positions,
            "version": LEDGER_VERSION}


def record_session(db, desk, t: int, day: date, symbols: list[str]) -> dict | None:
    """Write the session's DESK_EQUITY once. A session already recorded is never recorded again."""
    ref = f"{day}:{int(t)}"
    if db.one("SELECT 1 AS x FROM events WHERE type='DESK_EQUITY' AND ref=?", (ref,)):
        return None
    payload = session_payload(desk, t, day, symbols)
    db.event("DESK_EQUITY", payload, ref=ref)
    return payload


# ── reading the permanent record ─────────────────────────────────────────

def _events(db, *kinds: str) -> list[dict]:
    marks = ",".join("?" * len(kinds))
    return [json.loads(r["payload"]) | {"_type": r["type"], "_seq": r["seq"]} for r in
            db.query(f"SELECT seq, type, payload FROM events WHERE type IN ({marks}) ORDER BY seq", kinds)]


def _iso(t) -> str | None:
    return datetime.fromtimestamp(t, timezone.utc).strftime("%Y-%m-%d %H:%M UTC") if t else None


def _signal(dec: dict | None) -> str:
    if not dec:
        return "unknown: no opening decision recorded"
    mc, mm = dec.get("month_end_close"), dec.get("mean_of_ten")
    if mc is None or mm is None:
        return f"{STRATEGY} BUY for {dec.get('for_month')}"
    return (f"{STRATEGY} BUY for {dec.get('for_month')}: the {dec.get('month_end')} month-end close {mc:,.2f} was above "
            f"the mean of its last ten month-end closes, {mm:,.2f}")


def _reconciles(row: dict) -> bool | None:
    parts = [row[k] for k in ("gross_pnl", "spread", "commission", "slippage", "financing", "net_pnl")]
    if any(x is None for x in parts):
        return None
    g, s, c, sl, f, n = parts
    return abs(g - s - c - sl - f - n) < 0.01


def ledger(db, desk) -> dict:
    """Every trade the desk ever made, closed or open, with its costs, size, leverage and signal; every session's
    account at its close and at its intraday lows."""
    record = _events(db, "DESK_EQUITY", "DESK_INTRADAY_LOW", "DESK_DECISION", "DESK_TRADE_CLOSED")
    snaps = [e for e in record if e["_type"] == "DESK_EQUITY"]
    lows = [e for e in record if e["_type"] == "DESK_INTRADAY_LOW"]
    buys = {e["position"]: e for e in record
            if e["_type"] == "DESK_DECISION" and e.get("action") == "BUY" and e.get("position")}
    at_entry: dict[str, dict] = {}
    for s in snaps:
        for p in s["positions"]:
            if p["id"] not in at_entry and p.get("notional_usd") is not None:
                at_entry[p["id"]] = {"notional": p["notional_usd"],
                                     "leverage": round(p["notional_usd"] / s["equity"], 4) if s["equity"] > 0 else None}
    broker = {c.position_id: c for c in desk.broker.closed_since(0)}

    def common(pid, dec):
        e = at_entry.get(pid, {})
        return {"position": pid, "strategy": STRATEGY, "signal": _signal(dec), "decision_id": (dec or {}).get("decision_id"),
                "entry_notional_usd": e.get("notional"), "entry_leverage": e.get("leverage"),
                "risk_usd": ((dec or {}).get("risk") or {}).get("risk_amount")}
    rows = []
    for e in (x for x in record if x["_type"] == "DESK_TRADE_CLOSED"):
        pid = e.get("position")
        bc = broker.get(pid)
        row = common(pid, buys.get(pid)) | {
            "status": "CLOSED", "instrument": e.get("symbol"),
            "direction": "LONG" if (bc.side if bc else 1) > 0 else "SHORT", "opened": _iso(e.get("opened")),
            "closed": _iso(e.get("closed")), "exit_reason": e.get("reason"), "entry": e.get("entry"),
            "exit": e.get("exit"), "mark": None, "qty": e.get("qty"),
            "gross_pnl": round(bc.gross_pnl, 2) if bc and bc.gross_pnl is not None else None,
            "spread": e.get("spread_cost"), "commission": e.get("commission"), "slippage": e.get("slippage_cost"),
            "financing": round(bc.swap, 2) if bc and bc.swap is not None else None,
            "net_pnl": e.get("pnl"), "open_pnl": None, "r": e.get("r")}
        row["reconciles"] = _reconciles(row)
        rows.append(row)
    for p in open_positions(desk):
        rows.append(common(p["id"], buys.get(p["id"])) | {
            "status": "OPEN", "instrument": p["symbol"], "direction": "LONG" if p["side"] > 0 else "SHORT",
            "opened": _iso(p["opened"]), "closed": None, "exit_reason": None, "entry": p["entry"], "exit": None,
            "mark": p["mark"], "qty": p["qty"], "gross_pnl": None, "spread": None, "commission": None,
            "slippage": None, "financing": None, "net_pnl": None, "open_pnl": p["open_pnl"], "r": None,
            "reconciles": None})
    return {"rows": rows, "snaps": snaps, "lows": lows, "points": [e for e in record if e["_type"] in
                                                                   ("DESK_EQUITY", "DESK_INTRADAY_LOW")]}


# ── performance ──────────────────────────────────────────────────────────

def _drawdown(path: list[float]) -> tuple[float, float]:
    """The worst fall from a running peak along an equity path: (dollars, the fraction of that peak)."""
    peak, worst, worst_pct = None, 0.0, 0.0
    for v in path:
        peak = v if peak is None or v > peak else peak
        if peak - v > worst:
            worst, worst_pct = peak - v, (peak - v) / peak if peak else 0.0
    return round(worst, 2), round(worst_pct, 6)


def _periods(days: list[tuple[str, float, list[float]]], start_equity: float, key) -> list[dict]:
    """Per period (a day, an ISO week, a month): its closing equity less the closing equity before it, and the worst
    fall inside it, intraday lows included. `days`: (day, closing equity, the day's equity path) in time order."""
    out: list[dict] = []
    for d, end, path in days:
        k = key(date.fromisoformat(d))
        if not out or out[-1]["period"] != k:
            prev = out[-1]["end"] if out else start_equity
            out.append({"period": k, "start": prev, "end": end, "path": [prev] + path, "days": [d]})
        else:
            out[-1]["end"] = end
            out[-1]["path"] += path
            out[-1]["days"].append(d)
    for p in out:
        p["net"] = round(p["end"] - p["start"], 2)
        p["return"] = round(p["net"] / p["start"], 6) if p["start"] else None
        p["drawdown_usd"], p["drawdown"] = _drawdown(p.pop("path"))
    return out


def performance(led: dict, start_equity: float) -> dict:
    snaps = led["snaps"]
    ends: dict[str, float] = {}
    paths: dict[str, list[float]] = {}
    for e in led["points"]:
        if e.get("equity") is None:
            continue
        paths.setdefault(e["day"], []).append(e["equity"])
        if e["_type"] == "DESK_EQUITY":
            ends[e["day"]] = e["equity"]  # the day's last session sets its close
    days = [(d, ends[d], paths[d]) for d in sorted(ends)]
    daily = _periods(days, start_equity, str)
    weekly = _periods(days, start_equity, lambda d: "%04d-W%02d" % d.isocalendar()[:2])
    monthly = _periods(days, start_equity, lambda d: f"{d:%Y-%m}")
    rows = led["rows"]
    closed = [r for r in rows if r["status"] == "CLOSED"]
    for period in daily + weekly + monthly:
        mine = [r for r in closed if r["closed"] and any(r["closed"].startswith(d) for d in period["days"])]
        period["won"] = sum(1 for r in mine if r["net_pnl"] is not None and r["net_pnl"] > 0)
        period["lost"] = sum(1 for r in mine if r["net_pnl"] is not None and r["net_pnl"] <= 0)
        period["opened"] = sum(1 for r in rows if r["opened"] and any(r["opened"].startswith(d) for d in period["days"]))
    for m in monthly:
        m["target_progress"] = round(m["net"] / TARGET_MONTH_USD, 4)
    path = [start_equity] + [e["equity"] for e in led["points"] if e.get("equity") is not None]
    dd_usd, dd = _drawdown(path)
    current = snaps[-1]["equity"] if snaps else start_equity
    nets = [r["net_pnl"] for r in closed]

    def total(k):
        xs = [r[k] for r in closed]
        return None if any(x is None for x in xs) else round(sum(xs), 2)
    sessions_low = {(e["day"], tuple(e.get("symbols") or ())) for e in led["lows"]}
    sessions_eq = {(e["day"], tuple(e.get("symbols") or ())) for e in snaps}
    return {
        "start_equity": start_equity, "equity": current, "net_since_start": round(current - start_equity, 2),
        "return_since_start": round((current - start_equity) / start_equity, 6),
        "realized_net": total("net_pnl"), "unrealized": snaps[-1]["open_pnl"] if snaps else 0.0,
        "closed_trades": len(closed), "won": sum(1 for x in nets if x is not None and x > 0),
        "lost": sum(1 for x in nets if x is not None and x <= 0), "open_trades": len(rows) - len(closed),
        "costs": {k: total(k) for k in ("spread", "commission", "slippage", "financing")},
        "gross_realized": total("gross_pnl"),
        "not_reconciled": [r["position"] for r in closed if r["reconciles"] is False],
        "max_drawdown_usd": dd_usd, "max_drawdown": dd, "current_drawdown_usd": round(max(path) - current, 2),
        "daily": daily, "weekly": weekly, "monthly": monthly,
        "losing_days": [d for d in daily if d["net"] < 0], "losing_weeks": [w for w in weekly if w["net"] < 0],
        "losing_months": [m for m in monthly if m["net"] < 0],
        "exposure_usd": snaps[-1]["gross_exposure_usd"] if snaps else 0.0,
        "leverage": snaps[-1]["leverage"] if snaps else 0.0,
        "sessions": len(sessions_eq), "sessions_run": len(sessions_low),
        "sessions_missing": sorted(f"{d} {','.join(s)}" for d, s in sessions_low - sessions_eq),
        "last_session": snaps[-1]["day"] if snaps else None,
    }


# ── the report ───────────────────────────────────────────────────────────

def _usd(x) -> str:
    """A profit or loss, signed."""
    return "unknown" if x is None else f"+${x:,.2f}" if x > 0 else f"-${-x:,.2f}" if x < 0 else "$0.00"


def _amt(x) -> str:
    """An amount (equity, a cost, a notional), unsigned."""
    return "unknown" if x is None else f"${x:,.2f}"


def _pct(x) -> str:
    return "unknown" if x is None else f"{x * 100:+.2f}%"


def _num(x, nd=2) -> str:
    return "—" if x is None else f"{x:,.{nd}f}"


def _ar(perf: dict) -> str:
    d = perf["daily"][-1] if perf["daily"] else None
    day = (f"آخر يوم ({d['period']}) طلع {_usd(d['net'])}." if d else "بعد ما صارت ولا جلسة.")
    return ("**بالعربي:** هذا تقرير التداول الورقي وحده: فلوس مو حقيقية، ومو باكتيست، وما بيه ولا رقم من البحث. "
            f"الرصيد هسه {_amt(perf['equity'])}، يعني من البداية {_usd(perf['net_since_start'])}. {day} "
            f"الصفقات المسكّرة: {perf['closed_trades']} (ربحت {perf['won']}، خسرت {perf['lost']}). "
            f"أكبر نزول من القمة: {_amt(perf['max_drawdown_usd'])}. الـ$4,000 بالشهر هدف مو إلزام: "
            "النظام ما يزيد المخاطرة ولا يفتح صفقة حتى يوصله.")


def report(perf: dict, led: dict, limits: dict, now: datetime) -> str:
    L = ["# Trend desk: paper-trading performance", "",
         "**PAPER TRADING · NOT REAL MONEY · NOT A BACKTEST.** TRND-1 traded by the system itself, forward from "
         f"{START_DAY}, with simulated fills on each index's real daily close. Backtest and validated out-of-sample "
         "results are listed at the end and are never added to these figures.", "", _ar(perf), "",
         f"Updated {now:%Y-%m-%d %H:%M} UTC · sessions run: {perf['sessions_run']} · recorded: {perf['sessions']} · "
         f"last: {perf['last_session'] or 'none yet'} · {LEDGER_VERSION}", ""]
    if perf["sessions_missing"]:
        L += [f"**Sessions with no equity record:** {', '.join(perf['sessions_missing'])}. They are in the desk's own "
              "record (trades, decisions); only their closing equity is missing from the daily figures.", ""]
    if perf["not_reconciled"]:
        L += [f"**Trades whose costs do not add up to their net:** {', '.join(perf['not_reconciled'])}.", ""]
    L += ["## Daily", "",
          "Each session day's closing equity less the day before's. The newest is first; every day is in equity.csv.",
          "", "| Day | Equity at the close | Net | Return | Worst fall in the day | Trades opened | Closed: won / lost |",
          "|---|---|---|---|---|---|---|"]
    for d in list(reversed(perf["daily"]))[:30]:
        L.append(f"| {d['period']} | {_amt(d['end'])} | {_usd(d['net'])} | {_pct(d['return'])} | "
                 f"{_amt(d['drawdown_usd'])} | {d['opened']} | {d['won']} / {d['lost']} |")
    if not perf["daily"]:
        L.append("| no session yet | | | | | | |")
    c = perf["costs"]
    L += ["", f"## Cumulative (since {START_DAY})", "", "| | |", "|---|---|",
          f"| Starting equity | {_amt(perf['start_equity'])} |",
          f"| Equity now | {_amt(perf['equity'])}: {_usd(perf['net_since_start'])} "
          f"({_pct(perf['return_since_start'])}) |",
          f"| Realized net P&L (closed trades) | {_usd(perf['realized_net'])}, from {_usd(perf['gross_realized'])} "
          "gross |",
          f"| Unrealized P&L (open trades, at the last close) | {_usd(perf['unrealized'])} |",
          f"| Closed trades | {perf['closed_trades']}: {perf['won']} won, {perf['lost']} lost |",
          f"| Open trades | {perf['open_trades']} |",
          f"| Costs paid on closed trades | spread {_amt(c['spread'])} · commission {_amt(c['commission'])} · "
          f"slippage {_amt(c['slippage'])} · financing {_amt(c['financing'])} (swap-free) |",
          f"| Open exposure | {_amt(perf['exposure_usd'])} notional, {_num(perf['leverage'], 2)}x the equity |",
          f"| Maximum drawdown (intraday lows included) | {_amt(perf['max_drawdown_usd'])} "
          f"({perf['max_drawdown'] * 100:.2f}% of the peak) |",
          f"| Below the peak now | {_amt(perf['current_drawdown_usd'])} |",
          f"| Losing days / weeks / months | {len(perf['losing_days'])} of {len(perf['daily'])} · "
          f"{len(perf['losing_weeks'])} of {len(perf['weekly'])} · {len(perf['losing_months'])} of "
          f"{len(perf['monthly'])} |", ""]
    L += ["## Monthly dashboard", "",
          "The $4,000 a month is a target, never a quota: the desk does not trade more, or larger, to reach it "
          "(CLAUDE.md rule 8). A month in progress is marked so.", "",
          "| Month | Starting equity | Ending equity | Net | Return | Max drawdown | Trades won / lost | Of $4,000 |",
          "|---|---|---|---|---|---|---|---|"]
    this_month = f"{now:%Y-%m}"
    for m in perf["monthly"]:
        name = m["period"] + (" (in progress)" if m["period"] == this_month else "")
        L.append(f"| {name} | {_amt(m['start'])} | {_amt(m['end'])} | {_usd(m['net'])} | {_pct(m['return'])} | "
                 f"{_amt(m['drawdown_usd'])} ({m['drawdown'] * 100:.2f}%) | {m['won']} / {m['lost']} | "
                 f"{m['target_progress'] * 100:.1f}% |")
    if not perf["monthly"]:
        L.append("| none yet | | | | | | | |")
    L += ["", "## Every losing day, week and month", ""]
    for name, k in (("Days", "losing_days"), ("Weeks", "losing_weeks"), ("Months", "losing_months")):
        xs = perf[k]
        L.append(f"- **{name}:** " + (", ".join(f"{x['period']} {_usd(x['net'])}" for x in xs) if xs else "none yet"))
    L += ["", "## Every trade: the permanent ledger, never reset, nothing excluded", "",
          "| # | Status | Instrument | Side | Opened | Closed | Entry | Exit or mark | Lots | Notional at entry | "
          "Leverage at entry | Gross | Spread | Commission | Slippage | Financing | Net | Exit | Signal |",
          "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for i, r in enumerate(led["rows"], 1):
        closed = r["status"] == "CLOSED"
        lev = "—" if r["entry_leverage"] is None else f"{r['entry_leverage']:.3f}x"
        L.append(f"| {i} | {r['status']} | {r['instrument']} | {r['direction']} | {r['opened'] or '—'} | "
                 f"{r['closed'] or '—'} | {_num(r['entry'])} | {_num(r['exit'] if closed else r['mark'])} | "
                 f"{_num(r['qty'], 2)} | {_amt(r['entry_notional_usd'])} | {lev} | "
                 + (f"{_usd(r['gross_pnl'])} | {_amt(r['spread'])} | {_amt(r['commission'])} | {_amt(r['slippage'])} | "
                    f"{_amt(r['financing'])} | **{_usd(r['net_pnl'])}** | {r['exit_reason']} | " if closed else
                    f"open {_usd(r['open_pnl'])} | | | | | | | ")
                 + f"{r['signal']} |")
    if not led["rows"]:
        L.append("| none yet | | | | | | | | | | | | | | | | | | |")
    L += ["", "An open trade is marked at the last close's bid, so the spread and the slippage at its entry are already "
              "in its P&L; its commission is charged, and its costs itemized, when it closes. Each closed trade's "
              "gross less its costs equals its net, as the paper broker booked it.", "",
          "## Risk limits in force (never raised after a loss)", "", "| | |", "|---|---|"]
    L += [f"| {k} | {v} |" for k, v in limits.items()]
    L += ["", "## Kept apart: never added to the paper figures", "", "| Kind | What it is | Result | Where |",
          "|---|---|---|---|",
          "| Paper trading (this report) | TRND-1 traded forward by the system, simulated fills on real closes | "
          "above | trend-desk-data |",
          "| Backtest (descriptive, not a test) | The desk's own code at its own sizing, replayed on 2004-2026 bars "
          "already judged | +3.4% a year on average; 6 losing years of 22; worst year -6.78%; worst fall $28,038 | "
          "research/results/TREND-DESK-replay.json |",
          "| Validated out-of-sample | TRND-1's sealed holdout: the four indices at equal weight and fully invested, "
          "2021-01..2026-09 | +0.785% a month on the invested book (not on the desk's smaller sizing) | "
          "research/knowledge/TRND-1-H.json |", ""]
    return "\n".join(L)


def limits_of(desk) -> dict:
    p, lim = desk.gate.profile, desk.risk.limits
    return {"Per trade": f"at most ${p.risk_per_trade:,.0f} lost at its stop, all costs included "
                         f"({lim.risk_per_trade_pct}% of the starting balance); a fixed amount, never raised after a "
                         "win or a loss",
            "All open trades": f"at most ${p.max_open_risk:,.0f} at their stops together ({lim.max_open_risk_pct}%)",
            "Daily loss limit": f"${p.daily_loss_limit:,.0f} from the day's reference, each session's intraday lows "
                                f"included ({lim.daily_loss_limit_pct}%)",
            "Weekly loss limit": f"{lim.weekly_loss_limit_pct}% from the week's opening equity",
            "Maximum loss": f"${p.max_total_loss:,.0f} ({lim.max_drawdown_pct}%): equity at "
                            f"${p.starting_balance - p.max_total_loss:,.0f} fails the account and closes everything",
            "Positions": f"at most {p.max_open_positions}, one per index; long or flat, never short; leverage at most "
                         f"{lim.max_leverage:g}x",
            "NO TRADE": "an index whose rule says flat is not held; nothing is traded to meet a target"}


def write(state_dir: Path, db, desk, now: datetime) -> dict:
    led = ledger(db, desk)
    perf = performance(led, desk.gate.profile.starting_balance)
    with open(state_dir / "ledger.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=CSV_COLUMNS, extrasaction="ignore")
        w.writeheader()
        for r in led["rows"]:
            w.writerow(r)
    with open(state_dir / "equity.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["session_utc", "day", "symbols", "equity", "balance", "open_pnl", "gross_exposure_usd", "leverage"])
        for s in led["snaps"]:
            w.writerow([_iso(s["t"]), s["day"], " ".join(s["symbols"]), s["equity"], s["balance"], s["open_pnl"],
                        s["gross_exposure_usd"], s["leverage"]])
    (state_dir / "TRADING_REPORT.md").write_text(report(perf, led, limits_of(desk), now))
    return perf


def write_failure(state_dir: Path, err: BaseException, now: datetime) -> None:
    """The ledger could not be written: say so where it would have been, and leave no CSV that looks current."""
    for name in ("ledger.csv", "equity.csv"):
        (state_dir / name).unlink(missing_ok=True)
    (state_dir / "TRADING_REPORT.md").write_text(
        "# Trend desk: paper-trading performance\n\n"
        f"**NOT WRITTEN** at {now:%Y-%m-%d %H:%M} UTC: {type(err).__name__}: {err}. The desk's own record (desk.db, "
        "REPORT.md) is unaffected, and the ledger is rebuilt from it in full by the next run that succeeds.\n")
