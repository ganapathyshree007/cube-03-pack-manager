# AgentPrep — Visual Prep Compliance Agent

> **Cube Buildathon Round 2 — Prep Manager Track**  
> *Autonomous multi-agent system verifying e-commerce inbound product prep compliance against strict fulfillment rules.*

[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688.svg?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Next.js](https://img.shields.io/badge/Next.js-14-black.svg?logo=next.js&logoColor=white)](https://nextjs.org)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.0+-3178C6.svg?logo=typescript&logoColor=white)](https://www.typescriptlang.org)
[![SQLite](https://img.shields.io/badge/SQLite-3-003B57.svg?logo=sqlite&logoColor=white)](https://sqlite.org)
[![Tests](https://img.shields.io/badge/Tests-15%20Passed-emerald.svg)](backend/test_agentprep.py)
[![Netlify Status](https://img.shields.io/badge/Netlify-Live%20Demo-00A09D.svg?logo=netlify&logoColor=white)](https://agentprep.netlify.app)
[![YouTube Demo](https://img.shields.io/badge/YouTube-Video%20Demo-FF0000.svg?logo=youtube&logoColor=white)](https://youtu.be/Y4uIGEbHock?si=SrHmUFTGmJtcd0hO)

---

### 🌐 Live Deployment & Resources
- **🖥️ Live Web Application:** [https://agentprep.netlify.app](https://agentprep.netlify.app)
- **🎥 YouTube Video Walkthrough:** [https://youtu.be/Y4uIGEbHock?si=SrHmUFTGmJtcd0hO](https://youtu.be/Y4uIGEbHock?si=SrHmUFTGmJtcd0hO)
- **⚡ Live Backend API & Swagger Docs:** [https://cube26-prp-0310-fasihafatima06.onrender.com/docs](https://cube26-prp-0310-fasihafatima06.onrender.com/docs)
- **📦 GitHub Repository:** [https://github.com/fasihafatima06/cube26-prp-0310-fasihafatima06](https://github.com/fasihafatima06/cube26-prp-0310-fasihafatima06)

---

## 1. Problem Understanding

When physical merchandise arrives at an e-commerce fulfillment center (e.g. Amazon FBA), it must comply with stringent packaging, sealing, and labeling rules. Non-compliant units incur:
- **$25.00 defect penalties** per unit.
- Receiving delays, return-to-sender freight costs, and suspended seller accounts.
- Severe operational margin pressure: Prep centers operate on razor-thin **$0.40 to $1.10 per unit** margins.

Traditional warehouse lines rely on manual human inspection which is error-prone, slow, and provides no audit trail when disputed defect fees arrive 6 weeks later.

---

## 2. What AgentPrep Does

AgentPrep is an operational AI/computer-vision prep compliance agent for warehouse receiving.
A warehouse operator selects a product and uploads photographs of the prepared product.
AgentPrep evaluates the photographs against product-specific preparation rules and returns:
- **PASS**: Granted only when visual evidence directly confirms compliance.
- **FAIL**: Granted only when visual evidence directly proves a violation.
- **UNCERTAIN**: Granted when evidence is insufficient, blurred, glare-obscured, or missing views.

### Core Guiding Principle: "NEVER INVENT EVIDENCE"
If the available images do not provide enough evidence, the system **MUST return UNCERTAIN** rather than guessing PASS or FAIL.

---

## 3. Multi-Agent System Architecture

AgentPrep coordinates 6 specialized subagents through a deterministic orchestrator:

```
PERCEPTION  ──▶  EVIDENCE  ──▶  RULES  ──▶  SUFFICIENCY  ──▶  DECISION  ──▶  ACTION
```

1. **Prep Manager Agent**: Primary orchestrator coordinating the inspection lifecycle and audit trail.
2. **Evidence Agent**: Evaluates image clarity, exposure, glare, and required view angle coverage (`front`, `back`, `side`).
3. **Packaging Agent**: Inspects transparent polybag presence, bag boundaries, and heat-seal integrity.
4. **Barcode / Label Agent**: Verifies FNSKU label placement flatness (never crossing curved edges or seams) and ensures manufacturer UPC/EAN barcodes are completely covered.
5. **OCR / Text Agent**: Transcribes suffocation warnings, checks legibility, and parses expiration dates and orientation marks (`THIS WAY UP`, `FRAGILE`).
6. **Rules Agent**: Evaluates product-specific rules dynamically loaded from the database.
7. **Decision Agent**: Calculates evidence sufficiency and generates actionable operator steps.

---

## 4. Product-Specific Demo Catalog

Rules are **never hardcoded** in frontend components; they are persisted in SQLite and loaded dynamically:

| Product | Name | Category | Rules Enforced |
| :--- | :--- | :--- | :--- |
| **Product A** | Demo Bottle (`DEMO-BOTTLE-001`) | Liquid / Bottle | Polybag Presence, Polybag Sealing, Suffocation Warning, FNSKU Placement, Original Barcode Covered, Plastic Thickness (3 mil - physical) |
| **Product B** | Boxed Electronics (`DEMO-ELEC-002`) | Boxed Electronics | FNSKU Placement, Original Barcode Covered, Handling Marks Visible, Drop-Test Durability (physical) |
| **Product C** | Plush Toy (`DEMO-TOY-003`) | Plush & Soft Goods | Polybag Presence, Suffocation Warning, FNSKU Placement |

---

## 5. Quickstart & Local Setup

### Prerequisites
- Python 3.10+ (tested on Python 3.10 – 3.14)
- Node.js 18+ and npm

### 1. Backend Setup (FastAPI)
```bash
# From workspace root
cd backend

# Install dependencies
pip install -r requirements.txt

# Run automated test suite (all 15 tests pass)
pytest -v test_agentprep.py

# Launch FastAPI server
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```
- API Swagger Docs: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- Health check: [http://127.0.0.1:8000/](http://127.0.0.1:8000/)

### 2. Frontend Setup (Next.js)
```bash
# In a new terminal from workspace root
cd frontend

# Install dependencies (if not already installed)
npm install

# Start Next.js development server
npm run dev
```
- Open [http://localhost:3000](http://localhost:3000) in your browser.

---

## 6. Environment Variables

Create `.env` based on `.env.example`:

```ini
# Computer Vision Engine
VISION_PROVIDER=local       # 'local' (deterministic engine) or 'openai' / 'gemini'
VISION_API_KEY=            # API key for external VLM if configured
VISION_MODEL=gpt-4o-mini   # External VLM model name
OCR_PROVIDER=local
REASONING_PROVIDER=rules
DATABASE_URL=sqlite:///./database.db

# Frontend
PORT=8000
NEXT_PUBLIC_API_URL=http://127.0.0.1:8000
```

> **Security Note**: Never commit API keys or `.env` files. Secrets are read exclusively through environment variables on the backend.

---

## 7. API Endpoints Contract

AgentPrep exposes a fully typed REST API:

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `POST` | `/api/inspections` | Upload photographs and run multi-agent inspection |
| `GET` | `/api/inspections` | List inspection history with status and product filters |
| `GET` | `/api/inspections/{id}` | Get complete inspection response with checks and agent events |
| `GET` | `/api/inspections/{id}/evidence` | Get structured compliance evidence with real bounding box coordinates |
| `GET` | `/api/inspections/{id}/agent-event` | Get machine-readable agent event contract |
| `POST` | `/api/inspections/{id}/additional-evidence` | Upload supplementary photos (e.g. rear view) for uncertain checks |
| `POST` | `/api/inspections/{id}/feedback` | Operator override / continuous learning feedback |
| `GET` | `/api/inspections/{id}/recovery-claim` | Pod 05 Recovery Manager disputable claim payload |
| `GET` | `/api/products` | List all registered products |
| `GET` | `/api/products/{id}/rules` | Get dynamic preparation requirements for a product |
| `GET` | `/api/rules` | Registry of all active rules with visual verifiability flags |
| `GET` | `/api/agent/status` | Current status of Prep Manager and 6 active worker subagents |
| `GET` | `/api/agent/activity` | Real-time audit trail of orchestrator and subagent events |

---

## 8. Acceptance Test Results

AgentPrep is verified across 7 core acceptance scenarios backed by automated test suites:

| Scenario | Input Product & Visual Evidence | Expected Result | Actual Result | Status |
| :--- | :--- | :--- | :--- | :---: |
| **Scenario 1** | Demo Bottle: Polybag present, sealed, warning legible, flat FNSKU, barcode covered | **PASS** | **PASS** | `PASSED` |
| **Scenario 2** | Demo Bottle: FNSKU crosses curved package edge | **FAIL** (Curved edge violation) | **FAIL** (Curved edge violation) | `PASSED` |
| **Scenario 3** | Demo Bottle: Original UPC barcode left exposed on rear | **FAIL** (Exposed barcode) | **FAIL** (Exposed barcode) | `PASSED` |
| **Scenario 4** | Demo Bottle: Polybag missing suffocation warning text | **FAIL** (Missing warning) | **FAIL** (Missing warning) | `PASSED` |
| **Scenario 5** | Demo Bottle: Front view only; rear surface omitted | **UNCERTAIN** (Needs rear photo) | **UNCERTAIN** (Needs rear photo) | `PASSED` |
| **Scenario 6** | Boxed Electronics: Severe lighting glare and motion blur | **UNCERTAIN** (Quality insufficient) | **UNCERTAIN** (Quality insufficient) | `PASSED` |
| **Scenario 7** | Plush Toy: Compliant polybagging and warning print | **PASS** | **PASS** | `PASSED` |

### Key Acceptance Test (Section 25)
- **Input**: Demo Bottle with FNSKU overlapping curved edge.
- **Output**:
  - `OVERALL: FAIL`
  - `Polybag Presence: PASS`
  - `Suffocation Warning: PASS`
  - `FNSKU Placement: FAIL` (Reason: *FNSKU barcode label bounding box intersects a curved package edge or seam.*)
  - `Original Barcode Covered: PASS` (Reason: *Original barcode appears fully covered.*)
  - `Agent Action: CORRECT_AND_RESCAN` (Action: *Reposition FNSKU label entirely onto the flat front surface.*)

---

## 9. Security & Untrusted Input Protection

1. **Upload Validation**: File extension validation (`.jpg`, `.jpeg`, `.png`, `.webp`), 10 MB payload limits, and UUID sanitization.
2. **OCR Prompt Injection Shield**: OCR text extracted from package labels is strictly treated as untrusted data. Strings such as *"IGNORE ALL PREVIOUS INSTRUCTIONS"* are never injected into LLM system prompts.
3. **No Secret Exposure**: Zero secrets or credentials are sent to the client browser.
4. **Deterministic Fallback**: Runs 100% locally with zero external API calls if no VLM key is provided.

---

## 10. Assumptions & Limitations

- **Assumptions**:
  - Minimum photographic resolution $\ge 640 \times 480\text{ px}$.
  - Camera views are labeled or determined through multi-angle capture workflows.
- **Limitations**:
  - Physical properties (plastic film gauge, micrometer thickness, adhesive tensile strength, drop-test impact) cannot be reliably determined from 2D photographs and return `UNCERTAIN / Out of Scope`.
  - Hidden surfaces not captured in photos cannot be evaluated without additional captures.
