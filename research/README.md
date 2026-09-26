# research/

The research record that travels with the code.

| Path | What it is |
|---|---|
| [`registry.jsonl`](registry.jsonl) | The append-only **experiment registry** ([`aitrader/research/registry.py`](../aitrader/research/registry.py)): every trial, the market periods it used and in which role (fit / select / judge), its test count, and every verdict as a separate line. The archive's earlier verdicts are imported as declared exposure. |
| [`holdout.json`](holdout.json) | The sealed final holdout (fx-majors from 2017-01-01): single use, by a pre-registered final test only. |
| [`preregistrations/`](preregistrations/) | Pre-registration documents, committed **before** their experiments ran. Amendments are appended before the judged run, never after. |
| `results/` | Summaries of completed experiments (full per-trade output stays under `data/results/`, not committed). |

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
