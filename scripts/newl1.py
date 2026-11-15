"""NEWL-1: do perpetuals in their first month underperform those listed half a year to a year earlier?
(research/preregistrations/NEWL-1.md). Runs on GitHub's runner (.github/workflows/newl1.yml): Binance's archive is
not reachable from the director's session.

    python scripts/newl1.py probe                     # dates only: every contract and its first and last month
    python scripts/newl1.py hash                      # the code hash the preregistration quotes
    python scripts/newl1.py preregister dev           # (and later: validation, only after dev PASSED)
    python scripts/newl1.py run dev --data DIR        # fetch what the stage needs, judge it once, record the verdict

Nothing here trades. The stage reads no price after its own last exit day, and the validation stage's months are not
even fetched until it is registered.
"""

from __future__ import annotations

import argparse
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

from aitrader.research.dlab.feeds import VISION, checked, get, parse_daily_klines, parse_funding  # noqa: E402
from aitrader.research.events import listings as L  # noqa: E402
from aitrader.research.registry import Registry, Trial, Use, Verdict, bonferroni_t  # noqa: E402

R = ROOT / "research"
DOC = "research/preregistrations/NEWL-1.md"
PROBE = R / "results" / "NEWL-1-probe.json"
CODE = ("aitrader/research/events/listings.py", "scripts/newl1.py")
UNIVERSE = "crypto-perp-new-listings"
LISTING = "https://s3-ap-northeast-1.amazonaws.com/data.binance.vision?delimiter=/&prefix={prefix}{marker}"
NS = "{http://s3.amazonaws.com/doc/2006-03-01/}"
#: Everything that decides the result, frozen with the code. A change is a new registration, never an edit.
SPEC = {"program": "NEWL-1", "version": L.NEWL_VERSION, "universe": UNIVERSE,
        "stages": {"dev": {"trial": "NEWL-1", "entries": ["2021-01-01", "2023-12-31"]},
                   "validation": {"trial": "NEWL-1-V", "entries": ["2024-01-01", "2026-09-30"], "after": "NEWL-1"}},
        "lag_days": 1, "hold_days": 30, "late_lag_days": 2, "cost_per_fill": 0.0015, "seasoned_age_days": [181, 365],
        "min_pool": 3, "placebos": 1000, "seed": 20261115, "min_events": 60, "min_months": 18, "bar_floor": 3.0,
        "gates": ["t", "costs_x2", "halves", "top5_removed", "one_day_late", "beats_random", "without_best_year"]}


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
    """A trial's status, or None if it was never registered."""
    return reg.status_of(pid) if any(t.id == pid for t in reg.trials) else None


# ── the probe: dates only ───────────────────────────────────────────────────

def parse_listing(body: bytes) -> tuple[list[str], list[str], str | None]:
    """An S3 bucket listing: its sub-folders, its keys, and the marker to ask for the next page (None at the end)."""
    root = ET.fromstring(body)
    prefixes = [p.text for p in root.iter(NS + "Prefix") if p.text and p.text.endswith("/") and p.text != root.findtext(NS + "Prefix")]
    keys = [k.text for k in root.iter(NS + "Key") if k.text]
    truncated = (root.findtext(NS + "IsTruncated") or "false").lower() == "true"
    nxt = root.findtext(NS + "NextMarker") or (prefixes[-1] if prefixes else keys[-1] if keys else None)
    return prefixes, keys, nxt if truncated else None


def listing(prefix: str, fetch=get) -> tuple[list[str], list[str]]:
    prefixes, keys, marker = [], [], ""
    while True:
        # contract names are not all ASCII (a contract on a coin named in Chinese exists): every address is encoded
        body = fetch(LISTING.format(prefix=quote(prefix, safe="/"), marker=f"&marker={quote(marker, safe='/')}" if marker else ""))
        if body is None:
            raise RuntimeError(f"no listing for {prefix}")
        p, k, nxt = parse_listing(body)
        prefixes += p
        keys += k
        if not nxt:
            return prefixes, keys
        marker = nxt


def probe(fetch=get, now: datetime | None = None) -> dict:
    """Every USDT-M contract in the archive with its first and last month of daily klines. File names only: no
    price is read."""
    now = now or datetime.now(timezone.utc)
    base = "data/futures/um/monthly/klines/"
    syms, _ = listing(base, fetch)
    out = {}
    for p in syms:
        s = p[len(base):].strip("/")
        _, keys = listing(f"{base}{s}/1d/", fetch)
        ms = sorted(k.rsplit("-1d-", 1)[1][:7] for k in keys if k.endswith(".zip") and "-1d-" in k)
        if ms:
            out[s] = {"first": ms[0], "last": ms[-1], "months": len(ms)}
    cls = L.classify({s: v["first"] for s, v in out.items()})
    by_year: dict[str, int] = {}
    for s, m in cls["eligible"].items():
        by_year[m[:4]] = by_year.get(m[:4], 0) + 1
    return {"retrieved": now.isoformat(), "source": "https://data.binance.vision (S3 listing of " + base + ")",
            "what": "file names only: which months of daily klines exist for each contract. No price was read",
            "contracts": out, "eligible": cls["eligible"], "excluded": cls["excluded"], "eligible_by_first_year": by_year}


# ── the stage ───────────────────────────────────────────────────────────────

def _month(d: str) -> str:
    return d[:7]


def _months(a: str, b: str) -> list[str]:
    y, m = int(a[:4]), int(a[5:7])
    out = []
    while f"{y:04d}-{m:02d}" <= b:
        out.append(f"{y:04d}-{m:02d}")
        y, m = (y + 1, 1) if m == 12 else (y, m + 1)
    return out


def horizon(stage: str) -> tuple[str, str, str]:
    """The stage's first and last entry day, and the last day any of its positions can be held to."""
    a, b = SPEC["stages"][stage]["entries"]
    end = (date.fromisoformat(b) + timedelta(days=SPEC["late_lag_days"] - SPEC["lag_days"] + SPEC["hold_days"])).isoformat()
    return a, b, end


def needed(eligible: dict[str, str], stage: str) -> dict[str, list[str]]:
    """The months of each contract the stage can use: a contract listed in time to be an event or a seasoned member
    of a basket, from its first month to the month its basket membership ends, never past the stage's last day."""
    a, b, end = horizon(stage)
    lo = (date.fromisoformat(a) - timedelta(days=SPEC["seasoned_age_days"][1] + 31)).isoformat()
    out = {}
    for s, m in eligible.items():
        if not _month(lo) <= m <= _month(b):
            continue
        y, mm = int(m[:4]), int(m[5:7]) + 14
        last = f"{y + (mm - 1) // 12:04d}-{(mm - 1) % 12 + 1:02d}"
        out[s] = _months(m, min(last, _month(end)))
    return out


def fetch_stage(data: Path, want: dict[str, list[str]], fetch=checked, workers: int = 8) -> dict:
    data.mkdir(parents=True, exist_ok=True)
    mf = data / "manifest.json"
    man = json.loads(mf.read_text()) if mf.exists() else {"have": {}, "absent": {}}
    closes = json.loads((data / "close.json").read_text()) if (data / "close.json").exists() else {}
    funding = json.loads((data / "funding.json").read_text()) if (data / "funding.json").exists() else {}
    todo = [(s, m, k) for s, ms in sorted(want.items()) for m in ms for k in ("klines", "fundingRate")
            if m not in man["have"].get(f"{s}:{k}", []) and m not in man["absent"].get(f"{s}:{k}", [])]

    def one(job):
        s, m, k = job
        q = quote(s, safe="")
        url = f"{VISION}{k}/{q}/" + (f"1d/{q}-1d-{m}.zip" if k == "klines" else f"{q}-fundingRate-{m}.zip")
        try:
            return job, fetch(url), None
        except RuntimeError as e:
            return job, None, str(e)[:160]
    with ThreadPoolExecutor(max_workers=workers) as pool:
        got = list(pool.map(one, todo))
    failed = []
    for (s, m, k), raw, err in got:
        if err is not None:
            failed.append(f"{s}:{k}:{m}")
        elif raw is None:
            man["absent"].setdefault(f"{s}:{k}", []).append(m)
        else:
            (closes if k == "klines" else funding).setdefault(s, {}).update(
                parse_daily_klines(raw) if k == "klines" else parse_funding(raw))
            man["have"].setdefault(f"{s}:{k}", []).append(m)
    man.update(failed=failed, fetched_now=len(todo) - len(failed), retrieved=datetime.now(timezone.utc).isoformat())
    (data / "close.json").write_text(json.dumps(closes, sort_keys=True))
    (data / "funding.json").write_text(json.dumps(funding, sort_keys=True))
    mf.write_text(json.dumps(man, indent=1, sort_keys=True) + "\n")
    return man


def firewall(series: dict[str, dict[str, float]], end: str) -> dict[str, dict[str, float]]:
    """Nothing after the stage's last day reaches the computation."""
    return {s: {d: v for d, v in xs.items() if d <= end} for s, xs in series.items()}


def run(stage: str, data: Path, now: datetime, fetch=checked, reg: Registry | None = None, out_dir: Path | None = None,
        probe_file: Path = PROBE) -> dict:
    reg = reg or registry()
    st = SPEC["stages"][stage]
    pid = st["trial"]
    if not any(t.id == pid for t in reg.trials):
        raise SystemExit(f"{pid} is not registered: nothing is fetched or judged before it is")
    if reg.status_of(pid) != "PENDING":
        raise SystemExit(f"{pid} already has a verdict: a stage is judged once")
    if "after" in st and _status(reg, st["after"]) != "PASSED":
        raise SystemExit(f"{pid} is judged only after {st['after']} passed")
    design = reg.get(pid).design
    if design.get("code_sha256") != code_hash() or design.get("spec_sha256") != spec_sha():
        raise SystemExit(f"{pid}: the code or the spec differs from what was registered")
    pr = json.loads(probe_file.read_text())
    man = fetch_stage(data, needed(pr["eligible"], stage), fetch)
    if man["failed"]:
        raise SystemExit(f"{len(man['failed'])} archive files did not arrive (the first: {man['failed'][:3]}): "
                         "nothing is judged on a partial panel; the next run asks again")
    a, b, end = horizon(stage)
    closes = firewall(json.loads((data / "close.json").read_text()), end)
    funding = firewall(json.loads((data / "funding.json").read_text()), end)
    listed = {s: True for s in closes if s in pr["eligible"]}
    kw = dict(hold=SPEC["hold_days"], cost=SPEC["cost_per_fill"], seasoned=tuple(SPEC["seasoned_age_days"]),
              min_pool=SPEC["min_pool"])
    evs = L.events(listed, closes, funding, a, b, lag=SPEC["lag_days"], **kw)
    late = L.events(listed, closes, funding, a, b, lag=SPEC["late_lag_days"], **kw)
    bar = max(SPEC["bar_floor"], bonferroni_t(reg.tests_on(UNIVERSE, date.fromisoformat(a), date.fromisoformat(end) + timedelta(days=1))))
    res = L.judge(evs, late, bar, SPEC["cost_per_fill"], seed=SPEC["seed"], placebos=SPEC["placebos"],
                  min_events=SPEC["min_events"], min_months=SPEC["min_months"])
    body = {"program": pid, "stage": stage, "kind": "event_study", "verdict": res["verdict"], "judged": now.isoformat(),
            "code_sha256": code_hash(), "spec_sha256": spec_sha(), "spec": SPEC, "entries": [a, b], "last_day_read": end,
            "data": {"source": VISION, "months_fetched": sum(len(v) for v in man["have"].values()),
                     "months_absent": sum(len(v) for v in man["absent"].values()), "retrieved": man["retrieved"]},
            "result": {k: v for k, v in res.items()},
            "events": [{k: (round(v, 6) if isinstance(v, float) else v) for k, v in e.items() if k != "placebo_shorts"}
                       for e in evs]}
    out_dir = out_dir or R / "knowledge"
    out_dir.mkdir(parents=True, exist_ok=True)
    f = out_dir / f"{pid}.json"
    f.write_text(json.dumps(body, indent=1, sort_keys=True, default=str) + "\n")
    reg.record_verdict(Verdict(pid, now, res["verdict"], {
        "artifact": str(f.relative_to(ROOT)) if f.is_relative_to(ROOT) else str(f),
        "gates": res.get("gates"), "t": res["t"], "mean_cohort_x": res["mean_cohort_x"], "events": res["hedged_events"],
        "months": res["months"], "why": res.get("why")}))
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
    a, b, end = horizon(stage)
    reg.register(Trial(
        id=st["trial"], registered=now,
        title=f"{st['trial']}: newly listed Binance perpetuals against seasoned listings, {stage} stage",
        hypothesis="A perpetual entered short at the close of its first full day and held 30 days, hedged with an "
                   "equal-weight long basket of perpetuals listed 181 to 365 days earlier, earns a positive return "
                   "after funding and 15 bp a fill on both legs, averaged over monthly cohorts of entries.",
        uses=(Use(UNIVERSE, date.fromisoformat(a), date.fromisoformat(end) + timedelta(days=1), "judge"),),
        tests=1, configurations=1, preregistration=DOC,
        design={"code_sha256": h, "spec_sha256": spec_sha(), "stage": stage}))
    print("registered", st["trial"])


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("command", choices=("probe", "hash", "preregister", "run"))
    ap.add_argument("stage", nargs="?", choices=tuple(SPEC["stages"]))
    ap.add_argument("--data", default=str(ROOT / "data" / "newl1"))
    a = ap.parse_args(argv)
    now = datetime.now(timezone.utc)
    if a.command == "hash":
        print(code_hash(), spec_sha())
    elif a.command == "probe":
        body = probe(now=now)
        PROBE.parent.mkdir(parents=True, exist_ok=True)
        PROBE.write_text(json.dumps(body, indent=1, sort_keys=True) + "\n")
        print(json.dumps({"contracts": len(body["contracts"]), "eligible": len(body["eligible"]), "by_year": body["eligible_by_first_year"]}))
    elif a.command == "preregister":
        preregister(a.stage, now)
    else:
        body = run(a.stage, Path(a.data), now)
        print(json.dumps({"program": body["program"], "verdict": body["verdict"], "t": body["result"]["t"],
                          "gates": body["result"].get("gates")}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
