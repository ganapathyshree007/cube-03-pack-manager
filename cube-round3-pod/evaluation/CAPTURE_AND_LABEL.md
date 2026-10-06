# Real-photo capture and evaluation runbook

## Current readiness

No permitted product photograph or replacement provider credential is configured in this checkout. Live calls in this continuation: **0**. Held-out labelled photographs: **0**. All accuracy measures remain unmeasured. This runbook and the JSON schemas contain no manufactured image, label, reviewer or model result.

Do not reuse a key disclosed in chat. Configure a replacement locally only after confirming the provider account is free with billing disabled. Do not paste credentials into a report, terminal command, screenshot or chat. The existing adapter remains disabled. Recovery Phase 1 and deployment are outside this work.

## Capture a small supported catalogue

Use products you own or have permission to photograph and send to the selected provider. Record creator, origin and permission for every reference and scene. Use at most four supported identities per inspection. Assign a real, stable catalogue SKU to each distinct product/size/variant; do not infer manufacturer IDs from appearance. Take separate clear reference photographs showing the distinguishing label and size. References are identity aids, not package contents.

Place products in an open box. Capture one primary photograph showing the complete contents for countable cases. Keep the original image; do not crop using labels or expected counts. Record the physical scene, capture session, unit ID in the operations system, expected order, and separately the known physical contents. Hide expected quantities and label files from the model. Remove private shipping labels/customer information before capture.

## Eight required coverage scenarios

| Scenario tag | Capture | Human labelling focus |
|---|---|---|
| `correct_order` | Every ordered item and quantity visible | Exact visible identity and quantity; adequate coverage |
| `missing_item` | Omit one ordered SKU; expose the entire box | Absence is only established when coverage supports it |
| `wrong_item` | Substitute a different SKU or variant | Record visible discriminating attributes; do not force unreadable variants |
| `extra_item` | Add an unrequested item | Label the extra, including unknown identity when appropriate |
| `wrong_quantity` | Too few or too many of an ordered SKU | Keep this separate from entirely absent SKU cases |
| `identical_products` | Multiple separate instances of the same SKU | One label per physical instance; avoid double-counting views |
| `similar_products` | Similar packaging with a real size/variant difference | Record whether the distinguishing text is actually readable |
| `ambiguous_photo` | Controlled blur, glare, clutter or occlusion | Use unknown identity/count and UNCERTAIN where warranted |

Include empty boxes, partial occlusion, poor lighting, unreadable size and an out-of-catalogue product as additional cases. Scenario tags are evaluation metadata only, never model input or evidence. An ambiguous scene with a separate clearly visible discrepancy can still justify STOP & FIX; ambiguity does not erase verified discrepancies.

## Split before tuning

Keep files in an ignored directory, for example `.local/vision-evaluation/`. Allocate entire capture sessions and physical scenes to either development or held-out. Alternate angles, bursts, resized copies and edits of the same scene belong together. The freezer rejects repeated original or normalized image content and scene/session split leakage. It cannot reliably detect all near-duplicates: humans must inspect the split. For an unseen-product claim, also separate product identities; the current tool does not enforce SKU-disjointness. Otherwise explicitly report a closed-catalogue evaluation.

Keep the seven historic RPC experiments in development only. Do not upload restricted research data without its permission allowing the chosen processing. Start with one permitted **development** image for the authorized smoke test. This is not held-out evidence. Tuning on a held-out image permanently converts it to development.

The existing protocol targets at least 50 unseen units with two independent labels; the proposed 64-case distribution is a sampling plan, not completed data. Scenario coverage is reported even when incomplete. Never create a fresh unit ID merely to retry a spent unit.

## Label format

The machine-readable per-line contracts are [labels.schema.json](labels.schema.json) and [predictions.schema.json](predictions.schema.json). Store one JSON object per line in separate `labels.jsonl` and `predictions.jsonl`. These are local evaluation contracts, not replacements for the official evidence envelope.

Each label requires `case_id`, `reviewer_a`, `reviewer_b`, `adjudicator_id`, `adjudicated_at`, `adjudication_reason`, `decision`, `instances`, `count_resolved`, and `physical_defect`.

- Each reviewer independently supplies `id`, timezone-aware `labeled_at`, `decision`, `instances`, and `count_resolved` before seeing predictions or the other review. Retain originals. The adjudicator resolves disagreements before inference; do not silently replace either review.
- Each instance has a unique `instance_id`, `sku` (null if unknown), `variant`, and optional `region`. Region is normalized `x`, `y`, `width`, `height`, with positive size entirely inside the image. Label visible objects only; do not create regions for hidden objects. Human label boxes are not model boxes.
- Decisions are `seal`, `stop_and_fix`, or `uncertain`. `count_resolved=false` preserves visual uncertainty. `physical_defect` may be null when actual correctness is unknown. Known physical contents in the dataset manifest are separate from visually supportable labels.

Each prediction requires `case_id`, original `source_sha256`, timezone-aware `agent_started_at`, frozen `configuration_hash`, `evidence_record_id`, original automated `decision`, validated `instances`, `count_resolved`, and actual `model_calls` (0 or 1). Export saved evidence, not a human override. Preserve the source JSON separately. A null decision requires `failure_kind` (`provider`, `schema`, or `infrastructure`) and no validated instances/resolved counts. Optional `latency_ms`, `observed_cost`, and `cost_provenance` must come from records. Unknown cost is null, not a guessed zero. Include provider usage metadata in the accompanying original evidence.

Use normalized, retained instances from `payload.visual_observations.instances`: map `normalized_sku` to `sku`, `normalized_variant` to `variant`, and retain genuine `region` and `instance_id`. Unresolved identity is null, not the first candidate. Only mark `count_resolved` when the saved reconciliation establishes exactness. Preserve the original official decision: the experimental-model review gate remains in force even if deterministic counts match.

## Freeze and score offline

Create a manifest matching `evaluation.dataset.Dataset`, with products/references, cases, provenance, scene/session IDs, splits and expected order. Freeze the configuration/prompt/model version separately and save its SHA-256 as `configuration_hash`; retain the file for audit. Record these before inference.

From the repository root in PowerShell:

```powershell
.venv/Scripts/python.exe -m evaluation.dataset --manifest .local/vision-evaluation/manifest.json --root .local/vision-evaluation --output .local/vision-evaluation/frozen.json
.venv/Scripts/python.exe -m evaluation.verified --manifest .local/vision-evaluation/manifest.json --root .local/vision-evaluation --frozen .local/vision-evaluation/frozen.json --labels .local/vision-evaluation/labels.jsonl --predictions .local/vision-evaluation/predictions.jsonl --configuration-hash YOUR_FROZEN_CONFIGURATION_SHA256 --output .local/vision-evaluation/metrics.json
```

Neither command invokes a model. Output files are created exclusively to avoid overwriting a previous result. Re-freeze pre-extension manifests before new runs because normalized image hashes are now included; preserve earlier manifests and reports.

The evaluator rechecks all local images, hashes and splits, requires every held-out outcome (including failures), distinct reviewers, and labels/adjudication before inference. It computes SKU/variant multiset matches and exact quantity metrics from instances, including expected-but-absent SKUs. Detection uses separate one-to-one region matching. Truth with unresolved identity/count is excluded from identification/quantity metrics with an explicit count; missing human regions are excluded only from detection metrics. Unknown predictions and operational failures are separately reported. Every rate has its denominator; no samples means no accuracy result.

These checks cannot prove a reviewer exists, permission is valid, timestamps are truthful, or a call actually occurred. Audit against original labels, provider responses, stored evidence and the durable budget ledger. Never describe these declarations as independently verified provider execution.

## One authorized development smoke test, once prerequisites exist

Use the existing official workflow/provider boundary, not a direct provider script: bind permitted reference images and the primary scene, verify the Pod route and original whole-unit reservation, then submit once. Do not change the disabled configuration until authorized. Keep expected counts in backend reconciliation only. Save raw response, normalized instances, actual regions, per-SKU totals, expected comparison, original decision, model-call ledger and available usage/cost metadata. If transport/schema fails, preserve the failure and require review; do not retry or repair with a model. A zero-call prerequisite failure is not a vision result. A one-case success would establish only that case, not reliable counting or held-out accuracy.
