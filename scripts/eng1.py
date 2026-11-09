"""ENG-1: the energy futures term-structure premium (docs/DISCOVERY_PROGRAM.md, H1; research/preregistrations/ENG-1.md).

    python scripts/eng1.py fetch          # GitHub's runner: EIA's NYMEX futures, contracts 1-3 of four energies
    python scripts/eng1.py spec           # freeze the spec and the code hashes, before registration
    python scripts/eng1.py preregister    # register the trial; the preregistration must quote both hashes
    python scripts/eng1.py judge          # once: 1985-02..2018-12
    python scripts/eng1.py holdout        # once, and only after a PASS: 2019-01..2024-03

The question: does holding an energy future only while its curve is backwardated earn a positive net return, and more
than holding it always, at a swap-free CFD's costs? Backwardated means contract 2 above contract 3 at the month's last
priced day. The mechanism is the theory of storage and hedging pressure: scarce inventories give a convenience yield,
and hedgers pay longs a premium.

- **The data.** EIA's daily settlements of NYMEX contracts 1, 2 and 3 for:
  - WTI crude (RCLC*), from 1985-01;
  - NY Harbor heating oil (EER_EPD2F_PE*), from 1994-02;
  - NY Harbor RBOB gasoline (EER_EPMRR_PE*), from 2005-10;
  - Henry Hub natural gas (RNGC*), from 1994-01.
  EIA stopped publishing them after 2024-04-05. The dates were checked first by a probe that read no price
  (research/results/ENG-probe.json on branch eng-probe).
- **The book.** At each month's last priced day t, each energy is held from t to the next month's day t' if
  ln(C2/C3) > 0 at t, and is flat otherwise. The contract held is the one that is contract 2 at t. Its price at t' is
  that same contract's, identified through the exchange's expiry rule, so a roll never mixes contracts.
- **Sizing.** Inverse volatility from the past 12 monthly returns of holding it always, known at t, at 10% a year
  each, divided by the number of energies with data, capped at 2.0.
- **Costs.** No financing: a swap-free CFD. A spread and slippage on every entry and exit, and one way more each month
  a position is rolled. ×1, ×1.5 and ×2.
"""

from __future__ import annotations

import bisect
import hashlib
import json
import math
import sys
import urllib.request
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from aitrader.research.registry import Holdout, Registry, Trial, Use, Verdict  # noqa: E402

PID, HPID = "ENG-1", "ENG-1-H"
VERSION = "eng-1.0.0"
R = ROOT / "research"
DOC = "research/preregistrations/ENG-1.md"
SPEC = R / "specs" / "ENG-1.json"
OUT = R / "knowledge"
DATA = ROOT / "data" / "eng"
CODE = ("scripts/eng1.py",)
UNIVERSE = "energy-futures-eia"
SERIES = {"WTI": ("pet", ("RCLC1", "RCLC2", "RCLC3")),
          "HEATING_OIL": ("pet", tuple(f"EER_EPD2F_PE{n}_Y35NY_DPG" for n in (1, 2, 3))),
          "RBOB": ("pet", tuple(f"EER_EPMRR_PE{n}_Y35NY_DPG" for n in (1, 2, 3))),
          "NATGAS": ("ng", ("RNGC1", "RNGC2", "RNGC3"))}
URL = {"pet": "https://www.eia.gov/dnav/pet/hist_xls/{sid}d.xls", "ng": "https://www.eia.gov/dnav/ng/hist_xls/{sid}d.xls"}
JUDGE = (date(1985, 2, 1), date(2019, 1, 1))  # months whose return ends in 1985-02..2018-12
DEV = (date(1985, 2, 1), date(2002, 1, 1))
VAL = (date(2002, 1, 1), date(2019, 1, 1))
HOLD = (date(2019, 1, 1), date(2024, 4, 1))
TARGET_VOL, MAX_W, VOL_MONTHS, MIN_VOL_MONTHS = 0.10, 2.0, 12, 6
#: one way, in basis points of notional: the CFD's half spread plus 1 bp of slippage
COST_BP = {"WTI": 3.5, "HEATING_OIL": 7.0, "RBOB": 7.0, "NATGAS": 11.0}
COST_GRID = (1.0, 1.5, 2.0)
PERMUTATIONS, PERM_SEED = 2000, 41
BOOT_N, BOOT_SEED, BOOT_BLOCK = 5000, 43, 12
GATES = {"t": "monthly net t over 1985-02..2018-12 >= the threshold (every earlier test on these data; never below 3.0)",
         "development": "mean net > 0 over 1985-02..2001-12", "validation": "mean net > 0 over 2002-01..2018-12",
         "costs_x2": "mean net > 0 at twice the costs", "one_month_late": "mean net > 0 with the signal a month old",
         "beats_always_long": "the mean monthly difference to holding every energy always, same weights, is > 0",
         "beats_random": "the mean exceeds the 95th percentile of 2,000 books with each energy's long months shuffled",
         "leave_one_out": "mean net > 0 with any one energy left out",
         "top_year": "no year gives more than 25% of the total net",
         "bootstrap": "the 12-month block bootstrap's 95% interval of the mean is above 0"}
HOLDOUT_RULE = ("registered and read only if every gate passes: 2019-01..2024-03, the same book; it passes if its mean "
                "net is > 0 and > 0 at twice the costs, with every energy present")
UA = {"User-Agent": "Mozilla/5.0 (research; aitrader ENG-1)"}


# ── the exchange's calendar ─────────────────────────────────────────────

def _month_add(y: int, m: int, k: int) -> tuple[int, int]:
    n = y * 12 + (m - 1) + k
    return n // 12, n % 12 + 1


def expiry(kind: str, delivery: tuple[int, int], bdays: list[date]) -> date:
    """The last trading day of the contract for `delivery` (year, month), from NYMEX's rule, counted on `bdays`."""
    py, pm = _month_add(*delivery, -1)
    if kind == "WTI":  # 3 business days before the 25th of the month before delivery (or before the last day before)
        d25 = date(py, pm, 25)
        i = bisect.bisect_right(bdays, d25) - 1
        if bdays[i] != d25:
            i = bisect.bisect_right(bdays, d25 - timedelta(days=1)) - 1
        return bdays[i - 3]
    if kind in ("HEATING_OIL", "RBOB"):  # the last business day of the month before delivery
        first_next = date(*delivery, 1)
        return bdays[bisect.bisect_left(bdays, first_next) - 1]
    if kind == "NATGAS":  # 3 business days before the first day of the delivery month
        first = date(*delivery, 1)
        return bdays[bisect.bisect_left(bdays, first) - 3]
    raise ValueError(kind)


def extended(bdays: list[date], days: int = 130) -> list[date]:
    """The business days, with the weekdays after the last one added: later contracts' last trading days are known
    from the calendar, not from prices, and the data's last months need them."""
    last = bdays[-1]
    return bdays + [last + timedelta(days=i) for i in range(1, days + 1) if (last + timedelta(days=i)).weekday() < 5]


def front_delivery(kind: str, d: date, bdays: list[date]) -> tuple[int, int]:
    """The delivery month of contract 1 on day d: the first contract whose last trading day is d or later."""
    y, m = _month_add(d.year, d.month, 0)
    for k in range(0, 4):
        dm = _month_add(y, m, k)
        if expiry(kind, dm, bdays) >= d:
            return dm
    raise ValueError(f"no live contract on {d}")


# ── the book ─────────────────────────────────────────────────────────────

@dataclass
class Curve:
    """One energy's contracts 1-3 by day (only days with all three priced)."""
    kind: str
    days: list[date]
    c: dict[date, tuple[float, float, float]]


def decision_days(curve: Curve) -> dict[tuple[int, int], date]:
    """Each month's last day with all three contracts priced."""
    out: dict[tuple[int, int], date] = {}
    for d in curve.days:
        out[(d.year, d.month)] = d
    return out


def price_of(curve: Curve, delivery: tuple[int, int], d: date, bdays: list[date]) -> float | None:
    """The price on d of the contract for `delivery`, if it is contract 1, 2 or 3 that day."""
    f = front_delivery(curve.kind, d, bdays)
    k = (delivery[0] * 12 + delivery[1]) - (f[0] * 12 + f[1])
    return curve.c[d][k] if 0 <= k <= 2 else None


def legs(curves: dict[str, Curve], bdays: list[date], last: date) -> dict[str, dict[tuple[int, int], dict]]:
    """Per energy and per month m: the decision day t (month m-1's last priced day), the held contract (contract 2 at
    t), its return to month m's decision day, the basis at t, and the return of holding it always (for the volatility
    and the baseline). Only data before `last` is read."""
    out: dict[str, dict[tuple[int, int], dict]] = {}
    for name, cv in curves.items():
        dd = {k: v for k, v in decision_days(cv).items() if v < last}
        rows = {}
        for (y, m), t in sorted(dd.items()):
            nxt = _month_add(y, m, 1)
            if nxt not in dd:
                continue
            t2 = dd[nxt]
            f = front_delivery(cv.kind, t, bdays)
            held = _month_add(*f, 1)  # contract 2 at t
            p0, p1 = cv.c[t][1], price_of(cv, held, t2, bdays)
            c1, c2, c3 = cv.c[t]
            if p1 is None or p0 <= 0 or p1 <= 0 or c2 <= 0 or c3 <= 0:
                continue
            rows[nxt] = {"t": t, "t_next": t2, "held": held, "ret": p1 / p0 - 1.0,
                         "basis": 12.0 * math.log(c2 / c3)}
        out[name] = rows
    return out


def book(lg: dict[str, dict], period: tuple[date, date], k: float = 1.0, late: int = 0, always: bool = False,
         drop: str | None = None, longs: dict | None = None) -> list[dict]:
    """Monthly rows over `period`: weights, positions, gross, costs (entries, exits, rolls) and net. `late` uses the
    signal that many months old; `always` holds every energy; `drop` leaves one out; `longs` overrides the side."""
    names = [n for n in lg if n != drop]
    months = sorted({mo for n in names for mo in lg[n]})
    rows, prev = [], {}
    for mo in months:
        if not (period[0] <= date(*mo, 1) < period[1]):
            continue
        avail = [n for n in names if mo in lg[n]]
        w, pos = {}, {}
        for n in avail:
            hist = [lg[n][p]["ret"] for p in sorted(lg[n]) if p < mo][-VOL_MONTHS:]
            if len(hist) < MIN_VOL_MONTHS or np.std(hist, ddof=1) <= 0:
                continue
            sig_mo = _month_add(*mo, -late)
            if sig_mo not in lg[n]:
                continue
            on = 1.0 if always else (longs[n][mo] if longs is not None else float(lg[n][sig_mo]["basis"] > 0))
            w[n] = min(MAX_W, TARGET_VOL / (float(np.std(hist, ddof=1)) * math.sqrt(12)))
            pos[n] = on
        nav = max(1, len(w))
        expo = {n: w[n] * pos[n] / nav for n in w}
        gross = sum(expo[n] * lg[n][mo]["ret"] for n in expo)
        trade = sum(abs(expo.get(n, 0.0) - prev.get(n, 0.0)) * COST_BP[n] for n in set(expo) | set(prev)) * k / 1e4
        roll = sum(expo[n] * COST_BP[n] for n in expo) * k / 1e4  # each held position rolls once a month
        rows.append({"month": f"{mo[0]:04d}-{mo[1]:02d}", "n": len(w), "exposure": expo, "gross": gross,
                     "trade_cost": trade, "roll_cost": roll, "net": gross - trade - roll,
                     "contrib": {n: expo[n] * lg[n][mo]["ret"] for n in expo}})
        prev = expo
    return rows


# ── statistics ───────────────────────────────────────────────────────────

def _t(x: np.ndarray) -> float | None:
    if len(x) < 2 or x.std(ddof=1) == 0:
        return None
    return float(x.mean() / x.std(ddof=1) * math.sqrt(len(x)))


def block_bootstrap(x: np.ndarray, block: int = BOOT_BLOCK, n: int = BOOT_N, seed: int = BOOT_SEED):
    if len(x) < 2 * block:
        return None
    rng = np.random.default_rng(seed)
    starts = np.arange(0, len(x) - block + 1)
    k = int(math.ceil(len(x) / block))
    means = np.empty(n)
    for j in range(n):
        idx = np.concatenate([np.arange(s, s + block) for s in rng.choice(starts, k)])[:len(x)]
        means[j] = x[idx].mean()
    lo, hi = np.percentile(means, [2.5, 97.5])
    return round(float(lo), 6), round(float(hi), 6)


def summary(rows: list[dict]) -> dict:
    live = [r for r in rows if r["n"] > 0]
    if not live:
        return {"months": 0}
    x = np.array([r["net"] for r in live])
    sd = float(x.std(ddof=1)) if len(x) > 1 else 0.0
    eq = np.r_[0.0, np.cumsum(x)]
    years: dict[str, float] = {}
    for r in live:
        years[r["month"][:4]] = years.get(r["month"][:4], 0.0) + r["net"]
    total = float(x.sum())
    per: dict[str, list[float]] = {}
    exposed: dict[str, list[float]] = {}
    for r in live:
        for n, v in r["contrib"].items():
            per.setdefault(n, []).append(v)
        for n, e in r["exposure"].items():
            exposed.setdefault(n, []).append(1.0 if e > 0 else 0.0)
    turnover = [sum(abs(r["exposure"].get(n, 0.0) - p["exposure"].get(n, 0.0))
                    for n in set(r["exposure"]) | set(p["exposure"])) for p, r in zip(live, live[1:])]
    switches = sum(1 for p, r in zip(live, live[1:]) for n in set(r["exposure"]) & set(p["exposure"])
                   if (r["exposure"][n] > 0) != (p["exposure"][n] > 0))
    return {"months": len(live), "mean": round(float(x.mean()), 6), "t": _t(x) and round(_t(x), 3),
            "gross_mean": round(float(np.mean([r["gross"] for r in live])), 6),
            "trade_cost_mean": round(float(np.mean([r["trade_cost"] for r in live])), 6),
            "roll_cost_mean": round(float(np.mean([r["roll_cost"] for r in live])), 6),
            "a_year_pct": round(float(x.mean()) * 1200, 3), "vol_a_year_pct": round(sd * math.sqrt(12) * 100, 3),
            "sharpe": round(float(x.mean()) / sd * math.sqrt(12), 3) if sd > 0 else None,
            "worst_fall_pct": round(float(np.max(np.maximum.accumulate(eq) - eq)) * 100, 3),
            "months_won": round(float((x > 0).mean()), 4),
            "turnover_a_month": round(float(np.mean(turnover)), 4) if turnover else 0.0,
            "switches_a_year": round(switches / max(1.0, len(live) / 12), 2),
            "exposure_mean": round(float(np.mean([sum(r["exposure"].values()) for r in live])), 4),
            "by_year": {y: round(v * 100, 3) for y, v in sorted(years.items())},
            "top_year_share": round(max(years.values()) / total * 100, 3) if total > 0 else None,
            "by_energy": {n: {"months": len(v), "contrib_mean": round(float(np.mean(v)), 6),
                              "share_of_months_long": round(float(np.mean(exposed[n])), 3)}
                          for n, v in sorted(per.items())}}


def in_period(rows: list[dict], period: tuple[date, date]) -> list[dict]:
    lo, hi = f"{period[0]:%Y-%m}", f"{period[1]:%Y-%m}"
    return [r for r in rows if lo <= r["month"] < hi]


def shuffled_means(lg: dict, period: tuple[date, date], n: int = PERMUTATIONS, seed: int = PERM_SEED) -> np.ndarray:
    """Books with each energy's long months shuffled among its own months: the same exposure, no information."""
    rng = np.random.default_rng(seed)
    base = {e: {mo: float(r["basis"] > 0) for mo, r in rows.items()} for e, rows in lg.items()}
    out = np.empty(n)
    for j in range(n):
        longs = {}
        for e, sig in base.items():
            keys = list(sig)
            vals = rng.permutation([sig[k] for k in keys])
            longs[e] = dict(zip(keys, vals))
        x = [r["net"] for r in book(lg, period, longs=longs) if r["n"] > 0]
        out[j] = float(np.mean(x)) if x else 0.0
    return out


def evaluate(lg: dict, period: tuple[date, date], t_req: float, permutations: int = PERMUTATIONS) -> dict:
    rows = book(lg, period)
    main = summary(rows)
    x = np.array([r["net"] for r in rows if r["n"] > 0])
    stress = {f"x{k}": summary(book(lg, period, k=k)) for k in COST_GRID if k != 1.0}
    late = summary(book(lg, period, late=1))
    always_rows = book(lg, period, always=True)
    always = summary(always_rows)
    diff = np.array([a["net"] - b["net"] for a, b in zip(rows, always_rows) if a["n"] > 0])
    loo = {n: summary(book(lg, period, drop=n)).get("mean") for n in lg}
    perm = shuffled_means(lg, period, n=permutations)
    p95 = float(np.percentile(perm, 95)) if len(perm) else None
    dev, val = summary(in_period(rows, DEV)), summary(in_period(rows, VAL))
    ci = block_bootstrap(x)
    gates = {"t": (main.get("t") or 0) >= t_req, "development": (dev.get("mean") or 0) > 0,
             "validation": (val.get("mean") or 0) > 0, "costs_x2": (stress["x2.0"].get("mean") or 0) > 0,
             "one_month_late": (late.get("mean") or 0) > 0, "beats_always_long": len(diff) > 0 and diff.mean() > 0,
             "beats_random": p95 is not None and (main.get("mean") or 0) > p95,
             "leave_one_out": all((v or 0) > 0 for v in loo.values()),
             "top_year": main.get("top_year_share") is not None and main["top_year_share"] <= 25.0,
             "bootstrap": ci is not None and ci[0] > 0}
    brief = lambda s: {k: s.get(k) for k in ("months", "mean", "t", "a_year_pct", "sharpe", "worst_fall_pct")}
    return {"threshold_t": round(t_req, 4), "all": main, "development": brief(dev), "validation": brief(val),
            "costs_x1.5": brief(stress["x1.5"]), "costs_x2": brief(stress["x2.0"]), "one_month_late": brief(late),
            "always_long": brief(always),
            "vs_always_long": {"months": len(diff), "mean_difference": round(float(diff.mean()), 6) if len(diff) else None,
                               "t": _t(diff) and round(_t(diff), 3)},
            "random_shuffles": {"n": len(perm), "p95_mean": round(p95, 6) if p95 is not None else None,
                                "share_at_or_above": round(float(np.mean(perm >= (main.get("mean") or 0))), 4)},
            "leave_one_out_means": loo, "bootstrap_95": ci, "gates": gates,
            "failed_gates": [g for g, ok in gates.items() if not ok], "passed": all(gates.values())}


# ── the data ─────────────────────────────────────────────────────────────

def parse_xls(raw: bytes) -> dict[str, float]:
    import xlrd
    book_ = xlrd.open_workbook(file_contents=raw)
    names = book_.sheet_names()
    sh = book_.sheet_by_name("Data 1") if "Data 1" in names else book_.sheet_by_index(1)
    out = {}
    for r in range(sh.nrows):
        a, b = sh.cell(r, 0), sh.cell(r, 1) if sh.ncols > 1 else None
        if b is not None and a.ctype in (xlrd.XL_CELL_DATE, xlrd.XL_CELL_NUMBER) and b.ctype == xlrd.XL_CELL_NUMBER \
                and 20000 < a.value < 80000:
            out[str(date(1899, 12, 30) + timedelta(days=int(a.value)))] = float(b.value)
    return out


def _canon(x) -> str:
    return json.dumps(x, sort_keys=True, separators=(",", ":"))


def cmd_fetch(now: datetime) -> None:
    DATA.mkdir(parents=True, exist_ok=True)
    man = {"retrieved": now.isoformat(), "series": {}}
    for name, (kind, sids) in SERIES.items():
        for sid in sids:
            url = URL[kind].format(sid=sid)
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=120) as r:
                raw = r.read()
            series = parse_xls(raw)
            (DATA / f"{sid}.json").write_text(_canon(series))
            ks = sorted(series)
            man["series"][sid] = {"energy": name, "url": url, "rows": len(series), "first": ks[0], "last": ks[-1],
                                  "raw_sha256": hashlib.sha256(raw).hexdigest(),
                                  "sha256": hashlib.sha256(_canon(series).encode()).hexdigest()}
            print(sid, man["series"][sid]["rows"], ks[0], ks[-1], flush=True)
    (DATA / "manifest.json").write_text(json.dumps(man, indent=1, sort_keys=True) + "\n")


def load(last: date) -> tuple[dict[str, Curve], list[date]]:
    """The curves, with nothing on or after `last`, and the exchange's business days (any energy priced that day,
    the whole span: a calendar, not a price)."""
    man = json.loads((DATA / "manifest.json").read_text())
    raw = {}
    for sid, m in man["series"].items():
        text = (DATA / f"{sid}.json").read_text()
        if hashlib.sha256(text.encode()).hexdigest() != m["sha256"]:
            raise SystemExit(f"{sid}: the data differ from the manifest")
        raw[sid] = json.loads(text)
    bdays = extended(sorted({date.fromisoformat(d) for s in raw.values() for d in s}))
    curves = {}
    for name, (_, sids) in SERIES.items():
        s1, s2, s3 = (raw[s] for s in sids)
        days = sorted(date.fromisoformat(d) for d in set(s1) & set(s2) & set(s3) if date.fromisoformat(d) < last)
        curves[name] = Curve(name, days, {d: (s1[str(d)], s2[str(d)], s3[str(d)]) for d in days})
    return curves, bdays


# ── the program ──────────────────────────────────────────────────────────

def code_hash() -> str:
    h = hashlib.sha256()
    for p in CODE:
        h.update((ROOT / p).read_bytes())
    return h.hexdigest()


def spec_sha(s: dict) -> str:
    return hashlib.sha256(json.dumps(s, sort_keys=True, default=str).encode()).hexdigest()


def _dump(x) -> str:
    return json.dumps(x, indent=1, sort_keys=True, default=str) + "\n"


def _registry() -> Registry:
    return Registry.load(R / "registry.jsonl", Holdout.load(R / "holdout.json"))


def threshold(reg: Registry) -> float:
    return max(3.0, reg.threshold_for_next(UNIVERSE, new_tests=1))


def spec(reg: Registry) -> dict:
    return {"program": PID, "version": VERSION, "universe": UNIVERSE,
            "question": "does holding an energy future only while contract 2 is above contract 3 earn a positive net "
                        "return, and more than holding it always, at a swap-free CFD's costs?",
            "series": {k: list(v[1]) for k, v in SERIES.items()}, "signal": "12 * ln(C2/C3) > 0 at month m-1's last "
            "priced day; long contract 2 to month m's last priced day; flat otherwise",
            "weights": {"target_vol": TARGET_VOL, "max_weight": MAX_W, "vol_months": VOL_MONTHS,
                        "min_vol_months": MIN_VOL_MONTHS, "divided_by": "the number of energies with data"},
            "cost_bp_one_way": COST_BP, "roll": "one way more each month a position is held", "cost_grid": COST_GRID,
            "financing": "none (a swap-free CFD account)",
            "periods": {"judged": [str(d) for d in JUDGE], "development": [str(d) for d in DEV],
                        "validation": [str(d) for d in VAL], "holdout": [str(d) for d in HOLD]},
            "permutations": {"n": PERMUTATIONS, "seed": PERM_SEED},
            "bootstrap": {"n": BOOT_N, "seed": BOOT_SEED, "block_months": BOOT_BLOCK},
            "gates": GATES, "holdout_rule": HOLDOUT_RULE, "threshold_t": round(threshold(reg), 4)}


def _registered(reg: Registry) -> dict:
    frozen = json.loads(SPEC.read_text())
    if spec_sha(frozen["spec"]) != frozen["sha256"]:
        raise SystemExit(f"{SPEC} was edited after it was frozen")
    if reg.get(PID).design.get("spec_sha256") != frozen["sha256"] or code_hash() != frozen["code_sha256"]:
        raise SystemExit("the spec or the code differs from what was registered")
    return frozen


def cmd_spec() -> None:
    reg = _registry()
    if any(t.id == PID for t in reg.trials):
        raise SystemExit(f"{PID} is registered; its spec is frozen")
    s = spec(reg)
    SPEC.parent.mkdir(parents=True, exist_ok=True)
    SPEC.write_text(_dump({"spec": s, "sha256": spec_sha(s), "code_sha256": code_hash()}))
    print(spec_sha(s), "code", code_hash(), "threshold", s["threshold_t"])


def cmd_preregister(now: datetime) -> None:
    reg = _registry()
    frozen = json.loads(SPEC.read_text())
    if spec_sha(spec(reg)) != frozen["sha256"] or code_hash() != frozen["code_sha256"]:
        raise SystemExit("the spec or the code differs from what was frozen")
    text = (ROOT / DOC).read_text()
    if frozen["sha256"] not in text or frozen["code_sha256"] not in text:
        raise SystemExit(f"{DOC} must quote the spec and code sha256")
    reg.register(Trial(id=PID, registered=now, title="ENG-1: the energy futures term-structure premium, swap-free",
                       hypothesis="Does holding WTI, heating oil, RBOB and natural gas futures only while contract 2 is "
                                  "above contract 3 earn a positive net return, and more than holding them always?",
                       uses=(Use(UNIVERSE, date(1985, 1, 1), JUDGE[1], "judge"),), tests=1, configurations=1,
                       preregistration=DOC, design={"spec_sha256": frozen["sha256"], "code_sha256": frozen["code_sha256"],
                                                    "threshold_t": frozen["spec"]["threshold_t"]}))
    print("registered", PID)


def _write(name: str, body: dict) -> dict:
    body = json.loads(json.dumps(body, sort_keys=True, default=str))
    body["sha256"] = hashlib.sha256(json.dumps(body, sort_keys=True).encode()).hexdigest()
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / f"{name}.json").write_text(_dump(body))
    return body


def cmd_judge(now: datetime) -> None:
    reg = _registry()
    if reg.verdict_of(PID) is not None:
        raise SystemExit(f"{PID} already has a verdict")
    frozen = _registered(reg)
    curves, bdays = load(JUDGE[1])  # nothing from 2019 on is read
    lg = legs(curves, bdays, JUDGE[1])
    res = evaluate(lg, JUDGE, frozen["spec"]["threshold_t"])
    a = res["all"]
    verdict = "PASSED" if res["passed"] else "FAILED"
    body = _write(PID, {"program": PID, "verdict": verdict, "spec_sha256": frozen["sha256"],
                        "code_sha256": frozen["code_sha256"], "periods": frozen["spec"]["periods"], **res,
                        "months": {"n": a.get("months"), "mean": a.get("mean"), "t": a.get("t")},
                        "worst_fall": (a.get("worst_fall_pct") or 0) / 100, "by_year": a.get("by_year"),
                        "data": json.loads((DATA / "manifest.json").read_text())})
    reg.record_verdict(Verdict(PID, now, verdict, {"artifact": f"research/knowledge/{PID}.json",
                                                    "artifact_sha256": body["sha256"]}))
    print(f"{PID} {verdict}: {a['months']} months, {a['a_year_pct']:+.2f}% a year net, Sharpe {a['sharpe']}, t {a['t']} "
          f"against {res['threshold_t']}; failed: {res['failed_gates']}")


def cmd_holdout(now: datetime) -> None:
    reg = _registry()
    v = reg.verdict_of(PID)
    if v is None or v.status != "PASSED":
        raise SystemExit(f"{PID} has not passed: its holdout stays unread")
    if any(t.id == HPID for t in reg.trials):
        raise SystemExit(f"{HPID} is registered already: the holdout is read once")
    reg.register(Trial(id=HPID, registered=now, title="ENG-1 holdout: 2019-01..2024-03",
                       hypothesis="Does ENG-1's book, unchanged, earn a positive net return over 2019-01..2024-03?",
                       uses=(Use(UNIVERSE, HOLD[0], HOLD[1], "judge"),), tests=1, configurations=1,
                       preregistration=DOC, design={"rule": HOLDOUT_RULE}))
    curves, bdays = load(HOLD[1])
    lg = legs(curves, bdays, HOLD[1])
    rows = book(lg, HOLD)
    main, x2 = summary(rows), summary(book(lg, HOLD, k=2.0))
    present = {n for r in rows for n in r["exposure"]} | {n for n in lg if any(HOLD[0] <= date(*mo, 1) < HOLD[1]
                                                                                 for mo in lg[n])}
    gates = {"mean": (main.get("mean") or 0) > 0, "costs_x2": (x2.get("mean") or 0) > 0,
             "complete": present == set(SERIES)}
    verdict = "PASSED" if all(gates.values()) else "FAILED"
    body = _write(HPID, {"program": HPID, "holdout_of": PID, "verdict": verdict, "rule": HOLDOUT_RULE,
                         "all": main, "costs_x2": {k: x2.get(k) for k in ("mean", "t", "a_year_pct")},
                         "gates": gates, "failed_gates": [g for g, ok in gates.items() if not ok],
                         "months": {"n": main.get("months"), "mean": main.get("mean"), "t": main.get("t")}})
    reg.record_verdict(Verdict(HPID, now, verdict, {"artifact": f"research/knowledge/{HPID}.json",
                                                     "artifact_sha256": body["sha256"]}))
    print(f"{HPID} {verdict}: {main.get('months')} months, {main.get('a_year_pct')}% a year, t {main.get('t')}")


def main() -> int:
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    now = datetime.now(timezone.utc).replace(microsecond=0)
    if cmd == "fetch":
        cmd_fetch(now)
    elif cmd == "spec":
        cmd_spec()
    elif cmd == "preregister":
        cmd_preregister(now)
    elif cmd == "judge":
        cmd_judge(now)
    elif cmd == "holdout":
        cmd_holdout(now)
    else:
        print(__doc__)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
