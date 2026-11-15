"""Trade statistics that say when they are undefined.

A win rate over no closed trade is not zero: it does not exist. Every ratio here is None with its reason when it
cannot be computed, and carries its sample size (CLAUDE.md rule 6: a plausible zero is worse than a visible gap).
"""

from __future__ import annotations

import math

#: Fewer closed trades than this and a ratio is reported with `sample: "insufficient"`.
SMALL = 30


def mean_t(xs: list[float]) -> tuple[float | None, float | None]:
    """The mean and its t-statistic (mean over its standard error). The t is None with fewer than two values or no
    spread: it is never invented."""
    n = len(xs)
    if n == 0:
        return None, None
    m = sum(xs) / n
    if n < 2:
        return m, None
    var = sum((x - m) ** 2 for x in xs) / (n - 1)
    if var <= 0:
        return m, None
    return m, m / math.sqrt(var / n)


def trade_stats(pnls: list[float]) -> dict:
    """Closed trades' statistics. `undefined` names every figure that could not be computed and why."""
    n = len(pnls)
    wins = [x for x in pnls if x > 0]
    losses = [x for x in pnls if x < 0]
    undefined: dict[str, str] = {}
    out: dict = {"closed": n, "won": len(wins), "lost": len(losses), "flat": n - len(wins) - len(losses),
                 "total": sum(pnls), "gross_won": sum(wins), "gross_lost": sum(losses),
                 "sample": "none" if n == 0 else "insufficient" if n < SMALL else "ok"}
    if n == 0:
        for k in ("win_rate", "expectancy", "t", "average_win", "average_loss", "profit_factor"):
            out[k] = None
            undefined[k] = "no closed trade"
        out["undefined"] = undefined
        return out
    out["win_rate"] = len(wins) / n
    out["expectancy"], out["t"] = mean_t(pnls)
    if out["t"] is None:
        undefined["t"] = "fewer than two trades, or no spread between them"
    out["average_win"] = sum(wins) / len(wins) if wins else None
    out["average_loss"] = sum(losses) / len(losses) if losses else None
    if not wins:
        undefined["average_win"] = "no winning trade"
    if not losses:
        undefined["average_loss"] = "no losing trade"
    out["profit_factor"] = sum(wins) / -sum(losses) if losses else None
    if not losses:
        undefined["profit_factor"] = "no losing trade: the ratio has no denominator"
    out["undefined"] = undefined
    return out


def drawdown(values: list[float]) -> dict:
    """The largest fall from a running peak, in the series' own units, and how far the last value is below the peak.
    The series must begin with the starting value: a fall from the start counts."""
    if not values:
        return {"max": None, "now": None, "peak_at": None, "trough_at": None}
    peak, peak_i, worst, at = values[0], 0, 0.0, (0, 0)
    for i, v in enumerate(values):
        if v > peak:
            peak, peak_i = v, i
        if peak - v > worst:
            worst, at = peak - v, (peak_i, i)
    return {"max": worst, "now": peak - values[-1], "peak_at": at[0], "trough_at": at[1]}


def check(name: str, expected, found, tolerance: float = 0.0) -> dict:
    """One reconciliation: two routes to the same figure. A figure missing on either side fails the check."""
    if expected is None or found is None:
        return {"check": name, "expected": expected, "found": found, "tolerance": tolerance, "ok": False,
                "why": "a figure is missing"}
    if isinstance(expected, (int, float)) and isinstance(found, (int, float)):
        ok = math.isfinite(float(expected)) and math.isfinite(float(found)) and abs(float(expected) - float(found)) <= tolerance
    else:
        ok = expected == found
    return {"check": name, "expected": expected, "found": found, "tolerance": tolerance, "ok": bool(ok)}


__all__ = ["SMALL", "check", "drawdown", "mean_t", "trade_stats"]
