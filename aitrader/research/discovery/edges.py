"""The trading-edge registry: every hypothesis the research has judged, as one edge record each.

Built from the committed evidence only — the confirmatory and discovery artifacts in
research/knowledge and the walk-forward results in research/results — so it cannot say more
than the evidence does. A field the evidence does not contain is None, never a plausible
number (CLAUDE.md rule 6).

Promotion levels (Round 2; transitions outside TRANSITIONS are refused):

    RESEARCH -> HYPOTHESIS -> TESTING -> PROMISING -> VALIDATED -> DEGRADED -> RETIRED
                    \\            \\          \\                          ^
                     +------------+----------+--> REJECTED   (DEGRADED -> VALIDATED if it recovers)

(DISCOVERED -> VALIDATING are Round 1's names for HYPOTHESIS -> TESTING and are still accepted.)

PROMISING is NOT validated. A judged hypothesis is PROMISING when it failed the registry's bar but
its judged, out-of-sample result is positive after costs with t >= 2, survives the cost stress and
beats random entries: evidence worth a fresh, preregistered test on NEW data, never a trade. A
VALIDATED edge passed everything (battery, board, registry threshold); none exists yet.

REJECTED and RETIRED are final: a rejected idea returns only as a NEW hypothesis with a new id,
charged against the registry like any other test. A registry record is research evidence, not a
promotion: only a person writes models/artifacts/promoted_edges.json, and never a size.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, replace
from pathlib import Path

#: 1.1.0: Round 2 promotion levels (RESEARCH, HYPOTHESIS, TESTING, PROMISING) and the PROMISING rule
#: 1.2.0: UNCERTAIN; frozen-but-unrun hypotheses (Round 3) enter the registry as HYPOTHESIS
#: 1.3.0: a check marked as a preregistered GATE that failed blocks PROMISING (COT-1: development,
#: validation, incremental-over-control...); a holdout artifact (`holdout_of`) supersedes the record
#: of the hypothesis it judged
#: 1.4.0: cross-sectional programs (RV-1): one record per hypothesis, its status the latest classification
#: across the program's stage artifacts (Stage 1 -> Stage 2 -> holdout)
EDGES_VERSION = "edges-1.7.0"  # 1.5.0: scheduled-flow programs (FLOW-1); 1.6.0: trend portfolios (DIV-*);
#                                1.6.1: a trend holdout failure is named, and the holdout t is in the note;
#                                1.7.0: retail-CFD programs (RC-*), including a replication on a new universe
STATUSES = ("RESEARCH", "HYPOTHESIS", "TESTING", "PROMISING", "UNCERTAIN", "DISCOVERED", "VALIDATING", "VALIDATED",
            "REJECTED", "DEGRADED", "RETIRED")
TRANSITIONS = {
    "RESEARCH": ("HYPOTHESIS", "REJECTED"),
    "HYPOTHESIS": ("TESTING", "REJECTED", "UNCERTAIN"),
    "UNCERTAIN": ("TESTING", "REJECTED"),  # evidence insufficient either way (e.g. data unavailable)
    "TESTING": ("PROMISING", "VALIDATED", "REJECTED"),
    "PROMISING": ("TESTING", "VALIDATED", "REJECTED"),
    "DISCOVERED": ("VALIDATING", "REJECTED"),
    "VALIDATING": ("PROMISING", "VALIDATED", "REJECTED"),
    "VALIDATED": ("DEGRADED", "RETIRED"),
    "DEGRADED": ("VALIDATED", "RETIRED"),
    "REJECTED": (),
    "RETIRED": (),
}
PROMISING_T = 2.0


def judged_status(validated: bool, checks: dict) -> str:
    """VALIDATED only if the program validated it; PROMISING if it failed the bar but its judged result
    is positive (t >= 2), survives the cost stress and beats random entries; otherwise REJECTED."""
    if validated:
        return "VALIDATED"
    if any(isinstance(v, dict) and v.get("gate") and not v.get("pass") for v in checks.values()):
        return "REJECTED"  # a preregistered gate failed: not even a near miss
    sig = checks.get("significance", {})
    if (sig.get("mean_R") or 0) > 0 and (sig.get("t") or 0) >= PROMISING_T \
            and checks.get("costs_stress", {}).get("pass") and checks.get("beats_random", {}).get("pass"):
        return "PROMISING"
    return "REJECTED"
_DIR = {"BUY": "BUY", "SELL": "SELL", 1: "BUY", -1: "SELL"}


class TransitionError(ValueError):
    pass


@dataclass(frozen=True)
class EdgeRecord:
    edge_id: str
    program: str
    direction: str  # BUY | SELL | BOTH (a model trading either side)
    instrument: tuple[str, ...]
    timeframe: str | None
    market_regime: dict | None  # measured per-regime means, not a claim about when it works
    entry_conditions: str
    exit_conditions: str
    sample_size: int | None
    gross_expectancy: float | None
    net_expectancy: float | None
    t_stat: float | None
    t_required: float | None
    profit_factor: float | None
    drawdown: float | None
    out_of_sample_expectancy: float | None
    walk_forward_expectancy: float | None
    cost_sensitivity: float | None  # net mean R with costs x1.5 and slippage x2
    complexity: int  # number of conditions (a model counts its feature count)
    stability: dict | None  # per-year or per-fold means
    status: str
    failed_checks: tuple[str, ...]
    source: str
    note: str | None = None  # a recorded correction (research/knowledge/corrections.json), never a silent edit

    def __post_init__(self):
        if self.status not in STATUSES:
            raise ValueError(f"unknown status {self.status!r}")


def transition(rec: EdgeRecord, new: str) -> EdgeRecord:
    if new not in TRANSITIONS.get(rec.status, ()):
        raise TransitionError(f"{rec.edge_id}: {rec.status} -> {new} is not allowed")
    return replace(rec, status=new)


def _r(x, nd=4):
    return None if x is None else round(float(x), nd)


def from_confirmatory(art: dict, drafts: dict[str, dict] | None = None) -> list[EdgeRecord]:
    """Each judged hypothesis of a confirmatory (or discovery) artifact. Judged on a segment
    nothing was fitted on, so the judged mean IS the out-of-sample expectancy."""
    out = []
    validated = set(art.get("validated") or [])
    for c in art.get("judged") or []:
        ch = c["battery"]["checks"]
        sig = ch.get("significance", {})
        n = ch.get("min_trades", {}).get("n")
        ok = c["id"] in validated
        yrs = ch.get("years", {}).get("by_year")
        h = (drafts or {}).get(c["id"], {})
        out.append(EdgeRecord(
            edge_id=c["id"], program=art["program"], direction=_DIR.get(c.get("side"), "BOTH"),
            instrument=tuple(h.get("instruments") or ()), timeframe=h.get("timeframe"),
            market_regime=(ch.get("regimes") or {}).get("cells"),
            entry_conditions=c.get("condition") or c.get("kind", "?"), exit_conditions=c.get("exit") or "?",
            sample_size=n, gross_expectancy=None, net_expectancy=_r(sig.get("mean_R")), t_stat=_r(sig.get("t"), 3),
            t_required=_r(sig.get("threshold"), 3), profit_factor=None, drawdown=None,
            out_of_sample_expectancy=_r(sig.get("mean_R")), walk_forward_expectancy=None,
            cost_sensitivity=_r(ch.get("costs_stress", {}).get("mean_R")),
            complexity=len((c.get("condition") or "").split("&")) if c.get("condition") else 0,
            stability={"by_year": yrs} if yrs else None, status=judged_status(ok, ch),
            failed_checks=tuple(c["battery"].get("failed", [])), source=f"research/knowledge/{art['program']}.json"))
    return out


def from_walk_forward(res: dict) -> EdgeRecord:
    """A walk-forward lab result: the pooled out-of-fold trades ARE the walk-forward expectancy."""
    spec, sysm = res["spec"], res["system"]
    rob = res.get("robustness", {}).get("costs_x1.5_slip_x2", {})
    return EdgeRecord(
        edge_id=res["trial"], program=res["trial"],
        direction="BOTH" if len(spec.get("sides", [])) == 2 else _DIR.get(spec["sides"][0], "BOTH"),
        instrument=tuple(spec["symbols"]), timeframe=spec["timeframe"], market_regime=None,
        entry_conditions=f"{spec['model']} on {len(spec['features'])} features, trade where predicted net R > "
                         f"{spec['threshold_r']}", exit_conditions=f"template {spec['template']}",
        sample_size=sysm.get("n"), gross_expectancy=None, net_expectancy=_r(sysm.get("mean_R")),
        t_stat=_r(sysm.get("t"), 3), t_required=_r(res.get("threshold_t"), 3), profit_factor=None, drawdown=None,
        out_of_sample_expectancy=_r(sysm.get("mean_R")), walk_forward_expectancy=_r(sysm.get("mean_R")),
        cost_sensitivity=_r(rob.get("mean_R")), complexity=len(spec["features"]),
        stability={"folds": {f["start"]: f["mean_R"] for f in res.get("folds", [])}},
        status="VALIDATED" if res.get("verdict") == "PASS" else "REJECTED",
        failed_checks=tuple(k for k, v in (res.get("checks") or {}).items() if not v),
        source=f"research/results/{res['trial']}.json")


RV_PAIRS = ("AUDUSD", "EURUSD", "GBPUSD", "NZDUSD", "USDCAD", "USDCHF", "USDJPY")
_RV_STATUS = {"STAGE2": "TESTING", "HOLDOUT_ELIGIBLE": "TESTING", "REJECTED": "REJECTED", "PROMISING": "PROMISING",
              "VALIDATED": "VALIDATED"}


def from_cross_sectional(stages: list[dict]) -> list[EdgeRecord]:
    """Records of a cross-sectional program from its stage artifacts (ordered Stage 1, Stage 2, holdout).
    t is the Stage-1 IC t; expectancy fields are the Stage-2 weekly NET return of the currency-neutral book
    (a fraction of notional, NOT R), None when Stage 2 was not reached."""
    s1 = stages[0]
    status = dict(s1.get("classification", {}))
    s2 = next((a for a in stages if a.get("stage") == 2), None)
    for a in stages[1:]:
        status.update(a.get("classification", {}))
    out = []
    for hid, r in sorted(s1["results"].items()):
        two = (s2 or {}).get("results", {}).get(hid)
        out.append(EdgeRecord(
            edge_id=hid, program=s1["program"], direction="BOTH", instrument=RV_PAIRS, timeframe="W1",
            market_regime=None, entry_conditions=f"cross-sectional rank: {hid}",
            exit_conditions="weekly rebalance of a currency-neutral book",
            sample_size=r.get("weeks", (r.get("weeks_low") or 0) + (r.get("weeks_high") or 0)),
            gross_expectancy=_r(two["gross"]["mean"]) if two else None,
            net_expectancy=_r(two["net"]["mean"]) if two else None, t_stat=_r(r.get("t"), 3),
            t_required=_r(s1.get("threshold"), 3), profit_factor=None, drawdown=None,
            out_of_sample_expectancy=_r(two["net"]["mean"]) if two else None, walk_forward_expectancy=None,
            cost_sensitivity=_r(two["robustness"]["R5_costs"]["net_mean_costs_x2"]) if two else None, complexity=1,
            stability={"ic_by_year": r["ic_by_year"]} if r.get("ic_by_year") else None,
            status=_RV_STATUS[status[hid]],
            failed_checks=tuple(k for k, v in r.get("gates", {}).items() if not v),
            source=f"research/knowledge/{s1['program']}.json",
            note="cross-sectional book: t is the Stage-1 information-coefficient t; expectancies are weekly returns "
                 "of notional, not R"))
    return out


FLOW_INSTRUMENTS = {"GOTOBI": ("USDJPY",), "FIX": ("EURUSD", "GBPUSD", "AUDUSD", "NZDUSD", "USDJPY", "USDCHF", "USDCAD")}


def from_flow(stages: list[dict]) -> list[EdgeRecord]:
    """Records of a scheduled-flow program (judged artifact, then its holdout if one was opened).
    Expectancies are NET basis points of the entry mid per observation, not R."""
    judged = stages[0]
    status = {k: ("TESTING" if v == "HOLDOUT_ELIGIBLE" else v) for k, v in judged.get("classification", {}).items()}
    hold = next((a for a in stages if a.get("holdout_of")), None)
    for k, v in (hold or {}).get("classification", {}).items():
        status[k] = v
    out = []
    for hid, r in sorted(judged["results"].items()):
        fam = "GOTOBI" if "GOTOBI" in hid else "FIX"
        h = (hold or {}).get("results", {}).get(hid)
        out.append(EdgeRecord(
            edge_id=hid, program=judged["program"], direction="BUY" if hid.endswith("PRE") else "SELL" if hid.endswith("POST") else "BOTH",
            instrument=FLOW_INSTRUMENTS[fam], timeframe="M15", market_regime=None,
            entry_conditions="scheduled clock window (research/preregistrations/FLOW-1.md)",
            exit_conditions="fixed clock exit", sample_size=r["net"]["n"],
            gross_expectancy=_r(r["gross"]["mean"]), net_expectancy=_r(r["net"]["mean"]), t_stat=_r(r["net"]["t"], 3),
            t_required=_r(judged.get("threshold"), 3), profit_factor=None, drawdown=_r(r.get("max_drawdown_bps")),
            out_of_sample_expectancy=_r(h["net"]["mean"]) if h else _r(r["validation"]["mean"]),
            walk_forward_expectancy=None, cost_sensitivity=_r(r["costs_x2"]["mean"]), complexity=1,
            stability={"by_year": r.get("by_year")}, status=status[hid],
            failed_checks=tuple(r.get("failed_gates", ())), source=f"research/knowledge/{judged['program']}.json",
            note="scheduled order flow: expectancies are net basis points per observation, not R"))
    return out


def from_trend(stages: list[dict]) -> list[EdgeRecord]:
    """Records of a portfolio trend program. Expectancies are MONTHLY NET PORTFOLIO RETURNS (a fraction
    of capital), not R; t is the t of the mean monthly net return over the judged period."""
    judged = stages[0]
    status = {k: ("TESTING" if v == "HOLDOUT_ELIGIBLE" else v) for k, v in judged.get("classification", {}).items()}
    hold = next((a for a in stages if a.get("holdout_of")), None)
    for k, v in (hold or {}).get("classification", {}).items():
        status[k] = v
    assets = tuple(sorted((judged.get("data_manifest") or {}).get("assets", {})))
    out = []
    for hid, r in sorted(judged["results"].items()):
        h = (hold or {}).get("results", {}).get(hid)
        out.append(EdgeRecord(
            edge_id=hid, program=judged["program"], direction="BOTH", instrument=assets, timeframe="MN",
            market_regime=None, entry_conditions="time-series momentum sign, volatility-targeted",
            exit_conditions="monthly rebalance", sample_size=r["net"]["n"],
            gross_expectancy=_r(r["gross"].get("mean_monthly")), net_expectancy=_r(r["net"].get("mean_monthly")),
            t_stat=_r(r["net"].get("t"), 3), t_required=3.0, profit_factor=None, drawdown=_r(r["net"].get("max_drawdown")),
            out_of_sample_expectancy=_r(h["net"]["mean_monthly"]) if h else _r(r["validation"].get("mean_monthly")),
            walk_forward_expectancy=None, cost_sensitivity=_r(r["costs_x2"].get("mean_monthly")), complexity=1,
            stability={"by_year": r.get("by_year")}, status=status[hid],
            failed_checks=tuple(r.get("failed_gates", ())) + (("holdout",) if status[hid] == "REJECTED" and h else ()),
            source=f"research/knowledge/{judged['program']}.json",
            note="portfolio trend: expectancies are monthly net portfolio returns, not R"
                 + (f"; holdout {h['net']['n']} months, net t {h['net'].get('t')}" if h else "")))
    return out


_RETAIL_LONG_ONLY = ("TOM", "DIP", "REGIME", "VOLMAN", "BREAKOUT", "HALLOWEEN")
_RETAIL_STATUS = {"HOLDOUT_ELIGIBLE": "TESTING", "PROMISING": "PROMISING", "REJECTED": "REJECTED",
                  "VALIDATED": "VALIDATED", "PROMISING_REPLICATED": "PROMISING"}


def from_retail(judged: dict, holdouts: list[dict]) -> list[EdgeRecord]:
    """Records of a retail-CFD program (RC-*). Expectancies are MONTHLY NET RETURNS of the account (a
    fraction of equity) after spread, slippage, financing and dividends; gross is before the broker
    (no spread, slippage or markup; the benchmark rate still charged). A later holdout or replication
    of a hypothesis, on another universe, decides its final status."""
    out = []
    for hid, r in sorted(judged["results"].items()):
        status = _RETAIL_STATUS[judged["classification"][hid]]
        h = next((a["results"][hid] for a in holdouts if hid in a.get("results", {})), None)
        hv = next((a["classification"][hid] for a in holdouts if hid in a.get("classification", {})), None)
        failed = tuple(r.get("failed_gates", ()))
        note = "retail CFD: monthly net account returns after spread, slippage, financing and dividends, not R"
        if hv is not None:
            status = _RETAIL_STATUS[hv]
            failed += tuple(f"holdout:{g}" for g in h.get("failed_gates", ()))
            note += f"; replication/holdout {hv}: {h['net']['n']} months, net t {h['net'].get('t')}"
        sub = r.get("sub", {})
        out.append(EdgeRecord(
            edge_id=hid, program=judged["program"],
            direction="BUY" if any(k in hid for k in _RETAIL_LONG_ONLY) else "BOTH",
            instrument=tuple(sorted(r.get("per_instrument") or r.get("per_currency") or {})), timeframe="D1",
            market_regime=None, entry_conditions=f"see research/preregistrations/{judged['program']}.md",
            exit_conditions="rule exit (calendar, signal or monthly rebalance)", sample_size=r["net"].get("n"),
            gross_expectancy=_r(r["before_broker"].get("mean_monthly")), net_expectancy=_r(r["net"].get("mean_monthly")),
            t_stat=_r(r["net"].get("t"), 3), t_required=judged.get("t_required"), profit_factor=r["net"].get("profit_factor"),
            drawdown=_r(r["net"].get("max_drawdown")),
            out_of_sample_expectancy=_r(h["net"]["mean_monthly"]) if h else _r(sub.get("validation", {}).get("mean_monthly")),
            walk_forward_expectancy=None, cost_sensitivity=_r(r["costs_x2"].get("mean_monthly")), complexity=1,
            stability={"by_year": r.get("by_year")}, status=status, failed_checks=failed,
            source=f"research/knowledge/{judged['program']}.json", note=note))
    return out


def build(root: Path | str) -> dict:
    """The registry from what is committed under research/. Deterministic: sorted by edge id."""
    root = Path(root)
    drafts = {}
    for line in (root / "discovery" / "ledger.jsonl").read_text().splitlines():
        d = json.loads(line)
        if d.get("event") == "DRAFT":
            drafts[d["hypothesis"]["id"]] = d["hypothesis"]
    edges: list[EdgeRecord] = []
    holdout_ids: set[str] = set()  # judged again on the holdout: that record is the final one
    programs = {}
    for p in sorted((root / "knowledge").glob("*.json")):
        try:
            art = json.loads(p.read_text())
        except ValueError:
            continue
        if isinstance(art, dict) and art.get("kind") == "cross_sectional":
            continue  # read below, all stages of a program together
        if isinstance(art, dict) and "screen" in art and "program" in art and "judged" not in art:
            # a discovery program whose screen found nothing never produced an edge to record;
            # its size is still recorded, because every cell it tested was charged
            programs[art["program"]] = {"verdict": "FAILED" if not art.get("validated") else "PASS",
                                        "screened": art["screen"].get("tests"),
                                        "discoveries": art["screen"].get("discoveries"), "judged": 0,
                                        "validated": list(art.get("validated") or []),
                                        "threshold_t": art.get("threshold_t")}
            continue
        if not isinstance(art, dict) or "program" not in art or "judged" not in art:
            continue
        recs = from_confirmatory(art, drafts)
        if art.get("holdout_of"):
            superseded = {r.edge_id for r in recs}
            edges = [e for e in edges if e.edge_id not in superseded]
            holdout_ids.update(superseded)
        else:
            recs = [r for r in recs if r.edge_id not in holdout_ids]
        edges += recs
        programs[art["program"]] = {"verdict": art.get("verdict") or ("PASS" if art.get("validated") else "FAIL"),
                                    "judged": len(art["judged"]), "validated": list(art.get("validated") or []),
                                    "threshold_t": art.get("threshold_t")}
    for p in sorted((root / "results").glob("WF-*.json")):
        res = json.loads(p.read_text())
        edges.append(from_walk_forward(res))
        programs[res["trial"]] = {"verdict": res["verdict"], "judged": 1, "threshold_t": res.get("threshold_t")}
    xs: dict[str, list[dict]] = {}
    for p in sorted((root / "knowledge").glob("*.json")):
        try:
            art = json.loads(p.read_text())
        except ValueError:
            continue
        if isinstance(art, dict) and art.get("kind") == "cross_sectional":
            root_id = art["program"].split("-S2")[0].split("-H")[0]
            xs.setdefault(root_id, []).append(art)
    for pid, arts in sorted(xs.items()):
        arts.sort(key=lambda a: (a.get("stage", 3)))
        if arts[0].get("stage") != 1:
            continue
        edges += from_cross_sectional(arts)
        final = arts[-1]
        programs[pid] = {"verdict": final.get("verdict"), "judged": len(arts[0]["results"]),
                         "validated": [k for k, v in final.get("classification", {}).items() if v == "VALIDATED"],
                         "threshold_t": arts[0].get("threshold")}
    flows: dict[str, list[dict]] = {}
    for p in sorted((root / "knowledge").glob("*.json")):
        try:
            art = json.loads(p.read_text())
        except ValueError:
            continue
        if isinstance(art, dict) and art.get("kind") in ("flow", "trend"):
            flows.setdefault(art.get("holdout_of") or art["program"], []).append(art)
    for pid, arts in sorted(flows.items()):
        arts.sort(key=lambda a: bool(a.get("holdout_of")))
        if arts[0].get("holdout_of"):
            continue
        edges += from_flow(arts) if arts[0]["kind"] == "flow" else from_trend(arts)
        programs[pid] = {"verdict": arts[-1].get("verdict"), "judged": len(arts[0]["results"]),
                         "validated": [k for k, v in arts[-1].get("classification", {}).items() if v == "VALIDATED"],
                         "threshold_t": arts[0].get("threshold") or (3.0 if arts[0]["kind"] == "trend" else None)}
    retail: list[dict] = []
    for p in sorted((root / "knowledge").glob("*.json")):
        try:
            art = json.loads(p.read_text())
        except ValueError:
            continue
        if isinstance(art, dict) and art.get("kind") == "retail":
            retail.append(art)
    holds = [a for a in retail if a.get("holdout_of")]
    for art in (a for a in retail if not a.get("holdout_of")):
        edges += from_retail(art, holds)
        mine = [a for a in holds if a["holdout_of"] == art["program"]]
        programs[art["program"]] = {"verdict": art.get("verdict"), "judged": len(art["results"]),
                                    "validated": [], "threshold_t": art.get("t_required"),
                                    **({"holdout": {a["program"]: a.get("classification") for a in mine}} if mine else {})}
    spec_p = root / "specs" / "R3.json"
    if spec_p.exists() and not (root / "knowledge" / "R3.json").exists():
        spec = json.loads(spec_p.read_text())["spec"]
        for h in spec["hypotheses"]:
            edges.append(EdgeRecord(
                edge_id=h["id"], program="R3", direction=h["side"], instrument=(), timeframe="D1", market_regime=None,
                entry_conditions=h["condition"], exit_conditions=spec["exit"].split(" ")[0], sample_size=None,
                gross_expectancy=None, net_expectancy=None, t_stat=None, t_required=None, profit_factor=None,
                drawdown=None, out_of_sample_expectancy=None, walk_forward_expectancy=None, cost_sensitivity=None,
                complexity=len(h["condition"].split("&")), stability=None, status="HYPOTHESIS",
                failed_checks=("not run: policy-rate data unavailable (scripts/round3.py status)",),
                source="research/specs/R3.json"))
        programs["R3"] = {"verdict": "BLOCKED (policy-rate data unavailable)", "judged": 0, "threshold_t": None}
    corr_p = root / "knowledge" / "corrections.json"
    if corr_p.exists():
        corr = json.loads(corr_p.read_text())
        edges = [replace(e, note=corr[e.edge_id]["defect"] + " -> on the registered population: "
                         + json.dumps(corr[e.edge_id]["battery_on_registered_population"]))
                 if e.edge_id in corr else e for e in edges]
    edges.sort(key=lambda e: e.edge_id)
    counts = {s: sum(1 for e in edges if e.status == s) for s in STATUSES}
    return {"version": EDGES_VERSION, "counts": counts, "programs": programs,
            "edges": [asdict(e) for e in edges]}
