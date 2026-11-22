"""The edge registry says what the evidence says: statuses from verdicts, gaps as None, a fixed lifecycle."""

import json
from pathlib import Path

import pytest

from aitrader.research.discovery.edges import (STATUSES, TransitionError, _single, build, from_confirmatory,
                                               from_single,
                                               from_walk_forward, transition)

ROOT = Path(__file__).resolve().parents[2]


def _judged(hid, side, mean, t, validated=False):
    return {"id": hid, "side": side, "condition": "r120=low&er120=high", "exit": "D4", "kind": "opportunity",
            "battery": {"failed": [] if validated else ["significance"],
                        "checks": {"significance": {"mean_R": mean, "t": t, "threshold": 3.1},
                                   "min_trades": {"n": 300}, "costs_stress": {"mean_R": mean - 0.05},
                                   "years": {"by_year": {"2014": 0.3, "2015": -0.1}}}}}


def test_only_a_validated_verdict_makes_a_validated_edge_and_missing_numbers_stay_none():
    art = {"program": "X-1", "validated": ["X-1-B"],
           "judged": [_judged("X-1-A", "SELL", 0.19, 1.0), _judged("X-1-B", "BUY", 0.3, 3.5, validated=True)]}
    a, b = from_confirmatory(art, {"X-1-A": {"timeframe": "D1", "instruments": ["EURUSD"]}})
    assert (a.status, a.direction, a.timeframe, a.instrument) == ("REJECTED", "SELL", "D1", ("EURUSD",))
    assert b.status == "VALIDATED" and b.timeframe is None  # unknown is None, not a guess
    assert a.gross_expectancy is None and a.profit_factor is None and a.drawdown is None
    assert a.complexity == 2 and a.failed_checks == ("significance",)
    assert a.cost_sensitivity == pytest.approx(0.14)


def test_a_failed_walk_forward_is_rejected_with_the_checks_it_failed():
    res = {"trial": "WF-9", "verdict": "FAIL", "threshold_t": 3.2,
           "spec": {"sides": [1, -1], "symbols": ["EURUSD"], "timeframe": "M15", "model": "stumps",
                    "features": ["r1", "r6"], "threshold_r": 0.0, "template": "T2"},
           "system": {"n": 500, "mean_R": -0.05, "t": -1.1},
           "folds": [{"start": "2011-01-01", "mean_R": -0.05}],
           "checks": {"min_trades": True, "beats_random": False}}
    e = from_walk_forward(res)
    assert (e.status, e.direction, e.timeframe, e.walk_forward_expectancy) == ("REJECTED", "BOTH", "M15", -0.05)
    assert e.failed_checks == ("beats_random",) and e.cost_sensitivity is None


def test_the_lifecycle_is_fixed_and_rejected_or_retired_is_final():
    art = {"program": "X-2", "validated": ["X-2-A"], "judged": [_judged("X-2-A", "BUY", 0.3, 3.5, True),
                                                                 _judged("X-2-B", "BUY", 0.0, 0.1)]}
    ok, bad = from_confirmatory(art)
    degraded = transition(ok, "DEGRADED")
    assert transition(degraded, "VALIDATED").status == "VALIDATED"  # decay that reverses is variance
    retired = transition(degraded, "RETIRED")
    for dead in (bad, retired):
        for s in STATUSES:
            with pytest.raises(TransitionError):
                transition(dead, s)
    with pytest.raises(TransitionError):
        transition(bad, "VALIDATED")  # a rejected idea never becomes validated in place


def test_promising_is_a_near_miss_with_real_evidence_and_never_validated():
    def judged(hid, mean, t, costs_ok, random_ok):
        c = _judged(hid, "BUY", mean, t)
        c["battery"]["checks"]["costs_stress"]["pass"] = costs_ok
        c["battery"]["checks"]["beats_random"] = {"pass": random_ok}
        return c
    art = {"program": "X-3", "validated": [], "judged": [
        judged("P", 0.2, 2.4, True, True), judged("Q", 0.2, 1.9, True, True), judged("S", 0.2, 2.4, False, True),
        judged("U", 0.2, 2.4, True, False), judged("V", -0.2, -2.4, True, True)]}
    got = {e.edge_id: e.status for e in from_confirmatory(art)}
    assert got == {"P": "PROMISING", "Q": "REJECTED", "S": "REJECTED", "U": "REJECTED", "V": "REJECTED"}
    p = next(e for e in from_confirmatory(art) if e.edge_id == "P")
    assert transition(p, "TESTING").status == "TESTING"  # the next step is a fresh test, not a trade
    with pytest.raises(TransitionError):
        transition(p, "DEGRADED")


def test_the_committed_registry_matches_the_committed_evidence():
    reg = build(ROOT / "research")
    ids = {e["edge_id"] for e in reg["edges"]}
    assert {"CP-001-T1", "SL-002-01", "WF-002"} <= ids
    for e in reg["edges"]:
        assert e["status"] in STATUSES
        for k in ("size", "lots", "risk_pct", "risk_amount"):
            assert k not in e
    # VALIDATED only where a committed, opened holdout says so; a program verdict alone never suffices
    # ...and (edges-1.9.0, takeover audit) only with a holdout t >= 2.5: a sign alone validates nothing
    holdouts = {}
    for f in (ROOT / "research" / "knowledge").glob("*.json"):
        art = json.loads(f.read_text())
        if isinstance(art, dict) and art.get("holdout_of"):
            if isinstance(art.get("classification"), str):  # a single program's holdout: one verdict, its own t
                if art["classification"] == "VALIDATED":
                    holdouts[art["holdout_of"]] = (art.get("months") or {}).get("t")
                continue
            holdouts.update({h: ((art.get("results") or {}).get(h) or {}).get("net", {}).get("t")
                             for h, v in art.get("classification", {}).items() if v == "VALIDATED"})
    validated = {e["edge_id"] for e in reg["edges"] if e["status"] == "VALIDATED"}
    assert validated == {h for h, t in holdouts.items() if t is not None and t >= 2.5}
    # TRND-1 (holdout t 2.74) is the only one; DIV2-H1-TSMOM12 (holdout t 0.263) is REJECTED
    assert reg["counts"]["VALIDATED"] == len(validated) == 1 and validated == {"TRND-1"}
    trnd = next(e for e in reg["edges"] if e["edge_id"] == "TRND-1")
    assert trnd["t_stat"] >= trnd["t_required"] and trnd["out_of_sample_expectancy"] > 0
    div = next(e for e in reg["edges"] if e["edge_id"] == "DIV2-H1-TSMOM12")
    assert div["status"] == "REJECTED" and any("holdout" in c for c in div["failed_checks"])
    passed = {k for k, p in reg["programs"].items() if p["verdict"] == "PASSED"}
    assert passed <= {"DIV-2", "TRND-1", "SCX-1"}
    # SCX-1 passed its development stage on 2026-11-22 (t 3.02 at 10 bp) and its validation SCX-1-V then FAILED
    # (t -0.25): a stage pass that did not hold is REJECTED, with the failed stage named (edges-1.13.0)
    scx = {e["edge_id"]: e for e in reg["edges"] if str(e.get("program", "")).startswith("SCX-1")}
    assert {k: e["status"] for k, e in scx.items()} == {"SCX-1@0.001": "REJECTED", "SCX-1@0.0003": "REJECTED",
                                                        "SCX-1-V@0.001": "REJECTED"}
    assert "later stage SCX-1-V FAILED" in scx["SCX-1@0.001"]["failed_checks"]
    assert all(p["verdict"] in ("FAILED", "FAIL", "PASSED") or p["verdict"].startswith("BLOCKED")
               for p in reg["programs"].values())
    vix = next((e for e in reg["edges"] if e["edge_id"] == "R4-XA-VIX-A"), None)
    if vix is not None:  # a recorded correction is carried into the registry, never silently applied
        assert vix["note"] and "registered population" in vix["note"] and vix["status"] == "REJECTED"
    committed = ROOT / "research" / "knowledge" / "edge_registry.json"
    assert json.loads(committed.read_text())["counts"] == reg["counts"]


def test_a_single_program_is_validated_only_by_its_own_holdout_at_t_2_5():
    art = {"program": "X-9", "verdict": "PASSED", "gates": {"t": True}, "failed_gates": [], "threshold_t": 3.2,
           "months": {"n": 700, "mean": 0.005, "t": 3.5}}
    assert _single(art) and from_single(art, None).status == "TESTING"  # judged; its holdout is not opened
    hold = {"program": "X-9-H", "holdout_of": "X-9", "verdict": "PASSED", "gates": {}, "failed_gates": [],
            "classification": "VALIDATED", "months": {"n": 69, "mean": 0.007, "t": 2.6}}
    rec = from_single(art, hold)
    assert rec.status == "VALIDATED" and rec.t_stat == 3.5 and rec.t_required == 3.2
    assert rec.out_of_sample_expectancy == 0.007 and rec.direction is None  # the artifact does not record the side
    weak = from_single(art, {**hold, "months": {"n": 69, "mean": 0.007, "t": 2.4}})  # a sign alone validates nothing
    assert weak.status == "REJECTED" and any("holdout" in c for c in weak.failed_checks)
    assert from_single(art, {**hold, "classification": "REJECTED"}).status == "REJECTED"
    lost = {**art, "verdict": "FAILED", "failed_gates": ["t"], "months": {"n": 700, "mean": 0.001, "t": 1.3}}
    assert from_single(lost, None).status == "REJECTED"  # below t 2: not a near miss
    other = from_single({"program": "Y-1", "verdict": "FAILED", "gates": {"t": False}, "failed_gates": ["t"],
                         "events": {"n": 140, "mean": 0.001, "t": 1.0}}, None)
    assert other.t_stat is None and other.net_expectancy is None  # not a monthly statistic: nothing is guessed
    assert not any(_single({**art, k: v}) for k, v in (("judged", []), ("kind", "trend"), ("stage", 1),
                                                        ("verdict", "PROMOTED")))


def test_a_single_program_that_failed_on_the_bar_alone_is_a_near_miss_not_a_rejection():
    from aitrader.research.discovery.edges import judged_t
    base = {"program": "N-1", "verdict": "FAILED", "gates": {"t": False, "costs_x2": True}, "failed_gates": ["t"],
            "threshold_t": 3.39, "days": {"n": 8004, "mean": 7e-5, "t": 2.48}}
    rec = from_single(base, None)
    assert rec.status == "PROMISING" and "near miss" in rec.note and "2.48" in rec.note and "3.39" in rec.note
    assert "Not validated" in rec.note and rec.failed_checks == ("t",)
    assert rec.t_stat is None  # the monthly field stays empty for a daily statistic: nothing is guessed
    assert judged_t(base) == ("days", 2.48) and judged_t({"program": "Z"}) == (None, None)
    # another preregistered gate failed too: a failure, however high its t
    assert from_single({**base, "failed_gates": ["t", "top_year"]}, None).status == "REJECTED"
    assert from_single({**base, "failed_gates": ["costs_x2"]}, None).status == "REJECTED"
    # the bar alone, but its own t is below 2
    assert from_single({**base, "days": {"n": 8004, "mean": 1e-5, "t": 1.27}}, None).status == "REJECTED"
    # no statistic recorded where one is looked for: nothing is assumed
    assert from_single({k: v for k, v in base.items() if k != "days"}, None).status == "REJECTED"
    assert from_single({**base, "days": {"t": True}}, None).status == "REJECTED"


def test_on_the_committed_record_the_three_near_misses_are_promising_and_nothing_else_changed():
    reg = build(ROOT / "research")
    status = {e["edge_id"]: e["status"] for e in reg["edges"]}
    assert {k for k in ("DAY-1", "FXT-1", "TME-1") if status.get(k) == "PROMISING"} == {"DAY-1", "FXT-1", "TME-1"}
    assert status["VOLM-1"] == "REJECTED"  # the bar alone, but t 1.27
    assert status["ENG-1"] == "REJECTED" and status["XTS-1"] == "REJECTED"  # a second gate failed
    assert [k for k, v in status.items() if v == "VALIDATED"] == ["TRND-1"]


def test_an_intraday_gate_stored_as_the_string_false_is_a_failed_check():
    """numpy booleans reach the artifact JSON as "True"/"False"; "False" is truthy and must still fail."""
    from aitrader.research.discovery import edges as E
    art = {"program": "ID-X", "t_required_validation": 3.5,
           "development": {"M-x": {"summary": {"trades": 400, "net_r": 0.05, "gross_r": 0.15, "t_day": 1.5,
                                               "profit_factor": 1.1, "max_drawdown_pct": 10.0},
                                   "detail": {"by_symbol": {"EURUSD": {}}, "by_year": {}},
                                   "gates": {"net_r": True, "symbols_positive": "False", "t_day": False,
                                             "min_trades": "True"},
                                   "vs_matched_random_welch_t": 5.0}}}
    rec = E.from_intraday(art)[0]
    assert rec.status == "REJECTED"
    assert set(rec.failed_checks) == {"development:symbols_positive", "development:t_day"}


def test_an_artifact_without_a_list_of_judged_hypotheses_is_not_read_as_edges(tmp_path):
    """RADX-1 (a diagnosis of a paper ledger) keeps the hour it was judged under `judged`: it is no set of edges, and
    it must not stop the registry from building."""
    k = tmp_path / "knowledge"
    k.mkdir()
    (tmp_path / "discovery").mkdir()
    (tmp_path / "discovery" / "ledger.jsonl").write_text("")
    (k / "DIAG-1.json").write_text(json.dumps({"program": "DIAG-1", "kind": "diagnosis", "judged": "2026-11-14T19:19:22+00:00",
                                               "verdict": "FAILED"}))
    (k / "NULL-1.json").write_text(json.dumps({"program": "NULL-1", "judged": None}))
    reg = build(tmp_path)
    assert reg["edges"] == [] and reg["programs"] == {}
    committed = build(ROOT / "research")
    assert "RADX-1" not in committed["programs"] and not any(e["edge_id"].startswith("RADX") for e in committed["edges"])
    assert json.loads((ROOT / "research" / "knowledge" / "RADX-1.json").read_text())["kind"] == "diagnosis"


def test_an_event_study_is_one_record_per_judged_threshold_and_never_validated_by_one_stage():
    """edges-1.12.0: every threshold an event study judged was a counted test, so each is a record; too few entries
    is UNCERTAIN, never a rejection or a pass; a failure on the bar alone with t >= 2 is a near miss."""
    from aitrader.research.discovery.edges import from_event_study
    g = {"t": True, "costs_x2": True, "halves": True}
    art = {"program": "EV-1", "kind": "spot_event_study", "stage": "dev", "bar": 3.0, "verdict": "FAILED",
           "spec": {"instrument": "spot, bought outright"},
           "results": {"0.1": {"verdict": "FAILED", "t": -1.2, "mean_excess": -0.01, "traded": 400,
                               "gates": {**g, "t": False, "halves": "False"}, "costs_x2_mean": -0.02},
                       "0.2": {"verdict": "INCONCLUSIVE", "t": 0.4, "mean_excess": 0.002, "traded": 90,
                               "why": "90 entries in 20 weeks: 300 and 52 are needed"},
                       "0.3": {"verdict": "FAILED", "t": 2.4, "mean_excess": 0.004, "traded": 500, "gates": {**g, "t": False}},
                       "0.4": {"verdict": "PASSED", "t": 3.4, "mean_excess": 0.006, "traded": 600, "gates": g,
                               "by_year_sum": {"2024": 1.0}},
                       "0.5": {"verdict": "FAILED", "t": 2.6, "mean_excess": 0.005, "traded": 500,
                               "gates": {**g, "t": False, "halves": False}}}}
    recs = {r.edge_id: r for r in from_event_study(art)}
    assert set(recs) == {"EV-1@0.1", "EV-1@0.2", "EV-1@0.3", "EV-1@0.4", "EV-1@0.5"}
    assert recs["EV-1@0.5"].status == "REJECTED"  # t 2.6 but a second gate failed: not a near miss
    assert recs["EV-1@0.1"].status == "REJECTED" and set(recs["EV-1@0.1"].failed_checks) == {"t", "halves"}
    assert recs["EV-1@0.2"].status == "UNCERTAIN" and "inconclusive" in recs["EV-1@0.2"].failed_checks[0]
    assert recs["EV-1@0.3"].status == "PROMISING" and recs["EV-1@0.4"].status == "TESTING"
    assert all(r.direction == "BUY" and r.t_required == 3.0 and r.status != "VALIDATED" for r in recs.values())
    assert recs["EV-1@0.4"].stability == {"by_year": {"2024": 1.0}} and recs["EV-1@0.1"].cost_sensitivity == -0.02
    one = from_event_study({"program": "EV-2", "kind": "event_study", "verdict": "FAILED", "spec": {},
                            "result": {"verdict": "FAILED", "t": 0.1, "mean_cohort_x": -0.001, "events": 812,
                                       "gates": {"t": False}, "bar": 3.0}})
    assert [(r.edge_id, r.status, r.direction, r.sample_size) for r in one] == [("EV-2", "REJECTED", None, 812)]


def test_on_the_committed_record_the_event_studies_are_judged_edges():
    reg = build(ROOT / "research")
    status = {e["edge_id"]: e["status"] for e in reg["edges"]}
    assert status["NEWL-1"] == "REJECTED" and status["EXF-1@0.0005"] == "REJECTED"
    assert status["SQZ-1@0.001"] == "UNCERTAIN" and status["CASC-1@0.08"] == "REJECTED"
    assert {k for k in status if k.split("@")[0] in ("NEWL-1", "EXF-1", "SQZ-1", "CASC-1", "BAS-1")} and \
        all(v != "VALIDATED" for k, v in status.items() if k.split("@")[0] in ("NEWL-1", "EXF-1", "SQZ-1", "CASC-1", "BAS-1"))
    assert reg["programs"]["BAS-1"]["judged"] == 3 and reg["version"] == "edges-1.13.0"


def test_a_stage_pass_whose_later_stage_failed_is_rejected_and_only_on_the_threshold_it_judged():
    from aitrader.research.discovery.edges import after_later_stages, from_event_study, later_stage_failures

    def art(pid, stage, verdict, results):
        return {"program": pid, "stage": stage, "kind": "spot_event_study", "verdict": verdict, "bar": 3.0,
                "spec": {"instrument": "spot"}, "results": results}
    ok = {"verdict": "PASSED", "t": 3.2, "mean_net": 0.01, "gates": {"t": True}}
    bad = {"verdict": "FAILED", "t": -0.3, "mean_net": -0.001, "gates": {"t": False}}
    dev = art("Q-1", "dev", "PASSED", {"0.05": ok, "0.1": {**ok, "t": 3.1}})
    for later, want in ((art("Q-1-V", "validation", "FAILED", {"0.05": bad}), {"Q-1@0.05": "REJECTED", "Q-1@0.1": "TESTING"}),
                        (art("Q-1-V", "validation", "PASSED", {"0.05": ok}), {"Q-1@0.05": "TESTING", "Q-1@0.1": "TESTING"}),
                        (None, {"Q-1@0.05": "TESTING", "Q-1@0.1": "TESTING"})):
        arts = {"Q-1": dev, **({"Q-1-V": later} if later else {})}
        fails = later_stage_failures(arts)
        got = {r.edge_id: after_later_stages(r, fails).status for r in from_event_study(dev)}
        assert got == want
    # a validation pass whose forward stage failed is rejected in turn, and the development pass with it
    arts = {"Q-1": dev, "Q-1-V": art("Q-1-V", "validation", "PASSED", {"0.05": ok}),
            "Q-1-F": art("Q-1-F", "forward", "FAILED", {"0.05": bad})}
    fails = later_stage_failures(arts)
    assert after_later_stages(from_event_study(arts["Q-1-V"])[0], fails).status == "REJECTED"
    assert {r.edge_id: after_later_stages(r, fails).status for r in from_event_study(dev)}["Q-1@0.05"] == "REJECTED"
