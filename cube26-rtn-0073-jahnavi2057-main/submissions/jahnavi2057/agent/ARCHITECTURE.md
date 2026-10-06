# Architecture — Returns Manager AI Agent

---

## System Architecture

The Returns Manager is a full-stack web application with a Node.js/Express backend and a React (Vite) frontend. It follows a classic client-server architecture with a service layer for AI and business logic.

`
+------------------------------------------------------------+
¦                      React Frontend                        ¦
¦  Dashboard ¦ Analytics ¦ Inspection View ¦ Human Override  ¦
+------------------------------------------------------------+
                          ¦ HTTP (REST)
                          ¦ x-tenant-id header
+-------------------------?----------------------------------+
¦               Express.js API Server (:3001)                ¦
¦                                                            ¦
¦  +-------------+  +--------------+  +-------------------+ ¦
¦  ¦  Tenant     ¦  ¦  Returns     ¦  ¦  Inspection       ¦ ¦
¦  ¦  Middleware ¦  ¦  Router      ¦  ¦  Router           ¦ ¦
¦  +-------------+  +--------------+  +-------------------+ ¦
¦                                             ¦              ¦
¦  +------------------------------------------?------------+ ¦
¦  ¦              Service Layer                            ¦ ¦
¦  ¦  +--------------------+  +------------------------+  ¦ ¦
¦  ¦  ¦  vision.js         ¦  ¦  disposition.js        ¦  ¦ ¦
¦  ¦  ¦  (AI Inspection)   ¦  ¦  (Rules Engine)        ¦  ¦ ¦
¦  ¦  +--------------------+  +------------------------+  ¦ ¦
¦  +-------------+-----------------------------------------+ ¦
¦                ¦                                            ¦
+----------------+--------------------------------------------+
                 ¦ HTTPS (Gemini API)
+----------------?---------------+
¦   Google Gemini 2.5 Flash      ¦
¦   (generativelanguage API)     ¦
+--------------------------------+
`

---

## Components

### Frontend (`client/`)

| File | Role |
|------|------|
| `src/App.jsx` | Entire application: routing, all page components, API calls, state |
| `src/index.css` | Global dark-forest-green design system with CSS variables |

**Key UI Sections:**
- **Sidebar** — Navigation between Dashboard, Analytics, and Inspection pages; Tenant switcher
- **Dashboard Page** — Stats cards + returns table with inline status/disposition badges
- **Analytics Page** — Bar chart (dispositions) + Donut chart (statuses) rendered with pure CSS/SVG
- **Inspection Page** — Full record detail, image gallery, AI verdict cards with confidence bars, human override panel
- **AI Mode Badge** — Polls `/api/status` on load; shows green AI LIVE or red MOCK MODE

### Backend (`server/`)

| File | Role |
|------|------|
| `server/index.js` | Express app bootstrap, CORS, static file serving, port binding |
| `server/api.js` | All REST routes: `/returns`, `/returns/inspect`, `/returns/:id/override`, `/reload`, `/status` |
| `server/db.js` | In-memory data store; seeds from CSV on startup; handles tenant isolation |
| `server/middleware/tenant.js` | Extracts and validates `x-tenant-id` header on all protected routes |
| `server/services/vision.js` | Core AI service: image fetching, Gemini API call, retry logic, mock fallback |
| `server/services/disposition.js` | Deterministic rules engine: maps AI verdicts ? disposition outcomes |
| `server/data/catalogue.json` | Static product catalogue with SKU, name, expected parts, description |
| `server/data/return-images.json` | Maps record IDs to evidence image URLs |

---

## Data Flow

### Inspection Flow (Happy Path)

`
User clicks "Run AI Inspection"
         ¦
         ?
POST /api/returns/inspect
  { record_id, subject, sku, images[] }
         ¦
         ?
Tenant Middleware validates x-tenant-id
         ¦
         ?
db.getCatalogueItem(sku)
  ? product context (name, expected_parts, description)
         ¦
         ?
vision.runVisionInspection(images, catalogueItem)
  1. Fetch each image URL ? base64 inline data
  2. Build structured prompt with product context
  3. POST to Gemini 2.5 Flash (with retry on overload)
  4. Parse JSON array response ? checks[]
         ¦
         ?
disposition.determineDisposition(checks)
  ? "restock" | "refurbish" | "liquidate" | "dispose" | "pending_review"
         ¦
         ?
db.saveEvidenceRecord(tenantId, evidenceRecord)
  ? Stores with SHA-256 content hash
         ¦
         ?
Response: full evidence record ? UI updates
`

### Human Override Flow

`
Operator selects verdict + enters reason ? clicks Apply Override
         ¦
         ?
POST /api/returns/:id/override
  { revised_verdict, reason, operator_id }
         ¦
         ?
Tenant check ? record lookup
         ¦
         ?
db.saveOverride() ? appends to overrides[] array
  Original AI verdict preserved in overrides history
         ¦
         ?
record.outcome updated to revised_verdict
db.saveEvidenceRecord() ? new content hash
         ¦
         ?
Response: updated record
`

---

## Model / Agent Usage

### Model: Google Gemini 2.5 Flash

**Why Gemini 2.5 Flash?**
- Natively supports multimodal input (text + images in a single request)
- Fast inference latency suitable for interactive UI use (~5-10s per inspection)
- Available on the Generative Language API v1beta endpoint
- Capable of structured JSON output without function calling

**Prompt Design:**

The prompt is structured with three distinct sections:
1. **Product context** — SKU, product name, expected parts list, description from catalogue
2. **Numbered instructions** — Three checks (identity, completeness, condition) with explicit verdict options
3. **Output schema** — A JSON array template the model must follow

The model is instructed to:
- Use strictly `PASS`, `FAIL`, or `UNCERTAIN` for verdicts
- Express confidence as a decimal `0.0–1.0`
- Include the Amazon standard condition scale in the condition detail field
- Return only valid JSON — no surrounding prose

**Retry Logic:**

`callGeminiWithRetry()` in `vision.js` implements exponential backoff:
- Attempt 1: immediate
- Attempt 2: 1.5s delay
- Attempt 3: 3s delay
- Retries on 429 (rate limit), 503 (overload), and `RESOURCE_EXHAUSTED` errors

**Mock Fallback:**

When no `GEMINI_API_KEY` is set, `getMockResponse()` returns seeded, product-context-aware mock verdicts. The seed is derived from the product name (deterministic, consistent across page refreshes) with three scenario variants: clean return, damaged return, wrong item.

---

## Important Engineering Decisions

### 1. Deterministic Disposition Engine (not AI-generated)

The final disposition outcome (restock/refurbish/liquidate/dispose) is computed by a rules engine, **not** the AI. The AI produces structured check verdicts; the rules engine maps them to outcomes.

**Why?** This makes the disposition predictable, auditable, and easily adjustable by product managers without touching the AI prompt. It also prevents hallucinated outcomes — the AI cannot invent a new outcome.

### 2. Multi-Tenant Isolation via Header Middleware

Every API call must carry an `x-tenant-id` header. The middleware enforces this before any data access. The in-memory `returnsDb` Map stores `org_id` on each record, and all queries filter by it.

**Why?** This demonstrates the security model required for a SaaS returns platform without the complexity of a full auth system. The contract is explicit and testable.

### 3. Image Fetching Server-Side (not Client-Side)

Images are fetched and converted to base64 on the server before being sent to Gemini, rather than passing raw URLs to the model.

**Why?** Many product image URLs (Google Shopping, Amazon) implement hotlink protection and block requests from non-browser origins. Fetching server-side with a `User-Agent: Mozilla/5.0` header bypasses most CDN restrictions. It also means the Gemini API never needs to fetch images itself — reducing latency and external dependency.

### 4. Content Hashing on Every Save

Every evidence record is SHA-256 hashed before being stored (`db.js`).

**Why?** This creates a tamper-evident audit trail. Any modification to a record — including overrides — generates a new hash. In a production system this hash would be stored in an immutable log.

### 5. In-Memory Database (not File or DB)

Return records are stored in a JavaScript `Map` in process memory, seeded from CSV at startup.

**Why?** This is a hackathon build; there is no infrastructure to provision. The tradeoff is that data is lost on restart, but the API contract, data model, and isolation logic are all production-ready — swapping the `Map` for a real DB is a drop-in replacement.

### 6. Mock Mode with Smart Heuristics

Rather than returning a flat 0% confidence for all fields when no API key is set, the mock engine uses the product name as a seed to deterministically pick one of three realistic scenarios (perfect return, damaged, wrong item).

**Why?** Reviewers and demos need to see the system working end-to-end without an API key. A flat mock breaks the demo experience; a seeded mock makes it look credible and complete.

### 7. CSS Variables Design System

All colours, radii, and spacing are defined as CSS custom properties in `index.css`, not inline or via a utility framework.

**Why?** This makes the dark forest-green theme fully consistent and easy to retheme in a single file. It also avoids Tailwind's purge complexity and keeps the bundle small.
