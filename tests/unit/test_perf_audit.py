"""The audits of the two paper accounts (aitrader/perf/trend.py, radar.py) on ledgers built so every figure is known,
and each reconciliation shown to fail when the two routes to its figure disagree."""

from __future__ import annotations

import csv
import io
import json
import sqlite3

import pytest

from aitrader.memory.db import Database
from aitrader.perf import radar, trend
from aitrader.radar import core as R
from aitrader.radar import venues as Vn

ROOT = __import__("pathlib").Path(__file__).resolve().parents[2]

# ── the trend desk ──────────────────────────────────────────────────────────

COLS = ("position,status,strategy,signal,decision_id,instrument,direction,opened,closed,exit_reason,entry,exit,mark,qty,"
        "entry_notional_usd,entry_leverage,risk_usd,gross_pnl,spread,commission,slippage,financing,net_pnl,open_pnl,r,reconciles").split(",")


def desk():
    """A closed trade that made $480 after $20 of costs, and two open ones worth -$20 together: a US index up 100
    points on 2 units, and a German index down 200 points on 1 unit at 1.10 dollars to the euro."""
    led = [dict.fromkeys(COLS, "") | {"position": "P1", "status": "CLOSED", "instrument": "UK100", "direction": "LONG",
                                      "opened": "2026-11-02 16:30 UTC", "closed": "2026-11-04 16:30 UTC", "entry": "10000", "exit": "10250",
                                      "qty": "2", "risk_usd": "1400", "gross_pnl": "500", "spread": "10", "commission": "5", "slippage": "5",
                                      "financing": "0", "net_pnl": "480"},
           dict.fromkeys(COLS, "") | {"position": "P2", "status": "OPEN", "instrument": "US500", "direction": "LONG",
                                      "opened": "2026-11-03 21:00 UTC", "entry": "5000", "mark": "5100", "qty": "2",
                                      "entry_notional_usd": "10000", "risk_usd": "1200", "open_pnl": "200"},
           dict.fromkeys(COLS, "") | {"position": "P3", "status": "OPEN", "instrument": "GER40", "direction": "LONG",
                                      "opened": "2026-11-03 16:30 UTC", "entry": "20000", "mark": "19800", "qty": "1",
                                      "entry_notional_usd": "22000", "risk_usd": "1500", "open_pnl": "-220"}]
    eq = [{"session_utc": "2026-11-02 21:00 UTC", "day": "2026-11-02", "equity": "200100.0", "balance": "200000.0", "open_pnl": "100.0",
           "gross_exposure_usd": "20000", "leverage": "0.1"},
          {"session_utc": "2026-11-03 21:00 UTC", "day": "2026-11-03", "equity": "199700.0", "balance": "200000.0", "open_pnl": "-300.0",
           "gross_exposure_usd": "52000", "leverage": "0.26"},
          {"session_utc": "2026-11-04 21:00 UTC", "day": "2026-11-04", "equity": "200460.0", "balance": "200480.0", "open_pnl": "-20.0",
           "gross_exposure_usd": "31980.0", "leverage": "0.1595"}]
    state = {"paper_only": True, "real_money": False, "account": {"balance": 200480.0, "equity": 200460.0, "pnl": 460.0},
             "positions": [{"symbol": "US500", "units": 2.0, "entry": 5000.0, "price": 5100.0, "stop": 4800.0, "notional_usd": 10200.0, "pnl": 200.0},
                           {"symbol": "GER40", "units": 1.0, "entry": 20000.0, "price": 19800.0, "stop": 18800.0, "notional_usd": 21780.0, "pnl": -220.0}]}
    return led, eq, state


def failed(a):
    return [c["check"] for c in a["failed_checks"]]


def test_the_desk_reconciles_and_keeps_realized_apart_from_unrealized():
    a = trend.audit(*desk())
    assert a["reconciled"] and not a["failed_checks"] and len(a["checks"]) >= 25
    f = a["figures"]
    assert (f["realized_net"], f["realized_gross"], f["unrealized"], f["net_after_all_costs"]) == (480.0, 500.0, -20.0, 460.0)
    assert f["costs_on_closed_trades"] == {"spread": 10.0, "commission": 5.0, "slippage": 5.0, "financing": 0.0}
    assert f["equity_now"] == 200460.0 and f["balance_now"] == 200480.0 and f["open_positions"] == 2
    ct = f["closed_trades"]
    assert ct["closed"] == 1 and ct["win_rate"] == 1.0 and ct["profit_factor"] is None and ct["sample"] == "insufficient"
    assert "no losing trade" in ct["undefined"]["profit_factor"]
    # 200,100 was the peak before the fall to 199,700
    assert f["max_drawdown_session_closes"] == pytest.approx(400.0) and f["below_the_peak_now"] == pytest.approx(0.0)
    assert f["gross_exposure"] == 31980.0 and f["leverage"] == pytest.approx(31980 / 200460)
    # at the stops from here: 2 x 300 points, and 1 x 1000 points at 1.10
    assert f["open_risk_at_stops"] == pytest.approx(600 + 1100)
    assert [d["net"] for d in f["daily"]] == [100.0, -400.0, 760.0] and f["losing_days"] == 1
    assert f["monthly"][0]["net"] == 460.0 and f["monthly"][0]["of_target"] == pytest.approx(0.115)
    ger = next(p for p in a["positions"] if p["instrument"] == "GER40")
    assert ger["conversion_to_usd"] == pytest.approx(1.10) and ger["loss_at_stop_from_here_usd"] == pytest.approx(1100.0)
    assert f["concentration"]["one_risk_factor"] and f["concentration"]["largest_share_of_gross"] == pytest.approx(21780 / 31980)


def test_an_unrealized_gain_is_never_reported_as_realized():
    led, eq, st = desk()
    led = [r for r in led if r["status"] == "OPEN"]
    eq[-1] |= {"balance": "200000.0", "equity": "199980.0"}
    st["account"] = {"balance": 200000.0, "equity": 199980.0, "pnl": -20.0}
    f = trend.audit(led, eq, st)["figures"]
    assert f["realized_net"] == 0 and f["unrealized"] == -20.0 and f["closed_trades"]["closed"] == 0
    assert f["closed_trades"]["win_rate"] is None and f["closed_trades"]["undefined"]["win_rate"] == "no closed trade"
    assert f["benchmarks"]["same_indices_bought_and_held_at_the_desk_size"]["usd"] == -20.0


def test_after_an_exit_the_buy_and_hold_benchmark_is_unavailable_not_invented():
    b = trend.audit(*desk())["figures"]["benchmarks"]
    assert b["same_indices_bought_and_held_at_the_desk_size"]["usd"] is None and "later closes" in b["same_indices_bought_and_held_at_the_desk_size"]["why"]
    assert b["cash"]["usd"] == pytest.approx(200000 * 0.03875 * 2 / 365, abs=0.01)


@pytest.mark.parametrize("change, broken", [
    (lambda led, eq, st: eq[-1].update(equity="200470.0"), "in every session, equity is balance plus open P&L"),
    (lambda led, eq, st: led[0].update(net_pnl="490"), "P1 UK100: gross less its costs is its net"),
    (lambda led, eq, st: led[1].update(open_pnl="250"), "US500: units x (mark - entry) x the conversion is its open P&L"),
    (lambda led, eq, st: st["positions"].pop(), "the ledger and the state file hold the same open positions"),
    (lambda led, eq, st: st["account"].update(equity=200500.0), "the state file's equity is the last session's"),
    (lambda led, eq, st: led[2].update(risk_usd="1600"), "GER40: its risk at entry was within the per-trade limit"),
    (lambda led, eq, st: st["positions"][1].update(stop=10000.0), "open risk at the stops is within the limit for all trades together"),
    (lambda led, eq, st: led[2].update(direction="SHORT"), "every position is long: the desk never shorts"),
    (lambda led, eq, st: st.update(real_money=True), "paper only: the state file says no real money"),
    (lambda led, eq, st: eq.reverse(), "the sessions are in order and none is recorded twice"),
    (lambda led, eq, st: led[0].update(status="PENDING"), "every ledger row is OPEN or CLOSED"),
])
def test_each_reconciliation_fails_when_its_two_routes_disagree(change, broken):
    led, eq, st = desk()
    change(led, eq, st)
    a = trend.audit(led, eq, st)
    assert not a["reconciled"] and broken in failed(a)


def test_the_permanent_record_is_checked_link_by_link_and_a_rewritten_row_breaks_it(tmp_path):
    db = Database(tmp_path / "desk.db")
    for i, eq in enumerate((200000.0, 199500.0, 200100.0, 199900.0)):
        db.event("DESK_INTRADAY_LOW" if i % 2 else "DESK_EQUITY", {"day": f"2026-11-0{2 + i // 2}", "equity": eq})
    assert trend.chain(tmp_path / "desk.db") == {"table": "events", "rows": 4, "ok": True, "broken_at": None}
    pts = trend.points(tmp_path / "desk.db")
    assert [p["equity"] for p in pts] == [200000.0, 199500.0, 200100.0, 199900.0] and pts[1]["type"] == "DESK_INTRADAY_LOW"
    con = sqlite3.connect(tmp_path / "desk.db")
    for (name,) in con.execute("SELECT name FROM sqlite_master WHERE type='trigger'").fetchall():
        con.execute(f"DROP TRIGGER {name}")
    con.execute("UPDATE events SET payload = replace(payload, '199500.0', '199990.0') WHERE seq = 2")
    con.commit()
    con.close()
    c = trend.chain(tmp_path / "desk.db")
    assert not c["ok"] and c["broken_at"] == 2 and c["rows"] == 1


def test_the_drawdown_inside_a_day_comes_from_the_desks_own_record_and_is_compared_with_its_report():
    led, eq, st = desk()
    record = [{"type": "DESK_EQUITY", "day": "2026-11-02", "equity": 200100.0}, {"type": "DESK_INTRADAY_LOW", "day": "2026-11-03", "equity": 199200.0},
              {"type": "DESK_EQUITY", "day": "2026-11-03", "equity": 199700.0}, {"type": "DESK_EQUITY", "day": "2026-11-04", "equity": 200460.0}]
    rep = "| Equity now | $200,460.00: +$460.00 |\n| Maximum drawdown (intraday lows included) | $900.00 (0.45% of the peak) |\n| Below the peak now | $0.00 |\n"
    a = trend.audit(led, eq, st, record=record, chains=[{"table": "events", "rows": 4, "ok": True}], report=rep)
    assert a["reconciled"] and a["figures"]["max_drawdown_inside_a_day"]["value"] == 900.0
    assert a["figures"]["max_drawdown_session_closes"] == pytest.approx(400.0)  # the closes alone miss the low of the day
    wrong = trend.audit(led, eq, st, record=record, chains=[{"table": "events", "rows": 4, "ok": False}], report=rep.replace("$900.00", "$400.00"))
    assert "the desk's report prints this drawdown inside a day" in failed(wrong)
    assert any("permanent record `events` is unbroken" in x for x in failed(wrong))
    assert trend.audit(led, eq, st)["figures"]["max_drawdown_inside_a_day"]["value"] is None


def test_rows_reads_the_desks_csv():
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=COLS)
    w.writeheader()
    w.writerows(desk()[0])
    assert trend.rows(buf.getvalue()) == desk()[0]


# ── the funding radar ───────────────────────────────────────────────────────

T0, H, APR, RF = 1_794_009_600, 3600, 1 / 8760, 0.03875


def radar_book(hours=260):
    """A real radar book, made by the radar's own code on built quotes: one coin on a persistent spread that later
    reverses, another whose spread decays, and a third still open at the end."""
    def quotes(k):
        qs = [Vn.Quote("hyperliquid", "AAA", 1.0, (0.65 if k < 150 else -0.30) * APR, 100.0 + 0.01 * k, 50e6), Vn.Quote("gate", "AAA", 1.0, 0.05 * APR, 100.0, 50e6)]
        qs += [Vn.Quote("mexc", "BBB", 1.0, (0.45 if 20 < k < 190 else 0.0) * APR, 20.0, 50e6), Vn.Quote("gate", "BBB", 1.0, 0.0, 20.0, 50e6)]
        qs += [Vn.Quote("mexc", "CCC", 1.0, (0.90 if k > 150 else 0.0) * APR, 5.0, 50e6), Vn.Quote("dydx", "CCC", 1.0, 0.0, 5.0, 50e6)]
        return qs
    s = R.State()
    for k in range(hours):
        R.step(s, quotes(k), {}, T0 + k * H, R.Rules())
    return s


def as_ledger(s):
    d = s.to_json()
    d.pop("history")
    return json.loads(json.dumps(d))


def test_the_radar_book_reconciles_and_my_performance_is_the_radars_own():
    s = radar_book()
    led = as_ledger(s)
    assert len(led["closed"]) >= 2 and len(led["open"]) >= 1
    own = R.performance(s, R.Rules(), RF)
    report = "## Performance\n\n" + "\n".join(f"- {k}: {v}" for k, v in own.items()) + "\n"
    a = radar.audit(led, rf_apr=RF, report=report)
    assert a["reconciled"], a["failed_checks"]
    mine = a["figures"]["performance"]
    for k, v in own.items():
        if k != "rf_apr_pct_declared":
            assert mine[k] == pytest.approx(v, abs=2e-3) if isinstance(v, float) else mine[k] == v, k
    f = a["figures"]
    assert f["realized_bp"] == pytest.approx(sum(p.net_bp for p in s.closed), abs=0.05)
    assert f["unrealized_bp"] == pytest.approx(sum(p.net_bp for p in s.open), abs=0.05)
    # an open position has paid its entry fills only: closed now, it pays the same again
    leave = sum(Vn.TAKER_BP[p.short_venue] + Vn.TAKER_BP[p.long_venue] + 10 for p in s.open)
    assert f["unrealized_if_closed_now_bp"] == pytest.approx(f["unrealized_bp"] - leave, abs=0.11)
    assert f["book_pnl_pct"] == pytest.approx((f["realized_bp"] + f["unrealized_bp"]) / 2000, abs=1e-4)
    assert f["illustration_usd"]["realized"] == pytest.approx(f["realized_bp"] * 0.5, abs=0.06) and "not an account" in f["illustration_usd"]["what"]


def test_the_sources_add_up_and_the_classes_partition_the_closed_positions():
    led = as_ledger(radar_book())
    at = radar.audit(led, rf_apr=RF)["attribution"]
    s = at["sources"]
    assert s["net_bp"] == pytest.approx(s["funding_bp"] + s["price_bp"] - s["cost_bp"], abs=0.15)
    assert s["net_bp"] == pytest.approx(sum(radar.net_bp(p) for p in led["closed"]), abs=0.15)
    for table in (at["by_exit_reason"], at["by_holding_time"], *at["known_at_entry"].values()):
        assert sum(r["positions"] for r in table) == len(led["closed"])
        assert sum(r["sum_bp"] for r in table) == pytest.approx(s["net_bp"], abs=0.3)
    assert {r["class"] for r in at["by_exit_reason"]} <= {"spread_decayed", "spread_reversed", "rebalance", "max_age", "venue_unavailable"}


def many(n_thin=14, n_thick=14, thin=-28.0, thick=6.0):
    """Closed positions with a known net each: thin entries that lose, thick ones that earn a little."""
    closed, t = [], T0
    for i in range(n_thin + n_thick):
        is_thin = i < n_thin
        net = (thin if is_thin else thick) + (i % 3 - 1)
        closed.append({"id": f"X{i}-mexc-gate-{t}", "coin": f"X{i % 9}", "short_venue": "mexc", "long_venue": "gate", "opened": t,
                       "closed": t + 5 * H, "short_px0": 1.0, "long_px0": 1.0, "short_px": 1.0, "long_px": 1.0, "funding_bp": net + 34.0,
                       "cost_bp": 34.0, "entry_spread_apr": 0.30 if is_thin else 0.80, "reason": "spread_reversed"})
        t += 40 * H
    total, marks, run = 0.0, [{"t": T0 - H, "pnl_bp_total": 0.0, "open": 0}], 0.0
    by_close = {p["closed"]: p for p in closed}
    for k in range((closed[-1]["closed"] - T0) // H + 1):
        tt = T0 + k * H
        if tt in by_close:
            run += radar.net_bp(by_close[tt])
        marks.append({"t": tt, "pnl_bp_total": round(run, 4), "open": 0})
    total = run
    return {"open": [], "closed": closed, "marks": marks, "runs": len(marks)}, total


def test_the_largest_weakness_is_the_class_that_did_worst_against_the_rest_not_the_largest_class():
    led, total = many()
    a = radar.audit(led, rf_apr=RF)
    assert a["reconciled"], a["failed_checks"]
    w = a["attribution"]["largest_weakness"]
    assert (w["dimension"], w["class"], w["positions"]) == ("entry spread", "under 50%/yr", 14)
    assert w["mean_bp"] == pytest.approx(-28.0, abs=0.5) and w["rest_mean_bp"] == pytest.approx(6.0, abs=0.5)
    assert w["excess_loss_bp"] == pytest.approx(14 * (-28.0 - 6.0), abs=10) and w["t_against_the_rest"] < -20
    # every position is on one venue pair: the pair is the largest class and no weakness, having no rest to compare with
    assert all(x["class"] != "short mexc / long gate" or x["excess_loss_bp"] is None for x in a["attribution"]["known_at_entry"]["venue pair"])
    ct = a["figures"]["closed_trades"]
    assert ct["closed"] == 28 and ct["won"] == 14 and ct["win_rate"] == 0.5 and ct["sample"] == "insufficient"
    assert ct["profit_factor"] == pytest.approx(sum(6 + (i % 3 - 1) for i in range(14, 28)) / -sum(-28 + (i % 3 - 1) for i in range(14)))


def test_no_weakness_is_named_when_no_class_does_worse_than_the_rest_by_more_than_noise():
    led, _ = many(thin=6.0, thick=6.0)
    at = radar.audit(led, rf_apr=RF)["attribution"]
    thin = next(x for x in at["known_at_entry"]["entry spread"] if x["class"] == "under 50%/yr")
    # the thin entries are a hair below the rest (a seventh of a basis point): a difference, and not a weakness
    assert thin["excess_loss_bp"] < 0 and -radar.WEAK_DIFF_T < thin["t_against_the_rest"] < 0
    assert at["largest_weakness"] is None
    # and nine positions against the rest are too few to call, however badly they did
    few, _ = many(n_thin=9, n_thick=19)
    assert radar.audit(few, rf_apr=RF)["attribution"]["largest_weakness"] is None


def test_a_class_that_loses_like_the_rest_of_the_book_is_no_weakness():
    """Every position loses about 28 bp. The thin entries lose reliably, and no more than the others: removing them
    would not mend the book, so they are not named."""
    led, _ = many(thin=-28.0, thick=-27.6)
    at = radar.audit(led, rf_apr=RF)["attribution"]
    thin = next(x for x in at["known_at_entry"]["entry spread"] if x["class"] == "under 50%/yr")
    assert thin["t"] <= -radar.WEAK_OWN_T and thin["t_against_the_rest"] > -radar.WEAK_DIFF_T
    assert at["largest_weakness"] is None


def test_a_class_whose_loss_is_not_told_from_zero_is_no_weakness():
    """Thin entries that lose 25 bp on average with wins and losses of 45 around it, beside a rest that earns 60: they
    do worse than the rest beyond doubt, and their own loss is at t -2, short of the floor. Only the first rule of
    the two can refuse them, so this is the case that rule is for."""
    led, _ = many(thin=-25.0, thick=60.0)
    for i, p in enumerate(led["closed"][:14]):
        p["funding_bp"] += (45.0, -45.0)[i % 2]
    run, by_close = 0.0, {p["closed"]: p for p in led["closed"]}
    for m in led["marks"][1:]:
        if m["t"] in by_close:
            run += radar.net_bp(by_close[m["t"]])
        m["pnl_bp_total"] = round(run, 4)
    a = radar.audit(led, rf_apr=RF)
    assert a["reconciled"], a["failed_checks"]
    thin = next(x for x in a["attribution"]["known_at_entry"]["entry spread"] if x["class"] == "under 50%/yr")
    assert thin["mean_bp"] == pytest.approx(-25.0, abs=0.5) and -radar.WEAK_OWN_T < thin["t"] < -1.5
    assert thin["t_against_the_rest"] <= -radar.WEAK_DIFF_T and thin["rest_mean_bp"] > 50
    assert a["attribution"]["largest_weakness"] is None


def test_on_the_radars_real_ledger_of_2026_11_14_the_thin_entries_are_the_weakness():
    """The figures of the audited snapshot (docs/PERFORMANCE_ENGINEERING.md), as recorded by RADX-1: every closed
    position with what was known at its entry and its net."""
    rows = json.loads((ROOT / "research" / "knowledge" / "RADX-1.json").read_text())["positions"]
    thin = [r["net_bp"] for r in rows if r["thin"]]
    rest = [r["net_bp"] for r in rows if not r["thin"]]
    assert (len(thin), len(rest)) == (122, 88)
    from aitrader.perf.stats import mean_t
    m, t = mean_t(thin)
    assert m == pytest.approx(-27.6, abs=0.05) and t == pytest.approx(-6.58, abs=0.01) and t <= -radar.WEAK_OWN_T
    d = radar._welch(thin, rest)
    assert d == pytest.approx(-1.75, abs=0.02) and d <= -radar.WEAK_DIFF_T  # and it would not have reached 2.0


@pytest.mark.parametrize("change, broken", [
    (lambda d: d["closed"][0].update(funding_bp=d["closed"][0]["funding_bp"] + 5), "the positions add up to the last hourly mark of the book"),
    (lambda d: d["closed"][0].update(cost_bp=30.0), "every position paid each venue's fee and the declared slippage on every fill"),
    (lambda d: d["closed"].append(dict(d["closed"][0])), "no position is recorded twice"),
    (lambda d: d["closed"][1].update(reason=None), "every closed position has its closing hour and reason, and no open one has"),
    (lambda d: d["closed"][0].update(closed=d["closed"][0]["opened"] - H), "no position closed before it was opened"),
    (lambda d: d["marks"].append(dict(d["marks"][-1])), "the hourly marks are in order, on the hour, none twice"),
    (lambda d: d.update(runs=d["runs"] + 3), "the run count is the number of marks"),
    (lambda d: d["closed"][9].update(opened=d["closed"][0]["opened"] + H), "a coin never held two positions at once"),
])
def test_each_radar_reconciliation_fails_when_the_ledger_is_wrong(change, broken):
    led, _ = many()
    change(led)
    a = radar.audit(led, rf_apr=RF)
    assert not a["reconciled"] and broken in failed(a)


def test_a_figure_the_radars_report_prints_differently_fails_its_check():
    s = radar_book()
    own = R.performance(s, R.Rules(), RF)
    report = "\n".join(f"- {k}: {v}" for k, v in (own | {"max_dd_pct": own["max_dd_pct"] + 0.5}).items())
    a = radar.audit(as_ledger(s), rf_apr=RF, report=report)
    assert failed(a) == ["the radar's report prints this max_dd_pct"]
    assert radar.published("## Performance\n\n- days: 3.5\n- best_coin: INIT\n- closed_positions: 12\n") == {"days": 3.5, "best_coin": "INIT", "closed_positions": 12.0}
