"""PAPER_FORWARD performance: what the closed paper trades actually did, in dollars and in R, after costs.

Pure functions over the `outcome` records the orchestrator writes for every closed trade. Nothing is
estimated or filled in: a statistic that cannot be computed is None. Every summary carries its sample label
("none" / "insufficient" below 30 / "adequate"): ten trades at 70% is reported as exactly that, with
`sample: "insufficient"`. Losing trades, costs and every symbol are always included; nothing is filtered.
"""

from __future__ import annotations

import math
from collections import defaultdict
from datetime import datetime, timezone

PAPER_METRICS_VERSION = "paper-metrics-1.0.0"
MIN_SAMPLE = 30


def _sample(n: int) -> str:
    return "none" if n == 0 else "insufficient" if n < MIN_SAMPLE else "adequate"


def _round(x, k=4):
    return None if x is None or (isinstance(x, float) and not math.isfinite(x)) else round(x, k)


def _streaks(wins: list[bool]) -> tuple[int, int, int]:
    """Longest win run, longest loss run, current run (+n wins / -n losses)."""
    best_w = best_l = cur = 0
    for w in wins:
        cur = (cur + 1 if cur >= 0 else 1) if w else (cur - 1 if cur <= 0 else -1)
        best_w, best_l = max(best_w, cur), max(best_l, -cur)
    return best_w, best_l, cur


def summary(outcomes: list[dict]) -> dict:
    """Totals over closed trades with a known net P/L, oldest first."""
    rows = sorted((o for o in outcomes if o.get("net_pnl") is not None), key=lambda o: o["closed"])
    n = len(rows)
    out = {"trades": n, "sample": _sample(n), "unpriced": sum(1 for o in outcomes if o.get("net_pnl") is None)}
    if n == 0:
        return out
    net = [o["net_pnl"] for o in rows]
    wins = [x > 0 for x in net]
    gp, gl = sum(x for x in net if x > 0), -sum(x for x in net if x <= 0)
    rs = [o["r"] for o in rows if o.get("r") is not None]
    curve, peak, max_dd = 0.0, 0.0, 0.0
    for x in net:
        curve += x
        peak = max(peak, curve)
        max_dd = max(max_dd, peak - curve)
    days: dict[str, float] = defaultdict(float)
    for o in rows:
        days[datetime.fromtimestamp(o["closed"], timezone.utc).strftime("%Y-%m-%d")] += o["net_pnl"]
    bw, bl, cur = _streaks(wins)
    costs = [o.get("costs_total") for o in rows]
    gross = [o.get("gross_pnl") for o in rows]
    out.update({
        "wins": sum(wins), "losses": n - sum(wins), "win_rate": _round(sum(wins) / n),
        "gross_profit": _round(gp, 2), "gross_loss": _round(gl, 2), "net_pnl": _round(sum(net), 2),
        "gross_pnl_before_costs": _round(sum(gross), 2) if all(g is not None for g in gross) else None,
        "costs_total": _round(sum(costs), 2) if all(c is not None for c in costs) else None,
        "fees": _round(sum(o.get("fees") or 0 for o in rows), 2),
        "slippage": _round(sum(o.get("slippage") or 0 for o in rows), 2),
        "average_r": _round(sum(rs) / len(rs)) if rs else None,
        "expectancy_r": _round(sum(rs) / len(rs)) if rs else None,  # net R per trade
        "expectancy_usd": _round(sum(net) / n, 2),
        "profit_factor": _round(gp / gl) if gl > 0 else None,  # undefined, not infinite, with no loss
        "max_drawdown_usd": _round(max_dd, 2),
        "worst_day_usd": _round(min(days.values()), 2),
        "average_holding_h": _round(sum(o.get("holding_s") or 0 for o in rows) / n / 3600, 2),
        "max_consecutive_wins": bw, "max_consecutive_losses": bl, "current_streak": cur,
        "direction_right_rate": _round(_rate(rows, "prediction_correct")),
        "risk_estimate_right_rate": _round(_rate(rows, "risk_estimate_correct")),
    })
    return out


def _rate(rows: list[dict], key: str) -> float | None:
    xs = [o[key] for o in rows if o.get(key) is not None]
    return sum(xs) / len(xs) if xs else None


def breakdown(outcomes: list[dict], key: str) -> dict:
    groups: dict[str, list[dict]] = defaultdict(list)
    for o in outcomes:
        groups[str(o.get(key) or "unknown")].append(o)
    keep = ("trades", "sample", "win_rate", "net_pnl", "expectancy_r", "profit_factor")
    return {k: {f: v for f, v in summary(g).items() if f in keep} for k, g in sorted(groups.items())}


def report(outcomes: list[dict]) -> dict:
    return {"version": PAPER_METRICS_VERSION, "overall": summary(outcomes),
            "by_symbol": breakdown(outcomes, "symbol"), "by_direction": breakdown(outcomes, "direction"),
            "by_agent": breakdown(outcomes, "agent"), "by_regime": breakdown(outcomes, "regime"),
            "by_partition": breakdown(outcomes, "partition")}


__all__ = ["PAPER_METRICS_VERSION", "breakdown", "report", "summary"]
