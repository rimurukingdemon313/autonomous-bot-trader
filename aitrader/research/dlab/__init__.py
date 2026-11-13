"""The discovery lab (docs/DISCOVERY_LAB.md): data-driven discovery, kept apart from validation.

Discovery reads a DISCOVERY window only and may look at anything in it. It demands no significance. What it emits is a
frozen, causal rule with a class and a reason, kept for ever in an append-only ledger. Validation is a preregistered
test on a window discovery never read, at the registry's bar. Research only: nothing here trades.
"""

#: 1.1.0: broad panels. Rules traded on every instrument at once (cross-sectional books, pooled sign rules, a pooled
#: evolutionary search); per-instrument methods read each instrument against the market; a rule's entries count
#: positions opened or reversed.
#: 1.2.0: directed tests. A hypothesis submitted as rules (by the research director, by the idea engine, or by the
#: lab's own coverage map) is frozen, registered and looked at on the discovery rows exactly as a scan's rules are. A
#: book's parts may carry weights, so an aggregate of rules is itself a rule. Nothing a scan computes has changed.
DLAB_VERSION = "dlab-1.2.0"
#: What a discovery scan computes: its methods and its triage. A panel is scanned once for each. Unchanged by 1.2.0, so
#: no panel is scanned again because of it.
SCAN_VERSION = "dlab-1.1.0"
