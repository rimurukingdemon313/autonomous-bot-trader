"""FLOW-1: fix calendars, clocks across daylight saving, cost arithmetic, and planted effects that
must be found while a null market must not be."""

from __future__ import annotations

from datetime import date, datetime, timezone

import numpy as np
import pytest

from aitrader.data.bars import BarSeries
from aitrader.research.discovery import flow

UTC = timezone.utc


def m15(symbol, start: date, end: date, drift_fn=None, seed=0, sigma=0.00008, spread=0.00008, base=1.10):
    """Weekday M15 bars; drift_fn(t) adds a deterministic per-bar move (planted effect)."""
    rng = np.random.default_rng(seed)
    t0 = int(datetime(start.year, start.month, start.day, tzinfo=UTC).timestamp())
    t1 = int(datetime(end.year, end.month, end.day, tzinfo=UTC).timestamp())
    ts = np.arange(t0, t1, 900)
    ts = ts[[datetime.fromtimestamp(int(t), UTC).weekday() < 5 for t in ts]]
    steps = rng.normal(0, sigma, len(ts)) + (np.array([drift_fn(int(t)) for t in ts]) if drift_fn else 0.0)
    mid = base * np.exp(np.cumsum(steps))
    o = np.concatenate(([base], mid[:-1]))
    h = spread / 2 * o
    hi, lo = np.maximum(o, mid), np.minimum(o, mid)
    return BarSeries.from_columns(symbol, "M15", "test", open_time=ts, bid_open=o - h, bid_high=hi - h, bid_low=lo - h,
                                  bid_close=mid - h, ask_open=o + h, ask_high=hi + h, ask_low=lo + h, ask_close=mid + h,
                                  ticks=np.full(len(ts), 10), spread_mean=np.full(len(ts), spread),
                                  spread_max=np.full(len(ts), spread))


def test_gotobi_calendar_moves_weekend_days_back_and_includes_the_month_end():
    got = flow.gotobi_dates(date(2015, 5, 1), date(2015, 6, 1))
    # 5 Tue; 10 Sun -> Fri 8; 15 Fri; 20 Wed; 25 Mon; 31 Sun -> Fri 29
    assert got == [date(2015, 5, d) for d in (5, 8, 15, 20, 25, 29)]
    assert flow.last_business_days(date(2015, 5, 1), date(2015, 7, 1)) == [date(2015, 5, 29), date(2015, 6, 30)]


def test_the_london_clock_follows_daylight_saving_and_tokyo_has_none():
    summer, winter = flow.london_times(date(2015, 7, 31)), flow.london_times(date(2015, 1, 30))
    assert datetime.fromtimestamp(summer["entry"], UTC).hour == 15  # 16:15 BST = 15:15 UTC
    assert datetime.fromtimestamp(winter["entry"], UTC).hour == 16  # 16:15 GMT
    tk = flow.tokyo_times(date(2015, 5, 15))
    assert datetime.fromtimestamp(tk["pre_entry"], UTC) == datetime(2015, 5, 14, 23, 0, tzinfo=UTC)
    assert datetime.fromtimestamp(tk["fix_exit"], UTC) == datetime(2015, 5, 15, 1, 0, tzinfo=UTC)


def test_costs_by_hand_and_a_missing_bar_is_no_trade():
    b = m15("EURUSD", date(2015, 5, 4), date(2015, 5, 5), sigma=0.0)  # flat market, spread 0.8 pip
    op = flow.Opens(b)
    t0, t1 = int(b.open_time[0]), int(b.open_time[4])
    r = flow.trade(op, t0, t1, +1, flow.Costs(slippage_pips=0.1, commission_pips_rt=0.7))
    # flat: gross 0; net = -(spread 0.88 pip at 1.10 + 2 x 0.1 slip + 0.7 commission)
    assert r["gross_pips"] == pytest.approx(0.0, abs=1e-9)
    assert r["net_pips"] == pytest.approx(-(0.00008 * 1.10 / 0.0001 + 0.2 + 0.7), abs=1e-6)
    assert flow.trade(op, t0, t0 + 7, +1, flow.Costs()) is None  # no bar opens then
    x2 = flow.trade(op, t0, t1, +1, flow.Costs().stressed(2.0))
    assert x2["net_pips"] == pytest.approx(2 * r["net_pips"], rel=1e-9)  # every cost doubles


def gotobi_drift(per_bar):
    """USDJPY drifts up from 08:00 to 10:00 JST on gotobi days only (the planted effect)."""
    gset = set(flow.gotobi_dates(date(2010, 1, 1), date(2013, 1, 1)))

    def f(t):
        d = datetime.fromtimestamp(t, UTC)
        tokyo = d.astimezone(flow.TOKYO)
        return per_bar if (tokyo.date() in gset and 8 <= tokyo.hour < 10) else 0.0
    return f


@pytest.mark.parametrize("planted,expect", [(0.00025, "found"), (0.0, "absent")])
def test_a_planted_gotobi_effect_is_found_and_a_null_market_shows_none(planted, expect):
    b = m15("USDJPY", date(2010, 1, 1), date(2013, 1, 1), gotobi_drift(planted), seed=4, sigma=0.0004,
            spread=0.00005, base=90.0)
    op = flow.Opens(b)
    got = flow.gotobi_dates(date(2010, 1, 5), date(2013, 1, 1))
    ev = flow.gotobi_events(op, got, "pre", flow.Costs())
    s = flow.summary(ev)
    assert s["n"] > 150
    if expect == "found":
        assert s["t"] > 5
        others = [d for d in flow.business_days(date(2010, 1, 5), date(2013, 1, 1)) if d not in set(got)]
        ctrl = flow.gotobi_events(op, others, "pre", flow.Costs())
        assert flow.welch_t([e["net_bps"] for e in ev], [e["net_bps"] for e in ctrl]) > 5
    else:
        assert s["mean"] < 0 and abs(s["t"]) < 4  # costs only: slightly negative, no effect


def test_a_planted_fix_reversal_is_found_on_month_ends():
    me = set(flow.last_business_days(date(2012, 1, 1), date(2016, 1, 1)))
    rng = np.random.default_rng(9)
    pushes = {d: rng.choice([-1, 1]) for d in me}

    def drift(t):
        d = datetime.fromtimestamp(t, UTC).astimezone(flow.LONDON)
        if d.date() not in me:
            return 0.0
        k = pushes[d.date()]
        if 15 <= d.hour and (d.hour, d.minute) < (15, 45):
            return 0.0004 * k  # pushed before the fix...
        if (16, 15) <= (d.hour, d.minute) < (17, 15):
            return -0.0003 * k  # ...and reversed after it
        return 0.0
    bars = {s: m15(s, date(2012, 1, 1), date(2016, 1, 1), drift, seed=i, sigma=0.0002)
            for i, s in enumerate(("EURUSD", "GBPUSD", "AUDUSD", "NZDUSD"))}
    ev = flow.fix_events({s: flow.Opens(b) for s, b in bars.items()}, sorted(me), flow.Costs())
    s = flow.summary(ev)
    assert s["n"] >= 40 and s["mean"] > 0 and s["t"] > 4
    assert all(e["pairs"] == 4 for e in ev)


def test_statistics_by_hand():
    ev = [{"date": date(2010, 1, i + 1), "net_bps": x} for i, x in enumerate([1.0, -1.0, 3.0])]
    s = flow.summary(ev)
    assert s["mean"] == pytest.approx(1.0) and s["sd"] == pytest.approx(2.0)
    assert s["t"] == pytest.approx(1.0 / (2.0 / 3 ** 0.5), abs=1e-3)
    assert flow.max_drawdown([1.0, -1.0, -2.0, 3.0]) == pytest.approx(3.0)


def test_the_flow_study_never_reaches_risk_execution_or_the_broker():
    from pathlib import Path
    root = Path(__file__).resolve().parents[2]
    for p in (root / "aitrader" / "research" / "discovery" / "flow.py", root / "scripts" / "flow1.py"):
        src = p.read_text()
        for forbidden in ("aitrader.risk", "aitrader.broker", "aitrader.execution", "tradelocker"):
            assert forbidden not in src


def test_the_preregistered_designs_are_frozen():
    """FLOW-1 and DIV-1 were registered with a spec hash and a code hash: editing either study after
    registration would make every later result a claim about code that was never preregistered."""
    import json
    import sys
    from pathlib import Path
    root = Path(__file__).resolve().parents[2]
    sys.path.insert(0, str(root / "scripts"))
    import div1
    import flow1
    for mod in (flow1, div1):
        frozen = json.loads(mod.SPEC.read_text())
        assert mod.spec_sha(frozen["spec"]) == frozen["sha256"], mod.PID
        assert mod.code_hash() == frozen["code_sha256"], f"{mod.PID}: study code changed after registration"
