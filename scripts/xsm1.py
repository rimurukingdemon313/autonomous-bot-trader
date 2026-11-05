"""XSM-1: cross-sectional momentum among the largest Binance spot coins (research/preregistrations/XSM-1.md).

The owner, 2026-11-05: "don't fixate on the AI trading; anything that makes us a profit; never stop". XTS-1 asked
whether bitcoin and ether trend over time; it failed. XSM-1 asks a different question: among the large coins, do the
ones that rose most over the last three weeks beat the others over the next week? Liu, Tsyvinski & Wu (2022, "Common
Risk Factors in Cryptocurrency", Journal of Finance) found a strong cross-sectional momentum factor on past three-week
returns, rebalanced weekly, in 2014-2018, mostly among many small coins. XSM-1 asks whether it holds among the 20
largest coins a retail trader can actually trade, after costs, since 2018.

The rule, fixed before any XSM-1 data was fetched:
- every Sunday's daily close (00:00 UTC Monday), the universe is the 20 Binance spot USDT pairs with the largest
  USDT volume over the 28 days to that close, among those with a close on each of the 90 days to it. Stablecoins,
  fiat and leveraged tokens are not coins here (`tradable`). Fewer than 12 such pairs: no trade that week;
- the book holds, equally weighted, the 4 of those 20 whose close rose most over the 21 days to that close (ties by
  name), from that close to the next Sunday's. A coin with no close that next Sunday is valued at its last close in
  the week (a delisting's loss included); one with no later close at all, at its entry;
- the benchmark holds all 20 equally, the same way. Every trade, the drift of the week included, pays 0.15% of the
  notional traded: a 0.10% taker fee plus 0.05% of spread and slippage;
- the question is the weekly difference: the book's net minus the benchmark's net.

    python scripts/xsm1.py spec          # freeze the design (reads no data)
    python scripts/xsm1.py preregister   # register XSM-1 in research/registry.jsonl
    python scripts/xsm1.py fetch         # Binance's public archive (on GitHub's runner: blocked here)
    python scripts/xsm1.py judge         # 2018-10..2024-06: development, validation, the gates
    python scripts/xsm1.py holdout       # only if XSM-1 PASSED: 2024-07..2026-09, once

Each command refuses to run if the code or the spec changed since registration. Nothing here changes the bot.
"""

from __future__ import annotations

import csv
import gzip
import hashlib
import io
import json
import math
import sys
import urllib.parse
import xml.etree.ElementTree as ET
import zipfile
from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from statistics import NormalDist

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from aitrader.research.registry import Holdout, Registry, Trial, Use, Verdict, bonferroni_t  # noqa: E402
from scripts.xts1 import _get, months  # noqa: E402

R = ROOT / "research"
PID, HID = "XSM-1", "XSM-1-H"
DOC = "research/preregistrations/XSM-1.md"
SPEC = R / "specs" / "XSM-1.json"
OUT = R / "knowledge"
DATA = ROOT / "data" / "xsm"
CODE = ("scripts/xsm1.py", "scripts/xts1.py")
UNIVERSE = "crypto-binance-spot"
#: every earlier crypto test counts against this one's threshold
CRYPTO_UNIVERSES = ("crypto-binance-usdtm", "crypto-binance-usdtm-all", "crypto-xvenue-hl-binance",
                    "crypto-perp-live-xvenue", UNIVERSE)
FIRST_MONTH, LAST_MONTH = "2018-01", "2026-09"
DEV = (date(2018, 10, 1), date(2022, 1, 1))
VAL = (date(2022, 1, 1), date(2024, 7, 1))
JUDGE = (DEV[0], VAL[1])
HOLD = (date(2024, 7, 1), date(2026, 10, 1))
TOP_VOLUME, HELD, MIN_UNIVERSE = 20, 4, 12
LOOKBACK, VOLUME_DAYS, HISTORY_DAYS = 21, 28, 90
COST = 0.0015          # per unit of notional traded
TESTS = 1              # the weekly difference's t (G1)
LIST = "https://s3-ap-northeast-1.amazonaws.com/data.binance.vision?delimiter=/&prefix={p}&marker={m}"
BASE = "https://data.binance.vision/data/spot/monthly/klines/{s}/1d/{s}-1d-{m}.zip"
S3 = "{http://s3.amazonaws.com/doc/2006-03-01/}"
#: fiat currencies and stablecoins that do not carry "USD" in their name: not coins here
NOT_COINS = frozenset({"EUR", "GBP", "AUD", "TRY", "BRL", "RUB", "UAH", "NGN", "ZAR", "PLN", "RON", "ARS", "JPY", "MXN",
                       "COP", "CZK", "BIDR", "IDRT", "BKRW", "BVND", "DAI", "PAX", "VAI", "UST", "USTC", "AEUR",
                       "EURI"})

GATES = {
    "t": "t of the mean weekly difference (the book's net minus the benchmark's net), 2018-10..2024-06, >= the "
         "threshold",
    "development": "mean weekly difference > 0 in 2018-10..2021",
    "validation": "mean weekly difference > 0 in 2022..2024-06",
    "costs_x2": "mean weekly difference > 0 with the cost doubled",
    "book_pays": "the book's own mean weekly net > 0 over 2018-10..2024-06",
    "top_year": "no calendar year supplies more than 50% of the total difference",
}
HOLDOUT_RULE = ("2024-07..2026-09: mean weekly difference > 0 with one-sided t >= 1.645, > 0 with the cost doubled, "
                "and the book's own mean weekly net > 0")


def code_hash() -> str:
    h = hashlib.sha256()
    for p in CODE:
        h.update((ROOT / p).read_bytes())
    return h.hexdigest()


def spec_sha(s: dict) -> str:
    return hashlib.sha256(json.dumps(s, sort_keys=True).encode()).hexdigest()


def threshold(reg: Registry) -> float:
    earlier = sum(reg.tests_on(u, JUDGE[0], HOLD[1]) for u in CRYPTO_UNIVERSES)
    return max(3.0, bonferroni_t(earlier + TESTS))


def spec(reg: Registry) -> dict:
    return {"program": PID, "question": "among the 20 largest Binance spot coins, do the 4 that rose most over the "
                                        "last 21 days beat the 20 over the next week, after costs?",
            "universe": f"top {TOP_VOLUME} USDT pairs by USDT volume over {VOLUME_DAYS} days, among pairs with a "
                        f"close on each of the {HISTORY_DAYS} days to the rebalance; no stablecoins, fiat or "
                        f"leveraged tokens; fewer than {MIN_UNIVERSE}: no trade",
            "held": HELD, "lookback_days": LOOKBACK, "rebalance": "weekly, at Sunday's daily close (00:00 UTC)",
            "cost_per_side": COST, "not_coins": sorted(NOT_COINS),
            "data": "Binance spot daily klines (data.binance.vision), every USDT pair the archive lists, delisted ones "
                    "included; each monthly archive checked against its published sha256; a month that cannot be "
                    "fetched or checked stops the judge, never filled",
            "periods": {"development": [str(d) for d in DEV], "validation": [str(d) for d in VAL],
                        "holdout": [str(d) for d in HOLD]},
            "gates": GATES, "holdout_rule": HOLDOUT_RULE, "threshold_t": round(threshold(reg), 4), "tests": TESTS,
            "after": {"PASSED and VALIDATED": "proposed to the owner as a paper strategy of its own (rule 14), sized "
                                              "by the risk engine, followed forward on paper; never real money",
                      "otherwise": "reported as it is; nothing changes"}}


def _dump(x) -> str:
    return json.dumps(x, indent=1, sort_keys=True, default=str) + "\n"


def _write(name: str, body: dict) -> dict:
    body = json.loads(json.dumps(body, sort_keys=True, default=str))
    body["sha256"] = hashlib.sha256(json.dumps(body, sort_keys=True).encode()).hexdigest()
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / f"{name}.json").write_text(_dump(body))
    return body


# ── which pairs are coins ────────────────────────────────────────────────

def tradable(sym: str, bases: frozenset[str] | set[str]) -> bool:
    """A USDT pair whose base is a coin: not a stablecoin or fiat, not a leveraged token (BTCUP, ETHBULL...)."""
    if not sym.endswith("USDT") or len(sym) <= 4:
        return False
    base = sym[:-4]
    if "USD" in base or base in NOT_COINS or base in ("BULL", "BEAR") or base.endswith(("BULL", "BEAR")):
        return False
    for suffix in ("UP", "DOWN"):
        if base.endswith(suffix) and base[:-len(suffix)] in bases:
            return False
    return True


# ── the data ─────────────────────────────────────────────────────────────

def list_s3(prefix: str) -> tuple[list[str], list[str]]:
    """The archive's listing under `prefix`, every page: (sub-prefixes, keys)."""
    prefixes, keys, marker = [], [], ""
    while True:
        body = _get(LIST.format(p=urllib.parse.quote(prefix), m=urllib.parse.quote(marker)))
        if body is None:
            raise RuntimeError(f"the listing of {prefix} could not be read")
        root = ET.fromstring(body)
        prefixes += [e.text for e in root.iter(f"{S3}Prefix") if e.text and e.text != prefix]
        keys += [e.text for e in root.iter(f"{S3}Key") if e.text]
        if (root.findtext(f"{S3}IsTruncated") or "false").lower() != "true":
            return prefixes, keys
        marker = root.findtext(f"{S3}NextMarker") or (keys[-1] if keys else prefixes[-1])


def parse_month(data: bytes, checksum: bytes) -> list[tuple[str, float, float]]:
    """A month's archive as (UTC date, close, USDT volume), only if its sha256 matches the published one."""
    want = checksum.decode().split()[0].strip().lower()
    if hashlib.sha256(data).hexdigest() != want:
        raise ValueError("sha256 does not match the published checksum")
    z = zipfile.ZipFile(io.BytesIO(data))
    with z.open(z.namelist()[0]) as f:
        rows = [x for x in csv.reader(io.TextIOWrapper(f)) if x and x[0][:1].isdigit()]
    out = []
    for x in rows:
        t = int(float(x[0]))
        t = t // 1_000_000 if t > 10 ** 14 else t // 1000  # microseconds from 2025, milliseconds before
        close, qvol = float(x[4]), float(x[7])
        if not (close > 0 and math.isfinite(close) and qvol >= 0 and math.isfinite(qvol)):
            raise ValueError(f"an invalid close or volume {x[4]!r} {x[7]!r}")
        out.append((datetime.fromtimestamp(t, timezone.utc).date().isoformat(), close, qvol))
    return out


def _month(job: tuple[str, str]) -> tuple[str, str, list | None, str | None]:
    sym, m = job
    url = BASE.format(s=sym, m=m)
    data, chk = _get(url), _get(url + ".CHECKSUM")
    try:
        if data is None or chk is None:
            raise ValueError("not fetched")
        return sym, m, parse_month(data, chk), None
    except Exception as exc:  # noqa: BLE001 - recorded, never filled
        return sym, m, None, str(exc)


def cmd_fetch() -> None:
    DATA.mkdir(parents=True, exist_ok=True)
    root = "data/spot/monthly/klines/"
    syms = sorted(p[len(root):].strip("/") for p in list_s3(root)[0])
    bases = {s[:-4] for s in syms if s.endswith("USDT")}
    coins = [s for s in syms if tradable(s, bases)]
    excluded = sorted(s for s in syms if s.endswith("USDT") and s not in coins)
    jobs = []
    for s in coins:
        listed = {k.rsplit("-1d-", 1)[1][:7] for k in list_s3(f"{root}{s}/1d/")[1] if k.endswith(".zip")}
        jobs += [(s, m) for m in months(FIRST_MONTH, LAST_MONTH) if m in listed]
    print("pairs", len(syms), "coins", len(coins), "excluded", len(excluded), "months", len(jobs), flush=True)
    rows, failed = [], {}
    with ThreadPoolExecutor(16) as ex:
        results = list(ex.map(_month, jobs))
    retry = [(s, m) for s, m, got, why in results if got is None]
    results = [r for r in results if r[2] is not None] + [_month(j) for j in retry]  # one more, one at a time
    for s, m, got, why in results:
        if got is None:
            failed.setdefault(s, []).append({"month": m, "why": why})
        else:
            rows += [(s, d, c, v) for d, c, v in got]
    rows.sort()
    body = gzip.compress(("symbol,date,close,quote_volume\n" + "".join(f"{s},{d},{c!r},{v!r}\n"
                                                                        for s, d, c, v in rows)).encode(), mtime=0)
    (DATA / "klines.csv.gz").write_bytes(body)
    per = {}
    for s, d, _, _ in rows:
        p = per.setdefault(s, {"days": 0, "first": d, "last": d})
        p["days"] += 1
        p["last"] = d
    (DATA / "manifest.json").write_text(_dump({
        "retrieved": datetime.now(timezone.utc).isoformat(), "source": BASE, "file": "klines.csv.gz",
        "sha256": hashlib.sha256(body).hexdigest(), "coins": per, "excluded_pairs": excluded,
        "months_fetched": len(jobs) - sum(len(v) for v in failed.values()), "failed_months": failed}))
    print("rows", len(rows), "failed months", sum(len(v) for v in failed.values()), flush=True)


def load(until: date) -> dict[str, dict[date, tuple[float, float]]]:
    """Each coin's (close, USDT volume) by day, cut at `until` (exclusive), only if the file matches its manifest and
    no month before `until` failed: the judge never reads the holdout, and nothing is filled."""
    man = json.loads((DATA / "manifest.json").read_text())
    body = (DATA / man["file"]).read_bytes()
    if hashlib.sha256(body).hexdigest() != man["sha256"]:
        raise SystemExit(f"{man['file']} does not match its manifest: nothing is judged on it")
    bad = {s: [f["month"] for f in v if f["month"] < until.isoformat()[:7]] for s, v in man["failed_months"].items()}
    bad = {s: v for s, v in bad.items() if v}
    if bad:
        raise SystemExit(f"months not fetched or not checked: {bad}; nothing is filled")
    out: dict[str, dict[date, tuple[float, float]]] = {}
    for ln in gzip.decompress(body).decode().splitlines()[1:]:
        s, d, c, v = ln.split(",")
        day = date.fromisoformat(d)
        if day < until:
            out.setdefault(s, {})[day] = (float(c), float(v))
    return out


# ── the rule, and what it earned ─────────────────────────────────────────

def sundays(start: date, end: date) -> list[date]:
    """The rebalance days in [start, end) whose week also ends before `end`."""
    d = start + timedelta(days=(6 - start.weekday()) % 7)
    out = []
    while d + timedelta(days=7) < end:
        out.append(d)
        d += timedelta(days=7)
    return out


def universe(data: dict, d: date) -> list[str] | None:
    """The coins of the week that starts at d's close, known at that close; None when fewer than MIN_UNIVERSE."""
    ranked = []
    for s, rows in data.items():
        if any(d - timedelta(days=k) not in rows for k in range(HISTORY_DAYS)):
            continue
        ranked.append((-sum(rows[d - timedelta(days=k)][1] for k in range(VOLUME_DAYS)), s))
    top = [s for _, s in sorted(ranked)[:TOP_VOLUME]]
    return top if len(top) >= MIN_UNIVERSE else None


def momentum(rows: dict, d: date) -> float:
    return rows[d][0] / rows[d - timedelta(days=LOOKBACK)][0] - 1.0


def week_return(rows: dict, d: date) -> tuple[float, bool]:
    """From d's close to the next Sunday's, or to the last close in the week (a delisting); 0 with no later close."""
    for k in range(7, 0, -1):
        if d + timedelta(days=k) in rows:
            return rows[d + timedelta(days=k)][0] / rows[d][0] - 1.0, k == 7
    return 0.0, False


def books(data: dict, start: date, end: date, cost: float = COST) -> list[dict]:
    """Each week in [start, end): the book's and the benchmark's gross and net, and the coins held."""
    out: list[dict] = []
    drift = {"book": {}, "bench": {}}
    for d in sundays(start, end):
        coins = universe(data, d)
        row: dict = {"week": d, "coins": coins}
        if coins is None:  # no trade: sell what is held
            for k in drift:
                row[k] = {"gross": 0.0, "net": -cost * sum(drift[k].values())}
                drift[k] = {}
            out.append(row)
            continue
        held = sorted(coins, key=lambda s: (-momentum(data[s], d), s))[:HELD]
        rets = {s: week_return(data[s], d) for s in coins}
        row["held"], row["ended_early"] = held, sorted(s for s in coins if not rets[s][1])
        for k, members in (("book", held), ("bench", coins)):
            target = {s: 1.0 / len(members) for s in members}
            traded = sum(abs(target.get(s, 0.0) - drift[k].get(s, 0.0)) for s in set(target) | set(drift[k]))
            gross = sum(w * rets[s][0] for s, w in target.items())
            row[k] = {"gross": gross, "net": gross - cost * traded}
            drift[k] = {s: w * (1 + rets[s][0]) / (1 + gross) for s, w in target.items()} if gross > -1 else {}
        out.append(row)
    return out


def weekly(xs: list[float]) -> dict:
    n = len(xs)
    if n < 2:
        return {"n": n, "mean": xs[0] if xs else None, "t": None}
    m = sum(xs) / n
    sd = math.sqrt(sum((x - m) ** 2 for x in xs) / (n - 1))
    return {"n": n, "mean": m, "t": m / (sd / math.sqrt(n)) if sd > 0 else None, "sd": sd, "annual": m * 52,
            "annual_sharpe": m / sd * math.sqrt(52) if sd > 0 else None}


def drawdown(xs: list[float]) -> float:
    eq = peak = 1.0
    worst = 0.0
    for x in xs:
        eq *= 1 + x
        peak = max(peak, eq)
        worst = min(worst, eq / peak - 1)
    return worst


def gates(data: dict, thr: float) -> dict:
    rows = books(data, *JUDGE)
    diff = {r["week"]: r["book"]["net"] - r["bench"]["net"] for r in rows}
    s = weekly(list(diff.values()))
    dev = weekly([v for w, v in diff.items() if w < VAL[0]])
    val = weekly([v for w, v in diff.items() if w >= VAL[0]])
    x2 = weekly([r["book"]["net"] - r["bench"]["net"] for r in books(data, *JUDGE, cost=2 * COST)])
    book = weekly([r["book"]["net"] for r in rows])
    by_year: dict = {}
    for w, v in diff.items():
        by_year[w.year] = by_year.get(w.year, 0.0) + v
    total = sum(diff.values())
    top = max(by_year.values()) / total if total > 0 and by_year else None
    ok = {"t": s["t"] is not None and s["t"] >= thr,
          "development": (dev["mean"] or 0) > 0, "validation": (val["mean"] or 0) > 0,
          "costs_x2": (x2["mean"] or 0) > 0, "book_pays": (book["mean"] or 0) > 0,
          "top_year": top is not None and top <= 0.5}
    held: dict = {}
    for r in rows:
        for c in r.get("held") or []:
            held[c] = held.get(c, 0) + 1
    return {"difference": s, "development": dev, "validation": val, "costs_x2": x2, "book_net": book,
            "benchmark_net": weekly([r["bench"]["net"] for r in rows]),
            "book_max_drawdown": round(drawdown([r["book"]["net"] for r in rows]), 4),
            "benchmark_max_drawdown": round(drawdown([r["bench"]["net"] for r in rows]), 4),
            "by_year": {str(k): round(v, 4) for k, v in sorted(by_year.items())},
            "top_year_share": None if top is None else round(top, 3),
            "weeks": len(rows), "weeks_without_trade": sum(1 for r in rows if r["coins"] is None),
            "coin_weeks_ended_early": sum(len(r.get("ended_early") or []) for r in rows),
            "most_held": sorted(held.items(), key=lambda x: (-x[1], x[0]))[:15],
            "threshold_t": thr, "gates": ok, "failed_gates": [g for g, v in ok.items() if not v],
            "passed": all(ok.values())}


# ── the commands ─────────────────────────────────────────────────────────

def _registry() -> Registry:
    return Registry.load(R / "registry.jsonl", Holdout.load(R / "holdout.json"))


def _check_frozen(reg: Registry) -> dict:
    trial = reg.get(PID)
    frozen = json.loads(SPEC.read_text())
    if trial.design.get("spec_sha256") != frozen["sha256"] or frozen["code_sha256"] != code_hash():
        raise SystemExit("the spec or the code differs from what was preregistered")
    return frozen


def cmd_spec() -> None:
    reg = _registry()
    if any(t.id == PID for t in reg.trials):
        raise SystemExit(f"{PID} is registered; its spec is frozen")
    s = spec(reg)
    SPEC.parent.mkdir(parents=True, exist_ok=True)
    SPEC.write_text(_dump({"spec": s, "sha256": spec_sha(s), "code_sha256": code_hash()}))
    print(spec_sha(s), "threshold", s["threshold_t"])


def cmd_preregister(now: datetime) -> None:
    reg = _registry()
    frozen = json.loads(SPEC.read_text())
    s = spec(reg)
    if spec_sha(s) != frozen["sha256"] or code_hash() != frozen["code_sha256"]:
        raise SystemExit("the spec or the code changed since `spec`")
    if frozen["sha256"] not in (ROOT / DOC).read_text():
        raise SystemExit(f"{DOC} must quote the spec sha256 {frozen['sha256']}")
    reg.register(Trial(id=PID, registered=now, title="XSM-1: cross-sectional momentum among the 20 largest Binance "
                                                     "spot coins", hypothesis=s["question"],
                       uses=(Use(UNIVERSE, JUDGE[0], JUDGE[1], "judge"),), tests=TESTS, configurations=TESTS,
                       preregistration=DOC, design={"spec_sha256": frozen["sha256"], "code_sha256": frozen["code_sha256"],
                                                    "threshold_t": s["threshold_t"]}))
    print("registered", PID, "threshold", s["threshold_t"])


def cmd_judge(now: datetime) -> None:
    reg = _registry()
    frozen = _check_frozen(reg)
    if reg.verdict_of(PID) is not None:
        raise SystemExit(f"{PID} already has a verdict")
    res = gates(load(JUDGE[1]), frozen["spec"]["threshold_t"])
    man = json.loads((DATA / "manifest.json").read_text())
    body = _write(PID, {"program": PID, "verdict": "PASSED" if res["passed"] else "FAILED", **res,
                        "periods": frozen["spec"]["periods"], "spec_sha256": frozen["sha256"],
                        "code_sha256": frozen["code_sha256"],
                        "data": {k: man[k] for k in ("retrieved", "source", "file", "sha256", "months_fetched")}
                        | {"coins": len(man["coins"]), "excluded_pairs": len(man["excluded_pairs"])}})
    reg.record_verdict(Verdict(PID, now, body["verdict"], {"artifact": f"research/knowledge/{PID}.json",
                                                           "artifact_sha256": body["sha256"]}))
    print(body["verdict"], "failed:", res["failed_gates"], "difference", json.dumps(res["difference"]), "book",
          json.dumps(res["book_net"]), "weeks", res["weeks"])


def cmd_holdout(now: datetime) -> None:
    reg = _registry()
    frozen = _check_frozen(reg)
    judged = json.loads((OUT / f"{PID}.json").read_text())
    if judged["verdict"] != "PASSED":
        raise SystemExit("XSM-1 did not pass: the holdout stays unread")
    if any(t.id == HID for t in reg.trials):
        raise SystemExit("the holdout was opened once already")
    reg.register(Trial(id=HID, registered=now, title="XSM-1 holdout: 2024-07..2026-09", hypothesis=HOLDOUT_RULE,
                       uses=(Use(UNIVERSE, HOLD[0], HOLD[1], "judge"),), tests=1, configurations=1,
                       preregistration=DOC, design={"spec_sha256": frozen["sha256"]}))
    data = load(HOLD[1])
    rows = books(data, *HOLD)
    s = weekly([r["book"]["net"] - r["bench"]["net"] for r in rows])
    s2 = weekly([r["book"]["net"] - r["bench"]["net"] for r in books(data, *HOLD, cost=2 * COST)])
    book = weekly([r["book"]["net"] for r in rows])
    ok = bool(s["mean"] and s["mean"] > 0 and s["t"] is not None and s["t"] >= NormalDist().inv_cdf(0.95)
              and (s2["mean"] or 0) > 0 and (book["mean"] or 0) > 0)
    verdict = "PASSED" if ok else "FAILED"
    body = _write(HID, {"program": HID, "holdout_of": PID, "period": [str(d) for d in HOLD], "difference": s,
                        "costs_x2": s2, "book_net": book,
                        "book_max_drawdown": round(drawdown([r["book"]["net"] for r in rows]), 4),
                        "rule": HOLDOUT_RULE, "classification": "VALIDATED" if ok else "REJECTED",
                        "verdict": verdict})
    reg.record_verdict(Verdict(HID, now, verdict, {"artifact": f"research/knowledge/{HID}.json",
                                                   "artifact_sha256": body["sha256"]}))
    print(verdict, json.dumps(s), "x2", s2["mean"], "book", book["mean"])


def main() -> int:
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    now = datetime.now(timezone.utc)  # the command line's clock: every function above takes its dates as arguments
    {"spec": cmd_spec, "preregister": lambda: cmd_preregister(now), "fetch": cmd_fetch,
     "judge": lambda: cmd_judge(now), "holdout": lambda: cmd_holdout(now)}.get(cmd, lambda: print(__doc__))()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
