"""SEC-1 on funds built so the answer is known: the ranking reads only the closes up to the month-end it is made at;
every trade pays, the month's drift included; a fund without its closes is no trade for the month; sectors whose
lead persists pass and sectors whose lead reverses fail; the period's last month counts; the judge never reads the
holdout."""

from __future__ import annotations

import hashlib
import json
from datetime import date, timedelta

import pytest

import scripts.sec1 as S


def business_days(a: date, b: date) -> list[date]:
    return [a + timedelta(days=i) for i in range((b - a).days) if (a + timedelta(days=i)).weekday() < 5]


def market(monthly_ret, start=date(1998, 12, 22), end=date(2018, 1, 1)):
    """Each fund moves by monthly_ret(fund index, month count) spread evenly over the month's trading days."""
    days = business_days(start, end)
    per_month: dict = {}
    for d in days:
        per_month.setdefault((d.year, d.month), []).append(d)
    data = {s: {} for s in S.SECTORS}
    for i, s in enumerate(S.SECTORS):
        p = 100.0
        for k, (ym, ds) in enumerate(sorted(per_month.items())):
            step = (1 + monthly_ret(i, k)) ** (1 / len(ds))
            for d in ds:
                p *= step
                data[s][d] = p
    return data


def persists(i, k):
    """Three sectors lead for a year at a time (+3% a month against +0.5%), then the next three."""
    lead = {(k // 12) % 3 * 3 + j for j in range(3)}
    return 0.03 if i in lead else 0.005


def reverses(i, k):
    """Last month's leaders fall behind: a fund's month alternates between +3% and -1%, half of them in phase."""
    return 0.03 if (k + i) % 2 else -0.01


def test_the_ranking_reads_only_the_closes_up_to_its_month_end():
    data = market(persists)
    rows = {r["month"]: r for r in S.book(data, date(2005, 1, 1), date(2005, 3, 1))}
    later = {s: {d: (p * (3.0 if s == "XLU" and d >= date(2005, 2, 1) else 1.0)) for d, p in v.items()}
             for s, v in data.items()}
    assert S.book(later, date(2005, 2, 1), date(2005, 3, 1))[0]["held"] == rows[date(2005, 2, 1)]["held"]


def test_every_trade_pays_and_the_drift_is_traded_back():
    data = market(lambda i, k: 0.01 * (1 + i))  # the same three lead every month
    rows = S.book(data, date(2000, 1, 1), date(2000, 4, 1))
    assert rows[0]["held"] == rows[1]["held"] == ["XLY", "XLV", "XLU"]
    assert rows[0]["book"]["gross"] - rows[0]["book"]["net"] == pytest.approx(S.COST * 1.0)  # bought from cash
    assert rows[1]["book"]["gross"] - rows[1]["book"]["net"] < S.COST * 0.05  # only the drift traded back


def test_a_fund_without_its_closes_is_no_trade_for_the_month():
    data = market(persists)
    gone = date(2003, 6, 30)
    data["XLE"] = {d: p for d, p in data["XLE"].items() if d != gone}  # June 2003's month-end close missing
    months = {r["month"] for r in S.book(data, date(2003, 1, 1), date(2004, 1, 1))}
    assert date(2003, 6, 1) not in months and date(2003, 7, 1) not in months  # it ends one month and starts the next
    assert date(2003, 8, 1) in months


def test_sectors_whose_lead_persists_pass_and_sectors_whose_lead_reverses_fail():
    res = S.gates(market(persists), thr=3.12)
    assert res["passed"], res["failed_gates"]
    assert res["months"] == 216  # 2000-01..2017-12, the last month included
    bad = S.gates(market(reverses), thr=3.12)
    assert not bad["passed"] and bad["difference"]["mean"] < 0


def test_the_judge_never_reads_the_holdout(tmp_path, monkeypatch):
    monkeypatch.setattr(S, "DATA", tmp_path)
    man = {"series": {}}
    for sym in S.SECTORS:
        body = "date,close\n2017-12-28,1.0\n2017-12-29,1.0\n2018-01-02,2.0\n"
        (tmp_path / f"{sym}.csv").write_text(body)
        man["series"][sym] = {"file": f"{sym}.csv", "sha256": hashlib.sha256(body.encode()).hexdigest()}
    (tmp_path / "manifest.json").write_text(json.dumps(man))
    assert all(max(v) == date(2017, 12, 29) for v in S.load(S.JUDGE[1]).values())
    (tmp_path / "XLK.csv").write_text("date,close\n2017-12-28,9.0\n")
    with pytest.raises(SystemExit, match="does not match its manifest"):
        S.load(S.JUDGE[1])


def test_the_threshold_counts_every_earlier_test_on_us_equity_data():
    class Reg:
        def tests_on(self, u, a, b):
            return {"multi-asset-etf": 12, "multi-asset-long": 10, "equity-index-b": 2, "us-vol-etp": 2,
                    "us-equity-etf": 1}.get(u, 0)
    assert S.threshold(Reg()) == pytest.approx(max(3.0, S.bonferroni_t(27 + S.TESTS)))
