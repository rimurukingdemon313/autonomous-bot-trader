"""IX-3: the overnight drift of US equity-index CFDs at the European cash open (research only). ixd-1.0.0

Economic reason (Boyarchenko, Larsen & Whelan 2023, "The Overnight Drift", Review of Financial Studies):
US equity-index futures earn a large share of their return around the opening of European cash markets.
Dealers who absorbed end-of-day customer selling carry that inventory overnight and lay it off when
European liquidity arrives; the price rises as they are compensated for holding it. The drift is larger
after sessions that ended with selling pressure (negative end-of-day order imbalance, which shows up as
a negative last hour of the US cash session).

Everything is a causal function of H1 bid/ask bars:

- day d's entry time E_d is 09:00 Frankfurt (the Xetra cash open, DST-correct), a bar boundary;
- LONG at the open of the bar starting at E_d (ASK + slippage), exit at the open of the bar starting
  `hold_h` hours later (BID - slippage), unless the protective stop is hit first (checked against each
  held bar's range, gaps filled at the open);
- variant COND trades only when the previous US cash session's last hour (15:00 -> 16:00 New York) fell,
  measured from mids that are complete hours before E_d;
- protective stop: 2.5 x the standard deviation of the previous 60 holding-window returns, at least 3
  spreads;
- no financing: entry and exit are between two 17:00 New York rollovers.

Nothing here sizes a live trade; the risk engine is the only sizing authority.
"""

from __future__ import annotations

from datetime import date, datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo

import numpy as np

from .ixmom import Bars, Trade

IXD_VERSION = "ixd-1.0.0"
ENTRY_TZ, ENTRY_AT = "Europe/Berlin", time(9, 0)
US_TZ, US_LAST_HOUR, US_CLOSE = "America/New_York", time(15, 0), time(16, 0)


def _epoch(d: date, tz: str, hm: time) -> int:
    return int(datetime.combine(d, hm, tzinfo=ZoneInfo(tz)).astimezone(timezone.utc).timestamp())


def entry_epoch(d: date) -> int:
    return _epoch(d, ENTRY_TZ, ENTRY_AT)


def last_us_session(d: date) -> date:
    """The US session that ended before day d's European open: the previous weekday."""
    p = d - timedelta(days=1)
    while p.weekday() >= 5:
        p -= timedelta(days=1)
    return p


def trades(b: Bars, hold_h: int = 1, conditional: bool = False, slip_pts: float = 0.0, cost_mult: float = 1.0,
           vol_days: int = 60, stop_sd: float = 2.5) -> list[Trade]:
    idx = b.index()
    tz = ZoneInfo(ENTRY_TZ)
    days = sorted({datetime.fromtimestamp(int(x), timezone.utc).astimezone(tz).date() for x in b.t[::6]})
    out: list[Trade] = []
    past: list[float] = []
    for d in days:
        if d.weekday() >= 5:
            continue
        e = entry_epoch(d)
        i, j = idx.get(e), idx.get(e + hold_h * 3600)
        if i is None or j is None:
            continue
        mid_in = (b.bo[i] + b.ao[i]) / 2
        mid_out = (b.bo[j] + b.ao[j]) / 2
        p = last_us_session(d)
        a, c = idx.get(_epoch(p, US_TZ, US_LAST_HOUR)), idx.get(_epoch(p, US_TZ, US_CLOSE))
        signal = None
        if a is not None and c is not None:
            signal = ((b.bo[c] + b.ao[c]) - (b.bo[a] + b.ao[a])) / (b.bo[a] + b.ao[a])
        eligible = len(past) >= vol_days and (not conditional or (signal is not None and signal < 0))
        if eligible:
            sd = float(np.std(past[-vol_days:]))
            spread_in = float(b.ao[i] - b.bo[i])
            entry = float(b.ao[i] + (cost_mult - 1.0) * spread_in / 2 + cost_mult * slip_pts)
            dist = max(stop_sd * sd * mid_in, 3 * spread_in)
            stop = entry - dist
            exit_px, stopped = None, False
            for k in range(i, j):
                if k > i and b.bo[k] <= stop:
                    sp = float(b.ao[k] - b.bo[k])
                    exit_px, stopped = float(b.bo[k]) - (cost_mult - 1.0) * sp / 2 - cost_mult * slip_pts, True
                    break
                if b.bl[k] <= stop:
                    sp = float(b.ao[k] - b.bo[k])
                    exit_px, stopped = float(stop) - (cost_mult - 1.0) * sp / 2 - cost_mult * slip_pts, True
                    break
            if exit_px is None:
                sp = float(b.ao[j] - b.bo[j])
                exit_px = float(b.bo[j] - (cost_mult - 1.0) * sp / 2 - cost_mult * slip_pts)
            gross = (mid_out - mid_in) / mid_in * 1e4
            net = (exit_px - entry) / mid_in * 1e4
            out.append(Trade(b.symbol, d, 1, float(signal) if signal is not None else 0.0, entry, exit_px, stop,
                             float(gross), float(net), float(gross - net), float((exit_px - entry) / dist), stopped))
        past.append(mid_out / mid_in - 1.0)
    return out


__all__ = ["IXD_VERSION", "entry_epoch", "last_us_session", "trades"]
