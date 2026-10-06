# Cube Buildathon · 05 · Recovery Manager

**Commerce Context stream · Round 2 · Individual Build · Charan (`charan-dss-01`)**

> Five agents, one unit, one record that follows it.
> A physical product arrives, gets prepped, gets shipped, comes back. At every step a person makes a fast judgment that nobody records. **You build the agent that makes one of those judgments, and leaves proof.**

---

## 🌐 Live Production Deployments

| Component | Platform | Live URL | Status |
|---|---|---|---|
| **Frontend Operations Center** | Vercel | [https://cube26-rcy-0079.vercel.app/](https://cube26-rcy-0079.vercel.app/) | ✅ Online |
| **Backend REST API Core** | Render | [https://rcy-recovery-backend.onrender.com/](https://rcy-recovery-backend.onrender.com/) | ✅ Online |
| **API Documentation (Swagger)** | Render | [https://rcy-recovery-backend.onrender.com/docs](https://rcy-recovery-backend.onrender.com/docs) | ✅ Online |

---

## 🚀 Live Working Implementation & Submission Assets

This repository houses the complete, working **RCY Recovery Operations Center**:

- **Submissions Index:** [`submissions/charan-dss-01/README.md`](submissions/charan-dss-01/README.md)
- **Customer Letter:** [`submissions/charan-dss-01/01-customer-letter.md`](submissions/charan-dss-01/01-customer-letter.md)
- **PR/FAQ:** [`submissions/charan-dss-01/02-prfaq.md`](submissions/charan-dss-01/02-prfaq.md)
- **One-Pager:** [`submissions/charan-dss-01/03-one-pager.md`](submissions/charan-dss-01/03-one-pager.md)
- **Durable Constraints & Rules:** [`submissions/charan-dss-01/CLAUDE.md`](submissions/charan-dss-01/CLAUDE.md)
- **Architecture Specification:** [`ARCHITECTURE.md`](ARCHITECTURE.md)
- **Evaluation & Precision Report:** [`submissions/charan-dss-01/eval-report.md`](submissions/charan-dss-01/eval-report.md)
- **Cross-Pod Contract:** [`submissions/charan-dss-01/contract/evidence_contract.json`](submissions/charan-dss-01/contract/evidence_contract.json)
- **Headless Agent CLI Runner:** [`submissions/charan-dss-01/agent/run_recovery.py`](submissions/charan-dss-01/agent/run_recovery.py)

---

## 1. Problem Understanding

E-commerce brands selling across marketplaces (Amazon FBA, Walmart Marketplace, Target+) regularly suffer from automated penalty fees and deductions, including:
- **Inbound Defect Fees:** Alleged polybag missing, unsealed packaging, missing suffocation warnings, or unreadable FNSKU barcodes.
- **Fulfillment Fee Weight Tier Penalties:** Marketplace mis-weighing packages and overcharging on dimensional weight tiers.
- **Lost Inbound Inventory:** Cartons received short at fulfillment centers without automatic reimbursement.
- **Unreturned Customer Items:** Customer refunded for a return, but merchandise is never returned to active merchant inventory.

These deduction line items appear in accounting fee reports weeks after items depart the warehouse. The proof required to dispute these charges lives in fragmented, unstructured operational silos across the warehouse floor:
- **Receiving Docks:** Inbound carton scans, gross pallet scale weights, carrier bills of lading.
- **Prep Stations:** Polybag sealing logs, suffocation warnings, FNSKU barcode placement.
- **Pack Benches:** Carton packing scans, item tare weights, dimensional measurements.
- **Returns Lines:** LPN reverse-logistics inspections, restock dispositions.

Because manually correlating each deduction line item against floor logs is time-consuming and tedious, merchants forfeit **15% to 30% of their net operating margins** to uncontested fees. Meanwhile, legacy auto-dispute scrapers blindly dispute charges without proof, leading to marketplace account warnings and audit bans.

---

## 2. Solution Overview

**RCY Recovery Manager** is an evidence-first, multi-tenant AI operations center that turns physical warehouse records into defensible, audit-grade recovery claims:
- **Record-First Architecture:** Eliminates expensive computer vision hardware by ingesting structured scanner logs, weight scale timestamps, and custody transfers.
- **Deterministic Multi-Hop Graph Traversal:** Traverses relational hops ($\text{Charge} \to \text{Unit} \to \text{Shipment} \to \text{Order} \to \text{Operational Floor Log}$) to uncover proof even when identifiers differ.
- **Three-State Verdict Engine:**
  - `CONTRADICTED`: Upstream proof proves compliance prior to custody transfer $\to$ Defensible claim package generated (100% precision).
  - `SUPPORTED`: Floor logs confirm a genuine merchant defect $\to$ Claim safely skipped to protect account standing.
  - `SILENT`: Insufficient physical proof $\to$ Conservative skip with $0.00 recovery (zero hallucinated disputes).
  - `UNCERTAIN`: Conflicting timestamps or split custody $\to$ Flagged for human review.
- **Audit-Grade Claim Dossier Builder:** Automatically compiles formal dispute narrative letters, fact comparison tables, and immutable evidence attachments ready for Seller Central or 3PL submission.
- **"AI Prepares, Human Authorizes":** The AI agent conducts 99% of the tedious correlation and forensic analysis, while human operators review and authorize claim package freezing.

---

## 3. Setup Instructions

### Prerequisites
- Node.js 18+ and npm
- Python 3.10+ (tested on Python 3.11, 3.12, 3.14)
- Git

### Backend Setup (FastAPI)
```powershell
cd backend
python -m venv .venv

# On Windows:
.venv\Scripts\activate
# On Linux/macOS:
# source .venv/bin/activate

pip install -r requirements.txt
python seed.py        # Initializes multi-tenant schema & seeds baseline datasets (Alpha & Bravo)
pytest tests/ -v      # Runs automated verification suite (8/8 passing)
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```
The backend API and Swagger docs will be live at `http://127.0.0.1:8000/docs`.

### Frontend Setup (Next.js 14)
```powershell
cd frontend
npm install
npm run build         # Validates production build (10/10 routes)
npm run dev           # Starts local development server on port 3000
```
Open [http://localhost:3000](http://localhost:3000) to view the Operations Center and Landing Page.

### Headless Agent CLI Runner
```powershell
cd submissions/charan-dss-01/agent
python run_recovery.py --company org_demo_alpha
```

---

## 4. Usage Instructions

1. **Explore Live Operations Dashboard (`/dashboard`)**:
   - View top-level financial KPIs: Total Fees Assessed ($1,768.50), Recoverable Pipeline ($552.00–$928.50), Claim Precision Rate (100%), and Conservative Skips (43).
   - Inspect fee category breakdowns and verdict distributions.
   - Switch workspace tenants (`org_demo_alpha` vs. `org_demo_bravo`) in the top-right header to verify multi-tenant isolation.
2. **Ingest Warehouse Records & Fee Reports (`/data-sources`)**:
   - Drag and drop CSV, XLSX, PDF, or JSON files.
   - The parser inspects filenames and column headers to auto-categorize into `fee_report`, `receiving`, `prep`, `pack`, or `returns`.
   - Inspect the interactive Schema Preview and click "Confirm Ingestion" to write to the tenant database.
3. **Inspect Deductions (`/charges`)**:
   - Filter and search charges by status (`CONTRADICTED`, `SILENT`, `SUPPORTED`, `UNCERTAIN`), marketplace source, or date range.
   - Click "Investigate" on any charge (e.g., `CH-TC07-DUPLICATE`).
4. **Deep-Dive Forensic Analysis (`/investigations/[chargeId]`)**:
   - Interact with the **Multi-Hop Entity Graph** showing node linkages across Charge, Unit, Shipment, Order, and Evidence.
   - Review the **Chronological Custody Timeline** with operator IDs and timestamps.
   - Click the **"Why Not Claim?"** drawer on silent or supported charges to inspect the conservative rationale.
5. **Run Batch Recovery Pipeline (`/recovery`)**:
   - Trigger the agent to evaluate charges in batch mode.
   - Review qualified recoverable pipeline totals.
6. **Generate Frozen Claim Packages (`/claims`)**:
   - Click "View Dossier" or "Generate Claim Package" to view the formal legal dispute letter, fact comparison table, and operator citations.
   - Export claim packages as structured JSON or print to PDF for marketplace submission.

---

## 5. Assumptions & Limitations

### Assumptions
1. **Record-First Grounding:** Assumes upstream operational stations (Receiving, Prep, Pack, Returns) record barcode scans, weight measurements, or operator dispositions.
2. **Deterministic Entity Linking:** Assumes units can be correlated via shared identifiers (`unit_id`, `shipment_id`, `order_id`, or tracking numbers) across system hops.
3. **Conservative Discard Policy:** Assumes avoiding false claims is strictly more valuable than speculative claiming, prioritizing marketplace account health over dispute volume.

### Limitations
1. **No Vision / Image Heuristics:** The system deliberately does not analyze camera feeds or unlabeled photos; it relies strictly on structured operational logs.
2. **Channel Policy Variability:** Marketplace dispute guidelines vary across categories and channels; specific dispute requirements may require rule updates.
3. **Human Authorization for Submission:** To prevent accidental mass dispute spam, the UI requires operator authorization ("Generate Claim Package") before freezing a claim package for export.

---

## Your problem statement: Recovery Manager

|                              |                                                          |
| ---------------------------- | -------------------------------------------------------- |
| **Position in the chain**    | Step 5 of 5. Money back. This step has no camera.        |
| **Customer**                 | Anyone being charged fees they do not owe                |
| **What gets recorded**       | Claim filed                                              |
| **Who consumes your output** | The seller, and whoever reviews the claim at the channel |

Amazon charges inbound defect fees, loses units, damages inventory and mis-weighs parcels. Sellers are owed reimbursements they never claim, and charged fees they cannot contest, because contesting requires evidence and they have none. Today this is done by hand, by agencies taking a percentage, or not at all.

**This is not a vision agent.** No camera, no capture surface. It reads the evidence records the other four Managers produce, matches them against channel fee and reimbursement reports, and assembles a claim.

* Ingest a fee or reimbursement report and parse the charges
* Match each charge to the unit evidence covering it
* Decide whether the evidence contradicts the charge, supports it, or is insufficient
* Assemble a disputable claim with evidence attached and a dollar figure
* State explicitly what it cannot claim, and why

> **Build against the official evidence contract.** Recovery depends on the evidence produced by the other four Managers. For Round 2, use the evidence contract provided by the organisers as the baseline rather than creating a separate cross-pod contract.

> **Your eval is different.** Others measure a model against human labels on units. You measure claim correctness on charges, and you report precision, because a wrongly filed claim costs a seller standing with the channel while a missed one costs only money.

### The chain you are part of

```text
 Supplier delivery      Inbound to Amazon     Outbound to buyer     Customer return        Money back
 ┌──────────────┐      ┌──────────────┐      ┌──────────────┐      ┌──────────────┐      ┌──────────────┐
 │ 01 Receiving │ ───▶ │ 02 Prep      │ ───▶ │ 03 Pack      │ ───▶ │ 04 Returns   │      │ 05 Recovery  │
 │ condition on │      │ compliance   │      │ contents at  │      │ condition &  │      │ reads all    │
 │ arrival      │      │ proof        │      │ seal         │      │ disposition  │      │ four → claim │
 └──────┬───────┘      └──────┬───────┘      └──────┬───────┘      └──────┬───────┘      └──────▲───────┘
        └─────────────────────┴─────────────────────┴─────────────────────┴─────────────────────┘
```

The first four are the same machine: a camera, a model, and a decision bound to a record. What changes is the ruleset, the buyer and the moment. The fifth has no camera. It turns the other four's records into a claim.

Your output has to be usable by another pod. That's deliberate, and it's scored.

---

## Reference data

`data/` holds a **dummy** CSV for reference while you design and build. Its columns and meanings are listed in [`data/README.md`](data/README.md).

**The data is synthetic.** The SKUs, ASINs, FNSKUs, orders, suppliers, operators and amounts are all invented. The requirement flags and fee amounts are **not** Amazon's real rules or fees. Engineering rule 5 applies: look the authoritative rule up. The `photo_refs` paths are placeholders, and no images ship with this repo. Your fixtures and eval set are yours to capture.

All five buildathon repos share the same `unit_id` values (`UNIT-0001` … `UNIT-0100`). You can follow one unit from receiving through recovery, the same way the real records will be joined. In the sample, each unit takes one route: **FBA** (prep, then Amazon ships it and charges fees) or **merchant-fulfilled / 3PL** (the seller packs it). So a unit has a Prep record or a Pack record, never both.

Recovery also gets `data/upstream/`, a copy of the other four files, so you can practise the join before Round 3 integration.

---

## How this works

You have a defined problem statement, supporting domain information and an engineering repository to build from. Understand the customer and operational workflow before writing code, then build and measure whether the solution works.

Your goal is to turn the Recovery Manager problem into a working, measurable agent.

### What you're given

* This problem statement
* A domain brief covering the real economics, fee structures and what a working day in a warehouse looks like *(shared by the organisers)*
* The engineering rules in [`RULES.md`](RULES.md)
* Repository data and supporting resources
* One fully worked package for Returns Manager (customer letter, PR/FAQ, one-pager) as a reference for the standard expected. **Read it. Don't copy it.**

### What you produce

Build your solution in **your own GitHub fork**.

Your final Round 2 submission should include:

* A working Recovery Manager
* A `README.md` explaining your solution, setup, assumptions and limitations
* An `ARCHITECTURE.md`
* An eval report/results with numbers and named failure modes
* A working demo/video
* A deployment URL, where applicable
* Your mandatory LinkedIn post URL

## Build and submission flow

```text
Understand
    ↓
Build
    ↓
Test
    ↓
Evaluate
    ↓
Document
    ↓
Demo / Deploy
    ↓
Submit
```

Round 2 is an **individual build**.

The official build phase begins on **25 September 2026 at 9:00 AM IST**.

Submissions open from **27 September 2026**.

The final submission deadline is **1 October 2026 at 6:00 PM IST**.

The submission form closes permanently at the deadline. **There is no resubmission.**

All code commits forming your Round 2 submission must be made during the authorised build phase. Do not continue making Round 2 code changes after the build phase ends.

---

## Evaluation

Recovery Manager is evaluated differently from the vision-based Managers.

The primary question is:

> **When Recovery Manager recommends a claim, is that claim actually supported by the available evidence?**

Your evaluation should focus on:

* charge/report parsing,
* charge-to-unit matching,
* upstream evidence matching,
* evidence interpretation,
* claim correctness,
* claim precision,
* uncertainty/review handling,
* false claims and missed recoverable claims,
* important failure modes.

Report the methodology clearly.

### Primary metric

```text
Claim Precision
=
Correctly Supported Claims
--------------------------
All Claims Recommended
```

Where measurable, also report:

* total charges evaluated,
* claims recommended,
* correctly supported claims,
* incorrectly recommended claims,
* missed recoverable claims,
* `UNCERTAIN` / review rate,
* latency/cost where relevant.

---

## Round 2 Evaluation — 100 Points

| Criterion                                    |  Points |
| -------------------------------------------- | ------: |
| Problem Understanding & Solution Relevance   |  **15** |
| Agent Functionality & Decision Quality       |  **25** |
| Evaluation, Accuracy & Uncertainty Handling  |  **25** |
| Evidence, Traceability & Engineering Quality |  **20** |
| UX, Demo & Documentation                     |  **15** |
| **TOTAL**                                    | **100** |

For Recovery Manager, the evaluation focus is on **claim correctness and evidence quality**, not image-level accuracy.

---

## Evidence and decision traceability

Your Recovery Manager should make the claim traceable to the evidence that supports it.

At minimum, the workflow should make it possible to understand:

```text
Charge
   ↓
Unit
   ↓
Upstream Evidence
   ↓
Evidence Interpretation
   ↓
Claim Decision
   ↓
Supporting Evidence
```

Use the official evidence contract provided by the organisers as the baseline for interoperability.

Do not create a separate negotiated evidence schema for Round 2.

---

## PASS · FAIL · UNCERTAIN

For upstream checks and evidence states:

* **PASS** — the evidence supports the condition.
* **FAIL** — the evidence shows the condition is not met.
* **UNCERTAIN** — the evidence is insufficient for a reliable judgment.

`UNCERTAIN` is not simply a low-confidence PASS.

For Recovery, missing, contradictory or insufficient evidence should lead to an appropriate review/uncertain outcome rather than an unsupported claim.

---

## Engineering expectations

* **Tenancy isolation:** If you store persistent data, keep organisation/client data properly isolated.
* **Batch model calls:** Avoid unnecessary repeated model calls.
* **Fail open:** A model or dependency failure should not silently discard incoming information. Preserve the available information and move the case into an appropriate pending/review state.
* **Authoritative rules:** Where an external rule is required, use the authoritative source rather than relying on model memory or synthetic sample values.
* **Evidence traceability:** Preserve the records used to support recovery decisions.

---

## What we're being straight with you about

* **The core assumption is untested.** Nobody knows yet whether the evidence produced by automated upstream Managers will be reliable enough to support recovery claims at scale. Finding out that an assumption does not hold, and documenting that clearly, counts as a useful outcome.
* **Nobody has spoken to a customer yet.** If you can get a real prep center or seller on a call, ask them to rank the five problems by urgency. Don't ask whether they'd buy what you're building.
* **The background documents disagree in places.** A contradiction is a finding. Raise it as an Issue labelled `finding`.

---

## Submission

### Submissions open

**27 September 2026**

### Final deadline

**1 October 2026 · 6:00 PM IST**

The submission form closes permanently at the deadline.

**There is no reopening and no resubmission.**

Your final submission should include:

* your GitHub fork,
* working Recovery Manager,
* `README.md`,
* `ARCHITECTURE.md`,
* evaluation results,
* demo video,
* deployment URL where applicable,
* LinkedIn post URL.

### LinkedIn — Mandatory

Publish a LinkedIn post about your Round 2 build.

The post must:

* mention your Recovery Manager build,
* explain what you built,
* tag **CodeQuesters**,
* tag **Sydon.AI**.

Include the LinkedIn post URL in the submission form.

---

## Commit rule

All code commits forming your Round 2 submission must be made during the authorised build phase.

Round 2 begins:

**25 September 2026 · 9:00 AM IST**

Once the build phase ends, do not continue making Round 2 code changes.

---

## Round 2 → Round 3

Round 2 is about your **individual Recovery Manager**.

Participants selected for Round 3 will work in five-person Pods combining:

```text
Receiving Manager
+
Prep Manager
+
Pack Manager
+
Returns Manager
+
Recovery Manager
```

The objective is to integrate the five specialised agents into one connected end-to-end commerce system.

Your Round 2 implementation should therefore have clear outputs, structured evidence and an understandable interface for downstream integration.

---

*Cube Buildathon · Commerce Context*
