"""Post-mortems (per trade) and reflections (periodic): "why", not just "loss".

POST-MORTEM. Every closed trade gets a structured, deterministic cause:

    DATA_PROBLEM       the decision was made on flagged data
    EXECUTION_COST     fill slippage or spread at entry far beyond the plan
    REGIME_SHIFT       the regime at exit differs from the regime at entry
    EXIT_MANAGEMENT    reached +1R or more, then lost
    ENTRY_TIMING       immediately adverse: never reached +0.2R, stopped within 2 bars
    NORMAL_VARIANCE    a loss the prediction itself said was likely
    THESIS_WRONG       none of the above: the analysis was wrong
    THESIS_CONFIRMED   a win the prediction expected
    FAVOURABLE_VARIANCE a win the prediction thought unlikely

"Normal variance" is a real answer: a setup with a 45% predicted win rate
loses more often than not, and treating each of those losses as a mistake is
exactly how a system talks itself into curve-fitting.

REFLECTION. Periodically, over everything resolved so far: calibration,
overconfidence, repeated mistakes, where the system does well and badly,
whether objections and the risk engine reject good trades, whether execution
rather than analysis is costing money, drift, and LLM reliability. It
produces HYPOTHESES; it never changes behaviour itself — the lesson lifecycle
(experience.py) and offline experiments do that, with evidence.
"""

from __future__ import annotations

import math
import statistics as st
from collections import Counter, defaultdict

REVIEW_VERSION = "review-1.0.0"


def postmortem(trade: dict) -> dict:
    """`trade` keys: r, mfe_r, mae_r, bars_held, exit_reason, predicted_win, predicted_r,
    slippage_r, spread_entry, spread_decision, regime_entry, regime_exit, data_flags."""
    r = trade.get("r")
    if r is None or not math.isfinite(r):
        return {"version": REVIEW_VERSION, "outcome": "UNKNOWN", "cause": "UNKNOWN",
                "explanation": "result could not be measured; nothing is inferred"}
    outcome = "WIN" if r > 0.05 else "LOSS" if r < -0.05 else "FLAT"
    p = trade.get("predicted_win")
    mfe, bars = trade.get("mfe_r") or 0.0, trade.get("bars_held") or 0
    why: list[str] = []
    cause = None
    if trade.get("data_flags"):
        cause = "DATA_PROBLEM"
        why.append(f"decision used flagged data: {trade['data_flags']}")
    elif (trade.get("slippage_r") or 0) > 0.15 or (
            trade.get("spread_entry") and trade.get("spread_decision")
            and trade["spread_entry"] > 2 * trade["spread_decision"]):
        cause = "EXECUTION_COST"
        why.append(f"slippage {trade.get('slippage_r', 0):.2f}R; spread at entry {trade.get('spread_entry')} "
                   f"vs {trade.get('spread_decision')} at decision")
    elif outcome == "LOSS":
        if trade.get("regime_entry") and trade.get("regime_exit") and trade["regime_entry"] != trade["regime_exit"]:
            cause = "REGIME_SHIFT"
            why.append(f"regime changed {trade['regime_entry']} -> {trade['regime_exit']} during the trade")
        elif mfe >= 1.0:
            cause = "EXIT_MANAGEMENT"
            why.append(f"was +{mfe:.2f}R before reversing to {r:+.2f}R")
        elif mfe < 0.2 and bars <= 2:
            cause = "ENTRY_TIMING"
            why.append(f"immediately adverse: best {mfe:+.2f}R, stopped after {bars} bar(s)")
        elif p is not None and 0.3 <= p <= 0.8:
            cause = "NORMAL_VARIANCE"
            why.append(f"predicted win probability {p:.0%}: a loss was {1 - p:.0%} likely")
        else:
            cause = "THESIS_WRONG"
            why.append("no execution, timing, regime or variance explanation fits")
    else:
        if outcome == "WIN" and p is not None and p < 0.3:
            cause = "FAVOURABLE_VARIANCE"
            why.append(f"won although predicted win probability was {p:.0%}")
        else:
            cause = "THESIS_CONFIRMED" if outcome == "WIN" else "NORMAL_VARIANCE"
            why.append("the result is consistent with the prediction")
    return {
        "version": REVIEW_VERSION, "outcome": outcome, "cause": cause, "explanation": "; ".join(why),
        "analysis_or_execution": "execution" if cause == "EXECUTION_COST" else "data" if cause == "DATA_PROBLEM" else "analysis",
        "thesis_invalidated": trade.get("exit_reason") == "STOP",
        "r": r, "mfe_r": mfe, "mae_r": trade.get("mae_r"), "bars_held": bars,
    }


def _stats(xs: list[float]) -> dict:
    n = len(xs)
    if n == 0:
        return {"n": 0, "mean": None, "se": None, "sample": "none"}
    m = sum(xs) / n
    se = (st.stdev(xs) / math.sqrt(n)) if n > 1 else None
    return {"n": n, "mean": round(m, 4), "se": round(se, 4) if se else None,
            "win_rate": round(sum(1 for x in xs if x > 0) / n, 3),
            "sample": "insufficient" if n < 30 else "adequate"}


def reflect(evaluations: list, postmortems: list[dict], t: int, llm_reliability: dict | None = None) -> dict:
    """A structured self-review over resolved evaluations (traded and shadow)."""
    traded = [e for e in evaluations if e.traded]
    skipped = [e for e in evaluations if not e.traded]
    out: dict = {"version": REVIEW_VERSION, "t": t, "resolved": len(evaluations),
                 "traded": _stats([e.outcome_r for e in traded]),
                 "skipped_shadow": _stats([e.outcome_r for e in skipped])}

    # Calibration: predicted win probability vs realised, in bins.
    bins: dict[str, list[tuple[float, float]]] = defaultdict(list)
    for e in traded:
        if e.predicted_win is not None:
            b = min(9, int(e.predicted_win * 10))
            bins[f"{b / 10:.1f}-{(b + 1) / 10:.1f}"].append((e.predicted_win, 1.0 if e.outcome_r > 0 else 0.0))
    cal = {k: {"n": len(v), "predicted": round(st.mean(p for p, _ in v), 3),
               "realised": round(st.mean(w for _, w in v), 3)} for k, v in sorted(bins.items())}
    out["calibration"] = cal
    preds = [(e.predicted_r, e.outcome_r) for e in traded if e.predicted_r is not None]
    if len(preds) >= 10:
        gap = st.mean(p for p, _ in preds) - st.mean(o for _, o in preds)
        out["overconfidence_R"] = round(gap, 4)
        # CUSUM of (outcome - prediction): sustained drift, not a bad week
        c, worst = 0.0, 0.0
        sd = st.pstdev([o - p for p, o in preds]) or 1.0
        for p, o in preds:
            c = min(0.0, c + (o - p) / sd + 0.5)
            worst = min(worst, c)
        out["drift_cusum"] = round(worst, 3)
        out["drift_alarm"] = worst < -8.0
    # Where it does well and badly.
    for field_ in ("regime", "family", "symbol", "session", "vol_state"):
        groups: dict[str, list[float]] = defaultdict(list)
        for e in traded:
            groups[str(getattr(e, field_))].append(e.outcome_r)
        out[f"by_{field_}"] = {k: _stats(v) for k, v in sorted(groups.items())}
    # Repeated mistakes.
    causes = Counter(pm.get("cause") for pm in postmortems if pm.get("outcome") == "LOSS")
    out["loss_causes"] = dict(causes.most_common())
    out["repeated_mistakes"] = [c for c, n in causes.items()
                                if c not in ("NORMAL_VARIANCE",) and n >= max(5, 0.25 * sum(causes.values()))]
    # Are objections and rejections costing good trades?
    flagged: dict[str, list[float]] = defaultdict(list)
    for e in evaluations:
        for code in set(e.objections):
            flagged[code].append(e.outcome_r)
    base = _stats([e.outcome_r for e in evaluations])
    out["objection_effect"] = {code: {**_stats(v), "vs_all": round((_stats(v)["mean"] or 0) - (base["mean"] or 0), 4)}
                               for code, v in sorted(flagged.items())}
    out["skipped_minus_traded_R"] = (round(out["skipped_shadow"]["mean"] - out["traded"]["mean"], 4)
                                     if out["skipped_shadow"]["mean"] is not None and out["traded"]["mean"] is not None else None)
    out["execution_share_of_losses"] = (round(causes.get("EXECUTION_COST", 0) / sum(causes.values()), 3)
                                        if causes else None)
    out["llm_reliability"] = llm_reliability or {}

    hyp = []
    for code, s in out["objection_effect"].items():
        if s["n"] >= 30 and s["vs_all"] is not None and s["vs_all"] > 0.02:
            hyp.append({"kind": "OBJECTION_UNINFORMATIVE", "code": code,
                        "text": f"trades flagged {code} did not do worse ({s['vs_all']:+.3f}R vs all, n={s['n']})"})
    if out.get("drift_alarm"):
        hyp.append({"kind": "MODEL_DRIFT", "text": "outcomes persistently below predictions (CUSUM alarm)"})
    if out["skipped_minus_traded_R"] is not None and out["skipped_minus_traded_R"] > 0.05 and out["skipped_shadow"]["n"] >= 30:
        hyp.append({"kind": "OVER_FILTERING", "text": "skipped candidates did better than traded ones"})
    for c in out["repeated_mistakes"]:
        hyp.append({"kind": "REPEATED_MISTAKE", "cause": c, "text": f"{c} recurs across losses"})
    out["hypotheses"] = hyp
    return out
