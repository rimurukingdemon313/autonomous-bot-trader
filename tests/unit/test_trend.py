"""DIV-1 trend study: a planted trend is found, a random walk is not, the future never changes the
past, and costs are charged exactly as declared."""

from __future__ import annotations

from datetime import date, timedelta

import numpy as np
import pytest

from aitrader.research.discovery import trend


def weekdays(n, start=date(2005, 1, 3)):
    out, d = [], start
    while len(out) < n:
        if d.weekday() < 5:
            out.append(d)
        d += timedelta(days=1)
    return out


def panel(drift_regimes: bool, n_assets=8, n_days=252 * 14, seed=1):
    """Each asset's drift is persistent over ~9-month regimes (trends) or zero (random walk)."""
    rng = np.random.default_rng(seed)
    days = weekdays(n_days)
    closes = {}
    for a in range(n_assets):
        drift = np.zeros(n_days)
        if drift_regimes:
            k = 0
            while k < n_days:
                L = int(rng.integers(150, 250))
                drift[k:k + L] = rng.choice([-1, 1]) * 0.0012
                k += L
        r = rng.normal(0, 0.01, n_days) + drift
        closes[f"A{a}"] = 100 * np.exp(np.cumsum(r))
    return trend.Panel(days, closes)


def test_a_planted_trend_is_found_and_a_random_walk_is_not():
    found = trend.stats(trend.backtest(panel(True), "tsmom12"))
    null = trend.stats(trend.backtest(panel(False, seed=2), "tsmom12"))
    assert found["t"] > 3 and found["mean_monthly"] > 0
    assert abs(null["t"]) < 2.5


def test_changing_the_future_never_changes_past_returns_or_weights():
    p = panel(True, seed=5)
    base = trend.backtest(p, "blend")
    cut = len(p.dates) - 400
    shocked = trend.Panel(p.dates, {s: np.concatenate((c[:cut], c[cut:] * np.exp(np.linspace(0, 2, len(c) - cut))))
                                    for s, c in p.closes.items()})
    after = trend.backtest(shocked, "blend")
    last_safe = p.dates[cut - 1]
    old = [r for r in base if r["date"] <= last_safe]
    new = [r for r in after if r["date"] <= last_safe]
    assert len(old) == len(new) > 50
    for a, b in zip(old[:-1], new[:-1]):  # every month realised before the change is identical
        assert a["net"] == pytest.approx(b["net"], abs=1e-12)


def test_signals_read_only_month_ends_up_to_now():
    mc = np.array([100.0] * 12 + [110.0, 50.0])
    assert trend.signal(mc, 12, "tsmom12") == 1.0  # 110 vs 100, the later collapse unseen
    assert np.isnan(trend.signal(mc, 11, "tsmom12"))  # fewer than 12 months of history: no signal


def test_costs_are_charged_exactly():
    p = panel(True, n_assets=4, seed=3)
    a = trend.backtest(p, "tsmom12", trend.TrendCosts(0.0, 0.0, 0.0))
    b = trend.backtest(p, "tsmom12", trend.TrendCosts(10.0, 0.0, 0.0))
    assert all(x["cost"] == 0 for x in a)
    assert sum(y["cost"] for y in b) > 0 and all(y["net"] <= x["net"] + 1e-15 for x, y in zip(a, b))
    x2 = trend.TrendCosts().stressed(2.0)
    assert (x2.trade_bps, x2.financing_pa, x2.borrow_pa) == (10.0, 0.06, 0.01)


def test_volatility_uses_only_past_returns():
    c = np.exp(np.cumsum(np.r_[0, np.full(99, 0.01)]))
    v = trend.ewma_vol(c)
    c2 = c.copy()
    c2[80:] *= 3
    assert np.allclose(trend.ewma_vol(c2)[:80], v[:80], equal_nan=True)


def test_the_div1_loader_keeps_the_holdout_sealed_without_a_key(tmp_path, monkeypatch):
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
    import div1
    monkeypatch.setattr(div1, "DATA", tmp_path)
    days = weekdays(252 * 18, start=date(2006, 1, 2))
    for s in div1.ASSETS:
        (tmp_path / f"{s}.csv").write_text("date,adj_close\n" + "".join(f"{d.isoformat()},{100 + i * 0.01}\n"
                                                                        for i, d in enumerate(days)))
    sealed = div1.load_panel()
    assert max(sealed.dates) < div1.HOLD_START <= max(days)
    assert max(div1.load_panel(key=object()).dates) == max(days)  # only a key from open_final_test opens it
