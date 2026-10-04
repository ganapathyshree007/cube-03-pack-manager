# Local integration verification — 4 October 2026

Branch `post-competition/integrated-local-backend`, based on `b10e2c3`. Original competition snapshot `1e503a0` preserved. No deployment, hosted inference or teammate repository mutation.

## Inspection and baseline

- Inspected all five repository READMEs/rules/data documentation and available database models, APIs, evidence schemas and tests. Exact source commits and discrepancies are in [INTEGRATION_COMPARISON.md](INTEGRATION_COMPARISON.md).
- Receiving contains starter data only. Prep's source uses scenario/filename-driven findings in its deterministic engine. Returns persists in memory and can fall back to mocks. Recovery includes SQLite/PostgreSQL models and charge/evidence reasoning. Those limitations were not imported as hidden functionality.
- Prep live inspection page and full 3:03 walkthrough auto-generated transcript were inspected read-only. Workflow observations: SKU/category and rules, angle-labelled uploads, uncertain rear-view request, feedback, history/activity and JSON output. Video narration does not verify accuracy or training.
- Docker daemon unavailable; direct local PostgreSQL 17 started successfully. First baseline with PostgreSQL stopped failed from connection errors. After starting it, **101 existing tests passed in 7.11 seconds**, before code changes.
- Alembic upgraded local database from 001 to **002 (head)**. Original four Pack tables preserved; six integrated tables added.

## Implemented verification

- First integrated run: **22 passed** against PostgreSQL.
- Expanded suite: **133 passed in 17.11 seconds**. Final full suite after readiness/local-only guard tests: **137 passed in 18.98 seconds** (101 existing + 36 new integrated cases), zero failures/skips with `PACK_POSTGRES_TESTS=1`.
- Ruff check passed for the integrated code/tests.
- Real loopback HTTP API and a separate worker process ran at port 8010. Private generated bearer token used locally, not printed or committed.
- HTTP fixture demonstration persisted workflow `0b164028-214d-469b-8bdf-fe6e5dd82191`: Receiving manual fixture review → merchant Pack manual fixture review → explicit synthetic charge → Recovery UNCERTAIN with `claim_supported=false`. No Prep/Returns stage appeared without a corresponding route/event.
- Report saved locally at `.local/integrated-demo.json`; image clearly labelled SOFTWARE TEST FIXTURE. It is not a real product photo or a recognition success.
- First HTTP readiness check found missing access to Alembic's administrative version table. Fixed by checking required application tables instead of broadening database permissions; subsequent HTTP demonstration succeeded.
- Restarted both the actual API and worker processes after final code changes. Authenticated HTTP reopened the same workflow with states `completed`, `completed`, `review_needed`; saved image returned 200, anonymous image access returned 401, review queue returned 200, and readiness reported `integrated.v1` with inference blocked. Machine-readable local verification: `.local/integrated-restart-verification.json`.
- Final `alembic current`: **002 (head)**. Final read-only reference Git checks: all four teammate clone worktrees clean. Local changes do not include a push or deployment.

## Coverage and interpretation

Integration tests cover FBA/merchant/3PL routing; no double fulfillment; unknown route and explicit correction; receiving discrepancy/uncertainty; each unavailable visual manager; event linkage and deduplication; return disposition restrictions; no invented claims; local images and tamper rejection; cross-tenant/role denial and forced RLS; append-only audit permissions; stale and duplicate review; original findings/override preservation; concurrent starts/worker claims; cancellation/hold/resume; pre-dispatch retry/backoff/exhaustion; possible-dispatch timeout/malformed-result/DB-error handling; persistent call reservations; lease expiry and stale-owner fencing; DB transaction rollback after reservation; safe storage retry; input validation and token verification.

Provider failure cases are injected state-machine tests, not real model traffic. Schema-invalid review input is rejected; no automatic model-output parser is enabled in the integrated service. Database-outage response is injected; transaction rollback and reconnection/lease recovery use real PostgreSQL. This is not a full hardware power-loss or disk-corruption exercise.

## Incomplete/blocked

- Automatic vision for all integrated managers: BLOCKED. Existing Pack Ollama research remains experimental; no new accuracy measurements were made.
- Receiving executable source: absent. Prep scenario outputs cannot be treated as observations; Returns' cloud inference is excluded by local-only scope. Legacy Pack attempt import has no verified cross-contract mapping yet.
- Recovery eligibility/financial claim generation: BLOCKED until charge-specific authoritative rules, timing, identifiers and sufficient admissible evidence are supplied/validated. Evidence collection/review itself works locally.
- New API manual findings are explicitly attributed; they do not prove production condition grading, channel compliance or quantity accuracy.
- No final-round instructions supplied/found; dispatch disabled. No 50-unit independently double-labelled held-out evaluation conducted.
- Production authentication, integrated UI and cloud/public endpoints are outside this local backend delivery. No hosting changes or model expenses incurred.

Only the local backend/manual workflow and tested safety paths are verified. Do not call the five-manager vision product complete.
