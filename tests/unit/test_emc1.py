"""EMC-1 on currencies built so the answer is known: the policy rate is the one in force and a stale one is unknown; the
ranking reads only the rates known at the month-end; the book earns the spot move and the differential and pays its
spreads and the markup; a month with an unknown rate is no trade; carry that holds its value passes and carry eaten by
depreciation fails; the BIS file is read by its codes; the judge never reads the holdout."""

from __future__ import annotations

import hashlib
import json
from datetime import date, timedelta

import pytest

import scripts.emc1 as E

RATES = {"US": 2.0, "MX": 7.0, "ZA": 8.0, "TR": 15.0, "PL": 4.0, "HU": 6.0, "CZ": 1.0}


def business_days(a: date, b: date) -> list[date]:
    return [a + timedelta(days=i) for i in range((b - a).days) if (a + timedelta(days=i)).weekday() < 5]


def market(drift_pa, start=date(2004, 1, 1), end=date(2020, 2, 1), rates=RATES):
    """Each currency (units per dollar) moves by drift_pa(ccy) a year plus a small fixed wiggle; the policy rates are
    constant and published every calendar day."""
    days = business_days(start, end)
    fx = {}
    for k, c in enumerate(E.CURRENCIES):
        x, rows = 10.0, {}
        for i, d in enumerate(days):
            if i:
                x *= (1 + drift_pa(c)) ** (1 / 260) * (1 + (0.002 if (i + k) % 2 else -0.002))
            rows[d] = x
        fx[c] = rows
    cal = [start + timedelta(days=i) for i in range((end - start).days)]
    return {"fx": fx, "rates": {a: [(d, v) for d in cal] for a, v in rates.items()}}


def test_the_policy_rate_is_the_one_in_force_and_a_stale_one_is_unknown():
    s = [(date(2010, 1, d), 5.0) for d in range(1, 20)] + [(date(2010, 1, 20), 6.0)]  # published daily, then stops
    assert E.rate_at(s, date(2010, 1, 19)) == 5.0 and E.rate_at(s, date(2010, 1, 20)) == 6.0
    assert E.rate_at(s, date(2010, 1, 30)) == 6.0 and E.rate_at(s, date(2010, 1, 31)) is None  # 11 days old
    assert E.rate_at(s, date(2009, 12, 31)) is None


def test_the_ranking_reads_the_rates_known_at_the_month_end_and_the_book_earns_spot_and_differential():
    data = market(lambda c: 0.0)
    rows = E.book(data, date(2006, 1, 1), date(2006, 4, 1))
    assert rows[0]["held"] == ["TRY", "ZAR", "MXN"]
    later = {**data, "rates": {**data["rates"], "PL": [(d, 4.0 if d < date(2006, 2, 15) else 30.0)
                                                     for d, _ in data["rates"]["PL"]]}}
    got = {r["month"]: r["held"] for r in E.book(later, date(2006, 1, 1), date(2006, 5, 1))}
    assert got[date(2006, 2, 1)] == ["TRY", "ZAR", "MXN"] and got[date(2006, 3, 1)][0] == "PLN"  # from the next month-end
    ends = E.month_ends(data["fx"])
    t0, t1 = [d for d in ends if d.year == 2006 and d.month in (1, 2)]
    first = rows[1]  # February 2006: entered at January's month-end (rows[0] is January, bought from flat)
    days = (t1 - t0).days
    want = sum(data["fx"][c][t0] / data["fx"][c][t1] - 1 + (RATES[E.CURRENCIES[c][1]] - 2.0) / 100 * days / 365
               for c in ("TRY", "ZAR", "MXN")) / 3
    assert first["gross"] == pytest.approx(want)
    assert rows[0]["gross"] - rows[0]["net"] == pytest.approx(
        sum(E.CURRENCIES[c][2] for c in ("TRY", "ZAR", "MXN")) / 3 + E.MARKUP_PA * 31 / 365, rel=0.05)


def test_a_month_with_an_unknown_rate_is_no_trade():
    data = market(lambda c: 0.0)
    gap = [(d, v) for d, v in data["rates"]["HU"] if not date(2007, 3, 15) <= d < date(2007, 4, 5)]
    rows = E.book({**data, "rates": {**data["rates"], "HU": gap}}, date(2007, 1, 1), date(2007, 7, 1))
    months = {r["month"] for r in rows}
    assert date(2007, 4, 1) not in months and {date(2007, 3, 1), date(2007, 5, 1)} <= months


def test_carry_that_holds_its_value_passes_and_carry_eaten_by_depreciation_fails():
    res = E.gates(market(lambda c: 0.0), thr=3.0)
    assert res["passed"], res["failed_gates"]
    assert res["months"] == 179 and res["carry_part"]["mean"] > 0
    diff = {c: (RATES[E.CURRENCIES[c][1]] - 2.0) / 100 for c in E.CURRENCIES}
    bad = E.gates(market(lambda c: diff[c] + 0.01), thr=3.0)  # each falls by its differential and 1% more a year
    assert not bad["passed"] and bad["net"]["mean"] < 0


def test_the_bis_file_is_read_by_its_codes():
    raw = ("STRUCTURE,FREQ:Frequency,REF_AREA:Reference area,TIME_PERIOD:Time period or range,"
           "OBS_VALUE:Observation Value\n"
           "dataflow,D:Daily,ZA:South Africa,2010-01-05,7\n"
           "dataflow,D:Daily,ZA:South Africa,2010-01-04,7.5\n"
           "dataflow,M:Monthly,ZA:South Africa,2010-01,7\n"
           "dataflow,D:Daily,GB:United Kingdom,2010-01-04,0.5\n"
           "dataflow,D:Daily,TR:Turkey,2010-01-04,NaN-text\n").encode()
    assert E.parse_bis(raw, ["ZA", "TR"]) == {"ZA": [("2010-01-04", 7.5), ("2010-01-05", 7.0)], "TR": []}


def test_the_judge_never_reads_the_holdout(tmp_path, monkeypatch):
    monkeypatch.setattr(E, "DATA", tmp_path)
    man = {"series": {}}
    for c in E.CURRENCIES:
        body = "date,close\n2019-12-30,1.0\n2019-12-31,1.0\n2020-01-02,2.0\n"
        (tmp_path / f"{c}.csv").write_text(body)
        man["series"][c] = {"file": f"{c}.csv", "sha256": hashlib.sha256(body.encode()).hexdigest()}
    rates = "area,date,rate\nUS,2019-12-31,1.75\nUS,2020-01-02,1.75\n"
    (tmp_path / "rates.csv").write_text(rates)
    man["rates"] = {"file": "rates.csv", "sha256": hashlib.sha256(rates.encode()).hexdigest()}
    (tmp_path / "manifest.json").write_text(json.dumps(man))
    got = E.load(E.JUDGE[1])
    assert all(max(v) == date(2019, 12, 31) for v in got["fx"].values()) and got["rates"]["US"][-1][0] == date(2019, 12, 31)
    (tmp_path / "TRY.csv").write_text("date,close\n2019-12-30,9.0\n")
    with pytest.raises(SystemExit, match="does not match its manifest"):
        E.load(E.JUDGE[1])


def test_the_threshold_is_never_below_3():
    class Reg:
        def tests_on(self, u, a, b):
            return 0
    assert E.threshold(Reg()) == 3.0
