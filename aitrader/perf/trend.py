"""An independent audit of the trend desk's paper account (TRND-1 on the $200,000 profile).

Every figure is recomputed from the desk's three public files, each by a second route, and compared with what the desk
itself published:

- `ledger.csv`: one row a position, open or closed;
- `equity.csv`: one row a session;
- `state.json`: the account, the open positions with their stops, and the rule's state.

Realized and unrealized profit are never added into one "profit": the first is money booked by closed trades, the
second is the valuation of open ones at the last close and can vanish. A figure that cannot be recomputed from these
files (the drawdown inside a day, a benchmark that needs index prices after an exit) is reported as unavailable with
its reason, never estimated.
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
import re
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from .stats import check, drawdown, trade_stats

#: The profile's limits, as the desk's report states them. The audit checks the account against them; it sets none.
LIMITS = {"start": 200_000.0, "per_trade": 1_500.0, "open_together": 8_000.0, "max_positions": 4, "max_leverage": 1.0,
          "max_loss": 20_000.0, "monthly_target": 4_000.0}
CENT = 0.011  # two figures each rounded to the cent may differ by a cent


def rows(text: str) -> list[dict]:
    return list(csv.DictReader(io.StringIO(text)))


def _f(x) -> float | None:
    if x is None or x == "":
        return None
    return float(x)


def _session(s: str) -> datetime:
    return datetime.strptime(s.replace(" UTC", ""), "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc)


def chain(db: Path | str, table: str = "events") -> dict:
    """The desk's permanent record, checked link by link by a second implementation: each row's hash is the sha256 of
    the row before it and of its own content. A row removed, reordered or rewritten breaks every link after it."""
    con = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
    con.row_factory = sqlite3.Row
    try:
        prev, n = "genesis", 0
        for r in con.execute(f"SELECT * FROM {table} ORDER BY seq"):
            body = {k: r[k] for k in r.keys() if k not in ("prev_hash", "hash", "seq")}
            want = hashlib.sha256((prev + json.dumps(body, sort_keys=True, separators=(",", ":"))).encode()).hexdigest()
            if r["prev_hash"] != prev or r["hash"] != want:
                return {"table": table, "rows": n, "ok": False, "broken_at": r["seq"]}
            prev, n = r["hash"], n + 1
        return {"table": table, "rows": n, "ok": True, "broken_at": None}
    finally:
        con.close()


def points(db: Path | str) -> list[dict]:
    """Every equity the desk recorded, in the order it recorded them: each session's close and each session's lows."""
    con = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
    try:
        out = []
        for typ, payload in con.execute("SELECT type, payload FROM events WHERE type IN ('DESK_EQUITY', 'DESK_INTRADAY_LOW') "
                                        "ORDER BY seq"):
            e = json.loads(payload)
            if e.get("equity") is not None:
                out.append({"type": typ, "day": e.get("day"), "equity": float(e["equity"])})
        return out
    finally:
        con.close()


def published(report: str) -> dict:
    """The figures the desk's own report prints, read back from its text."""
    def money(pattern):
        m = re.search(pattern, report)
        return float(m.group(1).replace(",", "")) if m else None
    return {"max_drawdown_inside_a_day": money(r"Maximum drawdown \(intraday lows included\) \| \$([0-9,]+\.[0-9]+)"),
            "equity_now": money(r"\| Equity now \| \$([0-9,]+\.[0-9]+)"),
            "below_the_peak_now": money(r"\| Below the peak now \| \$([0-9,]+\.[0-9]+)")}


def audit(ledger: list[dict], equity: list[dict], state: dict, rf_apr: float = 0.03875, record: list[dict] | None = None,
          chains: list[dict] | None = None, report: str | None = None) -> dict:
    """`record`: the desk's own equity points (`points`), for the drawdown inside a day. `chains`: the result of
    `chain` for each table checked. `report`: the text of the desk's TRADING_REPORT.md, to compare with."""
    start = LIMITS["start"]
    checks: list[dict] = []
    open_rows = [r for r in ledger if r["status"] == "OPEN"]
    closed_rows = [r for r in ledger if r["status"] == "CLOSED"]
    other = [r["position"] for r in ledger if r["status"] not in ("OPEN", "CLOSED")]
    checks.append(check("every ledger row is OPEN or CLOSED", [], other))

    # ── realized: closed trades only ────────────────────────────────────────
    nets = [_f(r["net_pnl"]) for r in closed_rows]
    realized = sum(x for x in nets if x is not None)
    checks.append(check("every closed trade has a net P&L", 0, sum(x is None for x in nets)))
    costs = {k: sum(_f(r[k]) or 0.0 for r in closed_rows) for k in ("spread", "commission", "slippage", "financing")}
    gross = sum(_f(r["gross_pnl"]) or 0.0 for r in closed_rows)
    for r in closed_rows:
        g, n = _f(r["gross_pnl"]), _f(r["net_pnl"])
        c = sum(_f(r[k]) or 0.0 for k in ("spread", "commission", "slippage", "financing"))
        checks.append(check(f"{r['position']} {r['instrument']}: gross less its costs is its net",
                            None if g is None else round(g - c, 2), n, CENT))
    last = equity[-1] if equity else None
    balance = _f(last["balance"]) if last else None
    checks.append(check("the balance moved by exactly the closed trades' net P&L", round(start + realized, 2), balance, CENT))

    # ── unrealized: open trades, at the last close ──────────────────────────
    unreal = sum(_f(r["open_pnl"]) or 0.0 for r in open_rows)
    checks.append(check("every open trade has an open P&L", 0, sum(_f(r["open_pnl"]) is None for r in open_rows)))
    checks.append(check("the ledger's open P&L is the last session's open P&L", round(unreal, 2),
                        _f(last["open_pnl"]) if last else None, CENT))
    eq_now = _f(last["equity"]) if last else None
    checks.append(check("equity is the start plus realized plus unrealized", round(start + realized + unreal, 2), eq_now, CENT))
    bad = [e["session_utc"] for e in equity
           if abs((_f(e["balance"]) or 0) + (_f(e["open_pnl"]) or 0) - (_f(e["equity"]) or 0)) > CENT]
    checks.append(check("in every session, equity is balance plus open P&L", [], bad))
    times = [_session(e["session_utc"]) for e in equity]
    checks.append(check("the sessions are in order and none is recorded twice", True,
                        all(a < b for a, b in zip(times, times[1:]))))
    acct = state.get("account", {})
    checks.append(check("the state file's equity is the last session's", eq_now, acct.get("equity"), CENT))
    checks.append(check("the state file's balance is the last session's", balance, acct.get("balance"), CENT))
    checks.append(check("the state file's P&L is equity less the start", None if eq_now is None else round(eq_now - start, 2),
                        acct.get("pnl"), CENT))
    checks.append(check("paper only: the state file says no real money", (True, False),
                        (state.get("paper_only"), state.get("real_money"))))

    # ── each open position, recomputed from its prices ──────────────────────
    by_symbol = {p["symbol"]: p for p in state.get("positions", [])}
    checks.append(check("the ledger and the state file hold the same open positions",
                        sorted(r["instrument"] for r in open_rows), sorted(by_symbol)))
    positions, risk_now, gross_now = [], 0.0, 0.0
    for r in open_rows:
        p = by_symbol.get(r["instrument"])
        qty, entry, mark = _f(r["qty"]), _f(r["entry"]), _f(r["mark"])
        if p is None or not qty or not mark:
            continue
        # The index is quoted in its own currency; the desk's dollar notional gives the conversion it used.
        fx = p["notional_usd"] / (p["units"] * p["price"])
        pnl = qty * (mark - entry) * fx
        checks.append(check(f"{r['instrument']}: units x (mark - entry) x the conversion is its open P&L",
                            round(pnl, 2), _f(r["open_pnl"]), 0.02 + 2e-5 * abs(p["notional_usd"])))
        checks.append(check(f"{r['instrument']}: the state file's P&L is the ledger's", _f(r["open_pnl"]), p.get("pnl"), CENT))
        checks.append(check(f"{r['instrument']}: the state file's size is the ledger's", qty, p.get("units"), 1e-9))
        checks.append(check(f"{r['instrument']}: its risk at entry was within the per-trade limit", True,
                            (_f(r["risk_usd"]) or 9e9) <= LIMITS["per_trade"] + CENT))
        at_stop = qty * (mark - p["stop"]) * fx
        risk_now += max(at_stop, 0.0)
        gross_now += p["notional_usd"]
        positions.append({"instrument": r["instrument"], "direction": r["direction"], "opened": r["opened"],
                          "units": qty, "entry": entry, "mark": mark, "stop": p["stop"], "conversion_to_usd": fx,
                          "notional_usd": p["notional_usd"], "notional_at_entry_usd": _f(r["entry_notional_usd"]),
                          "unrealized_usd": _f(r["open_pnl"]), "move_since_entry": mark / entry - 1,
                          "loss_at_stop_from_here_usd": at_stop, "risk_at_entry_usd": _f(r["risk_usd"])})
    for p in positions:
        p["share_of_gross"] = p["notional_usd"] / gross_now if gross_now else None
    checks.append(check("the open positions' notional is the last session's gross exposure", round(gross_now, 2),
                        _f(last["gross_exposure_usd"]) if last else None, 0.05))
    lev = gross_now / eq_now if eq_now else None
    checks.append(check("leverage is gross exposure over equity", None if lev is None else round(lev, 4),
                        _f(last["leverage"]) if last else None, 2e-4))
    checks.append(check("open risk at the stops is within the limit for all trades together", True,
                        risk_now <= LIMITS["open_together"] + CENT))
    checks.append(check("positions and leverage are within their limits", True,
                        len(open_rows) <= LIMITS["max_positions"] and (lev or 0) <= LIMITS["max_leverage"]))
    checks.append(check("every position is long: the desk never shorts", [], [p["instrument"] for p in positions if p["direction"] != "LONG"]))

    # ── the equity history ──────────────────────────────────────────────────
    series = [start] + [_f(e["equity"]) for e in equity]
    dd = drawdown(series)
    days: dict[str, float] = {}
    for e in equity:
        days[e["day"]] = _f(e["equity"])  # the day's last session
    daily, prev = [], start
    for d, v in days.items():
        daily.append({"day": d, "equity": v, "net": round(v - prev, 2)})
        prev = v
    months: dict[str, dict] = {}
    for x in daily:
        m = months.setdefault(x["day"][:7], {"net": 0.0, "days": 0})
        m["net"], m["days"] = round(m["net"] + x["net"], 2), m["days"] + 1
    inside = {"value": None, "why": "the falls inside a day are not in equity.csv: they need the desk's database"}
    if record is not None:
        path = drawdown([start] + [x["equity"] for x in record])
        inside = {"value": round(path["max"], 2), "below_the_peak_now": round(path["now"], 2), "points": len(record),
                  "what": "along every equity the desk recorded: each session's close and each session's lows"}
        closes = [x["equity"] for x in record if x["type"] == "DESK_EQUITY"]
        checks.append(check("the database's session closes are equity.csv's", [round(_f(e["equity"]), 2) for e in equity],
                            [round(v, 2) for v in closes]))
    for c in chains or []:
        checks.append(check(f"the permanent record `{c['table']}` is unbroken ({c['rows']} rows, each hash recomputed)", True, c["ok"]))
    pub = published(report) if report is not None else {}
    if report is not None:
        checks.append(check("the desk's report prints this equity", eq_now, pub["equity_now"], CENT))
        if record is not None:
            checks.append(check("the desk's report prints this drawdown inside a day", inside["value"],
                                pub["max_drawdown_inside_a_day"], CENT))
            checks.append(check("the desk's report prints this distance below the peak", inside["below_the_peak_now"],
                                pub["below_the_peak_now"], CENT))
    span_days = (times[-1] - times[0]).total_seconds() / 86400 if len(times) > 1 else 0.0
    cash = start * rf_apr * span_days / 365.0
    net_total = None if eq_now is None else eq_now - start
    shares = [p["share_of_gross"] for p in positions if p["share_of_gross"] is not None]
    hhi = sum(s * s for s in shares) if shares else None
    entry_gross = sum(p["notional_at_entry_usd"] or 0.0 for p in positions)
    figures = {
        "initial_capital": start, "equity_now": eq_now, "balance_now": balance, "last_session": last["session_utc"] if last else None,
        "realized_net": round(realized, 2), "realized_gross": round(gross, 2), "costs_on_closed_trades": {k: round(v, 2) for k, v in costs.items()},
        "unrealized": round(unreal, 2),
        "net_after_all_costs": None if net_total is None else round(net_total, 2),
        "net_return": None if net_total is None else net_total / start,
        "open_positions": len(open_rows), "closed_trades": trade_stats([x for x in nets if x is not None]),
        "max_drawdown_session_closes": dd["max"], "below_the_peak_now": dd["now"],
        "max_drawdown_inside_a_day": inside,
        "gross_exposure": round(gross_now, 2), "leverage": lev, "open_risk_at_stops": round(risk_now, 2),
        "concentration": {"positions": len(positions), "largest_share_of_gross": max(shares) if shares else None,
                          "herfindahl": hhi, "effective_positions": (1 / hhi) if hhi else None,
                          "one_risk_factor": bool(positions) and all(p["direction"] == "LONG" for p in positions),
                          "note": "four equity indices, all long: one risk factor held four times"},
        "daily": daily, "monthly": [{"month": k, **v, "of_target": v["net"] / LIMITS["monthly_target"]} for k, v in months.items()],
        "losing_days": sum(x["net"] < 0 for x in daily), "days": len(daily),
        "benchmarks": {
            "cash": {"usd": round(cash, 2), "what": f"{rf_apr:.3%} a year on the starting balance for {span_days:.2f} days"},
            "same_indices_bought_and_held_at_the_desk_size": (
                {"usd": round(unreal, 2), "what": "identical to the desk while no trade has closed: the rule has not yet "
                                                  "made one decision the holder would not have made"}
                if not closed_rows else
                {"usd": None, "why": "after an exit, holding on needs the index's later closes: not in these files"}),
            "same_positions_fully_invested": (
                {"usd": round(unreal * start / entry_gross, 2), "what": "the same P&L scaled from the desk's exposure to "
                 "one times the account: what the validated rule's own sizing would show; the desk's risk limits do not allow it"}
                if entry_gross and not closed_rows else {"usd": None, "why": "not computable from these files"}),
        },
        "excess_over_cash": None if net_total is None else round(net_total - cash, 2),
    }
    return {"system": "TRND-1 trend desk (paper)", "figures": figures, "positions": positions, "checks": checks,
            "reconciled": all(c["ok"] for c in checks), "failed_checks": [c for c in checks if not c["ok"]]}


__all__ = ["LIMITS", "audit", "chain", "points", "published", "rows"]
