# Source comparison before integrated schema changes

Inspected 4 October 2026. Post-competition local work; no extension is asserted.
Read-only clones are under ignored `.local/references/`. No teammate code was copied.

| Source | Database/tables | Identifiers and interface | Evidence/business rules | Migrations/tests/status |
|---|---|---|---|---|
| Receiving `b5c4d1a` | CSV only | `record_id`, `org_id`, official `unit_id`, PO/line, SKU/ASIN; no executable API | Identity, carton/unit quantity, damage and quality flags; yes/no/uncertain | No application, models, migrations or executable tests; automatic adapter BLOCKED |
| Prep `cf6187d` | SQLite/SQLAlchemy: products, rules, inspections, inspection_images, inspection_checks, evidence_items, agent_events, inspection_feedbacks | Product/SKU, inspection ID, unit_id and work_order_id; multipart POST /inspections, GET history/evidence, feedback/additional-evidence | PASS/FAIL/UNCERTAIN, per-rule findings, image boxes; scenario engine derives some findings/boxes from filenames/hints | create_all rather than versioned migrations; 15 scenario/API tests inspected, not run here; automatic visual adapter BLOCKED |
| Pack `b10e2c3` | PostgreSQL: records, jobs, events, checkpoints | org/unit/order/SKU, catalogue, uploads, attempts, reviews, official export | seal/stop_and_fix/uncertain; persistent call reservation; experimental local recognition | Alembic 001; baseline 101 tests passed after local PostgreSQL startup |
| Returns `01db82b` | Node in-memory store; static catalogue and CSV | record_id, subject=unit string, org from x-tenant-id; POST /returns/inspect and /returns/:id/override | identity/completeness/condition; restock/refurbish/liquidate/dispose/pending_review | No migrations; seven test functions inspected, not run; implicit mock and provider retries are not adopted |
| Recovery `267b142` | SQLAlchemy SQLite default, PostgreSQL option: companies, users, source_files, charges, shipments, orders, evidence_records, evidence_chunks, investigations, investigation_evidence, claims, claim_ledger | company_id/org, charge/unit/shipment/order/SKU; charge/evidence import, investigations, claims | CONTRADICTED/SUPPORTED/SILENT/UNCERTAIN plus duplicate/reimbursed guards; optional LLM reasoning | create_all; 12 test functions inspected, not run; integrated conservative evidence review implemented independently, claim eligibility remains blocked |

## Conflicts and decisions

- Shared starter data defines UNIT-0001 through UNIT-0100 across organizations. Never generate substitute official IDs. Organization is part of every join.
- A Prep work_order_id is not silently treated as a merchant order ID. Its default UNIT-0001/WO-88902 are not valid mappings. Imports must supply explicit links.
- Route must be explicit FBA, merchant or 3PL; missing route stays unknown. Receiving precedes Prep OR Pack. Returns/Recovery require independent events. No source establishes routine Prep followed by Pack.
- Official Evidence Contract 1.1 uses UUID organization IDs, object subjects, lowercase check verdicts and object outcomes. Returns' string subject/outcome and Prep's recovery-claim payload are incompatible source formats. Preserve raw payloads; do not advertise them as official 1.1 exports.
- Internal envelope version `integrated.v1` is our contract, not an organiser schema. Official export is separately validated. Non-UUID source organizations require an explicit mapping before export; do not silently invent one.
- Scenario hints, invented barcode text/boxes, default confidence, sample $25 fees and example quantities are not real observations or channel policy. No model or cloud requests are made by the integrated service.
- No final-round document was supplied/found. The repository RULES documents Round 2: “Make **one** call per unit carrying all checks, never one call per check. At prep volumes that is the difference between a 90% gross margin and none.” This is not asserted as a final-round exemption or restriction. Integration dispatch is disabled; future enabling needs an explicit policy and adapter. Existing Pack's conservative one-call behavior is unchanged.
- No root LICENSE was found in these clones. Returns agent package.json declares ISC. Other source reuse permission remains unverified; implementation here is original, based on interface inspection.
- Prep live navigation and inspection page were inspected read-only: SKU/category selection, work-order/operator fields, explicit prebuilt scenarios versus uploaded photographs, view-angle selection and dynamic rules. Its linked walkthrough's full auto-generated transcript was read: uncertain rear-view request, feedback, category-specific rules, evidence/history, activity and JSON API. The narration's training, bounding-box and agent claims were not accepted as independently verified behavior. Source code takes precedence.
- Recovery's `CrossPodEvidenceContract` is also a source-specific schema, not official 1.1: it uses `org_id`, `source_stage`, top-level unit ID and uppercase findings. It remains preserved as source material, not silently normalized into a certified claim.

## Shared database design

Retain PostgreSQL and existing Pack tables. Add tenant-scoped units, workflows, durable manager runs, append-only audit events, request idempotency and a dispatch ledger through migration 002. Store local image metadata in existing records, never image blobs. Composite tenant foreign keys prevent cross-organization links. Keep original source payloads and separate execution state, machine output and attributed human disposition.
