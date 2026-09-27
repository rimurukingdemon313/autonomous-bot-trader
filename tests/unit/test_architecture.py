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
    live = ("agents", "decision", "risk", "execution", "broker")
    bad = [f"{p.relative_to(PKG)}" for p in modules(*live)
           if imports_of(p) & {"aitrader.research.lab", "aitrader.research.models", "aitrader.research.features_lab",
                               "aitrader.research.hypotheses"}]
    assert bad == []
