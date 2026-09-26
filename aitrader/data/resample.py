"""Building higher timeframes from lower ones, complete bars only.

Resampling leakage is the quiet version of look-ahead: an H4 bar that is
still forming contains prices from after the decision. So a higher bar is
emitted only once its whole period has ended at or before `as_of`
(DATA_CONTRACT.md §3).

Boundaries:
- H1 on UTC hours;
- H4 and D1 on the New York close (17:00 America/New_York), the standard FX
  day, following US daylight saving. The FX market is closed across the
  DST switch (Sunday 02:00 New York), so no bucket straddles it.
"""

from __future__ import annotations

from datetime import datetime, timezone
from zoneinfo import ZoneInfo

import numpy as np

from .bars import FIELDS, PERIOD_SECONDS, BarSeries

_NY = ZoneInfo("America/New_York")
#: New York close (17:00) becomes 00:00 in a clock seven hours ahead.
_CLOSE_SHIFT = 7 * 3600


def _ny_offset_seconds(t: np.ndarray) -> np.ndarray:
    """UTC offset of New York for each timestamp, exact to the hour."""
    hours = t // 3600
    uniq, inverse = np.unique(hours, return_inverse=True)
    offs = np.array(
        [int(datetime.fromtimestamp(int(h) * 3600, timezone.utc).astimezone(_NY)
             .utcoffset().total_seconds()) for h in uniq],
        dtype=np.int64,
    )
    return offs[inverse]


def bucket_start(open_time: np.ndarray, timeframe: str) -> np.ndarray:
    period = PERIOD_SECONDS[timeframe]
    t = np.asarray(open_time, dtype=np.int64)
    if timeframe in ("M15", "H1"):
        return t // period * period
    shift = _ny_offset_seconds(t) + _CLOSE_SHIFT
    return (t + shift) // period * period - shift


def resample(series: BarSeries, timeframe: str, *, as_of: int) -> BarSeries:
    """`series` aggregated to `timeframe`, keeping only buckets closed by `as_of`.

    `as_of` is mandatory: there is no safe default for "now".
    """
    target = PERIOD_SECONDS[timeframe]
    if target <= series.period or target % series.period:
        raise ValueError(f"cannot resample {series.timeframe} to {timeframe}")
    src = series.as_of(as_of)
    if len(src) == 0:
        return src.take(slice(0, 0)).__class__.from_columns(
            series.symbol, timeframe, series.source,
            **{f: np.array([]) for f in FIELDS})

    b = bucket_start(src.open_time, timeframe)
    starts = np.concatenate(([0], np.flatnonzero(np.diff(b)) + 1))
    ends = np.concatenate((starts[1:], [len(b)]))
    ticks = np.add.reduceat(src.ticks, starts)
    weighted = np.add.reduceat(src.spread_mean * src.ticks, starts)
    cols = {
        "open_time": b[starts],
        "bid_open": src.bid_open[starts],
        "bid_high": np.maximum.reduceat(src.bid_high, starts),
        "bid_low": np.minimum.reduceat(src.bid_low, starts),
        "bid_close": src.bid_close[ends - 1],
        "ask_open": src.ask_open[starts],
        "ask_high": np.maximum.reduceat(src.ask_high, starts),
        "ask_low": np.minimum.reduceat(src.ask_low, starts),
        "ask_close": src.ask_close[ends - 1],
        "ticks": ticks,
        "spread_mean": np.where(ticks > 0, weighted / np.maximum(ticks, 1), np.nan),
        "spread_max": np.maximum.reduceat(src.spread_max, starts),
    }
    complete = cols["open_time"] + target <= as_of
    cols = {k: v[complete] for k, v in cols.items()}
    return BarSeries.from_columns(series.symbol, timeframe, series.source, **cols)
