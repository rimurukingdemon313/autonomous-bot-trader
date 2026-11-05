"""VRP-1 on prices built so the answer is known: the day's exposure reads the VIX term structure of the close BEFORE the
one it is entered at; contango is short and an inverted curve is flat; entering, resizing and borrowing are paid; a
curve that inverts before the spikes pays the rule against the always-held short, and one that does not fails it; the
judge never reads the holdout's prices."""

from __future__ import annotations

import hashlib
import json
from datetime import date, timedelta

import pytest

import scripts.vrp1 as V


def trading_days(a: date, b: date) -> list[date]:
    return [a + timedelta(days=i) for i in range((b - a).days) if (a + timedelta(days=i)).weekday() < 5]


def market(days, etp_ret, ratio):
    """VIXY moved by etp_ret(i) each day; VIX3M fixed at 20 and the VIX at 20 x ratio(i)."""
    etp, vix, v3, c = {}, {}, {}, 20.0
    for i, d in enumerate(days):
        c *= 1 + etp_ret(i)
        etp[d], vix[d], v3[d] = c, 20.0 * ratio(i), 20.0
    return {V.ETP: etp, V.VIX: vix, V.VIX3M: v3}


def test_the_exposure_reads_the_curve_of_the_close_before_the_one_it_is_entered_at():
    days = trading_days(date(2015, 1, 5), date(2015, 3, 2))
    m = market(days, lambda i: -0.01, lambda i: 0.8)
    d, p, pp = days[20], days[19], days[18]
    assert V.book(m, d, d + timedelta(days=1))[d]["exp"] == 1.0  # contango two closes back: short over (p, d]
    late = {**m, V.VIX: {**m[V.VIX], p: 40.0}}  # inverted at p's close: published after p's 16:00, never read for d
    assert V.book(late, d, d + timedelta(days=1))[d]["exp"] == 1.0
    early = {**m, V.VIX: {**m[V.VIX], pp: 40.0}}
    assert V.book(early, d, d + timedelta(days=1))[d]["exp"] == 0.0
    missing = {**m, V.VIX3M: {k: v for k, v in m[V.VIX3M].items() if k != pp}}
    assert d not in V.book(missing, d, d + timedelta(days=1))  # no signal: no trade, never filled


def test_entering_resizing_and_borrowing_are_paid():
    days = trading_days(date(2015, 1, 5), date(2015, 3, 2))
    m = market(days, lambda i: -0.01, lambda i: 0.8)
    b = V.book(m, days[10], days[13])
    first, second = b[days[10]], b[days[11]]
    assert first["net"] == pytest.approx(0.01 - V.COST * (1 + 0.01) - V.BORROW_PA / 252, rel=1e-6)  # enter + resize
    assert second["net"] == pytest.approx(0.01 - V.COST * 0.01 - V.BORROW_PA / 252, rel=1e-6)       # resize only


def cycles(warns: bool):
    """100 calm days (VIXY -0.3% a day, curve in contango at 0.85), then 10 days of stress: the curve inverts (1.2)
    from the stress's first day, and VIXY spikes +4% a day from its third day. With warns=False the curve stays in
    contango through the spike and inverts only on calm days, at random-like places: it tells nothing."""
    def ret(i):
        k = i % 110
        return 0.04 if 102 <= k < 110 else -0.003

    def ratio(i):
        k = i % 110
        if warns:
            return 1.2 if k >= 100 else 0.85
        return 1.2 if k % 7 == 3 and k < 100 else 0.85
    return market(trading_days(date(2010, 12, 1), date(2022, 1, 1)), ret, ratio)


def test_a_curve_that_inverts_before_the_spikes_pays_the_rule_against_the_always_held_short():
    res = V.gates(cycles(warns=True), thr=3.0)
    assert res["passed"], res["failed_gates"]
    assert res["timing"]["mean"] > 0 and res["max_drawdown"] > res["reported_always_short"]["max_drawdown"]


def test_a_curve_that_tells_nothing_fails_the_timing_gate():
    res = V.gates(cycles(warns=False), thr=3.0)
    assert not res["passed"] and "timing" in res["failed_gates"]


def test_the_judge_never_reads_the_holdouts_prices(tmp_path, monkeypatch):
    monkeypatch.setattr(V, "DATA", tmp_path)
    man = {"series": {}}
    for sym in (V.ETP, V.VIX, V.VIX3M):
        body = "date,close\n2021-12-30,1.0\n2021-12-31,1.0\n2022-01-03,2.0\n"
        name = sym.lstrip("^")
        (tmp_path / f"{name}.csv").write_text(body)
        man["series"][sym] = {"file": f"{name}.csv", "sha256": hashlib.sha256(body.encode()).hexdigest()}
    (tmp_path / "manifest.json").write_text(json.dumps(man))
    got = V.load(V.JUDGE[1])
    assert all(max(v) == date(2021, 12, 31) for v in got.values())  # cut at the holdout
    (tmp_path / "VIXY.csv").write_text("date,close\n2021-12-30,9.0\n")  # a file that is not the one fetched
    with pytest.raises(SystemExit, match="does not match its manifest"):
        V.load(V.JUDGE[1])
