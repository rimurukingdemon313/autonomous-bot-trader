"""The discovery lab on markets built so the answer is known: each method finds the structure planted for it, a market
with nothing in it yields nothing promising, every emitted rule is classed with a reason and kept, and the validation
rows are out of discovery's reach."""

from __future__ import annotations

import json
from datetime import date, datetime, timezone

import numpy as np
import pytest

import scripts.dlab as L
from aitrader.research.dlab import datasets as D
from aitrader.research.dlab import methods as M
from aitrader.research.dlab import signals as S
from aitrader.research.dlab import triage as T
from aitrader.research.dlab.panel import Panel, key

FIT, CHECK = 2500, 2000


def market(plant=None, seed=11, rows=FIT + CHECK):
    p = D.synthetic(rows=rows, seed=seed, plant=plant)
    fit = np.zeros(p.T, dtype=bool)
    fit[:FIT] = True
    return p, fit


def ctx_of(plant=None, seed=11):
    p, fit = market(plant, seed)
    return M.Context(p, fit), p, fit


# ── each method finds what was planted for it ───────────────────────────────

def test_lead_lag_finds_the_planted_link_its_direction_and_that_the_reverse_is_absent():
    ctx, p, fit = ctx_of({"leadlag": 0.12})
    top = M.leadlag(ctx)[0]
    assert top.family == "cross-asset lead-lag" and top.spec["target"] == "A1" and top.spec["feat"] == {"f": "ret", "a": "A0", "k": 1}
    assert top.spec["side"] == 1 and top.detail["t_given_own_past_and_market"] > 3.0
    assert abs(top.detail["t_reverse_direction"]) < 3.0 and ctx.scanned["leadlag"] == 3 * 3 * 5
    flat, _, _ = ctx_of(None)
    assert max(e.fit for e in M.leadlag(flat)) < 3.5  # nothing planted: no link that strong


def test_information_sees_a_dependence_a_linear_correlation_cannot():
    ctx, p, fit = ctx_of({"ushape": 0.3})
    emitted, audit = M.info(ctx)
    rows = {r["feature"]: r for r in audit["A1"]["best"]}
    assert audit["A1"]["best"][0]["feature"] == "absret(A0)"  # the size of A0's move: the planted cause, found first
    raw = rows["ret(A0,1)"]  # A0's signed move carries the same information, and no linear trace of it
    assert raw["z"] >= 3.0 and abs(raw["t_linear"]) < 2.0 and audit["A1"]["non_linear_only"] >= 1
    assert any(e.spec["target"] == "A1" and e.spec["kind"] == "table" for e in emitted)
    r = S.pnl(next(e.spec for e in emitted if e.spec["target"] == "A1" and e.spec["feats"][0]["f"] == "absret"), p)
    assert S.stats(r["net"], ~fit, p.ppy)["t"] > 2.0  # and the table rule it emits earns on rows it never saw


def test_mutual_information_is_exact_on_a_known_table_and_zero_given_the_common_cause():
    a = np.array([0, 0, 1, 1] * 500)
    assert M.mi(a, a, 2, 2) == pytest.approx(np.log(2), abs=2e-3)  # a series tells everything about itself: ln 2
    rng = np.random.default_rng(0)
    b = rng.integers(0, 2, size=2000)
    assert abs(M.mi(a, b, 2, 2)) < 2e-3  # independent: nothing, once the small-sample bias is removed
    o = rng.integers(0, 2, size=4000)
    x, y = (o + (rng.random(4000) < 0.2)) % 2, (o + (rng.random(4000) < 0.2)) % 2
    assert M.mi(x, y, 2, 2) > 0.05 and abs(M.cmi(x, y, o, 2, 2, 2)) < 5e-3  # linked only through o


def test_ordinal_regime_and_anomaly_methods_each_find_their_planted_structure():
    ctx, p, fit = ctx_of({"regime": 0.10})
    reg = [e for e in M.regimes(ctx) if e.spec["target"] == "A1"]
    top = reg[0]  # the planted state is one series among eight: its own two regimes are the strongest rule
    assert top.spec["feats"] == [{"f": "aux", "name": "state"}] and top.detail["mean_run_rows"] > 3
    assert S.stats(S.pnl(top.spec, p)["net"], ~fit, p.ppy)["t"] > 2.0
    ctx, p, fit = ctx_of({"shock": 0.8})
    an = [e for e in M.anomaly(ctx) if e.spec["target"] == "A1"]
    assert an and an[0].spec["mode"] == "rev"
    ctx, p, fit = ctx_of({"leadlag": 0.12})
    assert all(e.spec["kind"] == "ordinal" and any(e.spec["map"]) for e in M.ordinal(ctx))


def test_k_means_separates_two_clouds():
    rng = np.random.default_rng(1)
    x = np.vstack([rng.normal(-3, 0.5, (200, 2)), rng.normal(3, 0.5, (200, 2))])
    cen, lab = M.kmeans(x, 2, rng)
    assert len(set(lab[:200])) == 1 and len(set(lab[200:])) == 1 and lab[0] != lab[-1]
    assert sorted(np.round(cen[:, 0]).tolist()) == [-3.0, 3.0]


def test_the_evolutionary_search_is_reproducible_bounded_and_finds_the_planted_rule():
    ctx, p, fit = ctx_of({"leadlag": 0.12})
    a = M.evolve(ctx, pop=80, gens=10)
    b = M.evolve(M.Context(p, fit), pop=80, gens=10)
    assert [key(e.spec) for e in a] == [key(e.spec) for e in b] and 0 < len(a) <= ctx.top
    top = a[0].spec
    assert top["target"] == "A1" and "ret" in json.dumps(top["node"]) and '"a": "A0"' in json.dumps(top["node"])
    for e in a:  # every rule kept is in position between 2% and 50% of the fit rows
        share = (S.positions(e.spec, p)[fit] != 0).mean()
        assert 0.015 <= share <= 0.55


def test_no_method_reads_a_row_after_the_fit_rows():
    """The firewall inside discovery: rewrite every return after the fit rows; the emitted rules must not change."""
    ctx, p, fit = ctx_of({"leadlag": 0.08}, seed=5)
    first, _ = M.discover(ctx)
    r = p.ret.copy()
    r[FIT + 1:] = np.random.default_rng(9).normal(0, 0.05, size=r[FIT + 1:].shape)
    aux = {k: np.concatenate([v[:FIT + 1], np.random.default_rng(8).normal(0, 3, size=len(v) - FIT - 1)]) for k, v in p.aux.items()}
    other = Panel(p.name, p.times, p.assets, r, aux, dict(p.cost), p.ppy)
    second, _ = M.discover(M.Context(other, fit))
    assert [key(e.spec) for e in first] == [key(e.spec) for e in second] and len(first) > 50


def test_combinations_join_different_families_only_and_a_book_spans_instruments():
    ctx, p, fit = ctx_of({"leadlag": 0.12})
    emitted, _ = M.discover(ctx)
    combos = [e for e in emitted if e.family == "combination"]
    assert combos and all(len(set(e.detail["families"])) == len(e.detail["families"]) for e in combos)
    books = [e for e in emitted if e.family == "pooled book"]
    assert books and all(len({x["target"] for x in e.spec["parts"]}) == len(e.spec["parts"]) >= 2 for e in books)
    assert {e.family for e in emitted} >= {"cross-asset lead-lag", "information (non-linear)", "ordinal pattern", "anomaly", "evolved rule"}


# ── triage: every rule classed, with its reason ─────────────────────────────

def emit(spec, family="cross-asset lead-lag", method="test"):
    return M.Emit(spec, family, method, 1.0, "built for the test")


def test_each_class_is_given_for_its_own_reason():
    p, fit = market({"leadlag": 0.14})
    lead = {"kind": "sign", "target": "A1", "feat": {"f": "ret", "a": "A0", "k": 1}, "w": 250, "band": 0.5, "side": 1}
    twin = {**lead, "band": 0.6}
    S.KINDS["leak"] = lambda p_, s: np.nan_to_num(np.sign(p_.fwd()[:, p_.col(s["target"])]))
    flip = {"kind": "sign", "target": "A0", "feat": {"f": "ret", "a": "A2", "k": 1}, "w": 250, "band": 0.0, "side": 1}
    rare = {"kind": "tree", "target": "A2", "side": 1, "hold": 1,
            "node": {"feat": {"f": "ret", "a": "A2", "k": 20}, "w": 250, "op": ">", "q": 0.998}}
    closed = [("an earlier family", {"kind": "level", "target": "A2", "feat": {"f": "aux", "name": "state"}, "op": ">", "x": 0.0, "side": 1})]
    weak = {"kind": "sign", "target": "A2", "feat": {"f": "ret", "a": "A0", "k": 20}, "w": 250, "band": 1.0, "side": 1}
    try:
        res = T.triage([emit(lead), emit(twin), emit({"kind": "leak", "target": "A1"}),
                        emit({"kind": "const", "target": "A0", "side": 1}), emit(flip), emit(rare), emit(closed[0][1]),
                        emit({**lead, "side": -1}), emit(weak)],
                       p, fit, ~fit, n_val=3000, bar=3.0, closed=closed, hint="more instruments")
    finally:
        del S.KINDS["leak"]
    by = {r["id"]: r for r in res["records"]}
    cls = lambda s: by[S.spec_id(s)]["class"]  # noqa: E731
    assert cls(lead) == "PROMISING_UNCONFIRMED" and by[S.spec_id(lead)]["in_batch"] and res["batch"] == [S.spec_id(lead)]
    assert cls(twin) == "DUPLICATE" and by[S.spec_id(twin)]["duplicate_of"] == S.spec_id(lead)
    assert cls({"kind": "leak", "target": "A1"}) == "SCIENTIFICALLY_INVALID" and "future" in by[S.spec_id({"kind": "leak", "target": "A1"})]["reason"]
    assert cls({"kind": "const", "target": "A0", "side": 1}) == "SCIENTIFICALLY_INVALID"  # the instrument's own return
    assert cls(rare) == "INSUFFICIENT_DATA" and cls(closed[0][1]) == "REPEATS_CLOSED_FAMILY"
    assert cls({**lead, "side": -1}) in ("NEGATIVE_EXPECTANCY", "OVERFIT")  # the mirror of a real effect loses
    assert all(r["class"] in T.CLASSES and r["reason"] for r in res["records"])
    w = by[S.spec_id(weak)]
    if w["class"] == "INSUFFICIENT_POWER":  # a positive but weak rule is given a plan, not dropped
        assert w["plan"]["ways"] and "independent_instruments_needed" in w["plan"] and w["plan"]["more_data"] == "more instruments"


def test_a_rule_that_only_pays_before_costs_is_said_to_be_killed_by_costs():
    p, fit = market({"leadlag": 0.06})
    dear = Panel(p.name, p.times, p.assets, p.ret, dict(p.aux), {a: 0.003 for a in p.assets}, p.ppy)
    lead = {"kind": "sign", "target": "A1", "feat": {"f": "ret", "a": "A0", "k": 1}, "w": 250, "band": 0.0, "side": 1}
    r = T.triage([emit(lead)], dear, fit, ~fit, n_val=3000, bar=3.0)["records"][0]
    assert r["class"] == "NEGATIVE_EXPECTANCY" and "before costs" in r["reason"] and r["check"]["gross_mean"] > 0 > r["check"]["mean"]


def test_the_chance_of_being_real_counts_every_distinct_look():
    lone = T.chances([4.0] + [0.0] * 5, 0.0, 1.0, tested=100)
    assert lone[0] > 0.99  # one strong rule among a hundred looks stays real
    best_of_noise = T.chances([2.4, 2.0, 1.8], 0.0, 1.0, tested=100)
    assert best_of_noise[0] < 0.3  # the best of a hundred noise rules does not
    assert T.chances([3.0, 3.0, 3.0], 0.0, 1.0, tested=100)[2] > T.chances([3.0], 0.0, 1.0, tested=100)[0]  # several agree
    a, b = np.array([1.0, -1.0, 2.0, 0.5] * 50), np.array([0.3, 0.1, -0.2, 0.9] * 50)
    assert T.distinct(["x", "y", "z", "m"], {"x": a, "y": a * 1.01, "z": b, "m": -a}) == 2  # a twin and a mirror: one look
    assert T.noise([3.0] * 20) == (0.0, 1.0) and T.noise([-0.5] * 20) == (-0.5, 1.0)  # real clusters do not move it up
    wide = T.noise([-3.0, -2.0, -1.0, 0.0, 0.0, 0.1, 0.2, 5.0, 6.0, 7.0])  # the spread comes from below the median only
    assert wide[0] == 0.0 and wide[1] == pytest.approx(np.sqrt(np.mean(np.array([3.05, 2.05, 1.05, 0.05, 0.05]) ** 2)))


def test_a_market_with_nothing_rarely_promotes_and_never_validates_and_a_planted_edge_is_found_and_validated():
    promoted_runs = promoted = 0
    for seed in (3, 4, 5, 6):
        full = D.synthetic(rows=FIT + CHECK + 3000, seed=seed)
        head = full.head(FIT + CHECK)
        fit = np.zeros(head.T, dtype=bool)
        fit[:FIT] = True
        emitted, _ = M.discover(M.Context(head, fit))
        res = T.triage(emitted, head, fit, ~fit, n_val=3000, bar=3.0)
        assert len(res["records"]) > 80 and T.summary(res["records"])["rules"] == len(res["records"])
        promoted_runs, promoted = promoted_runs + bool(res["batch"]), promoted + len(res["batch"])
        by = {r["id"]: r for r in res["records"]}
        vmask = np.zeros(full.T, dtype=bool)
        vmask[FIT + CHECK:] = True
        for i in res["batch"]:  # discovery may be fooled now and then; validation is what must not be
            assert not L.judge_rule(by[i]["spec"], full, vmask, 3.0, 5, L.mean_hold(by[i]) >= L.SLOW_ROWS)["passed"]
    assert promoted_runs <= 2 and promoted <= 3
    full = D.synthetic(rows=FIT + CHECK + 3000, seed=100, plant={"leadlag": 0.12})
    head = full.head(FIT + CHECK)
    fit = np.zeros(head.T, dtype=bool)
    fit[:FIT] = True
    emitted, _ = M.discover(M.Context(head, fit))
    res = T.triage(emitted, head, fit, ~fit, n_val=3000, bar=3.0)
    by = {r["id"]: r for r in res["records"]}
    assert res["batch"] and all("A1" in by[i]["targets"] for i in res["batch"][:1])
    vmask = np.zeros(full.T, dtype=bool)
    vmask[FIT + CHECK:] = True
    judged = [L.judge_rule(by[i]["spec"], full, vmask, 3.0, 5, L.mean_hold(by[i]) >= L.SLOW_ROWS) for i in res["batch"]]
    assert any(j["passed"] for j in judged) and all(2990 <= j["rows"] <= 3000 for j in judged)
    assert len({r["family"] for r in res["records"]}) >= 7 and res["noise"]["distinct_behaviours"] <= res["noise"]["rules"]


# ── validation's gates, and the firewall around the validation rows ─────────

def test_a_judged_rule_must_beat_its_own_positions_shifted_in_time():
    full = D.synthetic(rows=4000, seed=7, plant={"leadlag": 0.14})
    v = np.zeros(full.T, dtype=bool)
    v[1000:] = True
    lead = {"kind": "sign", "target": "A1", "feat": {"f": "ret", "a": "A0", "k": 1}, "w": 250, "band": 0.5, "side": 1}
    good = L.judge_rule(lead, full, v, 3.0, 5, delay_gate=False)
    assert good["passed"] and good["random"]["share_at_least_as_good"] < 0.01 and "one_row_late" not in good["gates"]
    assert good["bootstrap_95"][0] > 0 and good["worst_fall_pct"] > 0 and good["entries_a_year"] > 20
    slow = L.judge_rule(lead, full, v, 3.0, 5, delay_gate=True)
    assert "one_row_late" in slow["gates"] and abs(slow["one_row_late_mean"]) < 0.25 * slow["mean"]  # gone a row late
    drift = L.judge_rule({"kind": "const", "target": "A1", "side": 1}, full, v, 3.0, 5, delay_gate=False)
    assert not drift["gates"]["beats_random"]  # always long has no timing to beat


def test_the_scan_refuses_a_panel_that_holds_validation_rows(monkeypatch):
    w = {"fit": (date(2000, 1, 3), date(2008, 1, 1)), "check": (date(2008, 1, 1), date(2012, 1, 1)),
         "validation": (date(2012, 1, 1), date(2015, 1, 1))}
    monkeypatch.setitem(D.WINDOWS, "synthetic", w)
    monkeypatch.setitem(L.DATASETS, "syn", ("synthetic", lambda last: None, 5))
    p = D.synthetic(rows=3400, seed=1)  # runs past 2012-01-01
    with pytest.raises(SystemExit, match="validation rows"):
        L.scan("syn", 7, None, panel=p)
    ok = p.head(int(p.rows(date(2000, 1, 1), date(2012, 1, 1)).sum()))
    res = L.scan("syn", 7, None, panel=ok)
    assert res["rows"]["check"] > 900 and res["bar_on_validation"] == 3.0 and res["summary"]["rules"] == len(res["records"])
    assert set(res["summary"]["by_class"]) <= set(T.CLASSES)


def test_the_candidate_ledger_keeps_every_rule_and_records_a_run_once(tmp_path):
    p, fit = market(None, 3)
    emitted, _ = M.discover(M.Context(p, fit))
    res = T.triage(emitted, p, fit, ~fit, n_val=3000, bar=3.0)
    led = tmp_path / "dlab" / "candidates.jsonl"
    n = T.append(led, "RUN-1", res["records"], "2026-11-10T00:00:00+00:00", "dlab-test")
    rows = [json.loads(x) for x in led.read_text().splitlines()]
    assert n == len(rows) == len(res["records"]) and all(r["run"] == "RUN-1" and r["class"] and r["reason"] and r["spec"] for r in rows)
    with pytest.raises(SystemExit, match="recorded once"):
        T.append(led, "RUN-1", res["records"], "2026-11-10T00:00:00+00:00", "dlab-test")
    T.append(led, "RUN-2", res["records"][:3], "2026-11-11T00:00:00+00:00", "dlab-test")
    assert len(led.read_text().splitlines()) == n + 3


def test_the_validation_bar_counts_every_test_on_the_window_and_never_falls_below_three(tmp_path):
    from aitrader.research.registry import Holdout, Registry, Trial, Use
    hold = tmp_path / "holdout.json"
    hold.write_text(json.dumps({"universe": "fx-majors", "start": "2017-01-01", "sealed_at": "2026-09-26T20:28:47+00:00",
                                "rationale": "test"}))
    reg = Registry.load(tmp_path / "registry.jsonl", Holdout.load(hold))
    w = (date(2012, 1, 1), date(2024, 1, 1))
    assert L.bar_for(reg, "u", w, 12) == 3.0
    reg.register(Trial(id="BIG", registered=datetime(2026, 1, 1, tzinfo=timezone.utc), title="t", hypothesis="h",
                       uses=(Use("u", date(2013, 1, 1), date(2014, 1, 1), "judge"),), tests=200, configurations=200))
    assert L.bar_for(reg, "u", w, 12) > 3.6  # 212 tests on the window
    assert L.bar_for(reg, "u", (date(2000, 1, 1), date(2010, 1, 1)), 12) == 3.0  # none of them on this other window
