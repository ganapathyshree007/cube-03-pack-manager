# 02 · Press Release & FAQ (PR/FAQ)

## FOR IMMEDIATE RELEASE

### AI Recovery Operations Center Turns Physical Warehouse Logs into Defensible Financial Recovery Claims

**BANGALORE & SAN FRANCISCO — September 26, 2026** — Today marks the launch of **RCY Recovery Manager**, an evidence-grounded financial recovery platform that bridges the multi-million dollar divide between physical warehouse operations and e-commerce channel deductions. Built on strict conservative reasoning principles, Recovery Manager replaces blunt-force dispute bots with verifiable, audit-grade proof chains.

E-commerce brands lose an estimated 1.5% to 3% of top-line revenue annually to marketplace deductions: inbound defect penalties, alleged lost cartons, unreturned customer refunds, and dimension overcharges. While warehouse teams scrupulously inspect, prep, and photograph units prior to carrier handover, these operational records remain trapped in siloed warehouse systems while marketplace fee deductions pass unchallenged.

"Traditional recovery agencies play a numbers game: dispute everything and hope 20% stick," said Charan, Lead Architect of Recovery Manager. "That shotgun approach destroys channel trust. We designed Recovery Manager like a forensic financial investigator. If we can prove compliance with prep timestamps and operator logs, we build a bulletproof claim. If the evidence is missing or ambiguous, our agent says *SILENT* or *UNCERTAIN* and claims zero dollars. Conservative accuracy beats ungrounded volume every single time."

Key capabilities include:
- **Multi-Hop Hybrid RAG:** Traverses from financial charge to shipment, order, SKU, and upstream logs across Receiving, Prep, Pack, and Returns.
- **Evidence Graph & Chronological Timeline:** Interactively renders the physical unit lifecycle from supplier delivery to post-shipment fee deduction.
- **Conservative Reasoning Engine:** Explicitly handles `SILENT` (insufficient evidence) and `UNCERTAIN` (ambiguous custody) states.
- **Why Not Claim? Audit Drawer:** Transparently explains why specific charges cannot be claimed, identifying missing proof points.
- **Frozen Claim Packages:** Generates immutable dispute dossiers with exact monetary figures and evidentiary citations.

---

## Frequently Asked Questions (FAQ)

### 1. Does Recovery Manager use computer vision or inspect photos directly?
**No.** Recovery Manager is strictly an evidence-reasoning agent, not a computer vision model. It consumes structured operational logs, inspection checklists, and verified metadata produced by upstream Managers (Receiving, Prep, Pack, Returns). Photographic references are retained as audit attachments, but decision logic is derived purely from structured findings and immutable event logs.

### 2. What happens if a charge has no matching warehouse record?
The agent returns `SILENT`. It sets potential recovery to \$0.00 and generates an explicit "Why Not Claim?" explanation stating that no direct physical verification log exists for the unit. The system **never fabricates evidence or guesses**.

### 3. How does the system prevent duplicate claim filings?
The agent contains deterministic pre-evaluation gates that check for duplicate charge IDs, identical shipment/unit reason pairs within the same billing cycle, and offsetting reimbursement entries. If an existing claim or reimbursement exists, the charge is flagged as `DUPLICATE` or `ALREADY_REIMBURSED` with claimability set to false.

### 4. How is multi-tenant company data protected?
Every database query and retrieval vector is strictly scoped to `company_id`. Tenant isolation is enforced at the database schema level. An organization (`org_demo_alpha`) cannot inspect, query, or infer records belonging to another organization (`org_demo_bravo`).

### 5. Why is 100% precision prioritized over higher claim volume?
Disputing invalid charges triggers marketplace account reviews, fines, and potential suspension of FBA inbound privileges. A false claim costs seller standing; a conservative skip costs only the immediate deduction. By maintaining high precision, Recovery Manager claims are consistently accepted by marketplace dispute teams.
