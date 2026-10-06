# Recovery adjudication — Phase 0 reconnaissance

Status: plan for review, 6 October 2026. Baseline commit: `13309f7`, branch `integration/pod7-operations`. No implementation, schema migration, rule change or model call in this phase. Phase 1 requires the user's go-ahead. Findings and unresolved decisions are in [findings.md](findings.md).

Phase 0 verification: `$env:PACK_POSTGRES_TESTS='1'; .venv/Scripts/python.exe -m pytest -o addopts='' -q` completed with **271 passed in 47.78 seconds**. This includes PostgreSQL checks and synthetic/mock tests; it is not Recovery accuracy evaluation. Only docs/recovery-plan.md and docs/findings.md were added. No existing code or tests were changed.

## Inspected sources

- `backend/integrated/worker.py`, `service.py`, `contracts.py`, `models.py`: operational queue, admissibility, snapshots and safe default.
- `backend/pod/agents.py`, official schema files, `EVIDENCE-CONTRACT.md`: official adapter and contract boundary.
- `agents/recovery/app.py` and its manifest: explicitly illustrative organiser stub.
- `backend/commerce/service.py`, `models.py`, `api.py`: original/return linkage and charge-event ingress.
- `data/sample/*`, `data/sample/README.md`, `data/expected/README.md`, `docs/decisions.md`, `RULES.md` and Recovery tests in `tests/integration/` and `tests/pack_platform/`.
- `data/README.md` and `data/upstream/` are absent in this checkout. Do not invent their contents or silently import another repository's data.

## Current data model and charge storage

All application entities use the existing PostgreSQL database, with organisation-scoped queries/RLS. `cw_units` holds unit/order/shipment identifiers, SKU lines and source metadata. `cw_workflows` references units and records route, state, policy and version; its `(organization_id, unit_id)` is unique. `cw_runs` stores stage, trigger, state, output, review history and version. `cw_events` is the operational audit. `cw_requests` holds idempotent responses and `cw_calls` enforces unit call budgets.

There is no normalized charge, uploaded fee-report or claim table. Existing `charge_received` events are stored in Recovery run input and audit records. The commerce Recovery endpoint accepts `source_reference`, `amount_minor` and evidence-run IDs; it does not capture a full fee type, currency, marketplace or charge date. Those values must not be invented when migrating/linking legacy events. The organiser stub separately reads `data/sample/fee_report_sample.csv`; this is not application import.

`commerce_orders` points to the original fulfillment workflow. `commerce_returns` points to its original order and a distinct return workflow. `commerce_events` records business provenance. `pod_workflows`, `pod_evidence` and `pod_outputs` store official workflow envelopes, immutable evidence and cached outputs. Operational `integrated.v1` outputs are not themselves the official organiser evidence contract.

The operational worker already snapshots completed same-workflow upstream runs: ID, version, output and human-review history. Recovery currently remains review-needed with `CLAIM_ELIGIBILITY_UNVERIFIED` and no claim. The official Pod adapter also returns UNCERTAIN/no claim. Preserve both fallbacks and the original sample stub tests.

## Joining fulfillment and return evidence

1. Resolve identifiers inside the authenticated organisation; do not trust an uploaded tenant column as authority.
2. Find original workflow through `commerce_orders.workflow_id`, or verified `cw_units` identifiers for older operational records.
3. Join `commerce_returns.order_id` to the same tenant's order and follow each return's `workflow_id`.
4. Cross-check `commerce_returns.data.original_unit_id`, return unit/workflow source `original_unit_id` and `original_order_id` against the original order. Return unit IDs are `RETURN-<request-id>`, not the original physical-unit ID.
5. Retain every matching candidate; contradictions, multiple physical units or unclear scope require review. Never join on SKU alone or pick the first candidate. A customer order can contain several products/quantities: order identity alone does not establish a single physical item.
6. Reuse snapshot logic and preserve hashes, source workflow, original/effective verdict, review actors, versions and timestamps. Validate official envelopes and annotate the operational-to-official mapping explicitly.

The current worker only reads its own workflow; it does not yet perform this cross-workflow retrieval. There is no normalized shipment/tracking/custody log index. `shipment_id` exists on operational unit input; tracking/FNSKU/ASIN and custody transfer are not reliably structured there. Missing links remain unresolved rather than inferred.

## Data inventory: measured, not evaluation

| File | Actual rows |
|---|---:|
| receiving_sample.csv | 100 |
| prep_sample.csv | 62 |
| pack_sample.csv | 29 |
| returns_sample.csv | 24 |
| fee_report_sample.csv | 61 |

The 61 fee rows cover 44 distinct unit IDs: 40 rows for org_demo_alpha and 21 for org_demo_bravo. Fee types: weight tier 42, lost inbound 5, inbound defect 9, unreturned-item refund 4 and damaged-in-warehouse 1. Nine fee rows have amount 0.00. No unit has both Prep and Pack; nine Receiving units have neither. These counts were calculated from CSVs, not adjudicator predictions.

Fee columns are line_id, report_type, unit_id, org_id, sku, fnsku, fba_shipment_id, order_id, charge_type, quantity, amount_usd and posted_date. There is no explicit marketplace, tracking number or custody-transfer timestamp. USD is indicated by the source column; posted_date must retain date-only precision. Upstream photo references are placeholders. Sample rules, amounts and expected outcomes are synthetic, not authoritative labels or valid claim-policy sources.

## Contract-preserving implementation design (not yet implemented)

Keep the official `agent-input`, `agent-output` and `evidence` schemas unchanged. Use permitted `payload` fields for charge/match/rule/formula/dossier metadata; use `inputs` for source report references and hashes, `upstream_refs` and check evidence_refs for consumed official records. Retain the original subject IDs/scope on cross-workflow records; do not relabel return records as original-unit captures.

Map claim position to the check condition 'this charge is supported': CONTRADICTED -> FAIL, SUPPORTED -> PASS, SILENT/UNCERTAIN -> UNCERTAIN. These are claim positions in payload, never additional official verdict values. Apply effective overrides without erasing originals. A generic upstream PASS is not proof of any particular fee predicate. Pending parsing/dependency failures retain data and use official pending/error semantics. Deterministic confidence is null and model calls are zero.

Extend only internal persistence for fee reports/raw rows, charges, candidate matches, decision snapshots, claims and human authorizations. Add organisation keys, RLS, indexes and idempotency. Keep uploaded bytes privately with a hash and row/sheet position: normalized JSON alone cannot preserve verbatim CSV quoting or XLSX bytes. Unreadable files must retain an import-level failure even when rows cannot be enumerated. Use decimal arithmetic, explicit currency and formula inputs, never float money or implicit FX conversion.

The strongest identifier is only a candidate generator: contradicting identifiers or unit_scope still cause review. Secondary/catalogue matching requires documented date-window rules; no guessed window. Cross-workflow evidence should use existing official envelopes and additive context/payload references without redefining previous_evidence as arbitrary unrelated workflow records. Document and test that mapping before Phase 3.

## Phased delivery after approval

1. CSV/XLSX parser and private original-file retention; normalized charge rows, quarantine/duplicate counts and errors; authenticated upload route/CLI; parser and tenant tests. No adjudication or claims.
2. Scoped matching and explainable candidate paths; exact/secondary/inferred results, ambiguity and unknowns; no guessed scope/date windows.
3. Applicable-stage resolver and original/return evidence join; official schema adaptation, provenance, effective overrides, timing/custody checks.
4. Versioned deterministic rule registry. Begin with inbound-defect policy; all unsourced policies remain explicitly synthetic placeholders and operationally review-only. Add other fee types only with their own documented inputs/tests. Preserve safe defaults.
5. Draft dossier with charge assertion vs evidence, formula/inputs, exclusions and evidence snapshots. Explicit attributable authorization before freeze/export; immutable frozen snapshot and version checks; no submission.
6. Independent human/source labels and evaluator. Existing sample expected outcomes are stub outputs and must not be used as independent truth. Add labelled synthetic hard cases separately and report their origin; no accuracy result without independent labels and supported rule sources.
7. README/architecture and runbook updated to implemented behavior only, including a fee-report-to-authorized-dossier diagram.

Run the full test suite and report touched files at each phase, then wait for user go-ahead. No external publication, teammate-repository changes, paid resources or LLM narrative generation is planned.

## Approval questions before implementation

1. May Phase 1 use the actual data/sample files as explicitly synthetic parser fixtures while data/upstream and data/README.md remain unavailable?
2. Resolve placeholder policy behavior: recommended operational UNCERTAIN/no claim eligibility until authoritative policy exists, with synthetic decision previews clearly labelled. Does human authorization permit exporting a placeholder-based synthetic dossier only, or an actual claim? The current request contains both interpretations; no production claim will be enabled by assumption.
3. Resolve missing evidence: recommended missing/ambiguous required evidence -> UNCERTAIN with review; reserve SILENT for an explicitly documented no-claim condition where no human decision remains. Confirm this distinction before adjudication.

Authoritative fee policy/custody definitions, matching date windows and independent labels are later-phase dependencies, not prerequisites to safe file ingestion. Their absence must remain visible.
