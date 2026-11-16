"""HLQ-1: is the price drawn to the leveraged positions everyone can see? (research/preregistrations/HLQ-1.md)
Runs on GitHub's runner (.github/workflows/hlq1.yml): Hyperliquid's public API and Binance's archive are reachable
there, not from the research director's session.

    python scripts/hlq1.py probe                     # counts only: who can be read, how much, how fast
    python scripts/hlq1.py record --out DIR          # one snapshot of aggregated liquidation levels; no account kept
    python scripts/hlq1.py hash                      # the code and spec hashes the preregistration quotes
    python scripts/hlq1.py preregister forward       # before the first snapshot of its window
    python scripts/hlq1.py run forward --data DIR    # once, on or after the day its archive is whole

RESEARCH ONLY. Hyperliquid's positions are information: nothing here trades a perpetual, pays or receives funding.
The traded instrument would be a swap-free CFD on bitcoin or ether, long or short (short selling is needed for the
trades toward a long cluster below the price; no leverage is needed).
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import io
import json
import random
import sys
import threading
import time
import urllib.error
import urllib.request
import zipfile
from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from aitrader.research.dlab.feeds import checked  # noqa: E402
from aitrader.research.dlab.feeds import get as get_file  # noqa: E402
from aitrader.research.events import hlq as H  # noqa: E402
from aitrader.research.registry import Registry, Trial, Use, Verdict, bonferroni_t  # noqa: E402

R = ROOT / "research"
DOC = "research/preregistrations/HLQ-1.md"
CODE = ("aitrader/research/events/hlq.py", "scripts/hlq1.py")
UNIVERSE = "crypto-hl-visible-liquidations"
INFO = "https://api.hyperliquid.xyz/info"
BOARD = "https://stats-data.hyperliquid.xyz/Mainnet/leaderboard"
VISION = "https://data.binance.vision/"
LISTING = "https://s3-ap-northeast-1.amazonaws.com/data.binance.vision?delimiter=/&prefix={prefix}"
REC_VERSION = "hlq-rec-1.0.0"
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; research-data-fetch/1.0)", "Content-Type": "application/json"}
#: the recorder: accounts read per snapshot (largest account value first), requests per second, coins kept
ACCOUNTS = 800
RATE = 8.0
MIN_OI_USD = 5e6

SPEC = {"program": "HLQ-1", "version": H.HLQ_VERSION, "recorder": REC_VERSION, "universe": UNIVERSE,
        "instrument": "swap-free CFD on bitcoin or ether, long or short; Hyperliquid positions are information only",
        "prices": "Binance spot one-minute bars", "accounts": ACCOUNTS, "rule": {
            "lo": 0.01, "hi": 0.05, "imbalance": 0.75, "min_share": 0.01, "hold": 2880},
        "late_delay_minutes": 30, "cost_per_side": 0.001, "placebo_span_days": 3, "placebo_gap_hours": 6,
        "placebo_draws": 40, "placebos": 1000, "seed": 20261116, "nw_lag": 2, "bar_floor": 3.0,
        "owner_coins": ["BTC", "ETH"], "min_owner_trades": 30,
        "gates": ["t", "costs_x2", "halves", "top5_removed", "late_entry", "beats_placebo", "without_best_day",
                  "without_best_coin", "owner_instruments"],
        "stages": {"forward": {"trial": "HLQ-1", "snapshots": ["2026-12-01T00:00:00Z", "2027-06-01T00:00:00Z"],
                               "not_before": "2027-06-12", "tests": 1, "min_events": 300, "min_days": 100}}}


def code_hash() -> str:
    h = hashlib.sha256()
    for f in CODE:
        h.update((ROOT / f).read_bytes())
    return h.hexdigest()


def spec_sha() -> str:
    return hashlib.sha256(json.dumps(SPEC, sort_keys=True).encode()).hexdigest()


def registry() -> Registry:
    return Registry.load(R / "registry.jsonl")


def ms(iso: str) -> int:
    return int(datetime.fromisoformat(iso.replace("Z", "+00:00")).timestamp() * 1000)


# ── Hyperliquid, read only ──────────────────────────────────────────────────

def http(url: str, body: dict | None = None, tries: int = 4) -> object:
    """A read with no side effect: bounded exponential backoff with jitter (CLAUDE.md rule 3)."""
    data = json.dumps(body).encode() if body is not None else None
    last: Exception | None = None
    for k in range(tries):
        try:
            req = urllib.request.Request(url, data=data, method="POST" if body is not None else "GET", headers=HEADERS)
            with urllib.request.urlopen(req, timeout=60) as r:
                return json.loads(r.read())
        except Exception as e:  # noqa: BLE001 - a read: retried, then raised
            last = e
            time.sleep(min(30.0, 2.0 ** k) * (0.5 + random.random()))
    raise RuntimeError(f"{url}: {last}")


def board_rows(raw: object) -> list[tuple[str, float]]:
    """The leaderboard's (address, account value) pairs, largest first. Addresses stay in memory only."""
    rows = raw.get("leaderboardRows", []) if isinstance(raw, dict) else (raw or [])
    out = []
    for r in rows:
        a, v = (r or {}).get("ethAddress"), H._f((r or {}).get("accountValue"))
        if a and v is not None:
            out.append((a, v))
    return sorted(out, key=lambda x: -x[1])


def markets(raw: object) -> dict[str, tuple[float, float]]:
    """metaAndAssetCtxs -> coin: (mark, open interest in USD), for listed coins."""
    meta, ctxs = raw
    out = {}
    for u, c in zip(meta.get("universe", []), ctxs):
        if u.get("isDelisted"):
            continue
        m, oi = H._f(c.get("markPx")), H._f(c.get("openInterest"))
        if m and m > 0 and oi is not None:
            out[u["name"]] = (m, oi * m)
    return out


def read_states(addresses: list[str], fetch=http, rate: float = RATE, workers: int = 4) -> tuple[list[dict], int]:
    """Each account's clearinghouseState, at most `rate` requests a second. An account that does not answer is
    counted and left out; nothing is filled."""
    lock, nxt = threading.Lock(), [time.monotonic()]

    def one(a: str):
        with lock:
            wait = nxt[0] - time.monotonic()
            nxt[0] = max(nxt[0], time.monotonic()) + 1.0 / rate
        if wait > 0:
            time.sleep(wait)
        try:
            return fetch(INFO, {"type": "clearinghouseState", "user": a})
        except Exception:  # noqa: BLE001 - counted below
            return None
    with ThreadPoolExecutor(workers) as ex:
        got = list(ex.map(one, addresses))
    ok = [g for g in got if isinstance(g, dict)]
    return ok, len(addresses) - len(ok)


def snapshot(fetch=http, clock=lambda: int(time.time() * 1000), accounts: int = ACCOUNTS,
             min_oi: float = MIN_OI_USD) -> dict:
    """One snapshot: per coin with at least `min_oi` of open interest, the mark and open interest when it began, the
    mark when it ended, and the long and short notional by liquidation distance over the `accounts` largest
    accounts. No address is kept."""
    rows = board_rows(fetch(BOARD, None))
    t = clock()
    m0 = markets(fetch(INFO, {"type": "metaAndAssetCtxs"}))
    states, failed = read_states([a for a, _ in rows[:accounts]], fetch)
    t_end = clock()
    m1 = markets(fetch(INFO, {"type": "metaAndAssetCtxs"}))
    keep = {c for c, (_, oi) in m0.items() if oi >= min_oi}
    agg = H.aggregate(states, {c: m for c, (m, _) in m0.items()}, keep)
    coins = {}
    for c in sorted(keep):
        a = agg.get(c, {"L": {}, "S": {}})
        coins[c] = {"mark": m0[c][0], "mark_end": m1.get(c, (None,))[0], "oi_usd": round(m0[c][1]),
                    "L": {str(k): round(v) for k, v in sorted(a["L"].items())},
                    "S": {str(k): round(v) for k, v in sorted(a["S"].items())},
                    **{k: (round(a[k]) if isinstance(a.get(k), float) else a.get(k, 0))
                       for k in ("L_usd", "S_usd", "L_n", "S_n", "L_noliq", "S_noliq", "L_far", "S_far")}}
    return {"v": REC_VERSION, "t": t, "t_end": t_end, "board_rows": len(rows), "asked": min(accounts, len(rows)),
            "answered": len(states), "failed": failed, "coins": coins}


def write_snapshot(line: dict, out: Path) -> Path:
    t = datetime.fromtimestamp(line["t"] / 1000, timezone.utc)
    f = out / t.strftime("%Y-%m-%d") / (t.strftime("%Y-%m-%dT%H%M%SZ") + ".json.gz")
    f.parent.mkdir(parents=True, exist_ok=True)
    with gzip.open(f, "wt") as g:
        json.dump(line, g, sort_keys=True, separators=(",", ":"))
    return f


def binance_symbol(coin: str) -> str:
    """Hyperliquid's coin name as a Binance spot USDT pair (kPEPE, a thousand PEPE, trades as PEPEUSDT)."""
    c = coin[1:] if coin.startswith("k") and coin[1:].isupper() else coin
    return c.upper() + "USDT"


def has_spot_1m(symbol: str, fetch=get_file) -> bool:
    body = fetch(LISTING.format(prefix=f"data/spot/monthly/klines/{symbol}/1m/"))
    return bool(body) and b"<Key>" in body


DEPTH = (0.01, 0.02, 0.03, 0.05, 0.10, 0.25, 0.50)
DEPTH_LABELS = ("<1%", "1-2%", "2-3%", "3-5%", "5-10%", "10-25%", "25-50%", ">=50%")
LEVERAGE = ((1, 3), (4, 10), (11, 20), (21, 50), (51, 10 ** 6))


def depth(states: list[dict], marks: dict[str, float], coins: set[str]) -> dict:
    """How far from the mark each position's liquidation lies, and at what leverage, in counts and notional; and,
    for `coins`, the notional liquidated 1-5% away. No position and no account is kept."""
    n, usd = [0] * len(DEPTH_LABELS), [0.0] * len(DEPTH_LABELS)
    lev: dict[str, int] = {}
    near: dict[str, float] = {}
    noliq = 0
    for st in states:
        for ap in (st or {}).get("assetPositions") or []:
            p = (ap or {}).get("position") or {}
            c, szi = p.get("coin"), H._f(p.get("szi"))
            m = marks.get(c) if c else None
            if not m or not szi:
                continue
            v = abs(szi) * m
            lv = p.get("leverage") or {}
            x = H._f(lv.get("value"))
            band = next((f"{a}-{b}" for a, b in LEVERAGE if x is not None and a <= x <= b), "unknown")
            key = f"{lv.get('type', 'unknown')} {band}x"
            lev[key] = lev.get(key, 0) + 1
            liq = H._f(p.get("liquidationPx"))
            if liq is None or liq <= 0:
                noliq += 1
                continue
            d = abs(liq / m - 1)
            k = next((i for i, b in enumerate(DEPTH) if d < b), len(DEPTH))
            n[k] += 1
            usd[k] += v
            if 0.01 <= d <= 0.05 and c in coins:
                near[c] = near.get(c, 0.0) + v
    return {"positions": sum(n) + noliq, "no_liquidation_price": noliq,
            "by_distance": {lab: {"n": n[i], "usd": round(usd[i])} for i, lab in enumerate(DEPTH_LABELS)},
            "leverage": dict(sorted(lev.items())), "near_1_5pct_usd": {c: round(v) for c, v in sorted(near.items())}}


def probe(fetch=http, clock=lambda: int(time.time() * 1000), listing=has_spot_1m, sample: int = 200) -> dict:
    """What the recorder can read, in counts: no position, no address and no price path is kept."""
    t0 = time.monotonic()
    rows = board_rows(fetch(BOARD, None))
    board_s = time.monotonic() - t0
    m = markets(fetch(INFO, {"type": "metaAndAssetCtxs"}))
    t1 = time.monotonic()
    states, failed = read_states([a for a, _ in rows[:sample]], fetch)
    per = (time.monotonic() - t1) / max(1, sample)
    vals = [v for _, v in rows]
    pos = [ap.get("position") or {} for s in states for ap in s.get("assetPositions") or []]
    agg = H.aggregate(states, {c: x for c, (x, _) in m.items()})
    top = sorted(m, key=lambda c: -m[c][1])[:40]
    cover = {}
    for c in top:
        a = agg.get(c)
        cfg = SPEC["rule"]
        sig = H.signal({**a, "oi_usd": m[c][1]}, cfg["lo"], cfg["hi"], cfg["imbalance"], cfg["min_share"]) if a else None
        L, S, _, _ = H.clusters(a, cfg["lo"], cfg["hi"]) if a else (0.0, 0.0, None, None)
        cover[c] = {"oi_usd": round(m[c][1]), "binance_spot_1m": listing(binance_symbol(c)),
                    "covered_usd": round((a or {}).get("L_usd", 0) + (a or {}).get("S_usd", 0)),
                    "cluster_L_usd": round(L), "cluster_S_usd": round(S), "signal_now": sig is not None}
    # where the near liquidations are: the largest accounts, and random samples further down the board
    rng, n100k = random.Random(SPEC["seed"]), sum(v >= 1e5 for v in vals)
    marks_now = {c: x for c, (x, _) in m.items()}
    groups = {"ranks_1_200": states}
    for name, pool, k in (("ranks_201_800_sample", rows[200:800], 200), ("ranks_801_to_100k_sample", rows[800:n100k], 400),
                          ("below_100k_sample", rows[n100k:], 400)):
        got, _ = read_states([a for a, _ in rng.sample(pool, min(k, len(pool)))], fetch)
        groups[name] = got
    deep = {name: {"accounts": len(sts), **depth(sts, marks_now, set(top))} for name, sts in groups.items()}
    return {"retrieved": datetime.fromtimestamp(clock() / 1000, timezone.utc).isoformat(), "board_seconds": round(board_s, 1),
            "groups": deep,
            "board_rows": len(rows), "account_value_sum": round(sum(vals)),
            "account_value_top": {str(n): round(sum(vals[:n])) for n in (100, 400, 800, 1600)},
            "accounts_over": {"100k": sum(v >= 1e5 for v in vals), "1m": sum(v >= 1e6 for v in vals)},
            "coins_listed": len(m), "coins_oi_over": {k: sum(oi >= x for _, oi in m.values())
                                                       for k, x in (("5m", 5e6), ("20m", 2e7), ("100m", 1e8))},
            "sample_accounts": sample, "sample_answered": len(states), "sample_failed": failed,
            "seconds_per_account": round(per, 3), "positions": len(pos),
            "positions_with_liquidation_price": sum(1 for p in pos if H._f(p.get("liquidationPx"))),
            "top_coins": cover, "fields_of_a_position": sorted(pos[0]) if pos else []}


# ── Binance's archive and the judgement ───────────────────────────────────────

def months_between(a: int, b: int) -> list[str]:
    d, out = datetime.fromtimestamp(a / 1000, timezone.utc).date().replace(day=1), []
    end = datetime.fromtimestamp(b / 1000, timezone.utc).date()
    while d <= end:
        out.append(d.strftime("%Y-%m"))
        d = (d + timedelta(days=32)).replace(day=1)
    return out


def kline_url(symbol: str, month: str) -> str:
    return f"{VISION}data/spot/monthly/klines/{symbol}/1m/{symbol}-1m-{month}.zip"


def parse_klines(raw: bytes) -> list[tuple[int, float, float, float, float]]:
    """open time, open, high, low, close; the archive's open times in microseconds from 2025 on are read too."""
    out = []
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        for name in z.namelist():
            for line in z.read(name).decode().splitlines():
                p = line.split(",")
                if not p or not p[0].strip().isdigit():
                    continue
                t = int(p[0])
                t = t // 1000 if t > 10 ** 14 else t
                out.append((t, float(p[1]), float(p[2]), float(p[3]), float(p[4])))
    return out


def load_snapshots(src: Path, first: int, last: int) -> tuple[dict[str, list[dict]], dict]:
    """Every snapshot completed in [first, last) by the registered recorder, per coin; nothing outside the window is
    read, and a snapshot from another recorder is counted and left out."""
    by: dict[str, list[dict]] = {}
    seen = other = 0
    for f in sorted(src.glob("*/*.json.gz")):
        with gzip.open(f, "rt") as g:
            s = json.load(g)
        if not first <= s.get("t_end", -1) < last:
            continue
        if s.get("v") != REC_VERSION:
            other += 1
            continue
        seen += 1
        for c, a in s["coins"].items():
            by.setdefault(c, []).append({**a, "t": s["t"], "t_end": s["t_end"]})
    return by, {"snapshots": seen, "other_recorder": other}


def run(stage: str, data: Path, snaps_dir: Path, now: datetime, fetch=checked, reg: Registry | None = None,
        out_dir: Path | None = None) -> dict:
    reg = reg or registry()
    st = SPEC["stages"][stage]
    pid = st["trial"]
    out_dir = out_dir or R / "knowledge"
    if not any(t.id == pid for t in reg.trials):
        raise SystemExit(f"{pid} is not registered: nothing is judged before it is")
    if reg.status_of(pid) != "PENDING":
        raise SystemExit(f"{pid} already has a verdict: a stage is judged once")
    if now.date().isoformat() < st["not_before"]:
        raise SystemExit(f"{pid} is judged on or after {st['not_before']}, when its archive is whole")
    design = reg.get(pid).design
    if design.get("code_sha256") != code_hash() or design.get("spec_sha256") != spec_sha():
        raise SystemExit(f"{pid}: the code or the spec differs from what was registered")
    cfg, cost = SPEC["rule"], SPEC["cost_per_side"]
    first, last = (ms(x) for x in st["snapshots"])
    last_price = last + (cfg["hold"] + SPEC["late_delay_minutes"] + 2) * H.MINUTE
    snaps, seen = load_snapshots(snaps_dir, first, last)
    coins = sorted(c for c in snaps if c in set(design.get("coins", [])))
    t0 = first - first % H.DAY
    n = (last_price - t0) // H.MINUTE + 1
    paths, absent, failed = {}, [], []
    for c in coins:
        p = H.Path(t0, n)
        got = False
        for mo in months_between(t0, last_price):
            try:
                raw = fetch(kline_url(binance_symbol(c), mo))
            except Exception as e:  # noqa: BLE001 - counted: nothing is judged on a partial archive
                failed.append(f"{c} {mo}: {e}")
                continue
            if raw is None:
                absent.append(f"{c} {mo}")
                continue
            p.put([r for r in parse_klines(raw) if r[0] <= last_price])
            got = True
        if got:
            paths[c] = p
    if failed:
        raise SystemExit(f"{len(failed)} archive files did not arrive (the first: {failed[:3]}): nothing is judged on a "
                         "partial archive")
    held = [p.t0 + int(np.flatnonzero(np.isfinite(p.c))[-1]) * H.MINUTE for p in paths.values() if np.isfinite(p.c).any()]
    bar = max(SPEC["bar_floor"], bonferroni_t(max(1, reg.tests_on(UNIVERSE, date.fromisoformat(st["snapshots"][0][:10]),
                                                                    date.fromisoformat(st["snapshots"][1][:10])))))
    use = {c: snaps[c] for c in paths}
    evs = H.events(use, paths, first, last, cfg, cost)
    late = H.events(use, paths, first, last, cfg, cost, delay=SPEC["late_delay_minutes"])
    plac = H.placebos(use, paths, evs, cfg, cost, SPEC["placebo_span_days"] * H.DAY,
                      SPEC["placebo_gap_hours"] * 3_600_000, SPEC["placebo_draws"], SPEC["seed"])
    res = H.judge(evs, late, plac, bar, cost, st["min_events"], st["min_days"], tuple(SPEC["owner_coins"]),
                  SPEC["min_owner_trades"], SPEC["seed"], SPEC["placebos"], SPEC["nw_lag"])
    body = {"program": pid, "stage": stage, "kind": "forward_event_study", "verdict": res["verdict"],
            "judged": now.isoformat(), "code_sha256": code_hash(), "spec_sha256": spec_sha(), "spec": SPEC,
            "window": st["snapshots"], "last_minute_read": datetime.fromtimestamp(last_price / 1000, timezone.utc).isoformat(),
            "last_minute_held": datetime.fromtimestamp(max(held) / 1000, timezone.utc).isoformat() if held else None,
            "coins_judged": sorted(paths), "coins_absent": absent, **seen, "result": res}
    out_dir.mkdir(parents=True, exist_ok=True)
    f = out_dir / f"{pid}.json"
    f.write_text(json.dumps(body, indent=1, sort_keys=True, default=str) + "\n")
    data.mkdir(parents=True, exist_ok=True)
    with gzip.open(data / f"{pid}-events.json.gz", "wt") as g:
        json.dump({"events": evs, "late": late}, g, default=str)
    reg.record_verdict(Verdict(pid, now, res["verdict"], {
        "artifact": str(f.relative_to(ROOT)) if f.is_relative_to(ROOT) else str(f), "t": res["t"],
        "mean_net": res["mean_net"], "traded": res["traded"], "days": res["days"], "gates": res.get("gates"),
        "why": res.get("why")}))
    return body


def preregister(stage: str, now: datetime, coins: list[str]) -> None:
    st = SPEC["stages"][stage]
    h = code_hash()
    doc = (ROOT / DOC).read_text()
    if h not in doc or spec_sha() not in doc:
        raise SystemExit(f"{DOC} must quote the code sha256 {h} and the spec sha256 {spec_sha()}")
    if now >= datetime.fromisoformat(st["snapshots"][0].replace("Z", "+00:00")):
        raise SystemExit(f"{st['trial']} is registered before its first snapshot ({st['snapshots'][0]}), or not at all")
    if not set(SPEC["owner_coins"]) <= set(coins):
        raise SystemExit("the judged coins must include bitcoin and ether, the owner's instruments")
    a, b = (date.fromisoformat(x[:10]) for x in st["snapshots"])
    registry().register(Trial(
        id=st["trial"], registered=now, title="HLQ-1: visible liquidation clusters on Hyperliquid, forward",
        hypothesis="At a snapshot where one side holds at least 75% of the leveraged notional that Hyperliquid would "
                   "liquidate between 1% and 5% from the mark (and the two sides at least 1% of the coin's open "
                   "interest), the price reaches that side's mean distance before the same distance on the other side "
                   "often enough to earn a positive net return after 0.1% a side, averaged over daily cohorts.",
        uses=(Use(UNIVERSE, a, b, "judge"),), tests=st["tests"], configurations=1, preregistration=DOC,
        design={"code_sha256": h, "spec_sha256": spec_sha(), "stage": stage, "coins": sorted(coins)}))
    print("registered", st["trial"], "on", len(coins), "coins")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("command", choices=("probe", "record", "hash", "preregister", "run"))
    ap.add_argument("stage", nargs="?", choices=tuple(SPEC["stages"]))
    ap.add_argument("--out", default=str(ROOT / "data" / "hlq"))
    ap.add_argument("--data", default=str(ROOT / "data" / "hlq1"))
    ap.add_argument("--coins", default="")
    a = ap.parse_args(argv)
    now = datetime.now(timezone.utc)  # the command line's clock: every function above takes its time as an argument
    if a.command == "probe":
        body = probe()
        f = R / "results" / "HLQ-1-probe.json"
        f.write_text(json.dumps(body, indent=1, sort_keys=True) + "\n")
        print(json.dumps({k: body[k] for k in ("board_rows", "sample_answered", "positions", "coins_listed")}))
    elif a.command == "record":
        f = write_snapshot(snapshot(), Path(a.out))
        print("wrote", f.name)
    elif a.command == "hash":
        print(code_hash(), spec_sha())
    elif a.command == "preregister":
        preregister(a.stage, now, [c for c in a.coins.split(",") if c])
    else:
        body = run(a.stage, Path(a.data), Path(a.out), now)
        print(json.dumps({"program": body["program"], "verdict": body["verdict"],
                          "result": {k: body["result"].get(k) for k in ("traded", "days", "mean_net", "t", "gates")}}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
