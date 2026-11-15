"""BAS-1: does the arbitrage that high funding attracts lift the spot price? (research/preregistrations/BAS-1.md)
Runs on GitHub's runner (.github/workflows/bas1.yml). It reuses SQZ-1's frozen readers, signal, benchmark and judge
(scripts/sqz1.py, aitrader/research/events/squeeze.py), on the other tail of the funding.

    python scripts/bas1.py hash                    # the code hash the preregistration quotes
    python scripts/bas1.py preregister dev         # each later stage only after the one before PASSED
    python scripts/bas1.py run dev --data DIR      # fetch what the stage needs, judge it once, record the verdict

The traded instrument is SPOT, bought outright: no leverage, no short, no funding paid or received.
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from aitrader.research.dlab.feeds import checked  # noqa: E402
from aitrader.research.events import basis as B  # noqa: E402
from aitrader.research.events import squeeze as Q  # noqa: E402
import scripts.sqz1 as Z  # noqa: E402
from aitrader.research.registry import Registry, Trial, Use, Verdict, bonferroni_t  # noqa: E402

R = ROOT / "research"
DOC = "research/preregistrations/BAS-1.md"
PROBE = R / "results" / "SQZ-1-probe.json"  # the seasoned coins, their spot pairs and months (file names only)
CODE = ("aitrader/research/events/basis.py", "scripts/bas1.py", "aitrader/research/events/squeeze.py", "scripts/sqz1.py")
UNIVERSE = "crypto-spot-high-funding"
SPEC = {"program": "BAS-1", "version": B.BAS_VERSION, "universe": UNIVERSE, "instrument": "spot, bought outright",
        "thresholds": [0.0003, 0.0005, 0.001], "hold_days": 7, "late_lag_days": 1, "cost_per_side": 0.0015,
        "placebo_span_days": 30, "placebos": 1000, "seed": 20261115, "nw_lag": 2, "bar_floor": 3.0,
        "gates": ["t", "costs_x2", "halves", "top5_removed", "late_entry", "beats_placebo", "without_best_year",
                  "without_best_coin"],
        "stages": {
            "dev": {"trial": "BAS-1", "entries": ["2021-01-01", "2025-02-28"], "tests": 3, "min_events": 300, "min_weeks": 52},
            "validation": {"trial": "BAS-1-V", "after": "BAS-1", "entries": ["2025-03-08", "2026-10-24"], "tests": 1,
                           "min_events": 150, "min_weeks": 40},
            "forward": {"trial": "BAS-1-F", "after": "BAS-1-V", "entries": ["2026-12-01", "2027-05-24"],
                        "not_before": "2027-06-10", "tests": 1, "min_events": 60, "min_weeks": 10}}}


def code_hash() -> str:
    h = hashlib.sha256()
    for f in CODE:
        h.update((ROOT / f).read_bytes())
    return h.hexdigest()


def spec_sha() -> str:
    return hashlib.sha256(json.dumps(SPEC, sort_keys=True).encode()).hexdigest()


def registry() -> Registry:
    return Registry.load(R / "registry.jsonl")


def _status(reg: Registry, pid: str) -> str | None:
    return reg.status_of(pid) if any(t.id == pid for t in reg.trials) else None


def chosen_threshold(out_dir: Path) -> float:
    art = json.loads((out_dir / "BAS-1.json").read_text())
    if art.get("verdict") != "PASSED" or art.get("chosen_threshold") is None:
        raise SystemExit("the later stages use the threshold BAS-1 chose; BAS-1 has not passed")
    return float(art["chosen_threshold"])


def run(stage: str, data: Path, now: datetime, fetch=checked, reg: Registry | None = None, out_dir: Path | None = None,
        probe_file: Path = PROBE) -> dict:
    reg = reg or registry()
    st = SPEC["stages"][stage]
    pid = st["trial"]
    out_dir = out_dir or R / "knowledge"
    if not any(t.id == pid for t in reg.trials):
        raise SystemExit(f"{pid} is not registered: nothing is fetched or judged before it is")
    if reg.status_of(pid) != "PENDING":
        raise SystemExit(f"{pid} already has a verdict: a stage is judged once")
    if "after" in st and _status(reg, st["after"]) != "PASSED":
        raise SystemExit(f"{pid} is judged only after {st['after']} passed")
    if now.date().isoformat() < st.get("not_before", ""):
        raise SystemExit(f"{pid} is judged on or after {st['not_before']}, when its archive is whole")
    design = reg.get(pid).design
    if design.get("code_sha256") != code_hash() or design.get("spec_sha256") != spec_sha():
        raise SystemExit(f"{pid}: the code or the spec differs from what was registered")
    a, b = st["entries"]
    last_exit = Q.plus(b, SPEC["hold_days"] + SPEC["late_lag_days"])
    coins = json.loads(probe_file.read_text())["coins"]
    settle, spot, man = Z.fetch_all(coins, Z._months(Z._add_months(a[:7], -2), last_exit), fetch)
    if man["failed"]:
        raise SystemExit(f"{len(man['failed'])} archive files did not arrive (the first: {man['failed'][:3]}): "
                         "nothing is judged on a partial panel")
    settle, spot = Z.firewall(settle, spot, b, last_exit)
    fund = {s: Q.Funding(xs) for s, xs in settle.items()}
    seasoned = {s: v["seasoned"] for s, v in coins.items()}
    bench = Q.Bench(spot, seasoned)
    bar = max(SPEC["bar_floor"], bonferroni_t(max(1, reg.tests_on(UNIVERSE, date.fromisoformat(a), date.fromisoformat(b) + timedelta(days=1)))))
    cost = SPEC["cost_per_side"]
    ths = SPEC["thresholds"] if stage == "dev" else [chosen_threshold(out_dir)]
    results, kept = {}, {}
    for th in ths:
        evs = B.events(fund, spot, seasoned, bench, a, b, th, cost, SPEC["hold_days"])
        late = B.events(fund, spot, seasoned, bench, a, b, th, cost, SPEC["hold_days"], lag=SPEC["late_lag_days"])
        plac = B.placebos(fund, spot, seasoned, bench, evs, th, cost, SPEC["hold_days"], SPEC["placebo_span_days"])
        results[str(th)] = Q.judge(evs, late, plac, bar, cost, st["min_events"], st["min_weeks"], SPEC["seed"],
                                   SPEC["placebos"], SPEC["nw_lag"])
        kept[str(th)] = evs
    passed = [th for th in ths if results[str(th)]["verdict"] == "PASSED"]
    chosen = max(passed, key=lambda th: results[str(th)]["t"]) if passed else None
    verdict = "PASSED" if passed else ("INCONCLUSIVE" if all(r["verdict"] == "INCONCLUSIVE" for r in results.values()) else "FAILED")
    body = {"program": pid, "stage": stage, "kind": "spot_event_study", "verdict": verdict, "judged": now.isoformat(),
            "code_sha256": code_hash(), "spec_sha256": spec_sha(), "spec": SPEC, "entries": [a, b], "bar": bar,
            "chosen_threshold": chosen if stage == "dev" else ths[0], "last_day_read": last_exit,
            "data": {"files": man["files"], "absent": len(man["absent"]), "coins_with_spot": len(spot)}, "results": results}
    out_dir.mkdir(parents=True, exist_ok=True)
    f = out_dir / f"{pid}.json"
    f.write_text(json.dumps(body, indent=1, sort_keys=True, default=str) + "\n")
    data.mkdir(parents=True, exist_ok=True)
    with gzip.open(data / f"{pid}-events.json.gz", "wt") as g:
        json.dump(kept, g)
    best = results[str(chosen)] if chosen is not None else max(results.values(), key=lambda r: r["t"] if r["t"] is not None else -1e9)
    reg.record_verdict(Verdict(pid, now, verdict, {
        "artifact": str(f.relative_to(ROOT)) if f.is_relative_to(ROOT) else str(f), "chosen_threshold": body["chosen_threshold"],
        "t": best["t"], "mean_excess": best["mean_excess"], "traded": best["traded"], "weeks": best["weeks"],
        "gates": best.get("gates"), "why": best.get("why")}))
    return body


def preregister(stage: str, now: datetime) -> None:
    st = SPEC["stages"][stage]
    h = code_hash()
    doc = (ROOT / DOC).read_text()
    if h not in doc or spec_sha() not in doc:
        raise SystemExit(f"{DOC} must quote the code sha256 {h} and the spec sha256 {spec_sha()}")
    reg = registry()
    if "after" in st and _status(reg, st["after"]) != "PASSED":
        raise SystemExit(f"{st['trial']} is registered only after {st['after']} passed")
    a, b = st["entries"]
    reg.register(Trial(
        id=st["trial"], registered=now, title=f"{st['trial']}: high funding and the spot buyer, {stage} stage",
        hypothesis="A coin whose USDT-M perpetual paid its shorts at least theta per 8 hours over the last 72 hours "
                   "(high funding), bought on spot and held seven days, beats the equal-weight spot return of every "
                   "seasoned coin over the same days after 0.15% a side, averaged over weekly cohorts.",
        uses=(Use(UNIVERSE, date.fromisoformat(a), date.fromisoformat(b) + timedelta(days=1), "judge"),),
        tests=st["tests"], configurations=len(SPEC["thresholds"]) if stage == "dev" else 1, preregistration=DOC,
        design={"code_sha256": h, "spec_sha256": spec_sha(), "stage": stage}))
    print("registered", st["trial"])


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("command", choices=("hash", "preregister", "run"))
    ap.add_argument("stage", nargs="?", choices=tuple(SPEC["stages"]))
    ap.add_argument("--data", default=str(ROOT / "data" / "bas1"))
    ap.add_argument("--probe", default=str(PROBE))
    a = ap.parse_args(argv)
    now = datetime.now(timezone.utc)
    if a.command == "hash":
        print(code_hash(), spec_sha())
    elif a.command == "preregister":
        preregister(a.stage, now)
    else:
        body = run(a.stage, Path(a.data), now, probe_file=Path(a.probe))
        print(json.dumps({"program": body["program"], "verdict": body["verdict"], "chosen": body["chosen_threshold"],
                          "results": {k: {x: v.get(x) for x in ("traded", "weeks", "mean_excess", "t", "verdict", "gates")}
                                      for k, v in body["results"].items()}}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
