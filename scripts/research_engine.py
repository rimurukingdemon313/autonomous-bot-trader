"""The autonomous research engine (docs/AUTONOMOUS_RESEARCH_SYSTEM.md): one research cycle a day, with no person in
the loop and no way to approve anything.

RESEARCH ONLY. It imports no broker, places no order, sizes nothing and changes no trading rule. Each cycle runs these
steps, each recorded in `cycles.jsonl`:

1. **INTEGRITY.** It checks the permanent record, and any failure makes the cycle fail visibly. The checks:
   - the registry still loads in order, with no back-filling and the seal's rules intact;
   - every verdict's evidence still matches the hash recorded with it;
   - every spec hash is quoted in its preregistration;
   - the seal file is byte for byte the one pinned here;
   - the ideas ledger holds no duplicate.
2. **IDEAS.** The step runs once per cycle; a rerun of the same day skips it.
   - **Propose.** A proposer model (OpenRouter, role "researcher") suggests up to three hypotheses in a strict
     schema. The context it gets: every family already tested, the bar on each market, the costs, the seal, and the
     owner's conditions.
   - **Challenge.** A critic on a different model can only REJECT a hypothesis: a repeat, no mechanism, an
     implausible claim, a leak.
   - **Power gate.** It is deterministic. Each surviving hypothesis is checked against its market's Bonferroni bar,
     at the strength the proposer claims. One that cannot reach the bar even then is DROPPED. One that can is
     QUEUED_FOR_BUILD. A claimed net Sharpe ratio above 2 is DROPPED as a likely error or leak.
   - **Record.** Every hypothesis is written to `ideas.jsonl` with its fingerprint, the models, the critic's reason,
     the power figures and the decision.
3. **REPORT.** The research report is rebuilt with the ideas ledger.

What it never does: register, test or judge a hypothesis. A QUEUED idea is built by the research loop:
- that loop verifies the cited evidence first;
- the idea is preregistered with frozen spec and code hashes;
- it is judged once by its own preregistered gates.

AI proposes and challenges; arithmetic and preregistered rules decide (CLAUDE.md rule 5: AI can only subtract).

Recovery and duplicates:
- A model that fails or answers out of schema fails the IDEAS step. Nothing is repaired or invented. The next run
  retries the step.
- Ideas are written with their cycle id, so a crash after writing cannot write them twice.
- A fingerprint already in the ledger is never added again.
- No successful IDEAS step for 72 hours marks the engine STALLED, and the cycle fails visibly.
"""

from __future__ import annotations

import hashlib
import json
import math
import re
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Callable

ENGINE_VERSION = "research-engine-1.0.1"  # 1.0.1: a failing model is passed over, not waited out
#: research/holdout.json, byte for byte. Any change to the seal fails every cycle until a person re-pins it here.
SEAL_SHA256 = "3d2464db54bc2a147ae46f7b868a7c521c037288a4244f05faeac3c0870f0c89"
HORIZONS = ("scalping", "intraday", "swing", "position")
MAX_IDEAS = 3
MAX_CLAIMED_SHARPE = 2.0
STALL_HOURS = 72
DECISIONS = ("REJECTED_BY_CRITIC", "DROPPED_IMPLAUSIBLE", "DROPPED_POWER", "QUEUED_FOR_BUILD")

#: (ok, status, data, model, error): one structured answer from a model, or why there is none
Answer = tuple[bool, str, "dict | None", "str | None", "str | None"]
Ask = Callable[[str, list[dict], Callable[[dict], "str | None"], tuple], Answer]


# ── the permanent ledgers ────────────────────────────────────────────────

def read_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    return [json.loads(x) for x in path.read_text().splitlines() if x.strip()]


def append_jsonl(path: Path, rows: list[dict]) -> None:
    """Append whole lines in one write: a crash leaves either every row or none of a line half-written."""
    if not rows:
        return
    with open(path, "a") as f:
        f.write("".join(json.dumps(r, sort_keys=True, default=str) + "\n" for r in rows))
        f.flush()


def _words(s: str) -> str:
    return " ".join(re.findall(r"[a-z0-9]+", s.lower()))


def fingerprint(h: dict) -> str:
    """The same market, horizon and rule, however worded in case and punctuation, is the same idea."""
    return hashlib.sha256(f"{h['universe']}|{h['horizon']}|{_words(h['rule'])}".encode()).hexdigest()[:20]


# ── the power gate: arithmetic, no model ─────────────────────────────────

def _phi(x: float) -> float:
    return 0.5 * (1 + math.erf(x / math.sqrt(2)))


def power(claimed_sharpe: float, years: float, bar: float) -> dict:
    """At its claimed annual net Sharpe ratio over `years` of data it has not been tested on, the t a test would
    expect, and the chance it clears `bar` (t drawn around its expectation with unit spread)."""
    expected = claimed_sharpe * math.sqrt(years)
    return {"claimed_sharpe": claimed_sharpe, "years": years, "bar": round(bar, 4),
            "expected_t": round(expected, 3), "p_pass": round(1 - _phi(bar - expected), 3)}


def decide(h: dict, bar: float) -> tuple[str, str, dict | None]:
    if h["claimed_sharpe_annual"] > MAX_CLAIMED_SHARPE:
        return ("DROPPED_IMPLAUSIBLE", f"a claimed net Sharpe of {h['claimed_sharpe_annual']} at retail costs is "
                f"treated as an error or a leak until shown otherwise (above {MAX_CLAIMED_SHARPE})", None)
    pw = power(h["claimed_sharpe_annual"], h["years_of_fresh_data"], bar)
    if pw["expected_t"] < bar:
        return ("DROPPED_POWER", f"even at its claimed strength it expects t {pw['expected_t']} against a bar of "
                f"{pw['bar']}: it cannot pass, so it is not built", pw)
    return ("QUEUED_FOR_BUILD", f"at its claimed strength it expects t {pw['expected_t']} against {pw['bar']} "
            f"(passes {pw['p_pass']:.0%} of the time); the claim must be verified at its source before it is built", pw)


# ── what the models must answer ──────────────────────────────────────────

FIELDS = {"title": 160, "mechanism": 900, "universe": 60, "horizon": 20, "rule": 900, "data_source": 400,
          "evidence": 900, "why_new": 600, "needs_short_or_leverage": 200}


def validate_proposal(data: dict, universes: set[str]) -> str | None:
    hs = data.get("hypotheses") if isinstance(data, dict) else None
    if not isinstance(hs, list) or not 1 <= len(hs) <= MAX_IDEAS:
        return f"hypotheses must be a list of 1 to {MAX_IDEAS}"
    for i, h in enumerate(hs):
        if not isinstance(h, dict):
            return f"hypothesis {i} is not an object"
        for k, n in FIELDS.items():
            if not isinstance(h.get(k), str) or not h[k].strip() or len(h[k]) > n:
                return f"hypothesis {i}: {k} must be text of 1 to {n} characters"
        if h["horizon"] not in HORIZONS:
            return f"hypothesis {i}: horizon must be one of {HORIZONS}"
        if h["universe"] not in universes and not re.fullmatch(r"new:[a-z0-9-]{3,40}", h["universe"]):
            return f"hypothesis {i}: universe {h['universe']!r} is neither a listed market nor new:<name>"
        for k, lo, hi in (("claimed_sharpe_annual", 0.0, 10.0), ("years_of_fresh_data", 0.5, 100.0)):
            v = h.get(k)
            if isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v) or not lo < v <= hi:
                return f"hypothesis {i}: {k} must be a number in ({lo}, {hi}]"
    return None


def validate_review(data: dict, n: int) -> str | None:
    rs = data.get("reviews") if isinstance(data, dict) else None
    if not isinstance(rs, list) or len(rs) != n:
        return f"reviews must be a list of exactly {n}"
    if sorted(r.get("index") for r in rs if isinstance(r, dict)) != list(range(n)):
        return f"reviews must cover each index 0..{n - 1} once"
    for r in rs:
        if r.get("verdict") not in ("PASS", "REJECT"):
            return "each verdict must be PASS or REJECT"
        if not isinstance(r.get("reason"), str) or not r["reason"].strip() or len(r["reason"]) > 900:
            return "each review needs a reason of 1 to 900 characters"
    return None


# ── the context the proposer and the critic are given ────────────────────

SYSTEM_PROPOSER = """You are the hypothesis proposer of a quantitative research lab. You propose; you never approve.
A separate critic model, deterministic statistics and preregistered tests decide everything.

Propose up to three NEW trading hypotheses that could earn money net of retail costs. Each must rest on an economic
mechanism (who is forced or willing to lose, and why that persists), not on a chart pattern. Prefer mechanisms and
data this lab has never tested. Never propose a family listed as already tested or dropped unless you name genuinely
new evidence (new data, a new market, a new mechanism) in why_new.

Hard conditions (the owner's):
- the account is a swap-free (Islamic) CFD account: spread, slippage and commission, no overnight financing, and no
  interest-bearing instrument (no bonds, no carry earned as interest);
- say plainly in needs_short_or_leverage whether it needs short selling or leverage;
- research and paper only.

Statistical facts of this lab:
- every market's data has a Bonferroni bar (listed) that grows with each test on it;
- the FX majors from 2017 on are a sealed holdout and cannot be used for discovery;
- real effects have repeatedly shown before costs and vanished after them;
- many published anomalies faded after publication.
So claim only what the source supports: claimed_sharpe_annual is the NET annual Sharpe ratio the evidence supports
after retail costs, and years_of_fresh_data is how many years of data NOT already read by this lab a test could use.
Overstating either only wastes a test; a claim is checked at its source before anything is built.

Answer with JSON only: {"hypotheses": [{"title", "mechanism", "universe", "horizon", "rule", "data_source",
"evidence", "claimed_sharpe_annual", "years_of_fresh_data", "why_new", "needs_short_or_leverage"}]}
- universe: one of the listed markets, or "new:<short-name>" for data no test here has used;
- horizon: one of scalping, intraday, swing, position;
- rule: exact entry, exit and sizing-free position rule, with no look-ahead;
- evidence: the source (authors, year, venue) and what it measured, or "none: a new idea".
"""

SYSTEM_CRITIC = """You are the independent critic of a quantitative research lab. You can only REJECT; you cannot
approve, add, change or repair a hypothesis. Reject each hypothesis that:
- repeats a family already tested or dropped (name it) without genuinely new evidence;
- has no economic mechanism, or one that would not survive after publication;
- claims more than its evidence could support, or a net Sharpe ratio implausible at retail costs;
- cannot be tested without look-ahead, survivorship bias or data leakage, or on data that cannot be had;
- breaks the owner's conditions (swap-free, no interest-bearing instrument).
Otherwise PASS it to the statistics, which decide. Answer with JSON only:
{"reviews": [{"index": <int>, "verdict": "PASS" | "REJECT", "reason": "<why>", "duplicate_of": "<family or null>"}]}
"""


def context(known: list[str], bars: dict[str, dict], lessons: list[str]) -> str:
    lines = ["Markets (universe: tests already counted, the next test's bar t):"]
    lines += [f"- {u}: {b['tests']} tests, bar {b['next_bar_t']:.3f}" for u, b in sorted(bars.items())]
    lines += ["", "Lessons from the record:"] + [f"- {x}" for x in lessons]
    lines += ["", f"Families already tested or dropped ({len(known)}):"] + [f"- {k}" for k in known]
    return "\n".join(lines)


LESSONS = [
    "costs: a retail CFD's spread and slippage took the whole gross edge of every intraday family tested here",
    "power: with years of daily data, a net Sharpe below about 1 cannot reach a bar near 3; monthly rules need decades",
    "publication: most published calendar and flow anomalies tested here had faded in the years after their papers",
    "the one VALIDATED rule (TRND-1) is a slow trend filter on stock indices: the equity premium with smaller crashes",
]


# ── the cycle ────────────────────────────────────────────────────────────

@dataclass
class CycleResult:
    cycle: str
    integrity: list[str]
    ideas: str  # OK | SKIPPED (done earlier today) | FAILED: <why>
    new_ideas: list[dict]
    stalled: bool
    exit_code: int


class Engine:
    def __init__(self, root: Path, state: Path, ask: Ask | None, now: datetime) -> None:
        self.root, self.state, self.ask, self.now = Path(root), Path(state), ask, now
        self.attempts: list[dict] = []  # every model asked in this cycle, and how it answered
        self.state.mkdir(parents=True, exist_ok=True)
        self.cycle = now.astimezone(timezone.utc).strftime("%Y-%m-%d")

    # the record
    @property
    def ideas_path(self) -> Path:
        return self.state / "ideas.jsonl"

    @property
    def cycles_path(self) -> Path:
        return self.state / "cycles.jsonl"

    def _log(self, step: str, status: str, detail: object = None) -> None:
        append_jsonl(self.cycles_path, [{"cycle": self.cycle, "step": step, "status": status, "detail": detail,
                                         "at": self.now.isoformat(), "version": ENGINE_VERSION}])

    def integrity(self) -> list[str]:
        from aitrader.research.registry import Holdout, Registry, RegistryError
        from scripts.research_report import build_report
        problems = []
        seal = self.root / "research" / "holdout.json"
        if hashlib.sha256(seal.read_bytes()).hexdigest() != SEAL_SHA256:
            problems.append("the seal (research/holdout.json) differs from the one pinned in the engine")
        try:
            Registry.load(self.root / "research" / "registry.jsonl", Holdout.load(seal))
        except (RegistryError, ValueError, KeyError) as e:
            problems.append(f"the registry does not load: {e}")
            return problems
        c = build_report(self.root, self.now.date(), self.now, classify=lambda root: {"counts": {}, "standing": []}
                         )["cumulative"]
        problems += [f"{t}: its evidence no longer matches the hash recorded with its verdict"
                     for t in c["evidence_changed"]]
        problems += [f"{t}: its spec hash is not quoted in its preregistration" for t in c["spec_not_quoted"]]
        prints = [i["fingerprint"] for i in read_jsonl(self.ideas_path)]
        problems += [f"the ideas ledger holds {f} more than once" for f in sorted({p for p in prints
                                                                                    if prints.count(p) > 1})]
        return problems

    def known_families(self) -> list[str]:
        from scripts.research_report import queue_drops, read_registry
        trials, _ = read_registry(self.root)
        out = [t.get("title") or t["id"] for t in trials.values()]
        out += [i for x in queue_drops((self.root / "research" / "QUEUE.md").read_text()) for i in x["ideas"]]
        out += [f"{i['title']} ({i['decision']})" for i in read_jsonl(self.ideas_path)]
        return [x[:200] for x in out]

    def bars(self) -> dict[str, dict]:
        from aitrader.research.registry import Holdout, Registry
        from scripts.research_report import read_registry
        trials, _ = read_registry(self.root)
        reg = Registry.load(self.root / "research" / "registry.jsonl",
                            Holdout.load(self.root / "research" / "holdout.json"))
        us = sorted({u["universe"] for t in trials.values() for u in t.get("uses", [])})
        return {u: {"tests": reg.tests_on(u), "next_bar_t": reg.threshold_for_next(u)} for u in us}

    def ideas_done_today(self) -> bool:
        if any(i["cycle"] == self.cycle for i in read_jsonl(self.ideas_path)):
            return True  # written, even if the checkpoint after it was lost
        return any(c["cycle"] == self.cycle and c["step"] == "ideas" and c["status"] == "OK"
                   for c in read_jsonl(self.cycles_path))

    def _ask(self, role: str, msgs: list[dict], validate, avoid: tuple, tries: int = 3) -> Answer:
        """A model's answer, from up to `tries` models. A model that fails is never asked again in the step: one
        rate-limited, timed out, unavailable or out of schema (never repaired) is passed over and the next is asked;
        each call is a read with no side effects, so this is safe. A failure that names no model (no key, no free model,
        the budget or the day's quota spent) stops the step: no other model would answer. Every attempt is recorded."""
        failed: list[str] = []
        ans: Answer = (False, "NOT_ASKED", None, None, None)
        for _ in range(tries):
            ans = self.ask(role, msgs, validate, tuple(avoid) + tuple(failed))
            ok, status, _, model, _ = ans
            self.attempts.append({"role": role, "model": model, "status": status})
            if ok or model is None:
                return ans
            failed.append(model)
        return ans

    def generate(self) -> tuple[str, list[dict]]:
        if self.ideas_done_today():
            return "SKIPPED", []
        if self.ask is None:
            return "FAILED: no model client (OPENROUTER_API_KEY is not set)", []
        bars = self.bars()
        from aitrader.research.registry import bonferroni_t
        ctx = context(self.known_families(), bars, LESSONS)
        msgs = [{"role": "system", "content": SYSTEM_PROPOSER},
                {"role": "user", "content": f"Cycle {self.cycle}.\n\n{ctx}\n\nPropose up to {MAX_IDEAS}."}]
        ok, status, prop, proposer, err = self._ask("researcher", msgs, lambda d: validate_proposal(d, set(bars)), ())
        if not ok:
            return f"FAILED: the proposer gave no usable answer ({status}: {err})", []
        hs = prop["hypotheses"]
        listing = json.dumps([{k: h[k] for k in FIELDS} | {"claimed_sharpe_annual": h["claimed_sharpe_annual"],
                                                            "years_of_fresh_data": h["years_of_fresh_data"]}
                              for h in hs], indent=1)
        cmsgs = [{"role": "system", "content": SYSTEM_CRITIC},
                 {"role": "user", "content": f"{ctx}\n\nHypotheses to review (index from 0):\n{listing}"}]
        ok, status, rev, critic, err = self._ask("critic", cmsgs, lambda d: validate_review(d, len(hs)),
                                                 (proposer,) if proposer else ())
        if not ok:
            return f"FAILED: the critic gave no usable answer ({status}: {err}); nothing is recorded unreviewed", []
        if critic is not None and critic == proposer:
            return "FAILED: the critic was the proposer's own model; nothing is recorded", []
        reviews = {r["index"]: r for r in rev["reviews"]}
        seen = {i["fingerprint"] for i in read_jsonl(self.ideas_path)}
        rows = []
        for n, h in enumerate(hs):
            fp = fingerprint(h)
            if fp in seen:
                continue  # the same idea again: never recorded or built twice
            seen.add(fp)
            r = reviews[n]
            bar = bars[h["universe"]]["next_bar_t"] if h["universe"] in bars else bonferroni_t(1)
            if r["verdict"] == "REJECT":
                decision, why, pw = "REJECTED_BY_CRITIC", r["reason"], None
            else:
                decision, why, pw = decide(h, bar)
            rows.append({"cycle": self.cycle, "fingerprint": fp, "at": self.now.isoformat(), "source": "engine",
                         "proposer": proposer, "critic": critic, **{k: h[k] for k in FIELDS},
                         "claimed_sharpe_annual": h["claimed_sharpe_annual"],
                         "years_of_fresh_data": h["years_of_fresh_data"], "critic_verdict": r["verdict"],
                         "critic_reason": r["reason"], "duplicate_of": r.get("duplicate_of"), "power": pw,
                         "decision": decision, "why": why, "version": ENGINE_VERSION})
        append_jsonl(self.ideas_path, rows)
        return "OK", rows

    def stalled(self, ideas_status: str) -> bool:
        if ideas_status in ("OK", "SKIPPED"):
            return False
        oks = [datetime.fromisoformat(c["at"]) for c in read_jsonl(self.cycles_path)
               if c["step"] == "ideas" and c["status"] == "OK"]
        first = [datetime.fromisoformat(c["at"]) for c in read_jsonl(self.cycles_path)]
        since = max(oks) if oks else (min(first) if first else self.now)
        return self.now - since > timedelta(hours=STALL_HOURS)

    def run(self) -> CycleResult:
        problems = self.integrity()
        self._log("integrity", "OK" if not problems else "FAILED", problems or None)
        try:
            status, rows = self.generate()
        except Exception as e:  # noqa: BLE001 - recorded, retried next run; nothing half-written (one append)
            status, rows = f"FAILED: {type(e).__name__}: {e}", []
        stalled = self.stalled(status)
        if status != "SKIPPED":
            self._log("ideas", "OK" if status == "OK" else "FAILED",
                      {"why": status, "ideas": [r["fingerprint"] for r in rows], "attempts": self.attempts}
                      if status != "OK" else {"ideas": [r["fingerprint"] for r in rows], "attempts": self.attempts})
        if stalled:
            self._log("stall", "FAILED", f"no successful IDEAS step for over {STALL_HOURS} hours")
        code = 1 if problems else 2 if stalled else 0
        return CycleResult(self.cycle, problems, status, rows, stalled, code)


def openrouter_ask(env: dict | None = None) -> Ask | None:
    """The production `ask`: the project's own OpenRouter client (FREE models, bounded retries, budgets)."""
    from aitrader.llm.openrouter import OpenRouterClient, OpenRouterConfig
    cfg = OpenRouterConfig.from_env(env)
    if not cfg.configured:
        return None
    client = OpenRouterClient(cfg)

    def ask(role: str, messages: list[dict], validate, avoid: tuple) -> Answer:
        res = client.chat_json(role, messages, validate, dedupe_key=f"research:{role}", max_tokens=6000,
                               avoid=tuple(a for a in avoid if a), deadline_s=150.0)  # then the next model
        return res.ok, res.status, res.data, res.model, res.error
    return ask


__all__ = ["DECISIONS", "ENGINE_VERSION", "Engine", "SEAL_SHA256", "decide", "fingerprint", "openrouter_ask",
           "power", "read_jsonl", "validate_proposal", "validate_review"]
