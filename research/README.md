# research/

The research record that travels with the code.

| Path | What it is |
|---|---|
| [`registry.jsonl`](registry.jsonl) | The append-only **experiment registry** ([`aitrader/research/registry.py`](../aitrader/research/registry.py)): every trial, the market periods it used and in which role (fit / select / judge), its test count, and every verdict as a separate line. The archive's earlier verdicts are imported as declared exposure. |
| [`holdout.json`](holdout.json) | The sealed final holdout (fx-majors from 2017-01-01): single use, by a pre-registered final test only. |
| [`preregistrations/`](preregistrations/) | Pre-registration documents, committed **before** their experiments ran. Amendments are appended before the judged run, never after. |
| `results/` | Summaries of completed experiments (full per-trade output stays under `data/results/`, not committed). |
| [`discovery/`](discovery/) | The discovery engine's append-only records: `features.jsonl` (the feature catalog: provenance, budget, leakage status, uses, results) and `ledger.jsonl` (every hypothesis and each step of its lifecycle, rejected ones included). |
| `knowledge/` | What discovery and confirmatory programs concluded: the program artifact, the full screen table, the judged trades, frozen models. Research knowledge only; nothing here is loaded by the running system. See [docs/DISCOVERY.md](../docs/DISCOVERY.md). |

## The research lab

`aitrader/research/lab.py` (with `models.py`, `features_lab.py` and
`hypotheses.py`) runs hypotheses the registry has recorded:

- a declared space;
- registration first, with a frozen Bonferroni threshold;
- purged, embargoed walk-forward;
- random and k-NN baselines;
- robustness checks;
- one verdict per trial;
- artifacts under `research/artifacts/` only.

`scripts/research_lab.py scan | register | run` is the command line. See
docs/GAP_REPORT.md for what it can and cannot do yet.

## Rules the code enforces

- Ids are never reused and entries are never back-dated.
- A verdict is refused on a trial that already has one.
- Significance thresholds count every test on the same universe and
  period (Bonferroni), archive included.
- Any use of the holdout after the seal needs a pre-registration, and a
  second use raises `HoldoutSpent`.

Tests: `tests/unit/test_registry_and_store.py`.

## Binding contracts
[RESEARCH_CONTRACT.md](../RESEARCH_CONTRACT.md) ·
[VALIDATION_CONTRACT.md](../VALIDATION_CONTRACT.md) ·
[docs/RESEARCH_PROCESS.md](../docs/RESEARCH_PROCESS.md)
