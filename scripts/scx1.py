"""SCX-1: do stablecoins drift from par while their primary market is shut, and come back when it opens?
(research/preregistrations/SCX-1.md) Runs on GitHub's runner (.github/workflows/scx1.yml): Binance's archive is not
reachable from the research director's session.

    python scripts/scx1.py probe [--out FILE]      # file names only: which months of hourly bars each pair has
    python scripts/scx1.py hash                    # the code and spec hashes the preregistration quotes
    python scripts/scx1.py preregister dev         # each later stage only after the one before PASSED
    python scripts/scx1.py run dev --data DIR      # fetch what the stage needs, judge it once, record the verdict

The traded instrument is a spot exchange of one stablecoin for another, from a stock of both: no leverage, no
borrowing, no short sale, no interest. Nothing here trades.
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import sys
from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import quote

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from aitrader.research.dlab.feeds import checked, get  # noqa: E402
from aitrader.research.events import exfunding as X  # noqa: E402  (the archive's zip and CSV readers)
from aitrader.research.events import stablecoin as C  # noqa: E402
import scripts.sqz1 as Z  # noqa: E402  (the S3 listing reader and the month helpers)
from aitrader.research.registry import Registry, Trial, Use, Verdict, bonferroni_t  # noqa: E402

R = ROOT / "research"
DOC = "research/preregistrations/SCX-1.md"
PROBE = R / "results" / "SCX-1-probe.json"
CODE = ("aitrader/research/events/stablecoin.py", "aitrader/research/events/cascade.py", "scripts/scx1.py",
        "scripts/sqz1.py", "aitrader/research/events/exfunding.py")
BASE = "https://data.binance.vision/"
UNIVERSE = "stablecoin-pairs-weekend"
SPEC = {"program": "SCX-1", "version": C.SCX_VERSION, "universe": UNIVERSE, "pairs": list(C.PAIRS),
        "instrument": "a spot exchange of one stablecoin for another, from a stock of both",
        "thetas": [0.0003, 0.001], "entry_hour_utc": 22, "hold_hours": 23, "late_hours": 1,
        "cost_per_fill": 0.0001, "cost_round_trip": 0.0002, "binance_standard_fill": 0.001,
        "placebo_span_days": 14, "placebo_draws_per_entry": 20, "placebos": 1000, "seed": 20261122, "nw_lag": 1,
        "bar_floor": 3.0,
        "gates": ["t", "costs_x2", "halves", "top5_removed", "late_entry", "beats_placebo", "without_best_week",
                  "without_best_pair", "beats_weekdays"],
        "stages": {
            "dev": {"trial": "SCX-1", "decisions": ["2018-12-16", "2023-06-25"], "tests": 2, "min_events": 40,
                    "min_weeks": 40},
            "validation": {"trial": "SCX-1-V", "after": "SCX-1", "decisions": ["2023-07-02", "2026-10-25"],
                           "tests": 1, "min_events": 30, "min_weeks": 25},
            "forward": {"trial": "SCX-1-F", "after": "SCX-1-V", "decisions": ["2026-12-06", "2027-05-30"],
                        "not_before": "2027-06-10", "tests": 1, "min_events": 10, "min_weeks": 8}}}


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


def spot_url(symbol: str, month: str) -> str:
    q = quote(symbol, safe="")
    return f"{BASE}data/spot/monthly/klines/{q}/1h/{q}-1h-{month}.zip"


def probe(fetch=get, now: datetime | None = None) -> dict:
    """The months of hourly bars each pair has in the archive. File names only: no price is read."""
    now = now or datetime.now(timezone.utc)
    out = {}
    for p in C.PAIRS:
        keys = Z.listing(f"data/spot/monthly/klines/{p}/1h/", fetch)[1]
        out[p] = sorted(k.rsplit("-1h-", 1)[1][:7] for k in keys if k.endswith(".zip") and "-1h-" in k)
    per_stage = {}
    for name, st in SPEC["stages"].items():
        a, b = st["decisions"]
        ms_ = set(Z._months(a, b))
        per_stage[name] = {p: len(ms_ & set(v)) for p, v in out.items()}
        per_stage[name]["sundays"] = len(C.weekdays_in(a, b, 6))
    return {"retrieved": now.isoformat(), "what": "file names only: no price was read",
            "source": "https://data.binance.vision (S3 listing of data/spot/monthly/klines/<pair>/1h/)",
            "pairs": out, "per_stage": per_stage}


def fetch_stage(pairs: dict[str, list[str]], months: list[str], fetch=checked) -> tuple[dict, dict]:
    jobs = [(p, m) for p in sorted(pairs) for m in months if m in pairs[p]]
    bars: dict[str, dict[int, float]] = {p: {} for p in pairs if set(months) & set(pairs[p])}
    man = {"files": 0, "absent": [], "failed": []}

    def one(job):
        p, m = job
        try:
            raw = fetch(spot_url(p, m))
        except RuntimeError as e:
            return job, None, str(e)[:160]
        return job, (X.parse_bars(X.rows(raw)) if raw is not None else None), None
    with ThreadPoolExecutor(max_workers=8) as pool:
        for (p, m), got, err in pool.map(one, jobs):
            if err:
                man["failed"].append(f"{p}:{m}")
            elif got is None:
                man["absent"].append(f"{p}:{m}")
            else:
                man["files"] += 1
                bars[p].update({t: c for t, (c, _q) in got.items()})
    return bars, man


def firewall(bars: dict[str, dict[int, float]], last_ms: int) -> dict[str, dict[int, float]]:
    """Nothing that closes after the stage's last exit reaches the computation."""
    return {p: {t: v for t, v in b.items() if t + C.HOUR <= last_ms} for p, b in bars.items()}


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
    hold, late_h, hr = SPEC["hold_hours"], SPEC["late_hours"], SPEC["entry_hour_utc"]
    first_ms = C.ms_of(a) - (SPEC["placebo_span_days"] + 1) * C.DAY
    last_ms = C.ms_of(b) + (hr + late_h + hold) * C.HOUR  # the last exit's close
    months = Z._months(Z._add_months(a[:7], -1), datetime.fromtimestamp((last_ms - 1) / 1000, timezone.utc).date().isoformat())
    pr = json.loads(probe_file.read_text())
    bars, man = fetch_stage(pr["pairs"], months, fetch)
    if man["failed"]:
        raise SystemExit(f"{len(man['failed'])} archive files did not arrive (the first: {man['failed'][:3]}): "
                         "nothing is judged on a partial panel; the next run asks again")
    bars = firewall(bars, last_ms)
    sundays = C.weekdays_in(a, b, 6)
    wednesdays = C.weekdays_in(a, b, 2)
    bar = max(SPEC["bar_floor"], bonferroni_t(max(1, reg.tests_on(UNIVERSE, date.fromisoformat(a),
                                                                  date.fromisoformat(b) + timedelta(days=1)))))
    cost = SPEC["cost_round_trip"]
    thetas = SPEC["thetas"] if stage == "dev" else [chosen_theta(out_dir)]
    results, kept = {}, {}
    window = (max(first_ms, C.ms_of(a) - SPEC["placebo_span_days"] * C.DAY), last_ms)
    for th in thetas:
        evs = C.entries(bars, sundays, hr, hold, th, cost)
        late = C.entries(bars, sundays, hr, hold, th, cost, lag_hours=late_h)
        contra = C.entries(bars, wednesdays, hr, hold, th, cost)
        plac = C.placebos(bars, evs, hold, th, cost, SPEC["placebo_span_days"], SPEC["placebo_draws_per_entry"],
                          SPEC["seed"], window)
        res = C.judge(evs, late, contra, plac, bar, cost, st["min_events"], st["min_weeks"], SPEC["seed"],
                      SPEC["placebos"], SPEC["nw_lag"])
        std = 2 * SPEC["binance_standard_fill"]  # reported, not gated: the same swaps at Binance's standard fee
        okk = [e for e in evs if not e.get("missing")]
        res["mean_net_at_binance_standard_fees"] = (C._stat([{**e, "net": e["gross"] - std} for e in okk])
                                                    if okk else None)
        results[str(th)] = res
        kept[str(th)] = evs
    passed = [th for th in thetas if results[str(th)]["verdict"] == "PASSED"]
    chosen = max(passed, key=lambda th: results[str(th)]["t"]) if passed else None
    verdict = "PASSED" if passed else ("INCONCLUSIVE" if all(r["verdict"] == "INCONCLUSIVE" for r in results.values())
                                       else "FAILED")
    body = {"program": pid, "stage": stage, "kind": "spot_event_study", "verdict": verdict, "judged": now.isoformat(),
            "code_sha256": code_hash(), "spec_sha256": spec_sha(), "spec": SPEC, "decisions": [a, b], "bar": bar,
            "chosen_theta": chosen if stage == "dev" else thetas[0],
            "last_moment_read": datetime.fromtimestamp(last_ms / 1000, timezone.utc).isoformat(),
            "data": {"source": BASE, "files": man["files"], "absent": len(man["absent"]), "pairs": sorted(bars)},
            "results": results}
    out_dir.mkdir(parents=True, exist_ok=True)
    f = out_dir / f"{pid}.json"
    f.write_text(json.dumps(body, indent=1, sort_keys=True, default=str) + "\n")
    data.mkdir(parents=True, exist_ok=True)
    with gzip.open(data / f"{pid}-events.json.gz", "wt") as g:
        json.dump(kept, g)
    best = results[str(chosen)] if chosen is not None else max(
        results.values(), key=lambda r: r["t"] if r["t"] is not None else -1e9)
    reg.record_verdict(Verdict(pid, now, verdict, {
        "artifact": str(f.relative_to(ROOT)) if f.is_relative_to(ROOT) else str(f), "chosen_theta": body["chosen_theta"],
        "t": best["t"], "mean_net": best["mean_net"], "traded": best["traded"], "weeks": best["weeks"],
        "gates": best.get("gates"), "why": best.get("why")}))
    return body


def chosen_theta(out_dir: Path) -> float:
    art = json.loads((out_dir / "SCX-1.json").read_text())
    if art.get("verdict") != "PASSED" or art.get("chosen_theta") is None:
        raise SystemExit("the later stages use the threshold SCX-1 chose; SCX-1 has not passed")
    return float(art["chosen_theta"])


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
        id=st["trial"], registered=now, title=f"{st['trial']}: stablecoins while their primary market is shut, {stage} stage",
        hypothesis="A stablecoin pair standing at least theta from par at 22:00 UTC on Sunday, swapped into its cheap "
                   "side and back at 21:00 UTC on Monday, earns a positive net return after 1 bp a fill, averaged over "
                   "weeks, more than the same pair at random hours with the same deviation and more than the same rule "
                   "from Wednesday to Thursday.",
        uses=(Use(UNIVERSE, date.fromisoformat(a), date.fromisoformat(b) + timedelta(days=2), "judge"),),
        tests=st["tests"], configurations=len(SPEC["thetas"]) if stage == "dev" else 1, preregistration=DOC,
        design={"code_sha256": h, "spec_sha256": spec_sha(), "stage": stage}))
    print("registered", st["trial"])


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("command", choices=("probe", "hash", "preregister", "run"))
    ap.add_argument("stage", nargs="?", choices=tuple(SPEC["stages"]))
    ap.add_argument("--data", default=str(ROOT / "data" / "scx1"))
    ap.add_argument("--out", default=str(PROBE))
    ap.add_argument("--probe", default=str(PROBE))
    a = ap.parse_args(argv)
    now = datetime.now(timezone.utc)
    if a.command == "hash":
        print(code_hash(), spec_sha())
    elif a.command == "probe":
        body = probe(now=now)
        out = Path(a.out)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(body, indent=1, sort_keys=True) + "\n")
        print(json.dumps(body["per_stage"]))
    elif a.command == "preregister":
        preregister(a.stage, now)
    else:
        body = run(a.stage, Path(a.data), now, probe_file=Path(a.probe))
        print(json.dumps({"program": body["program"], "verdict": body["verdict"],
                          "t": {k: v["t"] for k, v in body["results"].items()}}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
