# Offline operations installation

This uses the built React website, FastAPI, a durable worker, one existing PostgreSQL database and private local image files. No Vite server, Supabase, Neon, Render, model API or internet connection is required at runtime. Python dependencies and the frontend build must already be installed; a fresh-machine dependency download still requires internet or a separately prepared package cache.

## Start on this laptop

```powershell
Set-Location C:\SYDON\cube-03-pack-manager
.\scripts\start-operations-offline.ps1
```

Open **http://127.0.0.1:8013/**. Choose **Local account file** and select `C:\SYDON\cube-03-pack-manager\.local\integrated-client.json`. Keep that file private. The optional tab-session checkbox allows reload without selecting it again.

The launcher starts the existing local PostgreSQL cluster if its bundled installation is present and not responding. It never initializes, resets or drops a database. It verifies tables, application-role safety, writable local storage and the built frontend before launching the site. Existing accounts are preserved. A missing installation/build/account pair reports a setup error rather than downloading or changing credentials.

Use `-CheckOnly` to check prerequisites, or `-Port 8014` if 8013 is occupied. An occupied port is not killed. The Python supervisor owns its API and worker processes; Ctrl+C stops those children and preserves saved records. PostgreSQL remains running. If the site was already started in the background by the assistant, use its existing URL instead of launching a duplicate.

Runtime configuration forces `INTEGRATED_MODE=local`, `MODEL_PROVIDER=none`, `STORAGE_MODE=local`, and disables the legacy Pack model worker. The database connection must still point to local PostgreSQL using the restricted application role. The ignored `.env` is not rewritten. Old cloud keys are neither needed nor sent.

## Included workflow

Connect → register synthetic product/unit → start workflow → upload synthetic evidence → review manager findings manually → save an attributed decision → reopen history. Receiving routes to Prep or Pack according to the saved route. Returns/Recovery require explicit events. All five managers share the existing database; each run has its own manager, unit, workflow and audit trail.

Automatic product recognition/counting is **unavailable**. No offline model is installed or enabled by this launcher. The previously failed Ollama research is not presented as working inference. Recovery collects prior evidence but does not create a supported claim. The Round 3 demo uses synthetic data only.

## Maintenance and verification

After changing frontend source, rebuild before starting/reloading the offline site:

```powershell
Set-Location C:\SYDON\cube-03-pack-manager\frontend
npm run build
```

The production assets include local fonts. The offline browser test blocks every request except localhost and exercises the real database/API/manual-review workflow:

```powershell
$env:OPERATIONS_TEST_BASE_URL='http://127.0.0.1:8013'
npm test -- operations.spec.ts --grep 'real local backend'
```

This is not a public URL or a hosted inference test. A physical phone cannot reach the laptop's loopback address; phone-width browser layout is tested, while physical camera hardware remains unverified.

Verified on 5 October 2026: the built-site end-to-end test passed in 14.0 seconds with external browser traffic blocked and zero attempted external page requests. It exercised upload, attributed manual review, persisted history, refresh, authorized image access, anonymous rejection and responsive layout. Final PostgreSQL-enabled backend suite: 160 passed in 8.09 seconds; Ruff passed. The earlier complete browser suite passed 13 tests; this additional run specifically tested the built offline site instead of Vite. These are software checks, not vision accuracy results.

Preserve both the PostgreSQL database and `.local/images` when backing up. Copying only the website does not include records/evidence. Account files and `.env` contain private credentials; keep them out of Git, shared archives and chat. The launcher does not create or publish a backup.
