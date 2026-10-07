"""One-off live check of the radar's venue parsers (not part of the radar)."""
import json
import sys
from itertools import permutations
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from aitrader.radar import core as R  # noqa: E402
from aitrader.radar import venues as V  # noqa: E402

quotes, errors = V.snapshot()
out = {"errors": errors, "count": {}, "samples": {}, "now_spreads": []}
for v in V.FETCHERS:
    out["count"][v] = sum(q.venue == v for q in quotes)
for coin in ("BTC", "ETH", "SOL", "DOGE", "PEPE", "XRP", "HYPE", "SUI"):
    out["samples"][coin] = [dict(venue=q.venue, scale=q.scale, apr=round(q.rate_per_hour * 8760, 4), mark=q.mark,
                                 vol=round(q.vol24_usd)) for q in quotes if q.coin == coin]
idx = R._index(quotes)
coins = {}
for q in idx.values():
    coins.setdefault(q.coin, []).append(q)
rules = R.Rules()
multi = [c for c, qs in coins.items() if len(qs) >= 2]
out["coins_on_2plus_venues"] = len(multi)
liq = 0
mism = []
for c in multi:
    l = [q for q in coins[c] if q.vol24_usd >= rules.min_vol_usd]
    best = None
    for a, b in permutations(l, 2):
        if not R.prices_agree(a, b, rules.max_price_gap):
            if a.venue < b.venue:
                mism.append((c, a.venue, a.mark / a.scale, b.venue, b.mark / b.scale))
            continue
        s = (a.rate_per_hour - b.rate_per_hour) * 8760
        if best is None or s > best[0]:
            best = (s, a.venue, b.venue)
    if len(l) >= 2:
        liq += 1
    if best:
        out["now_spreads"].append({"coin": c, "apr": round(best[0], 4), "short": best[1], "long": best[2]})
out["coins_liquid_on_2plus"] = liq
out["price_mismatches"] = mism[:40]
out["n_mismatches"] = len(mism)
out["now_spreads"].sort(key=lambda x: -x["apr"])
out["n_now_spread_ge_25"] = sum(x["apr"] >= 0.25 for x in out["now_spreads"])
out["n_now_spread_ge_15"] = sum(x["apr"] >= 0.15 for x in out["now_spreads"])
out["now_spreads"] = out["now_spreads"][:60]
Path("radar-check.json").write_text(json.dumps(out, indent=1, default=str))
print(json.dumps({k: out[k] for k in ("errors", "count", "coins_on_2plus_venues", "coins_liquid_on_2plus",
                                      "n_mismatches", "n_now_spread_ge_25", "n_now_spread_ge_15")}))
