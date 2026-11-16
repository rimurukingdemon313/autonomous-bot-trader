"""cTrader's Open API proxy, faked at the socket (tests only).

It speaks the wire format (length-prefixed frames, ProtoMessage envelopes, the official field numbers), answers each
request from a script of accounts, symbols and prices, and records every request it receives, so a test can say what
was NOT asked (no order, nothing after a refused demo check). It replaces the network, never the code under test.
"""

from __future__ import annotations

import socket
import struct
import threading
import time

from aitrader.broker.ctrader import proto as P

WRITES = ("ProtoOANewOrderReq", "ProtoOAAmendPositionSLTPReq", "ProtoOAClosePositionReq")
LOGIN, CTID = 98765432, 5550001  # distinctive, so a test can show they never reach a report


def px(x: float) -> int:
    return int(round(x * 1e5))


def spot(sid: int, bid: float | None = None, ask: float | None = None) -> dict:
    e = {"ctidTraderAccountId": CTID, "symbolId": sid}
    if bid is not None:
        e["bid"] = px(bid)
    if ask is not None:
        e["ask"] = px(ask)
    return e


def demo_account(**over) -> dict:
    return {"ctidTraderAccountId": CTID, "isLive": False, "traderLogin": LOGIN, "brokerTitleShort": "FakeBroker",
            **over}


def trader(**over) -> dict:
    return {"ctidTraderAccountId": CTID, "balance": 20_000_000, "moneyDigits": 2, "depositAssetId": 1,
            "swapFree": True, "traderLogin": LOGIN, "brokerName": "Fake Prop Firm", "accountType": 0,
            "accessRights": 0, "leverageInCents": 3000, **over}


SYMBOLS = [{"symbolId": 101, "symbolName": "US500.cash", "enabled": True},
           {"symbolId": 102, "symbolName": "US100.cash", "enabled": True},
           {"symbolId": 103, "symbolName": "GER40.cash", "enabled": True},
           {"symbolId": 104, "symbolName": "EURUSD", "enabled": True},
           {"symbolId": 105, "symbolName": "US500.f", "enabled": True}]
DETAILS = {101: {"symbolId": 101, "digits": 2, "pipPosition": 0, "minVolume": 100, "stepVolume": 100,
                 "lotSize": 100, "swapLong": -5.1, "swapShort": 1.2, "swapCalculationType": 1, "tradingMode": 0,
                 "schedule": [{"startSecond": 0, "endSecond": 3600 * 23}]},
           102: {"symbolId": 102, "digits": 2, "pipPosition": 0, "minVolume": 100},
           103: {"symbolId": 103, "digits": 1, "pipPosition": 0, "minVolume": 100}}


class FakeCTrader:
    def __init__(self, accounts=None, trader_rec=None, symbols=None, details=None, spots_before=(), spots=(),
                 errors=None, silent=(), disconnect_on=None, chunk: int | None = None, scope: int = 1,
                 answer_with=None):
        self.accounts = [demo_account()] if accounts is None else accounts
        self.trader = trader() if trader_rec is None else trader_rec
        self.symbols = SYMBOLS if symbols is None else symbols
        self.details = DETAILS if details is None else details
        self.spots_before, self.spots = list(spots_before), list(spots)
        self.errors = errors or {}
        self.silent = set(silent)
        self.disconnect_on = disconnect_on
        self.answer_with = answer_with or {}
        self.chunk, self.scope = chunk, scope
        self.requests: list[tuple[str, dict, str | None]] = []
        self.heartbeats = 0
        self.connected_to: tuple[str, int] | None = None
        self.a, self.b = socket.socketpair()
        self._t = threading.Thread(target=self._serve, daemon=True)
        self._t.start()

    # the transport's connect(host, port, timeout)
    def connect(self, host: str, port: int, timeout: float):
        self.connected_to = (host, port)
        return self.a

    def names(self) -> list[str]:
        return [n for n, _, _ in self.requests if n != "ProtoHeartbeatEvent"]

    def send(self, name: str, fields: dict, cid: str | None = None) -> None:
        data = P.frame(P.envelope(name, fields, cid))
        if self.chunk:
            for i in range(0, len(data), self.chunk):
                self.b.sendall(data[i:i + self.chunk])
                time.sleep(0.0005)
        else:
            self.b.sendall(data)

    def _serve(self) -> None:
        buf = b""
        try:
            while True:
                data = self.b.recv(65536)
                if not data:
                    return
                buf += data
                while len(buf) >= 4:
                    n = struct.unpack(">I", buf[:4])[0]
                    if len(buf) < 4 + n:
                        break
                    raw, buf = buf[4:4 + n], buf[4 + n:]
                    pt, payload, cid = P.open_envelope(raw)
                    name = P.NAME_OF[pt]
                    self._handle(name, P.decode(name, payload), cid)
        except OSError:
            return

    def _handle(self, name: str, f: dict, cid: str | None) -> None:
        self.requests.append((name, f, cid))
        if name == "ProtoHeartbeatEvent":
            self.heartbeats += 1
            return
        if name in self.silent:
            return
        if name == self.disconnect_on:
            self.send("ProtoOAClientDisconnectEvent", {"reason": "blocked by the administrator"})
            return
        if name in self.errors:
            code, desc = self.errors[name]
            self.send("ProtoOAErrorRes", {"errorCode": code, "description": desc}, cid)
            return
        if name in self.answer_with:
            self.send(self.answer_with[name][0], self.answer_with[name][1], cid)
            return
        acct = {"ctidTraderAccountId": f.get("ctidTraderAccountId", CTID)}
        if name == "ProtoOAApplicationAuthReq":
            self.send("ProtoOAApplicationAuthRes", {}, cid)
        elif name == "ProtoOAGetAccountListByAccessTokenReq":
            self.send("ProtoOAGetAccountListByAccessTokenRes", {"accessToken": f["accessToken"],
                                                                "permissionScope": self.scope,
                                                                "ctidTraderAccount": self.accounts}, cid)
        elif name == "ProtoOAAccountAuthReq":
            self.send("ProtoOAAccountAuthRes", acct, cid)
        elif name == "ProtoOATraderReq":
            self.send("ProtoOATraderRes", {**acct, "trader": self.trader}, cid)
        elif name == "ProtoOAAssetListReq":
            self.send("ProtoOAAssetListRes", {**acct, "asset": [{"assetId": 1, "name": "USD"}]}, cid)
        elif name == "ProtoOASymbolsListReq":
            self.send("ProtoOASymbolsListRes", {**acct, "symbol": self.symbols}, cid)
        elif name == "ProtoOASymbolByIdReq":
            self.send("ProtoOASymbolByIdRes", {**acct, "symbol": [self.details[i] for i in f.get("symbolId", [])
                                                                  if i in self.details]}, cid)
        elif name == "ProtoOASubscribeSpotsReq":
            for e in self.spots_before:  # a price may arrive before the answer: it must not be lost
                self.send("ProtoOASpotEvent", e)
            self.send("ProtoOASubscribeSpotsRes", {**acct, "subscribedSymbolId": f.get("symbolId", [])}, cid)
            for e in self.spots:
                self.send("ProtoHeartbeatEvent", {})
                self.send("ProtoOASpotEvent", e)
        elif name == "ProtoOAUnsubscribeSpotsReq":
            self.send("ProtoOAUnsubscribeSpotsRes", acct, cid)
        elif name == "ProtoOAAccountLogoutReq":
            self.send("ProtoOAAccountLogoutRes", acct, cid)
        else:
            self.send("ProtoErrorRes", {"errorCode": "UNSUPPORTED_MESSAGE"}, cid)

    def close(self) -> None:
        for s in (self.a, self.b):
            try:
                s.close()
            except OSError:
                pass


def env(**over) -> dict:
    base = {"CTRADER_CLIENT_ID": "client-id-0001", "CTRADER_CLIENT_SECRET": "client-secret-0002",
            "CTRADER_ACCESS_TOKEN": "access-token-0003", "CTRADER_ACCOUNT_LOGIN": str(LOGIN)}
    return {k: v for k, v in {**base, **over}.items() if v is not None}
