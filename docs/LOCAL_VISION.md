# Local vision with Render and Supabase

The current hosting plan avoids Azure model services. Render Free serves the
website and API; Supabase is intended for PostgreSQL and private image storage.
A separate worker on the owner's laptop runs an Ollama vision model. This is a
hybrid deployment: inspections require that laptop to remain on and connected.
Render and Supabase alone do not provide the model runtime in this plan.

## Model and configuration

Selected instruction model: `qwen3-vl:2b-instruct`, a 1.9 GB quantized vision-language model under Apache 2.0.
See [official model page](https://ollama.com/library/qwen3-vl:2b-instruct) and
[Ollama Windows installation](https://docs.ollama.com/windows).
Hardware suitability is not evidence of inspection accuracy.

Keep `MODEL_PROVIDER=none` until installation and a controlled test are ready.
For the local worker process only:

```dotenv
MODEL_PROVIDER=ollama
OLLAMA_BASE_URL=http://127.0.0.1:11434
OLLAMA_MODEL=qwen3-vl:2b-instruct
MODEL_TIMEOUT_SECONDS=600
WORKER_ENABLED=true
```

The model endpoint stays on loopback. Do not expose Ollama directly to the
internet. The local worker will need the dedicated Supabase database and storage
configuration, kept in local environment variables. Service-role credentials
must never enter frontend code, Git, screenshots, or chat.
Keep the Render worker disabled. Enabling a worker can process existing pending
captures: use a targeted attempt for initial evaluation.

Start the installed project-local runtime with `powershell -File scripts/start-local-model.ps1`.
For a controlled existing capture, run `.venv\Scripts\python.exe -m backend.worker --attempt-id <attempt-UUID>`.
For continuous processing on this laptop, run `powershell -File scripts/start-local-worker.ps1`. It starts the model runtime if needed, selects the explicit instruction model, and persists a first-activation queue cutoff in ignored `.local/worker-cutoff.txt`. Keep that cutoff file: historical research views are excluded, while new work queued during downtime is retained.
When enabling the worker for the first time, add `--created-after <ISO-timestamp-with-timezone>`
to exclude historical captures (for example, repeated research views). Preserve that
same cutoff on restart so new uploads queued while the laptop was offline are processed.
The cutoff is a queue control, not a way to reset a unit's one-call reservation.

## Counting and identification

One model request contains the primary counting photo, catalogue descriptions,
and up to sixteen reference photos explicitly labelled as references. Expected order
quantities are excluded. The model reports visible instances, possible identities,
identity verification, counting uncertainty and visibility limitations.
For local inference, the primary image is resized to a maximum edge of 1024 pixels. Up to sixteen references become a single labelled contact sheet with 240-pixel image tiles, preserving aspect ratio without cropping. Original evidence remains unchanged. This bounds input size but small labels can become harder to read; ambiguity must remain uncertain.

Ordinary code derives per-SKU counts, compares the order, applies decision rules
and stores evidence. Reference photos are never counted as box contents.

The call reservation is committed before inference. Timeouts, malformed JSON,
and truncated responses do not trigger retries or repair calls. Human review
remains available. Mock transport tests verify these properties but do not measure
model accuracy. Research-photo evaluation must report actual model output even
when it fails or remains uncertain; it cannot establish performance on customer
products or hidden box contents.

## Remaining deployment work

The dedicated Supabase project, database migration, private bucket, and secure
hosted authentication must be configured before public deployment. Supabase Auth
is implemented with administrator-assigned workspace roles; live sign-in still
requires dedicated project configuration. No live Render
service or complete cloud deployment is claimed by this document.

The project-local runtime uses Flash Attention and a q8_0 context cache to fit this laptop. The local request uses an 8192-token context and a 3000-token output cap. The primary view and catalogue sheet form two images in one request. These are engineering limits, not accuracy guarantees.

Use the explicit `-instruct` tag. The bare `qwen3-vl:4b` tag resolved to a thinking model during testing and exhausted the output cap without a final answer, even when thinking was disabled in the request. No failing unit was retried.
