"""Strict promotion gates: the only definition of VALIDATED in this repository (takeover audit).

Before the audit the word had four meanings: a registry verdict PASSED on a development period, an edge
registry VALIDATED reached by a holdout "sign rule" at t 0.26, a forward ELIGIBLE_FOR_REVIEW, and the
execution engine's edge status. They disagreed, and the README quoted whichever was handy. This module
is the one definition; `scripts/research_status.py` applies it to every experiment and writes the
canonical research_status.json, from which the README's headline is generated.

Statuses (exactly these):

    PROPOSED             an idea, not registered
    REGISTERED           frozen and registered; its evaluation has not produced a verdict
    FAILED               judged and did not pass, or a disqualifying gate failed
    PROMISING            positive after every cost with t >= 2.0 on data it was not selected on, and
                         nothing disqualifying failed; short of VALIDATED
    FORWARD_TESTING      PROMISING and running on an untouched forward period
    ELIGIBLE_FOR_REVIEW  every quantitative gate passed; awaits independent review and a human record
    VALIDATED            every gate passed, including review, reproduction, demo and a human record
    DEGRADED             was VALIDATED; the live record is significantly worse than tested
    RETIRED              withdrawn

A gate whose value was not measured FAILS. Absence of evidence is never a pass.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

PROMOTION_VERSION = "promotion-1.0.0"

STATUSES = ("PROPOSED", "REGISTERED", "FAILED", "PROMISING", "FORWARD_TESTING", "ELIGIBLE_FOR_REVIEW",
            "VALIDATED", "DEGRADED", "RETIRED")

#: name -> (description, test on the measured value). Fixed in code, versioned, never tuned on results.
GATES: dict[str, tuple[str, Callable[[Any], bool]]] = {
    "min_outcomes": ("at least 100 resolved evaluation outcomes", lambda v: v >= 100),
    "net_positive": ("positive net expectancy after every cost", lambda v: v > 0),
    "t_stat": ("t-statistic >= 2.5", lambda v: v >= 2.5),
    "median_positive": ("positive median trade", lambda v: v > 0),
    "first_half_positive": ("positive chronological first half", lambda v: v > 0),
    "second_half_positive": ("positive chronological second half", lambda v: v > 0),
    "forward_positive": ("positive untouched forward period", lambda v: v > 0),
    "costs_x2_positive": ("positive under 2x costs", lambda v: v > 0),
    "delay_positive": ("positive with one-bar or one-session delay", lambda v: v > 0),
    "no_leakage": ("no data leakage (tested)", lambda v: v is True),
    "no_survivorship": ("no survivorship bias", lambda v: v is True),
    "max_instrument_trade_share": ("no instrument contributes more than 50% of trades", lambda v: v <= 0.5),
    "max_day_profit_share": ("no day contributes more than 20% of total profits", lambda v: v <= 0.2),
    "max_month_profit_share": ("no month contributes more than 20% of total profits", lambda v: v <= 0.2),
    "max_trade_profit_share": ("no single trade contributes more than 10% of total profits", lambda v: v <= 0.1),
    "max_drawdown_r": ("maximum drawdown <= 20R", lambda v: v <= 20),
    "beats_baseline": ("better than the correct baseline", lambda v: v is True),
    "parameter_stability": ("parameter stability", lambda v: v is True),
    "feature_stability": ("feature stability", lambda v: v is True),
    "no_broker_anomaly": ("no dependence on one broker-specific anomaly", lambda v: v is True),
    "independent_review": ("independent code review", lambda v: v is True),
    "reproduced_clean": ("reproducible results from a clean environment", lambda v: v is True),
    "demo_consistent": ("demo execution does not invalidate the backtest", lambda v: v is True),
    "human_promotion_record": ("explicit human promotion record", lambda v: bool(v)),
}
#: Gates a person or a forward period must supply; the rest are measured by research.
HUMAN_OR_FORWARD = ("forward_positive", "independent_review", "reproduced_clean", "demo_consistent",
                    "human_promotion_record")
#: A failure of any of these makes the result FAILED, not merely short of validation.
DISQUALIFYING = ("net_positive", "costs_x2_positive", "no_leakage", "no_survivorship")


def evaluate(evidence: dict) -> dict:
    """Every gate with its measured value and pass/fail. A missing (None) value fails."""
    out: dict[str, dict] = {}
    for name, (desc, test) in GATES.items():
        v = evidence.get(name)
        try:
            ok = v is not None and bool(test(v))
        except TypeError:
            ok = False
        out[name] = {"required": desc, "value": v, "pass": ok}
    return out


def status(evidence: dict, *, registered: bool = True, judged: bool = True, forward_running: bool = False,
           degraded: bool = False, retired: bool = False) -> tuple[str, list[str]]:
    """(status, reasons). VALIDATED only when every gate passes; nothing here can be argued past."""
    if retired:
        return "RETIRED", ["withdrawn"]
    if not registered:
        return "PROPOSED", ["not registered"]
    if not judged:
        return "REGISTERED", ["no verdict yet"]
    g = evaluate(evidence)
    failed = [k for k, x in g.items() if not x["pass"]]
    if not failed:
        return ("DEGRADED" if degraded else "VALIDATED"), []
    hard = [k for k in failed if k in DISQUALIFYING and g[k]["value"] is not None]
    if hard:
        return "FAILED", [f"{k}: {g[k]['value']!r} ({g[k]['required']})" for k in hard]
    if all(k in HUMAN_OR_FORWARD for k in failed):
        return "ELIGIBLE_FOR_REVIEW", [f"awaiting {k}: {g[k]['required']}" for k in failed]
    t = evidence.get("t_stat")
    if (evidence.get("net_positive") or 0) > 0 and t is not None and t >= 2.0:
        return ("FORWARD_TESTING" if forward_running else "PROMISING"), \
            [f"{k}: {g[k]['value']!r} ({g[k]['required']})" for k in failed]
    return "FAILED", [f"{k}: {g[k]['value']!r} ({g[k]['required']})" for k in failed]


__all__ = ["DISQUALIFYING", "GATES", "HUMAN_OR_FORWARD", "PROMOTION_VERSION", "STATUSES", "evaluate", "status"]
