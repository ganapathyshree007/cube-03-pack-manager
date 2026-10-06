# Charan (charan-dss-01) · Recovery Manager

**Cube Buildathon · Round 2 · Step 5 of 5: Money Back**

The AI Recovery Operations Center converts operational evidence logs (Receiving, Prep, Pack, Returns) into defensible, audit-grade fee and reimbursement recovery claims.

---

## 🌐 Live Production Deployments

- **Frontend Operations Center (Vercel):** [https://cube26-rcy-0079.vercel.app/](https://cube26-rcy-0079.vercel.app/)
- **Backend REST API Core (Render):** [https://rcy-recovery-backend.onrender.com/](https://rcy-recovery-backend.onrender.com/)
- **Interactive API Documentation:** [https://rcy-recovery-backend.onrender.com/docs](https://rcy-recovery-backend.onrender.com/docs)

---

## Deliverables Index

| Document | Purpose |
|---|---|
| [`01-customer-letter.md`](01-customer-letter.md) | Customer letter addressing the seller / finance director |
| [`02-prfaq.md`](02-prfaq.md) | Press release and hard questions FAQ |
| [`03-one-pager.md`](03-one-pager.md) | Product metrics table, architecture summary, and kill condition |
| [`CLAUDE.md`](CLAUDE.md) | Durable engineering constraints, forbidden assumptions, and non-negotiables |
| [`build-brief.md`](build-brief.md) | Technical architecture, hybrid RAG, and agent execution graph |
| [`build-log.md`](build-log.md) | Chronological development and milestone log |
| [`eval-report.md`](eval-report.md) | Evaluation methodology, precision metrics, and failure modes analysis |
| [`contract/evidence_contract.json`](contract/evidence_contract.json) | Cross-pod interoperability evidence schema |
| [`agent/run_recovery.py`](agent/run_recovery.py) | Headless agent execution script for CI/CD and automated audits |

---

## Status

| Face | Deliverable | Status |
|---|---|---|
| 1 | Customer letter, PR/FAQ, one-pager | ☑ Complete |
| 2 | CLAUDE.md | ☑ Complete |
| 3 | Headless agent on fixtures | ☑ Complete |
| 4 | Eval report & Precision Metrics | ☑ Complete |
| 5 | Evidence record page & UI Dashboard | ☑ Complete |
| 6 | Cross-pod contract | ☑ Complete |

---

## Kill Condition

> **If an automated recovery agent produces false claims (>5% claim rejection rate by channel due to ungrounded or hallucinated evidence), the system must immediately cease automatic submission and require dual-human review, because false claims destroy seller channel standing.**
