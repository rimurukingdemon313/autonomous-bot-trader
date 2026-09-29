"""The real research universe and the DP-001 design.

- `load_universe`: H1 bars of the twelve FX pairs from the data store (which truncates at the
  sealed holdout), the 23 production features and the 12 discovery primitives on each.
- `feature_records`: one catalog record per feature, with its definition, provenance and
  point-in-time rule.
- `leakage_checker`: the truncation test on REAL bars — every input, other instruments included,
  cut at each sampled decision bar. Features only; no outcome is read.
- `dp001`: the first discovery program's design, its significance threshold taken from the
  registry at the moment it is built.
"""

from __future__ import annotations

from dataclasses import replace
from datetime import date

import numpy as np

from ...data import instruments
from ...data.bars import BarSeries
from ...features.store import FEATURE_VERSION, INDEX, NAMES, SPECS, compute_matrix
from ..labels import atr24
from ..registry import Registry
from .battery import BatteryRules
from .catalog import FeatureRecord, truncation_leaks
from .exits import EXIT_BY_KEY
from .primitives import PRIMITIVE_BY_NAME, PRIMITIVES, PRIMITIVES_VERSION, USD_SIGN, Others
from .program import ModelPlan, ProgramDesign
from .study import Segment, SymbolData

FX = ("EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "USDCAD", "USDCHF", "NZDUSD", "EURGBP", "EURJPY", "GBPJPY", "EURCHF",
      "AUDJPY")
STATES = ("er120", "vol_ratio", "ma_slope", "range_pos120", "d1_trend", "usd_basket", "atr_pctile", "usd_corr",
          "session")
TRIGGERS = ("r1", "r6", "r24", "bar_body", "range_pos24", "smc_sweep", "bar_range", "range_contraction",
            "up_persistence", "smc_structure")
GROUPS = (("session", ((0.0,), (1.0, 2.0), (3.0, 4.0))),
          ("smc_sweep", ((-1.0,), (0.0,), (1.0,))),
          ("smc_structure", ((-2.0, -1.0), (0.0,), (1.0, 2.0))))
CATEGORICAL = {"session", "weekday", "smc_sweep", "smc_structure"}
ALL_FEATURES = tuple(NAMES) + tuple(p.name for p in PRIMITIVES)


def feature_records(program: str) -> dict[str, FeatureRecord]:
    out = {}
    for spec in SPECS:
        out[spec.name] = FeatureRecord(
            spec.name, spec.description, spec.group, "categorical" if spec.name in CATEGORICAL else "continuous",
            "H1", ("own H1 bid/ask bars",), f"aitrader/features/store.py ({FEATURE_VERSION}); used in production",
            FEATURE_VERSION, f"from bars closed at or before the decision bar; NaN for the first {spec.window} bars",
            f"does the {spec.group} state it measures change the distribution of the next move after costs?", program)
    for p in PRIMITIVES:
        out[p.name] = FeatureRecord(
            p.name, p.definition, p.dimension, p.kind, "H1", p.requires,
            f"aitrader/research/discovery/primitives.py ({PRIMITIVES_VERSION}); research only", PRIMITIVES_VERSION,
            "higher timeframes from buckets closed by the bar's close; other instruments aligned on the same open "
            "time; NaN when history is short, never a default",
            f"does the {p.dimension} dimension, absent from the production features, carry information?", program)
    return out


def load_universe(store, symbols=FX) -> tuple[dict[str, SymbolData], dict[str, str]]:
    series = {s: store.load(s, "H1") for s in symbols}
    usd = Others({s: v for s, v in series.items() if s in USD_SIGN})
    data, hashes = {}, {}
    for s, ser in series.items():
        m = compute_matrix(ser)
        cols = {name: m[:, INDEX[name]] for name in NAMES}
        for p in PRIMITIVES:
            cols[p.name] = p.column(ser, m, usd)
        data[s] = SymbolData(s, ser, instruments.get(s).pip, cols, atr24(ser))
        hashes[s] = ser.content_hash()
    return data, hashes


def leakage_checker(series: dict[str, BarSeries], rows_per_symbol: int = 6, window: int = 3000):
    """A LeakageFn over real bars: per symbol, a `window`-bar stretch from the first quarter of its
    history, with `rows_per_symbol` decision rows in its second half (enough warm-up for every
    feature). Production columns share one truncated matrix per row."""
    usd = {k: v for k, v in series.items() if k in USD_SIGN}
    windows, prod_full, prod_part = {}, {}, {}
    for s, ser in sorted(series.items()):
        a = len(ser) // 4
        w = ser.take(slice(a, min(len(ser), a + window)))
        t0, t1 = int(w.open_time[0]), int(w.available_at[-1])
        others = {k: v.between(t0, t1) for k, v in usd.items()}
        rows = np.unique(np.linspace(len(w) // 2, len(w) - 1, rows_per_symbol).astype(int))
        windows[s] = (w, others, rows)

    def check(name: str) -> tuple[list[int], int, list[str]]:
        bad, n = [], 0
        for s, (w, others, rows) in windows.items():
            if name in INDEX:
                if s not in prod_full:
                    prod_full[s] = compute_matrix(w)
                    prod_part[s] = {int(i): compute_matrix(w.take(slice(0, int(i) + 1)))[int(i)] for i in rows}
                j = INDEX[name]
                for i in rows:
                    a_, b_ = prod_full[s][int(i), j], prod_part[s][int(i)][j]
                    if not ((np.isnan(a_) and np.isnan(b_)) or abs(a_ - b_) <= 1e-9 * max(1.0, abs(a_))):
                        bad.append(int(i))
            else:
                p = PRIMITIVE_BY_NAME[name]
                bad += truncation_leaks(lambda s_, o_: p.column(s_, None, o_), w, others, rows)
            n += len(rows)
        return bad, n, sorted(windows)

    return check


def dp001(registry: Registry) -> ProgramDesign:
    d = ProgramDesign(
        id="DP-001",
        title="Bounded state x trigger discovery on H1 FX with a three-way chronological split",
        question=("Does any cell of a declared state x trigger grid (19 features in terciles, both sides), or a "
                  "boosted-stumps model of 35 features, have positive net expectancy that survives a validation "
                  "period it never saw and then a frozen battery on a confirmation period — across instruments, "
                  "years, regimes, costs, delays and bin perturbations?"),
        universe=instruments.UNIVERSE_KEY, instruments=FX,
        segments=(Segment("discovery", "fit", date(2007, 6, 1), date(2011, 1, 1)),
                  Segment("validation", "select", date(2011, 1, 11), date(2013, 7, 1)),
                  Segment("confirmation", "judge", date(2013, 7, 11), date(2017, 1, 1))),
        states=STATES, triggers=TRIGGERS, groups=GROUPS, exits=tuple(EXIT_BY_KEY), rules=BatteryRules(t_threshold=1.0),
        holdout_start=registry.holdout.start if registry.holdout else date(2017, 1, 1),
        model=ModelPlan(features=ALL_FEATURES), feature_budget=40, min_embargo_days=10,
        lookback_start=date(2007, 3, 30))
    thr = registry.threshold_for_next(d.universe, d.segments[2].start, d.segments[2].end, new_tests=d.judged_tests())
    return replace(d, rules=replace(d.rules, t_threshold=thr))
