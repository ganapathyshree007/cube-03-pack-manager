# Render + Supabase deployment preparation

Status: configuration prepared and storage adapter tested with mocked HTTP. No live Render/Supabase deployment verified yet. Singapore is authorized. Existing unrelated projects must remain untouched.

## Resources

`render.yaml` now declares only a **Free Singapore Docker web service**. The user explicitly deferred the paid worker. `WORKER_ENABLED=false` keeps captures pending for human review and prevents inference processing even if model credentials are present. Free web services can sleep; this is not an always-on production service. Do not create a paid worker or upgrade a plan. Azure credits do not pay Render or Supabase. [Render pricing](https://render.com/pricing) and [compute plans](https://render.com/docs/compute-plans).

Create a dedicated Supabase project in [Southeast Asia (Singapore)](https://supabase.com/docs/guides/platform/regions), preferably in a Free organization if there is a free project slot. Supabase's free project allowance is account-limited; do not delete or upgrade existing projects to make room. [Supabase billing](https://supabase.com/docs/guides/platform/billing-on-supabase).

## Configuration sequence

1. Create the dedicated Supabase project. The owner enters its database password locally; never put credentials into chat or GitHub.
2. Run existing database migrations with an administrative connection, then use a separate non-owner, non-superuser, `NOBYPASSRLS` application role for web and worker. Do not run the application as Supabase `postgres` or `service_role`. Preserve forced RLS on every app table. Use a TLS database connection and the dashboard-provided connection details; keep migration credentials out of the running service environment.
3. Create a **private** `evidence` storage bucket. Do not add public read policies. Set server-only `SUPABASE_URL`, legacy `SUPABASE_SERVICE_ROLE_KEY` and `SUPABASE_STORAGE_BUCKET`. The storage adapter uses the legacy service-role JWT as Bearer authorization; a new `sb_secret_…` key is not currently interchangeable. Never expose this key in frontend variables. Application record authorization happens before server-side object access. Direct signed uploads remain outstanding.
4. Complete Entra app registration and roles; this version still uses Entra for hosted login even though Supabase stores data. Set `AUTH_MODE=entra`, tenant, audience, client ID and scope from `.env.example`. Register the final site's `/workspace` as the SPA redirect URI. Public landing page requires no login; workspace requires authenticated access. Never deploy with local authentication mode.
5. Configure the real Azure vision deployment, endpoint, API version and key in Render's secret environment settings. Render does not inherit an Azure managed identity. Without model access, keep the visible “Model not configured” state; no fake inference fallback. Configure a conservative daily limit and separate provider-side budget controls. The per-organization count limit is not a dollar spending cap.
6. Build the repository Docker image and deploy only the free web resource, then verify readiness, hosted sign-in, tenant isolation, private image access and one-call behavior. Verify a pending saved capture. Actual automatic inference remains deferred until a worker is explicitly authorized and running. Never claim model validation from fixture tests.
7. Finish the contract gaps recorded in `SUPPLIED_DATA_REVIEW.md`, validate hosted capture end to end, record the real demo and update README with the verified deployment URL.

Account sign-in is verified. An empty `cube-pack-manager` Render project has been created; Supabase creation is handed to the owner for the new password. Current blockers: available Supabase free slot and dedicated project secrets; hosted login setup; eligible configured vision model; remaining contract workflow work. Do not deploy unrelated project credentials or use their database/bucket as a shortcut.
