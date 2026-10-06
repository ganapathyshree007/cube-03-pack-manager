# CLAUDE.md · Recovery Manager Constraints & Non-Negotiables

## Non-Negotiable Rules

1. **NO COMPUTER VISION (Rule 1)**
   - Recovery Manager is NOT a vision agent.
   - Do NOT implement cameras, OpenCV pipelines, YOLO models, or image classification.
   - Images exist solely as opaque photo reference URIs (`photo_refs`) stored in records for audit attachments.

2. **NEVER INVENT EVIDENCE (Rule 2)**
   - NEVER fabricate evidence IDs, timestamps, inspection results, or operator notes.
   - Missing evidence MUST trigger `SILENT`.
   - Every claim statement must be directly traceable to a database row.

3. **NEVER INVENT CLAIM AMOUNTS (Rule 3)**
   - Potential recovery can only match the actual documented charge amount.
   - A $38 fee can only yield a $38 potential claim. Never extrapolate or hallucinate damages.

4. **SILENT IS A VALID RESULT (Rule 4)**
   - When evidence does not exist, return `SILENT`, `claim_supported: False`, `claim_amount: 0.0`.
   - Never force a `CONTRADICTED` or `SUPPORTED` verdict simply because an answer is expected.

5. **UNCERTAIN IS A VALID VERDICT (Rule 5 & Engineering Rule 4)**
   - Ambiguous, conflicting, or inconclusive custody logs yield `UNCERTAIN`.
   - `UNCERTAIN` is a first-class outcome, never a low-confidence pass.

6. **TENANCY ISOLATION BEFORE ANY FEATURE (Engineering Rule 1)**
   - Every query must be strictly scoped to `company_id`.
   - Zero row leakage between tenants (`org_demo_alpha` cannot read `org_demo_bravo`).

7. **BATCH MODEL CALLS (Engineering Rule 2)**
   - Batch evaluation across all checks for a unit/shipment in a single pass.

8. **FAIL OPEN (Engineering Rule 3)**
   - System or API errors must move cases to `pending_review` rather than failing warehouse workflows.

9. **FORBIDDEN LANGUAGE**
   - Do NOT say "tamper-evident" or "blockchain" unless cryptographically anchored.
   - Do NOT say "guaranteed reimbursement"—use "defensible claim".
   - Do NOT say "it works well"—report per-check precision, false positives, and false negatives.
