"""TradeLocker behind this system's Broker and MarketFeed interfaces.

AI -> decision -> risk engine -> execution engine -> THIS -> TradeLocker.
Nothing above the execution engine imports this module.

Safety, inherited and added:
- DEMO only: `is_demo()` runs the transferred two-signal demo guard (URL and
  the broker's own account/claims evidence); anything but a positive
  verification returns False, and the execution engine then refuses.
- Writes are never retried (the transport raises AmbiguousExecution).
- TradeLocker has no client-supplied order id, so after an ambiguous send
  the position is found by MATCHING the recorded intent: same instrument,
  side and quantity, opened after the intent, not already claimed by another
  intent. Exactly one match is required; two or more stay UNKNOWN and are
  reported, never guessed and never resent.

Declared approximations (DATA_CONTRACT.md §4): TradeLocker's history is one
price series per bar (bid). Ask bars are built as bid + the spread measured
from the live quote at fetch time, and that measured spread is the spread
of the latest bar; older bars' spread is unknown (NaN), which no feature
reads. Candle volume is the broker's tick volume.
"""

from __future__ import annotations

import time
from typing import Callable

import numpy as np

from ...data.bars import BarSeries
from ...observability import log_event
from ...risk.engine import InstrumentSpec, Quote
from ..base import (
    AccountSnapshot, AmbiguousExecution, BrokerError, BrokerPosition, BrokerRejected, ClosedTrade, Fill,
)
from ._compat import TradingConfig
from .client import TradeLockerBroker
from .demo_guard import verify_demo
from .history import TIMEFRAME_MINUTES

ADAPTER_VERSION = "tradelocker-adapter-1.0.0"


class TradeLockerAdapter:
    name = "tradelocker"

    def __init__(self, config: TradingConfig, symbols: list[str], *,
                 intent_lookup: Callable[[str], dict | None],
                 claimed_positions: Callable[[], set[str]],
                 client: TradeLockerBroker | None = None, clock: Callable[[], float] = time.time,
                 sleep: Callable[[float], None] = time.sleep) -> None:
        self.bars_errors: dict[tuple[str, str], str] = {}  # (symbol, timeframe) -> why the last fetch failed
        self.config = config
        self._symbols = list(symbols)
        self.client = client or TradeLockerBroker(config)
        self.intent_lookup = intent_lookup
        self.claimed_positions = claimed_positions
        self.clock = clock
        self._sleep = sleep
        self._last_demo: dict | None = None

    # ── safety ──────────────────────────────────────────────────────────

    def is_demo(self) -> bool | None:
        try:
            self.client.ensure_session()
            meta = self.client.account_metadata()
            claims = self.client.session_claims()
        except BrokerError as exc:
            self._last_demo = {"verified": False, "reason": f"could not read account evidence: {exc}"}
            return None
        v = verify_demo(self.config, meta, stage="execution", claims=claims)
        self._last_demo = v.as_dict()
        return True if v.verified else False

    def demo_status(self) -> dict | None:
        return self._last_demo

    # ── reads ───────────────────────────────────────────────────────────

    def account(self) -> AccountSnapshot:
        st = self.client.account_state()
        return AccountSnapshot(float(st.equity), float(st.balance), st.currency, int(self.clock()))

    def positions(self) -> list[BrokerPosition]:
        return [BrokerPosition(p.position_id, p.symbol, 1 if p.direction == "BUY" else -1, p.quantity,
                               p.entry_price, p.stop_loss, p.take_profit, None,
                               int(p.opened_at.timestamp()) if p.opened_at else 0)
                for p in self.client.positions()]

    def quote(self, symbol: str, now: int | None = None) -> Quote | None:
        try:
            spec = self.client.instrument(symbol)
            q = self.client.quote(spec)
        except BrokerError as exc:
            log_event("BROKER", f"no quote for {symbol}: {exc}", severity="warning", symbol=symbol)
            return None
        return Quote(symbol, float(q.bid), float(q.ask), int(q.timestamp.timestamp()))

    def _rate(self, ccy: str, account_ccy: str) -> float | None:
        if ccy == account_ccy:
            return 1.0
        for pair, invert in ((f"{ccy}{account_ccy}", False), (f"{account_ccy}{ccy}", True)):
            q = self.quote(pair)
            if q is not None:
                mid = (q.bid + q.ask) / 2
                return 1 / mid if invert else mid
        return None

    def spec(self, symbol: str) -> InstrumentSpec | None:
        try:
            s = self.client.instrument(symbol)
        except BrokerError:
            return None
        if s.tick_value and s.tick_size and s.contract_size:
            value = s.tick_value / (s.tick_size * s.contract_size)
        else:
            quote_ccy = s.quote_currency or symbol[3:6]
            value = self._rate(quote_ccy, s.account_currency or "USD")
            if value is None:
                return None  # cannot value a move: no size, no trade
        return InstrumentSpec(symbol, float(s.contract_size), float(s.min_lot), float(s.lot_step),
                              float(s.max_lot), float(value))

    # MarketFeed ---------------------------------------------------------

    def symbols(self) -> list[str]:
        return list(self._symbols)

    def bars(self, symbol: str, as_of: int, count: int, timeframe: str = "H1") -> BarSeries | None:
        """The last `count` COMPLETED bars of `timeframe` at `as_of` (M1, M5, M15, H1, H4 or D1)."""
        tf_s = TIMEFRAME_MINUTES[timeframe] * 60
        key = (symbol, timeframe)
        try:
            spec = self.client.instrument(symbol)
            rows = self.client.candles(spec, timeframe, count=count + 2)
        except BrokerError as exc:
            log_event("DATA", f"no bars for {symbol}: {exc}", severity="warning", symbol=symbol)
            self.bars_errors[key] = f"{timeframe} bars: {exc}"[:240]
            return None
        q = self.quote(symbol)
        if q is None or not rows:
            self.bars_errors[key] = (f"{timeframe} bars: the broker returned none" if not rows
                                     else f"{timeframe} bars: no live quote to measure the spread")
            return None
        spread = q.ask - q.bid
        rows = sorted(rows, key=lambda r: r["timestamp"])
        t = np.array([int(r["timestamp"].timestamp()) if hasattr(r["timestamp"], "timestamp") else int(r["timestamp"])
                      for r in rows], dtype=np.int64)
        closed = t + tf_s <= as_of  # a forming bar is never used
        if not closed.any():
            self.bars_errors[key] = f"{timeframe} bars: none completed yet"
            return None
        self.bars_errors.pop(key, None)
        pick = np.flatnonzero(closed)[-count:]
        o = np.array([rows[i]["open"] for i in pick], float)
        h = np.array([rows[i]["high"] for i in pick], float)
        low = np.array([rows[i]["low"] for i in pick], float)
        c = np.array([rows[i]["close"] for i in pick], float)
        vol = np.array([rows[i].get("volume") or 0 for i in pick], float)
        sm = np.full(len(pick), np.nan)
        sm[-1] = spread
        return BarSeries.from_columns(
            symbol, timeframe, "tradelocker", open_time=t[pick],
            bid_open=o, bid_high=h, bid_low=low, bid_close=c,
            ask_open=o + spread, ask_high=h + spread, ask_low=low + spread, ask_close=c + spread,
            ticks=vol.astype(np.int64), spread_mean=sm, spread_max=sm)

    # ── writes: never retried ───────────────────────────────────────────

    def place_market(self, symbol: str, side: int, qty: float, stop: float, target: float,
                     client_id: str, meta: dict | None = None) -> Fill:
        spec = self.client.instrument(symbol)
        before = {p.id for p in self.positions()}
        result = self.client.place_market_order(spec, direction="BUY" if side > 0 else "SELL",
                                                quantity=qty, stop_loss=stop, take_profit=target)
        # The order was accepted. Find the position it opened; if it is not
        # visible yet, the outcome is ambiguous and reconciliation will match it.
        for _ in range(3):
            new = [p for p in self.positions() if p.id not in before and p.symbol == symbol and p.side == side
                   and abs(p.qty - qty) < 1e-9]
            if len(new) == 1:
                p = new[0]
                return Fill(result.order_id or "", p.id, p.entry, p.opened or int(self.clock()))
            self._sleep(0.5)
        raise AmbiguousExecution(f"order {result.order_id} accepted; its position is not yet visible")

    def find_by_client_id(self, client_id: str) -> BrokerPosition | None:
        intent = self.intent_lookup(client_id)
        if not intent:
            return None
        claimed = self.claimed_positions()
        side = 1 if intent["side"] in ("BUY", 1) else -1
        match = [p for p in self.positions()
                 if p.symbol == intent["symbol"] and p.side == side and abs(p.qty - intent["qty"]) < 1e-9
                 and p.opened >= intent["ts"] - 60 and p.id not in claimed]
        if len(match) == 1:
            return match[0]
        if len(match) > 1:
            log_event("RECONCILE", f"{len(match)} positions match intent {client_id}; refusing to guess",
                      severity="critical", symbol=intent["symbol"])
        return None

    def close(self, position_id: str, client_id: str | None = None, reason: str = "MANUAL") -> ClosedTrade:
        self.client.close_position(position_id)
        # The realised result is read from the broker's history by
        # closed_since(); nothing is invented here.
        return ClosedTrade(position_id, client_id, "", 0, 0.0, float("nan"), float("nan"), 0, int(self.clock()),
                           "MANUAL", None)

    def closed_since(self, t: int) -> list[ClosedTrade]:
        out = []
        for row in self.client.closed_positions():
            try:
                pid = str(row.get("positionId") or row.get("id"))
                closed = row.get("closeDate") or row.get("closeTime") or row.get("lastModified")
                closed_t = int(float(closed) / (1000 if float(closed) > 1e11 else 1)) if closed else None
                if closed_t is None or closed_t < t:
                    continue
                side = 1 if str(row.get("side", "buy")).lower() == "buy" else -1
                entry = float(row.get("openPrice") or row.get("avgPrice") or "nan")
                exit_ = float(row.get("closePrice") or row.get("exitPrice") or "nan")
                pnl = row.get("realizedPl") if row.get("realizedPl") not in (None, "") else row.get("realizedPnL")
                out.append(ClosedTrade(pid, None, str(row.get("symbol", "")), side, float(row.get("qty") or 0),
                                       entry, exit_, int(float(row.get("openDate") or 0) / 1000), closed_t,
                                       "UNKNOWN", float(pnl) if pnl not in (None, "") else None))
            except (TypeError, ValueError):
                continue  # an unreadable row is skipped, never guessed
        return out

    def health(self) -> dict:
        try:
            h = self.client.health()
        except Exception as exc:  # health must never raise
            h = {"error": type(exc).__name__}
        return {"adapter": ADAPTER_VERSION, "demo": self._last_demo, **h, "config": self.config.broker.public()}
