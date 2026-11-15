"""SQZ-1: do crowded shorts pay the spot buyer? (research/preregistrations/SQZ-1.md) Runs on GitHub's runner
(.github/workflows/sqz1.yml): Binance's archive is not reachable from the director's session.

    python scripts/sqz1.py probe [--out FILE]      # file names, and the funding rates that define the signal
    python scripts/sqz1.py hash                    # the code hash the preregistration quotes
    python scripts/sqz1.py preregister dev         # each later stage only after the one before PASSED
    python scripts/sqz1.py run dev --data DIR      # fetch what the stage needs, judge it once, record the verdict

The traded instrument is SPOT, bought outright: no leverage, no short, no funding paid or received. The perpetual's
funding is information only. Nothing here trades.
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import sys
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import quote

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from aitrader.research.dlab.feeds import checked, get  # noqa: E402
from aitrader.research.events import exfunding as X  # noqa: E402  (the archive's zip and CSV readers)
from aitrader.research.events import squeeze as Q  # noqa: E402
from aitrader.research.registry import Registry, Trial, Use, Verdict, bonferroni_t  # noqa: E402

R = ROOT / "research"
DOC = "research/preregistrations/SQZ-1.md"
PROBE = R / "results" / "SQZ-1-probe.json"
PERPS = R / "results" / "EXF-1-probe.json"  # the USDT-M perpetuals and their funding months (file names)
CODE = ("aitrader/research/events/squeeze.py", "scripts/sqz1.py")
BASE = "https://data.binance.vision/"
LISTING = "https://s3-ap-northeast-1.amazonaws.com/data.binance.vision?delimiter=/&prefix={prefix}{marker}"
NS = "{http://s3.amazonaws.com/doc/2006-03-01/}"
UNIVERSE = "crypto-spot-crowded-shorts"
PREFIXES = ("1000000", "1000", "1M")
SPEC = {"program": "SQZ-1", "version": Q.SQZ_VERSION, "universe": UNIVERSE, "instrument": "spot, bought outright",
        "thresholds": [0.0003, 0.0005, 0.001], "hold_days": 7, "late_lag_days": 1, "cost_per_side": 0.0015,
        "seasoned_after_months": 7, "placebo_span_days": 30, "placebos": 1000, "seed": 20261115, "nw_lag": 2,
        "bar_floor": 3.0,
        "gates": ["t", "costs_x2", "halves", "top5_removed", "late_entry", "beats_placebo", "without_best_year",
                  "without_best_coin"],
        "stages": {
            "dev": {"trial": "SQZ-1", "entries": ["2021-01-01", "2023-06-30"], "tests": 3, "min_events": 300, "min_weeks": 52},
            "validation": {"trial": "SQZ-1-V", "after": "SQZ-1", "entries": ["2023-07-08", "2025-06-30"], "tests": 1,
                           "min_events": 300, "min_weeks": 52},
            "holdout": {"trial": "SQZ-1-H", "after": "SQZ-1-V", "entries": ["2025-07-08", "2026-10-24"], "tests": 1,
                        "min_events": 100, "min_weeks": 20},
            "forward": {"trial": "SQZ-1-F", "after": "SQZ-1-H", "entries": ["2026-12-01", "2027-05-24"],
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


def _months(a: str, b: str) -> list[str]:
    y, m, out = int(a[:4]), int(a[5:7]), []
    while f"{y:04d}-{m:02d}" <= b[:7]:
        out.append(f"{y:04d}-{m:02d}")
        y, m = (y + 1, 1) if m == 12 else (y, m + 1)
    return out


def _add_months(m: str, k: int) -> str:
    y, mm = int(m[:4]), int(m[5:7]) - 1 + k
    return f"{y + mm // 12:04d}-{mm % 12 + 1:02d}"


def spot_of(perp: str, spots: set[str]) -> str | None:
    """The spot pair a USDT-M perpetual's coin trades as, if Binance lists one (1000PEPEUSDT -> PEPEUSDT)."""
    for c in [perp] + [perp[len(p):] for p in PREFIXES if perp.startswith(p)]:
        if c in spots:
            return c
    return None


def seasoned_from(first_month: str, months: int) -> str:
    """The first day on which a contract first seen in `first_month` is at least `months` months old."""
    return _add_months(first_month, months) + "-01"


# ── the archive ─────────────────────────────────────────────────────────────

def url(kind: str, symbol: str, month: str) -> str:
    q = quote(symbol, safe="")
    if kind == "fundingRate":
        return f"{BASE}data/futures/um/monthly/fundingRate/{q}/{q}-fundingRate-{month}.zip"
    return f"{BASE}data/spot/monthly/klines/{q}/1d/{q}-1d-{month}.zip"


def parse_listing(body: bytes) -> tuple[list[str], list[str], str | None]:
    root = ET.fromstring(body)
    prefixes = [p.text for p in root.iter(NS + "Prefix") if p.text and p.text.endswith("/") and p.text != root.findtext(NS + "Prefix")]
    keys = [k.text for k in root.iter(NS + "Key") if k.text]
    truncated = (root.findtext(NS + "IsTruncated") or "false").lower() == "true"
    nxt = root.findtext(NS + "NextMarker") or (prefixes[-1] if prefixes else keys[-1] if keys else None)
    return prefixes, keys, nxt if truncated else None


def listing(prefix: str, fetch=get) -> tuple[list[str], list[str]]:
    prefixes, keys, marker = [], [], ""
    while True:
        body = fetch(LISTING.format(prefix=quote(prefix, safe="/"), marker=f"&marker={quote(marker, safe='/')}" if marker else ""))
        if body is None:
            raise RuntimeError(f"no listing for {prefix}")
        p, k, nxt = parse_listing(body)
        prefixes, keys = prefixes + p, keys + k
        if not nxt:
            return prefixes, keys
        marker = nxt


def parse_closes(rs: list[list[str]]) -> dict[str, float]:
    """{UTC day: close} of a month of daily spot klines; unreadable rows skipped, never repaired."""
    out = {}
    for r in rs:
        if len(r) > 4 and r[0].strip()[:1].isdigit():
            try:
                d, c = X.ms(r[0]), float(r[4])
            except ValueError:
                continue
            if c > 0:
                out[Q.iso(d)] = c
    return out


def universe(perps: dict, fetch=get) -> dict[str, dict]:
    """Every USDT-M perpetual whose coin Binance also lists as a spot pair against USDT, with its spot pair, the
    day it counts as seasoned and the months of spot klines that exist. File names only."""
    base = "data/spot/monthly/klines/"
    spots = {p[len(base):].strip("/") for p in listing(base, fetch)[0]}
    out = {}
    for s, v in sorted(perps.items()):
        sp = spot_of(s, spots)
        if sp and v.get("funding"):
            out[s] = {"spot": sp, "seasoned": seasoned_from(v["funding"][0], SPEC["seasoned_after_months"]),
                      "funding": v["funding"]}

    def months(s):
        _, keys = listing(f"{base}{out[s]['spot']}/1d/", fetch)
        return s, sorted(k.rsplit("-1d-", 1)[1][:7] for k in keys if k.endswith(".zip") and "-1d-" in k)
    with ThreadPoolExecutor(max_workers=16) as pool:
        for s, ms in pool.map(months, list(out)):
            out[s]["klines"] = ms
    return out


def fetch_all(coins: dict, months: list[str], fetch=checked) -> tuple[dict, dict, dict]:
    """The funding settlements and the spot closes of every coin for the months asked."""
    jobs = [(s, kind, m) for s in sorted(coins) for m in months for kind in ("fundingRate", "spot")
            if m in coins[s]["funding" if kind == "fundingRate" else "klines"]]

    def one(job):
        s, kind, m = job
        try:
            raw = fetch(url(kind, s if kind == "fundingRate" else coins[s]["spot"], m))
        except RuntimeError as e:
            return job, None, str(e)[:160]
        if raw is None:
            return job, None, None
        rows = X.rows(raw)
        return job, (X.parse_settlements(rows) if kind == "fundingRate" else parse_closes(rows)), None
    settle: dict[str, dict[int, float]] = {}
    spot: dict[str, dict[str, float]] = {}
    man = {"files": 0, "absent": [], "failed": []}
    with ThreadPoolExecutor(max_workers=16) as pool:
        for (s, kind, m), got, err in pool.map(one, jobs):
            if err:
                man["failed"].append(f"{s}:{kind}:{m}")
            elif got is None:
                man["absent"].append(f"{s}:{kind}:{m}")
            else:
                man["files"] += 1
                (settle.setdefault(s, {}).update(dict(got)) if kind == "fundingRate" else spot.setdefault(s, {}).update(got))
    return {s: sorted(v.items()) for s, v in settle.items()}, spot, man


# ── the probe ───────────────────────────────────────────────────────────────

def probe(fetch=get, fetch_checked=checked, now: datetime | None = None, perps: Path = PERPS) -> dict:
    """File names, and the funding rates of the dev and validation windows (the signal): no spot price is read."""
    now = now or datetime.now(timezone.utc)
    coins = universe(json.loads(perps.read_text())["um"], fetch)
    st = SPEC["stages"]
    months = _months(_add_months(st["dev"]["entries"][0][:7], -1), st["validation"]["entries"][1])
    jobs = {s: {**v, "klines": []} for s, v in coins.items()}  # funding only: no spot file is fetched here
    settle, _, man = fetch_all(jobs, months, fetch_checked)
    counts: dict[str, dict[str, int]] = {}
    for s, xs in settle.items():
        fd = Q.Funding(xs)
        d = max(coins[s]["seasoned"], st["dev"]["entries"][0])
        while d <= st["validation"]["entries"][1]:
            f = fd.signal(Q.day_ms(d))
            if f is not None and d[:7] in coins[s]["klines"]:
                y = counts.setdefault(d[:4], {"days": 0})
                y["days"] += 1
                for th in SPEC["thresholds"]:
                    if f <= -th:
                        y[str(th)] = y.get(str(th), 0) + 1
            d = Q.plus(d, 1)
    return {"retrieved": now.isoformat(), "source": "https://data.binance.vision (S3 listing)",
            "what": "file names; the USDT-M funding rates of 2020-12 to 2025-06 only. No spot price was read",
            "coins": coins, "funding_files": man["files"], "funding_absent": len(man["absent"]),
            "funding_failed": man["failed"], "signal_days_by_year": counts}


# ── a stage ─────────────────────────────────────────────────────────────────

def chosen_threshold(out_dir: Path) -> float:
    art = json.loads((out_dir / "SQZ-1.json").read_text())
    if art.get("verdict") != "PASSED" or art.get("chosen_threshold") is None:
        raise SystemExit("the later stages use the threshold SQZ-1 chose; SQZ-1 has not passed")
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
    settle, spot, man = fetch_all(coins, _months(_add_months(a[:7], -2), last_exit), fetch)
    if man["failed"]:
        raise SystemExit(f"{len(man['failed'])} archive files did not arrive (the first: {man['failed'][:3]}): "
                         "nothing is judged on a partial panel")
    cut = Q.day_ms(b) + Q.DAY  # no funding settled after the last entry day, no close after the last exit
    settle = {s: [(t, f) for t, f in xs if t < cut] for s, xs in settle.items()}
    spot = {s: {d: v for d, v in xs.items() if d <= last_exit} for s, xs in spot.items()}
    fund = {s: Q.Funding(xs) for s, xs in settle.items()}
    seasoned = {s: v["seasoned"] for s, v in coins.items()}
    bench = Q.Bench(spot, seasoned)
    bar = max(SPEC["bar_floor"], bonferroni_t(max(1, reg.tests_on(UNIVERSE, date.fromisoformat(a), date.fromisoformat(b) + timedelta(days=1)))))
    cost = SPEC["cost_per_side"]
    ths = SPEC["thresholds"] if stage == "dev" else [chosen_threshold(out_dir)]
    results, kept = {}, {}
    for th in ths:
        evs = Q.events(fund, spot, seasoned, bench, a, b, th, cost, SPEC["hold_days"])
        late = Q.events(fund, spot, seasoned, bench, a, b, th, cost, SPEC["hold_days"], lag=SPEC["late_lag_days"])
        plac = Q.placebos(fund, spot, seasoned, bench, evs, th, cost, SPEC["hold_days"], SPEC["placebo_span_days"])
        results[str(th)] = Q.judge(evs, late, plac, bar, cost, st["min_events"], st["min_weeks"], SPEC["seed"],
                                   SPEC["placebos"], SPEC["nw_lag"])
        kept[str(th)] = evs
    passed = [th for th in ths if results[str(th)]["verdict"] == "PASSED"]
    chosen = max(passed, key=lambda th: results[str(th)]["t"]) if passed else None
    verdict = "PASSED" if passed else ("INCONCLUSIVE" if all(r["verdict"] == "INCONCLUSIVE" for r in results.values()) else "FAILED")
    body = {"program": pid, "stage": stage, "kind": "spot_event_study", "verdict": verdict, "judged": now.isoformat(),
            "code_sha256": code_hash(), "spec_sha256": spec_sha(), "spec": SPEC, "entries": [a, b], "bar": bar,
            "chosen_threshold": chosen if stage == "dev" else ths[0], "last_day_read": last_exit,
            "data": {"source": BASE, "files": man["files"], "absent": len(man["absent"]), "coins_with_spot": len(spot)},
            "results": results}
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
        id=st["trial"], registered=now, title=f"{st['trial']}: crowded shorts and the spot buyer, {stage} stage",
        hypothesis="A coin whose USDT-M perpetual paid its longs at least theta per 8 hours over the last 72 hours "
                   "(crowded shorts), bought on spot and held seven days, beats the equal-weight spot return of "
                   "every seasoned coin over the same days after 0.15% a side, averaged over weekly cohorts.",
        uses=(Use(UNIVERSE, date.fromisoformat(a), date.fromisoformat(b) + timedelta(days=1), "judge"),),
        tests=st["tests"], configurations=len(SPEC["thresholds"]) if stage == "dev" else 1, preregistration=DOC,
        design={"code_sha256": h, "spec_sha256": spec_sha(), "stage": stage}))
    print("registered", st["trial"])


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("command", choices=("probe", "hash", "preregister", "run"))
    ap.add_argument("stage", nargs="?", choices=tuple(SPEC["stages"]))
    ap.add_argument("--data", default=str(ROOT / "data" / "sqz1"))
    ap.add_argument("--out", default=str(PROBE))
    ap.add_argument("--probe", default=str(PROBE))
    ap.add_argument("--perps", default=str(PERPS), help="probe: the USDT-M contracts' file listing (EXF-1's probe)")
    a = ap.parse_args(argv)
    now = datetime.now(timezone.utc)
    if a.command == "hash":
        print(code_hash(), spec_sha())
    elif a.command == "probe":
        body = probe(now=now, perps=Path(a.perps))
        out = Path(a.out)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(body, indent=1, sort_keys=True) + "\n")
        print(json.dumps({"coins": len(body["coins"]), "funding_files": body["funding_files"],
                          "signal_days_by_year": body["signal_days_by_year"]}))
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
