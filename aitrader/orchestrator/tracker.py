"""Outcome tracking: what every action WOULD have returned, measured forward.

For each decision point the tracker follows all declared action templates
(T1/T2 x BUY/SELL) bar by bar as new bars CLOSE, with exactly the fill model
of `research/labels.py`: enter at the next bar's open on the far side, exit
on the near side, stop before target, gap-through stops at the open,
slippage, commission and swap. A test holds the two to identical numbers.

This single mechanism serves three purposes, in backtest and live alike:
- pattern memory grows from experience (all four outcomes of a situation);
- skipped and rejected candidates get SHADOW outcomes, so the system can
  learn whether an objection, a lesson or the risk engine is costing it
  good trades;
- nothing is known before it happens: an outcome is emitted only when the
  bar that resolves it has closed.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable

import numpy as np

from ..data.resample import bucket_start
from ..research.labels import TEMPLATES, CostModel

ACTIONS = tuple(f"{t.key}:{s}" for t in TEMPLATES for s in ("BUY", "SELL"))


@dataclass
class _Leg:
    action: str
    side: int
    stop_atr: float
    target_atr: float
    max_bars: int
    entry: float | None = None
    stop: float | None = None
    target: float | None = None
    risk: float | None = None
    entry_day: int | None = None
    bars: int = 0
    best: float = -np.inf
    worst: float = np.inf
    r: float | None = None
    reason: int | None = None
    exit_time: int | None = None


@dataclass
class Tracked:
    key: str
    symbol: str
    decision_time: int
    atr: float
    features: np.ndarray
    context: dict
    legs: list[_Leg] = field(default_factory=list)

    @property
    def done(self) -> bool:
        return all(l.r is not None for l in self.legs)


class OutcomeTracker:
    def __init__(self, pip_of: Callable[[str], float], costs: CostModel = CostModel(),
                 on_resolved: Callable[[Tracked], None] | None = None) -> None:
        self.pip_of = pip_of
        self.costs = costs
        self.on_resolved = on_resolved
        self.open: dict[str, list[Tracked]] = {}

    def track(self, key: str, symbol: str, decision_time: int, atr: float, features: np.ndarray,
              context: dict) -> Tracked | None:
        if atr is None or not np.isfinite(atr) or atr <= 0:
            return None
        tr = Tracked(key, symbol, decision_time, atr, features, context,
                     [_Leg(f"{t.key}:{s}", 1 if s == "BUY" else -1, t.stop_atr, t.target_atr, t.max_bars)
                      for t in TEMPLATES for s in ("BUY", "SELL")])
        self.open.setdefault(symbol, []).append(tr)
        return tr

    def on_bar(self, symbol: str, bar: dict) -> list[Tracked]:
        """A bar of `symbol` has closed. Advance every open track on it."""
        done = []
        items = self.open.get(symbol)
        if not items:
            return done
        c = self.costs
        pip = self.pip_of(symbol)
        slip, comm = c.slippage_pips * pip, c.commission_pips_rt * pip
        k = c.spread_multiple
        mid = {x: (bar[f"ask_{x}"] + bar[f"bid_{x}"]) / 2 for x in ("open", "high", "low", "close")}
        half = {x: (bar[f"ask_{x}"] - bar[f"bid_{x}"]) / 2 * k for x in ("open", "high", "low", "close")}
        bid = {x: mid[x] - half[x] for x in mid}
        ask = {x: mid[x] + half[x] for x in mid}
        day = int(bucket_start(np.array([bar["open_time"]]), "D1")[0])
        keep = []
        for tr in items:
            if bar["open_time"] < tr.decision_time:
                keep.append(tr)
                continue
            for leg in tr.legs:
                if leg.r is not None:
                    continue
                if leg.entry is None:  # the first bar after the decision: enter at its open
                    leg.entry = (ask["open"] + slip) if leg.side > 0 else (bid["open"] - slip)
                    leg.stop = leg.entry - leg.side * leg.stop_atr * tr.atr
                    leg.target = leg.entry + leg.side * leg.target_atr * tr.atr
                    leg.risk = abs(leg.entry - leg.stop)
                    leg.entry_day = day
                side = leg.side
                if side > 0:
                    lo, hi, op, cl = bid["low"], bid["high"], bid["open"], bid["close"]
                    leg.best, leg.worst = max(leg.best, hi - leg.entry), min(leg.worst, lo - leg.entry)
                    stop_hit, tgt_hit = lo <= leg.stop, hi >= leg.target
                    stop_fill = min(op, leg.stop) - slip
                else:
                    lo, hi, op, cl = ask["low"], ask["high"], ask["open"], ask["close"]
                    leg.best, leg.worst = max(leg.best, leg.entry - lo), min(leg.worst, leg.entry - hi)
                    stop_hit, tgt_hit = hi >= leg.stop, lo <= leg.target
                    stop_fill = max(op, leg.stop) + slip
                leg.bars += 1
                exit_px = None
                if stop_hit:
                    exit_px, leg.reason = stop_fill, -1
                elif tgt_hit:
                    exit_px, leg.reason = leg.target, 1
                elif leg.bars >= leg.max_bars:
                    exit_px, leg.reason = cl - side * slip, 0
                if exit_px is not None:
                    nights = max(0, (day - leg.entry_day) // 86400)
                    swap = c.swap_atr_per_night * tr.atr * nights
                    leg.r = ((exit_px - leg.entry) * side - comm - swap) / leg.risk
                    leg.exit_time = bar["close_time"]
            if tr.done:
                done.append(tr)
                if self.on_resolved:
                    self.on_resolved(tr)
            else:
                keep.append(tr)
        self.open[symbol] = keep
        return done

    def pending(self) -> int:
        return sum(len(v) for v in self.open.values())
