"""GSR-1 on prices built so the answer is known: the stretch is measured only on closes up to the day; a trade is
taken and closed at the close after its signal and pays both sides and its financing; a stretch that never comes
back is closed after a year; a ratio whose stretches revert passes, and one that keeps running fails; the judge
never reads the holdout."""

from __future__ import annotations

import hashlib
import json
import math
from datetime import date, timedelta

import pytest

import scripts.gsr1 as G


def business_days(a: date, b: date) -> list[date]:
    return [a + timedelta(days=i) for i in range((b - a).days) if (a + timedelta(days=i)).weekday() < 5]


def market(log_ratio, start=date(2000, 8, 30), end=date(2020, 1, 1)):
    """Gold fixed at 1000; silver priced so that ln(gold / silver) = log_ratio(i) on the i-th business day."""
    days = business_days(start, end)
    return {G.GOLD: {d: 1000.0 for d in days},
            G.SILVER: {d: 1000.0 / math.exp(log_ratio(i)) for i, d in enumerate(days)}}


def wiggle(i):
    return 0.002 if i % 2 else -0.002


def spikes(revert: bool):
    """Every 250 business days a stretch of 0.15 in five days, alternately up and down. With `revert` it decays back
    over the next 30 days; without, it stays, and the ratio keeps running the same way."""
    def f(i):
        k, cycle = i % 250, i // 250
        sign = 1 if cycle % 2 else -1
        if revert:
            bump = 0.0 if k < 100 else 0.03 * min(k - 99, 5) if k < 105 else max(0.0, 0.15 * (1 - (k - 104) / 30))
            return 4.0 + sign * bump + wiggle(i)
        level = 0.15 * cycle + (0.03 * min(k - 99, 5) if k >= 100 else 0.0) + (0.001 * (k - 104) if k > 104 else 0)
        return 4.0 + level + wiggle(i)
    return f


def test_the_stretch_is_measured_only_on_closes_up_to_the_day():
    data = market(spikes(True))
    days, z = G.zscores(data)
    d = days[600]
    later = {**data, G.SILVER: {k: (v / 2 if k > d else v) for k, v in data[G.SILVER].items()}}
    assert G.zscores(later)[1][d] == pytest.approx(z[d])
    assert days[G.WINDOW - 2] not in z and days[G.WINDOW - 1] in z  # a full year of closes first


def test_a_trade_is_taken_at_the_close_after_its_signal_and_pays_both_sides_and_its_financing():
    data = market(spikes(True))
    days, z = G.zscores(data)
    daily, trades = G.run(data, date(2001, 9, 1), date(2004, 1, 1))
    first = trades[0]
    i = days.index(first["entry"])
    assert abs(z[days[i - 1]]) >= G.ENTER_Z and all(abs(z.get(days[j], 0)) < G.ENTER_Z for j in range(i - 30, i - 1)
                                                    if days[j] >= date(2001, 9, 1))
    assert daily[first["entry"]] == pytest.approx(-(G.COST[G.GOLD] + G.COST[G.SILVER]))  # in: costs, no return yet
    nxt = days[i + 1]
    side = 1 if first["side"] == "against_high" else -1
    rs = data[G.SILVER][nxt] / data[G.SILVER][first["entry"]] - 1
    fin = G.PAIR_FINANCING_PA * (nxt - first["entry"]).days / 365.0
    assert daily[nxt] == pytest.approx(side * rs - fin)  # gold does not move here
    j = days.index(first["exit"])
    assert side * z[days[j - 1]] <= 0 and first["net"] > 0  # out at the close after z came back through 0


def test_a_stretch_that_never_comes_back_is_closed_after_a_year():
    data = market(lambda i: 4.0 + (0.2 if i > 400 else 0.0) + 0.0005 * max(0, i - 400) + wiggle(i))
    _, trades = G.run(data, date(2001, 9, 1), date(2005, 1, 1))
    assert trades and trades[0]["days"] == G.MAX_HELD and trades[0]["net"] < 0


def test_a_ratio_whose_stretches_revert_passes_and_one_that_keeps_running_fails():
    res = G.gates(market(spikes(True)), thr=3.0)
    assert res["passed"], res["failed_gates"]
    assert res["trades_count"]["against_high"] > 5 and res["trades_count"]["against_low"] > 5
    bad = G.gates(market(spikes(False)), thr=3.0)
    assert not bad["passed"] and bad["net"]["mean"] < 0 and "both_sides" in bad["failed_gates"]


def test_the_judge_never_reads_the_holdout(tmp_path, monkeypatch):
    monkeypatch.setattr(G, "DATA", tmp_path)
    man = {"series": {}}
    for sym in (G.GOLD, G.SILVER):
        body = "date,close\n2019-12-30,1.0\n2019-12-31,1.0\n2020-01-02,2.0\n"
        name = sym.replace("=", "_")
        (tmp_path / f"{name}.csv").write_text(body)
        man["series"][sym] = {"file": f"{name}.csv", "sha256": hashlib.sha256(body.encode()).hexdigest()}
    (tmp_path / "manifest.json").write_text(json.dumps(man))
    assert all(max(v) == date(2019, 12, 31) for v in G.load(G.JUDGE[1]).values())
    (tmp_path / "SI_F.csv").write_text("date,close\n2019-12-30,9.0\n")
    with pytest.raises(SystemExit, match="does not match its manifest"):
        G.load(G.JUDGE[1])


def test_the_threshold_counts_its_universe_and_is_never_below_3():
    class Reg:
        def tests_on(self, u, a, b):
            return {"metals-futures-daily": 0}.get(u, 0)
    assert G.threshold(Reg()) == 3.0
