"""The instrument universe and the facts about each instrument.

Plausible price bands are narrower than a power of ten on purpose: a raw
feed in points (109305 for 1.09305) must fit exactly one scale or be
refused. A wrong scale raises nothing downstream; it silently measures the
wrong magnitude everywhere (docs/HISTORICAL_ARCHIVE.md).
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Instrument:
    symbol: str
    asset_class: str  # "fx" or "metal"
    pip: float  # the conventional pip, in price units
    band: tuple[float, float]  # plausible price range, used to validate scale
    quote: str  # quote currency

    def in_band(self, price: float) -> bool:
        return self.band[0] <= price <= self.band[1]


def _fx(symbol: str) -> Instrument:
    jpy = symbol.endswith("JPY")
    return Instrument(
        symbol=symbol,
        asset_class="fx",
        pip=0.01 if jpy else 0.0001,
        band=(40.0, 400.0) if jpy else (0.4, 3.0),
        quote=symbol[3:],
    )


UNIVERSE: dict[str, Instrument] = {
    s: _fx(s)
    for s in (
        "EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "USDCAD", "USDCHF",
        "NZDUSD", "EURGBP", "EURJPY", "GBPJPY", "EURCHF", "AUDJPY",
    )
}
UNIVERSE["XAUUSD"] = Instrument("XAUUSD", "metal", 0.1, (200.0, 5000.0), "USD")

#: The name used in the experiment registry for data drawn from this
#: universe. Contamination is a property of MARKET PERIODS, not of files:
#: a second copy of the same prices from another vendor is not unseen.
UNIVERSE_KEY = "fx-majors"


def get(symbol: str) -> Instrument:
    try:
        return UNIVERSE[symbol.upper()]
    except KeyError:
        raise KeyError(f"unknown instrument {symbol!r}; known: {', '.join(sorted(UNIVERSE))}") from None
