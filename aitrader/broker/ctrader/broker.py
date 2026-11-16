"""The system's Broker protocol on a cTrader DEMO account (docs/CTRADER.md).

What it adds to the connection:

- WRITES are sent once and never retried (CLAUDE.md rule 3). An order, a stop move or a close whose answer does not come
  raises AmbiguousExecution; the only recovery is to read the account (positions, deals), which the execution engine
  does by client id.
- Every write needs the hard risk gate's single-use permit for exactly that write, as on the paper broker: a broker
  without a gate refuses everything.
- The demo check is repeated from the broker's own account list before an order is created, and the host and that
  verdict are checked again just before it is sent (rule 1: startup, connection, creation, submission). A failed check
  refuses the write and calls `on_refusal`, which the runner wires to the kill switch.
- An order is refused on an account the broker does not report as swap-free (the owner's condition).
- Nothing is invented: a balance without its digits, a price without both sides, or a missing conversion rate is an
  error or None, never a plausible number.

Volumes are in 0.01 of a unit (cTrader's definition; the official samples send units x 100). One unit of an index
CFD is one unit of the index, as the trend desk sizes it.
"""

from __future__ import annotations

import math
import time
from typing import Callable

from ..base import (AccountSnapshot, AmbiguousExecution, BrokerError, BrokerPosition, BrokerRejected, ClosedTrade,
                    Fill)
from ...risk.engine import InstrumentSpec, Quote
from . import proto as P
from .guard import verify_demo, verify_swap_free
from .session import Credentials, Session
from .transport import DEMO_HOST

CTRADER_BROKER_VERSION = "ctrader-broker-1.0.0"
PRICE = 1e5
FILLED, ACCEPTED, REPLACED, CANCELLED, EXPIRED, REJECTED, PARTIAL = 3, 2, 4, 5, 6, 7, 11


class CTraderBroker:
    name = "ctrader-demo"

    def __init__(self, session: Session, creds: Credentials, symbols: dict[str, int], light: list[dict],
                 details: dict[int, dict], clock: Callable[[], int], *, gate=None,
                 on_refusal: Callable[[str], None] | None = None, write_timeout: float = 30.0,
                 quote_wait: float = 10.0, fresh_s: int = 20, monotonic=time.monotonic) -> None:
        self.s, self.c, self.creds = session, session.client, creds
        self.account_id = session.account_id
        self.ids = dict(symbols)  # desk symbol -> cTrader symbolId
        self.names = {v: k for k, v in self.ids.items()}
        self.light = {x["symbolId"]: x for x in light}
        self.details = details
        self.clock, self._mono = clock, monotonic
        self._gate = gate
        self.on_refusal = on_refusal or (lambda why: None)
        self.write_timeout, self.quote_wait, self.fresh_s = write_timeout, quote_wait, fresh_s
        self._verdict: bool | None = session.demo.ok
        self.refusal: str | None = None
        self._last: dict[int, list] = {}
        self._subscribed: set[int] = set()
        self._assets: dict[int, str] | None = None
        self._n = 0
        #: closes this broker sent itself in this run, with the P/L it measured: preferred to the deal list
        self._own_closes: dict[str, ClosedTrade] = {}

    # ── the gate ──

    def attach_gate(self, gate) -> None:
        if self._gate is not None and self._gate is not gate:
            raise BrokerError("a hard risk gate is already attached; it cannot be replaced")
        self._gate = gate

    # ── checks ──

    def _refuse(self, why: str) -> None:
        self._verdict = False
        self.refusal = why
        self.on_refusal(why)

    def is_demo(self) -> bool | None:
        """Asked of the broker each time: our host constant and its account list's isLive for this account. Could
        not tell -> None, which blocks as a refusal does."""
        try:
            _, listed = self.c.call("ProtoOAGetAccountListByAccessTokenReq", {"accessToken": self.creds.access_token},
                                    ("ProtoOAGetAccountListByAccessTokenRes",))
        except BrokerError:
            return None
        v = verify_demo(self.c.transport.host, listed.get("ctidTraderAccount", []), self.creds.login)
        if not v.ok or v.account_id != self.account_id:
            self._refuse(f"{v.why}. Fields read: {', '.join(v.looked_at)}")
            return False
        self._verdict = True
        return True

    def _trader(self) -> dict:
        _, res = self.c.call("ProtoOATraderReq", {"ctidTraderAccountId": self.account_id}, ("ProtoOATraderRes",))
        t = res.get("trader") or {}
        if t.get("ctidTraderAccountId") != self.account_id:
            raise BrokerError("the broker returned another account's record")
        return t

    def _before_write(self, what: str) -> None:
        """Creation: the demo check from the broker's list again, and swap-free from the account record again."""
        demo = self.is_demo()
        if demo is not True:
            raise BrokerRejected(f"DEMO_CHECK: {what} refused: the account is not verified demo now "
                                 f"({self.refusal or 'the broker could not be asked'})")
        sf = verify_swap_free(self._trader())
        if not sf.ok:
            raise BrokerRejected(f"SWAP_FREE: {what} refused: {sf.why}")

    def _at_submission(self, what: str) -> None:
        """Submission: the connection still goes to the demo proxy and the last verdict is still positive."""
        if self.c.transport.host != DEMO_HOST or self._verdict is not True:
            raise BrokerRejected(f"DEMO_CHECK: {what} refused at submission")

    # ── reads ──

    def _asset_names(self) -> dict[int, str]:
        if self._assets is None:
            _, res = self.c.call("ProtoOAAssetListReq", {"ctidTraderAccountId": self.account_id},
                                 ("ProtoOAAssetListRes",))
            self._assets = {a["assetId"]: a.get("name") for a in res.get("asset", []) if "assetId" in a}
        return self._assets

    def account(self) -> AccountSnapshot:
        t = self._trader()
        if "moneyDigits" not in t or "balance" not in t:
            raise BrokerError("the account record has no balance or no moneyDigits: the balance cannot be read")
        balance = t["balance"] / 10 ** t["moneyDigits"]
        _, u = self.c.call("ProtoOAGetPositionUnrealizedPnLReq", {"ctidTraderAccountId": self.account_id},
                           ("ProtoOAGetPositionUnrealizedPnLRes",))
        rows = u.get("positionUnrealizedPnL", [])
        if rows and "moneyDigits" not in u:
            raise BrokerError("unrealized P/L without moneyDigits: the equity cannot be read")
        upnl = sum(r.get("netUnrealizedPnL", 0) for r in rows) / 10 ** u.get("moneyDigits", 0)
        currency = self._asset_names().get(t.get("depositAssetId"))
        if not currency:
            raise BrokerError("the account's deposit currency is not in the broker's asset list")
        return AccountSnapshot(equity=balance + upnl, balance=balance, currency=currency, time=int(self.clock()))

    def _reconcile(self) -> list[dict]:
        _, res = self.c.call("ProtoOAReconcileReq", {"ctidTraderAccountId": self.account_id}, ("ProtoOAReconcileRes",))
        return res.get("position", [])

    def _position(self, p: dict) -> BrokerPosition:
        td = p.get("tradeData") or {}
        sid = td.get("symbolId")
        return BrokerPosition(id=str(p["positionId"]), symbol=self.names.get(sid, f"#{sid}"),
                              side=1 if td.get("tradeSide") == P.TRADE_SIDE["BUY"] else -1,
                              qty=td.get("volume", 0) / 100, entry=p.get("price"), stop=p.get("stopLoss"),
                              target=p.get("takeProfit"), client_id=td.get("label"),
                              opened=int(td.get("openTimestamp", 0) // 1000))

    def positions(self) -> list[BrokerPosition]:
        return [self._position(p) for p in self._reconcile()]

    def find_by_client_id(self, client_id: str) -> BrokerPosition | None:
        for p in self.positions():
            if p.client_id == client_id:
                return p
        return None

    def _subscribe(self) -> None:
        want = set(self.ids.values()) | set(self._conversion_ids())
        new = sorted(want - self._subscribed)
        if not new:
            return
        self.c.call("ProtoOASubscribeSpotsReq", {"ctidTraderAccountId": self.account_id, "symbolId": new,
                                                 "subscribeToSpotTimestamp": True}, ("ProtoOASubscribeSpotsRes",))
        self._subscribed |= set(new)

    def _absorb(self) -> None:
        for e in self.c.drain("ProtoOASpotEvent"):
            sid = e.get("symbolId")
            last = self._last.setdefault(sid, [None, None, None])
            if "bid" in e:
                last[0] = e["bid"]
            if "ask" in e:
                last[1] = e["ask"]
            last[2] = (e["timestamp"] // 1000) if "timestamp" in e else int(self.clock())

    def _mid_or_quote(self, sid: int) -> tuple[float, float, int] | None:
        """The symbol's last bid and ask with the broker's time of that price. A price older than `fresh_s` waits up
        to `quote_wait` for a newer one; if none comes it is returned with its own old time, so the risk engine and the
        gate see its age and refuse it. No price at all is None."""
        self._subscribe()
        deadline = self._mono() + self.quote_wait
        while True:
            self._absorb()
            bid, ask, t = self._last.get(sid, [None, None, None])
            have = bool(bid and ask and ask >= bid)
            if have and self.clock() - int(t) <= self.fresh_s:
                return bid / PRICE, ask / PRICE, int(t)
            left = deadline - self._mono()
            if left <= 0:
                return (bid / PRICE, ask / PRICE, int(t)) if have else None
            self.c.pump(min(left, 1.0))

    def quote(self, symbol: str, now: int | None = None) -> Quote | None:
        sid = self.ids.get(symbol)
        if sid is None:
            return None
        q = self._mid_or_quote(sid)
        return None if q is None else Quote(symbol, q[0], q[1], q[2])

    def _conversion_ids(self) -> list[int]:
        out = []
        for sym, sid in self.ids.items():
            r = self._conversion(sid)
            if r is not None and r[0] is not None:
                out.append(r[0])
        return out

    def _conversion(self, sid: int) -> tuple[int | None, bool] | None:
        """The symbol that converts this symbol's quote currency into the deposit currency: (its id, inverted?), or
        (None, False) when they are the same currency; None when no direct pair is listed."""
        ls = self.light.get(sid) or {}
        dep = self.s.trader.get("depositAssetId")
        quote = ls.get("quoteAssetId")
        if quote is None or dep is None:
            return None
        if quote == dep:
            return (None, False)
        for x in self.light.values():
            if (x.get("baseAssetId"), x.get("quoteAssetId")) == (quote, dep):
                return (x["symbolId"], False)
            if (x.get("baseAssetId"), x.get("quoteAssetId")) == (dep, quote):
                return (x["symbolId"], True)
        return None

    def spec(self, symbol: str) -> InstrumentSpec | None:
        sid = self.ids.get(symbol)
        d = self.details.get(sid) if sid is not None else None
        if not d or not all(k in d for k in ("minVolume", "stepVolume")):
            return None
        conv = self._conversion(sid)
        if conv is None:
            return None  # no listed pair converts the quote currency: nothing is sized or traded
        if conv[0] is None:
            rate = 1.0
        else:
            q = self._mid_or_quote(conv[0])
            if q is None:
                return None
            mid = (q[0] + q[1]) / 2
            rate = 1 / mid if conv[1] else mid
        mode = d.get("tradingMode", 0)
        return InstrumentSpec(symbol=symbol, contract_size=1.0, min_lot=d["minVolume"] / 100,
                              lot_step=d["stepVolume"] / 100,
                              max_lot=d["maxVolume"] / 100 if d.get("maxVolume") else float("inf"),
                              value_per_price_unit=rate, tradable=mode == 0)

    # ── writes: once, never retried ──

    def _write(self, name: str, fields: dict, mine, terminal) -> tuple[str, dict]:
        return self.c.write(name, fields, mine, terminal, timeout=self.write_timeout)

    def _volume(self, symbol: str, qty: float) -> int:
        d = self.details.get(self.ids[symbol]) or {}
        vol = int(round(qty * 100))
        step, lo = d.get("stepVolume"), d.get("minVolume")
        if not step or not lo:
            raise BrokerRejected(f"{symbol}: no volume step or minimum is known")
        if abs(vol - qty * 100) > 1e-6 or vol % step or vol < lo or (d.get("maxVolume") and vol > d["maxVolume"]):
            raise BrokerRejected(f"{symbol}: {qty} units is not a valid volume (step {step / 100}, min {lo / 100})")
        return vol

    def place_market(self, symbol: str, side: int, qty: float, stop: float, target: float | None,
                     client_id: str, meta: dict | None = None, permit=None) -> Fill:
        if self._gate is None:
            raise BrokerRejected("NO_RISK_GATE: this broker has no hard risk gate attached; it sends nothing")
        problem = self._gate.redeem(permit, symbol=symbol, side=side, qty=qty, stop=stop, target=target,
                                    client_id=client_id)
        if problem:
            raise BrokerRejected(problem)
        if symbol not in self.ids:
            raise BrokerRejected(f"{symbol} is not mapped to a symbol at this broker")
        self._before_write("the order")
        if self.find_by_client_id(client_id) is not None:
            raise BrokerRejected(f"client id {client_id} already used")
        vol = self._volume(symbol, qty)
        q = self.quote(symbol)
        if q is None:
            raise BrokerRejected(f"no price for {symbol}")
        ref = q.ask if side > 0 else q.bid
        if not (isinstance(stop, (int, float)) and math.isfinite(stop)) or (ref - stop) * side <= 0:
            raise BrokerRejected(f"stop {stop} is not on the loss side of the price {ref}")
        req = {"ctidTraderAccountId": self.account_id, "symbolId": self.ids[symbol], "orderType": P.ORDER_TYPE["MARKET"],
               "tradeSide": P.TRADE_SIDE["BUY" if side > 0 else "SELL"], "volume": vol,
               "relativeStopLoss": int(round(abs(ref - stop) * PRICE)), "label": client_id,
               "clientOrderId": client_id, "comment": str((meta or {}).get("rule") or "aitrader")[:100]}
        if target is not None:
            if (target - ref) * side <= 0:
                raise BrokerRejected(f"target {target} is not on the profit side of the price {ref}")
            req["relativeTakeProfit"] = int(round(abs(target - ref) * PRICE))
        self._at_submission("the order")

        def mine(name, msg, rcid, cid):
            o = msg.get("order") or {}
            return name == "ProtoOAExecutionEvent" and (rcid == cid or o.get("clientOrderId") == client_id)

        def terminal(name, msg):
            et = msg.get("executionType")
            return "DONE" if et == FILLED else "REJECTED" if et in (REJECTED, CANCELLED, EXPIRED) else None

        _, ev = self._write("ProtoOANewOrderReq", req, mine, terminal)
        deal, pos, order = ev.get("deal") or {}, ev.get("position") or {}, ev.get("order") or {}
        if "executionPrice" not in deal or "positionId" not in pos:
            raise AmbiguousExecution("the fill event carries no price or no position: read the account by client id")
        return Fill(str(order.get("orderId", deal.get("orderId"))), str(pos["positionId"]), float(deal["executionPrice"]),
                    int(deal.get("executionTimestamp", self.clock() * 1000) // 1000))

    def modify_stop(self, position_id: str, stop: float, permit=None) -> float:
        if self._gate is None:
            raise BrokerRejected("NO_RISK_GATE: this broker has no hard risk gate attached; it moves no stop")
        held = {p.id: p for p in self.positions()}.get(position_id)
        if held is None:
            raise BrokerRejected(f"no open position {position_id}")
        problem = self._gate.redeem_stop(permit, position_id=position_id, client_id=held.client_id, stop=stop)
        if problem:
            raise BrokerRejected(problem)
        self._before_write("the stop move")
        q = self.quote(held.symbol)
        if q is None:
            raise BrokerRejected(f"no price for {held.symbol}")
        exit_px = q.bid if held.side > 0 else q.ask
        if not (isinstance(stop, (int, float)) and math.isfinite(stop) and stop > 0) or (exit_px - stop) * held.side <= 0:
            raise BrokerRejected(f"stop {stop} is not on the loss side of the price {exit_px}")
        req = {"ctidTraderAccountId": self.account_id, "positionId": int(position_id), "stopLoss": float(stop)}
        if held.target is not None:
            req["takeProfit"] = float(held.target)  # an amend sets both: the target is kept as it is
        self._at_submission("the stop move")
        try:
            self._write("ProtoOAAmendPositionSLTPReq", req,
                        lambda n, m, rcid, cid: n == "ProtoOAExecutionEvent" and rcid == cid,
                        lambda n, m: "REJECTED" if m.get("executionType") == REJECTED else "DONE")
        except AmbiguousExecution:
            pass  # asked once; what the broker now holds is read below, never resent
        now = {p.id: p for p in self.positions()}.get(position_id)
        if now is None:
            raise AmbiguousExecution(f"position {position_id} is no longer open after the stop move")
        tick = 10 ** -int((self.details.get(self.ids.get(now.symbol), {}) or {}).get("digits", 2))
        if now.stop is None or abs(now.stop - stop) > tick / 2:
            raise AmbiguousExecution(f"the broker holds stop {now.stop}, not {stop}: outcome unknown, never resent")
        return float(now.stop)

    def close(self, position_id: str, client_id: str | None = None, reason: str = "MANUAL") -> ClosedTrade:
        pos = {str(p["positionId"]): p for p in self._reconcile()}.get(position_id)
        if pos is None:
            raise BrokerRejected(f"no open position {position_id}")
        bp = self._position(pos)
        self._before_write("the close")
        t0 = self._trader()
        before = t0.get("balance")
        req = {"ctidTraderAccountId": self.account_id, "positionId": int(position_id),
               "volume": int((pos.get("tradeData") or {}).get("volume", 0))}
        self._at_submission("the close")

        def mine(name, msg, rcid, cid):
            return name == "ProtoOAExecutionEvent" and (
                rcid == cid or str((msg.get("position") or {}).get("positionId")) == position_id
                and (msg.get("order") or {}).get("closingOrder") is True)

        def terminal(name, msg):
            et = msg.get("executionType")
            return "DONE" if et == FILLED else "REJECTED" if et in (REJECTED, CANCELLED, EXPIRED) else None

        _, ev = self._write("ProtoOAClosePositionReq", req, mine, terminal)
        deal = ev.get("deal") or {}
        cpd = deal.get("closePositionDetail") or {}
        md = cpd.get("moneyDigits")
        pnl = ((cpd["balance"] - before) / 10 ** md) if (md is not None and "balance" in cpd and before is not None
                                                         and t0.get("moneyDigits") == md) else None
        money = (lambda k: cpd[k] / 10 ** md if md is not None and k in cpd else None)
        ct = ClosedTrade(position_id=position_id, client_id=bp.client_id, symbol=bp.symbol, side=bp.side, qty=bp.qty,
                           entry=float(cpd.get("entryPrice", bp.entry)), exit=float(deal.get("executionPrice", math.nan)),
                           opened=bp.opened, closed=int(deal.get("executionTimestamp", self.clock() * 1000) // 1000),
                           reason=reason, pnl=pnl, gross_pnl=money("grossProfit"))
        self._own_closes[position_id] = ct
        return ct

    def closed_since(self, t: int) -> list[ClosedTrade]:
        """Positions the broker closed since t (a stop hit while nobody was connected), read from its closing deals.
        Their net P/L, commission and swap are left unknown (None): the deal reports them without a documented sign
        convention, and the balance before the deal is not in it. A close this broker sent itself is returned as
        close() measured it (the change in balance). The gross profit, whose sign is plain, is kept."""
        now_ms = int(self.clock()) * 1000
        _, res = self.c.call("ProtoOADealListReq", {"ctidTraderAccountId": self.account_id,
                                                    "fromTimestamp": max(0, int(t) * 1000), "toTimestamp": now_ms,
                                                    "maxRows": 1000}, ("ProtoOADealListRes",))
        if res.get("hasMore"):
            raise BrokerError("more closing deals than one page since the last read: not all could be read")
        out = []
        for d in sorted((d for d in res.get("deal", []) if d.get("closePositionDetail")),
                        key=lambda d: d.get("executionTimestamp", 0)):
            cpd = d["closePositionDetail"]
            md = cpd.get("moneyDigits")
            closed = int(d.get("executionTimestamp", 0) // 1000)
            if closed < t:
                continue
            if str(d["positionId"]) in self._own_closes:
                out.append(self._own_closes[str(d["positionId"])])  # closed by this broker: its measured P/L
                continue
            sid = d.get("symbolId")
            out.append(ClosedTrade(
                position_id=str(d["positionId"]), client_id=d.get("label"), symbol=self.names.get(sid, f"#{sid}"),
                side=-1 if d.get("tradeSide") == P.TRADE_SIDE["BUY"] else 1,  # the closing deal is the opposite side
                qty=cpd.get("closedVolume", d.get("filledVolume", 0)) / 100, entry=float(cpd["entryPrice"]),
                exit=float(d["executionPrice"]) if "executionPrice" in d else math.nan, opened=0, closed=closed,
                reason="UNKNOWN", pnl=None,
                gross_pnl=cpd["grossProfit"] / 10 ** md if md is not None and "grossProfit" in cpd else None))
        return out
