"""Who lost it: the market, or us? (owner, 2026-10-25: "make it so that if we lose, it is the market").

Every closed trade is checked, from the system's own journal, against everything the system controls. A trade
that passes every check lost (or won) to the market. A trade that fails one is OURS: a defect to find and fix,
never a market result, and it is named with the check it failed.

OURS, the checks:
    RULES     an approving risk verdict exists and every check in it passed (the rules in force that day)
    GATE      the hard risk gate approved this decision
    DATA      no data flags on the decision; the fill's quote no older than the gate's limit, nor stamped after it
    SIZE      sized to lose no more than the per-trade risk
    DESK      both traders chose the side traded (dual-AI trades)
    TIME      closed by its time exit when that came (TIME_SLACK_S of slack: the monitor runs every few seconds)
    WEEKEND   not open across the Friday close (17:00 New York)
    COSTS     the costs within COST_SLACK times the planned costs, plus COST_FLOOR_USD
    a check that cannot be read from the journal fails: missing evidence never clears us.

MARKET, when every check passed:
    STOP              stopped at its stop, the loss within the plan
    STOP_BEYOND_PLAN  stopped, filled beyond the planned loss: a gap or the spread at the stop. The market's, named
                      because it is beyond the plan (and whether it came in the rollover, 20:55-22:15 UTC)
    TIME_EXIT         closed by its time exit at a loss
    TARGET / CLOSED   a win at its target, or a trade closed for another reason (named)

Presentation and measurement only: nothing here can open, size or close a trade.
"""

from __future__ import annotations

import json
from collections import Counter
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

BLAME_VERSION = "blame-1.0.0"
NEW_YORK = ZoneInfo("America/New_York")
TIME_SLACK_S = 600
COST_SLACK, COST_FLOOR_USD = 1.5, 5.0
#: a loss this much beyond its planned maximum (and BEYOND_PLAN_USD) is beyond the plan
BEYOND_PLAN_REL, BEYOND_PLAN_USD = 0.02, 2.0
QUOTE_FUTURE_S = 5


def _ts(x) -> float | None:
    if isinstance(x, (int, float)) and not isinstance(x, bool):
        return float(x)
    if isinstance(x, str):
        try:
            return datetime.fromisoformat(x.replace("Z", "+00:00")).timestamp()
        except ValueError:
            return None
    return None


def _friday_close_after(t: float) -> float:
    """The first Friday 17:00 New York at or after `t`."""
    ny = datetime.fromtimestamp(t, NEW_YORK)
    close = (ny + timedelta(days=(4 - ny.weekday()) % 7)).replace(hour=17, minute=0, second=0, microsecond=0)
    if close.timestamp() < t:
        close = (close + timedelta(days=7))
    return close.timestamp()


def _in_rollover(t: float) -> bool:
    u = datetime.fromtimestamp(t, timezone.utc)
    m = u.hour * 60 + u.minute
    return 20 * 60 + 55 <= m <= 22 * 60 + 15


def verdict(outcome: dict, *, decision: dict | None, risk: list[dict], gate_approved: bool | None,
            position: dict | None, per_trade_risk: float, max_quote_age_s: float) -> dict:
    """One closed trade's verdict. `risk`: the risk verdicts recorded for its decision ({"approved", "checks"});
    `gate_approved`: whether the hard gate approved it (None: not read); `position`: its position record."""
    o, faults = outcome or {}, []
    net, planned = o.get("net_pnl"), o.get("planned_max_loss")
    opened, closed = _ts(o.get("opened")), _ts(o.get("closed"))
    if not isinstance(net, (int, float)) or opened is None or closed is None:
        return {"version": BLAME_VERSION, "decision_id": o.get("decision_id"), "verdict": "OURS",
                "faults": ["UNREADABLE: the trade's result or times cannot be read"], "market": None}
    # RULES
    approving = [r for r in risk if r.get("approved")]
    if not approving:
        faults.append("RULES: no approving risk verdict")
    else:
        failed = sorted({c.get("name") for r in approving for c in r.get("checks") or [] if not c.get("passed")})
        if failed:
            faults.append(f"RULES: approved with failed checks {failed}")
    # GATE
    if gate_approved is not True:
        faults.append("GATE: no hard-gate approval" if gate_approved is False else "GATE: the gate's decision is not read")
    # DATA
    flags = ((decision or {}).get("context") or {}).get("data_flags") if decision is not None else None
    if decision is None:
        faults.append("DATA: the decision is not in the journal")
    elif flags:
        faults.append(f"DATA: decided on flagged data {flags}")
    q = ((position or {}).get("quote_at_entry") or {}) if position is not None else {}
    qt = _ts(q.get("time"))
    if qt is None:
        faults.append("DATA: the fill's quote is not recorded")
    elif opened - qt > max_quote_age_s or qt - opened > QUOTE_FUTURE_S:
        faults.append(f"DATA: filled on a quote {opened - qt:.0f}s old (max {max_quote_age_s:.0f}s)")
    # SIZE
    if not isinstance(planned, (int, float)) or planned <= 0:
        faults.append("SIZE: the planned maximum loss is not recorded")
    elif planned > per_trade_risk + 0.01:
        faults.append(f"SIZE: sized to lose ${planned:.2f}, above the per-trade ${per_trade_risk:.2f}")
    # DESK
    da = o.get("dual_ai")
    if o.get("source") == "DUAL_AI" or da is not None:
        da = da or {}
        sides = {da.get("trader1_direction"), da.get("trader2_direction")}
        if da.get("rule") != "AGREE" or sides != {o.get("direction")}:
            faults.append(f"DESK: not both traders' choice (rule {da.get('rule')}, traders {sorted(map(str, sides))})")
    # TIME
    hold = (decision or {}).get("max_hold_minutes")
    held = o.get("holding_s")
    if isinstance(hold, (int, float)) and isinstance(held, (int, float)) and held > hold * 60 + TIME_SLACK_S:
        faults.append(f"TIME: held {held / 60:.0f} min, its time exit was {hold:.0f} min")
    # WEEKEND
    if closed > _friday_close_after(opened):
        faults.append("WEEKEND: open across the Friday close")
    # COSTS
    ec = o.get("expected_costs") or {}
    plan_costs = sum(float(ec.get(k) or 0.0) for k in ("commission", "slippage", "financing", "of_which_spread"))
    costs = o.get("costs_total")
    if isinstance(costs, (int, float)) and plan_costs > 0 and costs > COST_SLACK * plan_costs + COST_FLOOR_USD:
        faults.append(f"COSTS: ${costs:.2f} against ${plan_costs:.2f} planned")
    reason = o.get("exit_reason")
    if net >= 0:
        market = "TARGET" if reason == "TARGET" else f"CLOSED ({reason})"
    elif reason == "STOP":
        beyond = isinstance(planned, (int, float)) and -net > planned * (1 + BEYOND_PLAN_REL) + BEYOND_PLAN_USD
        market = ("STOP_BEYOND_PLAN" + (" (in the rollover)" if _in_rollover(closed) else "")) if beyond else "STOP"
    elif reason == "TIME":
        market = "TIME_EXIT"
    else:
        market = f"CLOSED ({reason})"
    return {"version": BLAME_VERSION, "decision_id": o.get("decision_id"), "symbol": o.get("symbol"),
            "direction": o.get("direction"), "closed": closed, "net_pnl": round(net, 2),
            "planned_max_loss": planned, "verdict": "OURS" if faults else "MARKET", "faults": faults,
            "market": None if faults else market}


def summary(verdicts: list[dict]) -> dict:
    """Losses and wins by verdict; every OURS listed, with what failed."""
    losses = [v for v in verdicts if (v.get("net_pnl") or 0) < 0]
    ours = [v for v in verdicts if v["verdict"] == "OURS"]
    market_losses = [v for v in losses if v["verdict"] == "MARKET"]
    kinds = Counter((v["market"] or "").split(" (")[0] for v in market_losses)
    usd = Counter()
    for v in market_losses:
        usd[(v["market"] or "").split(" (")[0]] += v["net_pnl"]
    return {"version": BLAME_VERSION, "trades": len(verdicts), "losses": len(losses),
            "loss_usd": round(sum(v["net_pnl"] for v in losses), 2),
            "market_losses": len(market_losses), "market_loss_usd": round(sum(v["net_pnl"] for v in market_losses), 2),
            "market_by_kind": {k: {"n": n, "usd": round(usd[k], 2)} for k, n in kinds.most_common()},
            "ours": len(ours), "ours_losses": sum(1 for v in ours if v["net_pnl"] < 0),
            "ours_loss_usd": round(sum(v["net_pnl"] for v in ours if v["net_pnl"] < 0), 2),
            "ours_trades": [{k: v.get(k) for k in ("decision_id", "symbol", "direction", "closed", "net_pnl", "faults")}
                            for v in ours],
            "beyond_plan": [{k: v.get(k) for k in ("decision_id", "symbol", "direction", "closed", "net_pnl",
                                                   "planned_max_loss", "market")}
                            for v in market_losses if (v["market"] or "").startswith("STOP_BEYOND_PLAN")]}


def from_journal(db, outcomes: list[dict], *, per_trade_risk: float, max_quote_age_s: float) -> dict:
    """The verdict of each closed trade in `outcomes`, read from the journal `db`, and their summary."""
    out = []
    for o in outcomes:
        did = o.get("decision_id")
        row = db.one("SELECT payload FROM decisions WHERE id=?", (did,))
        decision = json.loads(row["payload"]) if row else None
        risk = [json.loads(r["payload"]) for r in db.query("SELECT payload FROM risk_verdicts WHERE decision_id=?", (did,))]
        gates = [r["approved"] for r in db.query("SELECT approved FROM risk_gate_log WHERE decision_id=? AND kind='DECISION'",
                                                 (did,))]
        prow = db.one("SELECT payload FROM positions WHERE decision_id=?", (did,))
        position = json.loads(prow["payload"]) if prow else None
        out.append(verdict(o, decision=decision, risk=risk, gate_approved=(any(gates) if gates else None),
                           position=position, per_trade_risk=per_trade_risk, max_quote_age_s=max_quote_age_s))
    return {**summary(out), "per_trade": out}


__all__ = ["BLAME_VERSION", "from_journal", "summary", "verdict"]
