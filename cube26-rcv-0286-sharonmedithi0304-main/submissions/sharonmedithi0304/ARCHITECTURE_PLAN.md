# CUBE Buildathon Receiving Manager (01 · RCV) — Target Architecture Plan

## Executive Summary

This document specifies the target architecture for the **CUBE Receiving Manager (01 · RCV)** for Round 3 pod integration. The system verifies received inventory against purchase-order (PO) specifications, performs visual observation via a multimodal Vision-Language Model (VLM), executes 10 deterministic receiving checks, detects evidence contradictions (C1–C6), builds an evidence-backed trace (`PASS` / `FAIL` / `UNCERTAIN`), and exposes standardized integration interfaces for downstream pod managers (**Prep `0310`**, **Pack `03`**, **Returns `0073`**, and **Recovery `0079`**).

**Core Principle:** The deterministic decision engine ([`agent/inspection_agent.py`](file:///c:/Users/shaa0/Downloads/sharonmedithi0304-final/submissions/sharonmedithi0304/agent/inspection_agent.py)) and post-inspection review layer ([`agent/review_layer.py`](file:///c:/Users/shaa0/Downloads/sharonmedithi0304-final/submissions/sharonmedithi0304/agent/review_layer.py)) are **100% preserved**. The AI model observes; code decides.

---

## 1. Exact Target Folder Structure

```text
submissions/sharonmedithi0304/
├── README.md                      ← Primary project documentation & quickstart
├── ARCHITECTURE.md                ← Current architectural documentation
├── ARCHITECTURE_PLAN.md           ← Target architecture specification (this file)
├── eval-report.md                 ← Software test results & vision evaluation methodology
├── requirements.txt               ← Extended dependencies (fastapi, uvicorn, sqlalchemy, pydantic, etc.)
│
├── contract/
│   ├── evidence-record.json       ← Reconciled 10-check standard contract schema
│   └── inter_manager_envelope.json← Common pod integration envelope schema
│
├── agent/                         ← Preserved Deterministic Core (NO RE-IMPLEMENTATION)
│   ├── inspection_agent.py        ← Deterministic 10-check decision engine (PRESERVED)
│   ├── review_layer.py            ← Contradictions C1-C6, priority queue, overrides (PRESERVED)
│   ├── vision_adapter.py          ← One-call-per-unit boundary & validation (PRESERVED & EXPANDED)
│   ├── model_client.py            ← VLM Provider Interface & Clients (EXPANDED)
│   ├── test_agent.py              ← Manual test script
│   ├── test_model_client.py       ← Model client unit tests
│   ├── test_review_layer.py       ← Review layer unit tests
│   ├── test_vision_adapter.py     ← Vision adapter unit tests
│   └── fixtures/                  ← Test image fixtures
│
├── api/                           ├── NEW: Web API Layer (FastAPI)
│   ├── __init__.py
│   ├── main.py                    ← FastAPI application entrypoint & middleware
│   ├── routes_receiving.py        ← Endpoints: /inspect, /records, /overrides, /queue
│   ├── routes_integration.py      ← Endpoints: /export/prep, /export/returns, etc.
│   └── schemas.py                 ← Pydantic v2 request/response DTOs
│
├── db/                            ├── NEW: Persistence Layer
│   ├── __init__.py
│   ├── session.py                 ← SQLAlchemy 2.0 async engine & session maker
│   ├── models.py                  ← Database tables (Tenants, Units, Checks, Overrides)
│   └── repository.py              ← CRUD database operations & audit trail persistence
│
├── storage/                       ├── NEW: Object Storage / Image Management
│   ├── __init__.py
│   └── image_store.py             ← Local static file / S3 image loader & static server
│
├── ui/                            ├── Streamlit Operator Workstation UI
│   └── app.py                     ← Refactored UI consuming FastAPI / DB layer
│
└── tests/                         ├── NEW: Integration & API Test Suite
    ├── test_api_receiving.py      ← REST API integration tests
    ├── test_db_persistence.py     ← Database model & repository tests
    └── test_pod_contracts.py      ← Downstream envelope serialization tests
```

---

## 2. Technology Choices

| Component | Selected Technology | Justification |
|---|---|---|
| **Web API Framework** | **FastAPI** (Python 3.11+) | Async IO performance, automatic OpenAPI documentation, strict Pydantic validation, native integration with existing Python agent code. |
| **Data Validation** | **Pydantic v2** | High-performance JSON schema enforcement, strict type validation, seamless OpenAPI integration. |
| **Database ORM** | **SQLAlchemy 2.0 (Async)** + **SQLite / PostgreSQL** | Zero-config SQLite for local hackathon runs; seamless migration to PostgreSQL for production multi-tenant environments. |
| **Database Driver** | **aiosqlite** / **asyncpg** | Non-blocking database transactions under async FastAPI handlers. |
| **AI / VLM Provider** | **Gemini 2.5 Flash** / **OpenAI GPT-4o** | State-of-the-art multimodal vision capability, structured JSON output mode, sub-second latency, precise 2D bounding box extraction. |
| **Object Storage** | **FastAPI StaticFiles / S3-compatible** | Local image static file serving with URL generation (`photo_refs`). |
| **Operator Workstation** | **Streamlit** (Refactored) | Rapid operator UI development, rich dataframes, native session management, enhanced with custom CSS and bounding box overlays. |
| **Testing Framework** | **pytest** + **unittest** | Native execution of existing 52 `unittest` cases alongside new async API integration tests. |

---

## 3. Database Entities & Schemas

The database layer enforces **tenant isolation** via `tenant_id` on all tables and records append-only operator overrides.

```sql
-- 1. Tenants / Organizations
CREATE TABLE tenants (
    tenant_id VARCHAR(64) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 2. Receiving Units (Ingested PO & Received Physical State)
CREATE TABLE receiving_units (
    unit_id VARCHAR(64) PRIMARY KEY,
    record_id VARCHAR(64) NOT NULL UNIQUE,
    tenant_id VARCHAR(64) NOT NULL REFERENCES tenants(tenant_id),
    po_number VARCHAR(64) NOT NULL,
    po_line VARCHAR(32) NOT NULL,
    supplier VARCHAR(255) NOT NULL,
    sku VARCHAR(64) NOT NULL,
    asin VARCHAR(64),
    product_title VARCHAR(255) NOT NULL,
    
    -- Expected PO Specifications
    spec_colour VARCHAR(64),
    spec_variant VARCHAR(64),
    spec_components JSONB, -- Array of strings e.g. ["bottle", "cap"]
    cartons_ordered INTEGER NOT NULL,
    units_per_carton_ordered INTEGER NOT NULL,
    qty_ordered INTEGER NOT NULL,
    
    -- Received Physical Inputs
    cartons_received INTEGER,
    units_per_carton_counted INTEGER,
    qty_received INTEGER,
    identity_match VARCHAR(32), -- 'yes', 'no', 'uncertain'
    carton_damage VARCHAR(32),  -- 'none', 'crushing', 'water', 'tears'
    unit_damage VARCHAR(32),    -- 'none', 'crushing', 'water', 'tears'
    quality_flags TEXT,         -- Semicolon-delimited e.g. 'wrong_colour;missing_components'
    photo_refs JSONB NOT NULL,  -- Array of image URLs e.g. ["/images/rcv_001.jpg"]
    
    operator_id VARCHAR(64) NOT NULL,
    captured_at TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 3. Inspection Records (Engine Execution Results)
CREATE TABLE inspection_records (
    inspection_id VARCHAR(64) PRIMARY KEY,
    record_id VARCHAR(64) NOT NULL REFERENCES receiving_units(record_id),
    tenant_id VARCHAR(64) NOT NULL REFERENCES tenants(tenant_id),
    status VARCHAR(32) NOT NULL, -- 'complete', 'pending'
    overall_verdict VARCHAR(32) NOT NULL, -- 'PASS', 'FAIL', 'UNCERTAIN'
    engine_verdict VARCHAR(32) NOT NULL,
    findings JSONB NOT NULL,
    decision_trace JSONB NOT NULL,
    model_observations JSONB, -- Raw validated VLM observations
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 4. Check Results (Granular 10 Checks)
CREATE TABLE check_results (
    check_id VARCHAR(64) PRIMARY KEY,
    inspection_id VARCHAR(64) NOT NULL REFERENCES inspection_records(inspection_id),
    check_name VARCHAR(64) NOT NULL, -- 'identity', 'quantity', 'carton_damage', etc.
    verdict VARCHAR(32) NOT NULL,    -- 'PASS', 'FAIL', 'UNCERTAIN'
    expected_value JSONB,
    observed_value JSONB,
    evidence JSONB NOT NULL,         -- Array of evidence strings
    evidence_items JSONB,            -- Array of structured evidence objects with bounding boxes
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 5. Operator Overrides (Append-Only Audit Log)
CREATE TABLE operator_overrides (
    override_id VARCHAR(64) PRIMARY KEY,
    record_id VARCHAR(64) NOT NULL REFERENCES receiving_units(record_id),
    tenant_id VARCHAR(64) NOT NULL REFERENCES tenants(tenant_id),
    original_verdict VARCHAR(32) NOT NULL, -- Verdict before override ('PASS', 'FAIL', 'UNCERTAIN')
    disposition VARCHAR(32) NOT NULL,      -- 'ACCEPT', 'REJECT', 'NEEDS_REVIEW'
    reason TEXT NOT NULL,
    operator_id VARCHAR(64) NOT NULL,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_receiving_units_tenant ON receiving_units(tenant_id);
CREATE INDEX idx_inspection_records_tenant ON inspection_records(tenant_id);
CREATE INDEX idx_operator_overrides_record ON operator_overrides(record_id);
```

---

## 4. REST API Specification

FastAPI exposes the following endpoints under `/api/v1/receiving`:

### `POST /api/v1/receiving/inspect`
Execute receiving inspection for a unit. Automatically invokes VLM adapter (if image references provided) and runs `inspection_agent.inspect_unit()`.

- **Headers:** `X-Tenant-ID: org_demo_alpha`
- **Request Body:**
```json
{
  "record_id": "RCV-2026-001",
  "unit_id": "UNIT-8812",
  "po_number": "PO-9001",
  "po_line": "1",
  "supplier": "Apex Logistics",
  "sku": "BLUE-BOTTLE-001",
  "product_title": "Blue Water Bottle 1L",
  "spec_colour": "blue",
  "spec_variant": "standard",
  "spec_components": ["bottle", "cap"],
  "cartons_ordered": 2,
  "units_per_carton_ordered": 12,
  "qty_ordered": 24,
  "cartons_received": 2,
  "units_per_carton_counted": 12,
  "qty_received": 24,
  "photo_refs": ["/storage/images/rcv_001_front.jpg", "/storage/images/rcv_001_label.jpg"],
  "operator_id": "op_john_doe",
  "captured_at": "2026-10-04T18:00:00Z"
}
```
- **Response (200 OK):**
Returns complete runtime output contract containing overall verdict, 10 check results, findings, decision trace, and attention queue priority score.

### `GET /api/v1/receiving/records/{record_id}`
Retrieve stored inspection result, audit timeline, evidence trace, and override history for a unit.

### `POST /api/v1/receiving/overrides`
Record an append-only operator override.
- **Request Body:**
```json
{
  "record_id": "RCV-2026-001",
  "original_verdict": "UNCERTAIN",
  "disposition": "ACCEPT",
  "reason": "Visual inspection by operator confirms correct blue colour and all components present.",
  "operator_id": "op_senior_supervisor",
  "timestamp": "2026-10-04T18:15:00Z"
}
```

### `GET /api/v1/receiving/queue`
Retrieve the prioritized attention queue sorted by risk score:  
`Priority = 10 * FAIL + 6 * Conflicts + 2 * UNCERTAIN + 20 * Identity_FAIL`.

### `GET /api/v1/receiving/export/envelope/{record_id}`
Generate and return the standard Inter-Manager Common Evidence Envelope for downstream pod integration.

### `GET /health`
Liveness and readiness health probe.

---

## 5. VLM Adapter Interface & Real Model Integration

The VLM layer is isolated behind [`agent/vision_adapter.py`](file:///c:/Users/shaa0/Downloads/sharonmedithi0304-final/submissions/sharonmedithi0304/agent/vision_adapter.py) and [`agent/model_client.py`](file:///c:/Users/shaa0/Downloads/sharonmedithi0304-final/submissions/sharonmedithi0304/agent/model_client.py).

### Real Model Client Implementation (`GeminiVisionClient`)
In [`agent/model_client.py`](file:///c:/Users/shaa0/Downloads/sharonmedithi0304-final/submissions/sharonmedithi0304/agent/model_client.py), a production VLM client is added alongside `FakeModelClient`:

```python
class GeminiVisionClient:
    """Production Gemini 2.5 Flash Multimodal Vision Client."""

    def __init__(self, api_key: str, model_name: str = "gemini-2.5-flash"):
        self.api_key = api_key
        self.model_name = model_name

    def __call__(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        # 1. Load image bytes from payload["image_refs"]
        # 2. Format prompt instructions with expected PO fields
        # 3. Call Gemini API requesting Structured JSON Output matching CHECKS schema
        # 4. Return parsed JSON observations dict
        ...
```

### 1 Batched Model Call Protocol per Unit
For a single unit, `VisionInspectionAdapter.inspect_unit(unit, image_refs)` constructs **one payload** requesting observations for all 10 checks in a single inference request:

```json
{
  "instruction": "Inspect the supplied receiving images and report only what is visibly supported...",
  "expected": {
    "sku": "BLUE-BOTTLE-001",
    "colour": "blue",
    "variant": "standard",
    "components": ["bottle", "cap"],
    "cartons": 2,
    "units_per_carton": 12,
    "quantity": 24
  },
  "image_refs": ["/storage/images/rcv_001_front.jpg"],
  "required_checks": [
    "identity", "carton_count", "units_per_carton", "quantity",
    "carton_damage", "unit_damage", "colour", "variant", "components", "quality_flags"
  ]
}
```

### Strict Observation Schema & Bounding Boxes
The VLM returns **observations only** (NO PASS/FAIL decisions):
```json
{
  "observations": {
    "colour": {
      "observed_value": "blue",
      "uncertainty": false,
      "reason": "Visible bottle body is blue.",
      "evidence": [
        {
          "source_ref": "/storage/images/rcv_001_front.jpg",
          "detail": "Primary body item is blue",
          "location": { "x": 0.15, "y": 0.20, "width": 0.60, "height": 0.70 }
        }
      ]
    }
  }
}
```

### Fail-Open Enforcement
If the model call fails (timeout, network error, invalid JSON), `vision_adapter.py` catches the error and executes [`inspection_agent.pending_review()`](file:///c:/Users/shaa0/Downloads/sharonmedithi0304-final/submissions/sharonmedithi0304/agent/inspection_agent.py#L370):
- Status is set to `"pending"`.
- Overall verdict is set to `"UNCERTAIN"`.
- Unit receiving record is preserved without blocking warehouse operations.

---

## 6. Common Evidence Envelope (Pod Inter-Manager Schema)

Defined in [`contract/inter_manager_envelope.json`](file:///c:/Users/shaa0/Downloads/sharonmedithi0304-final/submissions/sharonmedithi0304/contract/inter_manager_envelope.json) for cross-pod integration:

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "CUBE Pod Inter-Manager Evidence Envelope",
  "type": "object",
  "required": [
    "envelope_id", "trace_id", "timestamp", "origin_manager",
    "tenant_id", "unit_id", "sku", "overall_verdict", "disposition", "payload"
  ],
  "properties": {
    "envelope_id": { "type": "string" },
    "trace_id": { "type": "string" },
    "timestamp": { "type": "string", "format": "date-time" },
    "origin_manager": { "type": "string", "enum": ["RCV"] },
    "tenant_id": { "type": "string" },
    "unit_id": { "type": "string" },
    "po_number": { "type": "string" },
    "sku": { "type": "string" },
    "overall_verdict": { "type": "string", "enum": ["PASS", "FAIL", "UNCERTAIN"] },
    "disposition": { "type": "string", "enum": ["ACCEPT", "REJECT", "NEEDS_REVIEW"] },
    "findings_summary": {
      "type": "array",
      "items": { "type": "string" }
    },
    "evidence_refs": {
      "type": "array",
      "items": { "type": "string" }
    },
    "payload": {
      "type": "object",
      "description": "RCV-specific full inspection trace and check details"
    }
  }
}
```

---

## 7. Data Flow Architecture

```text
[ Physical Goods Arrival & Photo Capture ]
                   │
                   ▼
  [ FastAPI: POST /api/v1/receiving/inspect ]
                   │
                   ▼ (Tenant Authorization & Image Store Validation)
     [ agent/vision_adapter.py ]
                   │
                   ├──► (1 Batched VLM Request) ──► [ Gemini 2.5 / GPT-4o ]
                   │                                         │
                   │◄── (Validated JSON Bounding Boxes) ──────┘
                   ▼
     [ agent/inspection_agent.py ]  <--- PRESERVED DETERMINISTIC ENGINE
                   │
                   ▼ (Runs 10 checks: identity, quantity, damage, colour...)
     [ agent/review_layer.py ]      <--- PRESERVED REVIEW LAYER
                   │
                   ▼ (Applies C1-C6 contradiction rules, priority score)
   [ db/repository.py (SQLAlchemy) ]
                   │
                   ├──► Stores Unit, Checks, Evidence, Trace in PostgreSQL
                   │
                   ├──► [ Streamlit Operator Workstation UI ]
                   │       └── Operator submits ACCEPT / REJECT disposition
                   │       └── Appends to operator_overrides table
                   │
                   └──► [ Inter-Manager Envelope Exporter ]
                           ├──► Prep Manager (0310)
                           ├──► Pack Manager (03)
                           ├──► Returns Manager (0073)
                           └──► Recovery Manager (0079)
```

---

## 8. Security Model & Tenant Isolation

1. **Tenant Isolation:** Every API request requires an `X-Tenant-ID` header. All SQL queries filter explicitly by `tenant_id`. Database row-level security (RLS) is enabled on PostgreSQL tables.
2. **Secret Management:** Secrets (VLM API keys, DB connection strings) are loaded exclusively via environment variables (`.env` file excluded from version control). Zero credentials exist in source code.
3. **Storage Isolation:** Image files are isolated in storage buckets partitioned by tenant: `/storage/{tenant_id}/{unit_id}/photo_01.jpg`.
4. **Input Sanitization:** Image upload paths and JSON responses are strictly validated via Pydantic v2 schemas to prevent path traversal and script injection.

---

## 9. Integration Boundaries (Downstream Manager Contracts)

### RCV Data Expose Matrix

| Downstream Pod Manager | Endpoint Used | Payload Content Provided by RCV | Downstream Action |
|---|---|---|---|
| **Prep Manager (`0310`)** | `GET /api/v1/receiving/export/prep/{unit_id}` | `unit_id`, `sku`, `product_title`, `quantity`, `quality_flags`, `components`, `disposition` | Determines if unit requires kitting, labeling, or repackaging. |
| **Pack Manager (`03`)** | `GET /api/v1/receiving/export/pack/{unit_id}` | `unit_id`, `sku`, `spec_variant`, confirmed component list, carton dimensions/damage | Prepares packing box size, cushioning, and shipping labels. |
| **Returns Manager (`0073`)** | `GET /api/v1/receiving/export/returns/{unit_id}` | `po_number`, `supplier`, `qty_ordered` vs `qty_received`, damage type, evidence image URLs, operator override reasons | Generates automated vendor RTV (Return to Vendor) claim package. |
| **Recovery Manager (`0079`)** | `GET /api/v1/receiving/export/recovery/{unit_id}` | Damaged units (`unit_damage`, `carton_damage`), quality defect findings, visual 2D bounding boxes | Routes damaged/defective items to refurbish, liquidate, or scrap queues. |

---

## 10. Preservation of `inspection_agent.py`

### Compatibility Verification & Preservation Mandate
A comprehensive audit of [`agent/inspection_agent.py`](file:///c:/Users/shaa0/Downloads/sharonmedithi0304-final/submissions/sharonmedithi0304/agent/inspection_agent.py) confirms:

- **No Incompatibilities Found:** The 10-check inspection function [`inspect_unit(unit)`](file:///c:/Users/shaa0/Downloads/sharonmedithi0304-final/submissions/sharonmedithi0304/agent/inspection_agent.py#L468) is entirely pure, stateless, and fully decoupled from UI/database layers.
- **Decision Engine Integrity:** `inspection_agent.py` accepts structured unit dictionaries (including VLM `observed_*` fields) and calculates deterministic verdicts (`PASS`, `FAIL`, `UNCERTAIN`).
- **Preservation Directive:** [`agent/inspection_agent.py`](file:///c:/Users/shaa0/Downloads/sharonmedithi0304-final/submissions/sharonmedithi0304/agent/inspection_agent.py) and [`agent/review_layer.py`](file:///c:/Users/shaa0/Downloads/sharonmedithi0304-final/submissions/sharonmedithi0304/agent/review_layer.py) **SHALL REMAIN 100% UNTOUCHED**. All new Web API, database persistence, VLM clients, and pod integration layers wrap around these core modules.
