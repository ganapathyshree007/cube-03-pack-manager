# Receiving Manager Architecture

## 1. Purpose

The Receiving Manager verifies whether received inventory matches the expected purchase-order information and records evidence for each inspection decision.

The system must not invent evidence. When available evidence is insufficient, the inspection returns `UNCERTAIN`.

---

## 2. Inspection Flow

```text
Purchase Order
      +
Product Specification
      +
Receiving Photos
      ↓
Receiving Inspection Agent
      ↓
┌─────────────────────────────┐
│ Identity                    │
│ Carton Count                │
│ Units per Carton            │
│ Quantity                    │
│ Carton Damage               │
│ Unit Damage                 │
│ Colour                      │
│ Variant                     │
│ Components                  │
│ Quality Flags               │
└─────────────────────────────┘
      ↓
Evidence + Verdicts
      ↓
PASS / FAIL / UNCERTAIN
      ↓
Decision Trace
      ↓
Evidence Record
```

## 3. Vision Adapter Boundary

`agent/vision_adapter.py` is the only model-facing layer. For one receiving
unit it sends one request containing the expected PO/product fields, all image
references and all ten required checks. The model returns observations only:
`observed_value`, `evidence` source references, `uncertainty`, and `reason`.

The adapter validates the complete response and rejects missing fields,
unavailable image references, invalid values, and malformed JSON. It maps the
observations into the existing flat input used by `inspection_agent.py`, which
remains responsible for PASS/FAIL/UNCERTAIN comparisons and the decision trace.
The model never produces the final verdict. Missing visual evidence produces
UNCERTAIN checks. Model failures and invalid responses preserve the receiving
record and return `status: "pending"` with a `pending_review` finding.

The provider is injected as a callable receiving one payload, so provider
credentials and SDK choices remain outside this repository's decision logic.

---

## 4. Demo UI (`app.py`)

`app.py` is a Streamlit UI layer only; it contains no decision logic. It
loads `data/receiving_sample.csv`, lets an operator pick a case, and calls
`inspection_agent.inspect_unit()` directly — the same deterministic
function `vision_adapter.py` delegates to.

It does **not** call `vision_adapter.py` or any model client, because the
sample dataset ships no real images (`data/README.md`). Calling the vision
layer here would mean synthesizing an observation that never happened. The
vision adapter + model client are real and already exercised by
`agent/test_vision_adapter.py` / `agent/test_model_client.py` with a
deterministic fake model client — just not by this demo UI.

Consequence: the sample CSV has no `observed_colour` / `observed_variant`
/ `observed_components` columns, so those three checks show `UNCERTAIN`
for every row in the demo. That is `inspection_agent.py` correctly
refusing to assume a match, not a defect.

## 5. Known contract gap

`contract/evidence-record.json` lists 6 checks. The runtime result
produced by `inspection_agent.py` (and shown in `app.py`) has 10 checks
(adds `carton_count`, `units_per_carton`, `colour`, `quality_flags`).
This has not been reconciled. The UI and tests use the actual runtime
shape, not the contract file.
## 6. Review layer

`agent/review_layer.py` runs after `inspect_unit()` and never edits its check verdicts.
It provides contradiction rules (C1-C6), the uncertainty guide, the decision summary,
the append-only `OverrideLog`, the audit timeline, the attention-queue formula and
failure-mode counts. `app.py` only renders these outputs.
Summary rule: engine FAIL stays FAIL; engine PASS with a conflict becomes UNCERTAIN; UNCERTAIN stays UNCERTAIN.
