# Verification report — 28 September 2026

This report distinguishes software fixtures from actual vision evidence. Latest local pass: 55 backend tests passed, 3 browser tests passed, frontend production build passed and lint passed. Both Bicep templates compiled and Docker Compose configuration validated during this build; cloud execution remains unverified.

## Executed

- Python 3.12.7, Node 24.15.0, npm 11.12.1, uv 0.11.14.
- PostgreSQL 17.11 local binaries, bound to 127.0.0.1. Application uses pack_app without superuser/RLS bypass.
- Alembic initial migration executed. All four business tables enable/force RLS.
- Backend unit/integration checks executed against PostgreSQL, including reconciliation, unknown counts, malformed observations, hash determinism, uploads, cross-tenant denial, idempotency, review attribution/staleness, provider failure and one-call reservation across attempts. Also tested competing workers, crash-after-reservation recovery, storage outage, independent demo sessions/expiry, submission quota, CSV import, catalogue archival and packed acknowledgement without changing the original hash.
- React TypeScript production build executed.
- Additional regression checks cover signed authentication tokens, original-image byte/hash preservation and tenant isolation, bounded worker lease recovery, and cancellation of pending model work after human review. The model remains unconfigured; these checks use explicitly labelled software fixtures.
- Playwright exercised real API/database flow: create product/order, upload explicit software-test image, pending result, refresh, human review, new attempt. Keyboard focus regression fixed. Automated axe checks found no WCAG A/AA violations on the tested overview and pending inspection views; this is not a complete accessibility certification. Responsive screenshots taken at desktop, 820px tablet and 390px phone; no horizontal overflow in inspected workflow.
- Bicep CLI 0.47.16 compiled foundation and application templates successfully including optional demo configuration.

## Not established

No real vision inference, official contract validation, customer usability study, calibrated confidence, held-out accuracy, model latency/cost, cloud deployment, hosted Entra flow or real demo recording. No generated image is counted as an evaluation unit.

Docker Desktop failed before engine startup with an inaccessible dockerInference socket. No global Docker data was removed or reset. Workspace-local PostgreSQL allowed actual persistence and RLS testing without substituting SQLite. Container build and execution have since passed on GitHub's Linux runner, as recorded below.

29 September update: the first GitHub Actions run successfully built the Docker image, ran backend/browser tests and compiled Bicep. Its final uv cache cleanup timed out because the background `uv run` server held the cache lock. CI now starts that server directly with the installed Python and stops it explicitly.

[Run 36595446848](https://github.com/ganapathyshree007/cube-03-pack-manager/actions/runs/36595446848), commit `4e5b19d`, passed completely: backend/browser tests, frontend build, Docker build, built-container startup and PostgreSQL readiness, frontend serving, empty-tenant summary, worker no-job execution and Bicep compilation. Local Docker Desktop remains unavailable. This confirms Linux container execution, not Azure deployment or real inference.

Commands: uv run ruff check backend tests evaluation; PACK_POSTGRES_TESTS=1 uv run pytest -q; npm run build; npx playwright test; bicep build infra/foundation.bicep; bicep build infra/application.bicep. Tests use isolated tenant IDs; browser records explicitly say SOFTWARE TEST ONLY.

After browser testing, run `uv run python -m scripts.clean_browser_fixtures` in local mode to remove only the explicitly identified browser fixtures and their unshared images. Other records are retained.
