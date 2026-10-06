"""The Yahoo feed: public prices for the paper account, read carefully and labelled honestly.

The HTTP layer is a fake returning Yahoo's chart format, with the untidy parts
real responses have: null values, a forming bar, an error body.
"""

from __future__ import annotations

import pytest

from aitrader.data.yahoo import QUOTE_TTL_S, YahooFeed
from aitrader.service.config import ServiceConfig, ServiceConfigError

H = 3600
T0 = 1_790_000_000 - 1_790_000_000 % H  # an hour boundary


def chart(n, period, price=1.10, nulls=(), meta_time=None):
    ts = [T0 + i * period for i in range(n)]
    q = {k: [None if i in nulls else price + (0.001 if k == "high" else -0.001 if k == "low" else 0) for i in range(n)]
         for k in ("open", "high", "low", "close")}
    return {"chart": {"result": [{"meta": {"regularMarketPrice": price, "regularMarketTime": meta_time or ts[-1] + 30},
                                  "timestamp": ts, "indicators": {"quote": [q]}}], "error": None}}


class Yahoo:
    def __init__(self, reply):
        self.reply, self.urls = reply, []

    def __call__(self, url):
        self.urls.append(url)
        r = self.reply(url) if callable(self.reply) else self.reply
        if isinstance(r, Exception):
            raise r
        return r


def feed(reply, now):
    return YahooFeed(["EURUSD", "USDJPY"], lambda: now, fetch=Yahoo(reply))


def test_completed_h1_bars_with_the_estimated_spread_around_the_price():
    now = T0 + 10 * H + 600  # ten bars closed, the eleventh is forming
    f = feed(chart(11, H, nulls={3}), now)
    b = f.bars("EURUSD", now, 100)
    assert len(b) == 9  # the forming bar and the bar with a null value are dropped
    assert b.source == "yahoo+est-spread"
    spread = float(b.ask_close[-1] - b.bid_close[-1])
    assert spread == pytest.approx(0.8 * 0.0001)  # EURUSD: 0.8 pip, an estimate
    assert "EURUSD%3DX" in f._fetch.urls[0] or "EURUSD=X" in f._fetch.urls[0]
    assert f.last_bars_ok == now


def test_the_quote_carries_yahoos_own_time_so_a_delay_stays_visible():
    now = T0 + 10 * H
    f = feed(chart(10, 60, price=1.2, meta_time=now - 75), now)
    q = f.quote("EURUSD")
    assert q.time == now - 75 and q.bid < 1.2 < q.ask
    for _ in range(10):
        f.quote("EURUSD")
    assert len(f._fetch.urls) == 1  # one request per TTL
    f.clock = lambda: now + QUOTE_TTL_S
    f.quote("EURUSD")
    assert len(f._fetch.urls) == 2


def test_a_refusal_is_reported_and_not_retried_within_its_window():
    now = T0 + 10 * H
    f = feed(ConnectionError("429 Too Many Requests"), now)
    for _ in range(5):
        assert f.bars("EURUSD", now, 100) is None
    assert len(f._fetch.urls) == 1
    assert "429" in f.data_error("EURUSD")
    assert f.quote("EURUSD") is None  # no price is ever invented


def test_an_error_body_is_an_error_not_an_empty_market():
    now = T0 + 10 * H
    f = feed({"chart": {"result": None, "error": {"code": "Not Found", "description": "No data found"}}}, now)
    assert f.bars("EURUSD", now, 10) is None and "Not Found" in f.data_error("EURUSD")


def test_h4_is_built_from_completed_h1_bars():
    now = T0 + 24 * H
    f = feed(chart(24, H), now)
    h4 = f.bars_tf("EURUSD", "H4", now, 10)
    assert h4 is not None and len(h4) >= 5


@pytest.mark.parametrize("env,ok", [({"DATA_SOURCE": "yahoo"}, True), ({"DATA_SOURCE": "yahoo", "MODE": "DEMO"}, False),
                                    ({"DATA_SOURCE": "bloomberg"}, False)])
def test_the_source_setting_is_validated(env, ok):
    e = {"MODE": "PAPER", **env}
    if ok:
        c = ServiceConfig.from_env(e)
        assert c.data_source == "yahoo" and c.risk.max_quote_age_s == 90
    else:
        with pytest.raises(ServiceConfigError):
            ServiceConfig.from_env(e)


def test_the_service_runs_paper_on_yahoo_without_any_broker(tmp_path, monkeypatch):
    from aitrader.broker.paper import PaperBroker
    from aitrader.service.runtime import Runtime

    cfg = ServiceConfig(mode="PAPER", data_dir=str(tmp_path), port=0, symbols=("EURUSD",), data_source="yahoo")
    rt = Runtime(cfg, knowledge_dir=tmp_path / "no-kb")
    assert isinstance(rt.broker, PaperBroker) and type(rt.feed).__name__ == "YahooFeed"
    assert rt.status()["components"]["broker"] == "PAPER (simulated)"
    assert rt.status()["components"]["data_source"] == "yahoo"


def test_end_to_end_a_model_trades_on_yahoo_prices_through_the_risk_engine(tmp_path, monkeypatch):
    """Yahoo-shaped responses built from a real-looking replay: the service analyses, the model
    trades, the risk engine sizes it, and the paper account fills it with the estimated spread."""
    import json

    import aitrader.service.runtime as runtime_mod
    from aitrader.llm.provider import LLMClient, LLMConfig
    from aitrader.service.runtime import Runtime
    from tests.integration.test_pipeline import START, market
    from tests.integration.test_service import _write_kb

    h1 = market("EURUSD", START, 24 * 7 * 20, 1, 1.30)
    now = int(h1.available_at[2000]) + 45

    def to_chart(ts, closes, meta_time):
        q = {"open": list(closes), "high": [c + 0.0004 for c in closes], "low": [c - 0.0004 for c in closes],
             "close": list(closes)}
        return {"chart": {"result": [{"meta": {"regularMarketPrice": closes[-1], "regularMarketTime": meta_time},
                                      "timestamp": list(ts), "indicators": {"quote": [q]}}], "error": None}}

    def fake(url):
        mid = h1.mid_close[:2001]
        if "interval=60m" in url:
            return to_chart(h1.open_time[:2001].tolist(), mid.tolist(), now - 5)
        step = {"1m": 60, "5m": 300, "15m": 900, "1d": 86400}[url.split("interval=")[1].split("&")[0]]
        ts = [(now // step - 60 + i) * step for i in range(60)]
        return to_chart(ts, [float(mid[-1])] * 60, now - 5)

    def transport(u, headers, body, timeout):
        user = json.loads(body["messages"][1]["content"])
        if "quote" not in user:
            return {"choices": [{"message": {"content": json.dumps({"what_happened": "x", "was_it_a_mistake": False})}}]}
        ask, atr = user["quote"]["ask"], user["timeframes"]["H1"]["atr14"]
        return {"choices": [{"message": {"content": json.dumps(
            {"action": "BUY", "timeframe": "H1", "stop": ask - 1.5 * atr, "target": ask + 3 * atr,
             "max_hold_minutes": 120, "thesis": "test", "invalidation": "stop", "confidence": 0.5})}}]}

    monkeypatch.setenv("DECISION_MODE", "llm_trader")
    monkeypatch.setattr(runtime_mod, "LLMClient",
                        lambda cfg: LLMClient(LLMConfig("openai_compatible", "https://x.test/v1", "k", "m1"), transport))
    import aitrader.data.yahoo as yahoo_mod
    monkeypatch.setattr(yahoo_mod, "_http", fake)
    _write_kb(tmp_path / "kb")
    cfg = ServiceConfig(mode="PAPER", data_dir=str(tmp_path / "rt"), port=0, symbols=("EURUSD",), data_source="yahoo",
                        decision_interval_min=1)
    rt = Runtime(cfg, knowledge_dir=tmp_path / "kb", clock=lambda: now)
    rt.resume()
    rt.run_cycle(decide=True)
    st = rt.status()["components"]
    assert st["data"] == "CONNECTED" and st["data_source"] == "yahoo"
    # The model's trade is sized and approved by the risk engine, then SHADOW: a language model may not
    # create a trade, on paper either (takeover audit).
    assert rt.broker.positions() == []
    v = rt.db.one("SELECT approved FROM risk_verdicts")
    assert v["approved"] == 1
    prop = json.loads(rt.db.one("SELECT payload FROM forward_proposals")["payload"])
    assert prop["route"] == "SHADOW" and prop["symbol"] == "EURUSD"
    ctx = json.loads(rt.db.one("SELECT payload FROM decisions")["payload"])["context"]
    assert ctx["features"]["metadata"]["not_provided_by_source"] == ["tick_activity"]  # excluded, and said so


def test_intermarket_context_is_read_from_completed_hours_and_a_failure_is_named():
    """DXY, the 10-year yield, gold and S&P futures, as context. The forming hour is never used; a
    market Yahoo cannot serve is reported with its reason, never filled in; it is read once per window."""
    now = T0 + 30 * H + 600

    def reply(url):
        if "GC%3DF" in url:
            return {"chart": {"result": None, "error": {"code": "Not Found"}}}
        c = chart(31, H)
        closes = [100 + i for i in range(31)]  # rises by 1 an hour; the 31st bar is still forming
        c["chart"]["result"][0]["indicators"]["quote"][0]["close"] = closes
        return c

    f = feed(reply, now)
    im = f.intermarket(now)
    dxy = im["markets"]["DXY"]
    assert dxy["last"] == 129  # bar 30 (index 29) is the last completed one, not the forming 130
    assert dxy["chg_1h_pct"] == pytest.approx(round(1 / 128 * 100, 3))
    assert dxy["chg_4h_pct"] == pytest.approx(round(4 / 125 * 100, 3))
    assert "unavailable" in im["markets"]["GOLD"] and "Not Found" in im["markets"]["GOLD"]["unavailable"]
    assert any("%5ETNX" in u for u in f._fetch.urls)  # the yield index symbol is URL-encoded
    n = len(f._fetch.urls)
    f.intermarket(now + 60)
    assert len(f._fetch.urls) == n  # cached for its window
