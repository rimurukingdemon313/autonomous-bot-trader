"""The replay engine (aitrader/perf/replay.py) on quotes built so the answer is known: the archive, the replay of the
radar's frozen `step`, the chronological validation and the forward challenger. The radar's own code is imported and
never changed: the last test pins its registered hash."""

from __future__ import annotations

import json

import pytest

from aitrader.perf import replay as P
from aitrader.radar import core as R
from aitrader.radar import venues as Vn

H, DAY = 3600, 86400
T0 = 1_794_009_600  # 2026-11-07 00:00 UTC: a day boundary
APR = 1 / 8760
RF = 0.03875


def row(k, venue, coin, apr, px=100.0, vol=50e6):
    return {"t": T0 + k * H, "venue": venue, "coin": coin, "scale": 1.0, "rate": apr * APR, "mark": px, "vol": vol}


def market(hours, fn):
    """`fn(k)` gives the hour's rows as (venue, coin, apr[, px]) tuples."""
    return [row(k, *x) for k in range(hours) for x in fn(k)]


def steady(k):
    """One coin with a persistent 60%/yr spread between two venues."""
    return [("hyperliquid", "AAA", 0.65), ("gate", "AAA", 0.05)]


def live(rows, rule=R.Rules()):
    """What the radar itself would have done hour by hour on these rows, from an empty book at the first hour."""
    s = R.State()
    for t, hour in sorted(P.by_hour(rows).items()):
        R.step(s, [Vn.Quote(r["venue"], r["coin"], r["scale"], r["rate"], r["mark"], r["vol"]) for r in hour], {}, t, rule)
    return s


# ── the archive ─────────────────────────────────────────────────────────────

def test_a_day_is_archived_once_it_is_over_and_the_day_in_progress_waits(tmp_path):
    rows = market(60, steady)  # two days and a half
    out = P.merge(tmp_path, rows)
    assert out["added"] == ["2026-11-07", "2026-11-08"] and not out["problems"]
    got, problems = P.load(tmp_path)
    assert not problems and len(got) == 2 * 24 * 2 and got == rows[:96]
    assert json.loads((tmp_path / "manifest.json").read_text())["days"]["2026-11-07"]["hours"] == 24
    # the day in progress is not on disk, and the replay still sees it
    assert not (tmp_path / "2026-11-09.jsonl.gz").exists()
    assert P.with_pending(got, rows) == rows


def test_an_archived_day_is_never_rewritten_and_a_changed_row_is_reported(tmp_path):
    rows = market(60, steady)
    P.merge(tmp_path, rows)
    before = (tmp_path / "2026-11-07.jsonl.gz").read_bytes()
    changed = [dict(r, rate=r["rate"] * 2) if r["t"] == T0 + 5 * H and r["venue"] == "gate" else r for r in rows]
    out = P.merge(tmp_path, changed)
    assert out["added"] == [] and len(out["problems"]) == 1 and "2026-11-07" in out["problems"][0] and "1 changed" in out["problems"][0]
    assert (tmp_path / "2026-11-07.jsonl.gz").read_bytes() == before
    again = P.merge(tmp_path, market(84, steady))  # a later run, a day further on
    assert again["added"] == ["2026-11-09"] and not again["problems"]


def test_the_first_day_is_marked_when_the_radar_only_held_part_of_it(tmp_path):
    rows = [r for r in market(60, steady) if r["t"] >= T0 + 7 * H]
    P.merge(tmp_path, rows)
    days = json.loads((tmp_path / "manifest.json").read_text())["days"]
    assert days["2026-11-07"]["starts_late"] and days["2026-11-07"]["hours"] == 17 and not days["2026-11-08"]["starts_late"]


def test_a_tampered_archive_is_refused_not_replayed(tmp_path):
    P.merge(tmp_path, market(60, steady))
    f = tmp_path / "2026-11-08.jsonl.gz"
    rows = P._unpack(f.read_bytes())
    rows[3]["mark"] = 999.0
    f.write_bytes(P._pack(rows))
    got, problems = P.load(tmp_path)
    assert len(problems) == 1 and "2026-11-08" in problems[0] and all(P.day_of(r["t"]) == "2026-11-07" for r in got)


# ── the replay ──────────────────────────────────────────────────────────────

def test_a_replay_of_the_original_rules_is_what_the_radar_did_on_the_same_hours():
    def fn(k):
        out = [("hyperliquid", "AAA", 0.65 if k < 150 else 0.02), ("gate", "AAA", 0.05)]
        out += [("mexc", "BBB", 0.45 if 20 < k < 190 else 0.0), ("gate", "BBB", 0.0)]
        return out
    rows = market(230, fn)
    real = P.ledger_of(live(rows))
    start = P.start_of(rows)
    assert start == T0 + 71 * H  # the hour the radar's 72-hour window is first full
    book = P.ledger_of(P.replay(rows, P.rules("original"), start))
    f = P.fidelity(book, real, start)
    assert f["real_positions"] >= 2 and f["matched"] == f["real_positions"] == f["same_net"] and f["trustworthy"]
    assert not f["only_in_the_real_ledger"] and not f["only_in_the_replay"]
    assert [m["pnl_bp_total"] for m in book["marks"]] == [m["pnl_bp_total"] for m in real["marks"] if m["t"] >= start]


def test_a_position_the_radar_already_held_at_the_start_is_the_expected_difference():
    rows = market(200, steady)
    real = P.ledger_of(live(rows))          # opened at hour 71, as soon as 72 hours were in hand
    late = T0 + 120 * H
    book = P.ledger_of(P.replay(rows, P.rules("original"), late))
    f = P.fidelity(book, real, late)
    assert f["held_at_the_start"] == ["AAA"] and f["real_positions"] == 0
    assert len(f["only_in_the_replay"]) == 1 and f["explained_by_a_position_held_at_the_start"] == 1


def test_nothing_is_traded_or_marked_before_the_start():
    rows = market(200, steady)
    s = P.replay(rows, P.rules("original"), T0 + 100 * H)
    assert s.marks[0]["t"] == T0 + 100 * H and s.runs == 100 and s.open[0].opened == T0 + 100 * H


def test_an_unknown_variant_is_refused():
    with pytest.raises(KeyError, match="declared in code"):
        P.rules("my-new-idea")
    assert set(P.VARIANTS) == {"original", "same-window", "thick-entry", "patient-exit", "all-three"}
    assert P.VARIANTS["original"] == {} and P.rules("original") == R.Rules()


def churn(k):
    """A coin whose spread was wide three days ago and is gone, with one hour in four showing 20%/yr: the 72-hour
    mean still passes the entry while the 24-hour mean has already decayed."""
    if k < 40:
        return [("mexc", "CCC", 1.50), ("gate", "CCC", 0.0)]
    return [("mexc", "CCC", 0.20 if k % 4 == 0 else 0.0), ("gate", "CCC", 0.0)]


def test_the_original_churns_on_a_spread_that_is_gone_and_the_same_window_variant_does_not():
    rows = market(110, churn)
    start = P.start_of(rows)
    a = P.ledger_of(P.replay(rows, P.rules("original"), start))
    b = P.ledger_of(P.replay(rows, P.rules("same-window"), start))
    assert len(a["closed"]) >= 3 and all(p["reason"] == "spread_decayed" for p in a["closed"])
    assert all(P.net_bp(p) < -30 for p in a["closed"])  # each turn is a full round trip of costs and almost no carry
    assert not b["closed"] and not b["open"]
    end = rows[-1]["t"] + H
    wa, wb = P.window(a, RF, start, end), P.window(b, RF, start, end)
    assert wa["book_excess_pct"] < 0 and wb["book_excess_pct"] == 0 and wb["positions"] == 0
    assert P.paired(wb, wa)["sum_difference_pct"] == pytest.approx(-wa["book_excess_pct"], abs=1e-4)


def test_the_thick_entry_variant_leaves_a_thin_spread_alone():
    rows = market(120, lambda k: [("mexc", "DDD", 0.35), ("gate", "DDD", 0.0)])
    start = P.start_of(rows)
    assert len(P.replay(rows, P.rules("original"), start).open) == 1
    assert not P.replay(rows, P.rules("thick-entry"), start).open


def test_the_patient_exit_variant_holds_through_one_bad_hour():
    def fn(k):
        return [("mexc", "EEE", -0.40 if k == 100 else 0.80), ("gate", "EEE", 0.0)]
    rows = market(130, fn)
    start = P.start_of(rows)
    a, b = P.replay(rows, P.rules("original"), start), P.replay(rows, P.rules("patient-exit"), start)
    assert a.closed and a.closed[0].reason == "spread_reversed" and a.closed[0].closed == T0 + 100 * H
    assert not b.closed and b.open[0].opened == start


# ── measuring on a window ───────────────────────────────────────────────────

def test_a_window_counts_the_hours_inside_it_and_the_positions_opened_inside_it():
    rows = market(24 * 9, steady)
    start = P.start_of(rows)  # day 3
    book = P.ledger_of(P.replay(rows, P.rules("original"), start))
    end = rows[-1]["t"] + H
    cut = T0 + 6 * DAY
    early, late, whole = (P.window(book, RF, a, b) for a, b in ((start, cut), (cut, end), (start, end)))
    assert early["days"] == 3 and late["days"] == 3 and whole["days"] == 6
    assert early["positions"] == 1 and late["positions"] == 0  # opened in the earlier part, never in the later
    assert early["book_excess_pct"] + late["book_excess_pct"] == pytest.approx(whole["book_excess_pct"], abs=2e-4)
    # one position on a 60%/yr spread: about 0.6 * 3/365 of N a part, on a book of 20N, less the cash on its 2N
    carry = (0.60 - 2 * RF) * 3 / 365 / 20 * 100
    assert late["book_excess_pct"] == pytest.approx(carry, rel=0.02)


def test_the_hour_after_a_missed_run_is_still_counted():
    rows = [r for r in market(24 * 6, steady) if r["t"] != T0 + 4 * DAY - H]  # the radar missed 23:00 before the cut
    start = P.start_of(rows)
    book = P.ledger_of(P.replay(rows, P.rules("original"), start))
    late = P.window(book, RF, T0 + 4 * DAY, T0 + 6 * DAY)
    assert late["days"] == 2 and late["book_excess_pct"] > 0
    whole = P.window(book, RF, start, T0 + 6 * DAY)
    early = P.window(book, RF, start, T0 + 4 * DAY)
    assert early["book_excess_pct"] + late["book_excess_pct"] == pytest.approx(whole["book_excess_pct"], abs=2e-4)


# ── the chronological validation ────────────────────────────────────────────

def two_regimes(k):
    """Earlier part: a thin 35%/yr spread that persists (the original profits from it, the thick entry stays out).
    Later part: the same coin only churns. A second coin churns throughout."""
    out = [("mexc", "FFF", 0.35 if k < 24 * 6 else (0.20 if k % 4 == 0 else 0.0)), ("gate", "FFF", 0.0)]
    return out


def test_the_candidate_is_chosen_on_the_earlier_part_and_a_short_later_part_judges_nothing():
    rows = market(24 * 11, two_regimes)
    v = P.validate(rows, RF)
    assert v["start"] == T0 + 71 * H and v["cut"] == T0 + 6 * DAY and v["end"] == T0 + 11 * DAY
    assert v["configurations_compared"] == 4
    best_earlier = max((n for n in P.VARIANTS if n != "original"), key=lambda n: v["variants"][n]["earlier"]["book_excess_pct"])
    assert v["candidate"] == best_earlier
    assert v["status"] == "INCONCLUSIVE" and "30" in v["why"] and not v["gates_on_the_later_part"]["enough_days"]
    assert v["variants"][v["candidate"]]["later"]["days"] == 5


def test_the_later_part_is_never_used_to_choose():
    rows = market(24 * 11, two_regimes)
    v = P.validate(rows, RF)
    earlier = {n: v["variants"][n]["earlier"]["book_excess_pct"] for n in P.VARIANTS}
    later = {n: v["variants"][n]["later"]["book_excess_pct"] for n in P.VARIANTS}
    # the thin spread paid on the earlier part and cost on the later one: who took it leads early and trails late
    assert earlier["same-window"] > earlier["thick-entry"] == 0 and later["same-window"] < later["thick-entry"] == 0
    assert max((n for n in P.VARIANTS if n != "original"), key=later.get) == "thick-entry"
    assert v["candidate"] == "same-window"  # chosen where it led; the later part would have chosen another


def test_too_few_hours_validate_nothing():
    assert P.validate(market(80, steady), RF)["status"] == "NOT ENOUGH HOURS"
    assert P.validate([], RF)["status"] == "NOT ENOUGH HOURS"


def test_every_gate_is_required_and_a_short_part_fails_on_its_length():
    good = {"days": 40, "closed": 35, "book_excess_pct": 1.2, "t_daily": 3.4, "excess_costs_x1.5_pct": 0.4,
            "excess_without_best_coin_pct": 0.6}
    pair = {"t": 3.1}
    assert all(P.gates(good, pair).values())
    for k, v, name in (("days", 29, "enough_days"), ("closed", 29, "enough_positions"), ("t_daily", 2.9, "excess_over_cash"),
                       ("book_excess_pct", -0.1, "excess_over_cash"), ("excess_costs_x1.5_pct", 0.0, "costs_x1.5"),
                       ("excess_without_best_coin_pct", 0.0, "without_best_coin"), ("t_daily", None, "excess_over_cash")):
        g = P.gates({**good, k: v}, pair)
        assert not g[name] and sum(not x for x in g.values()) == 1, k
    assert not P.gates(good, {"t": 2.9})["beats_the_original"] and not P.gates(good, {"t": None})["beats_the_original"]


# ── a registered challenger ─────────────────────────────────────────────────

def recurring(k):
    """Every four days a coin's spread is very wide for one day, then gone but for one hour in four at 18%/yr. For a
    day and a half after each burst the 72-hour mean still passes the original's entry while the 24-hour mean has
    decayed: the original re-enters at every blip and is closed the next hour."""
    burst = k % 96 < 24
    return [("mexc", "RRR", 1.50 if burst else (0.18 if k % 4 == 0 else 0.0)), ("gate", "RRR", 0.0)]


def test_a_challenger_waits_for_its_look_and_counts_only_hours_after_its_registration(tmp_path):
    rows = market(24 * 12, recurring)
    ch = {"id": "C-TEST", "variant": "same-window", "registered_t": T0 + 5 * DAY, "look_days": 6}
    early = P.forward(ch, rows, RF, now=T0 + 8 * DAY)
    assert early["status"] == "WAIT" and early["look_t"] == T0 + 11 * DAY
    assert P.freeze(tmp_path, early)["status"] == "WAIT" and not list(tmp_path.glob("challenger-*"))
    done = P.forward(ch, rows, RF, now=T0 + 12 * DAY)
    # both books start empty at the registration hour and stop at the look: nothing outside those hours is counted
    for name in ("original", "same-window"):
        book = P.ledger_of(P.replay(rows, P.rules(name), ch["registered_t"], done["look_t"]))
        key = "original" if name == "original" else "challenger"
        assert done[key]["positions"] == len(book["closed"]) + len(book["open"])
        assert all(ch["registered_t"] <= p["opened"] < done["look_t"] for p in book["closed"] + book["open"])
        assert book["marks"][0]["t"] == ch["registered_t"] and book["marks"][-1]["t"] == done["look_t"] - H
    whole = P.ledger_of(P.replay(rows, P.rules("original"), P.start_of(rows)))
    assert sum(1 for p in whole["closed"] if p["opened"] < ch["registered_t"]) >= 3  # churn before it: not counted
    assert done["original"]["positions"] > done["challenger"]["positions"] >= 1
    assert done["challenger_less_original"]["sum_difference_pct"] > 0
    assert done["status"] == "INCONCLUSIVE" and not done["gates"]["enough_days"]  # six days judge nothing


def test_a_look_is_frozen_once_and_read_back_ever_after(tmp_path):
    first = {"id": "C-TEST", "status": "FAILED", "gates": {"excess_over_cash": False}, "note": "the look"}
    assert P.freeze(tmp_path, first) == first
    luckier = {"id": "C-TEST", "status": "PASSED", "gates": {"excess_over_cash": True}, "note": "a later, luckier day"}
    assert P.freeze(tmp_path, luckier) == first
    assert json.loads((tmp_path / "challenger-C-TEST-look.json").read_text())["status"] == "FAILED"


def test_beating_the_original_by_losing_less_is_not_enough_to_pass():
    """A challenger that stays out of the churn beats the original day after day, and still proves no edge: it must
    also earn more than cash by its own account."""
    rows = market(24 * 80, recurring)
    ch = {"id": "C-IDLE", "variant": "same-window", "registered_t": T0 + 5 * DAY, "look_days": 60}
    done = P.forward(ch, rows, RF, now=T0 + 70 * DAY)
    assert done["original"]["book_excess_pct"] < done["challenger"]["book_excess_pct"]
    assert done["challenger_less_original"]["sum_difference_pct"] > 0 and done["gates"]["beats_the_original"]
    assert done["gates"]["enough_days"] and done["gates"]["enough_positions"] is not None
    assert not done["gates"]["excess_over_cash"] and done["status"] in ("FAILED", "INCONCLUSIVE")


# ── the radar itself is untouched ───────────────────────────────────────────

def test_the_radars_registered_code_is_unchanged():
    import scripts.radar_judge as J
    assert J.code_hash() == "d6690e181dbcd6a5e131a88b9b2b7912807429f8b6ea57a1e2dd1551e6112763"
    assert J.registry().get("RADAR-1").design["code_sha256"] == J.code_hash()
