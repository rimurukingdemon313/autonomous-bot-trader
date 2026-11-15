"""An independent audit of the funding radar's paper ledger (RADAR-1).

The radar publishes `ledger.json` every hour: every position, open and closed, and the hourly mark of the whole book.
This module recomputes the book from the positions alone, by its own arithmetic (it calls none of the radar's code),
and compares the result with the hourly marks and with the figures the radar's own report prints. It then says where
the profit and the loss came from.

Units. A position is two legs of notional N each; its P&L is in basis points of N. The book is ten slots of 2N, so
one basis point of N on one position is 1/2000 of a percent of the book. The radar has no cash account: a dollar
figure here is the same percentage applied to a stated book size, and is labelled so.

Realized and unrealized are kept apart. An open position is valued at its marks with its entry fills paid; its
closing fills are not yet paid, and its liquidation value (those fills charged) is given beside it.
"""

from __future__ import annotations

import math
import re

from .stats import check, drawdown, mean_t, trade_stats

#: Each venue's taker fee per fill and the declared slippage, in bp: restated here so the audit does not read the
#: radar's own table. A recorded cost that disagrees with these fails its check.
TAKER_BP = {"hyperliquid": 4.5, "gate": 5.0, "mexc": 2.0, "dydx": 5.0}
SLIP_BP = 5.0
SLOTS = 10
YEAR_S = 8760 * 3600
#: A class is a weakness only with at least this many positions on each side, and a mean below the rest's at this t.
WEAK_MIN, WEAK_T = 10, 2.0


def fills_bp(p: dict) -> float:
    """What one pair of fills (both legs, entering or leaving) costs."""
    return TAKER_BP[p["short_venue"]] + SLIP_BP + TAKER_BP[p["long_venue"]] + SLIP_BP


def basis_bp(p: dict) -> float:
    return ((p["long_px"] / p["long_px0"] - 1) - (p["short_px"] / p["short_px0"] - 1)) * 1e4


def net_bp(p: dict) -> float:
    return p["funding_bp"] + basis_bp(p) - p["cost_bp"]


def daily_excess(marks: list[dict], rf_apr: float) -> dict[int, float]:
    """The book's excess over cash for each UTC day (the day number is seconds // 86400), as a fraction of the book:
    each hour's change in the marked P&L, less the cash rate on the 2N of every position open through that hour."""
    t = [m["t"] for m in marks]
    pnl = [m["pnl_bp_total"] / 1e4 for m in marks]
    n_open = [m.get("open", 0) for m in marks]
    daily: dict[int, float] = {}
    for i in range(1, len(t)):
        inc = (pnl[i] - pnl[i - 1]) - rf_apr * 2 * n_open[i - 1] * (t[i] - t[i - 1]) / YEAR_S
        daily[t[i] // 86400] = daily.get(t[i] // 86400, 0.0) + inc / (2.0 * SLOTS)
    return daily


def performance(ledger: dict, rf_apr: float) -> dict:
    """The radar's own performance measures (research/preregistrations/RADAR-1.md), computed again from the ledger."""
    marks = ledger["marks"]
    if len(marks) < 2:
        return {"days": 0}
    t = [m["t"] for m in marks]
    pnl = [m["pnl_bp_total"] / 1e4 for m in marks]
    n_open = [m.get("open", 0) for m in marks]
    cap = 2.0 * SLOTS
    daily = daily_excess(marks, rf_apr)
    last = t[-1]
    by_coin: dict[str, float] = {}
    tot_exc = tot_cost = tot_cap_y = 0.0
    for p in ledger["closed"] + ledger["open"]:
        still = p.get("closed") is None
        leave = fills_bp(p) if still else 0.0  # an open position is valued as if closed now
        dur_y = ((last if still else p["closed"]) - p["opened"]) / YEAR_S
        e = (net_bp(p) - leave) / 1e4 - rf_apr * 2 * dur_y
        by_coin[p["coin"]] = by_coin.get(p["coin"], 0.0) + e
        tot_exc += e
        tot_cost += (p["cost_bp"] + leave) / 1e4
        tot_cap_y += 2 * dur_y
    best = max(by_coin, key=by_coin.get) if by_coin else None
    dd = drawdown([0.0] + [x / cap for x in pnl])
    _, t_daily = mean_t(list(daily.values()))
    return {"days": round((t[-1] - t[0]) / 86400, 2),
            "run_coverage": round(len(set(t)) / ((t[-1] - t[0]) / 3600 + 1), 4),
            "closed_positions": len(ledger["closed"]), "open_positions": len(ledger["open"]),
            "utilisation": round(sum(n_open) / len(n_open) / SLOTS, 4),
            "book_pnl_pct": round(pnl[-1] / cap * 100, 4),
            "book_excess_pct": round(tot_exc / cap * 100, 4),
            "ann_excess_deployed_pct": round(tot_exc / tot_cap_y * 100, 3) if tot_cap_y > 0 else None,
            "ann_excess_deployed_costs_x1.5_pct": round((tot_exc - 0.5 * tot_cost) / tot_cap_y * 100, 3) if tot_cap_y > 0 else None,
            "ann_excess_deployed_costs_x2_pct": round((tot_exc - tot_cost) / tot_cap_y * 100, 3) if tot_cap_y > 0 else None,
            "best_coin": best,
            "book_excess_without_best_coin_pct": round((tot_exc - by_coin[best]) / cap * 100, 4) if best else None,
            "max_dd_pct": round(dd["max"] * 100, 4),
            "t_excess_daily": None if t_daily is None else round(t_daily, 3)}


def published(report: str) -> dict:
    """The figures the radar's own report prints under its performance heading, read back from its text."""
    out: dict = {}
    for k, v in re.findall(r"^- ([A-Za-z0-9_.]+): (.+)$", report, flags=re.M):
        try:
            out[k] = float(v)
        except ValueError:
            out[k] = v.strip()
    return out


def _bucket(rows: list[dict], key) -> list[dict]:
    groups: dict[str, list[dict]] = {}
    for r in rows:
        groups.setdefault(key(r), []).append(r)
    out = []
    for name, g in groups.items():
        xs = [r["net_bp"] for r in g]
        m, t = mean_t(xs)
        out.append({"class": name, "positions": len(g), "sum_bp": round(sum(xs), 1), "mean_bp": round(m, 1),
                    "t": None if t is None else round(t, 2), "won": sum(x > 0 for x in xs),
                    "funding_bp": round(sum(r["funding_bp"] for r in g), 1), "price_bp": round(sum(r["basis_bp"] for r in g), 1),
                    "cost_bp": round(sum(r["cost_bp"] for r in g), 1)})
    return sorted(out, key=lambda x: x["sum_bp"])


def _welch(a: list[float], b: list[float]) -> float | None:
    """The t of the difference between two groups' means, their spreads not assumed equal. None if either is too small."""
    if len(a) < 2 or len(b) < 2:
        return None
    ma, mb = sum(a) / len(a), sum(b) / len(b)
    va = sum((x - ma) ** 2 for x in a) / (len(a) - 1)
    vb = sum((x - mb) ** 2 for x in b) / (len(b) - 1)
    se = math.sqrt(va / len(a) + vb / len(b))
    return round((ma - mb) / se, 2) if se > 0 else None


def _hold(h: float) -> str:
    return ("1 hour or less" if h <= 1 else "1 to 6 hours" if h <= 6 else "6 to 24 hours" if h <= 24
            else "1 to 3 days" if h <= 72 else "over 3 days")


def _spread(a: float) -> str:
    return "under 50%/yr" if a < 0.5 else "50 to 100%/yr" if a < 1.0 else "100%/yr or more"


def attribution(ledger: dict) -> dict:
    """Where the closed positions' P&L came from: by its three sources, and by class."""
    rows, last = [], {}
    for p in sorted(ledger["closed"], key=lambda p: (p["opened"], p["id"])):
        prev = last.get(p["coin"])
        gap = None if prev is None else (p["opened"] - prev) / 3600
        rows.append({"coin": p["coin"], "pair": f"short {p['short_venue']} / long {p['long_venue']}", "reason": p["reason"],
                     "hold_h": (p["closed"] - p["opened"]) / 3600, "entry_spread_apr": p["entry_spread_apr"],
                     "funding_bp": p["funding_bp"], "basis_bp": basis_bp(p), "cost_bp": p["cost_bp"], "net_bp": net_bp(p),
                     "reentry": gap is not None and gap <= 6})
        last[p["coin"]] = p["closed"]
    f, b, c = (sum(r[k] for r in rows) for k in ("funding_bp", "basis_bp", "cost_bp"))
    coins = _bucket(rows, lambda r: r["coin"])
    known_at_entry = {"entry spread": _bucket(rows, lambda r: _spread(r["entry_spread_apr"])),
                      "venue pair": _bucket(rows, lambda r: r["pair"]),
                      "time since the coin's previous position": _bucket(
                          rows, lambda r: "within 6 hours of the coin's previous exit" if r["reentry"] else "a first entry, or later")}
    # The largest weakness is not the largest class: it is the class that did worst against the rest of the book, by
    # a difference that is told from noise. Without that, every cycle would name one and propose a remedy for nothing.
    keys = {"entry spread": lambda r: _spread(r["entry_spread_apr"]), "venue pair": lambda r: r["pair"],
            "time since the coin's previous position": lambda r: "within 6 hours of the coin's previous exit" if r["reentry"] else "a first entry, or later"}
    for dim, xs in known_at_entry.items():
        for x in xs:
            mine = [r["net_bp"] for r in rows if keys[dim](r) == x["class"]]
            rest = [r["net_bp"] for r in rows if keys[dim](r) != x["class"]]
            x["rest_mean_bp"] = round(sum(rest) / len(rest), 1) if rest else None
            x["excess_loss_bp"] = round(sum(mine) - len(mine) * sum(rest) / len(rest), 1) if rest else None
            x["t_against_the_rest"] = _welch(mine, rest)
    worst = min(((dim, x) for dim, xs in known_at_entry.items() for x in xs
                 if x["positions"] >= WEAK_MIN and len(rows) - x["positions"] >= WEAK_MIN
                 and x["t_against_the_rest"] is not None and x["t_against_the_rest"] <= -WEAK_T),
                key=lambda dx: dx[1]["excess_loss_bp"], default=None)
    return {"sources": {"funding_bp": round(f, 1), "price_bp": round(b, 1), "gross_bp": round(f + b, 1), "cost_bp": round(c, 1),
                        "net_bp": round(f + b - c, 1), "cost_over_gross": round(c / (f + b), 2) if f + b > 0 else None,
                        "cost_per_position_bp": round(c / len(rows), 1) if rows else None,
                        "gross_per_position_bp": round((f + b) / len(rows), 1) if rows else None},
            "by_exit_reason": _bucket(rows, lambda r: r["reason"]),
            "by_holding_time": _bucket(rows, lambda r: _hold(r["hold_h"])),
            "known_at_entry": known_at_entry,
            "coins": {"traded": len(coins), "losing": sum(x["sum_bp"] < 0 for x in coins), "worst": coins[:5], "best": coins[-5:][::-1]},
            "median_hold_hours": round(sorted(r["hold_h"] for r in rows)[len(rows) // 2], 1) if rows else None,
            "largest_weakness": None if worst is None else {"dimension": worst[0], **worst[1]}}


def audit(ledger: dict, rf_apr: float = 0.03875, report: str | None = None, book_usd: float = 100_000.0) -> dict:
    checks: list[dict] = []
    closed, open_ = ledger["closed"], ledger["open"]
    marks = ledger["marks"]
    realized = sum(net_bp(p) for p in closed)
    unreal = sum(net_bp(p) for p in open_)
    leave = sum(fills_bp(p) for p in open_)
    checks.append(check("the positions add up to the last hourly mark of the book", round(realized + unreal, 2),
                        marks[-1]["pnl_bp_total"] if marks else None, 0.02))
    checks.append(check("the last mark counts the positions now open", len(open_), marks[-1].get("open") if marks else None))
    ts = [m["t"] for m in marks]
    checks.append(check("the hourly marks are in order, on the hour, none twice", True,
                        all(a < b for a, b in zip(ts, ts[1:])) and all(x % 3600 == 0 for x in ts)))
    checks.append(check("the run count is the number of marks", ledger.get("runs"), len(marks)))
    wrong = [p["id"] for p in closed if abs(p["cost_bp"] - 2 * fills_bp(p)) > 1e-6]
    wrong += [p["id"] for p in open_ if abs(p["cost_bp"] - fills_bp(p)) > 1e-6]
    checks.append(check("every position paid each venue's fee and the declared slippage on every fill", [], wrong))
    ids = [p["id"] for p in closed + open_]
    checks.append(check("no position is recorded twice", len(ids), len(set(ids))))
    checks.append(check("every closed position has its closing hour and reason, and no open one has", [],
                        [p["id"] for p in closed if p.get("closed") is None or not p.get("reason")]
                        + [p["id"] for p in open_ if p.get("closed") is not None]))
    checks.append(check("no position closed before it was opened", [], [p["id"] for p in closed if p["closed"] < p["opened"]]))
    held = [p["coin"] for p in open_]
    checks.append(check("at most ten positions are open, one a coin", True, len(held) <= SLOTS and len(held) == len(set(held))))
    # one position a coin at a time, through the whole history
    by_coin: dict[str, list[dict]] = {}
    for p in closed + open_:
        by_coin.setdefault(p["coin"], []).append(p)
    overlap = []
    for coin, ps in by_coin.items():
        ps.sort(key=lambda p: p["opened"])
        overlap += [b["id"] for a, b in zip(ps, ps[1:]) if a.get("closed") is None or b["opened"] < a["closed"]]
    checks.append(check("a coin never held two positions at once", [], overlap))

    perf = performance(ledger, rf_apr)
    pub = published(report) if report is not None else {}
    if report is not None:
        for k in ("closed_positions", "open_positions", "book_pnl_pct", "book_excess_pct", "ann_excess_deployed_pct",
                  "ann_excess_deployed_costs_x1.5_pct", "ann_excess_deployed_costs_x2_pct", "best_coin",
                  "book_excess_without_best_coin_pct", "max_dd_pct", "t_excess_daily", "utilisation", "run_coverage", "days"):
            tol = 0 if isinstance(perf.get(k), (str, int)) and not isinstance(perf.get(k), bool) else 2e-3
            checks.append(check(f"the radar's report prints this {k}", perf.get(k), pub.get(k), tol))

    cap_bp = 2000.0  # one percent of the book, in bp of N summed over positions
    usd = book_usd / 100.0 / cap_bp  # dollars for one bp of N, on a book of `book_usd`
    stats = trade_stats([net_bp(p) for p in closed])
    n_coin = {c: len(ps) for c, ps in by_coin.items()}
    total_pos = sum(n_coin.values())
    hhi = sum((n / total_pos) ** 2 for n in n_coin.values()) if total_pos else None
    top = max(n_coin, key=n_coin.get) if n_coin else None
    pairs: dict[str, int] = {}
    for p in closed + open_:
        k = f"short {p['short_venue']} / long {p['long_venue']}"
        pairs[k] = pairs.get(k, 0) + 1
    figures = {
        "capital": "ten slots of 2N: 20N. The radar has no cash account; N is not a dollar amount",
        "first_mark": ts[0] if ts else None, "last_mark": ts[-1] if ts else None, "days": perf.get("days"),
        "realized_bp": round(realized, 1), "realized_pct_of_book": round(realized / cap_bp, 4),
        "unrealized_bp": round(unreal, 1), "unrealized_pct_of_book": round(unreal / cap_bp, 4),
        "unrealized_if_closed_now_bp": round(unreal - leave, 1),
        "book_pnl_pct": round((realized + unreal) / cap_bp, 4),
        "book_pnl_if_closed_now_pct": round((realized + unreal - leave) / cap_bp, 4),
        "illustration_usd": {"book": book_usd, "realized": round(realized * usd, 2), "unrealized": round(unreal * usd, 2),
                             "net_if_closed_now": round((realized + unreal - leave) * usd, 2),
                             "what": f"the same percentages on a book of ${book_usd:,.0f} (N = ${book_usd / 20:,.0f} a leg): an "
                                     "illustration of scale, not an account"},
        "open_positions": len(open_), "closed_positions": len(closed), "closed_trades": stats,
        "performance": perf,
        "exposure": {"slots_in_use_now": len(open_), "slots": SLOTS, "share_of_capital_deployed_now": len(open_) / SLOTS,
                     "average_share_deployed": perf.get("utilisation")},
        "concentration": {"coins_traded": len(n_coin), "most_traded_coin": top,
                          "its_share_of_positions": round(n_coin[top] / total_pos, 3) if top else None,
                          "herfindahl_by_coin": None if hhi is None else round(hhi, 3),
                          "effective_coins": None if not hhi else round(1 / hhi, 1),
                          "venue_pairs": dict(sorted(pairs.items(), key=lambda kv: -kv[1]))},
        "benchmark": {"cash_apr": rf_apr, "book_excess_over_cash_pct": perf.get("book_excess_pct"),
                      "what": "the radar's own benchmark: each position's net less the cash rate on its 2N while it was open. "
                              "Doing nothing earns the cash rate and an excess of zero"},
    }
    return {"system": "RADAR-1 funding radar (paper)", "figures": figures, "attribution": attribution(ledger),
            "checks": checks, "reconciled": all(c["ok"] for c in checks), "failed_checks": [c for c in checks if not c["ok"]],
            "open": [{"coin": p["coin"], "short": p["short_venue"], "long": p["long_venue"], "opened": p["opened"],
                      "entry_spread_apr": p["entry_spread_apr"], "funding_bp": round(p["funding_bp"], 1),
                      "price_bp": round(basis_bp(p), 1), "cost_bp": p["cost_bp"], "net_bp": round(net_bp(p), 1),
                      "net_if_closed_now_bp": round(net_bp(p) - fills_bp(p), 1)} for p in open_]}


__all__ = ["SLIP_BP", "SLOTS", "TAKER_BP", "attribution", "audit", "basis_bp", "daily_excess", "fills_bp", "net_bp",
           "performance", "published"]
