"""One cycle of the autonomous discovery lab (docs/DISCOVERY_LAB.md). Research only: nothing here trades.

    python scripts/lab_cycle.py --state <dir>    # GitHub's runner, several times a day: .github/workflows/lab-cycle.yml

Every run starts on a fresh machine, so every run is a restart. The state directory holds the lab's memory (the task
queue, the checkpoint log, the source database, the forward record, the alerts and the budget:
aitrader/research/dlab/store.py) and the data it fetched. The workflow restores it from the `lab-data` branch and
publishes it back.

A cycle:

1. checks the permanent research record. If that fails, nothing else runs;
2. queues what is due: the newest data each panel's source should hold whole, a discovery scan of each panel under
   this version of the lab, the week's new papers, the day's forward marks of any validated rule;
3. orders the queue by what the lab's own record says each task is worth (brain.py);
4. runs tasks, the most valuable first, inside the cycle's budget. A task that fails is retried by later cycles, three
   times at most, and then reported. A task is known by its id and is never run twice;
5. learns: every classed rule becomes part of the lessons and of the next scan's allocation;
6. writes LAB_REPORT.md and raises alerts (a validated rule, a broken record, a task that keeps failing).

A scan that proposes rules queues their validation: a preregistered test on rows no scan has read, at the registry's
bar (scripts/dlab.py). The lab approves nothing itself: a rule is validated only by that test.

A scan and a validation each run once, so neither starts on data that are not whole: files the source did not answer
for, a month published for some instruments only, a fund served with a series that stops early, or files that stop
before a validation window ends. Each of those is a wait, said in the report, never an attempt. No forward mark is
written from such a panel either, or by a rule that no longer gives, on its validation rows, what its judge recorded.

In the repository itself a cycle writes the registry, each scan's and validation's spec, preregistration and evidence,
the candidate ledger and the lessons. The workflow commits exactly those paths.

Exit codes: 0, the cycle ran (a failed task is in the report and is retried); 1, the record failed its integrity
check.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import sys
import time
import urllib.request
from datetime import date, datetime, timezone
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import scripts.dlab as L  # noqa: E402
from aitrader.research.dlab import DLAB_VERSION  # noqa: E402
from aitrader.research.dlab import brain as B  # noqa: E402
from aitrader.research.dlab import datasets as D  # noqa: E402
from aitrader.research.dlab import feeds as F  # noqa: E402
from aitrader.research.dlab.signals import pnl  # noqa: E402
from aitrader.research.dlab.store import Store, abandoned, enqueue, mark, reprioritize, runnable, tasks  # noqa: E402
from aitrader.research.registry import Verdict  # noqa: E402
from scripts.research_engine import SEAL_SHA256  # noqa: E402
from scripts.research_report import evidence, read_registry  # noqa: E402

CYCLE_VERSION = "lab-cycle-1.0.0"
#: The panels the lab scans by itself: dataset -> its run tag, its feed and its nominal breadth. One scan for each
#: version of the lab: a second look at the same discovery rows under the same methods would find the same rules.
CATALOG = {"crypto-daily": {"tag": "CRD", "feed": "crypto_daily", "instruments": len(F.PERPS)},
           "etf-daily": {"tag": "ETF", "feed": "etf_daily", "instruments": len(F.ETFS), "daily": True}}
FEEDS = {"crypto_daily": F.crypto_daily, "etf_daily": F.etf_daily}
#: The newest period a feed can bring, which names its data task: a feed not listed here is asked for once a month.
#: A "daily" panel is also refreshed by the forward marks; a monthly one brings its new rows with its data task.
DUE = {"crypto_daily": F.due_month}
MIN_INSTRUMENTS = {"crypto_daily": 20, "etf_daily": 20}  # a feed that returns fewer is refused: the panel is not broad
SEED = 7
#: minutes a task may need: it is not started with less of the cycle's budget left
MINUTES = {"data": 10, "scan": 25, "validate": 10, "sources": 2, "forward": 5}
PRIORITY = {"validate": 5.0, "data": 4.0, "forward": 3.0, "sources": 0.5}


def _log(store: Store, now: datetime, step: str, status: str, detail: object = None) -> None:
    store.append("runs", [{"cycle": now.isoformat(), "step": step, "status": status, "detail": detail,
                           "version": CYCLE_VERSION, "lab": DLAB_VERSION}])


def ledger() -> list[dict]:
    return [json.loads(x) for x in L.LEDGER.read_text().splitlines() if x.strip()] if L.LEDGER.exists() else []


def artifacts() -> dict[str, dict]:
    return {p.stem: json.loads(p.read_text()) for p in sorted(L.OUT.glob("DLAB-*.json"))} if L.OUT.exists() else {}


# ── 1. the record ───────────────────────────────────────────────────────────

def integrity() -> list[str]:
    """What is wrong with the permanent record, in words. Empty: nothing.

    - the seal is the pinned one, and the registry loads (it refuses a back-filled or reused trial);
    - every verdict's evidence still has the hash recorded with it, and every preregistration quotes its spec;
    - every run in the candidate ledger is a registered scan with a verdict, and holds as many rules as that scan's
      evidence: a candidate cannot be dropped from the ledger, or added to it, after the fact."""
    problems = []
    seal = L.R / "holdout.json"
    if hashlib.sha256(seal.read_bytes()).hexdigest() != SEAL_SHA256:
        problems.append("the seal (research/holdout.json) differs from the pinned one")
    try:
        reg = L._registry()
    except Exception as e:  # the registry's own errors, or a line that is not JSON
        return problems + [f"the registry does not load: {type(e).__name__}: {e}"]
    trials, verdicts = read_registry(L.ROOT) if (L.R / "registry.jsonl").exists() else ({}, {})
    for tid, t in sorted(trials.items()):
        e = evidence(L.ROOT, t, verdicts.get(tid))
        if e["artifact_unchanged"] is False:
            problems.append(f"{tid}: its evidence no longer matches the hash recorded with its verdict")
        if e["spec_quoted"] is False:
            problems.append(f"{tid}: its spec hash is not quoted in its preregistration")
    arts, rows = artifacts(), ledger()
    for run in sorted({r["run"] for r in rows}):
        known = any(t.id == run for t in reg.trials)
        if not known or reg.verdict_of(run) is None or run not in arts:
            problems.append(f"{run}: the candidate ledger holds rules of a scan that is not registered and judged")
            continue
        n = sum(1 for r in rows if r["run"] == run and "event" not in r)
        if n != len(arts[run]["records"]):
            problems.append(f"{run}: the ledger holds {n} rules, its evidence {len(arts[run]['records'])}")
    return problems


# ── 2 and 3. the queue ──────────────────────────────────────────────────────

def next_run(tag: str, reg, store: Store) -> str:
    used = {t.id for t in reg.trials} | {t["args"].get("run") for t in tasks(store).values()}
    n = 1
    while f"DLAB-{tag}-{n}" in used:
        n += 1
    return f"DLAB-{tag}-{n}"


def existing_run(ds: str, reg) -> str | None:
    """A scan of this dataset already registered under this version of the lab, if its record reached the repository
    while the queue's memory of it did not (a run that died between its two pushes): it is resumed, not repeated."""
    for p in sorted((L.R / "specs").glob(f"DLAB-{CATALOG[ds]['tag']}-*.json")):
        s = json.loads(p.read_text())["spec"]
        if s.get("kind") == "discovery scan" and s["dataset"] == ds and s["version"] == DLAB_VERSION \
                and s["seed"] == SEED and any(t.id == p.stem for t in reg.trials) \
                and (reg.verdict_of(p.stem) is None or reg.verdict_of(p.stem).status != "ABANDONED"):
            return p.stem
    return None


def validated_rules() -> list[dict]:
    """Every rule that passed its registered validation, with what is needed to recompute it."""
    out = []
    for name, a in artifacts().items():
        if a.get("kind") == "discovery_validation" and a.get("passed_rules"):
            spec = json.loads((L.R / "specs" / f"{name}.json").read_text())["spec"]
            judged = {r["id"]: r["t"] for r in a["results"]}
            out += [{"trial": name, "run": a["scan"], "id": r["id"], "spec": r["spec"], "rule": r["rule"],
                     "family": r["family"], "dataset": spec["dataset"], "universe": spec["universe"],
                     "t": judged[r["id"]], "lags": spec["newey_west_lags"]}
                    for r in spec["rules"] if r["id"] in a["passed_rules"]]
    return out


def seed(store: Store, reg, now: datetime) -> list[str]:
    """Queue what is due. Returns the ids queued now."""
    new = []

    def q(task, kind, args, priority):
        if enqueue(store, task, kind, args, priority, now):
            new.append(task)
    for ds, c in CATALOG.items():
        period = DUE[c["feed"]](now) if c["feed"] in DUE else f"{now:%Y-%m}"
        q(f"data:{c['feed']}:{period}", "data", {"feed": c["feed"]}, PRIORITY["data"])
        task = f"scan:{ds}:{DLAB_VERSION}:{SEED}"
        if task not in tasks(store):
            q(task, "scan", {"dataset": ds, "seed": SEED, "run": existing_run(ds, reg) or next_run(c["tag"], reg, store)}, 2.0)
    year, week, _ = now.isocalendar()
    q(f"sources:{year}-W{week:02d}", "sources", {"week": week}, PRIORITY["sources"])
    if validated_rules():
        q(f"forward:{now:%Y-%m-%d}", "forward", {}, PRIORITY["forward"])
    return new


def prioritize(store: Store, table: dict, now: datetime) -> None:
    pr = {}
    for t in tasks(store).values():
        if t["kind"] == "scan" and t["status"] != "DONE":
            ds = t["args"]["dataset"]
            pr[t["task"]] = B.dataset_priority(CATALOG.get(ds, {}).get("instruments", 2), table.get(L.DATASETS[ds][0]))
    reprioritize(store, pr, now)


def incomplete(state: Path, feed: str) -> str | None:
    """Why a feed's files on disk are not a whole panel, or None. The feed says so itself, in its manifest."""
    d = Path(state) / "data" / feed
    if not ((d / "manifest.json").exists() and (d / "close.json").exists()):
        return "nothing is on file"
    return json.loads((d / "manifest.json").read_text()).get("incomplete")


def last_day_on_file(state: Path, feed: str) -> str | None:
    q = json.loads((Path(state) / "data" / feed / "manifest.json").read_text()).get("quality", {})
    return max((v["last"] for v in q.values() if v.get("rows") and v.get("last")), default=None)


def ready(t: dict, state: Path, store: Store) -> str | None:
    """Why a task cannot run yet, or None. Waiting is not an attempt. A scan and a validation wait for a COMPLETE fetch
    of their data: each runs once, and a panel with holes would be scanned or judged with them, and never again. A
    validation also waits until the files reach the end of its window."""
    if t["kind"] not in ("scan", "validate"):
        return None
    ds = t["args"].get("dataset") or json.loads((L.R / "specs" / f"{t['args']['run']}.json").read_text())["spec"]["dataset"]
    feed = CATALOG.get(ds, {}).get("feed")
    if not feed:
        return None
    fetched = any(x["kind"] == "data" and x["args"].get("feed") == feed and x["status"] == "DONE"
                  for x in tasks(store).values())
    why = incomplete(state, feed)
    if not fetched or why:
        return f"its data ({feed}) are not completely on file yet" + (f": {why}" if fetched else "")
    if t["kind"] == "validate":
        end, last = L._day(D.WINDOWS[L.DATASETS[ds][0]]["validation"][1]), last_day_on_file(state, feed)
        if last is None or (end - date.fromisoformat(last[:10])).days > L.MAX_GAP_DAYS:
            return f"its data ({feed}) end on {last}, before its validation window does ({end})"
    return None


# ── 4. the tasks ────────────────────────────────────────────────────────────

def usable_instruments(ds: str) -> int:
    """How many of a panel's instruments have the fit rows a scan needs, on the DISCOVERY rows only (the panel is loaded
    to the check rows' end, as a scan loads it). A feed can return every file and still leave a panel no scan can use:
    prices without the funding that makes a return, for one."""
    universe, loader, _ = L.DATASETS[ds]
    w = D.WINDOWS[universe]
    p = loader(w["check"][1])
    fit, fwd = p.rows(*w["fit"]), p.fwd()
    return sum(int((fit & np.isfinite(fwd[:, j])).sum() >= 2 * L.M.MIN_ROWS) for j in range(len(p.assets)))


def do_data(store: Store, state: Path, args: dict, now: datetime) -> dict:
    feed = args["feed"]
    man = FEEDS[feed](state / "data" / feed, now)
    q = man["quality"]
    if man.get("incomplete"):  # the feed's own reason: files that did not arrive, a month half-published, a stale fund
        raise RuntimeError(f"{feed}: {man['incomplete']}. The data are not complete: nothing is scanned, judged or "
                           "marked on them")
    have = [s for s, v in q.items() if v.get("rows", 0) >= 250 and not s.startswith("^")]
    if len(have) < MIN_INSTRUMENTS[feed]:
        raise RuntimeError(f"{feed}: only {len(have)} instruments have 250 rows; at least {MIN_INSTRUMENTS[feed]} are "
                           "needed. Nothing is scanned on a thin panel")
    usable = {ds: usable_instruments(ds) for ds, c in CATALOG.items() if c["feed"] == feed}
    for ds, n in usable.items():  # before any scan is registered: a scan runs once, and must not run on a husk
        if n < MIN_INSTRUMENTS[feed]:
            raise RuntimeError(f"{feed}: only {n} instruments of the {ds} panel have the fit rows a scan needs; at "
                               f"least {MIN_INSTRUMENTS[feed]} are needed. The files arrived, the panel is not usable")
    return {"feed": feed, "instruments": len(have), "usable_in_the_fit_rows": usable,
            "last_day": max(v["last"] for v in q.values() if v.get("rows")),
            "missing_days": sum(v.get("missing_days", 0) for v in q.values()),
            "moves_beyond_50pct": sum(v.get("moves_beyond_50pct", 0) for v in q.values()),
            "not_served": man.get("not_served", []), "fetched_now": man.get("fetched_now")}


def do_scan(store: Store, state: Path, args: dict, now: datetime) -> dict:
    ds, run = args["dataset"], args["run"]
    reg = L._registry()
    spec = L.R / "specs" / f"{run}.json"
    if any(t.id == run for t in reg.trials) and reg.verdict_of(run) is None and spec.exists() \
            and json.loads(spec.read_text())["code_sha256"] != L.code_hash():
        # registered under code that has since changed: it can never run as registered. It read no check row.
        reg.record_verdict(Verdict(run, now, "ABANDONED", {
            "reason": "the lab's code changed between this scan's registration and its run; it never ran"}))
        nxt = next_run(CATALOG[ds]["tag"], L._registry(), store)
        enqueue(store, f"scan:{ds}:{DLAB_VERSION}:{args['seed']}:after-{run}", "scan", {**args, "run": nxt}, 2.0, now)
        return {"run": run, "verdict": "ABANDONED", "requeued_as": nxt}
    universe = L.DATASETS[ds][0]
    arts = artifacts()
    record = B.arms(ledger(), {n: a["universe"] for n, a in arts.items() if a.get("kind") == "discovery_scan"})
    tops = B.allocation(record[universe], args["seed"]) if record.get(universe) else None
    art = L.auto_scan(ds, run, args["seed"], now, tops=tops)
    if art["batch"]:
        enqueue(store, f"validate:{run}", "validate", {"run": run, "dataset": ds}, PRIORITY["validate"], now)
    best = sorted((r for r in art["records"] if (r.get("check") or {}).get("t") is not None
                   and r["class"] in ("INSUFFICIENT_POWER", "PROMISING_UNCONFIRMED")),
                  key=lambda r: -r["check"]["t"])[:3]
    return {"run": run, "verdict": art["verdict"], "universe": universe, "instruments": len(art["instruments"]),
            "rules": art["summary"]["rules"], "by_class": art["summary"]["by_class"], "batch": len(art["batch"]),
            "scanned": sum(art["scanned"].values()), "noise": art["noise"],
            "best": [{"id": r["id"], "family": r["family"], "check_t": r["check"]["t"], "class": r["class"]} for r in best]}


def do_validate(store: Store, state: Path, args: dict, now: datetime) -> dict:
    run = args["run"]
    res = L.auto_validate(run, now)
    if res is None:
        return {"run": run, "verdict": None, "note": "the scan proposed nothing"}
    for r in res["results"]:
        if r["passed"]:
            alert(store, now, "DISCOVERY", f"{res['program']}: a rule passed its validation on unread rows",
                  f"Rule `{r['id']}` ({r['family']}): {r['rule']}\n\nt {r['t']} against {r['bar']}; mean net "
                  f"{r['a_year_pct']}% a year; every gate held. Evidence: research/knowledge/{res['program']}.json.\n\n"
                  "It is a candidate, not a trading system: it is marked forward on paper by the lab, and it trades "
                  "only on the owner's word, on paper, through the risk engine.")
    return {"trial": res["program"], "verdict": res["verdict"], "threshold_t": res["threshold_t"],
            "passed": res["passed_rules"],
            "results": [{"id": r["id"], "t": r["t"], "failed": r["failed_gates"]} for r in res["results"]]}


def do_sources(store: Store, state: Path, args: dict, now: datetime) -> dict:
    known = {r["id"] for r in store.read("sources")}
    new = F.papers(known, now, args["week"])
    store.append("sources", new)
    return {"new": len(new), "query": F.QUERIES[args["week"] % len(F.QUERIES)],
            "by_origin": {o: sum(1 for s in new if s["origin"] == o) for o in sorted({s["origin"] for s in new})}}


def do_forward(store: Store, state: Path, args: dict, now: datetime) -> dict:
    """Mark each validated rule on the rows after its validation window: its frozen spec, new data, nothing fitted.

    No mark is written from a panel that is not whole (the dataset waits), or by a rule that no longer gives, on its
    validation rows, the t its judge recorded: then the data or the code have changed since, and the task fails for a
    person to look. A panel marked "daily" is refreshed here; a monthly one brings its rows with its data task."""
    rules = validated_rules()
    seen = {(r["rule"], r["row"]) for r in store.read("forward")}
    new, waiting = [], {}
    for ds in sorted({r["dataset"] for r in rules}):
        universe, loader, _ = L.DATASETS[ds]
        c = CATALOG.get(ds, {})
        feed = c.get("feed")
        if feed and c.get("daily"):
            FEEDS[feed](state / "data" / feed, now)  # a fetch that is not complete changes nothing on file
        why = incomplete(state, feed) if feed else None
        if why:
            waiting[ds] = why
            continue
        w = D.WINDOWS[universe]["validation"]
        end, mine = w[1], [x for x in rules if x["dataset"] == ds]
        judged = loader(end)  # the panel exactly as the judge loaded it
        vmask = judged.rows(*w)
        for r in mine:
            t = L.nw_t(np.where(vmask, pnl(r["spec"], judged)["net"], np.nan), r["lags"])
            if t is None or abs(t - r["t"]) > 2e-3:
                raise RuntimeError(f"{r['id']} ({r['trial']}): on its validation rows the rule gives t {t} today, and its "
                                   f"judge recorded {r['t']}. The data or the code changed: no forward mark is written")
        p = loader(end.replace(year=2100))
        for r in mine:
            x = pnl(r["spec"], p)
            for i, t in enumerate(p.times):
                if t >= end and np.isfinite(x["net"][i]) and (r["id"], str(t)) not in seen:
                    new.append({"rule": r["id"], "trial": r["trial"], "row": str(t), "net": round(float(x["net"][i]), 8),
                                "exposure": round(float(abs(np.nan_to_num(x["pos"][i]))), 4), "at": now.isoformat()})
    store.append("forward", new)
    return {"rules": len(rules), "rows_added": len(new), **({"waiting_for_whole_data": waiting} if waiting else {})}


HANDLERS = {"data": do_data, "scan": do_scan, "validate": do_validate, "sources": do_sources, "forward": do_forward}


def run_tasks(store: Store, state: Path, now: datetime, max_tasks: int, max_minutes: float, started: float,
              clock=time.monotonic) -> list[dict]:
    ran: list[dict] = []
    tried: set[str] = set()
    while len(ran) < max_tasks:
        left = max_minutes - (clock() - started) / 60.0
        t = next((t for t in runnable(store, now) if t["task"] not in tried and ready(t, state, store) is None
                  and MINUTES[t["kind"]] <= left), None)
        if t is None:
            break
        tried.add(t["task"])
        mark(store, t["task"], "STARTED", now)
        try:
            res, status = HANDLERS[t["kind"]](store, state, t["args"], now), "DONE"
        except (Exception, SystemExit) as e:  # a failed task must not take the cycle, or its report, with it
            res, status = {"error": f"{type(e).__name__}: {e}"[:800]}, "FAILED"
        mark(store, t["task"], status, now, res)
        _log(store, now, f"task:{t['task']}", "OK" if status == "DONE" else "FAILED", res)
        ran.append({"task": t["task"], "kind": t["kind"], "status": status, "result": res})
    return ran


# ── 5. what the record teaches ──────────────────────────────────────────────

def learn(now: datetime) -> dict:
    arts = {n: a for n, a in artifacts().items() if a.get("kind") == "discovery_scan"}
    table = B.arms(ledger(), {n: a["universe"] for n, a in arts.items()})
    audits = {a["universe"]: a["information_audit"] for a in arts.values() if a.get("information_audit")}
    body = {"version": DLAB_VERSION, "arms": table, "lessons": B.lessons(table, audits)}
    path = L.R / "dlab" / "lessons.json"
    old = json.loads(path.read_text()) if path.exists() else {}
    if {k: old.get(k) for k in body} != json.loads(json.dumps(body)):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps({**body, "at": now.isoformat()}, indent=1, sort_keys=True) + "\n")
    return body


# ── 6. alerts and the report ────────────────────────────────────────────────

def alert(store: Store, now: datetime, level: str, title: str, body: str) -> bool:
    """Raise an alert once: the same level and title is not raised again."""
    aid = hashlib.sha256(f"{level}|{title}".encode()).hexdigest()[:12]
    if any(a["id"] == aid for a in store.read("alerts")):
        return False
    store.append("alerts", [{"id": aid, "event": "RAISED", "level": level, "title": title, "body": body,
                             "at": now.isoformat()}])
    return True


def send_alerts(store: Store, now: datetime, post) -> int:
    """Send every alert not yet sent. `post` returns where it went, or None if it could not be sent now."""
    rows = store.read("alerts")
    sent = {a["id"] for a in rows if a["event"] == "SENT"}
    n = 0
    for a in rows:
        if a["event"] == "RAISED" and a["id"] not in sent:
            try:
                where = post(a)
            except Exception as e:  # the alert stays unsent, and the next cycle tries again
                where = None
                print(f"alert {a['id']} not sent: {type(e).__name__}", file=sys.stderr)
            if where:
                store.append("alerts", [{"id": a["id"], "event": "SENT", "where": where, "at": now.isoformat()}])
                n += 1
    return n


def github_issue(env=None):
    """An alert as an issue on the repository: its owner is notified by GitHub. None without a token (a local run)."""
    env = os.environ if env is None else env
    token, repo = env.get("GITHUB_TOKEN"), env.get("GITHUB_REPOSITORY")
    if not token or not repo:
        return None

    def post(a: dict) -> str | None:
        req = urllib.request.Request(
            f"https://api.github.com/repos/{repo}/issues", method="POST",
            data=json.dumps({"title": f"[lab · {a['level']}] {a['title']}"[:240], "body": a["body"][:60000]}).encode(),
            headers={"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json",
                     "User-Agent": "research-lab-worker"})
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.loads(r.read()).get("html_url")
    return post


def _forward_summary(store: Store) -> list[dict]:
    by: dict[str, list[float]] = {}
    for r in store.read("forward"):
        by.setdefault(r["rule"], []).append(r["net"])
    out = []
    for rule, v in sorted(by.items()):
        a = np.asarray(v)
        sd = float(a.std(ddof=1)) if len(a) > 1 else 0.0
        out.append({"rule": rule, "rows": len(a), "mean": float(a.mean()), "total_pct": float(a.sum() * 100),
                    "t": float(a.mean() / sd * math.sqrt(len(a))) if sd > 0 and len(a) >= 20 else None})
    return out


def report(store: Store, state: Path, now: datetime, ran: list[dict], problems: list[str]) -> str:
    rows, arts, tk = ledger(), artifacts(), tasks(store)
    rules = [r for r in rows if "event" not in r]
    judged = [r for r in rows if r.get("event") == "VALIDATION"]
    by_class: dict[str, int] = {}
    for r in rules:
        by_class[r["class"]] = by_class.get(r["class"], 0) + 1
    scans = {n: a for n, a in arts.items() if a.get("kind") == "discovery_scan"}
    vals = {n: a for n, a in arts.items() if a.get("kind") == "discovery_validation"}
    passed = [r for r in judged if r["class"] == "VALIDATED_ON_UNREAD_ROWS"]
    waiting = [t for t in tk.values() if t["status"] not in ("DONE",)]
    lost = abandoned(store)
    sources = store.read("sources")
    alerts = store.read("alerts")
    budget = store.read("budget")
    fwd = _forward_summary(store)
    o = ["# Discovery lab: the autonomous research report", "",
         "**RESEARCH ONLY · NOT TRADING · NOTHING HERE IS A PROFIT CLAIM.** Written by the lab's own worker on GitHub's "
         "runner, with no person and no open conversation in the loop. A rule is validated only by a preregistered test "
         "on rows no scan has read, at the registry's bar; everything short of that is a candidate.", "",
         f"**بالعربي:** هذا تقرير المختبر الذاتي: بحث فقط، ما بيه تداول ولا وعد بربح. لحد هسه المختبر سوّى "
         f"{len(scans)} فحص اكتشاف وصنّف {len(rules)} قاعدة، وكلها محفوظة ويا سبب تصنيفها. "
         f"القواعد اللي وصلت اختبار التحقق المستقل: {len(judged)}، ونجح منها {len(passed)}. "
         f"بالطابور هسه {len(waiting)} مهمة. "
         + ("سجل البحث سليم." if not problems else "تنبيه: سجل البحث فشل بفحص السلامة، والمختبر وقّف التجارب."), "",
         f"Updated {now:%Y-%m-%d %H:%M} UTC · {CYCLE_VERSION} · {DLAB_VERSION} · cycles so far: {len(budget) + 1}", ""]
    if problems:
        o += ["## The record failed its integrity check: no experiment ran", ""] + [f"- {p}" for p in problems] + [""]
    o += ["## This cycle", ""]
    if ran:
        o += ["| Task | Result |", "|---|---|"]
        for t in ran:
            r = t["result"]
            text = r.get("error") or json.dumps({k: v for k, v in r.items() if k not in ("best", "noise", "results")})
            o.append(f"| `{t['task']}` | **{t['status']}** · {text[:300]} |")
    else:
        o.append("No task ran: nothing was due, or nothing could run yet (see the queue).")
    o += ["", "## The queue", "", "| Task | State | Attempts | Priority | Waiting for |", "|---|---|---|---|---|"]
    for t in sorted(waiting, key=lambda t: (-t["priority"], t["task"])):
        o.append(f"| `{t['task']}` | {t['status']} | {t['attempts']} | {t['priority']} | {ready(t, state, store) or ''} |")
    if not waiting:
        o.append("| (empty) | | | | |")
    o += ["", f"Done so far: {sum(1 for t in tk.values() if t['status'] == 'DONE')} tasks. A task is known by its id and "
          "never runs twice. A failed task is retried by later cycles, three times at most."]
    if lost:
        o += ["", "**Tasks that failed on every attempt (they need a person):**", ""]
        o += [f"- `{t['task']}`: {json.dumps(t['result'])[:300]}" for t in lost]
    o += ["", "## Discovery scans", "", "| Scan | Market | Instruments | Rules kept | Statistics looked at | Promising | Verdict |",
          "|---|---|---|---|---|---|---|"]
    for n, a in scans.items():
        o.append(f"| `{n}` | {a['universe']} | {len(a['instruments'])} | {a['summary']['rules']} | "
                 f"{sum(a['scanned'].values())} | {len(a['batch'])} | {a['verdict']} |")
    if not scans:
        o.append("| none yet | | | | | | |")
    o += ["", "A scan's verdict says only whether it proposed rules for validation. It validates and disproves nothing.",
          "", "## Every candidate, by class (cumulative)", "", "| Class | Rules |", "|---|---|"]
    o += [f"| {c} | {by_class.get(c, 0)} |" for c in L.T.CLASSES]
    fam: dict[str, dict[str, int]] = {}
    for r in rules:
        fam.setdefault(r["family"], {})[r["class"]] = fam.setdefault(r["family"], {}).get(r["class"], 0) + 1
    pos = ("INSUFFICIENT_POWER", "PROMISING_UNCONFIRMED")
    o += ["", "| Family | Rules | Positive out of sample | Promising |", "|---|---|---|---|"]
    o += [f"| {f} | {sum(c.values())} | {sum(c.get(k, 0) for k in pos)} | {c.get('PROMISING_UNCONFIRMED', 0)} |"
          for f, c in sorted(fam.items())]
    done = {(r["run"], r["id"]) for r in judged}  # a judged rule has its own table: it is no longer waiting
    best = sorted((r for r in rules if r["class"] in pos and (r.get("check") or {}).get("t") is not None
                   and (r["run"], r["id"]) not in done), key=lambda r: -r["check"]["t"])[:10]
    o += ["", "### The strongest candidates not yet judged", ""]
    if best:
        o += ["| Scan | Rule | Family | Check-row t | Class | Its plan |", "|---|---|---|---|---|---|"]
        for r in best:
            ways = "; ".join((r.get("plan") or {}).get("ways", []))[:260]
            if r.get("in_batch"):
                ways = "in its scan's validation batch"
            elif r["class"] == "PROMISING_UNCONFIRMED":
                ways = ("promising, and left out of its scan's batch: stronger rules of its family, or on its "
                        "instrument, took the places")
            o.append(f"| {r['run']} | {r['rule'][:150]} | {r['family']} | {r['check']['t']} | {r['class']} | {ways} |")
    else:
        o.append("None.")
    o += ["", "## Independent validation", ""]
    if vals:
        o += ["| Trial | Rules judged | Bar | Passed | Verdict |", "|---|---|---|---|---|"]
        o += [f"| `{n}` | {len(a['results'])} | {a['threshold_t']} | {len(a['passed_rules'])} | {a['verdict']} |"
              for n, a in vals.items()]
        text_of = {(r["run"], r["id"]): r for r in rules}
        o += ["", "Every rule judged, each once, on rows no scan had read:", "",
              "| Trial | Rule | Family | t | Bar | Result |", "|---|---|---|---|---|---|"]
        for j in sorted(judged, key=lambda j: (j["trial"], -(j["t"] or 0.0))):
            r = text_of.get((j["run"], j["id"]), {})
            o.append(f"| `{j['trial']}` | {r.get('rule', j['id'])[:150]} | {r.get('family', '')} | {j['t']} | {j['bar']} | "
                     f"{j['class']}: {j['reason']} |")
    else:
        o.append("No rule has reached a registered validation yet.")
    o += ["", "## Validated rules, marked forward on paper", ""]
    valid = validated_rules()
    if valid:
        marks = {f["rule"]: f for f in fwd}
        o += ["| Rule | Trial | Rows since its validation window | Mean net a row | Total | t |", "|---|---|---|---|---|---|"]
        for v in valid:
            f = marks.get(v["id"])
            o.append(f"| `{v['id']}` {v['rule'][:110]} | `{v['trial']}` | " + (
                "0: no row after its window is on file yet | | | |" if f is None else
                f"{f['rows']} | {f['mean']:.6f} | {f['total_pct']:.2f}% | {'' if f['t'] is None else round(f['t'], 2)} |"))
        o += ["", "A validated rule is a candidate, not a trading system. These marks are the rule's own frozen arithmetic "
              "on new rows: no order, no account. It trades only on the owner's word, on paper, through the risk engine."]
    else:
        o.append("None: no rule has passed its validation. Nothing is traded, on paper or otherwise, from this lab.")
    lessons = (json.loads((L.R / "dlab" / "lessons.json").read_text()).get("lessons", [])
               if (L.R / "dlab" / "lessons.json").exists() else [])
    o += ["", "## What the record has taught so far", ""] + ([f"- {x}" for x in lessons] or ["Nothing yet."])
    o += ["", "## The research-source database", "",
          f"{len(sources)} sources on file. Each has its link, its date and a status. A source's status is UNREAD until "
          "its claim is checked: nothing is claimed about a paper from its abstract.", ""]
    if sources:
        o += ["| Published | Source | Title |", "|---|---|---|"]
        o += [f"| {s.get('published') or ''} | [{s['origin']}]({s.get('url') or ''}) | {s['title'][:140]} |"
              for s in sorted(sources, key=lambda s: s.get("published") or "", reverse=True)[:10]]
    o += ["", "## Data on file", ""]
    any_data = False
    for feed in FEEDS:
        m = state / "data" / feed / "manifest.json"
        if m.exists():
            any_data = True
            man = json.loads(m.read_text())
            q = [v for v in man["quality"].values() if v.get("rows")]
            o.append(f"- `{feed}`: {len(q)} instruments, to {max(v['last'] for v in q)}; "
                     f"{sum(v.get('missing_days', 0) for v in q)} missing days in all; "
                     f"{sum(v.get('moves_beyond_50pct', 0) for v in q)} one-day moves beyond 50% (flagged, never "
                     f"removed); retrieved {man['retrieved'][:16]} UTC"
                     + (f" · **NOT COMPLETE: {man['incomplete']}**" if man.get("incomplete") else ""))
    if not any_data:
        o.append("None yet.")
    o += ["", "## Alerts", ""]
    raised = [a for a in alerts if a["event"] == "RAISED"]
    sent = {a["id"] for a in alerts if a["event"] == "SENT"}
    o += [f"- {a['at'][:16]} · {a['level']} · {a['title']} ({'sent' if a['id'] in sent else 'not sent yet'})"
          for a in raised] or ["None."]
    o += ["", "## Budget", "", "| Cycle | Seconds | Tasks run | Failed |", "|---|---|---|---|"]
    o += [f"| {b['cycle'][:16]} | {b['seconds']} | {b['tasks']} | {b['failed']} |" for b in budget[-6:]]
    o += ["", "No model call and no paid service is used by a cycle. Its data come from public archives.", ""]
    text = "\n".join(o)
    (state / "LAB_REPORT.md").write_text(text)
    return text


# ── the cycle ───────────────────────────────────────────────────────────────

def link_data(state: Path) -> None:
    """The loaders read data/<feed> in the repository: point those at the state directory's copies."""
    for feed in FEEDS:
        src, dst = state / "data" / feed, L.ROOT / "data" / feed
        src.mkdir(parents=True, exist_ok=True)
        if not dst.exists() and not dst.is_symlink():
            dst.parent.mkdir(parents=True, exist_ok=True)
            dst.symlink_to(src.resolve(), target_is_directory=True)


def cycle(state: Path, now: datetime, max_tasks: int = 4, max_minutes: float = 45.0, post=None,
          clock=time.monotonic) -> int:
    started = clock()
    state = Path(state)
    store = Store(state)
    link_data(state)
    problems = integrity()
    _log(store, now, "integrity", "OK" if not problems else "FAILED", problems or None)
    ran: list[dict] = []
    if problems:
        alert(store, now, "PROBLEM", "the research record failed its integrity check",
              "No experiment ran.\n\n" + "\n".join(f"- {p}" for p in problems))
    else:
        queued = seed(store, L._registry(), now)
        prioritize(store, learn(now)["arms"], now)
        _log(store, now, "queue", "OK", {"queued": queued})
        ran = run_tasks(store, state, now, max_tasks, max_minutes, started, clock)
        learn(now)
        for t in abandoned(store):
            # a day's forward marks are one task a day: one alert a month for them, not one a day
            what = f"the forward marks of {t['task'].split(':')[1][:7]}" if t["kind"] == "forward" else f"the task {t['task']}"
            alert(store, now, "PROBLEM", f"{what} failed on each of {t['attempts']} attempts",
                  f"`{t['task']}`\n\n" + json.dumps(t["result"], indent=1)[:4000])
    if post is not None:
        send_alerts(store, now, post)
    store.append("budget", [{"cycle": now.isoformat(), "seconds": round(clock() - started, 1), "tasks": len(ran),
                             "failed": sum(1 for t in ran if t["status"] == "FAILED"), "version": CYCLE_VERSION}])
    report(store, state, now, ran, problems)
    print(json.dumps({"cycle": now.isoformat(), "integrity": problems or "OK",
                      "ran": [(t["task"], t["status"]) for t in ran],
                      "queue": [t["task"] for t in runnable(store, now)]}, indent=1))
    return 1 if problems else 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--state", required=True, type=Path)
    ap.add_argument("--max-tasks", type=int, default=4)
    ap.add_argument("--max-minutes", type=float, default=45.0)
    a = ap.parse_args()
    now = datetime.now(timezone.utc).replace(microsecond=0)  # the command line's clock: the cycle takes it as an argument
    return cycle(a.state, now, a.max_tasks, a.max_minutes, github_issue())


__all__ = ["CATALOG", "CYCLE_VERSION", "alert", "cycle", "incomplete", "integrity", "learn", "ready", "report",
           "run_tasks", "seed", "send_alerts", "validated_rules"]

if __name__ == "__main__":
    raise SystemExit(main())
