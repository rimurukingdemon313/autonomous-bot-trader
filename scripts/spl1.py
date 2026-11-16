"""SPL-1: does a rally that spot buyers led keep going? (research/preregistrations/SPL-1.md) Runs on GitHub's runner
(.github/workflows/spl1.yml): Binance's archive is not reachable from the director's session. It reads CASC-1's
hourly panel with CASC-1's frozen readers and judge (scripts/casc1.py, aitrader/research/events/cascade.py).

    python scripts/spl1.py hash                    # the code hash the preregistration quotes
    python scripts/spl1.py preregister dev         # each later stage only after the one before PASSED
    python scripts/spl1.py run dev --data DIR      # fetch what the stage needs, judge it once, record the verdict

The traded instrument is SPOT, bought outright: no leverage, no short, no funding. The perpetual's price is
information only (whether the rise was led by leveraged buying there). Nothing here trades.
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
from aitrader.research.events import cascade as K  # noqa: E402
from aitrader.research.events import rally as P  # noqa: E402
import scripts.casc1 as C  # noqa: E402  (the hourly panel's readers, unchanged)
import scripts.sqz1 as Z  # noqa: E402  (months)
from aitrader.research.registry import Registry, Trial, Use, Verdict, bonferroni_t  # noqa: E402

R = ROOT / "research"
DOC = "research/preregistrations/SPL-1.md"
PROBE = R / "results" / "CASC-1-probe.json"  # which months of hourly spot and perpetual bars exist (file names only)
CODE = ("aitrader/research/events/rally.py", "scripts/spl1.py", "aitrader/research/events/cascade.py",
        "scripts/casc1.py", "scripts/sqz1.py")
UNIVERSE = "crypto-spot-spot-led-rallies"
#: CASC-1 read the same hourly panel over the development window: its tests count against this one's bar
COUNTED = (UNIVERSE, "crypto-spot-liquidation-falls")
SPEC = {"program": "SPL-1", "version": P.SPL_VERSION, "universe": UNIVERSE, "counted_universes": list(COUNTED),
        "instrument": "spot, bought outright", "rises": [0.08, 0.15], "perp_premium": 0.005, "look_hours": P.LOOK,
        "hold_hours": P.HOLD, "late_hours": 1, "cost_per_side": 0.0025, "placebo_span_hours": 168,
        "placebo_draws_per_entry": 40, "placebos": 1000, "seed": 20261116, "nw_lag": 1, "bar_floor": 3.0,
        "gates": ["t", "costs_x2", "halves", "top5_removed", "late_entry", "beats_placebo", "without_best_day",
                  "without_best_coin", "beats_leverage_led_rallies", "beats_market"],
        "stages": {
            "dev": {"trial": "SPL-1", "decisions": ["2023-07-01", "2025-02-28"], "tests": 2, "min_events": 150, "min_days": 40},
            "validation": {"trial": "SPL-1-V", "after": "SPL-1", "decisions": ["2025-03-08", "2026-10-29"], "tests": 1,
                           "min_events": 150, "min_days": 40},
            "forward": {"trial": "SPL-1-F", "after": "SPL-1-V", "decisions": ["2026-12-01", "2027-05-29"],
                        "not_before": "2027-06-10", "tests": 1, "min_events": 40, "min_days": 10}}}


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


def bar_for(reg: Registry, a: str, b: str) -> float:
    """Every test on this panel over the stage's window counts, CASC-1's included; never below the floor."""
    n = sum(reg.tests_on(u, date.fromisoformat(a), date.fromisoformat(b) + timedelta(days=1)) for u in COUNTED)
    return max(SPEC["bar_floor"], bonferroni_t(max(1, n)))


def chosen_rise(out_dir: Path) -> float:
    art = json.loads((out_dir / "SPL-1.json").read_text())
    if art.get("verdict") != "PASSED" or art.get("chosen_rise") is None:
        raise SystemExit("the later stages use the rise SPL-1 chose; SPL-1 has not passed")
    return float(art["chosen_rise"])


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
    a, b = st["decisions"]
    first_month = Z._add_months(a[:7], -1)
    t0 = C.ms(first_month + "-01")
    last_ms = C.ms(b) + 86_400_000 + (P.HOLD + SPEC["late_hours"]) * P.HOUR  # the last exit's close
    hours = (last_ms - t0) // P.HOUR
    months = Z._months(first_month, datetime.fromtimestamp((last_ms - 1) / 1000, timezone.utc).date().isoformat())
    coins = json.loads(probe_file.read_text())["coins"]
    panel, man = C.fetch_panel(coins, months, t0, hours, fetch)  # the grid ends at the last exit: nothing later fits
    if man["failed"]:
        raise SystemExit(f"{len(man['failed'])} archive files did not arrive (the first: {man['failed'][:3]}): "
                         "nothing is judged on a partial panel")
    first_h, last_h = (C.ms(a) - t0) // P.HOUR, (C.ms(b) + 86_400_000 - t0) // P.HOUR - 1
    bar = bar_for(reg, a, b)
    cost, prem = SPEC["cost_per_side"], SPEC["perp_premium"]
    rises = SPEC["rises"] if stage == "dev" else [chosen_rise(out_dir)]
    results, kept = {}, {}
    for x in rises:
        evs = P.events(panel, first_h, last_h, x, prem, cost)
        late = P.events(panel, first_h, last_h, x, prem, cost, lag=SPEC["late_hours"])
        contra = P.contrast(panel, first_h, last_h, x, prem, cost)
        plac = P.placebos(panel, evs, x, cost, SPEC["placebo_span_hours"], SPEC["placebo_draws_per_entry"], SPEC["seed"])
        results[str(x)] = P.judge(panel, evs, late, contra, plac, bar, cost, st["min_events"], st["min_days"],
                                  SPEC["seed"], SPEC["placebos"], SPEC["nw_lag"])
        kept[str(x)] = evs
    passed = [x for x in rises if results[str(x)]["verdict"] == "PASSED"]
    chosen = max(passed, key=lambda x: results[str(x)]["t"]) if passed else None
    verdict = "PASSED" if passed else ("INCONCLUSIVE" if all(r["verdict"] == "INCONCLUSIVE" for r in results.values()) else "FAILED")
    body = {"program": pid, "stage": stage, "kind": "spot_event_study", "verdict": verdict, "judged": now.isoformat(),
            "code_sha256": code_hash(), "spec_sha256": spec_sha(), "spec": SPEC, "decisions": [a, b], "bar": bar,
            "chosen_rise": chosen if stage == "dev" else rises[0],
            "last_moment_read": datetime.fromtimestamp(last_ms / 1000, timezone.utc).isoformat(),
            "data": {"source": C.BASE, "files": man["files"], "absent": len(man["absent"]), "coins": len(panel.coins)},
            "results": results}
    out_dir.mkdir(parents=True, exist_ok=True)
    f = out_dir / f"{pid}.json"
    f.write_text(json.dumps(body, indent=1, sort_keys=True, default=str) + "\n")
    data.mkdir(parents=True, exist_ok=True)
    with gzip.open(data / f"{pid}-events.json.gz", "wt") as g:
        json.dump(kept, g)
    best = results[str(chosen)] if chosen is not None else max(results.values(), key=lambda r: r["t"] if r["t"] is not None else -1e9)
    reg.record_verdict(Verdict(pid, now, verdict, {
        "artifact": str(f.relative_to(ROOT)) if f.is_relative_to(ROOT) else str(f), "chosen_rise": body["chosen_rise"],
        "t": best["t"], "mean_net": best["mean_net"], "traded": best["traded"], "days": best["days"],
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
    a, b = st["decisions"]
    reg.register(Trial(
        id=st["trial"], registered=now, title=f"{st['trial']}: spot-led rallies and the spot buyer, {stage} stage",
        hypothesis="A seasoned coin whose spot rose at least X in four hours while its perpetual never closed more than "
                   "0.25% above spot, bought on spot at that close and sold 24 hours later, earns a positive net return "
                   "after 0.25% a side, averaged over days, more than the market, than the same coin at hours it had "
                   "not risen, and than rallies its perpetual led.",
        uses=(Use(UNIVERSE, date.fromisoformat(a), date.fromisoformat(b) + timedelta(days=1), "judge"),),
        tests=st["tests"], configurations=len(SPEC["rises"]) if stage == "dev" else 1, preregistration=DOC,
        design={"code_sha256": h, "spec_sha256": spec_sha(), "stage": stage}))
    print("registered", st["trial"])


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("command", choices=("hash", "preregister", "run"))
    ap.add_argument("stage", nargs="?", choices=tuple(SPEC["stages"]))
    ap.add_argument("--data", default=str(ROOT / "data" / "spl1"))
    ap.add_argument("--probe", default=str(PROBE))
    a = ap.parse_args(argv)
    now = datetime.now(timezone.utc)  # the command line's clock: every function above takes its time as an argument
    if a.command == "hash":
        print(code_hash(), spec_sha())
    elif a.command == "preregister":
        preregister(a.stage, now)
    else:
        body = run(a.stage, Path(a.data), now, probe_file=Path(a.probe))
        print(json.dumps({"program": body["program"], "verdict": body["verdict"], "chosen": body["chosen_rise"],
                          "results": {k: {x: v.get(x) for x in ("traded", "days", "mean_net", "t", "verdict", "gates")}
                                      for k, v in body["results"].items()}}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
