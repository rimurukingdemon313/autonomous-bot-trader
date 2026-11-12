"""The discovery lab's foundations: no feature and no rule may read the future; a position's return is booked with its
costs exactly; a missing price is never filled. Built panels only."""

from __future__ import annotations

from datetime import date, timedelta

import numpy as np
import pytest

from aitrader.research.dlab import datasets as D
from aitrader.research.dlab import panel as P
from aitrader.research.dlab import signals as S


def days(n, start=date(2020, 1, 1)):
    return [start + timedelta(days=i) for i in range(n)]


def tiny(ret, aux=None, cost=0.001, hold=None):
    ret = np.asarray(ret, dtype=float)
    names = tuple(f"A{i}" for i in range(ret.shape[1]))
    return P.Panel("tiny", days(len(ret)), names, ret, aux or {}, {n: cost for n in names}, 252.0, hold)


def gappy(seed=0, rows=900):
    p = D.synthetic(rows=rows, seed=seed)
    r = p.ret.copy()
    rng = np.random.default_rng(seed)
    r[rng.random(r.shape) < 0.08] = np.nan  # a price missing on 8% of the rows
    return P.Panel("gappy", p.times, p.assets, r, dict(p.aux), dict(p.cost), p.ppy)


# ── trailing arithmetic ─────────────────────────────────────────────────────

def test_trailing_sums_ranks_and_z_scores_are_exact_and_skip_missing_rows():
    x = np.array([1.0, 2.0, np.nan, 4.0, 3.0])
    assert np.allclose(P.roll_sum(x, 2), [np.nan, 3.0, np.nan, 4.0, 7.0], equal_nan=True)  # a missing row adds nothing
    r = P.roll_rank(x, 3, min_n=2)
    assert np.isnan(r[0]) and r[1] == 1.0 and np.isnan(r[2]) and r[3] == 1.0 and r[4] == 0.5  # 3 among (4, 3)
    z = P.roll_z(np.array([1.0, 2.0, 3.0, 4.0]), 3, min_n=3)
    assert np.isnan(z[:2]).all() and z[2] == pytest.approx(1.0) and z[3] == pytest.approx(1.0)


def test_every_feature_at_a_row_is_the_same_when_later_rows_do_not_exist():
    p = gappy()
    for f in P.library(p) + [{"f": "vol", "a": "A0", "k": 20}]:
        full_f, full_r, full_z = P.feat(p, f), P.rank(p, f, 250), P.zscore(p, f, 250)
        for t in (300, 555, 899):
            cut = p.head(t + 1)
            for full, part in ((full_f, P.feat(cut, f)), (full_r, P.rank(cut, f, 250)), (full_z, P.zscore(cut, f, 250))):
                assert (np.isnan(full[t]) and np.isnan(part[t])) or full[t] == part[t], (f, t)


def test_a_panel_refuses_unordered_times_and_misshapen_data():
    with pytest.raises(ValueError):
        P.Panel("x", [date(2020, 1, 2), date(2020, 1, 1)], ("A",), np.zeros((2, 1)), {}, {"A": 0.0}, 252.0)
    with pytest.raises(ValueError):
        P.Panel("x", days(3), ("A",), np.zeros((2, 1)), {}, {"A": 0.0}, 252.0)


# ── a position's return ─────────────────────────────────────────────────────

def test_a_position_earns_the_return_to_the_next_priced_row_less_its_costs():
    # A0's returns realized at rows 1..5; row 3 has no price: its move arrives at row 4
    p = tiny([[np.nan], [0.01], [0.02], [np.nan], [0.05], [-0.03]], cost=0.001)
    S.KINDS["script"] = lambda p_, s: np.asarray(s["pos"], dtype=float)
    try:
        r = S.pnl({"kind": "script", "target": "A0", "pos": [0, 1, 1, -1, -1, 0]}, p)
    finally:
        del S.KINDS["script"]
    # decisions exist at the priced rows 1, 2, 4 (row 5 has no later price): positions 1, 1, -1
    assert np.allclose(r["gross"][[1, 2, 4]], [0.02, 0.05, 0.03])  # row 2's position earns the move to row 4
    assert np.allclose(r["net"][[1, 2, 4]], [0.02 - 0.001, 0.05, 0.03 - 0.002])  # entry; no change; a flip is two sides
    assert np.isnan(r["net"][[0, 3, 5]]).all()  # no price, or no later price: no decision, nothing booked


def test_costs_scale_a_roll_is_charged_while_held_and_a_late_entry_shifts_by_priced_rows():
    hold = np.zeros((6, 1))
    hold[2, 0] = 0.004  # holding over the interval that starts at row 2 costs a roll
    p = tiny([[np.nan], [0.01], [0.01], [0.01], [0.01], [0.01]], cost=0.001, hold=hold)
    spec = {"kind": "const", "target": "A0", "side": 1}
    r = S.pnl(spec, p)
    assert np.allclose(r["net"][1:5], [0.01 - 0.001, 0.01 - 0.004, 0.01, 0.01])
    assert np.allclose(S.pnl(spec, p, k=2.0)["net"][1:5], [0.01 - 0.002, 0.01 - 0.008, 0.01, 0.01])
    late = S.pnl(spec, p, delay=1)
    assert late["pos"][1] == 0 and late["net"][2] == pytest.approx(0.01 - 0.001 - 0.004)  # in one priced row later


def test_a_book_splits_capital_equally_and_idle_parts_earn_nothing():
    p = tiny([[np.nan, np.nan], [0.02, 0.04], [0.02, 0.04], [0.02, 0.04]], cost=0.0)
    book = {"kind": "book", "parts": [{"kind": "const", "target": "A0", "side": 1},
                                      {"kind": "const", "target": "A1", "side": -1}]}
    assert np.allclose(S.pnl(book, p)["net"][1:3], [(0.02 - 0.04) / 2] * 2)
    assert S.targets(book) == ("A0", "A1")


# ── rules are causal, and a rule that is not is caught ──────────────────────

def all_kinds(p):
    f0, f1 = {"f": "ret", "a": "A0", "k": 1}, {"f": "ret", "a": "A1", "k": 5}
    leaf = {"feat": f0, "w": 250, "op": ">", "q": 0.8}
    return [
        {"kind": "tree", "target": "A1", "node": {"and": [leaf, {"feat": f1, "w": 250, "op": "<", "q": 0.5}]}, "side": 1, "hold": 5},
        {"kind": "sign", "target": "A1", "feat": f0, "w": 250, "band": 0.5, "side": -1},
        {"kind": "table", "target": "A1", "feats": [f0, f1], "w": 250, "edges": [[1 / 3, 2 / 3]] * 2, "map": [1, 0, -1, 0, 0, 0, -1, 0, 1]},
        {"kind": "ordinal", "target": "A1", "a": "A1", "k": 1, "m": 3, "map": [1, 0, 0, -1, 0, 1]},
        {"kind": "regime", "target": "A1", "feats": [f0, f1], "w": 250, "centroids": [[1.0, 1.0], [-1.0, -1.0]], "map": [1, -1]},
        {"kind": "anomaly", "target": "A1", "vol_k": 60, "mu": [0.0] * 3, "prec": np.eye(3).tolist(), "thr": 6.0, "mode": "rev", "hold": 5},
        {"kind": "level", "target": "A1", "feat": {"f": "aux", "name": "state"}, "op": ">", "x": 0.0, "side": 1},
        {"kind": "combo", "target": "A1", "op": "vote", "parts": [
            {"kind": "sign", "target": "A1", "feat": f0, "w": 250, "band": 0.0, "side": 1},
            {"kind": "sign", "target": "A1", "feat": f1, "w": 250, "band": 0.0, "side": 1},
            {"kind": "level", "target": "A1", "feat": {"f": "aux", "name": "state"}, "op": ">", "x": 0.0, "side": 1}]},
    ]


def test_every_kind_of_rule_is_causal_and_takes_positions():
    p = gappy(seed=2)
    for s in all_kinds(p):
        pos = S.positions(s, p)
        assert set(np.unique(pos)) <= {-1.0, 0.0, 1.0} and (pos != 0).sum() > 10, s["kind"]
        assert S.causal(s, p), s["kind"]
        assert S.describe(s) and S.spec_id(s) == S.spec_id(dict(s))
    assert S.causal({"kind": "book", "parts": all_kinds(p)[:2]}, p)


def test_a_rule_that_reads_the_next_return_is_caught_by_truncation():
    p = gappy(seed=3)
    S.KINDS["leak"] = lambda p_, s: np.nan_to_num(np.sign(p_.fwd()[:, p_.col(s["target"])]))
    try:
        assert not S.causal({"kind": "leak", "target": "A1"}, p)
    finally:
        del S.KINDS["leak"]


def test_held_and_ordinal_codes_are_exact():
    b = np.array([0, 1, 0, 0, 0, 1, 0], dtype=bool)
    assert S.held(b, 3).tolist() == [False, True, True, True, False, True, True]
    p = tiny(np.expm1(np.array([[0.0], [0.01], [0.03], [0.02], [-0.01], [0.05]])), cost=0.0)
    code = S.ordinal_code(p, "A0", 1, 3)
    assert code[0] == -1 and code[1] == -1  # fewer than three returns
    assert code[2] == 0 and code[3] == 1  # (0.00, 0.01, 0.03) rising: the first ordering; (0.01, 0.03, 0.02): the next
    assert len({int(c) for c in code[2:]}) == 4 and code.max() < 6


def test_the_newey_west_t_shrinks_when_returns_are_positively_autocorrelated():
    rng = np.random.default_rng(0)
    e = rng.standard_normal(4000)
    iid = 0.05 + e
    ar = 0.05 + e + 0.6 * np.concatenate([[0.0], e[:-1]])
    plain = ar.mean() / ar.std(ddof=1) * np.sqrt(len(ar))
    assert S.nw_t(iid, 5) == pytest.approx(iid.mean() / iid.std(ddof=1) * np.sqrt(len(iid)), rel=0.08)
    assert S.nw_t(ar, 5) < 0.8 * plain


# ── the energy panel: contracts, rolls and the cut ──────────────────────────

def test_the_energy_panel_follows_one_contract_across_a_roll_and_reads_nothing_at_or_after_last(monkeypatch):
    import scripts.eng1 as e
    cal = [d for d in days(650, date(2009, 6, 1)) if d.weekday() < 5]  # the exchange's calendar starts earlier
    bdays = [d for d in cal if d >= date(2010, 1, 4)]
    front = {d: e.front_delivery("WTI", d, e.extended(cal)) for d in bdays}
    months = sorted(set(front.values()))
    base = {m: 50.0 + 3.0 * i for i, m in enumerate(months + [e._month_add(*months[-1], k) for k in (1, 2, 3)])}

    def price(m, d):  # every contract drifts by its own amount each day, so contracts are told apart
        return base[m] + 0.01 * (d - bdays[0]).days * (1 + 0.1 * (m[1] % 3))
    c = {d: tuple(price(e._month_add(*front[d], k), d) for k in range(3)) for d in bdays}
    curves = {"WTI": e.Curve("WTI", bdays, c)}
    monkeypatch.setattr(e, "load", lambda last: ({k: e.Curve(k, [d for d in v.days if d < last], v.c) for k, v in curves.items()},
                                                 e.extended(cal)))
    last = bdays[200]
    p = D.energy(last, assets=("WTI",), first=bdays[0])
    assert p.times[-1] < last and p.T == 200
    rolls = 0
    for i in range(1, p.T):
        d0, d1 = p.times[i - 1], p.times[i]
        held = e._month_add(*front[d0], 1)  # contract 2 yesterday: the contract held
        assert p.ret[i, 0] == pytest.approx(price(held, d1) / price(held, d0) - 1.0)  # the SAME contract's move
        if front[d1] != front[d0]:
            rolls += 1
            assert p.hold_cost[i - 1, 0] == pytest.approx(e.COST_BP["WTI"] / 1e4)
        else:
            assert p.hold_cost[i - 1, 0] == 0.0
    assert rolls >= 8 and "WTI.s23" in p.aux and np.isfinite(p.aux["WTI.s12"]).all()
