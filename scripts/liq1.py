"""LIQ-1: buying after forced crypto deleveraging (docs/DISCOVERY_PROGRAM.md, H2; research/preregistrations/LIQ-1.md).

    python scripts/liq1.py fetch          # GitHub's runner: Binance USDT-M open interest (5-minute snapshots) and 1h
                                          # klines, development months only: nothing from 2024 on is fetched
    python scripts/liq1.py spec           # freeze the spec and the code hashes, before registration
    python scripts/liq1.py preregister    # register stage 1 (select); the preregistration must quote both hashes
    python scripts/liq1.py develop        # once: stage 1 on the development data

The question: after an hour in which a perpetual's open interest and its price both fall below their own trailing
90-day 1st percentile, does a long position held 24 hours earn a positive net return, and more than matched random
entries? The mechanism is the fire sale: liquidations close leveraged positions whatever the price, and whoever
supplies liquidity in the cascade is paid when it reverses (Coval & Stafford 2007; Brunnermeier & Pedersen 2009).

Two stages, like CR-1:

- **Stage 1 (this file, role select)** measures the fixed rule on the development data, BTCUSDT from 2020-09 and
  ETHUSDT from 2021-12, to 2023-12. Its verdict is PASSED only if every preregistered gate holds, including a
  projected stage-2 t of at least 2.0. A PASS lets stage 2 be preregistered with the rule unchanged, on 2024-01..2026-10.
  A FAIL closes the family on these data, and stage 2's data stay unfetched.
- **Nothing is chosen in stage 1.** Every threshold, the hold and the entry are fixed in the spec before any value is
  read.

No look-ahead, by construction:
- the event of hour i uses the open-interest snapshots at the hour's start and end, and that hour's kline;
- its percentiles use only the 2,160 hours before it;
- the entry is the open of hour i + 2, one full hour after the event hour closes. That also covers a snapshot published
  up to five minutes late.

Costs: 15 bp a side (a crypto CFD's spread and slippage, as XTS-1 and FND-1A), stressed x1.5 and x2. No financing: a
swap-free account. The financing a non-swap-free account would charge is reported, never added.
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
import math
import sys
import urllib.request
import zipfile
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from aitrader.research.registry import Holdout, Registry, Trial, Use, Verdict  # noqa: E402

PID = "LIQ-1"
VERSION = "liq-1.0.0"
R = ROOT / "research"
DOC = "research/preregistrations/LIQ-1.md"
SPEC = R / "specs" / "LIQ-1.json"
OUT = R / "knowledge"
DATA = ROOT / "data" / "liq1"
CODE = ("scripts/liq1.py",)
UNIVERSE = "crypto-binance-usdtm"
SYMBOLS = ("BTCUSDT", "ETHUSDT")
OI_FIRST = {"BTCUSDT": date(2020, 9, 1), "ETHUSDT": date(2021, 12, 1)}  # the probe: research/results/LIQ-probe.json
DEV_END = date(2024, 1, 1)  # stage 1 fetches and reads nothing at or after this
STAGE2 = (date(2024, 1, 1), date(2026, 11, 1))  # stage 2's data, never fetched by stage 1
WINDOW_H = 90 * 24  # the trailing window of each percentile
MIN_WINDOW = 1800  # values a percentile needs in its window, else no event that hour
PCT = 1.0  # the percentile both falls must be below
ENTRY_LAG_H = 1  # hours between the event hour's close and the entry
HOLD_H = 24
COST = 0.0015  # one side, a fraction of notional
COST_GRID = (1.0, 1.5, 2.0)
FINANCING_PA_REPORTED = 0.20  # reported only: the account is swap-free
RANDOM_N, RANDOM_SEED = 2000, 47
BOOT_N, BOOT_SEED = 5000, 53
MIN_TRADES = 30
PROJECTED_T_MIN = 2.0
GATES = {
    "trades": f"at least {MIN_TRADES} trades, both coins together",
    "mean": "the mean net return a trade > 0, both coins together",
    "each_coin": "the mean net return a trade > 0 for BTCUSDT alone and for ETHUSDT alone",
    "costs_x2": "the mean net return a trade > 0 with the cost doubled",
    "one_hour_late": "the mean net return a trade > 0 with every entry one hour later",
    "beats_random": f"the mean net return a trade above the 95th percentile of {RANDOM_N} matched random books: the same "
                    "coin, calendar month and hour of the day for each trade, the same hold and cost",
    "projected_t": f"the week-clustered t, scaled to stage 2's coin-years, >= {PROJECTED_T_MIN}",
}
STAGE2_RULE = ("preregistered only after a stage-1 PASS, with the rule unchanged: 2024-01..2026-10 (entries whose exit is "
               "before 2026-11-01); it passes if the week-clustered t of the mean net return a trade >= its threshold "
               "(every earlier test on these data; never below 3.0), and the mean is > 0 for each coin, at costs x2 and "
               "one hour late, and above the 95th percentile of the matched random books")
BASE = "https://data.binance.vision/data/futures/um/"
UA = {"User-Agent": "Mozilla/5.0 (research; aitrader LIQ-1)"}
UTC = timezone.utc


# ── the hourly series ──────────────────────────────────────────────────────

@dataclass
class Series:
    """One perpetual's hours from t0 (an hour's start, UTC epoch seconds): kline i spans [t0 + i h, t0 + (i + 1) h),
    and oi[i] is the open-interest snapshot at exactly t0 + i h. A missing value is NaN, never filled."""
    symbol: str
    t0: int
    open: np.ndarray
    close: np.ndarray
    oi: np.ndarray

    def at(self, i: int) -> datetime:
        return datetime.fromtimestamp(self.t0 + 3600 * int(i), UTC)


def series_from(symbol: str, klines: dict[str, tuple[float, float]], oi: dict[str, float]) -> Series:
    """From hour keys ("YYYY-MM-DDTHH", UTC) to dense arrays over the hours the klines span."""
    if not klines:
        raise ValueError(f"{symbol}: no klines")
    hours = sorted(klines)
    first = datetime.strptime(hours[0], "%Y-%m-%dT%H").replace(tzinfo=UTC)
    last = datetime.strptime(hours[-1], "%Y-%m-%dT%H").replace(tzinfo=UTC)
    n = int((last - first).total_seconds() // 3600) + 1
    o, c, q = (np.full(n, np.nan) for _ in range(3))
    t0 = int(first.timestamp())
    for k, (op, cl) in klines.items():
        i = (int(datetime.strptime(k, "%Y-%m-%dT%H").replace(tzinfo=UTC).timestamp()) - t0) // 3600
        o[i], c[i] = op, cl
    for k, v in oi.items():
        i = (int(datetime.strptime(k, "%Y-%m-%dT%H").replace(tzinfo=UTC).timestamp()) - t0) // 3600
        if 0 <= i < n:
            q[i] = v
    for a in (o, c, q):
        a[~(np.isfinite(a) & (a > 0))] = np.nan
    return Series(symbol, t0, o, c, q)


def signals(s: Series) -> tuple[np.ndarray, np.ndarray]:
    """Hour i's log return (kline i) and its change in log open interest (the snapshot at its end less the one at its
    start). Both are known when hour i closes."""
    r = np.log(s.close / s.open)
    d = np.full(len(s.oi), np.nan)
    d[:-1] = np.log(s.oi[1:] / s.oi[:-1])
    return r, d


def trailing_pct(x: np.ndarray, window: int = WINDOW_H, min_n: int = MIN_WINDOW, q: float = PCT) -> np.ndarray:
    """At each i, the q-th percentile of the finite values among x[i - window .. i - 1]: hour i itself and everything
    after it are never in its own window."""
    out = np.full(len(x), np.nan)
    for i in range(window, len(x)):
        w = x[i - window:i]
        w = w[np.isfinite(w)]
        if len(w) >= min_n:
            out[i] = np.percentile(w, q)
    return out


def events(s: Series, q: float = PCT, window: int = WINDOW_H, min_n: int = MIN_WINDOW) -> list[int]:
    """The hours whose return and open-interest change are both below their own trailing percentile."""
    r, d = signals(s)
    pr, pd = trailing_pct(r, window, min_n, q), trailing_pct(d, window, min_n, q)
    ok = np.isfinite(r) & np.isfinite(d) & np.isfinite(pr) & np.isfinite(pd)
    return [int(i) for i in np.nonzero(ok & (r < pr) & (d < pd))[0]]


def trades(s: Series, ev: list[int], end: datetime, lag: int = ENTRY_LAG_H, hold: int = HOLD_H) -> tuple[list[dict], int]:
    """One long position at a time per coin: entry at the open of hour i + 1 + lag, exit at the open `hold` hours later.
    An event while a position is open is passed over. A trade whose entry or exit price is missing, or whose exit is
    not before `end`, is not taken; the missing ones are counted, never filled."""
    out, missing, free_at = [], 0, -1
    for i in ev:
        e = i + 1 + lag
        x = e + hold
        if e < free_at:
            continue
        if s.at(x) >= end:
            continue
        if x >= len(s.open) or not (np.isfinite(s.open[e]) and np.isfinite(s.open[x])):
            missing += 1
            continue
        out.append({"symbol": s.symbol, "event_hour": s.at(i).isoformat(), "entry": s.at(e).isoformat(),
                    "exit": s.at(x).isoformat(), "gross": float(s.open[x] / s.open[e] - 1.0)})
        free_at = x
    return out, missing


def net(tr: list[dict], k: float = 1.0) -> np.ndarray:
    return np.array([t["gross"] - 2.0 * COST * k for t in tr])


# ── statistics ─────────────────────────────────────────────────────────────

def week_of(iso: str) -> str:
    y, w, _ = datetime.fromisoformat(iso).isocalendar()
    return f"{y}-W{w:02d}"


def cluster_t(x: np.ndarray, groups: list[str]) -> float | None:
    """The mean's t with a cluster-robust standard error (CR1): trades of one ISO week, on either coin, are one
    cluster, so a cascade that hit both coins counts once."""
    n = len(x)
    keys = sorted(set(groups))
    g = len(keys)
    if n < 2 or g < 2:
        return None
    m = float(x.mean())
    e = x - m
    sums = {k: 0.0 for k in keys}
    for v, k in zip(e, groups):
        sums[k] += float(v)
    var = sum(v * v for v in sums.values()) / (n * n) * g / (g - 1)
    return None if var <= 0 else round(m / math.sqrt(var), 3)


def week_bootstrap(x: np.ndarray, groups: list[str], n: int = BOOT_N, seed: int = BOOT_SEED) -> list[float] | None:
    """The 95% interval of the mean a trade, resampling whole weeks."""
    if len(x) < 2:
        return None
    keys = sorted(set(groups))
    by = {k: [] for k in keys}
    for v, k in zip(x, groups):
        by[k].append(float(v))
    sums = np.array([sum(by[k]) for k in keys])
    cnts = np.array([len(by[k]) for k in keys])
    rng = np.random.default_rng(seed)
    pick = rng.integers(0, len(keys), size=(n, len(keys)))
    means = sums[pick].sum(axis=1) / cnts[pick].sum(axis=1)
    return [round(float(np.percentile(means, 2.5)), 6), round(float(np.percentile(means, 97.5)), 6)]


def matched_random(by_sym: dict[str, Series], tr: list[dict], end: datetime, n: int = RANDOM_N, seed: int = RANDOM_SEED,
                   hold: int = HOLD_H) -> np.ndarray:
    """n random books: each trade replaced by an entry drawn from the same coin's hours of the same calendar month and
    the same hour of the day, held the same hours, at the same cost. Returns each book's mean net a trade."""
    rng = np.random.default_rng(seed)
    pools: dict[tuple[str, str, int], np.ndarray] = {}
    for sym, s in by_sym.items():
        m = len(s.open) - hold
        if m <= 0:
            continue
        idx = np.arange(m)
        ok = np.isfinite(s.open[:m]) & np.isfinite(s.open[hold:hold + m])
        ok &= np.array([s.at(int(i) + hold) < end for i in idx], dtype=bool)
        for i in idx[ok]:
            d = s.at(int(i))
            pools.setdefault((sym, f"{d:%Y-%m}", d.hour), []).append(int(i))
    pools = {k: np.array(v) for k, v in pools.items()}
    cols = []
    for t in tr:
        d = datetime.fromisoformat(t["entry"])
        pool = pools.get((t["symbol"], f"{d:%Y-%m}", d.hour))
        if pool is None or not len(pool):
            raise ValueError(f"no random entry matches {t['symbol']} {t['entry']}")
        s = by_sym[t["symbol"]]
        e = rng.choice(pool, size=n)
        cols.append(s.open[e + hold] / s.open[e] - 1.0 - 2.0 * COST)
    return np.vstack(cols).mean(axis=0) if cols else np.array([])


def summary(tr: list[dict], k: float = 1.0) -> dict:
    x = net(tr, k)
    if not len(x):
        return {"trades": 0, "mean": None, "t": None}
    weeks = [week_of(t["entry"]) for t in tr]
    by_year: dict[str, list[float]] = {}
    for v, t in zip(x, tr):
        by_year.setdefault(t["entry"][:4], []).append(float(v))
    total = float(x.sum())
    top_week = max((abs(sum(float(v) for v, w in zip(x, weeks) if w == k_)) for k_ in set(weeks)), default=0.0)
    return {"trades": len(x), "mean": round(float(x.mean()), 6), "median": round(float(np.median(x)), 6),
            "t": cluster_t(x, weeks), "weeks": len(set(weeks)), "won": int((x > 0).sum()),
            "hit_rate": round(float((x > 0).mean()), 3), "best": round(float(x.max()), 6),
            "worst": round(float(x.min()), 6), "sd": round(float(x.std(ddof=1)), 6) if len(x) > 1 else None,
            "total": round(total, 6), "top_week_share": round(top_week / abs(total), 3) if total else None,
            "by_year": {y: {"trades": len(v), "mean": round(float(np.mean(v)), 6)} for y, v in sorted(by_year.items())}}


def coin_years(start: date, end: date) -> float:
    return (end - start).days / 365.25


def evaluate(by_sym: dict[str, Series], end: datetime) -> dict:
    """Stage 1 on the series given: every gate, and the figures the knowledge file reports."""
    tr_all, late_all, raw, missing = [], [], {}, {}
    for sym, s in by_sym.items():
        ev = events(s)
        raw[sym] = len(ev)
        tr, miss = trades(s, ev, end)
        late, _ = trades(s, ev, end, lag=ENTRY_LAG_H + 1)
        tr_all += tr
        late_all += late
        missing[sym] = miss
    tr_all.sort(key=lambda t: t["entry"])
    main, x15, x2, late = summary(tr_all), summary(tr_all, 1.5), summary(tr_all, 2.0), summary(late_all)
    coins = {sym: summary([t for t in tr_all if t["symbol"] == sym]) for sym in by_sym}
    rnd = matched_random(by_sym, tr_all, end) if tr_all else np.array([])
    p95 = float(np.percentile(rnd, 95)) if len(rnd) else None
    x = net(tr_all)
    weeks = [week_of(t["entry"]) for t in tr_all]
    y1 = sum(coin_years(OI_FIRST[s] + timedelta(days=90), DEV_END) for s in by_sym)
    y2 = coin_years(*STAGE2) * len(by_sym)
    projected = round(main["t"] * math.sqrt(y2 / y1), 3) if main.get("t") is not None and y1 > 0 else None
    hours = {sym: int(np.isfinite(s.open).sum()) for sym, s in by_sym.items()}
    gates = {"trades": main["trades"] >= MIN_TRADES,
             "mean": (main["mean"] or 0) > 0,
             "each_coin": all((c["mean"] or 0) > 0 for c in coins.values()),
             "costs_x2": (x2["mean"] or 0) > 0,
             "one_hour_late": (late["mean"] or 0) > 0,
             "beats_random": p95 is not None and main["mean"] is not None and main["mean"] > p95,
             "projected_t": projected is not None and projected >= PROJECTED_T_MIN}
    return {"all": main, "costs_x1.5": {k: x15.get(k) for k in ("mean", "t")},
            "costs_x2": {k: x2.get(k) for k in ("mean", "t")},
            "one_hour_late": {k: late.get(k) for k in ("trades", "mean", "t")}, "by_coin": coins,
            "event_hours": raw, "trades_missing_a_price": missing,
            "random": {"books": int(len(rnd)), "mean": round(float(rnd.mean()), 6) if len(rnd) else None,
                       "p95": round(p95, 6) if p95 is not None else None,
                       "share_at_least_as_good": round(float((rnd >= (main["mean"] or 0)).mean()), 4) if len(rnd) else None},
            "bootstrap_95": week_bootstrap(x, weeks),
            "exposure": {sym: round(sum(1 for t in tr_all if t["symbol"] == sym) * HOLD_H / hours[sym], 4)
                         for sym in by_sym if hours[sym]},
            "trades_a_coin_year": round(main["trades"] / y1, 2) if y1 else None,
            "financing_reported_only": {"per_trade": round(FINANCING_PA_REPORTED * HOLD_H / (24 * 365), 6),
                                        "note": "a swap-free account pays none; a financed one would"},
            "coin_years": {"stage1": round(y1, 3), "stage2": round(y2, 3)}, "projected_stage2_t": projected,
            "gates": gates, "failed_gates": [g for g, ok in gates.items() if not ok],
            "passed": all(gates.values()), "trades": tr_all}


# ── the data (GitHub's runner) ─────────────────────────────────────────────

def _get(url: str, tries: int = 4) -> bytes:
    last = None
    for k in range(tries):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60) as r:
                return r.read()
        except Exception as e:  # a read with no side effect: bounded retries
            last = e
            import time
            time.sleep(2 * (k + 1))
    raise RuntimeError(f"{url}: {last}")


def checked(url: str) -> tuple[bytes, str]:
    """The file and its sha256, refused unless it matches Binance's published CHECKSUM."""
    raw = _get(url)
    want = _get(url + ".CHECKSUM").decode().split()[0].strip().lower()
    got = hashlib.sha256(raw).hexdigest()
    if got != want:
        raise SystemExit(f"{url}: sha256 {got} differs from its CHECKSUM {want}: stopped, nothing is filled")
    return raw, got


def _rows(raw: bytes) -> list[list[str]]:
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        name = z.namelist()[0]
        return list(csv.reader(io.TextIOWrapper(z.open(name), encoding="utf-8")))


def _number(x: str) -> float | None:
    try:
        v = float(x)
    except (TypeError, ValueError):
        return None
    return v if math.isfinite(v) and v > 0 else None


def parse_metrics(raw: bytes) -> tuple[dict[str, float], int]:
    """The open-interest snapshots taken exactly on the hour, {"YYYY-MM-DDTHH": sum_open_interest}, and the number of
    rows that could not be read. Such a row's hour stays missing: it is counted, never filled."""
    rows = _rows(raw)
    head = [h.strip().lstrip("\ufeff") for h in rows[0]]
    if "create_time" not in head or "sum_open_interest" not in head:
        raise SystemExit(f"a metrics file without create_time or sum_open_interest: {head}")
    i_t, i_oi = head.index("create_time"), head.index("sum_open_interest")
    out, bad = {}, 0
    for r in rows[1:]:
        try:
            t = datetime.fromisoformat(r[i_t].strip())
        except (IndexError, ValueError):
            bad += 1
            continue
        if t.minute or t.second or t.microsecond:
            continue
        v = _number(r[i_oi]) if len(r) > i_oi else None
        if v is None:
            bad += 1
            continue
        out[f"{t:%Y-%m-%dT%H}"] = v
    return out, bad


def parse_klines(raw: bytes) -> tuple[dict[str, tuple[float, float]], int]:
    """Each 1h kline's open and close, {"YYYY-MM-DDTHH": (open, close)}, and the number of rows that could not be
    read. A header row, if any, is skipped; a row that cannot be read leaves its hour missing, counted."""
    out, bad = {}, 0
    for n, r in enumerate(_rows(raw)):
        if not r or not r[0].strip().isdigit():
            bad += n > 0 and bool(r)
            continue
        ms = int(r[0])
        t = datetime.fromtimestamp(ms / (1e6 if ms > 1e14 else 1e3), UTC)
        if t.minute or t.second:
            raise SystemExit(f"a 1h kline opens off the hour: {t}")
        o, c = (_number(r[1]), _number(r[4])) if len(r) > 4 else (None, None)
        if o is None or c is None:
            bad += 1
            continue
        out[f"{t:%Y-%m-%dT%H}"] = (o, c)
    return out, bad


def files(symbol: str) -> list[tuple[str, str]]:
    """The development files: (kind, url). Nothing at or after DEV_END."""
    out = []
    d = OI_FIRST[symbol]
    while d < DEV_END:
        out.append(("metrics", f"{BASE}daily/metrics/{symbol}/{symbol}-metrics-{d:%Y-%m-%d}.zip"))
        d += timedelta(days=1)
    y, m = OI_FIRST[symbol].year, OI_FIRST[symbol].month
    while date(y, m, 1) < DEV_END:
        out.append(("klines", f"{BASE}monthly/klines/{symbol}/1h/{symbol}-1h-{y:04d}-{m:02d}.zip"))
        y, m = (y + 1, 1) if m == 12 else (y, m + 1)
    return out


def _canon(x) -> str:
    return json.dumps(x, sort_keys=True, separators=(",", ":"))


def cmd_fetch(now: datetime) -> None:
    DATA.mkdir(parents=True, exist_ok=True)
    man = {"retrieved": now.isoformat(), "dev_end": str(DEV_END), "symbols": {}}
    for sym in SYMBOLS:
        todo = files(sym)
        with ThreadPoolExecutor(max_workers=16) as pool:
            got = list(pool.map(lambda kv: (kv[0], kv[1], *checked(kv[1])), todo))
        oi, kl, recs, bad = {}, {}, [], 0
        for kind, url, raw, sha in got:
            part, b = parse_metrics(raw) if kind == "metrics" else parse_klines(raw)
            (oi if kind == "metrics" else kl).update(part)
            recs.append({"url": url, "sha256": sha, "rows": len(part), "unreadable_rows": b})
            bad += b
        late = [k for k in list(oi) + list(kl) if k >= f"{DEV_END:%Y-%m-%d}T00"]
        if late:
            raise SystemExit(f"{sym}: {len(late)} hours at or after {DEV_END} were read: stopped")
        (DATA / f"{sym}-oi.json").write_text(_canon(oi))
        (DATA / f"{sym}-klines.json").write_text(_canon(kl))
        man["symbols"][sym] = {
            "files": len(recs), "oi_hours": len(oi), "kline_hours": len(kl), "unreadable_rows": bad,
            "first": min(kl), "last": max(kl), "files_sha256": recs,
            "oi_sha256": hashlib.sha256(_canon(oi).encode()).hexdigest(),
            "klines_sha256": hashlib.sha256(_canon(kl).encode()).hexdigest()}
        print(sym, len(recs), "files", len(oi), "oi hours", len(kl), "kline hours", min(kl), max(kl), flush=True)
    (DATA / "manifest.json").write_text(json.dumps(man, indent=1, sort_keys=True) + "\n")


def load() -> dict[str, Series]:
    """The development series, checked against the manifest. An hour at or after DEV_END is refused."""
    man = json.loads((DATA / "manifest.json").read_text())
    out = {}
    for sym in SYMBOLS:
        m = man["symbols"][sym]
        oi_text, kl_text = (DATA / f"{sym}-oi.json").read_text(), (DATA / f"{sym}-klines.json").read_text()
        if (hashlib.sha256(oi_text.encode()).hexdigest() != m["oi_sha256"]
                or hashlib.sha256(kl_text.encode()).hexdigest() != m["klines_sha256"]):
            raise SystemExit(f"{sym}: the data differ from the manifest")
        oi, kl = json.loads(oi_text), {k: tuple(v) for k, v in json.loads(kl_text).items()}
        if any(k >= f"{DEV_END:%Y-%m-%d}T00" for k in list(oi) + list(kl)):
            raise SystemExit(f"{sym}: the data hold hours at or after {DEV_END}: stage 1 refuses them")
        out[sym] = series_from(sym, kl, oi)
    return out


# ── the program ────────────────────────────────────────────────────────────

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


def stage2_threshold(reg: Registry) -> float:
    """What stage 2 would need if registered now, counting the spot universe's tests too, since spot and perpetual
    prices move together. Recorded for information; stage 2 records its own at its registration."""
    n = reg.tests_on(UNIVERSE, *STAGE2) + reg.tests_on("crypto-binance-spot", *STAGE2) + 1
    from aitrader.research.registry import bonferroni_t
    return max(3.0, bonferroni_t(n))


def spec(reg: Registry) -> dict:
    return {"program": PID, "version": VERSION, "universe": UNIVERSE, "stage": 1, "role": "select",
            "question": "after an hour in which a perpetual's open interest and its price both fall below their own "
                        "trailing 90-day 1st percentile, does a long position held 24 hours earn a positive net return, "
                        "and more than matched random entries?",
            "symbols": list(SYMBOLS), "oi_first": {k: str(v) for k, v in OI_FIRST.items()},
            "data": "Binance USDT-M futures (data.binance.vision): daily metrics files (5-minute open-interest "
                    "snapshots; the one on each hour is used) and monthly 1h klines, each file checked against its "
                    "published CHECKSUM; nothing at or after the development end is fetched or read",
            "development_end": str(DEV_END), "stage2_period": [str(d) for d in STAGE2],
            "event": {"return": "hour i's log(close/open)", "oi_change": "log(OI at hour i's end / OI at its start)",
                      "rule": f"both below their own {PCT}th percentile over the {WINDOW_H} hours before hour i "
                              f"(at least {MIN_WINDOW} finite values each)"},
            "trade": {"entry": f"the open of hour i + 1 + {ENTRY_LAG_H}", "hold_hours": HOLD_H, "side": "long only",
                      "positions": "one at a time per coin; an event while one is open is passed over",
                      "missing_price": "the trade is not taken and is counted; nothing is filled"},
            "cost_per_side": COST, "cost_grid": list(COST_GRID), "financing": "none (swap-free); "
            f"{FINANCING_PA_REPORTED:.0%} a year reported only",
            "random": {"books": RANDOM_N, "seed": RANDOM_SEED, "match": "coin, calendar month, hour of the day"},
            "bootstrap": {"n": BOOT_N, "seed": BOOT_SEED, "unit": "ISO week"},
            "t": "week-clustered (CR1): trades of one ISO week on either coin are one cluster",
            "gates": GATES, "stage2_rule": STAGE2_RULE,
            "stage2_threshold_t_if_registered_now": round(stage2_threshold(reg), 4)}


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
    print(spec_sha(s), "code", code_hash(), "stage-2 threshold now", s["stage2_threshold_t_if_registered_now"])


def cmd_preregister(now: datetime) -> None:
    reg = _registry()
    frozen = json.loads(SPEC.read_text())
    if spec_sha(spec(reg)) != frozen["sha256"] or code_hash() != frozen["code_sha256"]:
        raise SystemExit("the spec or the code differs from what was frozen")
    text = (ROOT / DOC).read_text()
    if frozen["sha256"] not in text or frozen["code_sha256"] not in text:
        raise SystemExit(f"{DOC} must quote the spec and code sha256")
    reg.register(Trial(id=PID, registered=now,
                       title="LIQ-1 stage 1: buying after forced crypto deleveraging (development, select)",
                       hypothesis="After an hour in which BTCUSDT's or ETHUSDT's open interest and price both fall below "
                                  "their trailing 90-day 1st percentile, does a long held 24 hours earn a positive net "
                                  "return, more than matched random entries?",
                       uses=(Use(UNIVERSE, OI_FIRST["BTCUSDT"], DEV_END, "select"),), tests=1, configurations=1,
                       preregistration=DOC, design={"spec_sha256": frozen["sha256"], "code_sha256": frozen["code_sha256"],
                                                    "stage": 1}))
    print("registered", PID)


def _write(name: str, body: dict) -> dict:
    body = json.loads(json.dumps(body, sort_keys=True, default=str))
    body["sha256"] = hashlib.sha256(json.dumps(body, sort_keys=True).encode()).hexdigest()
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / f"{name}.json").write_text(_dump(body))
    return body


def cmd_develop(now: datetime) -> None:
    reg = _registry()
    if reg.verdict_of(PID) is not None:
        raise SystemExit(f"{PID} already has a verdict")
    frozen = _registered(reg)
    res = evaluate(load(), datetime(DEV_END.year, DEV_END.month, DEV_END.day, tzinfo=UTC))
    verdict = "PASSED" if res["passed"] else "FAILED"
    a = res["all"]
    body = _write(PID, {"program": PID, "stage": 1, "verdict": verdict, "spec_sha256": frozen["sha256"],
                        "code_sha256": frozen["code_sha256"], "development_end": str(DEV_END),
                        "meaning": ("stage 2 may be preregistered, with the rule unchanged" if res["passed"] else
                                    "the family is closed on these data; stage 2's data stay unfetched"),
                        **res, "data": json.loads((DATA / "manifest.json").read_text())})
    reg.record_verdict(Verdict(PID, now, verdict, {"artifact": f"research/knowledge/{PID}.json",
                                                    "artifact_sha256": body["sha256"]}))
    print(f"{PID} stage 1 {verdict}: {a['trades']} trades, mean net {a['mean']}, t {a['t']}, projected stage-2 t "
          f"{res['projected_stage2_t']}; failed: {res['failed_gates']}")


def main() -> int:
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    now = datetime.now(UTC).replace(microsecond=0)
    if cmd == "fetch":
        cmd_fetch(now)
    elif cmd == "spec":
        cmd_spec()
    elif cmd == "preregister":
        cmd_preregister(now)
    elif cmd == "develop":
        cmd_develop(now)
    else:
        print(__doc__)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
