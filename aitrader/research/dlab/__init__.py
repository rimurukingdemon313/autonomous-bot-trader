"""The discovery lab (docs/DISCOVERY_LAB.md): data-driven discovery, kept apart from validation.

Discovery reads a DISCOVERY window only and may look at anything in it. It demands no significance. What it emits is a
frozen, causal rule with a class and a reason, kept for ever in an append-only ledger. Validation is a preregistered
test on a window discovery never read, at the registry's bar. Research only: nothing here trades.
"""

DLAB_VERSION = "dlab-1.0.0"
