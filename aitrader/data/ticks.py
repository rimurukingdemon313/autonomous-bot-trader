"""Aggregating bid/ask ticks into bars. Numpy only, so it is testable anywhere.

Invalid ticks (non-finite, non-positive, ask below bid) are DROPPED and
COUNTED, never repaired. The counts travel into the data manifest, so an
instrument whose feed was mostly rejected is visible rather than quietly
thin (DATA_CONTRACT.md §4, §5).
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np


@dataclass
class TickAudit:
    received: int = 0
    kept: int = 0
    non_finite: int = 0
    non_positive: int = 0
    crossed: int = 0  # ask < bid
    out_of_order: int = 0

    def as_dict(self) -> dict:
        return dict(self.__dict__)

    def add(self, other: "TickAudit") -> None:
        for k, v in other.__dict__.items():
            setattr(self, k, getattr(self, k) + v)


@dataclass
class TickBars:
    columns: dict[str, np.ndarray]
    audit: TickAudit = field(default_factory=TickAudit)


def aggregate(t_ms: np.ndarray, bid: np.ndarray, ask: np.ndarray, period: int) -> TickBars:
    """Bars of `period` seconds from ticks at millisecond UTC timestamps.

    A bar exists only where at least one valid tick exists. Empty intervals
    produce no bar: a gap stays a gap.
    """

    t_ms = np.asarray(t_ms, dtype=np.int64)
    bid = np.asarray(bid, dtype=np.float64)
    ask = np.asarray(ask, dtype=np.float64)
    audit = TickAudit(received=len(t_ms))

    finite = np.isfinite(bid) & np.isfinite(ask)
    audit.non_finite = int((~finite).sum())
    positive = finite & (bid > 0) & (ask > 0)
    audit.non_positive = int((finite & ~positive).sum())
    ordered = positive & (ask >= bid)
    audit.crossed = int((positive & ~ordered).sum())
    t_ms, bid, ask = t_ms[ordered], bid[ordered], ask[ordered]

    if len(t_ms) > 1:
        backwards = int((np.diff(t_ms) < 0).sum())
        audit.out_of_order = backwards
        if backwards:
            order = np.argsort(t_ms, kind="stable")
            t_ms, bid, ask = t_ms[order], bid[order], ask[order]
    audit.kept = len(t_ms)

    if len(t_ms) == 0:
        empty_f = np.array([], dtype=np.float64)
        cols = {k: empty_f for k in (
            "bid_open", "bid_high", "bid_low", "bid_close",
            "ask_open", "ask_high", "ask_low", "ask_close", "spread_mean", "spread_max")}
        cols["open_time"] = np.array([], dtype=np.int64)
        cols["ticks"] = np.array([], dtype=np.int64)
        return TickBars(cols, audit)

    bucket = (t_ms // 1000) // period * period
    starts = np.concatenate(([0], np.flatnonzero(np.diff(bucket)) + 1))
    ends = np.concatenate((starts[1:], [len(bucket)]))
    counts = ends - starts
    spread = ask - bid

    cols = {
        "open_time": bucket[starts],
        "bid_open": bid[starts],
        "bid_high": np.maximum.reduceat(bid, starts),
        "bid_low": np.minimum.reduceat(bid, starts),
        "bid_close": bid[ends - 1],
        "ask_open": ask[starts],
        "ask_high": np.maximum.reduceat(ask, starts),
        "ask_low": np.minimum.reduceat(ask, starts),
        "ask_close": ask[ends - 1],
        "ticks": counts.astype(np.int64),
        "spread_mean": np.add.reduceat(spread, starts) / counts,
        "spread_max": np.maximum.reduceat(spread, starts),
    }
    return TickBars(cols, audit)


def week_openings(t_ms: np.ndarray, min_gap_hours: float = 30.0) -> np.ndarray:
    """UTC timestamps (seconds) of the first tick after each weekend-sized gap.

    Used to MEASURE the feed's clock rather than assume it: the FX week
    opens Sunday 17:00 New York, i.e. 21:00 or 22:00 UTC.
    """
    t = np.asarray(t_ms, dtype=np.int64) // 1000
    if len(t) < 2:
        return np.array([], dtype=np.int64)
    gaps = np.flatnonzero(np.diff(t) >= min_gap_hours * 3600) + 1
    return t[gaps]
