"""Radar probe: which public funding-rate endpoints answer from a GitHub runner (status code and record count only)."""

from __future__ import annotations

import json
import sys
import urllib.request

ENDPOINTS = {
    "hyperliquid": ("POST", "https://api.hyperliquid.xyz/info", {"type": "metaAndAssetCtxs"}),
    "binance": ("GET", "https://fapi.binance.com/fapi/v1/premiumIndex", None),
    "bybit": ("GET", "https://api.bybit.com/v5/market/tickers?category=linear", None),
    "okx": ("GET", "https://www.okx.com/api/v5/public/mark-price?instType=SWAP", None),
    "gate": ("GET", "https://api.gateio.ws/api/v4/futures/usdt/contracts", None),
    "kraken_futures": ("GET", "https://futures.kraken.com/derivatives/api/v3/tickers", None),
    "dydx": ("GET", "https://indexer.dydx.trade/v4/perpetualMarkets", None),
    "bitget": ("GET", "https://api.bitget.com/api/v2/mix/market/tickers?productType=USDT-FUTURES", None),
    "mexc": ("GET", "https://contract.mexc.com/api/v1/contract/funding_rate", None),
}


def main(out: str) -> int:
    res = {}
    for name, (method, url, body) in ENDPOINTS.items():
        try:
            data = json.dumps(body).encode() if body else None
            req = urllib.request.Request(url, data=data, method=method, headers={
                "Content-Type": "application/json", "User-Agent": "Mozilla/5.0 (radar probe)"})
            with urllib.request.urlopen(req, timeout=30) as r:
                raw = r.read()
                res[name] = {"status": r.status, "bytes": len(raw)}
        except Exception as exc:  # noqa: BLE001
            res[name] = {"error": str(exc)[:200]}
    json.dump(res, open(out, "w"), indent=1)
    print(json.dumps(res, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1]))
