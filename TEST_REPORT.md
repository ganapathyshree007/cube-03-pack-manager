# Post-competition verification — 1 October 2026

Original competition snapshot: `1e503a0` on `main`. This audit is on `post-competition/completion-audit`; submission eligibility for later work is unverified.

- **100 backend tests passed in 3.58 seconds** with `PACK_POSTGRES_TESTS=1` against actual local PostgreSQL, after the hosted adapter was added. These include forced RLS, image authorization, idempotency, stale reviews, durable one-call reservations, recovery/competing workers, private rejected-response retention, occlusion, and single-request Gemini success/timeout/quota/schema fixtures.
- **Six browser tests passed in 7.4 seconds** against a separate local API on port 8001 with `MODEL_PROVIDER=none` and tenant `browser-audit-post-competition`. The real API flow covered product/order creation, synthetic image upload, pending result, refresh, attributed review and retake. Other tests cover keyboard focus, automated accessibility, mobile landing layout, and mocked Supabase rejection/per-check review. No browser fixture triggered live inference.
- Frontend production build and Ruff passed. The bundle is approximately 895 kB before gzip, with a chunk-size warning; optimization remains desirable.
- Google AI Studio model-list request returned HTTP 200 and listed `gemini-2.5-flash` with 1,048,576 input / 65,536 output token limits. This was metadata access, **zero hosted inference calls**. Account owner confirmed Free tier with billing disabled; account billing was not independently audited.
- One additional **real local research** inference ran on RPC 583, exactly once: 18,750 ms worker processing, 18,578 ms model adapter timing, 6,359 prompt / 408 output tokens. It failed per-product identity/counting and falsely stopped the constructed correct research order. See EVALUATION.md.

No public authentication/upload/inference/refresh/isolation test has passed, and no held-out benchmark has run. Backend tests do not measure vision accuracy. The latest UI observation-list change requires its final browser/build recheck, recorded below when executed.

Earlier verification logs are preserved in [VERIFICATION_HISTORY.md](docs/VERIFICATION_HISTORY.md). Statements there such as “model unconfigured” describe historical stages only.
