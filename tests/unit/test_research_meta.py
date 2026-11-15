"""The collective reading of the record (scripts/research_meta.py) on ledgers built so each figure is known."""

from __future__ import annotations

import json
import math
from pathlib import Path

import pytest

import scripts.research_meta as M

ROOT = Path(__file__).resolve().parents[2]


def rule(i, fit_t, check_t, cls="NEGATIVE_EXPECTANCY", gross_over_net=1.0, hold=3.0, family="own-lag", n=400, mean=None, plan=None):
    mean = mean if mean is not None else check_t * 1e-4
    return {"run": "DLAB-CRD-1", "id": f"r{i}", "class": cls, "family": family, "reason": "", "fit": {"t": fit_t},
            "check": {"t": check_t, "mean": mean, "gross_mean": mean * gross_over_net, "n": n, "mean_hold": hold}, "plan": plan}


def test_the_t_before_costs_keeps_the_spread_and_changes_the_mean():
    r = rule(0, 2.0, -1.0, mean=-2e-4)
    r["check"]["gross_mean"] = 3e-4  # positive before costs, negative after
    assert M.gross_t(r) == pytest.approx(1.5)
    assert M.gross_t({"check": {"t": 1.0, "mean": 0.0, "gross_mean": 1e-4}}) is None  # no mean to scale from: not invented
    assert M.gross_t({"check": {"t": None, "mean": 1e-4, "gross_mean": 1e-4}}) is None


def test_strength_that_carries_over_shows_as_a_correlation_and_strength_that_does_not_shows_as_none():
    carried = M.panel([rule(i, 1.0 + 0.1 * i, -1.0 + 0.1 * i) for i in range(40)])
    assert carried["fit_check_correlation"] == pytest.approx(1.0) and carried["fit_check_rank_correlation"] == pytest.approx(1.0)
    assert [q["rules"] for q in carried["by_fit_strength"]] == [11, 10, 10, 9]
    assert carried["by_fit_strength"][0]["mean_check_t"] < carried["by_fit_strength"][-1]["mean_check_t"]
    # the check t alternates whatever the fit t was: nothing carries
    flat = M.panel([rule(i, 1.0 + 0.1 * i, (-1.0, 1.0)[i % 2]) for i in range(40)])
    assert abs(flat["fit_check_correlation"]) < 0.1 and flat["correlation_standard_error"] == pytest.approx(1 / math.sqrt(37), abs=1e-3)
    assert flat["positive_after_costs"] == 0.5 and flat["check_t_centre"] == 0.0


def test_rules_that_only_costs_stopped_are_counted_apart():
    rows = [rule(i, 2.0, -1.0, gross_over_net=-0.5, hold=1.0) for i in range(6)]       # positive before costs, lost after
    rows += [rule(10 + i, 2.0, -1.0, gross_over_net=0.5, hold=1.0) for i in range(4)]  # lost before costs too
    rows += [rule(20 + i, 2.0, 1.0, cls="INSUFFICIENT_POWER", hold=20.0) for i in range(5)]
    p = M.panel(rows)
    assert p["lost"] == 10 and p["lost_only_after_costs"] == 6
    fast = next(h for h in p["by_holding_time"] if h["held"] == "under 2 rows")
    slow = next(h for h in p["by_holding_time"] if h["held"] == "15 rows or more")
    assert fast["rules"] == 10 and fast["positive_after_costs"] == 0 and slow["rules"] == 5 and slow["positive_after_costs"] == 1
    fam = p["by_family"][0]
    assert fam["rules"] == 15 and fam["positive_after_costs"] == 5 and fam["positive_before_costs_only"] == 6


def test_a_rule_without_a_recorded_holding_time_is_in_no_holding_bucket():
    p = M.panel([rule(i, 2.0, 0.5 - 0.1 * i, hold=None) for i in range(12)])
    assert p["by_holding_time"] == [] and p["with_fit_and_check"] == 12


def test_what_survives_selection_is_the_spread_beyond_a_t_statistics_own():
    """A population of t centred at -0.5 with a spread of 2: three quarters of a rule's distance from the centre is
    real (1 - 1/4). Its positive members average well above zero on the rows they were chosen on, and less after."""
    ts = [-0.5 + 2.0 * z for z in (-1.5, -1.2, -0.9, -0.6, -0.3, 0.0, 0.3, 0.6, 0.9, 1.2, 1.5)] * 4
    sd = M._sd(ts)
    rows = [rule(i, 2.0, t, cls="INSUFFICIENT_POWER" if t > 0 else "NEGATIVE_EXPECTANCY", family=f"f{i % 4}") for i, t in enumerate(ts)]
    p = M.panel(rows)
    w = p["weak_positives"]
    keep = 1 - 1 / sd ** 2
    assert w["share_of_the_distance_that_survives_selection"] == pytest.approx(keep, abs=0.01)
    chosen = [t for t in ts if t > 0]
    assert w["rules"] == len(chosen) and w["mean_check_t"] == pytest.approx(sum(chosen) / len(chosen), abs=0.01)
    expected = -0.5 + keep * (sum(chosen) / len(chosen) + 0.5)
    assert w["expected_t_of_a_member_on_new_rows"] == pytest.approx(expected, abs=0.02) and 0 < expected < sum(chosen) / len(chosen)
    assert w["aggregate_expected_t_on_new_rows"] < w["aggregate_t_on_the_rows_it_was_chosen_on"]
    # pure noise (a spread of one or less): nothing survives, and the aggregate is expected at the population's centre
    noise = M.panel([rule(i, 2.0, -0.5 + 0.9 * z, cls="INSUFFICIENT_POWER" if -0.5 + 0.9 * z > 0 else "NEGATIVE_EXPECTANCY")
                     for i, z in enumerate((-1.5, -1.0, -0.5, 0.0, 0.5, 1.0, 1.5) * 5)])
    assert noise["weak_positives"]["share_of_the_distance_that_survives_selection"] == 0
    assert noise["weak_positives"]["expected_t_of_a_member_on_new_rows"] == pytest.approx(-0.5, abs=0.01)
    assert noise["weak_positives"]["aggregate_expected_t_on_new_rows"] < 0 and noise["weak_positives"]["chance_to_reach_3"] < 0.001


def test_the_plans_say_how_long_the_weak_positives_would_have_to_wait():
    rows = [rule(i, 2.0, 1.0, cls="INSUFFICIENT_POWER", plan={"more_discovery_years": y}) for i, y in enumerate((0.4, 2.0, 2.5, 40.0, 90.0))]
    rows += [rule(9, 2.0, -1.0)]
    w = M.panel(rows)["weak_positives"]
    assert (w["plans"], w["told_from_noise_within_one_more_year"], w["within_three"], w["median_more_years_needed"]) == (5, 1, 3, 2.5)


def test_a_closed_family_is_named_from_the_triages_reason():
    assert M._closed("it behaves as cross-coin momentum (the 7-day winners against the losers: XSM-1) (correlation 0.73), judged and closed") == "XSM-1"
    assert M._closed("it behaves as single-coin momentum (hold SOLUSDT while its 28-day return is positive: XTS-1) (correlation 0.71)") == "XTS-1"
    assert M._closed("something the triage has no name for") == "other"


def test_the_registry_and_the_edges_are_counted_from_the_files(tmp_path):
    r = tmp_path / "research"
    (r / "knowledge").mkdir(parents=True)
    (r / "dlab").mkdir()
    lines = [{"kind": "trial", "id": "A-1", "tests": 3, "uses": [{"universe": "u1"}, {"universe": "u1"}]},
             {"kind": "trial", "id": "B-1", "tests": 1, "uses": [{"universe": "u1"}, {"universe": "u2"}]},
             {"kind": "trial", "id": "C-1", "tests": 2, "uses": [{"universe": "u2"}]},
             {"kind": "verdict", "trial": "A-1", "status": "FAILED"}, {"kind": "verdict", "trial": "B-1", "status": "PASSED"}]
    (r / "registry.jsonl").write_text("\n".join(json.dumps(x) for x in lines) + "\n")
    edges = [{"edge_id": "E1", "status": "REJECTED", "failed_checks": ["development:t_day", "years"], "net_expectancy": -0.1, "t_stat": -1.0},
             {"edge_id": "E2", "status": "REJECTED", "failed_checks": ["t"], "net_expectancy": 0.05, "t_stat": 2.4},
             {"edge_id": "E3", "status": "PROMISING", "failed_checks": ["t"], "t_stat": 2.7, "t_required": 3.6, "program": "P"},
             {"edge_id": "E4", "status": "VALIDATED", "failed_checks": [], "t_stat": 3.8, "t_required": 3.4}]
    (r / "knowledge" / "edge_registry.json").write_text(json.dumps({"edges": edges, "counts": {"REJECTED": 2, "PROMISING": 1, "VALIDATED": 1, "RETIRED": 0}}))
    (r / "dlab" / "candidates.jsonl").write_text("\n".join(json.dumps(rule(i, 2.0, 0.1 * i - 1)) for i in range(20)) + "\n")
    m = M.build(tmp_path)
    g, e = m["registry"], m["edges"]
    assert (g["trials"], g["verdicts"], g["tests"]) == (3, 2, 6) and g["status"] == {"FAILED": 1, "PASSED": 1, "PENDING": 1}
    assert g["universes"]["u1"] == {"trials": 2, "tests": 4, "failed": 1, "passed": 1, "pending": 0}
    assert g["universes"]["u2"] == {"trials": 2, "tests": 3, "failed": 0, "passed": 1, "pending": 1} and g["pending"] == ["C-1"]
    assert e["rejected"] == 2 and dict(e["failed_checks"]) == {"t_day": 1, "years": 1, "t": 1}
    assert e["rejected_on_one_gate"] == 1 and e["of_them_on_the_bar"] == 1 and e["rejected_with_a_negative_mean"] == 1
    assert e["rejected_t_above_2"] == 1 and [x["edge"] for x in e["near_misses"]] == ["E3"] and [x["edge"] for x in e["validated"]] == ["E4"]
    assert m["rules"] == 20 and m["panels"]["perpetuals (55 Binance contracts by day)"]["rules"] == 20
    text = M.render(m, __import__("datetime").datetime(2026, 11, 15, tzinfo=__import__("datetime").timezone.utc))
    assert "3 registered hypotheses with 6 counted tests" in text and "| `u1` | 2 | 4 | 1 | 1 | 0 |" in text and "| E3 | 2.70 | 3.60 |" in text


def test_the_committed_document_is_what_the_script_computes_while_the_record_has_not_moved():
    """The lab's worker adds to the record by itself. When it has, this document is behind and says its own date; when
    it has not, every computed figure in it must be the script's."""
    committed = json.loads((ROOT / "research" / "META_ANALYSIS.json").read_text())
    now = M.build()
    if (now["rules"], now["registry"]["trials"], now["registry"]["verdicts"], now["edges"]["edges"]) != (
            committed["rules"], committed["registry"]["trials"], committed["registry"]["verdicts"], committed["edges"]["edges"]):
        pytest.skip("the record has moved since the document was written")
    assert json.loads(json.dumps(now)) == committed
    doc = (ROOT / "docs" / "RESEARCH_META_ANALYSIS.md").read_text()
    assert "## 5. The director's reading" in doc and f"- {now['rules']} rules found in data" in doc
