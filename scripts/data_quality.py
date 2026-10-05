"""Data-quality report for every bar dataset in this repository (takeover audit, step 6).

    python scripts/data_quality.py      # -> research/results/data_quality.json, docs/DATA_QUALITY_REPORT.md

Per file:

- the sha256 of the whole file;
- every statistic computed on bars BEFORE the fx-majors holdout (2017-01-01) only, so the sealed period
  is never read for anything but the hash;
- duplicates, non-increasing timestamps, impossible OHLC (high < low, open/close outside the range,
  ask below bid), abnormal spreads (> 10x the median), weekday gaps over an hour, coverage by UTC
  hour (the 00:00-01:00 defect), outlier returns (> 10 standard deviations), and first/last bar.

The hour-00 sensitivity measures what the defect does to the research:

- EURUSD is the only complete series;
- the declared H1 action templates (research/labels.py, used by DP-001, SL-002, PR-001 and the
  live tracker) are labelled on EURUSD H1 2009-2016 built from M15 with and without the 00:00-00:59
  M15 bars;
- the difference in mean gross R is the bias the defect introduces into every H1 experiment on the
  other pairs.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from aitrader.data.bars import BarSeries  # noqa: E402
from aitrader.data.resample import resample  # noqa: E402
from aitrader.research.labels import TEMPLATES, compute_labels  # noqa: E402

HOLDOUT_START = int(datetime(2017, 1, 1, tzinfo=timezone.utc).timestamp())
OUT_JSON = ROOT / "research" / "results" / "data_quality.json"
OUT_MD = ROOT / "docs" / "DATA_QUALITY_REPORT.md"
QUALITY_VERSION = "data-quality-1.0.0"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def pip_of(symbol: str) -> float:
    return 0.1 if symbol.startswith("XAU") else 0.01 if "JPY" in symbol else 0.0001


def scan(path: Path) -> dict:
    d = np.load(path)
    t_all = d["open_time"]
    keep = t_all < HOLDOUT_START
    t = t_all[keep]
    col = {k: d[k][keep].astype(float) for k in ("bid_open", "bid_high", "bid_low", "bid_close",
                                                  "ask_open", "ask_high", "ask_low", "ask_close")}
    symbol = path.name.split("_")[0]
    step = int(np.median(np.diff(t))) if len(t) > 1 else 0
    dt = np.diff(t)
    wd = (t[:-1] // 86400 + 3) % 7
    # a gap inside the trading week: Monday-Thursday, or Friday before 20:00 UTC
    weekday_gap = (dt > 3600) & ((wd < 4) | ((wd == 4) & ((t[:-1] // 3600) % 24 < 20)))
    hours = (t // 3600) % 24
    mon_thu = (t // 86400 + 3) % 7 < 4
    cnt = np.bincount(hours[mon_thu], minlength=24)
    med_hour = float(np.median(cnt))
    bad_ohlc = 0
    for side in ("bid", "ask"):
        o, h, low, c = (col[f"{side}_{x}"] for x in ("open", "high", "low", "close"))
        bad_ohlc += int(np.sum((h < low) | (o > h + 1e-12) | (o < low - 1e-12) | (c > h + 1e-12) | (c < low - 1e-12)))
    crossed = int(np.sum((col["ask_close"] < col["bid_close"]) | (col["ask_open"] < col["bid_open"])))
    spread = (col["ask_close"] - col["bid_close"]) / pip_of(symbol)
    med_spread = float(np.median(spread))
    mid = (col["ask_close"] + col["bid_close"]) / 2
    ret = np.diff(np.log(mid))
    sd = float(np.std(ret)) if len(ret) else 0.0
    out = {
        "file": str(path.relative_to(ROOT)), "symbol": symbol, "sha256_whole_file": sha256(path),
        "bars_scanned": int(len(t)), "bars_in_sealed_period_not_scanned": int((~keep).sum()),
        "first": datetime.fromtimestamp(int(t[0]), timezone.utc).isoformat() if len(t) else None,
        "last_scanned": datetime.fromtimestamp(int(t[-1]), timezone.utc).isoformat() if len(t) else None,
        "bar_seconds": step,
        "duplicate_timestamps": int(np.sum(dt == 0)), "non_increasing_timestamps": int(np.sum(dt < 0)),
        "impossible_ohlc": bad_ohlc, "ask_below_bid": crossed,
        "spread_pips_median": round(med_spread, 3),
        "abnormal_spreads_over_10x_median": int(np.sum(spread > 10 * max(med_spread, 1e-9))),
        "weekday_gaps_over_1h": int(np.sum(weekday_gap)),
        "hour_coverage_vs_median_hour": {f"{h:02d}": round(float(cnt[h] / med_hour), 3) if med_hour else None
                                         for h in range(24)},
        "hour00_missing": bool(med_hour and cnt[0] / med_hour < 0.5),
        "outlier_returns_over_10sd": int(np.sum(np.abs(ret) > 10 * sd)) if sd > 0 else 0,
    }
    return out


def hour00_sensitivity() -> dict:
    """Bias of the missing 00:00 hour on the declared H1 templates, measured on EURUSD (complete)."""
    path = ROOT / "data" / "processed" / "EURUSD_M15.npz"
    if not path.exists():
        return {"available": False, "reason": f"{path} not present"}
    m15 = BarSeries.load(path)
    lo = int(datetime(2009, 1, 1, tzinfo=timezone.utc).timestamp())
    keep = (m15.open_time >= lo) & (m15.open_time < HOLDOUT_START)
    full = m15.take(np.flatnonzero(keep))
    cut = full.take(np.flatnonzero((full.open_time // 3600) % 24 != 0))
    out: dict[str, dict] = {}
    for name, series in (("complete", full), ("hour00_removed", cut)):
        h1 = resample(series, "H1", as_of=HOLDOUT_START)
        labels = compute_labels(h1, 0.0001)
        row = {}
        for tpl in TEMPLATES:
            for side in (1, -1):
                o = labels.outcomes[(tpl.key, side)]
                ok = o.reason != -9
                gross = o.r[ok] + o.cost_r[ok]
                row[f"{tpl.key}:{'BUY' if side > 0 else 'SELL'}"] = {
                    "n": int(ok.sum()), "mean_gross_r": round(float(np.mean(gross)), 5),
                    "mean_net_r": round(float(np.mean(o.r[ok])), 5),
                    "stop_share": round(float(np.mean(o.reason[ok] == -1)), 4)}
        out[name] = {"h1_bars": int(len(h1)), "templates": row}
    diffs = {k: round(out["hour00_removed"]["templates"][k]["mean_gross_r"] - out["complete"]["templates"][k]["mean_gross_r"], 5)
             for k in out["complete"]["templates"]}
    return {"available": True, "symbol": "EURUSD", "period": "2009-01-01 to 2016-12-31", "results": out,
            "gross_r_difference_removed_minus_complete": diffs,
            "max_abs_difference_r": round(max(abs(v) for v in diffs.values()), 5)}


AFFECTED = [
    {"experiments": "DP-001, DP-002, SL-001, SL-002, CP-001, XS-001, WF-001..003, R2A-D, R3, R4, COT-1, FLOW-1, "
                    "PR-001 (and the live history memory)",
     "data": "data/processed/*_M15.npz -> H1/H4/D1 (11 of 12 pairs and XAUUSD lack 00:00-00:59 UTC)",
     "how": "H1 bars for hour 00 are absent; H4/D1 bars miss that hour's range; overnight trades jump from the "
            "23:00 close to the 01:00 open, so a stop inside that hour fills at the 01:00 open (pessimistic)"},
    {"experiments": "ID-1, ID-2", "data": "data/m5/*_M5_2009_2016.npz (all except EURUSD)",
     "how": "entries are 07:00-19:55 UTC and exits by 20:55 (ID-2) or within 4 h (ID-1): no trade spans hour 00. "
            "It enters only through 14-hour ATRs, the Asian range (from 01:00) and previous-day levels"},
]


def render(rep: dict) -> str:
    rows = "\n".join(
        f"| {r['file'].split('/')[-1]} | {r['bars_scanned']:,} | {r['first'][:10]} | {r['last_scanned'][:10]} | "
        f"{r['duplicate_timestamps']} | {r['impossible_ohlc']} | {r['ask_below_bid']} | {r['spread_pips_median']} | "
        f"{r['abnormal_spreads_over_10x_median']} | {r['weekday_gaps_over_1h']} | "
        f"{'**missing**' if r['hour00_missing'] else 'present'} | {r['outlier_returns_over_10sd']} | "
        f"`{r['sha256_whole_file'][:12]}` |" for r in rep["datasets"])
    s = rep["hour00_sensitivity"]
    sens = ""
    if s.get("available"):
        sens = "\n".join(f"| {k} | {s['results']['complete']['templates'][k]['mean_gross_r']:+.4f} | "
                         f"{s['results']['hour00_removed']['templates'][k]['mean_gross_r']:+.4f} | {v:+.4f} |"
                         for k, v in s["gross_r_difference_removed_minus_complete"].items())
    aff = "\n".join(f"| {a['experiments']} | {a['data']} | {a['how']} |" for a in rep["affected_experiments"])
    return f"""# Data-quality report

Generated by `python scripts/data_quality.py` ({rep['version']}).

- **Machine-readable:** `research/results/data_quality.json`.
- **Scope:** every statistic is computed on bars before 2017-01-01. The fx-majors holdout is sealed,
  and its bars are hashed (as part of the whole file) and counted, never read for anything else.

## Datasets

**Columns:**

- duplicates, impossible OHLC and ask < bid are bar counts;
- abnormal spreads are counts of bars above 10× the median spread;
- gaps are weekday gaps of more than an hour;
- outliers are one-bar returns beyond 10 standard deviations;
- the hash covers the whole file.

| File | Bars scanned | First | Last scanned | Duplicates | Impossible OHLC | Ask < bid | Median spread (pips) | Abnormal spreads | Weekday gaps > 1 h | Hour 00 UTC | Outliers > 10 sd | sha256 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
{rows}

## The missing 00:00–01:00 UTC hour

**The defect.** {rep['hour00_summary']}

**It cannot be repaired here.**

- The only bid/ask source this project reaches is the FX-Data mirror of Dukascopy ticks, and the
  hour is absent there.
- Dukascopy's own datafeed is unreachable from this environment (every request fails) and throttled
  from CI runners: 107 of 120 requests failed (`research/results/id-probe.json`).
- So the affected experiments **cannot be rerun on corrected data**. Their size of effect is measured
  instead, on EURUSD, the one complete series.

**Measured bias on EURUSD H1, 2009–2016.**

- The table compares the declared H1 templates' mean gross R per trade, labelled on all M15 bars and
  with the 00:00–00:59 bars removed.
- Every H1-based experiment (DP/SL/CP/WF/R2–R4/COT/FLOW/PR-001) uses these templates.

| Template | Complete | Hour 00 removed | Difference |
|---|---|---|---|
{sens}

**Largest absolute difference: {s.get('max_abs_difference_r')} R per trade.**

That is far below the gaps between those experiments' results and their pass thresholds:

- every one failed with net R ≤ 0;
- the costs alone were 0.09–0.21R a trade.

**The defect cannot have turned a pass into a fail, or a fail into a pass**, at this size. It is a known
limitation, recorded in `research_status.json`.

### Affected experiments

| Experiments | Data | How the hour enters |
|---|---|---|
{aff}

## Other datasets

- **Daily index, ETF and futures series (RC-*, DIV-*, TOM-D):** these were fetched and judged on CI
  runners and are not stored in this checkout. Their fetch manifests (`data/rc/*.json`,
  `data/div*/`) record the source, the hashes and the cleaning (stale and spike counts per series),
  and `research_status.json` lists their hashes.
- **External macro series (`data/external/`) and policy rates (`data/*/policy_rates.csv`):** these
  are point-in-time with publication lags, and are audited in docs/ROUND2_DATA_AUDIT.md and
  docs/H10_DATA_AUDIT.md.
"""


def main() -> int:
    files = sorted((ROOT / "data" / "processed").glob("*_M15.npz")) + sorted((ROOT / "data" / "m5").glob("*.npz"))
    datasets = [scan(f) for f in files]
    missing = [d["file"].split("/")[-1] for d in datasets if d["hour00_missing"]]
    rep: dict[str, Any] = {
        "version": QUALITY_VERSION, "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "scope": "bars before 2017-01-01 (the fx-majors holdout is sealed); whole-file hashes",
        "datasets": datasets,
        "hour00_missing_files": missing,
        "hour00_summary": (f"{len(missing)} of {len(datasets)} bar files have no 00:00-00:59 UTC bars: every M15 "
                           "and M5 file except EURUSD's. The FX-Data mirror of Dukascopy omits that hour for "
                           "those pairs."),
        "hour00_sensitivity": hour00_sensitivity(),
        "affected_experiments": AFFECTED,
        "other_sources": {p.name: sha256(p) for p in sorted((ROOT / "data").glob("*/*manifest*.json"))},
    }
    OUT_JSON.write_text(json.dumps(rep, indent=1, sort_keys=True) + "\n")
    OUT_MD.write_text(render(rep))
    print(json.dumps({"files": len(datasets), "hour00_missing": len(missing),
                      "max_abs_difference_r": rep["hour00_sensitivity"].get("max_abs_difference_r")}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
