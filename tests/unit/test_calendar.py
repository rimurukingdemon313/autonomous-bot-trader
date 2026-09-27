"""The economic calendar: what the models are told about scheduled news, and what they are never told.

The feed is a fake with known events, and the clock is pinned, so every
answer is known by construction.
"""

from __future__ import annotations

from datetime import datetime, timezone

from aitrader.data.calendar import REFRESH_S, RETRY_S, EconomicCalendar, currencies_for, session_at

T = int(datetime(2026, 9, 25, 12, 0, tzinfo=timezone.utc).timestamp())


def iso(minutes: int) -> str:
    return datetime.fromtimestamp(T + minutes * 60, timezone.utc).isoformat()


EVENTS = [
    {"title": "Non-Farm Payrolls", "country": "USD", "impact": "High", "date": iso(30), "forecast": "180K", "previous": "150K"},
    {"title": "ECB Press Conference", "country": "EUR", "impact": "High", "date": iso(-60)},
    {"title": "BoJ minutes", "country": "JPY", "impact": "Medium", "date": iso(90)},
    {"title": "Bank Holiday", "country": "USD", "impact": "Holiday", "date": iso(10)},
    {"title": "Old", "country": "USD", "impact": "High", "date": iso(-600)},
    {"title": "Far", "country": "USD", "impact": "High", "date": iso(3000)},
]


class Feed:
    def __init__(self, events=EVENTS, fail=False):
        self.events, self.fail, self.calls = events, fail, 0

    def __call__(self):
        self.calls += 1
        if self.fail:
            raise ConnectionError("unreachable")
        return self.events


def cal(tmp_path, feed, now=T):
    clock = {"t": now}
    return EconomicCalendar(tmp_path / "c.json", clock=lambda: clock["t"], fetch=feed), clock


def test_the_pairs_events_in_the_window_with_minutes_away(tmp_path):
    c, _ = cal(tmp_path, Feed())
    out = c.for_symbol("EURUSD", T)
    assert out["feed"]["status"] == "FRESH"
    assert [(e["title"], e["minutes_away"]) for e in out["events"]] == [("ECB Press Conference", -60),
                                                                         ("Non-Farm Payrolls", 30)]
    assert out["events"][1]["forecast"] == "180K"
    assert [e["title"] for e in c.for_symbol("USDJPY", T)["events"]] == ["Non-Farm Payrolls", "BoJ minutes"]


def test_gold_follows_usd_releases():
    assert currencies_for("XAUUSD") == ("USD",) and currencies_for("EURUSD") == ("EUR", "USD")


def test_an_unreachable_feed_is_reported_as_unknown_never_as_no_events(tmp_path):
    c, _ = cal(tmp_path, Feed(fail=True))
    out = c.for_symbol("EURUSD", T)
    assert out["feed"]["status"] == "UNAVAILABLE" and "unreachable" in out["feed"]["reason"]
    assert out["events"] is None  # unknown is not "nothing scheduled"


def test_it_downloads_at_most_hourly_and_backs_off_after_a_failure(tmp_path):
    feed = Feed()
    c, clock = cal(tmp_path, feed)
    for _ in range(5):
        c.for_symbol("EURUSD", T)
    assert feed.calls == 1
    clock["t"] += REFRESH_S
    c.for_symbol("EURUSD", T)
    assert feed.calls == 2
    feed.fail = True
    clock["t"] += REFRESH_S
    c.for_symbol("EURUSD", T)
    c.for_symbol("EURUSD", T)
    assert feed.calls == 3  # one failed try, then it waits
    out = c.for_symbol("EURUSD", T)
    assert out["feed"]["status"] in ("FRESH", "CACHED") and out["events"]  # the last good copy is still shown
    clock["t"] += RETRY_S
    c.for_symbol("EURUSD", T)
    assert feed.calls == 4


def test_a_restart_starts_from_the_saved_copy(tmp_path):
    c, _ = cal(tmp_path, Feed())
    c.for_symbol("EURUSD", T)
    again, _ = cal(tmp_path, Feed(fail=True))
    assert [e["title"] for e in again.for_symbol("EURUSD", T)["events"]] == ["ECB Press Conference", "Non-Farm Payrolls"]


def test_the_dashboard_read_never_downloads(tmp_path):
    feed = Feed()
    c, _ = cal(tmp_path, feed)
    assert c.state(refresh=False)["status"] == "UNAVAILABLE" and feed.calls == 0


def test_sessions():
    at = lambda h: int(datetime(2026, 9, 25, h, tzinfo=timezone.utc).timestamp())  # noqa: E731
    assert session_at(at(3)) == ["Asia (Tokyo/Sydney)"] and session_at(at(13)) == ["London", "New York"]
