"""Structured forward lessons: what keeps going wrong, named, counted and confirmed before it acts.

Each resolved forward outcome (learning/forward.py) is TAGGED deterministically from its own path:

    WRONG_DIRECTION         a loss that never got +0.25R and never went the right way afterwards
    BAD_ENTRY               a loss that went against first (-0.5R or worse) and later reached +1R:
                            the direction was right, the timing was not
    STOP_TOO_TIGHT          stopped out, then the target was reached inside the holding window
    TARGET_TOO_CLOSE        the target was hit and price ran at least twice as far afterwards
    VOLATILITY_MISMATCH     stopped out with a stop inside half an H1 ATR: inside the noise
    COST_EROSION            gross R positive, net R not; or costs at least 0.3R of the trade
    FALSE_BREAKOUT          WRONG_DIRECTION on a proposal whose stated method or family is a breakout
    LIQUIDITY_SWEEP_FAILURE WRONG_DIRECTION on a proposal whose method or family is a sweep/liquidity play

and AGGREGATE codes come from a whole scope, never from one trade:

    BAD_REGIME              a regime in which a signal class loses significantly (t <= -2)
    AI_OVERCONFIDENCE       a model's stated probability of reaching the target exceeds what happened
                            by at least 0.10 (z >= 2)
    AI_UNDERCONFIDENCE      the reverse
    SYMBOL_FAILURE          an instrument on which a signal class loses significantly
    MODEL_FAILURE           a model whose proposals lose significantly

LIFECYCLE, all from the immutable ledger, versioned in `forward_lessons` (append-only):

    CANDIDATE  from LEARNING-partition outcomes only: in a scope with >= 30 resolved outcomes and a
               negative mean net R, the tag explains >= 25% of them (>= 10 occurrences); or the
               aggregate test above holds.
    ACTIVE     confirmed on EVALUATION-partition outcomes that resolved AFTER the candidate was
               created: >= 30 of them in the scope, and the same test holds again.
    REJECTED   that confirmation was attempted on >= 30 such outcomes and failed.

What an ACTIVE lesson may do: it is shown to the model traders as information and on the dashboard.
It never changes code, a parameter, a risk limit or a size, and it never creates a trade. One
outcome can never create, confirm or reject a lesson: every threshold is a sample size.
"""

from __future__ import annotations

import hashlib
import json
import math
import statistics as st
from collections import defaultdict

TAXONOMY_VERSION = "taxonomy-1.0.0"
PER_TRADE = ("WRONG_DIRECTION", "BAD_ENTRY", "STOP_TOO_TIGHT", "TARGET_TOO_CLOSE", "VOLATILITY_MISMATCH",
             "COST_EROSION", "FALSE_BREAKOUT", "LIQUIDITY_SWEEP_FAILURE")
AGGREGATE = ("BAD_REGIME", "AI_OVERCONFIDENCE", "AI_UNDERCONFIDENCE", "SYMBOL_FAILURE", "MODEL_FAILURE")
CODES = PER_TRADE + AGGREGATE
MIN_SCOPE_N = 30
MIN_TAGGED = 10
MIN_SHARE = 0.25


def _method(r: dict) -> str:
    return f"{r.get('method') or ''} {r.get('family') or ''}".lower()


def tags(r: dict) -> list[str]:
    """Per-trade tags of one ledger row with a resolved outcome."""
    o = r.get("outcome") or {}
    if o.get("net_r") is None:
        return []
    out = []
    net, gross, cost = o["net_r"], o["gross_r"], o["cost_r"]
    mfe, mae = o.get("mfe_r") or 0.0, o.get("mae_r") or 0.0
    post = o.get("post_exit_best_r")
    loss = net <= 0
    if loss and mfe < 0.25 and (post is None or post < 0.5) and o["reason"] in ("STOP", "TIME"):
        out.append("WRONG_DIRECTION")
        m = _method(r)
        if "breakout" in m:
            out.append("FALSE_BREAKOUT")
        if "sweep" in m or "liquidity" in m:
            out.append("LIQUIDITY_SWEEP_FAILURE")
    if loss and mae <= -0.5 and not o.get("mfe_first") and (mfe >= 1.0 or (post or 0) >= 1.0):
        out.append("BAD_ENTRY")
    if o["reason"] == "STOP" and o.get("target_after_exit"):
        out.append("STOP_TOO_TIGHT")
    rr = r.get("reward_risk")
    if o["reason"] == "TARGET" and rr and post is not None and post >= 2 * rr:
        out.append("TARGET_TOO_CLOSE")
    if o["reason"] == "STOP" and r.get("stop_atr") is not None and r["stop_atr"] < 0.5:
        out.append("VOLATILITY_MISMATCH")
    if (gross > 0 and net <= 0) or cost >= 0.3:
        out.append("COST_EROSION")
    return out


def _resolved(rows, part: str, after: int | None = None, as_of: int | None = None):
    out = []
    for r in rows:
        o = r.get("outcome")
        if r.get("partition") != part or not o or o.get("net_r") is None:
            continue
        if after is not None and o["resolved_at"] <= after:
            continue
        if as_of is not None and o["resolved_at"] > as_of:
            continue
        out.append(r)
    return out


def _t(xs: list[float]) -> float | None:
    if len(xs) < 2:
        return None
    sd = st.stdev(xs)
    return (st.mean(xs) / (sd / math.sqrt(len(xs)))) if sd > 0 else None


def _scopes(r: dict):
    sc = r.get("signal_class") or "?"
    yield ("signal_class", sc)
    yield ("signal_class+regime", f"{sc}|{r.get('regime') or '?'}")
    yield ("signal_class+symbol", f"{sc}|{r['symbol']}")
    if r.get("model"):
        yield ("model", r["model"])


def _test(code: str, scope_kind: str, rows: list[dict]) -> dict | None:
    """The lesson's test on `rows` (all in one scope). Returns its evidence, or None if not applicable."""
    n = len(rows)
    if n < MIN_SCOPE_N:
        return {"n": n, "holds": None}
    net = [r["outcome"]["net_r"] for r in rows]
    mean, t = st.mean(net), _t(net)
    ev = {"n": n, "mean_net_r": round(mean, 4), "t": None if t is None else round(t, 2)}
    if code in PER_TRADE:
        hit = [r for r in rows if code in tags(r)]
        share = len(hit) / n
        ev.update({"tagged": len(hit), "share": round(share, 3),
                   "impact_r": round(st.mean(r["outcome"]["net_r"] for r in hit) - mean, 4) if hit else None,
                   "evidence": [r["decision_id"] for r in hit[-20:]]})
        ev["holds"] = mean < 0 and len(hit) >= MIN_TAGGED and share >= MIN_SHARE
        return ev
    if code == "BAD_REGIME" and scope_kind == "signal_class+regime" or \
            code == "SYMBOL_FAILURE" and scope_kind == "signal_class+symbol" or \
            code == "MODEL_FAILURE" and scope_kind == "model":
        ev["holds"] = t is not None and t <= -2.0
        return ev
    if code in ("AI_OVERCONFIDENCE", "AI_UNDERCONFIDENCE") and scope_kind == "model":
        pairs = [(r["confidence"], 1.0 if r["outcome"]["reason"] == "TARGET" else 0.0) for r in rows
                 if isinstance(r.get("confidence"), (int, float))]
        if len(pairs) < MIN_SCOPE_N:
            return {"n": len(pairs), "holds": None}
        stated, hit = st.mean(p for p, _ in pairs), st.mean(w for _, w in pairs)
        se = math.sqrt(max(hit * (1 - hit), 1e-9) / len(pairs))
        gap = stated - hit
        ev.update({"stated": round(stated, 3), "realised": round(hit, 3), "gap": round(gap, 3), "z": round(gap / se, 2)})
        ev["holds"] = (gap >= 0.10 and gap / se >= 2) if code == "AI_OVERCONFIDENCE" else (gap <= -0.10 and gap / se <= -2)
        return ev
    return None


def lesson_id(code: str, scope_kind: str, scope: str) -> str:
    return f"{code}:{hashlib.sha256(f'{code}|{scope_kind}|{scope}'.encode()).hexdigest()[:10]}"


STATEMENTS = {
    "WRONG_DIRECTION": "losses here are mostly wrong-direction calls: the market never went the proposed way",
    "BAD_ENTRY": "losses here often had the right direction but entered too early (went against first)",
    "STOP_TOO_TIGHT": "stops here are often hit before the target is reached anyway",
    "TARGET_TOO_CLOSE": "targets here are often hit with at least as far again left on the table",
    "VOLATILITY_MISMATCH": "stops here are often inside half an H1 ATR: inside the noise",
    "COST_EROSION": "costs eat the edge here: positive gross, non-positive net, or costs >= 0.3R",
    "FALSE_BREAKOUT": "breakout proposals here often fail with no follow-through",
    "LIQUIDITY_SWEEP_FAILURE": "sweep/liquidity proposals here often fail",
    "BAD_REGIME": "this signal class loses significantly in this regime",
    "AI_OVERCONFIDENCE": "this model's stated probability of reaching the target is too high",
    "AI_UNDERCONFIDENCE": "this model's stated probability of reaching the target is too low",
    "SYMBOL_FAILURE": "this signal class loses significantly on this instrument",
    "MODEL_FAILURE": "this model's proposals lose significantly",
}


def evaluate(rows: list[dict], previous: dict[str, dict], t: int) -> list[dict]:
    """New lesson versions at time `t` given the ledger `rows` and each lesson's latest version.

    Only state CHANGES are returned (to be appended). Uses outcomes resolved at or before `t`."""
    learn = _resolved(rows, "LEARNING", as_of=t)
    scoped: dict = defaultdict(list)
    for r in learn:
        for k, v in _scopes(r):
            scoped[(k, v)].append(r)
    changes = []
    for (kind, scope), rs in scoped.items():
        for code in CODES:
            lid = lesson_id(code, kind, scope)
            prev = previous.get(lid)
            status = (prev or {}).get("status")
            if status in ("ACTIVE", "REJECTED"):
                continue  # decided; a later version would need new evidence through a new candidate
            if status is None:
                ev = _test(code, kind, rs)
                if ev is None or not ev.get("holds"):
                    continue
                changes.append({"lesson_id": lid, "version": 1, "status": "CANDIDATE", "code": code,
                                "scope_kind": kind, "scope": scope, "statement": STATEMENTS[code],
                                "created": t, "learning_evidence": ev, "version_tag": TAXONOMY_VERSION})
                continue
            # CANDIDATE: confirm on EVALUATION outcomes resolved after its creation
            later = [r for r in _resolved(rows, "EVALUATION", after=prev["created"], as_of=t)
                     if (kind, scope) in set(_scopes(r))]
            ev = _test(code, kind, later)
            if ev is None or ev.get("holds") is None:
                continue
            changes.append({**{k: prev[k] for k in ("lesson_id", "code", "scope_kind", "scope", "statement",
                                                     "created", "learning_evidence")},
                            "version": prev["version"] + 1, "status": "ACTIVE" if ev["holds"] else "REJECTED",
                            "decided": t, "evaluation_evidence": ev, "version_tag": TAXONOMY_VERSION})
    return changes


class LessonBook:
    """The forward lessons as stored (append-only), with the latest version of each."""

    def __init__(self, db) -> None:
        self.db = db

    def latest(self) -> dict[str, dict]:
        out = {}
        for r in self.db.query("SELECT lesson_id, payload FROM forward_lessons ORDER BY seq"):
            out[r["lesson_id"]] = json.loads(r["payload"])
        return out

    def update(self, rows: list[dict], t: int) -> list[dict]:
        changes = evaluate(rows, self.latest(), t)
        for c in changes:
            with self.db.tx() as conn:
                if conn.execute("SELECT 1 FROM forward_lessons WHERE lesson_id=? AND version=?",
                                (c["lesson_id"], c["version"])).fetchone():
                    continue
                self.db.append("forward_lessons", {"lesson_id": c["lesson_id"], "version": c["version"],
                                                   "status": c["status"], "payload": c}, conn=conn)
        return changes

    def active(self) -> list[dict]:
        return [v for v in self.latest().values() if v["status"] == "ACTIVE"]
