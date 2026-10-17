"""One-off diagnostic (side branch only): can the runner read the economic calendar the news rule needs
(risk 1.10.0 stands aside without one)? Reads ForexFactory's public weekly feed. Never trades."""
import json, sys, time
from pathlib import Path
sys.path.insert(0, ".")
from aitrader.data.calendar import CALENDAR_URL, EconomicCalendar

out = Path(sys.argv[1]); out.mkdir(parents=True, exist_ok=True)
cal = EconomicCalendar(out / "calendar_cache.json")
now = int(time.time())
st = cal.state()
views = {s: cal.for_symbol(s, now) for s in ("EURUSD", "GBPUSD", "USDJPY")}
high = []
with cal._lock:
    events = list(cal._events)
for e in events:
    if str(e.get("impact")) == "High":
        high.append({k: e.get(k) for k in ("date", "country", "title", "impact", "forecast", "previous")})
lines = [f"url {CALENDAR_URL}", f"state {json.dumps(st)}", f"events in feed {len(events)}; High impact {len(high)}", ""]
lines += [f"{h['date']} {h['country']} {h['title']} (forecast {h['forecast']}, previous {h['previous']})" for h in high[:60]]
lines += ["", "for_symbol EURUSD feed: " + json.dumps(views["EURUSD"]["feed"])]
(out / "REPORT.md").write_text("\n".join(lines) + "\n")
(out / "calendar.json").write_text(json.dumps({"state": st, "high": high, "views": views}, indent=1, default=str))
print("\n".join(lines[:8]))
