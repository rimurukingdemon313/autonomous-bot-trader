"""Structured logging with secret redaction at the sink (SECURITY_CONTRACT.md §4).

Every log line is one JSON object on stdout (Railway collects stdout).
Secrets are redacted where lines are WRITTEN, not at each call site: any
value of a secret environment variable, and anything shaped like a bearer
or access token, is replaced before the line leaves the process.
"""

from __future__ import annotations

import json
import os
import re
import sys
import threading
import uuid
from datetime import datetime, timezone
from typing import Any

SECRET_ENV_KEYS = (
    "TRADELOCKER_PASSWORD", "TRADELOCKER_EMAIL", "AI_API_KEY", "DASHBOARD_TOKEN",
    "DATABASE_URL", "TELEGRAM_BOT_TOKEN",
)
PLACEHOLDER = "***redacted***"
_TOKEN_SHAPES = (
    re.compile(r"(Bearer\s+)[A-Za-z0-9\-_\.=]+"),
    re.compile(r'("(?:accessToken|refreshToken|access_token|refresh_token|password|api_key|apiKey)"\s*:\s*)"[^"]*"'),
    re.compile(r"\beyJ[A-Za-z0-9\-_]{10,}\.[A-Za-z0-9\-_]{10,}\.[A-Za-z0-9\-_]{5,}"),  # JWT
    re.compile(r"\bsk-[A-Za-z0-9]{12,}"),
)
_lock = threading.Lock()
_recent: list[dict] = []


_SECRET_NAME = re.compile(r"(_API_KEY|_TOKEN|_PASSWORD|_SECRET)$")


def _secret_values() -> list[str]:
    """Named secrets, and ANY variable shaped like one (AI_OPENROUTER_API_KEY, AI_GEMINI_API_KEY, ...)."""
    vals = []
    for key, v in os.environ.items():
        if key in SECRET_ENV_KEYS or _SECRET_NAME.search(key):
            if len(v) >= 4:
                vals.append(v)
    return sorted(set(vals), key=len, reverse=True)


def redact(text: str) -> str:
    cleaned = str(text)
    for secret in _secret_values():
        cleaned = cleaned.replace(secret, PLACEHOLDER)
    for pat in _TOKEN_SHAPES:
        cleaned = pat.sub(lambda m: (m.group(1) if m.groups() else "") + (f'"{PLACEHOLDER}"' if m.groups() and m.group(1).rstrip().endswith(":") else PLACEHOLDER), cleaned)
    return cleaned


def _coerce(value: Any) -> Any:
    if isinstance(value, str):
        return redact(value)
    if isinstance(value, dict):
        return {k: (PLACEHOLDER if any(s in str(k).lower() for s in ("password", "token", "secret", "api_key", "apikey"))
                    else _coerce(v)) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_coerce(v) for v in value]
    if value is None or isinstance(value, (int, float, bool)):
        return value
    return redact(str(value))


def log_event(stage: str, message: str, *, severity: str = "info", symbol: str | None = None,
              event_id: str | None = None, **fields: Any) -> dict:
    record = {"event_id": event_id or uuid.uuid4().hex[:16],
              "ts": datetime.now(timezone.utc).isoformat(timespec="milliseconds"),
              "stage": stage, "severity": severity, "symbol": symbol, "message": redact(message),
              **_coerce(fields)}
    line = json.dumps(record, separators=(",", ":"), default=str)
    with _lock:
        _recent.append(record)
        del _recent[:-500]
        print(line, file=sys.stdout, flush=True)
    return record


def recent(n: int = 100) -> list[dict]:
    with _lock:
        return list(_recent[-n:])
