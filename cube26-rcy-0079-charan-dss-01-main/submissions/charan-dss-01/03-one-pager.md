# 03 · One-Pager: Recovery Manager (Step 5 of 5)

## Executive Summary
Recovery Manager transforms disconnected physical warehouse records (Receiving, Prep, Pack, Returns) into defensible, audit-grade financial recovery claims against e-commerce channel deductions. Operating strictly without computer vision or hallucinated amounts, it uses conservative hybrid RAG and deterministic legal validation to maintain 100% claim precision.

**Live Production Deployments:**
- **Operations Center (Frontend):** [https://cube26-rcy-0079.vercel.app/](https://cube26-rcy-0079.vercel.app/)
- **REST API Core (Backend):** [https://rcy-recovery-backend.onrender.com/](https://rcy-recovery-backend.onrender.com/)

---

## Core Product Metrics Table

| Metric | Target | Evaluated Actual (Baseline Dataset) | Significance |
|---|---|---|---|
| **Claim Precision** | ≥ 95.0% | **100.0%** (12/12) | 0 false claims submitted to marketplace channel |
| **Claim Rejection / Failure Rate** | ≤ 5.0% | **0.0%** | Zero marketplace standing penalties |
| **Conservative Discard Rate** | First-class | **80.3%** (49/61 charges skipped) | Correctly refuse ungrounded claims (`SILENT` / `UNCERTAIN`) |
| **Tenancy Isolation Leakage** | 0 rows | **0.0 rows** | Complete RLS isolation between Alpha & Bravo |
| **Total Fees Processed** | All lines | **$214.20 USD** (61 lines) | Complete ingestion of sample dataset |
| **Total Recovery Identified** | Grounded | **$438.50 USD** | Defensible fee + lost unit reimbursement |
| **Batch Decision Latency** | < 50ms/unit | **18.2ms/unit** | Millisecond-level throughput on high volumes |

---

## The 4 Evaluation Verdicts

```text
┌─────────────────┬──────────────────────────────────────────────────────────────────┐
│ Verdict         │ Meaning & Recovery Action                                        │
├─────────────────┼──────────────────────────────────────────────────────────────────┤
│ CONTRADICTED    │ Physical logs refute channel allegation → Defensible claim filed │
│ SUPPORTED       │ Warehouse records substantiate channel defect → Dispute skipped  │
│ SILENT          │ Missing physical proof → Claim refused ($0.00)                   │
│ UNCERTAIN       │ Ambiguous custody / conflicting logs → Flagged for human review   │
└─────────────────┴──────────────────────────────────────────────────────────────────┘
```

---

## The Single Kill Condition

> **If the automated agent produces false claims resulting in a >5% rejection rate by channel dispute teams due to ungrounded or hallucinated evidence, the system must immediately cease automatic claim submission and fall back to dual-human review.**
