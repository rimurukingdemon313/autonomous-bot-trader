"""Loading validated bars, with the final holdout enforced in the loader.

Research code cannot read the sealed period by accident: `DataStore.load`
truncates every series at the holdout start unless it is handed a
`HoldoutKey`, and the only way to get a key is `open_final_test`, which
requires a pre-registered PENDING trial in the registry that is the first
post-seal use of the holdout (VALIDATION_CONTRACT.md §8).

Production (paper/demo) reads live data from the broker, not this store,
so the seal constrains research without blinding the running system.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date
from functools import lru_cache
from pathlib import Path

import numpy as np

from ..research.registry import Holdout, Registry, RegistryError
from . import instruments
from .bars import BarSeries
from .resample import resample
from .validate import validate


class DataUnavailable(RuntimeError):
    """The requested data does not exist or failed validation."""


@dataclass(frozen=True)
class HoldoutKey:
    trial_id: str


def open_final_test(registry: Registry, trial_id: str) -> HoldoutKey:
    """The one door into the sealed period."""
    h = registry.holdout
    if h is None:
        raise RegistryError("no holdout is defined")
    trial = registry.get(trial_id)
    if registry.status_of(trial_id) != "PENDING":
        raise RegistryError(f"{trial_id} is not pending")
    if not trial.preregistration:
        raise RegistryError(f"{trial_id} is not pre-registered")
    if not any(u.overlaps(h.universe, h.start, date.max) for u in trial.uses):
        raise RegistryError(f"{trial_id} does not declare use of the holdout")
    users = [t.id for t in registry.touching(h.universe, h.start, date.max)
             if t.registered >= h.sealed_at]
    if users != [trial_id]:
        raise RegistryError(f"the holdout's post-seal users are {users}; only a sole first user may open it")
    return HoldoutKey(trial_id)


class DataStore:
    def __init__(self, root: Path | str, holdout: Holdout | None) -> None:
        self.root = Path(root)
        self.holdout = holdout
        manifest = self.root.parent / "manifest.json"
        self.manifest = json.loads(manifest.read_text()) if manifest.exists() else {"datasets": {}}

    def symbols(self) -> list[str]:
        return sorted(s for s, d in self.manifest.get("datasets", {}).items()
                      if "error" not in d and (self.root / d["file"]).exists())

    @lru_cache(maxsize=64)
    def _raw(self, symbol: str) -> BarSeries:
        entry = self.manifest.get("datasets", {}).get(symbol)
        if not entry or "error" in entry:
            raise DataUnavailable(f"{symbol}: not ingested ({(entry or {}).get('error', 'missing')})")
        series = BarSeries.load(self.root / entry["file"])
        if series.content_hash() != entry["content_sha256"]:
            raise DataUnavailable(f"{symbol}: file does not match its manifest hash; refusing to use it")
        report = validate(series, instruments.get(symbol))
        if not report.usable:
            raise DataUnavailable(f"{symbol}: failed validation: {report.hard}")
        return series

    def load(self, symbol: str, timeframe: str = "M15", *, key: HoldoutKey | None = None) -> BarSeries:
        series = self._raw(symbol.upper())
        if self.holdout is not None and key is None:
            cutoff = self.holdout.start_epoch()
            series = series.take(slice(0, int(np.searchsorted(series.open_time, cutoff, side="left"))))
            as_of = cutoff
        else:
            as_of = int(series.available_at[-1]) if len(series) else 0
        if timeframe == "M15":
            return series
        return resample(series, timeframe, as_of=as_of)
