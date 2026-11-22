"""TRINITY-MASTER's rules as ported (aitrader/position/trinity.py), checked against the owner's package itself
(research/external/trinity/trinity_omega_suite.py): the same features, the same weights on every row, the same
equity; the grid, the sensors at t-1, and no row reading a later one."""

import hashlib
import importlib.util
import inspect
import math
from datetime import date, timedelta
from pathlib import Path

import pytest

from aitrader.position import trinity as T

ROOT = Path(__file__).resolve().parents[2]
PKG_PATH = ROOT / "research" / "external" / "trinity" / "trinity_omega_suite.py"


@pytest.fixture(scope="module")
def pkg():
    spec = importlib.util.spec_from_file_location("trinity_omega_suite_as_received", PKG_PATH)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def _base_rows(pkg):
    base = pkg.FULL_PANEL[["date", "QQQ", "SPY", "GLD", "UUP", "TLT", "VIX", "DBC"]]
    return [{k: (r[k].date() if k == "date" else float(r[k])) for k in base.columns} for _, r in base.iterrows()]


def test_the_package_is_the_one_received():
    assert hashlib.sha256(PKG_PATH.read_bytes()).hexdigest() == T.SOURCE_SHA256


def test_the_weight_functions_are_the_package_s_own_text(pkg):
    for name in ("_apply_dd_brake", "weights_trnd1_pro", "weights_nexus4_pro", "weights_omega_apex",
                 "weights_trinity_master"):
        theirs = inspect.getsource(getattr(pkg, name)).replace("row: pd.Series", "row: dict")
        assert inspect.getsource(getattr(T, name)) == theirs, name


def test_every_feature_equals_the_package_s(pkg):
    feat = T.features(_base_rows(pkg))
    cols = [c for c in pkg.FULL_PANEL.columns if c != "date" and not c.startswith("fwd_")]
    checked = 0
    for i, (_, pr) in enumerate(pkg.FULL_PANEL.iterrows()):
        for c in cols:
            a, b = feat[i][c], float(pr[c])
            assert math.isnan(a) == math.isnan(b), (i, c, a, b)
            if not math.isnan(b):
                assert abs(a - b) <= 1e-12 * max(1.0, abs(b)), (i, c, a, b)
                checked += 1
    assert checked > 24_000


def test_every_decision_equals_the_package_s_loop(pkg):
    dec = T.decide(T.features(_base_rows(pkg)))
    cum = pk = 0.0
    prev = {a: 0.0 for a in pkg.ASSETS}
    for k, (_, row) in enumerate(pkg.V20_PANEL.iterrows()):
        w = pkg.weights_trinity_master(row, cum - pk)
        c = sum(abs(w[a] - prev[a]) for a in pkg.ASSETS) * pkg.COST_BPS_DEFAULT
        cum += sum(w[a] * row[f"fwd_{a}"] for a in pkg.ASSETS) - c
        pk = max(pk, cum)
        prev = dict(w)
        d = dec[k]
        assert d["date"] == row["date"].date()
        assert max(abs(d["weights"][a] - w[a]) for a in pkg.ASSETS) < 1e-12
        assert sorted(d["buy"]) == sorted(pkg.CTRADER_SYMBOL_MAP[a]["canonical"] for a in pkg.ASSETS if w[a] > 1e-4)
        assert abs(d["cum"] - cum) < 1e-12
    # the package's table: +$270,973 on $200,000 over its 288 periods
    assert round(cum * 200_000) == 270_973
    # one more row than the package judged: its last close, decided, with no return yet
    assert len(dec) == len(pkg.V20_PANEL) + 1 and dec[-1]["ret"] is None and dec[-1]["cum"] is None


def test_the_map_and_the_constants_are_the_package_s(pkg):
    assert T.CFD_OF == {a: v["canonical"] for a, v in pkg.CTRADER_SYMBOL_MAP.items()}
    assert T.STEP == pkg.DAILY_LOOKBACK_EQUIVALENTS["rebalance_trading_days"] == 15
    assert T.COST == pkg.COST_BPS_DEFAULT
    assert inspect.signature(pkg.build_hard_gate_orders).parameters["stop_rel"].default == T.STOP_REL


def _days(n, start=date(2026, 1, 5)):
    out, d = [], start
    while len(out) < n:
        if d.weekday() < 5:
            out.append(d)
        d += timedelta(days=1)
    return out


def test_the_grid_is_every_fifteenth_trading_day_through_the_anchor():
    days = _days(100)
    g = T.grid(days, days[40])
    assert days[40] in g and days[25] in g and days[55] in g and days[10] in g
    assert all((days.index(d) - 40) % 15 == 0 for d in g)
    assert len(g) == len(range(10, 100, 15))
    with pytest.raises(ValueError):
        T.grid(days, date(2026, 1, 3))  # a Saturday is not a trading day


def _closes(days, f=lambda i, s: 100.0 + i):
    return {s: {d: float(f(i, s)) for i, d in enumerate(days)} for s in T.ASSETS + T.SENSORS}


def test_the_sensors_are_read_at_the_trading_day_before_the_grid_day():
    days = _days(60)
    closes = _closes(days)
    g = T.grid(days, days[30])
    rows = T.rows_at(g, closes, days)
    r30 = next(r for r in rows if r["date"] == days[30])
    assert r30["QQQ"] == 130.0 and r30["VIX"] == 129.0  # assets on the day, sensors the day before
    closes["VIX"][days[30]] = 999.0  # the grid day's own VIX is not read
    assert next(r for r in T.rows_at(g, closes, days) if r["date"] == days[30])["VIX"] == 129.0
    closes["VIX"][days[29]] = 55.0
    assert next(r for r in T.rows_at(g, closes, days) if r["date"] == days[30])["VIX"] == 55.0


def test_a_missing_close_is_an_error_never_a_filled_value():
    days = _days(60)
    closes = _closes(days)
    del closes["TLT"][days[29]]
    with pytest.raises(ValueError, match="missing"):
        T.rows_at(T.grid(days, days[30]), closes, days)


def test_no_decision_reads_a_later_row(pkg):
    rows = _base_rows(pkg)
    full = T.decide(T.features(rows))
    cut = 150
    part = T.decide(T.features(rows[:cut + 1]))
    for a, b in zip(full[:cut - T.WARMUP + 1], part):
        assert a["date"] == b["date"] and a["weights"] == b["weights"] and a["buy"] == b["buy"]
    # moving every later close moves nothing before it
    shocked = [dict(r) for r in rows]
    for r in shocked[cut + 1:]:
        for k in ("QQQ", "SPY", "GLD", "DBC", "UUP", "TLT", "VIX"):
            r[k] *= 0.5
    again = T.decide(T.features(shocked))
    assert [x["weights"] for x in again[:cut - T.WARMUP + 1]] == [x["weights"] for x in part]


def test_a_decision_needs_its_warm_up():
    with pytest.raises(ValueError):
        T.decide([], book_start=T.WARMUP - 1)
