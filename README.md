# Pack Manager

**Order verification before sealing.** A constrained AI inspection workflow for merchant-fulfilled sellers and 3PL pack stations. One model call observes an open box; ordinary code compares supported identities/counts with the saved order. Unclear evidence remains UNCERTAIN, discrepancies STOP & FIX, and errors save a pending record without AI permission to seal.

Built in the supplied fork. The original problem statement is preserved in [docs/STARTER_README.md](docs/STARTER_README.md). RULES.md is unchanged.

**Post-competition continuation:** integrated local work is on `post-competition/integrated-local-backend`, starting from `b10e2c3`. Original Round 2 snapshot `1e503a0` remains preserved in history; it is not the current main HEAD. The handbook/RULES deadline is 1 October 18:00 IST; the participant reports a portal deadline of 23:59 IST. No extension document has been verified. Do not present these changes as the original submission.

**Integrated local backend (4 October):** a separate loopback API combines Receiving → Prep **or** Pack, plus explicit Returns and Recovery events. PostgreSQL stores durable runs, local evidence, attributed manual reviews and failure recovery. Automatic visual adapters are BLOCKED; the working demonstration uses clearly labelled manual software fixtures, not live AI. Recovery gathers evidence but cannot approve or submit a claim. No cloud deployment or inference is used by this service. See [local run/API instructions](docs/INTEGRATED_LOCAL.md), [source comparison](docs/INTEGRATION_COMPARISON.md), and [verification report](docs/INTEGRATED_VERIFICATION.md). The existing Pack website and experimental adapter are preserved separately.

**Current validation:** local model inference runs, but research tests did not establish correct product identification or counting. Local-model results require human review. See [actual test results](docs/LOCAL_MODEL_RESULTS.md).

## Implemented scope

- React/TypeScript workspace: catalogue/reference photos, orders/CSV import, capture, results, history, retake, supervisor review and JSON export.
- FastAPI, SQLAlchemy, Alembic and PostgreSQL with forced row-level security and a non-bypass application role.
- Durable jobs and one inference reservation per organization + unit_id, shared across all attempts. Failed calls are never retried automatically.
- Local Ollama vision adapter and private Supabase storage adapter implemented. The public target is Render Free + Supabase with a separately hosted Gemini endpoint; the laptop is local research only; see [local vision setup and remaining deployment work](docs/LOCAL_VISION.md). Model accuracy and hosted operation require separate verification.
- Deterministic reconciliation; synthetic observations exist only in isolated software tests, never as a live UI mode.
- Legacy Azure configuration remains optional and disabled by default. Azure model setup was cancelled before deployment or inference; an unused account/resource group was created. No live public deployment URL is verified.

This is not an autonomous multi-tool LLM agent. The participant explicitly selected the starter's one-call rule over the earlier controller design. No model calls generate explanations or choose tools.

## Start locally

### Integrated operations frontend (5 October, post-competition)

The new local operations interface is connected to the integrated API: searchable workflows, route-specific timelines, private evidence upload, attributed manual review and saved history. Automatic visual inspection remains **BLOCKED**. This does not establish product recognition/counting accuracy.

Start PostgreSQL, the integrated API on **8010**, and its worker using [the local backend instructions](docs/INTEGRATED_LOCAL.md). Then:

```powershell
cd C:\SYDON\cube-03-pack-manager\frontend
npm ci
npm run dev -- --port 5173
```

Open **http://127.0.0.1:5173/operations.html**. Select the ignored `.local/integrated-client.json` using **Local account file**; it is read locally and the token authenticates requests to the loopback API. Tokens stay in memory unless you explicitly choose tab-session persistence. Never copy this file into source or build settings.

`INTEGRATED_API_TARGET` in frontend local configuration defaults to `http://127.0.0.1:8010`; it is a server-side Vite proxy setting, restricted to loopback. No cloud credentials are required. All five managers share one PostgreSQL database; `cw_runs` stores their separate outputs and `cw_events` stores the audit trail. Images use authorized local file storage with database metadata.

Verified: **138 backend tests, 12 browser tests, frontend build and Ruff passed**. The browser suite includes a real local API upload/review/refresh flow and clearly labelled UI fixtures. See [frontend endpoints, verification and limitations](docs/OPERATIONS_FRONTEND.md). The original Pack interface is preserved separately.

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

1. Add real authorized products and distinguishing variants. Up to four reference images per SKU; 30 catalogue SKUs maximum. Experimental local and Gemini adapters support only 1–4 active products, each with a valid reference; one reference per product enters the call. The broader 30-SKU database limit does not imply model support. References compare identity; only the primary photo contributes counts.
2. Create an order with a stable physical unit ID. Positive whole quantities only; duplicate SKU lines merge. CSV columns: order_id, unit_id, channel, order_lines. Lines use SKU:qty;SKU:qty. observed_in_box and operator_verdict are ignored.
3. Expose every item and label in one layer. Choose the order and upload its open-box photograph.
4. With no configured provider/worker, Save for review persists pending evidence. With a configured provider and worker, inspection processes once and displays checks and evidence.
5. A corrected box starts a new attempt. Retakes do not reset the unit budget. Supervisor review records actor/reason separately from the automated result.
6. The workspace export remains provisional. A strict Evidence Contract 1.1 reader is available at `/v1/records/{record_id}` for eligible captures; the full capture/review migration is still in progress. See [supplied-data review](docs/SUPPLIED_DATA_REVIEW.md).

## Model configuration and deployment

Default `MODEL_PROVIDER=none` makes no inference calls. Local experiments use `ollama` with `qwen3-vl:2b-instruct`; its recognition/counting failed validation. Keep `LOCAL_MODEL_REVIEW_REQUIRED=true`.

The new optional `gemini` adapter uses one REST request to the verified model ID `gemini-2.5-flash`. Set server-side `GEMINI_API_KEY`, `GEMINI_MODEL`, and `GEMINI_FREE_TIER_CONFIRMED=true` only after checking the account is Free tier with billing disabled. Keep `HOSTED_MODEL_REVIEW_REQUIRED=true`. Quota errors become pending; never enable paid billing or retry the same unit. Key/model-list access was verified, but no hosted image inference has been verified. Do not share keys in chat, source, browser code or exports. Replace any key disclosed in chat.

Google's free tier may use content for product improvement. Only submit photographs permitted for that processing. Restricted RPC files remain private local research. No Azure calls have been made; legacy Azure modules are disabled unless explicitly selected.

Prefer the existing same-origin React + FastAPI Docker deployment on Render to avoid introducing a second origin before the current app works. Supabase supplies private storage, authentication and PostgreSQL. Vercel is an optional later frontend split, not a deployed component. `python -m backend.service` supervises the API and optional remote-inference worker; jobs/reservations remain in PostgreSQL across restarts. It rejects local auth, local storage and Ollama. Free Render can sleep, interrupt jobs or suspend on quota exhaustion: this is a limited preview, not an always-on production service. See [deployment runbook](docs/DEPLOYMENT_RENDER.md).

No public app URL is currently verified. Never treat localhost or a dashboard URL as the deployment URL.

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

## Verified and unfinished

See [TEST_REPORT.md](TEST_REPORT.md) for current software results and [EVALUATION.md](EVALUATION.md) for the seven original RPC experiments plus one separately reported post-competition experiment. Valid JSON is not proof of recognition. No held-out accuracy or own-product performance has been established.

The interface supports catalogue/order management, desktop uploads, saved pending inspections, expected-versus-observed tables, readable model claims, attributed reviews and history. Phone-width layouts and keyboard behavior were software-tested; actual phone camera capture is not yet verified. No independent barcode decoder or calibrated confidence is claimed.

Outstanding: dedicated Supabase provisioning and secrets, real hosted authentication/storage, authorized hosted-test photos, public deployment/end-to-end inference, 50 unseen units with two prior independent human labels, full official capture/direct-upload/share workflow, demo recording and LinkedIn publication. Detailed status and exact actions are in [SUBMISSION_CHECKLIST.md](SUBMISSION_CHECKLIST.md). Do not call the project production-ready or fully complete.
