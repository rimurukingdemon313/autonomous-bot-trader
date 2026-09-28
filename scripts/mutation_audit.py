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
     "aitrader/risk/engine.py", 'Check("drawdown", dd > -max_dd,', 'Check("drawdown", True,',
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
    ("boundary-imports", "research code cannot import the broker or execution",
     "aitrader/research/lab.py", "from .models import MODEL_FAMILIES, MODELS_VERSION",
     "from .models import MODEL_FAMILIES, MODELS_VERSION\nfrom ..broker.paper import PaperBroker  # noqa: F401",
     ["tests/unit/test_architecture.py"]),
    ("boundary-sizing", "only the risk engine computes a position size",
     "aitrader/decision/synthesis.py", "        cand, required, conf, contra = best_decision",
     "        cand, required, conf, contra = best_decision\n        qty = 1.0  # noqa: F841",
     ["tests/unit/test_architecture.py"]),
    ("llm-trader-side", "a model trade with its stop or target on the wrong side is refused",
     "aitrader/agents/llm_trader.py", "    if (entry - stop) * side <= 0 or (target - entry) * side <= 0:", "    if False:", ["tests/unit/test_llm_trader.py", "tests/unit/test_trading_room.py"]),
    ("llm-trader-block-first", "a market-wide block stops the decision before the model is consulted",
     "aitrader/agents/llm_trader.py", "    if blocking:\n        return (\"blocked before consulting the model", "    if False:\n        return (\"blocked before consulting the model", ["tests/unit/test_llm_trader.py", "tests/unit/test_trading_room.py"]),
    ("llm-trader-paused", "while paused or stopped the model is not consulted",
     "aitrader/agents/llm_trader.py", "    if not ctx.trading_allowed:", "    if False:", ["tests/unit/test_llm_trader.py", "tests/unit/test_trading_room.py"]),
    ("llm-trader-no-backtest", "the model trader refuses to be backtested",
     "aitrader/agents/llm_trader.py", '        if ctx.mode == "BACKTEST":', "        if False:", ["tests/unit/test_llm_trader.py"]),
    ("llm-trader-stop-distance", "an absurdly far stop (a typo) is refused",
     "aitrader/agents/llm_trader.py", "    if dist > MAX_STOP_ATR:", "    if False:", ["tests/unit/test_llm_trader.py", "tests/unit/test_trading_room.py"]),
    ("llm-trader-lesson", "a validated lesson about its own trades blocks the repeat",
     "aitrader/agents/llm_trader.py", "        if hits:", "        if False:", ["tests/unit/test_llm_trader.py", "tests/unit/test_trading_room.py"]),
    ("llm-view-not-veto", "the quant system's view of the market is information to the model, not a veto",
     "aitrader/agents/llm_trader.py", " and not o.data.get(\"action\") and o.code in PRE_MODEL_BLOCKS]",
     " and not o.data.get(\"action\")]", ["tests/unit/test_llm_trader.py", "tests/unit/test_trading_room.py"]),
    ("provider-failover", "when a provider fails, the next provider answers",
     "aitrader/llm/provider.py", "        for ep in endpoints:", "        for ep in endpoints[:1]:",
     ["tests/unit/test_llm_providers.py"]),
    ("provider-key-redaction", "every *_API_KEY variable is redacted from logs",
     "aitrader/observability.py", "        if key in SECRET_ENV_KEYS or _SECRET_NAME.search(key):",
     "        if key in SECRET_ENV_KEYS:", ["tests/unit/test_llm_providers.py"]),
    ("cadence-evidence-refused", "the evidence system refuses a decision cadence it was never tested at",
     "aitrader/service/runtime.py", "if cfg.decision_interval_min and self.orch.brain.config.decision_mode not in MODEL_MODES:",
     "if False:", ["tests/integration/test_cadence.py"]),
    ("cadence-rotation", "pairs rotate so every pair is analysed in turn",
     "aitrader/service/runtime.py", "        self._rotation = (self._rotation + k) % len(syms)\n", "", ["tests/integration/test_cadence.py"]),
    ("paper-preopen-bar", "a bar from before a position opened never closes it",
     "aitrader/broker/paper.py", 'if p["symbol"] != symbol or p["opened"] > bar["open_time"]:',
     'if p["symbol"] != symbol:', ["tests/integration/test_cadence.py"]),
    ("fast-monitor", "open paper positions are checked on M1 bars between H1 closes",
     "aitrader/service/runtime.py", "        self._monitor_fast(now)\n", "", ["tests/integration/test_cadence.py"]),
    ("market-row-isolation", "one pair's failed price does not blank the pairs table",
     "aitrader/service/runtime.py", "            except Exception as exc:\n                q, q_err = None,",
     "            except ZeroDivisionError as exc:\n                q, q_err = None,", ["tests/integration/test_cadence.py"]),
    ("calendar-unknown-not-empty", "an unreachable calendar is reported as unknown, never as no events",
     "aitrader/data/calendar.py", "out[\"events\"] = None  # unknown, not \"none\"", "out[\"events\"] = []",
     ["tests/unit/test_calendar.py"]),
    ("calendar-rate-limit", "the calendar is downloaded at most hourly",
     "aitrader/data/calendar.py", "if self._fetched_at is not None and now - self._fetched_at < REFRESH_S:",
     "if False:", ["tests/unit/test_calendar.py"]),
    ("room-roles", "each mind is told its role in the team",
     "aitrader/agents/trading_room.py", "role = \" AND \".join(f\"{r}, {desc[r]}\" for r in roles[m])",
     "role = \"any\"", ["tests/unit/test_trading_room.py"]),
    ("history-integrity", "the history memory loads only if it matches its card",
     "aitrader/service/runtime.py", "            if digest == meta.get(\"sha256\"):\n                desk = HistoryDesk(",
     "            if True:\n                desk = HistoryDesk(", ["tests/unit/test_history_desk.py"]),
    ("history-episodes", "overlapping hours are not counted as independent evidence",
     "aitrader/memory/history.py", "* (ev.k / max(1, ev.distinct_episodes or ev.k)) ** 0.5", "* 1.0",
     ["tests/unit/test_history_desk.py"]),
    ("review-closes", "the model closes its open trade when it decides to",
     "aitrader/orchestrator/core.py", "            if verdict and verdict[\"action\"] == \"CLOSE\":",
     "            if False:", ["tests/integration/test_cadence.py"]),
    ("review-only-close", "a review can only hold or close; anything else holds",
     "aitrader/agents/llm_trader.py", "    if d.get(\"action\") not in (\"HOLD\", \"CLOSE\"):\n        return \"action must be HOLD or CLOSE\"",
     "    if False:\n        return \"action must be HOLD or CLOSE\"", ["tests/integration/test_cadence.py"]),
    ("review-paused", "no position is reviewed while trading is paused",
     "aitrader/orchestrator/core.py", "        if reviewer is None or not self._trading_allowed():", "        if reviewer is None:", ["tests/integration/test_cadence.py"]),
    ("minute-time-exit", "a holding time of minutes is honoured between cycles",
     "aitrader/service/runtime.py", "        self.orch.time_exits(now)  # a holding time", "        pass  # a holding time", ["tests/integration/test_cadence.py"]),
    ("review-by-turn", "an open trade is reviewed on its own pair's turn, not every cycle",
     "aitrader/orchestrator/core.py", "            if symbols is not None and row[\"symbol\"] not in symbols:\n                continue",
     "            if False:\n                continue", ["tests/integration/test_cadence.py"]),
    ("history-per-timeframe", "a failing timeframe never erases the history shape another learned",
     "aitrader/broker/tradelocker/history.py", "            self.reset(tf)\n", "            self.reset()\n",
     ["tests/unit/test_history_fetcher.py"]),
    ("history-cooldown", "a timeframe the broker does not serve is not re-probed until the cooldown ends",
     "aitrader/broker/tradelocker/history.py", "        if known is None and blocked:", "        if False:",
     ["tests/unit/test_history_fetcher.py"]),
    ("data-state-honest", "quotes without bars are reported as such, never as CONNECTED",
     "aitrader/service/runtime.py", "        if bars_ok == \"n/a\" or (bars_ok and now - bars_ok < 3 * 3600):",
     "        if True:", ["tests/integration/test_cadence.py"]),
    ("yahoo-forming-bar", "a forming Yahoo bar is never used",
     "aitrader/data/yahoo.py", "        ok &= t + PERIOD_S[tf] <= as_of", "        ok &= t > 0", ["tests/unit/test_yahoo_feed.py"]),
    ("yahoo-quote-own-time", "a Yahoo price carries Yahoo's time, not the time it was fetched",
     "aitrader/data/yahoo.py", "float(px) + half, int(at))", "float(px) + half, int(t))", ["tests/unit/test_yahoo_feed.py"]),
    ("source-unavailable-features", "a feature the source never provides is excluded, not treated as missing data",
     "aitrader/orchestrator/core.py", "        if absent and any(m in absent for m in fv.missing):", "        if False:", ["tests/unit/test_yahoo_feed.py"]),
    ("strict-json", "every response is strict JSON: a NaN becomes null, never an unparseable NaN",
     "aitrader/service/server.py", "json.dumps(_finite(body), default=str, allow_nan=False)", "json.dumps(body, default=str)",
     ["tests/integration/test_service.py"]),
    ("monitor-no-gap", "a stop hit while the team deliberated is still applied",
     "aitrader/service/runtime.py", 'bars = self.feed.bars_tf(s, "M1", now, 60)', 'bars = self.feed.bars_tf(s, "M1", now, 5)',
     ["tests/integration/test_cadence.py"]),
    ("model-not-asked-when-refused", "no model call for a trade the risk engine's account checks already refuse",
     "aitrader/agents/llm_trader.py", "    if ctx.account_blocks:\n", "    if False:\n",
     ["tests/integration/test_cadence.py"]),
    ("account-gates-complete", "the pre-model account checks include every position limit evaluate() applies",
     "aitrader/risk/engine.py", "        out += self._c_positions(account, instrument)\n", "",
     ["tests/unit/test_risk.py", "tests/integration/test_cadence.py"]),
    ("time-exit-label", "a holding-time exit is recorded as TIME",
     "aitrader/execution/engine.py", 'if reason in ("MODEL_EXIT", "TIME") else', 'if reason == "MODEL_EXIT" else',
     ["tests/integration/test_cadence.py"]),
    ("llm-user-agent", "model requests carry their own User-Agent (Cloudflare refuses Python's default)",
     "aitrader/llm/provider.py", '"Content-Type": "application/json", "User-Agent": USER_AGENT}',
     '"Content-Type": "application/json"}', ["tests/unit/test_llm_providers.py"]),
    ("llm-rest-after-refusal", "a model refused for quota or an unknown name rests instead of being asked every minute",
     "aitrader/llm/provider.py", "                self._after(label, last)\n", "", ["tests/unit/test_llm_providers.py"]),
    ("memory-atomic-save", "the live memory is written beside the target and swapped in whole",
     "aitrader/memory/patterns.py", "        os.replace(tmp, path)\n", "        os.replace(tmp, path)\n        path.write_bytes(b'PK')\n",
     ["tests/integration/test_service.py"]),
    ("map-swing-confirmed", "a swing exists only once the bars after it have closed",
     "aitrader/features/market_map.py", "and h[i] >= h[i + 1:i + k + 1].max()]", "]",
     ["tests/unit/test_market_map.py"]),
    ("map-fvg-walk-forward", "a fair value gap that price traded through is not reported",
     "aitrader/features/market_map.py", "        if status != \"filled\":\n", "        if True:\n",
     ["tests/unit/test_market_map.py"]),
    ("intermarket-completed", "intermarket context never uses a forming hour",
     "aitrader/data/yahoo.py", "ok = np.isfinite(c[:n]) & (t[:n] + 3600 <= as_of)", "ok = np.isfinite(c[:n])",
     ["tests/unit/test_yahoo_feed.py"]),
    ("provider-failures-visible", "each AI provider's failures are counted and shown",
     "aitrader/llm/provider.py", "                self._note(ep.name, last)\n", "", ["tests/unit/test_llm_providers.py"]),
    ("room-own-voice", "a mind speaks only through its own provider",
     "aitrader/agents/trading_room.py", "|speak|{len(said)}\", only=m)", "|speak|{len(said)}\", only=None)", ["tests/unit/test_trading_room.py"]),
    ("room-hears-discussion", "each mind reads everything its teammates said before it",
     "aitrader/agents/trading_room.py", "{**packet, \"you\": m, \"discussion\": list(said)}",
     "{**packet, \"you\": m, \"discussion\": []}", ["tests/unit/test_trading_room.py"]),
    ("room-joint-checked", "the team's joint plan is checked and never repaired",
     "aitrader/agents/trading_room.py", "        problem = level_problem(ctx, p)\n        if problem:",
     "        problem = level_problem(ctx, p)\n        if False:", ["tests/unit/test_trading_room.py"]),
    ("room-nothing-seen", "when every mind sees nothing, no joint call is made",
     "aitrader/agents/trading_room.py", "if all(room[\"final\"][m][\"action\"] == \"NO_TRADE\" for m in present):",
     "if False:", ["tests/unit/test_trading_room.py"]),
    ("room-lesson", "a validated lesson blocks the team's trade",
     "aitrader/agents/trading_room.py", "hit = lesson_block(ctx, 1 if p[\"action\"] == \"BUY\" else -1)",
     "hit = None and lesson_block(ctx, 1 if p[\"action\"] == \"BUY\" else -1)", ["tests/unit/test_trading_room.py"]),
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
