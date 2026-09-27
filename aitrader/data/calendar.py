"""The economic calendar: scheduled releases, their importance, forecast and previous value.

Source: the ForexFactory weekly calendar feed (the one the historical
archive used in production, `bot/news.py`, transferred here as a smaller
reader). It is a SCHEDULE: what is due, when, how important, what is
forecast. It is not a headline feed; nothing here claims to know news that
has not been scheduled.

What the models receive (`for_symbol`):

- the events for the pair's currencies from 2 hours ago to 24 hours ahead,
  each with minutes away (negative = already released);
- the market session open now (Asia / London / New York);
- the feed's state: FRESH, CACHED (older copy, with its age) or
  UNAVAILABLE with the reason. An unavailable feed is reported as such,
  never as "no events": a plausible-looking empty list would be a
  fabricated value.

Fetching is rate-limited (the feed asks for at most one download an hour)
and a failure waits 5 minutes before the next try. The last good copy is
kept on the volume, so a restart does not start blind.
"""

from __future__ import annotations

import json
import threading
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

from ..observability import log_event

CALENDAR_URL = "https://nfs.faireconomy.media/ff_calendar_thisweek.json"
CALENDAR_VERSION = "calendar-1.0.0"
REFRESH_S = 3600          # the feed's own guidance: at most one download an hour
RETRY_S = 300             # after a failure
STALE_S = 3 * 86400       # an older copy is still shown, marked CACHED, up to 3 days
WINDOW_BACK_MIN, WINDOW_AHEAD_MIN = 120, 24 * 60

#: Gold and silver trade in USD: USD releases move them (the archive's fix: not ("USD", "USD")).
METALS = {"XAUUSD": ("USD",), "XAGUSD": ("USD",)}


def currencies_for(symbol: str) -> tuple[str, ...]:
    s = "".join(ch for ch in symbol.upper() if ch.isalpha())[:6]
    if s in METALS:
        return METALS[s]
    return (s[:3], s[3:]) if len(s) == 6 else ()


def session_at(t: int) -> list[str]:
    """Major FX sessions open at `t` (UTC hours, approximate, ignoring DST shifts)."""
    h = datetime.fromtimestamp(t, timezone.utc).hour
    out = []
    if h >= 23 or h < 8:
        out.append("Asia (Tokyo/Sydney)")
    if 7 <= h < 16:
        out.append("London")
    if 12 <= h < 21:
        out.append("New York")
    return out or ["between sessions"]


def _http_fetch() -> list:
    req = urllib.request.Request(CALENDAR_URL, headers={"User-Agent": "aitrader/1.0"})
    with urllib.request.urlopen(req, timeout=15) as resp:  # noqa: S310 - fixed https URL
        return json.loads(resp.read().decode("utf-8"))


def _parse_time(raw) -> int | None:
    try:
        return int(datetime.fromisoformat(str(raw).replace("Z", "+00:00")).timestamp())
    except (TypeError, ValueError):
        return None


class EconomicCalendar:
    def __init__(self, cache_path: Path | str, clock: Callable[[], float] = time.time,
                 fetch: Callable[[], list] = _http_fetch) -> None:
        self.cache_path = Path(cache_path)
        self.clock, self._fetch = clock, fetch
        self._lock = threading.Lock()
        self._events: list[dict] = []
        self._fetched_at: float | None = None
        self._next_try = 0.0
        self._error: str | None = None
        self._load_cache()

    def _load_cache(self) -> None:
        try:
            raw = json.loads(self.cache_path.read_text())
            self._events, self._fetched_at = list(raw["events"]), float(raw["fetched_at"])
        except (OSError, ValueError, KeyError, TypeError):
            pass

    def _refresh(self) -> None:
        now = self.clock()
        if self._fetched_at is not None and now - self._fetched_at < REFRESH_S:
            return
        if now < self._next_try:
            return
        try:
            events = self._fetch()
            if not isinstance(events, list):
                raise ValueError("the calendar feed returned an unexpected shape")
        except Exception as exc:  # a read: report it and try again later, never invent events
            self._error = f"{type(exc).__name__}: {exc}"[:200]
            self._next_try = now + RETRY_S
            log_event("NEWS", f"economic calendar unavailable: {self._error}", severity="warning")
            return
        self._events, self._fetched_at, self._error = events, now, None
        try:
            self.cache_path.parent.mkdir(parents=True, exist_ok=True)
            self.cache_path.write_text(json.dumps({"fetched_at": now, "events": events}))
        except OSError:
            pass

    def state(self, refresh: bool = True) -> dict:
        """The feed's state. `refresh=False` never downloads: for the dashboard, which must not wait on it."""
        with self._lock:
            if refresh:
                self._refresh()
            now = self.clock()
            if self._fetched_at is None:
                if self._error is None:  # never tried (the dashboard read never downloads)
                    return {"status": "PENDING", "reason": "first download at the next decision"}
                return {"status": "UNAVAILABLE", "reason": self._error}
            age = int(now - self._fetched_at)
            if age > STALE_S:
                return {"status": "UNAVAILABLE", "reason": f"last copy is {age // 3600} h old"
                        + (f"; {self._error}" if self._error else "")}
            return {"status": "FRESH" if age < REFRESH_S * 2 else "CACHED", "age_min": age // 60,
                    **({"last_error": self._error} if self._error else {})}

    def for_symbol(self, symbol: str, t: int) -> dict:
        """What the models read about scheduled news for `symbol` at time `t`."""
        st = self.state()
        out = {"source": "ForexFactory economic calendar (scheduled releases, not headlines)",
               "feed": st, "session_open_now": session_at(t), "currencies": list(currencies_for(symbol))}
        if st["status"] == "UNAVAILABLE":
            out["events"] = None  # unknown, not "none"
            return out
        want = set(currencies_for(symbol))
        rows = []
        with self._lock:
            events = list(self._events)
        for e in events:
            if str(e.get("country")) not in want or str(e.get("impact")) in ("Holiday", "Non-Economic"):
                continue
            at = _parse_time(e.get("date"))
            if at is None:
                continue
            mins = (at - t) // 60
            if -WINDOW_BACK_MIN <= mins <= WINDOW_AHEAD_MIN:
                rows.append({"minutes_away": int(mins), "currency": e.get("country"), "title": e.get("title"),
                             "impact": e.get("impact"), "forecast": e.get("forecast") or None,
                             "previous": e.get("previous") or None})
        rows.sort(key=lambda r: r["minutes_away"])
        out["events"] = rows[:25]
        return out
