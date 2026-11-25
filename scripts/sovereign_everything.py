"""The owner's SOVEREIGN package tried on everything (asked on 2026-11-25: "try it on everything"; docs/SOVEREIGN.md).

    python3 -B scripts/sovereign_everything.py <package.py> <history_dir> <history_extra_dir or -> <out.json>

DESCRIPTIVE BACKTEST, NOT A TEST. It registers nothing and validates nothing; the best of many rows is expected to
look good by chance. It runs the owner's own engines, built by the package's own factories and never edited, through
the red team's accounting (scripts/sovereign_redteam.py: a close's target earns the next day, every unit traded pays
the cost, the backtest's two-step shield apart from the live layer, a prop firm's rules on the day's adverse
extremes), from 2008-01-04 to 2026-11-20:

Part 1, every knob the specification names, on its seven funds: SOVEREIGN-TITAN-MAX at the seven settings of its
section 3.3 (the funded and the eval modes among them), SOVEREIGN-TITAN-7 and SEC-TSMOM-4 in both risk modes; each
started on five successive days (the five-tranche rebalance's phase); at 0, 8 and 16 bps; on time and one day late;
with and without the live layer.

Part 2, every market the owner trades, added in steps to the same rules (each at the package's funded settings):
E1 bitcoin from its first Yahoo bar in IBIT's place; E2 and ether; E3 and the index CFDs GER40, UK100, JP225 and
HK50; E4 and copper (CPER) and natural gas (UNG). An added market takes its sector's place in the package's own
sector map and a cap stated below; the package's file is not touched (a fresh copy of the module is extended in
memory for each step). A market's bar is the last one dated on or before the US session's day (a local holiday
leaves it flat); before its first bar it is held flat, so it is never selected and earns nothing. Index CFDs are
taken in their own currency's returns, with no conversion.

The package's drawdown brake, for every rule of both parts (added 2026-11-25, after the first run showed a rule
ending with more at 16 bps than at 8): how many days the brake held the account at half size or a quarter, and the
same weights with the brake held off (the drawdown handed to the shield pinned at zero) at 8 and 16 bps, with their
worst fall and the one-year windows that break a prop firm's rules. A diagnostic of what the brake does, never a
variant to trade: without it the account takes the falls the brake exists to stop.
"""

from __future__ import annotations

import json
import sys
import types
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts import sovereign_redteam as rt

LABEL = ("DESCRIPTIVE BACKTEST, NOT A TEST: the owner's own code on real daily bars at every setting it names and on "
         "the other markets the owner trades; it validates nothing, and the best of many rows is expected to look "
         "good by chance")
#: the specification's section 3.3, in its order: fast_d, slow_d, vol_core (the second is the funded mode, the fourth
#: the eval mode)
PARAM_ROWS = ((12, 28, 0.0175), (15, 35, 0.0175), (18, 42, 0.0175), (15, 35, 0.0155), (15, 35, 0.0185),
              (12, 35, 0.0175), (18, 35, 0.0175))
OFFSETS = (0, 1, 2, 3, 4)
COSTS = (0.0, 8.0, 16.0)
CORE = ("QQQ", "SPY", "IWM", "GLD", "SLV", "USO")
#: an added market: (the series it is read from, its sector in the package's map, its cap). Caps: an index takes
#: QQQ's and IWM's 0.55; ether IBIT's 0.25; copper GLD's 0.30; natural gas SLV's 0.12, the package's cap for a
#: gap-prone market.
ADDED = {"ETH": ("ETH-USD", "CRYPTO", 0.25), "GER40": ("^GDAXI", "EQUITY", 0.55), "UK100": ("^FTSE", "EQUITY", 0.55),
         "JP225": ("^N225", "EQUITY", 0.55), "HK50": ("^HSI", "EQUITY", 0.55), "COPPER": ("CPER", "METALS", 0.30),
         "NATGAS": ("UNG", "ENERGY", 0.12)}
STEPS = (("E1: bitcoin from 2014 in IBIT's place", ()),
         ("E2: E1 and ether", ("ETH",)),
         ("E3: E2 and GER40, UK100, JP225, HK50", ("ETH", "GER40", "UK100", "JP225", "HK50")),
         ("E4: E3 and copper and natural gas", ("ETH", "GER40", "UK100", "JP225", "HK50", "COPPER", "NATGAS")))


def engines(M) -> list[tuple[str, callable]]:
    """Every engine the package names, each from its own factory."""
    out = []
    for f, s, v in PARAM_ROWS:
        out.append((f"SOVEREIGN-TITAN-MAX {f}d/{s}d/{v}",
                    lambda f=f, s=s, v=v: M.make_titan_fusion(vol_core=v, fast_d=f, slow_d=s, eq_short_mode="bear05",
                                                              metal_short_mode="guard90")))
    for name in ("SOVEREIGN-TITAN-7", "SEC-TSMOM-4"):
        for mode in ("funded", "eval"):
            out.append((f"{name} {mode}", lambda name=name, mode=mode: M.STRATEGY_REGISTRY[name](risk_mode=mode)))
    return out


def weights_of(factory, px: dict, assets: list[str], offset: int = 0) -> np.ndarray:
    """The engine run day by day from day `offset` (its five-tranche phase shifts with it); rows before are zero."""
    n = len(px["days"])
    ds = {a: px["c"][a][offset:] for a in assets}
    m = n - offset
    rets = {a: [0.0] + [ds[a][i] / ds[a][i - 1] - 1.0 for i in range(1, m)] for a in assets}
    eng, st = factory(), {}
    W = np.zeros((n, len(assets)))
    for t in range(m):
        w = eng(ds, rets, assets, t, 1.0, st)
        W[offset + t] = [w[a] for a in assets]
    return W


def fail_share(M, W, px, assets, i0: int, i1: int, step: int = 21) -> dict:
    starts = list(range(i0, i1 - 252, step))
    fails = sum(1 for s in starts if rt.prop(rt.replay(M, W, px, assets, s, s + 252, 8.0))["first_failure"])
    return {"starts": len(starts), "failed_within_a_year": fails, "share": fails / len(starts) if starts else None}


def unbraked(M):
    """The package's own shield handed a drawdown of zero, so its two-step brake never engages (its intraday exit,
    which the backtest does not use, is unchanged). The package's module is not touched."""
    return types.SimpleNamespace(apply_prop_shield=lambda w, current_drawdown=0.0, intraday_pnl_pct=0.0:
                                 M.apply_prop_shield(w, 0.0, intraday_pnl_pct))


def brake(M, W, px, assets, i0, i1) -> dict:
    """What the brake did to one weight path: the share of days it held the account at half size or less (a drawdown
    of 5%) and at a quarter (7.5%), at 8 bps; and the same weights with the brake held off."""
    book = rt.replay(M, W, px, assets, i0, i1, 8.0)
    eq = np.array([book["capital"]] + [r["equity"] for r in book["rows"]])
    dd = (eq / np.maximum.accumulate(eq) - 1.0)[:-1]  # the drawdown each day's target was set with
    N = unbraked(M)
    keep = ("profit", "t", "max_dd_intraday", "worst_day", "mean_gross")
    off = {f"{int(c)}bp": {k: v for k, v in rt.summary(rt.replay(N, W, px, assets, i0, i1, c)).items() if k in keep}
           for c in (8.0, 16.0)}
    return {"days_at_half_or_less": float(np.mean(dd <= -0.05)), "days_at_a_quarter": float(np.mean(dd <= -0.075)),
            "mean_gross_with_brake": rt.summary(book)["mean_gross"], "brake_off": off,
            "brake_off_prop_one_year_windows": fail_share(N, W, px, assets, i0, i1)}


def evaluate(M, W, px, assets, i0, i1, reg, costs=COSTS, prop_starts=True) -> dict:
    """One weight path: the continuous account at each cost, one day late, with the live layer, its regimes."""
    out = {f"{int(c)}bp": rt.summary(rt.replay(M, W, px, assets, i0, i1, c)) for c in costs}
    out["8bp_one_day_late"] = rt.summary(rt.replay(M, W, px, assets, i0, i1, 8.0, delay=1))
    out["8bp_live_layer"] = rt.summary(rt.replay(M, W, px, assets, i0, i1, 8.0, live_layer=True))
    out["regimes_8bp"] = {p: rt.summary(rt.replay(M, W, px, assets, a, b, 8.0))["profit"] for p, (a, b) in reg.items()}
    if prop_starts:
        out["prop_one_year_windows"] = fail_share(M, W, px, assets, i0, i1)
        out["brake"] = brake(M, W, px, assets, i0, i1)
    return out


def span(px: dict) -> tuple[int, int, dict]:
    reg = rt.regimes(px["days"])
    return reg["2008-2013"][0], reg["2025-2026"][1], reg


def part1(M, px: dict, assets: list[str]) -> dict:
    i0, i1, reg = span(px)
    out = {}
    for label, factory in engines(M):
        rows = {}
        for k in OFFSETS:
            W = weights_of(factory, px, assets, k)
            rows[f"start+{k}"] = evaluate(M, W, px, assets, i0, i1, reg, prop_starts=(k == 0))
        out[label] = rows
    return out


# ── the other markets ─────────────────────────────────────────────────

def aligned(raw_series: dict, days: list[str]) -> tuple[list, list, list, list, list]:
    """A market's adjusted bars on the core days: the last bar dated on or before each day; flat at its first close
    before its first bar. Returns c, o, h, l and whether the day has the market's own bar."""
    keys = sorted(raw_series)
    base_row = raw_series[keys[0]]
    base = base_row["c"] * ((base_row["adj"] / base_row["c"]) if base_row.get("adj") else 1.0)
    rows = []  # (c, o, h, l, own bar)
    j = -1
    for d in days:
        while j + 1 < len(keys) and keys[j + 1] <= d:
            j += 1
        if j < 0:  # before its first bar: flat, never selected, earns nothing
            rows.append((base, base, base, base, False))
            continue
        row = raw_series[keys[j]]
        f = (row["adj"] / row["c"]) if row.get("adj") else 1.0
        cc = row["c"] * f
        if keys[j] == d:
            rows.append((cc, (row["o"] or row["c"]) * f, (row["h"] or row["c"]) * f, (row["l"] or row["c"]) * f, True))
        else:  # a day the market did not trade: flat at its last close
            rows.append((cc, cc, cc, cc, False))
    c, o, h, lo, own = (list(x) for x in zip(*rows))
    return c, o, h, lo, own


def wide_panel(raw_core: dict, raw_extra: dict, added: tuple, last: str = rt.LAST) -> tuple[dict, list[str]]:
    """The six core funds on their common days, bitcoin in IBIT's place, and the added markets."""
    px = rt.panel({a: raw_core[a] for a in CORE}, list(CORE), last=last)
    days = px["days"]
    # bitcoin trades every day: its bar for a US session's day is that UTC day's close, aligned like any other market
    for a, series in [("IBIT", "BTC-USD")] + [(a, ADDED[a][0]) for a in added]:
        c, o, h, lo, own = aligned(raw_extra[series], days)
        px["c"][a], px["o"][a], px["h"][a], px["l"][a], px["live"][a] = c, o, h, lo, own
    return px, list(CORE) + ["IBIT"] + list(added)


def extended_module(pkg: str, added: tuple):
    """A fresh copy of the package's module whose sector map and caps also name the added markets. The file on disk
    is not touched, and no other copy sees the change."""
    M = rt.load_package(pkg)
    for a in added:
        M.SECTORS[a] = ADDED[a][1]
        M.TAIL_CAPS[a] = ADDED[a][2]
    return M


def split(M, W, px, assets, i0, i1) -> dict:
    """Where the profit came from: the same decisions with the crypto positions removed, and the crypto positions alone
    (each through the same shield, so the two need not add up to the whole)."""
    crypto = [j for j, a in enumerate(assets) if M.SECTORS[a] == "CRYPTO"]
    no_c, only_c = W.copy(), np.zeros_like(W)
    no_c[:, crypto] = 0.0
    only_c[:, crypto] = W[:, crypto]
    out = {}
    for label, X in (("without crypto", no_c), ("crypto only", only_c)):
        sm = rt.summary(rt.replay(M, X, px, assets, i0, i1, 8.0))
        out[label] = {"profit": sm["profit"], "t": sm["t"]}
    return out


def part2(pkg: str, raw_core: dict, raw_extra: dict) -> dict:
    out = {}
    for label, added in STEPS:
        M = extended_module(pkg, added)
        px, assets = wide_panel(raw_core, raw_extra, added)
        i0, i1, reg = span(px)
        rows = {}
        for name in M.STRATEGY_REGISTRY:
            W = weights_of(lambda name=name, M=M: M.STRATEGY_REGISTRY[name](risk_mode="funded"), px, assets)
            ev = evaluate(M, W, px, assets, i0, i1, reg, costs=(8.0, 16.0))
            ev["share_of_days_holding"] = {a: float(np.mean(np.abs(W[i0:i1, j]) > 1e-9)) for j, a in enumerate(assets)}
            ev["split_8bp"] = split(M, W, px, assets, i0, i1)
            rows[name] = ev
        out[label] = {"assets": assets, "first_bars": {a: px["days"][px["live"][a].index(True)]
                                                       if True in px["live"][a] else None for a in assets},
                      "rules": rows}
    return out


def run(pkg: str, hist: Path, hist_extra: Path | None) -> dict:
    M = rt.load_package(pkg)
    assets = list(M.SECTORS)
    raw = rt.load_history(hist, assets)
    px = rt.panel(raw, assets)
    R = {"label": LABEL, "package": pkg, "from": rt.START, "to": rt.LAST, "days": len(px["days"]),
         "manifest": json.loads((hist / "manifest.json").read_text())["series"],
         "part1": part1(M, px, assets)}
    if hist_extra is not None:
        from scripts.sovereign_data import EXTRA, file_name
        raw_extra = {s: json.loads((hist_extra / f"{file_name(s)}.json").read_text()) for s in EXTRA}
        R["manifest_extra"] = json.loads((hist_extra / "manifest.json").read_text())["series"]
        R["added"] = {a: {"series": v[0], "sector": v[1], "cap": v[2]} for a, v in ADDED.items()}
        R["part2"] = part2(pkg, raw, raw_extra)
    return R


def _m(x) -> str:
    return "n/a" if x is None else f"{x:+,.0f}".replace("+-", "-")


def _t(x) -> str:
    return "n/a" if x is None else f"{x:.2f}"


def _pct(x) -> str:
    return "n/a" if x is None else f"{x * 100:.0f}%"


def _row(label: str, r: dict) -> str:
    b = r["8bp"]
    regs = r["regimes_8bp"]
    zero = f" {_m(r['0bp']['profit'])} |" if "0bp" in r else ""
    t = _t(b.get("t"))
    fail = r.get("prop_one_year_windows", {}).get("share")
    return (f"| {label} |{zero} {_m(b['profit'])} | {_m(r['16bp']['profit'])} | "
            f"{_m(r['8bp_one_day_late']['profit'])} | {t} | {b['max_dd_intraday'] * 100:.1f}% | "
            f"{b['worst_day'] * 100:.1f}% | {_m(regs['2025-2026'])} | {sum(1 for v in regs.values() if v > 0)}/5 | "
            f"{_pct(fail)} | {r['8bp_live_layer']['stopped_from'] or 'never'} |")


HEAD = ("| Rule | Before costs | 8 bps | 16 bps | 8 bps, a day late | t at 8 bps | Worst fall | Worst day | "
        "2025-2026 | Regimes won | One-year windows that break a prop firm's rules | The live layer stops it |\n"
        "|---|---|---|---|---|---|---|---|---|---|---|---|")
HEAD2 = HEAD.replace(" Before costs |", "").replace("|---|---|---|---|---|---|---|---|---|---|---|---|",
                                                     "|---|---|---|---|---|---|---|---|---|---|---|")
BRAKE_HEAD = ("| Rule | Days at half size or less | Days at a quarter | Mean exposure with the brake | Without the brake: "
              "8 bps | t | 16 bps | Worst fall | Worst day | Mean exposure | One-year windows that break a prop firm's "
              "rules |\n|---|---|---|---|---|---|---|---|---|---|---|")


def _brake_row(label: str, b: dict) -> str:
    o, o16 = b["brake_off"]["8bp"], b["brake_off"]["16bp"]
    return (f"| {label} | {_pct(b['days_at_half_or_less'])} | {_pct(b['days_at_a_quarter'])} | "
            f"{b['mean_gross_with_brake']:.2f} | {_m(o['profit'])} | {_t(o.get('t'))} | {_m(o16['profit'])} | "
            f"{o['max_dd_intraday'] * 100:.1f}% | {o['worst_day'] * 100:.1f}% | {o['mean_gross']:.2f} | "
            f"{_pct(b['brake_off_prop_one_year_windows']['share'])} |")


BRAKE_NOTE = ("The package's two-step brake halves every position once the account is 5% below its best close and "
              "quarters it at 7.5%. A row's brake columns: the share of days it held the account there (8 bps, "
              "continuous from 2008), and the same weights with the brake held off. The second half is a diagnostic "
              "of what the brake does, not a variant: its worst falls are what the brake exists to stop, and a prop "
              "firm's account would not survive them.")


def markdown(R: dict) -> str:
    L = ["# SOVEREIGN on everything: the owner's three rules at every setting and on every market", "",
         (f"**{R['label']}.** One $200,000 account from {R['from']} to {R['to']} for each row, the owner's own code "
          "(`research/external/sovereign/sovereign_top3_suite.py`, unchanged) through the red team's accounting "
          "(`scripts/sovereign_redteam.py`). Every figure is in `research/results/SOVEREIGN-everything.json`."), "",
         "## Part 1: every setting the specification names, on its seven funds", "", HEAD]
    for label, rows in R["part1"].items():
        L.append(_row(label, rows["start+0"]))
    spread = max(max(r["8bp"]["profit"] for r in rows.values()) - min(r["8bp"]["profit"] for r in rows.values())
                 for rows in R["part1"].values())
    same = spread <= 5.0
    L += ["", ("Started on each of five successive days, every rule ends within a dollar or two of the same figure: the "
               f"five-tranche rebalance is a five-day moving average of the daily target, whatever day it starts on "
               f"(the widest gap is ${spread:,.0f}). "
               "The specification's 'weekday grid' is not what its code does when it is run every day."
               if same else "Started on five successive days, the rules end on different figures (see the JSON)."), "",
          "### The drawdown brake", "", BRAKE_NOTE, "", BRAKE_HEAD]
    for label, rows in R["part1"].items():
        L.append(_brake_row(label, rows["start+0"]["brake"]))
    L.append("")
    if "part2" in R:
        added = ", ".join(f"{a} ({v['series']}, {v['sector'].lower()}, cap {v['cap']})" for a, v in R["added"].items())
        L += ["## Part 2: the same rules on the other markets the owner trades", "",
              (f"Each step adds to the one before; every rule at the package's funded settings. Added markets and "
               f"their caps: {added}."), ""]
        for label, step in R["part2"].items():
            firsts = ", ".join(f"{a} {d}" for a, d in step["first_bars"].items() if a not in CORE)
            L += [f"### {label}", "", f"First bars: {firsts}.", "", HEAD2]
            for name, r in step["rules"].items():
                L.append(_row(name, r))
            L += ["", "Where the profit came from, at 8 bps: " + "; ".join(
                f"{name} {_m(r['split_8bp']['without crypto']['profit'])} without its crypto positions, "
                f"{_m(r['split_8bp']['crypto only']['profit'])} from them alone" for name, r in step["rules"].items()) + ".", ""]
        L += ["### The drawdown brake on the other markets", "", BRAKE_NOTE, "", BRAKE_HEAD]
        for label, step in R["part2"].items():
            for name, r in step["rules"].items():
                L.append(_brake_row(f"{label.split(':')[0]} {name}", r["brake"]))
        L.append("")
    L += ["## How to read it", "",
          ("- A row is a description of the past, not a test. Among this many rows the best is expected to look good "
           "by chance; no row was registered, and none can be validated on these days, which are now read."),
          "- The bar a registered test must clear here is t 3.0. Read the t column against it.", ""]
    return "\n".join(L) + "\n"


def main(argv: list[str]) -> int:
    pkg, hist, extra, out = argv[0], Path(argv[1]), (None if argv[2] == "-" else Path(argv[2])), Path(argv[3])
    R = run(pkg, hist, extra)
    out.write_text(json.dumps(R, indent=1, sort_keys=True, default=str) + "\n")
    out.with_suffix(".md").write_text(markdown(R))
    for label, rows in R["part1"].items():
        p = [rows[k]["8bp"]["profit"] for k in rows]
        print(f"{label:36s} 8bp profit by start day: " + " ".join(f"{x:+,.0f}" for x in p))
    for label, step in R.get("part2", {}).items():
        print(label, {n: round(v["8bp"]["profit"]) for n, v in step["rules"].items()})
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))

