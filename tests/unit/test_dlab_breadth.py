"""The lab on a broad panel: one rule traded on every instrument at once. Built markets only, so each answer is known
by construction: a cross-sectional book's weights and P&L by hand; a planted effect that only a book can carry; the
closed families' tombstones; the daily crypto and ETF panels from canned files."""

from __future__ import annotations

import json
from datetime import date, timedelta

import numpy as np
import pytest

import scripts.dlab as L
from aitrader.research.dlab import datasets as D
from aitrader.research.dlab import methods as M
from aitrader.research.dlab import triage as T
from aitrader.research.dlab.panel import Panel, feat, library, tfeat
from aitrader.research.dlab.signals import causal, describe, pnl, stats, xs_book, xs_weights
from aitrader.research.registry import Holdout, Registry, Trial, Use


def days(n: int, start: date = date(2021, 1, 1)) -> list[date]:
    return [start + timedelta(days=i) for i in range(n)]


def small(ret: np.ndarray, aux: dict | None = None, cost: float = 0.001) -> Panel:
    names = tuple(f"I{j}" for j in range(ret.shape[1]))
    return Panel("built", days(len(ret)), names, ret, aux or {}, {n: cost for n in names}, 365.0)


X = {"feat": {"f": "ret", "k": 1}, "q": 0.25, "hold": 1, "min": 6, "side": 1}


def test_a_cross_sectional_book_holds_the_top_against_the_bottom_with_no_net_exposure():
    rng = np.random.default_rng(1)
    r = rng.normal(0, 0.01, size=(40, 8))
    r[10] = [0.08, 0.07, 0.01, 0.0, -0.01, 0.02, -0.07, -0.08]  # row 10: I0, I1 the top two; I6, I7 the bottom two
    p = small(r)
    w = xs_weights(p, X)
    assert w[10].tolist() == [0.25, 0.25, 0, 0, 0, 0, -0.25, -0.25]
    assert np.allclose(w.sum(axis=1), 0) and np.allclose(np.abs(w[1:]).sum(axis=1), 1.0)  # one unit, no net exposure
    assert (xs_weights(p, {**X, "side": -1}) == -w).all()
    book = pnl(xs_book(p, X), p)
    turn = np.abs(w[10] - w[9]).sum()
    by_hand = float(w[10] @ r[11]) - 0.001 * turn  # weights decided at row 10 earn row 11's returns, less the turnover
    assert book["net"][10] == pytest.approx(by_hand, abs=1e-12)
    assert book["pos"][10] == pytest.approx(1.0)


def test_a_book_ranks_only_what_is_priced_and_opens_nothing_on_a_thin_row():
    rng = np.random.default_rng(2)
    r = rng.normal(0, 0.01, size=(30, 8))
    r[12, 3:] = np.nan  # row 12: five of the eight have no price
    r[20, 0] = np.nan  # row 20: one is missing
    p = small(r)
    w = xs_weights(p, X)
    assert (w[12] == 0).all()  # three priced instruments: fewer than `min`
    assert w[20, 0] == 0 and np.abs(w[20]).sum() == pytest.approx(1.0)  # the unpriced one is in neither side
    assert int((w[20] > 0).sum()) == 1 == int((w[20] < 0).sum())  # a quarter of seven is one a side


def test_a_held_book_is_the_mean_of_the_last_rows_books_and_trades_less():
    rng = np.random.default_rng(3)
    p = small(rng.normal(0, 0.01, size=(120, 10)))
    one, five = xs_weights(p, X), xs_weights(p, {**X, "hold": 5})
    assert np.allclose(five[50], one[46:51].mean(axis=0))
    assert np.abs(np.diff(five, axis=0)).sum() < 0.5 * np.abs(np.diff(one, axis=0)).sum()


def test_a_book_and_its_features_cannot_see_later_rows():
    rng = np.random.default_rng(4)
    aux = {f"I{j}.fund": rng.normal(0, 1e-4, 300) for j in range(8)}
    p = small(rng.normal(0, 0.01, size=(300, 8)), aux)
    for x in (X, {**X, "hold": 5}, {**X, "feat": {"f": "aux", "s": "fund", "d": 5}}, {**X, "feat": {"f": "vol", "k": 20}}):
        assert causal(xs_book(p, x), p)
        w = xs_weights(p, x)
        assert (xs_weights(p.head(200), x)[199] == w[199]).all()
    for f in ({"f": "rel", "a": "I2", "k": 5}, {"f": "xavg", "of": {"f": "aux", "s": "fund"}},
              {"f": "xavg", "of": {"f": "vol", "k": 20}}):
        full, cut = feat(p, f), feat(p.head(180), f)
        assert np.allclose(full[:180], cut, equal_nan=True)
    assert feat(p, {"f": "rel", "a": "I2", "k": 5})[100] == pytest.approx(
        feat(p, {"f": "ret", "a": "I2", "k": 5})[100] - feat(p, {"f": "mkt", "k": 5})[100])


def test_on_a_broad_panel_a_rule_reads_its_own_instrument_and_the_market_only():
    rng = np.random.default_rng(5)
    aux = {f"I{j}.fund": rng.normal(0, 1e-4, 60) for j in range(9)}
    aux["VIX"] = rng.normal(3, 0.1, 60)
    p = small(rng.normal(0, 0.01, size=(60, 9)), aux)
    lib = library(p, target="I3")
    named = {f.get("a") for f in lib if "a" in f} | {f["name"].split(".")[0] for f in lib if f["f"] == "aux" and "." in f["name"]}
    assert named == {"I3"}  # no other instrument's series
    kinds = {f["f"] for f in lib}
    assert {"ret", "rel", "volr", "absret", "mkt", "disp", "xavg", "aux"} <= kinds
    assert {"f": "aux", "name": "VIX"} in lib and {"f": "aux", "name": "I3.fund"} in lib
    assert all("a" not in f and not f.get("name", "").startswith("I") for f in library(p))  # no target: the market only
    assert M._star({"feat": {"f": "ret", "a": "*", "k": 5}, "x": [{"f": "aux", "name": "*.fund"}]}, "I7") == {
        "feat": {"f": "ret", "a": "I7", "k": 5}, "x": [{"f": "aux", "name": "I7.fund"}]}
    assert tfeat({"f": "aux", "s": "fund", "d": 5}, "I1") == {"f": "aux", "name": "I1.fund", "d": 5}
    narrow = small(rng.normal(0, 0.01, size=(60, 3)))
    assert library(narrow, target="I0") == library(narrow)  # a narrow panel: every pair, as before


def test_entries_count_positions_opened_or_reversed_not_resized():
    q = np.array([0, 1, 1, 0.5, 0.5, 0, -1, -1, 1, 0], dtype=float)
    s = stats(np.full(10, 0.01) * np.arange(1, 11) / 10 + np.linspace(0, 0.01, 10), np.ones(10, bool), 252.0, q)
    assert s["in_position"] == 7 and s["entries"] == 3  # opened long, opened short, reversed to long


@pytest.fixture(scope="module")
def planted():
    """Twelve instruments, each of whose next return leans against its last move relative to the market's: no single
    instrument's rule is strong, the book of all of them is. Costs are small, so the effect survives them."""
    p = D.synthetic(rows=3300, assets=12, seed=11, plant={"xs": 0.06}, cost=0.00005)
    head = p.head(2100)
    fit = np.zeros(head.T, dtype=bool)
    fit[250:1300] = True
    check = np.zeros(head.T, dtype=bool)
    check[1300:] = True
    ctx = M.Context(head, fit, seed=7)
    emitted, _ = M.discover(ctx)
    res = T.triage(emitted, head, fit, check, n_val=2400, bar=3.0, closed=D.closed(head))
    return p, head, fit, check, ctx, emitted, res


def test_breadth_finds_an_effect_that_only_a_book_of_every_instrument_can_carry(planted):
    p, head, fit, check, ctx, emitted, res = planted
    recs = {r["id"]: r for r in res["records"]}
    xs = [r for r in res["records"] if r["family"] == "cross-sectional"]
    pooled = [r for r in res["records"] if r["family"] == "pooled time-series"]
    assert xs and pooled and ctx.scanned["breadth"] > 100
    best = max(xs, key=lambda r: r["check"]["t"])
    x = best["spec"]["parts"][0]["xs"]
    assert x["feat"] == {"f": "ret", "k": 1} and x["side"] == -1  # the planted rule: against the last relative move
    assert best["check"]["t"] > 4 and len(best["targets"]) == 12
    single = max((r["check"]["t"] or -9) for r in res["records"] if len(r["targets"]) == 1)
    assert best["check"]["t"] > single + 1.5  # no rule on one instrument comes near the book
    assert res["batch"] and all(recs[i]["family"] in ("cross-sectional", "pooled time-series", "pooled book", "combination")
                                for i in res["batch"][:1])
    top = recs[res["batch"][0]]
    assert top["class"] == "PROMISING_UNCONFIRMED" and top["power"]["p_pass"] >= T.P_MIN
    # on 1,200 rows no method and no triage read, the book holds
    vmask = np.zeros(p.T, dtype=bool)
    vmask[2100:] = True
    j = L.judge_rule(best["spec"], p, vmask, 3.0, 5, L.mean_hold(best) >= L.SLOW_ROWS)
    assert j["t"] > 3.0 and j["gates"]["beats_random"] and j["gates"]["costs_x2"] and j["gates"]["halves"]
    assert "top 20%" in describe(best["spec"]) or "top 34%" in describe(best["spec"])


def test_a_book_s_entries_and_holding_time_are_its_legs(planted):
    *_, res = planted
    fast = next(r for r in res["records"] if r["family"] == "cross-sectional" and r["spec"]["parts"][0]["xs"]["hold"] == 1)
    slow = next(r for r in res["records"] if r["family"] == "cross-sectional" and r["spec"]["parts"][0]["xs"]["hold"] == 20)
    assert fast["check"]["entries"] > 500 and fast["check"]["mean_hold"] < L.SLOW_ROWS  # entered a row late, another rule
    assert slow["check"]["mean_hold"] >= L.SLOW_ROWS  # a slow book: the delay is a gate for it
    assert fast["parents"] == [] or len(fast["parents"]) == 12


def test_with_nothing_planted_no_book_is_promoted():
    promoted = 0
    for seed in (21, 22):
        p = D.synthetic(rows=2100, assets=12, seed=seed, cost=0.00005)
        fit = np.zeros(p.T, dtype=bool)
        fit[250:1300] = True
        check = np.zeros(p.T, dtype=bool)
        check[1300:] = True
        emitted, _ = M.discover(M.Context(p, fit, seed=7))
        res = T.triage(emitted, p, fit, check, n_val=2400, bar=3.0, closed=D.closed(p))
        books = [r for r in res["records"] if r["family"] in ("cross-sectional", "pooled time-series")]
        assert books and max(r["check"]["t"] or -9 for r in books) < 3.2
        promoted += len(res["batch"])
        assert all(r["class"] in T.CLASSES and r["reason"] for r in res["records"])
    assert promoted <= 2


def crypto_like(rows: int = 900, n: int = 10, seed: int = 0) -> Panel:
    rng = np.random.default_rng(seed)
    r = rng.normal(0.0005, 0.03, size=(rows, n))
    names = tuple(f"C{j}USDT" for j in range(n))
    aux = {}
    for j, s in enumerate(names):
        aux[f"{s}.fund"] = rng.normal(1e-4, 2e-4, rows)
        aux[f"{s}.fund7"] = np.convolve(aux[f"{s}.fund"], np.ones(7) / 7, mode="full")[:rows]
    return Panel("crypto-perp-daily", days(rows), names, r, aux, {s: 0.0013 for s in names}, 365.0)


def test_the_closed_families_are_named_when_a_broad_scan_meets_them_again():
    p = crypto_like()
    fit = np.zeros(p.T, dtype=bool)
    fit[250:600] = True
    check = ~fit
    check[:250] = False
    names = [n for n, _ in D.closed(p)]
    assert any("XSM-1" in n for n in names) and any("XTS-1" in n for n in names) and any("CR-3" in n for n in names)
    assert any("VOLM-1" in n for n in names) and any("trend following across the panel" in n for n in names)

    def xs(feat_, side, hold):
        return M.Emit(xs_book(p, {"feat": feat_, "q": 0.2, "hold": hold, "min": 6, "side": side}), "cross-sectional",
                      "breadth", 1.0, "test")
    emitted = [xs({"f": "ret", "k": 20}, 1, 5),  # cross-coin momentum under another lookback
               xs({"f": "aux", "s": "fund7"}, -1, 5),  # funding carry
               xs({"f": "ret", "k": 1}, -1, 1)]  # a one-day reversal: not a closed family
    recs = T.triage(emitted, p, fit, check, n_val=600, bar=3.0, closed=D.closed(p))["records"]
    assert recs[0]["class"] == "REPEATS_CLOSED_FAMILY" and "XSM-1" in recs[0]["reason"]
    assert recs[1]["class"] == "REPEATS_CLOSED_FAMILY" and "funding carry" in recs[1]["reason"]
    assert recs[2]["class"] != "REPEATS_CLOSED_FAMILY"


def test_the_daily_crypto_panel_charges_funding_and_never_assumes_it(tmp_path):
    d0 = date(2019, 9, 1)
    ds = [(d0 + timedelta(days=i)).isoformat() for i in range(40)]
    close = {"BTCUSDT": {d: 100.0 * 1.01 ** i for i, d in enumerate(ds)},
             "ETHUSDT": {d: 50.0 * 0.99 ** i for i, d in enumerate(ds[5:])},
             "XRPUSDT": {d: 0.25 for d in ds}, "NOTLISTED": {d: 1.0 for d in ds}}
    fund = {"BTCUSDT": {d: 0.0003 for d in ds}, "ETHUSDT": {d: -0.0002 for d in ds[5:]}, "XRPUSDT": {d: 0.0 for d in ds}}
    del fund["BTCUSDT"][ds[20]]  # one day's settlements are not on file
    (tmp_path / "close.json").write_text(json.dumps(close))
    (tmp_path / "funding.json").write_text(json.dumps(fund))
    p = D.crypto_daily(d0 + timedelta(days=30), data=tmp_path)
    assert p.assets == ("BTCUSDT", "ETHUSDT", "XRPUSDT")  # the listed-by-2020 universe only, in its fixed order
    assert p.times[-1] == d0 + timedelta(days=29) and p.T == 30  # nothing on or after `last`
    assert p.ret[10, 0] == pytest.approx(0.01 - 0.0003)  # a long earns the move less the funding it paid
    assert p.ret[10, 1] == pytest.approx(-0.01 + 0.0002)  # and is paid when funding is negative
    assert np.isnan(p.ret[20, 0]) and np.isnan(p.aux["BTCUSDT.fund"][20])  # unknown funding: no return, not a zero
    assert np.isnan(p.ret[0, 0]) and np.isnan(p.ret[:6, 1]).all()  # no earlier close, or not yet listed
    assert p.aux["BTCUSDT.fund7"][15] == pytest.approx(0.0003)
    assert p.cost == {"BTCUSDT": 0.0007, "ETHUSDT": 0.0007, "XRPUSDT": 0.0013}  # CR-3's costs: majors 7 bp, the rest 13
    again = D.crypto_daily(d0 + timedelta(days=25), data=tmp_path)
    assert np.allclose(again.ret, p.ret[:25], equal_nan=True)  # a later file changes nothing earlier
    with pytest.raises(SystemExit):
        D.crypto_daily(d0, data=tmp_path)


def test_the_etf_panel_follows_spys_calendar_and_carries_the_vix(tmp_path):
    ds = [d.isoformat() for d in days(30, date(2006, 1, 2)) if d.weekday() < 5]
    close = {"SPY": {d: 100.0 + i for i, d in enumerate(ds)}, "GLD": {d: 50.0 + i for i, d in enumerate(ds) if i != 7},
             "QQQ": {d: 40.0 for d in ds[3:]}, "^VIX": {d: 20.0 for d in ds[:-2]}, "ZZZ": {d: 1.0 for d in ds}}
    close["GLD"]["2006-01-07"] = 999.0  # a Saturday print: not on SPY's calendar
    (tmp_path / "close.json").write_text(json.dumps(close))
    p = D.etf_daily(date.fromisoformat(ds[-1]), data=tmp_path)
    assert p.assets == ("SPY", "QQQ", "GLD") and len(p.times) == len(ds) - 1 and p.ppy == 252.0
    assert p.ret[5, 0] == pytest.approx(105 / 104 - 1)
    g = p.col("GLD")
    assert np.isnan(p.ret[7, g]) and p.ret[8, g] == pytest.approx(58 / 56 - 1)  # a missing day is not filled
    assert p.aux["VIX"][0] == pytest.approx(np.log(20.0)) and np.isnan(p.aux["VIX"][-1])
    del close["SPY"]
    (tmp_path / "close.json").write_text(json.dumps(close))
    with pytest.raises(SystemExit, match="SPY"):
        D.etf_daily(date(2006, 2, 1), data=tmp_path)


def test_a_validation_bar_counts_the_tests_of_related_universes(tmp_path, monkeypatch):
    (tmp_path / "holdout.json").write_text(json.dumps({"universe": "fx-majors", "start": "2017-01-01", "rationale": "t",
                                                       "sealed_at": "2026-09-26T20:28:47+00:00"}))
    reg = Registry.load(tmp_path / "registry.jsonl", Holdout.load(tmp_path / "holdout.json"))
    from datetime import datetime, timezone
    now = datetime(2026, 11, 1, tzinfo=timezone.utc)
    w = (date(2024, 7, 1), date(2026, 11, 1))
    assert L.bar_for(reg, "crypto-perp-daily", w, 12) == 3.0
    reg.register(Trial(id="OLD-1", registered=now, title="t", hypothesis="h", tests=40, configurations=40,
                       uses=(Use("crypto-binance-spot", date(2024, 1, 1), date(2025, 1, 1), "judge"),)))
    assert L.tests_counted(reg, "crypto-perp-daily", w) == 40  # the same market under another name
    assert L.bar_for(reg, "crypto-perp-daily", w, 12) > 3.2
    assert L.bar_for(reg, "us-etf-broad-daily", w, 12) == 3.0  # not that market
    assert L.tests_counted(reg, "crypto-perp-daily", (date(2025, 1, 1), date(2026, 1, 1))) == 0  # outside its window
    for u, w_ in D.WINDOWS.items():
        assert w_["fit"][1] == w_["check"][0] and w_["check"][1] == w_["validation"][0], u  # no gap, no overlap


def test_a_later_scan_of_the_same_rows_is_judged_against_the_earlier_scans_looks_too():
    p = D.synthetic(rows=2100, assets=3, seed=5, plant={"leadlag": 0.10})
    fit = np.zeros(p.T, dtype=bool)
    fit[:1300] = True
    emitted, _ = M.discover(M.Context(p, fit, seed=7))
    first = T.triage(emitted, p, fit, ~fit, n_val=2000, bar=3.0)
    again = T.triage(emitted, p, fit, ~fit, n_val=2000, bar=3.0, prior_looks=400)
    a = {r["id"]: r["power"]["p_real"] for r in first["records"] if "power" in r}
    b = {r["id"]: r["power"]["p_real"] for r in again["records"] if "power" in r}
    assert a.keys() == b.keys() and all(b[i] <= a[i] for i in a) and any(b[i] < a[i] for i in a)
    assert again["noise"]["of_them_from_earlier_scans"] == 400
    assert again["noise"]["distinct_behaviours"] == first["noise"]["distinct_behaviours"] + 400


def test_one_year_may_not_carry_a_rule_and_a_short_window_is_not_failed_for_being_short():
    """Two and a third years of daily rows, as the crypto validation window is: 2025 alone holds 43% of them."""
    rng = np.random.default_rng(8)
    ds = days(853, date(2024, 7, 1))
    lead = rng.normal(0, 0.01, 853)
    steady = np.concatenate([[0.0], 0.006 * np.sign(lead[:-1])]) + rng.normal(0, 0.004, 853)  # follows the leader always
    lucky = rng.normal(0, 0.004, 853)
    in_2025 = np.array([d.year == 2025 and d.month <= 6 for d in ds])
    lucky[1:] += np.where(in_2025[1:], 0.012 * np.sign(lead[:-1]), 0.0)  # follows it for half of one year only
    p = Panel("built", ds, ("LEAD", "STEADY", "LUCKY"), np.column_stack([lead, steady, lucky]), {},
              {"LEAD": 0.0, "STEADY": 0.0001, "LUCKY": 0.0001}, 365.0)
    vmask = np.ones(p.T, dtype=bool)

    def rule(target):
        return {"kind": "level", "target": target, "feat": {"f": "ret", "a": "LEAD", "k": 1}, "op": ">", "x": 0.0, "side": 1}
    good, bad = L.judge_rule(rule("STEADY"), p, vmask, 3.0, 5, False), L.judge_rule(rule("LUCKY"), p, vmask, 3.0, 5, False)
    assert good["rows_by_year"]["2025"] / good["rows"] > 0.42 and 0.35 < good["top_year_share"] < 0.6
    assert good["gates"]["top_year"] and good["passed"]  # 2025 gives about its share of the rows: not a failure
    assert bad["t"] > 3.0 and bad["top_year_share"] > 0.9 and not bad["gates"]["top_year"] and not bad["passed"]
    assert "top_year" in L.GATES and "1.5 times" in L.GATES["top_year"]
