"""CONF-1 on a ledger built so the answer is known: only H1 agreements under the floor, decided in a look's window
and resolved by its date, count; nothing is judged before its date; EVALUATION is judged only after LEARNING
qualified; days that move together are not counted as independent agreements."""

from __future__ import annotations

import pytest

from aitrader.memory.db import Database
from scripts.conf1 import SPEC, judge, spec_sha, status, ts, units, verdict

DAY = 86400
L0, E0 = ts("2026-11-02T00:00:00Z"), ts("2026-11-16T00:00:00Z")  # the LEARNING and EVALUATION windows open
L_DUE, E_DUE = ts("2026-11-20T00:00:00Z"), ts("2026-11-27T00:00:00Z")


class Ledger:
    def __init__(self, path):
        self.db, self.n = Database(path), 0

    def add(self, t, net, *, family="DUAL_AI_LOW_CONFIDENCE", tf="H1", part=None, recorded=None):
        self.n += 1
        did = f"d{self.n}:low-confidence"
        part = part or ("EVALUATION" if E0 <= t < ts("2026-11-23T00:00:00Z") else "LEARNING")
        self.db.append("forward_proposals", {"decision_id": did, "symbol": "EURUSD", "t": int(t), "partition": part,
                                             "payload": {"family": family, "timeframe": tf, "decision_id": did}})
        if net is not None:
            self.db.append("forward_outcomes", {"decision_id": did, "resolved_at": int(t) + 7200, "partition": part,
                                                "ts": float(recorded if recorded is not None else t + 2 * DAY),
                                                "payload": {"status": "RESOLVED", "net_r": net}})
        return did

    def days(self, start, n_days, per_day, net):
        for d in range(n_days):
            for k in range(per_day):
                self.add(start + d * DAY + 3600 * (k + 1), net(d, k))


def test_only_h1_agreements_under_the_floor_decided_in_the_window_and_resolved_by_its_date_count(tmp_path):
    led = Ledger(tmp_path / "a.db")
    keep = led.add(L0 + 3600, 0.5)
    led.add(L0 - 3600, 9.0)                                     # decided before the window
    led.add(L0 + 7200, 9.0, family="DUAL_AI")                   # let through by the floor: reported, never judged
    led.add(L0 + 7200, 9.0, tf="M15")                           # another chart
    led.add(L0 + 9000, 9.0, recorded=L_DUE + 1)                 # recorded after the look's date: a later database
    led.add(L0 + 9000, None)                                    # decided, not resolved
    u = units(str(tmp_path / "a.db"), "LEARNING")
    assert [r["id"] for r in u["rows"]] == [keep] and u["decided"] == 3 and u["not_resolved_by_the_date"] == 2


def test_nothing_is_judged_before_its_date_and_the_status_reads_no_outcome(tmp_path):
    led = Ledger(tmp_path / "a.db")
    led.days(L0, 10, 12, lambda d, k: 0.6)
    path = str(tmp_path / "a.db")
    assert judge(path, L_DUE - 1)["verdict"] == "NOT DUE"
    s = status(path, L_DUE - 1)
    assert s["LEARNING"]["decided_so_far"] == 120 and not s["LEARNING"]["due"]
    assert "mean" not in str(s) and "net" not in str(s)  # blind: counts and dates only


def winning_weeks(led, start, n_days, per_day):
    # 2 of every 3 agreements gain 1.6 R, 1 loses 1.1 R: about +0.70 R each, every day a little different
    led.days(start, n_days, per_day, lambda d, k: (1.6 if k % 3 else -1.1) + 0.01 * d)


def test_a_rule_that_pays_on_both_looks_is_confirmed_and_evaluation_waits_for_its_own_date(tmp_path):
    led = Ledger(tmp_path / "a.db")
    winning_weeks(led, L0, 10, 12)
    winning_weeks(led, E0, 5, 12)
    path = str(tmp_path / "a.db")
    res = judge(path, L_DUE)
    assert res["looks"]["LEARNING"]["verdict"] == "QUALIFIED" and res["looks"]["EVALUATION"]["verdict"] == "NOT DUE"
    res = judge(path, E_DUE)
    assert res["verdict"] == "CONFIRMED" and res["looks"]["EVALUATION"]["under_the_floor"]["n"] == 60


def test_when_learning_does_not_qualify_evaluation_is_never_judged(tmp_path):
    led = Ledger(tmp_path / "a.db")
    led.days(L0, 10, 12, lambda d, k: 0.5 if k % 2 else -1.0)  # -0.25 R each
    winning_weeks(led, E0, 5, 12)
    res = judge(str(tmp_path / "a.db"), E_DUE)
    assert res["verdict"] == "FAILED" and res["looks"]["EVALUATION"]["verdict"] == "NOT JUDGED"
    assert "under_the_floor" not in res["looks"]["EVALUATION"]  # not looked at


def test_one_big_day_is_not_ten_independent_agreements(tmp_path):
    # every agreement of one day moves together: 9 days lose a little, 1 day of several pairs at once wins big
    led = Ledger(tmp_path / "a.db")
    led.days(L0, 10, 12, lambda d, k: 3.0 if d == 4 else -0.05 + 0.02 * (k % 3))
    res = judge(str(tmp_path / "a.db"), L_DUE)["looks"]["LEARNING"]
    s = res["under_the_floor"]
    assert s["mean_r"] >= 0.10 and s["t"] >= 2.0  # counted per agreement it would pass
    assert s["days_t"] < 2.0 and res["verdict"] == "FAILED"  # counted per day it does not


def test_too_few_agreements_is_inconclusive_never_a_verdict():
    s = {"n": 99, "mean_r": 2.0, "t": 9.0, "days_mean_r": 2.0, "days_t": 9.0}
    assert verdict("LEARNING", s) == "INCONCLUSIVE"
    assert verdict("EVALUATION", {**s, "n": 49}) == "INCONCLUSIVE"


def test_the_spec_is_frozen_by_its_hash():
    assert spec_sha(SPEC) == spec_sha(dict(SPEC))
    assert spec_sha({**SPEC, "looks": {**SPEC["looks"], "LEARNING": {**SPEC["looks"]["LEARNING"], "min_t": 1.0}}}) \
        != spec_sha(SPEC)


@pytest.mark.parametrize("look", ["LEARNING", "EVALUATION"])
def test_each_look_is_judged_after_its_window_closes(look):
    w = SPEC["looks"][look]
    assert ts(w["from"]) < ts(w["to"]) < ts(w["judge_at"])
