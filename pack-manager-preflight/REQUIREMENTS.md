# Requirements and unresolved contract

## Source distinction

| Requirement | Source | State |
|---|---|---|
| One individual specialized agent; official fork | Handbook pp. 3–6 | Confirmed |
| Build opens 25 Sep 2026, 09:00 IST; submission opens 27 Sep; deadline 1 Oct 18:00 IST | Handbook pp. 5–6 | Confirmed; separate operational cutoff may be announced |
| Rubric 15/25/25/20/15 | Handbook p. 9 | Confirmed |
| Evidence fields and PASS/FAIL/UNCERTAIN check verdicts | Handbook p. 11 | Field names confirmed; exact schema absent |
| At least 50 unseen vision units where applicable; two independent human labels before agent run | Handbook p. 12 | Confirmed |
| README, architecture, demo, evaluation, fork, LinkedIn URL; deployment URL where applicable | Handbook pp. 7–8 | Confirmed |
| Exact open-box SKU/quantity verification and eight scenarios | Participant specification | Requested; separate PCK statement missing |
| React/FastAPI/LangGraph/PostgreSQL/Azure architecture | Participant specification | Proposed unless starter mandates alternatives |
| Public Azure application | Participant specification | Project requirement, stronger than handbook's conditional URL |
| 64 held-out cases | Participant specification | Proposed target, not organizer minimum |
| SEAL and STOP & FIX | Participant specification | UI labels; not presumed official outcome enums |

No direct conflict has been established. The handbook describes Pack Manager broadly as packaging readiness; the participant supplies narrower SKU/count verification. Confirm the detailed track requirements before fixing check keys or final outcome mappings.

## Contract questions to resolve from starter

Read README, RULES, all applicable AGENTS.md files, setup instructions, schemas and validation fixtures before editing the fork. Determine:

- Types/requiredness of record_id, schema_version, organization_id, client_id, agent, subject, captured_at, operator_label, images, checks, outcome, overrides, status and content_hash.
- Allowed check keys, confidence scale/nullability, status/outcome enums, timestamp encoding, image representation, schema version and extra-field policy.
- Official content-hash canonicalization, immutable field inclusion and override behavior.
- Authentication, tenant identifiers, persistence conventions and mandated frameworks.
- Starter test commands, supported runtimes and integration/export fixtures.

Do not present a provisional record as an official-schema example. Generate that deliverable only from an actual persisted inspection after mapping the real contract.

## Acceptance gates

1. Boot: official fork read, dependencies locked, PostgreSQL migrated, actual screen connected to API.
2. Real slice: authorized versioned order → saved real photo → queued job → actual vision and model-selected tools → deterministic checks → persisted result → UI evidence and export.
3. Recovery: distinct clear/ambiguous tool paths; restart preserves pause; corrected box creates new attempt; timeout/malformed output never approves sealing.
4. Workflow: catalogue/order CRUD, history, review attribution, isolated public sessions, responsive keyboard-accessible UI and error states.
5. Cloud: authorized resources, deployment and real inference through verified HTTPS URL with laptop-independent worker.
6. Evaluation: frozen prompts/capture rules; real unseen cases; prior independent labels; metrics with denominators and limitations.

Never collapse implemented, locally tested, real-provider tested, cloud deployed, public URL verified and held-out evaluated into a single completion claim.
