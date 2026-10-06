# Visual inspection implementation and verification

## Latest prerequisite recheck (6 October 2026)

Re-read the audit and configuration. A fresh Settings load from `C:/SYDON/cube-round3-pod` reads that project's `.env`: key absent, GEMINI_MODEL unset, Gemini vision disabled. GEMINI_MODEL is the supported variable; MODEL_NAME is ignored. No secret value was printed. No matching offline launcher or integrated local-site API process was running at the check; this is not proof of a configured live server.

The latest request still contains literal placeholders for photo folder, provider-account billing confirmation and Pod type. They cannot establish permission or eligibility. `pod-assignment.json` explicitly has assignment_verified=false and assigned_type=null. No development unit was selected and no durable reservation was attempted. **Actual model calls: 0. Output, latency and provider cost metadata: unavailable because no request occurred. Held-out samples: 0; accuracy remains unmeasured.**

No storage path, credential, runtime setting or review gate was modified. Before any storage change, inventory existing image-record keys and hashes, copy into isolated storage without deleting originals, verify every referenced image/hash and tenant access, then switch with a rollback plan. This is a plan only; no files were relocated. Recovery remains gated; no deployment or push.

Relevant software tests rerun: `$env:PACK_POSTGRES_TESTS='1'; .venv/Scripts/python.exe -m pytest tests/pack_platform/test_gemini_provider.py tests/pack_platform/test_pod_bridge.py tests/pack_platform/test_visual_observations.py tests/pack_platform/test_verified_evaluation.py -o addopts='' -q`: **41 passed in 3.46s**. Synthetic/injected responses only, not a live smoke test or accuracy benchmark.


## Replacement-key configuration audit (6 October 2026)

Read the Round 3 participant handbook from Downloads, RULES.md, the visual-inspection report and capture runbook. Checked Settings and the offline launcher without printing any credentials or dotenv contents. Effective config file when launched from this repository (and by the offline launcher): `C:/SYDON/cube-round3-pod/.env`. The loader uses `.env` relative to the process working directory; environment variables take precedence and Settings is cached. The offline launcher explicitly changes to the integrated repository root.

Safe configuration result: **Gemini key absent** in both this dotenv and the current process environment; **selected Gemini model unset**. The code expects `GEMINI_MODEL`, not `MODEL_NAME`; extra dotenv names are ignored. The replacement described by the user is not available to this integrated process. No key was copied from another project or used from chat.

Live test blocked before provider invocation:

- Intended integrated Gemini configuration is absent; the offline launcher deliberately forces provider none. Configure a future authorized vision run separately from that launcher, without weakening the review gate.
- Billing-disabled/free-tier account status is unverified, and local free-tier confirmation is absent. A flag alone would not establish account billing status.
- No product/reference image with documented development-use permission is present in `data/input/`; it contains README/.gitkeep only. No eligible development unit was selected or created, so no unit reservation was attempted or consumed.
- Effective storage points into the separate `cube-03-pack-manager` project. Establish an integrated-project storage directory and preserve/reconcile existing image records before changing that location; do not silently redirect saved evidence.

No dotenv, provider setting, storage path, budget or model-review policy was modified. Pod route verification remains required before an official workflow run. **Live requests: 0. No detections, count results, provider latency or billing metadata obtained. Held-out samples remain 0; accuracy is unmeasured.** Recovery remains gated. No deployment or push.

Relevant software verification: `$env:PACK_POSTGRES_TESTS='1'; .venv/Scripts/python.exe -m pytest tests/pack_platform/test_gemini_provider.py tests/pack_platform/test_pod_bridge.py tests/pack_platform/test_visual_observations.py tests/pack_platform/test_verified_evaluation.py -o addopts='' -q` -> **41 passed in 4.07s**. These use synthetic/injected provider data; they are not a development inference test or a held-out benchmark.


## Real-vision readiness continuation from 96a9af0

Configuration checked without displaying secrets: provider `none`, vision disabled, provider not configured, replacement key absent, free-tier confirmation false. No previously disclosed key was used. `data/input/` has only README/.gitkeep, with no permitted photograph ready for the requested development smoke test. **No live call made; actual call count 0; no inference cost incurred by this task, and no provider billing measurement available.** No item observations/regions are presented as real detections.

Implemented `evaluation/verified.py`, JSON schemas for independently reviewed labels and saved predictions, and [capture instructions](../evaluation/CAPTURE_AND_LABEL.md) covering all eight scenarios. The offline evaluator binds to the frozen manifest/image hashes, requires all held-out outcomes, rejects invalid timestamps/reviewer identity reuse/call counts and computes SKU/variant/quantity metrics from instances rather than accepting submitted matching scores. Failures stay in denominators; unresolved truth and missing regions have explicit exclusions. The freezer now detects metadata-only copies through normalized-image hashes, alongside original hash, scene and session checks. Near-duplicate detection still requires human audit. Re-freeze older manifests before new evaluations; retain their originals.

Validation results for this continuation:

- `$env:PACK_POSTGRES_TESTS='1'; .venv/Scripts/python.exe -m pytest -o addopts='' -q`: **308 passed in 28.11s**.
- `.venv/Scripts/python.exe -m pytest tests/pack_platform/test_verified_evaluation.py tests/pack_platform/test_dataset.py tests/pack_platform/test_evaluation.py tests/pack_platform/test_visual_observations.py -o addopts='' -q`: **33 passed in 0.51s**, after the final scenario-reporting addition.
- Ruff `check --isolated --select E4,E7,E9,F evaluation/verified.py evaluation/dataset.py tests/pack_platform/test_verified_evaluation.py`: passed.
- `python -m evaluation.verified --help`: passed. These commands use the repository virtual environment; Ruff uses the already installed sibling-repository executable.
- No frontend/runtime/migration changes in this continuation; no new build or browser claim is made.

**Software tests:** synthetic inputs only. **Development smoke tests:** 0 new. **Held-out accuracy:** 0 labelled samples, unmeasured. Seven prior RPC development experiments remain unsuccessful/unreliable and separate. Automatic clearance remains disabled for unvalidated model outputs. Whole-unit budget, manual review and Recovery Phase 1 gates are unchanged. No deployment or cloud resource creation.


## Configuration actually found

6 October 2026: model_provider=none, pod_vision_enabled=false, provider_configured=false; no Gemini key, model name or free-tier confirmation configured in this target repository. No credential value was printed. No live provider request was made. The existing transport targets Gemini generateContent only when explicitly configured; the offline launcher forces provider none. No new model, SDK, detector weights or training dependency was installed.

RULES.md section 5 says: **“Batch your model calls. One call per unit carrying all checks, never one call per check. Report model.calls.”** It applies to the whole system. Existing durable reservations remain shared across managers and original-unit return links, not reset for a retake. Independent Receiving, Prep, Pack and Returns calls cannot all be enabled under this interpretation. Required organiser clarification: does a later custody/return event receive a new explicitly defined evaluation budget, and if so how are those units identified? Until clarified, only the existing Pack provider boundary is eligible; other visual stages remain attributed manual review/unavailable. No inferred exemption.

## Implemented path

Private upload -> authorized workflow image/reference records -> durable official queue -> tenant and image-hash checks -> whole-unit reservation -> at most one configured provider call -> saved raw response -> schema-validated instances -> deterministic overlap handling -> SKU/variant totals -> expected-order reconciliation -> official evidence -> human review.

The provider receives identity catalogue alternatives and one primary counting view, not expected quantities. References are distinct from the primary photograph by ID and hash and never counted. The selected catalogue is bounded to four identities. Unsupported SKU IDs are rejected; there is no fuzzy or case-insensitive identity invention.

The existing observation schema is extended additively in backend/schemas.py and agents/pack/source/schemas.py. Optional provider-returned regions use normalized x/y/width/height, positive dimensions and bounds within the primary image. Non-finite/invalid geometry is rejected. Missing regions remain null. Optional variant, visible_attributes and model_score are supported; scores are explicitly uncalibrated model output, not confidence certified by the application.

`backend/pod/visual_observations.py` attaches the actual saved image ID/hash in code, assigns matched/unmatched/uncertain status and aggregates one per retained supported instance by exact catalogue SKU and variant. Missing or disagreeing named variants remain unresolved. A known distinct SKU/variant can be an extra; a bare variant disagreement does not establish another SKU.

Deduplication: normalized IoU >= 0.85, stable response order. Same candidate identity/variant retains the first and records later IDs as suppressed. Conflicting overlapping identities remain uncertain. **Every overlap makes exact counting unresolved** because two overlapping objects might really be different items. Missing boxes are never fabricated and cannot support geometric deduplication. Raw response remains separate from deduplicated results.

Comparison records expected quantity, observed visible count, exactness and difference. Difference is null when exact count is unresolved. Absence is only asserted with sufficient coverage; supported excess/wrong SKUs can still indicate STOP & FIX. Existing experimental-model validation prevents automatic clearance even when deterministic counts match. Human overrides stay separate.

Successful provider text and provider observations are stored in tenant-private `pod_model_response` records; failures use the existing diagnostic/pending path. Official evidence references the raw record ID and separately contains normalized observations and deterministic comparison. No database migration is required. The existing records infrastructure is reused, not described as external tamper-proof storage.

## Operations UI

Open **Visual inspection evidence** in a workflow. It loads tenant-authorized official evidence, the private primary photograph, actual model-returned regions when present, per-instance identity/status/attributes, and expected-versus-observed totals. It labels experimental observations and uncalibrated scores. Empty/error states do not imply a successful inspection. Existing upload and review controls remain available; recapture does not grant another call.

This is an evidence viewer, not a new live launch wizard. Existing `/v1/pod/workflows` API selects inspection_mode=vision, scene_image_id and catalogue_ids after reference binding. A verified Pod assignment and authorized configured provider are still prerequisites. `/v1/pod/vision-status` reports readiness without exposing credentials. No live result currently exists to display.

## Teammate boundaries

Receiving structured comparisons and Prep recorded view coverage from the prior audited adaptation remain human-attributed. No simulated Prep boxes/features/costs were imported. Returns' mock fallback, repeated provider calls and unsafe text-based disposition remain excluded; automatic returned-product/component vision is **not implemented**. Recovery remains event/evidence-gated with no fee importer, claim amount or adjudicator; its Phase 1 approval is still pending. Pack was extended rather than replaced.

## Data and evaluation

`data/input/` contains only README/.gitkeep. No authorized independently double-labelled held-out catalogue/photo set is present there. Private software test images and teammate scenarios are not a real accuracy benchmark. The seven earlier RPC development experiments remain failed/unreliable recognition experiments and are not reused as held-out evaluation or uploaded to any service.

Existing evaluation/dataset.py and evaluation/evaluate.py retain frozen split, source-scene, two-reviewer and label-before-run checks. New evaluation/instance_metrics.py adds exact SKU/variant, descending-IoU greedy one-to-one matching at IoU 0.5. It reports TP/FP/FN, precision/recall by manager/scenario and counts exclusions where instance annotations are absent. Missing predicted boxes cannot match a labelled region. It reuses the existing order/check/quantity and uncertainty metrics and never calls a model.

```powershell
.venv/Scripts/python.exe -m evaluation.instance_metrics path-to-independent-cases.jsonl path-to-report.json
```

Input uses the existing evaluator case contract plus `instance_labels` (sku, variant, normalized region) and `predicted_instances` (normalized_sku, normalized_variant, region). Labels must be independent of predictions. Freeze by capture session/source scene; include SKU-disjoint tests where feasible. Cover correct/missing/wrong/extra/quantity/identical/similar cases and blur/glare/occlusion/lighting/clutter. Empty input is rejected, not reported as perfect accuracy.

Held-out sample count: **0**. Identification precision/recall, detection precision/recall, exact per-SKU quantity accuracy, order accuracy, false approvals and scenario uncertainty rates: **unmeasured**. Live call count for this work: **0**. Inference cost: no call made; no bill measured. No training performed.

## Provider reference checks

Reviewed official [structured-output documentation](https://ai.google.dev/gemini-api/docs/structured-output) and [image-understanding documentation](https://ai.google.dev/gemini-api/docs/image-understanding). Structured output is not proof that the values describe the scene correctly. No model availability or account eligibility was inferred from documentation. Existing provider configuration was not enabled or changed to another model.

## Remaining blockers

Authorized fresh provider configuration without disclosed keys; verified Pod assignment/shared fork; permitted real catalogue references and independent image labels; lifecycle budget clarification; real Returns/Receiving/Prep vision paths; measured real-world counting. No public deployment or claim of complete automation.

## Visual inspection verification (6 October 2026)

Software checks below use synthetic observations/images or injected provider responses, not a vision accuracy benchmark. Live calls: **0**. Held-out samples: **0**. See [VISUAL_INSPECTION.md](VISUAL_INSPECTION.md) for the contract, limitations and prerequisites.

| Command/check | Actual result |
|---|---|
| PowerShell `$env:PACK_POSTGRES_TESTS='1'; .venv/Scripts/python.exe -m pytest -o addopts='' -q` | **297 passed in 29.89s**, PostgreSQL enabled |
| Same environment, `.venv/Scripts/python.exe -m pytest tests/pack_platform -o addopts='' -q` | **204 passed in 16.91s** |
| Frontend `npm run build` | TypeScript/build passed; existing dependency annotation and >500 kB bundle warnings remain |
| Frontend `$env:OPERATIONS_TEST_BASE_URL='http://127.0.0.1:5174'; npx playwright test tests/vision.spec.ts tests/operations.spec.ts --grep-invert 'real local'` | **7 passed in 6.6s**, labelled UI fixtures |
| Frontend `$env:OPERATIONS_TEST_BASE_URL='http://127.0.0.1:8014'; npx playwright test tests/commerce.spec.ts tests/operations.spec.ts --grep 'real local'` | **2 passed in 16.0s**, local database/worker, synthetic upload and attributed human review; no inference |
| Ruff `check --isolated --select E4,E7,E9,F backend/pod backend/schemas.py backend/gemini_provider.py agents/pack/source/schemas.py evaluation/instance_metrics.py tests/pack_platform/test_visual_observations.py` | Passed using existing sibling-repository Ruff executable |
| `.venv/Scripts/python.exe -m alembic current` | **004 (head)**; no migration added |
| `git diff --check` | Passed |
| SHA-256 comparison of 242 files in private pre-audit teammate manifest | **0 changed** |

The first new browser harness failed to load React imported directly inside the page; moving imports to a Vite-served test module fixed it. The final seven-test run passed. The latest server was restarted at http://127.0.0.1:8014/ with vision disabled. Nothing was deployed or pushed publicly.
