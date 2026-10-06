# Teammate audit and bounded integration

Audit date: 6 October 2026. Target baseline: `13309f7`, branch `integration/pod7-operations`. Existing uncommitted user documents `IMPLEMENTED_STATUS.md`, `findings.md` and `recovery-plan.md` were preserved. No deployment, hosted inference, external messages or Recovery Phase 1 implementation is authorized by this audit.

## Exact source folders

All four extracted folders were found directly under `C:\SYDON`:

- `cube26-rcv-0286-sharonmedithi0304-main`
- `cube26-prp-0310-fasihafatima06-main`
- `cube26-rtn-0073-jahnavi2057-main`
- `cube26-rcy-0079-charan-dss-01-main`

These extracted archives do not establish a Git commit identity. SHA-256 source fingerprints are recorded in `TEAM_SOURCE_HASHES.json`; full before/after manifests are private audit artifacts under `.local/`. No teammate directory is an implementation target. Offline test copies are inside this target repository's ignored `.local/teammate-tests/`.

## Comparison

Paths in this table are relative to the named teammate root unless marked Target.

| Manager / capability | Target baseline | Teammate executable evidence | Actual status / compatibility / concerns | Integration decision |
|---|---|---|---|---|
| Receiving recorded checks | Human identity/quantity/damage/quality reviews and official adapter | `submissions/sharonmedithi0304/agent/inspection_agent.py`: `inspect_unit`, quantity/carton/colour/variant/component/damage checks | Real deterministic comparison of supplied fields; not image recognition. Missing quality_flags defaults to empty in source; component sets lose duplicate counts. Output dictionary is not the Round 3 envelope. | Adapt structured comparison with strict types, explicit missing-as-unknown, duplicate component preservation, official checks and original review attribution. |
| Receiving vision | No automatic Receiving model | Same submission `agent/vision_adapter.py` and `model_client.py`: batched Gemini transport, validated observations, injected fake transport tests | Genuine callable provider path, live accuracy unverified. Reference alias matching and expected-count prompt are not adopted. No shared durable Pod reservation in standalone path. | Do not enable or copy provider transport; no hosted calls authorized. |
| Receiving UI/review | Authenticated PostgreSQL operations, immutable review history | Submission `app.py` Streamlit; `agent/review_layer.py` uncertainty explanations/contradictions | App explicitly describes its org filter as not tenant isolation; runtime ten-check output differs from its older local contract. | Keep target auth/store/UI. Adapt only deterministic check concepts; no standalone app integration. |
| Prep visual pipeline | FBA-only manual Prep and versioned required checks | `backend/app/agents/prep_manager.py`, `vision/provider_adapter.py`, `vision/deterministic.py` | Provider adapter returns local engine even when external mode is selected. Filename/scenario branches supply features, boxes and sample barcode/text. Per-image processing; hardcoded fee/cost and recovery_disputable for UNCERTAIN. Not verified visual inference. | Exclude scenario engine, generated locations, costs, fees, claim flags and standalone orchestrator. |
| Prep evidence coverage | Manual required_views finding | `backend/app/agents/evidence_agent.py`: required-view set difference, blur/glare aggregation | Useful deterministic coverage idea, but its inputs come from simulated vision. Empty observations can appear quality-sufficient. | Adapt to explicit human-recorded image IDs/views and tri-state quality flags; missing observations remain UNCERTAIN. Only reached on selected Prep branch. |
| Prep app/storage | Target tenant-authenticated PostgreSQL | `backend/app/main.py`, `db/database.py`, `api/inspections.py`, `test_agentprep.py` | FastAPI/SQLite, import-time seed/image writes, static uploads, permissive CORS; inspected routes do not establish equivalent authenticated tenant isolation. Tests run scenario fixtures. | Keep target routing, RLS, image service and durable workers. Run only isolated copy. |
| Pack | Experimental scene/reference adapter, deterministic comparison, durable budget and manual fallback | Target `backend/pod/agents.py`, `agents/pack/source/` | Real adapter code, no established product/count accuracy. | Preserve existing Pack. No replacement. |
| Returns vision | Owned returns and human evidence; automatic adapter unavailable | `submissions/jahnavi2057/agent/server/services/vision.js`: Gemini request, `callGeminiWithRetry`, no-key mock | Real provider code, but automatic retries conflict with unit budget; missing key invokes name/image-count-based mock findings. External image fetching also differs from target's private storage boundary. | Exclude provider/mock path; retain unavailable/manual boundary. |
| Returns disposition | Explicit attributed human disposition; non-PASS cannot restock | `server/services/disposition.js`: substring condition mapping | Missing/UNCERTAIN checks -> pending_review is compatible and already present. 'not new' -> restock; unrecognized text -> refurbish; identity FAIL can imply disposal without business authorization. These are not authoritative safe rules. | Do not import disposition decisions. Target's existing conservative human flow remains. |
| Returns auth/storage/contracts | PostgreSQL, customer ownership and original-order linkage | `server/middleware/tenant.js`, `db.js`, `api.js`, submission contract JSON | Caller-provided x-tenant-id chosen from two demo orgs is not authentication. In-memory Maps are non-durable. /reload precedes tenant middleware. Output uses provisional organization_id/subject contract, not official Round 3 envelope. | Keep target auth, storage and official adapter; do not mount teammate API. |
| Recovery | Charge-event prerequisite and immutable snapshots; review-only fallback | `backend/app/ingestion/parsers.py`, `rag/retrieval.py`, `agents/recovery_agent.py`, `services/claim_service.py` | Actual parser/retrieval/investigation/claim code exists. Retrieval filters company, but exposed routes accept company_id query parameters without target authentication. Rules and amounts lack an authoritative versioned registry; first-candidate matches and float money need review. | Read-only audit. Parser interfaces, matching provenance and snapshot ideas are candidates for the separately approved Recovery phases. Nothing imported. |
| Recovery model reasoning | No claim adjudication/model call | `services/llm_reasoner.py`: analyzes unknown fees to decide claim support | LLM verdict reasoning is incompatible with requested deterministic adjudication; no shared per-unit Pod budget. | Exclude. Recovery Phase 1 remains gated. |

## Target changes actually made

1. `backend/pod/receiving_checks.py`: adapted Receiving field comparisons as strict, deterministic checks over **human-recorded** `source_payload.receiving_observations`. Unknown fields/types are rejected; omitted observations remain uncertain. No image inference and no new model call.
2. `backend/pod/prep_checks.py`: adapted recorded view coverage through `source_payload.prep_capture`, with a requirement source, explicit required views and authorized image IDs. Unknown blur/glare stays unknown; duplicate image IDs cannot prove extra views. No quality score, generated box or fee rule.
3. `backend/pod/agents.py`: adds these checks only to existing receiving/prep human-review adaptation, after tenant/workflow image authorization and hash verification. Preserves original review fields, run/version and source payload. Supplemented results explicitly request review. All prior safe unavailable/Pack/Recovery paths remain.
4. New focused tests plus database-backed adapter tests cover missing/malformed observations, duplicate components, unavailable image references, FBA-only coverage, no Pack on that route, provenance and zero model calls.

This is a bounded integration of verified deterministic capabilities, **not installation of three functioning visual agents**. Source payloads can be supplied through the existing supervisor review API. There are no new structured-observation UI fields; those remain an API capability. Human-recorded fields are not independent proof of actual conditions. They cannot create a Recovery claim.

### Example optional review payload additions

Keep all existing required review fields and private image IDs. For Receiving:

```json
{"source_payload":{"receiving_observations":{"qty_ordered":4,"qty_received":3,"quality_flags":[]}}}
```

Omitted colour, variant, components and damage remain UNCERTAIN. This does not assert the numbers were inferred from an image.

For Prep:

```json
{"source_payload":{"prep_capture":{"source_reference":"WORK-ORDER-REFERENCE","required_views":["front","back"],"views":[{"image_id":"EXISTING-AUTHORIZED-IMAGE-ID","view":"front","blurry":false,"glare":false}]}}}
```

The absent back view yields UNCERTAIN. Required views are an operator-attributed work-order requirement, not an invented channel rule.

## Contract and state ownership

The Round 3 handbook, RULES.md and organiser schemas remain the baseline. No teammate provisional contract replaces them. `checks`, `inputs`, `upstream_refs`, `payload` and hashes retain their official meanings. Supplemental check keys are additive; deterministic confidence is null and model calls are zero. Source fields and original human reviews survive in payload. Invalid data becomes a persisted pending adapter result; it cannot silently become success.

The existing orchestrator still validates wrong tenant/workflow/stage/schema/hash, owns route/state/final outcome and uses existing PostgreSQL fencing/idempotency. No new dispatch path bypasses reservations. Pod assignment remains unset; explicit fixture sample-flow tests are not an assignment. Receiving provenance is not proof of a visual inspection. Prep/Pack remain alternatives, Returns event-gated and Recovery event/evidence-gated.

## Executed verification and limits

- Before changes: PostgreSQL-enabled full suite **271 passed in 59.39s**; Alembic **004 (head)**; production build passed with existing bundle/annotation warnings.
- Receiving teammate tests: **69 passed**, executed in a target-only copy with external socket connections blocked and provider secrets removed. Tests use fake/injected transports; no live vision conclusion.
- Prep teammate tests: **15 passed**, isolated SQLite/database/images inside target scratch, provider set local and external connections blocked. Initial network guard also blocked Windows event-loop loopback; after allowing loopback, all tests passed. This was a harness issue, not a teammate test failure. Deprecation warnings remain.
- Returns: five offline characterization assertions executed against its pure disposition function, including reproduction of unsafe 'not new' and unrecognized-condition defaults. These confirm current code behavior, not correctness. The complete Returns app/test suite was not run; its provider/mock and dependency environment were not installed.
- Recovery: source audit only. Full service/test execution was deliberately deferred rather than invoking database seeding or possible LLM/claim paths. No Recovery importer/adjudicator/dossier implemented.
- Focused target adapter run before final coverage additions: **15 passed**.
- After changes: `PACK_POSTGRES_TESTS=1` (PowerShell environment assignment), `.venv/Scripts/python.exe -m pytest -o addopts='' -q`: **284 passed in 50.72s**. New tests added; existing tests retained.
- `npx playwright test tests/commerce.spec.ts tests/operations.spec.ts --grep 'real local'` against port 8014: **2 passed in 24.0s**. These validate the existing local customer/operations flow, not the new API-only observation fields.
- `npx playwright test tests/operations.spec.ts --grep-invert 'real local backend'` against port 5174: **6 passed in 19.2s**.
- Scoped Ruff `check --isolated --select E4,E7,E9,F` on Pod code and changed tests: passed. No new migration; database remains at 004.
- All four source file manifests matched exactly after the audit and isolated tests.
- Final `npm run build` in frontend passed TypeScript and production bundling; existing dependency-annotation and bundle-size warnings remain. No frontend code was changed by this audit.

No independent visual benchmark or fee-claim precision was measured. No tests were deleted or weakened. Original teammate archives, their APIs and any advertised deployment URLs were not modified or treated as verified public deployments.

## Remaining blockers

Verified Pod assignment/shared fork; automatic visual agents and securely configured provider; held-out labels; official-evidence UI; authored channel/fee rules; separate Recovery approval. For future live agents, batch under the shared whole-unit budget rather than connecting each standalone provider client. No paid resources or deployment are part of this task.
