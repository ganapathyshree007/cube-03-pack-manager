# Deployment runbook — Azure not deployed

No subscription, resource group, region, model deployment, permission or spending allowance has been supplied. No paid resource has been created. Bicep compilation is local syntax/type validation only, not resource availability, quota, deployment success or a verified URL.

## Required inputs and authorization

- Explicit authorized subscription, existing resource group, region, resource scope and budget ceiling/contact email.
- Azure CLI authentication and permissions to provision listed resources and role assignments in that scope. Confirm PostgreSQL 17/B1ms and Container Apps availability in the chosen region.
- Entra API app and SPA registration, delegated scope, API audience, and Pack.Operator / Pack.Supervisor app roles. Configure the actual HTTPS origin as a SPA redirect URI after deployment. The API verifies JWTs directly; it does not trust Easy Auth headers from an unverified ingress.
- Actual Azure OpenAI resource endpoint, supported API version and vision deployment. Grant the app managed identity the appropriate inference role on that existing resource. Model access is not created by these templates.
- Locally generated distinct strong database admin/app passwords and demo signing secret (32+ characters). Store temporary parameter files only under ignored .local and remove them after transferring secrets securely. Never commit secrets or log parameter objects.

## Provision foundation once

Review infra/foundation.bicep. It creates ACR Basic; Blob with public access/shared keys disabled; PostgreSQL Flexible Server (17, B1ms, 32 GiB, 7-day backup, no HA); delegated subnets/private DNS; Container Apps environment; app/migration identities; Key Vault secrets and scoped role assignments; Log Analytics with 1 GiB/day cap; monthly budget alerts at 80% actual and 100% forecast.

Copy infra/foundation.parameters.example.json into .local/foundation.parameters.json. Replace every placeholder, including budget amount and a valid first-of-month UTC start date. Add secure parameters databaseAdminPassword, databaseAppPassword and demoSigningSecret only to that ignored local file, or use approved Key Vault parameter references. The prefix is 3–11 lowercase alphanumeric characters.

```powershell
az account set --subscription YOUR_AUTHORIZED_SUBSCRIPTION
az deployment group what-if --resource-group YOUR_AUTHORIZED_GROUP --template-file infra/foundation.bicep --parameters '@.local/foundation.parameters.json'
# Execute only after explicit resource/spending authorization:
az deployment group create --resource-group YOUR_AUTHORIZED_GROUP --name pack-foundation --template-file infra/foundation.bicep --parameters '@.local/foundation.parameters.json'
```

Budget alerts do not stop spending. Review charge categories: warm worker/web CPU-memory, PostgreSQL compute/storage/backup, ACR, Blob transactions/capacity, logs, model tokens and network egress. No monthly price is estimated without the actual region/usage/pricing. Daily app submissions default to 100 per organization; optional demo is capped at 25 new sessions/day, 2 submissions/session/day and 10 uploads/session. These logical limits are not a guaranteed monetary cap.

## Build and release application

Copy infra/application.parameters.example.json to ignored .local/application.parameters.json and set actual Entra values, location/prefix and model configuration if available. Keep demoEnabled=false until session isolation, expiry and cost controls are verified in cloud. Public demo uploads/catalogue/orders are session-owned; no real customer catalogue is exposed. The demo has no supervisor role.

```powershell
./scripts/deploy.ps1 -Subscription YOUR_SUBSCRIPTION -ResourceGroup YOUR_GROUP -ApplicationParameters .local/application.parameters.json -Registry YOUR_ACR_NAME -Prefix YOUR_PREFIX -ImageTag TESTED_COMMIT_SHA
```

This builds a commit-tagged image in ACR, deploys web/worker/migration definitions, runs the separate migration job, waits for success and checks readiness. PostgreSQL has no public endpoint; migrations run inside the Container Apps network. The migration identity can read the admin connection/app password; the app identity can only read its connection/demo signing secret. Confirm RBAC propagation before retrying a failed deployment. Never run competing migrations from replicas.

The first release may show unready web/worker replicas until migration finishes. Subsequent migrations must remain backward-compatible because application deployment precedes job execution in this baseline release script. For a breaking schema change, stage migration and traffic changes separately. No destructive automatic down migration is provided.

GitHub workflow deploy.yml uses OIDC and a protected azure-production environment. Configure AZURE_CLIENT_ID, AZURE_TENANT_ID, AZURE_SUBSCRIPTION_ID, AZURE_RESOURCE_GROUP, AZURE_REGISTRY, AZURE_PREFIX and APPLICATION_PARAMETERS_JSON as environment variables. No long-lived Azure credential is required by the workflow. Dispatch only a tested commit SHA during the authorized build window. No workflow has run on GitHub yet.

## Verify after release

1. Check readiness and liveness independently; neither spends model tokens.
2. Sign in as operator and supervisor; verify forbidden review and cross-tenant guessed image access.
3. Create real authorized order/photo evidence; run one actual inference on a fresh non-held-out capability-test unit. If unsupported API parameters/JSON/images fail, retain pending and fix configuration before using another authorized unit. Do not repeat the same unit.
4. Export and inspect checks, original observation, order/catalogue snapshots and model/usage provenance.
5. Restart/revise worker and verify reserved calls never replay. Switch off the laptop and repeat the cloud workflow on a new real unit from another client.
6. If enabling anonymous demo, test two independent browsers cannot access each other's records/photos, enforce quotas, expire uploads through the running worker and verify cookies are Secure/HttpOnly/SameSite.
7. Record actual URL/results in README and TEST_REPORT only after successful verification. A readiness response alone is not a passed end-to-end model test.

## Rollback and teardown

Keep prior tested image tags/revisions. Redeploy the prior image or activate its revision after confirming database compatibility; never destructively downgrade data as part of ordinary rollback. A lease recovers interrupted work while reservations prevent additional inference calls.

Teardown is intentionally manual: export required evidence, identify the exact authorized resource group and review retained backup/Key Vault policies, then explicitly approve deleting that scope. No teardown script executes automatically. Local Compose volumes likewise should not be removed without deciding whether to retain evidence.

Current verification gaps: cloud provisioning, network reachability, identity grants, model capability, hosted sign-in, demo expiry in Azure and GitHub OIDC. Docker image build/execution passed in GitHub CI on 29 September. Docker Desktop's local engine error is documented in TEST_REPORT.md. Azure CLI 2.90.0 is available in the ignored local tools directory; Azure sign-in and an authorized subscription/scope/budget are still required.
