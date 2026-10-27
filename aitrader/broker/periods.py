"""Declared account periods of the PAPER account.

The owner asked, on 2026-10-27, for "a new account for the new setup". The paper account had lost $3,454 under
the setups that the fixes of 23-26 October replaced. A period is that new account: a paper account for one setup,
measured from the moment the setup first decided. It starts at `start_balance`, and only the trades opened from
`starts` move it:
- once closed, by their booked net P/L;
- while open, by their P/L as the broker values it.

Nothing is moved, removed or reset. The journal, the broker's balance, the hard gate and the risk engine are
untouched and keep guarding the whole account, which every report still shows. The trades before the period are
reported apart, as theirs. A value that cannot be read (an unpriced trade, an open position the broker cannot value)
makes the period's equity None, never a guess.

A period is declared here, in reviewed code. No request, dashboard control or model can open one.
"""

from __future__ import annotations

from datetime import datetime

from ..learning.paper_metrics import summary

PERIODS_VERSION = "paper-periods-1.0.0"

#: The owner's request (2026-10-27): a new account for the new setup, from the first shift that ran it. That shift
#: began 2026-10-26 16:22 UTC, the first with both traders paid (paid-trial 1.2.0, 2590c8b) and trades on Trader 1's
#: levels (dual-ai 1.10.0, 48bd1e8). The trades before it stay in the journal and are reported apart.
DECLARED: tuple[dict, ...] = (
    {"id": "new-setup-2026-10-26", "starts": "2026-10-26T16:22:00Z", "start_balance": 200_000.0,
     "requested": "2026-10-27",
     "setup": "dual-ai 1.10.0 (a trade on Trader 1's levels) with both traders paid (paid-trial 1.2.0: Trader 1 "
              "xiaomi/mimo-v2.6-pro, Trader 2 anthropic/claude-haiku-5.5)",
     "reason": "owner: a new account for the new setup, from the first shift that ran it; the account before it is "
               "kept and reported apart"},
)


def _ts(x) -> float | None:
    if isinstance(x, (int, float)) and not isinstance(x, bool):
        return float(x)
    if isinstance(x, str):
        try:
            return datetime.fromisoformat(x.replace("Z", "+00:00")).timestamp()
        except ValueError:
            return None
    return None


def current(declared: tuple[dict, ...] | None = None) -> dict | None:
    """The latest declared period, or None."""
    declared = DECLARED if declared is None else declared
    return max(declared, key=lambda p: _ts(p["starts"]) or 0.0) if declared else None


def _account(outcomes: list[dict], open_positions: list[dict], start: float | None) -> dict:
    closed_unpriced = sum(1 for o in outcomes if not isinstance(o.get("net_pnl"), (int, float)))
    closed = sum(o["net_pnl"] for o in outcomes if isinstance(o.get("net_pnl"), (int, float)))
    open_unpriced = sum(1 for p in open_positions if not isinstance(p.get("pnl"), (int, float)))
    open_pnl = None if open_unpriced else sum(p["pnl"] for p in open_positions)
    readable = not closed_unpriced and open_pnl is not None
    total = round(closed + open_pnl, 2) if readable else None
    return {"closed_pnl": round(closed, 2), "open_pnl": None if open_pnl is None else round(open_pnl, 2),
            "total_pnl": total, "equity": None if total is None or start is None else round(start + total, 2),
            "open": len(open_positions), "unpriced": closed_unpriced + open_unpriced,
            "performance": summary(outcomes)}


def view(outcomes: list[dict], open_positions: list[dict], period: dict | None) -> dict | None:
    """The period's own account, and the account before it, from the closed outcomes and the open positions."""
    if period is None:
        return None
    t0 = _ts(period["starts"])
    if t0 is None:
        return {"id": period.get("id"), "available": False, "reason": f"unreadable start {period.get('starts')!r}"}
    opened = lambda x: _ts(x.get("opened"))  # noqa: E731
    mine = [o for o in outcomes if (opened(o) or 0.0) >= t0]
    before = [o for o in outcomes if (opened(o) or 0.0) < t0]
    open_mine = [p for p in open_positions if (opened(p) or 0.0) >= t0]
    open_before = [p for p in open_positions if (opened(p) or 0.0) < t0]
    start = float(period["start_balance"])
    return {"version": PERIODS_VERSION, **{k: period[k] for k in ("id", "starts", "setup", "reason", "requested")},
            "start_balance": start, **_account(mine, open_mine, start),
            "decision_ids": [o.get("decision_id") for o in mine],
            "before": {"until": period["starts"], **_account(before, open_before, None)}}


def period_of(outcome_or_position: dict, period: dict | None) -> str | None:
    """The period a trade belongs to: the period's id from its start, "before" earlier; None without a period."""
    if period is None:
        return None
    t0, t = _ts(period["starts"]), _ts(outcome_or_position.get("opened"))
    return None if t0 is None or t is None else period["id"] if t >= t0 else "before"


__all__ = ["DECLARED", "PERIODS_VERSION", "current", "period_of", "view"]
