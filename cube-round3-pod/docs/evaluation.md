# Evaluation — local continuation

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


## Teammate integration checkpoint

PostgreSQL-enabled target suite: **284 passed in 50.72s** after adding Receiving structured comparisons and Prep recorded-view coverage. Browser regression checks: **2 real local flows + 6 labelled UI fixtures passed**. These optional checks use human-recorded source payloads and make zero model calls. Teammate isolated checks: Receiving 69 passed; Prep 15 passed on scenario fixtures; Returns five characterization assertions exposed unsafe text defaults, which were not imported. Recovery remained a source-only audit. See TEAM_AGENT_COMPARISON.md for commands, provenance and limitations. No vision or claim-precision metric is implied.

## Latest verification — 6 October 2026

| Command/check | Actual result |
|---|---|
| `PACK_POSTGRES_TESTS=1 .venv/Scripts/python.exe -m pytest -o addopts='' -q` (PowerShell environment assignment) | **271 passed in 41.00 seconds**, existing PostgreSQL, including new commerce and official-bridge tests |
| `npm run build` in frontend | Passed TypeScript and production build; dependency annotation and bundle-size warnings remain |
| `npx playwright test tests/commerce.spec.ts tests/operations.spec.ts --grep 'real local'`, OPERATIONS_TEST_BASE_URL=http://127.0.0.1:8014 | **2 passed**: persisted customer/analytics workflow and operations upload/review/history/mobile workflow |
| `npx playwright test tests/operations.spec.ts --grep-invert 'real local backend'`, OPERATIONS_TEST_BASE_URL=http://127.0.0.1:5174 | **6 passed**, explicit UI fixtures including reduced motion/error/duplicate guards |
| Ruff `check --isolated --select E4,E7,E9,F` on changed backend integration/commerce/Pod modules and associated tests | Passed |

The initial plain pytest run passed 199 and skipped 71 database tests because its opt-in flag was missing. The first browser attempt found stopped local services. Existing PostgreSQL was restarted without reset. The first database-enabled run then found five reservation failures: insert rowcount was unreliable for detecting a successful reservation. Replaced it with INSERT RETURNING; all 271 tests subsequently passed, including durable-budget tests. The phone-width navigation regression was fixed by wrapping navigation controls.

New tests include inventory concurrency, ownership, no invented Receiving event, policy/Pod holds and stale policy review, branch selection, return quantities, Recovery gates, tenant analytics, immutable official evidence, schema checks, lease fencing and whole-unit budgets. Model responses in these tests are synthetic/mocked, never proof of recognition. The local browser tests deliberately leave clearly labelled fixtures; default analytics excludes them.

The following results are historical checks from 5 October. Current live vision and held-out sample counts remain zero.

## Software verification performed in this checkout

| Check | Result | What it establishes |
|---|---|---|
| Official starter integration and end-to-end suite | 93 passed | Official stub contracts, routing, evidence, errors and HTTP behavior |
| Imported Pack deterministic policy suite | 26 passed | Reconciliation rules using synthetic structured observations |
| Provider/authentication/storage subset | 27 passed | Software behavior and mocked provider handling; no live inference |
| PostgreSQL integrated workflow/context/readiness subset | 37 passed | Existing migrated local database, tenant-scoped synthetic fixture workflows |
| Browser fixtures | 6 passed | Login, keyboard/accessibility, stale/error states, request guard, public auth configuration failure |
| Real local API/worker browser workflow | 1 passed | Local account sign-in, synthetic order, fixture upload, human review, saved evidence, refresh, mobile layout and image authentication |
| Frontend production build | Passed | TypeScript and bundled build; non-blocking dependency annotation and bundle-size warnings remain |
| Standard organiser sample runner | 100 completed runs | EXCEPTION 51, CLEAN 33, NEEDS_REVIEW 9, CLAIM_RECOMMENDED 7; workflow COMPLETED 83, BLOCKED 17. These are stub replay outputs, not vision performance |

The initial official suite had two Windows/environment failures: content-addressed paths used backslashes; an unavailable endpoint raised connection timeout instead of connection error. The path normalization and timeout classification fixes passed the unchanged official tests. The first new local browser attempt stopped because the test photograph was absent; a labelled synthetic test image was created and the full workflow passed. Existing data was preserved.

The local browser test asserted zero external network requests, no checked WCAG A/AA violations, no horizontal overflow at 390px width, the phone camera capture attribute and HTTP 401 for an unauthenticated saved-image request. A capture attribute is not a physical-phone camera test. Desktop/mobile screenshots are private under `.local/qa/`.

These are selected suites, not a claim that every imported test has been rerun. A new API/worker restart recovery test, complete official-to-platform bridge, real manager contracts and public end-to-end verification remain incomplete.

## Vision development and held-out evaluation

Seven previous distinct RPC development experiments are preserved in the original repository's ignored `.local/` data. Five attempts failed from context/output limits; one returned valid JSON but described catalogue references instead of the six scene objects; another reference-constrained attempt failed. No expected SKU identification or reliable counting was established. Valid JSON was not a recognition success. Do not reuse these cases as held-out tests.

No new live model call was made in this continuation. No Azure call was made. Hosted identification and counting remain unverified. Local Qwen3-VL 2B remains experimental. Disclosed credentials must be revoked; a replacement must be configured locally rather than posted in chat.

Held-out labelled sample count: 0. The recommended >=50 unseen units with two independent human labels are not available. Per-check TP/TN/FP/FN, exact-order match rate, unsafe SEAL rate, false stops, uncertainty rate, automatic coverage, provider/schema failure rate on held-out data, model latency and actual inference cost are **not measured**. Do not report zero failures as an accuracy metric when the denominator is zero.

All eight required visual scenarios remain unevaluated on held-out photographs: correct, missing, wrong, extra, wrong quantity, identical duplicates, similar variants and ambiguous images. Occlusion, blur/glare, unreadable sizes, unknown items and empty-box vision behavior also need labelled evaluation. Provider/duplicate/stale-review software tests cannot replace that evaluation.

Named development failure modes: input/output exhaustion; catalogue/scene confusion; unsupported identity; unresolved counting. Deployment blockers: unverified Pod type/shared fork, missing official durable adapter integration and unverified safe hosted inference. No public URL or model-performance claim is made.
