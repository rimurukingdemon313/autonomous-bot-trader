"""What the lab learns from its own record, and how that changes what it does next.

Every finished scan and validation leaves classed rules in the candidate ledger. From them, and from nothing else:

- `arms`: for each market and each family of rules, how many rules were emitted and what became of them;
- `lessons`: the same counts as plain statements, kept beside the ledger and given to the idea engine's proposer;
- `allocation`: how many rules each method may emit in the next scan. A method whose rules keep surviving gets more
  room, one whose rules keep overfitting gets less, and none falls below a floor: a family that has found nothing
  yet is still explored;
- `dataset_priority`: which market the queue should scan next: an unscanned one first, a broad one before a narrow
  one (many instruments are what give a pooled test its power), and a market whose earlier rules survived before one
  whose rules did not.

It decides order and effort only. It cannot change a rule's class, a bar or a verdict.
"""

from __future__ import annotations

import math

import numpy as np

METHOD_OF = {"cross-asset lead-lag": "leadlag", "own-lag": "leadlag", "information (non-linear)": "info",
             "ordinal pattern": "ordinal", "regime": "regimes", "anomaly": "anomaly", "evolved rule": "evolve"}
BASE, FLOOR, CEILING = 24, 8, 48
POSITIVE = ("INSUFFICIENT_POWER", "PROMISING_UNCONFIRMED")


def arms(ledger: list[dict], universe_of: dict[str, str]) -> dict[str, dict[str, dict]]:
    """universe -> family -> counts. `universe_of`: run id -> universe."""
    by_id: dict[tuple, tuple] = {}
    out: dict[str, dict[str, dict]] = {}
    for r in ledger:
        u = universe_of.get(r.get("run"))
        if u is None:
            continue
        if r.get("event") == "VALIDATION":
            fam = by_id.get((r["run"], r["id"]))
            if fam is not None:
                c = out[u][fam]
                c["validated" if r["class"] == "VALIDATED_ON_UNREAD_ROWS" else "rejected_by_validation"] += 1
            continue
        fam = r["family"]
        by_id[(r["run"], r["id"])] = fam
        c = out.setdefault(u, {}).setdefault(fam, {k: 0 for k in (
            "rules", "positive", "promising", "validated", "rejected_by_validation", "overfit", "negative",
            "negative_after_costs_only", "insufficient_data", "invalid", "duplicate")})
        c["rules"] += 1
        cls = r["class"]
        c["positive"] += cls in POSITIVE
        c["promising"] += cls == "PROMISING_UNCONFIRMED"
        c["overfit"] += cls == "OVERFIT"
        c["negative"] += cls == "NEGATIVE_EXPECTANCY"
        c["negative_after_costs_only"] += cls == "NEGATIVE_EXPECTANCY" and "positive before costs" in (r.get("reason") or "")
        c["insufficient_data"] += cls == "INSUFFICIENT_DATA"
        c["invalid"] += cls in ("SCIENTIFICALLY_INVALID", "REPEATS_CLOSED_FAMILY")
        c["duplicate"] += cls == "DUPLICATE"
    return out


def _total(table: dict[str, dict]) -> dict:
    out: dict = {}
    for c in table.values():
        for k, v in c.items():
            out[k] = out.get(k, 0) + v
    return out


def usefulness(c: dict) -> float:
    """A family's worth so far, as a posterior mean in (0, 1): a validated rule counts most, a promising one next, a
    merely positive one a little. With no rules yet it is the prior, one half."""
    good = 3.0 * c.get("validated", 0) + c.get("promising", 0) + 0.25 * (c.get("positive", 0) - c.get("promising", 0))
    return (1.0 + good) / (2.0 + c.get("rules", 0))


def allocation(table: dict[str, dict], seed: int = 0) -> dict[str, int]:
    """How many rules each method may emit in a market's next scan: Thompson sampling over each family's record there,
    so effort follows evidence and a family with little evidence is still tried."""
    rng = np.random.default_rng(seed)
    draw: dict[str, float] = {}
    for fam, method in METHOD_OF.items():
        c = table.get(fam, {})
        good = 3.0 * c.get("validated", 0) + c.get("promising", 0) + 0.25 * (c.get("positive", 0) - c.get("promising", 0))
        a, b = 1.0 + good, 1.0 + max(c.get("rules", 0) - good, 0.0)
        draw[method] = max(draw.get(method, 0.0), float(rng.beta(a, b)))
    mean = float(np.mean(list(draw.values())))
    return {m: int(min(CEILING, max(FLOOR, round(BASE * v / mean)))) for m, v in sorted(draw.items())}


def dataset_priority(n_instruments: int, table: dict[str, dict] | None) -> float:
    """An unscanned market first (1.0), breadth next (up to 1.0), then what its earlier rules were worth (up to 2.0)."""
    breadth = min(1.0, math.log2(max(n_instruments, 1) + 1) / math.log2(33))
    if not table:
        return round(1.0 + breadth, 4)
    return round(breadth + 2.0 * usefulness(_total(table)), 4)


def lessons(table: dict[str, dict[str, dict]], audits: dict[str, dict] | None = None) -> list[str]:
    """The record as statements a person, or a proposer model, can read."""
    out = []
    for u, fams in sorted(table.items()):
        t = _total(fams)
        if not t.get("rules"):
            continue
        out.append(f"{u}: {t['rules']} rules from data-driven discovery; {t['promising']} promising; "
                   f"{t['positive'] - t['promising']} positive out of sample but not told from noise; {t['negative']} lost "
                   f"out of sample ({t['negative_after_costs_only']} of them only after costs); {t['overfit']} overfit; "
                   f"{t['validated']} passed validation and {t['rejected_by_validation']} failed it")
        worst = max(fams.items(), key=lambda kv: kv[1]["overfit"] / max(kv[1]["rules"], 1))
        if worst[1]["rules"] >= 8 and worst[1]["overfit"] / worst[1]["rules"] >= 0.3:
            out.append(f"{u}: {worst[0]} rules overfit most often ({worst[1]['overfit']} of {worst[1]['rules']})")
        costly = [(f, c) for f, c in fams.items() if c["negative_after_costs_only"] >= 3]
        for f, c in sorted(costly):
            out.append(f"{u}: {c['negative_after_costs_only']} {f} rules were positive before costs and negative after: "
                       "this market's costs, not its information, stopped them")
        a = (audits or {}).get(u)
        if a:
            n = sum(v["features"] for v in a.values())
            hits = sum(v["z_at_least_2"] for v in a.values())
            nl = sum(v["non_linear_only"] for v in a.values())
            out.append(f"{u}: the information audit found {hits} of {n} feature-instrument pairs with z >= 2 about the next "
                       f"return ({nl} of them with no linear trace); chance alone gives about {0.023 * n:.1f}")
    return out


__all__ = ["METHOD_OF", "allocation", "arms", "dataset_priority", "lessons", "usefulness"]
