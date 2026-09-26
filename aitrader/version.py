"""Component versions (docs/VERSIONING.md).

Every behaviour change bumps the matching component. Every decision and
every experiment records `stamp()`, and results are analysed per version.
"""

from __future__ import annotations

from .features.store import FEATURE_VERSION
from .research.labels import LABEL_VERSION

DATA_VERSION = "data-1.0.0"


def stamp() -> dict[str, str]:
    return {"data": DATA_VERSION, "features": FEATURE_VERSION, "labels": LABEL_VERSION}
