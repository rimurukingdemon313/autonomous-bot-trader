"""RC-EQ2 rules (research/preregistrations/RC-EQ2.md). rc2-1.0.0

Kept apart from rc.py so that RC-EQ's frozen code hash still holds.
"""

from __future__ import annotations

import numpy as np

RC2_VERSION = "rc2-1.0.0"


def halloween(dates, closes, n_universe: int, enter_month: int = 10, exit_month: int = 4) -> dict:
    """E8 "Sell in May" (Bouman & Jacobsen 2002): long from the last close of `enter_month` to the last
    close of `exit_month` (Nov-Apr for 10, 4), flat otherwise. Reads the calendar only, never a price."""
    out = {}
    w = 1.0 / n_universe
    for name, c in closes.items():
        idx = [j for j in range(len(c)) if np.isfinite(c[j]) and c[j] > 0]
        tgt = np.zeros(len(c))
        for k, j in enumerate(idx):
            m = dates[j].month
            last_of_month = k + 1 == len(idx) or dates[idx[k + 1]].month != m
            # in the market for months enter+1 .. exit (wrapping the year), entered at enter's last close
            months_in = {(enter_month + i - 1) % 12 + 1 for i in range(1, (exit_month - enter_month) % 12 + 1)}
            if m in months_in:
                held = not (m == exit_month and last_of_month)
            else:
                held = m == enter_month and last_of_month
            tgt[j] = w if held else 0.0
        out[name] = tgt
    return out


__all__ = ["RC2_VERSION", "halloween"]
