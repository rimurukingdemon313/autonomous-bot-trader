"""QT-2: the London true open (QT-1's T3) with a wider stop and a longer hold (research only). qt-2.0.0

QT-1's T3 earned +0.10R a trade before costs on 2009-2013 and beat its matched random (Welch t 2.97), but costs
of about 0.16R a trade left it at -0.05R. A trade's cost is fixed in pips, so its share of R falls as the stop
widens. QT-2 asks one question: does T3, with its stop `stop_mult` times as far and held to `until`, keep enough of
its edge to pay its costs? The signal is T3's, unchanged: only the stop, the target and the time exit move.
"""

from __future__ import annotations

import dataclasses

from .intraday import Bars, Signal
from .quarters import _utc_hour, ny_clock, session_true_open

QUARTERS_WIDE_VERSION = "qt-2.0.0"
LONDON = 360  # the London session's start, minutes from 18:00 New York (00:00 New York)
ENTRY = LONDON + 180  # T3 enters at 03:00 New York


def london_true_open_wide(b: Bars, stop_mult: float = 1.0, r: float = 2.0, until: int = LONDON + 360,
                          buf: float = 0.10) -> list[Signal]:
    """T3's signals with the stop `stop_mult` times T3's distance from the signal close, the target r times that,
    and the time exit at New York trading-day minute `until` (720 = 06:00 New York, London's end, as T3;
    1080 = 12:00 New York, the end of New York AM)."""
    _, _, off = ny_clock(b)
    out = []
    for s in session_true_open(b, LONDON, buf, 2.0):
        ref = b.c[s.i]
        d = abs(ref - s.stop) * stop_mult
        st = ref - s.side * d
        out.append(dataclasses.replace(s, stop=float(st), target=float(ref + s.side * r * d),
                                       max_bars=(until - ENTRY) // 5,
                                       deadline_hour=_utc_hour(until, int(off[s.i]))))
    return out


__all__ = ["QUARTERS_WIDE_VERSION", "london_true_open_wide"]
