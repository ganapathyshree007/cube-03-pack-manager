# Returns Manager AI Agent

An AI-powered returns inspection dashboard that uses computer vision to automatically evaluate returned products, determine disposition, and flag items for human review.

---

## Problem Understanding

E-commerce and retail operations suffer massive financial losses due to inefficient returns processing. Today, returns inspection is done manually — a human physically examines each returned unit, checks for completeness, assesses condition, and decides whether to restock, refurbish, liquidate, or dispose of the item. This process is:

- **Slow**: Manual inspection creates backlogs at scale
- **Inconsistent**: Human judgment varies across operators and shifts
- **Costly**: Labour-intensive at high return volumes
- **Undocumented**: Decisions lack structured audit trails

**The core challenge**: How do you reliably automate returns inspection across hundreds of SKUs with varying product types, conditions, and evidence quality — while keeping humans in the loop for ambiguous cases?

---

## Solution Overview

The Returns Manager AI Agent provides an end-to-end automated inspection pipeline:

1. **Evidence ingestion** — Each returned unit is linked to photographic evidence (image URLs or base64 data)
2. **AI Vision inspection** — Google Gemini 2.5 Flash analyses the images against the product catalogue to check:
   - **Identity**: Does the returned item match the expected SKU?
   - **Completeness**: Are all expected parts present?
   - **Condition**: What is the physical state of the item?
3. **Disposition engine** — A deterministic rules engine maps AI verdicts to one of four outcomes: `restock`, `refurbish`, `liquidate`, or `dispose`
4. **Human override** — Any record (especially `pending_review` flagged ones) can be manually resolved by an operator with a reason logged for audit
5. **Analytics dashboard** — Visual stats on outcome distributions, return trends, and inspection completion rates
6. **Multi-tenant isolation** — All data is strictly separated by `x-tenant-id` header, supporting multiple organisations on the same instance

---

## Setup

### Prerequisites

- Node.js v18+
- A Google Gemini API key (https://aistudio.google.com/)

### Installation

`ash
# From the agent/ directory
npm install
cd client && npm install && cd ..
`

### Environment Variables

Create a `.env` file in the `agent/` directory:

`env
GEMINI_API_KEY=your_gemini_api_key_here
`

> **Note**: If no API key is provided, the system automatically falls back to **Mock Mode**, which generates realistic demo responses using product context. This is clearly indicated in the UI with a red MOCK MODE badge (turns green AI LIVE when a valid key is detected).

### Running

`ash
npm run dev
`

This starts:
- Backend API server on http://localhost:3001
- Frontend Vite dev server on http://localhost:5173

---

## Usage

### Dashboard
- View all returns across the active tenant (org_demo_alpha or org_demo_bravo)
- See status badges: pending, pending_review, completed
- Click any row to open the detailed inspection view

### Running an AI Inspection
1. Click any return record from the Dashboard
2. Click Run AI Inspection (or Retry AI Inspection if previously flagged)
3. The AI analyses the evidence images and returns:
   - A verdict (PASS / FAIL / UNCERTAIN) and confidence score for each check
   - A final disposition outcome
4. If all checks pass, the record is automatically marked completed with a disposition
5. If any check fails (e.g., identity mismatch), it is flagged as pending_review

### Resolving Pending Reviews (Human Override)
1. Open a record in pending_review state
2. In the Resolve Pending Review panel on the right, select a final disposition
3. Enter a reason for the decision
4. Click Apply Override — the decision is logged with timestamp and operator info

### Analytics Tab
- Bar chart of dispositions (restock / refurbish / liquidate / dispose / pending)
- Donut chart of inspection statuses
- Summary stats: total returns, inspected count, pending count, recovery rate

### Switching Tenants
Use the Tenant Context dropdown in the sidebar to switch between org_demo_alpha and org_demo_bravo.

---

## Assumptions

- **Images are accessible at inspection time**: The system fetches external image URLs when running AI inspection. Hotlink-blocked URLs are gracefully skipped.
- **One Gemini API key serves all tenants**: API key management is a deployment concern, not a per-tenant concern in this implementation.
- **Product catalogue is static**: The catalogue.json file defines expected parts and descriptions per SKU. In production this would be a database.
- **Returns data is seeded from CSV**: The data/returns_sample.csv file is the source of truth for return records. Changes persist in-memory only (reset on server restart).
- **Tenant ID is trusted from the header**: In production, this would be validated against a JWT or session token.
- **Single operator per session**: The override system logs a hardcoded operator_label. A real system would authenticate the human reviewer.

---

## Limitations

- **No persistent storage**: All inspection results and overrides are stored in-memory and are lost on server restart. A production system would use a database (PostgreSQL, Firestore, etc.).
- **Image quality dependency**: AI accuracy degrades significantly with low-resolution, blurry, or poorly lit images.
- **No batch inspection**: Inspection must be triggered per-record from the UI. Bulk AI processing is not yet implemented.
- **External image URLs may expire**: Thumbnails from Google/Amazon shopping results can become unavailable.
- **Rate limits**: The Gemini API has per-minute quotas. High-volume concurrent inspections could hit rate limits (exponential backoff retry is implemented for overload errors).
- **Catalogue coverage**: Only SKUs defined in catalogue.json get AI context. Unknown SKUs are inspected without product-specific guidance.
