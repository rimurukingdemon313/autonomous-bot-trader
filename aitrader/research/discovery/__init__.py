"""The discovery engine: from market data to accepted or rejected knowledge, under statistical control.

    MARKET DATA -> FEATURE/STATE DISCOVERY (primitives, catalog) -> PATTERN DISCOVERY (screen)
    -> HYPOTHESIS GENERATION (hypothesis) -> REGISTRATION (registry + ledger) -> VALIDATION
    (battery: walk-forward years, out-of-sample, costs, regimes, instruments, permutation,
    deflated Sharpe) -> RESEARCH BOARD (five analysts, synthesis) -> ACCEPT / REJECT
    -> VERSIONED KNOWLEDGE -> NEXT HYPOTHESES (program)

Research only. Nothing in this package is imported by the running system; a VALIDATED
hypothesis is a research artifact, not a trading rule (tests/unit/test_discovery_authority.py).
"""
