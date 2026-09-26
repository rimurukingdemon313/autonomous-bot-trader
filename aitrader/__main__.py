"""Entry point: `python -m aitrader` starts the service (API, dashboard, scheduler)."""

from __future__ import annotations

import sys

from .observability import log_event
from .service.config import ServiceConfig, ServiceConfigError


def main() -> int:
    try:
        cfg = ServiceConfig.from_env()
    except ServiceConfigError as exc:
        log_event("STARTUP", f"configuration refused: {exc}", severity="critical")
        return 2
    from .service.runtime import Runtime
    from .service.server import serve, serve_startup_failure
    try:
        rt = Runtime(cfg)
    except Exception as exc:  # startup incomplete: no trading, but the failure must be visible
        reason = f"{type(exc).__name__}: {exc} (DATA_DIR={cfg.data_dir})"
        log_event("STARTUP", f"startup failed, not trading: {reason}", severity="critical")
        serve_startup_failure(cfg.port, reason)
        return 3
    serve(rt)
    return 0


if __name__ == "__main__":
    sys.exit(main())
