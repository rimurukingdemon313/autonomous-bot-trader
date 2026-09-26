"""Performance measurement. Never win rate alone; small samples are labelled.

Everything is computed from the immutable trade records the orchestrator
wrote, so the numbers describe what the system actually did.
"""

from __future__ import annotations

import math
from collections import defaultdict
from datetime import datetime, timezone

import numpy as np


def _t(xs: np.ndarray) -> float | None:
    if len(xs) < 2 or np.std(xs, ddof=1) == 0:
        return None
    return float(np.mean(xs) / (np.std(xs, ddof=1) / math.sqrt(len(xs))))


def r_stats(rs, min_sample: int = 30) -> dict:
    x = np.asarray([r for r in rs if r is not None and np.isfinite(r)], float)
    n = len(x)
    if n == 0:
        return {"n": 0, "sample": "none"}
    wins, losses = x[x > 0], x[x <= 0]
    out = {
        "n": n, "avg_R": round(float(x.mean()), 4), "median_R": round(float(np.median(x)), 4),
        "t": (round(_t(x), 2) if _t(x) is not None else None),
        "win_rate": round(float((x > 0).mean()), 4),
        "avg_win_R": round(float(wins.mean()), 4) if len(wins) else None,
        "avg_loss_R": round(float(losses.mean()), 4) if len(losses) else None,
        "profit_factor_R": round(float(wins.sum() / -losses.sum()), 3) if len(losses) and losses.sum() < 0 else None,
        "total_R": round(float(x.sum()), 2),
        "sample": "insufficient" if n < min_sample else "adequate",
    }
    if n >= 20:
        rng = np.random.default_rng(0)
        boots = rng.choice(x, size=(5000, n), replace=True).mean(axis=1)
        out["bootstrap_p05_avg_R"] = round(float(np.percentile(boots, 5)), 4)
        out["p_avg_R_le_0"] = round(float((boots <= 0).mean()), 4)
    return out


def max_consecutive_losses(rs) -> int:
    worst = cur = 0
    for r in rs:
        cur = cur + 1 if (r is not None and r <= 0) else 0
        worst = max(worst, cur)
    return worst


def equity_metrics(trades: list[dict], start_balance: float) -> dict:
    """Realised equity (trade closes) — open-position marks are not invented."""
    trades = sorted(trades, key=lambda t: t["closed"])
    eq, peak, max_dd = start_balance, start_balance, 0.0
    curve, daily = [], defaultdict(float)
    for t in trades:
        pnl = t.get("pnl")
        if pnl is None:
            continue
        eq += pnl
        peak = max(peak, eq)
        max_dd = min(max_dd, (eq - peak) / peak)
        curve.append((t["closed"], round(eq, 2)))
        daily[t["closed"] // 86400] += pnl
    out = {"start": start_balance, "end": round(eq, 2), "net": round(eq - start_balance, 2),
           "return_pct": round((eq / start_balance - 1) * 100, 2), "max_drawdown_pct": round(max_dd * 100, 2),
           "curve": curve}
    if len(daily) >= 60 and len(trades) >= 30:
        days = sorted(daily)
        span = np.arange(days[0], days[-1] + 1)
        rets = np.array([daily.get(d, 0.0) for d in span]) / start_balance
        sd = rets.std(ddof=1)
        down = rets[rets < 0]
        out["sharpe_daily_ann"] = round(float(rets.mean() / sd * math.sqrt(252)), 3) if sd > 0 else None
        out["sortino_daily_ann"] = (round(float(rets.mean() / down.std(ddof=1) * math.sqrt(252)), 3)
                                    if len(down) > 1 and down.std(ddof=1) > 0 else None)
    else:
        out["sharpe_daily_ann"] = out["sortino_daily_ann"] = None
        out["note"] = "Sharpe/Sortino not reported: fewer than 60 trading days or 30 trades"
    gross_win = sum(t["pnl"] for t in trades if t.get("pnl") and t["pnl"] > 0)
    gross_loss = -sum(t["pnl"] for t in trades if t.get("pnl") and t["pnl"] < 0)
    out["profit_factor"] = round(gross_win / gross_loss, 3) if gross_loss > 0 else None
    return out


def breakdown(trades: list[dict], key) -> dict:
    groups: dict[str, list] = defaultdict(list)
    for t in trades:
        groups[str(key(t))].append(t.get("r"))
    return {k: r_stats(v) for k, v in sorted(groups.items())}


def year_of(ts: int) -> int:
    return datetime.fromtimestamp(int(ts), timezone.utc).year


def summarise(trades: list[dict], start_balance: float) -> dict:
    rs = [t.get("r") for t in sorted(trades, key=lambda t: t["closed"])]
    return {
        "overall": r_stats(rs),
        "equity": equity_metrics(trades, start_balance),
        "max_consecutive_losses": max_consecutive_losses(rs),
        "by_year": breakdown(trades, lambda t: year_of(t["opened"])),
        "by_symbol": breakdown(trades, lambda t: t["symbol"]),
        "by_regime": breakdown(trades, lambda t: t.get("regime")),
        "by_family": breakdown(trades, lambda t: t.get("family")),
        "by_exit": breakdown(trades, lambda t: t.get("exit_reason")),
        "position_hours": int(sum((t["closed"] - t["opened"]) / 3600 for t in trades)),
    }
