"""A declared operator adjustment of the paper account: once per id, finite, journaled with the account state, and
only the trades the operator named (aitrader/broker/adjustments.py)."""

from __future__ import annotations

import json
import math

import pytest

from aitrader.broker import adjustments
from aitrader.broker.paper import PaperBroker
from aitrader.memory.db import Database


def test_the_declared_removal_names_exactly_the_four_trades_of_the_retired_debate_rule():
    (adj,) = adjustments.DECLARED
    assert adj["rule"] == "DEBATE" and adj["requested"] == "2026-10-15" and "journal" in adj["reason"]
    assert sorted(adj["decision_ids"]) == sorted(["ea3d671b2daab0f128af67bc", "e5274d880fc3d2b5a155b156",
                                                  "84ff17d2520ad60b7a8f52b8", "61b50d48c7fd17eff3124309"])


def test_an_adjustment_moves_the_balance_once_and_is_journaled_with_the_account(tmp_path):
    db = Database(tmp_path / "a.db")
    b = PaperBroker(None, lambda: 1_000, db, start_balance=200_000)
    assert b.adjust("x", 1416.51, "operator: test", {"rule": "DEBATE"}) is True
    assert b.adjust("x", 1416.51, "operator: test") is False  # the same id never moves it twice
    assert b.state["balance"] == pytest.approx(201_416.51)
    again = PaperBroker(None, lambda: 2_000, db, start_balance=200_000)  # a restart reads it back
    assert again.state["balance"] == pytest.approx(201_416.51) and [a["id"] for a in again.adjustments()] == ["x"]
    (ev,) = [json.loads(r["payload"]) for r in db.query("SELECT payload FROM events WHERE type='PAPER_ADJUSTMENT'")]
    assert ev["balance_before"] == 200_000 and ev["balance_after"] == pytest.approx(201_416.51) and ev["rule"] == "DEBATE"


@pytest.mark.parametrize("amount", [math.nan, math.inf, "1416", True, None])
def test_an_adjustment_that_is_not_a_finite_amount_is_refused_and_moves_nothing(tmp_path, amount):
    b = PaperBroker(None, lambda: 1_000, Database(tmp_path / "a.db"), start_balance=200_000)
    with pytest.raises(ValueError):
        b.adjust("x", amount, "operator: test")
    with pytest.raises(ValueError):
        b.adjust("y", 10.0, "")  # and never without a reason
    assert b.state["balance"] == 200_000 and b.adjustments() == []
