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
UNIVERSE["XAGUSD"] = Instrument("XAGUSD", "metal", 0.001, (8.0, 60.0), "USD")

#: The name used in the experiment registry for data drawn from this
#: universe. Contamination is a property of MARKET PERIODS, not of files:
#: a second copy of the same prices from another vendor is not unseen.
UNIVERSE_KEY = "fx-majors"


def get(symbol: str) -> Instrument:
    try:
        return UNIVERSE[symbol.upper()]
    except KeyError:
        raise KeyError(f"unknown instrument {symbol!r}; known: {', '.join(sorted(UNIVERSE))}") from None


def price_scale(symbol: str, raw_median: float) -> float:
    """The single power of ten that puts a raw median price inside the band.

    Exactly one must fit. None, or more than one, is an error: a wrong scale
    raises nothing downstream and silently measures the wrong magnitude
    everywhere (costs in pips, spreads, the band checks themselves).
    """
    inst = get(symbol)
    fits = [10.0 ** k for k in range(-6, 5) if inst.in_band(raw_median * 10.0 ** k)]
    if len(fits) != 1:
        raise ValueError(f"{symbol}: raw median {raw_median:g} fits {len(fits)} scales {fits}; refusing to guess")
    return fits[0]
