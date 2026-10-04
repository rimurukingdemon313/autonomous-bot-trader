"""TOM-D: diagnostics of RC-EQ's E1 turn-of-the-month candidate (research/preregistrations/TOM-D.md).

Descriptive only: the frozen rule rc.tom(k_pre=1, k_post=3) is decomposed and stressed on the data
already used (universe A 1990-2020, universe B 1990-2026). Nothing here is a test; no variant can
be validated by it. Runs on a GitHub runner (.github/workflows/tom-diag.yml):

    python scripts/tom_diag.py fetch    # universes A and B from Yahoo (A is never loaded after 2020)
    python scripts/tom_diag.py spec | preregister
    python scripts/tom_diag.py run      # research/results/TOM-D.json, TOM-D-trades-A.csv, TOM-D-trades-B.csv
"""

from __future__ import annotations

import csv
import hashlib
import itertools
import json
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

import rc_eq  # noqa: E402
from aitrader.research.discovery import rc, retail, tomdiag  # noqa: E402
from aitrader.research.registry import Registry, Trial, Use  # noqa: E402

R = ROOT / "research"
PID = "TOM-D"
DOC = "research/preregistrations/TOM-D.md"
SPEC = R / "specs" / "TOM-D.json"
OUT = R / "results"
CODE = ("aitrader/research/discovery/tomdiag.py", "scripts/tom_diag.py", *rc_eq.CODE)
A_PERIOD = rc_eq.JUDGE  # 1990-01 -> 2020-12; A is never loaded after 2020
B_PERIOD = rc_eq.B_PERIOD  # 1990-01 -> 2026-09
SPLIT = date(2009, 1, 1)
ORIGINAL = {"k_pre": 1, "k_post": 3}
NEIGHBOURHOOD = {"original": (1, 3), "entry_one_day_earlier": (2, 3), "entry_one_day_later": (0, 3),
                 "exit_one_day_earlier": (1, 2), "exit_one_day_later": (1, 4)}
COST_GRID = (1.0, 1.25, 1.5, 2.0, 3.0)
#: classification fixed before any result: MSCI market classification (Israel developed since 2010)
EMERGING_B = ("IND50", "KOR200", "MEX35", "BRA60", "MYS30", "IDN")
MAJOR = ("US500", "NAS100", "JPN225", "UK100", "GER40", "FRA40", "AUS200", "EU50")  # 2 bp-spread CFDs
POOLED_PERIOD = A_PERIOD  # A and B together only where both exist: 1990-2020


def code_hash() -> str:
    h = hashlib.sha256()
    for p in CODE:
        h.update((ROOT / p).read_bytes())
    return h.hexdigest()


def spec() -> dict:
    return {"program": PID, "kind": "diagnostic", "rule": "rc.tom", "original": ORIGINAL,
            "neighbourhood": NEIGHBOURHOOD, "cost_grid": COST_GRID, "split": str(SPLIT),
            "periods": {"A": [str(d) for d in A_PERIOD], "B": [str(d) for d in B_PERIOD],
                        "pooled": [str(d) for d in POOLED_PERIOD]},
            "universes": {"A": list(rc_eq.UNIVERSE_A), "B": list(rc_eq.UNIVERSE_B), "emerging_b": EMERGING_B,
                          "major": MAJOR},
            "weightings": ["equal (the rule)", "inverse volatility, 60 daily returns (diagnostic variant)"],
            "costs": rc_eq.COSTS.__dict__,
            "versions": {"retail": retail.RETAIL_VERSION, "rc": rc.RC_VERSION, "tomdiag": tomdiag.TOMDIAG_VERSION}}


def spec_sha(s: dict) -> str:
    return hashlib.sha256(json.dumps(s, sort_keys=True).encode()).hexdigest()


def _dump(x) -> str:
    return json.dumps(x, indent=1, sort_keys=True, default=str) + "\n"


def cmd_fetch():
    for tag, uni in (("A3", rc_eq.UNIVERSE_A), ("B2", rc_eq.UNIVERSE_B)):
        for k, v in rc_eq._fetch(uni, tag).items():
            print(tag, k, v["first"], v["last"], v["rows"])


def cmd_spec():
    reg = Registry.load(R / "registry.jsonl")
    if any(t.id == PID for t in reg.trials):
        raise SystemExit(f"{PID} is registered; its plan is frozen")
    s = spec()
    SPEC.write_text(_dump({"spec": s, "sha256": spec_sha(s), "code_sha256": code_hash()}))
    print(spec_sha(s))


def cmd_preregister(now):
    # The universe-B seal was spent by RC-EQ2-H; this trial re-reads spent data descriptively (role
    # "select", 0 tests), so it is registered without a holdout guard: there is nothing left to guard.
    reg = Registry.load(R / "registry.jsonl")
    frozen = json.loads(SPEC.read_text())
    if spec_sha(spec()) != frozen["sha256"] or code_hash() != frozen["code_sha256"]:
        raise SystemExit("the plan or the code changed since `spec`")
    if frozen["sha256"] not in (ROOT / DOC).read_text():
        raise SystemExit(f"{DOC} must quote the spec sha256")
    reg.register(Trial(id=PID, registered=now, title="TOM-D: diagnostics of the turn-of-the-month candidate (descriptive)",
                       hypothesis="none: decomposition, decay, cost, calendar, universe and weighting diagnostics of "
                                  "RC-EQ's E1 TOM on data already used",
                       uses=(Use("multi-asset-long", A_PERIOD[0], A_PERIOD[1], "select"),
                             Use("multi-asset-etf", date(2008, 1, 1), A_PERIOD[1], "select"),
                             Use("equity-index-b", B_PERIOD[0], B_PERIOD[1], "select")),
                       tests=0, configurations=len(NEIGHBOURHOOD) + len(COST_GRID) + 2, preregistration=DOC,
                       design={"spec_sha256": frozen["sha256"], "code_sha256": frozen["code_sha256"]}))
    print("registered", PID)


# ── analysis ────────────────────────────────────────────────────────────

def _sim(days, closes, universe, rates, targets, costs=rc_eq.COSTS):
    return retail.simulate(days, closes, targets, rc_eq.instruments(universe), lambda k, d: rates.at(k, d), costs)


def _sub(closes, names):
    return {n: closes[n] for n in names}


def _uni(universe, names):
    return {n: universe[n] for n in names}


def headline(res, period) -> dict:
    s = retail.summarize(res, *period)
    keep = ("n", "annual_return", "annual_vol", "t", "sharpe", "sortino", "max_drawdown", "max_drawdown_compounded",
            "profit_factor", "win_rate", "trades", "trades_per_year", "expectancy_bps_per_unit", "gross_annual",
            "trading_cost_annual", "financing_annual", "net_annual", "time_in_market", "avg_gross_exposure",
            "turnover_annual", "median_holding_days", "profit_factor_months")
    out = {k: s.get(k) for k in keep}
    out["cagr"] = tomdiag.cagr(res.dates, res.net(), *period)
    return out


def analyse(tag, days, closes, universe, rates, period) -> dict:
    n = len(universe)
    tg = rc.tom(days, closes, n, **ORIGINAL)
    res = _sim(days, closes, universe, rates, tg)
    bench = _sim(days, closes, universe, rates, tg, rc_eq.COSTS.frictionless())
    ledger = [r for r in tomdiag.trade_ledger(res, closes, rc_eq.instruments(universe), rc_eq.COSTS, bench)
              if period[0] <= date.fromisoformat(r["exit"]) < period[1]]
    years = len(retail.monthly(res.dates, res.net(), *period)) / 12.0
    pre, post = (period[0], SPLIT), (SPLIT, period[1])

    def led(p):
        return [r for r in ledger if p[0] <= date.fromisoformat(r["exit"]) < p[1]]

    def yrs(p):
        return len(retail.monthly(res.dates, res.net(), *p)) / 12.0

    out = {"headline": {"full": headline(res, period), "pre_2009": headline(res, pre), "post_2009": headline(res, post)},
           "components_annual": {"full": tomdiag.components(ledger, years), "pre_2009": tomdiag.components(led(pre), yrs(pre)),
                                 "post_2009": tomdiag.components(led(post), yrs(post))}}
    # contributions (net, fraction of equity, summed over the period)
    by_index = {k: round(sum(r["net"] for r in ledger if r["instrument"] == k), 5) for k in universe}
    by_index_gross = {k: round(sum(r["gross"] for r in ledger if r["instrument"] == k), 5) for k in universe}
    by_year: dict = {}
    by_month: dict = {}
    for r in ledger:
        y, m = int(r["entry"][:4]), int(r["entry"][5:7])
        by_year[y] = by_year.get(y, 0.0) + r["net"]
        by_month[m] = by_month.get(m, 0.0) + r["net"]
    total = sum(r["net"] for r in ledger)
    out["contributions"] = {"by_index_net": by_index, "by_index_gross": by_index_gross,
                            "by_year_net": {k: round(v, 5) for k, v in sorted(by_year.items())},
                            "by_entry_month_net": {k: round(v, 5) for k, v in sorted(by_month.items())},
                            "total_net": round(total, 5)}
    out["concentration"] = {"indices": tomdiag.concentration(by_index, total),
                            "years": tomdiag.concentration(by_year, total),
                            "best_10pct_trades_share": tomdiag.top_trades_share(ledger, 0.10),
                            "trades": len(ledger), "winning_trades": sum(r["net"] > 0 for r in ledger)}
    # leave out one and two indices (re-simulated with the same 1/N sizing)
    names = list(universe)
    loo = {}
    for k in names:
        rest = [m for m in names if m != k]
        loo[k] = headline(_sim(days, closes, universe, rates, {m: tg[m] for m in rest}), period)
    pair = []
    for a, b in itertools.combinations(names, 2):
        rest = [m for m in names if m not in (a, b)]
        h = headline(_sim(days, closes, universe, rates, {m: tg[m] for m in rest}), period)
        pair.append((h.get("t") or 0.0, a, b, h.get("annual_return")))
    pair.sort()
    out["leave_out"] = {"one": {k: {"annual_return": v["annual_return"], "t": v["t"]} for k, v in loo.items()},
                        "worst_pairs": [{"removed": [a, b], "t": t, "annual_return": ar} for t, a, b, ar in pair[:5]],
                        "pairs_tested": len(pair), "pairs_with_net_le_zero": sum(1 for _, _, _, ar in pair if (ar or 0) <= 0)}
    # cost grid (same rule, every cost x k)
    grid = {}
    for k in COST_GRID:
        r = _sim(days, closes, universe, rates, tg, rc_eq.COSTS.stressed(k))
        h = headline(r, period)
        hp = headline(r, post)
        grid[f"x{k:g}"] = {**{x: h[x] for x in ("cagr", "annual_return", "sharpe", "t", "max_drawdown_compounded",
                                                  "profit_factor")},
                          "post_2009_annual": hp["annual_return"], "post_2009_t": hp["t"]}
    out["cost_grid"] = grid
    comp = out["components_annual"]["full"]
    netA = comp["net"]
    out["breakeven"] = {
        "markup_pa": tomdiag.breakeven(netA, comp["markup"], rc_eq.COSTS.index_markup_pa),
        "all_cost_multiplier": tomdiag.breakeven(netA, comp["spread"] + comp["slippage"] + comp["markup"], 1.0),
        "post_2009_markup_pa": tomdiag.breakeven(out["components_annual"]["post_2009"]["net"],
                                                  out["components_annual"]["post_2009"]["markup"], rc_eq.COSTS.index_markup_pa),
        "mean_benchmark_pct_while_held": _held_benchmark(res, bench, ledger)}
    # calendar neighbourhood
    nb = {}
    for label, (kp, kq) in NEIGHBOURHOOD.items():
        t2 = rc.tom(days, closes, n, k_pre=kp, k_post=kq)
        r = _sim(days, closes, universe, rates, t2)
        b2 = _sim(days, closes, universe, rates, t2, rc_eq.COSTS.frictionless())
        nb[label] = {"k_pre": kp, "k_post": kq, "full": headline(r, period), "post_2009": headline(r, post),
                     "before_broker_full": headline(b2, period)}
    out["calendar_neighbourhood"] = nb
    # weighting
    iv = tomdiag.inverse_vol(tg, closes)
    rv = _sim(days, closes, universe, rates, iv)
    out["weighting"] = {"equal": out["headline"]["full"], "inverse_vol": headline(rv, period),
                        "inverse_vol_post_2009": headline(rv, post), "equal_post_2009": out["headline"]["post_2009"]}
    # holding-time economics
    dr_pre = tomdiag.day_returns(days, closes, *pre)
    dr_post = tomdiag.day_returns(days, closes, *post)
    td = [r["trading_days"] for r in ledger]
    cd = [r["calendar_days"] for r in ledger]
    fin = [(r["benchmark"] + r["markup"]) / r["weight"] for r in ledger if r["weight"]]
    out["holding"] = {"mean_trading_days": round(float(np.mean(td)), 3), "median_trading_days": float(np.median(td)),
                      "mean_calendar_days": round(float(np.mean(cd)), 3), "median_calendar_days": float(np.median(cd)),
                      "exposure_days_per_year_per_index": round(sum(cd) / years / n, 2),
                      "financing_bps_per_trade_per_unit": round(float(np.mean(fin)) * 1e4, 2),
                      "markup_bps_per_calendar_day": round(rc_eq.COSTS.index_markup_pa / 360 * 100, 3),
                      "day_returns_pre_2009": dr_pre, "day_returns_post_2009": dr_post,
                      "day_returns_full": tomdiag.day_returns(days, closes, *period)}
    # decay diagnostics
    out["decay"] = _decay(days, closes, universe, rates, res, ledger, period)
    out["bootstrap"] = {lab: tomdiag.bootstrap_mean_ci([v for _, v in retail.monthly(res.dates, res.net(), *p)])
                        for lab, p in (("full", period), ("pre_2009", pre), ("post_2009", post))}
    out["adverse_excursion"] = tomdiag.adverse_excursion(ledger, closes, days)
    out["calendar_handling"] = _calendar(days, closes, period)
    out["_ledger"] = ledger
    return out


def _held_benchmark(res, bench, ledger) -> float | None:
    """Mean benchmark rate (percent) paid while positions were held, recovered from the frictionless run."""
    b = -sum(r["benchmark"] for r in ledger)
    notional_days = sum(r["weight"] * r["calendar_days"] for r in ledger)
    return round(b / notional_days * 360 * 100, 3) if notional_days else None


def _decay(days, closes, universe, rates, res, ledger, period) -> dict:
    out = {}
    # rolling five-year blocks: TOM days minus other days, gross, pooled over indices
    blocks = []
    y0 = period[0].year
    while y0 < period[1].year:
        a, b = date(y0, 1, 1), min(date(y0 + 5, 1, 1), period[1])
        d = tomdiag.day_returns(days, closes, a, b)
        blocks.append({"from": str(a), "to": str(b), **(d["difference"] or {}), "tom_mean_bps": d["tom_days"]["mean_bps"],
                       "other_mean_bps": d["other_days"]["mean_bps"]})
        y0 += 5
    out["five_year_blocks"] = blocks
    # per index: gross price return per trade, before and after 2009
    per = {}
    for k in universe:
        pre = [r["price_return"] for r in ledger if r["instrument"] == k and date.fromisoformat(r["exit"]) < SPLIT]
        post = [r["price_return"] for r in ledger if r["instrument"] == k and date.fromisoformat(r["exit"]) >= SPLIT]
        per[k] = {"pre_bps": round(float(np.mean(pre)) * 1e4, 2) if pre else None, "pre_n": len(pre),
                  "post_bps": round(float(np.mean(post)) * 1e4, 2) if post else None, "post_n": len(post)}
    out["per_index_price_return_per_trade"] = per
    # regimes at entry: benchmark rate below 1% (zero-rate policy) and trailing volatility vs its own past median
    def bucket(pred):
        xs = [r["price_return"] for r in ledger if pred(r)]
        return {"mean_bps": round(float(np.mean(xs)) * 1e4, 2) if xs else None, "n": len(xs)}

    rate_at = {}
    for r in ledger:
        rate_at[(r["instrument"], r["entry"])] = rates.at(universe[r["instrument"]][1], date.fromisoformat(r["entry"]))
    out["by_benchmark_rate"] = {"below_1pct": bucket(lambda r: rate_at[(r["instrument"], r["entry"])] < 1.0),
                                "at_least_1pct": bucket(lambda r: rate_at[(r["instrument"], r["entry"])] >= 1.0)}
    vol = _entry_vol(days, closes, ledger)
    out["by_entry_volatility"] = {"above_own_past_median": bucket(lambda r: vol.get((r["instrument"], r["entry"])) is True),
                                  "below_own_past_median": bucket(lambda r: vol.get((r["instrument"], r["entry"])) is False)}
    # anticipation: the profile of relative days -5..+6 before and after 2009 is in holding.day_returns_*
    return out


def _entry_vol(days, closes, ledger) -> dict:
    """(instrument, entry) -> whether the 60-day volatility at entry is above the median of its own
    earlier entries' volatility (expanding, causal); None before 10 earlier entries."""
    pos = {str(d): i for i, d in enumerate(days)}
    valid = {k: np.array([j for j in range(len(c)) if np.isfinite(c[j])]) for k, c in closes.items()}
    out, hist = {}, {}
    for r in sorted(ledger, key=lambda x: x["entry"]):
        c = closes[r["instrument"]]
        v_idx = valid[r["instrument"]]
        k = int(np.searchsorted(v_idx, pos[r["entry"]], "right"))
        if k < 61:
            continue
        seg = c[v_idx[k - 61:k]]
        v = float(np.std(np.diff(np.log(seg)), ddof=1))
        h = hist.setdefault(r["instrument"], [])
        out[(r["instrument"], r["entry"])] = (v > float(np.median(h))) if len(h) >= 10 else None
        h.append(v)
    return out


def _calendar(days, closes, period) -> dict:
    """How often the data's last trading day of a month is not the month's last weekday (a holiday
    or a vendor gap): the windows the exchange calendar shifts."""
    shifted = months = 0
    for c in closes.values():
        idx = [j for j in range(len(c)) if np.isfinite(c[j]) and period[0] <= days[j] < period[1]]
        last: dict = {}
        for j in idx:
            last[(days[j].year, days[j].month)] = days[j]
        for (y, m), d in last.items():
            months += 1
            e = date(y + (m == 12), m % 12 + 1, 1)
            lw = e - timedelta(days=1)
            while lw.weekday() >= 5:
                lw -= timedelta(days=1)
            shifted += d != lw
    return {"instrument_months": months, "last_trading_day_not_last_weekday": shifted,
            "share": round(shifted / months, 4) if months else None}


def _universes(closes_a, closes_b):
    dev_b = [k for k in rc_eq.UNIVERSE_B if k not in EMERGING_B]
    allu = {**rc_eq.UNIVERSE_A, **rc_eq.UNIVERSE_B}
    sets = {"all_26": list(allu), "developed": list(rc_eq.UNIVERSE_A) + dev_b, "major_8": list(MAJOR),
            "a_only": list(rc_eq.UNIVERSE_A), "b_only": list(rc_eq.UNIVERSE_B), "b_developed": dev_b,
            "b_emerging": list(EMERGING_B)}
    for m in MAJOR:
        sets[f"all_26_without_{m}"] = [k for k in allu if k != m]
    return allu, sets


def cmd_run(now):
    reg = Registry.load(R / "registry.jsonl")
    frozen = json.loads(SPEC.read_text())
    if reg.get(PID).design.get("spec_sha256") != frozen["sha256"] or frozen["code_sha256"] != code_hash():
        raise SystemExit("the plan or the code differs from what was registered")
    rates = rc.Rates(rc_eq.DATA / "policy_rates.csv")
    da, ca, rep_a = rc_eq.load(rc_eq.UNIVERSE_A, A_PERIOD[1])
    db, cb, rep_b = rc_eq.load(rc_eq.UNIVERSE_B, B_PERIOD[1])
    body = {"program": PID, "kind": "diagnostic", "spec_sha256": frozen["sha256"],
            "data": {"cleaning_A": rep_a, "cleaning_B": rep_b,
                     "fetch": {t: json.loads((rc_eq.DATA / f"fetch_manifest_{t}.json").read_text()) for t in ("A3", "B2")}}}
    for tag, (d, c, u, p) in {"A": (da, ca, rc_eq.UNIVERSE_A, A_PERIOD), "B": (db, cb, rc_eq.UNIVERSE_B, B_PERIOD)}.items():
        res = analyse(tag, d, c, u, rates, p)
        ledger = res.pop("_ledger")
        with open(OUT / f"TOM-D-trades-{tag}.csv", "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(ledger[0]))
            w.writeheader()
            for r in ledger:
                w.writerow({k: (round(v, 7) if isinstance(v, float) else v) for k, v in r.items()})
        body[tag] = res
        h = res["headline"]
        print(tag, json.dumps(h["full"]), "\n  post-2009", json.dumps(h["post_2009"]), flush=True)
    # universes pooled over 1990-2020 (A is not loaded after 2020)
    series = {}
    for uni, (dd, cc) in ((rc_eq.UNIVERSE_A, (da, ca)), (rc_eq.UNIVERSE_B, (db, cb))):
        for k in uni:
            idx = [j for j in range(len(cc[k])) if np.isfinite(cc[k][j])]
            series[k] = ([dd[j] for j in idx], [cc[k][j] for j in idx])
    days, closes = rc.panel(series, rc_eq.LOAD_FROM, POOLED_PERIOD[1])
    allu, sets = _universes(ca, cb)
    subs = {}
    for name, members in sets.items():
        u = {k: allu[k] for k in members}
        cl = {k: closes[k] for k in members}
        tg = rc.tom(days, cl, len(u), **ORIGINAL)
        r = _sim(days, cl, u, rates, tg)
        subs[name] = {"members": len(members), "full": headline(r, POOLED_PERIOD),
                      "post_2009": headline(r, (SPLIT, POOLED_PERIOD[1]))}
        print(name, subs[name]["full"]["annual_return"], subs[name]["full"]["t"], flush=True)
    body["universes_1990_2020"] = subs
    (OUT / "TOM-D.json").write_text(_dump(body))
    print("written research/results/TOM-D.json")


def main() -> int:
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    now = datetime.now(timezone.utc)
    {"fetch": cmd_fetch, "spec": cmd_spec, "preregister": lambda: cmd_preregister(now),
     "run": lambda: cmd_run(now)}.get(cmd, lambda: print(__doc__))()
    return 0


if __name__ == "__main__":
    sys.exit(main())
