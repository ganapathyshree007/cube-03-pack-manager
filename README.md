# Pack Manager

**Order verification before sealing.** A constrained AI inspection workflow for merchant-fulfilled sellers and 3PL pack stations. One model call observes an open box; ordinary code compares supported identities/counts with the saved order. Unclear evidence remains UNCERTAIN, discrepancies STOP & FIX, and errors save a pending record without AI permission to seal.

Built in the supplied fork. The original problem statement is preserved in [docs/STARTER_README.md](docs/STARTER_README.md). RULES.md is unchanged.

## Implemented scope

- React/TypeScript workspace: catalogue/reference photos, orders/CSV import, capture, results, history, retake, supervisor review and JSON export.
- FastAPI, SQLAlchemy, Alembic and PostgreSQL with forced row-level security and a non-bypass application role.
- Durable jobs and one inference reservation per organization + unit_id, shared across all attempts. Failed calls are never retried automatically.
- Local Ollama vision adapter and private Supabase storage adapter implemented. The current plan is Render Free + Supabase with a laptop model worker; see [local vision setup and remaining deployment work](docs/LOCAL_VISION.md). Model accuracy and hosted operation require separate verification.
- Deterministic reconciliation; synthetic observations exist only in isolated software tests, never as a live UI mode.
- Legacy Azure configuration remains optional and disabled by default. Azure model setup was cancelled before deployment or inference; an unused account/resource group was created. No live public deployment URL is verified.

This is not an autonomous multi-tool LLM agent. The participant explicitly selected the starter's one-call rule over the earlier controller design. No model calls generate explanations or choose tools.

## Start locally

Use Docker Desktop (Linux engine), Python 3.12 and Node 24. Versions are locked in uv.lock, requirements.lock and frontend/package-lock.json.

```powershell
Copy-Item .env.example .env
docker compose up --build -d
```

Open http://127.0.0.1:8000. Local authentication is development-only; never expose it publicly. Development database credentials must not be used in Azure.

Host development:

```powershell
uv sync --frozen
docker compose up -d db
uv run alembic upgrade head
cd frontend
npm ci
npm run build
cd ..
uv run uvicorn backend.main:app --host 127.0.0.1 --port 8000 --no-proxy-headers
# Separate terminal:
uv run python -m backend.worker
```

Docker Desktop failed to start on the build machine. Local verification used workspace-local PostgreSQL 17 binaries on loopback, not SQLite. The fallback runtime is ignored by Git; Docker Compose is the standard setup.

For a local interface walkthrough, run `uv run python -m scripts.seed_local_demo` while the server is running. This adds three clearly labelled fictional products, three orders and one draft inspection without photographs, model calls or invented outcomes. Archive these demo products before configuring a real merchandise catalogue. See [docs/REAL_DATA_SETUP.md](docs/REAL_DATA_SETUP.md) for the real inspection inputs.

## Operator workflow

1. Add real authorized products and distinguishing variants. Up to four reference images per SKU; 30 catalogue SKUs maximum. The first six configured reference images enter the single model call, a documented baseline limit.
2. Create an order with a stable physical unit ID. Positive whole quantities only; duplicate SKU lines merge. CSV columns: order_id, unit_id, channel, order_lines. Lines use SKU:qty;SKU:qty. observed_in_box and operator_verdict are ignored.
3. Expose every item and label in one layer. Choose the order and upload its open-box photograph.
4. Without Azure, Save for review persists pending evidence. With a configured provider and worker, inspection processes once and displays checks and evidence.
5. A corrected box starts a new attempt. Retakes do not reset the unit budget. Supervisor review records actor/reason separately from the automated result.
6. The workspace export remains provisional. A strict Evidence Contract 1.1 reader is available at `/v1/records/{record_id}` for eligible captures; the full capture/review migration is still in progress. See [supplied-data review](docs/SUPPLIED_DATA_REVIEW.md).

## Secure Azure model configuration

Edit ignored .env locally. Set AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_API_VERSION and AZURE_OPENAI_VISION_DEPLOYMENT to values from your actual deployment. Do not guess region, API version or model capability. The adapter requires image input, JSON output and max_completion_tokens support; real capability testing is pending.

Prefer DefaultAzureCredential: Azure CLI login locally, or managed identity with the Azure OpenAI inference role in cloud. If needed, use AZURE_OPENAI_API_KEY only in ignored local .env or approved Key Vault configuration. Never put secrets in React, Git, chat or exported records. SDK retries are zero. Capability testing consumes its dedicated unit's one-call budget; do not probe an evaluation unit and run it again.

## Verification

```powershell
uv run ruff check backend tests evaluation
uv run pytest -q
$env:PACK_POSTGRES_TESTS='1'
uv run pytest -q
cd frontend
npm run build
npx playwright install chromium
npx playwright test
```

Browser tests require the server, migrated database and .local/test-only.png. CI creates an explicitly synthetic image. Browser test records are labeled SOFTWARE TEST ONLY. None of these checks measures vision accuracy.

## Remaining gates

The official Evidence Contract 1.1 has now been supplied; full workflow compatibility remains in progress. Real-provider access, verified product/SKU mappings, genuine packing scenes, human review labels, held-out evaluation, hosted sign-in, cloud isolation verification and real demo recording remain pending. Singapore is authorized. The latest hosting constraint is free Render/Supabase only, with the paid worker deferred. The Azure credit balance and expiry remain unverified; no paid resources have been created. See [Render deployment preparation](docs/DEPLOYMENT_RENDER.md). Docker image build and execution passed in [GitHub CI](https://github.com/ganapathyshree007/cube-03-pack-manager/actions/runs/36595446848). No measured accuracy, latency, savings or commercial advantage is claimed.

Hosted access supports Entra sign-in and optional isolated anonymous demo sessions. Demo sessions have no supervisor privileges, expire after 24 hours and are capped at ten images and two submissions/day. The demo stays disabled until a signing secret is configured. Orders/history have search and 50-row pagination; supervisors can archive products while retaining snapshots. A separate attributed packed acknowledgement never changes the automated outcome. There is no independent barcode decoder. Image-only verification cannot certify hidden contents or capture freshness.

See ARCHITECTURE.md, EVALUATION.md, DEPLOYMENT.md, TEST_REPORT.md, docs/CONTRACT.md, docs/FINDINGS.md and SUBMISSION_CHECKLIST.md.
