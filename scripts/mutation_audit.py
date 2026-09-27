"""Mutation audit: remove each safety guard in turn and require a test to fail.

    python scripts/mutation_audit.py            # writes docs/MUTATION_AUDIT.md

A guard whose removal no test notices is a guard nobody is checking
(docs/TESTING_PHILOSOPHY.md). Each mutant replaces one exact snippet; the
file is restored whatever happens. A mutant whose snippet is not found is
reported as STALE, never skipped silently.
"""

from __future__ import annotations

import os
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# (id, guard, file, original, mutant, tests)
MUTANTS = [
    ("risk-ceiling", "per-trade risk is clamped to the 1 % hard ceiling",
     "aitrader/risk/engine.py", "pct = min(self.risk_per_trade_pct, HARD_MAX_RISK_PCT)",
     "pct = self.risk_per_trade_pct", ["tests/unit/test_risk.py"]),
    ("risk-streak", "risk only ever decreases after losses",
     "aitrader/risk/engine.py", "return max(floor_, 0.5 ** (run // step)) if step > 0 else 1.0",
     "return 1.0", ["tests/unit/test_risk.py"]),
    ("risk-drawdown", "maximum drawdown halts trading",
     "aitrader/risk/engine.py", 'check("drawdown", dd > -max_dd,', 'check("drawdown", True,',
     ["tests/unit/test_risk.py"]),
    ("exec-killswitch", "an unreadable kill switch counts as active",
     "aitrader/execution/engine.py", 'if not isinstance(ks, dict) or ks.get("active") is not False:',
     'if isinstance(ks, dict) and ks.get("active") is True:', ["tests/unit/test_execution.py"]),
    ("exec-demo", "no order unless the account is positively verified demo/paper",
     "aitrader/execution/engine.py", "if demo is not True and not self.allow_live:",
     "if demo is False and not self.allow_live:", ["tests/unit/test_execution.py"]),
    ("exec-no-resend", "an ambiguous write is resolved by query, never resent",
     "aitrader/execution/engine.py",
     '            self._set_status(cid, "UNKNOWN", {"reason": str(exc)})\n            found = self._lookup(cid)',
     '            self._set_status(cid, "UNKNOWN", {"reason": str(exc)})\n'
     '            self.broker.place_market(decision.instrument, side, verdict.qty, verdict.stop, verdict.target,'
     ' cid + "-retry", meta=meta or {})\n            found = self._lookup(cid)',
     ["tests/unit/test_execution.py"]),
    ("exec-stale-price", "no order when the live price is already beyond the stop",
     "aitrader/execution/engine.py", "if (live - verdict.stop) * side <= 0:", "if False:",
     ["tests/unit/test_execution.py"]),
    ("demo-name", "an account NAME can fail the demo check but never pass it",
     "aitrader/broker/tradelocker/demo_guard.py",
     "    for field, raw in names:\n        text = str(raw).strip().lower()",
     "    candidates.extend(names)\n    for field, raw in names:\n        text = str(raw).strip().lower()",
     ["tests/unit/test_tradelocker_adapter.py"]),
    ("live-refused", "MODE=LIVE is refused at startup, with its own reason",
     "aitrader/service/config.py", 'if mode == "LIVE":', 'if mode == "NEVER":',
     ["tests/integration/test_service.py"]),
    ("live-both-layers", "MODE=LIVE is refused even if the allow-list were widened",
     "aitrader/service/config.py", ['if mode == "LIVE":', 'if mode not in ("PAPER", "DEMO"):'],
     ['if mode == "NEVER":', 'if mode not in ("PAPER", "DEMO", "LIVE"):'],
     ["tests/integration/test_service.py"]),
    ("token", "resume / clear / scan / revert need the dashboard token",
     "aitrader/service/server.py", "if given and hmac.compare_digest(given.encode(), token.encode()):",
     "if True:", ["tests/integration/test_service.py"]),
    ("knowledge-hash", "the knowledge base loads only if it matches its card",
     "aitrader/service/runtime.py", 'if digest != meta.get("sha256"):', "if False:",
     ["tests/integration/test_service.py"]),
    ("cycle-lock", "cycles, scans and bar monitoring never run concurrently",
     "aitrader/service/runtime.py", "        with self._cycle_lock:\n            return self._run_cycle_locked(",
     "        if True:\n            return self._run_cycle_locked(", ["tests/integration/test_service.py"]),
    ("revert-append-only", "a knowledge revert is a new, higher version; numbers are never reused",
     "aitrader/orchestrator/core.py", "self.knowledge_version = max(latest, parent) + 1",
     "self.knowledge_version = parent + 1 if not extra else extra.get('revert_to', parent) + 1",
     ["tests/integration/test_service.py"]),
    ("shadow-journal", "skipped candidates' outcomes are journalled for restart",
     "aitrader/orchestrator/core.py", 'if shadows and self.cfg.journal == "full":', "if False:",
     ["tests/integration/test_pipeline.py"]),
    ("log-redaction", "secret environment values never reach a log line",
     "aitrader/observability.py", "    for secret in _secret_values():", "    for secret in []:",
     ["tests/unit/test_observability.py"]),
    ("learning-overlap", "overlapping outcomes are not counted as independent evidence",
     "aitrader/learning/experience.py", "        return overlap * max(1.0, self.n / max(1, uniq))", "        return 1.0",
     ["tests/unit/test_learning.py"]),
    ("lab-register-first", "nothing is evaluated before it is registered",
     "aitrader/research/lab.py", '            raise LabError(f"{trial_id} is not registered: nothing is evaluated before it is") from None',
     '            trial = None', ["tests/unit/test_research_lab.py"]),
    ("lab-no-rescue", "a failed hypothesis cannot be re-run with a new threshold or dates",
     "aitrader/research/lab.py", 'if t.design.get("substance") == spec.substance() and self.registry.status_of(t.id) == "FAILED":',
     'if False:', ["tests/unit/test_research_lab.py"]),
    ("lab-llm-cutoff", "a language-model hypothesis is never judged on data the model may have read",
     "aitrader/research/lab.py", "            if spec.fit_start < spec.llm_cutoff:", "            if False:", ["tests/unit/test_research_lab.py"]),
    ("lab-holdout", "the lab never touches the sealed holdout",
     "aitrader/research/lab.py", "        if h is not None and h.universe == spec.universe and spec.judge_end > h.start:",
     "        if False:", ["tests/unit/test_research_lab.py"]),
    ("lab-isolation", "the lab never writes where production loads",
     "aitrader/research/lab.py", "        if self.artifacts_dir == PRODUCTION_ARTIFACTS or PRODUCTION_ARTIFACTS in self.artifacts_dir.parents:",
     "        if False:", ["tests/unit/test_research_lab.py"]),
    ("lab-purge", "walk-forward trains only on outcomes resolved before the fold (minus an embargo)",
     "aitrader/research/lab.py", "(rt >= 0) & (rt < f0 - embargo) & np.isfinite(y)", "(rt >= 0) & np.isfinite(y)", ["tests/unit/test_research_lab.py"]),
    ("lab-scan-overlap", "the scan counts only non-overlapping outcomes",
     "aitrader/research/lab.py", "            ok &= _non_overlapping(t, rt, sym)", "            pass", ["tests/unit/test_research_lab.py"]),
    ("feature-leakage-gate", "a leaky candidate feature is rejected before evaluation",
     "aitrader/research/features_lab.py", '"status": "ELIGIBLE" if not bad else "REJECTED_LEAKAGE"',
     '"status": "ELIGIBLE"', ["tests/unit/test_research_lab.py"]),
    ("holdout-loader", "the loader truncates at the sealed holdout without a key",
     "aitrader/data/store.py", "if self.holdout is not None and key is None:", "if False:",
     ["tests/unit/test_registry_and_store.py"]),
    ("holdout-single-use", "the final holdout answers one question, once",
     "aitrader/research/registry.py", "                if prior:\n                    raise HoldoutSpent(",
     "                if False:\n                    raise HoldoutSpent(", ["tests/unit/test_registry_and_store.py"]),
    ("memory-point-in-time", "an analogue counts only after its outcome resolved",
     "aitrader/memory/patterns.py", 'n_avail = int(np.searchsorted(avail, t, side="right"))',
     "n_avail = len(avail)", ["tests/unit/test_regime_and_patterns.py"]),
    ("label-stop-first", "stop and target in one bar resolve as the stop (labels)",
     "aitrader/research/labels.py", "tgt_hit = open_ & ~stop_hit & (hi >= target)",
     "tgt_hit = open_ & (hi >= target)", ["tests/unit/test_labels.py"]),
    ("paper-stop-first", "stop and target in one bar resolve as the stop (paper broker)",
     "aitrader/broker/paper.py",
     '                    if lo <= p["stop"]:\n                        closed.append(self._close(pid, min(op, p["stop"]) - slip, bar["close_time"], "STOP"))\n'
     '                    elif hi >= p["target"]:',
     '                    if hi >= p["target"]:\n                        closed.append(self._close(pid, p["target"], bar["close_time"], "TARGET"))\n'
     '                    elif lo <= p["stop"]:\n                        closed.append(self._close(pid, min(op, p["stop"]) - slip, bar["close_time"], "STOP"))\n'
     '                    elif False:',
     ["tests/unit/test_execution.py", "tests/integration/test_pipeline.py"]),
    ("synth-blocking", "a market-wide BLOCKING objection gives NO_TRADE before any candidate is weighed",
     "aitrader/decision/synthesis.py", '        if blocking:\n            return no_trade("blocked: "',
     '        if False:\n            return no_trade("blocked: "', ["tests/unit/test_agents.py"]),
    ("synth-blocking-both-layers", "a BLOCKING objection gives NO_TRADE (market-wide and per-candidate layers removed)",
     "aitrader/decision/synthesis.py",
     ['        if blocking:\n            return no_trade("blocked: "', "            if block:\n"],
     ['        if False:\n            return no_trade("blocked: "', "            if False:\n"],
     ["tests/unit/test_agents.py"]),
    ("reviewer-required", "a failed Reviewer (which carries lesson matching) gives NO_TRADE",
     "aitrader/decision/synthesis.py", 'REQUIRED_AGENTS = ("market", "setup", "risk", "adversary", "reviewer")',
     'REQUIRED_AGENTS = ("market", "setup", "risk", "adversary")', ["tests/unit/test_agents.py"]),
    ("synth-missing-agent", "a missing or failed agent gives NO_TRADE",
     "aitrader/decision/synthesis.py", "if r is None or not r.ok:", "if False:",
     ["tests/unit/test_agents.py"]),
    ("unfamiliar", "an unfamiliar market state blocks the trade",
     "aitrader/agents/analysts.py", "        if not rg.familiar:", "        if False:",
     ["tests/unit/test_agents.py", "tests/integration/test_pipeline.py"]),
    ("llm-vocabulary", "a model reply outside the closed objection vocabulary is discarded",
     "aitrader/agents/analysts.py", 'o.get("code") not in OBJECTION_CODES or ', "",
     ["tests/unit/test_agents.py"]),
    ("db-immutable", "episodic history cannot be updated or deleted",
     "aitrader/memory/db.py", "BEGIN SELECT RAISE(ABORT, '{table} is immutable history'); END",
     "BEGIN SELECT 1; END", ["tests/unit/test_db.py"]),
    ("price-scale", "an ambiguous price scale is refused, never guessed",
     "aitrader/data/instruments.py", "if len(fits) != 1:", "if not fits:", ["tests/unit/test_data.py"]),
]


def run_tests(tests: list[str]) -> tuple[bool, float]:
    t0 = time.time()
    # No bytecode is written: a mutant of the same size restored within the same
    # second would otherwise stay cached and silently poison every later run.
    r = subprocess.run([sys.executable, "-B", "-m", "pytest", "-x", "-q", "-p", "no:cacheprovider", *tests],
                       cwd=ROOT, capture_output=True, text=True, env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"})
    return r.returncode == 0, time.time() - t0


def main() -> int:
    rows = []
    for mid, guard, rel, old, new, tests in MUTANTS:
        path = ROOT / rel
        src = path.read_text()
        olds, news = ([old], [new]) if isinstance(old, str) else (old, new)
        counts = [src.count(o) for o in olds]
        if any(c != 1 for c in counts):
            rows.append((mid, guard, rel, "STALE", f"snippets found {counts} times", tests))
            print(mid, "STALE", flush=True)
            continue
        mutated = src
        for o, n in zip(olds, news):
            mutated = mutated.replace(o, n)
        try:
            path.write_text(mutated)
            passed, secs = run_tests(tests)
        finally:
            path.write_text(src)
            for stale in path.parent.glob(f"__pycache__/{path.stem}.*.pyc"):
                stale.unlink()
        verdict = "SURVIVED" if passed else "KILLED"
        rows.append((mid, guard, rel, verdict, f"{secs:.0f}s", tests))
        print(mid, verdict, flush=True)
    killed = sum(r[3] == "KILLED" for r in rows)
    lines = [
        "# Mutation audit",
        "",
        "Each row removes or inverts one safety guard and runs the tests that",
        "should notice. **KILLED** = a test failed, as it must. **SURVIVED** = no",
        "test noticed: the guard is unchecked. Generated by",
        "`python scripts/mutation_audit.py`; the source is restored after each mutant.",
        "",
        f"**{killed} of {len(rows)} killed.**",
        "",
        "| Guard | Where | Result | Tests run |",
        "|---|---|---|---|",
    ]
    for mid, guard, rel, verdict, note, tests in rows:
        lines.append(f"| {guard} (`{mid}`) | `{rel}` | **{verdict}** ({note}) | "
                     + ", ".join(f"`{t.split('/')[-1]}`" for t in tests) + " |")
    (ROOT / "docs" / "MUTATION_AUDIT.md").write_text("\n".join(lines) + "\n")
    return 0 if killed == len(rows) else 1


if __name__ == "__main__":
    raise SystemExit(main())
