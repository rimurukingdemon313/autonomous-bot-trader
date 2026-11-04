"""CONF-2 on a ledger built so the answer is known: only H1 agreements below the floor that the senior judged in
shadow count, in two groups (approved at even odds or more, and the rest); an unusable review is no unit; nothing is
judged before its date; the approved trades must pay AND beat the rest; EVALUATION waits for a QUALIFIED LEARNING
look; days that move together are not independent trades."""

from __future__ import annotations

from aitrader.memory.db import Database
from scripts.conf2 import SPEC, judge, spec_sha, status, ts, units, verdict

DAY = 86400
L0, E0 = ts("2026-11-05T00:00:00Z"), ts("2026-11-16T00:00:00Z")
L_DUE, E_DUE = ts("2026-11-20T00:00:00Z"), ts("2026-11-27T00:00:00Z")


class Ledger:
    def __init__(self, path):
        self.path, self.db, self.n = str(path), Database(path), 0

    def add(self, t, net, review=("APPROVE", 70), *, family="DUAL_AI_LOW_CONFIDENCE", tf="H1", recorded=None,
            asked=True):
        self.n += 1
        did = f"d{self.n:04d}"
        part = "EVALUATION" if E0 <= t < ts("2026-11-23T00:00:00Z") else "LEARNING"
        ss = ({"asked": True, "model": "anthropic/claude-opus-5.5", "status": "OK", "verdict": review[0],
               "confidence": review[1], "reason": "x"} if asked and review else
              {"asked": True, "model": "anthropic/claude-opus-5.5", "status": "INVALID: not json"} if asked else
              {"asked": False, "why": "today's paid budget is kept for the reviews of real trade candidates"})
        self.db.append("decisions", {"id": did, "symbol": "EURUSD", "timeframe": "H1", "decision": "NO_TRADE",
                                     "mode": "PAPER_FORWARD", "payload": {"id": did, "family": "DUAL_AI",
                                                                          "timestamp": int(t),
                                                                          "ai": {"dual_ai": {"senior_shadow": ss}}}})
        pid = f"{did}:low-confidence"
        self.db.append("forward_proposals", {"decision_id": pid, "symbol": "EURUSD", "t": int(t), "partition": part,
                                             "payload": {"family": family, "timeframe": tf, "decision_id": pid}})
        if net is not None:
            self.db.append("forward_outcomes", {"decision_id": pid, "resolved_at": int(t) + 7200, "partition": part,
                                                "ts": float(recorded if recorded is not None else t + 2 * DAY),
                                                "payload": {"status": "RESOLVED", "net_r": net}})
        return pid

    def days(self, start, n_days, per_day, net, review):
        for d in range(n_days):
            for k in range(per_day):
                self.add(start + d * DAY + 3600 * (k + 1), net(d, k), review(d, k))


def test_only_reviewed_h1_agreements_below_the_floor_count_in_two_groups(tmp_path):
    led = Ledger(tmp_path / "a.db")
    a = led.add(L0 + 3600, 0.5, ("APPROVE", 70))
    v = led.add(L0 + 3700, -0.5, ("VETO", 80))
    low = led.add(L0 + 3800, 0.4, ("APPROVE", 45))  # an approval below even odds is no approval
    led.add(L0 + 3900, 9.0, None)                      # an unusable review: no unit, never repaired
    led.add(L0 + 4000, 9.0, asked=False)               # not asked (no room today): no unit
    led.add(L0 + 4100, 9.0, family="DUAL_AI")          # at the floor: not this question
    led.add(L0 + 4200, 9.0, tf="M15")
    led.add(L0 - 3600, 9.0)                            # before the window
    led.add(L0 + 4300, 9.0, recorded=L_DUE + 1)        # recorded after the look's date
    u = units(led.path, "LEARNING")
    groups = {r["id"]: r["group"] for r in u["rows"]}
    assert groups == {a: "APPROVED", v: "REST", low: "REST"}
    assert u["without_a_usable_review"] == 2 and u["not_resolved_by_the_date"] == 1


def test_nothing_is_judged_before_its_date_and_the_status_reads_no_outcome(tmp_path):
    led = Ledger(tmp_path / "a.db")
    led.days(L0, 8, 10, lambda d, k: 0.6, lambda d, k: ("APPROVE", 70) if k % 2 else ("VETO", 70))
    assert judge(led.path, L_DUE - 1)["verdict"] == "NOT DUE"
    s = status(led.path, L_DUE - 1)["LEARNING"]
    assert (s["reviewed_so_far"], s["approved_so_far"], s["due"]) == (80, 40, False)
    assert "mean" not in str(s) and "net" not in str(s)


def picks_winners(d, k):
    """Approved trades win 2 in 3 at +1.6 R and lose 1 in 3 at -1.1 R (about +0.70 R); the rest lose about -0.30 R;
    every day a little different."""
    return (1.6 if k % 3 else -1.1) + 0.01 * d if k % 2 == 0 else -0.3 + 0.01 * d


def approve_even(d, k):
    return ("APPROVE", 75) if k % 2 == 0 else ("VETO", 75)


def test_a_judgement_that_picks_winners_on_both_looks_is_confirmed_and_evaluation_waits_for_its_date(tmp_path):
    led = Ledger(tmp_path / "a.db")
    led.days(L0, 8, 12, picks_winners, approve_even)
    led.days(E0, 5, 12, picks_winners, approve_even)
    res = judge(led.path, L_DUE)
    assert res["looks"]["LEARNING"]["verdict"] == "QUALIFIED" and res["looks"]["EVALUATION"]["verdict"] == "NOT DUE"
    res = judge(led.path, E_DUE)
    e = res["looks"]["EVALUATION"]
    assert res["verdict"] == "CONFIRMED" and e["approved"]["n"] == 30 and e["rest"]["n"] == 30 and e["gap_r"] > 0.5


def test_approvals_that_pay_but_do_not_beat_the_rest_fail(tmp_path):
    # the market paid everyone: the judgement adds nothing
    led = Ledger(tmp_path / "a.db")
    led.days(L0, 8, 12, lambda d, k: (1.6 if k % 3 else -1.1) + 0.01 * d, approve_even)
    res = judge(led.path, E_DUE)["looks"]
    assert res["LEARNING"]["approved"]["mean_r"] > 0.1 and res["LEARNING"]["verdict"] == "FAILED"
    assert res["EVALUATION"]["verdict"] == "NOT JUDGED" and "approved" not in res["EVALUATION"]


def test_one_big_day_is_not_many_independent_trades(tmp_path):
    led = Ledger(tmp_path / "a.db")
    led.days(L0, 8, 12, lambda d, k: (3.0 if d == 3 else -0.05 + 0.02 * (k % 3)) if k % 2 == 0 else -0.8,
             approve_even)
    a = judge(led.path, L_DUE)["looks"]["LEARNING"]
    assert a["approved"]["t"] >= 2.0 and a["approved"]["days_t"] < 2.0 and a["verdict"] == "FAILED"


def test_too_few_in_either_group_is_inconclusive_never_a_verdict():
    good = {"n": 29, "mean_r": 2.0, "t": 9.0, "days_mean_r": 2.0, "days_t": 9.0}
    g = {"gap_r": 2.0, "welch_t": 9.0}
    assert verdict("LEARNING", good, {**good, "n": 100}, g) == "INCONCLUSIVE"
    assert verdict("LEARNING", {**good, "n": 100}, {**good, "n": 29}, g) == "INCONCLUSIVE"
    assert verdict("EVALUATION", {**good, "n": 14}, {**good, "n": 100}, g) == "INCONCLUSIVE"


def test_the_spec_is_frozen_by_its_hash_and_each_look_is_judged_after_its_window():
    assert spec_sha(SPEC) == spec_sha(dict(SPEC))
    looks = {**SPEC["looks"], "LEARNING": {**SPEC["looks"]["LEARNING"], "min_gap_r": 0.0}}
    assert spec_sha({**SPEC, "looks": looks}) != spec_sha(SPEC)
    for w in SPEC["looks"].values():
        assert ts(w["from"]) < ts(w["to"]) < ts(w["judge_at"])
