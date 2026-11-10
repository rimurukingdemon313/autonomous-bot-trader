"""The discovery lab's runner (docs/DISCOVERY_LAB.md). Research only: nothing here trades.

A discovery scan, registered before it runs (it reads its discovery window only):

    python scripts/dlab.py scan-spec     --dataset energy --run DLAB-ENG-1   # freeze the scan's spec and code hashes
    python scripts/dlab.py scan-register --run DLAB-ENG-1                    # its preregistration must quote both
    python scripts/dlab.py scan-run      --run DLAB-ENG-1                    # once: every rule classed and kept

The validation of the rules a scan found promising, on rows no scan has read, at the registry's bar:

    python scripts/dlab.py spec        --run DLAB-ENG-1    # freeze the batch: each rule, the gates, the bar
    python scripts/dlab.py preregister --run DLAB-ENG-1    # registers DLAB-ENG-1-V
    python scripts/dlab.py judge       --run DLAB-ENG-1    # once

Or both, end to end, with the preregistrations written by the lab itself (what the autonomous worker runs):

    python scripts/dlab.py auto --dataset energy --run DLAB-ENG-1

And what the lab itself can and cannot find, on built markets:

    python scripts/dlab.py oc            # null calibration and the detection curve
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import date, datetime, timezone
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from aitrader.research.dlab import DLAB_VERSION  # noqa: E402
from aitrader.research.dlab import datasets as D  # noqa: E402
from aitrader.research.dlab import methods as M  # noqa: E402
from aitrader.research.dlab import triage as T  # noqa: E402
from aitrader.research.dlab.signals import nw_t, parts_of, pnl, stats  # noqa: E402
from aitrader.research.registry import Holdout, Registry, Trial, Use, Verdict, bonferroni_t  # noqa: E402

R = ROOT / "research"
OUT = R / "knowledge"
LEDGER = R / "dlab" / "candidates.jsonl"
CODE = ("scripts/dlab.py", "aitrader/research/dlab/__init__.py", "aitrader/research/dlab/panel.py",
        "aitrader/research/dlab/signals.py", "aitrader/research/dlab/methods.py", "aitrader/research/dlab/triage.py",
        "aitrader/research/dlab/datasets.py", "scripts/eng1.py")
DATASETS = {"energy": ("energy-futures-eia", D.energy, 5), "crypto": ("crypto-binance-usdtm", D.crypto_hourly, 24)}
MAX_RULES, MAX_SCANNED = 400, 20000  # what a scan may emit and may look at: its charge against its discovery window
RANDOM_N, RANDOM_SEED, BOOT_N, BOOT_SEED, BOOT_BLOCK = 1000, 61, 2000, 67, 20
TOP_YEAR = 0.35
SLOW_ROWS = 3.0  # a rule's mean rows in position per entry, on the check rows, from which the delay is a gate
GATES = {
    "t": "the Newey-West t of the rule's net return over the validation rows >= the threshold",
    "costs_x2": "its mean net return > 0 with every cost doubled",
    "one_row_late": f"its mean net return > 0 entering one row late, for a rule that holds {SLOW_ROWS} rows or more on "
                    "average. For a faster rule the figure is reported and is not a gate: entered a row late, a "
                    "one-row rule is another rule",
    "halves": "its mean net return > 0 in each half of the validation rows",
    "beats_random": f"its mean net return above the 95th percentile of {RANDOM_N} books that hold its own positions "
                    "shifted in time (the same exposure and turnover, no timing)",
    "top_year": f"no calendar year gives more than {TOP_YEAR:.0%} of its total net return",
}


def code_hash() -> str:
    h = hashlib.sha256()
    for p in CODE:
        h.update((ROOT / p).read_bytes())
    return h.hexdigest()


def sha(x) -> str:
    return hashlib.sha256(json.dumps(x, sort_keys=True, default=str).encode()).hexdigest()


def _dump(x) -> str:
    return json.dumps(x, indent=1, sort_keys=True, default=str) + "\n"


def _registry() -> Registry:
    return Registry.load(R / "registry.jsonl", Holdout.load(R / "holdout.json"))


def _write(name: str, body: dict) -> dict:
    body = json.loads(json.dumps(body, sort_keys=True, default=str))
    body["sha256"] = hashlib.sha256(json.dumps(body, sort_keys=True).encode()).hexdigest()
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / f"{name}.json").write_text(_dump(body))
    return body


def _day(x) -> date:
    return x.date() if isinstance(x, datetime) else x


def bar_for(reg: Registry, universe: str, window: tuple, new_tests: int) -> float:
    """The bar a batch of `new_tests` rules must clear on the validation window: Bonferroni over every test already
    counted on that window and the batch, never below 3.0."""
    n = reg.tests_on(universe, _day(window[0]), _day(window[1])) + new_tests
    return max(3.0, bonferroni_t(n))


# ── a discovery scan ───────────────────────────────────────────────────────

def scan_spec(dataset: str, run: str, seed: int, tops: dict | None = None) -> dict:
    universe = DATASETS[dataset][0]
    w = D.WINDOWS[universe]
    return {"program": run, "version": DLAB_VERSION, "kind": "discovery scan", "role": "select", "dataset": dataset,
            "universe": universe, "seed": seed, "windows": {k: [str(v[0]), str(v[1])] for k, v in w.items()},
            "rules_each_method_may_emit": dict(sorted((tops or {}).items())) or "24 each (no record to learn from yet)",
            "methods": ["leadlag", "info", "ordinal", "regimes", "anomaly", "evolve", "combine"],
            "families": list(M.FAMILIES), "classes": list(T.CLASSES),
            "limits": {"rules_emitted": MAX_RULES, "statistics_scanned": MAX_SCANNED},
            "triage": {"same_behaviour_correlation": T.SAME, "least_chance_to_pass": T.P_MIN, "haircut": T.HAIRCUT,
                       "batch": T.MAX_BATCH, "per_family": T.PER_FAMILY, "per_instrument": T.PER_TARGET},
            "firewall": "the panel is loaded with nothing at or after the check rows' end: the validation rows are "
                        "not in memory during discovery",
            "validation": "a separate registration (" + run + "-V): the promising rules, frozen, judged once on the "
                          "validation window at max(3.0, Bonferroni over every test on that window)"}


def cmd_scan_spec(a) -> None:
    reg = _registry()
    if any(t.id == a.run for t in reg.trials):
        raise SystemExit(f"{a.run} is registered; its spec is frozen")
    s = scan_spec(a.dataset, a.run, a.seed)
    (R / "specs").mkdir(parents=True, exist_ok=True)
    (R / "specs" / f"{a.run}.json").write_text(_dump({"spec": s, "sha256": sha(s), "code_sha256": code_hash()}))
    print(sha(s), "code", code_hash())


def _frozen(run: str) -> dict:
    f = json.loads((R / "specs" / f"{run}.json").read_text())
    if sha(f["spec"]) != f["sha256"]:
        raise SystemExit(f"research/specs/{run}.json was edited after it was frozen")
    return f


def cmd_scan_register(a, now: datetime) -> None:
    reg, f = _registry(), _frozen(a.run)
    if code_hash() != f["code_sha256"]:
        raise SystemExit("the code differs from what was frozen")
    doc = f"research/preregistrations/{a.run}.md"
    text = (ROOT / doc).read_text()
    if f["sha256"] not in text or f["code_sha256"] not in text:
        raise SystemExit(f"{doc} must quote the spec and code sha256")
    s = f["spec"]
    w = D.WINDOWS[s["universe"]]
    reg.register(Trial(id=a.run, registered=now, title=f"{a.run}: a discovery scan of {s['universe']} (select)",
                       hypothesis="Which causal rules, found by seven independent methods on the fit rows, are positive "
                                  "on the check rows, distinct, and worth a registered validation?",
                       uses=(Use(s["universe"], _day(w["fit"][0]), _day(w["check"][1]), "select"),),
                       tests=MAX_RULES, configurations=MAX_SCANNED, preregistration=doc,
                       design={"spec_sha256": f["sha256"], "code_sha256": f["code_sha256"]}))
    print("registered", a.run)


def known_rules(universe: str) -> dict:
    """Every rule earlier scans of this market classed: id -> (run, class)."""
    out: dict = {}
    if LEDGER.exists():
        runs = {p.stem: json.loads(p.read_text()).get("universe") for p in OUT.glob("DLAB-*.json")}
        for line in LEDGER.read_text().splitlines():
            r = json.loads(line)
            if "event" not in r and runs.get(r["run"]) == universe and r["class"] != "DUPLICATE":
                out.setdefault(r["id"], (r["run"], r["class"]))
    return out


def scan(dataset: str, seed: int, reg: Registry | None = None, panel=None, tops: dict | None = None) -> dict:
    """One discovery scan: the emitted rules, classed. Reads nothing at or after the check rows' end."""
    universe, loader, _ = DATASETS[dataset]
    w = D.WINDOWS[universe]
    p = panel if panel is not None else loader(w["check"][1])
    if p.times[-1] >= w["validation"][0]:
        raise SystemExit("the discovery panel holds validation rows: refused")
    fit, check = p.rows(*w["fit"]), p.rows(*w["check"])
    ctx = M.Context(p, fit, seed=seed, tops=dict(tops or {}))
    emitted, audit = M.discover(ctx)
    if len(emitted) > MAX_RULES or sum(ctx.scanned.values()) > MAX_SCANNED:
        raise SystemExit(f"the scan emitted {len(emitted)} rules from {sum(ctx.scanned.values())} statistics: over its limits")
    years = (w["validation"][1] - w["validation"][0]).days / 365.25
    bar = bar_for(reg, universe, w["validation"], T.MAX_BATCH) if reg is not None else 3.0
    res = T.triage(emitted, p, fit, check, n_val=p.ppy * years, bar=bar, closed=D.closed(p), hint=D.HINTS.get(universe, ""),
                   known=known_rules(universe) if reg is not None else None)
    return {"universe": universe, "rows": {"panel": p.T, "fit": int(fit.sum()), "check": int(check.sum()),
                                           "validation_expected": int(p.ppy * years)},
            "first_row": str(p.times[0]), "last_row": str(p.times[-1]), "instruments": list(p.assets),
            "scanned": dict(sorted(ctx.scanned.items())), "bar_on_validation": round(bar, 4), "information_audit": audit,
            **res, "summary": T.summary(res["records"])}


def cmd_scan_run(a, now: datetime) -> None:
    reg, f = _registry(), _frozen(a.run)
    if reg.verdict_of(a.run) is not None:
        raise SystemExit(f"{a.run} already has a verdict: a scan runs once")
    if reg.get(a.run).design.get("spec_sha256") != f["sha256"] or code_hash() != f["code_sha256"]:
        raise SystemExit("the spec or the code differs from what was registered")
    s = f["spec"]
    res = scan(s["dataset"], s["seed"], reg)
    verdict = "PASSED" if res["batch"] else "FAILED"
    body = _write(a.run, {"program": a.run, "kind": "discovery_scan", "verdict": verdict, "spec_sha256": f["sha256"],
                          "code_sha256": f["code_sha256"], "windows": s["windows"],
                          "meaning": ("the batch goes to a registered validation" if res["batch"] else
                                      "no rule is worth a registered validation; every rule is kept with its class"),
                          **res})
    T.append(LEDGER, a.run, res["records"], now.isoformat(), DLAB_VERSION)
    reg.record_verdict(Verdict(a.run, now, verdict, {"artifact": f"research/knowledge/{a.run}.json",
                                                      "artifact_sha256": body["sha256"], "rules": len(res["records"]),
                                                      "batch": res["batch"]}))
    print(json.dumps({"run": a.run, "verdict": verdict, "summary": res["summary"], "noise": res["noise"],
                      "batch": res["batch"], "scanned": res["scanned"]}, indent=1))


# ── the validation of a batch ──────────────────────────────────────────────

def _shifted_mean(spec: dict, p, vmask: np.ndarray, offset: int, k: float = 1.0) -> float:
    """The mean net return on the validation rows of the rule's own positions moved `offset` rows in time."""
    means = []
    for part in parts_of(spec):
        j = p.col(part["target"])
        fwd = p.fwd()[:, j]
        rows = np.nonzero(vmask & np.isfinite(fwd))[0]
        pos = np.roll(np.nan_to_num(pnl(part, p)["pos"][rows]), offset)
        turn = np.abs(pos - np.concatenate([[0.0], pos[:-1]]))
        net = pos * fwd[rows] - k * (p.cost[part["target"]] * turn + p.hold_cost[rows, j] * np.abs(pos))
        means.append(float(net.mean()) if len(net) else 0.0)
    return float(np.mean(means))


def mean_hold(rec: dict) -> float:
    """A rule's mean rows in position per entry on the check rows: known before its validation."""
    return round((rec["check"]["in_position"] or 0) / max(rec["check"]["entries"] or 1, 1), 2)


def judge_rule(spec: dict, p, vmask: np.ndarray, bar: float, lags: int, delay_gate: bool = True) -> dict:
    """One rule on the validation rows: every figure the report needs, and its gates."""
    r = pnl(spec, p)
    net = np.where(vmask, r["net"], np.nan)
    s = stats(net, vmask, p.ppy, r["pos"])
    v = net[np.isfinite(net)]
    t = nw_t(net, lags)
    x2 = stats(pnl(spec, p, k=2.0)["net"], vmask, p.ppy)["mean"]
    late = stats(pnl(spec, p, delay=1)["net"], vmask, p.ppy)["mean"]
    rows = np.nonzero(vmask & np.isfinite(r["net"]))[0]
    half = rows[len(rows) // 2] if len(rows) else 0
    idx = np.arange(p.T)
    halves = [stats(net, vmask & (idx < half), p.ppy)["mean"], stats(net, vmask & (idx >= half), p.ppy)["mean"]]
    rng = np.random.default_rng(RANDOM_SEED)
    n = len(rows)
    rnd = np.array([_shifted_mean(spec, p, vmask, int(o)) for o in rng.integers(20, max(n - 20, 21), size=RANDOM_N)])
    actual = _shifted_mean(spec, p, vmask, 0)
    by_year: dict = {}
    for i in rows:
        y = str(p.times[i])[:4]
        by_year[y] = by_year.get(y, 0.0) + float(r["net"][i])
    total = float(sum(by_year.values()))
    top = max(by_year.values()) / total if total > 0 else None
    cum = np.cumsum(v)
    fall = float((np.maximum.accumulate(cum) - cum).max()) if len(cum) else 0.0
    brng = np.random.default_rng(BOOT_SEED)
    blocks = max(1, len(v) // BOOT_BLOCK)
    starts = brng.integers(0, max(len(v) - BOOT_BLOCK, 1), size=(BOOT_N, blocks))
    boot = np.array([np.concatenate([v[i:i + BOOT_BLOCK] for i in row]).mean() for row in starts]) if len(v) > BOOT_BLOCK else np.array([0.0])
    gross = stats(np.where(vmask, r["gross"], np.nan), vmask, p.ppy)["mean"]
    gates = {"t": t is not None and t >= bar, "costs_x2": (x2 or 0) > 0,
             "halves": all((h or 0) > 0 for h in halves), "beats_random": actual > float(np.percentile(rnd, 95)),
             "top_year": top is not None and top <= TOP_YEAR}
    if delay_gate:
        gates["one_row_late"] = (late or 0) > 0
    years = len(v) / p.ppy if len(v) else 0.0

    def rd(x, k=6):
        return None if x is None else round(float(x), k)
    return {"rows": s["n"], "mean": rd(s["mean"], 8), "gross_mean": rd(gross, 8),
            "costs_mean": rd((gross or 0) - (s["mean"] or 0), 8), "a_year_pct": rd((s["mean"] or 0) * p.ppy * 100, 3),
            "t": rd(t, 3), "t_plain": rd(s["t"], 3), "sharpe": rd(s["sharpe"], 3), "bar": round(bar, 4),
            "bootstrap_95": [rd(np.percentile(boot, 2.5), 8), rd(np.percentile(boot, 97.5), 8)],
            "worst_fall_pct": rd(fall * 100, 2), "exposure": rd(s.get("exposure"), 4),
            "entries_a_year": rd(s.get("entries", 0) / years, 1) if years else None,
            "costs_x2_mean": rd(x2, 8), "one_row_late_mean": rd(late, 8), "half_means": [rd(h, 8) for h in halves],
            "random": {"books": RANDOM_N, "p95": rd(np.percentile(rnd, 95), 8), "mean": rd(rnd.mean(), 8),
                       "share_at_least_as_good": rd(float((rnd >= actual).mean()), 4)},
            "top_year_share": rd(top, 3), "by_year": {y: rd(x, 5) for y, x in sorted(by_year.items())},
            "gates": gates, "failed_gates": [g for g, ok in gates.items() if not ok], "passed": all(gates.values())}


def batch_spec(run: str, reg: Registry) -> dict:
    art = json.loads((OUT / f"{run}.json").read_text())
    if not art["batch"]:
        raise SystemExit(f"{run} proposed no rule for validation")
    by_id = {r["id"]: r for r in art["records"]}
    scan_s = _frozen(run)["spec"]
    w = D.WINDOWS[art["universe"]]
    rules = [{"id": i, "family": by_id[i]["family"], "why": by_id[i]["why"], "rule": by_id[i]["rule"],
              "spec": by_id[i]["spec"], "estimated_chance_to_pass": by_id[i]["power"]["p_pass"],
              "mean_hold_rows": mean_hold(by_id[i]), "delay_is_a_gate": mean_hold(by_id[i]) >= SLOW_ROWS}
             for i in art["batch"]]
    return {"program": f"{run}-V", "version": DLAB_VERSION, "kind": "discovery validation", "role": "judge",
            "scan": run, "scan_artifact_sha256": art["sha256"], "dataset": scan_s["dataset"], "universe": art["universe"],
            "validation_window": [str(w["validation"][0]), str(w["validation"][1])], "rules": rules,
            "newey_west_lags": DATASETS[scan_s["dataset"]][2], "gates": GATES,
            "random": {"books": RANDOM_N, "seed": RANDOM_SEED}, "bootstrap": {"n": BOOT_N, "seed": BOOT_SEED, "block_rows": BOOT_BLOCK},
            "threshold_t": round(bar_for(reg, art["universe"], w["validation"], len(rules)), 4),
            "verdict_rule": "each rule is judged on its own: it passes only if every gate holds. The trial PASSES if at "
                            "least one rule passes",
            "after": "a rule that passes is a candidate for the owner and for a forward paper test; it trades only on "
                     "the owner's word, on paper, through the risk engine, the hard gate and the paper broker"}


def cmd_spec(a) -> None:
    reg, pid = _registry(), f"{a.run}-V"
    if any(t.id == pid for t in reg.trials):
        raise SystemExit(f"{pid} is registered; its spec is frozen")
    s = batch_spec(a.run, reg)
    (R / "specs" / f"{pid}.json").write_text(_dump({"spec": s, "sha256": sha(s), "code_sha256": code_hash()}))
    print(sha(s), "code", code_hash(), "threshold", s["threshold_t"], "rules", len(s["rules"]))


def cmd_preregister(a, now: datetime) -> None:
    reg, pid = _registry(), f"{a.run}-V"
    f = _frozen(pid)
    if sha(batch_spec(a.run, reg)) != f["sha256"] or code_hash() != f["code_sha256"]:
        raise SystemExit("the spec or the code differs from what was frozen")
    doc = f"research/preregistrations/{pid}.md"
    text = (ROOT / doc).read_text()
    if f["sha256"] not in text or f["code_sha256"] not in text:
        raise SystemExit(f"{doc} must quote the spec and code sha256")
    s = f["spec"]
    w = D.WINDOWS[s["universe"]]
    reg.register(Trial(id=pid, registered=now, title=f"{pid}: {len(s['rules'])} rules of {a.run} on the validation window",
                       hypothesis="Does any rule the discovery scan found promising earn a positive net return on rows "
                                  "the scan never read, at the registry's bar?",
                       uses=(Use(s["universe"], _day(w["validation"][0]), _day(w["validation"][1]), "judge"),),
                       tests=len(s["rules"]), configurations=len(s["rules"]), preregistration=doc,
                       design={"spec_sha256": f["sha256"], "code_sha256": f["code_sha256"], "threshold_t": s["threshold_t"]}))
    print("registered", pid)


def cmd_judge(a, now: datetime) -> None:
    reg, pid = _registry(), f"{a.run}-V"
    if reg.verdict_of(pid) is not None:
        raise SystemExit(f"{pid} already has a verdict")
    f = _frozen(pid)
    if reg.get(pid).design.get("spec_sha256") != f["sha256"] or code_hash() != f["code_sha256"]:
        raise SystemExit("the spec or the code differs from what was registered")
    s = f["spec"]
    w = D.WINDOWS[s["universe"]]
    p = DATASETS[s["dataset"]][1](w["validation"][1])
    vmask = p.rows(*w["validation"])
    results = [{"id": r["id"], "family": r["family"], "rule": r["rule"], "why": r["why"],
                **judge_rule(r["spec"], p, vmask, s["threshold_t"], s["newey_west_lags"], r["delay_is_a_gate"])}
               for r in s["rules"]]
    passed = [r["id"] for r in results if r["passed"]]
    verdict = "PASSED" if passed else "FAILED"
    body = _write(pid, {"program": pid, "kind": "discovery_validation", "verdict": verdict, "scan": a.run,
                        "spec_sha256": f["sha256"], "code_sha256": f["code_sha256"], "threshold_t": s["threshold_t"],
                        "validation_window": s["validation_window"], "validation_rows": int(vmask.sum()),
                        "results": results, "passed_rules": passed})
    with open(LEDGER, "a") as fh:
        fh.write("".join(json.dumps({"run": a.run, "event": "VALIDATION", "trial": pid, "id": r["id"], "at": now.isoformat(),
                                     "class": "VALIDATED_ON_UNREAD_ROWS" if r["passed"] else "REJECTED_BY_VALIDATION",
                                     "reason": ("every gate held" if r["passed"] else "failed: " + ", ".join(r["failed_gates"])),
                                     "t": r["t"], "mean": r["mean"], "bar": r["bar"]}, sort_keys=True) + "\n" for r in results))
    reg.record_verdict(Verdict(pid, now, verdict, {"artifact": f"research/knowledge/{pid}.json",
                                                    "artifact_sha256": body["sha256"], "passed_rules": passed}))
    for r in results:
        print(f"{r['id']} {'PASSED' if r['passed'] else 'FAILED'} t {r['t']} vs {r['bar']} mean {r['mean']} "
              f"a year {r['a_year_pct']}% failed {r['failed_gates']} | {r['rule'][:70]}")
    print(pid, verdict)


# ── preregistrations written by the lab itself, and the two steps run end to end ──

def prereg_scan_doc(run: str, f: dict, day: str) -> str:
    s = f["spec"]
    w = s["windows"]
    return "\n".join([
        f"# {run}: a discovery scan of {s['universe']} (preregistration)", "",
        f"**Written {day} by the discovery lab, before the scan ran.** Research only: nothing here trades.", "",
        f"- Spec sha256: `{f['sha256']}` (`research/specs/{run}.json`)",
        f"- Code sha256: `{f['code_sha256']}` (the lab: `scripts/dlab.py`, `aitrader/research/dlab/`)",
        "- Protocol: `docs/DISCOVERY_LAB.md`", "",
        "## What a scan does", "",
        "It asks significance of nothing. Seven independent methods read the fit rows and emit their strongest rules: "
        "lead-lag with a causal screen, information theory, ordinal patterns, regimes by clustering, anomalies, an "
        "evolutionary search, and combinations across families. Each rule is then evaluated once on the check rows, "
        "which no method read, and classed with its reason. Every rule is kept in `research/dlab/candidates.jsonl`.", "",
        "## The rows", "", "| Rows | From | To (exclusive) | Use |", "|---|---|---|---|",
        f"| Fit | {w['fit'][0]} | {w['fit'][1]} | the methods read these and nothing later |",
        f"| Check | {w['check'][0]} | {w['check'][1]} | each emitted rule is evaluated here once |",
        f"| Validation | {w['validation'][0]} | {w['validation'][1]} | **not loaded.** Read once, by `{run}-V`, if a rule is promising |",
        "", "## What is counted", "",
        f"- The scan is charged {s['limits']['rules_emitted']} tests and {s['limits']['statistics_scanned']} configurations "
        "against its fit and check rows (role select), its limits on what it may emit and look at. Those rows can no "
        "longer judge anything at an ordinary bar: they are a discovery set.",
        "- The validation rows are charged only for the rules later judged on them.", "",
        "## What follows", "",
        f"- At most {s['triage']['batch']} rules classed PROMISING_UNCONFIRMED (at most {s['triage']['per_family']} a family "
        f"and {s['triage']['per_instrument']} an instrument) go to `{run}-V`: frozen, and judged once on the validation "
        "rows at max(3.0, Bonferroni over every test on those rows).",
        "- The scan's verdict is PASSED if it proposes such a batch and FAILED if it does not. Neither is a result about "
        "any rule: no rule is validated or disproved by a scan.", ""])


def prereg_batch_doc(run: str, f: dict, day: str, earlier: int) -> str:
    s = f["spec"]
    out = [f"# {s['program']}: {len(s['rules'])} rules of {run} on the validation rows (preregistration)", "",
           f"**Written {day} by the discovery lab, before any validation row was loaded.** Research only: nothing here "
           "trades.", "",
           f"- Spec sha256: `{f['sha256']}` (`research/specs/{s['program']}.json`)",
           f"- Code sha256: `{f['code_sha256']}`",
           f"- The scan's evidence: `research/knowledge/{run}.json` (sha256 `{s['scan_artifact_sha256']}`)", "",
           "## The question", "",
           f"Does any rule that the scan `{run}` found promising earn a positive net return on rows the scan never read "
           f"({s['validation_window'][0]} to {s['validation_window'][1]}), at the registry's bar?", "",
           "## The rules (frozen: nothing is refitted)", "",
           "| Rule | Family | What it does | Why it might hold | Mean rows held | Chance to pass, estimated |", "|---|---|---|---|---|---|"]
    out += [f"| `{r['id']}` | {r['family']} | {r['rule'][:300]} | {r['why'][:200]} | {r['mean_hold_rows']} | "
            f"{r['estimated_chance_to_pass']:.0%} |" for r in s["rules"]]
    out += ["", "The estimated chances come from the discovery rows. They are overstated when the market holds nothing: "
            "the test below is what counts.", "",
            "## The test (each rule judged once, on its own)", "", "| Gate | Rule |", "|---|---|"]
    out += [f"| {g} | {text} |" for g, text in s["gates"].items()]
    out += ["", f"**Threshold: t >= {s['threshold_t']}.** The validation rows carry {earlier} earlier tests in the registry; "
            f"with these {len(s['rules'])}, Bonferroni gives {bonferroni_t(earlier + len(s['rules'])):.3f}, and the "
            "floor is 3.0.", "",
            f"The t is Newey-West with {s['newey_west_lags']} lags. Also reported for each rule: the mean, the gross "
            "mean and the costs, the Sharpe ratio, a block-bootstrap 95% interval, the worst fall, the exposure, the "
            "entries a year, and each year.", "",
            "## What follows", "",
            "- A rule that fails is REJECTED_BY_VALIDATION, and its family is closed on these rows.",
            "- " + s["after"][0].upper() + s["after"][1:] + ".", ""]
    return "\n".join(out)


def auto_scan(dataset: str, run: str, seed: int, now: datetime, panel=None, tops: dict | None = None) -> dict:
    """A whole discovery scan: freeze, write its preregistration, register, run once, record. Resumes where a crash
    left it: a scan that is registered but has no verdict is run, not registered again."""
    reg = _registry()
    spec_path, doc = R / "specs" / f"{run}.json", ROOT / "research" / "preregistrations" / f"{run}.md"
    if not any(t.id == run for t in reg.trials):
        s = scan_spec(dataset, run, seed, tops)
        spec_path.parent.mkdir(parents=True, exist_ok=True)
        spec_path.write_text(_dump({"spec": s, "sha256": sha(s), "code_sha256": code_hash()}))
        f = _frozen(run)
        doc.parent.mkdir(parents=True, exist_ok=True)
        doc.write_text(prereg_scan_doc(run, f, f"{now:%Y-%m-%d}"))
        cmd_scan_register(argparse.Namespace(run=run), now)
        reg = _registry()
    if reg.verdict_of(run) is not None:
        return json.loads((OUT / f"{run}.json").read_text())
    f = _frozen(run)
    if reg.get(run).design.get("spec_sha256") != f["sha256"] or code_hash() != f["code_sha256"]:
        raise SystemExit(f"{run}: the spec or the code differs from what was registered")
    limits = f["spec"]["rules_each_method_may_emit"]
    res = scan(f["spec"]["dataset"], f["spec"]["seed"], reg, panel, limits if isinstance(limits, dict) else None)
    verdict = "PASSED" if res["batch"] else "FAILED"
    body = _write(run, {"program": run, "kind": "discovery_scan", "verdict": verdict, "spec_sha256": f["sha256"],
                        "code_sha256": f["code_sha256"], "windows": f["spec"]["windows"],
                        "meaning": ("the batch goes to a registered validation" if res["batch"] else
                                    "no rule is worth a registered validation; every rule is kept with its class"),
                        **res})
    T.append(LEDGER, run, res["records"], now.isoformat(), DLAB_VERSION)
    reg.record_verdict(Verdict(run, now, verdict, {"artifact": f"research/knowledge/{run}.json",
                                                    "artifact_sha256": body["sha256"], "rules": len(res["records"]),
                                                    "batch": res["batch"]}))
    return body


def same_rules(run: str, art: dict) -> None:
    """Before a batch is frozen: each of its rules, recomputed by today's code on the DISCOVERY rows, must give the
    check-row figure the scan recorded. Code that has changed since the scan may not quietly turn a rule into another
    one. No validation row is loaded."""
    f = _frozen(run)["spec"]
    w = D.WINDOWS[art["universe"]]
    p = DATASETS[f["dataset"]][1](w["check"][1])
    check = p.rows(*w["check"])
    for r in art["records"]:
        if r["id"] in art["batch"]:
            t = stats(pnl(r["spec"], p)["net"], check, p.ppy)["t"]
            if t is None or abs(t - r["check"]["t"]) > 2e-3:
                raise SystemExit(f"{run}: today's code no longer computes rule {r['id']} as the scan did "
                                 f"(check-row t {t} against {r['check']['t']}): its batch is not registered")


def auto_validate(run: str, now: datetime) -> dict | None:
    """The validation of a scan's batch, end to end: freeze, write its preregistration, register, judge once. None if
    the scan proposed nothing. Resumes after a crash: registered without a verdict means judge."""
    art = json.loads((OUT / f"{run}.json").read_text())
    if not art["batch"]:
        return None
    reg, pid = _registry(), f"{run}-V"
    if not any(t.id == pid for t in reg.trials):
        same_rules(run, art)
        s = batch_spec(run, reg)
        (R / "specs" / f"{pid}.json").write_text(_dump({"spec": s, "sha256": sha(s), "code_sha256": code_hash()}))
        f = _frozen(pid)
        w = D.WINDOWS[s["universe"]]["validation"]
        (ROOT / "research" / "preregistrations" / f"{pid}.md").write_text(
            prereg_batch_doc(run, f, f"{now:%Y-%m-%d}", reg.tests_on(s["universe"], _day(w[0]), _day(w[1]))))
        cmd_preregister(argparse.Namespace(run=run), now)
        reg = _registry()
    if reg.verdict_of(pid) is None:
        cmd_judge(argparse.Namespace(run=run), now)
    return json.loads((OUT / f"{pid}.json").read_text())


# ── what the lab can and cannot find ───────────────────────────────────────

def operating_characteristic(seeds: int = 12, rows: int = 7500) -> dict:
    """On built markets shaped like a daily panel (three instruments; ten years of fit rows, eight of check rows and
    twelve of validation rows): how often a scan promotes anything when there is nothing to find, and how often it
    promotes, and then validates, a planted structure of a given size."""
    fit_n, chk_n = 2500, 2000
    plants = [("nothing", None)]
    for ic in (0.03, 0.05, 0.08, 0.12):
        plants.append((f"lead-lag, correlation {ic}", {"leadlag": ic}))
    plants += [("U-shape 0.15 (no linear trace)", {"ushape": 0.15}), ("regime drift 0.06", {"regime": 0.06}),
               ("shock reversal 0.5", {"shock": 0.5})]
    out = []
    for label, plant in plants:
        promoted = validated = false_valid = rules = 0
        hits = []
        for seed in range(seeds):
            p = D.synthetic(rows=rows, seed=100 + seed, plant=plant)
            head = p.head(fit_n + chk_n)
            fit = np.zeros(head.T, dtype=bool)
            fit[:fit_n] = True
            ctx = M.Context(head, fit, seed=7)
            emitted, _ = M.discover(ctx)
            n_val = rows - fit_n - chk_n
            res = T.triage(emitted, head, fit, ~fit, n_val=n_val, bar=3.0)
            rules += len(res["records"])
            by_id = {r["id"]: r for r in res["records"]}
            vmask = np.zeros(p.T, dtype=bool)
            vmask[fit_n + chk_n:] = True
            ok_any = False
            for i in res["batch"]:
                j = judge_rule(by_id[i]["spec"], p, vmask, 3.0, 5, mean_hold(by_id[i]) >= SLOW_ROWS)
                real = plant is not None and "A1" in by_id[i]["targets"]
                ok_any |= j["passed"] and real
                false_valid += j["passed"] and not real
            promoted += bool(res["batch"])
            validated += ok_any
            hits.append(len(res["batch"]))
        out.append({"market": label, "runs": seeds, "runs_with_a_promoted_rule": promoted,
                    "runs_with_the_planted_rule_validated": validated if plant else None,
                    "validated_rules_that_were_noise": false_valid, "mean_rules_per_run": round(rules / seeds, 1),
                    "promoted_per_run": hits})
        print(json.dumps(out[-1]), flush=True)
    return {"version": DLAB_VERSION, "rows": {"fit": fit_n, "check": chk_n, "validation": rows - fit_n - chk_n},
            "note": "a lead-lag correlation c gives a linear rule a gross Sharpe ratio of about c x sqrt(252) a year",
            "results": out}


def cmd_oc(a) -> None:
    res = operating_characteristic(a.seeds)
    (R / "dlab").mkdir(parents=True, exist_ok=True)
    (R / "dlab" / "operating_characteristic.json").write_text(_dump(res))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("cmd", choices=["scan-spec", "scan-register", "scan-run", "spec", "preregister", "judge", "oc",
                                    "auto"])
    ap.add_argument("--dataset", choices=sorted(DATASETS), default="energy")
    ap.add_argument("--run", default="")
    ap.add_argument("--seed", type=int, default=7)
    ap.add_argument("--seeds", type=int, default=12)
    a = ap.parse_args()
    now = datetime.now(timezone.utc).replace(microsecond=0)
    if a.cmd != "oc" and not a.run:
        ap.error("--run is required")
    {"scan-spec": lambda: cmd_scan_spec(a), "scan-register": lambda: cmd_scan_register(a, now),
     "scan-run": lambda: cmd_scan_run(a, now), "spec": lambda: cmd_spec(a), "preregister": lambda: cmd_preregister(a, now),
     "judge": lambda: cmd_judge(a, now), "oc": lambda: cmd_oc(a),
     "auto": lambda: (auto_scan(a.dataset, a.run, a.seed, now), auto_validate(a.run, now))}[a.cmd]()
    return 0


__all__ = ["auto_scan", "auto_validate", "bar_for", "batch_spec", "code_hash", "judge_rule", "mean_hold",
           "operating_characteristic", "prereg_batch_doc", "prereg_scan_doc", "same_rules", "scan", "scan_spec"]

if __name__ == "__main__":
    raise SystemExit(main())
