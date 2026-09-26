"""Market regime and familiarity.

Regime boundaries are QUANTILES OF TRAINING DATA, fitted once per model
version and stored; nothing about the current or future data enters them
(VALIDATION_CONTRACT.md §4). The labels are descriptions, not strategy:
whether a regime is persistent or informative is measured by
`regime_report`, and a label that turns out uninformative is still a
harmless description.

Familiarity answers "have I seen a state like this before?" with a
Mahalanobis distance to the training distribution. A state beyond the
training 99.5th percentile is UNFAMILIAR, and the decision layer treats
that as NO_TRADE (PROJECT_SPEC.md §4).
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field

import numpy as np

from ..features.store import INDEX

REGIME_VERSION = "regime-1.0.0"

FAMILIARITY_FEATURES = (
    "r24", "r120", "er24", "er120", "dist_ma48", "ma_slope", "vol_ratio",
    "rv_ratio", "range_pos120", "spread_rel", "tick_activity",
)

LABELS = ("TRENDING_UP", "TRENDING_DOWN", "RANGING", "TRANSITION", "ABNORMAL")
VOL_STATES = ("LOW_VOL", "NORMAL_VOL", "HIGH_VOL")


@dataclass(frozen=True)
class RegimeState:
    label: str
    vol_state: str
    trend_direction: int  # +1 / -1 / 0
    abnormal: bool
    familiarity_distance: float
    familiar: bool
    reasons: tuple[str, ...] = ()

    def as_dict(self) -> dict:
        d = asdict(self)
        d["reasons"] = list(self.reasons)
        return d


@dataclass
class RegimeModel:
    version: str
    trained_until: int  # epoch seconds: no training row decided after this
    n_train: int
    q: dict[str, float]
    mean: list[float]
    inv_cov: list[list[float]]
    familiarity_threshold: float
    features: tuple[str, ...] = FAMILIARITY_FEATURES
    meta: dict = field(default_factory=dict)

    # ── fit / persist ───────────────────────────────────────────────────

    @classmethod
    def fit(cls, matrix: np.ndarray, decision_times: np.ndarray, *, trained_until: int) -> "RegimeModel":
        if len(decision_times) and int(np.max(decision_times)) > trained_until:
            raise ValueError("training rows extend past trained_until: that would be look-ahead")
        cols = [INDEX[f] for f in FAMILIARITY_FEATURES]
        x = matrix[:, cols]
        x = x[np.all(np.isfinite(x), axis=1)]
        if len(x) < 500:
            raise ValueError(f"only {len(x)} complete training rows; too few to fit a regime model")

        def pct(name, p):
            col = matrix[:, INDEX[name]]
            return float(np.nanpercentile(col, p))

        q = {
            "vol_p20": pct("vol_ratio", 20), "vol_p80": pct("vol_ratio", 80), "vol_p995": pct("vol_ratio", 99.5),
            "er_p33": pct("er120", 33), "er_p67": pct("er120", 67),
            "spread_p995": pct("spread_rel", 99.5), "slope_abs_p50": float(np.nanpercentile(np.abs(matrix[:, INDEX["ma_slope"]]), 50)),
        }
        mean = x.mean(axis=0)
        cov = np.cov(x, rowvar=False)
        cov += np.eye(cov.shape[0]) * 1e-6 * np.trace(cov) / cov.shape[0]
        inv = np.linalg.inv(cov)
        d = np.sqrt(np.einsum("ij,jk,ik->i", x - mean, inv, x - mean))
        return cls(REGIME_VERSION, int(trained_until), int(len(x)), q, mean.tolist(), inv.tolist(),
                   float(np.percentile(d, 99.5)))

    def to_json(self) -> str:
        d = asdict(self)
        d["features"] = list(self.features)
        return json.dumps(d, sort_keys=True)

    @classmethod
    def from_json(cls, raw: str) -> "RegimeModel":
        d = json.loads(raw)
        d["features"] = tuple(d["features"])
        return cls(**d)

    # ── inference ───────────────────────────────────────────────────────

    def familiarity(self, values: dict[str, float]) -> float:
        x = np.array([values.get(f, np.nan) for f in self.features], dtype=float)
        if not np.all(np.isfinite(x)):
            return float("inf")
        diff = x - np.asarray(self.mean)
        return float(np.sqrt(diff @ np.asarray(self.inv_cov) @ diff))

    def classify(self, values: dict[str, float]) -> RegimeState:
        q = self.q
        reasons: list[str] = []
        vr, er, slope, spread = (values.get(k, np.nan) for k in ("vol_ratio", "er120", "ma_slope", "spread_rel"))
        dist = self.familiarity(values)
        familiar = bool(np.isfinite(dist) and dist <= self.familiarity_threshold)
        if not familiar:
            reasons.append(f"unfamiliar state: distance {dist:.2f} > {self.familiarity_threshold:.2f}")
        if not all(np.isfinite(v) for v in (vr, er, slope, spread)):
            return RegimeState("ABNORMAL", "NORMAL_VOL", 0, True, dist, False, tuple(reasons + ["missing regime inputs"]))

        abnormal = vr > q["vol_p995"] or spread > q["spread_p995"]
        if vr > q["vol_p995"]:
            reasons.append(f"volatility ratio {vr:.2f} beyond training 99.5% ({q['vol_p995']:.2f})")
        if spread > q["spread_p995"]:
            reasons.append(f"spread/ATR {spread:.3f} beyond training 99.5% ({q['spread_p995']:.3f})")
        vol_state = "HIGH_VOL" if vr > q["vol_p80"] else "LOW_VOL" if vr < q["vol_p20"] else "NORMAL_VOL"
        direction = int(np.sign(slope)) if abs(slope) > q["slope_abs_p50"] else 0
        if abnormal:
            label = "ABNORMAL"
        elif er > q["er_p67"] and direction != 0:
            label = "TRENDING_UP" if direction > 0 else "TRENDING_DOWN"
        elif er < q["er_p33"]:
            label = "RANGING"
        else:
            label = "TRANSITION"
        return RegimeState(label, vol_state, direction, abnormal, dist, familiar, tuple(reasons))


def regime_report(labels: list[str], outcomes: np.ndarray | None = None) -> dict:
    """Does the data support these regimes? Persistence and outcome by regime.

    Persistence: probability that the next observation has the same label.
    A "regime" that flips every bar is noise with a name.
    """
    lab = np.asarray(labels)
    out: dict = {"counts": {k: int((lab == k).sum()) for k in LABELS}}
    if len(lab) > 1:
        same = lab[1:] == lab[:-1]
        out["persistence"] = {k: float(same[lab[:-1] == k].mean()) if (lab[:-1] == k).any() else None for k in LABELS}
    if outcomes is not None:
        o = np.asarray(outcomes, dtype=float)
        out["mean_outcome"] = {}
        for k in LABELS:
            sel = (lab == k) & np.isfinite(o)
            n = int(sel.sum())
            out["mean_outcome"][k] = {"n": n, "mean": float(o[sel].mean()) if n else None,
                                      "se": float(o[sel].std(ddof=1) / np.sqrt(n)) if n > 1 else None}
    return out
