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
        n = int((b.available_at <= as_of).sum())  # completed bars only, and at most `count`, like a real feed
        return b.take(slice(max(0, n - count), n))

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
    assert len(mtf["M5"]["bars"]) == 18
    ok = {"action": "BUY", "timeframe": "M5", "stop": 1.1, "target": 1.2, "max_hold_hours": 1, "thesis": "scalp"}
    assert validate_proposal(ok) is None
    assert validate_proposal({**ok, "timeframe": "S30"}) is not None  # never on a timeframe it cannot see


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
        elif "holds this open paper position" in system:
            reply = {"action": "HOLD", "reason": "let it work"}
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
    decided = [r["symbol"] for r in rt.db.query("SELECT symbol FROM decisions ORDER BY rowid")]
    assert decided == list(SYMS)  # one pair per cycle, in rotation
    # EURUSD and GBPUSD are now open: two USD positions, the per-currency limit. The risk engine
    # would refuse any USDJPY trade, so the model is not asked for one, and the record says why.
    assert [p["instrument"] for p in packets] == list(SYMS[:2])
    last = json.loads(rt.db.one("SELECT payload FROM decisions WHERE symbol='USDJPY'")["payload"])
    assert "currency_exposure" in last["no_trade_reason"]
    assert all("M5" in p["timeframes"] and len(p["timeframes"]["M5"]["bars"]) == 18 for p in packets)
    assert all("history" in p and "calendar" in p for p in packets)  # every decision carries both desks
    assert all(p["market_map"].get("structure") and p["market_map"]["levels"].get("round_numbers") for p in packets)
    assert all(p["intermarket"]["available"] is False for p in packets)  # this feed has none: said, not invented
    assert all(len(p["strategy_desk"]["strategies"]) == 16 and "H1" in p["strategy_desk"]["scoreboard"] for p in packets)
    traded = rt.db.query("SELECT d.timeframe AS tf, v.approved AS ok, v.payload AS vp FROM decisions d "
                         "JOIN risk_verdicts v ON v.decision_id = d.id")
    assert traded and all(r["tf"] == "M5" for r in traded)
    assert any(r["ok"] == 1 and json.loads(r["vp"])["qty"] > 0 for r in traded)  # sized by the risk engine


def review_rt(tmp_path, monkeypatch, verdict):
    """A live-like runtime with one open paper position and a model whose review answer is `verdict`."""
    import json

    import aitrader.service.runtime as runtime_mod
    from aitrader.llm.provider import LLMClient, LLMConfig

    from .test_service import _write_kb

    asked = []

    def transport(url, headers, body, timeout):
        system, user = body["messages"][0]["content"], json.loads(body["messages"][1]["content"])
        if "holds this open paper position" in system:
            asked.append(user)
            reply = verdict
        else:
            reply = {"action": "NO_TRADE", "thesis": "nothing"}
        return {"choices": [{"message": {"content": json.dumps(reply)}}]}

    monkeypatch.setattr(runtime_mod, "LLMClient",
                        lambda cfg: LLMClient(LLMConfig("openai_compatible", "https://x.test/v1", "k", "m1"), transport))
    _write_kb(tmp_path / "kb")
    monkeypatch.setenv("DECISION_MODE", "llm_trader")
    data = {s: market(s, START, 24 * 7 * 20, i + 1, 1.30 if "JPY" not in s else 110.0) for i, s in enumerate(SYMS)}
    clock = Clock(int(data["EURUSD"].available_at[2000]))
    feed = LiveLikeFeed(data)
    broker = PaperBroker(feed, clock, None, start_balance=20_000)
    rt = Runtime(ServiceConfig(mode="PAPER", data_dir=str(tmp_path / "rt"), port=0, symbols=SYMS, dashboard_token="t",
                               decision_interval_min=5, symbols_per_cycle=1),
                 feed=feed, broker=broker, clock=clock, knowledge_dir=tmp_path / "kb")
    broker.db = rt.db
    q = feed.quote("EURUSD", clock.t)
    fill = broker.place_market("EURUSD", 1, 0.1, q.bid - 0.0050, q.ask + 0.0100, "cid-r")
    rt.db.append("decisions", {"id": "d-r", "symbol": "EURUSD", "timeframe": "M1", "decision": "BUY", "mode": "PAPER",
                               "payload": {"thesis": "scalp", "max_hold_minutes": 3}})
    with rt.db.tx() as c:
        c.execute("INSERT INTO positions(id, intent_id, decision_id, symbol, side, qty, entry, stop, target, opened, "
                  "status, payload, updated) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
                  (fill.position_id, "cid-r", "d-r", "EURUSD", "BUY", 0.1, fill.price, q.bid - 0.0050, q.ask + 0.0100,
                   clock.t, "OPEN", "{}", 0.0))
    return rt, clock, asked


def test_the_model_closes_its_trade_whenever_it_decides(tmp_path, monkeypatch):
    rt, clock, asked = review_rt(tmp_path, monkeypatch, {"action": "CLOSE", "reason": "momentum faded"})
    rt.resume()
    clock.t += 60
    rt.run_cycle(decide=True)
    assert asked and asked[0]["position"]["symbol"] == "EURUSD" and "R_now" in asked[0]["position"]
    assert rt.broker.positions() == []  # closed after a minute, on its own call
    assert rt.broker.closed_since(0)[-1].reason == "MODEL_EXIT"  # and recorded as its own exit
    ev = rt.db.one("SELECT payload FROM events WHERE type='POSITION_REVIEWED'")
    assert "momentum faded" in ev["payload"]


@pytest.mark.parametrize("verdict", [{"action": "HOLD", "reason": "let it run"}, {"action": "SELL MORE"}, "garbage"])
def test_a_hold_or_an_unusable_answer_keeps_the_trade(tmp_path, monkeypatch, verdict):
    rt, clock, asked = review_rt(tmp_path, monkeypatch, verdict)
    rt.resume()
    clock.t += 60
    rt.run_cycle(decide=True)
    assert len(rt.broker.positions()) == 1  # a review can only close; anything else holds
    logged = rt.db.one("SELECT payload FROM events WHERE type='POSITION_REVIEWED'")["payload"]
    if verdict == {"action": "HOLD", "reason": "let it run"}:
        assert "let it run" in logged
    else:  # a malformed answer is not recorded as the model's decision
        assert "no model answered" in logged


def test_nothing_is_reviewed_while_trading_is_paused(tmp_path, monkeypatch):
    rt, clock, asked = review_rt(tmp_path, monkeypatch, {"action": "CLOSE", "reason": "x"})
    rt.pause("test")
    clock.t += 60
    rt.run_cycle(decide=True)
    assert asked == [] and len(rt.broker.positions()) == 1


def test_a_holding_time_of_minutes_is_honoured_between_cycles(tmp_path, monkeypatch):
    rt, clock, _ = review_rt(tmp_path, monkeypatch, {"action": "HOLD", "reason": "x"})
    clock.t += 2 * 60
    rt.monitor_once()
    assert len(rt.broker.positions()) == 1
    clock.t += 60 + 1  # three minutes: the model's own max_hold_minutes
    rt.monitor_once()
    assert rt.broker.positions() == []
    assert rt.broker.closed_since(0)[-1].reason == "TIME"  # labelled as what it was, not MANUAL


def test_an_open_trade_is_reviewed_on_its_own_pairs_turn(tmp_path, monkeypatch):
    rt, clock, asked = review_rt(tmp_path, monkeypatch, {"action": "HOLD", "reason": "x"})
    rt.resume()
    for _ in range(3):  # rotation: EURUSD, GBPUSD, USDJPY
        clock.t += 60
        rt.run_cycle(decide=True)
    assert len(asked) == 1 and asked[0]["position"]["symbol"] == "EURUSD"  # one call, on EURUSD's turn


class QuotesOnlyFeed(LiveLikeFeed):
    """A broker that sends live quotes but no candle history: what TradeLocker looks like when
    its history endpoint fails. Decisions cannot be made, and the dashboard must say why."""

    last_bars_ok = None

    def __init__(self, series):
        super().__init__(series)
        self.last_ok = None

    def bars(self, symbol, as_of, count):
        return None

    def quote(self, symbol, now):
        self.last_ok = now
        return super().quote(symbol, now)

    def data_error(self, symbol):
        return "H1 bars: no known TradeLocker history endpoint shape returned candles"


def test_quotes_without_bars_are_reported_as_such_never_as_connected(tmp_path, monkeypatch):
    rt, clock, _ = build(tmp_path, monkeypatch, decision_interval_min=1)
    rt.feed = rt.orch.feed = QuotesOnlyFeed({s: rt.feed._series[s] for s in SYMS}) if hasattr(rt.feed, "_series") \
        else QuotesOnlyFeed({s: market(s, START, 24 * 7 * 20, i + 1, 1.30 if "JPY" not in s else 110.0)
                             for i, s in enumerate(SYMS)})
    rt.market()  # a quote arrives: the old dashboard called this CONNECTED
    rt.orch.decide("EURUSD", clock.t)
    data = rt.status()["components"]["data"]
    assert data.startswith("QUOTES ONLY, NO BARS") and "history endpoint" in data
    row = next(r for r in rt.market() if r["symbol"] == "EURUSD")
    assert row["decision"] == "NO_DATA" and "history endpoint" in row["reason"]


def test_a_stop_hit_while_the_team_was_deliberating_is_still_applied(tmp_path, monkeypatch):
    """The monitor waits while a cycle runs (minutes, with slow free models). When it resumes,
    every completed minute since the last one it applied must still be checked."""
    rt, clock, feed = build(tmp_path, monkeypatch, decision_interval_min=1)
    q = feed.quote("EURUSD", clock.t)
    rt.broker.place_market("EURUSD", 1, 0.1, q.bid - 0.0020, q.ask + 0.0040, "cid-gap")
    mid = (q.bid + q.ask) / 2
    start = (clock.t // 60) * 60
    lows = [mid - 0.0005] * 3 + [mid - 0.0030] + [mid - 0.0005] * 11  # the stop is hit in minute 4 of 15
    feed.lower[("EURUSD", "M1")] = minute_bars("EURUSD", start, lows, [mid + 0.0005] * 15, mid)
    clock.t = start + 15 * 60 + 1  # the monitor was blocked for 15 minutes
    rt.monitor_once()
    assert rt.broker.positions() == []
    assert rt.broker.closed_since(0)[-1].closed == start + 4 * 60  # closed at the minute it happened


def test_yahoo_prices_a_conversion_pair_that_is_not_on_the_list():
    from aitrader.data.yahoo import YahooFeed

    meta = {"chart": {"result": [{"meta": {"regularMarketPrice": 150.0, "regularMarketTime": 100},
                                  "timestamp": [], "indicators": {"quote": [{}]}}], "error": None}}
    f = YahooFeed(["EURUSD"], lambda: 100, fetch=lambda url: meta)
    q = f.quote("USDJPY")  # needed to value a JPY profit; not a traded pair
    assert q is not None and q.bid < 150.0 < q.ask


def test_once_the_daily_loss_limit_is_spent_the_models_are_not_asked(tmp_path, monkeypatch):
    """The risk engine would refuse any trade for the rest of the day; asking the team every minute
    anyway spent thousands of calls in a simulated day. Its own account checks now run first, and
    the decision says which one stopped it."""
    import json

    import aitrader.service.runtime as runtime_mod
    from aitrader.data.resample import bucket_start
    from aitrader.llm.provider import LLMClient, LLMConfig

    from .test_service import _write_kb

    asked = []

    def transport(url, headers, body, timeout):
        asked.append(body["messages"][0]["content"][:40])
        return {"choices": [{"message": {"content": json.dumps({"action": "NO_TRADE", "thesis": "x"})}}]}

    monkeypatch.setattr(runtime_mod, "LLMClient",
                        lambda cfg: LLMClient(LLMConfig("openai_compatible", "https://x.test/v1", "k", "m1"), transport))
    _write_kb(tmp_path / "kb")
    monkeypatch.setenv("DECISION_MODE", "llm_trader")
    data = {s: market(s, START, 24 * 7 * 20, i + 1, 1.30 if "JPY" not in s else 110.0) for i, s in enumerate(SYMS)}
    clock = Clock(int(data["EURUSD"].available_at[2000]))
    feed = LiveLikeFeed(data)
    broker = PaperBroker(feed, clock, None, start_balance=20_000)
    rt = Runtime(ServiceConfig(mode="PAPER", data_dir=str(tmp_path / "rt"), port=0, symbols=SYMS, dashboard_token="t",
                               decision_interval_min=1, symbols_per_cycle=1),
                 feed=feed, broker=broker, clock=clock, knowledge_dir=tmp_path / "kb")
    broker.db = rt.db
    rt.resume()
    clock.t += 60
    rt.run_cycle(decide=True)
    assert asked  # a normal day: the model is asked
    asked.clear()
    day = int(bucket_start(np.array([clock.t + 60]), "D1")[0])
    rt.db.set_kv("day_start", {"day": day, "equity": 20_600}, reason="test: the day started higher")  # now -2.9%
    for _ in range(3):
        clock.t += 60
        rt.run_cycle(decide=True)
    assert asked == []
    last = json.loads(rt.db.one("SELECT payload FROM decisions ORDER BY rowid DESC LIMIT 1")["payload"])
    assert "daily_loss" in last["no_trade_reason"] and "not consulted" in last["no_trade_reason"]
