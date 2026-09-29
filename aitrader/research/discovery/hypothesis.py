"""Hypotheses as explicit, testable objects with a permanent, append-only lifecycle.

    DRAFT -> PREREGISTERED -> RUNNING -> COMPLETED -> VALIDATED | REJECTED
    COMPLETED -> SHELVED  (passed its stage but was not selected for judgment: the budget is K)
    DRAFT -> SHELVED   (not pursued: out of budget, or a better-placed sibling was chosen)
    DRAFT -> REJECTED  (refused before any test: e.g. it repeats a rejected idea)

A hypothesis states what would make it false before any number is seen (`falsification`), how
many configurations it may consume (`budget`), and exactly how a trade is entered, exited and
risked. Risk is always "1R = the exit's initial stop distance": the size of a position is the
Risk Engine's decision alone, so no hypothesis carries a size, a leverage or a risk amount.

The ledger (research/discovery/ledger.jsonl) is never edited. A rejected idea stays searchable,
and the SUBSTANCE of a rejected hypothesis — its condition, side, exit, instruments and
timeframe, whatever the wording — cannot be drafted again as new, except as a prospective test
on data that did not exist when it was rejected.

Sources: the screen (observations), a language model (closed vocabulary, prospective only: every
bar of history predates its training cutoff), live lessons (translated approximately, stated as
such), and hypotheses derived from how a previous one failed (also prospective only).
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path

from .exits import EXIT_BY_KEY
from .study import LABELS, Condition

HYPOTHESIS_VERSION = "hypothesis-1.0.0"
STATES = ("DRAFT", "PREREGISTERED", "RUNNING", "COMPLETED", "VALIDATED", "REJECTED", "SHELVED")
TRANSITIONS = {
    "DRAFT": ("PREREGISTERED", "SHELVED", "REJECTED"),
    "PREREGISTERED": ("RUNNING",),
    "RUNNING": ("RUNNING", "COMPLETED"),  # RUNNING again = resumed after an interruption (same code, same data)
    "COMPLETED": ("VALIDATED", "REJECTED", "SHELVED"),
    "VALIDATED": (),
    "REJECTED": (),
    "SHELVED": (),
}
REQUIRES = {"PREREGISTERED": ("trial", "preregistration_sha256"), "RUNNING": ("trial",),
            "COMPLETED": ("summary",), "VALIDATED": ("checks",), "REJECTED": ("reason",), "SHELVED": ("reason",)}
ORIGINS = ("screen", "model", "llm", "lesson", "derived", "human")
KINDS = ("opportunity", "veto")  # veto: the claim is that trading this LOSES (it can only subtract)
RISK = "1R = the exit's initial stop distance; the position size is the Risk Engine's alone; one position per " \
       "instrument; no pyramiding, no averaging down"
ENTRY = "market order at the next bar's open after an H1 close where the condition holds; a signal while the " \
        "hypothesis already holds a position on that instrument is not a trade"
FORBIDDEN_FIELDS = ("size", "lots", "units", "leverage", "risk_amount", "risk_pct", "position_size")


class LedgerError(ValueError):
    pass


def condition_key(condition: str) -> str:
    """The canonical form of a condition: a bin conjunction, or a frozen model score threshold."""
    if condition.startswith("model:"):
        parts = condition.split(":")
        if len(parts) != 3 or not parts[1] or not parts[2].startswith("q"):
            raise LedgerError(f"a model condition is model:<artifact id>:q<quantile>, not {condition!r}")
        float(parts[2][1:])
        return condition
    return Condition.parse(condition).key


@dataclass(frozen=True)
class Hypothesis:
    id: str
    statement: str
    rationale: str
    mechanism: str
    features: tuple[str, ...]  # catalog ids (name@version)
    condition: str  # a study.Condition key ("er120=high&r24=low") or a model score ("model:<id>:q0.90")
    side: str  # BUY | SELL
    instruments: tuple[str, ...]
    timeframe: str
    exit: str  # an exit key, or "MENU" when the exit is itself being selected (budget counts it)
    expected_effect: str
    falsification: tuple[str, ...]
    budget: int  # configurations this hypothesis may consume
    origin: str
    program: str
    kind: str = "opportunity"
    entry: str = ENTRY
    risk: str = RISK
    parent: str | None = None
    prospective_only: bool = False
    evidence: dict = field(default_factory=dict)

    def validate(self) -> None:
        for f in ("id", "statement", "rationale", "mechanism", "condition", "timeframe", "expected_effect", "entry",
                  "risk", "program"):
            if not str(getattr(self, f) or "").strip():
                raise LedgerError(f"hypothesis needs {f!r}")
        if not self.id.replace("-", "").replace("_", "").replace(".", "").isalnum():
            raise LedgerError(f"hypothesis id {self.id!r} must be a plain slug")
        condition_key(self.condition)
        if self.side not in ("BUY", "SELL"):
            raise LedgerError("side must be BUY or SELL")
        if self.exit != "MENU" and self.exit not in EXIT_BY_KEY:
            raise LedgerError(f"unknown exit {self.exit!r}")
        if not self.instruments or not self.features or not self.falsification:
            raise LedgerError("instruments, features and falsification criteria must be declared")
        if self.budget < 1:
            raise LedgerError("a hypothesis needs a budget of at least one configuration")
        if self.origin not in ORIGINS or self.kind not in KINDS:
            raise LedgerError(f"unknown origin/kind {self.origin!r}/{self.kind!r}")
        if self.origin in ("llm", "derived") and not self.prospective_only:
            raise LedgerError(f"a {self.origin} hypothesis was shaped by data it could have seen: prospective only")
        blob = json.dumps(self.to_json()).lower()
        for word in FORBIDDEN_FIELDS:
            if f'"{word}"' in blob:
                raise LedgerError(f"a hypothesis never carries {word!r}: sizing is the Risk Engine's")

    def substance(self) -> str:
        """What is actually tested — independent of wording, id or origin."""
        body = [condition_key(self.condition), self.side, self.exit, sorted(self.instruments), self.timeframe,
                self.kind]
        return hashlib.sha256(json.dumps(body).encode()).hexdigest()[:16]

    def to_json(self) -> dict:
        d = asdict(self)
        d["features"], d["instruments"], d["falsification"] = (list(self.features), list(self.instruments),
                                                               list(self.falsification))
        return d

    @classmethod
    def from_json(cls, raw: dict) -> "Hypothesis":
        d = dict(raw)
        for k in ("features", "instruments", "falsification"):
            d[k] = tuple(d[k])
        return cls(**d)


class Ledger:
    def __init__(self, path: Path | str) -> None:
        self.path = Path(path)
        self._h: dict[str, Hypothesis] = {}
        self._events: dict[str, list[dict]] = {}
        if self.path.exists():
            for line in self.path.read_text(encoding="utf-8").splitlines():
                if line.strip():
                    self._apply(json.loads(line), replay=True)

    # ── writes ──────────────────────────────────────────────────────────

    def draft(self, h: Hypothesis, now: datetime) -> Hypothesis:
        h.validate()
        if h.id in self._h:
            raise LedgerError(f"hypothesis {h.id} already exists; ids are never reused")
        sub = h.substance()
        for other in self._h.values():
            if other.substance() != sub:
                continue
            st = self.state(other.id)
            if st in ("REJECTED", "VALIDATED") and not (h.prospective_only and h.parent == other.id):
                raise LedgerError(f"{h.id} repeats {other.id} ({st}) under a new name; only a prospective "
                                  "retest that names it as parent may test the same substance again")
            if st not in ("REJECTED", "VALIDATED", "SHELVED") and not (h.prospective_only and h.parent == other.id):
                raise LedgerError(f"{h.id} duplicates {other.id}, which is still {st}")
        self._write({"event": "DRAFT", "id": h.id, "hypothesis": h.to_json(), "substance": sub,
                     "version": HYPOTHESIS_VERSION, "at": now.isoformat()})
        return h

    def transition(self, hid: str, state: str, now: datetime, **data) -> None:
        cur = self.state(hid)
        if state not in TRANSITIONS.get(cur, ()):
            raise LedgerError(f"{hid}: {cur} -> {state} is not a permitted transition")
        missing = [k for k in REQUIRES.get(state, ()) if k not in data]
        if missing:
            raise LedgerError(f"{hid}: {state} needs {missing}")
        last = self._events[hid][-1]["at"]
        if now.isoformat() < last:
            raise LedgerError(f"{hid}: an event cannot be dated before the previous one")
        self._write({"event": "STATE", "id": hid, "state": state, "data": data, "at": now.isoformat()})

    # ── reads ───────────────────────────────────────────────────────────

    def get(self, hid: str) -> Hypothesis:
        try:
            return self._h[hid]
        except KeyError:
            raise LedgerError(f"unknown hypothesis {hid!r}") from None

    def state(self, hid: str) -> str:
        self.get(hid)
        states = [e["state"] for e in self._events[hid] if e["event"] == "STATE"]
        return states[-1] if states else "DRAFT"

    def history(self, hid: str) -> list[dict]:
        self.get(hid)
        return [dict(e) for e in self._events[hid]]

    def hypotheses(self, state: str | None = None, program: str | None = None) -> list[Hypothesis]:
        return [h for h in self._h.values() if (state is None or self.state(h.id) == state)
                and (program is None or h.program == program)]

    def search(self, text: str = "", state: str | None = None) -> list[dict]:
        t = text.lower()
        out = []
        for h in self._h.values():
            blob = " ".join([h.id, h.statement, h.rationale, h.mechanism, h.condition, h.side]).lower()
            if t in blob and (state is None or self.state(h.id) == state):
                out.append({"id": h.id, "state": self.state(h.id), "statement": h.statement,
                            "condition": h.condition, "side": h.side, "program": h.program})
        return out

    def counts(self) -> dict:
        out: dict[str, int] = {}
        for h in self._h.values():
            s = self.state(h.id)
            out[s] = out.get(s, 0) + 1
        return dict(sorted(out.items()))

    # ── internals ───────────────────────────────────────────────────────

    def _write(self, e: dict) -> None:
        self._apply(e)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(e, sort_keys=True) + "\n")

    def _apply(self, e: dict, replay: bool = False) -> None:
        if e.get("event") == "DRAFT":
            h = Hypothesis.from_json(e["hypothesis"])
            if replay and h.substance() != e.get("substance"):
                raise LedgerError(f"{h.id}: stored substance does not match the hypothesis; the ledger was edited")
            self._h[h.id] = h
            self._events[h.id] = [e]
        elif e.get("event") == "STATE":
            if e["id"] not in self._h:
                raise LedgerError(f"state change for unknown hypothesis {e['id']}")
            self._events[e["id"]].append(e)
        else:
            raise LedgerError(f"unknown ledger event {e.get('event')!r}")


# ── generators ─────────────────────────────────────────────────────────

#: plain-language description of each bin, for statements
DESCRIBE = {
    "er120": ("the last 120 bars were choppy (low trend efficiency)", "trend efficiency was middling",
              "the last 120 bars trended cleanly (high trend efficiency)"),
    "vol_ratio": ("volatility had contracted versus its 10-day norm", "volatility was normal",
                  "volatility had expanded versus its 10-day norm"),
    "ma_slope": ("the 48-bar average sat well below the 240-bar one", "the averages were flat",
                 "the 48-bar average sat well above the 240-bar one"),
    "range_pos120": ("price sat near the bottom of its 120-bar range", "price sat mid-range",
                     "price sat near the top of its 120-bar range"),
    "d1_trend": ("the daily close sat below its 20-day average", "the daily close sat near its average",
                 "the daily close sat above its 20-day average"),
    "usd_basket": ("the dollar had weakened over 24 hours", "the dollar was little changed",
                   "the dollar had strengthened over 24 hours"),
    "atr_pctile": ("volatility was low for the last 10 days", "volatility was typical",
                   "volatility was high for the last 10 days"),
    "usd_corr": ("the pair moved against the dollar basket", "the pair was loosely tied to the dollar",
                 "the pair moved with the dollar basket"),
    "session": ("the bar closed in the Asian session", "the bar closed in the London / overlap session",
                "the bar closed in the late New York / off-hours session"),
    "r1": ("the last bar fell sharply", "the last bar was quiet", "the last bar rose sharply"),
    "r6": ("price fell over 6 bars", "price was flat over 6 bars", "price rose over 6 bars"),
    "r24": ("price fell over 24 bars", "price was flat over 24 bars", "price rose over 24 bars"),
    "bar_body": ("the last bar closed near its low", "the last bar was indecisive", "the last bar closed near its high"),
    "range_pos24": ("price closed near its 24-bar low", "price closed mid-range", "price closed near its 24-bar high"),
    "smc_sweep": ("a confirmed swing high was swept and rejected", "no liquidity sweep",
                  "a confirmed swing low was swept and reclaimed"),
    "bar_range": ("the last bar was narrow", "the last bar was ordinary", "the last bar was wide (range expansion)"),
    "range_contraction": ("the 24-bar range was tight within the 120-bar range", "the ranges were typical",
                          "the 24-bar range filled most of the 120-bar range"),
    "up_persistence": ("most of the last 24 bars closed down", "up and down closes were balanced",
                       "most of the last 24 bars closed up"),
    "smc_structure": ("the last swings made lower highs and lower lows", "the swing structure was mixed",
                      "the last swings made higher highs and higher lows"),
}
#: features whose high bin means price moved UP (a BUY after it is continuation, a SELL reversal)
DIRECTIONAL = {"r1", "r6", "r24", "bar_body", "range_pos24", "range_pos120", "ma_slope", "d1_trend", "smc_sweep",
               "up_persistence", "smc_structure", "lag_r24", "dist_ma48", "h4_trend", "brk_hi120", "brk_lo120"}


def describe(cond: Condition) -> str:
    parts = []
    for f, b in cond.terms:
        d = DESCRIBE.get(f)
        parts.append(d[b] if d else f"{f} was in its {LABELS[b]} tercile")
    return " and ".join(parts)


def mechanism_for(cond: Condition, side: str) -> str:
    """A CONJECTURED mechanism, stated so it can be argued with — not evidence."""
    up = side == "BUY"
    for f, b in cond.terms:
        if f in DIRECTIONAL and b != 1:
            if (b == 2) == up:
                return (f"continuation (conjectured): after {DESCRIBE.get(f, (f,) * 3)[b]}, order flow in the same "
                        "direction persists for a while (momentum, trend-following flows, stops beyond the move)")
            return (f"reversal (conjectured): after {DESCRIBE.get(f, (f,) * 3)[b]}, the move overshoots and retraces "
                    "(liquidity provision, profit-taking, stops already triggered)")
    return ("state-dependent (conjectured): the market state described changes the distribution of the next "
            "move; no directional mechanism is claimed")


def falsification_from(rules: dict) -> tuple[str, ...]:
    return tuple(f"{k}: {v}" for k, v in rules.items())


def from_screen(hid: str, row: dict, *, program: str, instruments: tuple[str, ...], feature_ids: dict[str, str],
                rules: dict, budget: int) -> Hypothesis:
    cond = Condition.parse(row["condition"])
    side = row["side"]
    return Hypothesis(
        id=hid, statement=f"When {describe(cond)} at an H1 close, a {side} at the next open has positive net "
                          "expectancy under at least one declared exit.",
        rationale=(f"screen observation on the discovery segment only: n={row['n']}, mean {row['mean_R']:+.3f}R "
                   f"(exit E1), clustered t {row['t']}, BH q {row['q']:.4f} among {rules.get('screen_tests')} tests"),
        mechanism=mechanism_for(cond, side), features=tuple(feature_ids[f] for f in cond.features),
        condition=cond.key, side=side, instruments=tuple(instruments), timeframe="H1", exit="MENU",
        expected_effect="mean net R per trade > 0 on data the screen never saw",
        falsification=falsification_from({k: v for k, v in rules.items() if k != "screen_tests"}), budget=budget,
        origin="screen", program=program,
        evidence={"screen": {k: row[k] for k in ("n", "mean_R", "se", "t", "q", "clusters")}})


def from_lesson(hid: str, lesson: dict, *, program: str, instruments: tuple[str, ...], feature_ids: dict[str, str],
                rules: dict) -> Hypothesis | None:
    """A live lesson (negative expectancy in a context) as a VETO hypothesis on history it never saw.

    The live regime labels map only approximately onto frozen terciles, and the strategy family
    cannot be expressed in the research vocabulary at all — the rationale says so. Returns None
    for a context with no mapping rather than guessing one."""
    ctx = lesson.get("context") or []
    if len(ctx) != 4:
        return None
    family, direction, regime, vol = ctx
    reg = {"RANGING": (("er120", 0),), "TRANSITION": (("er120", 1),),
           "TRENDING_UP": (("er120", 2), ("ma_slope", 2)), "TRENDING_DOWN": (("er120", 2), ("ma_slope", 0))}.get(regime)
    vs = {"LOW_VOL": ("vol_ratio", 0), "NORMAL_VOL": ("vol_ratio", 1), "HIGH_VOL": ("vol_ratio", 2)}.get(vol)
    if reg is None or vs is None:
        return None
    terms = tuple(reg) + (vs,)
    cond = Condition(terms)
    side = "BUY" if int(direction) > 0 else "SELL"
    return Hypothesis(
        id=hid, statement=f"When {describe(cond)}, {side} positions have NEGATIVE net expectancy (a veto).",
        rationale=(f"from live lesson {lesson.get('lesson_id')} ({lesson.get('status')}): {lesson.get('statement')}. "
                   f"Translated approximately: live regime {regime}/{vol} -> {cond.key}; the family {family} cannot "
                   "be expressed in the research vocabulary, so this tests the context for ANY entry."),
        mechanism=mechanism_for(cond, side), features=tuple(feature_ids[f] for f, _ in terms), condition=cond.key,
        side=side, instruments=tuple(instruments), timeframe="H1", exit="E1",
        expected_effect="mean net R per trade < 0 on history the lesson never saw",
        falsification=falsification_from(rules), budget=1, origin="lesson", program=program, kind="veto",
        evidence={"lesson": {k: lesson.get(k) for k in ("lesson_id", "version", "status", "discovery", "validation")}})


def llm_drafts(client, *, program: str, id_prefix: str, vocabulary: dict, observations: dict, rules: dict,
               feature_ids: dict[str, str], cutoff: str, max_drafts: int = 3) -> list[Hypothesis]:
    """Ask a language model for up to `max_drafts` hypotheses in the closed vocabulary.

    A reply that is not exactly valid is discarded, never repaired. Every draft is prospective
    only: the model's training data covers all of the history here, so history cannot test it."""
    feats = sorted(vocabulary["features"])
    exits = sorted(vocabulary["exits"])
    insts = sorted(vocabulary["instruments"])

    def validate(d: dict) -> str | None:
        items = d.get("hypotheses")
        if not isinstance(items, list) or not 1 <= len(items) <= max_drafts:
            return f"hypotheses must be a list of 1..{max_drafts}"
        for h in items:
            if not isinstance(h, dict):
                return "each hypothesis must be an object"
            for k in ("statement", "rationale", "mechanism"):
                if not isinstance(h.get(k), str) or not h[k].strip():
                    return f"{k} must be a non-empty string"
            cond = h.get("condition")
            if not isinstance(cond, list) or not 1 <= len(cond) <= 2:
                return "condition must list 1 or 2 terms"
            seen = set()
            for term in cond:
                if not isinstance(term, dict) or term.get("feature") not in feats or term.get("bin") not in LABELS:
                    return "condition terms need a declared feature and a bin in low/mid/high"
                if term["feature"] in seen:
                    return "a feature may appear once"
                seen.add(term["feature"])
            if h.get("side") not in ("BUY", "SELL") or h.get("exit") not in exits:
                return "side must be BUY/SELL and exit a declared key"
            if not isinstance(h.get("instruments"), list) or not h["instruments"] or \
                    any(i not in insts for i in h["instruments"]):
                return "instruments must be declared symbols"
        return None

    system = ("You propose falsifiable FX research hypotheses. Use ONLY the vocabulary given; do not invent "
              "features, exits or instruments; never mention position size or leverage. Reply with ONE JSON "
              'object: {"hypotheses": [{"statement": "...", "rationale": "...", "mechanism": "...", '
              '"condition": [{"feature": "...", "bin": "low|mid|high"}], "side": "BUY|SELL", "exit": "...", '
              f'"instruments": [...]}}]}}. Vocabulary: {json.dumps({"features": feats, "exits": exits, "instruments": insts})}')
    res = client.complete_json("research", system, {"observations": observations}, validate)
    if not res.ok:
        return []
    out = []
    for i, h in enumerate(res.data["hypotheses"]):
        cond = Condition(tuple((t["feature"], LABELS.index(t["bin"])) for t in h["condition"]))
        out.append(Hypothesis(
            id=f"{id_prefix}-{i + 1}", statement=h["statement"][:400], rationale=h["rationale"][:600],
            mechanism=h["mechanism"][:400], features=tuple(feature_ids[f] for f in cond.features),
            condition=cond.key, side=h["side"], instruments=tuple(sorted(set(h["instruments"]))), timeframe="H1",
            exit=h["exit"], expected_effect="mean net R per trade > 0 on data recorded after the draft",
            falsification=falsification_from(rules), budget=1, origin="llm", program=program,
            prospective_only=True, evidence={"model": res.model, "training_cutoff": cutoff}))
    return out


def derive_next(h: Hypothesis, exit_key: str, failed: list[str], checks: dict, *, program: str, hid: str,
                instruments_ok: tuple[str, ...] = ()) -> Hypothesis | None:
    """One follow-up from HOW a hypothesis failed — never from how close it came. Always prospective:
    it was shaped by the data that judged its parent. A failure of the core claim (significance,
    permutation, the random baseline) has no follow-up: that idea is dead, not unlucky."""
    core = {"significance", "permutation", "beats_random", "min_trades"}
    if not failed or core & set(failed):
        return None
    base = dict(h.to_json(), id=hid, origin="derived", program=program, parent=h.id, prospective_only=True,
                budget=1, evidence={"parent_failed": failed, "parent_exit": exit_key})
    if set(failed) <= {"costs_stress", "delay_stress"}:
        wider = "E2" if exit_key != "E2" else "E5"
        base.update(exit=wider, statement=h.statement + f" Managed with {wider}, whose wider stop makes costs a "
                                                         "smaller fraction of 1R.",
                    rationale=f"{h.id} failed only on execution stress with {exit_key}")
    elif set(failed) <= {"instruments", "leave_one_out"} and instruments_ok:
        base.update(exit=exit_key, instruments=list(instruments_ok),
                    statement=h.statement + f" Restricted to {', '.join(instruments_ok)}.",
                    rationale=f"{h.id} held only on some instruments; restricting is a new claim to test forward")
    else:
        base.update(exit=exit_key, rationale=f"{h.id} failed {failed}; retest unchanged on new data only")
    return Hypothesis.from_json(base)
