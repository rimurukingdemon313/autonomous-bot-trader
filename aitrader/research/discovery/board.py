"""The research board: five analysts read one result, and the synthesis can only subtract.

    market        how the result behaves across regimes, sessions and time (is it decaying?)
    opportunity   whether the edge is large enough to matter after costs, frequent enough to
                  measure, and consistent with its own conjectured mechanism and exit
    risk          drawdown, losing streaks and tail losses in R (never in money: sizing is the
                  Risk Engine's), including losses beyond the stop that no per-trade limit bounds
    adversarial   every way the result could be luck or concentration: the multiple-testing
                  count, the deflated Sharpe ratio, one instrument or one year carrying it
    reviewer      INDEPENDENT: recomputes n, mean and the clustered t from the raw trades with its
                  own code, and checks that every trade lies inside the judged segment, that no two
                  trades on one instrument overlap, that the exit is the declared one, and that
                  the preregistration and threshold are the ones that were frozen

There is no vote. The preregistered battery decides; any analyst's BLOCKING objection turns a
VALIDATED result into REJECTED, and nothing turns a REJECTED one into VALIDATED. A language
model may add objections (it critiques; it never proposes a verdict), and they too can only
subtract.
"""

from __future__ import annotations

import json
import math
from dataclasses import asdict, dataclass, field

import numpy as np

BOARD_VERSION = "board-1.0.0"
ANALYSTS = ("market", "opportunity", "risk", "adversarial", "reviewer")
TAIL_LOSS_R = -3.0  # a single trade worse than this escaped its stop by a gap
CONCENTRATION = 0.6  # one instrument or one year carrying more than this share of total R ...
# ... while the rest of the trades earn less than a third as much per trade


@dataclass
class Opinion:
    analyst: str
    findings: list[str] = field(default_factory=list)  # what it measured
    concerns: list[str] = field(default_factory=list)  # recorded, never change the verdict
    blocking: list[str] = field(default_factory=list)  # each one turns VALIDATED into REJECTED
    data: dict = field(default_factory=dict)

    @property
    def stance(self) -> str:
        return "OBJECT" if self.blocking else "CONCERN" if self.concerns else "SUPPORT"

    def to_json(self) -> dict:
        return asdict(self) | {"stance": self.stance}


def market_analyst(res: dict) -> Opinion:
    d = res["decomposition"]
    years = {int(k): v for k, v in d.get("by_year", {}).items() if v["n"] >= 20}
    f, concerns = [], []
    if years:
        ys = sorted(years)
        f.append("by year: " + ", ".join(f"{y} {years[y]['mean_R']:+.3f}R (n={years[y]['n']})" for y in ys))
        if len(ys) >= 3:
            slope = float(np.polyfit(ys, [years[y]["mean_R"] for y in ys], 1)[0])
            if slope < 0 and years[ys[-1]]["mean_R"] < 0:
                concerns.append(f"decaying: the yearly mean falls by {slope:+.3f}R/year and the last year is negative")
    cells = res["checks"].get("regimes", {}).get("cells", {})
    if cells:
        worst = min(cells, key=lambda k: cells[k]["mean_R"] or 0)
        f.append(f"regime cells: {len(cells)} populated; weakest {worst} {cells[worst]['mean_R']:+.3f}R")
    sess = d.get("by_session", {})
    if sess:
        neg = [k for k, v in sess.items() if v["n"] >= 20 and (v["t"] or 0) <= -2]
        if neg:
            concerns.append(f"significantly negative in session(s) {neg}")
    return Opinion("market", f, concerns, [], {"years": len(years)})


def opportunity_analyst(res: dict, h: dict, per_segment: dict) -> Opinion:
    d = res["decomposition"]
    f, concerns = [], []
    gross, cost = d.get("cost_R", {}).get("gross_mean_R"), d.get("cost_R", {}).get("mean")
    if gross and cost is not None and gross > 0:
        share = cost / gross
        f.append(f"costs take {share:.0%} of the gross edge ({cost:.3f}R of {gross:.3f}R per trade)")
        if share > 0.5:
            concerns.append("thin: costs take more than half of the gross edge")
    signs = {k: v.get("mean_R") for k, v in per_segment.items()}
    f.append("mean R by segment: " + ", ".join(f"{k} {v:+.3f}" for k, v in signs.items() if v is not None))
    if any(v is not None and v <= 0 for v in signs.values()):
        concerns.append("not positive in every segment it was measured in")
    mech, exit_ = h.get("mechanism", ""), res["exit"]
    if mech.startswith("reversal") and exit_ in ("E5", "E7"):
        concerns.append(f"a reversal mechanism managed by a trailing exit ({exit_}) is internally inconsistent")
    if mech.startswith("continuation") and exit_ == "E3":
        concerns.append("a continuation mechanism with the shortest symmetric exit (E3) is inconsistent")
    return Opinion("opportunity", f, concerns, [], {"segments": signs})


def risk_analyst(res: dict) -> Opinion:
    d, tr = res["decomposition"], res["trades"]
    f = [f"max drawdown {d.get('max_drawdown_R')}R, longest losing streak {d.get('longest_losing_streak')}",
         "all figures in R; the position size is the Risk Engine's alone"]
    blocking, concerns = [], []
    if tr.n:
        worst = float(np.min(tr.r))
        p95 = float(np.percentile(-np.minimum(tr.mae, 0), 95))
        f.append(f"worst trade {worst:+.2f}R; 95th percentile adverse excursion {p95:.2f}R")
        if worst < TAIL_LOSS_R:
            blocking.append(f"a trade lost {worst:.2f}R: gaps carried it past its stop, a loss no per-trade "
                            "risk limit bounds")
    if (d.get("longest_losing_streak") or 0) >= 15:
        concerns.append("a losing streak of 15 or more trades would test any operator's discipline")
    return Opinion("risk", f, concerns, blocking, {})


def adversarial_analyst(res: dict, *, configurations: int, prior_tests: int) -> Opinion:
    d = res["decomposition"]
    f = [f"{configurations} configurations were examined by this program; {prior_tests} earlier tests "
         "touched the judged period"]
    blocking, concerns = [], []
    ds = res.get("deflated_sharpe", {})
    if ds.get("dsr") is not None:
        f.append(f"deflated Sharpe ratio {ds['dsr']:.3f} over {ds['trials']} trials")
        if ds["dsr"] < 0.95:
            concerns.append("the deflated Sharpe ratio does not clear 0.95 once every trial is counted")
    total = d.get("total_R") or 0.0
    for group in ("by_instrument", "by_year"):
        g = d.get(group, {})
        parts = {k: (v["mean_R"] or 0) * v["n"] for k, v in g.items()}
        if total > 0 and len(parts) > 1:
            top = max(parts, key=parts.get)
            share = parts[top] / total
            rest_n = sum(v["n"] for k, v in g.items() if k != top)
            rest_mean = (total - parts[top]) / rest_n if rest_n else 0.0
            # a group that is simply a large part of the sample is not concentration: it is when the
            # rest of the sample earns little per trade that one group is carrying the result
            if share > CONCENTRATION and rest_mean < (g[top]["mean_R"] or 0) / 3:
                blocking.append(f"{top} alone carries {share:.0%} of the total R ({group[3:]}); the rest earns "
                                f"{rest_mean:+.3f}R per trade")
    perm = res["checks"].get("permutation", {})
    f.append(f"permutation p {perm.get('p')}; random-entry Welch t {res['checks'].get('beats_random', {}).get('welch_t')}")
    return Opinion("adversarial", f, concerns, blocking, {})


def reviewer(res: dict, *, segment_epochs: tuple[int, int], holdout_epoch: int, declared_exit: str,
             frozen_threshold: float, preregistration_sha256: str, expected_sha256: str, sign: float = 1.0) -> Opinion:
    """Recomputes from the raw trades with its own code; any mismatch blocks."""
    tr = res["trades"]
    blocking, f = [], []
    r = [sign * float(x) for x in tr.r.tolist()]
    n = len(r)
    mean = sum(r) / n if n else float("nan")
    weeks: dict[int, float] = {}
    for x, t in zip(r, tr.t.tolist()):
        wk = (int(t) - 4 * 86400) // (7 * 86400)
        weeks[wk] = weeks.get(wk, 0.0) + (x - mean)
    g = len(weeks)
    se = math.sqrt(g / (g - 1) * sum(v * v for v in weeks.values()) / n ** 2) if n and g > 1 else None
    t_mine = mean / se if se else None
    sig = res["checks"]["significance"]
    if n != res["checks"]["min_trades"]["n"]:
        blocking.append(f"trade count {n} does not match the battery's {res['checks']['min_trades']['n']}")
    if sig["t"] is not None and (t_mine is None or abs(t_mine - sig["t"]) > 1e-3):
        blocking.append(f"recomputed t {t_mine} does not match the battery's {sig['t']}")
    t0, t1 = segment_epochs
    if n and (min(tr.t.tolist()) < t0 or max(tr.t.tolist()) >= t1 or max(tr.exit_t.tolist()) > t1):
        blocking.append("a trade lies outside the judged segment")
    if n and max(tr.exit_t.tolist()) > holdout_epoch:
        blocking.append("a trade reaches into the sealed holdout")
    by_sym: dict[str, list[tuple[int, int]]] = {}
    for s, row, bars in zip(tr.symbol.tolist(), tr.row.tolist(), tr.bars.tolist()):
        by_sym.setdefault(s, []).append((int(row), int(row) + int(bars)))
    for s, spans in by_sym.items():
        spans.sort()
        if any(b[0] < a[1] for a, b in zip(spans, spans[1:])):
            blocking.append(f"overlapping trades on {s}")
    if res["exit"] != declared_exit:
        blocking.append(f"exit {res['exit']} is not the declared {declared_exit}")
    if abs(sig["threshold"] - round(frozen_threshold, 3)) > 1e-9:
        blocking.append(f"threshold {sig['threshold']} is not the frozen {frozen_threshold:.3f}")
    if preregistration_sha256 != expected_sha256:
        blocking.append("the design that ran is not the design that was preregistered")
    f.append(f"recomputed independently: n={n}, mean {mean:+.5f}R, clustered t "
             f"{'n/a' if t_mine is None else f'{t_mine:.3f}'} ({g} weeks)")
    return Opinion("reviewer", f, [], blocking,
                   {"n": n, "mean_R": round(mean, 6) if n else None, "t": round(t_mine, 4) if t_mine else None})


def llm_objections(client, summary: dict, max_items: int = 5) -> list[dict]:
    """A model's critique: objections only, each marked blocking or not. Invalid replies are dropped."""
    def validate(d: dict) -> str | None:
        items = d.get("objections")
        if not isinstance(items, list) or len(items) > max_items:
            return f"objections must be a list of at most {max_items}"
        for o in items:
            if not isinstance(o, dict) or not isinstance(o.get("text"), str) or not o["text"].strip() \
                    or not isinstance(o.get("blocking"), bool):
                return "each objection needs text and a boolean blocking"
        return None

    system = ("You review a trading-research result as a sceptic. You may only raise objections: reasons the "
              "result could be wrong, lucky or unusable. You cannot approve anything. Reply with ONE JSON object: "
              '{"objections": [{"text": "...", "blocking": true|false}]}; blocking only for a concrete flaw.')
    res = client.complete_json("research_critic", system, json.loads(json.dumps(summary, default=str)), validate)
    if not res.ok:
        return []
    return [{"text": o["text"][:500], "blocking": o["blocking"], "model": res.model} for o in res.data["objections"]]


def synthesize(battery_verdict: str, opinions: list[Opinion], llm: list[dict] = ()) -> dict:
    """No voting: the battery decides and every blocking objection subtracts."""
    if battery_verdict not in ("VALIDATED", "REJECTED"):
        raise ValueError(f"unknown battery verdict {battery_verdict!r}")
    blocked = [f"{o.analyst}: {b}" for o in opinions for b in o.blocking]
    blocked += [f"llm ({x.get('model')}): {x['text']}" for x in llm if x.get("blocking")]
    verdict = "VALIDATED" if battery_verdict == "VALIDATED" and not blocked else "REJECTED"
    return {"version": BOARD_VERSION, "verdict": verdict, "battery_verdict": battery_verdict,
            "blocked_by": blocked if battery_verdict == "VALIDATED" else [],
            "objections_after_rejection": blocked if battery_verdict == "REJECTED" else [],
            "concerns": [f"{o.analyst}: {c}" for o in opinions for c in o.concerns],
            "llm_objections": list(llm),
            "opinions": [o.to_json() for o in opinions],
            "rule": "no voting: the preregistered battery decides; the board can only subtract"}
