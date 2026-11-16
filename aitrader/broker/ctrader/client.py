"""Requests and answers over the Open API connection: each request carries its own clientMsgId and is matched to the
answer that carries it back; everything else that arrives (prices, executions) is kept as an event, never dropped.

Only reads are made here. A write (an order, a stop move, a close) is never retried: if its answer does not come, its
outcome is unknown and the only recovery is to ask the broker what exists (CLAUDE.md rule 3).
"""

from __future__ import annotations

import time

from ..base import BrokerError
from . import proto as P

#: what an error code means for the operator (ProtoOAErrorCode, official names)
HINTS = {
    "CH_CLIENT_AUTH_FAILURE": "the Open API application is not activated yet, or CTRADER_CLIENT_ID / "
                              "CTRADER_CLIENT_SECRET are wrong",
    "CH_OA_CLIENT_NOT_FOUND": "no Open API application has this CTRADER_CLIENT_ID",
    "CH_ACCESS_TOKEN_INVALID": "the access token was refused: make a new one for the application and replace "
                               "CTRADER_ACCESS_TOKEN",
    "OA_AUTH_TOKEN_EXPIRED": "the access token has expired: make a new one and replace CTRADER_ACCESS_TOKEN",
    "CH_CTID_TRADER_ACCOUNT_NOT_FOUND": "the token does not grant this trading account",
    "ACCOUNT_NOT_AUTHORIZED": "the account was not authorised on this connection",
    "SERVER_IS_UNDER_MAINTENANCE": "cTrader's server is under maintenance",
    "REQUEST_FREQUENCY_EXCEEDED": "too many requests: cTrader's rate limit",
    "CONNECTIONS_LIMIT_EXCEEDED": "the application has too many open connections",
    "CH_SERVER_NOT_REACHABLE": "the broker's trading service is not available",
}
DISCONNECTS = ("ProtoOAClientDisconnectEvent", "ProtoOAAccountsTokenInvalidatedEvent", "ProtoOAAccountDisconnectEvent")
ERRORS = ("ProtoOAErrorRes", "ProtoErrorRes")


class ApiError(BrokerError):
    """The server answered a request with an error. For a read, nothing changed."""

    def __init__(self, request: str, code: str | None, description: str | None):
        self.request, self.code, self.description = request, code, description
        hint = HINTS.get(code or "")
        super().__init__(f"{request}: {code or 'error without a code'}"
                         + (f" ({description})" if description else "") + (f": {hint}" if hint else ""))


class ConnectionLost(BrokerError):
    """The server ended the session or invalidated the token."""


class CallTimeout(BrokerError):
    """No answer to a request in time."""


class ProtocolError(BrokerError):
    """An answer that does not fit the request."""


class Client:
    def __init__(self, transport, clock=time.monotonic, heartbeat_every: float = 10.0):
        self.transport, self._clock, self.heartbeat_every = transport, clock, heartbeat_every
        self.events: list[tuple[str, dict | None, str | None]] = []
        self._n = 0
        self._last_send = clock()

    def _send(self, name: str, fields: dict, cid: str | None = None) -> None:
        self.transport.send(P.envelope(name, fields, cid))
        self._last_send = self._clock()

    def heartbeat_if_due(self) -> None:
        """The proxy closes a connection idle for 30 seconds; a heartbeat every 10 keeps it."""
        if self._clock() - self._last_send >= self.heartbeat_every:
            self._send("ProtoHeartbeatEvent", {})

    def _read(self, timeout: float) -> tuple[str | None, dict | None, str | None] | None:
        raw = self.transport.recv(timeout)
        self.heartbeat_if_due()
        if raw is None:
            return None
        pt, payload, cid = P.open_envelope(raw)
        name = P.NAME_OF.get(pt)
        if name == "ProtoHeartbeatEvent":
            return None
        msg = P.decode(name, payload) if name else None
        if name in DISCONNECTS:
            reason = (msg or {}).get("reason") or ""
            self.transport.close()
            raise ConnectionLost(f"{name}" + (f": {reason}" if reason else ""))
        return name or f"payloadType {pt}", msg, cid

    def call(self, name: str, fields: dict, expect: tuple[str, ...], timeout: float = 20.0) -> tuple[str, dict]:
        """Send one READ request and return the answer that carries its clientMsgId: (message name, fields)."""
        self._n += 1
        cid = f"c{self._n}"
        self._send(name, fields, cid)
        deadline = self._clock() + timeout
        while True:
            left = deadline - self._clock()
            if left <= 0:
                raise CallTimeout(f"{name}: no answer within {timeout:.0f} s")
            got = self._read(min(left, self.heartbeat_every))
            if got is None:
                continue
            rname, msg, rcid = got
            if rcid != cid:
                self.events.append(got)
                continue
            if rname in expect:
                return rname, msg or {}
            if rname in ERRORS:
                raise ApiError(name, (msg or {}).get("errorCode"), (msg or {}).get("description"))
            raise ProtocolError(f"{name}: answered with {rname}, expected {', '.join(expect)}")

    def pump(self, seconds: float) -> None:
        """Read whatever arrives for `seconds` (prices, executions) into the events, keeping the connection alive."""
        deadline = self._clock() + seconds
        while True:
            left = deadline - self._clock()
            if left <= 0:
                return
            got = self._read(min(left, self.heartbeat_every))
            if got is not None:
                self.events.append(got)

    def drain(self, name: str) -> list[dict]:
        """Remove and return the events of one kind, in arrival order."""
        keep, out = [], []
        for e in self.events:
            (out if e[0] == name else keep).append(e)
        self.events = keep
        return [m or {} for _, m, _ in out]
