# models/

**Status: the research knowledge base is built by
[`scripts/build_knowledge.py`](../scripts/build_knowledge.py) into
`models/artifacts/`.**

| File | What it is |
|---|---|
| `artifacts/memory.npz` | Historical-analogue memory: one row per past decision situation (18 standardised features) with the realised R of every action template, and the time each outcome became known. float16 on disk. |
| `artifacts/regime.json` | Regime quantiles and the familiarity distribution, fitted on training rows only. |
| `artifacts/knowledge_card.json` | The card: data range (always before the sealed holdout), symbols, dataset hashes, feature/label/memory/regime versions, code commit, the SHA-256 of the two files above, and its **status**. |

## Loading rules (enforced in `aitrader/service/runtime.py`)

- The service loads the base only if SHA-256(`memory.npz` + `regime.json`)
  equals the card's `sha256`. A missing card or file, or a different hash,
  loads **nothing**: no regime model means no cycle decides. The dashboard
  shows `KNOWLEDGE: MISSING | INCOMPLETE | MISMATCH`.
- The card's status is shown as it is. A `RESEARCH_CANDIDATE` may run in
  paper or demo as a forward test (docs/SYSTEM_LIFECYCLE.md, Amendment 1),
  labelled unvalidated. LIVE needs a VALIDATED status and every gate.
- The running system grows its own memory from forward outcomes
  (`DATA_DIR/memory_live.npz`). It never rewrites the base.
- No model computes a position size or a risk amount.

## Research model families (not loaded by production)

`aitrader/research/models.py`:

- **ridge**, **logistic** and **k-NN**, in numpy, each with fixed,
  recorded hyper-parameters;
- a lab PASS writes a hashed artifact under `research/artifacts/<trial>/`;
- production does not load from there. Promotion is a reviewed step that
  includes the holdout test;
- tree/boosting, time-series and Bayesian families are **not
  implemented**. `MODEL_FAMILIES` is the declared plug-in point.

The current production estimator, the analogue memory above, is a k-NN
lookup. It is not a trained model.

## Language models

No model weights live here. The optional language-model layer is a
provider configured by environment variables (docs/AI_MODELS.md).

## Binding contracts
[MODEL_CONTRACT.md](../MODEL_CONTRACT.md) · [docs/VERSIONING.md](../docs/VERSIONING.md)
