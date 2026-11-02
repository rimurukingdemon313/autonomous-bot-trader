"""The time machine's picture (dual-ai 1.16.0): the replays of a trade as a fan, its stop, target and entry, and the
odds, from the numbers learning/timemachine.py recorded. Deterministic: the same numbers give the same bytes."""

from __future__ import annotations

import numpy as np

from . import font
from .canvas import Canvas

FAN_VERSION = "fan-1.0.0"
W, H = 960, 540
LEFT, RIGHT, TOP, BOTTOM = 90, 930, 56, 420
INK, MUTED = (30, 30, 30), (120, 120, 120)
GREEN, RED, BAND = (34, 139, 76), (200, 50, 50), (70, 110, 190)


def render_time_machine(tm: dict, symbol: str) -> bytes | None:
    """A PNG of one time-machine run, or None without one."""
    rows = ((tm or {}).get("fan") or {}).get("rows") or []
    if not rows:
        return None
    entry, stop, target = float(tm["entry"]), float(tm["stop"]), float(tm["target"])
    hours = [0.0] + [float(r[0]) for r in rows]
    pct = np.array([[entry] * 5] + [r[1:6] for r in rows], float)  # p05, p25, p50, p75, p95 per hour
    lo = min(stop, target, entry, float(pct.min()))
    hi = max(stop, target, entry, float(pct.max()))
    pad = (hi - lo) * 0.06 or abs(entry) * 0.001
    lo, hi = lo - pad, hi + pad
    span_h = max(hours[-1], 1.0)
    xs = lambda h: LEFT + (RIGHT - LEFT) * h / span_h  # noqa: E731
    ys = lambda p: BOTTOM - (BOTTOM - TOP) * (p - lo) / (hi - lo)  # noqa: E731
    c = Canvas(W, H)
    c.frame(LEFT, TOP, RIGHT, BOTTOM, (200, 200, 200))
    for x in range(LEFT, RIGHT):
        h = (x - LEFT) / (RIGHT - LEFT) * span_h
        band = [float(np.interp(h, hours, pct[:, k])) for k in range(5)]
        c.blend(x, ys(band[4]), x + 1, ys(band[0]), BAND, 0.18)
        c.blend(x, ys(band[3]), x + 1, ys(band[1]), BAND, 0.35)
    for k in range(1, len(hours)):
        c.line(xs(hours[k - 1]), ys(pct[k - 1, 2]), xs(hours[k]), ys(pct[k, 2]), BAND, width=2)
    fmt = (lambda p: f"{p:.3f}") if abs(entry) > 20 else (lambda p: f"{p:.5f}")  # noqa: E731
    for price, color, name in ((target, GREEN, "TARGET"), (stop, RED, "STOP")):
        c.hline(ys(price), LEFT, RIGHT, color, width=2)
        c.text(RIGHT - 190, ys(price) - 18, f"{name} {fmt(price)}", (255, 255, 255), scale=2, bg=color)
    c.hline(ys(entry), LEFT, RIGHT, MUTED, width=1, dash=6)
    c.text(LEFT + 6, ys(entry) - 18, f"ENTRY {fmt(entry)}", INK, scale=2, bg=(240, 240, 240))
    title = f"{symbol} {tm.get('side', '')} - TIME MACHINE - {int(tm.get('replays', 0)):,} REPLAYS OF {int(tm.get('hours', 0))} H"
    c.text(LEFT, 14, title, INK, scale=3 if font.width(title, 3) <= W - LEFT - 10 else 2)
    c.text(LEFT, BOTTOM + 8, "NOW", MUTED, scale=2)
    c.text(RIGHT - 70, BOTTOM + 8, f"+{int(span_h)} H", MUTED, scale=2)
    pt, ps, pn = (float(tm.get(k) or 0.0) for k in ("target_first", "stop_first", "neither"))
    c.text(LEFT, BOTTOM + 40, f"TARGET FIRST {pt:.0%}   STOP FIRST {ps:.0%}   NEITHER {pn:.0%}", INK, scale=3)
    c.text(LEFT, BOTTOM + 76, f"NEEDS {float(tm.get('win_rate_needed') or 0):.0%} OF THE DECIDED: "
                              f"{str(tm.get('verdict', '')).upper()}", INK, scale=2)
    c.text(LEFT, BOTTOM + 100, "A SIMULATION OF THE PAIR'S LAST 60 DAYS, NOT A FORECAST", MUTED, scale=2)
    return c.png()


__all__ = ["FAN_VERSION", "render_time_machine"]
