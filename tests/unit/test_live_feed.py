"""The live feed spends the broker's rate limit carefully.

TradeLocker sits behind Cloudflare, which answered 1015 (rate limited) when the
dashboard and the scheduler each fetched every price and every bar series on
their own. The fake broker counts requests, so the budget is asserted, not assumed.
"""

from __future__ import annotations

from aitrader.risk.engine import Quote
from aitrader.service.runtime import LiveFeedAdapter

from tests.integration.test_pipeline import START, market


class Broker:
    def __init__(self):
        self.quotes = 0
        self.bar_requests: list[tuple[str, int]] = []
        self.series = market("EURUSD", START, 24 * 60, 1, 1.30)

    def quote(self, symbol):
        self.quotes += 1
        return Quote(symbol, 1.1, 1.1001, 0)

    def bars(self, symbol, as_of, count, timeframe):
        self.bar_requests.append((timeframe, count))
        s = self.series
        return s.take(slice(max(0, len(s) - count), len(s)))


def feed():
    clock = {"t": int(market("EURUSD", START, 24 * 60, 1, 1.30).available_at[-1])}
    return LiveFeedAdapter(Broker(), lambda: clock["t"]), clock


def test_a_quote_is_fetched_once_per_ttl_whoever_asks():
    f, clock = feed()
    for _ in range(20):  # the dashboard, the account, the market table, a decision...
        assert f.quote("EURUSD").bid == 1.1
    assert f.tl.quotes == 1
    clock["t"] += LiveFeedAdapter.QUOTE_TTL_S
    f.quote("EURUSD")
    assert f.tl.quotes == 2


def test_one_bar_request_serves_every_length_asked_for():
    f, clock = feed()
    t = clock["t"]
    lens = [len(f.bars("EURUSD", t, n)) for n in (3, 260, 720)]
    assert lens == [3, 260, 720]  # each caller gets exactly what it asked for
    assert f.tl.bar_requests == [("H1", 720)]  # from ONE request


def test_a_failed_fetch_is_not_retried_within_its_window():
    f, clock = feed()
    f.tl.bars = lambda *a: (_ for _ in ()).throw(ConnectionError("429"))
    calls = []
    orig = f.tl.bars
    f.tl.bars = lambda *a: calls.append(a) or orig(*a)
    for _ in range(5):
        assert f.bars("EURUSD", clock["t"], 260) is None
    assert len(calls) == 1
