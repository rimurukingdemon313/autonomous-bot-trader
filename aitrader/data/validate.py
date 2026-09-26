"""Data validation and the per-instrument quality report (DATA_CONTRACT.md §5).

HARD failures make a series unusable: nothing downstream may read it.
SOFT findings are reported and travel with the data; they are facts about
the feed, not reasons to repair it.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone

import numpy as np

from .bars import BarSeries
from .instruments import Instrument

#: Weekday gaps longer than this many hours are reported. Shorter pauses
#: happen in thin hours and are not anomalies.
GAP_REPORT_HOURS = 2.0
#: A bar-to-bar mid move beyond this many robust deviations is a spike
#: CANDIDATE. Reported, not removed: real markets gap too (SNB, 2015).
SPIKE_MADS = 25.0


@dataclass
class QualityReport:
    symbol: str
    timeframe: str
    bars: int
    first: str | None
    last: str | None
    hard: list[str] = field(default_factory=list)
    soft: dict[str, object] = field(default_factory=dict)

    @property
    def usable(self) -> bool:
        return not self.hard

    def as_dict(self) -> dict:
        return {
            "symbol": self.symbol, "timeframe": self.timeframe, "bars": self.bars,
            "first": self.first, "last": self.last, "usable": self.usable,
            "hard": self.hard, "soft": self.soft,
        }


def _iso(t: int) -> str:
    return datetime.fromtimestamp(int(t), timezone.utc).isoformat()


def validate(series: BarSeries, instrument: Instrument) -> QualityReport:
    n = len(series)
    rep = QualityReport(
        series.symbol, series.timeframe, n,
        _iso(series.open_time[0]) if n else None,
        _iso(series.open_time[-1]) if n else None,
    )
    if n == 0:
        rep.hard.append("no bars")
        return rep

    t = series.open_time
    # Time: strictly increasing, on the timeframe's grid.
    if n > 1 and not np.all(np.diff(t) > 0):
        rep.hard.append(f"timestamps not strictly increasing ({int((np.diff(t) <= 0).sum())} times)")
    if series.timeframe in ("M15", "H1"):
        off = int((t % series.period != 0).sum())
        if off:
            rep.hard.append(f"{off} bars off the {series.timeframe} grid")

    # Prices: finite, positive, internally consistent, bid <= ask.
    for side in ("bid", "ask"):
        o, h, l, c = (getattr(series, f"{side}_{x}") for x in ("open", "high", "low", "close"))
        allp = np.concatenate([o, h, l, c])
        if not np.all(np.isfinite(allp)):
            rep.hard.append(f"non-finite {side} prices")
            continue
        if np.any(allp <= 0):
            rep.hard.append(f"non-positive {side} prices")
        bad = int(((l > np.minimum(o, c)) | (h < np.maximum(o, c)) | (l > h)).sum())
        if bad:
            rep.hard.append(f"{bad} bars with inconsistent {side} OHLC")
    for x in ("open", "high", "low", "close"):
        crossed = int((getattr(series, f"ask_{x}") < getattr(series, f"bid_{x}")).sum())
        if crossed:
            rep.hard.append(f"{crossed} bars with ask_{x} < bid_{x}")

    # Scale: the median must sit inside the instrument's plausible band.
    med = float(np.median(series.mid_close))
    if not instrument.in_band(med):
        rep.hard.append(
            f"median price {med:g} outside plausible band {instrument.band}: wrong scale or wrong instrument"
        )

    # Soft: gaps during the trading week.
    if n > 1:
        dt = np.diff(t)
        weekday = np.array([datetime.fromtimestamp(int(x), timezone.utc).weekday() for x in t[:-1]])
        # A gap starting Friday or Saturday is the weekend.
        long_gaps = (dt > GAP_REPORT_HOURS * 3600) & (weekday < 4)
        rep.soft["weekday_gaps_over_2h"] = int(long_gaps.sum())
        rep.soft["longest_weekday_gap_hours"] = round(float(dt[weekday < 4].max()) / 3600, 2) if np.any(weekday < 4) else 0.0

        mid = series.mid_close
        r = np.diff(np.log(mid))
        mad = float(np.median(np.abs(r - np.median(r)))) or 1e-12
        spikes = np.flatnonzero(np.abs(r) > SPIKE_MADS * mad)
        rep.soft["spike_candidates"] = int(len(spikes))
        rep.soft["spike_examples"] = [_iso(t[i + 1]) for i in spikes[:5]]

    spread_pips = series.spread_mean / instrument.pip
    rep.soft["spread_pips_median"] = round(float(np.nanmedian(spread_pips)), 3)
    rep.soft["spread_pips_p95"] = round(float(np.nanpercentile(spread_pips, 95)), 3)
    rep.soft["zero_tick_bars"] = int((series.ticks <= 0).sum())
    return rep
