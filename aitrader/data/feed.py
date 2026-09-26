"""Market feeds: the one interface through which decisions see prices.

`ReplayFeed` serves recorded bars as of a clock time — the backtest's view.
A live feed (TradeLocker) implements the same interface, so the orchestrator
cannot tell which one it is running on; that is what makes a backtest a test
of the system that actually runs.
"""

from __future__ import annotations

from typing import Protocol

import numpy as np

from ..risk.engine import Quote
from .bars import BarSeries


class MarketFeed(Protocol):
    def symbols(self) -> list[str]: ...
    def bars(self, symbol: str, as_of: int, count: int) -> BarSeries | None: ...
    def quote(self, symbol: str, now: int) -> Quote | None: ...


class ReplayFeed:
    def __init__(self, series: dict[str, BarSeries]) -> None:
        self.series = dict(series)
        self._avail = {s: v.available_at for s, v in self.series.items()}

    def symbols(self) -> list[str]:
        return sorted(self.series)

    def index_at(self, symbol: str, t: int) -> int:
        """Index of the last bar closed at or before t (-1 if none)."""
        return int(np.searchsorted(self._avail[symbol], t, side="right")) - 1

    def bars(self, symbol: str, as_of: int, count: int) -> BarSeries | None:
        s = self.series.get(symbol)
        if s is None:
            return None
        k = self.index_at(symbol, as_of) + 1
        if k <= 0:
            return None
        return s.take(slice(max(0, k - count), k))

    def quote(self, symbol: str, now: int) -> Quote | None:
        s = self.series.get(symbol)
        if s is None:
            return None
        i = self.index_at(symbol, now)
        if i < 0:
            return None
        return Quote(symbol, float(s.bid_close[i]), float(s.ask_close[i]), int(s.available_at[i]))

    def bar_closing_at(self, symbol: str, t: int) -> dict | None:
        """The bar that closed exactly at t, as a dict, or None."""
        s = self.series.get(symbol)
        if s is None:
            return None
        i = self.index_at(symbol, t)
        if i < 0 or int(s.available_at[i]) != t:
            return None
        return {"open_time": int(s.open_time[i]), "close_time": t,
                **{f: float(getattr(s, f)[i]) for f in (
                    "bid_open", "bid_high", "bid_low", "bid_close", "ask_open", "ask_high", "ask_low", "ask_close")}}
