"""Pattern discovery by a declared, bounded screen — every cell counted, every result kept.

The screen asks one narrow question of the DISCOVERY segment only: in which cells of a declared
grid does a baseline trade (exit E1) have a positive mean net R? The grid is

    singles:  each declared feature in its low / mid / high bin                 x BUY, SELL
    pairs:    each STATE feature bin  x  each TRIGGER feature bin               x BUY, SELL

and nothing else: no thresholds are tuned, no cell is added after seeing results. Every cell
is a test, including cells with too few trades (p = 1), so the false-discovery control counts
what was actually looked at. Survivors (Benjamini-Hochberg q <= 0.10, n >= 100) become DRAFT
hypotheses; the screen proves nothing by itself — it only decides what the later, untouched
segments are asked.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from ..labels import BUY, SELL
from .stats import bh, p_one_sided
from .study import Condition, Study

SCREEN_VERSION = "screen-1.0.0"
SIDES = {BUY: "BUY", SELL: "SELL"}


@dataclass(frozen=True)
class Grid:
    states: tuple[str, ...]
    triggers: tuple[str, ...]

    def __post_init__(self) -> None:
        if set(self.states) & set(self.triggers):
            raise ValueError("a feature is either a state or a trigger")

    def conditions(self) -> list[Condition]:
        out = [Condition(((f, b),)) for f in self.states + self.triggers for b in (0, 1, 2)]
        out += [Condition(((s, a), (t, b))) for s in self.states for t in self.triggers
                for a in (0, 1, 2) for b in (0, 1, 2)]
        return out

    def size(self) -> int:
        return 2 * len(self.conditions())

    def to_json(self) -> dict:
        return {"states": list(self.states), "triggers": list(self.triggers), "tests": self.size()}


def screen(study: Study, grid: Grid, exit_key: str = "E1", min_n: int = 100, q: float = 0.10,
           keep: int = 20, z_lower: float = 2.0) -> dict:
    """Every cell x side of the grid on `study`; BH-FDR over all of them; the best `keep` survivors
    by the lower edge of their interval (mean - z_lower * clustered se)."""
    rows = []
    for cond in grid.conditions():
        masks = study.masks(cond)
        for side in (BUY, SELL):
            st = study.trades(masks, exit_key, side).stats()
            testable = st["n"] >= min_n and st["t"] is not None
            rows.append({"condition": cond.key, "side": SIDES[side], "n": st["n"],
                         "mean_R": _r(st["mean"]), "se": _r(st["se"]), "t": _r(st["t"], 3),
                         "clusters": st["clusters"], "testable": testable,
                         "p": p_one_sided(st["t"]) if testable else 1.0})
    rejected, qv = bh(np.array([r["p"] for r in rows]), q)
    for r, rej, qq in zip(rows, rejected, qv):
        r["q"] = float(qq)
        r["discovery"] = bool(rej and r["testable"] and (r["mean_R"] or 0) > 0)
        r["lower"] = (r["mean_R"] - z_lower * r["se"]) if r["testable"] and r["se"] is not None else None
    found = [r for r in rows if r["discovery"]]
    found.sort(key=lambda r: (-r["lower"], r["condition"], r["side"]))
    return {"version": SCREEN_VERSION, "segment": study.segment.to_json(), "exit": exit_key, "min_n": min_n,
            "q": q, "tests": len(rows), "testable": sum(r["testable"] for r in rows),
            "discoveries": len(found), "survivors": found[:keep], "table": rows}


def _r(x, nd=5):
    return None if x is None else round(float(x), nd)
