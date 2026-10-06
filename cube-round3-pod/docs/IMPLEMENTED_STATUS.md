# CUBE Round 3 — Implementation Status Report

**As of:** 6 October 2026  
**Project:** Integrated commerce operations, including PCK Pack Manager  
**Repository:** `C:\SYDON\cube-round3-pod`  
**Branch:** `integration/pod7-operations`  
**Latest implementation commit:** `13309f7` — Add local commerce policies, customer portal and durable official adapters

## 1. Overall status

The project has a working local commerce application with customer order requests, inventory reservation, returns, product-specific workflow policies, an operations dashboard, human evidence review, durable processing and analytics.

The application also has an adapter connecting its PostgreSQL storage to the organiser's official workflow and evidence contracts. This does **not** mean all five automatic agents are complete. Automatic visual inspection is unavailable or experimental, and the real Recovery fee-adjudication layer has not been implemented.

Current scope is local-only. No public deployment or validated AI accuracy is claimed. Pod 7's assigned type and shared Round 3 fork are still unverified.

## 2. Implemented features at a glance

| Area | Implemented | Important boundary |
|---|---|---|
| Customer portal | Catalogue, cart quantities, order requests, owned history, eligible returns | No payment collection |
| Inventory | Inbound receipt provenance, available/reserved stock, transactional reservation | No automatic return restocking or cancellation stock release |
| Workflow policy | Versioned rules, route selection, required checks, skip reasons, holds | Unknown category/assignment does not silently proceed |
| Operations dashboard | Workflow list/details, evidence upload, review, history, state tracker | Automatic agents are not all connected |
| Evidence review | Attributed human findings, preserved original results, version checks | Human decisions are not presented as AI verification |
| Analytics | Persisted orders, returns, stage states, processing durations and filters | Fixtures excluded by default; unavailable measures are not invented |
| Official-contract bridge | Durable workflow queue/store, schema validation and evidence APIs | Full official-evidence UI is unfinished |
| Pack AI boundary | Configurable adapter, scene/reference separation, deterministic comparison | Experimental, disabled locally, accuracy unverified |
| Recovery | Charge-event gate, saved evidence snapshots and review-required fallback | No real fee importer, adjudicator or dossier yet |
| Security/reliability | Roles, tenant isolation, private images, idempotency, durable call budget | Public deployment/authentication remains unverified |

## 3. Customer portal

The separate customer page supports:

- Local sign-in using the customer account file.
- Browsing active catalogue products and available quantities.
- Selecting quantities and submitting an order request.
- Server-side product, price, quantity, inventory and identity validation.
- Transactional stock reservation and linked fulfillment workflow creation.
- Viewing only the signed-in customer's orders and safe status messages.
- Reopening saved orders after refresh or another sign-in.
- Requesting returns for eligible owned, delivered products.
- Return quantity validation against purchased and previously requested quantities.
- Configured return-window enforcement.

Checkout explicitly does not collect payment or card details. Customer responses do not expose internal agent evidence, private payloads or other customers' orders.

**Main implementation:** `frontend/src/operations/commerce.tsx`, `frontend/shop.html`, `backend/commerce/api.py`, `backend/commerce/service.py`.

## 4. Catalogue, inventory and product policies

Operators can configure product category, price, fulfillment route, active status, policy version, return window and synthetic-fixture designation. Supervisors can publish immutable policy versions with a source reference and rules for product/category/route selection.

Policies record required and optional checks, selected rule IDs, skipped-stage reasons and unresolved configuration. Unknown categories, conflicting policy matches or unverified Pod assignment hold work for review. Supervisor policy review uses the current workflow version, preserves policy history and is limited to unstarted held workflows.

Inbound inventory receipts include quantity and source provenance. Checkout reserves already-received stock and **does not create a fictitious Receiving inspection**. Inventory updates use database transactions and row locks; concurrent reservations are tested against overselling.

An operator-recorded receipt establishes recorded provenance, not an AI-verified inspection.

**Main implementation:** `backend/commerce/policy.py`, `backend/commerce/service.py`, `backend/commerce/models.py`.

## 5. Workflow routing and conditional activation

Implemented route behavior:

```text
Actual inbound receiving evidence / recorded inventory receipt
                         |
                 Product policy
                         |
             +-----------+-----------+
             |                       |
       Standard FBA            Merchant / 3PL
             |                       |
            Prep                    Pack
             +-----------+-----------+
                         |
           Returns only on a return event
                         |
     Recovery only with charge event + admissible evidence
```

Prep and Pack are alternative branches, not sequential stages on the normal route. Specialist FBA is held as unsupported. Unknown Pod assignment is not inferred from starter defaults.

Inapplicable stages carry reasons rather than appearing as successful inspections. Missing automatic adapters stop visibly for review. Errors, missing evidence and UNCERTAIN results never become PASS by default.

The application's Recovery event/evidence gate follows the user's latest requirement. It differs from the starter's terminal Recovery sample flow and remains a team-review item before submission.

## 6. Operations dashboard and human review

Implemented operations functionality includes:

- Workflow listing and per-workflow details.
- Selected route, policy reasons and stage status display.
- Persisted state updates through polling, without simulated progress.
- Uploading evidence images and protected image retrieval.
- Expected-versus-observed review information where available.
- Explicit human findings, reviewer attribution and review history.
- Stale-review rejection using record versions.
- Workflow controls with policy checks.
- Delivery confirmation only after passing completed fulfillment evidence and a recorded delivery source.
- Desktop and mobile layouts, keyboard/accessibility checks and reduced-motion behavior.

The main tracker presents operational `cw_*` records. Official Pod workflow/evidence records are exposed through APIs, but a complete official-evidence browser is not yet integrated into this screen.

**Main implementation:** `frontend/src/operations/main.tsx`, `operations.css`, `backend/integrated/api.py`, `service.py`, `worker.py`.

## 7. Current status of the five managers

| Manager | Current application behavior | Not yet established |
|---|---|---|
| Receiving | Inbound provenance, human-review records, official-contract adaptation of attributed reviews | Automatic visual receiving inspection |
| Prep | FBA route selection, policy checks and human-review evidence | Connected automatic Prep agent |
| Pack | Merchant/3PL route, human review, experimental vision adapter and deterministic reconciliation code | Reliable live product identification/counting |
| Returns | Eligible return requests linked to original orders, separate return workflows and reviewed dispositions | Connected automatic visual Returns agent |
| Recovery | Charge-event/evidence prerequisites, upstream snapshots and safe review-required outcome | Real fee-report adjudication, justified claim amounts and dossiers |

The original `agents/*/app.py` organiser sample entry points must not be confused with fully implemented automatic managers. Recovery's original entry point is explicitly labelled an organiser stub with illustrative rules.

## 8. Pack identification and counting

The code prepares a constrained vision workflow:

- One primary package photograph supplies physical item counts.
- Explicit catalogue/reference images support identity comparison only.
- The supported reference catalogue is deliberately small, not arbitrary long-tail recognition.
- Expected order quantities are excluded from the model request and used later by deterministic comparison.
- Structured observations are schema-validated.
- Malformed/provider failures route to pending/review without another model call.
- Unbenchmarked matching output still requires review rather than automatic clearance.

**What has not been proven:** accurate product identity, repeated-item counts, similar-variant recognition or reliable decisions on real shipping boxes.

Seven prior RPC development experiments remain unsuccessful recognition/counting experiments: five failed from context/output limits, one produced valid JSON describing references instead of the six scene items, and one further reference-constrained attempt failed. These are not held-out evaluation cases or successful inspections.

The local launcher forces model provider `none`. No live inference was performed during the latest commerce implementation or Recovery reconnaissance. The earlier local Qwen3-VL 2B adapter remains experimental. No Azure calls were made in the recorded work.

## 9. Recovery Manager: implemented versus planned

### Implemented now

1. Record a charge event against an existing workflow.
2. Check for admissible completed upstream evidence before activation.
3. Collect same-workflow upstream run IDs, versions, outputs and human-review history.
4. Preserve those evidence snapshots with the Recovery result.
5. Return review-required / `CLAIM_ELIGIBILITY_UNVERIFIED` without creating a claim.
6. Expose an official-contract adapter that also conservatively returns UNCERTAIN/no claim.

### Not implemented yet

- CSV/XLSX fee-report import and quarantined-row storage.
- Normalized charge records and duplicate detection.
- Identifier matching through unit, shipment, order and tracking relationships.
- Automatic evidence retrieval across original fulfillment and separate return workflows.
- Authoritative charge-specific rules and deterministic fee adjudication.
- Justified claim-amount formulas.
- Draft/authorized/frozen claim lifecycle and immutable dossiers.
- Exportable dispute letters and structured claim packages.
- Independently labelled Recovery accuracy evaluation.

**Phase 0 only is complete** for the new Recovery request. The plan and findings are documented in `docs/recovery-plan.md` and `docs/findings.md`. Phase 1 awaits the user's approval; no Recovery implementation changes were made during reconnaissance.

Measured sample inventory: 61 synthetic fee rows covering 44 distinct unit IDs, split into 40 rows for org_demo_alpha and 21 for org_demo_bravo. These are data counts, not accuracy results. The requested `data/upstream/` and `data/README.md` are absent; actual files are under `data/sample/`.

## 10. Database and durability

The managers share **one PostgreSQL database**, with separate tables for different responsibilities and tenant isolation. They do not each use a separate database.

| Tables | Purpose |
|---|---|
| Existing catalogue/image records | Product information and private evidence references |
| `cw_units`, `cw_workflows`, `cw_runs` | Operational units, workflows and stage execution |
| `cw_events`, `cw_requests`, `cw_calls` | Audit, idempotency and durable call budget |
| `pod_workflows`, `pod_evidence`, `pod_outputs` | Official workflow envelopes, evidence and cached outputs |
| `commerce_inventory`, `commerce_orders`, `commerce_returns` | Stock reservations, purchases and return linkage |
| `commerce_events`, `commerce_policies` | Business provenance and immutable policies |

Migration 003 introduced the Pod bridge tables; migration 004 introduced commerce tables. Migration head **004** was verified. Existing records and original competition commits were preserved.

Return workflows use separate `RETURN-*` unit identifiers with explicit original-order/unit references. These relationships exist, but Recovery does not yet traverse them automatically.

Durable workers use saved queues, leases, version checks and fencing. Official evidence is append-only at the application/database permissions boundary. A content hash is not claimed to be an externally anchored tamper-proof record.

## 11. Security and model-call safety

- Customer and operations roles are separated.
- Tenant-scoped queries and PostgreSQL row-level security protect records.
- Private images require authorisation.
- Idempotency makes duplicate requests safe.
- Review and policy changes reject stale versions.
- Whole-unit model reservations persist across attempts and restarts.
- Original physical-unit identity is retained for return call-budget purposes.
- No hidden retries, model-based JSON repair or extra explanation calls are used.
- Local credentials remain in ignored account/configuration files, not committed source.

Previously disclosed API keys must not be reused. Local account-file sign-in is a development facility, not proof of secure public deployment.

## 12. Analytics

The dashboard derives metrics from saved orders, returns, workflows and stage records. It supports date, product/category, route, status and stage filters where available.

It reports order/return volumes, workflow states, stage processing and waiting information. Durations require recorded start and finish timestamps; missing historical measurements are omitted. Return dispositions use recorded decisions. Unsupported damaged dispositions are unavailable rather than inferred from customer reasons.

Synthetic fixtures are excluded by default and can be included explicitly. Analytics is tenant-scoped and does not add reporting totals to operational records.

## 13. Verification actually performed

| Check | Recorded result | Scope |
|---|---|---|
| Full backend suite with PostgreSQL enabled | **271 passed in 47.78 seconds**, latest Recovery Phase 0 rerun | Software behavior, including synthetic/mock cases; not AI accuracy |
| Real local browser workflows | **2 passed** | Customer order/history/analytics and operations upload/review/refresh/mobile |
| Browser fixture tests | **6 passed** | UI, reduced motion, errors, duplicate guards and authentication configuration |
| Frontend production build | Passed | TypeScript and production bundle |
| Scoped Ruff checks | Passed | E4/E7/E9/F checks on the modified backend areas and associated tests |
| Database migration check | `004 (head)` | Existing local database |

The last implementation full backend run also passed 271 tests in 41.00 seconds; Phase 0 reran the same suite. These are separate runs, not additional unique tests. Browser/build results belong to the implementation checkpoint and were not rerun for this documentation-only report.

Non-blocking build warnings remain for dependency annotations and bundle size. Mobile browser layout and camera-input attributes were checked; a physical phone-camera capture was not verified.

Fixes made during verification included mobile navigation wrapping and using INSERT RETURNING to detect successful call-budget reservations reliably.

Held-out labelled vision sample count remains **0**. Claim precision, exact product/count accuracy and real hosted inference performance remain unmeasured. Passing backend tests does not establish these metrics.

## 14. Local access and operation

- Operations: http://127.0.0.1:8014/operations.html
- Customer portal: http://127.0.0.1:8014/shop.html

These are local addresses and require PostgreSQL, the website and worker to be running. They are not public deployment URLs.

The startup command, local account-file locations and API route guide are documented in `docs/LOCAL_COMMERCE.md`. Do not share account files or place credentials in documentation/screenshots.

No cloud resources, paid upgrades or public deployment were performed in the local continuation. Vercel/Render/Supabase end-to-end hosting is not verified.

## 15. Remaining work and dependencies

1. Approve Recovery Phase 1 and resolve the recorded placeholder-policy and SILENT/UNCERTAIN questions.
2. Implement Recovery importer, matching, cross-workflow evidence, sourced rules, authorization and dossiers one approved phase at a time.
3. Verify Pod 7's assigned type and the shared team fork.
4. Integrate teammates' actual automatic agents without presenting stubs as real inference.
5. Obtain permitted evidence, authoritative fee sources and independent labels before reporting accuracy.
6. Validate Pack identification/counting with a safely configured provider and the one-call budget.
7. Complete the official-evidence UI and separate declared response models for all commerce projections.
8. Address cancellation inventory handling and return restocking if required for the next product scope.
9. Verify physical-phone operation and public end-to-end behavior only when deployment is authorized again.

This report describes a tested local application foundation with explicit unfinished AI and Recovery capabilities. It is not a declaration that all five automatic managers or the competition submission are complete.

## 16. Supporting documentation

- [Local setup and API runbook](LOCAL_COMMERCE.md)
- [Implementation checklist](IMPLEMENTATION_CHECKLIST.md)
- [Evaluation and test record](evaluation.md)
- [Recovery Phase 0 plan](recovery-plan.md)
- [Recovery findings](findings.md)
- [Architecture](../ARCHITECTURE.md)
- [Source provenance](../PROVENANCE.md)

This report is a documentation-only addition after commit 13309f7. It does not authorize or begin Recovery Phase 1.
