"""COT-1: does CFTC positioning carry directional information for FX, beyond what price already shows?

    python scripts/cot1.py draft         # leakage tests on real data, catalog, ledger DRAFTs, event counts
    python scripts/cot1.py spec          # write research/specs/COT-1.json and print its sha256
    python scripts/cot1.py preregister   # registry trial; the document must quote the spec sha256
    python scripts/cot1.py run           # once: development, validation, judged battery, 2016 confirmation
    python scripts/cot1.py holdout       # only if a candidate passed EVERYTHING else: the sealed 2017 test

The design is frozen in research/specs/COT-1.json and research/preregistrations/COT-1.md before any
outcome is computed. Nothing is fitted: the 52-week windows are rolling and causal, the extreme
levels (0.90 / 0.10) are fixed, and the only estimated quantities are the er120 / vol_ratio regime
medians, from the fit period before the judged one (as in every round).

Stages, in order, each computed only if the previous one allows it:
  1. judged period 2008-07-11 -> 2016-01-01 (development 2008-07-11 -> 2014-01-01 and validation
     2014 -> 2016 reported separately): the full battery at the registry's threshold, plus the
     preregistered gates (development > 0, validation > 0, beats its price-only control, positive
     without its 5 best trades);
  2. 2016 confirmation (COT-unseen; outside the project's seal): computed ONLY for a hypothesis that
     is PROMISING or better after stage 1;
  3. the sealed holdout (2017): ONLY for the single best hypothesis that passed everything else,
     per RESEARCH_PROTOCOL.md section 2 -- a separate command that spends the single-use key.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from dataclasses import asdict, dataclass, replace
from datetime import date, datetime, timezone
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from aitrader.data.cot import COT_VERSION, CotStore  # noqa: E402
from aitrader.data.external import ExternalStore  # noqa: E402
from aitrader.data.instruments import UNIVERSE_KEY  # noqa: E402
from aitrader.data.store import DataStore, open_final_test  # noqa: E402
from aitrader.research.discovery.battery import (REGIME_CONTEXT, BatteryRules, decompose, regime_binnings,  # noqa: E402
                                                 run_battery)
from aitrader.research.discovery.board import (adversarial_analyst, market_analyst, opportunity_analyst,  # noqa: E402
                                               reviewer, risk_analyst, synthesize)
from aitrader.research.discovery.catalog import FeatureCatalog, FeatureRecord  # noqa: E402
from aitrader.research.discovery.cot import (COT_STUDY_VERSION, FLOW_DAYS, HI, LO, MIN_HISTORY, NEIGHBOURS,  # noqa: E402
                                             PAIRS, RULES, STEP_DAYS, TREND_BARS, VIX_LEVEL, WINDOW_DAYS, RuleSignal,
                                             SignedStudy, truncation_leaks, weekly)
from aitrader.research.discovery.edges import PROMISING_T, judged_status  # noqa: E402
from aitrader.research.discovery.hypothesis import Hypothesis, Ledger  # noqa: E402
from aitrader.research.discovery.program import _dump, _jsonable, code_sha256  # noqa: E402
from aitrader.research.discovery.stats import cluster_t, deflated_sharpe, week_of  # noqa: E402
from aitrader.research.discovery.study import Segment, epoch  # noqa: E402
from aitrader.research.discovery.universe import load_universe  # noqa: E402
from aitrader.research.labels import BUY, CostModel  # noqa: E402
from aitrader.research.registry import Holdout, Registry, Trial, Use, Verdict  # noqa: E402

R = ROOT / "research"
PID, HPID = "COT-1", "COT-1-H"
DOC = "research/preregistrations/COT-1.md"
SPEC = R / "specs" / "COT-1.json"
SYMBOLS = tuple(sorted(PAIRS))
EXIT = "D3"
COSTS = CostModel(swap_atr_per_night=0.01)
COSTS_X2 = CostModel(slippage_pips=0.4, commission_pips_rt=1.4, swap_atr_per_night=0.02, spread_multiple=2.0)
PURGE = 6  # D3 holds 5 bars, plus the one-bar delay stress
FIT = Segment("fit", "fit", date(2007, 4, 2), date(2008, 7, 1))
DEV = Segment("development", "judge", date(2008, 7, 11), date(2014, 1, 1))
VAL = Segment("validation", "judge", date(2014, 1, 1), date(2016, 1, 1))
JUDGE = Segment("judged", "judge", date(2008, 7, 11), date(2016, 1, 1))
CONF = Segment("confirmation_2016", "judge", date(2016, 1, 1), date(2017, 1, 1))
HOLD = Segment("holdout", "judge", date(2016, 1, 1), date(2018, 1, 1))
H17 = Segment("holdout_2017", "judge", date(2017, 1, 1), date(2018, 1, 1))
USES = ((date(2007, 3, 30), date(2008, 7, 1), "fit"), (date(2008, 7, 1), date(2016, 1, 1), "judge"),
        (date(2016, 1, 1), date(2017, 1, 1), "judge"))
HOLDOUT_T = 1.645  # one-sided 5% for the single candidate the protocol allows
TOP_REMOVED = 5
WF_YEARS = tuple(range(2010, 2016))
WF_MIN_TRADES = 30
EXTRA_CODE = ("aitrader/data/cot.py", "aitrader/data/external.py", "scripts/cot1.py")


@dataclass(frozen=True)
class H:
    hid: str
    rule: str
    kind: str
    control: str
    family: str
    features: tuple[str, ...]
    statement: str
    mechanism: str
    sources: str


BNM = ("Brunnermeier, Nagel & Pedersen, Carry trades and currency crashes, NBER Macroeconomics Annual 23 (2008): "
       "speculators' net futures positions in carry currencies relate to future crash risk")
KW = ("Klitgaard & Weir, Exchange rate changes and net positions of speculators in the futures market, FRBNY "
      "Economic Policy Review 10 (2004): weekly position CHANGES move with same-week exchange rates; little evidence "
      "that they predict later moves")
TY = ("Tornell & Yuan, Speculation and hedging in the currency futures markets: are they informative to the spot "
      "exchange rates?, Journal of Futures Markets 32 (2012): examines whether turning points of net positions "
      "are informative")
HYPS = (
    H("COT1-P-REV", "p_rev", "opportunity", "a_rev", "primary", ("cot_spec_pct",),
      "When Leveraged Money's net position (as a share of open interest) is at a 52-week extreme (percentile >= 0.90 "
      "or <= 0.10), trading the currency AGAINST it for one week (D3) has positive net expectancy.",
      "reversal: a crowded speculative position has few marginal buyers (sellers) left and unwinds",
      f"{BNM}; {TY}"),
    H("COT1-P-CONT", "p_cont", "opportunity", "a_cont", "primary", ("cot_spec_pct",),
      "When Leveraged Money's net position is at a 52-week extreme, trading the currency WITH it for one week has "
      "positive net expectancy.",
      "continuation: speculators trade on information or trends that persist beyond the report", f"{KW}; {TY}"),
    H("COT1-C-REV", "c_rev", "opportunity", "a_rev", "price+cot", ("cot_spec_pct", "cot_px_pct"),
      "When positioning AND the currency's price are both at a same-side 52-week extreme, trading against them for "
      "one week has positive net expectancy -- and more than the price extreme alone.",
      "reversal: a stretched price that is also crowded has the least support left", f"{BNM}"),
    H("COT1-C-CONT", "c_cont", "opportunity", "a_cont", "price+cot", ("cot_spec_pct", "cot_px_pct"),
      "When positioning and price are both at a same-side 52-week extreme, trading with them for one week has "
      "positive net expectancy -- and more than the price extreme alone.",
      "continuation: positioning confirms that the price extreme is a trend, not noise", f"{KW}"),
    H("COT1-I-REV", "i_rev", "opportunity", "a_rev", "cot-beyond-price", ("cot_spec_pct", "cot_px_pct"),
      "When positioning is at a 52-week extreme but price is NOT at the same-side extreme, trading against the "
      "positioning for one week has positive net expectancy.",
      "reversal: positioning information that price has not shown (the pure positioning effect)", f"{BNM}"),
    H("COT1-I-CONT", "i_cont", "opportunity", "a_cont", "cot-beyond-price", ("cot_spec_pct", "cot_px_pct"),
      "When positioning is at a 52-week extreme but price is not, trading with the positioning for one week has "
      "positive net expectancy.",
      "continuation: speculators position ahead of a move that price has not yet made", f"{TY}"),
    H("COT1-F-CONT", "f_cont", "opportunity", "af_cont", "flow", ("cot_spec_flow_pct",),
      "When the 4-week change in Leveraged Money's net position is at a 52-week extreme, trading with the flow for "
      "one week has positive net expectancy.",
      "continuation: position building reflects information that is still being priced", f"{KW}"),
    H("COT1-F-REV", "f_rev", "opportunity", "af_rev", "flow", ("cot_spec_flow_pct",),
      "When the 4-week positioning change is at a 52-week extreme, trading against the flow for one week has "
      "positive net expectancy.",
      "reversal: a burst of position building overshoots and is given back", f"{KW}"),
    H("COT1-U-REV", "u_rev", "opportunity", "a_rev", "unwind", ("cot_spec_pct", "cot_spec_step"),
      "When positioning is at a 52-week extreme AND last week's change points back toward neutral, trading "
      "against the positioning for one week has positive net expectancy.",
      "reversal: the unwind of a crowded position has started and is self-reinforcing", f"{BNM}; {TY}"),
    H("COT1-V-REV", "v_rev", "opportunity", "av_rev", "volatility", ("cot_spec_pct", "cot_vix"),
      "When positioning is at a 52-week extreme while VIX >= 20, trading against the positioning for one week has "
      "positive net expectancy.",
      "reversal: in stress, funding constraints force crowded positions to unwind", f"{BNM}"),
    H("COT1-X-VETO", "x_veto", "veto", "a_trend", "filter", ("cot_spec_pct", "cot_px_trend"),
      "Taking the 13-week trend trade where positioning is ALREADY at an extreme in the trend's direction LOSES "
      "(negative net expectancy): positioning works as a veto on a price strategy.",
      "reversal: a crowded trend is the one most likely to stall; filtering it improves the price strategy",
      f"{BNM}"),
)
CONTROLS = ("a_rev", "a_cont", "af_cont", "af_rev", "av_rev", "a_trend", "a_trend_uncrowded")
FEATURE_DEFS = {
    "cot_spec_pct": ("spec_pct", "positioning", "percentile of Leveraged Money net / open interest among the reports of "
                     "the previous 52 weeks (ties half; >= 39 reports)", ("cftc:tff",)),
    "cot_spec_z": ("spec_z", "positioning", "z-score of Leveraged Money net / open interest against the previous 52 "
                   "weeks (robustness variant only)", ("cftc:tff",)),
    "cot_spec_flow_pct": ("spec_flow_pct", "positioning", "percentile of the 4-week (25..31 day) change of Leveraged "
                          "Money net / open interest among the previous 52 weeks", ("cftc:tff",)),
    "cot_spec_step": ("spec_step", "positioning", "1-week (4..10 day) change of Leveraged Money net / open interest",
                      ("cftc:tff",)),
    "cot_px_pct": ("px_pct", "price", "percentile of the currency's log value in USD at the decision bar among its "
                   "values at the previous 52 weeks' decision bars", ("own D1 bars",)),
    "cot_px_flow_pct": ("px_flow_pct", "price", "percentile of the currency's 4-week log change among the previous 52 "
                        "weeks' (weekly decision-bar samples)", ("own D1 bars",)),
    "cot_px_trend": ("trend", "price", "log change of the currency's value over the 65 D1 bars before the decision "
                     "bar (13 weeks)", ("own D1 bars",)),
    "cot_vix": ("vix", "risk", "Cboe VIX close public at the decision bar (16:45 New York)", ("external:vix",)),
}


def code_hash() -> str:
    h = hashlib.sha256(code_sha256().encode())
    for p in EXTRA_CODE:
        h.update(p.encode() + b"\0" + (ROOT / p).read_bytes() + b"\0")
    return h.hexdigest()


def feature_records() -> dict[str, FeatureRecord]:
    return {name: FeatureRecord(
        name, f"per COT report, placed on its decision D1 bar: {text}", dim, "continuous", "D1", req,
        f"aitrader/research/discovery/cot.py ({COT_STUDY_VERSION}); aitrader/data/cot.py ({COT_VERSION})",
        COT_STUDY_VERSION, "a report is used from 17:00 New York on the first weekday >= as-of + 6 days, on the first "
        "D1 bar closing then; 2013 shutdown reports dropped; windows use earlier reports only; NaN when history is "
        "short, never a default", "does speculative positioning carry directional information beyond price?", PID)
        for name, (col, dim, text, req) in FEATURE_DEFS.items()}


def spec(reg: Registry) -> dict:
    thr = reg.threshold_for_next(UNIVERSE_KEY, USES[1][0], USES[1][1], new_tests=len(HYPS))
    cot_files = json.loads((ROOT / "data" / "cot" / "manifest.json").read_text())["files"]
    return {
        "id": PID, "version": COT_STUDY_VERSION,
        "question": "Does CFTC positioning (Leveraged Money, TFF futures-only) predict the direction of the seven "
                    "direct USD pairs over the following week, after costs, out of sample -- and does it add "
                    "anything beyond a price-only rule with the same timing, exit and costs?",
        "instruments": list(SYMBOLS), "orientation": {s: {"currency": c, "sign": o} for s, (c, o) in PAIRS.items()},
        "data": {"cot": {k: v["zip_sha256"] for k, v in cot_files.items()}, "cot_loader": COT_VERSION,
                 "bars": "D1 bid/ask, data/manifest.json", "vix": "data/external/manifest.json"},
        "positioning": "Leveraged Money long minus short (spreads excluded) / open interest; the currency future's "
                       "own orientation (+ = bullish the currency)",
        "publication": "17:00 New York on the first weekday >= as-of + 6 days; 2013-10-01..2013-12-24 dropped",
        "decision_bar": "the first D1 bar closing at or after the release; none if the next report is already public",
        "lookback": {"window_days": WINDOW_DAYS, "min_reports": MIN_HISTORY, "normalisation": "percentile rank "
                     "(ties half) among the previous 52 weeks' reports; z-score only as a robustness variant"},
        "levels": {"hi": HI, "lo": LO, "neighbours": [list(x) for x in NEIGHBOURS], "vix": VIX_LEVEL},
        "lags_days": {"flow": list(FLOW_DAYS), "step": list(STEP_DAYS)}, "trend_bars": TREND_BARS,
        "rules": {k: r.text for k, r in RULES.items()},
        "hypotheses": [asdict(h) for h in HYPS], "controls": list(CONTROLS),
        "entry": "market order at the open of the bar after the decision bar (= the decision bar's close)",
        "exit": {"key": EXIT, "rule": "time exit after 5 D1 bars (the next decision bar's close), protective stop "
                                      "2.0 x ATR24(D1); 1R = the stop distance; no target"},
        "costs": COSTS.describe() | {"swap": "0.01 x ATR24(D1) per New York close crossed"},
        "segments": {s.name: s.to_json() for s in (FIT, DEV, VAL, JUDGE, CONF, HOLD, H17)},
        "registry_uses": [[a.isoformat(), b.isoformat(), r] for a, b, r in USES],
        "prior_tests": reg.tests_on(UNIVERSE_KEY, USES[1][0], USES[1][1]),
        "threshold_t": round(thr, 4),
        "battery": BatteryRules(t_threshold=thr).describe(),
        "gates": {"development": "mean R (claim-signed) > 0 on 2008-07-11 -> 2014-01-01",
                  "validation": "mean R > 0 on 2014-01-01 -> 2016-01-01",
                  "incremental": "judged mean R minus the declared price-only control's judged mean R > 0; for the "
                                 "veto: the uncrowded trend control's mean minus the trend control's mean > 0",
                  "top5_removed": f"judged mean R > 0 without the {TOP_REMOVED} best trades",
                  "confirmation_2016": "computed only for PROMISING-or-better: 2016 mean R > 0 and > 0 under the "
                                       "cost stress"},
        "status": {"PROMISING": f"judged mean > 0, clustered t >= {PROMISING_T}, cost stress and beats-random pass, "
                                "every gate passes (edges.judged_status), and the 2016 confirmation passes",
                   "VALIDATED": "every battery check at the registry threshold, no blocking board objection, every "
                                "gate, the 2016 confirmation, then the sealed holdout",
                   "REJECTED": "anything else"},
        "holdout": {"policy": "RESEARCH_PROTOCOL.md section 2: one preregistered final test of ONE candidate that "
                              "passed everything else; the best such by judged t; never for a PROMISING one",
                    "pass": f"2016-2017 pooled mean > 0 with clustered t >= {HOLDOUT_T}, 2017 alone mean > 0, and "
                            "2016-2017 mean > 0 under the cost stress"},
        "robustness_reported": ["neighbouring levels 0.85/0.15 and 0.95/0.05 (battery perturbation, gating)",
                                "z-score definition at the same normal quantiles", "bullish vs bearish extremes",
                                "costs x2 (spread x2, slippage x4, commission and swap x2)",
                                "without the best trade", f"without the {TOP_REMOVED} best trades (gating)",
                                "by instrument, year, regime; entry one bar late (battery)"],
        "walk_forward": f"fixed rules: each calendar year is an out-of-sample fold; plus a descriptive walk-forward "
                        f"of SELECTION: in each year {WF_YEARS[0]}..{WF_YEARS[-1]} trade the opportunity hypothesis "
                        f"with the best judged mean over all earlier years (>= {WF_MIN_TRADES} trades); no verdict "
                        "depends on it",
        "abc": {"A (price only)": ["a_rev", "a_cont"], "B (COT only)": ["p_rev", "p_cont"],
                "C (price + COT)": ["c_rev", "c_cont"]},
        "not_tested_here": ["other lookbacks (52 weeks is frozen)", "derived cross pairs", "asset-manager and dealer "
                            "positioning as signals (reported descriptively)", "relative currency strength",
                            "position sizing (the Risk Engine's alone)"],
    }


def spec_sha(s: dict) -> str:
    return hashlib.sha256(json.dumps(s, sort_keys=True).encode()).hexdigest()


def load(holdout, key=None):
    class Keyed:
        def __init__(self, store):
            self.store = store

        def load(self, symbol, timeframe):
            return self.store.load(symbol, timeframe, key=key)

    store = DataStore(ROOT / "data" / "processed", holdout)
    data, hashes = load_universe(Keyed(store) if key else store, symbols=SYMBOLS, timeframe="D1")
    cot = CotStore(ROOT / "data" / "cot", holdout).load(key=key)
    vix = ExternalStore(ROOT / "data" / "external", holdout).load("vix", holdout_key=key)
    ws = {s: weekly(data[s].series, cot[PAIRS[s][0]], vix) for s in SYMBOLS}
    return data, hashes, ws


def studies(data, segments, costs=COSTS):
    fit = SignedStudy(data, FIT, {}, costs, purge_bars=PURGE)
    ctx = regime_binnings({f: {s: data[s].columns[f][fit.rows[s]] for s in SYMBOLS} for f in ("er120", "vol_ratio")})
    return {seg.name: SignedStudy(data, seg, {}, costs, purge_bars=PURGE, context=ctx) for seg in segments}


def _r(x, nd=5):
    return None if x is None or not np.isfinite(x) else round(float(x), nd)


def metrics(tr, sign: float = 1.0) -> dict:
    """Everything the report asks for, in R; `claim_*` is signed by the hypothesis (a veto claims losses)."""
    if tr.n == 0:
        return {"n": 0}
    d = decompose(tr)
    st = cluster_t(sign * tr.r, week_of(tr.t))
    years = max((tr.t.max() - tr.t.min()) / (365.25 * 86400), 1 / 52)
    out = {k: d.get(k) for k in ("n", "win_rate", "avg_win_R", "avg_loss_R", "mean_R", "t", "total_R", "profit_factor",
                                  "max_drawdown_R", "longest_losing_streak", "by_instrument", "by_year", "by_regime")}
    out.update(claim_mean_R=_r(st["mean"]), claim_t=_r(st["t"], 3), gross_mean_R=d["cost_R"]["gross_mean_R"],
               cost_mean_R=d["cost_R"]["mean"], sharpe_per_trade=_r(deflated_sharpe(tr.r, 1)["sharpe"], 4),
               trades_per_year=_r(tr.n / years, 1))
    if "side" in tr.context:
        orient = np.array([PAIRS[s][1] for s in tr.symbol])
        ccy = tr.context["side"] * orient
        out["by_currency_direction"] = {k: {"n": int(m.sum()), "mean_R": _r(tr.r[m].mean()) if m.any() else None}
                                        for k, m in (("long_currency", ccy > 0), ("short_currency", ccy < 0))}
    return out


def mean_of(tr, sign: float = 1.0):
    return float((sign * tr.r).mean()) if tr.n else None


def without_top(tr, k: int, sign: float = 1.0):
    if tr.n <= k:
        return None
    r = np.sort(sign * tr.r)[::-1]
    return float(r[k:].mean())


def _ledger():
    return Ledger(R / "discovery" / "ledger.jsonl")


def hypotheses_for_ledger(recs) -> list[Hypothesis]:
    return [Hypothesis(
        id=h.hid, statement=h.statement, rationale=f"{h.sources}. Control: {h.control} (price only, same decision "
        "bars, timing, exit and costs).", mechanism=h.mechanism, features=tuple(recs[f].id for f in h.features),
        condition=f"rule:{h.rule}", side="SIGNED", instruments=SYMBOLS, timeframe="D1", exit=EXIT,
        expected_effect="claim-signed mean net R per trade > 0 on 2008-07-11 .. 2016-01-01, positive in development "
                        "and validation, above its price-only control", kind=h.kind,
        falsification=tuple(f"{k}: {v}" for k, v in BatteryRules(t_threshold=1.0).describe().items()
                            if k != "significance"), budget=1, origin="human", program=PID,
        evidence={"family": h.family}) for h in HYPS]


def cmd_draft(now) -> None:
    holdout = Holdout.load(R / "holdout.json")
    data, _, ws = load(holdout)
    cot = CotStore(ROOT / "data" / "cot", holdout).load()
    vix = ExternalStore(ROOT / "data" / "external", holdout).load("vix")
    cat = FeatureCatalog(R / "discovery" / "features.jsonl")
    if cat.budget(PID)[1] == 0:
        cat.open_program(PID, len(FEATURE_DEFS), now)
    recs = feature_records()
    bad_all: dict[str, list] = {}
    n_rows = 0
    for s in SYMBOLS:
        w = ws[s]
        rows = w.row[w.row >= 0]
        rows = rows[(rows > 300)][::8]
        bad = truncation_leaks(data[s].series, cot[PAIRS[s][0]], vix, rows)
        n_rows += len(rows)
        for k, v in bad.items():
            bad_all.setdefault(k, []).extend(f"{s}:{i}" for i in v)
    leaky = {k: v for k, v in bad_all.items() if v}
    for name, rec in recs.items():
        rec = cat.register(rec, now)
        if cat.leakage_status(rec.id) != "PASSED":
            col = FEATURE_DEFS[name][0]
            print(name, cat.record_leakage(rec.id, [int(x.split(":")[1]) for x in bad_all.get(col, [])], n_rows,
                                           list(SYMBOLS), now), f"{n_rows} rows")
    if leaky:
        raise SystemExit(f"LEAKAGE: {sorted(leaky)} -- nothing is drafted")
    print(f"truncation test: {n_rows} decision rows, {len(bad_all)} columns (features and every rule), 0 leaks")
    led = _ledger()
    for h in hypotheses_for_ledger(recs):
        try:
            led.get(h.id)
        except Exception:
            led.draft(h, now)
    # how often each rule fires, per segment: signal counts only, no outcome is read
    sts = studies(data, (DEV, VAL, JUDGE))
    counts = {}
    for name, rule in RULES.items():
        sig = RuleSignal(rule, ws)
        counts[name] = {seg: int(sum((m != 0).sum() for m in sig.masks(st).values())) for seg, st in sts.items()}
    out = R / "results" / "COT-1-event-counts.json"
    out.write_text(json.dumps({"note": "signal counts per segment before any outcome was computed; trades can be fewer "
                                       "(one position per instrument)", "counts": counts}, indent=1, sort_keys=True)
                   + "\n")
    for k, v in counts.items():
        print(f"{k:18} {v}")


def cmd_spec() -> None:
    reg = Registry.load(R / "registry.jsonl", Holdout.load(R / "holdout.json"))
    if any(t.id == PID for t in reg.trials):
        raise SystemExit(f"{PID} is registered; its spec is frozen")
    s = spec(reg)
    sha = spec_sha(s)
    SPEC.write_text(json.dumps({"spec": s, "sha256": sha, "code_sha256": code_hash()}, indent=1, sort_keys=True) + "\n")
    print(sha, "threshold", s["threshold_t"])


def cmd_preregister(now) -> None:
    reg = Registry.load(R / "registry.jsonl", Holdout.load(R / "holdout.json"))
    frozen = json.loads(SPEC.read_text())
    s = spec(reg)
    sha = spec_sha(s)
    if sha != frozen["sha256"] or code_hash() != frozen["code_sha256"]:
        raise SystemExit("the spec or the code changed since `spec`; regenerate and re-read before registering")
    doc = (ROOT / DOC).read_text()
    if sha not in doc:
        raise SystemExit(f"{DOC} must quote the spec sha256 {sha}")
    led = _ledger()
    for h in HYPS:
        if led.state(h.hid) != "DRAFT":
            raise SystemExit(f"{h.hid} is {led.state(h.hid)}")
    trial = reg.register(Trial(
        id=PID, registered=now, title="CFTC positioning as directional information for FX (COT-1)",
        hypothesis=s["question"], uses=tuple(Use(UNIVERSE_KEY, a, b, r) for a, b, r in USES), tests=len(HYPS),
        configurations=len(HYPS), preregistration=DOC,
        design={"spec_sha256": sha, "code_sha256": frozen["code_sha256"], "spec": s}))
    for h in HYPS:
        led.transition(h.hid, "PREREGISTERED", now, trial=PID, preregistration_sha256=sha)
    print(f"registered {trial.id}: {trial.tests} tests, t >= {s['threshold_t']}")


def judge_one(h: H, sig, sts, rules, thr, sha, control_trades, n_prior, holdout_epoch) -> tuple[dict, object]:
    sign = -1.0 if h.kind == "veto" else 1.0
    res = run_battery(sts["judged"], sig, BUY, EXIT, rules, kind=h.kind, trials=len(HYPS), key=h.hid)
    main = res["trades"]
    seg = {n: sts[n].trades(sig.masks(sts[n]), EXIT, BUY, context=REGIME_CONTEXT) for n in ("development", "validation")}
    m_main = mean_of(main, sign)
    if h.kind == "veto":
        inc = (mean_of(control_trades["a_trend_uncrowded"]["judged"]) or 0) - (mean_of(control_trades["a_trend"]["judged"])
                                                                               or 0)
        inc_text = "uncrowded trend minus trend"
    else:
        c = mean_of(control_trades[h.control]["judged"])
        inc = None if m_main is None or c is None else m_main - c
        inc_text = f"{h.hid} minus {h.control}"
    top = without_top(main, TOP_REMOVED, sign)
    gates = {
        "development": (mean_of(seg["development"], sign) or 0) > 0,
        "validation": (mean_of(seg["validation"], sign) or 0) > 0,
        "incremental": inc is not None and inc > 0,
        "top5_removed": top is not None and top > 0,
    }
    data = {"development": {"mean_R": _r(mean_of(seg["development"], sign)), "n": seg["development"].n},
            "validation": {"mean_R": _r(mean_of(seg["validation"], sign)), "n": seg["validation"].n},
            "incremental": {"value_R": _r(inc), "definition": inc_text},
            "top5_removed": {"mean_R": _r(top)}}
    for k, ok in gates.items():
        res["checks"][k] = {"pass": bool(ok), "gate": True, **data[k]}
    res["failed"] = [k for k, v in res["checks"].items() if not v["pass"]]
    res["verdict"] = "VALIDATED" if not res["failed"] else "REJECTED"
    opinions = [market_analyst(res),
                opportunity_analyst(res, {"mechanism": h.mechanism}, {k: data[k] for k in ("development", "validation")}),
                risk_analyst(res),
                adversarial_analyst(res, configurations=len(HYPS), prior_tests=n_prior),
                reviewer(res, segment_epochs=(epoch(JUDGE.start), epoch(JUDGE.end)), holdout_epoch=holdout_epoch,
                         declared_exit=EXIT, frozen_threshold=thr, preregistration_sha256=sha, expected_sha256=sha,
                         sign=sign)]
    syn = synthesize(res["verdict"], opinions)
    # descriptive robustness (the gating ones are already in the battery and the gates)
    zsig = RuleSignal(sig.rule, sig.weekly, z=True)
    ztr = sts["judged"].trades(zsig.masks(sts["judged"]), EXIT, BUY)
    x2 = sts["judged_costs_x2"].trades(sig.masks(sts["judged_costs_x2"]), EXIT, BUY)
    rob = {"z_definition": {"n": ztr.n, "claim_mean_R": _r(mean_of(ztr, sign))},
           "costs_x2": {"n": x2.n, "claim_mean_R": _r(mean_of(x2, sign))},
           "without_best_trade": _r(without_top(main, 1, sign)),
           f"without_{TOP_REMOVED}_best_trades": _r(top),
           "neighbouring_levels": res["checks"]["perturbation"].get("mean_R"),
           "delay_one_bar": res["checks"]["delay_stress"].get("mean_R"),
           "cost_stress": res["checks"]["costs_stress"].get("mean_R")}
    entry = {"id": h.hid, "kind": h.kind, "origin": "human", "family": h.family, "statement": h.statement,
             "condition": f"rule:{h.rule}", "side": "SIGNED", "exit": EXIT, "control": h.control,
             "segments": {"development": metrics(seg["development"], sign), "validation": metrics(seg["validation"], sign),
                          "judged": metrics(main, sign)},
             "robustness": rob, "board": syn}
    return entry, res


def walk_forward_selection(trades_by_h: dict) -> dict:
    """Descriptive: each year, trade the opportunity hypothesis that had the best mean over all earlier years."""
    out, pooled_r, pooled_t = {}, [], []
    for y in WF_YEARS:
        best, best_m = None, -np.inf
        for hid, tr in trades_by_h.items():
            past = tr.years() < y
            if past.sum() >= WF_MIN_TRADES and tr.r[past].mean() > best_m:
                best, best_m = hid, float(tr.r[past].mean())
        if best is None:
            out[str(y)] = {"chosen": None}
            continue
        tr = trades_by_h[best]
        now_ = tr.years() == y
        pooled_r.append(tr.r[now_])
        pooled_t.append(tr.t[now_])
        out[str(y)] = {"chosen": best, "past_mean_R": _r(best_m), "n": int(now_.sum()),
                       "mean_R": _r(tr.r[now_].mean()) if now_.any() else None}
    r = np.concatenate(pooled_r) if pooled_r else np.zeros(0)
    t = np.concatenate(pooled_t) if pooled_t else np.zeros(0)
    st = cluster_t(r, week_of(t))
    return {"by_year": out, "pooled": {"n": int(len(r)), "mean_R": _r(st["mean"]), "t": _r(st["t"], 3)}}


def cmd_run(now) -> None:
    holdout = Holdout.load(R / "holdout.json")
    reg = Registry.load(R / "registry.jsonl", holdout)
    trial = reg.get(PID)
    if reg.status_of(PID) != "PENDING":
        raise SystemExit(f"{PID} already has a verdict; it runs once")
    frozen = json.loads(SPEC.read_text())
    if trial.design["spec_sha256"] != frozen["sha256"] or trial.design["code_sha256"] != code_hash():
        raise SystemExit("the spec or the code differs from what was preregistered")
    sha, thr = frozen["sha256"], float(trial.design["spec"]["threshold_t"])
    data, hashes, ws = load(holdout)
    sts = studies(data, (DEV, VAL, JUDGE))
    sts["judged_costs_x2"] = studies(data, (JUDGE,), COSTS_X2)["judged"]
    rules = BatteryRules(t_threshold=thr)
    led = _ledger()
    n_prior = reg.tests_on(UNIVERSE_KEY, USES[1][0], USES[1][1]) - len(HYPS)

    control_trades, controls = {}, {}
    for c in CONTROLS:
        sig = RuleSignal(RULES[c], ws)
        control_trades[c] = {n: st.trades(sig.masks(st), EXIT, BUY, context=REGIME_CONTEXT)
                             for n, st in sts.items() if n in ("development", "validation", "judged")}
        controls[c] = {"rule": RULES[c].text, "segments": {n: metrics(tr) for n, tr in control_trades[c].items()}}

    judged, trades_by_h, status = [], {}, {}
    for h in HYPS:
        if led.state(h.hid) == "PREREGISTERED":
            led.transition(h.hid, "RUNNING", now, trial=PID, stage="judged", exit=EXIT)
        entry, res = judge_one(h, RuleSignal(RULES[h.rule], ws), sts, rules, thr, sha, control_trades, n_prior,
                               epoch(holdout.start))
        if h.kind == "opportunity":
            trades_by_h[h.hid] = res["trades"]
        res.pop("trades")
        entry["battery"] = res
        if entry["board"]["verdict"] == "VALIDATED":
            status[h.hid] = "VALIDATED_PENDING"
        else:
            status[h.hid] = judged_status(False, res["checks"])
        judged.append(entry)
        print(f"{h.hid:12} n={res['checks']['min_trades']['n']:4} mean={res['checks']['significance']['mean_R']} "
              f"t={res['checks']['significance']['t']} -> {status[h.hid]}  failed={res['failed']}")

    # stage 2: the 2016 confirmation, computed only for what earned it
    eligible = [e for e in judged if status[e["id"]] in ("PROMISING", "VALIDATED_PENDING")]
    if eligible:
        conf = studies(data, (CONF,))["confirmation_2016"]
        for e in eligible:
            h = next(x for x in HYPS if x.hid == e["id"])
            sign = -1.0 if h.kind == "veto" else 1.0
            sig = RuleSignal(RULES[h.rule], ws)
            tr = conf.trades(sig.masks(conf), EXIT, BUY, context=REGIME_CONTEXT)
            stress = conf.trades(sig.masks(conf), EXIT, BUY, stress="costs")
            m, ms = mean_of(tr, sign), mean_of(stress, sign)
            ok = m is not None and m > 0 and ms is not None and ms > 0
            e["battery"]["checks"]["confirmation_2016"] = {"pass": ok, "gate": True, "mean_R": _r(m), "n": tr.n,
                                                           "cost_stress_mean_R": _r(ms)}
            e["segments"]["confirmation_2016"] = metrics(tr, sign)
            if not ok:
                e["battery"]["failed"].append("confirmation_2016")
                status[e["id"]] = "REJECTED"
            elif status[e["id"]] == "VALIDATED_PENDING":
                status[e["id"]] = "HOLDOUT_ELIGIBLE"
    for e in judged:
        e["status"] = status[e["id"]]
        hid = e["id"]
        if led.state(hid) == "RUNNING":
            led.transition(hid, "COMPLETED", now, summary={"n": e["battery"]["checks"]["min_trades"]["n"],
                                                           "t": e["battery"]["checks"]["significance"]["t"],
                                                           "failed": e["battery"]["failed"]})
        if led.state(hid) == "COMPLETED" and status[hid] != "HOLDOUT_ELIGIBLE":
            led.transition(hid, "REJECTED", now, reason="; ".join(e["battery"]["failed"] or ["board objection"])
                           + (" (PROMISING: a near miss, not a trading rule)" if status[hid] == "PROMISING" else ""))

    abc = {}
    for mapping in ("rev", "cont"):
        a, b, c = f"a_{mapping}", f"p_{mapping}", f"c_{mapping}"
        bt = next(e for e in judged if e["condition"] == f"rule:{b}")
        ct = next(e for e in judged if e["condition"] == f"rule:{c}")
        abc[mapping] = {}
        for seg_name in ("development", "validation", "judged"):
            ma = controls[a]["segments"][seg_name].get("mean_R")
            mb = bt["segments"][seg_name].get("mean_R")
            mc = ct["segments"][seg_name].get("mean_R")
            abc[mapping][seg_name] = {
                "A_price_only": {"n": controls[a]["segments"][seg_name].get("n"), "mean_R": ma},
                "B_cot_only": {"n": bt["segments"][seg_name].get("n"), "mean_R": mb},
                "C_price_and_cot": {"n": ct["segments"][seg_name].get("n"), "mean_R": mc},
                "B_minus_A": _r(mb - ma) if None not in (ma, mb) else None,
                "C_minus_A": _r(mc - ma) if None not in (ma, mc) else None}
    wf = walk_forward_selection(trades_by_h)
    eligible_final = sorted((e for e in judged if e["status"] == "HOLDOUT_ELIGIBLE"),
                            key=lambda e: -(e["battery"]["checks"]["significance"]["t"] or 0))
    verdict = "PASSED" if eligible_final else "FAILED"
    data_sha = dict(sorted(hashes.items())) | {"cot_zip_" + k: v for k, v in trial.design["spec"]["data"]["cot"].items()}
    body = {"program": PID, "version": COT_STUDY_VERSION, "design_sha256": sha, "code_sha256": code_hash(),
            "data_sha256": data_sha, "threshold_t": round(thr, 4), "prior_tests": n_prior,
            "judged": judged, "controls": controls, "abc": abc, "walk_forward_selection": wf,
            "holdout_eligible": [e["id"] for e in eligible_final], "validated": [], "verdict": verdict,
            "status": {e["id"]: e["status"] for e in judged},
            "knowledge": [{"id": e["id"], "status": e["status"]} for e in judged if e["status"] != "REJECTED"]}
    body = json.loads(json.dumps(body, sort_keys=True, default=_jsonable))
    body["sha256"] = hashlib.sha256(json.dumps(body, sort_keys=True).encode()).hexdigest()
    (R / "knowledge" / f"{PID}.json").write_text(_dump(body))
    reg.record_verdict(Verdict(PID, now, verdict, {"artifact": f"research/knowledge/{PID}.json",
                                                   "artifact_sha256": body["sha256"], "status": body["status"],
                                                   "holdout_eligible": body["holdout_eligible"]}))
    print(json.dumps({"verdict": verdict, "status": body["status"], "abc": abc, "walk_forward": wf["pooled"]},
                     indent=1))


def cmd_holdout(now) -> None:
    holdout = Holdout.load(R / "holdout.json")
    reg = Registry.load(R / "registry.jsonl", holdout)
    art = json.loads((R / "knowledge" / f"{PID}.json").read_text())
    if not art["holdout_eligible"]:
        raise SystemExit("no hypothesis passed everything else: the sealed holdout stays sealed")
    hid = art["holdout_eligible"][0]  # one candidate: the best by judged t
    entry = next(e for e in art["judged"] if e["id"] == hid)
    h = next(x for x in HYPS if x.hid == hid)
    reg.register(Trial(id=HPID, registered=now, title=f"Sealed-holdout test of {hid}", hypothesis=h.statement,
                       uses=(Use(UNIVERSE_KEY, H17.start, H17.end, "judge"),), tests=1, configurations=1,
                       preregistration=DOC, design={"spec_sha256": art["design_sha256"], "candidate": hid}))
    key = open_final_test(reg, HPID)
    data, hashes, ws = load(holdout, key)
    sts = studies(data, (HOLD, H17))
    sign = -1.0 if h.kind == "veto" else 1.0
    sig = RuleSignal(RULES[h.rule], ws)
    pooled = sts["holdout"].trades(sig.masks(sts["holdout"]), EXIT, BUY, context=REGIME_CONTEXT)
    y17 = sts["holdout_2017"].trades(sig.masks(sts["holdout_2017"]), EXIT, BUY)
    stress = sts["holdout"].trades(sig.masks(sts["holdout"]), EXIT, BUY, stress="costs")
    st = cluster_t(sign * pooled.r, week_of(pooled.t))
    ok = (st["t"] is not None and st["mean"] > 0 and st["t"] >= HOLDOUT_T and (mean_of(y17, sign) or 0) > 0
          and (mean_of(stress, sign) or 0) > 0)
    checks = dict(entry["battery"]["checks"])
    checks["holdout"] = {"pass": ok, "gate": True, "mean_R": _r(st["mean"]), "t": _r(st["t"], 3), "n": pooled.n,
                         "mean_R_2017": _r(mean_of(y17, sign)), "cost_stress_mean_R": _r(mean_of(stress, sign))}
    led = _ledger()
    if ok:
        led.transition(hid, "VALIDATED", now, checks={k: v["pass"] for k, v in checks.items()})
    else:
        led.transition(hid, "REJECTED", now, reason="failed the sealed holdout")
    body = {"program": HPID, "holdout_of": PID, "judged": [dict(entry, battery={**entry["battery"], "checks": checks,
                                                                                 "failed": [k for k, v in checks.items()
                                                                                            if not v["pass"]]})],
            "segments": {"holdout_2016_2017": metrics(pooled, sign), "holdout_2017": metrics(y17, sign)},
            "validated": [hid] if ok else [], "verdict": "PASSED" if ok else "FAILED",
            "data_sha256": dict(sorted(hashes.items()))}
    body = json.loads(json.dumps(body, sort_keys=True, default=_jsonable))
    body["sha256"] = hashlib.sha256(json.dumps(body, sort_keys=True).encode()).hexdigest()
    (R / "knowledge" / f"{HPID}.json").write_text(_dump(body))
    reg.record_verdict(Verdict(HPID, now, body["verdict"], {"artifact": f"research/knowledge/{HPID}.json",
                                                            "artifact_sha256": body["sha256"]}))
    print(json.dumps(checks["holdout"], indent=1))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=("draft", "spec", "preregister", "run", "holdout"))
    a = ap.parse_args()
    now = datetime.now(timezone.utc)
    {"draft": lambda: cmd_draft(now), "spec": cmd_spec, "preregister": lambda: cmd_preregister(now),
     "run": lambda: cmd_run(now), "holdout": lambda: cmd_holdout(now)}[a.cmd]()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
