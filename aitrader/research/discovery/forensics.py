"""Why trades lose: every losing trade classified by COUNTERFACTUALS computed on the same bars.

A loss is assigned the FIRST cause below that the price path supports (the order is the
priority, and it is fixed so the percentages mean something):

    COSTS            the trade was a winner before costs (gross R > 0) and a loser after them
    EXIT_GAVE_BACK   it was at least +1R in profit at some point, and still ended as a loss
    STOP_TOO_TIGHT   it was stopped out, and the same entry with a stop twice as wide (same
                     target, same horizon) would have ended in profit after costs
    ENTRY_TIMING     entering one bar earlier or one bar later would have ended in profit
    WRONG_DIRECTION  it never went +0.25R in its favour, and the opposite trade from the same bar
                     would have ended in profit after costs
    NORMAL_VARIANCE  none of the above: a reasonable trade that lost, as some must

Each counterfactual is ANALYSIS, not a trading rule: "one bar earlier" uses a bar the decision
could have been made on, but the lesson is only a hypothesis until tested out of sample. Regime
is reported as a table (mean R and loss rate per er120 x vol_ratio cell), not forced into a cause.
"""

from __future__ import annotations

from dataclasses import replace

import numpy as np

from ..labels import CostModel
from .exits import ExitSpec, simulate

FORENSICS_VERSION = "forensics-1.0.0"
CAUSES = ("COSTS", "EXIT_GAVE_BACK", "STOP_TOO_TIGHT", "ENTRY_TIMING", "WRONG_DIRECTION", "NORMAL_VARIANCE")


def _one(series, row: int, side: int, exit_: ExitSpec, pip: float, costs: CostModel, atr, delay: int = 0):
    o = simulate(series, np.array([row]), side, exit_, pip, costs, atr=atr, delay=delay)
    return {k: (float(getattr(o, k)[0]) if k != "reason" else int(o.reason[0]))
            for k in ("r", "mfe_r", "mae_r", "cost_r", "reason")}


def classify(series, row: int, side: int, exit_: ExitSpec, pip: float, costs: CostModel = CostModel(),
             atr=None) -> dict:
    """The outcome of one trade and, if it lost, its cause (see the module docstring)."""
    base = _one(series, row, side, exit_, pip, costs, atr)
    out = {"row": int(row), "side": int(side), **base, "cause": None}
    if not np.isfinite(base["r"]) or base["r"] >= 0:
        return out
    if base["r"] + base["cost_r"] > 0:
        out["cause"] = "COSTS"
    elif base["mfe_r"] >= 1.0:
        out["cause"] = "EXIT_GAVE_BACK"
    elif base["reason"] == -1 and _one(series, row, side, replace(exit_, stop_atr=2 * exit_.stop_atr), pip, costs,
                                        atr)["r"] > 0:
        out["cause"] = "STOP_TOO_TIGHT"
    elif any(np.isfinite(x["r"]) and x["r"] > 0 for x in (
            _one(series, row - 1, side, exit_, pip, costs, atr) if row >= 1 else {"r": np.nan},
            _one(series, row, side, exit_, pip, costs, atr, delay=1))):
        out["cause"] = "ENTRY_TIMING"
    elif base["mfe_r"] < 0.25 and _one(series, row, -side, exit_, pip, costs, atr)["r"] > 0:
        out["cause"] = "WRONG_DIRECTION"
    else:
        out["cause"] = "NORMAL_VARIANCE"
    return out


def breakdown(results: list[dict]) -> dict:
    """Share of losing trades AND share of the R lost, per cause; plus what winners and losers did."""
    losers = [x for x in results if x["cause"] is not None]
    winners = [x for x in results if x["cause"] is None and np.isfinite(x["r"])]
    lost = -sum(x["r"] for x in losers)
    table = {}
    for c in CAUSES:
        xs = [x for x in losers if x["cause"] == c]
        table[c] = {"trades": len(xs), "share_of_losses": round(len(xs) / len(losers), 4) if losers else None,
                    "share_of_R_lost": round(-sum(x["r"] for x in xs) / lost, 4) if lost > 0 else None}
    arr = lambda xs, k: np.array([x[k] for x in xs], float)  # noqa: E731
    return {
        "version": FORENSICS_VERSION, "trades": len(results), "losers": len(losers), "winners": len(winners),
        "mean_R": round(float(np.mean([x["r"] for x in results if np.isfinite(x["r"])])), 4) if results else None,
        "mean_cost_R": round(float(np.nanmean(arr(results, "cost_r"))), 4) if results else None,
        "causes": table,
        "winners_median_mae_R": round(float(np.median(arr(winners, "mae_r"))), 3) if winners else None,
        "losers_median_mfe_R": round(float(np.median(arr(losers, "mfe_r"))), 3) if losers else None,
        "winners_median_mfe_R": round(float(np.median(arr(winners, "mfe_r"))), 3) if winners else None,
    }
