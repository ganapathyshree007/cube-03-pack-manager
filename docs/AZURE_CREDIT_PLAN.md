# India-only deployment and 30-day credit plan

Checked 30 September 2026. Participant authorization: use the existing Azure for Students $100 credit, keep deployment in India, and preserve service for at least 30 days (through 30 October 2026). Do not upgrade to paid billing or remove the spending limit.

## Confirmed subscription blocker

Read-only Azure checks found the subscription enabled with spendingLimit On and an enforced `sys.regionrestriction` policy. The policy denies resources outside Indonesia Central, India South Central, Malaysia West, Korea Central and East Asia, except global resources and the policy's B2C-directory exception.

India South Central (`indiasouthcentral`) is the only allowed India region. It is distinct from South India (`southindia`). Container Apps managed-environment locations did not include India South Central. Cognitive Services model and quota queries for India South Central returned NoRegisteredProviderFound and supported-location lists excluding that region. PostgreSQL lists India South Central, but deploying the database alone would not unblock the app/model.

Central India is listed for the required application services but is denied by this subscription's current policy. Model catalogue entries are not proof of student-subscription inference eligibility or granted deployment quota.

No paid resources have been created. No policy, spending limit or billing offer has been changed. Do not provision a partial stack while the regional/model access blocker remains.

## Proposed allocation, not a price quote or applied limit

| Purpose | Maximum planning allocation for 30 days |
|---|---:|
| Application, database, private storage, registry and logs | $50 |
| Vision inference | $20 |
| Deployment/testing and miscellaneous usage | $10 |
| Untouched reserve | $20 |

Target consumption is at most $80 over 30 days, leaving $20 headroom. This allocation is not yet a validated forecast. The real remaining balance and credit expiration must also be checked in the Azure Sponsorships portal. A nominal $100 starting credit does not prove $100 remains or that it will remain valid through 30 October.

Before provisioning, select an eligible India regional vision deployment and obtain its actual token rates and quota. Global Standard processing can occur outside India; it must not be treated as India-only processing. Measure a separate genuine capability-test unit, then derive a conservative global daily inference cap from the worst permitted input/output size, not just average calls. Keep one call per unit and zero automatic inference retries.

The current templates are a baseline, not the approved credit profile: both web and worker request 0.5 vCPU/1 GiB, the worker stays on, logs allow 1 GiB/day, and the default 100 submissions/day is per organization rather than a global monetary cap. These must be resized/capped and the final estimate rechecked before deployment. Keep anonymous demo disabled initially. Consider web scale-to-zero, smaller tested replicas, capped logs and an application-wide reservation budget that stops new inference before the model allocation is exhausted.

Azure budget alerts do not stop spending. A monthly budget also resets during this 30-day period. Preserve the student spending limit; exhausting the credit can still disable the service before 30 days, so credit protection alone is not an uptime guarantee. Do not claim 30-day availability until access, pricing, remaining credit, expiry and enforced usage limits are verified.

## Next required external step

Ask Azure subscription support whether Central India or South India can be enabled for this student subscription, with Container Apps and an eligible regional vision model. Confirm student-credit eligibility and quota for inference. Approval is not guaranteed. Do not switch to an overseas region or paid subscription without participant authorization.

If the student offer cannot support an India deployment, a buildathon-provided or institution-provided India-enabled subscription/model endpoint is an alternative to investigate. It is not currently available or assumed.

Sources: [Azure student credit and expiry](https://learn.microsoft.com/en-us/azure/cost-management-billing/manage/azurestudents-subscription-disabled), [Foundry deployment regional processing](https://learn.microsoft.com/en-us/azure/foundry/foundry-models/concepts/models-sold-directly-by-azure-region-availability?pivots=standard), [Container Apps billing](https://learn.microsoft.com/en-us/azure/container-apps/billing). Subscription policy and service availability findings came from authenticated read-only Azure CLI queries.
