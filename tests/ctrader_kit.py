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


class FakeTradingCTrader(FakeCTrader):
    """The fake proxy with an account that trades: positions, a balance, deals, prices, and the execution events a
    write produces. Each write can be told to answer, stay silent, apply silently (the answer is lost), or refuse."""

    def __init__(self, prices=None, order_mode="fill", amend_mode="apply", close_mode="fill", commission=-3.0,
                 clock=time.time, **kw):
        self.prices = dict(prices or {101: (5000.0, 5000.5)})
        self.order_mode, self.amend_mode, self.close_mode = order_mode, amend_mode, close_mode
        self.commission = commission  # account currency per close, as the broker reports it (signed)
        self.balance = 200_000.0
        self.positions: dict[int, dict] = {}
        self.deals: list[dict] = []
        self._ids = 7000
        self.clock = clock  # the broker's clock: its prices and deals are stamped with it
        super().__init__(**kw)

    def _id(self) -> int:
        self._ids += 1
        return self._ids

    def set_price(self, sid: int, bid: float, ask: float) -> None:
        self.prices[sid] = (bid, ask)
        self.send("ProtoOASpotEvent", spot(sid, bid, ask) | {"timestamp": int(self.clock() * 1000)})

    def _trader_now(self) -> dict:
        return {**self.trader, "balance": int(round(self.balance * 100))}

    def _handle(self, name: str, f: dict, cid: str | None) -> None:
        acct = {"ctidTraderAccountId": CTID}
        if name == "ProtoOATraderReq" and name not in self.errors and name not in self.silent:
            self.requests.append((name, f, cid))
            self.send("ProtoOATraderRes", {**acct, "trader": self._trader_now()}, cid)
        elif name == "ProtoOASubscribeSpotsReq":
            self.requests.append((name, f, cid))
            self.send("ProtoOASubscribeSpotsRes", {**acct, "subscribedSymbolId": f.get("symbolId", [])}, cid)
            for sid in f.get("symbolId", []):
                if sid in self.prices:
                    b, a = self.prices[sid]
                    self.send("ProtoOASpotEvent", spot(sid, b, a) | {"timestamp": int(self.clock() * 1000)})
        elif name == "ProtoOAReconcileReq":
            self.requests.append((name, f, cid))
            self.send("ProtoOAReconcileRes", {**acct, "position": list(self.positions.values())}, cid)
        elif name == "ProtoOAGetPositionUnrealizedPnLReq":
            self.requests.append((name, f, cid))
            rows = []
            for p in self.positions.values():
                td = p["tradeData"]
                bid, ask = self.prices[td["symbolId"]]
                side = 1 if td["tradeSide"] == 1 else -1
                exit_px = bid if side > 0 else ask
                gross = (exit_px - p["price"]) * side * td["volume"] / 100
                rows.append({"positionId": p["positionId"], "grossUnrealizedPnL": int(round(gross * 100)),
                             "netUnrealizedPnL": int(round(gross * 100))})
            self.send("ProtoOAGetPositionUnrealizedPnLRes", {**acct, "positionUnrealizedPnL": rows,
                                                             "moneyDigits": 2}, cid)
        elif name == "ProtoOADealListReq":
            self.requests.append((name, f, cid))
            self.send("ProtoOADealListRes", {**acct, "deal": self.deals, "hasMore": False}, cid)
        elif name == "ProtoOANewOrderReq" and name not in self.errors:
            self.requests.append((name, f, cid))
            self._order(f, cid)
        elif name == "ProtoOAAmendPositionSLTPReq" and name not in self.errors:
            self.requests.append((name, f, cid))
            self._amend(f, cid)
        elif name == "ProtoOAClosePositionReq" and name not in self.errors:
            self.requests.append((name, f, cid))
            self._close(f, cid)
        else:
            super()._handle(name, f, cid)

    def _order(self, f: dict, cid: str | None) -> None:
        mode = self.order_mode
        if mode == "silent":
            return
        order_id = self._id()
        order = {"orderId": order_id, "tradeData": {"symbolId": f["symbolId"], "volume": f["volume"],
                                                    "tradeSide": f["tradeSide"], "label": f.get("label")},
                 "orderType": 1, "orderStatus": 1, "clientOrderId": f.get("clientOrderId")}
        if mode == "reject":
            self.send("ProtoOAExecutionEvent", {"ctidTraderAccountId": CTID, "executionType": 7,
                                                "order": order, "errorCode": "NOT_ENOUGH_MONEY"}, cid)
            return
        if mode == "order_error":
            self.send("ProtoOAOrderErrorEvent", {"ctidTraderAccountId": CTID, "errorCode": "MARKET_CLOSED"}, cid)
            return
        bid, ask = self.prices[f["symbolId"]]
        side = 1 if f["tradeSide"] == 1 else -1
        px = ask if side > 0 else bid
        pid = self._id()
        stop = px - side * f["relativeStopLoss"] / 1e5 if "relativeStopLoss" in f else None
        now_ms = int(self.clock() * 1000)
        pos = {"positionId": pid, "tradeData": {"symbolId": f["symbolId"], "volume": f["volume"],
                                                "tradeSide": f["tradeSide"], "openTimestamp": now_ms,
                                                "label": f.get("label")},
               "positionStatus": 1, "swap": 0, "price": px, "moneyDigits": 2}
        if stop is not None:
            pos["stopLoss"] = round(stop, 5)
        self.positions[pid] = pos
        if mode == "silent_fill":
            return  # filled, but the answer never comes
        deal = {"dealId": self._id(), "orderId": order_id, "positionId": pid, "volume": f["volume"],
                "filledVolume": f["volume"], "symbolId": f["symbolId"], "createTimestamp": now_ms,
                "executionTimestamp": now_ms, "executionPrice": px, "tradeSide": f["tradeSide"], "dealStatus": 2}
        self.send("ProtoOAExecutionEvent", {"ctidTraderAccountId": CTID, "executionType": 2, "order": order}, cid)
        self.send("ProtoOAExecutionEvent", {"ctidTraderAccountId": CTID, "executionType": 3, "order": order,
                                            "position": pos, "deal": deal}, cid)

    def _amend(self, f: dict, cid: str | None) -> None:
        p = self.positions.get(f["positionId"])
        if self.amend_mode == "silent" or p is None:
            return
        if self.amend_mode == "reject":
            self.send("ProtoOAErrorRes", {"errorCode": "TRADING_BAD_STOPS", "description": "bad stop"}, cid)
            return
        p["stopLoss"] = f["stopLoss"]
        if self.amend_mode == "silent_apply":
            return
        self.send("ProtoOAExecutionEvent", {"ctidTraderAccountId": CTID, "executionType": 4, "position": p}, cid)

    def _close(self, f: dict, cid: str | None) -> None:
        p = self.positions.get(f["positionId"])
        if self.close_mode == "silent" or p is None:
            return
        td = p["tradeData"]
        bid, ask = self.prices[td["symbolId"]]
        side = 1 if td["tradeSide"] == 1 else -1
        px = bid if side > 0 else ask
        gross = (px - p["price"]) * side * td["volume"] / 100
        self.balance += gross + self.commission
        del self.positions[f["positionId"]]
        now_ms = int(self.clock() * 1000)
        deal = {"dealId": self._id(), "orderId": self._id(), "positionId": p["positionId"], "volume": td["volume"],
                "filledVolume": td["volume"], "symbolId": td["symbolId"], "createTimestamp": now_ms,
                "executionTimestamp": now_ms, "executionPrice": px, "tradeSide": 2 if side > 0 else 1,
                "dealStatus": 2, "label": td.get("label"),
                "closePositionDetail": {"entryPrice": p["price"], "grossProfit": int(round(gross * 100)), "swap": 0,
                                        "commission": int(round(self.commission * 100)),
                                        "balance": int(round(self.balance * 100)), "moneyDigits": 2,
                                        "closedVolume": td["volume"]}}
        self.deals.append(deal)
        if self.close_mode == "silent_fill":
            return
        order = {"orderId": deal["orderId"], "tradeData": td, "orderType": 1, "orderStatus": 2, "closingOrder": True,
                 "positionId": p["positionId"]}
        self.send("ProtoOAExecutionEvent", {"ctidTraderAccountId": CTID, "executionType": 3, "order": order,
                                            "position": {**p, "positionStatus": 2}, "deal": deal}, cid)

    def stop_out(self, pid: int, px: float) -> None:
        """The broker's own stop closes a position while nobody is connected: only a deal remains."""
        p = self.positions.pop(pid)
        td = p["tradeData"]
        side = 1 if td["tradeSide"] == 1 else -1
        gross = (px - p["price"]) * side * td["volume"] / 100
        self.balance += gross + self.commission
        now_ms = int(self.clock() * 1000)
        self.deals.append({"dealId": self._id(), "orderId": self._id(), "positionId": pid, "volume": td["volume"],
                           "filledVolume": td["volume"], "symbolId": td["symbolId"], "createTimestamp": now_ms,
                           "executionTimestamp": now_ms, "executionPrice": px, "tradeSide": 2 if side > 0 else 1,
                           "dealStatus": 2, "label": td.get("label"),
                           "closePositionDetail": {"entryPrice": p["price"], "grossProfit": int(round(gross * 100)),
                                                   "swap": 0, "commission": int(round(self.commission * 100)),
                                                   "balance": int(round(self.balance * 100)), "moneyDigits": 2,
                                                   "closedVolume": td["volume"]}})
