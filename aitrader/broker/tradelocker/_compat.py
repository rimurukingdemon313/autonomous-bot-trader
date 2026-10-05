"""Compatibility layer for the TradeLocker client transferred from the archive.

The client (`client.py`, `http.py`, `history.py`, `symbols.py`, `models.py`,
`demo_guard.py`) ran against real TradeLocker demo accounts in the archive
project and is transferred with only its imports rewritten to this module.
Its errors ARE this system's broker errors, so the execution engine handles
them without translation: a write whose outcome is unknown raises
`AmbiguousExecution` here and is never resent there.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from datetime import datetime, timezone

from ...observability import log_event  # noqa: F401  (re-exported)
from ..base import AmbiguousExecution, BrokerError, BrokerRejected  # noqa: F401

#: DEMO ONLY until LIVE is explicitly approved (RISK_CONTRACT.md §5). There is
#: deliberately no environment override for this constant.
REQUIRE_DEMO = True

DEMO_URL_MARKERS = ("demo.tradelocker.com", "demo-api", "/demo")
LIVE_URL_MARKERS = ("live.tradelocker.com", "live-api", "prod.tradelocker.com")


class BotError(RuntimeError):
    pass


class ConfigError(BotError):
    pass


class DemoVerificationError(BotError):
    def __init__(self, message: str, detail: dict | None = None) -> None:
        super().__init__(message)
        self.detail = detail or {}


class BrokerAuthError(BrokerError):
    pass


class BrokerRateLimited(BrokerError):
    pass


class CircuitOpen(BrokerError):
    pass


class SymbolUnavailable(BrokerError):
    """The account does not carry the symbol. Carries the symbol and the nearest names the account does
    carry. (Before the takeover audit this class took no keyword arguments, so raising it with them was a
    TypeError: callers that catch BrokerError never saw it, and the diagnosis was lost.)"""

    def __init__(self, message: str, *, symbol: str | None = None, suggestions: tuple = ()) -> None:
        super().__init__(message)
        self.symbol = symbol
        self.suggestions = tuple(suggestions)


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def from_epoch(value: float) -> datetime:
    """Accept epoch seconds or milliseconds (brokers mix both)."""
    seconds = value / 1000.0 if abs(value) > 10**11 else value
    return datetime.fromtimestamp(seconds, tz=timezone.utc)


@dataclass(frozen=True)
class BrokerConfig:
    email: str | None = field(default=None, repr=False)
    password: str | None = field(default=None, repr=False)
    server: str | None = None
    account_id: str | None = None
    base_url: str = "https://demo.tradelocker.com/backend-api"
    request_timeout: float = 20.0
    max_attempts: int = 4
    circuit_failure_threshold: int = 5
    circuit_reset_seconds: float = 60.0
    min_request_interval: float = 0.6  # Cloudflare answered 1015 at 0.15s in the archive

    @property
    def is_demo_url(self) -> bool:
        url = self.base_url.lower()
        if any(m in url for m in LIVE_URL_MARKERS):
            return False
        return any(m in url for m in DEMO_URL_MARKERS)

    @property
    def is_live_url(self) -> bool:
        return any(m in self.base_url.lower() for m in LIVE_URL_MARKERS)

    @property
    def configured(self) -> bool:
        return all([self.email, self.password, self.server, self.account_id])

    def public(self) -> dict:
        return {"server": self.server, "account_id_set": bool(self.account_id), "base_url": self.base_url,
                "credentials_set": bool(self.email and self.password), "demo_url": self.is_demo_url}


@dataclass(frozen=True)
class TradingConfig:
    """The part of the archive's config the client reads."""

    broker: BrokerConfig
    require_demo: bool = REQUIRE_DEMO

    @classmethod
    def from_env(cls, env: dict | None = None) -> "TradingConfig":
        e = os.environ if env is None else env
        return cls(BrokerConfig(
            email=e.get("TRADELOCKER_EMAIL") or None,
            password=e.get("TRADELOCKER_PASSWORD") or None,
            server=e.get("TRADELOCKER_SERVER") or None,
            account_id=e.get("TRADELOCKER_ACCOUNT_ID") or None,
            base_url=(e.get("TRADELOCKER_BASE_URL") or "https://demo.tradelocker.com/backend-api").rstrip("/"),
            min_request_interval=float(e.get("BROKER_MIN_REQUEST_INTERVAL", "0.6")),
        ))
