"""KRP-1: does a coin's Korean premium lift its global price the next day? (research/preregistrations/KRP-1.md)
Runs on GitHub's runner (.github/workflows/krp1.yml): neither Upbit nor Binance's archive is reachable from the
research director's session.

    python scripts/krp1.py probe [--out FILE]      # names and months only: which coins trade on both venues
    python scripts/krp1.py hash                    # the code and spec hashes the preregistration quotes
    python scripts/krp1.py preregister dev         # each later stage only after the one before PASSED
    python scripts/krp1.py run dev --data DIR      # fetch what the stage needs, judge it once, record the verdict

The traded instrument is the coin's SPOT, bought outright on Binance, against a short of bitcoin through a
swap-free CFD over the same hours: no leverage, no funding, one short sale (bitcoin's, stated). Upbit's prices are
information only. Nothing here trades.
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import quote

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from aitrader.research.dlab.feeds import checked, get  # noqa: E402
from aitrader.research.events import exfunding as X  # noqa: E402  (the archive's zip and CSV readers)
from aitrader.research.events import korea as K  # noqa: E402
import scripts.sqz1 as Z  # noqa: E402  (the S3 listing reader and the month helpers)
from aitrader.research.registry import Registry, Trial, Use, Verdict, bonferroni_t  # noqa: E402

R = ROOT / "research"
DOC = "research/preregistrations/KRP-1.md"
PROBE = R / "results" / "KRP-1-probe.json"
CODE = ("aitrader/research/events/korea.py", "aitrader/research/events/cascade.py", "scripts/krp1.py",
        "scripts/sqz1.py", "aitrader/research/events/exfunding.py")
BASE = "https://data.binance.vision/"
UPBIT_MARKETS = "https://api.upbit.com/v1/market/all?isDetails=false"
UPBIT_DAYS = "https://api.upbit.com/v1/candles/days?market={market}&count=200&to={to}"
UNIVERSE = "crypto-spot-korean-premium"
SPEC = {"program": "KRP-1", "version": K.KRP_VERSION, "universe": UNIVERSE,
        "instrument": "coin spot bought outright on Binance, short bitcoin through a swap-free CFD over the same hours",
        "thetas": [0.05, 0.10], "rho_cap": 1.0, "trailing_days": 30, "min_age_days": 30,
        "min_upbit_krw": 500_000_000, "min_binance_usd": 1_000_000, "lag_hours": 1, "late_hours": 2,
        "hold_hours": 24, "cost_round_trip": 0.006,  # 0.25% a side on the coin, 0.05% a side on the BTC CFD
        "placebo_span_days": 30, "placebo_draws_per_entry": 20, "placebos": 1000, "seed": 20261122, "nw_lag": 1,
        "bar_floor": 3.0, "upbit_lookback_days": 90,
        "gates": ["t", "costs_x2", "halves", "top5_removed", "late_entry", "beats_placebo", "without_best_day",
                  "without_best_coin", "beats_korean_discounts"],
        "stages": {
            "dev": {"trial": "KRP-1", "decisions": ["2018-01-01", "2025-02-28"], "tests": 2, "min_events": 150,
                    "min_days": 60},
            "validation": {"trial": "KRP-1-V", "after": "KRP-1", "decisions": ["2025-03-08", "2026-10-29"],
                           "tests": 1, "min_events": 80, "min_days": 30},
            "forward": {"trial": "KRP-1-F", "after": "KRP-1-V", "decisions": ["2026-12-01", "2027-05-29"],
                        "not_before": "2027-06-10", "tests": 1, "min_events": 30, "min_days": 10}}}


def code_hash() -> str:
    h = hashlib.sha256()
    for f in CODE:
        h.update((ROOT / f).read_bytes())
    return h.hexdigest()


def spec_sha() -> str:
    return hashlib.sha256(json.dumps(SPEC, sort_keys=True).encode()).hexdigest()


def registry() -> Registry:
    return Registry.load(R / "registry.jsonl")


def _status(reg: Registry, pid: str) -> str | None:
    return reg.status_of(pid) if any(t.id == pid for t in reg.trials) else None


def spot_url(symbol: str, month: str) -> str:
    q = quote(symbol, safe="")
    return f"{BASE}data/spot/monthly/klines/{q}/1h/{q}-1h-{month}.zip"


# ── the probe: names and months only ────────────────────────────────────────

def probe(fetch=get, now: datetime | None = None, delisted: list[str] | None = None) -> dict:
    """Every coin Upbit quotes in KRW (and any delisted code given), with the months of hourly Binance spot bars its
    USDT pair has. Names and file names only: no price is read."""
    now = now or datetime.now(timezone.utc)
    body = fetch(UPBIT_MARKETS)
    if body is None:
        raise RuntimeError("Upbit's market list did not arrive")
    listed = sorted({m["market"][4:] for m in json.loads(body) if str(m.get("market", "")).startswith("KRW-")})
    names = sorted(set(listed) | set(delisted or []))

    def months(c):
        keys = Z.listing(f"data/spot/monthly/klines/{c}USDT/1h/", fetch)[1]
        return c, sorted(k.rsplit("-1h-", 1)[1][:7] for k in keys if k.endswith(".zip") and "-1h-" in k)
    with ThreadPoolExecutor(max_workers=8) as pool:
        got = dict(pool.map(months, names + ["BTC"]))
    coins = {c: {"binance_1h": got[c], "upbit_listed_now": c in listed}
             for c in names if got.get(c) and c not in K.EXCLUDED}
    per_stage = {}
    for name, st in SPEC["stages"].items():
        a, b = st["decisions"]
        ms_ = set(Z._months(a, b))
        per_stage[name] = {"coins_with_binance_months": sum(1 for v in coins.values() if ms_ & set(v["binance_1h"])),
                           "btc_months": len(ms_ & set(got.get("BTC", []))), "months": len(ms_)}
    return {"retrieved": now.isoformat(), "what": "names and file names only: no price was read",
            "sources": [UPBIT_MARKETS, "https://data.binance.vision (S3 listing of data/spot/monthly/klines/*/1h/)"],
            "upbit_krw_markets_now": len(listed), "delisted_codes_tried": sorted(set(delisted or []) - set(listed)),
            "btc_1h": got.get("BTC", []), "coins": coins, "per_stage": per_stage}


# ── the stage ───────────────────────────────────────────────────────────────

def upbit_daily(market: str, first_day: str, last_day: str, fetch=get, pause: float = 0.12) -> dict | None:
    """{UTC day: (KRW close, KRW turnover)} of `market`'s daily candles from first_day to last_day, both included.
    Nothing after last_day is asked for (the `to` bound is exclusive). None if Upbit does not serve the market."""
    out: dict[str, tuple[float, float]] = {}
    to = (date.fromisoformat(last_day) + timedelta(days=1)).isoformat() + "T00:00:00Z"
    while True:
        try:
            body = fetch(UPBIT_DAYS.format(market=quote(market, safe=""), to=quote(to, safe="")))
        except RuntimeError as e:
            if "HTTP Error 400" in str(e) or "HTTP Error 404" in str(e):
                return None if not out else out
            raise
        if body is None:
            return None if not out else out
        rows = json.loads(body)
        if not isinstance(rows, list) or not rows:
            return out
        for r in rows:
            d = str(r.get("candle_date_time_utc", ""))[:10]
            if first_day <= d <= last_day:
                try:
                    out[d] = (float(r["trade_price"]), float(r["candle_acc_trade_price"]))
                except (KeyError, TypeError, ValueError):
                    continue
        oldest = min(str(r.get("candle_date_time_utc", "9999")) for r in rows)
        if oldest[:10] <= first_day or len(rows) < 200:
            return out
        to = oldest[:19] + "Z"
        time.sleep(pause)


def fetch_stage(coins: dict, btc_months: list[str], stage: str, fetch_up=get, fetch_bn=checked) -> tuple[K.Panel, dict]:
    st = SPEC["stages"][stage]
    a, b = st["decisions"]
    up_first = (date.fromisoformat(a) - timedelta(days=SPEC["upbit_lookback_days"])).isoformat()
    first_month = Z._add_months(a[:7], -2)
    t0 = K.ms_of(first_month + "-01")
    last_ms = K.ms_of(b) + K.DAY + (SPEC["late_hours"] + SPEC["hold_hours"]) * K.HOUR  # the last exit's close
    hours = (last_ms - t0) // K.HOUR
    months = Z._months(first_month, K.day_of_ms(last_ms - 1))
    panel = K.Panel(sorted(coins), t0, hours)
    man = {"files": 0, "absent": [], "failed": [], "upbit_markets": 0, "upbit_absent": [], "upbit_failed": []}
    for c, v in coins.items():
        if v["binance_1h"]:
            panel.first_binance[c] = K.ms_of(v["binance_1h"][0] + "-01")
    for c in sorted(coins) + ["BTC"]:  # Upbit's quotation API: one request at a time, inside its rate limit
        try:
            got = upbit_daily(f"KRW-{c}", up_first, b, fetch_up)
        except RuntimeError as e:
            man["upbit_failed"].append(f"{c}: {str(e)[:120]}")
            continue
        if got is None:
            man["upbit_absent"].append(c)
        else:
            man["upbit_markets"] += 1
            panel.put_upbit(c, got)
    jobs = [(c, m) for c in sorted(coins) for m in months if m in coins[c]["binance_1h"]] + \
           [("BTC", m) for m in months if m in btc_months]

    def one(job):
        c, m = job
        try:
            raw = fetch_bn(spot_url(f"{c}USDT", m))
        except RuntimeError as e:
            return job, None, str(e)[:160]
        return job, (X.parse_bars(X.rows(raw)) if raw is not None else None), None
    with ThreadPoolExecutor(max_workers=16) as pool:
        for (c, m), got, err in pool.map(one, jobs):
            if err:
                man["failed"].append(f"{c}:{m}")
            elif got is None:
                man["absent"].append(f"{c}:{m}")
            else:
                man["files"] += 1
                panel.put_hourly(c, got)
    return panel, man


def run(stage: str, data: Path, now: datetime, fetch_up=get, fetch_bn=checked, reg: Registry | None = None,
        out_dir: Path | None = None, probe_file: Path = PROBE) -> dict:
    reg = reg or registry()
    st = SPEC["stages"][stage]
    pid = st["trial"]
    out_dir = out_dir or R / "knowledge"
    if not any(t.id == pid for t in reg.trials):
        raise SystemExit(f"{pid} is not registered: nothing is fetched or judged before it is")
    if reg.status_of(pid) != "PENDING":
        raise SystemExit(f"{pid} already has a verdict: a stage is judged once")
    if "after" in st and _status(reg, st["after"]) != "PASSED":
        raise SystemExit(f"{pid} is judged only after {st['after']} passed")
    if now.date().isoformat() < st.get("not_before", ""):
        raise SystemExit(f"{pid} is judged on or after {st['not_before']}, when its archive is whole")
    design = reg.get(pid).design
    if design.get("code_sha256") != code_hash() or design.get("spec_sha256") != spec_sha():
        raise SystemExit(f"{pid}: the code or the spec differs from what was registered")
    pr = json.loads(probe_file.read_text())
    panel, man = fetch_stage(pr["coins"], pr["btc_1h"], stage, fetch_up, fetch_bn)
    if man["failed"] or man["upbit_failed"]:
        raise SystemExit(f"{len(man['failed'])} archive files and {len(man['upbit_failed'])} Upbit markets did not "
                         f"arrive (the first: {(man['failed'] + man['upbit_failed'])[:3]}): nothing is judged on a "
                         "partial panel; the next run asks again")
    if not panel.upbit.get("BTC"):
        raise SystemExit("Upbit's bitcoin candles did not arrive: no premium can be measured")
    a, b = st["decisions"]
    days = K.days_between(a, b)
    look = K.days_with_lookback(days, SPEC["trailing_days"])
    series = {c: K.rho_series(panel, c, look) for c in panel.coins}
    bar = max(SPEC["bar_floor"], bonferroni_t(max(1, reg.tests_on(UNIVERSE, date.fromisoformat(a),
                                                                  date.fromisoformat(b) + timedelta(days=1)))))
    cost = SPEC["cost_round_trip"]
    thetas = SPEC["thetas"] if stage == "dev" else [chosen_theta(out_dir)]
    results, kept = {}, {}
    for th in thetas:
        evs = K.entries(panel, days, th, +1, SPEC, series=series)
        late = K.entries(panel, days, th, +1, SPEC, lag_hours=SPEC["late_hours"], series=series)
        contra = K.entries(panel, days, th, -1, SPEC, series=series)
        plac = K.placebos(panel, evs, th, SPEC, series, SPEC["seed"], window=(a, b))
        results[str(th)] = K.judge(evs, late, contra, plac, bar, cost, st["min_events"], st["min_days"],
                                   SPEC["seed"], SPEC["placebos"], SPEC["nw_lag"])
        kept[str(th)] = evs
    passed = [th for th in thetas if results[str(th)]["verdict"] == "PASSED"]
    chosen = max(passed, key=lambda th: results[str(th)]["t"]) if passed else None
    verdict = "PASSED" if passed else ("INCONCLUSIVE" if all(r["verdict"] == "INCONCLUSIVE" for r in results.values())
                                       else "FAILED")
    body = {"program": pid, "stage": stage, "kind": "spot_event_study", "verdict": verdict, "judged": now.isoformat(),
            "code_sha256": code_hash(), "spec_sha256": spec_sha(), "spec": SPEC, "decisions": [a, b], "bar": bar,
            "chosen_theta": chosen if stage == "dev" else thetas[0],
            "last_moment_read": datetime.fromtimestamp((panel.t0 + panel.n * K.HOUR) / 1000, timezone.utc).isoformat(),
            "data": {"sources": [UPBIT_DAYS.split("?")[0], BASE], "binance_files": man["files"],
                     "binance_absent": len(man["absent"]), "upbit_markets": man["upbit_markets"],
                     "upbit_absent": man["upbit_absent"], "coins": len(panel.coins)},
            "results": results}
    out_dir.mkdir(parents=True, exist_ok=True)
    f = out_dir / f"{pid}.json"
    f.write_text(json.dumps(body, indent=1, sort_keys=True, default=str) + "\n")
    data.mkdir(parents=True, exist_ok=True)
    with gzip.open(data / f"{pid}-events.json.gz", "wt") as g:
        json.dump(kept, g)
    best = results[str(chosen)] if chosen is not None else max(
        results.values(), key=lambda r: r["t"] if r["t"] is not None else -1e9)
    reg.record_verdict(Verdict(pid, now, verdict, {
        "artifact": str(f.relative_to(ROOT)) if f.is_relative_to(ROOT) else str(f), "chosen_theta": body["chosen_theta"],
        "t": best["t"], "mean_net": best["mean_net"], "traded": best["traded"], "days": best["days"],
        "gates": best.get("gates"), "why": best.get("why")}))
    return body


def chosen_theta(out_dir: Path) -> float:
    art = json.loads((out_dir / "KRP-1.json").read_text())
    if art.get("verdict") != "PASSED" or art.get("chosen_theta") is None:
        raise SystemExit("the later stages use the threshold KRP-1 chose; KRP-1 has not passed")
    return float(art["chosen_theta"])


def preregister(stage: str, now: datetime) -> None:
    st = SPEC["stages"][stage]
    h = code_hash()
    doc = (ROOT / DOC).read_text()
    if h not in doc or spec_sha() not in doc:
        raise SystemExit(f"{DOC} must quote the code sha256 {h} and the spec sha256 {spec_sha()}")
    reg = registry()
    if "after" in st and _status(reg, st["after"]) != "PASSED":
        raise SystemExit(f"{st['trial']} is registered only after {st['after']} passed")
    a, b = st["decisions"]
    reg.register(Trial(
        id=st["trial"], registered=now, title=f"{st['trial']}: the Korean coin premium and the global price, {stage} stage",
        hypothesis="A coin whose price in bitcoin on Upbit stands at least theta above its price in bitcoin on Binance "
                   "at the 00:00 UTC close, after 30 days with the median gap below theta/2, bought on Binance spot an "
                   "hour later against a short of bitcoin and closed 24 hours after that, earns a positive net return "
                   "after 0.6% a round trip, averaged over days, more than the same coin on ordinary days and more than "
                   "Korean discounts of the same size.",
        uses=(Use(UNIVERSE, date.fromisoformat(a), date.fromisoformat(b) + timedelta(days=1), "judge"),),
        tests=st["tests"], configurations=len(SPEC["thetas"]) if stage == "dev" else 1, preregistration=DOC,
        design={"code_sha256": h, "spec_sha256": spec_sha(), "stage": stage}))
    print("registered", st["trial"])


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("command", choices=("probe", "hash", "preregister", "run"))
    ap.add_argument("stage", nargs="?", choices=tuple(SPEC["stages"]))
    ap.add_argument("--data", default=str(ROOT / "data" / "krp1"))
    ap.add_argument("--out", default=str(PROBE))
    ap.add_argument("--probe", default=str(PROBE))
    ap.add_argument("--delisted", default="", help="probe: a JSON file with a list of delisted Upbit codes to try")
    a = ap.parse_args(argv)
    now = datetime.now(timezone.utc)
    if a.command == "hash":
        print(code_hash(), spec_sha())
    elif a.command == "probe":
        extra = json.loads(Path(a.delisted).read_text()) if a.delisted and Path(a.delisted).exists() else []
        body = probe(now=now, delisted=extra if isinstance(extra, list) else extra.get("codes", []))
        out = Path(a.out)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(body, indent=1, sort_keys=True) + "\n")
        print(json.dumps({"upbit_krw": body["upbit_krw_markets_now"], "coins_on_both": len(body["coins"]),
                          "per_stage": body["per_stage"]}))
    elif a.command == "preregister":
        preregister(a.stage, now)
    else:
        body = run(a.stage, Path(a.data), now, probe_file=Path(a.probe))
        print(json.dumps({"program": body["program"], "verdict": body["verdict"],
                          "t": {k: v["t"] for k, v in body["results"].items()}}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
