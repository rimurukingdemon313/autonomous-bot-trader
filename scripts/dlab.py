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
import re
import sys
from datetime import date, datetime, timezone
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from aitrader.research.dlab import DLAB_VERSION, SCAN_VERSION  # noqa: E402
from aitrader.research.dlab import datasets as D  # noqa: E402
from aitrader.research.dlab import methods as M  # noqa: E402
from aitrader.research.dlab import triage as T  # noqa: E402
from aitrader.research.dlab.signals import (  # noqa: E402
    KINDS, causal, describe, nw_t, parts_of, pnl, spec_id, stats, targets, weights)
from aitrader.research.registry import Holdout, Registry, Trial, Use, Verdict, bonferroni_t  # noqa: E402

R = ROOT / "research"
OUT = R / "knowledge"
LEDGER = R / "dlab" / "candidates.jsonl"
CODE = ("scripts/dlab.py", "aitrader/research/dlab/__init__.py", "aitrader/research/dlab/panel.py",
        "aitrader/research/dlab/signals.py", "aitrader/research/dlab/methods.py", "aitrader/research/dlab/triage.py",
        "aitrader/research/dlab/datasets.py", "aitrader/research/dlab/feeds.py", "scripts/eng1.py")
#: dataset -> (universe, loader, Newey-West lags)
DATASETS = {"energy": ("energy-futures-eia", D.energy, 5), "crypto": ("crypto-binance-usdtm", D.crypto_hourly, 24),
            "crypto-daily": ("crypto-perp-daily", D.crypto_daily, 5), "etf-daily": ("us-etf-broad-daily", D.etf_daily, 5)}
#: what a scan may emit and may look at: its charge against its discovery window (DLAB-ENG-1, under 1.0.0: 400, 20000)
MAX_RULES, MAX_SCANNED = 600, 100000
RANDOM_N, RANDOM_SEED, BOOT_N, BOOT_SEED, BOOT_BLOCK = 1000, 61, 2000, 67, 20
TOP_YEAR = 0.35
TOP_YEAR_SE = 2.0  # in a short window: a year may give its share of the rows plus this many standard errors of it
SLOW_ROWS = 3.0  # a rule's mean rows in position per entry, on the check rows, from which the delay is a gate
MAX_GAP_DAYS = 5  # a panel holds a whole validation window if it ends within these days of it: a weekend and a holiday
GATES = {
    "t": "the Newey-West t of the rule's net return over the validation rows >= the threshold",
    "costs_x2": "its mean net return > 0 with every cost doubled",
    "one_row_late": f"its mean net return > 0 entering one row late, for a rule that holds {SLOW_ROWS} rows or more on "
                    "average. For a faster rule the figure is reported and is not a gate: entered a row late, a "
                    "one-row rule is another rule",
    "halves": "its mean net return > 0 in each half of the validation rows",
    "beats_random": f"its mean net return above the 95th percentile of {RANDOM_N} books that hold its own positions "
                    "shifted in time (the same exposure and turnover, no timing)",
    "top_year": f"no calendar year gives more than {TOP_YEAR:.0%} of its total net return; or, where a year holds so "
                "many of the window's rows that this cannot be asked, more than the year's share of the rows plus two "
                "standard errors of that share for a rule at t 3.0",
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


def covers(p, window: tuple) -> str | None:
    """Why a panel does not hold a whole validation window, or None. A batch is judged once: on data that stop early
    it would be judged on fewer rows than were registered, and could never be judged again."""
    gap = (_day(window[1]) - _day(p.times[-1])).days
    if gap <= MAX_GAP_DAYS:
        return None
    return f"the panel ends on {_day(p.times[-1])}, {gap} days before its validation window does ({_day(window[1])})"


def tests_counted(reg: Registry, universe: str, window: tuple) -> int:
    """Every test the registry holds on a window of this market: the universe's own, and those of the universes that
    read the same market's returns under another name (datasets.RELATED)."""
    return sum(reg.tests_on(u, _day(window[0]), _day(window[1])) for u in (universe, *D.RELATED.get(universe, ())))


def year_cap(share_of_rows: float) -> float:
    """The most of a rule's total net return one calendar year may give. A year that holds a share s of the rows of a
    rule whose total stands at t 3.0 gives s of the total, give or take sqrt(s (1 - s)) / 3: two of those above s is
    allowed, and never less than 35%. Over a twelve-year window that is 35%; in a window of two or three years a year
    holds a third or more of the rows, and a flat 35% would fail a steady rule for the window's shortness."""
    s_ = min(max(share_of_rows, 0.0), 1.0)
    return max(TOP_YEAR, s_ + TOP_YEAR_SE * float(np.sqrt(s_ * (1.0 - s_))) / 3.0)


def free_places(reg: Registry, universe: str, window: tuple) -> int:
    """How many rules a batch may hold while the validation bar stays at its floor of 3.0: a place among those costs
    the bar nothing, so a positive rule may take one without being promising."""
    n, k = tests_counted(reg, universe, window), 0
    while k < T.MAX_BATCH and bonferroni_t(n + k + 1) <= 3.0:
        k += 1
    return k


def bar_for(reg: Registry, universe: str, window: tuple, new_tests: int) -> float:
    """The bar a batch of `new_tests` rules must clear on the validation window: Bonferroni over every test already
    counted on that window and the batch, never below 3.0."""
    return max(3.0, bonferroni_t(tests_counted(reg, universe, window) + new_tests))


# ── a discovery scan ───────────────────────────────────────────────────────

def scan_spec(dataset: str, run: str, seed: int, tops: dict | None = None) -> dict:
    universe = DATASETS[dataset][0]
    w = D.WINDOWS[universe]
    return {"program": run, "version": SCAN_VERSION, "kind": "discovery scan", "role": "select", "dataset": dataset,
            "universe": universe, "seed": seed, "windows": {k: [str(v[0]), str(v[1])] for k, v in w.items()},
            "rules_each_method_may_emit": dict(sorted((tops or {}).items())) or "24 each (no record to learn from yet)",
            "methods": ["leadlag", "info", "ordinal", "regimes", "anomaly", "evolve", "breadth", "combine"],
            "related_universes": list(D.RELATED.get(universe, ())),
            "families": list(M.FAMILIES), "classes": list(T.CLASSES),
            "limits": {"rules_emitted": MAX_RULES, "statistics_scanned": MAX_SCANNED},
            "triage": {"same_behaviour_correlation": T.SAME, "least_chance_to_pass": T.P_MIN,
                       "least_chance_for_a_place_that_costs_the_bar_nothing": T.P_FREE, "haircut": T.HAIRCUT,
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
                       hypothesis="Which causal rules, found by the lab's independent methods on the fit rows, are "
                                  "positive on the check rows, distinct, and worth a registered validation?",
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


def earlier_looks(universe: str) -> int:
    """The distinct behaviours earlier scans evaluated on this market's check rows."""
    arts = [json.loads(p.read_text()) for p in OUT.glob("DLAB-*.json")] if OUT.exists() else []
    return sum(a["noise"]["distinct_behaviours"] - a["noise"].get("of_them_from_earlier_scans", 0)
               for a in arts if a.get("kind") in ("discovery_scan", "directed_test") and a.get("universe") == universe)


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
                   known=known_rules(universe) if reg is not None else None,
                   prior_looks=earlier_looks(universe) if reg is not None else 0,
                   free_places=free_places(reg, universe, w["validation"]) if reg is not None else 0)
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

def _shifted_means(spec: dict, p, vmask: np.ndarray, offsets, k: float = 1.0) -> np.ndarray:
    """For each offset: the mean net return on the validation rows of the rule's own positions moved that many rows in
    time (each part on its own priced rows, the parts averaged: by their shares, where the book has them)."""
    legs, shares = [], weights(spec)
    for part in parts_of(spec):
        j = p.col(part["target"])
        fwd = p.fwd()[:, j]
        rows = np.nonzero(vmask & np.isfinite(fwd))[0]
        legs.append((np.nan_to_num(pnl(part, p)["pos"][rows]), fwd[rows], p.cost[part["target"]], p.hold_cost[rows, j]))
    out = []
    for o in offsets:
        means = []
        for pos0, f, c, h in legs:
            pos = np.roll(pos0, int(o))
            turn = np.abs(pos - np.concatenate([[0.0], pos[:-1]]))
            net = pos * f - k * (c * turn + h * np.abs(pos))
            means.append(float(net.mean()) if len(net) else 0.0)
        out.append(float(np.mean(means)) if shares is None else float(np.dot(shares, means)))
    return np.asarray(out)


def mean_hold(rec: dict) -> float:
    """A rule's mean rows in position per entry on the check rows: known before its validation."""
    c = rec["check"]
    return c["mean_hold"] if "mean_hold" in c else round((c["in_position"] or 0) / max(c["entries"] or 1, 1), 2)


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
    rnd = _shifted_means(spec, p, vmask, rng.integers(20, max(n - 20, 21), size=RANDOM_N))
    actual = float(_shifted_means(spec, p, vmask, [0])[0])
    by_year, n_year = {}, {}
    for i in rows:
        y = str(p.times[i])[:4]
        by_year[y], n_year[y] = by_year.get(y, 0.0) + float(r["net"][i]), n_year.get(y, 0) + 1
    total = float(sum(by_year.values()))
    top = max(by_year.values()) / total if total > 0 else None
    spread = total > 0 and all(v / total <= year_cap(n_year[y] / len(rows)) for y, v in by_year.items())
    cum = np.cumsum(v)
    fall = float((np.maximum.accumulate(cum) - cum).max()) if len(cum) else 0.0
    brng = np.random.default_rng(BOOT_SEED)
    blocks = max(1, len(v) // BOOT_BLOCK)
    starts = brng.integers(0, max(len(v) - BOOT_BLOCK, 1), size=(BOOT_N, blocks))
    boot = np.array([np.concatenate([v[i:i + BOOT_BLOCK] for i in row]).mean() for row in starts]) if len(v) > BOOT_BLOCK else np.array([0.0])
    gross = stats(np.where(vmask, r["gross"], np.nan), vmask, p.ppy)["mean"]
    gates = {"t": t is not None and t >= bar, "costs_x2": (x2 or 0) > 0,
             "halves": all((h or 0) > 0 for h in halves), "beats_random": actual > float(np.percentile(rnd, 95)),
             "top_year": bool(spread)}
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
            "rows_by_year": dict(sorted(n_year.items())),
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
    short = covers(p, w["validation"])
    if short:
        raise SystemExit(f"{pid}: {short}: nothing is judged until the data hold the whole window")
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
        "It asks significance of nothing. Independent methods read the fit rows and emit their strongest rules: "
        "lead-lag with a causal screen, information theory, ordinal patterns, regimes by clustering, anomalies, an "
        "evolutionary search, combinations across families and, on a broad panel, rules traded on every instrument "
        "at once (cross-sectional books and pooled rules). Each rule is then evaluated once on the check rows, which "
        "no method read, and classed with its reason. Every rule is kept in `research/dlab/candidates.jsonl`.", "",
        f"Instruments and data: dataset `{s['dataset']}` (`aitrader/research/dlab/datasets.py`). The validation "
        "window's bar also counts the earlier tests on: " + (", ".join(s.get("related_universes") or []) or "no other universe") + ".", "",
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
        f"- At most {s['triage']['batch']} rules (at most {s['triage']['per_family']} a family and "
        f"{s['triage']['per_instrument']} an instrument) go to `{run}-V`: frozen, and judged once on the validation "
        "rows at max(3.0, Bonferroni over every test on those rows). They are the rules classed "
        "PROMISING_UNCONFIRMED and, while the bar with them added is still 3.0, the next strongest rules that are "
        "positive in both halves of the check rows: a place that costs the bar nothing is not withheld.",
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
            prereg_batch_doc(run, f, f"{now:%Y-%m-%d}", tests_counted(reg, s["universe"], w)))
        cmd_preregister(argparse.Namespace(run=run), now)
        reg = _registry()
    if reg.verdict_of(pid) is None:
        cmd_judge(argparse.Namespace(run=run), now)
    return json.loads((OUT / f"{pid}.json").read_text())


# ── a directed test: a hypothesis submitted as rules ───────────────────────

MAX_DIRECTED = 48  # rules one directed test may hold
MAX_SUBMISSION_BYTES = 4_000_000
AUTHOR_ROLES = ("director", "engine", "lab")
DIRECTED_FAMILIES = M.FAMILIES + ("aggregate",)
_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{2,79}$")
_TEXT = {"title": 8, "hypothesis": 40, "mechanism": 40, "why_now": 20, "refuted_by": 20}


def refuse(sub: object) -> list[str]:
    """Why a submission cannot be taken, in words. Empty: it can. No data is read here and nothing is repaired: a
    submission is taken as it was written, or not at all."""
    if not isinstance(sub, dict):
        return ["it is not an object"]
    out = []
    if not isinstance(sub.get("id"), str) or not _ID.match(sub["id"]):
        out.append("its id must be 3 to 80 letters, digits, dots, dashes or underscores")
    for k, least in _TEXT.items():
        if not isinstance(sub.get(k), str) or len(sub[k].strip()) < least:
            out.append(f"`{k}` must say something (at least {least} characters)")
    a = sub.get("author")
    if not (isinstance(a, dict) and a.get("role") in AUTHOR_ROLES and all(
            isinstance(a.get(k), str) and a[k].strip() for k in ("model", "interface"))):
        out.append(f"`author` must name a role ({', '.join(AUTHOR_ROLES)}), the model and the interface it wrote through")
    if sub.get("dataset") not in DATASETS:
        out.append(f"`dataset` must be one of {', '.join(sorted(DATASETS))}")
    if not isinstance(sub.get("parents", []), list) or not all(isinstance(x, str) for x in sub.get("parents", [])):
        out.append("`parents` must be a list of the records, sources or findings it comes from")
    if not isinstance(sub.get("in_sample_on_check_rows", False), bool):
        out.append("`in_sample_on_check_rows` must be true or false")
    rules = sub.get("rules")
    if not isinstance(rules, list) or not 1 <= len(rules) <= MAX_DIRECTED:
        return out + [f"`rules` must hold 1 to {MAX_DIRECTED} rules"]
    seen = set()
    for i, r in enumerate(rules):
        if not (isinstance(r, dict) and isinstance(r.get("spec"), dict)):
            out.append(f"rule {i}: it must be an object with a `spec`")
            continue
        s = r["spec"]
        parts = s.get("parts") if s.get("kind") == "book" else [s]
        if s.get("kind") != "book" and s.get("kind") not in KINDS or s.get("kind") == "const":
            out.append(f"rule {i}: kind {s.get('kind')!r} is not a rule the lab can test")
        elif not (isinstance(parts, list) and parts and all(
                isinstance(x, dict) and x.get("kind") in KINDS and x.get("kind") != "const"
                and isinstance(x.get("target"), str) for x in parts)) or (s["kind"] == "book" and len(parts) < 2):
            out.append(f"rule {i}: every part must be a rule on a named instrument, and a book holds at least two")
        if r.get("family") not in DIRECTED_FAMILIES:
            out.append(f"rule {i}: `family` must be one of {', '.join(DIRECTED_FAMILIES)}")
        if not isinstance(r.get("why"), str) or len(r["why"].strip()) < 10:
            out.append(f"rule {i}: `why` must say what it would mean if the rule held")
        if r.get("orient", "as written") not in ("as written", "fit"):
            out.append(f"rule {i}: `orient` is 'as written' or 'fit'")
        try:
            k_ = spec_id(s)
        except (TypeError, ValueError):
            out.append(f"rule {i}: its spec is not plain data")
            continue
        if k_ in seen:
            out.append(f"rule {i}: the same rule appears twice")
        seen.add(k_)
    return out


def mirror(spec: dict) -> dict:
    """The same rule on the other side: every position's sign reversed."""
    k = spec["kind"]
    if k == "book" or k == "combo":
        return {**spec, "parts": [mirror(x) for x in spec["parts"]]}
    if k == "xsleg":
        return {**spec, "xs": {**spec["xs"], "side": -spec["xs"]["side"]}}
    if k in ("table", "ordinal", "regime"):
        return {**spec, "map": [-float(v) for v in spec["map"]]}
    if k == "anomaly":
        return {**spec, "mode": {"cont": "rev", "rev": "cont", "long": "short", "short": "long"}[spec["mode"]]}
    return {**spec, "side": -spec["side"]}


def directed_rules(sub: dict, p, fit: np.ndarray, known: dict, closed: list) -> tuple[list[dict], list[dict]]:
    """Each submitted rule against the data it would run on. Returns the rules that can be tested (oriented by the fit
    rows where they ask for it) and the rules refused, each with its reason. Only the fit rows are read: nothing here
    looks at a check-row return, so a refusal costs no test and a rule that passes has still seen nothing."""
    rows = np.nonzero(fit)[0]
    tomb = None
    ok, no = [], []
    for i, r in enumerate(sub["rules"]):
        s = r["spec"]

        def refused(why: str) -> None:
            no.append({"rule": i, "family": r["family"], "what": _words(s), "why": why,
                       **({"cell": r["cell"]} if isinstance(r.get("cell"), str) else {})})
        if not set(targets(s)) <= set(p.assets):
            refused("it names an instrument this panel does not hold: " + ", ".join(sorted(set(targets(s)) - set(p.assets))[:5]))
            continue
        try:
            x = pnl(s, p)
            g = stats(x["gross"], fit, p.ppy, x["pos"])
            if r.get("orient") == "fit":
                if not g["t"]:
                    refused("it earns nothing on the fit rows, so they cannot say which way it points")
                    continue
                if g["t"] < 0:
                    s = mirror(s)
                    x = pnl(s, p)
                    g = stats(x["gross"], fit, p.ppy, x["pos"])
            sound = causal(s, p, points=3)
        except (KeyError, ValueError, IndexError, TypeError, ZeroDivisionError) as e:
            refused(f"it cannot be computed on this panel ({type(e).__name__}: {str(e)[:120]})")
            continue
        held_rows, entries = _activity(s, p, fit)
        if not sound:
            refused("its position at a row changes when later rows are removed: it reads the future")
        elif held_rows < T.MIN_IN_POSITION or entries < T.MIN_ENTRIES:
            refused(f"{held_rows} rows in position and {entries} entries on the fit rows: too few to be a rule")
        elif spec_id(s) in known:
            refused(f"the same rule was classed {known[spec_id(s)][1]} by {known[spec_id(s)][0]}: it is not looked at twice")
        else:
            if tomb is None:  # the closed families, as they behaved on the fit rows
                tomb = [(n, T.behaviour(c, p, rows)) for n, c in closed if set(targets(c)) <= set(p.assets)]
            b = T.behaviour(s, p, rows)
            rep = next(((n, T._corr(b, c)) for n, c in tomb if T._corr(b, c) >= T.SAME), None)
            if rep is not None:
                refused(f"on the fit rows it behaves as {rep[0]} (correlation {rep[1]:.2f}), judged and closed")
            else:
                ok.append({"id": spec_id(s), "family": r["family"], "why": r["why"].strip(), "spec": s,
                           "oriented_by_the_fit_rows": r.get("orient") == "fit", "fit_gross_t": round(g["t"], 3) if g["t"] else None})
    return ok, no


def _activity(spec: dict, p, mask: np.ndarray) -> tuple[int, int]:
    """Rows in position and positions opened or reversed on the masked rows. A book's are its parts', taken together,
    as the triage counts them."""
    each = [pnl(x, p) for x in parts_of(spec)]
    each = [stats(x["net"], mask, p.ppy, x["pos"]) for x in each]
    return sum(x.get("in_position") or 0 for x in each), sum(x.get("entries") or 0 for x in each)


def _words(spec: dict) -> str:
    try:
        return describe(spec)[:200]
    except (KeyError, TypeError, ValueError, IndexError):
        return "a rule that cannot be put in words"


def directed_spec(dataset: str, run: str, sub: dict, rules: list[dict], refused: list[dict]) -> dict:
    universe = DATASETS[dataset][0]
    w = D.WINDOWS[universe]
    return {"program": run, "version": DLAB_VERSION, "kind": "directed test", "role": "select", "dataset": dataset,
            "universe": universe, "windows": {k: [str(v[0]), str(v[1])] for k, v in w.items()},
            "submission": {**{k: sub[k] for k in ("id", "author", "title", "hypothesis", "mechanism", "why_now", "refuted_by")},
                           "submitted": sub.get("submitted"), "parents": list(sub.get("parents", [])),
                           "in_sample_on_check_rows": bool(sub.get("in_sample_on_check_rows", False)),
                           "sha256": sha(sub)},
            "rules": rules, "refused_before_registration": refused,
            "related_universes": list(D.RELATED.get(universe, ())), "classes": list(T.CLASSES),
            "triage": {"same_behaviour_correlation": T.SAME, "least_chance_to_pass": T.P_MIN,
                       "least_chance_for_a_place_that_costs_the_bar_nothing": T.P_FREE, "haircut": T.HAIRCUT,
                       "batch": T.MAX_BATCH, "per_family": T.PER_FAMILY, "per_instrument": T.PER_TARGET},
            "firewall": "the panel is loaded with nothing at or after the check rows' end: the validation rows are "
                        "not in memory. A rule was oriented, where it asked, by the fit rows alone",
            "validation": "a separate registration (" + run + "-V): the promising rules, frozen, judged once on the "
                          "validation window at max(3.0, Bonferroni over every test on that window)"}


def prereg_directed_doc(run: str, f: dict, day: str) -> str:
    s = f["spec"]
    sub, w = s["submission"], s["windows"]
    a = sub["author"]
    o = [f"# {run}: a directed test on {s['universe']} (preregistration)", "",
         f"**Written {day} by the discovery lab's worker, before any check row was read.** Research only: nothing here "
         "trades.", "",
         f"- Spec sha256: `{f['sha256']}` (`research/specs/{run}.json`)",
         f"- Code sha256: `{f['code_sha256']}` (the lab: `scripts/dlab.py`, `aitrader/research/dlab/`)",
         f"- Submission `{sub['id']}` (sha256 `{sub['sha256']}`), written by the {a['role']} ({a['model']}, through "
         f"{a['interface']})", "- Protocol: `docs/DISCOVERY_LAB.md`, `docs/RESEARCH_INSTITUTION.md`", "",
         "## The hypothesis", "", f"**{sub['title']}**", "", sub["hypothesis"], "", f"Mechanism: {sub['mechanism']}", "",
         f"Why now: {sub['why_now']}", "", f"What would refute it: {sub['refuted_by']}", "",
         "Comes from: " + (", ".join(sub["parents"]) or "nothing on record"), ""]
    if sub["in_sample_on_check_rows"]:
        o += ["**Its rules were chosen on the check rows.** Their check-row figures are therefore in sample and show "
              "nothing. Only the validation rows, which no scan and no test has read, can judge them.", ""]
    o += ["## The rules, frozen", "", "| Id | Family | The rule | Why |", "|---|---|---|---|"]
    o += [f"| `{r['id']}` | {r['family']} | {_words(r['spec'])}"
          + (" (pointed by the fit rows)" if r["oriented_by_the_fit_rows"] else "") + f" | {r['why'][:300]} |" for r in s["rules"]]
    if s["refused_before_registration"]:
        o += ["", "Refused before this registration, on the fit rows alone, and not tested (no test is charged for them):", ""]
        o += [f"- {x['what']}: {x['why']}" for x in s["refused_before_registration"]]
    o += ["", "## The rows", "", "| Rows | From | To (exclusive) | Use |", "|---|---|---|---|",
          f"| Fit | {w['fit'][0]} | {w['fit'][1]} | a rule that asked was pointed by these; nothing else was read |",
          f"| Check | {w['check'][0]} | {w['check'][1]} | each rule is evaluated here once |",
          f"| Validation | {w['validation'][0]} | {w['validation'][1]} | **not loaded.** Read once, by `{run}-V`, if a rule is promising |",
          "", "## What is counted", "",
          f"- The test is charged {len(s['rules'])} tests against its fit and check rows (role select): one for each rule.",
          "- Each rule is classed against every look earlier scans and tests took at the same check rows, not only "
          "against this test's own rules.",
          "- The validation rows are charged only for the rules later judged on them.", "",
          "## What follows", "",
          f"- At most {s['triage']['batch']} rules go to `{run}-V`: frozen, and judged once on the validation rows at "
          "max(3.0, Bonferroni over every test on those rows), with every other gate (doubled costs, a late entry for a "
          "slow rule, both halves, 1,000 time-shifted books, no one year carrying it).",
          "- The verdict is PASSED if the test proposes such a batch and FAILED if it does not. Neither is a result "
          "about any rule: no rule is validated or disproved here. No model approves anything: a rule is validated "
          "only by that separate test.", ""]
    return "\n".join(o)


def auto_directed(dataset: str, run: str, sub: dict, now: datetime, panel=None) -> dict:
    """A submitted hypothesis, end to end: check its rules against the data, freeze, write its preregistration,
    register, look once at the check rows, class, record. Resumes where a crash left it. If no rule survives the
    checks, nothing is registered and nothing is charged: the result says why."""
    reg = _registry()
    universe, loader, _ = DATASETS[dataset]
    w = D.WINDOWS[universe]
    p = panel if panel is not None else loader(w["check"][1])
    if p.times[-1] >= w["validation"][0]:
        raise SystemExit("the panel given to a directed test holds validation rows: refused")
    fit, check = p.rows(*w["fit"]), p.rows(*w["check"])
    if not any(t.id == run for t in reg.trials):
        problems = refuse(sub)
        if problems:
            return {"program": run, "verdict": "REFUSED", "why": problems, "refused": []}
        rules, refused = directed_rules(sub, p, fit, known_rules(universe), D.closed(p))
        if not rules:
            return {"program": run, "verdict": "REFUSED", "why": ["no rule of the submission can be tested"], "refused": refused}
        s = directed_spec(dataset, run, sub, rules, refused)
        (R / "specs").mkdir(parents=True, exist_ok=True)
        (R / "specs" / f"{run}.json").write_text(_dump({"spec": s, "sha256": sha(s), "code_sha256": code_hash()}))
        f = _frozen(run)
        doc = ROOT / "research" / "preregistrations" / f"{run}.md"
        doc.parent.mkdir(parents=True, exist_ok=True)
        doc.write_text(prereg_directed_doc(run, f, f"{now:%Y-%m-%d}"))
        reg.register(Trial(id=run, registered=now, title=f"{run}: a directed test of {len(rules)} rules on {universe} (select)",
                           hypothesis=sub["hypothesis"].strip()[:900],
                           uses=(Use(universe, _day(w["fit"][0]), _day(w["check"][1]), "select"),),
                           tests=len(rules), configurations=len(rules), preregistration=f"research/preregistrations/{run}.md",
                           design={"spec_sha256": f["sha256"], "code_sha256": f["code_sha256"], "submission": sub["id"]}))
        print("registered", run)
        reg = _registry()
    judged = reg.verdict_of(run)
    if judged is not None:  # looked at once: the record is returned, never recomputed
        return json.loads((OUT / f"{run}.json").read_text())
    f = _frozen(run)
    if reg.get(run).design.get("spec_sha256") != f["sha256"] or code_hash() != f["code_sha256"]:
        raise SystemExit(f"{run}: the spec or the code differs from what was registered")
    s = f["spec"]
    emitted = [M.Emit(r["spec"], r["family"], "directed", abs(r["fit_gross_t"] or 0.0), r["why"],
                      {"submission": s["submission"]["id"], "author": s["submission"]["author"]["role"],
                       "oriented_by_the_fit_rows": r["oriented_by_the_fit_rows"]}) for r in s["rules"]]
    years = (w["validation"][1] - w["validation"][0]).days / 365.25
    bar = bar_for(reg, universe, w["validation"], T.MAX_BATCH)
    res = T.triage(emitted, p, fit, check, n_val=p.ppy * years, bar=bar, closed=D.closed(p), hint=D.HINTS.get(universe, ""),
                   known=known_rules(universe), prior_looks=earlier_looks(universe),
                   free_places=free_places(reg, universe, w["validation"]))
    if s["submission"]["in_sample_on_check_rows"]:
        for r in res["records"]:
            r["in_sample_on_check_rows"] = True
            r["reason"] = (r.get("reason") or "") + ("; its rules were chosen on these check rows, so this figure is in "
                                                     "sample and shows nothing: only the validation rows judge it")
    verdict = "PASSED" if res["batch"] else "FAILED"
    body = _write(run, {"program": run, "kind": "directed_test", "verdict": verdict, "spec_sha256": f["sha256"],
                        "code_sha256": f["code_sha256"], "windows": s["windows"], "universe": universe,
                        "rows": {"panel": p.T, "fit": int(fit.sum()), "check": int(check.sum()),
                                 "validation_expected": int(p.ppy * years)},
                        "first_row": str(p.times[0]), "last_row": str(p.times[-1]), "instruments": list(p.assets),
                        "submission": {k: s["submission"][k] for k in ("id", "author", "title", "in_sample_on_check_rows")},
                        "refused_before_registration": s["refused_before_registration"], "bar_on_validation": round(bar, 4),
                        "meaning": ("the batch goes to a registered validation" if res["batch"] else
                                    "no rule is worth a registered validation; every rule is kept with its class"),
                        **res, "summary": T.summary(res["records"])})
    T.append(LEDGER, run, res["records"], now.isoformat(), DLAB_VERSION)
    reg.record_verdict(Verdict(run, now, verdict, {"artifact": f"research/knowledge/{run}.json",
                                                    "artifact_sha256": body["sha256"], "rules": len(res["records"]),
                                                    "batch": res["batch"]}))
    return body


def aggregate_of(runs: list[str]) -> dict:
    """One rule that is every rule of the given runs classed positive on the check rows and not told from noise, held
    together: the families share the capital equally, the rules of a family share theirs equally, and the parts of a
    rule (a book's legs) share the rule's. Deterministic: built from the candidate ledger as it stands."""
    rows = [json.loads(x) for x in LEDGER.read_text().splitlines() if x.strip()]
    mine = [r for r in rows if "event" not in r and r["run"] in runs and r["class"] in ("INSUFFICIENT_POWER", "PROMISING_UNCONFIRMED")]
    fams: dict[str, list[dict]] = {}
    for r in sorted(mine, key=lambda r: (r["family"], r["id"])):
        if weights(r["spec"]) is None:  # an aggregate is not put inside an aggregate
            fams.setdefault(r["family"], []).append(r)
    if not fams:
        raise SystemExit(f"no rule of {', '.join(runs)} is classed positive: nothing to hold together")
    parts = []
    for members in fams.values():
        for r in members:
            leaves = parts_of(r["spec"])
            share = 1.0 / (len(fams) * len(members) * len(leaves))
            parts += [{**x, "share": share} for x in leaves]
    return {"kind": "book", "parts": parts}


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


def operating_characteristic_broad(seeds: int = 6, assets: int = 24, only: tuple | None = None) -> dict:
    """The same question on a broad panel shaped like the crypto one (790 fit rows, 730 check rows, 850 validation
    rows): how small a cross-sectional effect, present in every instrument, the lab promotes and then validates. The
    planted effect lasts one row, so a book must trade every row to earn it: the last line plants the largest effect
    again at a one-way cost of 5 basis points, where that turnover costs more than the effect pays."""
    fit_n, chk_n, val_n = 790 + 250, 730, 850  # 250 rows of warm-up before the fit rows, as the real panels have
    out = []
    cases = [("nothing", None, 0.00005)] + [(f"cross-sectional reversal, correlation {ic} in each instrument", {"xs": ic},
                                             0.00005) for ic in (0.01, 0.02, 0.03)]
    cases.append(("cross-sectional reversal, correlation 0.03, at a one-way cost of 5 basis points", {"xs": 0.03}, 0.0005))
    if only is not None:  # some of the cases only: the study can be run a case at a time and its results joined
        cases = [c for i, c in enumerate(cases) if i in only]
    for label, plant, cost in cases:
        promoted = validated = false_valid = rules = 0
        hits = []
        for seed in range(seeds):
            p = D.synthetic(rows=fit_n + chk_n + val_n, assets=assets, seed=300 + seed, plant=plant, cost=cost)
            head = p.head(fit_n + chk_n)
            fit = np.zeros(head.T, dtype=bool)
            fit[250:fit_n] = True
            check = np.zeros(head.T, dtype=bool)
            check[fit_n:] = True
            emitted, _ = M.discover(M.Context(head, fit, seed=7))
            res = T.triage(emitted, head, fit, check, n_val=val_n, bar=3.0, closed=D.closed(head),
                           free_places=T.MAX_BATCH)
            rules += len(res["records"])
            by_id = {r["id"]: r for r in res["records"]}
            vmask = np.zeros(p.T, dtype=bool)
            vmask[fit_n + chk_n:] = True
            ok_any = False
            for i in res["batch"]:
                j = judge_rule(by_id[i]["spec"], p, vmask, 3.0, 5, mean_hold(by_id[i]) >= SLOW_ROWS)
                real = plant is not None and by_id[i]["family"] in ("cross-sectional", "pooled time-series", "pooled book")
                ok_any |= j["passed"] and real
                false_valid += j["passed"] and not real
            promoted += any(by_id[i]["class"] == "PROMISING_UNCONFIRMED" for i in res["batch"])
            validated += ok_any
            hits.append(len(res["batch"]))
        out.append({"market": label, "one_way_cost": cost, "runs": seeds, "runs_with_a_promising_rule": promoted,
                    "runs_with_a_pooled_rule_validated": validated if plant else None,
                    "validated_rules_that_were_not_pooled": false_valid, "mean_rules_per_run": round(rules / seeds, 1),
                    "rules_judged_per_run": hits})
        print(json.dumps(out[-1]), flush=True)
    return {"version": DLAB_VERSION, "instruments": assets,
            "rows": {"fit": fit_n - 250, "check": chk_n, "validation": val_n},
            "note": "the effect is in every instrument, so a book of all of them carries it and an instrument alone "
                    "cannot. A correlation c in each of N instruments gives the book a gross Sharpe ratio of about "
                    "c x sqrt(252 N) a year. Twelve places in each batch cost the bar nothing, as on the crypto panel: "
                    "every judged rule faces t 3.0 and every other gate",
            "results": out}


def cmd_oc(a) -> None:
    (R / "dlab").mkdir(parents=True, exist_ok=True)
    if a.broad:
        (R / "dlab" / "operating_characteristic_broad.json").write_text(_dump(operating_characteristic_broad(a.seeds)))
    else:
        (R / "dlab" / "operating_characteristic.json").write_text(_dump(operating_characteristic(a.seeds)))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("cmd", choices=["scan-spec", "scan-register", "scan-run", "spec", "preregister", "judge", "oc",
                                    "auto"])
    ap.add_argument("--dataset", choices=sorted(DATASETS), default="energy")
    ap.add_argument("--run", default="")
    ap.add_argument("--seed", type=int, default=7)
    ap.add_argument("--seeds", type=int, default=12)
    ap.add_argument("--broad", action="store_true", help="oc: the broad-panel study")
    a = ap.parse_args()
    now = datetime.now(timezone.utc).replace(microsecond=0)
    if a.cmd != "oc" and not a.run:
        ap.error("--run is required")
    {"scan-spec": lambda: cmd_scan_spec(a), "scan-register": lambda: cmd_scan_register(a, now),
     "scan-run": lambda: cmd_scan_run(a, now), "spec": lambda: cmd_spec(a), "preregister": lambda: cmd_preregister(a, now),
     "judge": lambda: cmd_judge(a, now), "oc": lambda: cmd_oc(a),
     "auto": lambda: (auto_scan(a.dataset, a.run, a.seed, now), auto_validate(a.run, now))}[a.cmd]()
    return 0


__all__ = ["aggregate_of", "auto_directed", "auto_scan", "auto_validate", "bar_for", "batch_spec", "code_hash",
           "covers", "directed_rules", "directed_spec", "judge_rule", "mean_hold", "mirror", "refuse",
           "operating_characteristic", "operating_characteristic_broad", "prereg_batch_doc", "prereg_scan_doc", "same_rules", "scan", "scan_spec",
           "tests_counted"]

if __name__ == "__main__":
    raise SystemExit(main())
