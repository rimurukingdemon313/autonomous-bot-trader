"""TRND-1 on the owner's cTrader DEMO account, run by the system itself (aitrader/position/demo_desk.py,
docs/CTRADER.md).

    python scripts/demo_desk.py --state DIR [--clear-kill-switch REASON] [--resume REASON]

Each run, on GitHub's runner on weekday mornings while the index CFDs trade:

1. Read Yahoo's final daily bars for the four indices, with the paper desk's own reader (scripts/trend_desk.py).
2. Open the demo connection.
   - Demo and swap-free are checked from the broker's own records.
   - A failed demo check trips the kill switch, and nothing is sent.
3. Run the desk once (demo_desk.run).
4. Write the report (REPORT.md, state.json) next to the account's journal (demo.db). The workflow carries all three
   on the demo-desk-data branch.

Credentials come only from the environment (GitHub secrets), never from a file or an argument. Without them the run
reports NOT CONFIGURED and sends nothing.

`--clear-kill-switch` and `--resume` are a person's acts, made through a hand-started run. Each is recorded with its
reason. A pause is lifted only when no order's outcome is still unknown.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from aitrader.broker.base import BrokerError  # noqa: E402
from aitrader.broker.ctrader import proto as P  # noqa: E402
from aitrader.broker.ctrader.broker import CTraderBroker  # noqa: E402
from aitrader.broker.ctrader.client import Client  # noqa: E402
from aitrader.broker.ctrader.session import Credentials, open_session, scrub  # noqa: E402
from aitrader.broker.ctrader.symbols import match_symbols  # noqa: E402
from aitrader.broker.ctrader.transport import DemoRefused, Transport  # noqa: E402
from aitrader.memory.db import Database  # noqa: E402
from aitrader.position import demo_desk as D  # noqa: E402
from aitrader.position.trend_desk import INDICES, DailyFeed  # noqa: E402
from aitrader.version import stamp  # noqa: E402
from scripts import trend_desk as TD  # noqa: E402  (the paper desk's Yahoo reader, unchanged)

START_KEY = "demo_start_balance"


def symbol_map(client: Client, account_id: int) -> tuple[dict[str, int], list[dict], dict[int, dict]]:
    """The desk's indices at this broker: (desk name -> symbolId, the light symbols, the details of those mapped)."""
    _, sl = client.call("ProtoOASymbolsListReq", {"ctidTraderAccountId": account_id}, ("ProtoOASymbolsListRes",))
    light = sl.get("symbol", [])
    ids = {}
    for desk, xs in match_symbols(light).items():
        enabled = [x for x in xs if x.get("enabled") is not False]
        if enabled:
            ids[desk] = enabled[0]["symbolId"]
    details = {}
    if ids:
        _, sb = client.call("ProtoOASymbolByIdReq", {"ctidTraderAccountId": account_id,
                                                     "symbolId": sorted(ids.values())}, ("ProtoOASymbolByIdRes",))
        details = {x["symbolId"]: x for x in sb.get("symbol", [])}
    return ids, light, details


def operator_acts(db: Database, clear: str | None, resume: str | None) -> list[str]:
    done = []
    if clear:
        db.set_kv("kill_switch", {"active": False, "cleared_by": "a person, by a hand-started run", "reason": clear},
                  reason=f"kill switch cleared by a person: {clear}")
        done.append(f"kill switch cleared: {clear}")
    if resume:
        unknown = db.query("SELECT id FROM intents WHERE status IN ('SUBMITTING', 'UNKNOWN')")
        if unknown:
            done.append(f"NOT resumed: {len(unknown)} order(s) still have an unknown outcome")
        else:
            db.set_kv("paused", False, reason=f"resumed by a person: {resume}")
            done.append(f"resumed: {resume}")
    return done


def report(state: dict) -> str:
    st = state.get("status")
    lines = ["# DEMO DESK · TRND-1 on a cTrader demo account · DEMO ONLY · NOT REAL MONEY", ""]
    if st == "NOT_CONFIGURED":
        return "\n".join(lines + ["**بالعربي:** ما اشتغل: أسرار GitHub ناقصة: " + ", ".join(state["missing"]), ""])
    if st in ("REFUSED", "ERROR"):
        return "\n".join(lines + [f"**بالعربي:** وقف ({st}): {state.get('why')}. ما انبعث أي أمر.", ""])
    a = state["account"]
    held = [p["symbol"] for p in state["positions"]]
    ks, paused = state["kill_switch"], state["paused"]
    lines += [f"**بالعربي:** حساب تجربة عند {a.get('broker')}. الرصيد {a.get('balance')} والقيمة مع المفتوح "
              f"{a.get('equity')} {a.get('currency') or ''}. "
              + ("ماسك: " + "، ".join(held) + ". " if held else "ما ماسك شي. ")
              + ("مفتاح الإيقاف شغّال: ما يتداول لحد ما شخص يطفيه. " if ks.get("active") is not False else "")
              + ("التداول موقوف لحد ما تنقرا نتيجة أمر مجهول. " if paused else "")
              + ("القاعدة مو مرقّاة للتجربة بعد، فما ينبعث أي أمر. " if not state["promoted"] else "")
              + "هذا حساب تجربة، مو فلوس حقيقية.", ""]
    lines += ["| | |", "|---|---|", f"| Broker | {a.get('broker')} (swap-free: {state['swap_free']}) |",
              f"| Balance / equity | {a.get('balance')} / {a.get('equity')} {a.get('currency') or ''} |",
              f"| Starting balance (the gate's reference) | {state['start_balance']} |",
              f"| Rule | {state['rules_note']} |",
              f"| Kill switch | {json.dumps(ks, ensure_ascii=False)} |", f"| Paused | {paused} |",
              f"| Updated | {state['updated']} |", "", "## Positions", "",
              "| Index | Units | Entry | Stop | Client id |", "|---|---|---|---|---|"]
    for p in state["positions"]:
        lines.append(f"| {p['symbol']} | {p['qty']} | {p['entry']} | {p['stop']} | {p['client_id']} |")
    if not state["positions"]:
        lines.append("| none | | | | |")
    lines += ["", "## This run", "", "| Kind | Index | Action | Result | Detail |", "|---|---|---|---|---|"]
    for e in state["events"]:
        lines.append(f"| {e.get('kind')} | {e.get('symbol', '')} | {e.get('action', '')} | {e.get('result', '')} | "
                     f"{str(e.get('detail') or e.get('why') or '')[:160]} |")
    if state.get("acts"):
        lines += ["", "## A person's acts this run", ""] + [f"- {x}" for x in state["acts"]]
    if state.get("problems"):
        lines += ["", "## Data problems", ""] + [f"- {x}" for x in state["problems"]]
    return "\n".join(lines) + "\n"


def main(argv=None, env=None, connect=None, fetch=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--state", required=True, type=Path)
    ap.add_argument("--clear-kill-switch", default="")
    ap.add_argument("--resume", default="")
    a = ap.parse_args(argv)
    env = os.environ if env is None else env
    now = datetime.now(timezone.utc)  # the command line's clock: everything below takes it as an argument
    a.state.mkdir(parents=True, exist_ok=True)
    out = {"version": D.DEMO_DESK_VERSION, "updated": now.isoformat(), "demo_only": True, "real_money": False}
    creds, missing = Credentials.from_env(env)
    secrets = creds.secrets() if creds else ()

    def finish(state: dict, rc: int) -> int:
        body = scrub(json.dumps(state, indent=1, sort_keys=True, default=str), secrets)
        (a.state / "state.json").write_text(body + "\n")
        (a.state / "REPORT.md").write_text(scrub(report(json.loads(body)), secrets))
        print(scrub(json.dumps({k: state.get(k) for k in ("status", "why", "positions", "acts")}, default=str), secrets))
        return rc

    if creds is None:
        return finish(out | {"status": "NOT_CONFIGURED", "missing": missing}, 0)
    db = Database(a.state / "demo.db")
    acts = operator_acts(db, a.clear_kill_switch.strip() or None, a.resume.strip() or None)
    bars, rates, problems = (fetch or TD.fetch)(now)
    client = None
    try:
        client = Client(Transport(connect=connect))
        session = open_session(client, creds)
        ids, light, details = symbol_map(client, session.account_id)
        clock = (lambda: int(datetime.now(timezone.utc).timestamp()))
        broker = CTraderBroker(session, creds, ids, light, details, clock, on_refusal=lambda why: D.trip(db, why))
        start = db.get_kv(START_KEY, None)
        if start is None:
            start = broker.account().balance
            db.set_kv(START_KEY, start, reason="the demo desk's first run: the account's starting balance")
        rules, note = D.load_demo_rules()
        desk = D.build(db, broker, DailyFeed(bars, rates), clock, rules, float(start), note)
        events = D.run(desk, bars, clock())
        acct = broker.account()
        state = out | {"status": "DONE", "acts": acts, "problems": problems, "start_balance": start,
                       "rules_note": note, "promoted": any(r.rule_id == D.RULE_ID for r in rules),
                       "swap_free": session.swap_free.ok, "kill_switch": db.get_kv("kill_switch", None),
                       "paused": bool(db.get_kv("paused", False)),
                       "account": {"broker": session.trader.get("brokerName"), "balance": round(acct.balance, 2),
                                   "equity": round(acct.equity, 2), "currency": acct.currency},
                       "positions": [{"symbol": p.symbol, "qty": p.qty, "entry": p.entry, "stop": p.stop,
                                      "client_id": p.client_id} for p in broker.positions() if p.symbol in INDICES],
                       "mapped": sorted(ids), "events": events, "versions": stamp()}
        rc = 0
    except DemoRefused as e:
        D.trip(db, str(e))
        state, rc = out | {"status": "REFUSED", "why": str(e), "acts": acts}, 1
    except (BrokerError, P.ProtoError, OSError) as e:
        state, rc = out | {"status": "ERROR", "why": f"{type(e).__name__}: {e}", "acts": acts}, 1
    finally:
        if client is not None:
            client.transport.close()
    db.query("PRAGMA wal_checkpoint(TRUNCATE)")
    return finish(state, rc)


if __name__ == "__main__":
    raise SystemExit(main())
