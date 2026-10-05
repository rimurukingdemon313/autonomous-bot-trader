"""Forward performance statistics, in R, with gross, costs and net kept apart.

Pure functions over the forward ledger's rows (learning/forward.py). Nothing here is fabricated: a
statistic that needs more data than exists is None, and every summary carries its sample label
("none" / "insufficient" below 30 / "adequate"). A 100% win rate over two trades is reported as
exactly that, with `sample: "insufficient"`.

ELIGIBILITY. `eligibility` applies the definition of a forward edge worth an operator's review
(docs/FORWARD_VALIDATION.md) to EVALUATION-partition outcomes only. It never promotes anything:
the most it says is ELIGIBLE_FOR_REVIEW. Promotion to VALIDATED is a reviewed, versioned act
(decision/edge_status.py).
"""

from __future__ import annotations

import math
import statistics as st
from collections import defaultdict
from datetime import datetime, timezone

METRICS_VERSION = "forward-metrics-1.0.0"
MIN_SAMPLE = 30

#: The forward-eligibility definition. Fixed in code, versioned, never tuned on results.
ELIGIBILITY = {
    "min_n": 100,              # resolved EVALUATION outcomes
    "min_t": 2.5,              # t of the mean net R
    "costs_x2_positive": True,  # still positive with every cost doubled
    "halves_positive": True,    # positive in both chronological halves
    "max_symbol_share": 0.5,    # no instrument supplies more than half the trades
    "max_day_share": 0.2,       # no single day supplies more than a fifth
    "max_drawdown_r": 20.0,     # worst peak-to-trough of cumulative net R
    "beats_baseline": True,     # net mean above the unconditional baseline over the same weeks
}


def _sample(n: int) -> str:
    return "none" if n == 0 else "insufficient" if n < MIN_SAMPLE else "adequate"


def _r(x, k=4):
    return None if x is None or not math.isfinite(x) else round(x, k)


def stats(rows: list[dict]) -> dict:
    """Summary of resolved outcomes. `rows` are ledger rows with an `outcome` (others are ignored)."""
    res = [r for r in rows if r.get("outcome") and r["outcome"].get("net_r") is not None]
    res.sort(key=lambda r: r["outcome"]["resolved_at"])
    net = [r["outcome"]["net_r"] for r in res]
    gross = [r["outcome"]["gross_r"] for r in res]
    cost = [r["outcome"]["cost_r"] for r in res]
    n = len(net)
    out = {"n": n, "sample": _sample(n), "proposals": len(rows),
           "unresolved": sum(1 for r in rows if not r.get("outcome")),
           "no_data": sum(1 for r in rows if r.get("outcome") and r["outcome"].get("net_r") is None)}
    if n == 0:
        return out
    wins = [x for x in net if x > 0]
    losses = [x for x in net if x <= 0]
    mean = st.mean(net)
    sd = st.stdev(net) if n > 1 else None
    se = sd / math.sqrt(n) if sd else None
    eq, peak, dd = 0.0, 0.0, 0.0
    for x in net:
        eq += x
        peak = max(peak, eq)
        dd = max(dd, peak - eq)
    run = worst_run = 0
    for x in net:
        run = run + 1 if x <= 0 else 0
        worst_run = max(worst_run, run)
    gl = -sum(losses)
    mfe = [r["outcome"].get("mfe_r") for r in res if r["outcome"].get("mfe_r") is not None]
    mae = [r["outcome"].get("mae_r") for r in res if r["outcome"].get("mae_r") is not None]
    out.update({
        "wins": len(wins), "losses": len(losses), "win_rate": _r(len(wins) / n, 3),
        "avg_r": _r(mean), "median_r": _r(st.median(net)), "expectancy_r": _r(mean), "sd_r": _r(sd),
        "t": _r(mean / se, 3) if se else None,
        "gross_r_total": _r(sum(gross), 3), "cost_r_total": _r(sum(cost), 3), "net_r_total": _r(sum(net), 3),
        "gross_avg_r": _r(st.mean(gross)), "cost_avg_r": _r(st.mean(cost)),
        "net_avg_costs_x2": _r(st.mean(g - 2 * c for g, c in zip(gross, cost))),
        "profit_factor": _r(sum(wins) / gl, 3) if gl > 0 else None,
        "avg_winner_r": _r(st.mean(wins)) if wins else None, "avg_loser_r": _r(st.mean(losses)) if losses else None,
        "max_drawdown_r": _r(dd, 3), "max_consecutive_losses": worst_run,
        "sharpe_like": _r(mean / sd, 3) if sd else None,  # per trade, not annualised: trades are irregular
        "mfe_avg_r": _r(st.mean(mfe)) if mfe else None, "mae_avg_r": _r(st.mean(mae)) if mae else None,
        "concentration": concentration(res),
    })
    return out


def concentration(res: list[dict]) -> dict:
    n = len(res)
    if not n:
        return {}

    def top(key):
        c: dict = defaultdict(int)
        for r in res:
            c[key(r)] += 1
        k, v = max(c.items(), key=lambda kv: kv[1])
        return {"top": k, "share": round(v / n, 3)}
    day = lambda r: datetime.fromtimestamp(r["t"], timezone.utc).strftime("%Y-%m-%d")  # noqa: E731
    return {"symbol": top(lambda r: r["symbol"]), "day": top(day),
            "model": top(lambda r: r.get("model") or "none"), "regime": top(lambda r: r.get("regime") or "?")}


def breakdown(rows: list[dict], key) -> dict:
    groups: dict = defaultdict(list)
    for r in rows:
        groups[str(key(r))].append(r)
    return {k: stats(v) for k, v in sorted(groups.items())}


def periods(rows: list[dict], fmt: str) -> dict:
    """Net R by day ("%Y-%m-%d"), week ("%G-W%V") or month ("%Y-%m") of resolution."""
    out: dict = defaultdict(lambda: {"n": 0, "net_r": 0.0, "gross_r": 0.0, "cost_r": 0.0})
    for r in rows:
        o = r.get("outcome")
        if not o or o.get("net_r") is None:
            continue
        k = datetime.fromtimestamp(o["resolved_at"], timezone.utc).strftime(fmt)
        out[k]["n"] += 1
        for f in ("net_r", "gross_r", "cost_r"):
            out[k][f] = round(out[k][f] + o[f], 4)
    return dict(sorted(out.items()))


def calibration(rows: list[dict]) -> dict:
    """Stated model confidence (probability of reaching the target) against what happened."""
    pairs = [(r["confidence"], 1.0 if r["outcome"]["reason"] == "TARGET" else 0.0) for r in rows
             if r.get("outcome") and r["outcome"].get("net_r") is not None and isinstance(r.get("confidence"), (int, float))]
    n = len(pairs)
    if not n:
        return {"n": 0, "sample": "none"}
    stated = st.mean(p for p, _ in pairs)
    hit = st.mean(w for _, w in pairs)
    se = math.sqrt(max(hit * (1 - hit), 1e-9) / n)
    bins: dict = defaultdict(list)
    for p, w in pairs:
        bins[f"{min(9, int(p * 10)) / 10:.1f}"].append((p, w))
    return {"n": n, "sample": _sample(n), "stated": round(stated, 3), "realised": round(hit, 3),
            "gap": round(stated - hit, 3), "z": round((stated - hit) / se, 2),
            "bins": {k: {"n": len(v), "stated": round(st.mean(p for p, _ in v), 3),
                         "realised": round(st.mean(w for _, w in v), 3)} for k, v in sorted(bins.items())}}


def eligibility(rows: list[dict], baseline_mean: float | None) -> dict:
    """Forward eligibility on EVALUATION rows. Returns every criterion with its measured value."""
    ev = [r for r in rows if r.get("partition") == "EVALUATION"]
    s = stats(ev)
    E = ELIGIBILITY
    res = sorted([r for r in ev if r.get("outcome") and r["outcome"].get("net_r") is not None],
                 key=lambda r: r["outcome"]["resolved_at"])
    half = len(res) // 2
    h = [st.mean(r["outcome"]["net_r"] for r in part) if part else None for part in (res[:half], res[half:])]
    conc = s.get("concentration") or {}
    crit = {
        "n": {"value": s["n"], "required": E["min_n"], "pass": s["n"] >= E["min_n"]},
        "mean_positive": {"value": s.get("avg_r"), "pass": (s.get("avg_r") or 0) > 0},
        "t": {"value": s.get("t"), "required": E["min_t"], "pass": (s.get("t") or 0) >= E["min_t"]},
        "costs_x2": {"value": s.get("net_avg_costs_x2"), "pass": (s.get("net_avg_costs_x2") or 0) > 0},
        "halves": {"value": [_r(x) for x in h], "pass": all(x is not None and x > 0 for x in h)},
        "symbol_share": {"value": (conc.get("symbol") or {}).get("share"), "required": E["max_symbol_share"],
                         "pass": ((conc.get("symbol") or {}).get("share") or 1) <= E["max_symbol_share"]},
        "day_share": {"value": (conc.get("day") or {}).get("share"), "required": E["max_day_share"],
                      "pass": ((conc.get("day") or {}).get("share") or 1) <= E["max_day_share"]},
        "drawdown": {"value": s.get("max_drawdown_r"), "required": E["max_drawdown_r"],
                     "pass": s.get("max_drawdown_r") is not None and s["max_drawdown_r"] <= E["max_drawdown_r"]},
        "baseline": {"value": baseline_mean, "pass": baseline_mean is not None and (s.get("avg_r") or 0) > baseline_mean,
                     "note": None if baseline_mean is not None else "no baseline measured over the same weeks: not passed"},
    }
    if s["n"] < MIN_SAMPLE:
        status = "INSUFFICIENT"
    elif all(c["pass"] for c in crit.values()):
        status = "ELIGIBLE_FOR_REVIEW"
    elif (s.get("avg_r") or 0) <= 0:
        status = "NOT_POSITIVE"
    else:
        status = "COLLECTING"
    return {"status": status, "criteria": crit, "evaluation": s, "version": METRICS_VERSION,
            "note": "ELIGIBLE_FOR_REVIEW is the most forward data can say: promotion to VALIDATED is a reviewed act"}


#: Track A vs Track B (takeover audit, step 9). Track A: every proposal the deterministic path made. Track B:
#: the same proposals minus those the advisory language model would have vetoed. Identical by construction
#: (one ledger, one set of decisions); the model's veto is applied only if B beats A here.
AI_VETO_RULE = {"min_n_each": 100, "min_t_difference": 2.0, "must_also_hold": ["costs_x2", "both_halves"]}


def ai_veto_ab(rows: list[dict]) -> dict:
    """Compare Track A (all EVALUATION proposals with a recorded model opinion) with Track B (A minus the
    would-vetoed ones). Rows without a recorded opinion (ai_would_veto None) are outside the experiment."""
    rows = [r for r in rows if r.get("partition") == "EVALUATION" and r.get("ai_would_veto") is not None
            and r.get("outcome") and r["outcome"].get("net_r") is not None]
    a = rows
    b = [r for r in rows if not r["ai_would_veto"]]
    vetoed = [r for r in rows if r["ai_would_veto"]]
    sa, sb, sv = stats(a), stats(b), stats(vetoed)
    nets_v = [r["outcome"]["net_r"] for r in vetoed]
    diff = None
    if len(vetoed) > 1 and len(b) > 1:
        # B - A per proposal equals removing the vetoed trades: test whether the vetoed mean is below the kept mean
        kept = [r["outcome"]["net_r"] for r in b]
        se = math.sqrt(st.variance(nets_v) / len(nets_v) + st.variance(kept) / len(kept))
        diff = _r((st.mean(kept) - st.mean(nets_v)) / se, 3) if se > 0 else None

    def by(key):
        return {k: {"A": stats([r for r in a if str(key(r)) == k]).get("avg_r"),
                    "B": stats([r for r in b if str(key(r)) == k]).get("avg_r")}
                for k in sorted({str(key(r)) for r in a})}
    out = {
        "rule": AI_VETO_RULE,
        "track_a": sa, "track_b": sb, "vetoed": {"n": len(vetoed), "avg_r": sv.get("avg_r"),
                                                  "missed_winners": sum(1 for x in nets_v if x > 0),
                                                  "avoided_losers": sum(1 for x in nets_v if x <= 0)},
        "t_kept_minus_vetoed": diff,
        "by_regime": by(lambda r: r.get("regime") or "?"), "by_symbol": by(lambda r: r["symbol"]),
        "costs_x2": {"A": sa.get("net_avg_costs_x2"), "B": sb.get("net_avg_costs_x2")},
    }
    enough = len(b) >= AI_VETO_RULE["min_n_each"] and len(vetoed) >= AI_VETO_RULE["min_n_each"]
    better = (diff is not None and diff >= AI_VETO_RULE["min_t_difference"]
              and (sb.get("net_avg_costs_x2") or -9) > (sa.get("net_avg_costs_x2") or -9))
    out["verdict"] = ("INSUFFICIENT" if not enough else
                      "VETO_HELPS: eligible for a reviewed decision to apply it" if better else
                      "VETO_DOES_NOT_HELP: keep it advisory")
    return out
