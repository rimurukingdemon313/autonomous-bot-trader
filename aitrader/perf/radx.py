"""RADX-1: where the funding radar's losses come from, stated on its earlier positions and checked on its later ones.

The radar's public paper ledger is split by the hour a position was opened. What the earlier part showed is written
as two predictions about properties known when a position is opened; each is then computed once on the later part
(research/preregistrations/RADX-1.md). The arithmetic is exact: it reads recorded positions and assumes nothing.

It is a test of a diagnosis, not of a remedy. Removing a class of entries changes which later entries happen, and
the ledger cannot show the positions that were never opened: a remedy is measured by replaying the radar's rules on
its stored quotes (aitrader/perf/replay.py), and then forward.
"""

from __future__ import annotations

from .stats import mean_t

#: Positions opened before this hour are the design part (2026-10-30 11:00 UTC). Fixed on 2026-11-13, before any
#: outcome of a later position was computed: it was the 60th percentile of the opening times of the 204 positions
#: closed by then.
CUT = 1793358000
#: The round trip costs 33 to 39 bp. A position opened on a trailing spread under this earns less than that in the
#: few days such spreads last.
THIN_APR = 0.50
#: A position opened this soon after the same coin's previous position was closed for a decayed spread.
CHURN_H = 6
BAR = 3.0


def net_bp(p: dict) -> float:
    """Funding received, plus what the two legs' prices did, less every fill's cost: in bp of one leg's notional."""
    basis = ((p["long_px"] / p["long_px0"] - 1) - (p["short_px"] / p["short_px0"] - 1)) * 1e4
    return p["funding_bp"] + basis - p["cost_bp"]


def classify(closed: list[dict]) -> list[dict]:
    """Each closed position with what was known when it was opened: its entry spread, and how long before it the same
    coin's previous position had closed, and why. Positions are read in the order they were opened."""
    out, last = [], {}
    for p in sorted(closed, key=lambda p: (p["opened"], p["id"])):
        prev = last.get(p["coin"])
        gap_h = None if prev is None or prev[0] > p["opened"] else (p["opened"] - prev[0]) / 3600
        out.append({"id": p["id"], "coin": p["coin"], "opened": p["opened"], "closed": p["closed"], "net_bp": net_bp(p),
                    "thin": p["entry_spread_apr"] < THIN_APR,
                    "churn": gap_h is not None and gap_h <= CHURN_H and prev[1] == "spread_decayed",
                    "hours_since_previous": gap_h, "previous_reason": None if prev is None else prev[1]})
        last[p["coin"]] = (p["closed"], p["reason"])
    return out


def _side(rows: list[dict], key: str) -> dict:
    """The class's own figures, and the same without the coin that lost the most in it (one coin must not carry it)."""
    xs = [r["net_bp"] for r in rows if r[key]]
    rest = [r["net_bp"] for r in rows if not r[key]]
    m, t = mean_t(xs)
    by: dict[str, float] = {}
    for r in rows:
        if r[key]:
            by[r["coin"]] = by.get(r["coin"], 0.0) + r["net_bp"]
    worst = min(by, key=by.get) if by else None
    without = [r["net_bp"] for r in rows if r[key] and r["coin"] != worst]
    mw, _ = mean_t(without)
    return {"positions": len(xs), "sum_bp": sum(xs), "mean_bp": m, "t": t, "won": sum(x > 0 for x in xs),
            "coins": len(by), "coins_negative": sum(v < 0 for v in by.values()), "worst_coin": worst,
            "mean_bp_without_worst_coin": mw, "others": len(rest), "others_mean_bp": mean_t(rest)[0]}


def holds(side: dict) -> bool:
    """A prediction holds when the class loses on average at the bar, and still loses without its worst coin."""
    return (side["t"] is not None and side["t"] <= -BAR and side["mean_bp"] < 0
            and side["mean_bp_without_worst_coin"] is not None and side["mean_bp_without_worst_coin"] < 0)


def evaluate(ledger: dict, cut: int = CUT) -> dict:
    """Both parts' figures, and the verdict from the later part alone. Open positions are left out: their outcome is
    not final. A position counts for the part it was OPENED in."""
    rows = classify(ledger["closed"])
    parts = {"design": [r for r in rows if r["opened"] < cut], "later": [r for r in rows if r["opened"] >= cut]}
    out = {"cut": cut, "thin_apr": THIN_APR, "churn_hours": CHURN_H, "bar": BAR,
           "snapshot_t": ledger["marks"][-1]["t"] if ledger.get("marks") else None}
    for name, part in parts.items():
        m, t = mean_t([r["net_bp"] for r in part])
        out[name] = {"positions": len(part), "sum_bp": sum(r["net_bp"] for r in part), "mean_bp": m, "t": t,
                     "P1_thin_entries": _side(part, "thin"), "P2_churn_after_decay": _side(part, "churn"),
                     "either": _side([{**r, "either": r["thin"] or r["churn"]} for r in part], "either")}
    later = out["later"]
    gates = {"P1_thin_entries": holds(later["P1_thin_entries"]), "P2_churn_after_decay": holds(later["P2_churn_after_decay"])}
    out["gates"] = gates
    out["verdict"] = "PASSED" if all(gates.values()) else "FAILED"
    return out


__all__ = ["BAR", "CHURN_H", "CUT", "THIN_APR", "classify", "evaluate", "holds", "net_bp"]
