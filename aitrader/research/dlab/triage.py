"""What becomes of every emitted rule: evaluated once on rows no method read, kept for ever, and classed.

Discovery asks for no significance. It asks six plainer questions, in this order, and the first that applies classes
the rule:

    SCIENTIFICALLY_INVALID   it reads the future, or it is only the instrument's own return (no timing)
    REPEATS_CLOSED_FAMILY    it behaves as a family the record has already judged and closed (named)
    INSUFFICIENT_DATA        too few rows in position on the check rows to estimate anything
    NEGATIVE_EXPECTANCY      it lost on the check rows (before costs, or only after them: said which)
    OVERFIT                  strong on the rows that shaped it, gone on the rows that did not
    DUPLICATE                it behaves as a stronger rule already kept (named): the diversity mechanism
    INSUFFICIENT_POWER       positive, but too small for the validation window: it gets a research plan
    PROMISING_UNCONFIRMED    positive in both halves of the check rows, distinct, and worth a registered test

Nothing is deleted: every rule's class, reason, figures and plan go to an append-only ledger.

No rule's check-row t is taken at its face value: the rules that reach the last step were the best of many. Two
corrections are made, and both are estimates, not tests:

- **the chance it is real.** Under no effect a check-row t is about normal: centred on the run's own median when that
  is below zero (costs) and on zero otherwise, with the spread of the run's rules below that median (never less than
  1). A rule's chance of being real is one less its
  false-discovery rate against that noise, counting every DISTINCT behaviour the run evaluated: twenty variants of
  one behaviour are one look, not twenty. A lone strong rule among a hundred noise rules keeps a real chance; a rule
  no stronger than the best of a hundred noise rules does not;
- **its strength if real.** Three quarters of its check-row t: the winner's-curse haircut.

A rule is PROMISING when it is positive in both halves of the check rows and its chance of passing its validation, by
those two numbers, is at least 1 in 4. Validation stays what it was: a preregistered test on unread rows at the
registry's bar. Discovery only decides what that test is asked.
"""

from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np

from .methods import Emit
from .panel import Panel
from .signals import _b, causal, describe, pnl, spec_id, stats, targets

CLASSES = ("SCIENTIFICALLY_INVALID", "REPEATS_CLOSED_FAMILY", "INSUFFICIENT_DATA", "NEGATIVE_EXPECTANCY", "OVERFIT",
           "DUPLICATE", "INSUFFICIENT_POWER", "PROMISING_UNCONFIRMED")
SAME = 0.7  # two rules whose check-row returns correlate this much are one behaviour
BETA = 0.9  # a rule this close to always holding its instrument has no timing
MIN_IN_POSITION, MIN_ENTRIES = 30, 8
P_MIN = 0.25  # the least estimated chance of passing its validation to be worth a registered test
HAIRCUT = 0.75  # a selected rule's strength, if real, as a share of its check-row t (the winner's curse)
MAX_BATCH, PER_FAMILY, PER_TARGET = 12, 3, 4


def _phi(x: float) -> float:
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def _corr(a: np.ndarray, b: np.ndarray) -> float:
    if a.std() == 0 or b.std() == 0:
        return 0.0
    return float(np.corrcoef(a, b)[0, 1])


def behaviour(spec: dict, p: Panel, rows: np.ndarray) -> np.ndarray:
    """What the rule did on the given rows: its net return, 0 where it held nothing or could not decide."""
    return _b(pnl(spec, p)["net"][rows])


def evaluate(e: Emit, p: Panel, fit: np.ndarray, check: np.ndarray) -> dict:
    """One rule's record: its figures on the fit rows (which shaped it) and on the check rows (which did not)."""
    r = pnl(e.spec, p)
    f, c = stats(r["net"], fit, p.ppy, r["pos"]), stats(r["net"], check, p.ppy, r["pos"])
    rows = np.nonzero(check)[0]
    half = rows[len(rows) // 2] if len(rows) else 0
    idx = np.arange(p.T)
    h1, h2 = stats(r["net"], check & (idx < half), p.ppy), stats(r["net"], check & (idx >= half), p.ppy)
    g = stats(r["gross"], check, p.ppy)
    late = stats(pnl(e.spec, p, delay=1)["net"], check, p.ppy)
    x2 = stats(pnl(e.spec, p, k=2.0)["net"], check, p.ppy)

    def rnd(v, n=6):
        return None if v is None else round(float(v), n)
    return {"id": spec_id(e.spec), "family": e.family, "method": e.method, "why": e.why, "detail": e.detail,
            "spec": e.spec, "rule": describe(e.spec), "targets": list(targets(e.spec)),
            "parents": [spec_id(x) for x in e.spec["parts"]] if e.spec["kind"] in ("combo", "book") else [],
            "causal": causal(e.spec, p, points=3),
            "fit": {"t": rnd(f["t"], 3), "mean": rnd(f["mean"], 8), "sharpe": rnd(f["sharpe"], 3)},
            "check": {"n": c["n"], "t": rnd(c["t"], 3), "mean": rnd(c["mean"], 8), "sharpe": rnd(c["sharpe"], 3),
                      "gross_mean": rnd(g["mean"], 8), "exposure": rnd(c.get("exposure"), 4),
                      "in_position": c.get("in_position"), "entries": c.get("entries"),
                      "half_means": [rnd(h1["mean"], 8), rnd(h2["mean"], 8)],
                      "one_row_late_mean": rnd(late["mean"], 8), "costs_x2_mean": rnd(x2["mean"], 8)}}


def noise(z: list[float]) -> tuple[float, float]:
    """The centre and the spread of a check-row t under no effect, from the run's own rules.

    - The centre is the run's median when that is below zero (noise rules pay costs), and zero otherwise.
    - The spread is that of the rules BELOW the median, never less than 1: real effects arrive as clusters of similar
      rules above the median, and must not make themselves look ordinary by widening the noise."""
    if len(z) < 8:
        return 0.0, 1.0
    v = np.asarray(z, dtype=float)
    med = float(np.median(v))
    low = v[v < med] - med
    return min(0.0, med), max(1.0, float(np.sqrt(np.mean(low * low))) if len(low) else 1.0)


def distinct(ids: list[str], beh: dict) -> int:
    """How many different behaviours a set of rules holds: a rule that correlates SAME or more with an earlier one, in
    either direction (a rule and its mirror are one look), is not counted again."""
    kept: list[np.ndarray] = []
    for i in ids:
        if not any(abs(_corr(beh[i], k)) >= SAME for k in kept):
            kept.append(beh[i])
    return len(kept)


def chances(z: list[float], mu0: float, sd0: float, tested: int) -> list[float]:
    """For rules in descending order of t: each one's chance of being real, one less its false-discovery rate
    (Benjamini-Hochberg, one-sided, over `tested` rules)."""
    p = [1.0 - _phi((v - mu0) / sd0) for v in z]
    q, best = [0.0] * len(z), 1.0
    for i in range(len(z) - 1, -1, -1):
        best = min(best, tested * p[i] / (i + 1))
        q[i] = best
    return [round(1.0 - x, 4) for x in q]


def power(z: float, p_real: float, n_check: int, n_val: float, bar: float) -> dict:
    """If the rule is real at three quarters of its check-row strength, the t its validation would expect; and its
    chance of passing: the chance it is real times the chance that t reaches `bar`."""
    t = HAIRCUT * z * math.sqrt(n_val / max(n_check, 1))
    return {"p_real": round(p_real, 4), "strength_if_real": round(HAIRCUT * z, 3), "t_expected": round(t, 3),
            "bar": round(bar, 4), "p_pass": round(p_real * (1.0 - _phi(bar - t)), 4)}


def plan(pw: dict, z: float, n_check: int, n_val: float, ppy: float, book: dict | None, hint: str) -> dict:
    """What it would take to test a rule that is positive but not worth a registered test as it stands."""
    out = {"family_book": book, "more_data": hint}
    if pw["p_real"] < 0.5:
        # a chance of 1 in 2 needs a check-row t that the run's noise rarely gives: how many more check rows at this
        # strength, by t growing with the square root of the rows
        need = 3.0  # about the t at which one rule among a hundred is as likely real as noise
        out["check_rows_needed"] = int(n_check * (need / max(z, 0.1)) ** 2)
        out["more_discovery_years"] = round(max(0.0, out["check_rows_needed"] - n_check) / ppy, 1)
    t = pw["t_expected"]
    out["independent_instruments_needed"] = int(math.ceil(((pw["bar"] + 0.0) / max(t, 0.05)) ** 2))
    out["forward_years_needed"] = round(max(0.0, n_val * ((pw["bar"] / max(t, 0.05)) ** 2 - 1.0)) / ppy, 1)
    ways = []
    if book and book["class"] == "PROMISING_UNCONFIRMED":
        ways.append(f"its family's book across instruments ({book['id']}) is promising and carries it to validation")
    elif book:
        ways.append(f"its family's book across instruments ({book['id']}) is {book['class']} too")
    if "more_discovery_years" in out:
        ways.append(f"it cannot be told from noise yet: about {out['more_discovery_years']} more years of discovery "
                    "rows at this strength would tell")
    if out["forward_years_needed"] <= 3.0:
        ways.append(f"if real, about {out['forward_years_needed']} more years after the validation window reach half power")
    else:
        ways.append(f"if real, the same mechanism on about {out['independent_instruments_needed']} independent "
                    "instruments reaches half power in the window")
    out["feasible"] = bool((book or {}).get("class") == "PROMISING_UNCONFIRMED" or out["forward_years_needed"] <= 3.0
                           or out.get("more_discovery_years", 99) <= 5.0 or (hint and out["independent_instruments_needed"] <= 12))
    out["ways"] = ways
    return out


def triage(emitted: list[Emit], p: Panel, fit: np.ndarray, check: np.ndarray, n_val: float, bar: float,
           closed: list[tuple[str, dict]] | None = None, hint: str = "", known: dict | None = None) -> dict:
    """Class every emitted rule. Returns the records (each with its class, reason and plan), the run's noise and the
    batch proposed for validation. `known`: rule id -> (run, class) for rules an earlier scan of this market already
    classed: such a rule is recorded as seen and is not looked at again."""
    known = known or {}
    seen = [{"id": spec_id(e.spec), "family": e.family, "method": e.method, "why": e.why, "detail": e.detail,
             "spec": e.spec, "rule": describe(e.spec), "targets": list(targets(e.spec)), "parents": [],
             "class": "DUPLICATE", "duplicate_of": spec_id(e.spec), "in_batch": False,
             "reason": f"the same rule was classed {known[spec_id(e.spec)][1]} by {known[spec_id(e.spec)][0]}: it is not "
                       "looked at twice"} for e in emitted if spec_id(e.spec) in known]
    emitted = [e for e in emitted if spec_id(e.spec) not in known]
    recs = [evaluate(e, p, fit, check) for e in emitted]
    rows = np.nonzero(check)[0]
    beh = {r["id"]: behaviour(r["spec"], p, rows) for r in recs}
    always = {a: behaviour({"kind": "const", "target": a, "side": 1}, p, rows) for a in p.assets}
    tomb = [(name, behaviour(s, p, rows)) for name, s in (closed or []) if all(t in p.assets for t in targets(s))]

    def beta(r):
        own = np.mean([always[t] for t in r["targets"]], axis=0)
        return abs(_corr(beh[r["id"]], own))

    for r in recs:  # the classes that need no comparison with other rules
        c, cls, why = r["check"], None, None
        rep = next(((n, _corr(beh[r["id"]], b)) for n, b in tomb if _corr(beh[r["id"]], b) >= SAME), None)
        if not r["causal"]:
            cls, why = "SCIENTIFICALLY_INVALID", "its position at a row changes when later rows are removed: it reads the future"
        elif (c["exposure"] or 0) >= 0.8 and beta(r) >= BETA:
            cls, why = "SCIENTIFICALLY_INVALID", (f"it holds its instrument {c['exposure']:.0%} of the time and its return "
                                                  f"is the instrument's own (correlation {beta(r):.2f}): no timing")
        elif rep is not None:
            cls, why = "REPEATS_CLOSED_FAMILY", f"it behaves as {rep[0]} (correlation {rep[1]:.2f}), judged and closed"
            r["repeats"] = rep[0]
        elif c["t"] is None or (c["in_position"] or 0) < MIN_IN_POSITION or (c["entries"] or 0) < MIN_ENTRIES:
            cls, why = "INSUFFICIENT_DATA", (f"{c['in_position'] or 0} rows in position and {c['entries'] or 0} entries on "
                                             f"the check rows: too few to estimate (at least {MIN_IN_POSITION} and "
                                             f"{MIN_ENTRIES})")
        elif c["mean"] <= 0:
            if (c["gross_mean"] or 0) > 0:
                cls, why = "NEGATIVE_EXPECTANCY", "positive before costs on the check rows, negative after them"
            elif (r["fit"]["t"] or 0) >= 2.0:
                cls, why = "OVERFIT", (f"t {r['fit']['t']} on the rows that shaped it, t {c['t']} on the rows that did "
                                       "not: negative before costs too")
            else:
                cls, why = "NEGATIVE_EXPECTANCY", f"it lost on the check rows before costs too (t {c['t']})"
        elif (r["fit"]["t"] or 0) >= 3.0 and c["t"] < 0.5:
            cls, why = "OVERFIT", f"t {r['fit']['t']} on the rows that shaped it, all but gone on the check rows (t {c['t']})"
        r["class"], r["reason"] = cls, why
    zs = [r["check"]["t"] for r in recs if r["check"]["t"] is not None and r["class"] not in
          ("SCIENTIFICALLY_INVALID", "REPEATS_CLOSED_FAMILY", "INSUFFICIENT_DATA")]
    mu0, sd0 = noise(zs)
    looks = distinct([r["id"] for r in recs if r["check"]["t"] is not None and r["class"] not in
                      ("SCIENTIFICALLY_INVALID", "REPEATS_CLOSED_FAMILY", "INSUFFICIENT_DATA")], beh)
    kept: list[dict] = []
    for r in sorted((r for r in recs if r["class"] is None), key=lambda r: -r["check"]["t"]):
        dup = next((k for k in kept if _corr(beh[r["id"]], beh[k["id"]]) >= SAME), None)
        if dup is not None:
            r["class"], r["duplicate_of"] = "DUPLICATE", dup["id"]
            r["reason"] = f"it behaves as {dup['id']} ({dup['rule'][:80]}), which is stronger on the check rows"
        else:
            kept.append(r)
    for r, p_real in zip(kept, chances([r["check"]["t"] for r in kept], mu0, sd0, looks)):
        r["power"] = pw = power(r["check"]["t"], p_real, r["check"]["n"], n_val, bar)
        both = all((h or 0) > 0 for h in r["check"]["half_means"])
        said = (f"check-row t {r['check']['t']}: about {pw['p_real']:.0%} to be real against this run's noise; if real, "
                f"an expected t of {pw['t_expected']} against {pw['bar']} on the validation rows; about "
                f"{pw['p_pass']:.0%} to pass")
        if pw["p_pass"] >= P_MIN and both:
            r["class"], r["reason"] = "PROMISING_UNCONFIRMED", "positive in both halves of the check rows; " + said
        else:
            r["class"] = "INSUFFICIENT_POWER"
            r["reason"] = "positive on the check rows; " + said + ("" if both else "; and one half of the check rows lost")
    books = {r["detail"].get("family"): r for r in recs if r["family"] == "pooled book"}
    for r in kept:
        if r["class"] == "INSUFFICIENT_POWER":
            b_ = books.get(r["family"])
            r["plan"] = plan(r["power"], r["check"]["t"], r["check"]["n"], n_val, p.ppy,
                             {"id": b_["id"], "class": b_["class"]} if b_ is not None and b_["id"] != r["id"] else None,
                             hint)
    promising = sorted((r for r in recs if r["class"] == "PROMISING_UNCONFIRMED"), key=lambda r: -r["power"]["p_pass"])
    batch, fam, tgt = [], {}, {}
    for r in promising:
        t_ = ",".join(r["targets"])
        if len(batch) < MAX_BATCH and fam.get(r["family"], 0) < PER_FAMILY and tgt.get(t_, 0) < PER_TARGET:
            batch.append(r["id"])
            fam[r["family"]], tgt[t_] = fam.get(r["family"], 0) + 1, tgt.get(t_, 0) + 1
    for r in recs:
        r["in_batch"] = r["id"] in batch
    recs += seen
    return {"records": recs, "noise": {"centre_t": round(mu0, 3), "spread_t": round(sd0, 3), "rules": len(zs),
                                       "distinct_behaviours": looks}, "batch": batch}


def summary(recs: list[dict]) -> dict:
    by_class, by_family, grid = {}, {}, {}
    for r in recs:
        by_class[r["class"]] = by_class.get(r["class"], 0) + 1
        by_family[r["family"]] = by_family.get(r["family"], 0) + 1
        grid.setdefault(r["family"], {})[r["class"]] = grid.setdefault(r["family"], {}).get(r["class"], 0) + 1
    distinct = sum(r["class"] in ("INSUFFICIENT_POWER", "PROMISING_UNCONFIRMED") for r in recs)
    return {"rules": len(recs), "by_class": dict(sorted(by_class.items())), "by_family": dict(sorted(by_family.items())),
            "family_by_class": {k: dict(sorted(v.items())) for k, v in sorted(grid.items())},
            "distinct_positive_behaviours": distinct,
            "families_with_a_positive_rule": sorted({r["family"] for r in recs if r["class"] in
                                                     ("INSUFFICIENT_POWER", "PROMISING_UNCONFIRMED")})}


def append(ledger: Path, run: str, recs: list[dict], at: str, version: str) -> int:
    """Every rule of a run, for ever. A run is written once: a second write of the same run is refused."""
    ledger.parent.mkdir(parents=True, exist_ok=True)
    if ledger.exists() and any(json.loads(x).get("run") == run for x in ledger.read_text().splitlines() if x.strip()):
        raise SystemExit(f"run {run} is in {ledger} already: a run is recorded once")
    with open(ledger, "a") as f:
        f.write("".join(json.dumps({"run": run, "at": at, "version": version, **r}, sort_keys=True) + "\n" for r in recs))
    return len(recs)


__all__ = ["CLASSES", "HAIRCUT", "MAX_BATCH", "P_MIN", "SAME", "append", "behaviour", "chances", "distinct", "evaluate", "noise",
           "plan", "power", "summary", "triage"]
