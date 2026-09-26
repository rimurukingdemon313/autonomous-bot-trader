# dashboard/

**Status: implemented** in [`aitrader/service/static/`](../aitrader/service/static/),
served by [`aitrader/service/server.py`](../aitrader/service/server.py).

Presentation only. Every panel reads a real endpoint; a value the system
does not have is shown as N/A with the reason, never as zero.

Panels: status bar, account, market and chart, AI pipeline, agent
opinions, decision flow, risk, trades, memory and learning, learning
progression, post-mortems, performance, research, health, logs.

Controls are split by **direction**:

| Control | Needs `DASHBOARD_TOKEN`? |
|---|---|
| Emergency stop, pause | no: anyone who can reach it can make the system safer |
| Resume, clear stop, scan now, revert knowledge, verify | yes; refused entirely if no token is configured |

No control can open, size or close a trade. Mobile-first: a single column,
tap targets of 38 px or more, tables scroll inside their own box.

Tests: `tests/integration/test_service.py` (real HTTP).

## Binding contracts
[ARCHITECTURE.md](../ARCHITECTURE.md) · [SECURITY_CONTRACT.md](../SECURITY_CONTRACT.md)
