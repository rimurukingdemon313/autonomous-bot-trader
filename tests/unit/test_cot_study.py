"""COT-1 study machinery, on markets built so the right answer is known in advance.

The planted market: weekly reports whose Leveraged Money position is ordinary noise, except on
planted weeks where it sits far above (bullish) or below (bearish) its 52-week history; after each
planted report's decision bar the CURRENCY moves in the direction of the positioning for exactly
the five bars a D3 trade holds. So trading WITH the extreme (p_cont) wins by construction, trading
against it (p_rev) loses, on a CCYUSD pair and an inverted USDCCY pair alike.
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
import zipfile
from datetime import date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo

import numpy as np
import pytest

from aitrader.data import cot as cot_data
from aitrader.data.bars import BarSeries
from aitrader.data.cot import CotSeries, CotStore, available_at
from aitrader.data.external import ExternalSeries
from aitrader.research.discovery import cot as cot_mod
from aitrader.research.discovery.battery import BatteryRules, regime_binnings, run_battery
from aitrader.research.discovery.cot import (RULES, RuleSignal, SignedStudy, lagged, pair_sides, trailing,
                                             truncation_leaks, weekly)
from aitrader.research.discovery.edges import build, judged_status
from aitrader.research.discovery.exits import EXIT_BY_KEY
from aitrader.research.discovery.hypothesis import Hypothesis, LedgerError
from aitrader.research.discovery.study import Segment, SymbolData
from aitrader.research.labels import BUY, CostModel, atr24
from aitrader.research.registry import Holdout

NY = ZoneInfo("America/New_York")
START = date(2009, 1, 5)  # a Monday, in winter
WEEKS = 140


def ny17(d: date) -> int:
    return int(datetime(d.year, d.month, d.day, 17, tzinfo=NY).timestamp())


def weekdays(start: date, weeks: int) -> list[date]:
    return [start + timedelta(days=7 * w + k) for w in range(weeks) for k in range(5)]


def bars(symbol: str, days: list[date], mid: np.ndarray, half: float = 0.00002) -> BarSeries:
    close_t = np.array([ny17(d) for d in days], np.int64)
    o = np.concatenate(([mid[0]], mid[:-1]))
    hi, lo = np.maximum(o, mid) + 0.0003, np.minimum(o, mid) - 0.0003
    n = len(mid)
    return BarSeries.from_columns(symbol, "D1", "synthetic", open_time=close_t - 86400,
                                  bid_open=o - half, bid_high=hi - half, bid_low=lo - half, bid_close=mid - half,
                                  ask_open=o + half, ask_high=hi + half, ask_low=lo + half, ask_close=mid + half,
                                  ticks=np.full(n, 100), spread_mean=np.full(n, 2 * half),
                                  spread_max=np.full(n, 4 * half))


def cot_series(ccy: str, as_of: list[date], spec: np.ndarray) -> CotSeries:
    oi = np.full(len(spec), 1000.0)
    z = np.zeros(len(spec))
    fields = {"oi": oi, "lev_long": 100 + 1000 * np.maximum(spec, 0), "lev_short": 100 + 1000 * np.maximum(-spec, 0),
              "dealer_long": z, "dealer_short": z, "am_long": z, "am_short": z, "other_long": z, "other_short": z,
              "nonrept_long": z, "nonrept_short": z}
    return CotSeries(ccy, np.array([int(datetime(d.year, d.month, d.day, tzinfo=timezone.utc).timestamp())
                                    for d in as_of], np.int64),
                     np.array([available_at(d) for d in as_of], np.int64), fields)


def planted(symbol: str, seed: int = 1, plant: bool = True, drift: float = 0.004):
    """Bars and a COT series for one pair; returns (series, cot, planted report indices, their signs)."""
    rng = np.random.default_rng(seed)
    days = weekdays(START, WEEKS)
    as_of = [START + timedelta(days=1 + 7 * w) for w in range(WEEKS - 1)]  # Tuesdays
    spec = rng.normal(0, 0.05, len(as_of))
    idx = np.arange(56, len(as_of) - 2, 5)
    signs = np.where(np.arange(len(idx)) % 2 == 0, 1, -1)
    spec[idx] = signs * 0.5  # far outside a year of N(0, 0.05) history: an extreme by construction
    ccy, orient = cot_mod.PAIRS[symbol]
    steps = rng.normal(0, 0.0004, len(days))
    cot = cot_series(ccy, as_of, spec)
    t_close = np.array([ny17(d) for d in days], np.int64)
    if plant:
        for j, sg in zip(idx, signs):
            i = int(np.searchsorted(t_close, cot.available_at[j], side="left"))
            steps[i + 1:i + 6] += orient * sg * drift  # the currency follows the positioning for 5 bars
    mid = 1.3 + np.cumsum(steps)
    return bars(symbol, days, mid), cot, idx, signs


def symbol_data(series: BarSeries, seed: int = 3) -> SymbolData:
    rng = np.random.default_rng(seed)
    n = len(series)
    return SymbolData(series.symbol, series, 0.0001, {"er120": rng.random(n), "vol_ratio": rng.random(n)},
                      atr24(series))


# ── features ─────────────────────────────────────────────────────────────────────────────────────

def test_trailing_percentile_and_z_use_only_the_previous_52_weeks():
    days = np.arange(0, 7 * 60, 7)
    x = np.arange(60, dtype=float)
    pct, z = trailing(x, days)
    assert np.isnan(pct[:39]).all()  # fewer than 39 earlier reports: unknown, never a default
    assert pct[39] == 1.0 and pct[59] == 1.0  # a new high beats every earlier value
    x2 = x.copy()
    x2[59] = -1.0
    assert trailing(x2, days)[0][59] == 0.0
    # the report exactly 52 weeks earlier is inside the window; 53 weeks earlier is not
    lo = np.searchsorted(days, days[59] - 364, side="left")
    assert days[lo] == days[59] - 364
    assert z[59] == pytest.approx((59 - x[lo:59].mean()) / x[lo:59].std(ddof=1))


def test_lagged_takes_the_report_four_weeks_back_and_never_invents_one():
    days = np.array([0, 7, 14, 21, 28, 35, 49])
    x = np.arange(7, dtype=float)
    lg = lagged(x, days, (25, 31))
    assert np.isnan(lg[:4]).all()
    assert lg[4] == 0.0 and lg[5] == 1.0
    assert lg[6] == 3.0  # day 49: the report of day 21 (28 days back), not a gap-filled one


def test_a_report_decides_on_the_monday_bar_that_closes_at_its_release():
    s, cot, idx, _ = planted("EURUSD")
    w = weekly(s, cot)
    j = 60
    i = int(w.row[j])
    assert s.available_at[i] == cot.available_at[j]  # Monday 17:00 New York, as-of + 6 days
    assert datetime.fromtimestamp(int(s.available_at[i]), NY).weekday() == 0


def test_a_report_superseded_before_any_bar_closed_makes_no_decision():
    s, cot, _, _ = planted("EURUSD")
    gap = (s.available_at <= cot.available_at[60]) | (s.available_at >= cot.available_at[62])
    w = weekly(s.take(np.flatnonzero(gap)), cot)
    assert w.row[60] >= 0 and w.row[61] == -1 and w.row[62] >= 0


def test_usd_quote_pairs_invert_the_currency_signal():
    s_e, cot, idx, signs = planted("EURUSD")
    s_j, cot_j, _, _ = planted("USDJPY")
    w_e, w_j = weekly(s_e, cot), weekly(s_j, cot_j)
    j = idx[0]
    sides_e = pair_sides(RULES["p_cont"], w_e)
    sides_j = pair_sides(RULES["p_cont"], w_j)
    assert sides_e[w_e.row[j]] == signs[0]  # bullish EUR -> buy EURUSD
    assert sides_j[w_j.row[j]] == -signs[0]  # bullish JPY -> sell USDJPY
    assert (pair_sides(RULES["p_rev"], w_e) == -sides_e).all()


def test_every_rule_and_control_shares_one_decision_set():
    s, cot, _, _ = planted("EURUSD")
    w = weekly(s, cot)
    undefined = ~np.isfinite(w.f["spec_pct"])
    for rule in RULES.values():
        assert (rule.direction(w)[undefined] == 0).all(), rule.name
    trend = RULES["a_trend"].direction(w)
    assert ((RULES["x_veto"].direction(w) != 0) | (RULES["a_trend_uncrowded"].direction(w) != 0)
            == (trend != 0)).all()  # crowded + uncrowded = the trend control, exactly


# ── point in time ────────────────────────────────────────────────────────────────────────────────

def _vix(days: list[date]) -> ExternalSeries:
    obs = np.array([int(datetime(d.year, d.month, d.day, tzinfo=timezone.utc).timestamp()) for d in days], np.int64)
    av = np.array([int(datetime(d.year, d.month, d.day, 16, 45, tzinfo=NY).timestamp()) for d in days], np.int64)
    return ExternalSeries("vix", obs, 15 + 10 * np.abs(np.sin(np.arange(len(days)) / 9)), av)


def test_no_feature_or_rule_changes_when_everything_after_the_decision_is_cut():
    s, cot, _, _ = planted("USDCHF")
    vix = _vix(weekdays(START, WEEKS))
    rows = weekly(s, cot, vix).row
    rows = rows[rows >= 0][45::7]
    bad = truncation_leaks(s, cot, vix, rows)
    assert len(rows) >= 8 and all(not v for v in bad.values()), {k: v for k, v in bad.items() if v}


def test_the_truncation_check_catches_a_planted_look_ahead(monkeypatch):
    s, cot, _, _ = planted("EURUSD")
    rows = weekly(s, cot).row
    rows = rows[rows >= 0][60::9]
    monkeypatch.setattr(cot_mod, "lagged", lambda x, days, window: np.append(x[1:], np.nan))  # the NEXT report
    bad = truncation_leaks(s, cot, None, rows)
    assert bad["spec_flow_pct"] or bad["spec_step"]


# ── trades ───────────────────────────────────────────────────────────────────────────────────────

def _study(symbols=("EURUSD", "USDJPY"), plant=True):
    data, ws = {}, {}
    for k, sym in enumerate(symbols):
        s, cot, _, _ = planted(sym, seed=10 + k, plant=plant)
        data[sym] = symbol_data(s, seed=20 + k)
        ws[sym] = weekly(s, cot)
    fit = Segment("fit", "fit", START, date(2009, 12, 1))
    seg = Segment("judged", "judge", date(2010, 1, 15), date(2011, 8, 1))
    base = SignedStudy(data, fit, {}, CostModel(swap_atr_per_night=0.01), purge_bars=6)
    ctx = regime_binnings({f: {s: data[s].columns[f][base.rows[s]] for s in data} for f in ("er120", "vol_ratio")})
    return SignedStudy(data, seg, {}, CostModel(swap_atr_per_night=0.01), purge_bars=6, context=ctx), ws


def test_trading_with_the_planted_extreme_wins_and_against_it_loses_on_both_orientations():
    study, ws = _study()
    cont = study.trades(RuleSignal(RULES["p_cont"], ws).masks(study), "D3")
    rev = study.trades(RuleSignal(RULES["p_rev"], ws).masks(study), "D3")
    assert cont.n == rev.n >= 20
    assert set(cont.symbol) == {"EURUSD", "USDJPY"}
    assert cont.r.mean() > 0.5 and rev.r.mean() < -0.5
    for sym in ("EURUSD", "USDJPY"):
        assert cont.r[cont.symbol == sym].mean() > 0.3
    assert set(np.unique(cont.context["side"])) == {-1, 1}


def test_one_position_per_instrument_across_both_sides():
    study, ws = _study(symbols=("EURUSD",))
    rows = study.rows["EURUSD"]
    d3 = EXIT_BY_KEY["D3"]
    buy, sell = study.outcome("EURUSD", d3, BUY, "base"), study.outcome("EURUSD", d3, -1, "base")
    m = np.zeros(len(rows), np.int8)
    m[40], m[41], m[44], m[70] = 1, -1, -1, -1
    tr = study.trades({"EURUSD": m}, "D3")
    # expected by hand: the buy at 40 blocks every signal until its own exit, whichever side it is
    want, free = [], 0
    for p, o in ((40, buy), (41, sell), (44, sell), (70, sell)):
        if p >= free:
            want.append(p)
            free = int(o["free"][p])
    assert 41 not in want  # one bar into a 5-bar trade is always blocked
    assert list(tr.row) == [rows[p] for p in want]
    assert list(tr.context["side"]) == [1 if p == 40 else -1 for p in want]
    spans = sorted(zip(tr.row, tr.row + tr.bars))
    assert all(b[0] >= a[1] for a, b in zip(spans, spans[1:]))


def test_the_battery_judges_a_signed_rule_and_random_entries_take_random_sides():
    study, ws = _study()
    res = run_battery(study, RuleSignal(RULES["p_cont"], ws), BUY, "D3", BatteryRules(t_threshold=3.0, min_trades=10,
                      permutations=40, random_draws=5), key="t")
    assert res["checks"]["significance"]["pass"] and res["checks"]["beats_random"]["pass"]
    assert len(res["checks"]["perturbation"]["mean_R"]) == 2  # the two neighbouring threshold pairs
    m = study.random_masks({"EURUSD": 200}, np.random.default_rng(0))["EURUSD"]
    assert (m != 0).sum() == 200 and set(np.unique(m[m != 0])) == {-1, 1}


def test_in_a_world_without_the_effect_neither_mapping_wins():
    study, ws = _study(plant=False)
    for name in ("p_cont", "p_rev"):
        tr = study.trades(RuleSignal(RULES[name], ws).masks(study), "D3")
        assert abs(tr.r.mean()) < 0.35, name


# ── loader ───────────────────────────────────────────────────────────────────────────────────────

def _tff(rows: list[tuple[str, str, str]]) -> bytes:
    cols = ["As_of_Date_In_Form_YYMMDD", "CFTC_Contract_Market_Code", "FutOnly_or_Combined"] + list(cot_data.FIELDS.values())
    buf = io.StringIO()
    wr = csv.writer(buf)
    wr.writerow(cols)
    for d, code, kind in rows:
        wr.writerow([d, code, kind] + ["100"] * len(cot_data.FIELDS))
    return buf.getvalue().encode("latin-1")


def test_the_loader_drops_shutdown_reports_and_refuses_mixed_report_types():
    raw = _tff([("130924", "099741", "FutOnly"), ("131001", "099741", "FutOnly"), ("131231", "099741", "FutOnly"),
                ("130924", "999999", "FutOnly")])
    eur = cot_data.parse({"a": raw})["EUR"]
    assert len(eur) == 2  # 2013-10-01 has no verifiable release date: dropped, not dated by guess
    assert eur.available_at[0] == ny17(date(2013, 9, 30))
    with pytest.raises(ValueError):
        cot_data.parse({"a": _tff([("130924", "099741", "FutAndOpt")])})


def test_the_store_verifies_the_files_and_seals_the_holdout(tmp_path):
    root = tmp_path / "cot"
    root.mkdir()
    files = {}
    for (zname, member), body in zip(cot_data.FILES.items(),
                                     (_tff([("161220", "099741", "FutOnly")]), _tff([("170103", "099741", "FutOnly")]))):
        with zipfile.ZipFile(root / zname, "w") as z:
            z.writestr(member, body)
        files[zname] = {"zip_sha256": hashlib.sha256((root / zname).read_bytes()).hexdigest()}
    (root / "manifest.json").write_text(json.dumps({"files": files}))
    h = Holdout("fx-majors", date(2017, 1, 1), datetime(2026, 1, 1, tzinfo=timezone.utc), "test")
    assert len(CotStore(root, h).load()["EUR"]) == 1  # the 2017 report is sealed
    assert len(CotStore(root, h).load(key=object())["EUR"]) == 2
    (root / "manifest.json").write_text(json.dumps({"files": {k: {"zip_sha256": "0" * 64} for k in files}}))
    with pytest.raises(ValueError):
        CotStore(root, h).load()


# ── registry semantics ───────────────────────────────────────────────────────────────────────────

def _checks(gate_ok: bool) -> dict:
    return {"significance": {"pass": False, "mean_R": 0.2, "t": 2.5}, "costs_stress": {"pass": True},
            "beats_random": {"pass": True}, "validation": {"pass": gate_ok, "gate": True}}


def test_a_failed_preregistered_gate_is_never_promising():
    assert judged_status(False, _checks(True)) == "PROMISING"
    assert judged_status(False, _checks(False)) == "REJECTED"


def test_a_holdout_record_supersedes_the_record_it_judged(tmp_path):
    (tmp_path / "discovery").mkdir()
    (tmp_path / "discovery" / "ledger.jsonl").write_text("")
    k = tmp_path / "knowledge"
    k.mkdir()
    entry = {"id": "H-1", "side": "SIGNED", "condition": "rule:p_rev", "exit": "D3", "kind": "opportunity",
             "battery": {"failed": [], "checks": _checks(True)}}
    (k / "P.json").write_text(json.dumps({"program": "P", "judged": [entry], "validated": []}))
    (k / "P-H.json").write_text(json.dumps({"program": "P-H", "holdout_of": "P", "judged": [entry],
                                            "validated": ["H-1"]}))
    reg = build(tmp_path)
    assert [(e["edge_id"], e["program"], e["status"]) for e in reg["edges"]] == [("H-1", "P-H", "VALIDATED")]


def test_a_signed_side_belongs_to_a_rule_and_only_to_a_rule():
    base = dict(id="X-1", statement="s", rationale="r", mechanism="m", features=("f@1",), condition="rule:p_rev",
                side="SIGNED", instruments=("EURUSD",), timeframe="D1", exit="D3", expected_effect="e",
                falsification=("x",), budget=1, origin="human", program="X")
    Hypothesis(**base).validate()
    for bad in ({"side": "BUY"}, {"condition": "r1=high"}, {"condition": "rule:"}):
        with pytest.raises(LedgerError):
            Hypothesis(**(base | bad)).validate()
