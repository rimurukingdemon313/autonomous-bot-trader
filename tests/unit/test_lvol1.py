"""LVOL-1 on funds built so the answer is known: funds that move less than the market for the same return pass the
alpha test, and funds that only scale the market fail; each fund must carry the alpha on its own; a month without a
known T-bill yield is no trade; the judge never reads the holdout."""

from __future__ import annotations

import hashlib
import json
import random
from datetime import date, timedelta

import pytest

import scripts.lvol1 as L


def business_days(a: date, b: date) -> list[date]:
    return [a + timedelta(days=i) for i in range((b - a).days) if (a + timedelta(days=i)).weekday() < 5]


def market(alpha_daily: dict, beta=0.6, start=date(2011, 6, 1), end=date(2021, 2, 1)):
    """SPY moves on a fixed pseudo-random path; each low-volatility fund moves beta times SPY plus its own daily alpha
    and a little noise of its own. The T-bill yield is 1% every day."""
    rng = random.Random(7)
    days = business_days(start, end)
    px = {s: {} for s in (*L.LOW_VOL, L.MARKET)}
    p = {s: 100.0 for s in px}
    for i, d in enumerate(days):
        if i:
            m = 0.0004 + rng.gauss(0, 0.01)
            p[L.MARKET] *= 1 + m
            for s in L.LOW_VOL:
                p[s] *= 1 + beta * m + alpha_daily[s] + rng.gauss(0, 0.002)
        for s in px:
            px[s][d] = p[s]
    return {**px, L.RATE: {d: 1.0 for d in days}}


def test_funds_that_move_less_for_the_same_return_pass_and_funds_that_only_scale_the_market_fail():
    res = L.gates(market({"SPLV": 0.0003, "USMV": 0.0003}), thr=3.15)
    assert res["passed"], res["failed_gates"]
    assert res["months"] == 108 and res["alpha"]["beta"] == pytest.approx(0.6, abs=0.05)
    flat = L.gates(market({"SPLV": 0.0, "USMV": 0.0}), thr=3.15)
    assert not flat["passed"] and "t" in flat["failed_gates"]


def test_each_fund_must_carry_the_alpha_on_its_own():
    res = L.gates(market({"SPLV": 0.0006, "USMV": -0.0002}), thr=1.0)
    assert res["alpha"]["alpha"] > 0 and res["each_fund"]["USMV"]["alpha"] < 0
    assert "each_fund" in res["failed_gates"]


def test_a_month_without_a_known_yield_is_no_trade():
    data = market({"SPLV": 0.0, "USMV": 0.0})
    data[L.RATE] = {d: v for d, v in data[L.RATE].items() if not date(2014, 2, 20) <= d < date(2014, 3, 10)}
    months = {r["month"] for r in L.book(data, date(2014, 1, 1), date(2014, 6, 1))}
    assert date(2014, 3, 1) not in months and {date(2014, 2, 1), date(2014, 4, 1)} <= months


def test_the_judge_never_reads_the_holdout(tmp_path, monkeypatch):
    monkeypatch.setattr(L, "DATA", tmp_path)
    man = {"series": {}}
    for sym in (*L.LOW_VOL, L.MARKET, L.RATE):
        body = "date,close\n2020-12-30,1.0\n2020-12-31,1.0\n2021-01-04,2.0\n"
        name = sym.lstrip("^")
        (tmp_path / f"{name}.csv").write_text(body)
        man["series"][sym] = {"file": f"{name}.csv", "sha256": hashlib.sha256(body.encode()).hexdigest()}
    (tmp_path / "manifest.json").write_text(json.dumps(man))
    assert all(max(v) == date(2020, 12, 31) for v in L.load(L.JUDGE[1]).values())
    (tmp_path / "USMV.csv").write_text("date,close\n2020-12-30,9.0\n")
    with pytest.raises(SystemExit, match="does not match its manifest"):
        L.load(L.JUDGE[1])


def test_the_threshold_counts_every_earlier_test_on_us_equity_data():
    class Reg:
        def tests_on(self, u, a, b):
            return {"multi-asset-etf": 12, "multi-asset-long": 10, "equity-index-b": 2, "us-vol-etp": 2,
                    "us-equity-etf": 4}.get(u, 0)
    assert L.threshold(Reg()) == pytest.approx(max(3.0, L.bonferroni_t(30 + L.TESTS)))
