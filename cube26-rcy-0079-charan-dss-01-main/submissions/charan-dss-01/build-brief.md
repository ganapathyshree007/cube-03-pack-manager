# Build Brief · Recovery Manager

## Problem Statement & Context
Marketplace channels (e.g., Amazon FBA) regularly assess deductions against sellers: inbound defect fees, lost inbound shipments, customer refunds where items were allegedly not returned, and shipping weight tier adjustments. Sellers lack the cross-system evidence infrastructure to challenge these deductions defensibly, resulting in either uncontested margin loss or reckless claims filed by contingent agencies that jeopardize seller account standing.

Recovery Manager sits at **Step 5 of 5: Money Back** in the Commerce Context stream. Unlike the first four managers (Receiving, Prep, Pack, Returns), Recovery Manager has no camera. It ingests the structured operational records created by the other four managers, matches each financial fee against physical unit history, and determines whether the evidence **contradicts**, **supports**, or is **silent/uncertain** regarding the deduction.

---

## High-Level Architecture

```text
┌────────────────────────────────────────────────────────┐
│             Enterprise Next.js Frontend                │
│  - Multi-tenant workspace selector (Alpha / Bravo)     │
│  - Operations Dashboard with real DB metrics           │
│  - Interactive Evidence Graph & Chronological Timeline │
│  - "Why Not Claim?" Conservative Audit Drawer          │
│  - Frozen Claim Package Generator with JSON/PDF export │
└───────────────────────────┬────────────────────────────┘
                            │ REST JSON API
┌───────────────────────────▼────────────────────────────┐
│                    FastAPI Backend                     │
│  - Tenant-isolated SQLAlchemy Models & Postgres RLS    │
│  - Hybrid RAG Engine (Multi-Hop + Cosine Embeddings)   │
│  - Deterministic Rule Engine & Conservative Agent      │
│  - Cloudinary & Local Storage Integration Pipeline     │
└───────────────────────────┬────────────────────────────┘
                            │
┌───────────────────────────▼────────────────────────────┐
│         Relational & Vector Storage Layer              │
│  - PostgreSQL + pgvector (with zero-dep SQLite fallback│
│  - Companies, Charges, EvidenceRecords, Chunks, Claims │
└────────────────────────────────────────────────────────┘
```

---

## Data Flow & Multi-Hop Traversal

```text
FINANCIAL CHARGE
  │
  ├── 1. Exact Key Extraction (unit_id, shipment_id, order_id, sku)
  │
  ├── 2. Tenancy Gate (company_id match enforcement)
  │
  ├── 3. Multi-Hop Upstream Traversal
  │      Charge ──▶ Unit ──▶ Shipment ──▶ Prep Record (polybag, barcode, label)
  │      Charge ──▶ Order ──▶ Pack Record (carton seal, order line match)
  │      Charge ──▶ Returns Desk (physical condition, disposition)
  │      Charge ──▶ Receiving (supplier PO, cartons count, unit damage)
  │
  ├── 4. Relevance & Establishment Evaluation
  │      What does this specific record prove?
  │      What does it NOT prove?
  │
  ├── 5. Conservative Agent Decision Matrix
  │      - Duplicate fee? ──▶ DUPLICATE ($0 claim)
  │      - Offsetting reimbursement? ──▶ ALREADY_REIMBURSED ($0 claim)
  │      - No direct operational records? ──▶ SILENT ($0 claim)
  │      - Inconclusive / conflicting logs? ──▶ UNCERTAIN ($0 claim)
  │      - Upstream records confirm defect? ──▶ SUPPORTED ($0 claim)
  │      - Upstream records refute defect? ──▶ CONTRADICTED (Claim fee amount)
  │
  └── 6. Claim Package Assembly
         Frozen audit trail, legal defense statement, and evidence citations
```
