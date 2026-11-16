"""The connection to cTrader's Open API proxy: TLS to the DEMO host only, one length-prefixed frame at a time.

The host is a module constant, never configuration: no variable, default, retry or error path can point this at the
live proxy (CLAUDE.md rule 1). The live host is named here only so that it can be refused by name.
"""

from __future__ import annotations

import socket
import ssl
import struct
import time

from ..base import BrokerError
from . import proto as P

DEMO_HOST = "demo.ctraderapi.com"
LIVE_HOST = "live.ctraderapi.com"  # never connected to
PORT = 5035  # Protobuf over TLS (spotware/OpenApiPy: EndPoints.PROTOBUF_PORT)


class DemoRefused(BrokerError):
    """The demo check failed: nothing may trade, and the reason names the fields it looked at."""


class TransportError(BrokerError):
    """The connection failed or closed. Nothing sent after this is known to have arrived."""


def _tls(host: str, port: int, timeout: float):
    ctx = ssl.create_default_context()  # the system's CA store; certificate and host name are verified
    raw = socket.create_connection((host, port), timeout=timeout)
    try:
        return ctx.wrap_socket(raw, server_hostname=host)
    except Exception:
        raw.close()
        raise


class Transport:
    """Frames over one socket. `connect(host, port, timeout)` returns the socket; tests pass one joined to a fake
    server, and nothing else changes."""

    def __init__(self, host: str = DEMO_HOST, port: int = PORT, timeout: float = 20.0, connect=None,
                 clock=time.monotonic):
        if host != DEMO_HOST:
            raise DemoRefused(f"the cTrader host must be {DEMO_HOST}; {host!r} is refused (CLAUDE.md rule 1)")
        self.host, self.port, self._clock = host, port, clock
        try:
            self._sock = (connect or _tls)(host, port, timeout)
        except OSError as e:
            raise TransportError(f"could not connect to {host}:{port}: {type(e).__name__}: {e}") from e
        self._buf = b""
        self.closed = False

    def send(self, data: bytes) -> None:
        if self.closed:
            raise TransportError("the connection is closed")
        try:
            self._sock.sendall(P.frame(data))
        except OSError as e:  # socket.timeout included: how much arrived is unknown
            self.close()
            raise TransportError(f"send failed: {type(e).__name__}: {e}") from e

    def _take(self) -> bytes | None:
        if len(self._buf) < 4:
            return None
        n = struct.unpack(">I", self._buf[:4])[0]
        if n > P.MAX_FRAME:
            self.close()
            raise TransportError(f"the server announced a frame of {n} bytes (limit {P.MAX_FRAME})")
        if len(self._buf) < 4 + n:
            return None
        f, self._buf = self._buf[4:4 + n], self._buf[4 + n:]
        return f

    def recv(self, timeout: float) -> bytes | None:
        """The next whole frame, or None if none completed within `timeout`. A frame cut by the timeout stays
        buffered and is completed by the next call: the stream never loses its place."""
        deadline = self._clock() + max(0.0, timeout)
        while True:
            f = self._take()
            if f is not None:
                return f
            if self.closed:
                raise TransportError("the connection is closed")
            left = deadline - self._clock()
            if left <= 0:
                return None
            try:
                self._sock.settimeout(left)
                chunk = self._sock.recv(65536)
            except (socket.timeout, TimeoutError):
                return None
            except OSError as e:
                self.close()
                raise TransportError(f"receive failed: {type(e).__name__}: {e}") from e
            if not chunk:
                self.close()
                raise TransportError("the server closed the connection")
            self._buf += chunk

    def close(self) -> None:
        if not self.closed:
            self.closed = True
            try:
                self._sock.close()
            except OSError:
                pass
