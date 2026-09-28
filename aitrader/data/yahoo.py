"""Market data from Yahoo Finance's public chart API: no broker, no account, no key.

Selected with DATA_SOURCE=yahoo (PAPER only). It serves the same interface as
the broker feed: completed bars on M1, M5, M15, H1, H4 (resampled from H1) and
D1, and a live price.

What it is and is not, stated where it matters:

- Yahoo publishes one price per bar, not a bid and an ask. The paper
  account still has to pay a spread, so each pair gets a FIXED, typical
  spread (`SPREADS_PIPS`, overridable with PAPER_SPREAD_PIPS_<PAIR>), added
  around the price. It is an estimate, labelled as such in every bar's
  source ("yahoo+est-spread"), never presented as a broker quote.
- The price is Yahoo's last traded/indicative FX rate with its own
  timestamp. The quote carries THAT time, not the time we fetched it, so a
  delayed price is seen as delayed by the freshness checks.
- A forming bar is never returned; a bar with a missing value is dropped.
- Yahoo publishes no FX volume, so the volume-based feature (tick_activity)
  is declared unavailable (`unavailable_features`) rather than reported as
  missing data; every other feature must still be present.
- Reads are cached (a price for 10 s, bars per timeframe window) and a
  failure is cached for its window too, so a refusal does not become a
  retry storm. Every failure is kept with its reason for the dashboard.
"""

from __future__ import annotations

import json
import threading
import time
import urllib.request
from typing import Callable

import numpy as np

from ..data.bars import BarSeries
from ..data.resample import resample
from ..observability import log_event
from ..risk.engine import Quote

YAHOO_VERSION = "yahoo-feed-1.0.0"
CHART_URL = "https://query1.finance.yahoo.com/v8/finance/chart/{sym}?interval={interval}&range={range}"

#: Yahoo interval and the range that holds enough completed bars for the traders.
INTERVALS = {"M1": ("1m", "1d"), "M5": ("5m", "5d"), "M15": ("15m", "5d"), "H1": ("60m", "60d"), "D1": ("1d", "1y")}
PERIOD_S = {"M1": 60, "M5": 300, "M15": 900, "H1": 3600, "H4": 14400, "D1": 86400}
CACHE_S = {"M1": 60, "M5": 60, "M15": 60, "H1": 300, "D1": 3600}
QUOTE_TTL_S = 10

#: Typical retail spreads in pips at liquid hours: an estimate for the paper account, not a quote.
SPREADS_PIPS = {"EURUSD": 0.8, "GBPUSD": 1.2, "USDJPY": 1.0, "AUDUSD": 1.0, "USDCAD": 1.5, "USDCHF": 1.5,
                "NZDUSD": 1.5, "EURGBP": 1.2, "EURJPY": 1.5, "GBPJPY": 2.5, "EURCHF": 1.8, "AUDJPY": 1.8,
                "XAUUSD": 3.0}


def pip(symbol: str) -> float:
    return 0.1 if symbol.startswith("XAU") else 0.01 if symbol.endswith("JPY") else 0.0001


def yahoo_symbol(symbol: str) -> str:
    return "GC=F" if symbol == "XAUUSD" else f"{symbol}=X"  # gold: the front futures contract, not spot


def _http(url: str) -> dict:
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (aitrader paper feed)",
                                               "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=15) as resp:  # noqa: S310 - fixed https host
        return json.loads(resp.read().decode("utf-8"))


class YahooFeed:
    #: Fields this source never provides: excluded from the completeness check, and recorded.
    unavailable_features = ("tick_activity",)

    def __init__(self, symbols, clock: Callable[[], float], fetch: Callable[[str], dict] | None = None,
                 spreads_pips: dict | None = None) -> None:
        self._symbols = list(symbols)
        self.clock = clock
        self._fetch = fetch or (lambda url: _http(url))  # resolved at call time
        self.spreads = {s: (spreads_pips or {}).get(s, SPREADS_PIPS.get(s, 2.0)) * pip(s) for s in self._symbols}
        self._lock = threading.Lock()
        self._bars: dict = {}
        self._quotes: dict = {}
        self.errors: dict[tuple[str, str], str] = {}
        self.last_ok: int | None = None
        self.last_bars_ok: int | None = None
        self.last_error: str | None = None

    def symbols(self):
        return list(self._symbols)

    # ── raw ─────────────────────────────────────────────────────────────

    def _chart(self, symbol: str, tf: str) -> dict:
        interval, rng = INTERVALS[tf]
        payload = self._fetch(CHART_URL.format(sym=yahoo_symbol(symbol), interval=interval, range=rng))
        chart = (payload or {}).get("chart") or {}
        if chart.get("error"):
            raise ValueError(f"Yahoo: {chart['error']}")
        result = (chart.get("result") or [None])[0]
        if not result:
            raise ValueError("Yahoo returned no result")
        return result

    def _series(self, symbol: str, tf: str, as_of: int) -> BarSeries | None:
        result = self._chart(symbol, tf)
        t = np.asarray(result.get("timestamp") or [], dtype=float)
        q = ((result.get("indicators") or {}).get("quote") or [{}])[0]
        cols = {k: np.asarray([np.nan if v is None else v for v in (q.get(k) or [])], dtype=float)
                for k in ("open", "high", "low", "close")}
        n = min([len(t)] + [len(v) for v in cols.values()])
        if n == 0:
            return None
        t, cols = t[:n], {k: v[:n] for k, v in cols.items()}
        ok = np.isfinite(t)
        for v in cols.values():
            ok &= np.isfinite(v) & (v > 0)
        ok &= t + PERIOD_S[tf] <= as_of  # a forming bar is never used
        if tf in ("M1", "M5", "M15", "H1"):
            ok &= (t.astype(np.int64) % PERIOD_S[tf]) == 0  # Yahoo's odd partial rows are not bars
        if not ok.any():
            return None
        t = t[ok].astype(np.int64)
        o, h, lo, c = (cols[k][ok] for k in ("open", "high", "low", "close"))
        h, lo = np.maximum.reduce([h, o, c]), np.minimum.reduce([lo, o, c])
        half = self.spreads.get(symbol, 2.0 * pip(symbol)) / 2
        spread = np.full(len(t), 2 * half)
        return BarSeries.from_columns(
            symbol, tf, "yahoo+est-spread", open_time=t,
            bid_open=o - half, bid_high=h - half, bid_low=lo - half, bid_close=c - half,
            ask_open=o + half, ask_high=h + half, ask_low=lo + half, ask_close=c + half,
            ticks=np.zeros(len(t), dtype=np.int64), spread_mean=spread, spread_max=spread)

    # ── the feed interface ──────────────────────────────────────────────

    def bars(self, symbol, as_of, count):
        return self.bars_tf(symbol, "H1", as_of, count)

    def bars_tf(self, symbol, timeframe, as_of, count):
        if timeframe == "H4":
            h1 = self.bars_tf(symbol, "H1", as_of, 10**6)
            if h1 is None or len(h1) == 0:
                return None
            out = resample(h1, "H4", as_of=as_of)
        else:
            if timeframe not in INTERVALS:
                return None
            key = (symbol, timeframe, int(as_of) // CACHE_S[timeframe])
            with self._lock:
                hit = key in self._bars
            if not hit:
                try:
                    got = self._series(symbol, timeframe, int(as_of))
                    if got is None:
                        self.errors[(symbol, timeframe)] = f"{timeframe} bars: Yahoo returned no completed bars"
                    else:
                        self.errors.pop((symbol, timeframe), None)
                        self.last_ok = int(self.clock())
                        if timeframe == "H1":
                            self.last_bars_ok = self.last_ok
                except Exception as exc:  # a read: report it, cache the miss for its window
                    got = None
                    self.errors[(symbol, timeframe)] = f"{timeframe} bars: {type(exc).__name__}: {exc}"[:240]
                    self.last_error = self.errors[(symbol, timeframe)]
                    log_event("DATA", f"Yahoo {symbol} {timeframe}: {exc}", severity="warning", symbol=symbol)
                with self._lock:
                    self._bars[key] = got
                    if len(self._bars) > 400:
                        self._bars.pop(next(iter(self._bars)))
            with self._lock:
                out = self._bars[key]
        if out is None or len(out) <= count:
            return out
        return out.take(slice(len(out) - count, len(out)))

    def quote(self, symbol, now=None):
        t = self.clock()
        with self._lock:
            hit = self._quotes.get(symbol)
        if hit is not None and t - hit[0] < QUOTE_TTL_S:
            return hit[1]
        q = None
        try:
            meta = self._chart(symbol, "M1").get("meta") or {}
            px, at = meta.get("regularMarketPrice"), meta.get("regularMarketTime")
            if isinstance(px, (int, float)) and px > 0 and isinstance(at, (int, float)):
                half = self.spreads.get(symbol, 2.0 * pip(symbol)) / 2  # a conversion pair off the list
                q = Quote(symbol, float(px) - half, float(px) + half, int(at))  # Yahoo's time, not ours
                self.last_ok = int(t)
            else:
                self.last_error = f"{symbol}: Yahoo gave no price"
        except Exception as exc:
            self.last_error = f"{symbol} price: {type(exc).__name__}: {exc}"[:240]
        with self._lock:
            self._quotes[symbol] = (t, q)
        return q

    def data_error(self, symbol: str) -> str | None:
        return self.errors.get((symbol, "H1")) or self.last_error
