"""Authority boundaries, checked in the source: who may import what.

A reasoning or research module that imported the broker or the execution
engine could reach the market without the risk engine. These tests read the
import graph itself, so a new shortcut fails here even if nothing calls it yet.
"""

from __future__ import annotations

import ast
import re
from pathlib import Path

PKG = Path(__file__).resolve().parents[2] / "aitrader"


def imports_of(path: Path) -> set[str]:
    tree = ast.parse(path.read_text())
    out = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            mod = node.module or ""
            if node.level:  # relative: resolve against the package
                base = path.relative_to(PKG).parts[:-node.level]
                mod = ".".join(("aitrader", *base, *(mod.split(".") if mod else ())))
            out.add(mod)
        elif isinstance(node, ast.Import):
            out |= {a.name for a in node.names}
    return out


def modules(*dirs: str):
    for d in dirs:
        yield from (PKG / d).rglob("*.py")


FORBIDDEN_FOR_REASONING = ("aitrader.broker", "aitrader.execution", "aitrader.service")


def test_reasoning_and_research_cannot_reach_the_broker_or_execution():
    bad = []
    for path in modules("agents", "decision", "research", "learning", "llm", "memory", "regime", "features"):
        for mod in imports_of(path):
            if mod.startswith(FORBIDDEN_FOR_REASONING):
                bad.append(f"{path.relative_to(PKG)} imports {mod}")
    assert bad == []


def test_only_the_risk_engine_computes_a_position_size():
    sizing = re.compile(r"\bqty\s*=|\blots?\s*=|position_size\s*=")
    offenders = []
    for path in PKG.rglob("*.py"):
        rel = path.relative_to(PKG).as_posix()
        if rel.startswith(("risk/", "broker/")):  # the engine sizes; brokers carry the size they are given
            continue
        for i, line in enumerate(path.read_text().splitlines(), 1):
            if sizing.search(line.split("#")[0]):
                offenders.append(f"{rel}:{i}: {line.strip()}")
    allowed = ("execution/engine.py",)  # passes verdict.qty through, never computes it
    assert [o for o in offenders if not o.startswith(allowed)] == []


def test_the_research_lab_is_not_imported_by_the_live_decision_path():
    # Everything that runs: the orchestrator and the service too (the orchestrator once imported
    # research.hypotheses, and with it the lab, to write experiment proposals).
    live = ("agents", "decision", "risk", "execution", "broker", "orchestrator", "service", "learning", "memory", "llm")
    bad = [f"{p.relative_to(PKG)}" for p in modules(*live)
           if imports_of(p) & {"aitrader.research.lab", "aitrader.research.models", "aitrader.research.features_lab",
                               "aitrader.research.hypotheses"}]
    assert bad == []


def test_nothing_that_runs_imports_the_discovery_engine():
    """Discovery is research: a VALIDATED hypothesis is knowledge, never a rule the system executes."""
    bad = [f"{p.relative_to(PKG)}" for p in PKG.rglob("*.py")
           if not p.relative_to(PKG).as_posix().startswith("research/discovery/")
           and any(m.startswith("aitrader.research.discovery") for m in imports_of(p))]
    assert bad == []


def test_the_discovery_engine_reads_only_data_features_and_research():
    allowed = ("aitrader.data", "aitrader.features", "aitrader.research")
    bad = [f"{p.relative_to(PKG)} imports {m}" for p in modules("research/discovery") for m in imports_of(p)
           if m.startswith("aitrader") and not m.startswith(allowed)]
    assert bad == []  # no risk engine, execution, broker, service, orchestrator, agents, memory or llm client


def test_only_the_execution_engine_sends_an_order():
    """The broker's write is called from one place, right after the hard risk gate (docs/HARD_RISK_GATE.md). A second
    caller would be a second path to the market; it would still need the gate's permit, but it should not exist."""
    callers = [p.relative_to(PKG).as_posix() for p in PKG.rglob("*.py") if ".place_market(" in p.read_text()]
    assert callers == ["execution/engine.py"]
