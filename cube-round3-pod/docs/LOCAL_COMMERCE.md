# Local commerce continuation — 6 October 2026

The customer portal supports catalogue browsing, transactional stock reservations, order requests without payment, owned history and eligible return requests. Operations supports immutable policies, product configuration, inbound receipts, policy holds/review, evidence review, delivery confirmation and persisted-data analytics.

## Start locally

Install requirements.txt and requirements.lock in the Python 3.12 virtual environment. Run `npm --prefix frontend ci` and `npm --prefix frontend run build`. Keep DATABASE_URL (restricted role), MIGRATION_DATABASE_URL (owner) and STORAGE_ROOT in ignored .env. Apply migrations using `.venv/Scripts/python.exe -m alembic upgrade head`. Preserve existing data.

```powershell
./scripts/start-operations-offline.ps1 -Port 8014 -PostgresBin C:\SYDON\cube-03-pack-manager\.local\tools\pgsql\bin -PostgresData C:\SYDON\cube-03-pack-manager\.local\pgdata
```

The explicit paths reuse this machine's existing database. No reset occurs. Add `-CheckOnly` to check prerequisites. The launcher forces model provider none and runs the local worker. Restart after backend changes; rebuild after frontend changes.

Open `/operations.html` using `.local/integrated-client.json` or `/shop.html` using `.local/customer-client.json`. Create a customer account with `scripts/create_local_customer.py`. Select the account file on the login screen. Account files are credentials; do not share or commit them.

## Routing and usage

Configure products and publish a versioned policy in Commerce setup. Record actual inbound receipt provenance before selling inventory. Customer checkout reserves this stock and never invents a Receiving inspection. Standard FBA selects Prep; merchant/3PL selects Pack. Specialist FBA is held as unsupported. Unknown categories or Pod assignment hold work. After verifying the actual assignment, update pod-assignment.json and use version-checked policy review on unstarted held orders.

Delivery requires completed passing fulfillment evidence and a source. Customer returns require an owned delivered purchase within the configured window, with quantities bounded by prior requests. Recovery needs an actual charge event AND admissible completed evidence; no claim is automatically submitted. This Recovery condition follows the latest user instruction and differs from the starter flow, requiring team review before submission.

## Database and API

Migration 003 adds pod_workflows, pod_evidence and pod_outputs. Migration 004 adds commerce_inventory, commerce_orders, commerce_returns, commerce_events and commerce_policies. Existing catalogue and cw_* operational records are reused. These are tables in one PostgreSQL database, not separate databases for five managers.

API prefix: `/operations-api/v1`. Writes require Idempotency-Key; versioned edits require expected_version. Request contracts are available at `/operations-api/openapi.json`.

| Access | Routes under the API prefix | Purpose |
|---|---|---|
| Customer | commerce/session, commerce/catalogue, commerce/orders, commerce/returns | Safe identity, catalogue and owned history |
| Customer | POST commerce/orders and commerce/orders/{id}/returns | Atomic order and return |
| Supervisor | commerce/admin/policies, commerce/admin/products/{id}, commerce/admin/inventory/{id}/receipts | Policy, product and receipt configuration |
| Operations | commerce/admin/orders | Linked workflows |
| Supervisor | commerce/admin/orders/{id}/delivered | Delivery confirmation |
| Supervisor | commerce/admin/workflows/{id}/policy-review and /recovery-events | Audited transitions |
| Supervisor | commerce/admin/analytics | Date/product/category/route/status/stage filters |
| Operations | pod/workflows and pod/workflows/{id} | Official workflow and evidence |
| Supervisor | pod/catalogue/{id}/reference and pod/workflows/{id}/resume | Reference binding and explicit resume |

Strict request bodies and role gates protect these routes. Official envelopes use organiser output schemas. Commerce projections are tested but not all declare separate Pydantic response models. Analytics excludes fixtures by default, measures only recorded durations and leaves unsupported damaged dispositions unavailable rather than inferring them from reasons.

## Explicit limits

Pod assignment/shared fork remain unresolved. Automatic Receiving/Prep/Returns are incomplete; Pack is experimental and disabled. Original CLI agents remain labelled sample stubs. The main tracker reads operational cw_* records; a complete official-evidence browser is not yet integrated. No live recognition, held-out accuracy, public deployment or physical-phone camera verification is claimed. Payments, carrier integration, automatic cancellation stock release and return restocking are not implemented. Never reuse keys disclosed in chat.
