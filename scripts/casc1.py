"""CASC-1: is a liquidation-led crash bought back? (research/preregistrations/CASC-1.md) Runs on GitHub's runner
(.github/workflows/casc1.yml): Binance's archive is not reachable from the director's session.

    python scripts/casc1.py probe [--out FILE]     # file names only: which months of hourly bars exist
    python scripts/casc1.py hash                   # the code hash the preregistration quotes
    python scripts/casc1.py preregister dev        # each later stage only after the one before PASSED
    python scripts/casc1.py run dev --data DIR     # fetch what the stage needs, judge it once, record the verdict

The traded instrument is SPOT, bought outright: no leverage, no short, no funding. The perpetual's price is
information only (whether the fall was led by forced selling there). Nothing here trades.
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
from aitrader.research.events import cascade as K  # noqa: E402
from aitrader.research.events import exfunding as X  # noqa: E402  (the archive's zip and CSV readers)
import scripts.sqz1 as Z  # noqa: E402  (the S3 listing reader, the coins and their spot pairs)
from aitrader.research.registry import Registry, Trial, Use, Verdict, bonferroni_t  # noqa: E402

R = ROOT / "research"
DOC = "research/preregistrations/CASC-1.md"
PROBE = R / "results" / "CASC-1-probe.json"
COINS = R / "results" / "SQZ-1-probe.json"  # seasoned coins and their spot pairs (file names only)
CODE = ("aitrader/research/events/cascade.py", "scripts/casc1.py", "scripts/sqz1.py")  # sqz1: its readers
BASE = "https://data.binance.vision/"
UNIVERSE = "crypto-spot-liquidation-falls"
SPEC = {"program": "CASC-1", "version": K.CASC_VERSION, "universe": UNIVERSE, "instrument": "spot, bought outright",
        "drops": [0.08, 0.15], "perp_discount": 0.005, "look_hours": K.LOOK, "hold_hours": K.HOLD, "late_hours": 1,
        "cost_per_side": 0.0025, "placebo_span_hours": 168, "placebo_draws_per_entry": 40, "placebos": 1000,
        "seed": 20261115, "nw_lag": 1, "bar_floor": 3.0,
        "gates": ["t", "costs_x2", "halves", "top5_removed", "late_entry", "beats_placebo", "without_best_day",
                  "without_best_coin", "beats_spot_led_falls"],
        "stages": {
            "dev": {"trial": "CASC-1", "decisions": ["2023-07-01", "2025-02-28"], "tests": 2, "min_events": 150, "min_days": 40},
            "validation": {"trial": "CASC-1-V", "after": "CASC-1", "decisions": ["2025-03-08", "2026-10-29"], "tests": 1,
                           "min_events": 150, "min_days": 40},
            "forward": {"trial": "CASC-1-F", "after": "CASC-1-V", "decisions": ["2026-12-01", "2027-05-29"],
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


def ms(d: str) -> int:
    return int(datetime.fromisoformat(d).replace(tzinfo=timezone.utc).timestamp() * 1000)


def url(kind: str, symbol: str, month: str) -> str:
    q = quote(symbol, safe="")
    if kind == "perp":
        return f"{BASE}data/futures/um/monthly/klines/{q}/1h/{q}-1h-{month}.zip"
    return f"{BASE}data/spot/monthly/klines/{q}/1h/{q}-1h-{month}.zip"


def parse_hourly(rs: list[list[str]]) -> dict[int, float]:
    """{bar open time in ms: close} of a month of hourly klines; unreadable rows skipped, never repaired."""
    out = {}
    for r in rs:
        if len(r) > 4 and r[0].strip()[:1].isdigit():
            try:
                t, c = X.ms(r[0]), float(r[4])
            except ValueError:
                continue
            if c > 0:
                out[t] = c
    return out


def probe(fetch=get, now: datetime | None = None, coins_file: Path = COINS) -> dict:
    """Which months of hourly bars exist for each seasoned coin's spot pair and perpetual. File names only."""
    now = now or datetime.now(timezone.utc)
    coins = json.loads(coins_file.read_text())["coins"]

    def months(s):
        sp = Z.listing(f"data/spot/monthly/klines/{coins[s]['spot']}/1h/", fetch)[1]
        pp = Z.listing(f"data/futures/um/monthly/klines/{s}/1h/", fetch)[1]
        f = lambda keys: sorted(k.rsplit("-1h-", 1)[1][:7] for k in keys if k.endswith(".zip") and "-1h-" in k)
        return s, f(sp), f(pp)
    out = {}
    with ThreadPoolExecutor(max_workers=16) as pool:
        for s, a, b in pool.map(months, sorted(coins)):
            out[s] = {"spot": coins[s]["spot"], "seasoned": coins[s]["seasoned"], "spot_1h": a, "perp_1h": b}
    st = SPEC["stages"]
    both = {name: sum(1 for v in out.values() if set(Z._months(st[name]["decisions"][0], st[name]["decisions"][1])) & set(v["spot_1h"]) & set(v["perp_1h"]))
            for name in ("dev", "validation")}
    return {"retrieved": now.isoformat(), "source": "https://data.binance.vision (S3 listing)",
            "what": "file names only: which months of hourly spot and perpetual bars exist. No price was read",
            "coins": out, "coins_with_both_in_window": both}


def fetch_panel(coins: dict, months: list[str], t0: int, hours: int, fetch=checked) -> tuple[K.Panel, dict]:
    jobs = [(s, kind, m) for s in sorted(coins) for m in months for kind in ("spot", "perp")
            if m in coins[s]["spot_1h" if kind == "spot" else "perp_1h"]]
    panel = K.Panel(sorted(coins), t0, hours, {s: ms(v["seasoned"]) for s, v in coins.items()})
    man = {"files": 0, "absent": [], "failed": []}

    def one(job):
        s, kind, m = job
        try:
            raw = fetch(url(kind, coins[s]["spot"] if kind == "spot" else s, m))
        except RuntimeError as e:
            return job, None, str(e)[:160]
        return job, (parse_hourly(X.rows(raw)) if raw is not None else None), None
    with ThreadPoolExecutor(max_workers=16) as pool:
        for (s, kind, m), got, err in pool.map(one, jobs):
            if err:
                man["failed"].append(f"{s}:{kind}:{m}")
            elif got is None:
                man["absent"].append(f"{s}:{kind}:{m}")
            else:
                man["files"] += 1
                panel.put(kind, s, got)
    return panel, man


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
    t0 = ms(first_month + "-01")
    last_ms = ms(b) + 86_400_000 + (K.HOLD + SPEC["late_hours"]) * K.HOUR  # the last exit's close
    hours = (last_ms - t0) // K.HOUR
    months = Z._months(first_month, datetime.fromtimestamp((last_ms - 1) / 1000, timezone.utc).date().isoformat())
    coins = json.loads(probe_file.read_text())["coins"]
    panel, man = fetch_panel(coins, months, t0, hours, fetch)  # the grid ends at the last exit: nothing later fits
    if man["failed"]:
        raise SystemExit(f"{len(man['failed'])} archive files did not arrive (the first: {man['failed'][:3]}): "
                         "nothing is judged on a partial panel")
    first_h, last_h = (ms(a) - t0) // K.HOUR, (ms(b) + 86_400_000 - t0) // K.HOUR - 1
    bar = max(SPEC["bar_floor"], bonferroni_t(max(1, reg.tests_on(UNIVERSE, date.fromisoformat(a), date.fromisoformat(b) + timedelta(days=1)))))
    cost, prem = SPEC["cost_per_side"], SPEC["perp_discount"]
    drops = SPEC["drops"] if stage == "dev" else [chosen_drop(out_dir)]
    results, kept = {}, {}
    for d in drops:
        evs = K.events(panel, first_h, last_h, d, prem, cost)
        late = K.events(panel, first_h, last_h, d, prem, cost, lag=SPEC["late_hours"])
        contra = K.contrast(panel, first_h, last_h, d, prem, cost)
        plac = K.placebos(panel, evs, d, cost, SPEC["placebo_span_hours"], SPEC["placebo_draws_per_entry"], SPEC["seed"])
        results[str(d)] = K.judge(panel, evs, late, contra, plac, bar, cost, st["min_events"], st["min_days"],
                                  SPEC["seed"], SPEC["placebos"], SPEC["nw_lag"])
        kept[str(d)] = evs
    passed = [d for d in drops if results[str(d)]["verdict"] == "PASSED"]
    chosen = max(passed, key=lambda d: results[str(d)]["t"]) if passed else None
    verdict = "PASSED" if passed else ("INCONCLUSIVE" if all(r["verdict"] == "INCONCLUSIVE" for r in results.values()) else "FAILED")
    body = {"program": pid, "stage": stage, "kind": "spot_event_study", "verdict": verdict, "judged": now.isoformat(),
            "code_sha256": code_hash(), "spec_sha256": spec_sha(), "spec": SPEC, "decisions": [a, b], "bar": bar,
            "chosen_drop": chosen if stage == "dev" else drops[0],
            "last_moment_read": datetime.fromtimestamp(last_ms / 1000, timezone.utc).isoformat(),
            "data": {"source": BASE, "files": man["files"], "absent": len(man["absent"]), "coins": len(panel.coins)},
            "results": results}
    out_dir.mkdir(parents=True, exist_ok=True)
    f = out_dir / f"{pid}.json"
    f.write_text(json.dumps(body, indent=1, sort_keys=True, default=str) + "\n")
    data.mkdir(parents=True, exist_ok=True)
    with gzip.open(data / f"{pid}-events.json.gz", "wt") as g:
        json.dump(kept, g)
    best = results[str(chosen)] if chosen is not None else max(results.values(), key=lambda r: r["t"] if r["t"] is not None else -1e9)
    reg.record_verdict(Verdict(pid, now, verdict, {
        "artifact": str(f.relative_to(ROOT)) if f.is_relative_to(ROOT) else str(f), "chosen_drop": body["chosen_drop"],
        "t": best["t"], "mean_net": best["mean_net"], "traded": best["traded"], "days": best["days"],
        "gates": best.get("gates"), "why": best.get("why")}))
    return body


def chosen_drop(out_dir: Path) -> float:
    art = json.loads((out_dir / "CASC-1.json").read_text())
    if art.get("verdict") != "PASSED" or art.get("chosen_drop") is None:
        raise SystemExit("the later stages use the fall CASC-1 chose; CASC-1 has not passed")
    return float(art["chosen_drop"])


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
        id=st["trial"], registered=now, title=f"{st['trial']}: liquidation-led falls and the spot buyer, {stage} stage",
        hypothesis="A seasoned coin whose spot fell at least X in four hours while its perpetual closed at least 0.5% "
                   "below spot, bought on spot at that close and sold 24 hours later, earns a positive net return "
                   "after 0.25% a side, averaged over days, more than the same coin at hours it had not fallen and "
                   "more than falls led by spot.",
        uses=(Use(UNIVERSE, date.fromisoformat(a), date.fromisoformat(b) + timedelta(days=1), "judge"),),
        tests=st["tests"], configurations=len(SPEC["drops"]) if stage == "dev" else 1, preregistration=DOC,
        design={"code_sha256": h, "spec_sha256": spec_sha(), "stage": stage}))
    print("registered", st["trial"])


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("command", choices=("probe", "hash", "preregister", "run"))
    ap.add_argument("stage", nargs="?", choices=tuple(SPEC["stages"]))
    ap.add_argument("--data", default=str(ROOT / "data" / "casc1"))
    ap.add_argument("--out", default=str(PROBE))
    ap.add_argument("--probe", default=str(PROBE))
    ap.add_argument("--coins", default=str(COINS))
    a = ap.parse_args(argv)
    now = datetime.now(timezone.utc)
    if a.command == "hash":
        print(code_hash(), spec_sha())
    elif a.command == "probe":
        body = probe(now=now, coins_file=Path(a.coins))
        out = Path(a.out)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(body, indent=1, sort_keys=True) + "\n")
        print(json.dumps({"coins": len(body["coins"]), "with_both": body["coins_with_both_in_window"]}))
    elif a.command == "preregister":
        preregister(a.stage, now)
    else:
        body = run(a.stage, Path(a.data), now, probe_file=Path(a.probe))
        print(json.dumps({"program": body["program"], "verdict": body["verdict"], "chosen": body["chosen_drop"],
                          "results": {k: {x: v.get(x) for x in ("traded", "days", "mean_net", "t", "verdict", "gates")}
                                      for k, v in body["results"].items()}}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
