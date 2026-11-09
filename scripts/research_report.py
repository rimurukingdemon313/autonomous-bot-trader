"""The research pipeline's report, kept apart from trading (the owner, 2026-11-09).

    python scripts/research_report.py                    # -> docs/RESEARCH_REPORT.md and research/RESEARCH_REPORT.json
    python scripts/research_report.py --day 2026-11-09   # the daily section for that UTC day

RESEARCH ONLY: NO MONEY, NO TRADING RESULT. Every figure here is either:

- a test of an idea on history (a backtest), judged once against rules fixed before it ran; or
- a sealed out-of-sample check.

Paper-trading results are in the trend desk's TRADING_REPORT.md on the trend-desk-data branch. They are never added
here, and these are never added there.

It is built only from what is committed:

- research/registry.jsonl: every trial registered and every verdict, with their times. It is append-only.
- the trading-edge classification (aitrader/research/discovery/edges.py), rebuilt here and never copied. A registry
  PASSED is a test outcome, not a status: only that classification says VALIDATED.
- research/knowledge/*.json: each verdict's evidence. Its own hash, recorded with the verdict, is checked against the
  file as it is now.
- research/preregistrations/*.md: each spec's hash must be quoted there.
- research/QUEUE.md: ideas checked and dropped before building, by date (no test spent on them).

A day with nothing new says so. Nothing is padded to look active.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from datetime import date, datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from aitrader.research.registry import Holdout, Registry  # noqa: E402

REPORT_VERSION = "research-report-1.0.0"
DROP_HEAD = re.compile(r"^\*\*[^*]*?\b(?:checked|considered|dropped)\b[^*]*?(\d{4}-\d{2}-\d{2})", re.I)


# ── the record ───────────────────────────────────────────────────────────

def read_registry(root: Path) -> tuple[dict[str, dict], dict[str, dict]]:
    trials, verdicts = {}, {}
    for line in (root / "research" / "registry.jsonl").read_text().splitlines():
        if line.strip():
            r = json.loads(line)
            if r.get("kind", "trial") == "trial":
                trials[r["id"]] = r
            else:
                verdicts[r["trial"]] = r
    return trials, verdicts


def queue_drops(text: str) -> list[dict]:
    """The dated sections of research/QUEUE.md that record ideas checked and dropped before building: each section's
    date, its heading, and the ideas in its table, one per row. A section without a table is one check, named by its
    heading."""
    out, cur, prev, ideas_table = [], None, "", False
    for line in text.splitlines():
        if line.startswith("|") and not prev.startswith("|"):  # a table's header row: only an Idea table lists ideas
            ideas_table = line.startswith("| Idea")
        prev = line
        m = DROP_HEAD.match(line)
        if m:
            cur = {"date": m.group(1), "heading": line.strip("* ").split("**")[0].strip().rstrip("."), "ideas": []}
            out.append(cur)
            continue
        if cur is None:
            continue
        if line.startswith("**") or line.startswith("#"):
            cur = None  # the section ends at the next bold heading
            continue
        if ideas_table and line.startswith("| ") and not line.startswith("| Idea"):
            cur["ideas"].append(line.split("|")[1].strip())
    return out


def _body_sha(body: dict) -> str:
    return hashlib.sha256(json.dumps({k: v for k, v in body.items() if k != "sha256"}, sort_keys=True).encode()
                          ).hexdigest()


def evidence(root: Path, trial: dict, verdict: dict | None) -> dict:
    """What can be checked about a verdict's evidence now: its preregistration, the spec hash quoted there, its
    knowledge file, and that file's hash against the one recorded with the verdict. None: nothing to check."""
    prereg = trial.get("preregistration")
    p = root / prereg if prereg else None
    spec = (trial.get("design") or {}).get("spec_sha256")
    res = (verdict or {}).get("result") or {}
    art = res.get("artifact") or (f"research/knowledge/{trial['id']}.json"
                                  if (root / f"research/knowledge/{trial['id']}.json").exists() else None)
    out = {"preregistration": prereg, "preregistration_exists": p.exists() if p else None,
           "spec_quoted": (spec in p.read_text()) if spec and p and p.exists() else None,
           "artifact": art, "artifact_unchanged": None}
    if art and res.get("artifact_sha256"):
        a = root / art
        out["artifact_unchanged"] = a.exists() and _body_sha(json.loads(a.read_text())) == res["artifact_sha256"]
    elif art and spec and (root / art).exists():  # no hash recorded with the verdict: the file must name the spec
        body = json.loads((root / art).read_text())  # (and the code, where it records one) registered before the test
        code = (trial.get("design") or {}).get("code_sha256")
        if body.get("spec_sha256"):
            out["artifact_unchanged"] = body["spec_sha256"] == spec and \
                (not body.get("code_sha256") or not code or body["code_sha256"] == code)
    return out


def classification(root: Path) -> dict:
    from aitrader.research.discovery.edges import build
    reg = build(root / "research")
    return {"counts": {k: v for k, v in reg["counts"].items() if v},
            "standing": [{k: e.get(k) for k in ("edge_id", "program", "status", "t_stat", "t_required",
                                                 "out_of_sample_expectancy", "note", "source")}
                         for e in reg["edges"] if e["status"] != "REJECTED"]}


# ── the report ───────────────────────────────────────────────────────────

def _day(ts: str) -> str:
    return ts[:10]


def _ok(x) -> str:
    return "—" if x is None else "yes" if x else "**NO**"


def build_report(root: Path, day: date, now: datetime, classify=classification, ideas: list[dict] | None = None,
                 cycles: list[dict] | None = None) -> dict:
    trials, verdicts = read_registry(root)
    reg = Registry.load(root / "research" / "registry.jsonl", Holdout.load(root / "research" / "holdout.json"))
    drops = queue_drops((root / "research" / "QUEUE.md").read_text())
    d = str(day)
    universes = sorted({u["universe"] for t in trials.values() for u in t.get("uses", [])})
    pending = []
    for tid, t in trials.items():
        if tid in verdicts:
            continue
        judge = [u for u in t.get("uses", []) if u.get("role") == "judge"]
        pending.append({"id": tid, "registered": _day(t["registered"]), "title": t.get("title"),
                        "judge_until": max(u["end"] for u in judge) if judge else None,
                        "kind": "forward" if judge and max(u["end"] for u in judge) > d else
                        "archive record" if tid.startswith("archive-") else "design only" if not judge else "due"})
    checked = [evidence(root, trials[v["trial"]], v) for v in verdicts.values() if v["trial"] in trials]
    return {
        "version": REPORT_VERSION, "generated": now.isoformat(), "day": d,
        "today": {
            "registered": [{"id": t["id"], "title": t.get("title"), "hypothesis": t.get("hypothesis"),
                            "preregistration": t.get("preregistration"), "tests": t.get("tests"),
                            "uses": t.get("uses")} for t in trials.values() if _day(t["registered"]) == d],
            "verdicts": [{"id": v["trial"], "status": v["status"], "result": v.get("result"),
                          "evidence": evidence(root, trials.get(v["trial"], {"id": v["trial"]}), v)}
                         for v in verdicts.values() if _day(v["recorded"]) == d],
            "dropped_before_building": [x for x in drops if x["date"] == d],
        },
        "cumulative": {
            "trials": len(trials), "verdicts": len(verdicts),
            "by_verdict": {s: sum(1 for v in verdicts.values() if v["status"] == s)
                           for s in sorted({v["status"] for v in verdicts.values()})},
            "pending": pending,
            "dropped_before_building": sum(len(x["ideas"]) for x in drops),
            "drop_checks": len(drops), "drop_days": len({x["date"] for x in drops}),
            "bars": {u: {"tests": reg.tests_on(u), "next_bar_t": round(reg.threshold_for_next(u), 4)}
                     for u in universes},
            "evidence_checked": sum(1 for c in checked if c["artifact_unchanged"] is not None),
            "evidence_unchanged": sum(1 for c in checked if c["artifact_unchanged"] is True),
            "evidence_changed": [v["trial"] for v, c in zip(verdicts.values(), checked)
                                 if c["artifact_unchanged"] is False],
            "spec_not_quoted": [v["trial"] for v, c in zip(verdicts.values(), checked) if c["spec_quoted"] is False],
        },
        "classification": classify(root),
        "seal": json.loads((root / "research" / "holdout.json").read_text()),
        "recent_verdicts": [{"id": v["trial"], "recorded": v["recorded"], "status": v["status"],
                             "evidence": evidence(root, trials.get(v["trial"], {"id": v["trial"]}), v)}
                            for v in sorted(verdicts.values(), key=lambda v: v["recorded"], reverse=True)[:25]],
        "engine": None if ideas is None else engine_section(ideas, cycles or [], d),
    }


def engine_section(ideas: list[dict], cycles: list[dict], d: str) -> dict:
    """What the autonomous engine (scripts/research_engine.py) generated: today, all time, what waits to be built,
    and whether it is running."""
    ok = [c for c in cycles if c["step"] == "ideas" and c["status"] == "OK"]
    last = [c for c in cycles if c["step"] == "ideas"]
    built = {i.get("built_as") for i in ideas if i.get("built_as")}
    return {"today": [i for i in ideas if i["cycle"] == d],
            "by_decision": {k: sum(1 for i in ideas if i["decision"] == k) for k in sorted({i["decision"] for i in ideas})},
            "queued": [i for i in ideas if i["decision"] == "QUEUED_FOR_BUILD" and not i.get("built_as")],
            "built": sorted(x for x in built if x), "total": len(ideas),
            "last_ok": ok[-1]["at"] if ok else None, "last": last[-1] if last else None,
            "integrity": next((c for c in reversed(cycles) if c["step"] == "integrity"), None)}


def _ar(r: dict) -> str:
    t, c = r["today"], r["cumulative"]
    passed = sum(1 for v in t["verdicts"] if v["status"] == "PASSED")
    dropped = sum(len(x["ideas"]) for x in t["dropped_before_building"])
    checks = len(t["dropped_before_building"])
    val = [s["edge_id"] for s in r["classification"]["standing"] if s["status"] == "VALIDATED"]
    today = ("اليوم ما صار شي جديد بالبحث." if not (t["registered"] or t["verdicts"] or checks) else
             f"اليوم: {len(t['registered'])} فرضية جديدة انسجلت، {len(t['verdicts'])} انحكمت ({passed} نجحت)، "
             f"و{checks} فحص قبل البناء رفض {dropped} فكرة من غير ما نصرف عليها اختبار.")
    return ("**بالعربي:** هذا تقرير البحث وحده: اختبارات أفكار على بيانات تاريخية، مو أرباح تداول، وما بيه ولا رقم "
            f"من الحساب الورقي. {today} المجموع من البداية: {c['trials']} فرضية مسجلة، "
            f"{c['by_verdict'].get('FAILED', 0)} فشلت. المعتمد (VALIDATED): {'، '.join(val) or 'ولا وحدة'}.")


def engine_markdown(e: dict) -> list[str]:
    L = ["## The autonomous engine's ideas (generated by models, never approved by them)", "",
         "A proposer model suggests hypotheses; a critic on another model can only reject; arithmetic drops any that "
         "cannot reach their market's bar even at the strength claimed. A queued idea is built only after its claim "
         "is checked at the source, then preregistered and judged once. The engine itself registers, tests and "
         "approves nothing.", ""]
    last, integ = e["last"], e["integrity"]
    L += [f"- Last cycle: {last['at'][:16].replace('T', ' ') + ' UTC, ' + last['status'] if last else 'none yet'}"
          + (f" ({str((last.get('detail') or {}).get('why')).removeprefix('FAILED: ')})"
             if last and last['status'] != 'OK' else ""),
          f"- Last successful idea step: {e['last_ok'][:16].replace('T', ' ') + ' UTC' if e['last_ok'] else 'none yet'}",
          "- Integrity of the record at the last cycle: "
          + ("OK" if integ and integ["status"] == "OK" else "; ".join(integ.get("detail") or []) if integ else "not run"),
          f"- All time: {e['total']} ideas: " + (", ".join(f"{k} {v}" for k, v in e["by_decision"].items()) or "none"),
          ""]
    L += ["**Today:**", ""]
    for i in e["today"]:
        L.append(f"- **{i['decision']}**: {i['title']} ({i['universe']}, {i['horizon']}). {i['why']}"
                 + ("" if i["decision"] != "REJECTED_BY_CRITIC" else f" (critic: {i.get('critic') or '?'})"))
    if not e["today"]:
        L.append("- none")
    L += ["", "**Queued for building** (each waits for its claim to be checked at the source):", ""]
    for i in e["queued"]:
        L.append(f"- {i['title']} ({i['universe']}; queued {i['cycle']}; claimed net Sharpe "
                 f"{i['claimed_sharpe_annual']} over {i['years_of_fresh_data']} fresh years): {i['evidence']}")
    if not e["queued"]:
        L.append("- none")
    return L + [""]


def markdown(r: dict) -> str:
    t, c, k = r["today"], r["cumulative"], r["classification"]
    L = ["# Research pipeline report", "",
         "**RESEARCH ONLY · NO MONEY · NOT A TRADING RESULT.** Every figure here is a test of an idea on history "
         "(a backtest), judged once against rules fixed before it ran, or a sealed out-of-sample check. Paper-trading "
         "results are in the trend desk's TRADING_REPORT.md (`trend-desk-data` branch) and are never added here.",
         "", _ar(r), "", f"Generated {r['generated'][:16].replace('T', ' ')} UTC from the committed record · "
         f"{r['version']}", "", f"## Today ({r['day']}, UTC)", ""]
    if not (t["registered"] or t["verdicts"] or t["dropped_before_building"]):
        L += ["Nothing new today: no idea checked, no test registered, no verdict.", ""]
    L += ["**New hypotheses registered** (each preregistered before any data was read):", ""]
    L += [f"- **{x['id']}**: {x['title']}. {x['hypothesis']} (`{x['preregistration']}`, {x['tests']} test"
          f"{'s' if x['tests'] != 1 else ''} counted)" for x in t["registered"]] or ["- none"]
    L += ["", "**Verdicts recorded** (each judged once):", ""]
    for v in t["verdicts"]:
        res = v["result"] or {}
        head = ", ".join(f"{k} {res[k]}" for k in ("t", "a_year_pct", "net_bp_per_trade") if k in res)
        gates = res.get("failed_gates")
        L.append(f"- **{v['id']}: {v['status']}**" + (f" ({head})" if head else "")
                 + (f"; failed gates: {', '.join(gates)}" if gates else "")
                 + f". Evidence: `{v['evidence']['artifact'] or '—'}`; matches its verdict: "
                 f"{_ok(v['evidence']['artifact_unchanged'])}")
    if not t["verdicts"]:
        L.append("- none")
    L += ["", "**Ideas checked and dropped before building** (no test spent; the reasons are in `research/QUEUE.md`):",
          ""]
    for x in t["dropped_before_building"]:
        L.append(f"- {x['heading']}" + (": " + "; ".join(x["ideas"]) if x["ideas"] else "") + ".")
    if not t["dropped_before_building"]:
        L.append("- none")
    L += ["", "## Cumulative (since the registry began)", "", "| | |", "|---|---|",
          f"| Hypotheses registered | {c['trials']} |",
          f"| Verdicts | {c['verdicts']}: " + ", ".join(f"{s} {n}" for s, n in c["by_verdict"].items()) + " |",
          f"| Ideas dropped before building (no test spent) | {c['dropped_before_building']} in the tables of "
          f"{c['drop_checks']} dated checks, on {c['drop_days']} days |",
          "| Status of every judged hypothesis (the edge classification) | "
          + ", ".join(f"{s} {n}" for s, n in sorted(k["counts"].items())) + " |",
          f"| Evidence files that still match their verdict | {c['evidence_unchanged']} of "
          f"{c['evidence_checked']} checked"
          + (f"; **changed: {', '.join(c['evidence_changed'])}**" if c["evidence_changed"] else "") + " |",
          f"| Specs whose hash is missing from their preregistration | "
          f"{', '.join(c['spec_not_quoted']) or 'none'} |", ""]
    if r.get("engine") is not None:
        L += engine_markdown(r["engine"])
    L += ["## Validation status", "",
          "Every judged hypothesis not rejected, as the edge classification states it. Only VALIDATED may be "
          "promoted, and only by a person; PROMISING did not reach its bar and is not traded.", "",
          "| Edge | Status | t (bar) | Out-of-sample | The classification's note | Source |", "|---|---|---|---|---|---|"]
    for s in k["standing"]:
        oos = s["out_of_sample_expectancy"]
        L.append(f"| {s['edge_id']} | **{s['status']}** | {s['t_stat']} ({s['t_required']}) | "
                 f"{'—' if oos is None else f'{oos * 100:+.2f}% a month'} | {s['note'] or '—'} | `{s['source']}` |")
    L += ["", "**Forward tests running, each judged once at its preregistered end** (nothing is concluded before):",
          ""]
    for p in sorted((p for p in c["pending"] if p["kind"] == "forward"), key=lambda p: p["registered"]):
        until = "an open end (see its preregistration)" if (p["judge_until"] or "") >= "2100" else p["judge_until"]
        L.append(f"- {p['id']} (registered {p['registered']}; data to {until}): {p['title']}")
    other = [p for p in c["pending"] if p["kind"] != "forward"]
    if other:
        L += ["", "Also registered without a verdict here, and counted in every bar: "
              + "; ".join(f"{p['id']} ({p['kind']})" for p in sorted(other, key=lambda p: p["registered"])) + "."]
    L += ["", "## The bar each market's next test must clear", "",
          "Bonferroni over every test already counted on that market's data. The more an idea's data has been read, "
          "the higher its bar: discovery never lowers it.", "", "| Market data | Tests counted | Next bar (t) |",
          "|---|---|---|"]
    for u, b in sorted(c["bars"].items(), key=lambda kv: -kv[1]["tests"]):
        L.append(f"| {u} | {b['tests']} | {b['next_bar_t']:.3f} |")
    seal = r["seal"]
    L += ["", f"The sealed holdout: {seal['universe']} from {seal['start']} (sealed {seal['sealed_at'][:10]}). It is "
              "opened once, by a preregistered final test of a candidate that has passed, and never for discovery.",
          "", "## The last 25 verdicts, with their evidence", "",
          "| Recorded | Hypothesis | Verdict | Preregistration | Spec hash quoted | Evidence file | Matches |",
          "|---|---|---|---|---|---|---|"]
    for v in r["recent_verdicts"]:
        e = v["evidence"]
        L.append(f"| {v['recorded'][:10]} | {v['id']} | {v['status']} | "
                 f"{'`' + e['preregistration'] + '`' if e['preregistration'] else '—'} | {_ok(e['spec_quoted'])} | "
                 f"{'`' + e['artifact'] + '`' if e['artifact'] else '—'} | {_ok(e['artifact_unchanged'])} |")
    L += ["", "**Matches**: the evidence file's own hash equals the one recorded with its verdict; where none was "
              "recorded, the file names the spec (and code) hashes registered before the test. Every verdict is in "
              "`research/registry.jsonl`. Each program's command and frozen spec are in its preregistration, and the "
              "program refuses to judge if its spec or code no longer match the hashes recorded at registration.", ""]
    return "\n".join(L)


def write(root: Path, day: date, now: datetime, classify=classification, out: Path | None = None,
          ideas: list[dict] | None = None, cycles: list[dict] | None = None) -> dict:
    """To docs/ and research/ in the repository, or to `out` (the engine's state, published on research-data)."""
    r = build_report(root, day, now, classify, ideas, cycles)
    md, js = ((out / "RESEARCH_REPORT.md", out / "RESEARCH_REPORT.json") if out else
              (root / "docs" / "RESEARCH_REPORT.md", root / "research" / "RESEARCH_REPORT.json"))
    md.write_text(markdown(r))
    js.write_text(json.dumps(r, indent=1, sort_keys=True, default=str) + "\n")
    return r


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--day", type=date.fromisoformat)
    args = ap.parse_args()
    now = datetime.now(timezone.utc)  # the command line's clock; build_report takes it as an argument
    r = write(ROOT, args.day or now.date(), now)
    print(json.dumps({"day": r["day"], "registered": len(r["today"]["registered"]),
                      "verdicts": len(r["today"]["verdicts"]),
                      "dropped": sum(len(x["ideas"]) for x in r["today"]["dropped_before_building"]),
                      "status": r["classification"]["counts"]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
