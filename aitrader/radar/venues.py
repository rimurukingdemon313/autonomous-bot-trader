"""Live funding snapshots from perpetual-futures venues reachable from a GitHub runner (public endpoints, no keys).

Each fetcher returns `Quote`s: the venue's CURRENT funding rate normalised to a per-hour rate, the mark price and
24-hour traded notional in USD. Coins are normalised to their base asset; contracts quoted per 1000 (1000PEPE,
kPEPE) keep a `scale` so prices can be compared. A venue that fails returns nothing and records why: a missing
venue is never filled with zeros (CLAUDE.md rule 6).

Binance and Bybit refuse US-hosted runners (HTTP 451 / 403, research/results/radar-probe.json), so they are not used.
"""

from __future__ import annotations

import json
import urllib.request
from dataclasses import dataclass
from typing import Callable

VENUES_VERSION = "radar-venues-1.0.0"
UA = {"User-Agent": "Mozilla/5.0 (aitrader funding radar)", "Content-Type": "application/json"}

#: Taker fee per fill, bp (public base-tier schedules; declared, stressed in the report).
TAKER_BP = {"hyperliquid": 4.5, "gate": 5.0, "mexc": 2.0, "dydx": 5.0}


@dataclass(frozen=True)
class Quote:
    venue: str
    coin: str  # base asset, upper case, without 1000/k prefixes
    scale: float  # contract units per price unit: 1000 for 1000PEPE / kPEPE, else 1
    rate_per_hour: float  # funding paid by longs to shorts per hour, as a fraction of notional
    mark: float  # mark price of the contract as quoted (scale included)
    vol24_usd: float


Fetch = Callable[[str, dict | None], object]


def http(url: str, body: dict | None = None) -> object:
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, method="POST" if body is not None else "GET", headers=UA)
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read())


def _base(sym: str) -> tuple[str, float]:
    s = sym.upper()
    for p, k in (("1000000", 1e6), ("1000", 1e3), ("1M", 1e6)):
        if s.startswith(p) and len(s) > len(p):
            return s[len(p):], k
    return s, 1.0


def hyperliquid(get: Fetch = http) -> list[Quote]:
    meta, ctxs = get("https://api.hyperliquid.xyz/info", {"type": "metaAndAssetCtxs"})
    out = []
    for u, c in zip(meta["universe"], ctxs):
        if u.get("isDelisted"):
            continue
        name = u["name"]
        coin, scale = (name[1:].upper(), 1e3) if name.startswith("k") and name[1:].isupper() else _base(name)
        try:
            out.append(Quote("hyperliquid", coin, scale, float(c["funding"]), float(c["markPx"]),
                             float(c.get("dayNtlVlm") or 0.0)))
        except (KeyError, TypeError, ValueError):
            continue
    return out


def gate(get: Fetch = http) -> list[Quote]:
    contracts = {c["name"]: c for c in get("https://api.gateio.ws/api/v4/futures/usdt/contracts", None)}
    out = []
    for t in get("https://api.gateio.ws/api/v4/futures/usdt/tickers", None):
        c = contracts.get(t.get("contract"))
        if not c or c.get("in_delisting"):
            continue
        coin, scale = _base(t["contract"].replace("_USDT", ""))
        try:
            interval_h = float(c["funding_interval"]) / 3600
            out.append(Quote("gate", coin, scale, float(t["funding_rate"]) / interval_h, float(t["mark_price"]),
                             float(t.get("volume_24h_quote") or 0.0)))
        except (KeyError, TypeError, ValueError, ZeroDivisionError):
            continue
    return out


def mexc(get: Fetch = http) -> list[Quote]:
    rates = {r["symbol"]: r for r in get("https://contract.mexc.com/api/v1/contract/funding_rate", None)["data"]}
    out = []
    for t in get("https://contract.mexc.com/api/v1/contract/ticker", None)["data"]:
        sym = t.get("symbol", "")
        r = rates.get(sym)
        if not sym.endswith("_USDT") or r is None:
            continue
        coin, scale = _base(sym.replace("_USDT", ""))
        try:
            cycle = float(r["collectCycle"])
            out.append(Quote("mexc", coin, scale, float(r["fundingRate"]) / cycle, float(t["fairPrice"]),
                             float(t.get("amount24") or 0.0)))
        except (KeyError, TypeError, ValueError, ZeroDivisionError):
            continue
    return out


def dydx(get: Fetch = http) -> list[Quote]:
    out = []
    for name, m in get("https://indexer.dydx.trade/v4/perpetualMarkets", None)["markets"].items():
        if m.get("status") != "ACTIVE" or not name.endswith("-USD"):
            continue
        coin, scale = _base(name[:-4])
        try:
            out.append(Quote("dydx", coin, scale, float(m["nextFundingRate"]), float(m["oraclePrice"]),
                             float(m.get("volume24H") or 0.0)))
        except (KeyError, TypeError, ValueError):
            continue
    return out


FETCHERS = {"hyperliquid": hyperliquid, "gate": gate, "mexc": mexc, "dydx": dydx}


def snapshot(get: Fetch = http) -> tuple[list[Quote], dict[str, str]]:
    """Every venue's quotes, and the error for each venue that failed (never silently empty)."""
    quotes, errors = [], {}
    for name, f in FETCHERS.items():
        try:
            quotes += f(get)
        except Exception as exc:  # noqa: BLE001 - recorded per venue, reported, never zero-filled
            errors[name] = f"{type(exc).__name__}: {str(exc)[:160]}"
    return quotes, errors


__all__ = ["FETCHERS", "TAKER_BP", "VENUES_VERSION", "Quote", "dydx", "gate", "hyperliquid", "mexc", "snapshot"]
