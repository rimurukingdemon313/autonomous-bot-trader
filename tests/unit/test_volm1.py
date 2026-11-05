"""VOLM-1 on markets built so the answer is known: the month's exposure reads only the variances known at the close
before it; it is capped; entering, trading the drift back and a CFD's financing are paid; the T-bill yield is the one
last published, and a stale one is no trade; turbulence that pays less than calm passes the alpha test and
turbulence that pays in proportion to its risk does not; the judge never reads the holdout."""

from __future__ import annotations

import hashlib
import json
from datetime import date, timedelta

import pytest

import scripts.volm1 as V


def business_days(a: date, b: date) -> list[date]:
    return [a + timedelta(days=i) for i in range((b - a).days) if (a + timedelta(days=i)).weekday() < 5]


def market(mu_sd, start=date(1993, 1, 29), end=date(2022, 2, 1), rate=2.0):
    """A market whose daily return in month k is mu + sd or mu - sd on alternate days, (mu, sd) = mu_sd(k), where
    k counts months from the start; the T-bill yield is `rate` every day."""
    px, irx, p = {}, {}, 100.0
    days = business_days(start, end)
    for i, d in enumerate(days):
        if i:
            k = (d.year - start.year) * 12 + d.month - start.month
            mu, sd = mu_sd(k)
            p *= 1 + mu + (sd if i % 2 else -sd)
        px[d], irx[d] = p, rate
    return {V.MARKET: px, V.RATE: irx}


def regimes(calm, wild):
    """Three calm months, then three turbulent ones, and so on: last month's variance tells the next month's."""
    return lambda k: wild if (k // 3) % 2 else calm


def test_the_exposure_reads_only_the_variances_known_before_its_month_and_is_capped():
    data = market(regimes((0.0005, 0.005), (0.0, 0.02)))
    rows = {r["month"]: r for r in V.book(data, date(1995, 1, 1), date(1997, 1, 1))}
    ms = V.months_of(data)
    i = next(j for j, m in enumerate(ms) if m["key"] == (1996, 2))
    past = [m["RV"] for m in ms[:i]]
    assert rows[date(1996, 2, 1)]["w"] == pytest.approx(min(V.MAX_EXPOSURE, (sum(past) / len(past)) / ms[i - 1]["RV"]))
    later = {**data, V.MARKET: {d: (p * 3 if d >= date(1996, 2, 1) else p) for d, p in data[V.MARKET].items()}}
    assert V.book(later, date(1996, 2, 1), date(1996, 3, 1))[0]["w"] == rows[date(1996, 2, 1)]["w"]  # no peeking
    assert max(r["w"] for r in rows.values()) == V.MAX_EXPOSURE  # after a calm quarter, capped at 2


def test_entering_trading_the_drift_back_and_the_financing_are_paid():
    data = market(lambda k: (0.0, 0.01))
    rows = V.book(data, date(1995, 1, 1), date(1995, 4, 1))
    first, second = rows[0], rows[1]
    ms = {m["key"]: m for m in V.months_of(data)}
    m1 = ms[(1995, 1)]
    fin = V.MARKUP_PA * m1["cal"] / 365.0
    assert first["managed"] == pytest.approx(first["w"] * (m1["R"] - m1["RF"]) - first["w"] * fin
                                             - V.COST * first["w"])  # bought from flat
    assert first["market"] == pytest.approx(m1["R"] - m1["RF"] - fin)
    m2 = ms[(1995, 2)]
    drifted = first["w"] * (1 + m1["R"]) / (1 + first["w"] * m1["R"])
    fin2 = V.MARKUP_PA * m2["cal"] / 365.0
    assert second["managed"] == pytest.approx(second["w"] * (m2["R"] - m2["RF"]) - second["w"] * fin2
                                              - V.COST * abs(second["w"] - drifted))


def test_the_yield_is_the_one_last_published_and_a_stale_one_is_no_trade():
    data = market(lambda k: (0.0, 0.01))
    holiday = date(1995, 10, 9)  # Columbus Day: the stock market trades, the bond market does not
    irx = {d: v for d, v in data[V.RATE].items() if d != holiday}
    months = {m["key"]: m for m in V.months_of({**data, V.RATE: irx})}
    assert months[(1995, 10)]["RF"] is not None
    stale = {d: v for d, v in data[V.RATE].items() if not date(1995, 11, 1) <= d < date(1995, 11, 20)}
    rows = V.book({**data, V.RATE: stale}, date(1995, 9, 1), date(1996, 1, 1))
    assert date(1995, 11, 1) not in {r["month"] for r in rows}  # unknown financing: no trade, never assumed
    assert {date(1995, 10, 1), date(1995, 12, 1)} <= {r["month"] for r in rows}


def test_turbulence_that_pays_less_than_calm_passes_and_turbulence_paid_for_its_risk_does_not():
    res = V.gates(market(regimes((0.002, 0.005), (-0.0005, 0.02))), thr=3.11)  # calm pays well, turbulence loses
    assert res["passed"], res["failed_gates"]
    assert res["alpha"]["alpha"] > 0 and res["exposure"]["months_at_cap"] > 0
    fair = V.gates(market(regimes((0.0002, 0.005), (0.0032, 0.02))), thr=3.11)  # 16 times the variance, 16 times the mean
    assert not fair["passed"] and "t" in fair["failed_gates"]


def test_the_alpha_is_ols_with_white_errors():
    xs = [0.01 * ((i * 7) % 11 - 5) for i in range(60)]
    rows = [{"market": x, "managed": 0.002 + 1.5 * x + 0.001 * (1 if i % 2 else -1)} for i, x in enumerate(xs)]
    a = V.alpha(rows)
    assert a["alpha"] == pytest.approx(0.002, abs=2e-4) and a["beta"] == pytest.approx(1.5, abs=0.01)
    assert a["t"] > 10 and len(a["contributions"]) == 60


def test_the_judge_never_reads_the_holdout(tmp_path, monkeypatch):
    monkeypatch.setattr(V, "DATA", tmp_path)
    man = {"series": {}}
    for sym in (V.MARKET, V.RATE):
        body = "date,close\n2021-12-30,1.0\n2021-12-31,1.0\n2022-01-03,2.0\n"
        name = sym.lstrip("^")
        (tmp_path / f"{name}.csv").write_text(body)
        man["series"][sym] = {"file": f"{name}.csv", "sha256": hashlib.sha256(body.encode()).hexdigest()}
    (tmp_path / "manifest.json").write_text(json.dumps(man))
    assert all(max(v) == date(2021, 12, 31) for v in V.load(V.JUDGE[1]).values())
    (tmp_path / "SPY.csv").write_text("date,close\n2021-12-30,9.0\n")
    with pytest.raises(SystemExit, match="does not match its manifest"):
        V.load(V.JUDGE[1])


def test_the_threshold_counts_every_earlier_test_on_us_equity_data():
    class Reg:
        def tests_on(self, u, a, b):
            return {"multi-asset-etf": 12, "multi-asset-long": 10, "equity-index-b": 2, "us-vol-etp": 2}.get(u, 0)
    assert V.threshold(Reg()) == pytest.approx(max(3.0, V.bonferroni_t(26 + V.TESTS)))
