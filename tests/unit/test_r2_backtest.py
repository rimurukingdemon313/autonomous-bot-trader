"""The Round 2 descriptive backtest (scripts/r2_backtest.py) on markets built so the answer is known: every Sunday
swap at every threshold with each fill's cost charged twice, the rule on every weekday, weekly compounding, every
premium trade (fresh or not) with one position per coin, the position simulation's cap and arithmetic, a frozen
study spec left exactly as registered, and nothing reported on a partial panel."""

import math
from datetime import datetime, timezone

import pytest

from aitrader.research.events import korea as K
from aitrader.research.events import stablecoin as C
from scripts import krp1 as K1
from scripts import r2_backtest as B
from tests.unit.test_krp1 import _days, _panel

H = C.HOUR
WEEKS = 60


def _stable(dev: float = -0.0012) -> tuple[dict[str, dict[int, float]], tuple[str, str]]:
    """One pair at par, except that the hour closing at 22:00 UTC on each Sunday closes at exp(dev)."""
    t0 = C.ms_of("2021-01-03")  # a Sunday
    b = {t0 + i * H: 1.0 for i in range(-2 * 24, WEEKS * 7 * 24 + 3 * 24)}
    for w in range(WEEKS):
        b[t0 + w * 7 * 24 * H + 21 * H] = math.exp(dev)
    sundays = C.weekdays_in("2021-01-03", "2030-01-01", 6)
    return {"USDCUSDT": b}, ("2021-01-03", sundays[WEEKS - 1])


def test_every_sunday_swap_at_every_threshold_with_each_fill_charged_twice():
    bars, window = _stable()
    s = B.scx_rows(bars, window)
    reg = s["thetas"]["0.001"]
    assert reg["gross"]["n"] == WEEKS and abs(reg["gross"]["mean"] - 0.0012) < 1e-12
    assert abs(reg["net"]["1bp_a_fill"]["mean"] - (0.0012 - 0.0002)) < 1e-12
    assert abs(reg["net"]["10bp_a_fill"]["mean"] - (0.0012 - 0.0020)) < 1e-12  # Binance's standard fee: a loss
    assert s["thetas"]["0.002"]["gross"] == {"n": 0} and s["thetas"]["0.005"]["gross"] == {"n": 0}
    assert len(s["registered_rule_trades"]) == WEEKS
    eq = reg["equity_at_1bp_a_fill"]
    assert abs(eq["end"] - B.CAPITAL * (1 + math.expm1(0.0012) - 0.0002) ** WEEKS) < 1e-6
    assert eq["max_drawdown"] == 0.0 and reg["equity_at_10bp_a_fill"]["end"] < B.CAPITAL
    assert reg["by_year_at_1bp_a_fill"]["2021"]["n"] == 52


def test_the_same_rule_on_every_weekday_shows_whether_sunday_stands_apart():
    bars, window = _stable()
    w = B.scx_rows(bars, window)["weekdays_at_10bp"]
    assert w["Sunday"]["gross"]["n"] == WEEKS
    assert all(w[d]["gross"] == {"n": 0} for d in B.WEEKDAYS if d != "Sunday")  # at par on the other days


def test_every_premium_day_is_a_trade_while_only_a_fresh_one_is_an_entry_of_the_registered_kind():
    p = _panel(persistent=True)
    days = _days()
    look = K.days_with_lookback(days, K1.SPEC["trailing_days"])
    series = {c: K.rho_series(p, c, look) for c in p.coins}
    spec = B.krp_spec(24)
    fresh = [e for e in K.entries(p, days, 0.05, +1, spec, series=series) if not e.get("missing")]
    anyp = [e for e in B.any_entries(p, days, 0.05, +1, spec, series) if not e.get("missing")]
    assert fresh == [] and len(anyp) >= 80 and {e["coin"] for e in anyp} == {"AAA"}
    t_ins = sorted(K.ms_of(e["day"]) for e in anyp)
    assert all(b - a >= K.DAY for a, b in zip(t_ins, t_ins[1:]))  # one position per coin at a time
    held = [e for e in B.any_entries(p, days, 0.05, +1, B.krp_spec(72), series) if not e.get("missing")]
    gaps = [K.ms_of(b["day"]) - K.ms_of(a["day"]) for a, b in zip(held, held[1:])]
    assert held and all(g >= 3 * K.DAY for g in gaps)  # a 72-hour position blocks the coin for three days
    assert B.any_entries(p, days, 0.05, -1, spec, series) == []  # a premium is no discount
    capped = _panel(spike_rho=1.5, persistent=True)
    s2 = {c: K.rho_series(capped, c, look) for c in capped.coins}
    assert B.any_entries(capped, days, 0.05, +1, spec, s2) == []  # beyond the cap: a data mismatch, not a trade


def test_a_fresh_spike_is_found_by_both_and_the_rows_cover_every_threshold_and_hold():
    p = _panel()
    k = B.krp_rows(p, ("2024-02-05", "2024-04-30"))
    reg = k["fresh"]["0.05@24h"]
    assert reg["gross"]["n"] == 1 and abs(reg["gross"]["mean"] - 0.03) < 1e-9  # the built 3% rise against bitcoin
    assert abs(reg["net"]["0.006"]["mean"] - 0.024) < 1e-9 and k["registered_rule_trades"][0]["coin"] == "AAA"
    assert k["any_premium"]["0.05@24h"]["gross"]["n"] == 1 and k["korean_discounts"]["0.05@24h"]["gross"] == {"n": 0}
    assert set(k["fresh"]) == {f"{t:g}@{h}h" for t in B.KRP_THETAS for h in B.KRP_HOLDS}
    assert k["fresh"]["0.1@24h"]["gross"] == {"n": 0}  # 8% does not reach 10%


def test_the_position_simulation_books_at_exit_and_caps_open_positions(monkeypatch):
    evs = [{"day": "2024-01-01", "excess": 0.05}, {"day": "2024-01-01", "excess": -0.02},
           {"day": "2024-01-03", "excess": -0.01}]
    monkeypatch.setattr(B, "KRP_MAX_OPEN", 1)
    r = B.simulate(evs, 24, 0.006, ("2024-01-01", "2025-01-01"))
    first = B.CAPITAL + B.KRP_ALLOC * B.CAPITAL * (0.05 - 0.006)
    second = first + B.KRP_ALLOC * first * (-0.01 - 0.006)
    assert r["trades_taken"] == 2 and r["skipped_at_the_cap"] == 1 and r["won"] == 1
    assert abs(r["end"] - second) < 1e-9 and r["max_drawdown"] < 0


def test_the_frozen_study_spec_is_left_as_registered_and_a_partial_panel_reports_nothing(tmp_path):
    before = K1.spec_sha()

    def fails(url):
        raise RuntimeError(f"{url}: timed out")
    small = tmp_path / "krp-probe.json"  # one coin, so the panel stays small
    small.write_text('{"coins": {"AAA": {"binance_1h": ["2019-01"], "upbit_listed_now": true}}, "btc_1h": ["2019-01"]}')
    with pytest.raises(SystemExit, match="did not arrive"):
        B.fetch_krp(small, fetch_up=fails, fetch_bn=fails)
    assert K1.spec_sha() == before and "full" not in K1.SPEC["stages"]
    probe = tmp_path / "probe.json"
    probe.write_text('{"pairs": {"USDCUSDT": ["2019-01"]}}')
    with pytest.raises(SystemExit, match="SCX-1 archive files did not arrive"):
        B.fetch_scx(probe, fails)
    with pytest.raises(SystemExit, match="did not arrive"):
        B.run(tmp_path / "out", datetime(2026, 11, 22, tzinfo=timezone.utc), fetch_scx_fn=fails, fetch_up=fails,
              fetch_bn=fails, scx_probe=probe, krp_probe=small)
    assert not (tmp_path / "out").exists()


def test_the_report_labels_itself_descriptive_and_names_the_months_it_spends():
    bars, window = _stable()
    p = _panel()
    body = {"what": B.LABEL, "version": B.R2BT_VERSION, "run_at": "2026-11-22T00:00:00+00:00", "spends": "x",
            "scx": {**B.scx_rows(bars, window), "data": {"files": 1, "absent": 0, "last_moment_read": "t"}},
            "krp": {**B.krp_rows(p, ("2024-02-05", "2024-04-30")),
                    "data": {"binance_files": 1, "binance_absent": 0, "upbit_markets": 3, "upbit_absent": 0,
                             "last_moment_read": "t"}}}
    md = B.markdown(body)
    assert "NOT A TEST" in md and "(registered)" in md and "| Sunday |" in md
    assert "5%, 24h (registered)" in md and "10 bp (registered)" in md
