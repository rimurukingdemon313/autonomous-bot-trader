"""DAY-1 (scripts/day1.py) on markets built so the answer is known: Wilder's 2-day RSI as computed by hand; a sharp
two-day dip in an uptrend is bought at its close and sold at the first close above the 5-day mean; the same dip below
the 200-day mean is not bought; the 6% stop is hit by a day's low and a gap below it fills at the open; a trade that
never recovers is closed at its 10th close; a later bar changes nothing before it; the basket gives each index a
quarter; costs are charged once per fill."""

from __future__ import annotations

from datetime import date, timedelta

import pytest

import scripts.day1 as D


def weekdays(n: int, start: date = date(2000, 1, 3)) -> list[date]:
    out, d = [], start
    while len(out) < n:
        if d.weekday() < 5:
            out.append(d)
        d += timedelta(days=1)
    return out


def bars_from(closes: list[float], lows: dict[int, float] | None = None, opens: dict[int, float] | None = None):
    days = weekdays(len(closes))
    out = []
    for i, c in enumerate(closes):
        o = (opens or {}).get(i, c)
        lo = min((lows or {}).get(i, min(o, c)), o, c)
        out.append((days[i], o, max(o, c), lo, c))
    return out


def rising(n: int, start: float = 100.0, step: float = 0.002) -> list[float]:
    out, p = [], start
    for _ in range(n):
        p *= 1 + step
        out.append(p)
    return out


def test_wilders_2_day_rsi_by_hand():
    r = D.rsi([10.0, 11.0, 10.0, 12.0, 11.0])
    assert r[:2] == [None, None]
    assert r[2] == pytest.approx(50.0)  # gains 1, 0 and losses 0, 1: equal averages
    assert r[3] == pytest.approx(100 - 100 / (1 + 1.25 / 0.25))  # (0.5 + 2) / 2 against (0.5 + 0) / 2
    assert r[4] == pytest.approx(50.0)


def test_a_sharp_dip_in_an_uptrend_is_bought_at_its_close_and_sold_at_the_first_close_above_the_5_day_mean():
    closes = rising(260)
    dip = [closes[-1] * 0.97]  # one 3% fall after a steady climb: the 2-day RSI drops to about 6
    after = [dip[-1] * 1.005, dip[-1] * 1.03, dip[-1] * 1.06]
    bars = bars_from(closes + dip + after)
    assert D.rsi([b[4] for b in bars])[260] < D.RSI_BUY
    trades, daily = D.trades(bars)
    assert len(trades) == 1
    t = trades[0]
    entry_i = 260  # the dip's close
    assert t["entry_day"] == bars[entry_i][0] and t["entry"] == pytest.approx(dip[-1])
    window = [b[4] for b in bars]
    exit_i = next(i for i in range(entry_i + 1, len(bars)) if window[i] > sum(window[i - 4:i + 1]) / 5)
    assert t["exit_day"] == bars[exit_i][0] and t["why"] == "MEAN"
    assert t["net"] == pytest.approx(window[exit_i] / dip[-1] - 1 - 2 * D.COST_SIDE)
    assert daily[bars[entry_i][0]] == pytest.approx(-D.COST_SIDE)  # bought at the close: only the fill's cost
    assert sum(daily.values()) == pytest.approx(sum(window[i] / window[i - 1] - 1 for i in range(entry_i + 1, exit_i + 1))
                                                - 2 * D.COST_SIDE)


def test_the_same_dip_below_the_200_day_mean_is_not_bought():
    closes = list(reversed(rising(260)))  # falling for a year: every close is below its 200-day mean
    dip = [closes[-1] * 0.97, closes[-1] * 0.97 * 0.97]
    trades, daily = D.trades(bars_from(closes + dip + [dip[-1] * 1.05] * 3))
    assert trades == [] and daily == {}


def test_the_stop_is_hit_by_the_days_low_and_a_gap_below_it_fills_at_the_open():
    closes = rising(260)
    entry = closes[-1] * 0.97  # bought at this dip's close (bar 260)
    # the next day closes a little lower but trades 7% under the entry inside the day
    bars = bars_from(closes + [entry, entry * 0.999, entry * 1.05], lows={261: entry * 0.93})
    t = D.trades(bars)[0][0]
    assert t["why"] == "STOP" and t["exit"] == pytest.approx(entry * (1 - D.STOP))
    gap = bars_from(closes + [entry, entry * 0.90, entry * 1.05], opens={261: entry * 0.91})
    g = D.trades(gap)[0][0]
    assert g["why"] == "STOP" and g["exit"] == pytest.approx(entry * 0.91)  # opened below the stop: filled there


def test_a_trade_that_never_recovers_is_closed_at_its_10th_close():
    closes = rising(260)
    dip = [closes[-1] * 0.97]
    sag = [dip[-1] * (1 - 0.004 * k) for k in range(1, 16)]  # a little lower each day: never above its 5-day mean
    t = D.trades(bars_from(closes + dip + sag))[0][0]
    assert t["why"] == "TIME" and t["days"] == D.MAX_DAYS


def test_a_later_bar_changes_nothing_before_it():
    closes = rising(260)
    seq = closes + [closes[-1] * 0.97, closes[-1] * 0.94, closes[-1] * 0.95, closes[-1] * 0.99, closes[-1] * 1.01]
    full = bars_from(seq + [seq[-1] * 1.5, seq[-1] * 0.5])
    part = full[:len(seq)]
    t_full, d_full = D.trades(full)
    t_part, d_part = D.trades(part)
    cut = part[-1][0]
    assert [t for t in t_full if t["exit_day"] <= cut] == t_part
    assert {d: v for d, v in d_full.items() if d <= cut} == d_part


def test_the_basket_gives_each_index_a_quarter_and_counts_every_trading_day():
    closes = rising(260)
    dip = [closes[-1] * 0.97]
    a = bars_from(closes + dip + [dip[-1] * 1.04] * 2)
    b = bars_from(closes + [closes[-1] * 1.001] * 4)  # no dip: never trades
    data = {"^GSPC": a, "^NDX": b, "^GDAXI": b, "^FTSE": b}
    daily, tr = D.basket(data, a[0][0], a[-1][0] + timedelta(days=1))
    _, alone = D.trades(a)
    assert len(daily) == len(a) and sum(len(v) for v in tr.values()) == 1
    for d, v in alone.items():
        assert daily[d] == pytest.approx(v / 4)


def test_the_gates_on_a_market_whose_dips_always_recover():
    closes, p = [], 100.0
    for i in range(8_600):  # 1988-06 to 2021-04
        p *= 1.004 if i % 20 != 10 else 0.96  # a 4% fall every 20 days, then the climb resumes
        closes.append(p)
    days = weekdays(len(closes), date(1988, 6, 1))
    bars = [(d, c, c, c, c) for d, c in zip(days, closes)]
    data = {s: bars for s in D.INDICES}
    res = D.gates(data, thr=3.0)
    assert res["trades"]["trades"] > 4 * 300 and res["trades"]["won"] > 0.9
    assert res["gates"]["development"] and res["gates"]["validation"] and res["gates"]["costs_x2"]
    assert res["gates"]["t"] and res["days"]["t"] > 3.0
    flat = [(d, 100.0, 100.0, 100.0, 100.0) for d in days]
    none = D.gates({s: flat for s in D.INDICES}, thr=3.0)
    assert none["trades"]["trades"] == 0 and not none["passed"]
