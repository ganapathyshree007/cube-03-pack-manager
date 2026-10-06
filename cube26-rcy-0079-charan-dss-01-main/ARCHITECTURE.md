# ARCHITECTURE · RCY RECOVERY MANAGER

## Complete Architectural Blueprint

The **RCY Recovery Manager** is an evidence-grounded AI financial recovery operations center. It ingests marketplace channel fee and reimbursement reports, matches them against upstream physical operational logs (Receiving, Prep, Pack, Returns), conservatively analyzes whether evidence contradicts or supports each deduction, and produces formal, defensible claim packages.

---

## 1. System Architecture & Topology

**Production Deployments:**
- **Frontend (Vercel):** [https://cube26-rcy-0079.vercel.app/](https://cube26-rcy-0079.vercel.app/)
- **Backend (Render):** [https://rcy-recovery-backend.onrender.com/](https://rcy-recovery-backend.onrender.com/)
- **API Swagger Docs:** [https://rcy-recovery-backend.onrender.com/docs](https://rcy-recovery-backend.onrender.com/docs)

```text
┌─────────────────────────────────────────────────────────────────────────────────┐
│                          Next.js 14 Enterprise UI                               │
│  - Multi-tenant workspace switcher (org_demo_alpha, org_demo_bravo)             │
│  - Real-time Operations Dashboard (Fees, Recoverable Pipeline, Claim Precision) │
│  - Charges Explorer with search & multi-filter                                  │
│  - Interactive Evidence Graph (Charge ↔ Unit ↔ Shipment ↔ Order ↔ Evidence)     │
│  - Chronological Evidence Timeline with authentic timestamps                    │
│  - "Why Not Claim?" Conservative Audit Drawer                                   │
│  - Claim Package Builder (Frozen audit snapshot, JSON/PDF export)               │
│  - Data Ingestion & Manual Record Entry Center                                  │
└──────────────────────────────────────┬──────────────────────────────────────────┘
                                       │ REST API (JSON)
┌──────────────────────────────────────▼──────────────────────────────────────────┐
│                            FastAPI Backend Core                                 │
│  ├── Multi-Tenant Middleware & Tenant-Scoped SQLAlchemy 2.0 ORM                 │
│  ├── Ingestion Engine (CSV, XLSX, PDF, JSON normalizers with validation preview)│
│  ├── Hybrid RAG Engine (Multi-Hop Traversal + Semantic Cosine Embeddings)       │
│  ├── Conservative Recovery Agent (Deterministic Gates + Heuristic/LLM Reasoner) │
│  ├── Claim Assembly & Audit Service (Immutably freezes claim evidence packages) │
│  └── Storage Service (Cloudinary integration with tenant-isolated local fallback│
└──────────────────────────┬──────────────────────────────────────────┬───────────┘
                           │                                          │
┌──────────────────────────▼───────────────┐ ┌────────────────────────▼───────────┐
│     Relational & Vector Storage Layer    │ │          Cloudinary Storage        │
│  - PostgreSQL with pgvector              │ │  - /company/{id}/charges/          │
│    (Auto-fallback to SQLite + Cosine)    │ │  - /company/{id}/evidence/         │
│  - Complete tenant isolation (company_id)│ │  - /company/{id}/claims/           │
└──────────────────────────────────────────┘ └────────────────────────────────────┘
```

---

## 2. System Components

The platform consists of four primary modular layers:

### A. Presentation Layer (Next.js 14 App Router)
- **AppShell Architecture (`AppShell.jsx`):** Dynamically isolates the public landing page (`/`) into a full-width experience while maintaining a persistent fixed-sidebar application shell for all authenticated operations routes (`/dashboard`, `/charges`, `/recovery`, `/evidence`, `/claims`, `/data-sources`, `/investigations/[id]`).
- **Interactive Forensic Visualizers:** 
  - `EvidenceGraph.jsx`: Interactive SVG-based node-link graph mapping relational hops.
  - `EvidenceTimeline.jsx`: Chronological custody verification with operator IDs and timestamps.
  - `ClaimPackageModal.jsx`: Frozen dispute dossier preview with instant JSON export and print-to-PDF formatting.
  - `WhyNotClaimModal.jsx`: Conservative audit drawer explaining why ungrounded claims are refused.

### B. Application & API Core (FastAPI)
- **Multi-Tenant REST Router (`routes.py`):** Provides endpoints for tenant switching, fee exploration, batch investigations, evidence cataloging, and claim package generation.
- **Dynamic CORS Middleware (`main.py`):** Configured for cross-origin security across local development (`localhost:3000`) and production Vercel environments.
- **Two-Tier Ingestion Parser (`parsers.py`):** Auto-detects document types by filename keywords, falling back to DataFrame column analysis. Handles CSV, XLSX, PDF, and JSON with automated NaN sanitization and schema pre-validation.

### C. Forensic Intelligence & Reasoning Core
- **Hybrid RAG Engine (`retrieval.py`):** Couples deterministic relational entity resolution with semantic cosine embedding retrieval over chunked operational notes.
- **Conservative Recovery Agent (`recovery_agent.py`):** Governed by deterministic marketplace defect rules (prep polybag compliance, package tare scale weights, return restock scans) and zero-speculation fallback.
- **Claim Assembly Service (`claim_service.py`):** Freezes snapshot-immutable claim packages with policy citations and evidence hashes.

### D. Relational & Persistence Layer
- **SQLAlchemy 2.0 ORM (`session.py`, `models.py`):** Multi-tenant schema with company-scoped row-level security (RLS). Supports PostgreSQL with modern dynamic drivers (`psycopg` v3 + `psycopg2` fallback) and SQLite for zero-setup local execution.
- **Storage Subsystem (`storage_service.py`):** Tenant-isolated object storage partitioned by `/company/{company_id}/`.

```text
┌──────────────┐       1:N       ┌──────────────┐
│  companies   │────────────────▶│    users     │
└──────┬───────┘                 └──────────────┘
       │ 1:N
       ├─────────────────────────┐
       │ 1:N                     │ 1:N
┌──────▼───────┐          ┌──────▼──────────────┐
│   charges    │          │  evidence_records   │
└──────┬───────┘          └──────┬──────────────┘
       │ 1:1                     │ 1:N
┌──────▼───────┐          ┌──────▼──────────────┐
│investigations│          │   evidence_chunks   │
└──────┬───────┘          └─────────────────────┘
       │ 1:N
┌──────▼──────────────────┐
│ investigation_evidence  │
└─────────────────────────┘
       │ 1:1
┌──────▼───────┐
│    claims    │
└──────────────┘
```

---

## 3. End-to-End Data Flow

The Recovery Manager executes an autonomous 5-phase data pipeline:

```text
[Phase 1: Ingestion]
Fee Reports & Floor Logs (CSV/XLSX/PDF/JSON)
  │
  ▼ Two-Tier Parser (Filename -> Column Inspection -> NaN Sanitation)
Database Ingestion: charges, evidence_records, evidence_chunks (Tenant-Scoped RLS)
  │
  ▼
[Phase 2: Entity Identification & Graph Traversal]
Charge ID (e.g. CH-TC07-DUPLICATE, $15.00 Inbound Defect Fee)
  │
  ▼ [Hop 1: Key Resolution]
Unit ID: UNIT-TC07
  │
  ▼ [Hop 2: Upstream Physical Record Traversal]
Shipment ID & Order ID ──▶ Upstream Floor Logs (Prep: PRP-TC07, Receiving: RCV-TC07, Returns: RTN-TC07)
  │
  ▼ [Hop 3: Semantic Alignment & Relevance Matching]
Cosine similarity matching of defect description against operator notes
  │
  ▼
[Phase 3: Conservative Forensic Assessment]
Rule-based evaluation against authoritative channel policies:
  ├── Case A: Pre-shipment scan contradicts defect allegation? ──▶ Verdict: CONTRADICTED (100% Recoverable)
  ├── Case B: Floor logs substantiate merchant defect?         ──▶ Verdict: SUPPORTED (Skip Claim)
  ├── Case C: Insufficient physical custody proof?            ──▶ Verdict: SILENT ($0.00 Recovery)
  └── Case D: Conflicting timestamps or split custody?        ──▶ Verdict: UNCERTAIN (Human Review)
  │
  ▼
[Phase 4: "AI Prepares, Human Authorizes"]
Qualified recoverable claim displayed in Recovery Pipeline.
Operator reviews evidence graph and authorizes claim package freezing.
  │
  ▼
[Phase 5: Immutable Claim Package Assembly]
Claims table frozen: Formal Dispute Letter + Fact Comparison Table + Raw Scan Citations + JSON/PDF Export.
```

---

## 4. Model & Agent Usage

The recovery decision engine uses a dual-engine architecture combining **deterministic rule gates** with **Google Gemini LLM reasoning**:

### A. Deterministic Rule Gates (Primary & Fast)
Where channel specifications publish concrete requirements, deterministic rules take precedence:
- **Packaging & Prep Violations:** Directly evaluates boolean flags (`polybag_present_sealed == 'yes'`, `original_barcode_covered == 'yes'`, `fnsku_label_placement == 'flat'`). If pre-shipment custody confirms compliance $\to$ `CONTRADICTED`.
- **Weight Tier Adjustments:** Compares scale tare readings from pack bench against channel billed weight brackets. If pack bench recorded weight is strictly below billed tier $\to$ `CONTRADICTED` with delta refund amount.
- **Unreturned Customer Items:** Checks return line inspection timestamps. If item was received and restocked $\to$ `CONTRADICTED`.

### B. Google Gemini Reasoning Engine (Heuristic & Complex Cases)
For ambiguous descriptions, complex defect language, or cross-document narrative synthesis:
- **Model:** `gemini-2.5-flash` via Google Generative Language API.
- **Prompt Engineering:** Strict system instructions forbidding hallucination, enforcing three-state outcomes (`CONTRADICTED`, `SUPPORTED`, `SILENT`), and bounding claim dollar amounts to documented charges.
- **Fail-Open Safe Fallback:** If the Gemini API is unreachable or key is unset, the agent automatically falls back to deterministic rule synthesis without halting pipeline execution.

### C. Vector Cosine Embeddings
- Model: `text-embedding-3-small` / fast local dense projection.
- Purpose: Computes similarity embeddings over `evidence_chunks` to bridge vocabulary gaps (e.g. mapping "scuffed polywrap" to "packaging abrasion defect").

---

## 5. Important Engineering Decisions

| # | Decision | Rationale & Trade-off |
|---|---|---|
| **D1** | **Record-First Architecture over Computer Vision** | Building vision models requiring live warehouse cameras is brittle, expensive, and difficult to deploy across 3PL facilities. Focusing on structured scanner logs, scale weights, and barcode custody timestamps delivers 10x faster adoption with 100% audit defensibility. |
| **D2** | **Conservative Defensibility over Dispute Volume** | Aggressive scrapers submit hundreds of speculative claims, resulting in 60%+ rejection rates and marketplace suspension warnings. Our three-state engine treats `SILENT` ($0.00 recovery) as a first-class outcome, ensuring 100% precision on filed claims. |
| **D3** | **Multi-Hop Relational Traversal over Pure Vector RAG** | Standard naive RAG performs similarity searches on text chunks, frequently creating hallucinated associations across different shipments. Relational multi-hop traversal deterministically enforces that a unit strictly matches its parent shipment, order, and custody timestamps. |
| **D4** | **"AI Prepares, Human Authorizes" (HITL)** | Submitting financial disputes is a legally binding merchant action. The agent autonomously does 99% of the investigative heavy lifting, but requires deliberate operator confirmation to freeze claim dossiers. |
| **D5** | **Multi-Tenant Row-Level Security (RLS)** | Tenancy isolation is enforced at the database query level (`company_id`). Verified via automated tests (`test_tenant_isolation`) that `org_demo_alpha` can never observe or query `org_demo_bravo` records. |
| **D6** | **Dual PostgreSQL Driver Support (Psycopg 3 & 2)** | To ensure seamless cloud portability across Render, Neon, Supabase, and local SQLite, `session.py` dynamically detects and routes between `psycopg` (v3) and `psycopg2` without driver conflicts. |

