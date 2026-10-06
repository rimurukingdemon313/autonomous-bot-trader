"""Placebo audit of the simulators: random entries in random directions on a driftless random walk, built from
a fine path so a bar's high/low are the path's true extremes. A simulator whose fill rules are honest shows no
gross edge. Writes research/results/NE-placebo-audit.json.

    python scripts/ne_placebo_audit.py

Two regimes: path steps finer than the spread (a liquid market's ticks) and steps coarser than the spread
(fast markets, where a stop is jumped rather than touched). Seeds are fixed.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from aitrader.research.canon import engine as E  # noqa: E402
from aitrader.research.discovery import intraday as I  # noqa: E402

OUT = ROOT / "research" / "results" / "NE-placebo-audit.json"
T0 = 1425307800
N_BARS, N_TRADES = 200_000, 4000


def path_bars(sub: int, sd_sub: float, spread: float, seed: int, start: float):
    rng = np.random.default_rng(seed)
    path = start + np.cumsum(rng.normal(0, sd_sub, N_BARS * sub + 1))
    seg = path[:-1].reshape(N_BARS, sub)
    o, c = seg[:, 0], path[sub::sub]
    h, lo = np.maximum(seg.max(1), c), np.minimum(seg.min(1), c)
    hs = spread / 2
    return np.arange(N_BARS) * 300 + T0, o - hs, h - hs, lo - hs, c - hs, o + hs, h + hs, lo + hs, c + hs


def t_of(g: np.ndarray) -> float:
    return float(g.mean() / (g.std(ddof=1) / np.sqrt(len(g))))


def main() -> int:
    res: dict = {"bars": N_BARS, "orders": N_TRADES, "canon": {}, "intraday.simulate": {}}
    regimes = {"fine (step < spread)": (64, 0.05, 0.4, 1000.0), "coarse (step > spread)": (4, 0.6, 0.2, 1000.0)}
    for name, (sub, sd, spread, start) in regimes.items():
        cols = path_bars(sub, sd, spread, 3, start)
        q = E.Quotes("RW", 300, *cols)
        sdbar = sd * np.sqrt(sub)
        for ex, rr in (("stop+time", None), ("stop+target 1:1.5", 1.5), ("stop+target 1:2", 2.0)):
            rng = np.random.default_rng(1)
            idx = np.sort(rng.choice(np.arange(10, N_BARS - 1000, 40), N_TRADES, replace=False))
            sides = rng.choice([-1, 1], len(idx))
            stop_bp = 3 * sdbar / start * 1e4
            orders = [E.Order(int(i), int(s), stop_bp=stop_bp, target_bp=rr * stop_bp if rr else None, max_bars=30)
                      for i, s in zip(idx, sides)]
            tr = E.simulate(q, orders, E.Costs()).trades
            g = np.array([x.gross_bp for x in tr])
            res["canon"][f"{name} | {ex}"] = {"trades": len(tr), "gross_bp": round(float(g.mean()), 4),
                                               "t": round(t_of(g), 2)}
    # intraday.simulate (ID-1, ID-2): FX scale, its own Costs and risk checks; stops 12 bar-sigmas so the
    # production risk checks admit the trades
    for name, (sub, sd) in {"fine (step < spread)": (64, 0.00001), "coarse (step > spread)": (4, 0.00012)}.items():
        cols = path_bars(sub, sd, 0.00007, 7, 1.1)
        b = I.Bars("EURUSD", 0.0001, *cols)
        sdbar = sd * np.sqrt(sub)
        for ex, rr in (("1:1.5", 1.5), ("1:2", 2.0)):
            rng = np.random.default_rng(3)
            idx = np.sort(rng.choice(np.arange(20, N_BARS - 1000, 40), N_TRADES, replace=False))
            sig = []
            for i, s in zip(idx, rng.choice([-1, 1], len(idx))):
                ref = (b.ao[i] + b.bo[i]) / 2
                sig.append(I.Signal(int(i), int(s), float(ref - s * 12 * sdbar), float(ref + s * rr * 12 * sdbar), 36))
            tr, _ = I.simulate(b, sig, I.Costs())
            g = np.array([x.gross_mid / x.risk for x in tr])
            res["intraday.simulate"][f"{name} | {ex}"] = {"trades": len(tr), "gross_r": round(float(g.mean()), 4),
                                                          "t": round(t_of(g), 2)}
    OUT.write_text(json.dumps(res, indent=1) + "\n")
    print(json.dumps(res, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
