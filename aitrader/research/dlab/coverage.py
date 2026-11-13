"""What has been looked at out of sample, and what has not: the lab's map of its own search.

A discovery scan gives its places to the rules that are strongest on the fit rows. That is a choice, and it leaves
holes: the first scan of the perpetuals gave 22 of its 24 cross-sectional places to rankings on funding, and no
ranking on past returns or on volatility reached the check rows at all. A hole is not a result. This module names the
holes, so that the worker can fill them with a directed test and the research director can see them.

The map is over a declared space, and nothing wider: each ranking a cross-sectional book may be built on
(`methods.rankings`), at each holding period (`methods.XS_HOLDS`). A cell has been looked at once any book on that
ranking and that holding period has been evaluated on the check rows, whichever way it pointed and whatever share it
held: its direction is set by the fit rows, and the two shares are near enough one behaviour. A cell whose book was
refused before any test (it behaves as a closed family) is set aside, with the reason, and is not asked for again.

Filling the holes is the one task the lab gives itself. When there are none, it gives itself none, and says so.
"""

from __future__ import annotations

from .methods import XS_HOLDS, XS_SHARES, _f, rankings
from .panel import Panel, broad, key
from .signals import xs_book


def cell(feat: dict, hold: int) -> str:
    return f"{key(feat)}|{hold}"


def cells(p: Panel) -> list[tuple[dict, int]]:
    """Every cell of the panel's map, in a fixed order. A panel that is not broad has no cross-sectional book."""
    return [(f, h) for f in rankings(p) for h in XS_HOLDS] if broad(p) else []


def of_spec(spec: dict) -> str | None:
    """The cell a rule sits in, or None if it is not a cross-sectional book."""
    parts = spec.get("parts") or []
    if spec.get("kind") == "book" and parts and parts[0].get("kind") == "xsleg":
        x = parts[0]["xs"]
        return cell(x["feat"], x.get("hold", 1))
    return None


def looked_at(records: list[dict]) -> set[str]:
    """The cells of every cross-sectional book among the classed rules of one market."""
    return {c for c in (of_spec(r["spec"]) for r in records if isinstance(r.get("spec"), dict)) if c}


def set_aside(refusals: list[dict]) -> dict[str, str]:
    """cell -> why, for books refused before a test: a refusal names the rule's cell."""
    return {r["cell"]: r["why"] for r in refusals if r.get("cell")}


def gaps(p: Panel, records: list[dict], refusals: list[dict] | None = None) -> list[tuple[dict, int]]:
    """The cells no classed rule sits in and no refusal has set aside."""
    done = looked_at(records) | set(set_aside(refusals or []))
    return [(f, h) for f, h in cells(p) if cell(f, h) not in done]


def submission(dataset: str, p: Panel, holes: list[tuple[dict, int]], day: str, cycle_version: str) -> dict:
    """The lab's own submission: one book for each hole, pointed by the fit rows. The first share is used: a second
    book on the other share would be the same look."""
    n = len(p.assets)
    rules = [{"family": "cross-sectional", "orient": "fit", "cell": cell(f, h),
              "why": f"no rule ranking the instruments on {_f(f)} and held {h} rows has been looked at out of sample",
              "spec": xs_book(p, {"feat": f, "q": XS_SHARES[0], "hold": h, "min": max(6, n // 4), "side": 1})}
             for f, h in holes]
    names = sorted({_f(f) for f, _ in holes})
    return {"id": f"lab-coverage-{dataset}-{day}", "submitted": day,
            "author": {"role": "lab", "model": "none (deterministic code)", "interface": f"the lab's worker, {cycle_version}"},
            "dataset": dataset, "title": f"The cross-sectional rankings of {dataset} no scan has looked at out of sample",
            "hypothesis": ("Among the instruments of this panel, a ranking on one of the features below separates the "
                           "next rows' returns after costs. Each ranking is a separate, simple claim; none was chosen "
                           "because it looked strong: they are the rankings the scans' places did not reach."),
            "mechanism": ("None is claimed in advance. These are the remaining cells of a declared space ("
                          + ", ".join(names) + f"; held {', '.join(str(h) for h in XS_HOLDS)} rows), looked at so that "
                          "the space is covered and a missing result is not mistaken for a negative one."),
            "why_now": (f"{len(holes)} of the {len(cells(p))} ranking-and-holding-period cells of this panel have no "
                        "classed rule: the scans gave their places to the rankings strongest on the fit rows."),
            "refuted_by": ("A book that is not positive on the check rows in both halves, or that cannot be told from "
                           "the noise of every look already taken at those rows."),
            "parents": ["docs/DISCOVERY_LAB.md section 11", "aitrader/research/dlab/coverage.py"], "rules": rules}


__all__ = ["cell", "cells", "gaps", "looked_at", "of_spec", "set_aside", "submission"]
