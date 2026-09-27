"""A frequent decision cadence for the model-trader modes, and what it must never loosen.

- DECISION_INTERVAL_MIN is refused for the evidence system (it runs at its tested cadence);
- SYMBOLS_PER_CYCLE rotates through every pair, none skipped, none repeated early;
- open paper positions are checked on M1 bars between H1 closes, and a bar from
  before the position opened never closes it;
- one pair's failed price does not blank the pairs table;
- the models read completed M5/M15 bars when the feed has them, and may trade on them.
"""

from __future__ import annotations

import numpy as np
import pytest

from aitrader.agents.llm_trader import multi_timeframe, validate_proposal
from aitrader.broker.paper import PaperBroker
from aitrader.data.bars import BarSeries
from aitrader.data.feed import ReplayFeed
from aitrader.service.config import ServiceConfig, ServiceConfigError
from aitrader.service.runtime import FAST_DELAY_S, Runtime

from .test_pipeline import START, market
from .test_service import Clock

SYMS = ("EURUSD", "GBPUSD", "USDJPY")


def minute_bars(symbol, start, lows, highs, mid=1.30):
    n = len(lows)
    half = 0.00005
    cols = {"open_time": start + 60 * np.arange(n), "ticks": np.ones(n), "spread_mean": np.full(n, 2 * half),
            "spread_max": np.full(n, 2 * half)}
    for side, k in (("bid", -half), ("ask", half)):
        cols |= {f"{side}_open": np.full(n, mid + k), f"{side}_close": np.full(n, mid + k),
                 f"{side}_low": np.asarray(lows) + k, f"{side}_high": np.asarray(highs) + k}
    return BarSeries.from_columns(symbol, "M1", "test", **cols)


class LiveLikeFeed(ReplayFeed):
    """The replay, plus the broker-only lower timeframes a live feed has."""

    def __init__(self, series, lower=None, broken=()):
        super().__init__(series)
        self.lower, self.broken, self.asked = lower or {}, set(broken), []

    def bars_tf(self, symbol, timeframe, as_of, count):
        self.asked.append((symbol, timeframe))
        b = self.lower.get((symbol, timeframe))
        if b is None:
            return None
        keep = b.available_at <= as_of
        return b.take(slice(0, int(keep.sum())))

    def quote(self, symbol, now):
        if symbol in self.broken:
            raise ConnectionError("broker timed out")
        q = super().quote(symbol, now)
        # A live broker stamps its quote with the current time; the replay stamps the last
        # H1 close, which mid-hour the stale-data check (rightly) refuses.
        return None if q is None else type(q)(q.symbol, q.bid, q.ask, now)


def build(tmp_path, monkeypatch, mode="llm_trader", lower=None, broken=(), **cfg):
    monkeypatch.setenv("DECISION_MODE", mode)
    data = {s: market(s, START, 24 * 7 * 20, i + 1, 1.30 if "JPY" not in s else 110.0) for i, s in enumerate(SYMS)}
    feed = LiveLikeFeed(data, lower, broken)
    clock = Clock(int(data["EURUSD"].available_at[2000]))
    broker = PaperBroker(feed, clock, None, start_balance=20_000)
    rt = Runtime(ServiceConfig(mode="PAPER", data_dir=str(tmp_path), port=0, symbols=SYMS, dashboard_token="t", **cfg),
                 feed=feed, broker=broker, clock=clock, knowledge_dir=tmp_path / "no-kb")
    broker.db = rt.db
    return rt, clock, feed


@pytest.mark.parametrize("env,ok", [({"DECISION_INTERVAL_MIN": "1"}, True), ({"DECISION_INTERVAL_MIN": "0"}, True),
                                    ({"DECISION_INTERVAL_MIN": "241"}, False), ({"DECISION_INTERVAL_MIN": "-5"}, False),
                                    ({"SYMBOLS_PER_CYCLE": "3", "SYMBOLS": "EURUSD,GBPUSD"}, False)])
def test_the_cadence_settings_are_bounded(env, ok):
    if ok:
        assert ServiceConfig.from_env({"MODE": "PAPER", **env}).decision_interval_min == int(env["DECISION_INTERVAL_MIN"])
    else:
        with pytest.raises(ServiceConfigError):
            ServiceConfig.from_env({"MODE": "PAPER", **env})


def test_the_evidence_system_refuses_a_cadence_it_was_never_tested_at(tmp_path, monkeypatch):
    with pytest.raises(ServiceConfigError, match="tested at"):
        build(tmp_path, monkeypatch, mode="evidence", decision_interval_min=5)
    rt, _, _ = build(tmp_path / "b", monkeypatch, mode="trading_room", decision_interval_min=1)
    assert rt.decision_interval_s == 60


def test_the_next_decision_lands_just_after_the_interval_boundary(tmp_path, monkeypatch):
    rt, clock, _ = build(tmp_path, monkeypatch, decision_interval_min=5)
    clock.t = (clock.t // 300) * 300 + 7
    assert rt._next_decision_time() == (clock.t // 300 + 1) * 300 + FAST_DELAY_S
    rt2, _, _ = build(tmp_path / "b", monkeypatch)
    assert rt2._next_decision_time() is None  # no interval: the tested H1 cadence


def test_pairs_rotate_so_every_pair_is_analysed_in_turn(tmp_path, monkeypatch):
    rt, _, _ = build(tmp_path, monkeypatch, decision_interval_min=1, symbols_per_cycle=2)
    picks = [rt._cycle_symbols() for _ in range(3)]
    assert picks == [["EURUSD", "GBPUSD"], ["USDJPY", "EURUSD"], ["GBPUSD", "USDJPY"]]
    rt_all, _, _ = build(tmp_path / "b", monkeypatch)
    assert rt_all._cycle_symbols() is None  # 0 = every pair, every cycle


def test_an_open_paper_position_is_stopped_on_the_minute_not_at_the_next_hour(tmp_path, monkeypatch):
    rt, clock, feed = build(tmp_path, monkeypatch, decision_interval_min=1)
    q = feed.quote("EURUSD", clock.t)
    opened = clock.t
    fill = rt.broker.place_market("EURUSD", 1, 0.1, q.bid - 0.0020, q.ask + 0.0040, "cid-1")
    mid = (q.bid + q.ask) / 2
    lows = [mid - 0.0030, mid - 0.0005, mid - 0.0005, mid - 0.0030]  # the first minute is BEFORE the open
    start = (opened // 60) * 60 - 60
    feed.lower[("EURUSD", "M1")] = minute_bars("EURUSD", start, lows, [mid + 0.0005] * 4, mid)
    clock.t = start + 3 * 60 + 1  # three minutes have closed: the pre-open one and two after
    rt.monitor_once()
    assert [p.id for p in rt.broker.positions()] == [fill.position_id]  # the pre-open low closed nothing
    clock.t = start + 4 * 60 + 1
    rt.monitor_once()
    assert rt.broker.positions() == []
    closed = rt.broker.closed_since(0)[-1]
    assert closed.reason == "STOP" and closed.closed == start + 4 * 60  # within the minute


def test_one_pairs_failed_price_does_not_blank_the_pairs_table(tmp_path, monkeypatch):
    rt, _, _ = build(tmp_path, monkeypatch, broken=("GBPUSD",))
    rows = {r["symbol"]: r for r in rt.market()}
    assert list(rows) == list(SYMS)
    assert rows["GBPUSD"]["bid"] is None and "timed out" in rows["GBPUSD"]["quote_error"]
    assert rows["EURUSD"]["bid"] is not None and rows["EURUSD"]["quote_error"] is None


def test_the_models_read_completed_m5_and_m15_bars_and_may_trade_on_them():
    h1 = market("EURUSD", START, 24 * 40, 1, 1.3)
    as_of = int(h1.available_at[-1])
    m5 = minute_bars("EURUSD", as_of - 60 * 50, [1.299] * 50, [1.301] * 50)
    m5 = BarSeries.from_columns("EURUSD", "M5", "test", **{f: getattr(m5, f) for f in (
        "open_time", "bid_open", "bid_high", "bid_low", "bid_close", "ask_open", "ask_high", "ask_low", "ask_close",
        "ticks", "spread_mean", "spread_max")})
    mtf = multi_timeframe(h1, as_of, {"M5": m5, "M15": None})
    assert set(mtf) == {"M5", "H1", "H4", "D1"}  # a missing lower timeframe is simply absent
    assert len(mtf["M5"]["bars"]) == 24
    ok = {"action": "BUY", "timeframe": "M5", "stop": 1.1, "target": 1.2, "max_hold_hours": 1, "thesis": "scalp"}
    assert validate_proposal(ok) is None
    assert validate_proposal({**ok, "timeframe": "M1"}) is not None  # never on a timeframe it cannot see


def test_every_few_minutes_the_model_reads_m5_and_trades_on_it_through_the_risk_engine(tmp_path, monkeypatch):
    """End to end at a 5-minute cadence: the packet carries completed M5 bars, the model trades on M5,
    the risk engine sizes it, and pairs rotate one per cycle."""
    import json

    import aitrader.service.runtime as runtime_mod
    from aitrader.llm.provider import LLMClient, LLMConfig

    from .test_service import _write_kb

    packets = []

    def transport(url, headers, body, timeout):
        system, user = body["messages"][0]["content"], json.loads(body["messages"][1]["content"])
        if "reviewing one of YOUR OWN" in system:
            reply = {"what_happened": "closed", "was_it_a_mistake": False}
        else:
            packets.append(user)
            ask, atr = user["quote"]["ask"], user["timeframes"]["H1"]["atr14"]
            reply = {"action": "BUY", "timeframe": "M5", "stop": ask - 1.0 * atr, "target": ask + 1.5 * atr,
                     "max_hold_hours": 1, "thesis": "M5 scalp", "invalidation": "stop", "memory_used": "none"}
        return {"choices": [{"message": {"content": json.dumps(reply)}}]}

    monkeypatch.setattr(runtime_mod, "LLMClient",
                        lambda cfg: LLMClient(LLMConfig("openai_compatible", "https://x.test/v1", "k", "m1"), transport))
    _write_kb(tmp_path / "kb")
    monkeypatch.setenv("DECISION_MODE", "llm_trader")
    data = {s: market(s, START, 24 * 7 * 20, i + 1, 1.30 if "JPY" not in s else 110.0) for i, s in enumerate(SYMS)}
    clock = Clock(int(data["EURUSD"].available_at[2000]))
    lower = {}
    for s, h1 in data.items():
        mid = float(h1.mid_close[2000])
        b = minute_bars(s, clock.t - 300 * 60, [mid * 0.999] * 60, [mid * 1.001] * 60, mid)
        lower[(s, "M5")] = BarSeries.from_columns(s, "M5", "test", **{f: getattr(b, f) for f in (
            "bid_open", "bid_high", "bid_low", "bid_close", "ask_open", "ask_high", "ask_low", "ask_close",
            "ticks", "spread_mean", "spread_max")}, open_time=clock.t - 300 * 60 + 300 * np.arange(60))
    feed = LiveLikeFeed(data, lower)
    broker = PaperBroker(feed, clock, None, start_balance=20_000)
    rt = Runtime(ServiceConfig(mode="PAPER", data_dir=str(tmp_path / "rt"), port=0, symbols=SYMS, dashboard_token="t",
                               decision_interval_min=5, symbols_per_cycle=1),
                 feed=feed, broker=broker, clock=clock, knowledge_dir=tmp_path / "kb")
    broker.db = rt.db
    rt.resume()
    for _ in range(3):
        clock.t += 300
        rt.run_cycle(decide=True)
    assert [p["instrument"] for p in packets] == list(SYMS)  # one pair per cycle, in rotation
    assert all("M5" in p["timeframes"] and len(p["timeframes"]["M5"]["bars"]) == 24 for p in packets)
    traded = rt.db.query("SELECT d.timeframe AS tf, v.approved AS ok, v.payload AS vp FROM decisions d "
                         "JOIN risk_verdicts v ON v.decision_id = d.id")
    assert traded and all(r["tf"] == "M5" for r in traded)
    assert any(r["ok"] == 1 and json.loads(r["vp"])["qty"] > 0 for r in traded)  # sized by the risk engine
