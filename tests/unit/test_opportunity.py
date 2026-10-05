"""ID-2 opportunity engine: the vectorised labeller fills exactly as the ID-1 simulator; no feature,
memory or cost input reads a later bar; walk-forward never trains on a trade that had not exited;
the portfolio enforces the risk engine's account limits; the tree family finds an interaction a
linear model cannot; a planted opportunity is selected and a random walk yields nothing."""

from __future__ import annotations

import sys
from datetime import date, datetime, timezone
from pathlib import Path

import numpy as np
import pytest

from aitrader.research.discovery import intraday as ID
from aitrader.research.discovery import opportunity as OP

ROOT = Path(__file__).resolve().parents[2]
T0 = int(datetime(2010, 1, 4, 0, 0, tzinfo=timezone.utc).timestamp())  # a Monday


def walk(n, seed, symbol="EURUSD", px=1.1, vol=0.0004, spread=0.00006, t0=T0, drop=0.0, pip=0.0001):
    rng = np.random.default_rng(seed)
    mid = px * np.exp(np.cumsum(rng.normal(0, vol, n)))
    o = np.r_[mid[0], mid[:-1]]
    pad = np.abs(rng.normal(0, vol * 0.8, n))
    h, lo = np.maximum(o, mid) + pad * px, np.minimum(o, mid) - pad * px
    t = t0 + 300 * np.arange(n)
    sp = spread * (1 + 0.5 * rng.random(n)) * px / 1.1
    keep = rng.random(n) >= drop
    keep[0] = True
    hs = sp / 2
    return ID.Bars(symbol, pip, t[keep], (o - hs)[keep], (h - hs)[keep], (lo - hs)[keep], (mid - hs)[keep],
                   (o + hs)[keep], (h + hs)[keep], (lo + hs)[keep], (mid + hs)[keep])


def cut_bars(b: ID.Bars, t_last: int) -> ID.Bars:
    return b.slice(0, int(np.searchsorted(b.t, t_last, side="right")))


# ── the labeller is the simulator ───────────────────────────────────────

@pytest.mark.parametrize("scale", sorted(OP.SCALES))
@pytest.mark.parametrize("stress", [1.0, 1.5])
def test_the_vectorised_labeller_fills_exactly_as_the_simulator(scale, stress):
    b = walk(288 * 25, 3, drop=0.002)
    costs = ID.Costs().stressed(stress)
    idx = OP.candidates(b)
    lab = OP.label_scale(b, idx, scale, costs)
    sd = OP.scale_stop(b, scale)
    rng = np.random.default_rng(5)
    checked = {0: 0, 1: 0, 3: 0}
    for q in rng.choice(len(lab.i), 600, replace=False):
        i, s = int(lab.i[q]), int(lab.side[q])
        sig = ID.Signal(i, s, b.c[i] - s * sd[i], b.c[i] + s * OP.RR * sd[i], OP.SCALES[scale][1],
                        deadline_hour=(OP.EXIT_BY - 1) / 3600)
        tr, sk = ID.simulate(b, [sig], costs)
        if lab.status[q] == 0:
            t = tr[0]
            assert (t.entry_i, t.exit_i) == (lab.entry_i[q], lab.exit_i[q])
            for a, v in ((t.entry, lab.entry[q]), (t.exit, lab.exit_px[q]), (t.risk, lab.risk[q]),
                         (t.gross_mid, lab.gross[q]), (t.spread, lab.spread[q]), (t.slippage, lab.slippage[q]),
                         (t.commission, lab.commission[q]), (t.financing, lab.financing[q]), (t.r, lab.r[q])):
                assert a == pytest.approx(v, abs=1e-12)
            assert t.reason == OP.REASONS[lab.reason[q]]
        else:
            assert tr == [] and sk[{1: "end_of_data", 2: "bad_stop", 3: "risk_checks"}[int(lab.status[q])]] == 1
        checked[int(lab.status[q]) if lab.status[q] in checked else 0] += 1
    assert checked[0] > 300
    assert (b.t[lab.exit_i[lab.status == 0]] % 86400 + 300 <= OP.EXIT_BY).all()  # flat by 20:55 UTC


def test_every_standard_trade_is_flat_before_the_rollover_and_pays_no_financing():
    b = walk(288 * 10, 9)
    lab = OP.label_scale(b, OP.candidates(b), "S60")
    ok = lab.status == 0
    assert ok.sum() > 1000 and np.all(lab.financing[ok] == 0)
    assert set(np.unique(lab.reason[ok])) <= {0, 1, 2}


# ── higher timeframes and causality ────────────────────────────────────

def test_higher_timeframe_atr_and_trend_use_completed_bars_only():
    b = walk(288 * 30, 4)
    assert np.array_equal(np.nan_to_num(OP.tf_trend(b, 60), nan=9), np.nan_to_num(ID.h1_trend(b), nan=9))
    assert np.array_equal(np.nan_to_num(OP.tf_atr(b, 5), nan=9), np.nan_to_num(b.atr, nan=9))
    a60 = OP.tf_atr(b, 60)
    hours = b.t // 3600
    hi = np.array([b.h[hours == u].max() for u in np.unique(hours)])
    lo = np.array([b.l[hours == u].min() for u in np.unique(hours)])
    cl = np.array([b.c[hours == u][-1] for u in np.unique(hours)])
    ref = ID.atr(hi, lo, cl, 14)
    k = 288 * 3 + 12 * 10 + 10  # the 10:50 bar of day 3: hour 10 is still open
    assert a60[k] == pytest.approx(ref[3 * 24 + 9])
    assert a60[k + 1] == pytest.approx(ref[3 * 24 + 10])  # 10:55 closes the hour


def _panel(n=288 * 16, drop=0.01):
    names = list(ID.USD_SIGN)
    return {k: walk(n, 40 + j, k, px=(110.0 if k.endswith("JPY") else 1.1), pip=(0.01 if k.endswith("JPY") else 0.0001),
                    drop=drop) for j, k in enumerate(names)}


def test_no_feature_memory_or_cost_input_reads_a_later_bar():
    panel = _panel()
    ctx = OP.cross_context(panel)
    ticks = {k: np.random.default_rng(1).integers(10, 200, len(b)).astype(float) for k, b in panel.items()}
    full = {k: OP.base_features(b, ticks[k], ctx[k]) for k, b in panel.items()}
    for t_cut in (T0 + 300 * (288 * 12 + 77), T0 + 300 * (288 * 14 + 140)):
        p2 = {k: cut_bars(b, t_cut) for k, b in panel.items()}
        ctx2 = OP.cross_context(p2)
        for k, b2 in p2.items():
            m = len(b2)
            part = OP.base_features(b2, ticks[k][:m], ctx2[k])
            for name in OP.FEATURES:
                assert np.array_equal(np.nan_to_num(full[k][name][:m], nan=9e9), np.nan_to_num(part[name], nan=9e9)), \
                    (k, name, np.flatnonzero(np.nan_to_num(full[k][name][:m], nan=9e9) != np.nan_to_num(part[name], nan=9e9))[:5])
    b = panel["EURUSD"]
    for sc in OP.SCALES:
        mem_full = OP.memory(b, OP.label_scale(b, OP.candidates(b), sc), 20, 10)
        b2 = cut_bars(b, T0 + 300 * (288 * 13 + 150))
        mem_part = OP.memory(b2, OP.label_scale(b2, OP.candidates(b2), sc), 20, 10)
        assert any(np.isfinite(v).sum() > 100 for v in mem_full.values())
        for name, v in mem_part.items():
            assert np.array_equal(np.nan_to_num(mem_full[name][:len(b2)], nan=9), np.nan_to_num(v, nan=9)), (sc, name)
        assert np.array_equal(np.nan_to_num(OP.cost_ratio(b, sc)[:len(b2)], nan=9), np.nan_to_num(OP.cost_ratio(b2, sc), nan=9))


def test_memory_is_the_mean_of_the_last_resolved_grid_trades_only():
    b = walk(288 * 6, 2)
    lab = OP.label_scale(b, OP.candidates(b), "S5")
    mem = OP.memory(b, lab, n_own=5, n_hour=3)
    r = lab.r
    grid = (b.minute[lab.i] % 15 == 0) & (lab.status == 0) & (lab.side == 1)
    for t in (288 * 3 + 150, 288 * 4 + 200, 288 * 5 + 100):
        done = np.flatnonzero(grid & (lab.exit_i < t))
        done = done[np.argsort(lab.exit_i[done], kind="stable")]
        assert mem["mem_long"][t] == pytest.approx(r[done[-5:]].mean(), abs=1e-6)
        same_hour = done[b.hour[lab.i[done]] == b.hour[t]]
        assert mem["memh_long"][t] == pytest.approx(r[same_hour[-3:]].mean(), abs=1e-6)


def test_design_orients_every_feature_to_the_side_and_respects_ablations():
    b = walk(288 * 8, 6)
    base = OP.base_features(b, np.ones(len(b)), None)
    idx = OP.candidates(b)[-50:]
    mem = OP.memory(b, OP.label_scale(b, OP.candidates(b), "S5"))
    cr = OP.cost_ratio(b, "S5")
    xb, names = OP.design(base, idx, 1, cr, mem, 2, 8)
    xs, _ = OP.design(base, idx, -1, cr, mem, 2, 8)
    col = {n: k for k, n in enumerate(names)}
    np.testing.assert_array_equal(xs[:, col["mom12"]], -xb[:, col["mom12"]])
    np.testing.assert_array_equal(xs[:, col["room_up"]], xb[:, col["room_dn"]])
    np.testing.assert_array_equal(xs[:, col["atr_rank"]], xb[:, col["atr_rank"]])
    assert (xb[:, col["side"]] == 1).all() and (xs[:, col["side"]] == -1).all() and (xb[:, col["inst2"]] == 1).all()
    np.testing.assert_array_equal(xs[:, col["mem_own"]], xb[:, col["mem_other"]])
    _, nd = OP.design(base, idx, 1, cr, mem, 2, 8, drop=("liquidity", "memory"))
    assert not {"sw_pd6", "d_pdh", "mem_own"} & set(nd) and "mom1" in nd
    _, no = OP.design(base, idx, 1, cr, mem, 2, 8, only=("liquidity",))
    assert set(no) == {k for k, v in OP.FEATURES.items() if v[0] == "liquidity"}


# ── models and walk-forward ─────────────────────────────────────────────

def test_boosted_trees_find_an_interaction_a_linear_model_cannot_and_are_deterministic():
    rng = np.random.default_rng(0)
    X = rng.normal(0, 1, (40000, 6)).astype(np.float32)
    X[rng.random(X.shape) < 0.02] = np.nan
    truth = 0.5 * np.sign(np.nan_to_num(X[:, 0])) * np.sign(np.nan_to_num(X[:, 1]))
    y = truth + rng.normal(0, 1.0, len(X))
    tr, te = slice(0, 30000), slice(30000, None)
    trees = OP.fit_trees(X[tr], y[tr], rounds=60)
    ridge = OP.fit_ridge(X[tr], y[tr])
    pt, pr = trees.predict(X[te]), ridge.predict(X[te])
    assert np.corrcoef(pt, truth[te])[0, 1] > 0.8
    assert abs(np.corrcoef(pr, truth[te])[0, 1]) < 0.1
    np.testing.assert_array_equal(pt, OP.fit_trees(X[tr], y[tr], rounds=60).predict(X[te]))


def test_walk_forward_trains_only_on_trades_that_exited_before_each_fold():
    n = 5000
    t_entry = np.arange(n) * 3600
    t_exit = t_entry + np.random.default_rng(1).integers(0, 30, n) * 3600
    y = np.random.default_rng(2).normal(0, 1, n)
    seen = []

    class Stub:
        def __init__(self, rows):
            self.rows = rows

        def predict(self, X):
            return np.full(len(X), 1.0)

    def fit(X, yy):
        seen.append(X[:, 0].astype(int))
        return Stub(X)

    folds = [(2000 * 3600, 3000 * 3600), (3000 * 3600, 4000 * 3600)]
    pred = OP.walk_forward(t_entry, t_exit, np.ones(n, bool), y, lambda rows: rows[:, None].astype(float), folds, fit,
                           embargo=86400)
    for (lo, hi), rows in zip(folds, seen):
        assert len(rows) > 1000 and (t_exit[rows] < lo - 86400).all()
        assert set(np.flatnonzero(t_exit < lo - 86400)) == set(rows)
    assert np.isnan(pred[:2000]).all() and np.isfinite(pred[2000:4000]).all() and np.isnan(pred[4000:]).all()


# ── the portfolio is the risk engine's account limits ──────────────────

def test_the_portfolio_enforces_open_symbol_currency_and_daily_loss_limits():
    symbols = ["EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "EURGBP", "NZDCAD"]
    #            sym  t_dec t_free day  r     prio
    rows = [(0, 100, 500, 1, -1.0, 1.0),   # 0 taken
            (0, 110, 600, 1, 1.0, 9.0),    # 1 refused: EURUSD already open
            (1, 120, 500, 1, -1.0, 1.0),   # 2 taken: USD now in two positions
            (2, 130, 500, 1, 1.0, 1.0),    # 3 refused: USD would be in three
            (4, 140, 500, 1, 0.0, 1.0),    # 4 taken: EUR and GBP each in one position
            (5, 150, 500, 1, 1.0, 1.0),    # 5 refused: three positions open
            (3, 600, 900, 1, -1.0, 1.0),   # 6 taken: all flat; the day is at -2R
            (0, 1000, 1100, 1, -2.0, 1.0),  # 7 taken: the day is at -3R (stop at -4R)
            (1, 1200, 1300, 1, 1.0, 1.0),  # 8 refused: the day's closed trades lost 5R
            (1, 1200, 1300, 2, 1.0, 1.0)]  # 9 taken: the next trading day
    a = np.array(rows, float)
    sym, t_dec, t_free, day, r, prio = (a[:, k] for k in range(6))
    chosen = OP.portfolio(sym.astype(int), t_dec, t_free, day.astype(int), r, prio, np.ones(len(a), bool), symbols)
    assert list(chosen) == [0, 2, 4, 6, 7, 9]
    # at the same time, the higher priority wins the last slot
    a2 = np.array([(0, 100, 900, 1, 0, 1.0), (1, 100, 900, 1, 0, 1.0), (2, 100, 900, 1, 0, 5.0), (3, 100, 900, 1, 0, 9.0)])
    ch2 = OP.portfolio(a2[:, 0].astype(int), a2[:, 1], a2[:, 2], a2[:, 3].astype(int), a2[:, 4], a2[:, 5],
                       np.ones(4, bool), symbols, OP.Limits(max_open=3, max_per_currency=3))
    assert sorted(ch2) == [0, 2, 3]


# ── end to end ──────────────────────────────────────────────────────────

def _id2():
    sys.path.insert(0, str(ROOT / "scripts"))
    import id2
    return id2


def test_a_planted_opportunity_is_selected_and_its_matched_random_is_not():
    """Plant: after a strong 12-bar rise during 12:00-14:00 UTC, price drifts up for two hours.
    The engine, given every feature and no hint, must learn it walk-forward and trade it."""
    id2 = _id2()
    rng = np.random.default_rng(21)
    days = 200
    n = 288 * days
    panel = {}
    for k, (s, px) in enumerate((("EURUSD", 1.1), ("GBPUSD", 1.5))):
        steps = rng.normal(0, 0.0004, n)
        mid = px * np.exp(np.cumsum(steps))
        hour = (np.arange(n) * 300 // 3600) % 24
        mv = np.r_[np.zeros(12), np.log(mid[12:] / mid[:-12])]
        sd = 0.0004 * np.sqrt(12)
        trig = np.flatnonzero((mv > 1.5 * sd) & (hour >= 12) & (hour < 14))
        last = -100
        for i in trig:
            if i - last > 24 and i + 30 < n:
                steps[i + 1:i + 25] += 0.00025
                last = i
        mid = px * np.exp(np.cumsum(steps))
        o = np.r_[mid[0], mid[:-1]]
        pad = np.abs(rng.normal(0, 0.0003, n)) * px
        hs = 0.00004 * px
        t = T0 + 300 * np.arange(n)
        h, lo = np.maximum(o, mid) + pad, np.minimum(o, mid) - pad
        panel[s] = ID.Bars(s, 0.0001, t, o - hs, h - hs, lo - hs, mid - hs, o + hs, h + hs, lo + hs, mid + hs)
    P = id2.Panel(None, data=panel)
    sc = "S5"
    T = P.rows[sc]
    tradable = T["status"] == 0
    y = np.where(tradable, T["r"], np.nan).astype(float)
    month = 30 * 86400
    folds = [(T0 + m * month, T0 + (m + 1) * month) for m in range(3, days // 30)]
    pred = OP.walk_forward(T["t_dec"], np.where(tradable, T["t_free"], np.iinfo(np.int64).max), tradable & T["grid"],
                           y, lambda rows: P.X(sc, rows), folds, lambda X, yy: OP.fit_trees(X, yy, rounds=60, min_leaf=300))
    elig = np.isfinite(pred) & (pred > 0.05)
    rows = id2.select(P, sc, elig, np.nan_to_num(pred, nan=-9))
    tr = P.trades(sc, rows)
    s = ID.summarize(tr)
    mr = []
    for seed in (1, 2, 3):
        mr += P.trades(sc, id2.matched_rows(P, sc, rows, seed))
    m = ID.summarize(mr)
    assert s["trades"] >= 60, s
    assert s["net_r"] > 0.1 and m["net_r"] < s["net_r"] - 0.15
    buys = [t for t in tr if t.side == 1]
    sells = [t for t in tr if t.side == -1]
    assert np.mean([t.r for t in buys]) > 0.2  # unconditional BUYs here: about -0.17R
    # only BUYs were planted: a selected SELL that also profited would be information from the future
    assert np.mean([t.r for t in sells]) < 0.05
    inside = [t.r for t in buys if 12 <= (t.entry_t // 3600) % 24 < 16]
    outside = [t.r for t in buys if not 12 <= (t.entry_t // 3600) % 24 < 16]
    assert len(inside) > 30 and np.mean(inside) > np.mean(outside) + 0.3  # the edge sits where it was planted


def test_the_id2_runner_judges_every_configuration_and_promotes_nothing_on_a_random_walk(tmp_path, monkeypatch):
    id2 = _id2()
    t0 = int(datetime(2010, 11, 1, tzinfo=timezone.utc).timestamp())
    n = 288 * 425
    panel = {s: walk(n, 60 + k, s, px=1.1 + 0.3 * k, t0=t0, drop=0.001) for k, s in enumerate(("EURUSD", "GBPUSD"))}
    monkeypatch.setattr(id2, "CACHE", tmp_path)
    monkeypatch.setattr(OP, "SCALES", {"S5": (5, 48), "S60": (60, 144)})
    monkeypatch.setattr(OP, "GROUPS", ("liquidity", "memory"))
    monkeypatch.setattr(OP, "FAMILIES", {"ridge": OP.fit_ridge,
                                         "trees": lambda X, y: OP.fit_trees(X, y, rounds=5, min_leaf=300)})
    monkeypatch.setattr(id2, "DEV_OOS", (date(2011, 1, 1), date(2012, 1, 1)))
    monkeypatch.setattr(id2, "FOLDS_DEV", (2011,))
    monkeypatch.setattr(id2, "VAL", (date(2011, 7, 1), date(2012, 1, 1)))
    monkeypatch.setattr(id2, "FOLDS_VAL", (2011,))
    P = id2.Panel(None, data=panel)
    body = {"controls": {}}
    promoted = id2.development(P, body)
    assert promoted == []  # a random walk passes nothing
    hyps = set(body["development"])
    assert len(hyps) == 2 * 2 * len(id2.TAUS) + len(id2.RULES) * 2
    any_trades = [h for h, v in body["development"].items() if v["summary"]["trades"]]
    assert {h for h in hyps if h.startswith("R-")} <= set(any_trades)
    for h in any_trades:
        v = body["development"][h]
        assert set(v["gates"]) == {"min_trades", "net_r", "t_day", "profit_factor", "costs_x1.25", "beats_matched_random",
                                   "symbols_positive"}
        assert v["summary"]["net_r"] < 0.15
        d = v["detail"]
        assert {"1m", "3m", "6m"} <= set(d["windows"]) and "weekly" in d and "direction" in d
        assert d["concurrency"]["max_simultaneous"] <= 2  # two instruments
    assert set(body["controls"]) == {"RANDOM-S5", "RANDOM-S60"}
    assert body["controls"]["RANDOM-S5"]["development"]["net_r"] < 0
    assert {"spearman_ic", "deciles"} <= set(body["ranking"]["trees-S5"])
    id2.ablations(P, body)
    assert set(body["ablations"]) >= {"ridge-S5-drop-liquidity", "ridge-S60-only-memory"}
    v = id2.validate(P, "M-ridge-S5-tau0.00", body["development"]["M-ridge-S5-tau0.00"], 3.0)
    assert set(v["stress"]) == {"x1.25", "x1.5", "x2.0", "slippage_0.3"} and len(v["neighbours"]) == 2
    assert v["passed"] is False
    v2 = id2.validate(P, "R-MOM-S60", body["development"]["R-MOM-S60"], 3.0)
    assert "neighbours" in v2["gates"] and v2["passed"] is False


def test_the_id2_design_is_frozen_once_registered():
    import json
    id2 = _id2()
    spec = ROOT / "research" / "specs" / "ID-2.json"
    if not spec.exists():
        pytest.skip("ID-2 not yet specified")
    frozen = json.loads(spec.read_text())
    assert frozen["code_sha256"] == id2.code_hash(), "ID-2 code changed after its spec was frozen"
    assert frozen["sha256"] == id2.spec_sha(frozen["spec"])
