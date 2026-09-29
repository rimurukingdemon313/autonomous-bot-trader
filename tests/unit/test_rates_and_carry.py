"""Interest-rate data and the carry proxy: point in time, never interpolated, never substituted,
and every component of a carry trade's return kept separate."""

from __future__ import annotations

import hashlib
import json
from datetime import date, datetime, timezone

import numpy as np
import pytest

from aitrader.data.rates import (RateSeries, RateStore, available_at, coverage, differential, parse_bis_cbpol,
                                 parse_euribor, parse_fred)
from aitrader.research.discovery.carry import CARRY_LABEL, CarryStudy, carry_r, rate_primitives
from aitrader.research.discovery.exits import EXIT_BY_KEY
from aitrader.research.discovery.study import Condition, Segment, SymbolData, fit_binning
from aitrader.research.labels import BUY, SELL, CostModel, atr24
from tests.unit.discovery_market import series


def utc(y, m, d, h=0, mi=0):
    return int(datetime(y, m, d, h, mi, tzinfo=timezone.utc).timestamp())


def step(ccy, points, rate_type="POLICY"):
    """A rate series from (date, value) points, as a publisher would list them."""
    eff = np.array([utc(d.year, d.month, d.day) for d, _ in points], np.int64)
    av = np.array([available_at(rate_type, d) for d, _ in points], np.int64)
    return RateSeries(ccy, rate_type, "test", "not revised", eff, np.array([v for _, v in points], float), av)


def test_a_policy_rate_is_a_step_known_only_after_its_decision_never_interpolated():
    s = step("AUD", [(date(2010, 1, 4), 3.75), (date(2010, 3, 2), 4.00)])
    before, at_close = utc(2010, 3, 2, 21, 59), utc(2010, 3, 2, 22, 0)  # 17:00 New York (EST) = 22:00 UTC
    between = utc(2010, 2, 1, 12)
    got = s.asof([before, at_close, between, utc(2009, 12, 1)])
    assert got[0] == 3.75 and got[1] == 4.00 and got[2] == 3.75 and np.isnan(got[3])  # a step, no ramp
    assert available_at("INTERBANK_3M", date(2012, 1, 2)) == utc(2012, 1, 2, 11)  # 12:00 CET


def test_official_formats_parse_and_a_monthly_value_waits_for_its_month_to_end():
    bis = (b"FREQ,REF_AREA,TIME_PERIOD,OBS_VALUE\nD,AU,2010-03-02,4.00\nD,JP,2010-03-02,0.10\n"
           b"M,NZ,2010-03,2.50\nD,BR,2010-03-02,8.75\n")
    got = parse_bis_cbpol(bis)
    assert set(got) == {"AUD", "JPY", "NZD"}  # an area outside the universe is ignored, not mapped
    assert got["NZD"].effective[0] == utc(2010, 4, 1)  # the March figure is not used inside March
    fred = parse_fred(b"DATE,DFF\n2010-03-01,0.13\n2010-03-02,.\n", "USD", "POLICY", "DFF")
    assert list(fred.value) == [0.13]  # a missing value ('.') is missing, not zero
    eur = parse_euribor(b"date,rate,maturity_level,granularity\n2012-01-02,1.343,3m,monthly\n"
                        b"2012-01-02,1.0,1m,monthly\n")
    assert list(eur.value) == [1.343] and eur.rate_type == "INTERBANK_3M"


def test_unverified_files_are_refused_and_missing_currencies_are_unavailable(tmp_path):
    raw = b"date,rate,maturity_level,granularity\n2008-06-02,4.9,3m,monthly\n2008-07-01,4.9,3m,monthly\n"
    (tmp_path / "e.csv").write_bytes(raw)
    (tmp_path / "manifest.json").write_text(json.dumps({"e.csv": {"format": "euribor", "sha256": "0" * 64}}))
    with pytest.raises(ValueError):
        RateStore(tmp_path).load()
    (tmp_path / "manifest.json").write_text(json.dumps({"e.csv": {"format": "euribor",
                                                                  "sha256": hashlib.sha256(raw).hexdigest()}}))
    s = RateStore(tmp_path).load()
    cov = coverage(s, date(2008, 7, 11), date(2008, 7, 30))
    assert cov["EUR"]["status"] == "AVAILABLE" and cov["USD"]["status"] == "UNAVAILABLE"
    # a pair needs BOTH sides of the SAME rate type: nothing is substituted
    assert np.isnan(differential(s, "EURUSD", "INTERBANK_3M", [utc(2008, 7, 20)])).all()
    assert np.isnan(differential(s, "EURUSD", "POLICY", [utc(2008, 7, 20)])).all()


RATES = {("EUR", "POLICY"): step("EUR", [(date(2009, 12, 1), 1.0), (date(2010, 3, 1), 1.5)]),
         ("USD", "POLICY"): step("USD", [(date(2009, 12, 1), 0.25)]),
         ("JPY", "POLICY"): step("JPY", [(date(2009, 12, 1), 1.5)])}


def d1(sym, n=200, drift=0.0):
    rng = np.random.default_rng(3)
    mid = (110.0 if sym.endswith("JPY") else 1.2) * np.exp(np.cumsum(drift + rng.normal(0, 1e-5, n)))
    return series(sym, mid, rng, wick=1e-5, half=1e-6, timeframe="D1")


def test_the_states_are_signed_to_the_pair_and_blind_to_later_decisions():
    p = rate_primitives(RATES, "POLICY")
    eur, jpy = d1("EURUSD"), d1("USDJPY")
    lvl_e, lvl_j = p["rate_level"].column(eur, None, {}), p["rate_level"].column(jpy, None, {})
    march = np.searchsorted(eur.available_at, utc(2010, 3, 2))
    assert lvl_e[march - 5] == 1.0 and lvl_e[march + 1] == 2.0  # EUR-USD 0.75pp, then 1.25pp: buying earns
    assert lvl_j[10] == 0.0  # USD 0.25 vs JPY 1.5: buying USDJPY pays 1.25pp
    move = p["policy_move"].column(eur, None, {})
    assert move[march + 1] == 2.0 and move[march - 5] == 1.0  # the March hike, only once it was announced
    for name, prim in p.items():
        full = prim.column(eur, None, {})
        for i in (40, march - 1, march, march + 3, 150):
            t = int(eur.available_at[i])
            cut = {k: v.truncated(t) for k, v in RATES.items()}
            assert np.array_equal(rate_primitives(cut, "POLICY")[name].column(eur, None, {})[i:i + 1],
                                  full[i:i + 1], equal_nan=True), (name, i)


def test_the_carry_proxy_has_the_right_size_and_sign():
    t0 = utc(2010, 1, 5)
    long_ = carry_r(RATES, "POLICY", "EURUSD", BUY, [t0], [t0 + 30 * 86400], np.array([1.2]), np.array([0.012]))
    short = carry_r(RATES, "POLICY", "EURUSD", SELL, [t0], [t0 + 30 * 86400], np.array([1.2]), np.array([0.012]))
    assert long_[0] == pytest.approx(0.0075 * 30 / 365 * 1.2 / 0.012) and short[0] == pytest.approx(-long_[0])
    assert np.isnan(carry_r(RATES, "POLICY", "EURGBP", BUY, [t0], [t0 + 86400], np.ones(1), np.ones(1))[0])
    assert CARRY_LABEL == "RATE-DIFFERENTIAL CARRY PROXY"


def test_a_carry_trade_splits_into_spot_carry_and_financing_and_the_battery_sees_their_sum():
    sym = "EURUSD"
    s_ = d1(sym, n=260)
    sd = {sym: SymbolData(sym, s_, 0.0001, {"A": np.full(260, 2.0)}, atr24(s_))}
    seg = Segment("judge", "judge", date(2010, 3, 1), date(2010, 8, 1))
    st = CarryStudy(sd, seg, {"A": fit_binning("A", {}, groups=((0.0,), (1.0,), (2.0,)))},
                    CostModel(swap_atr_per_night=0.0), rates=RATES, rate_type="POLICY")
    o = st.outcome(sym, EXIT_BY_KEY["D4"], BUY)
    ok = np.isfinite(o["r"])
    assert ok.any()
    assert np.allclose(o["r"][ok], (o["spot"] + o["carry"] - o["financing"])[ok])
    assert (o["carry"][ok] > 0).all() and (o["financing"][ok] > 0).all()  # long EUR earns; the broker's markup costs
    tr = st.trades(st.masks(Condition.parse("A=high")), "D4", BUY)
    assert tr.n > 0 and np.isfinite(tr.r).all()
