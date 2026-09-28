"""TradeLocker candle history: one learned endpoint shape PER timeframe, and no probing floods.

The broker is a fake that serves H1 only in the documented shape and never
serves M1, the situation that made a single shared shape flap: an M1 request
failing used to erase the shape H1 had learned.
"""

from __future__ import annotations

import pytest

from aitrader.broker.tradelocker._compat import BrokerError, BrokerRejected
from aitrader.broker.tradelocker.history import FAILED_COOLDOWN_S, STRATEGIES, HistoryFetcher

BARS = {"d": {"barDetails": [{"t": 1_700_000_000_000 + i * 3_600_000, "o": 1.1, "h": 1.2, "l": 1.0, "c": 1.15}
                             for i in range(5)]}}


class Broker:
    def __init__(self):
        self.calls = []

    def __call__(self, path, params):
        self.calls.append((path, params["resolution"]))
        if path == STRATEGIES[0].path and params["resolution"] == "1H" and "tradableInstrumentId" in params:
            return BARS
        if params["resolution"] in ("1m", "1M"):
            raise BrokerRejected("400 unsupported resolution")
        return {"d": {"barDetails": []}}


def fetcher():
    clock = {"t": 0.0}
    return HistoryFetcher(Broker(), clock=lambda: clock["t"]), clock


def test_a_failing_timeframe_never_erases_the_shape_another_timeframe_learned():
    h, _ = fetcher()
    assert len(h.fetch(instrument_id=1, route_id=2, timeframe="H1", count=5)) == 5
    learned = h.describe()["by_timeframe"]["H1"]
    with pytest.raises(BrokerError):
        h.fetch(instrument_id=1, route_id=2, timeframe="M1", count=5)
    assert h.describe()["by_timeframe"] == {"H1": learned}  # H1 still knows its shape
    before = len(h._request.calls)
    h.fetch(instrument_id=1, route_id=2, timeframe="H1", count=5)
    assert len(h._request.calls) == before + 1  # one request, no re-probing


def test_a_timeframe_the_broker_does_not_serve_is_not_reprobed_until_the_cooldown_ends():
    h, clock = fetcher()
    with pytest.raises(BrokerError):
        h.fetch(instrument_id=1, route_id=2, timeframe="M1", count=5)
    probes = len(h._request.calls)
    assert probes == len(STRATEGIES)
    for _ in range(10):
        with pytest.raises(BrokerError, match="probed recently"):
            h.fetch(instrument_id=1, route_id=2, timeframe="M1", count=5)
    assert len(h._request.calls) == probes  # no flood
    clock["t"] += FAILED_COOLDOWN_S + 1
    with pytest.raises(BrokerError):
        h.fetch(instrument_id=1, route_id=2, timeframe="M1", count=5)
    assert len(h._request.calls) == 2 * probes  # tried again after the cooldown


class FlakyM1Broker(Broker):
    """Serves H1 (documented shape) and M1 (upper-case shape) until M1 stops being served."""

    def __init__(self):
        super().__init__()
        self.m1_ok = True

    def __call__(self, path, params):
        if params["resolution"] == "1M":  # the upper-case minute shape: bars, until they stop
            self.calls.append((path, params["resolution"]))
            return BARS if (self.m1_ok and path == STRATEGIES[1].path) else {"d": {"barDetails": []}}
        return super().__call__(path, params)


def test_when_a_learned_timeframe_stops_working_only_that_timeframe_is_forgotten():
    b = FlakyM1Broker()
    h = HistoryFetcher(b, clock=lambda: 0.0)
    h.fetch(instrument_id=1, route_id=2, timeframe="H1", count=5)
    h.fetch(instrument_id=1, route_id=2, timeframe="M1", count=5)
    assert set(h.describe()["by_timeframe"]) == {"H1", "M1"}
    b.m1_ok = False
    with pytest.raises(BrokerError):
        h.fetch(instrument_id=1, route_id=2, timeframe="M1", count=5)
    assert set(h.describe()["by_timeframe"]) == {"H1"}  # H1's shape survives M1's failure
