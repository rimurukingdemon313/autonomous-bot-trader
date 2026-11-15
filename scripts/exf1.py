"""EXF-1: do perpetual futures price their discrete funding payments? (research/preregistrations/EXF-1.md)
Runs on GitHub's runner (.github/workflows/exf1.yml): Binance's archive is not reachable from the director's session.

    python scripts/exf1.py probe [--out FILE] [--no-funding]   # file names, and the funding rates (no price, no bar)
    python scripts/exf1.py hash                                # the code hash the preregistration quotes
    python scripts/exf1.py preregister dev                     # each later stage only after the one before PASSED
    python scripts/exf1.py run dev --data DIR                  # fetch what the stage needs, judge it once, record it

Stages, in order, each judged once: dev (USDT-M 2021-2023, chooses the threshold), validation (USDT-M 2024-2025),
holdout (USDT-M 2026-01 to 2026-10, sealed), replication (COIN-M 2021-2025, other contracts and other holders) and
forward (USDT-M settlements after the registration). Nothing here trades.
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
from aitrader.research.events import exfunding as X  # noqa: E402
from aitrader.research.registry import Registry, Trial, Use, Verdict, bonferroni_t  # noqa: E402

R = ROOT / "research"
DOC = "research/preregistrations/EXF-1.md"
PROBE = R / "results" / "EXF-1-probe.json"
CODE = ("aitrader/research/events/exfunding.py", "scripts/exf1.py")
BASE = "https://data.binance.vision/"
LISTING = "https://s3-ap-northeast-1.amazonaws.com/data.binance.vision?delimiter=/&prefix={prefix}{marker}"
NS = "{http://s3.amazonaws.com/doc/2006-03-01/}"
UNIVERSES = {"um": "crypto-perp-funding-settlements", "cm": "crypto-coinm-funding-settlements"}
#: bases that are dollars: their funding and premium are another market's
STABLE = ("USDC", "BUSD", "TUSD", "FDUSD", "USDP", "DAI", "USDE", "PYUSD", "UST", "USD1", "EUR")
#: Everything that decides the result, frozen with the code. A change is a new registration, never an edit.
SPEC = {"program": "EXF-1", "version": X.EXF_VERSION, "universes": UNIVERSES, "bars": "5m",
        "thresholds": [0.0005, 0.001, 0.002, 0.005], "select_floor": 0.0005, "cost_per_fill": 0.0010,
        "min_quote_volume": 100000.0, "nw_lag": 2, "placebos": 1000, "seed": 20261115, "bar_floor": 3.0,
        "gates": ["t", "costs_x2", "halves", "top5_removed", "early_entry", "beats_placebo", "without_best_year",
                  "without_best_symbol"],
        "stages": {
            "dev": {"trial": "EXF-1", "venue": "um", "settlements": ["2021-01-01", "2023-12-31"], "tests": 4,
                    "min_events": 300, "min_weeks": 52},
            "validation": {"trial": "EXF-1-V", "after": "EXF-1", "venue": "um", "settlements": ["2024-01-01", "2025-12-31"],
                           "tests": 1, "min_events": 300, "min_weeks": 52},
            "holdout": {"trial": "EXF-1-H", "after": "EXF-1-V", "venue": "um", "settlements": ["2026-01-01", "2026-10-31"],
                        "tests": 1, "min_events": 100, "min_weeks": 20},
            "replication": {"trial": "EXF-1-R", "after": "EXF-1-H", "venue": "cm", "settlements": ["2021-01-01", "2025-12-31"],
                            "tests": 1, "min_events": 100, "min_weeks": 26},
            "forward": {"trial": "EXF-1-F", "after": "EXF-1-R", "venue": "um", "settlements": ["2026-11-23", "2027-03-28"],
                        "not_before": "2027-04-10", "tests": 1, "min_events": 100, "min_weeks": 10}}}


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


def _ms(d: str) -> int:
    return int(datetime.fromisoformat(d).replace(tzinfo=timezone.utc).timestamp() * 1000)


def _months(a: str, b: str) -> list[str]:
    y, m, out = int(a[:4]), int(a[5:7]), []
    while f"{y:04d}-{m:02d}" <= b[:7]:
        out.append(f"{y:04d}-{m:02d}")
        y, m = (y + 1, 1) if m == 12 else (y, m + 1)
    return out


def _prev_month(m: str) -> str:
    y, mm = int(m[:4]), int(m[5:7])
    return f"{y - 1:04d}-12" if mm == 1 else f"{y:04d}-{mm - 1:02d}"


def _month_of(t: int) -> str:
    return datetime.fromtimestamp(t / 1000, timezone.utc).strftime("%Y-%m")


# ── the archive's addresses ─────────────────────────────────────────────────

def index_name(venue: str, symbol: str) -> str:
    """The index a contract is priced against: USDT-M indices carry the contract's name; a COIN-M perpetual's
    index is its pair (BTCUSD_PERP -> BTCUSD)."""
    return symbol.split("_")[0] if venue == "cm" else symbol


def url(venue: str, kind: str, symbol: str, month: str) -> str:
    q = quote(symbol, safe="")
    if kind == "fundingRate":
        return f"{BASE}data/futures/{venue}/monthly/fundingRate/{q}/{q}-fundingRate-{month}.zip"
    if kind == "index":
        i = quote(index_name(venue, symbol), safe="")
        return f"{BASE}data/futures/{venue}/monthly/indexPriceKlines/{i}/5m/{i}-5m-{month}.zip"
    return f"{BASE}data/futures/{venue}/monthly/klines/{q}/5m/{q}-5m-{month}.zip"


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


def _file_months(keys: list[str], tag: str) -> list[str]:
    return sorted(k.rsplit(tag, 1)[1][:7] for k in keys if k.endswith(".zip") and tag in k)


def contracts(venue: str, fetch=get) -> dict[str, dict[str, list[str]]]:
    """Every perpetual of a venue that has funding files, with the months that exist of its funding, its 5-minute
    klines and its index's 5-minute klines. File names only."""
    base = f"data/futures/{venue}/monthly/fundingRate/"
    syms, _ = listing(base, fetch)
    out = {}
    for p in syms:
        s = p[len(base):].strip("/")
        if venue == "um" and (not s.endswith("USDT") or s[:-4] in STABLE):
            continue
        if venue == "cm" and not s.endswith("_PERP"):
            continue
        out[s] = {"funding": _file_months(listing(f"{base}{s}/", fetch)[1], "-fundingRate-")}
    def avail(s: str) -> tuple[str, list[str], list[str]]:
        k = _file_months(listing(f"data/futures/{venue}/monthly/klines/{s}/5m/", fetch)[1], "-5m-")
        i = _file_months(listing(f"data/futures/{venue}/monthly/indexPriceKlines/{index_name(venue, s)}/5m/", fetch)[1], "-5m-")
        return s, k, i
    with ThreadPoolExecutor(max_workers=16) as pool:
        for s, k, i in pool.map(avail, sorted(out)):
            out[s].update(klines=k, index=i)
    return out


# ── funding, and the plan of what bars a stage needs ───────────────────────

def fetch_funding(venue: str, cons: dict, months: list[str], fetch=checked) -> tuple[dict, dict]:
    """{symbol: [(T, rate)]} for the months asked, and {"absent": [...], "failed": [...]}."""
    jobs = [(s, m) for s in sorted(cons) for m in months if m in cons[s].get("funding", [])]
    def one(job):
        s, m = job
        try:
            raw = fetch(url(venue, "fundingRate", s, m))
            return job, (X.parse_settlements(X.rows(raw)) if raw is not None else None), None
        except RuntimeError as e:
            return job, None, str(e)[:160]
    out: dict[str, dict[int, float]] = {}
    man = {"absent": [], "failed": [], "files": 0}
    with ThreadPoolExecutor(max_workers=16) as pool:
        for (s, m), got, err in pool.map(one, jobs):
            if err:
                man["failed"].append(f"{s}:{m}")
            elif got is None:
                man["absent"].append(f"{s}:{m}")
            else:
                man["files"] += 1
                out.setdefault(s, {}).update(dict(got))
    return {s: sorted(v.items()) for s, v in out.items()}, man


def plan(settle: dict[str, list[tuple[int, float]]], a: int, b: int, floor: float) -> dict[str, list[str]]:
    """For each contract, the months of bars the stage needs: those of every settlement in [a, b] whose prediction
    (the previous settlement's rate) reaches the floor, and of the interval before it (its entry and its placebos)."""
    need: dict[str, set[str]] = {}
    for s, xs in settle.items():
        for (t0, f0), (t, _) in zip(xs, xs[1:]):
            if a <= t <= b and abs(f0) >= floor and 0 < t - t0 <= X.MAX_GAP:
                need.setdefault(s, set()).update({_month_of(t), _month_of(t0)})
    return {s: sorted(v) for s, v in sorted(need.items())}


def fetch_bars(venue: str, s: str, months: list[str], cons: dict, fetch=checked) -> tuple[dict, dict, dict]:
    perp: dict[int, tuple[float, float]] = {}
    index: dict[int, tuple[float, float]] = {}
    man = {"absent": [], "failed": [], "files": 0}
    for m in months:
        for kind, into, have in (("klines", perp, cons[s].get("klines", [])), ("index", index, cons[s].get("index", []))):
            if m not in have:
                man["absent"].append(f"{s}:{kind}:{m}")
                continue
            try:
                raw = fetch(url(venue, kind, s, m))
            except RuntimeError as e:
                man["failed"].append(f"{s}:{kind}:{m}: {str(e)[:120]}")
                continue
            if raw is None:
                man["absent"].append(f"{s}:{kind}:{m}")
                continue
            man["files"] += 1
            into.update(X.parse_bars(X.rows(raw)))
    return perp, index, man


# ── the probe ───────────────────────────────────────────────────────────────

def probe(fetch=get, fetch_checked=checked, now: datetime | None = None, read_funding: bool = True) -> dict:
    """File names for both venues; and, unless asked not to, the USDT-M funding rates of the dev and validation
    windows (the payments, which define the events: no price, premium or index bar is read)."""
    now = now or datetime.now(timezone.utc)
    body = {"retrieved": now.isoformat(), "source": "https://data.binance.vision (S3 listing)",
            "what": "file names of both venues; the USDT-M funding rates of 2020-12 to 2025-12 only. No bar was read",
            "um": contracts("um", fetch), "cm": contracts("cm", fetch)}
    if read_funding:
        st = SPEC["stages"]
        months = _months(_prev_month(st["dev"]["settlements"][0][:7]), st["validation"]["settlements"][1])
        settle, man = fetch_funding("um", body["um"], months, fetch_checked)
        counts: dict[str, dict[str, int]] = {}
        for xs in settle.values():
            for (t0, f0), (t, _) in zip(xs, xs[1:]):
                if 0 < t - t0 <= X.MAX_GAP:
                    y = _month_of(t)[:4]
                    for th in SPEC["thresholds"]:
                        if abs(f0) >= th:
                            counts.setdefault(y, {}).setdefault(str(th), 0)
                            counts[y][str(th)] += 1
                    counts.setdefault(y, {}).setdefault("all", 0)
                    counts[y]["all"] += 1
        plans = {}
        for name in ("dev", "validation"):
            a, b = st[name]["settlements"]
            p = plan(settle, _ms(a), _ms(b) + 86_399_999, SPEC["select_floor"])
            plans[name] = {"symbols": len(p), "symbol_months": sum(len(v) for v in p.values()),
                           "with_both_bar_files": sum(1 for s, ms_ in p.items() for m in ms_
                                                      if m in body["um"][s].get("klines", []) and m in body["um"][s].get("index", []))}
        body.update(funding_files=man["files"], funding_absent=len(man["absent"]), funding_failed=man["failed"],
                    predictions_by_year=counts, bar_plan=plans)
    return body


# ── a stage ─────────────────────────────────────────────────────────────────

def horizon(stage: str) -> tuple[int, int]:
    a, b = SPEC["stages"][stage]["settlements"]
    return _ms(a), _ms(b) + 86_399_999


def chosen_threshold(out_dir: Path) -> float:
    art = json.loads((out_dir / "EXF-1.json").read_text())
    th = art.get("chosen_threshold")
    if art.get("verdict") != "PASSED" or th is None:
        raise SystemExit("the later stages use the threshold EXF-1 chose; EXF-1 has not passed")
    return float(th)


def run(stage: str, data: Path, now: datetime, fetch=checked, list_fetch=get, reg: Registry | None = None,
        out_dir: Path | None = None, probe_file: Path = PROBE) -> dict:
    reg = reg or registry()
    st = SPEC["stages"][stage]
    pid, venue = st["trial"], st["venue"]
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
    a, b = horizon(stage)
    cons = json.loads(probe_file.read_text())[venue]
    months = _months(_prev_month(st["settlements"][0][:7]), st["settlements"][1])
    settle, fman = fetch_funding(venue, cons, months, fetch)
    settle = {s: [(t, f) for t, f in xs if t <= b] for s, xs in settle.items()}  # nothing after the stage's last day
    need = plan(settle, a, b, SPEC["select_floor"])
    evs: list[dict] = []
    bman = {"absent": [], "failed": [], "files": 0}

    def one(s):
        perp, index, man = fetch_bars(venue, s, need[s], cons, fetch)
        perp = {t: v for t, v in perp.items() if t + X.M5 <= b + 1}
        index = {t: v for t, v in index.items() if t + X.M5 <= b + 1}
        return X.events(s, settle[s], perp, index, a, b), man
    with ThreadPoolExecutor(max_workers=12) as pool:
        for got, man in pool.map(one, list(need)):
            evs += got
            for k in ("absent", "failed"):
                bman[k] += man[k]
            bman["files"] += man["files"]
    if fman["failed"] or bman["failed"]:
        raise SystemExit(f"{len(fman['failed']) + len(bman['failed'])} archive files did not arrive (the first: "
                         f"{(fman['failed'] + bman['failed'])[:3]}): nothing is judged on a partial panel")
    universe = UNIVERSES[venue]
    bar = max(SPEC["bar_floor"], bonferroni_t(max(1, reg.tests_on(universe, datetime.fromtimestamp(a / 1000, timezone.utc).date(),
                                                                datetime.fromtimestamp(b / 1000, timezone.utc).date() + timedelta(days=1)))))
    cost, qv = SPEC["cost_per_fill"], SPEC["min_quote_volume"]
    kw = dict(min_events=st["min_events"], min_weeks=st["min_weeks"], seed=SPEC["seed"], placebos=SPEC["placebos"],
              lag=SPEC["nw_lag"])
    results, chosen = {}, None
    ths = SPEC["thresholds"] if stage == "dev" else [chosen_threshold(out_dir)]
    for th in ths:
        results[str(th)] = X.judge(X.trades(evs, th, cost, qv), bar, cost, **kw)
    passed = [th for th in ths if results[str(th)]["verdict"] == "PASSED"]
    if passed:
        chosen = max(passed, key=lambda th: results[str(th)]["t"])
        verdict = "PASSED"
    else:
        verdict = "INCONCLUSIVE" if all(r["verdict"] == "INCONCLUSIVE" for r in results.values()) else "FAILED"
    body = {"program": pid, "stage": stage, "kind": "settlement_study", "verdict": verdict, "judged": now.isoformat(),
            "code_sha256": code_hash(), "spec_sha256": spec_sha(), "spec": SPEC, "venue": venue,
            "settlements": st["settlements"], "bar": bar, "chosen_threshold": chosen if stage == "dev" else ths[0],
            "data": {"source": BASE, "funding_files": fman["files"], "funding_absent": len(fman["absent"]),
                     "bar_files": bman["files"], "bar_files_absent": len(bman["absent"]), "symbols_with_bars": len(need),
                     "last_moment_read": datetime.fromtimestamp((b + 1) / 1000, timezone.utc).isoformat()},
            "mechanism": X.mechanism(evs), "results": results}
    out_dir.mkdir(parents=True, exist_ok=True)
    f = out_dir / f"{pid}.json"
    f.write_text(json.dumps(body, indent=1, sort_keys=True, default=str) + "\n")
    data.mkdir(parents=True, exist_ok=True)
    with gzip.open(data / f"{pid}-events.json.gz", "wt") as g:  # every settlement measured, for the audit
        json.dump(evs, g)
    (data / f"{pid}-manifest.json").write_text(json.dumps({"funding": fman, "bars": bman}, indent=1) + "\n")
    best = results[str(chosen)] if chosen is not None else max(results.values(), key=lambda r: r["t"] if r["t"] is not None else -1e9)
    reg.record_verdict(Verdict(pid, now, verdict, {
        "artifact": str(f.relative_to(ROOT)) if f.is_relative_to(ROOT) else str(f),
        "chosen_threshold": body["chosen_threshold"], "t": best["t"], "mean": best["mean"], "trades": best["trades"],
        "weeks": best["weeks"], "gates": best.get("gates"), "why": best.get("why")}))
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
    a, b = st["settlements"]
    reg.register(Trial(
        id=st["trial"], registered=now,
        title=f"{st['trial']}: the ex-funding pass-through of perpetual futures, {stage} stage",
        hypothesis="Across a funding settlement, a perpetual's premium over its index moves by less than the funding "
                   "paid, so that the side the previous rate says receives the funding, held from five minutes before "
                   "the settlement to five minutes after, earns a positive return after two fills of 10 bp, averaged "
                   "over weekly cohorts; nothing comparable is earned at the same distance from no settlement.",
        uses=(Use(UNIVERSES[st["venue"]], date.fromisoformat(a), date.fromisoformat(b) + timedelta(days=1), "judge"),),
        tests=st["tests"], configurations=len(SPEC["thresholds"]) if stage == "dev" else 1, preregistration=DOC,
        design={"code_sha256": h, "spec_sha256": spec_sha(), "stage": stage}))
    print("registered", st["trial"])


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("command", choices=("probe", "hash", "preregister", "run"))
    ap.add_argument("stage", nargs="?", choices=tuple(SPEC["stages"]))
    ap.add_argument("--data", default=str(ROOT / "data" / "exf1"))
    ap.add_argument("--out", default=str(PROBE))
    ap.add_argument("--probe", default=str(PROBE))
    ap.add_argument("--no-funding", action="store_true")
    a = ap.parse_args(argv)
    now = datetime.now(timezone.utc)
    if a.command == "hash":
        print(code_hash(), spec_sha())
    elif a.command == "probe":
        body = probe(now=now, read_funding=not a.no_funding)
        out = Path(a.out)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(body, indent=1, sort_keys=True) + "\n")
        print(json.dumps({k: body.get(k) for k in ("funding_files", "funding_absent", "predictions_by_year", "bar_plan")}))
    elif a.command == "preregister":
        preregister(a.stage, now)
    else:
        body = run(a.stage, Path(a.data), now, probe_file=Path(a.probe))
        print(json.dumps({"program": body["program"], "verdict": body["verdict"], "chosen": body["chosen_threshold"],
                          "results": {k: {x: v.get(x) for x in ("trades", "weeks", "mean", "t", "verdict", "gates")}
                                      for k, v in body["results"].items()}}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
