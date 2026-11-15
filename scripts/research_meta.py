"""What the whole research record says when it is read together (docs/RESEARCH_META_ANALYSIS.md).

    python scripts/research_meta.py            # writes docs/RESEARCH_META_ANALYSIS.md and research/META_ANALYSIS.json

Everything is computed from committed files: the registry (research/registry.jsonl), the edge registry
(research/knowledge/edge_registry.json) and the discovery lab's ledger of classed rules
(research/dlab/candidates.jsonl). No market data is read, so no row is looked at that was not already looked at, and
no test is charged. It describes the record. It validates nothing and proposes no trade.
"""

from __future__ import annotations

import argparse
import json
import math
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

META_VERSION = "meta-1.0.0"
PANELS = {"perpetuals (55 Binance contracts by day)": ("DLAB-CRD-1", "DLAB-CRD-D1"),
          "funds (31 US-listed funds by day)": ("DLAB-ETF-1", "DLAB-ETF-D1"),
          "energy (WTI and natural gas by day)": ("DLAB-ENG-1",)}
POSITIVE = ("INSUFFICIENT_POWER", "PROMISING_UNCONFIRMED")
HOLDS = ((0, 2, "under 2 rows"), (2, 5, "2 to 5 rows"), (5, 15, "5 to 15 rows"), (15, 1e9, "15 rows or more"))
BAR = 3.0


def _mean(xs):
    return sum(xs) / len(xs) if xs else None


def _sd(xs):
    if len(xs) < 2:
        return None
    m = _mean(xs)
    return math.sqrt(sum((x - m) ** 2 for x in xs) / (len(xs) - 1))


def _median(xs):
    s = sorted(xs)
    return None if not s else s[len(s) // 2] if len(s) % 2 else (s[len(s) // 2 - 1] + s[len(s) // 2]) / 2


def _corr(a, b):
    if len(a) < 3:
        return None
    ma, mb = _mean(a), _mean(b)
    va, vb = sum((x - ma) ** 2 for x in a), sum((y - mb) ** 2 for y in b)
    return sum((x - ma) * (y - mb) for x, y in zip(a, b)) / math.sqrt(va * vb) if va > 0 and vb > 0 else None


def _ranks(xs):
    order = sorted(range(len(xs)), key=lambda i: xs[i])
    r = [0.0] * len(xs)
    for k, i in enumerate(order):
        r[i] = float(k)
    return r


def _r(x, nd=2):
    return None if x is None else round(x, nd)


def gross_t(r: dict) -> float | None:
    """The check-row t before costs: the same spread of daily P&L, the mean without its costs."""
    c = r["check"]
    if not c.get("mean") or c.get("gross_mean") is None or c.get("t") is None:
        return None
    return c["gross_mean"] / c["mean"] * c["t"]


def panel(rows: list[dict]) -> dict:
    """One panel's classed rules read together."""
    both = [r for r in rows if (r.get("fit") or {}).get("t") is not None and (r.get("check") or {}).get("t") is not None
            and r["class"] != "INSUFFICIENT_DATA"]
    ft, ct = [r["fit"]["t"] for r in both], [r["check"]["t"] for r in both]
    gt = [g for g in (gross_t(r) for r in both) if g is not None and abs(g) < 50]
    qs = sorted(ft)
    cuts = [qs[int(len(qs) * q)] for q in (0.25, 0.5, 0.75)] if len(qs) >= 8 else []
    quart = []
    if cuts:
        for name, lo, hi in (("weakest quarter", -1e9, cuts[0]), ("second", cuts[0], cuts[1]), ("third", cuts[1], cuts[2]),
                             ("strongest quarter", cuts[2], 1e9)):
            sel = [r for r in both if lo < r["fit"]["t"] <= hi] if name != "weakest quarter" else [r for r in both if r["fit"]["t"] <= hi]
            if sel:
                quart.append({"quarter": name, "rules": len(sel), "fit_t_from": _r(min(r["fit"]["t"] for r in sel)),
                              "fit_t_to": _r(max(r["fit"]["t"] for r in sel)), "mean_check_t": _r(_mean([r["check"]["t"] for r in sel])),
                              "positive_after_costs": _r(_mean([r["check"]["t"] > 0 for r in sel]))})
    holds = []
    for lo, hi, name in HOLDS:
        sel = [r for r in both if r["check"].get("mean_hold") is not None and lo <= r["check"]["mean_hold"] < hi]
        if sel:
            holds.append({"held": name, "rules": len(sel), "mean_check_t": _r(_mean([r["check"]["t"] for r in sel])),
                          "median_gross_bp_a_row": _r(_median([(r["check"].get("gross_mean") or 0) * 1e4 for r in sel])),
                          "median_net_bp_a_row": _r(_median([r["check"]["mean"] * 1e4 for r in sel])),
                          "positive_after_costs": _r(_mean([r["check"]["t"] > 0 for r in sel]))})
    fams = []
    for fam in sorted({r["family"] for r in rows}):
        mine = [r for r in both if r["family"] == fam]
        if not mine:
            continue
        fams.append({"family": fam, "rules": len(mine), "mean_check_t": _r(_mean([r["check"]["t"] for r in mine])),
                     "positive_after_costs": sum(r["check"]["t"] > 0 for r in mine),
                     "positive_before_costs_only": sum((r["check"].get("gross_mean") or 0) > 0 and r["check"]["mean"] <= 0 for r in mine),
                     "overfit": sum(r["class"] == "OVERFIT" for r in mine)})
    weak = [r for r in rows if r["class"] in POSITIVE]
    centre, spread = _mean(ct), _sd(ct)
    # What survives selection on the check rows: a t-statistic has a sampling spread of about one, so what the spread
    # of the rules' t leaves beyond that is how much real difference there is between them.
    keep = max(0.0, 1.0 - 1.0 / spread ** 2) if spread and spread > 0 else 0.0
    weak_t = [r["check"]["t"] for r in weak]
    exp_member = centre + keep * (_mean(weak_t) - centre) if weak_t else None
    fams_w = Counter(r["family"] for r in weak)
    shares = [1.0 / (len(fams_w) * fams_w[r["family"]]) for r in weak]
    sds = [abs(r["check"]["mean"]) * math.sqrt(r["check"]["n"]) / abs(r["check"]["t"]) for r in weak] if weak else []
    agg_mean = sum(w * r["check"]["mean"] for w, r in zip(shares, weak))
    agg_sd = math.sqrt(sum((w * s) ** 2 for w, s in zip(shares, sds))) if sds else None
    n_check = _median([r["check"]["n"] for r in weak]) if weak else None
    agg_in = agg_mean / agg_sd * math.sqrt(n_check) if agg_sd else None
    # the aggregate's t scales with its members' means: the same share of it survives as of a member's
    frac = (exp_member / _mean(weak_t)) if weak_t and _mean(weak_t) else None
    agg_out = agg_in * frac if agg_in is not None and frac is not None else None
    p_pass = 0.5 * math.erfc((BAR - agg_out) / math.sqrt(2)) if agg_out is not None else None
    plans = [r["plan"] for r in weak if isinstance(r.get("plan"), dict)]
    years = [p["more_discovery_years"] for p in plans if p.get("more_discovery_years") is not None]
    return {"rules": len(rows), "by_class": dict(Counter(r["class"] for r in rows)),
            "with_fit_and_check": len(both),
            "fit_check_correlation": _r(_corr(ft, ct), 3), "fit_check_rank_correlation": _r(_corr(_ranks(ft), _ranks(ct)), 3),
            "correlation_standard_error": _r(1 / math.sqrt(len(both) - 3), 3) if len(both) > 3 else None,
            "check_t_centre": _r(centre), "check_t_spread": _r(spread), "positive_after_costs": _r(_mean([t > 0 for t in ct])),
            "gross_check_t_centre": _r(_mean(gt)), "gross_check_t_spread": _r(_sd(gt)), "positive_before_costs": _r(_mean([g > 0 for g in gt])),
            "by_fit_strength": quart, "by_holding_time": holds, "by_family": fams,
            "lost_only_after_costs": sum((r["check"].get("gross_mean") or 0) > 0 and r["class"] == "NEGATIVE_EXPECTANCY" for r in both),
            "lost": sum(r["class"] == "NEGATIVE_EXPECTANCY" for r in rows),
            "weak_positives": {"rules": len(weak), "families": len(fams_w), "mean_check_t": _r(_mean(weak_t)), "best_check_t": _r(max(weak_t)) if weak_t else None,
                               "share_of_the_distance_that_survives_selection": _r(keep), "expected_t_of_a_member_on_new_rows": _r(exp_member),
                               "aggregate_t_on_the_rows_it_was_chosen_on": _r(agg_in), "aggregate_expected_t_on_new_rows": _r(agg_out),
                               "chance_to_reach_3": _r(p_pass, 4),
                               "told_from_noise_within_one_more_year": sum(y <= 1 for y in years), "within_three": sum(y <= 3 for y in years),
                               "median_more_years_needed": _r(_median(years), 1), "plans": len(plans)},
            "too_few_rows": sum(r["class"] == "INSUFFICIENT_DATA" for r in rows),
            "closed_families": dict(Counter(_closed(r["reason"]) for r in rows if r["class"] == "REPEATS_CLOSED_FAMILY"))}


def _closed(reason: str) -> str:
    """The closed family a rule was recognised as, from the reason the triage wrote."""
    for tag in ("XSM-1", "XTS-1", "SEC-1", "CR-", "FND-", "TRND-1", "DIV-", "VOLM-1"):
        if tag in reason:
            i = reason.index(tag)
            return reason[i:].split(")")[0].split(",")[0].split(" ")[0].rstrip(":")
    return "other"


def registry_summary(root: Path = ROOT) -> dict:
    reg = [json.loads(x) for x in (root / "research" / "registry.jsonl").read_text().splitlines() if x.strip()]
    trials = [r for r in reg if r["kind"] == "trial"]
    verdicts = {r["trial"]: r for r in reg if r["kind"] == "verdict"}
    status = Counter(verdicts[t["id"]]["status"] if t["id"] in verdicts else "PENDING" for t in trials)
    uni: dict[str, dict] = {}
    for t in trials:
        st = verdicts[t["id"]]["status"] if t["id"] in verdicts else "PENDING"
        for u in sorted({x["universe"] for x in t["uses"]}):
            d = uni.setdefault(u, {"trials": 0, "tests": 0, "failed": 0, "passed": 0, "pending": 0})
            d["trials"] += 1
            d["tests"] += t["tests"]
            d["failed"] += st == "FAILED"
            d["passed"] += st == "PASSED"
            d["pending"] += st == "PENDING"
    return {"trials": len(trials), "verdicts": len(verdicts), "status": dict(status), "tests": sum(t["tests"] for t in trials),
            "universes": dict(sorted(uni.items(), key=lambda kv: -kv[1]["tests"])),
            "pending": [t["id"] for t in trials if t["id"] not in verdicts],
            "passed": [t["id"] for t in trials if t["id"] in verdicts and verdicts[t["id"]]["status"] == "PASSED"]}


def edges_summary(root: Path = ROOT) -> dict:
    e = json.loads((root / "research" / "knowledge" / "edge_registry.json").read_text())
    rej = [x for x in e["edges"] if x["status"] == "REJECTED"]
    checks = Counter(c.split(":")[-1] for x in rej for c in (x.get("failed_checks") or []))
    one = [x for x in rej if len(x.get("failed_checks") or []) == 1]
    net = [x["net_expectancy"] for x in rej if x.get("net_expectancy") is not None]
    ts = [x["t_stat"] for x in rej if x.get("t_stat") is not None]
    return {"edges": len(e["edges"]), "counts": {k: v for k, v in e["counts"].items() if v},
            "rejected": len(rej), "failed_checks": checks.most_common(12),
            "rejected_on_one_gate": len(one), "of_them_on_the_bar": sum((x["failed_checks"][0].split(":")[-1] in ("t", "significance", "t_day")) for x in one),
            "rejected_with_a_negative_mean": sum(x < 0 for x in net), "rejected_with_a_recorded_mean": len(net),
            "rejected_t_median": _r(_median(ts)), "rejected_t_above_2": sum(t >= 2 for t in ts), "rejected_with_a_t": len(ts),
            "near_misses": [{"edge": x["edge_id"], "t": x.get("t_stat"), "bar": x.get("t_required"), "program": x.get("program")}
                            for x in e["edges"] if x["status"] == "PROMISING"],
            "validated": [{"edge": x["edge_id"], "t": x.get("t_stat"), "bar": x.get("t_required")} for x in e["edges"] if x["status"] == "VALIDATED"]}


def build(root: Path = ROOT) -> dict:
    rows = [json.loads(x) for x in (root / "research" / "dlab" / "candidates.jsonl").read_text().splitlines() if x.strip()]
    rows = [r for r in rows if "event" not in r]
    return {"version": META_VERSION, "rules": len(rows), "by_class": dict(Counter(r["class"] for r in rows)),
            "panels": {name: panel([r for r in rows if r["run"] in runs]) for name, runs in PANELS.items()},
            "registry": registry_summary(root), "edges": edges_summary(root)}


# ── the document ────────────────────────────────────────────────────────────

def _pct(x):
    return "n/a" if x is None else f"{x * 100:.0f}%"


def _n(x, nd=2):
    return "n/a" if x is None else f"{x:,.{nd}f}"


def render(m: dict, now: datetime) -> str:
    g, e = m["registry"], m["edges"]
    o = ["# What the research record says when it is read together", "",
         "**RESEARCH ONLY · NOTHING HERE IS A PROFIT CLAIM.** Written by `scripts/research_meta.py` from the committed "
         "record alone: the registry, the edge registry and the discovery lab's ledger of classed rules. No market data "
         "is read, so nothing is looked at that was not already looked at, and no test is charged. It describes the "
         "record; it validates nothing.", "",
         f"Generated {now:%Y-%m-%d %H:%M} UTC · {m['version']}", "",
         "## 1. What was read", "",
         f"- {g['trials']} registered hypotheses with {g['tests']:,} counted tests; {g['verdicts']} verdicts: "
         + ", ".join(f"{v} {k}" for k, v in sorted(g["status"].items(), key=lambda kv: -kv[1])) + ".",
         f"- {e['edges']} judged trading edges: " + ", ".join(f"{v} {k}" for k, v in sorted(e["counts"].items(), key=lambda kv: -kv[1])) + ".",
         f"- {m['rules']} rules found in data by the discovery lab and classed, each kept with its reason: "
         + ", ".join(f"{v} {k}" for k, v in sorted(m["by_class"].items(), key=lambda kv: -kv[1])) + ".", "",
         "## 2. The registered hypotheses, by the data they used", "",
         "| Data | Hypotheses | Counted tests | Failed | Passed | Pending |", "|---|---|---|---|---|---|"]
    o += [f"| `{u}` | {d['trials']} | {d['tests']:,} | {d['failed']} | {d['passed']} | {d['pending']} |" for u, d in g["universes"].items()]
    o += ["", f"A PASSED line is a stage, not an edge: {', '.join(g['passed'])}. The edge registry below says which of them is a "
          f"validated edge: {', '.join(x['edge'] for x in e['validated']) or 'none'}.", "",
          "Pending: " + ", ".join(g["pending"]) + ".", "",
          "## 3. Why the judged edges failed", "",
          f"Of {e['rejected']} rejected edges, {e['rejected_with_a_recorded_mean']} have a recorded mean after costs and "
          f"{e['rejected_with_a_negative_mean']} of those are negative. {e['rejected_with_a_t']} have a t-statistic: its median is "
          f"{_n(e['rejected_t_median'])}, and {e['rejected_t_above_2']} reached 2. {e['rejected_on_one_gate']} failed a single gate, "
          f"{e['of_them_on_the_bar']} of them the bar itself.", "",
          "| Gate failed | Edges |", "|---|---|"]
    o += [f"| {k} | {v} |" for k, v in e["failed_checks"]]
    o += ["", "The gates fail together: an edge that is not there fails its t, its random baseline, its halves and its "
          "instruments at once. The exceptions are the near misses, which failed on the bar alone:", "",
          "| Near miss | t | Bar |", "|---|---|---|"]
    o += [f"| {x['edge']} | {_n(x['t'], 2) if x['t'] is not None else 'in its artifact'} | {_n(x['bar'], 2)} |" for x in e["near_misses"]]
    o += ["", "## 4. The rules found in data", ""]
    for name, p in m["panels"].items():
        w = p["weak_positives"]
        o += [f"### {name[0].upper() + name[1:]}", "",
              f"{p['rules']} rules: " + ", ".join(f"{v} {k}" for k, v in sorted(p["by_class"].items(), key=lambda kv: -kv[1])) + ".", "",
              f"**Does a rule's strength where it was found carry to the rows after?** Over {p['with_fit_and_check']} rules the "
              f"correlation between the fit-row t and the check-row t is **{_n(p['fit_check_correlation'], 3)}** (by rank "
              f"{_n(p['fit_check_rank_correlation'], 3)}; standard error {_n(p['correlation_standard_error'], 3)}).", ""]
        if p["by_fit_strength"]:
            o += ["| By strength on the fit rows | Rules | Fit t | Mean check t | Positive after costs |", "|---|---|---|---|---|"]
            o += [f"| {q['quarter']} | {q['rules']} | {_n(q['fit_t_from'])} to {_n(q['fit_t_to'])} | {_n(q['mean_check_t'])} | {_pct(q['positive_after_costs'])} |"
                  for q in p["by_fit_strength"]]
            o += [""]
        o += [f"**Before and after costs.** Before costs the check-row t are centred at {_n(p['gross_check_t_centre'])} (spread "
              f"{_n(p['gross_check_t_spread'])}) and {_pct(p['positive_before_costs'])} are positive. After costs: centred at "
              f"{_n(p['check_t_centre'])} (spread {_n(p['check_t_spread'])}), {_pct(p['positive_after_costs'])} positive. "
              f"{p['lost_only_after_costs']} of the {p['lost']} rules that lost did so only after costs.", "",
              ]
        if p["by_holding_time"]:
            o += ["| Held for | Rules | Median before costs | Median after costs | Mean check t | Positive after costs |", "|---|---|---|---|---|---|"]
            o += [f"| {h['held']} | {h['rules']} | {_n(h['median_gross_bp_a_row'])} bp a row | {_n(h['median_net_bp_a_row'])} bp a row | {_n(h['mean_check_t'])} | "
                  f"{_pct(h['positive_after_costs'])} |" for h in p["by_holding_time"]]
        else:
            o += ["Holding times were not recorded for this panel's rules (its scan ran under the lab's first version)."]
        o += ["", "| Family | Rules | Mean check t | Positive after costs | Positive before costs only | Overfit |", "|---|---|---|---|---|---|"]
        o += [f"| {f['family']} | {f['rules']} | {_n(f['mean_check_t'])} | {f['positive_after_costs']} | {f['positive_before_costs_only']} | {f['overfit']} |"
              for f in p["by_family"]]
        if w["rules"]:
            o += ["", f"**The {w['rules']} weak positives** (positive on the check rows, not told from noise; {w['families']} families; "
                  f"mean check t {_n(w['mean_check_t'])}, best {_n(w['best_check_t'])}). They were chosen on the check rows from a population "
                  f"centred at {_n(p['check_t_centre'])}. A t-statistic's own sampling spread is about one, so of a rule's distance from the "
                  f"centre about {_pct(w['share_of_the_distance_that_survives_selection'])} is expected to survive: a member's expected t on new "
                  f"rows is **{_n(w['expected_t_of_a_member_on_new_rows'])}**. Held together with the capital shared by family, they show t "
                  f"{_n(w['aggregate_t_on_the_rows_it_was_chosen_on'])} on the rows they were chosen on (if uncorrelated) and an expected "
                  f"**{_n(w['aggregate_expected_t_on_new_rows'])}** on new rows: a chance of about {_n((w['chance_to_reach_3'] or 0) * 100, 1)}% to reach "
                  f"3.0. By their own plans {w['told_from_noise_within_one_more_year']} of {w['plans']} could be told from noise with one more year "
                  f"of rows and {w['within_three']} with three (median {_n(w['median_more_years_needed'], 1)} years)."]
        if p["closed_families"]:
            o += ["", "Recognised by what they do as families already judged and closed: "
                  + ", ".join(f"{k} {v}" for k, v in sorted(p["closed_families"].items(), key=lambda kv: -kv[1])) + "."]
        o += [""]
    return "\n".join(o)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(ROOT / "docs" / "RESEARCH_META_ANALYSIS.md"))
    ap.add_argument("--json", default=str(ROOT / "research" / "META_ANALYSIS.json"))
    ap.add_argument("--now", default=None)
    a = ap.parse_args(argv)
    now = datetime.fromisoformat(a.now) if a.now else datetime.now(timezone.utc)
    m = build()
    tail = Path(a.out).with_suffix(".tail.md")
    text = render(m, now)
    if tail.exists():  # the director's reading of the tables: written by hand, kept apart from what is computed
        text += "\n" + tail.read_text()
    Path(a.out).write_text(text + ("\n" if not text.endswith("\n") else ""))
    Path(a.json).write_text(json.dumps(m, indent=1, sort_keys=True) + "\n")
    print(json.dumps({"rules": m["rules"], "trials": m["registry"]["trials"], "edges": m["edges"]["edges"]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
