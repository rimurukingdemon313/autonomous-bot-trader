"""The TRINITY desk's run (scripts/trinity_paper_desk.py), on built series: nothing before the anchor's close is
final, the proxies' scale is fixed once, a late bar is waited for, every session is audited into the spec's file, the
design book is kept apart, and the report says what the rule is."""

import json
from datetime import date, datetime, timedelta, timezone

from aitrader.position import trinity as T
from aitrader.position import trinity_paper_desk as D
from aitrader.position.trend_desk import PromotedRule
from scripts import trinity_paper_desk as R

RULE = PromotedRule(D.RULE_ID, "EXPERIMENTAL", "HEALTHY", D.INSTRUMENTS, "PAPER", "a test", "2026-11-21", {})


def _weekdays(first, n):
    out, d = [], first
    while len(out) < n:
        if d.weekday() < 5:
            out.append(d)
        d += timedelta(days=1)
    return out


DAYS = _weekdays(date(2025, 1, 2), 230)
ANCHOR = DAYS[200]
LEVEL = {"QQQ": 400.0, "SPY": 500.0, "GLD": 300.0, "DBC": 25.0, "^VIX": 14.0, "TLT": 100.0, "UUP": 25.0,
         "^NDX": 20_000.0, "^GSPC": 6_000.0, "USO": 75.0, "GC=F": 3_300.0, "CL=F": 70.0}


def series(days=DAYS, g=0.0005, futures_factor=1.0):
    out = {}
    for sym, p0 in LEVEL.items():
        rising = sym not in ("^VIX", "TLT", "UUP")
        rows, prev = {}, p0
        for i, d in enumerate(days):
            c = p0 * ((1 + g) ** i if rising else 1.0) * (futures_factor if sym in ("GC=F", "CL=F") else 1.0)
            rows[d.isoformat()] = {"o": prev, "h": max(prev, c) * 1.001, "l": min(prev, c) * 0.999, "c": c,
                                   "adj": c, "v": 1.0}
            prev = c
        out[sym] = rows
    return out


def at(day, hh=22, mm=0):
    return datetime(day.year, day.month, day.day, hh, mm, tzinfo=timezone.utc)


def test_before_the_anchor_s_close_is_final_nothing_starts(tmp_path):
    s = series()
    # 29 minutes after the New York close: the anchor's bar is not final yet (it counts 30 minutes after)
    early = datetime.fromtimestamp(D.close_time(ANCHOR) + 29 * 60, timezone.utc)
    st = R.run(tmp_path, early, {k: {d: r for d, r in v.items() if d <= ANCHOR.isoformat()} for k, v in s.items()},
               rules=[RULE], rules_note="t", anchor=ANCHOR)
    assert st["account"] is None and st["processed_this_run"] == [] and st["scale"] is None
    assert "بعده ما بدا" in (tmp_path / "REPORT.md").read_text()
    # a minute later it is final, and the session runs
    st = R.run(tmp_path, early + timedelta(minutes=1), {k: {d: r for d, r in v.items() if d <= ANCHOR.isoformat()}
                                                         for k, v in s.items()}, rules=[RULE], rules_note="t",
               anchor=ANCHOR)
    assert st["processed_this_run"] == [str(ANCHOR)] and st["scale"]["USOIL"]["day"] == str(ANCHOR)


def test_the_anchor_session_runs_and_the_proxies_scale_is_fixed_once(tmp_path):
    s = series()
    st = R.run(tmp_path, at(ANCHOR), {k: {d: r for d, r in v.items() if d <= ANCHOR.isoformat()} for k, v in s.items()},
               rules=[RULE], rules_note="t", anchor=ANCHOR)
    assert st["processed_this_run"] == [str(ANCHOR)]
    k = st["scale"]["XAUUSD"]["k"]
    i = DAYS.index(ANCHOR)
    assert abs(k - (3_300.0 * 1.0005 ** i) / (300.0 * 1.0005 ** i)) < 1e-9 and st["scale"]["XAUUSD"]["day"] == str(ANCHOR)
    held = {p["symbol"] for p in st["positions"]}
    assert {"NAS100", "US500"} <= held
    # a later run, with futures that moved away from the funds, keeps the first scale: prices are never rewritten
    later = DAYS[i + 3]
    s2 = series(futures_factor=1.5)
    st2 = R.run(tmp_path, at(later), {kk: {d: r for d, r in v.items() if d <= later.isoformat()} for kk, v in s2.items()},
                rules=[RULE], rules_note="t", anchor=ANCHOR)
    assert st2["scale"]["XAUUSD"]["k"] == k
    assert st2["processed_this_run"] == [str(d) for d in DAYS[i + 1:i + 4]]


def test_a_late_bar_is_waited_for_never_skipped(tmp_path):
    s = series()
    i = DAYS.index(ANCHOR)
    cut = {k: {d: r for d, r in v.items() if d <= DAYS[i + 2].isoformat()} for k, v in s.items()}
    del cut["USO"][DAYS[i + 2].isoformat()]  # USOIL's price for the last day has not come yet
    st = R.run(tmp_path, at(DAYS[i + 2]), cut, rules=[RULE], rules_note="t", anchor=ANCHOR)
    assert st["processed_this_run"] == [str(DAYS[i]), str(DAYS[i + 1])]
    full = {k: {d: r for d, r in v.items() if d <= DAYS[i + 2].isoformat()} for k, v in s.items()}
    st = R.run(tmp_path, at(DAYS[i + 2]), full, rules=[RULE], rules_note="t", anchor=ANCHOR)
    assert st["processed_this_run"] == [str(DAYS[i + 2])]


def test_a_hole_in_one_series_stops_the_run_there_and_is_named(tmp_path):
    s = series()
    i = DAYS.index(ANCHOR)
    end = DAYS[i + 4]
    cut = {k: {d: r for d, r in v.items() if d <= end.isoformat()} for k, v in s.items()}
    del cut["^GSPC"][DAYS[i + 2].isoformat()]  # US500's bar for one day is missing; later days are there
    st = R.run(tmp_path, at(end), cut, rules=[RULE], rules_note="t", anchor=ANCHOR)
    assert st["processed_this_run"] == [str(DAYS[i]), str(DAYS[i + 1])]
    assert any(str(DAYS[i + 2]) in p and "US500" in p for p in st["problems"])
    full = {k: {d: r for d, r in v.items() if d <= end.isoformat()} for k, v in s.items()}
    st = R.run(tmp_path, at(end), full, rules=[RULE], rules_note="t", anchor=ANCHOR)
    assert st["processed_this_run"] == [str(d) for d in DAYS[i + 2:i + 5]]


def test_every_session_is_audited_into_the_spec_s_file_and_the_design_book_is_apart(tmp_path):
    s = series()
    i = DAYS.index(ANCHOR)
    end = DAYS[i + 20]
    st = R.run(tmp_path, at(end), {k: {d: r for d, r in v.items() if d <= end.isoformat()} for k, v in s.items()},
               rules=[RULE], rules_note="t", anchor=ANCHOR)
    audit = json.loads((tmp_path / "research" / "results" / "TRINITY-MASTER-daily-audit.json").read_text())
    assert audit["sessions"] == 21 and audit["validated"] is False and audit["paper_only"] is True
    assert audit["sessions_failing_a_check"] == [] and audit["sessions_with_a_check_unknown"] == []
    book = json.loads((tmp_path / "design_book.json").read_text())
    assert [r["day"] for r in book["rebalances"]] == [str(DAYS[i]), str(DAYS[i + 15])]
    assert len(book["daily"]) == 20 and book["equity"] != st["account"]["equity"]
    report = (tmp_path / "REPORT.md").read_text()
    assert "NOT VALIDATED" in report and "EXPERIMENTAL" in report and "never traded" in report
    trading = (tmp_path / "TRADING_REPORT.md").read_text()
    assert "NOT VALIDATED" in trading and "design book" in trading and "never added" in trading


def test_the_design_book_is_the_package_s_own_arithmetic():
    s = series()
    closes, days = R.signal_closes(s)
    ohlc = {a: {date.fromisoformat(d): (r["o"], r["h"], r["l"], r["c"]) for d, r in s[R.SIGNAL_SOURCE[a]].items()}
            for a in T.ASSETS}
    book = R.design_book(closes, days, ANCHOR, ohlc)
    rows = T.rows_at(T.grid(days, ANCHOR), closes, days)
    at_ = next(i for i, r in enumerate(rows) if r["date"] == ANCHOR)
    dec = T.decide(T.features(rows), book_start=at_)
    # on the rebalance closes the book's equity is the package's cumulative return
    eq = {r["day"]: r["equity"] for r in book["daily"]}
    assert abs(eq[str(dec[1]["date"])] - 200_000 * (1 + dec[0]["cum"])) < 0.01


def test_the_replay_anchor_has_its_warm_up(tmp_path):
    days = _weekdays(date(2024, 1, 2), 400)
    s = series(days)
    hist = tmp_path / "history"
    hist.mkdir()
    for sym, rows in s.items():
        (hist / f"{sym.replace('^', '_').replace('=', '_')}.json").write_text(json.dumps(rows))
    st = R.replay(hist, tmp_path / "state", days[10], at(days[-1]))
    assert st["anchor"] == str(days[(T.WARMUP + 1) * T.STEP]) and st["processed_this_run"]
