"""Directed tests: a hypothesis submitted as rules goes through the same registration, the same look at the check rows
and the same triage as a scan's rules. Built markets, so each answer is known by construction: a planted rule is found
and validated, a rule that is noise is not, and what cannot be tested is refused before any test is charged."""

from __future__ import annotations

import copy
import json
from datetime import date, datetime, timedelta, timezone

import numpy as np
import pytest

import scripts.dlab as L
from aitrader.research.dlab import coverage as V
from aitrader.research.dlab import datasets as D
from aitrader.research.dlab import methods as M
from aitrader.research.dlab import signals as S
from aitrader.research.dlab import triage as T
from aitrader.research.registry import Holdout, Registry

NOW = datetime(2026, 11, 13, 12, 0, tzinfo=timezone.utc)
W = {"fit": (date(2000, 1, 3), date(2009, 8, 1)), "check": (date(2009, 8, 1), date(2017, 4, 1)),
     "validation": (date(2017, 4, 1), date(2026, 1, 1))}
PLANTED = {"kind": "sign", "target": "A1", "feat": {"f": "ret", "a": "A0", "k": 1}, "w": 250, "band": 0.5, "side": 1}
NOISE = {"kind": "sign", "target": "A2", "feat": {"f": "ret", "a": "A2", "k": 5}, "w": 250, "band": 0.5, "side": 1}
TREND = {"kind": "level", "target": "A0", "feat": {"f": "ret", "a": "A0", "k": 252}, "op": ">", "x": 0.0, "side": 1}


def submission(rules: list[dict], sid: str = "D-2026-11-13-leadlag", **more) -> dict:
    return {"id": sid, "submitted": "2026-11-13", "dataset": "syn",
            "author": {"role": "director", "model": "test-model", "interface": "a test"},
            "title": "A0's move leads A1's next row", "parents": ["DLAB-SYN-1"],
            "hypothesis": "A1's next row moves with the sign of A0's last move, beyond half a standard deviation.",
            "mechanism": "A1 is slower to take in what moves A0: a lead-lag between two related instruments.",
            "why_now": "The scan looked at pairs one at a time; this states the link directly.",
            "refuted_by": "A check-row mean that is not positive in both halves.", "rules": rules, **more}


def rule(spec: dict, **more) -> dict:
    return {"family": "cross-asset lead-lag", "why": "the link stated as one rule", "spec": spec, **more}


@pytest.fixture
def lab(tmp_path, monkeypatch):
    r = tmp_path / "research"
    (r / "specs").mkdir(parents=True)
    (r / "preregistrations").mkdir()
    (r / "holdout.json").write_text(json.dumps({"universe": "fx-majors", "start": "2017-01-01", "rationale": "test",
                                                "sealed_at": "2026-09-26T20:28:47+00:00"}))
    for name, val in (("ROOT", tmp_path), ("R", r), ("OUT", r / "knowledge"), ("LEDGER", r / "dlab" / "candidates.jsonl")):
        monkeypatch.setattr(L, name, val)
    monkeypatch.setattr(L, "code_hash", lambda: "c" * 64)
    full = D.synthetic(rows=7500, seed=100, plant={"leadlag": 0.12})
    loads = []

    def loader(last):
        loads.append(last)
        return full.head(sum(t < last for t in full.times))
    monkeypatch.setitem(D.WINDOWS, "synthetic", W)
    monkeypatch.setitem(L.DATASETS, "syn", ("synthetic", loader, 5))
    return tmp_path, loads, full


def registry(root) -> Registry:
    return Registry.load(root / "research" / "registry.jsonl", Holdout.load(root / "research" / "holdout.json"))


def lines(root) -> int:
    p = root / "research" / "registry.jsonl"
    return len(p.read_text().splitlines()) if p.exists() else 0


def test_a_book_with_shares_is_the_weighted_mean_and_an_ordinary_book_is_what_it_was():
    p = D.synthetic(rows=900, assets=3, seed=3)
    a, b = PLANTED, NOISE
    na, nb = S.pnl(a, p)["net"], S.pnl(b, p)["net"]
    plain = S.pnl({"kind": "book", "parts": [a, b]}, p)["net"]
    ok = np.isfinite(na) | np.isfinite(nb)
    assert S.weights({"kind": "book", "parts": [a, b]}) is None  # `w` is a rule's window, never a weight
    assert np.array_equal(plain[ok], np.mean([np.nan_to_num(na), np.nan_to_num(nb)], axis=0)[ok])
    book = {"kind": "book", "parts": [{**a, "share": 3.0}, {**b, "share": 1.0}]}
    assert S.weights(book) == [0.75, 0.25] and S.weights({"kind": "book", "parts": [{**a, "share": 2.0}, b]}) == [2 / 3, 1 / 3]
    w = S.pnl(book, p)
    assert np.allclose(w["net"][ok], (0.75 * np.nan_to_num(na) + 0.25 * np.nan_to_num(nb))[ok]) and np.isnan(w["net"][~ok]).all()
    assert np.allclose(w["pos"], 0.75 * np.abs(np.nan_to_num(S.pnl(a, p)["pos"])) + 0.25 * np.abs(np.nan_to_num(S.pnl(b, p)["pos"])))
    for bad in (0.0, -1.0, float("nan")):
        with pytest.raises(ValueError, match="shares must be positive"):
            S.weights({"kind": "book", "parts": [{**a, "share": bad}, b]})
    mask = np.zeros(p.T, dtype=bool)
    mask[300:] = True
    # the random baseline of a validation weighs the parts as the book does, at every shift
    ma, mb = L._shifted_means(a, p, mask, [0, 37]), L._shifted_means(b, p, mask, [0, 37])
    assert np.allclose(L._shifted_means(book, p, mask, [0, 37]), 0.75 * ma + 0.25 * mb, rtol=1e-12, atol=0)
    assert np.allclose(L._shifted_means({"kind": "book", "parts": [a, b]}, p, mask, [0, 37]), (ma + mb) / 2, rtol=1e-12, atol=0)
    assert abs(ma[0] - mb[0]) > 1e-6  # the two parts differ, so the weights matter
    assert "aggregate of 2 weighted parts" in S.describe(book) and S.causal(book, p, points=2)


def test_a_submission_is_taken_as_it_was_written_or_refused_with_its_reasons(monkeypatch):
    monkeypatch.setitem(L.DATASETS, "syn", ("synthetic", None, 5))
    good = submission([rule(PLANTED), rule(NOISE, orient="fit")])
    assert L.refuse(good) == []

    def why(change) -> str:
        sub = copy.deepcopy(good)
        change(sub)
        return " | ".join(L.refuse(sub))
    assert "not an object" in " | ".join(L.refuse([good]))
    assert "its id" in why(lambda s: s.update(id="a b"))
    assert "`mechanism` must say something" in why(lambda s: s.update(mechanism="because"))
    assert "`author` must name a role" in why(lambda s: s["author"].update(role="oracle"))
    assert "`author` must name a role" in why(lambda s: s["author"].pop("model"))
    assert "`dataset` must be one of" in why(lambda s: s.update(dataset="the moon"))
    assert "`rules` must hold 1 to 48" in why(lambda s: s.update(rules=[]))
    assert "`rules` must hold 1 to 48" in why(lambda s: s.update(rules=[rule({**PLANTED, "band": 0.01 * i}) for i in range(49)]))
    assert "is not a rule the lab can test" in why(lambda s: s["rules"][0]["spec"].update(kind="const"))
    assert "is not a rule the lab can test" in why(lambda s: s["rules"][0]["spec"].update(kind="oracle"))
    assert "a book holds at least two" in why(lambda s: s["rules"][0].update(spec={"kind": "book", "parts": [PLANTED]}))
    assert "`family` must be one of" in why(lambda s: s["rules"][0].update(family="magic"))
    assert "`why` must say" in why(lambda s: s["rules"][0].update(why="x"))
    assert "`orient` is" in why(lambda s: s["rules"][0].update(orient="up"))
    assert "the same rule appears twice" in why(lambda s: s["rules"].append(rule(PLANTED)))
    assert "`in_sample_on_check_rows` must be true or false" in why(lambda s: s.update(in_sample_on_check_rows="yes"))
    assert "`parents` must be a list" in why(lambda s: s.update(parents="DLAB-1"))
    assert L.mirror(PLANTED)["side"] == -1 and L.mirror(L.mirror(PLANTED)) == PLANTED
    book = S.xs_book(D.synthetic(rows=50, assets=6), {"feat": {"f": "ret", "k": 1}, "q": 0.2, "hold": 1, "min": 6, "side": 1})
    assert L.mirror(book)["parts"][0]["xs"]["side"] == -1 and L.mirror({"kind": "table", "map": [1.0, -1.0, 0.0]})["map"] == [-1.0, 1.0, -0.0]


def test_a_directed_test_is_registered_looked_at_once_and_its_planted_rule_is_validated(lab, monkeypatch):
    root, loads, full = lab
    monkeypatch.setitem(S.KINDS, "peek", lambda p, s: np.sign(np.nan_to_num(p.fwd()[:, p.col(s["target"])])))
    sub = submission([rule(L.mirror(PLANTED), orient="fit"),  # written the wrong way round: the fit rows point it
                      rule(NOISE),
                      rule({**PLANTED, "target": "ZZ"}),  # an instrument the panel does not hold
                      rule(TREND, family="own-lag"),  # a closed family, under no name
                      rule({"kind": "peek", "target": "A1"})])  # tomorrow's return
    with pytest.raises(SystemExit, match="holds validation rows: refused"):
        L.auto_directed("syn", "DLAB-SYN-D1", sub, NOW, panel=full)  # the whole market, validation rows included
    assert lines(root) == 0
    art = L.auto_directed("syn", "DLAB-SYN-D1", sub, NOW)
    reg = registry(root)
    t = reg.get("DLAB-SYN-D1")
    assert t.tests == 2 and t.uses[0].role == "select" and t.uses[0].universe == "synthetic"  # one test for each rule taken
    assert set(loads) == {W["check"][1]}  # the validation rows were never in memory
    frozen = json.loads((root / "research" / "specs" / "DLAB-SYN-D1.json").read_text())
    rules = frozen["spec"]["rules"]
    assert [r["spec"] for r in rules] == [PLANTED, NOISE] and rules[0]["oriented_by_the_fit_rows"] and rules[0]["fit_gross_t"] > 3
    refused = {r["rule"]: r["why"] for r in frozen["spec"]["refused_before_registration"]}
    assert "does not hold: ZZ" in refused[2] and "behaves as trend following" in refused[3] and "reads the future" in refused[4]
    doc = (root / "research" / "preregistrations" / "DLAB-SYN-D1.md").read_text()
    assert frozen["sha256"] in doc and "c" * 64 in doc and "written by the director (test-model" in doc
    assert "pointed by the fit rows" in doc and "Refused before this registration" in doc and "No model approves anything" in doc
    recs = {r["id"]: r for r in art["records"]}
    planted, noise = recs[S.spec_id(PLANTED)], recs[S.spec_id(NOISE)]
    assert art["kind"] == "directed_test" and art["verdict"] == "PASSED" and len(recs) == 2
    assert planted["class"] == "PROMISING_UNCONFIRMED" and planted["in_batch"] and planted["method"] == "directed"
    assert noise["class"] != "PROMISING_UNCONFIRMED" and not noise["in_batch"] and noise["reason"]
    assert reg.verdict_of("DLAB-SYN-D1").status == "PASSED" and lines(root) == 2
    assert set(L.known_rules("synthetic")) == set(recs) and L.earlier_looks("synthetic") == art["noise"]["distinct_behaviours"] >= 1
    assert L.auto_directed("syn", "DLAB-SYN-D1", sub, NOW + timedelta(hours=1))["sha256"] == art["sha256"] and lines(root) == 2
    # its validation: the same judge a scan's batch meets, on rows nothing has read
    res = L.auto_validate("DLAB-SYN-D1", NOW + timedelta(hours=2))
    assert res["verdict"] == "PASSED" and res["passed_rules"] == [S.spec_id(PLANTED)] and res["results"][0]["t"] > 3
    assert loads.count(W["validation"][1]) == 1 and registry(root).get("DLAB-SYN-D1-V").uses[0].role == "judge"
    # the same rule asked for again is refused, and a submission with nothing left to test registers nothing
    again = L.auto_directed("syn", "DLAB-SYN-D2", submission([rule(PLANTED)], "D-again"), NOW + timedelta(hours=3))
    assert again["verdict"] == "REFUSED" and "not looked at twice" in again["refused"][0]["why"] and lines(root) == 4
    assert not (root / "research" / "specs" / "DLAB-SYN-D2.json").exists()
    bad = L.auto_directed("syn", "DLAB-SYN-D2", {**sub, "mechanism": ""}, NOW + timedelta(hours=3))
    assert bad["verdict"] == "REFUSED" and "`mechanism`" in bad["why"][0] and lines(root) == 4
    # a later test is judged against every look already taken at these check rows
    later = L.auto_directed("syn", "DLAB-SYN-D2", submission([rule({**NOISE, "band": 1.0})], "D-later"), NOW + timedelta(hours=4))
    assert later["noise"]["of_them_from_earlier_scans"] == art["noise"]["distinct_behaviours"] and later["verdict"] == "FAILED"


def test_rules_chosen_on_the_check_rows_say_so_and_an_aggregate_shares_capital_by_family(lab):
    root, _, full = lab
    led = root / "research" / "dlab" / "candidates.jsonl"
    led.parent.mkdir(parents=True)
    book = {"kind": "book", "parts": [NOISE, {**NOISE, "target": "A0", "feat": {"f": "ret", "a": "A0", "k": 5}}]}

    def row(rid, family, cls, spec):
        return json.dumps({"run": "DLAB-SYN-1", "id": rid, "family": family, "class": cls, "spec": spec})
    led.write_text("\n".join([row("a", "cross-asset lead-lag", "INSUFFICIENT_POWER", PLANTED),
                              row("b", "cross-asset lead-lag", "INSUFFICIENT_POWER", book),
                              row("c", "own-lag", "PROMISING_UNCONFIRMED", {**NOISE, "band": 1.0}),
                              row("d", "own-lag", "NEGATIVE_EXPECTANCY", {**NOISE, "band": 2.0}),
                              row("e", "own-lag", "INSUFFICIENT_POWER", {**NOISE, "band": 0.7}).replace("DLAB-SYN-1", "DLAB-OTHER-1"),
                              json.dumps({"run": "DLAB-SYN-1", "event": "VALIDATION", "id": "a"})]) + "\n")
    agg = L.aggregate_of(["DLAB-SYN-1"])
    shares = [x["share"] for x in agg["parts"]]
    # two families share the capital; the lead-lag family's two rules share theirs; the book's two legs share its rule's
    assert shares == [0.25, 0.125, 0.125, 0.5] and sum(shares) == 1.0 and S.weights(agg) == shares
    assert [x["target"] for x in agg["parts"]] == ["A1", "A2", "A0", "A2"]  # the losing rule and the other run's are not in it
    with pytest.raises(SystemExit, match="nothing to hold together"):
        L.aggregate_of(["DLAB-NONE-1"])
    led.unlink()
    sub = submission([{"family": "aggregate", "why": "every weak positive, held together", "spec": agg}], "D-aggregate",
                     in_sample_on_check_rows=True)
    art = L.auto_directed("syn", "DLAB-SYN-D1", sub, NOW)
    r = art["records"][0]
    assert r["in_sample_on_check_rows"] and "in sample and shows nothing" in r["reason"] and r["family"] == "aggregate"
    assert "Its rules were chosen on the check rows" in (root / "research" / "preregistrations" / "DLAB-SYN-D1.md").read_text()
    assert art["submission"]["in_sample_on_check_rows"] is True


def test_the_coverage_map_names_the_holes_and_the_labs_own_test_fills_them(lab, monkeypatch):
    root, _, _ = lab
    p = D.synthetic(rows=2100, assets=12, seed=11, plant={"xs": 0.06}, cost=0.00005)
    fit = np.zeros(p.T, dtype=bool)
    fit[250:1300] = True
    cells = V.cells(p)
    assert len(cells) == 27 and len(M.rankings(p)) == 9 and V.cells(D.synthetic(rows=50, assets=3)) == []  # narrow: no map
    assert V.gaps(p, []) == cells

    def book(feat, hold, side=1, q=0.2):
        return S.xs_book(p, {"feat": feat, "q": q, "hold": hold, "min": 6, "side": side})
    seen = [{"spec": book({"f": "ret", "k": 1}, 1, side=-1, q=0.34)}, {"spec": PLANTED}, {"spec": book({"f": "vol", "k": 20}, 5)}]
    holes = V.gaps(p, seen)
    # a cell is looked at whichever way its book pointed and whatever share it held; a rule that is no book fills none
    assert len(holes) == 25 and ({"f": "ret", "k": 1}, 1) not in holes and ({"f": "ret", "k": 1}, 5) in holes
    aside = [{"cell": V.cell({"f": "ret", "k": 60}, 20), "why": "it behaves as cross-sectional momentum"}, {"why": "no cell"}]
    assert len(V.gaps(p, seen, aside)) == 24 and V.set_aside(aside) == {V.cell({"f": "ret", "k": 60}, 20): aside[0]["why"]}
    sub = V.submission("syn", p, holes, "2026-11-13", "lab-cycle-test")
    assert L.refuse(sub) == [] and sub["author"]["role"] == "lab" and len(sub["rules"]) == 25
    assert all(r["orient"] == "fit" and V.of_spec(r["spec"]) == r["cell"] for r in sub["rules"])
    # run as a directed test on a market where the one-row reversal is planted: its slower cells are found, pointed
    # against the last move by the fit rows, and every hole ends with a classed rule or a reason
    monkeypatch.setitem(D.WINDOWS, "synthetic", {"fit": (p.times[250], p.times[1300]), "check": (p.times[1300], p.times[1900]),
                                                 "validation": (p.times[1900], p.times[-1] + timedelta(days=1))})
    monkeypatch.setitem(L.DATASETS, "syn", ("synthetic", lambda last: p.head(sum(t < last for t in p.times)), 5))
    art = L.auto_directed("syn", "DLAB-SYN-D1", sub, NOW)
    refused = art["refused_before_registration"]
    assert len(art["records"]) + len(refused) == 25 and all(r.get("cell") for r in refused)
    assert V.gaps(p, seen + art["records"], aside + refused) == []  # no hole is asked for twice
    slow = next(r for r in art["records"] if V.of_spec(r["spec"]) == V.cell({"f": "ret", "k": 1}, 5))
    assert slow["spec"]["parts"][0]["xs"]["side"] == -1 and slow["check"]["t"] > 2 and slow["detail"]["oriented_by_the_fit_rows"]
    assert registry(root).get("DLAB-SYN-D1").tests == len(art["records"])
    assert all(r["class"] in T.CLASSES and r["reason"] for r in art["records"])
