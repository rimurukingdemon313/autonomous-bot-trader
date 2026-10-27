"""The new account of a setup: only the trades opened from its start move it, the ones before are reported apart,
and a value that cannot be read makes its equity None, never a guess. Nothing in the journal is touched."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from aitrader.broker import periods

START = datetime(2026, 10, 26, 16, 22, tzinfo=timezone.utc).timestamp()
P = {"id": "p2", "starts": "2026-10-26T16:22:00Z", "start_balance": 200_000.0, "requested": "2026-10-27",
     "setup": "the new setup", "reason": "owner: a new account"}


def trade(opened, net, did, r=0.5):
    return {"decision_id": did, "opened": opened, "closed": opened + 3600, "net_pnl": net, "r": r}


def pos(opened, pnl, pid):
    return {"id": pid, "opened": opened, "pnl": pnl}


def test_only_the_trades_opened_from_its_start_move_the_new_account():
    old = [trade(START - 7200, -3000.0, "a", -1.0), trade(START - 60, -207.12, "b", -0.85)]
    new = [trade(START, -104.31, "c", -0.86), trade(START + 600, 250.0, "d", 1.2)]
    open_ = [pos(START + 900, 272.58, "P111"), pos(START + 4000, 47.16, "P112"), pos(START - 100, -10.0, "P0")]
    v = periods.view(old + new, open_, P)
    assert v["decision_ids"] == ["c", "d"] and v["performance"]["trades"] == 2
    assert v["closed_pnl"] == pytest.approx(145.69) and v["open_pnl"] == pytest.approx(319.74) and v["open"] == 2
    assert v["total_pnl"] == pytest.approx(465.43) and v["equity"] == pytest.approx(200_465.43)
    b = v["before"]  # kept apart, as theirs: never folded into the new account
    assert b["performance"]["trades"] == 2 and b["closed_pnl"] == pytest.approx(-3207.12) and b["open"] == 1
    assert b["equity"] is None  # the account before has no start of its own here: the whole account says it
    assert periods.period_of(new[0], P) == "p2" and periods.period_of(old[1], P) == "before"


def test_a_value_that_cannot_be_read_makes_the_equity_none_never_a_guess():
    v = periods.view([trade(START + 60, 100.0, "c")], [pos(START + 900, None, "P111")], P)
    assert v["equity"] is None and v["total_pnl"] is None and v["unpriced"] == 1 and v["closed_pnl"] == 100.0
    v = periods.view([trade(START + 60, None, "c")], [], P)
    assert v["equity"] is None and v["unpriced"] == 1


def test_a_new_account_with_no_trade_yet_is_its_start_and_nothing_else():
    v = periods.view([trade(START - 60, -50.0, "a")], [], P)
    assert v["equity"] == 200_000.0 and v["total_pnl"] == 0.0 and v["performance"]["trades"] == 0
    assert v["performance"]["sample"] == "none"


def test_the_declared_period_is_the_owners_new_account_from_the_first_shift_of_the_new_setup():
    p = periods.current()
    assert p["id"] == "new-setup-2026-10-26" and p["start_balance"] == 200_000.0
    assert periods._ts(p["starts"]) == START  # the first shift that ran both paid traders on Trader 1's levels
    assert "owner" in p["reason"] and "Trader 1" in p["setup"]
    assert periods.current(()) is None and periods.view([], [], None) is None
    later = {**P, "id": "p3", "starts": "2026-11-02T00:00:00Z"}
    assert periods.current((P, later))["id"] == "p3"  # the latest declared period is the account now
