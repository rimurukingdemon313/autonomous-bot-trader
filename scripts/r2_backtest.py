"""Round 2's two strategies on every trade they could have made: a DESCRIPTIVE backtest, not a test.

The owner asked on 2026-11-22 to see, without flattery, whether the new strategies make money when applied to every
possible trade. This runs SCX-1 (stablecoins at the weekend) and KRP-1 (the Korean coin premium) on the whole of
their data, 2018 to October 2026, at every threshold, every cost level and several holding periods, with the frozen
study code imported unchanged (never edited), and writes every figure, the losing rows with the winning ones.

It is not a test and cannot change a verdict: SCX-1 and KRP-1 FAILED as registered. These tables have many rows, so
some look good by chance; a row picked for being the best is a fit to the past, not an edge. The run reads KRP-1's
validation months (2025-03 to 2026-10), which no study had read: from now on they are spent for the Korean-premium
family. Nothing here trades, nothing is registered, and the registry is not touched.

    python scripts/r2_backtest.py run --out research/results   # on GitHub's runner: the data hosts are not
                                                               # reachable from the research session
"""

from __future__ import annotations

import argparse
import copy
import json
import math
import sys
from datetime import date, datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from aitrader.research.dlab.feeds import checked, get  # noqa: E402
from aitrader.research.events import korea as K  # noqa: E402
from aitrader.research.events import stablecoin as C  # noqa: E402
from aitrader.research.events.cascade import nw_t  # noqa: E402
import scripts.krp1 as K1  # noqa: E402  (the frozen study: its fetch and its spec, read, never changed)
import scripts.scx1 as S1  # noqa: E402
import scripts.sqz1 as Z  # noqa: E402

R2BT_VERSION = "r2-backtest-1.0.0"
SCX_WINDOW = ("2018-12-16", "2026-10-25")  # every Sunday the archive's monthly files cover
KRP_WINDOW = ("2018-01-01", "2026-10-29")  # development and validation, and the week between them
SCX_THETAS = (0.0001, 0.0003, 0.0005, 0.001, 0.002, 0.005)  # 1 bp is every Sunday off par: the tick is 1 bp
SCX_REGISTERED = 0.001
SCX_FILL_BP = (0.0, 0.5, 1.0, 2.0, 5.0, 10.0)  # 1 bp a fill was the study's; 10 bp is Binance's standard fee
KRP_THETAS = (0.02, 0.03, 0.05, 0.10, 0.20)
KRP_REGISTERED = 0.05
KRP_COSTS = (0.0, 0.002, 0.004, 0.006, 0.010)  # a round trip, both legs; 0.6% was the study's
KRP_HOLDS = (6, 24, 72, 168)
CAPITAL = 10_000.0
KRP_ALLOC = 0.10  # each position takes 10% of the equity at its entry, against an equal short of bitcoin
KRP_MAX_OPEN = 10
WEEKDAYS = ("Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday")
LABEL = ("DESCRIPTIVE BACKTEST, NOT A TEST: it cannot change a verdict (SCX-1 and KRP-1 FAILED as registered); a row "
         "chosen for being the best is a fit to the past, not an edge")


# ── figures ─────────────────────────────────────────────────────────────────

def summary(pairs: list[tuple[str, float]], lag: int = 1) -> dict:
    """(cohort, return) pairs: the mean over cohorts of each cohort's mean, as the studies average it, with its
    Newey-West t; and per trade, the count, mean, median, positive share, sum (each trade one unit), worst, best."""
    if not pairs:
        return {"n": 0}
    acc: dict[str, list[float]] = {}
    for k, x in pairs:
        acc.setdefault(k, []).append(x)
    m, t = nw_t([sum(v) / len(v) for _, v in sorted(acc.items())], lag)
    xs = sorted(x for _, x in pairs)
    return {"n": len(xs), "cohorts": len(acc), "mean": m, "t": t, "per_trade_mean": sum(xs) / len(xs),
            "median": xs[len(xs) // 2], "positive_share": sum(x > 0 for x in xs) / len(xs), "sum": sum(xs),
            "worst": xs[0], "best": xs[-1]}


def by_key(evs: list[dict], key, value, cost: float) -> dict[str, dict]:
    """Per group (a year, a pair, a coin): the count, the mean before costs and after `cost`, the sum after it."""
    acc: dict[str, list[float]] = {}
    for e in evs:
        acc.setdefault(str(key(e)), []).append(value(e))
    return {k: {"n": len(v), "mean_gross": sum(v) / len(v), "mean_net": sum(v) / len(v) - cost,
                "sum_net": sum(v) - cost * len(v)} for k, v in sorted(acc.items())}


def drawdown(curve: list[float]) -> float:
    peak, worst = -math.inf, 0.0
    for x in curve:
        peak = max(peak, x)
        worst = min(worst, x / peak - 1)
    return worst


def years_between(a: str, b: str) -> float:
    return max((date.fromisoformat(b) - date.fromisoformat(a)).days / 365.25, 1e-9)


def growth(start: float, end: float, years: float) -> float | None:
    return (end / start) ** (1 / years) - 1 if end > 0 else None


# ── SCX-1: every Sunday swap ────────────────────────────────────────────────

def compound_weekly(evs: list[dict], cost: float, window: tuple[str, str]) -> dict:
    """$10,000 held in stablecoins; each traded Sunday splits it equally over that Sunday's swaps (simple return
    exp(gross) - 1, less the round trip), and the weeks compound. Weeks without a swap earn nothing here (the
    stablecoins themselves pay no interest)."""
    acc: dict[str, list[float]] = {}
    for e in evs:
        acc.setdefault(e["day"], []).append(math.expm1(e["gross"]) - cost)
    eq, curve = CAPITAL, [CAPITAL]
    for _, v in sorted(acc.items()):
        eq *= 1 + sum(v) / len(v)
        curve.append(eq)
    yrs = years_between(*window)
    return {"start": CAPITAL, "end": eq, "return": eq / CAPITAL - 1, "per_year": growth(CAPITAL, eq, yrs),
            "weeks_traded": len(acc), "years": yrs, "max_drawdown": drawdown(curve)}


def scx_rows(bars: dict[str, dict[int, float]], window: tuple[str, str] = SCX_WINDOW) -> dict:
    a, b = window
    sundays = C.weekdays_in(a, b, 6)
    out: dict = {"window": [a, b], "pairs": sorted(bars), "entry": "Sunday 22:00 UTC close, exit 23 hours later",
                 "thetas": {}, "weekdays_at_10bp": {}}
    for th in SCX_THETAS:
        evs = [e for e in C.entries(bars, sundays, 22, 23, th, 0.0) if not e.get("missing")]
        row = {"gross": summary([(e["day"], e["gross"]) for e in evs]), "net": {}}
        for f in SCX_FILL_BP:
            row["net"][f"{f:g}bp_a_fill"] = summary([(e["day"], e["gross"] - 2 * f / 1e4) for e in evs])
        row["by_year_at_1bp_a_fill"] = by_key(evs, lambda e: e["day"][:4], lambda e: e["gross"], 2e-4)
        row["by_pair_at_1bp_a_fill"] = by_key(evs, lambda e: e["pair"], lambda e: e["gross"], 2e-4)
        row["equity_at_1bp_a_fill"] = compound_weekly(evs, 2e-4, window)
        row["equity_at_10bp_a_fill"] = compound_weekly(evs, 2e-3, window)
        out["thetas"][f"{th:g}"] = row
        if th == SCX_REGISTERED:
            out["registered_rule_trades"] = [{"pair": e["pair"], "day": e["day"], "delta": e["delta"],
                                              "gross": e["gross"]} for e in evs]
    for wd, name in enumerate(WEEKDAYS):  # the same rule on every day of the week: does Sunday stand apart?
        evs = [e for e in C.entries(bars, C.weekdays_in(a, b, wd), 22, 23, SCX_REGISTERED, 0.0) if not e.get("missing")]
        out["weekdays_at_10bp"][name] = {"gross": summary([(e["day"], e["gross"]) for e in evs]),
                                         "net_at_1bp_a_fill": summary([(e["day"], e["gross"] - 2e-4) for e in evs])}
    return out


# ── KRP-1: every premium trade ──────────────────────────────────────────────

def krp_spec(hold: int, lag: int = 1) -> dict:
    s = copy.deepcopy(K1.SPEC)
    s["hold_hours"], s["lag_hours"], s["cost_round_trip"] = hold, lag, 0.0
    return s


def any_entries(p: K.Panel, days: list[str], theta: float, sign: int, spec: dict,
                series: dict[str, dict[str, float]]) -> list[dict]:
    """Every eligible coin-day whose premium of the sign reaches theta (|rho| within the cap), fresh or not, one
    position per coin at a time: all the trades the premium offered, not only the registered fresh spikes."""
    out = []
    for c in p.coins:
        if c in K.EXCLUDED:
            continue
        s, busy = series.get(c, {}), -1
        for d in days:
            t_in = K.ms_of(d) + K.DAY + (spec["lag_hours"] - 1) * K.HOUR
            r = s.get(d)
            if t_in <= busy or r is None or abs(r) > spec["rho_cap"] or sign * r < theta or not K.eligible(p, c, d, spec):
                continue
            e = K.trade(p, c, d, spec["lag_hours"], spec["hold_hours"], 0.0)
            e["rho"] = r
            out.append(e)
            busy = t_in + spec["hold_hours"] * K.HOUR - 1
    return out


def simulate(evs: list[dict], hold: int, cost: float, window: tuple[str, str], lag: int = 1) -> dict:
    """$10,000; each trade takes 10% of the realized equity at its entry, long the coin against an equal short of
    bitcoin, and books (excess - cost) of that at its exit; at most 10 open at once (later entries are skipped).
    Exits are booked before entries at the same hour."""
    events = []
    for i, e in enumerate(evs):
        t_in = K.ms_of(e["day"]) + K.DAY + (lag - 1) * K.HOUR
        events += [(t_in, 1, i), (t_in + hold * K.HOUR, 0, i)]
    eq, curve, open_, alloc, taken, skipped, wins = CAPITAL, [CAPITAL], set(), {}, 0, 0, 0
    for t, kind, i in sorted(events):
        if kind == 1:
            if len(open_) >= KRP_MAX_OPEN:
                skipped += 1
                continue
            open_.add(i)
            alloc[i] = KRP_ALLOC * eq
            taken += 1
        elif i in open_:
            open_.discard(i)
            pnl = alloc.pop(i) * (evs[i]["excess"] - cost)
            wins += pnl > 0
            eq += pnl
            curve.append(eq)
    yrs = years_between(*window)
    return {"start": CAPITAL, "end": eq, "return": eq / CAPITAL - 1, "per_year": growth(CAPITAL, eq, yrs),
            "trades_taken": taken, "skipped_at_the_cap": skipped, "won": wins, "years": yrs,
            "max_drawdown": drawdown(curve)}


def krp_row(evs: list[dict], hold: int, window: tuple[str, str]) -> dict:
    row = {"gross": summary([(e["day"], e["excess"]) for e in evs]),
           "unhedged_coin": summary([(e["day"], e["ret"]) for e in evs]), "net": {}}
    for c in KRP_COSTS:
        row["net"][f"{c:g}"] = summary([(e["day"], e["excess"] - c) for e in evs])
    row["by_year_at_0.6%"] = by_key(evs, lambda e: e["day"][:4], lambda e: e["excess"], 0.006)
    coins = by_key(evs, lambda e: e["coin"], lambda e: e["excess"], 0.006)
    ranked = sorted(coins.items(), key=lambda kv: kv[1]["sum_net"])
    row["coins"] = len(coins)
    row["worst_coins_at_0.6%"] = dict(ranked[:5])
    row["best_coins_at_0.6%"] = dict(ranked[-5:])
    row["equity_at_0.6%"] = simulate(evs, hold, 0.006, window)
    row["equity_at_0.2%"] = simulate(evs, hold, 0.002, window)
    return row


def krp_rows(p: K.Panel, window: tuple[str, str] = KRP_WINDOW) -> dict:
    a, b = window
    days = K.days_between(a, b)
    look = K.days_with_lookback(days, K1.SPEC["trailing_days"])
    series = {c: K.rho_series(p, c, look) for c in p.coins}
    out: dict = {"window": [a, b], "coins_in_panel": len(p.coins),
                 "entry": "an hour after the 00:00 UTC close; long the coin on Binance spot, short bitcoin",
                 "fresh": {}, "any_premium": {}, "korean_discounts": {}, "late_entry_2h": {}}
    for hold in KRP_HOLDS:
        spec = krp_spec(hold)
        for th in KRP_THETAS:
            key = f"{th:g}@{hold}h"
            fresh = [e for e in K.entries(p, days, th, +1, spec, series=series) if not e.get("missing")]
            out["fresh"][key] = krp_row(fresh, hold, window)
            if hold == 24:
                anyp = [e for e in any_entries(p, days, th, +1, spec, series) if not e.get("missing")]
                out["any_premium"][key] = krp_row(anyp, hold, window)
                disc = [e for e in K.entries(p, days, th, -1, spec, series=series) if not e.get("missing")]
                out["korean_discounts"][key] = krp_row(disc, hold, window)
                late = [e for e in K.entries(p, days, th, +1, krp_spec(hold, lag=2), series=series)
                        if not e.get("missing")]
                out["late_entry_2h"][key] = {"gross": summary([(e["day"], e["excess"]) for e in late]),
                                             "net_at_0.6%": summary([(e["day"], e["excess"] - 0.006) for e in late])}
                if th == KRP_REGISTERED:
                    out["registered_rule_trades"] = [{"coin": e["coin"], "day": e["day"], "rho": e["rho"],
                                                      "excess": e["excess"], "ret": e["ret"]} for e in fresh]
    return out


# ── the run ─────────────────────────────────────────────────────────────────

def fetch_scx(probe_file: Path, fetch=checked) -> tuple[dict, dict, str]:
    a, b = SCX_WINDOW
    last_ms = C.ms_of(b) + (22 + 23) * C.HOUR  # the last exit's close
    months = Z._months(Z._add_months(a[:7], -1), datetime.fromtimestamp((last_ms - 1) / 1000, timezone.utc).date().isoformat())
    bars, man = S1.fetch_stage(json.loads(probe_file.read_text())["pairs"], months, fetch)
    if man["failed"]:
        raise SystemExit(f"{len(man['failed'])} SCX-1 archive files did not arrive (the first: {man['failed'][:3]}): "
                         "nothing is reported on a partial panel")
    return S1.firewall(bars, last_ms), man, datetime.fromtimestamp(last_ms / 1000, timezone.utc).isoformat()


def fetch_krp(probe_file: Path, fetch_up=get, fetch_bn=checked) -> tuple[K.Panel, dict]:
    pr = json.loads(probe_file.read_text())
    saved = K1.SPEC
    K1.SPEC = {**copy.deepcopy(saved), "stages": {**copy.deepcopy(saved["stages"]),
                                                  "full": {"decisions": list(KRP_WINDOW)}}}
    try:  # the study's own fetch, on the whole window; its module and its file stay as they were
        panel, man = K1.fetch_stage(pr["coins"], pr["btc_1h"], "full", fetch_up, fetch_bn)
    finally:
        K1.SPEC = saved
    if man["failed"] or man["upbit_failed"]:
        raise SystemExit(f"{len(man['failed'])} archive files and {len(man['upbit_failed'])} Upbit markets did not "
                         f"arrive (the first: {(man['failed'] + man['upbit_failed'])[:3]}): nothing is reported on a "
                         "partial panel")
    if not panel.upbit.get("BTC"):
        raise SystemExit("Upbit's bitcoin candles did not arrive: no premium can be measured")
    return panel, man


def run(out_dir: Path, now: datetime, fetch_scx_fn=checked, fetch_up=get, fetch_bn=checked,
        scx_probe: Path = S1.PROBE, krp_probe: Path = K1.PROBE) -> dict:
    bars, sman, s_last = fetch_scx(scx_probe, fetch_scx_fn)
    panel, kman = fetch_krp(krp_probe, fetch_up, fetch_bn)
    body = {"what": LABEL, "version": R2BT_VERSION, "run_at": now.isoformat(),
            "spends": "KRP-1's validation months, 2025-03 to 2026-10, are read here for the first time: they are spent "
                      "for the Korean-premium family",
            "scx": {**scx_rows(bars), "data": {"files": sman["files"], "absent": len(sman["absent"]),
                                               "last_moment_read": s_last}},
            "krp": {**krp_rows(panel), "data": {"binance_files": kman["files"], "binance_absent": len(kman["absent"]),
                                                "upbit_markets": kman["upbit_markets"],
                                                "upbit_absent": len(kman["upbit_absent"]),
                                                "last_moment_read": datetime.fromtimestamp(
                                                    (panel.t0 + panel.n * K.HOUR) / 1000, timezone.utc).isoformat()}}}
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "ROUND2-full-backtest.json").write_text(json.dumps(body, indent=1, sort_keys=True, default=str) + "\n")
    (out_dir / "ROUND2-full-backtest.md").write_text(markdown(body))
    return body


# ── the report ──────────────────────────────────────────────────────────────

def _bp(x) -> str:
    return "" if x is None else f"{x * 1e4:+.1f} bp"


def _pc(x, d: int = 2) -> str:
    return "" if x is None else f"{x * 100:+.{d}f}%"


def _t(x) -> str:
    return "" if x is None else f"{x:.2f}"


def _usd(x) -> str:
    return "" if x is None else f"${x:,.0f}"


def markdown(b: dict) -> str:
    s, k = b["scx"], b["krp"]
    o = ["# Round 2's strategies on every possible trade", "", f"**{b['what']}.** {b['spends']}.", "",
         f"Run {b['run_at']} ({b['version']}). Every row is in `research/results/ROUND2-full-backtest.json`, with every "
         "trade of the two registered rules.", "",
         f"## SCX-1: stablecoins at the weekend ({s['window'][0]} to {s['window'][1]})", "",
         f"{s['entry']}; {s['data']['files']} archive files, {s['data']['absent']} absent; pairs: "
         f"{', '.join(s['pairs'])}.", "",
         "| Threshold | Swaps | Weeks | Gross a swap | t (gross) | Net at 1 bp a fill | t | Net at 10 bp a fill | "
         "$10,000 at 1 bp a fill | Worst fall |", "|---|---|---|---|---|---|---|---|---|---|"]
    for th, r in s["thetas"].items():
        g, n1, n10, eq = r["gross"], r["net"]["1bp_a_fill"], r["net"]["10bp_a_fill"], r["equity_at_1bp_a_fill"]
        if not g.get("n"):
            o.append(f"| {float(th) * 1e4:g} bp | 0 | | | | | | | | |")
            continue
        o.append(f"| {float(th) * 1e4:g} bp{' (registered)' if float(th) == SCX_REGISTERED else ''} | {g['n']} | "
                 f"{g['cohorts']} | {_bp(g['mean'])} | {_t(g['t'])} | {_bp(n1['mean'])} | {_t(n1['t'])} | "
                 f"{_bp(n10['mean'])} | {_usd(eq['end'])} ({_pc(eq['per_year'])} a year) | {_pc(eq['max_drawdown'])} |")
    o += ["", "The same rule at 10 bp on every day of the week (22:00 UTC, 23 hours):", "",
          "| Day | Swaps | Gross a swap | t | Net at 1 bp a fill |", "|---|---|---|---|---|"]
    for d, r in s["weekdays_at_10bp"].items():
        g = r["gross"]
        o.append(f"| {d} | {g.get('n', 0)} | {_bp(g.get('mean'))} | {_t(g.get('t'))} | "
                 f"{_bp(r['net_at_1bp_a_fill'].get('mean'))} |")
    reg = s["thetas"][f"{SCX_REGISTERED:g}"]
    o += ["", "The registered rule (10 bp) by year, at 1 bp a fill:", "", "| Year | Swaps | Gross | Net | Sum of nets |",
          "|---|---|---|---|---|"]
    for y, r in reg["by_year_at_1bp_a_fill"].items():
        o.append(f"| {y} | {r['n']} | {_bp(r['mean_gross'])} | {_bp(r['mean_net'])} | {_bp(r['sum_net'])} |")
    o += ["", f"## KRP-1: the Korean coin premium ({k['window'][0]} to {k['window'][1]})", "",
          f"{k['entry']}; {k['data']['binance_files']} archive files ({k['data']['binance_absent']} absent), "
          f"{k['data']['upbit_markets']} Upbit markets ({k['data']['upbit_absent']} absent), "
          f"{k['coins_in_panel']} coins.", "",
          "Fresh spikes (the registered rule's kind), every threshold and hold:", "",
          "| Threshold, hold | Trades | Days | Gross a trade (vs bitcoin) | t (gross) | Net at 0.6% | t | Net at 0.2% | "
          "$10,000 at 0.6% | at 0.2% | Worst fall at 0.6% |", "|---|---|---|---|---|---|---|---|---|---|---|"]
    for key, r in k["fresh"].items():
        o.append(_krp_line(key, r))
    for name, title in (("any_premium", "Every premium day, fresh or not (24 hours)"),
                        ("korean_discounts", "Korean discounts instead (the contrast; 24 hours)")):
        o += ["", f"{title}:", "", "| Threshold, hold | Trades | Days | Gross a trade (vs bitcoin) | t (gross) | "
              "Net at 0.6% | t | Net at 0.2% | $10,000 at 0.6% | at 0.2% | Worst fall at 0.6% |",
              "|---|---|---|---|---|---|---|---|---|---|---|"]
        for key, r in k[name].items():
            o.append(_krp_line(key, r))
    regk = k["fresh"][f"{KRP_REGISTERED:g}@24h"]
    o += ["", "The registered rule (5%, 24 hours) by year, at 0.6% a round trip:", "",
          "| Year | Trades | Gross | Net | Sum of nets |", "|---|---|---|---|---|"]
    for y, r in regk["by_year_at_0.6%"].items():
        o.append(f"| {y} | {r['n']} | {_pc(r['mean_gross'])} | {_pc(r['mean_net'])} | {_pc(r['sum_net'], 1)} |")
    o += ["", "Read it as a description. The registered rows were judged once, on their own stages, and failed; the "
          "others were never registered, and the best of many rows is expected to look good by chance.", ""]
    return "\n".join(o)


def _krp_line(key: str, r: dict) -> str:
    g, n6, n2 = r["gross"], r["net"]["0.006"], r["net"]["0.002"]
    if not g.get("n"):
        return f"| {key} | 0 | | | | | | | | | |"
    e6, e2 = r["equity_at_0.6%"], r["equity_at_0.2%"]
    th, hold = key.split("@")
    tag = " (registered)" if float(th) == KRP_REGISTERED and hold == "24h" else ""
    return (f"| {float(th) * 100:g}%, {hold}{tag} | {g['n']} | {g['cohorts']} | {_pc(g['mean'])} | {_t(g['t'])} | "
            f"{_pc(n6['mean'])} | {_t(n6['t'])} | {_pc(n2['mean'])} | {_usd(e6['end'])} | {_usd(e2['end'])} | "
            f"{_pc(e6['max_drawdown'])} |")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("command", choices=("run",))
    ap.add_argument("--out", default=str(ROOT / "research" / "results"))
    args = ap.parse_args(argv)
    body = run(Path(args.out), datetime.now(timezone.utc))
    reg_s = body["scx"]["thetas"][f"{SCX_REGISTERED:g}"]["net"]["1bp_a_fill"]
    reg_k = body["krp"]["fresh"][f"{KRP_REGISTERED:g}@24h"]["net"]["0.006"]
    print(json.dumps({"scx_registered_net_1bp": reg_s, "krp_registered_net_0.6%": reg_k}, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(main())
