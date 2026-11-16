"""Probe a cTrader DEMO account (docs/CTRADER.md): is it demo, is it swap-free, does it quote the trend desk's four
index CFDs, and what do they really cost? It places no order, and it never refreshes the token (a refresh token works
once: using it here would leave the stored one dead).

    python scripts/ctrader_probe.py --minutes 10 --out DIR    # GitHub's runner, with the CTRADER_* secrets set

Credentials come only from the environment (GitHub secrets). The report names no account number and no secret.
"""

from __future__ import annotations

import argparse
import json
import os
import statistics
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from aitrader.broker.base import BrokerError  # noqa: E402
from aitrader.broker.ctrader import proto as P  # noqa: E402
from aitrader.broker.ctrader.client import Client  # noqa: E402
from aitrader.broker.ctrader.session import ENV, Credentials, open_session, scrub  # noqa: E402
from aitrader.broker.ctrader.transport import DEMO_HOST, DemoRefused, Transport  # noqa: E402
from aitrader.broker.ctrader.symbols import NAMES, match_symbols  # noqa: E402
from aitrader.data.instruments import INDEX_CFDS  # noqa: E402

PROBE_VERSION = "ctrader-probe-1.0.0"
PRICE = 1e5  # spot prices are integers in 1/100000 of a unit (ProtoOASpotEvent)
def spread_summary(samples: list[tuple[float, float]], assumed: float | None) -> dict:
    """Spreads (ask - bid, index points) over every quote update with both sides known. None where there were no
    quotes: never a zero."""
    if not samples:
        return {"quotes": 0, "median": None, "p90": None, "max": None, "median_bp": None, "assumed": assumed,
                "note": "no quotes in the window (market closed, or no price stream)"}
    sp = sorted(s for s, _ in samples)
    mids = [m for _, m in samples]
    med = statistics.median(sp)
    p90 = sp[min(len(sp) - 1, int(0.9 * (len(sp) - 1) + 0.5))]
    mid = statistics.median(mids)
    return {"quotes": len(sp), "median": round(med, 4), "p90": round(p90, 4), "max": round(sp[-1], 4),
            "median_mid": round(mid, 2), "median_bp": round(med / mid * 1e4, 3) if mid > 0 else None,
            "assumed": assumed, "vs_assumed": round(med / assumed, 2) if assumed else None}


def record_spreads(client: Client, account_id: int, ids: dict[int, str], seconds: float, clock=time.monotonic) -> dict:
    """Subscribe to the symbols' prices for `seconds`; a spot event may carry only the side that changed, so each
    side's last value is kept and a spread is counted only when both are known."""
    if not ids:
        return {}
    client.call("ProtoOASubscribeSpotsReq", {"ctidTraderAccountId": account_id, "symbolId": list(ids),
                                             "subscribeToSpotTimestamp": True}, ("ProtoOASubscribeSpotsRes",))
    last: dict[int, list[int | None]] = {i: [None, None] for i in ids}
    samples: dict[int, list[tuple[float, float]]] = {i: [] for i in ids}
    deadline = clock() + seconds
    while True:
        for e in client.drain("ProtoOASpotEvent"):
            sid = e.get("symbolId")
            if sid not in last:
                continue
            if "bid" in e:
                last[sid][0] = e["bid"]
            if "ask" in e:
                last[sid][1] = e["ask"]
            bid, ask = last[sid]
            if bid and ask and ask >= bid:
                samples[sid].append(((ask - bid) / PRICE, (ask + bid) / 2 / PRICE))
        left = deadline - clock()
        if left <= 0:
            break
        client.pump(min(left, 5.0))
    client.call("ProtoOAUnsubscribeSpotsReq", {"ctidTraderAccountId": account_id, "symbolId": list(ids)},
                ("ProtoOAUnsubscribeSpotsRes",))
    return {ids[i]: spread_summary(samples[i], INDEX_CFDS[ids[i]].spread if ids[i] in INDEX_CFDS else None)
            for i in ids}


def _symbol_detail(s: dict) -> dict:
    keep = ("digits", "pipPosition", "lotSize", "minVolume", "stepVolume", "maxVolume", "swapLong", "swapShort",
            "swapRollover3Days", "chargeSwapAtWeekends", "scheduleTimeZone", "enableShortSelling",
            "preciseTradingCommissionRate", "commissionType", "slDistance", "distanceSetIn", "measurementUnits")
    out = {k: s[k] for k in keep if k in s}
    if "tradingMode" in s:
        out["tradingMode"] = P.TRADING_MODE.get(s["tradingMode"], s["tradingMode"])
    if "swapCalculationType" in s:
        out["swapCalculationType"] = P.SWAP_CALCULATION.get(s["swapCalculationType"], s["swapCalculationType"])
    sched = s.get("schedule") or []
    out["open_hours_a_week"] = round(sum(max(0, i.get("endSecond", 0) - i.get("startSecond", 0)) for i in sched)
                                     / 3600, 1) if sched else None
    return out


def probe(client: Client, creds: Credentials, seconds: float, now: datetime, clock=time.monotonic) -> dict:
    rep: dict = {"version": PROBE_VERSION, "time": now.isoformat(), "host": DEMO_HOST, "orders_placed": 0,
                 "status": "STARTED"}
    try:
        s = open_session(client, creds)
    except DemoRefused as e:
        return rep | {"status": "REFUSED", "demo": {"ok": False, "why": str(e)}}
    rep["demo"] = {"ok": True, "why": s.demo.why, "fields": list(s.demo.looked_at)}
    rep["swap_free"] = {"ok": s.swap_free.ok, "why": s.swap_free.why, "fields": list(s.swap_free.looked_at)}
    t = s.trader
    digits = t.get("moneyDigits")
    _, assets = client.call("ProtoOAAssetListReq", {"ctidTraderAccountId": s.account_id}, ("ProtoOAAssetListRes",))
    names = {a.get("assetId"): a.get("name") for a in assets.get("asset", [])}
    rep["account"] = {
        "broker": t.get("brokerName"), "token_scope": s.scope,
        "account_type": P.ACCOUNT_TYPE.get(t.get("accountType", 0)),
        "access_rights": P.ACCESS_RIGHTS.get(t.get("accessRights", 0)),
        "deposit_currency": names.get(t.get("depositAssetId")),
        "balance": (t["balance"] / 10 ** digits) if digits is not None and "balance" in t else None,
        "leverage": (t["leverageInCents"] / 100) if "leverageInCents" in t else None,
        "is_limited_risk": t.get("isLimitedRisk")}
    _, sl = client.call("ProtoOASymbolsListReq", {"ctidTraderAccountId": s.account_id}, ("ProtoOASymbolsListRes",))
    light = sl.get("symbol", [])
    found = match_symbols(light)
    rep["symbols_listed"] = len(light)
    chosen: dict[int, str] = {}
    detail: dict[str, list[dict]] = {}
    wanted = [x["symbolId"] for xs in found.values() for x in xs]
    full = {}
    if wanted:
        _, sb = client.call("ProtoOASymbolByIdReq", {"ctidTraderAccountId": s.account_id, "symbolId": wanted},
                            ("ProtoOASymbolByIdRes",))
        full = {x["symbolId"]: x for x in sb.get("symbol", [])}
    for desk, xs in found.items():
        detail[desk] = [{"name": x.get("symbolName"), "enabled": x.get("enabled"),
                         **_symbol_detail(full.get(x["symbolId"], {}))} for x in xs]
        enabled = [x for x in xs if x.get("enabled") is not False]
        if enabled:
            chosen[enabled[0]["symbolId"]] = desk
    rep["desk_symbols"] = detail
    rep["missing"] = [d for d, xs in found.items() if not xs]
    rep["spreads"] = record_spreads(client, s.account_id, chosen, seconds, clock)
    rep["spread_window_seconds"] = seconds
    try:
        client.call("ProtoOAAccountLogoutReq", {"ctidTraderAccountId": s.account_id}, ("ProtoOAAccountLogoutRes",),
                    timeout=10)
    except BrokerError:
        pass  # the session ends with the connection either way
    rep["status"] = "DONE"
    return rep


def markdown(rep: dict) -> str:
    st = rep.get("status")
    lines = [f"# cTrader demo probe · {rep.get('time')} · no order was placed", ""]
    if st == "NOT_CONFIGURED":
        lines += ["**بالعربي:** الفحص ما اشتغل: أسرار GitHub ناقصة: " + ", ".join(rep.get("missing_settings", [])), ""]
        return "\n".join(lines) + "\n"
    if st == "REFUSED":
        lines += ["**بالعربي:** الحساب انرفض بفحص التجربة (DEMO)، وما انطلب منه أي شي بعد الرفض.", "",
                  f"- Demo check: **REFUSED**. {rep['demo']['why']}", ""]
        return "\n".join(lines) + "\n"
    if st == "ERROR":
        lines += ["**بالعربي:** الفحص وقف بخطأ، والسبب مكتوب جوه.", "", f"- Error: {rep.get('error')}", ""]
        return "\n".join(lines) + "\n"
    a, sf = rep["account"], rep["swap_free"]
    ar = ("الحساب تجريبي حسب سجل الوسيط نفسه. "
          + ("وبدون فوائد (swap-free) حسب سجل الوسيط." if sf["ok"] else
             "بس الوسيط ما يكول إنه بدون فوائد، فما ينفتح عليه أي أمر لحد ما يصير بدون فوائد.")
          + (" المؤشرات الأربعة موجودة." if not rep["missing"] else
             " ناقص من المؤشرات: " + ", ".join(rep["missing"]) + "."))
    lines += [f"**بالعربي:** {ar}", "", "| | |", "|---|---|",
              f"| Demo | {rep['demo']['why']} |",
              f"| Swap-free | {'YES' if sf['ok'] else 'NO'}: {sf['why']} |",
              f"| Broker | {a.get('broker')} ({a.get('account_type')}, {a.get('access_rights')}, token "
              f"{a.get('token_scope')}) |",
              f"| Balance | {a.get('balance')} {a.get('deposit_currency') or ''} (leverage "
              f"{a.get('leverage')}) |", ""]
    lines += ["## The desk's indices at this broker", "",
              "| Desk | Broker symbol | Spread median | p90 | max | bp | Assumed | Quotes | Swap long/short (type) | "
              "Min volume | Hours a week |", "|---|---|---|---|---|---|---|---|---|---|---|"]
    for desk in NAMES:
        xs = rep["desk_symbols"].get(desk) or []
        sp = rep["spreads"].get(desk) or {}
        if not xs:
            lines.append(f"| {desk} | not found | | | | | | | | | |")
            continue
        x = xs[0]
        lines.append(f"| {desk} | {x.get('name')} | {sp.get('median')} | {sp.get('p90')} | {sp.get('max')} | "
                     f"{sp.get('median_bp')} | {sp.get('assumed')} | {sp.get('quotes')} | {x.get('swapLong')}/"
                     f"{x.get('swapShort')} ({x.get('swapCalculationType')}) | {x.get('minVolume')} | "
                     f"{x.get('open_hours_a_week')} |")
    lines += ["", f"Spreads are in index points, over every price update in a {rep['spread_window_seconds']:.0f}-second "
                  "window; 'Assumed' is the desk's declared spread (aitrader/data/instruments.py). Volumes are in 0.01 "
                  "of a unit (cTrader's definition). A symbol's swap terms are the instrument's; the account's "
                  "swap-free flag decides whether they are charged.", ""]
    return "\n".join(lines) + "\n"


def write(out: Path, rep: dict, secrets: tuple[str, ...]) -> None:
    out.mkdir(parents=True, exist_ok=True)
    body = scrub(json.dumps(rep, indent=1, sort_keys=True, default=str), secrets)
    (out / "probe.json").write_text(body + "\n")
    (out / "REPORT.md").write_text(scrub(markdown(json.loads(body)), secrets))


def main(argv=None, env=None, connect=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--minutes", type=float, default=10.0)
    ap.add_argument("--out", type=Path, required=True)
    a = ap.parse_args(argv)
    env = os.environ if env is None else env
    now = datetime.now(timezone.utc)  # the command line's clock: probe() takes it as an argument
    creds, missing = Credentials.from_env(env)
    if creds is None:
        rep = {"version": PROBE_VERSION, "time": now.isoformat(), "status": "NOT_CONFIGURED", "orders_placed": 0,
               "missing_settings": missing, "expected_settings": list(ENV)}
        write(a.out, rep, ())
        print(f"NOT CONFIGURED: missing {', '.join(missing)} (GitHub: Settings > Secrets and variables > Actions)")
        return 1
    secrets = creds.secrets()
    client = None
    try:
        client = Client(Transport(connect=connect))
        rep = probe(client, creds, max(0.0, a.minutes) * 60, now)
    except (BrokerError, P.ProtoError, OSError) as e:
        rep = {"version": PROBE_VERSION, "time": now.isoformat(), "status": "ERROR", "orders_placed": 0,
               "error": f"{type(e).__name__}: {e}"}
    finally:
        if client is not None:
            client.transport.close()
    write(a.out, rep, secrets)
    print(scrub(json.dumps({k: rep.get(k) for k in ("status", "demo", "swap_free", "missing", "spreads", "error")},
                           default=str), secrets))
    return 0 if rep["status"] == "DONE" else 1


if __name__ == "__main__":
    raise SystemExit(main())
